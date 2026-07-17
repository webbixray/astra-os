import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

if (!globalThis.crypto?.randomUUID) {
  Object.defineProperty(globalThis, 'crypto', {
    value: { randomUUID: () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16); }) },
    writable: true,
  });
}

const mockPathname = vi.fn().mockReturnValue('/campaigns');
vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname(),
}));

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  localStorage.setItem('astra_orgs', JSON.stringify([{ id: 'org-1' }]));
  mockFetch.mockReset();
});

import { useAIStream } from './useAIStream';

function mockStreamResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  const encodedChunks = chunks.map((c) => encoder.encode(c));

  return {
    ok: true,
    status: 200,
    headers: new Headers({ 'Content-Type': 'text/event-stream' }),
    body: {
      getReader() {
        let idx = 0;
        return {
          read: vi.fn().mockImplementation(async () => {
            if (idx >= encodedChunks.length) return { done: true, value: undefined };
            return { done: false, value: encodedChunks[idx++] };
          }),
          releaseLock: vi.fn(),
          cancel: vi.fn(),
        };
      },
    },
  } as unknown as Response;
}

describe('useAIStream', () => {
  it('starts with a welcome message', () => {
    const { result } = renderHook(() => useAIStream());
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0]!.role).toBe('assistant');
    expect(result.current.messages[0]!.content).toContain('Hello');
    expect(result.current.isStreaming).toBe(false);
  });

  it('adds user message and assistant placeholder on send', async () => {
    mockFetch.mockResolvedValue(mockStreamResponse(['data: [DONE]\n\n']));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Create a campaign');
    });

    expect(result.current.messages).toHaveLength(3);
    expect(result.current.messages[1]!.role).toBe('user');
    expect(result.current.messages[1]!.content).toBe('Create a campaign');
    expect(result.current.messages[2]!.role).toBe('assistant');
  });

  it('streams content from the API', async () => {
    mockFetch.mockResolvedValue(mockStreamResponse([
      'data: Hello\n',
      'data:  world\n',
      'data: [DONE]\n\n',
    ]));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Say hello');
    });

    const assistantMsg = result.current.messages[2]!;
    expect(assistantMsg.role).toBe('assistant');
    expect(assistantMsg.content).toContain('Hello');
    expect(assistantMsg.content).toContain('world');
  });

  it('sets streaming state correctly', async () => {
    mockFetch.mockResolvedValue(mockStreamResponse(['data: [DONE]\n\n']));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Test');
    });

    expect(result.current.isStreaming).toBe(false);
  });

  it('shows error message on fetch failure', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Trigger error');
    });

    const assistantMsg = result.current.messages[2]!;
    expect(assistantMsg.content).toBe('Sorry, I encountered an error. Please try again.');
  });

  it('stops streaming on abort', async () => {
    const abortSpy = vi.fn();
    vi.stubGlobal('AbortController', class {
      signal = { aborted: false, addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(), onabort: null, reason: '', throwIfAborted: vi.fn() } as unknown as AbortSignal;
      abort(why?: unknown) { abortSpy(why); }
    });

    mockFetch.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useAIStream());

    act(() => {
      result.current.sendMessage('Test');
    });

    act(() => {
      result.current.stopStreaming();
    });

    expect(abortSpy).toHaveBeenCalled();
    expect(result.current.isStreaming).toBe(false);
  });

  it('sends request with correct payload', async () => {
    mockFetch.mockResolvedValue(mockStreamResponse(['data: [DONE]\n\n']));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Optimize budget');
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/stream'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
        body: expect.stringContaining('"message":"Optimize budget"'),
      }),
    );
  });

  it('includes page context in request', async () => {
    mockPathname.mockReturnValue('/campaigns/camp-123');
    mockFetch.mockResolvedValue(mockStreamResponse(['data: [DONE]\n\n']));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Analyze campaign');
    });

    const body = JSON.parse((mockFetch.mock.calls[0]![1] as RequestInit).body as string);
    expect(body.page_context).toEqual({ page: '/campaigns/camp-123', campaign: 'camp-123' });
  });

  it('allows setting messages externally', () => {
    const { result } = renderHook(() => useAIStream());

    act(() => {
      result.current.setMessages([]);
    });

    expect(result.current.messages).toEqual([]);
  });
});
