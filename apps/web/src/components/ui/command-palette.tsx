'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Command, Search, ArrowRight } from 'lucide-react';
import { useGlobalSearch } from '@/lib/keyboard';

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  href?: string;
  action?: () => void;
}

const DEFAULT_COMMANDS: CommandItem[] = [
  { id: 'go-dashboard', label: 'Go to Dashboard', href: '/dashboard' },
  { id: 'go-campaigns', label: 'Go to Campaigns', href: '/campaigns' },
  { id: 'go-content', label: 'Go to Content Studio', href: '/content' },
  { id: 'go-ai-content', label: 'AI Content Composer', href: '/ai-content' },
  { id: 'go-analytics', label: 'View Analytics', href: '/analytics' },
  { id: 'go-workflows', label: 'Manage Workflows', href: '/workflows' },
  { id: 'go-advertising', label: 'Ad Accounts', href: '/advertising' },
  { id: 'go-email', label: 'Email Campaigns', href: '/email/campaigns' },
  { id: 'go-reports', label: 'Reports', href: '/reports' },
  { id: 'go-team', label: 'Team Settings', href: '/team' },
  { id: 'go-settings', label: 'Settings', href: '/settings' },
  { id: 'go-monitoring', label: 'System Monitoring', href: '/monitoring' },
];

export function CommandPalette() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useGlobalSearch(() => setIsOpen((prev) => !prev));

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const filtered = query
    ? DEFAULT_COMMANDS.filter(
        (cmd) =>
          cmd.label.toLowerCase().includes(query.toLowerCase()) ||
          cmd.description?.toLowerCase().includes(query.toLowerCase()),
      )
    : DEFAULT_COMMANDS;

  const handleSelect = (cmd: CommandItem) => {
    setIsOpen(false);
    if (cmd.action) cmd.action();
    else if (cmd.href) router.push(cmd.href);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && filtered[selectedIndex]) {
      handleSelect(filtered[selectedIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      onClick={() => setIsOpen(false)}
    >
      <div
        className="w-full max-w-lg rounded-lg border bg-card shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b px-4 py-3">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search pages and commands..."
            aria-label="Search pages and commands"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <kbd className="rounded border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
            ESC
          </kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              onClick={() => handleSelect(cmd)}
              className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                i === selectedIndex ? 'bg-accent text-accent-foreground' : 'text-foreground hover:bg-accent/50'
              }`}
            >
              <Command className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="flex-1 text-left">{cmd.label}</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100" />
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="py-6 text-center text-sm text-muted-foreground">No results found</p>
          )}
        </div>
      </div>
    </div>
  );
}
