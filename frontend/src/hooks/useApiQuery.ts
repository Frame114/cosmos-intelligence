import { useCallback, useEffect, useState } from "react";
import { apiGet } from "../api/client";

export interface ResourceState<T> {
  data?: T;
  error?: Error;
  pending: boolean;
  updatedAt?: number;
  refresh: () => void;
}

interface StoredState<T> extends Omit<ResourceState<T>, "refresh"> {
  key: string | null;
}

export function useApiQuery<T>(path: string | null): ResourceState<T> {
  const [stored, setStored] = useState<StoredState<T>>({ key: path, pending: Boolean(path) });
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    if (!path) {
      setStored({ key: null, pending: false });
      return;
    }

    const controller = new AbortController();
    const isSameQuery = stored.key === path;
    setStored((current) => ({
      key: path,
      data: isSameQuery ? current.data : undefined,
      updatedAt: isSameQuery ? current.updatedAt : undefined,
      pending: true,
      error: undefined,
    }));

    void apiGet<T>(path, controller.signal)
      .then((data) => setStored({ key: path, data, pending: false, updatedAt: Date.now() }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setStored((current) => ({
          key: path,
          data: current.key === path ? current.data : undefined,
          updatedAt: current.key === path ? current.updatedAt : undefined,
          pending: false,
          error: error instanceof Error ? error : new Error("The request could not be completed."),
        }));
      });

    return () => controller.abort();
    // stored state is read intentionally only to preserve data for a same-query refresh.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, revision]);

  const refresh = useCallback(() => setRevision((value) => value + 1), []);
  const visible = stored.key === path ? stored : { key: path, pending: Boolean(path) };
  return { ...visible, refresh };
}
