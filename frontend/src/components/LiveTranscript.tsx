import type { TranscriptMessage } from '../api'

type LiveTranscriptProps = {
  callId: string | null
  messages: TranscriptMessage[]
  status: 'idle' | 'connecting' | 'connected' | 'closed' | 'error'
}

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function LiveTranscript({ callId, messages, status }: LiveTranscriptProps) {
  return (
    <section className="panel transcript-panel">
      <div className="panel-header transcript-header">
        <div>
          <h2>Live Transcript</h2>
          <p>
            {callId
              ? `Streaming call ${callId}`
              : 'Start a patient call to open the live transcript.'}
          </p>
        </div>
        <span className={`transcript-status status-${status}`}>{status}</span>
      </div>

      <div className="transcript-window" aria-live="polite">
        {messages.length === 0 ? (
          <p className="status-message">
            {callId ? 'Waiting for transcript messages...' : 'No active call transcript.'}
          </p>
        ) : (
          messages.map((message, index) => (
            <article
              key={`${message.timestamp}-${index}`}
              className={`transcript-message role-${message.role}`}
            >
              <div className="transcript-message-meta">
                <strong>{message.role === 'agent' ? 'Agent' : 'User'}</strong>
                <span>{formatTimestamp(message.timestamp)}</span>
              </div>
              <p>{message.content}</p>
            </article>
          ))
        )}
      </div>
    </section>
  )
}
