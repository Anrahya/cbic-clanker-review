import { useEffect, useRef, useState } from 'react'
import { useSessionStore } from '../stores/session'
import type { StreamEvent } from '../lib/types'

const getWsUrl = () => {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws`
}

export function useWebSocket(sessionId: string | null) {
  const store = useSessionStore()
  const [isConnected, setIsConnected] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const processedEventsRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!sessionId) {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      setIsConnected(false)
      reconnectCountRef.current = 0
      processedEventsRef.current.clear()
      return
    }

    function connect() {
      if (wsRef.current?.readyState === WebSocket.OPEN) return
      
      const ws = new WebSocket(`${getWsUrl()}/${sessionId}`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log(`[WS] Connected to session ${sessionId}`)
        setIsConnected(true)
        reconnectCountRef.current = 0
      }

      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data) as StreamEvent
          
          // Basic dedup for replays (events should ideally have IDs, but we can hash timestamp+type+content)
          const eventHash = `${event.timestamp}-${event.type}-${event.counsel_name || ''}-${event.content?.slice(0, 20) || ''}`
          if (processedEventsRef.current.has(eventHash)) {
            return
          }
          processedEventsRef.current.add(eventHash)
          
          store.handleEvent(event)
        } catch (e) {
          console.error('[WS] Failed to parse message:', e)
        }
      }

      ws.onclose = (e) => {
        setIsConnected(false)
        wsRef.current = null
        
        // Don't auto-reconnect if it was a clean terminal close (e.g. 1000 or custom 4004)
        if (e.code === 1000 || e.code === 4004) {
          console.log(`[WS] Connection closed cleanly (code: ${e.code})`)
          return
        }

        const storeStatus = useSessionStore.getState().status
        if (storeStatus === 'complete' || storeStatus === 'error') {
          return // terminal state reached
        }

        // Exponential backoff
        if (reconnectCountRef.current < 10) {
          const delay = Math.min(1000 * Math.pow(2, reconnectCountRef.current), 30000)
          console.log(`[WS] Connection lost. Reconnecting in ${delay}ms...`)
          reconnectCountRef.current++
          reconnectTimeoutRef.current = window.setTimeout(connect, delay)
        } else {
          console.error('[WS] Max reconnect attempts reached.')
          store.handleEvent({ type: 'error', timestamp: Date.now(), error: 'Lost connection to server' })
        }
      }

      ws.onerror = (err) => {
        console.error('[WS] Error:', err)
        // onclose will handle the reconnect
      }
    }

    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted')
        wsRef.current = null
      }
    }
  }, [sessionId, store])

  return { isConnected }
}
