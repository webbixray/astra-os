'use client';

import { useState, useCallback, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { API_BASE_URL } from '@/lib/constants';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface PageContext {
  page: string;
  campaign?: string;
  content?: string;
}

function getPageContext(pathname: string): PageContext {
  const ctx: PageContext = { page: pathname };
  if (pathname.startsWith('/campaigns/') && pathname !== '/campaigns/new') {
    ctx.campaign = pathname.split('/')[2];
  }
  if (pathname.startsWith('/content/') && pathname !== '/content/new') {
    ctx.content = pathname.split('/')[2];
  }
  return ctx;
}

export function useAIStream() {
  const pathname = usePathname();
  const messagesRef = useRef<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm ASTRA, your AI marketing department. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [messages, setMessages] = useState<Message[]>(messagesRef.current);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    messagesRef.current = [...messagesRef.current, userMsg];
    setMessages(messagesRef.current);

    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    messagesRef.current = [...messagesRef.current, assistantMsg];
    setMessages(messagesRef.current);
    setIsStreaming(true);

    const abortController = new AbortController();
    abortRef.current = abortController;

    let orgId = '00000000-0000-0000-0000-000000000000';
    if (typeof window !== 'undefined') {
      try {
        const stored = JSON.parse(localStorage.getItem('astra_orgs') || '[]');
        orgId = (stored?.[0]?.id) || orgId;
      } catch {
        // localStorage corrupted, use fallback
      }
    }
    const prevMessages = messagesRef.current
      .filter((m) => m.id !== 'welcome' && m.id !== assistantId)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          organization_id: orgId,
          message: content,
          page_context: getPageContext(pathname),
          messages: prevMessages,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) throw new Error('Stream failed');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            messagesRef.current = messagesRef.current.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + data } : m,
            );
            setMessages(messagesRef.current);
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        setIsStreaming(false);
        return;
      }
      messagesRef.current = messagesRef.current.map((m) =>
        m.id === assistantId
          ? { ...m, content: 'Sorry, I encountered an error. Please try again.' }
          : m,
      );
      setMessages(messagesRef.current);
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [pathname]);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return {
    messages,
    sendMessage,
    stopStreaming,
    isStreaming,
    setMessages,
  };
}
