import { useEffect, useState } from 'react'
import {
  createCall,
  fetchPatients,
  fetchCallRecords,
  type CallAttempt,
  type Patient,
} from './api'
import { CallHistory } from './components/CallHistory'
import { PatientTable } from './components/PatientTable'

function App() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null)
  const [callAttempts, setCallAttempts] = useState<CallAttempt[]>([])
  const [loadingPatients, setLoadingPatients] = useState(true)
  const [patientsError, setPatientsError] = useState<string | null>(null)
  const [startingCall, setStartingCall] = useState(false)

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
      await createCall(selectedPatient.id)
      setCallAttempts((current) =>
        current.map((attempt) =>
          attempt.id === attemptId
            ? { ...attempt, status: 'initiated', message: 'Call record created.' }
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

      <CallHistory attempts={callAttempts} />
    </main>
  )
}

export default App
