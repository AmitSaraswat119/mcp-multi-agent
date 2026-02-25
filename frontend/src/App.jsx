import { useWebSocket } from './hooks/useWebSocket.js'
import ChatWindow from './components/ChatWindow.jsx'
import ToolSidebar from './components/ToolSidebar.jsx'
import './App.css'

export default function App() {
  const { messages, toolEvents, status, sendMessage, isLoading } = useWebSocket()

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-left">
          <span className="app-logo">⚡</span>
          <h1 className="app-title">MCP Multi-Agent Demo</h1>
        </div>
        <div className={`status-badge status-${status}`}>
          <span className="status-dot" />
          {status === 'connected' ? 'Connected' : status === 'connecting' ? 'Connecting…' : 'Disconnected'}
        </div>
      </header>

      <main className="app-main">
        <section className="chat-panel">
          <ChatWindow
            messages={messages}
            onSend={sendMessage}
            isLoading={isLoading}
            disabled={status !== 'connected'}
          />
        </section>
        <aside className="sidebar-panel">
          <ToolSidebar toolEvents={toolEvents} />
        </aside>
      </main>
    </div>
  )
}
