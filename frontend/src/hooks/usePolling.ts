import { useEffect, useRef, useCallback, useState } from 'react'

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
): { data: T | null; error: string | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const mounted = useRef(true)

  const tick = useCallback(async () => {
    try {
      const result = await fetcher()
      if (mounted.current) {
        setData(result)
        setError(null)
      }
    } catch (e) {
      if (mounted.current) {
        setError(e instanceof Error ? e.message : 'Unknown error')
      }
    } finally {
      if (mounted.current) {
        setLoading(false)
      }
    }
  }, [fetcher])

  useEffect(() => {
    mounted.current = true
    tick()
    const id = setInterval(tick, intervalMs)
    return () => {
      mounted.current = false
      clearInterval(id)
    }
  }, [tick, intervalMs])

  return { data, error, loading }
}
