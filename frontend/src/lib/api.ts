const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  const json: ApiResponse<T> = await res.json()
  if (json.code !== 0) {
    throw new Error(json.message)
  }
  return json.data
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

export interface Device {
  id: number
  device_id: string
  device_name: string
  device_type: string
  location: string | null
  status: number
  firmware_version: string | null
  last_online_at: string | null
  created_at: string
  updated_at: string
}

export interface DashboardSummary {
  total_devices: number
  online_count: number
  offline_count: number
  fault_count: number
  online_rate: number
  avg_temperature: number | null
  avg_humidity: number | null
  last_updated: string | null
}

export interface TrendPoint {
  device_id: string
  temperature: number | null
  humidity: number | null
  reported_at: string
}

export interface OnlineDevice {
  device_id: string
  device_name: string
  last_online_at: string | null
}

export interface AlarmEntry {
  device_id: string
  alarm_type: string
  message: string
  metric_value: number
  threshold_value: number
  triggered_at: string
}
