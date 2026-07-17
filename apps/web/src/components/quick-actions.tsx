'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

interface QuickAction {
  id: string;
  label: string;
  icon: string;
  shortcut?: string;
  action: () => void;
  group: string;
}

const defaultActions: QuickAction[] = [
  { id: 'new-campaign', label: 'Create New Campaign', icon: '📢', shortcut: '⌘N', action: () => {}, group: 'Campaigns' },
  { id: 'view-campaigns', label: 'View All Campaigns', icon: '📋', action: () => {}, group: 'Campaigns' },
  { id: 'new-content', label: 'Create New Content', icon: '✏️', shortcut: '⌘⇧N', action: () => {}, group: 'Content' },
  { id: 'view-content', label: 'View All Content', icon: '📄', action: () => {}, group: 'Content' },
  { id: 'view-analytics', label: 'View Analytics', icon: '📊', action: () => {}, group: 'Analytics' },
  { id: 'export-report', label: 'Export Report', icon: '📤', action: () => {}, group: 'Analytics' },
  { id: 'invite-member', label: 'Invite Team Member', icon: '👤', action: () => {}, group: 'Team' },
  { id: 'settings', label: 'Open Settings', icon: '⚙️', shortcut: '⌘,', action: () => {}, group: 'Settings' },
  { id: 'help', label: 'Open Help Center', icon: '❓', shortcut: '⌘/', action: () => {}, group: 'Help' },
  { id: 'keyboard-shortcuts', label: 'Keyboard Shortcuts', icon: '⌨️', shortcut: '⌘K', action: () => {}, group: 'Help' },
];

interface QuickActionsMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  actions?: QuickAction[];
}

export function QuickActionsMenu({ open, onOpenChange, actions = defaultActions }: QuickActionsMenuProps) {
  const [_search, _setSearch] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onOpenChange(!open);
      }
      if (e.key === 'Escape') {
        onOpenChange(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onOpenChange]);

  const groupedActions = actions.reduce(
    (acc, action) => {
      if (!acc[action.group]) acc[action.group] = [];
      acc[action.group]!.push(action);
      return acc;
    },
    {} as Record<string, QuickAction[]>,
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0">
        <Command className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-gray-500 [&_[cmdk-group]]:px-2">
          <CommandInput placeholder="Type a command or search..." />
          <CommandList>
            <CommandEmpty>No results found.</CommandEmpty>
            {Object.entries(groupedActions).map(([group, groupActions]) => (
              <CommandGroup key={group} heading={group}>
                {groupActions.map((action) => (
                  <CommandItem
                    key={action.id}
                    value={action.label}
                    onSelect={() => {
                      action.action();
                      onOpenChange(false);
                    }}
                  >
                    <span className="mr-2">{action.icon}</span>
                    <span>{action.label}</span>
                    {action.shortcut && (
                      <kbd className="ml-auto flex h-5 items-center gap-1 rounded border bg-gray-100 px-1.5 font-mono text-[10px] font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                        {action.shortcut}
                      </kbd>
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}

export function QuickActionsButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        variant="outline"
        className={cn(
          'relative h-9 w-full justify-start rounded-[0.5rem] bg-gray-100 text-sm text-gray-500 dark:bg-gray-800 dark:text-gray-400',
          'sm:pr-12 md:w-40 lg:w-64',
        )}
        onClick={() => setOpen(true)}
      >
        <span className="hidden lg:inline-flex">Search commands...</span>
        <span className="inline-flex lg:hidden">Search...</span>
        <kbd className="pointer-events-none absolute right-1.5 top-1.5 hidden h-5 select-none items-center gap-1 rounded border bg-gray-100 px-1.5 font-mono text-[10px] font-medium dark:bg-gray-800 sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>
      <QuickActionsMenu open={open} onOpenChange={setOpen} />
    </>
  );
}
