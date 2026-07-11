import { useCallback, useEffect, useRef, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

export function useDebouncedCallback<T extends (...args: unknown[]) => unknown>(
  callback: T,
  delay: number,
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  return useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => callback(...args), delay);
    },
    [callback, delay],
  );
}

export function useIntersectionObserver(
  callback: IntersectionObserverCallback,
  options?: IntersectionObserverInit,
): [React.RefObject<HTMLDivElement | null>] {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(callback, options);
    observer.observe(element);

    return () => observer.disconnect();
  }, [callback, options]);

  return [ref];
}

export function useVirtualization<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan: number = 5,
  scrollRef?: React.RefObject<HTMLDivElement | null>,
): { visibleItems: T[]; totalHeight: number; offsetY: number; onScroll: (e: React.UIEvent<HTMLDivElement>) => void } {
  const [scrollTop, setScrollTop] = useState(0);

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan,
  );

  const onScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems: items.slice(startIndex, endIndex),
    totalHeight: items.length * itemHeight,
    offsetY: startIndex * itemHeight,
    onScroll,
  };
}

export function useLazyLoad<T>(
  fetchFn: () => Promise<T>,
  options?: { threshold?: number; rootMargin?: string },
): { ref: React.RefObject<HTMLDivElement | null>; data: T | null; loading: boolean; error: Error | null } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [ref, setRef] = useState<HTMLDivElement | null>(null);
  const hasLoaded = useRef(false);
  const fetchFnRef = useRef(fetchFn);
  fetchFnRef.current = fetchFn;

  useEffect(() => {
    if (!ref || hasLoaded.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && !hasLoaded.current) {
          hasLoaded.current = true;
          setLoading(true);
          fetchFnRef.current()
            .then(setData)
            .catch(setError)
            .finally(() => setLoading(false));
        }
      },
      { threshold: options?.threshold ?? 0, rootMargin: options?.rootMargin ?? '100px' },
    );

    observer.observe(ref);
    return () => observer.disconnect();
  }, [ref, fetchFn, options?.threshold, options?.rootMargin]);

  return { ref: { current: ref } as React.RefObject<HTMLDivElement | null>, data, loading, error };
}

export function useImagePreloader(urls: string[]): { loaded: boolean; progress: number } {
  const [loaded, setLoaded] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (urls.length === 0) {
      setLoaded(true);
      setProgress(1);
      return;
    }

    let loadedCount = 0;
    const total = urls.length;

    urls.forEach((url) => {
      const img = new Image();
      img.onload = img.onerror = () => {
        loadedCount++;
        setProgress(loadedCount / total);
        if (loadedCount === total) {
          setLoaded(true);
        }
      };
      img.src = url;
    });
  }, [urls]);

  return { loaded, progress };
}
