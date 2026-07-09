import { useEffect, useState } from 'react'
import {
  createTranscriptSocket,
  createCall,
  fetchPatients,
  fetchCallRecords,
  isTranscriptSnapshot,
  type CallAttempt,
  type Patient,
  type TranscriptMessage,
  type TranscriptSocketEvent,
} from './api'
import { CallHistory } from './components/CallHistory'
import { LiveTranscript } from './components/LiveTranscript'
import { PatientTable } from './components/PatientTable'

function App() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null)
  const [callAttempts, setCallAttempts] = useState<CallAttempt[]>([])
  const [loadingPatients, setLoadingPatients] = useState(true)
  const [patientsError, setPatientsError] = useState<string | null>(null)
  const [startingCall, setStartingCall] = useState(false)
  const [activeTranscriptCallId, setActiveTranscriptCallId] = useState<string | null>(null)
  const [transcriptMessages, setTranscriptMessages] = useState<TranscriptMessage[]>([])
  const [transcriptStatus, setTranscriptStatus] = useState<
    'idle' | 'connecting' | 'connected' | 'closed' | 'error'
  >('idle')

  useEffect(() => {
    let cancelled = false

    async function loadPatients() {
      setLoadingPatients(true)
      setPatientsError(null)

      try {
        const data = await fetchPatients()
        if (!cancelled) {
          setPatients(data)
        }
      } catch (error) {
        if (!cancelled) {
          setPatientsError(
            error instanceof Error ? error.message : 'Failed to load patients',
          )
        }
      } finally {
        if (!cancelled) {
          setLoadingPatients(false)
        }
      }
    }

    void loadPatients()

    return () => {
      cancelled = true
    }
  }, [])

  const selectedPatient = patients.find((patient) => patient.id === selectedPatientId)

  useEffect(() => {
    let cancelled = false

    async function loadCallRecords() {
      if (!selectedPatientId || !selectedPatient) {
        setCallAttempts([])
        return
      }

      try {
        const data = await fetchCallRecords(selectedPatientId)
        if (cancelled) {
          return
        }

        const mappedAttempts: CallAttempt[] = data.map((record) => ({
          id: record.call_attempt_id,
          patientId: record.patient_id,
          patientName: `${selectedPatient.first_name} ${selectedPatient.last_name}`,
          startedAt: record.started_at ?? record.created_at,
          status:
            record.call_status === 'failed'
              ? 'failed'
              : record.call_status === 'pending'
                ? 'pending'
                : record.call_status === 'ended'
                  ? 'ended'
                  : 'initiated',
          message: record.summary ?? undefined,
          retellCallId: record.retell_call_id,
        }))
        setCallAttempts(mappedAttempts)
      } catch {
        if (!cancelled) {
          setCallAttempts([])
        }
      }
    }

    void loadCallRecords()

    return () => {
      cancelled = true
    }
  }, [selectedPatientId, selectedPatient])

  async function handleStartCall() {
    if (!selectedPatient) {
      return
    }

    const attemptId = crypto.randomUUID()
    const startedAt = new Date().toISOString()

    setCallAttempts((current) => [
      {
        id: attemptId,
        patientId: selectedPatient.id,
        patientName: `${selectedPatient.first_name} ${selectedPatient.last_name}`,
        startedAt,
        status: 'pending',
      },
      ...current,
    ])
    setStartingCall(true)

    try {
      const callRecord = await createCall(selectedPatient.id)
      setActiveTranscriptCallId(callRecord.retell_call_id)
      setCallAttempts((current) =>
        current.map((attempt) =>
          attempt.id === attemptId
            ? {
                ...attempt,
                id: callRecord.call_attempt_id,
                status: 'initiated',
                message: 'Call record created.',
                retellCallId: callRecord.retell_call_id,
              }
            : attempt,
        ),
      )
    } catch (error) {
      setCallAttempts((current) =>
        current.map((attempt) =>
          attempt.id === attemptId
            ? {
                ...attempt,
                status: 'failed',
                message:
                  error instanceof Error
                    ? error.message
                    : 'Failed to create call record.',
              }
            : attempt,
        ),
      )
    } finally {
      setStartingCall(false)
    }
  }

  useEffect(() => {
    if (!activeTranscriptCallId) {
      setTranscriptMessages([])
      setTranscriptStatus('idle')
      return
    }

    setTranscriptMessages([])
    setTranscriptStatus('connecting')

    const socket = createTranscriptSocket(activeTranscriptCallId)

    socket.addEventListener('open', () => {
      setTranscriptStatus('connected')
    })

    socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data as string) as TranscriptSocketEvent
      if (isTranscriptSnapshot(message)) {
        setTranscriptMessages(message.messages)
      } else {
        setTranscriptMessages((current) => [...current, message])
      }
    })

    socket.addEventListener('error', () => {
      setTranscriptStatus('error')
    })

    socket.addEventListener('close', () => {
      setTranscriptStatus((current) => (current === 'error' ? 'error' : 'closed'))
    })

    return () => {
      socket.close()
    }
  }, [activeTranscriptCallId])

  return (
    <main className="app">
      <header className="app-header">
        <div>
          <p className="eyebrow">Patient AI Appointment Reminder</p>
          <h1>Patient Calling Portal</h1>
          <p className="lede">
            Select a patient, then start a call attempt.
          </p>
        </div>

        <button
          type="button"
          className="primary-button"
          disabled={!selectedPatient || startingCall}
          onClick={() => void handleStartCall()}
        >
          {startingCall ? 'Starting Call...' : 'Start Call'}
        </button>
      </header>

      <section className="panel">
        <div className="panel-header">
          <h2>Patient List</h2>
          <p>
            {selectedPatient
              ? `Selected: ${selectedPatient.first_name} ${selectedPatient.last_name}`
              : 'Select a patient to enable Start Call.'}
          </p>
        </div>

        <PatientTable
          patients={patients}
          selectedPatientId={selectedPatientId}
          onSelectPatient={setSelectedPatientId}
          loading={loadingPatients}
          error={patientsError}
        />
      </section>

      <LiveTranscript
        callId={activeTranscriptCallId}
        messages={transcriptMessages}
        status={transcriptStatus}
      />

      <CallHistory attempts={callAttempts} />
    </main>
  )
}

export default App
