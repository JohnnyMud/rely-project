import type { Patient } from '../api'

type PatientRowProps = {
  patient: Patient
  selected: boolean
  onSelect: (patientId: string) => void
}

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatTime(value: string): string {
  const [hours, minutes] = value.split(':')
  const date = new Date()
  date.setHours(Number(hours), Number(minutes), 0, 0)
  return date.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function PatientRow({ patient, selected, onSelect }: PatientRowProps) {
  return (
    <tr
      className={selected ? 'patient-row selected' : 'patient-row'}
      onClick={() => onSelect(patient.id)}
    >
      <td>
        <input
          type="radio"
          name="selected-patient"
          checked={selected}
          onChange={() => onSelect(patient.id)}
          aria-label={`Select ${patient.first_name} ${patient.last_name}`}
        />
      </td>
      <td>
        <div className="patient-name">
          {patient.first_name} {patient.last_name}
        </div>
        <div className="patient-meta">{patient.medical_record_number}</div>
      </td>
      <td>{patient.phone_number}</td>
      <td>
        <div>{formatDate(patient.appointment_date)}</div>
        <div className="patient-meta">
          {formatTime(patient.appointment_time)} ({patient.timezone})
        </div>
      </td>
    </tr>
  )
}
