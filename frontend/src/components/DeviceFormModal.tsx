import { useState } from 'react'
import { X } from 'lucide-react'
import type { Device } from '../lib/api'

interface DeviceFormModalProps {
  device?: Device | null
  onClose: () => void
  onSubmit: (data: { device_id: string; device_name: string; device_type: string; location: string }) => Promise<void>
}

export default function DeviceFormModal({ device, onClose, onSubmit }: DeviceFormModalProps) {
  const [deviceId, setDeviceId] = useState(device?.device_id || '')
  const [name, setName] = useState(device?.device_name || '')
  const [type, setType] = useState(device?.device_type || 'temperature_sensor')
  const [location, setLocation] = useState(device?.location || '')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await onSubmit({ device_id: deviceId, device_name: name, device_type: type, location })
      onClose()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-cardBg border border-borderBg rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">{device ? 'Edit Device' : 'Add Device'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Device ID</label>
            <input
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              disabled={!!device}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="temperature_sensor">Temperature Sensor</option>
              <option value="humidity_sensor">Humidity Sensor</option>
              <option value="multi_sensor">Multi Sensor</option>
              <option value="gateway">Gateway</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Location</label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div className="flex justify-end space-x-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : device ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
