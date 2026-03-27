from __future__ import annotations

import asyncio
import uuid
import time
import logging
import traceback
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from clanker_zone.config import CouncilConfig
from clanker_zone.council import CouncilBuilder
from clanker_zone.domains.gst.corpus import discover_rule_bundles, discover_rule_bundles_from_chapters
from clanker_zone.domains.gst.dossiers import build_gst_dossiers
from clanker_zone.domains.gst.false_positive_filter import apply_gst_false_positive_filter
from clanker_zone.domains.gst.signals import run_heuristic_signals
from clanker_zone.domains.gst.policy import GST_CONSTITUTION, GST_COUNSEL_ROSTER, GST_DOMAIN_OVERVIEW, GST_OUTPUT_CONTRACT
from clanker_zone.domains.gst.prompts import build_issue_task_prompt, build_task_prompt
from clanker_zone.provider.minimax import MiniMaxProvider, MiniMaxProviderConfig
from clanker_zone.report.persistence import write_deliberation_artifacts
from clanker_zone.workflow import run_issue_council

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("clanker_zone.server")

app = FastAPI(title="Clanker Zone Mission Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"
    EXPIRED = "expired"


class Session:
    def __init__(self, session_id: str, rule_number: str):
        self.id = session_id
        self.rule_number = rule_number
        self.state = SessionState.PENDING
        self.journal: list[dict] = []
        self.queue = asyncio.Queue()
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.report: Optional[dict] = None
        self.error: Optional[str] = None


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.ttl_seconds = 3600
        
    def create_session(self, rule_number: str) -> Session:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = Session(session_id, rule_number)
        self.sessions[session_id] = session
        return session
        
    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)
        
    def expire_sessions(self):
        now = time.time()
        expired_ids = []
        for sid, sess in self.sessions.items():
            if now - sess.created_at > self.ttl_seconds and sess.state != SessionState.RUNNING:
                expired_ids.append(sid)
        for sid in expired_ids:
            self.sessions[sid].state = SessionState.EXPIRED
            logger.info(f"Expired session {sid}")


session_manager = SessionManager()
executor = ThreadPoolExecutor(max_workers=4)


class ReviewRequest(BaseModel):
    rule_number: str
    corpus_path: str = "pc"
    model: str = "MiniMax-M2.7"
    max_concurrency: int = 6


class ReviewResponse(BaseModel):
    session_id: str
    rule_number: str
    status: str


def _discover_bundles(corpus: Path):
    if any(corpus.glob("chapter_*")):
        return discover_rule_bundles_from_chapters(corpus)
    return discover_rule_bundles(corpus)


