export interface CacheOptions {
  ttl?: number;
  maxEntries?: number;
  staleWhileRevalidate?: boolean;
  keyPrefix?: string;
}

interface CacheEntry<T> {
  value: T;
  timestamp: number;
  expiresAt?: number;
}

export class MemoryCache<T = unknown> {
  private cache = new Map<string, CacheEntry<T>>();
  private ttl: number;
  private maxEntries: number;
  private keyPrefix: string;

  constructor(options: CacheOptions = {}) {
    this.ttl = options.ttl ?? 5 * 60 * 1000;
    this.maxEntries = options.maxEntries ?? 100;
    this.keyPrefix = options.keyPrefix ?? 'cache';
  }

  private getKey(key: string): string {
    return `${this.keyPrefix}:${key}`;
  }

  get(key: string): T | null {
    const entry = this.cache.get(this.getKey(key));
    if (!entry) return null;

    if (entry.expiresAt && Date.now() > entry.expiresAt) {
      this.cache.delete(this.getKey(key));
      return null;
    }

    return entry.value;
  }

  set(key: string, value: T, ttl?: number): void {
    if (this.cache.size >= this.maxEntries) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    const entry: CacheEntry<T> = {
      value,
      timestamp: Date.now(),
      expiresAt: ttl ? Date.now() + ttl : this.ttl ? Date.now() + this.ttl : undefined,
    };

    this.cache.set(this.getKey(key), entry);
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  delete(key: string): boolean {
    return this.cache.delete(this.getKey(key));
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }

  keys(): string[] {
    return Array.from(this.cache.keys()).map((k) => k.replace(`${this.keyPrefix}:`, ''));
  }

  getOrSet(key: string, factory: () => T | Promise<T>, ttl?: number): T | Promise<T> {
    const cached = this.get(key);
    if (cached !== null) return cached;

    const value = factory();
    if (value instanceof Promise) {
      return value.then((v) => {
        this.set(key, v, ttl);
        return v;
      });
    }

    this.set(key, value, ttl);
    return value;
  }
}

export class StorageCache<T = unknown> implements Cache<T> {
  private cache: MemoryCache<T>;
  private storageKey: string;

  constructor(options: CacheOptions = {}) {
    this.cache = new MemoryCache(options);
    this.storageKey = options.keyPrefix ?? 'astra-cache';
  }

  get(key: string): T | null {
    const memCached = this.cache.get(key);
    if (memCached !== null) return memCached;

    try {
      if (typeof window === 'undefined') return null;
      const stored = localStorage.getItem(`${this.storageKey}:${key}`);
      if (!stored) return null;

      const entry: CacheEntry<T> = JSON.parse(stored);
      if (entry.expiresAt && Date.now() > entry.expiresAt) {
        localStorage.removeItem(`${this.storageKey}:${key}`);
        return null;
      }

      this.cache.set(key, entry.value);
      return entry.value;
    } catch {
      return null;
    }
  }

  set(key: string, value: T, ttl?: number): void {
    this.cache.set(key, value, ttl);

    try {
      if (typeof window === 'undefined') return;
      const entry: CacheEntry<T> = {
        value,
        timestamp: Date.now(),
        expiresAt: ttl ? Date.now() + ttl : undefined,
      };
      localStorage.setItem(`${this.storageKey}:${key}`, JSON.stringify(entry));
    } catch {
      // Storage full or not available
    }
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  delete(key: string): boolean {
    this.cache.delete(key);
    try {
      if (typeof window === 'undefined') return false;
      localStorage.removeItem(`${this.storageKey}:${key}`);
      return true;
    } catch {
      return false;
    }
  }

  clear(): void {
    this.cache.clear();
    try {
      if (typeof window === 'undefined') return;
      const keys = Object.keys(localStorage).filter((k) => k.startsWith(`${this.storageKey}:`));
      keys.forEach((k) => localStorage.removeItem(k));
    } catch {
      // Ignore
    }
  }
}

export const apiCache = new MemoryCache({ ttl: 60 * 1000, maxEntries: 200 });
export const uiCache = new MemoryCache({ ttl: 5 * 60 * 1000, maxEntries: 50 });

export function cached<T>(
  cache: MemoryCache<T>,
  key: string,
  factory: () => T | Promise<T>,
  ttl?: number,
): T | Promise<T> {
  return cache.getOrSet(key, factory, ttl);
}
