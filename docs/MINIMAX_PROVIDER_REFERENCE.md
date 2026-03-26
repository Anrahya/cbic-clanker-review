# MiniMax Provider Reference

This project's live `clanker_zone` review path uses MiniMax M2.7 through the MiniMax platform APIs.

## Core Links

- Text Generation guide:
  [https://platform.minimax.io/docs/guides/text-generation](https://platform.minimax.io/docs/guides/text-generation)
- Text Chat guide:
  [https://platform.minimax.io/docs/guides/text-chat](https://platform.minimax.io/docs/guides/text-chat)
- Prompt Caching:
  [https://platform.minimax.io/docs/api-reference/text-prompt-caching](https://platform.minimax.io/docs/api-reference/text-prompt-caching)
- Quickstart prerequisites:
  [https://platform.minimax.io/docs/guides/quickstart-preparation](https://platform.minimax.io/docs/guides/quickstart-preparation)

## Notes For This Repo

- The project currently targets `MiniMax-M2.7`.
- Provider integration lives in [clanker_zone/provider/minimax.py](/Users/renoa/Documents/cbic-verify/clanker_zone/provider/minimax.py).
- The local `.env` may contain `MINIMAX_API_KEY`, and the provider auto-loads it for `clanker-zone` commands.
- Prompt caching matters for this project because the council uses large repeated prompt prefixes across many dossier reviews.

## Recommended Reading Order

1. Quickstart prerequisites
2. Text Generation guide
3. Prompt Caching reference
4. Text Chat guide

The Text Chat guide is useful background, but the core reasoning/review pipeline should follow the Text Generation and provider compatibility references first.
