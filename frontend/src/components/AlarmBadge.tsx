import { Bell } from 'lucide-react'

interface AlarmBadgeProps {
  count: number
  onClick: () => void
}

export default function AlarmBadge({ count, onClick }: AlarmBadgeProps) {
  if (count === 0) return null

  return (
    <button
      onClick={onClick}
      className="relative flex items-center space-x-2 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-full text-rose-400 text-xs cursor-pointer"
    >
      <span className="absolute -top-0.5 -right-0.5 flex h-3 w-3">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
        <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500" />
      </span>
      <Bell className="w-3.5 h-3.5" />
      <span>{count} alarm{count > 1 ? 's' : ''}</span>
    </button>
  )
}
