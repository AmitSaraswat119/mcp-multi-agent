import { useState, useEffect, useRef, useCallback } from 'react'

const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/chat`

export function useWebSocket() {
  const [messages, setMessages] = useState([])
  const [toolEvents, setToolEvents] = useState([])
  const [status, setStatus] = useState('disconnected')
  const [isLoading, setIsLoading] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimeout = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setStatus('connecting')
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
    }

    ws.onclose = () => {
      setStatus('disconnected')
      setIsLoading(false)
      // Auto-reconnect after 3 seconds
      reconnectTimeout.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      setStatus('disconnected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleEvent(data)
      } catch (e) {
        console.error('Failed to parse WS message:', e)
      }
    }
  }, [])

  const handleEvent = useCallback((event) => {
    switch (event.type) {
      case 'tool_start':
        setToolEvents(prev => [{
          ...event,
          status: 'running',
          timestamp: Date.now(),
        }, ...prev])
        break

      case 'tool_end':
        setToolEvents(prev => prev.map(e =>
          e.call_id === event.call_id
            ? { ...e, ...event, status: event.error ? 'error' : 'done' }
            : e
        ))
        break

      case 'assistant_message':
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: event.content,
          id: Date.now(),
        }])
        setIsLoading(false)
        break

      case 'error':
        setMessages(prev => [...prev, {
          role: 'error',
          content: event.content,
          id: Date.now(),
        }])
        setIsLoading(false)
        break

      default:
        console.warn('Unknown event type:', event.type)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimeout.current)
      wsRef.current?.close()
    }
  }, [connect])

  const sendMessage = useCallback((content) => {
    if (!content.trim() || wsRef.current?.readyState !== WebSocket.OPEN) return

    setMessages(prev => [...prev, {
      role: 'user',
      content,
      id: Date.now(),
    }])
    setIsLoading(true)

    wsRef.current.send(JSON.stringify({ type: 'user_message', content }))
  }, [])

  return { messages, toolEvents, status, sendMessage, isLoading }
}