def background_council_run(session: Session, req: ReviewRequest, event_loop: asyncio.AbstractEventLoop):
    session.state = SessionState.RUNNING
    logger.info(f"Starting background run for session {session.id} (Rule {req.rule_number})")
    
    def emit(event: dict):
        session.journal.append(event)
        event_loop.call_soon_threadsafe(session.queue.put_nowait, event)

    try:
        corpus_path = Path(req.corpus_path)
        bundles = _discover_bundles(corpus_path)
        try:
            bundle = next(b for b in bundles if b.rule_json["metadata"]["rule_number"] == req.rule_number)
        except StopIteration:
            raise ValueError(f"Rule {req.rule_number} not found in corpus {corpus_path}")

        heuristic_signals = []
        try:
            raw_path = Path(bundle.raw_html_path) if bundle.raw_html_path else None
            heuristic_signals = run_heuristic_signals(
                rule_path=Path(bundle.rule_path),
                schema_path=Path(bundle.schema_path),
                raw_path=raw_path,
                hint_json=bundle.hint_json,
            )
        except Exception as exc:
            logger.warning(f"Deterministic signal generation failed: {exc}")

        dossiers = build_gst_dossiers(bundle, heuristic_signals=heuristic_signals)
        builder = CouncilBuilder(CouncilConfig(model_name=req.model), "gst", GST_COUNSEL_ROSTER)
        plan = builder.build_plan(
            dossiers=dossiers,
            constitution=GST_CONSTITUTION,
            domain_overview=GST_DOMAIN_OVERVIEW,
            output_contract=GST_OUTPUT_CONTRACT,
            metadata={"rule_number": req.rule_number, "session_id": session.id},
        )
        
        provider_config = MiniMaxProviderConfig(model=req.model)
        try:
            provider = MiniMaxProvider(provider_config)
            provider.resolve_api_key() # Fail fast if no API key
        except RuntimeError as e:
            logger.error(f"Missing MiniMax API key: {e}")
            raise e
            
        run = run_issue_council(
            plan=plan,
            roster=GST_COUNSEL_ROSTER,
            provider=provider,
            specialist_prompt_builder=build_task_prompt,
            issue_prompt_builder=build_issue_task_prompt,
            max_concurrency=req.max_concurrency,
            on_event=emit,
        )
        
        run.rule_report = apply_gst_false_positive_filter(
            report=run.rule_report,
            dossiers=plan.dossiers,
        )
        
        # Persist run artifacts into a clean hierarchy under reports/
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path("reports") / f"rule_{req.rule_number}" / f"{ts}_{session.id}"
        write_deliberation_artifacts(out_dir=out_dir, plan=plan, run=run)
        
        # We need to emit the filtered report if the false-positive filter changed anything
        # Actually workflow.py emitted report_complete before the filter, so let's emit a final one
        final_report = run.rule_report.model_dump(mode="json")
        session.report = final_report
        emit({
            "type": "report_complete",
            "timestamp": int(time.time() * 1000),
            "report": final_report,
            "filtered": True
        })
        
        session.state = SessionState.COMPLETE
        session.completed_at = time.time()
        logger.info(f"Session {session.id} completed successfully.")
        
    except Exception as exc:
        err_msg = str(exc)
        logger.error(f"Session {session.id} failed: {err_msg}")
        logger.error(traceback.format_exc())
        session.state = SessionState.ERROR
        session.error = err_msg
        emit({
            "type": "error",
            "timestamp": int(time.time() * 1000),
            "error": err_msg
        })
    finally:
        # Push a sentinel to cleanly unblock the websocket if it's waiting
        event_loop.call_soon_threadsafe(session.queue.put_nowait, {"type": "_internal_end"})


@app.post("/api/review", response_model=ReviewResponse)
async def start_review(req: ReviewRequest):
    session = session_manager.create_session(req.rule_number)
    loop = asyncio.get_running_loop()
    executor.submit(background_council_run, session, req, loop)
    return ReviewResponse(session_id=session.id, rule_number=req.rule_number, status=session.state.value)


@app.get("/api/sessions")
async def list_sessions():
    return {
        "sessions": [
            {
                "session_id": s.id,
                "rule_number": s.rule_number,
                "status": s.state.value,
                "created_at": s.created_at,
            }
            for s in session_manager.sessions.values()
            if s.state != SessionState.EXPIRED
        ]
    }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.id,
        "rule_number": session.rule_number,
        "status": session.state.value,
        "created_at": session.created_at,
        "completed_at": session.completed_at,
        "error": session.error,
        "report": session.report,
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()

    # Replay journal
    for event in session.journal:
        if event.get("type") == "_internal_end":
            continue
        try:
            await websocket.send_json(event)
        except WebSocketDisconnect:
            return

    # If already terminal, close gracefully
    if session.state in (SessionState.COMPLETE, SessionState.ERROR, SessionState.EXPIRED):
        await websocket.close()
        return

    # Stream real-time queue
    try:
        while True:
            event = await session.queue.get()
            if event.get("type") == "_internal_end":
                break
            await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from {session_id}")
    except Exception as exc:
        logger.error(f"WebSocket error on {session_id}: {exc}")
    finally:
        if session.state in (SessionState.COMPLETE, SessionState.ERROR):
            try:
                await websocket.close()
            except Exception:
                pass


@app.on_event("startup")
async def startup_event():
    logger.info("Server started.")


@app.on_event("shutdown")
async def shutdown_event():
    executor.shutdown(wait=False)
    logger.info("Server shut down.")
