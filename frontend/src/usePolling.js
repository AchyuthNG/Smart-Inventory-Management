import { useEffect, useRef, useState, useCallback } from "react";

/**
 * usePolling — re-fetch `fn` every `interval` ms.
 * Accepts an optional `refetchKey` to manually trigger an immediate refetch.
 */
export function usePolling(fn, interval = 7000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const refetch = useCallback(async () => {
    try {
      const result = await fnRef.current();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
    const id = setInterval(refetch, interval);
    return () => clearInterval(id);
  }, [refetch, interval]);

  return { data, error, loading, refetch };
}