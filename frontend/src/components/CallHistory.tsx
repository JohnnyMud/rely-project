import type { CallAttempt } from '../api'

type CallHistoryProps = {
  attempts: CallAttempt[]
}

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  })
}

function statusLabel(status: CallAttempt['status']): string {
  switch (status) {
    case 'pending':
      return 'Pending'
    case 'success':
      return 'Created'
    case 'failed':
      return 'Failed'
  }
}

export function CallHistory({ attempts }: CallHistoryProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Call Attempts</h2>
        <p>Recent call attempts for the selected patient.</p>
      </div>

      {attempts.length === 0 ? (
        <p className="status-message">No call attempts yet. Select a patient and click Start Call.</p>
      ) : (
        <ul className="call-history">
          {attempts.map((attempt) => (
            <li key={attempt.id} className={`call-item status-${attempt.status}`}>
              <div className="call-item-main">
                <strong>{attempt.patientName}</strong>
                <span className={`status-badge status-${attempt.status}`}>
                  {statusLabel(attempt.status)}
                </span>
              </div>
              <div className="call-item-meta">
                <span>{formatTimestamp(attempt.startedAt)}</span>
                {attempt.message ? <span>{attempt.message}</span> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
