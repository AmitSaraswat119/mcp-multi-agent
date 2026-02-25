import '../styles/ChatWindow.css'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const isError = message.role === 'error'

  return (
    <div className={`message-row ${isUser ? 'message-user' : 'message-assistant'}`}>
      {!isUser && (
        <div className="message-avatar">
          {isError ? '⚠' : '⚡'}
        </div>
      )}
      <div className={`message-bubble ${isError ? 'message-error' : ''}`}>
        <pre className="message-content">{message.content}</pre>
      </div>
      {isUser && (
        <div className="message-avatar message-avatar-user">U</div>
      )}
    </div>
  )
}
