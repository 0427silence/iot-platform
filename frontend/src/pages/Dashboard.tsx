import { useCallback, useState } from 'react'
import { Wifi, WifiOff, AlertTriangle, Activity } from 'lucide-react'
import { api, type DashboardSummary, type TrendPoint, type OnlineDevice, type AlarmEntry } from '../lib/api'
import { usePolling } from '../hooks/usePolling'
import StatCard from '../components/StatCard'
import TrendChart from '../components/TrendChart'
import LoadingSkeleton from '../components/LoadingSkeleton'
import AlarmBadge from '../components/AlarmBadge'

export default function Dashboard() {
  const [showAlarms, setShowAlarms] = useState(false)

  const fetchSummary = useCallback(() => api.get<DashboardSummary>('/dashboard/summary'), [])
  const fetchTrend = useCallback(() => api.get<TrendPoint[]>('/dashboard/trend?limit=30'), [])
  const fetchOnline = useCallback(() => api.get<OnlineDevice[]>('/dashboard/devices/online'), [])
  const fetchAlarms = useCallback(() => api.get<AlarmEntry[]>('/alarms/active'), [])

  const summary = usePolling(fetchSummary, 5000)
  const trend = usePolling(fetchTrend, 5000)
  const online = usePolling(fetchOnline, 5000)
  const alarms = usePolling(fetchAlarms, 10000)

  if (summary.loading) {
    return <LoadingSkeleton />
  }

  const s = summary.data
  const activeAlarms = alarms.data || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Dashboard</h2>
        <AlarmBadge count={activeAlarms.length} onClick={() => setShowAlarms(!showAlarms)} />
      </div>

      {showAlarms && activeAlarms.length > 0 && (
        <div className="glass-card rounded-xl p-4 border-rose-500/30">
          <h3 className="text-sm font-semibold text-rose-400 mb-3">Active Alarms</h3>
          <div className="space-y-2">
            {activeAlarms.map((a, i) => (
              <div key={i} className="flex items-center justify-between text-sm bg-rose-500/5 rounded-lg p-3">
                <span className="text-gray-300">{a.message}</span>
                <span className="text-gray-500 text-xs">
                  {new Date(a.triggered_at).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Devices" value={s?.total_devices ?? 0} icon={Activity} />
        <StatCard title="Online" value={s?.online_count ?? 0} icon={Wifi} trend="up" />
        <StatCard title="Offline" value={s?.offline_count ?? 0} icon={WifiOff} trend="down" />
        <StatCard title="Alerts" value={activeAlarms.length} icon={AlertTriangle} trend={activeAlarms.length > 0 ? 'down' : undefined} />
      </div>

      <TrendChart data={trend.data || []} />

      <div className="glass-card rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-400 mb-4">Online Devices</h3>
        {online.data && online.data.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b border-borderBg">
                <th className="text-left py-2">Device</th>
                <th className="text-left py-2">Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {online.data.map((d) => (
                <tr key={d.device_id} className="border-b border-borderBg/50">
                  <td className="py-2 text-white">{d.device_name}</td>
                  <td className="py-2 text-gray-400">
                    {d.last_online_at ? new Date(d.last_online_at).toLocaleTimeString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-500 text-center py-4">No devices online — start the simulator</p>
        )}
      </div>

      {summary.error && (
        <div className="glass-card rounded-xl p-4 border-rose-500/30 text-rose-400 text-sm">
          Backend error: {summary.error}. Make sure the API server is running on port 8000.
        </div>
      )}
    </div>
  )
}
