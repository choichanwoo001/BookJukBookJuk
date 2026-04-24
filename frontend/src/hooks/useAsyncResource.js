import { useEffect, useState } from 'react'

export function useAsyncResource({
  enabled = true,
  initialData,
  load,
  deps = [],
  resetOnDisable = true,
}) {
  const [data, setData] = useState(initialData)
  const [isLoading, setIsLoading] = useState(Boolean(enabled))
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    if (!enabled) {
      if (resetOnDisable) setData(initialData)
      setIsLoading(false)
      setError(null)
      return undefined
    }

    setIsLoading(true)
    setError(null)
    Promise.resolve()
      .then(() => load())
      .then((result) => {
        if (cancelled) return
        setData(result)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err)
        if (resetOnDisable) setData(initialData)
      })
      .finally(() => {
        if (cancelled) return
        setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [enabled, resetOnDisable, ...deps])

  return { data, setData, isLoading, error }
}
