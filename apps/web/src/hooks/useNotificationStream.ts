'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { API_BASE_URL } from '@/lib/constants';

const RECONNECT_BASE_MS = 2000;
const RECONNECT_MAX_MS = 30000;
const MAX_RETRIES = 10;

export function useNotificationStream(orgId: string | undefined) {
  const qc = useQueryClient();
  const controllerRef = useRef<AbortController | null>(null);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryDelayRef = useRef(RECONNECT_BASE_MS);
  const retryCountRef = useRef(0);
  const mountedRef = useRef(true);

  const invalidate = useCallback(() => {
    qc.invalidateQueries({ queryKey: ['notifications'] });
    qc.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
  }, [qc]);

  const connect = useCallback(() => {
    if (!orgId || !mountedRef.current) return;

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    fetch(`${API_BASE_URL}/notifications/stream?organization_id=${orgId}`, {
      headers: {
        Accept: 'text/event-stream',
      },
      credentials: 'include',
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok || !response.body) {
          throw new Error(`SSE connection failed: ${response.status}`);
        }

        retryDelayRef.current = RECONNECT_BASE_MS;
        retryCountRef.current = 0;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (mountedRef.current) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const raw = line.slice(6).trim();
              if (!raw || raw === '[DONE]') continue;
              try {
                const event = JSON.parse(raw);
                const eventType = event.type || event.event;
                if (eventType === 'notification' || eventType === 'notification.created') {
                  qc.invalidateQueries({ queryKey: ['notifications'] });
                  qc.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
                } else if (eventType === 'unread_count') {
                  qc.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
                } else {
                  invalidate();
                }
              } catch {
                invalidate();
              }
            }
          }
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        if (!mountedRef.current) return;
        if (retryCountRef.current >= MAX_RETRIES) return;

        retryCountRef.current += 1;
        retryTimeoutRef.current = setTimeout(() => {
          retryDelayRef.current = Math.min(retryDelayRef.current * 1.5, RECONNECT_MAX_MS);
          connect();
        }, retryDelayRef.current);
      });
  }, [orgId, invalidate]);

  useEffect(() => {
    mountedRef.current = true;

    const delay = setTimeout(() => {
      connect();
    }, 100);

    return () => {
      mountedRef.current = false;
      controllerRef.current?.abort();
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      clearTimeout(delay);
    };
  }, [connect]);
}
