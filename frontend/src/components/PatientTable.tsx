import type { Patient } from '../api'
import { PatientRow } from './PatientRow'

type PatientTableProps = {
  patients: Patient[]
  selectedPatientId: string | null
  onSelectPatient: (patientId: string) => void
  loading: boolean
  error: string | null
}

export function PatientTable({
  patients,
  selectedPatientId,
  onSelectPatient,
  loading,
  error,
}: PatientTableProps) {
  if (loading) {
    return <p className="status-message">Loading patients...</p>
  }

  if (error) {
    return <p className="status-message error">{error}</p>
  }

  if (patients.length === 0) {
    return <p className="status-message">No patients found.</p>
  }

  return (
    <div className="table-wrap">
      <table className="patient-table">
        <thead>
          <tr>
            <th scope="col">Select</th>
            <th scope="col">Patient</th>
            <th scope="col">Phone</th>
            <th scope="col">Appointment</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((patient) => (
            <PatientRow
              key={patient.id}
              patient={patient}
              selected={patient.id === selectedPatientId}
              onSelect={onSelectPatient}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
