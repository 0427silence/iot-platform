import { useCallback, useState } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { api, type Device } from '../lib/api'
import { usePolling } from '../hooks/usePolling'
import DeviceFormModal from '../components/DeviceFormModal'
import LoadingSkeleton from '../components/LoadingSkeleton'

export default function Devices() {
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Device | null>(null)
  const [search, setSearch] = useState('')

  const fetchDevices = useCallback(() => api.get<Device[]>('/devices'), [])
  const { data: devices, error, loading } = usePolling(fetchDevices, 5000)

  const handleCreate = async (payload: { device_id: string; device_name: string; device_type: string; location: string }) => {
    await api.post('/devices', payload)
  }

  const handleUpdate = async (payload: { device_id: string; device_name: string; device_type: string; location: string }) => {
    if (!editing) return
    await api.put(`/devices/${editing.device_id}`, {
      device_name: payload.device_name,
      device_type: payload.device_type,
      location: payload.location,
    })
  }

  const handleDelete = async (deviceId: string) => {
    if (!confirm(`Delete device ${deviceId}?`)) return
    await api.del(`/devices/${deviceId}`)
  }

  const filtered = (devices || []).filter(
    (d) =>
      d.device_name.toLowerCase().includes(search.toLowerCase()) ||
      d.device_id.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) return <LoadingSkeleton />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Devices</h2>
        <button
          onClick={() => { setEditing(null); setShowModal(true) }}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          <span>Add Device</span>
        </button>
      </div>

      <input
        type="text"
        placeholder="Search devices..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-sm bg-cardBg border border-borderBg rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
      />

      <div className="glass-card rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-borderBg">
              <th className="text-left py-3 px-4">Name</th>
              <th className="text-left py-3 px-4">ID</th>
              <th className="text-left py-3 px-4">Type</th>
              <th className="text-left py-3 px-4">Status</th>
              <th className="text-left py-3 px-4">Location</th>
              <th className="text-right py-3 px-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr key={d.id} className="border-b border-borderBg/50 hover:bg-white/5">
                <td className="py-3 px-4 text-white">{d.device_name}</td>
                <td className="py-3 px-4 text-gray-400 font-mono text-xs">{d.device_id}</td>
                <td className="py-3 px-4 text-gray-400">{d.device_type}</td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                    d.status === 1 ? 'bg-emerald-500/10 text-emerald-400' :
                    d.status === 2 ? 'bg-rose-500/10 text-rose-400' :
                    'bg-gray-500/10 text-gray-400'
                  }`}>
                    {d.status === 1 ? 'Online' : d.status === 2 ? 'Fault' : 'Offline'}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-500">{d.location || '—'}</td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => { setEditing(d); setShowModal(true) }}
                    className="p-1.5 text-gray-400 hover:text-white mr-1"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(d.device_id)}
                    className="p-1.5 text-gray-400 hover:text-rose-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-500">
                  No devices found. Add one or start the simulator.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <DeviceFormModal
          device={editing}
          onClose={() => setShowModal(false)}
          onSubmit={editing ? handleUpdate : handleCreate}
        />
      )}

      {error && (
        <div className="glass-card rounded-xl p-4 border-rose-500/30 text-rose-400 text-sm">
          Error: {error}
        </div>
      )}
    </div>
  )
}
