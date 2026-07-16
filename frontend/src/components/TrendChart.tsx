import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import type { TrendPoint } from '../lib/api'

interface TrendChartProps {
  data: TrendPoint[]
}

export default function TrendChart({ data }: TrendChartProps) {
  if (data.length === 0) {
    return (
      <div className="glass-card rounded-xl p-6 text-center text-gray-500">
        No trend data yet — start the simulator to see charts
      </div>
    )
  }

  const chartData = data.map((d) => ({
    time: new Date(d.reported_at).toLocaleTimeString(),
    temperature: d.temperature,
    humidity: d.humidity,
  }))

  return (
    <div className="glass-card rounded-xl p-6">
      <h3 className="text-sm font-semibold text-gray-400 mb-4">Temperature & Humidity (24h)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#232d3f" />
          <XAxis dataKey="time" stroke="#4b5563" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="temp" stroke="#60a5fa" tick={{ fontSize: 12 }} unit="°C" />
          <YAxis yAxisId="humid" orientation="right" stroke="#34d399" tick={{ fontSize: 12 }} unit="%" />
          <Tooltip
            contentStyle={{ background: '#161b26', border: '1px solid #232d3f', borderRadius: '8px' }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <Legend />
          <Line yAxisId="temp" type="monotone" dataKey="temperature" stroke="#60a5fa" dot={false} name="Temperature °C" />
          <Line yAxisId="humid" type="monotone" dataKey="humidity" stroke="#34d399" dot={false} name="Humidity %" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
