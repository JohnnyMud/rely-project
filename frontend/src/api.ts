const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export type Patient = {
  id: string
  first_name: string
  last_name: string
  date_of_birth: string
  phone_number: string
  home_address: string
  insurance_number: string
  medical_record_number: string
  appointment_date: string
  appointment_time: string
  timezone: string
}

export type CallRecord = {
  call_attempt_id: string
  patient_id: string
  retell_call_id: string | null
  created_at: string
  started_at: string | null
  ended_at: string | null
  call_duration: number | null
  call_status: string
  successful: boolean | null
  recording_url: string | null
  summary: string | null
}

export type CallAttemptStatus = 'pending' | 'success' | 'failed'

export type CallAttempt = {
  id: string
  patientId: string
  patientName: string
  startedAt: string
  status: CallAttemptStatus
  message?: string
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string | { msg: string }[] }
    if (typeof data.detail === 'string') {
      return data.detail
    }
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      return data.detail[0]?.msg ?? response.statusText
    }
  } catch {
    // Fall through to status text.
  }

  return response.statusText || 'Request failed'
}

export async function fetchPatients(): Promise<Patient[]> {
  const response = await fetch(`${API_BASE}/patients`)

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return response.json() as Promise<Patient[]>
}

export async function fetchCallRecords(patientId: string): Promise<CallRecord[]> {
  const response = await fetch(`${API_BASE}/patients/${patientId}/calls`)
  if (!response.ok) {
    throw new Error(await parseError(response))
  }
  return response.json() as Promise<CallRecord[]>
}

export async function createCall(patientId: string): Promise<CallRecord> {
  const response = await fetch(`${API_BASE}/patients/${patientId}/calls`, {
    method: 'POST',
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return response.json() as Promise<CallRecord>
}
