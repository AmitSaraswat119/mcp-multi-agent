import { useState } from 'react'
import '../styles/ToolCard.css'

function getServerColor(toolName) {
  if (toolName.startsWith('github_')) return 'var(--accent-github)'
  if (toolName === 'web_search' || toolName === 'get_answer' || toolName.startsWith('web_')) return 'var(--accent-search)'
  if (toolName.startsWith('fs_')) return 'var(--accent-filesystem)'
  return 'var(--text-muted)'
}

function getServerLabel(toolName) {
  if (toolName.startsWith('github_')) return 'GitHub'
  if (toolName === 'web_search' || toolName === 'get_answer' || toolName.startsWith('web_')) return 'Search'
  if (toolName.startsWith('fs_')) return 'Files'
  return 'Tool'
}

function formatArgs(args) {
  if (!args || Object.keys(args).length === 0) return ''
  return Object.entries(args)
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join(', ')
}

export default function ToolCard({ event }) {
  const [expanded, setExpanded] = useState(false)
  const color = getServerColor(event.tool)
  const label = getServerLabel(event.tool)
  const isRunning = event.status === 'running'
  const isError = event.status === 'error'

  return (
    <div className="tool-card" style={{ '--server-color': color }}>
      <div className="tool-card-header" onClick={() => !isRunning && setExpanded(e => !e)}>
        <div className="tool-card-left">
          <span className="server-badge" style={{ background: color }}>
            {label}
          </span>
          <span className="tool-name">{event.tool}</span>
        </div>
        <div className="tool-card-right">
          {isRunning ? (
            <div className="tool-spinner" />
          ) : isError ? (
            <span className="tool-status-icon tool-status-error">✗</span>
          ) : (
            <span className="tool-status-icon tool-status-done">✓</span>
          )}
          {!isRunning && (
            <span className="expand-icon">{expanded ? '▲' : '▼'}</span>
          )}
        </div>
      </div>

      <div className="tool-args">
        {formatArgs(event.args)}
      </div>

      {expanded && event.result && (
        <div className="tool-result">
          <div className="tool-result-label">Result</div>
          <pre className="tool-result-content">{event.result}</pre>
        </div>
      )}
    </div>
  )
}
