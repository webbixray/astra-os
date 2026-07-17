import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useNotificationStream } from './useNotificationStream';

const mockInvalidateQueries = vi.fn();

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }),
}));

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  localStorage.clear();
  vi.restoreAllMocks();
});

function createMockReader(results: Array<{ done: boolean; value?: Uint8Array }>) {
  let index = 0;
  return {
    read: vi.fn().mockImplementation(() => {
      if (index >= results.length) return Promise.resolve({ done: true, value: undefined });
      return Promise.resolve(results[index++]);
    }),
  };
}

describe('useNotificationStream', () => {
  it('does not connect when orgId is undefined', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    renderHook(() => useNotificationStream(undefined));
    act(() => { vi.advanceTimersByTime(200); });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('connects to SSE endpoint with correct headers', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 200 }),
    );
    renderHook(() => useNotificationStream('org-1'));
    act(() => { vi.advanceTimersByTime(200); });

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/notifications/stream?organization_id=org-1'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: 'text/event-stream',
        }),
        credentials: 'include',
      }),
    );
  });

  it('invalidates queries on SSE data event', async () => {
    createMockReader([
      { done: false, value: new TextEncoder().encode('data: {"type":"new_notification"}\n\n') },
      { done: true },
    ]);

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        new ReadableStream({
          start(controller) {
            controller.enqueue(new TextEncoder().encode('data: {"type":"new_notification"}\n\n'));
            controller.close();
          },
        }),
        { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
      ),
    );

    renderHook(() => useNotificationStream('org-1'));
    act(() => { vi.advanceTimersByTime(200); });

    // Wait for the async fetch to resolve and process
    await act(async () => {
      await Promise.resolve();
    });

    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['notifications'] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['notifications', 'unread-count'] });
  });

  it('cleans up on unmount', () => {
    const abortSpy = vi.fn();
    const OriginalAbortController = globalThis.AbortController;
    vi.spyOn(globalThis, 'AbortController').mockImplementation(() => ({
      abort: abortSpy,
      signal: new OriginalAbortController().signal,
    } as unknown as AbortController));

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 200 }),
    );

    const { unmount } = renderHook(() => useNotificationStream('org-1'));
    act(() => { vi.advanceTimersByTime(200); });
    unmount();

    expect(abortSpy).toHaveBeenCalled();
  });

  it('retries on connection failure with backoff', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network error'));

    renderHook(() => useNotificationStream('org-1'));
    await act(async () => { vi.advanceTimersByTime(200); });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    await act(async () => { vi.advanceTimersByTime(3000); });
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });
});
