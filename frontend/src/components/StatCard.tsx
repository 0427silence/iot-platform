import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: 'up' | 'down'
}

export default function StatCard({ title, value, subtitle, icon: Icon, trend }: StatCardProps) {
  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold mt-1 text-white">{value}</p>
          {subtitle && (
            <p className={`text-xs mt-1 ${
              trend === 'up' ? 'text-emerald-400' :
              trend === 'down' ? 'text-rose-400' :
              'text-gray-500'
            }`}>
              {subtitle}
            </p>
          )}
        </div>
        <div className="p-2 bg-blue-600/10 rounded-lg">
          <Icon className="w-5 h-5 text-blue-400" />
        </div>
      </div>
    </div>
  )
}
