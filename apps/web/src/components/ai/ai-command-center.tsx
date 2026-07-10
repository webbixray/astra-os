'use client';

import { useState, useRef, useEffect } from 'react';
import { Command, Send, Sparkles, StopCircle, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAIStream } from '@/hooks/useAIStream';

const SLASH_SUGGESTIONS = [
  { command: '/campaign', description: 'Manage campaigns' },
  { command: '/content', description: 'Create or search content' },
  { command: '/analytics', description: 'View performance metrics' },
  { command: '/help', description: 'List all commands' },
];

export function AICommandCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const { messages, sendMessage, stopStreaming, isStreaming } = useAIStream();
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    setShowSuggestions(false);
    const msg = input;
    setInput('');
    await sendMessage(msg);
  };

  const handleInputChange = (value: string) => {
    setInput(value);
    setShowSuggestions(value.startsWith('/'));
  };

  const selectSuggestion = (cmd: string) => {
    setInput(cmd + ' ');
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105"
          aria-label="Open AI Command Center"
        >
          <Sparkles className="h-5 w-5" />
        </button>
      )}

      <div
        className={cn(
          'fixed bottom-6 right-6 z-50 flex w-96 flex-col rounded-xl border bg-card shadow-2xl transition-all duration-200',
          isOpen ? 'h-[600px] opacity-100' : 'h-0 opacity-0 pointer-events-none',
        )}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <Command className="h-4 w-4" />
            <span className="text-sm font-medium">ASTRA AI</span>
            {isStreaming && (
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            )}
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="rounded-md p-1 hover:bg-accent"
            aria-label="Close"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex gap-3',
                message.role === 'user' ? 'justify-end' : 'justify-start',
              )}
            >
              <div
                className={cn(
                  'max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground',
                )}
              >
                {message.content || (isStreaming ? <span className="animate-pulse">...</span> : null)}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="border-t p-4 relative">
          {showSuggestions && (
            <div className="absolute bottom-full left-4 right-4 mb-2 rounded-lg border bg-popover p-2 shadow-lg">
              {SLASH_SUGGESTIONS.map((s) => (
                <button
                  key={s.command}
                  type="button"
                  onClick={() => selectSuggestion(s.command)}
                  className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-accent"
                >
                  <span className="font-medium text-primary">{s.command}</span>
                  <span className="text-muted-foreground">{s.description}</span>
                </button>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') setShowSuggestions(false);
              }}
              placeholder="Ask anything... (type / for commands)"
              aria-label="Ask AI anything"
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="flex h-9 w-9 items-center justify-center rounded-md bg-destructive text-destructive-foreground"
                aria-label="Stop"
              >
                <StopCircle className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground disabled:opacity-50"
                aria-label="Send"
              >
                <Send className="h-4 w-4" />
              </button>
            )}
          </div>
        </form>
      </div>
    </>
  );
}
