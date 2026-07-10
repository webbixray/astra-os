import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
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

beforeEach(() => {
  localStorage.setItem('astra_access_token', 'test-token');
  localStorage.setItem('astra_orgs', JSON.stringify([{ id: 'org-1' }]));
});

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

import { useAIStream } from './useAIStream';

function createStreamResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  return new Response(
    new ReadableStream({
      async start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
          await new Promise((r) => setTimeout(r, 0));
        }
        controller.close();
      },
    }),
    { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
  );
}

describe('useAIStream', () => {
  it('starts with a welcome message', () => {
    const { result } = renderHook(() => useAIStream());
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe('assistant');
    expect(result.current.messages[0].content).toContain('Hello');
    expect(result.current.isStreaming).toBe(false);
  });

  it('adds user message and assistant placeholder on send', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(createStreamResponse(['data: [DONE]\n\n']));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Create a campaign');
    });

    expect(result.current.messages).toHaveLength(3); // welcome + user + assistant
    expect(result.current.messages[1].role).toBe('user');
    expect(result.current.messages[1].content).toBe('Create a campaign');
    expect(result.current.messages[2].role).toBe('assistant');
  });

  it('streams content from the API', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      createStreamResponse([
        'data: Hello\n',
        'data:  world\n',
        'data: [DONE]\n\n',
      ]),
    );

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Say hello');
    });

    const assistantMsg = result.current.messages[2];
    expect(assistantMsg.role).toBe('assistant');
    expect(assistantMsg.content).toContain('Hello');
    expect(assistantMsg.content).toContain('world');
  });

  it('sets streaming state correctly', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(createStreamResponse(['data: [DONE]\n\n']));

    const { result } = renderHook(() => useAIStream());

    const sendPromise = result.current.sendMessage('Test');
    expect(result.current.isStreaming).toBe(true);

    await act(async () => {
      await sendPromise;
    });

    expect(result.current.isStreaming).toBe(false);
  });

  it('shows error message on fetch failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Trigger error');
    });

    const assistantMsg = result.current.messages[2];
    expect(assistantMsg.content).toBe('Sorry, I encountered an error. Please try again.');
  });

  it('stops streaming on abort', async () => {
    const abortSpy = vi.fn();
    vi.spyOn(globalThis, 'AbortController').mockImplementation(() => ({
      abort: abortSpy,
      signal: new AbortController().signal,
    } as unknown as AbortController));

    vi.spyOn(globalThis, 'fetch').mockImplementation(
      () => new Promise(() => {}), // never resolves
    );

    const { result } = renderHook(() => useAIStream());

    result.current.sendMessage('Test');
    act(() => {
      result.current.stopStreaming();
    });

    expect(abortSpy).toHaveBeenCalled();
    expect(result.current.isStreaming).toBe(false);
  });

  it('sends request with correct payload', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      createStreamResponse(['data: [DONE]\n\n']),
    );

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Optimize budget');
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/chat/stream'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token',
        }),
        body: expect.stringContaining('"message":"Optimize budget"'),
      }),
    );
  });

  it('includes page context in request', async () => {
    mockPathname.mockReturnValue('/campaigns/camp-123');
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      createStreamResponse(['data: [DONE]\n\n']),
    );

    const { result } = renderHook(() => useAIStream());

    await act(async () => {
      await result.current.sendMessage('Analyze campaign');
    });

    const body = JSON.parse((fetchSpy.mock.calls[0][1] as RequestInit).body as string);
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
