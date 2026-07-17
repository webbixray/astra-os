import { useEffect } from 'react';

type ShortcutHandler = (e: KeyboardEvent) => void;

interface Shortcut {
  key: string;
  meta?: boolean;
  ctrl?: boolean;
  shift?: boolean;
  handler: ShortcutHandler;
}

const registeredShortcuts: Shortcut[] = [];

function matchesShortcut(e: KeyboardEvent, shortcut: Shortcut): boolean {
  if (e.key.toLowerCase() !== shortcut.key.toLowerCase()) return false;
  if (shortcut.meta && !e.metaKey) return false;
  if (shortcut.ctrl && !e.ctrlKey) return false;
  if (shortcut.shift && !e.shiftKey) return false;
  if (!shortcut.meta && !shortcut.ctrl && (e.metaKey || e.ctrlKey)) return false;
  return true;
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
  for (const shortcut of registeredShortcuts) {
    if (matchesShortcut(e, shortcut)) {
      e.preventDefault();
      shortcut.handler(e);
      return;
    }
  }
}

export function useKeyboardShortcut(key: string, handler: ShortcutHandler, options?: { meta?: boolean; ctrl?: boolean; shift?: boolean }) {
  useEffect(() => {
    const shortcut: Shortcut = {
      key,
      handler,
      meta: options?.meta ?? false,
      ctrl: options?.ctrl ?? false,
      shift: options?.shift ?? false,
    };
    registeredShortcuts.push(shortcut);
    if (registeredShortcuts.length === 1) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      const idx = registeredShortcuts.indexOf(shortcut);
      if (idx !== -1) registeredShortcuts.splice(idx, 1);
      if (registeredShortcuts.length === 0) {
        document.removeEventListener('keydown', handleKeyDown);
      }
    };
  }, [key, handler, options?.meta, options?.ctrl, options?.shift]);
}

export function useGlobalSearch(handler: () => void) {
  useKeyboardShortcut('k', handler, { meta: true });
}
