'use client';

import { useState, useEffect } from 'react';

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

const SHORTCUTS: Shortcut[] = [
  { keys: ['Cmd', 'K'], description: 'Open command palette', category: 'Navigation' },
  { keys: ['Cmd', 'N'], description: 'Create new item', category: 'Navigation' },
  { keys: ['Cmd', '/'], description: 'Show keyboard shortcuts', category: 'Navigation' },
  { keys: ['Cmd', '.'], description: 'Toggle sidebar', category: 'Navigation' },
  { keys: ['Esc'], description: 'Close modal/palette', category: 'Navigation' },
  { keys: ['1-9'], description: 'Navigate to section', category: 'Navigation' },
  { keys: ['Cmd', 'S'], description: 'Save current form', category: 'Actions' },
  { keys: ['Cmd', 'Enter'], description: 'Submit form', category: 'Actions' },
  { keys: ['Cmd', 'Backspace'], description: 'Delete selected', category: 'Actions' },
  { keys: ['Cmd', 'E'], description: 'Edit current item', category: 'Actions' },
  { keys: ['Cmd', 'D'], description: 'Duplicate item', category: 'Actions' },
  { keys: ['?'], description: 'Show help', category: 'Help' },
];

interface KeyboardShortcutsModalProps {
  open: boolean;
  onClose: () => void;
}

export function KeyboardShortcutsModal({ open, onClose }: KeyboardShortcutsModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const categories = [...new Set(SHORTCUTS.map((s) => s.category))];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative z-50 w-full max-w-lg rounded-lg border bg-card p-6 shadow-xl">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Keyboard Shortcuts</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            &times;
          </button>
        </div>

        <div className="space-y-6">
          {categories.map((category) => (
            <div key={category}>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">
                {category}
              </h3>
              <div className="space-y-2">
                {SHORTCUTS.filter((s) => s.category === category).map((shortcut, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-muted"
                  >
                    <span className="text-sm">{shortcut.description}</span>
                    <div className="flex gap-1">
                      {shortcut.keys.map((key, j) => (
                        <span key={j}>
                          <kbd className="rounded border bg-muted px-1.5 py-0.5 text-xs font-medium">
                            {key}
                          </kbd>
                          {j < shortcut.keys.length - 1 && (
                            <span className="mx-0.5 text-muted-foreground">+</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          Press <kbd className="rounded border bg-muted px-1 py-0.5 text-xs">Esc</kbd> to
          close
        </div>
      </div>
    </div>
  );
}

export function useKeyboardShortcuts() {
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMeta = e.metaKey || e.ctrlKey;

      if (isMeta && e.key === '/') {
        e.preventDefault();
        setShortcutsOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return { shortcutsOpen, setShortcutsOpen };
}
