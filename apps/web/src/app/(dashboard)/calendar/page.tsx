'use client';

import { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, CalendarDays } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCalendarEvents } from '@/features/calendar/api/useCalendar';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const TYPE_COLORS: Record<string, string> = {
  campaign: 'border-l-blue-500 bg-blue-500/10 text-blue-500',
  content: 'border-l-emerald-500 bg-emerald-500/10 text-emerald-500',
  ad_campaign: 'border-l-purple-500 bg-purple-500/10 text-purple-500',
};

const TYPE_LABELS: Record<string, string> = {
  campaign: 'Campaign',
  content: 'Content',
  ad_campaign: 'Ad Campaign',
};

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getMonthDays(year: number, month: number): Date[] {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const days: Date[] = [];
  const startPad = first.getDay();
  for (let i = 0; i < startPad; i++) {
    days.push(new Date(year, month, -startPad + i + 1));
  }
  for (let d = 1; d <= last.getDate(); d++) {
    days.push(new Date(year, month, d));
  }
  const endPad = 42 - days.length;
  for (let i = 1; i <= endPad; i++) {
    days.push(new Date(year, month + 1, i));
  }
  return days;
}

function formatDate(d: Date): string {
  return d.toISOString().split('T')[0] ?? '';
}

export default function CalendarPage() {
  const { orgId } = useOrg();
  const today = useMemo(() => new Date(), []);
  const [current, setCurrent] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));

  const year = current.getFullYear();
  const month = current.getMonth();
  const monthStart = formatDate(new Date(year, month, 1));
  const monthEnd = formatDate(new Date(year, month + 1, 0));

  const { data: events, isLoading } = useCalendarEvents(orgId ?? '', monthStart, monthEnd);
  const days = useMemo(() => getMonthDays(year, month), [year, month]);

  const isToday = (d: Date) =>
    d.getFullYear() === today.getFullYear() &&
    d.getMonth() === today.getMonth() &&
    d.getDate() === today.getDate();

  const isCurrentMonth = (d: Date) => d.getMonth() === month;

  const eventsForDay = (d: Date) => {
    const ds = formatDate(d);
    return (events || []).filter((e) => {
      if (!e.start_date) return false;
      const start = e.start_date.split('T')[0];
      return start === ds;
    });
  };

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <CalendarDays className="h-6 w-6" />
          <h1 className="text-2xl font-semibold">Calendar</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setCurrent(new Date(today.getFullYear(), today.getMonth(), 1))}>
            Today
          </Button>
          <Button variant="ghost" size="icon" aria-label="Previous month" onClick={() => setCurrent(new Date(year, month - 1, 1))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="min-w-40 text-center font-medium">
            {current.toLocaleString('default', { month: 'long', year: 'numeric' })}
          </span>
          <Button variant="ghost" size="icon" aria-label="Next month" onClick={() => setCurrent(new Date(year, month + 1, 1))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-blue-500" /> Campaigns
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-emerald-500" /> Content
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-purple-500" /> Ad Campaigns
        </span>
      </div>

      <div className="grid grid-cols-7 gap-px rounded-lg border bg-muted">
        {DAY_NAMES.map((name) => (
          <div key={name} className="bg-background px-3 py-2 text-center text-xs font-medium text-muted-foreground">
            {name}
          </div>
        ))}
        {days.map((d, i) => {
          const dayEvents = eventsForDay(d);
          return (
            <div
              key={i}
              className={cn(
                'min-h-24 bg-background p-2 transition-colors',
                !isCurrentMonth(d) && 'opacity-40',
              )}
            >
              <span
                className={cn(
                  'inline-flex h-6 w-6 items-center justify-center rounded-full text-sm',
                  isToday(d) && 'bg-primary text-primary-foreground font-medium',
                )}
              >
                {d.getDate()}
              </span>
              <div className="mt-1 flex flex-col gap-0.5">
                {dayEvents.slice(0, 3).map((ev) => (
                  <Link
                    key={ev.id}
                    href={ev.link || '#'}
                    className={cn(
                      'truncate rounded px-1 py-0.5 text-xs border-l-2',
                      TYPE_COLORS[ev.type] || 'border-l-muted',
                    )}
                  >
                    {ev.title}
                  </Link>
                ))}
                {dayEvents.length > 3 && (
                  <span className="text-xs text-muted-foreground px-1">
                    +{dayEvents.length - 3} more
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {!isLoading && events && events.length > 0 && (
        <div className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 text-sm font-medium">Upcoming This Month</h2>
          <div className="flex flex-col gap-2">
            {events.slice(0, 10).map((ev) => (
              <Link
                key={ev.id}
                href={ev.link || '#'}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-accent transition-colors"
              >
                <span className={cn('h-2 w-2 rounded-full', TYPE_COLORS[ev.type]?.split(' ')[0]?.replace('border-l-', 'bg-') ?? 'bg-muted')} />
                <span className="min-w-20 text-xs text-muted-foreground">{ev.start_date?.split('T')[0]}</span>
                <span className="font-medium">{ev.title}</span>
                <span className="ml-auto text-xs text-muted-foreground">{TYPE_LABELS[ev.type]}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
