import ToolCard from './ToolCard.jsx'
import '../styles/ToolSidebar.css'

export default function ToolSidebar({ toolEvents }) {
  return (
    <div className="tool-sidebar">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Tool Activity</h2>
        <div className="sidebar-legend">
          <span className="legend-dot" style={{ background: 'var(--accent-github)' }} /> GitHub
          <span className="legend-dot" style={{ background: 'var(--accent-search)' }} /> Search
          <span className="legend-dot" style={{ background: 'var(--accent-filesystem)' }} /> Files
        </div>
      </div>

      <div className="tool-events-list">
        {toolEvents.length === 0 ? (
          <div className="sidebar-empty">
            <p>Tool calls will appear here as the agent works.</p>
          </div>
        ) : (
          toolEvents.map((event) => (
            <ToolCard key={event.call_id} event={event} />
          ))
        )}
      </div>
    </div>
  )
}
