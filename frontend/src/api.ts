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

export type Call = {
  id: string
  patient_id: string
  call_date: string
  call_time: string
  call_duration: number
  call_type: string
  call_status: string
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

export async function createCall(patientId: string): Promise<Call> {
  const now = new Date()
  const body = {
    id: `call_${crypto.randomUUID()}`,
    patient_id: patientId,
    call_date: now.toISOString().slice(0, 10),
    call_time: now.toTimeString().slice(0, 8),
    call_duration: 0,
    call_type: 'appointment_reminder',
    call_status: 'initiated',
  }

  const response = await fetch(`${API_BASE}/calls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  return response.json() as Promise<Call>
}
