export default function LoadingSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass-card rounded-xl p-5 animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/2 mb-3" />
          <div className="h-8 bg-gray-700 rounded w-1/3" />
        </div>
      ))}
    </div>
  )
}
