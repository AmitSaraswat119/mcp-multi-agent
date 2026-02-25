import { useState, useRef, useEffect } from 'react'
import ChatMessage from './ChatMessage.jsx'
import '../styles/ChatWindow.css'

export default function ChatWindow({ messages, onSend, isLoading, disabled }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading || disabled) return
    onSend(input.trim())
    setInput('')
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">⚡</div>
            <h2>MCP Multi-Agent Demo</h2>
            <p>Ask me anything! I can search the web, explore GitHub repos, and manage files.</p>
            <div className="chat-suggestions">
              <button className="suggestion" onClick={() => onSend('List repos for octocat')}>
                List repos for octocat
              </button>
              <button className="suggestion" onClick={() => onSend('Search the web for latest AI news')}>
                Search the web for latest AI news
              </button>
              <button className="suggestion" onClick={() => onSend('List the files in my sandbox')}>
                List the files in my sandbox
              </button>
              <button className="suggestion" onClick={() => onSend('Find a popular Python repo on GitHub, read its README, and save a summary locally')}>
                Find a repo, read README, save summary
              </button>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="loading-indicator">
            <div className="loading-dots">
              <span /><span /><span />
            </div>
            <span className="loading-text">Agent is thinking…</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'Connecting to server…' : 'Ask the agent anything… (Enter to send)'}
          disabled={disabled || isLoading}
          rows={1}
        />
        <button
          type="submit"
          className="send-button"
          disabled={!input.trim() || isLoading || disabled}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>
    </div>
  )
}
