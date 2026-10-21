import { useCallback, useEffect, useState } from "react";

export const POLL_MS = 2000;

export interface Polled<T> {
  data: T | undefined;
  error: Error | undefined;
  refresh: () => void;
}

/** Load now and every two seconds, keeping the latest result or error. */
export function usePolling<T>(load: () => Promise<T>): Polled<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<Error>();
  const [requests, setRequests] = useState(0);
  const refresh = useCallback(() => {
    setRequests((count) => count + 1);
  }, []);

  useEffect(() => {
    let active = true;
    const fetchNow = () => {
      load().then(
        (value) => {
          if (!active) return;
          setData(value);
          setError(undefined);
        },
        (reason: unknown) => {
          if (active) setError(reason instanceof Error ? reason : new Error());
        },
      );
    };
    fetchNow();
    const timer = setInterval(fetchNow, POLL_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [load, requests]);

  return { data, error, refresh };
}
