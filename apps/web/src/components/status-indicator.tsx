'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

type Status = 'active' | 'inactive' | 'pending' | 'error' | 'success' | 'warning' | 'info';

interface StatusIndicatorProps {
  status: Status;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
  className?: string;
}

const statusStyles: Record<Status, string> = {
  active: 'bg-green-500',
  inactive: 'bg-gray-400',
  pending: 'bg-yellow-500',
  error: 'bg-red-500',
  success: 'bg-green-500',
  warning: 'bg-orange-500',
  info: 'bg-blue-500',
};

const statusBadgeStyles: Record<Status, string> = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  success: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  warning: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
};

const dotSizes = {
  sm: 'h-2 w-2',
  md: 'h-3 w-3',
  lg: 'h-4 w-4',
};

export function StatusIndicator({ status, label, size = 'md', showDot = true, className }: StatusIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      {showDot && (
        <span
          className={cn(
            'rounded-full',
            dotSizes[size],
            statusStyles[status],
            (status === 'active' || status === 'success') && 'animate-pulse',
          )}
        />
      )}
      {label && <span className="text-sm font-medium">{label}</span>}
    </div>
  );
}

interface StatusBadgeProps {
  status: Status;
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const displayLabel = label || status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <Badge variant="secondary" className={cn(statusBadgeStyles[status], className)}>
      {displayLabel}
    </Badge>
  );
}

interface ConnectionStatusProps {
  isConnected: boolean;
  lastSync?: string;
  className?: string;
}

export function ConnectionStatus({ isConnected, lastSync, className }: ConnectionStatusProps) {
  return (
    <div className={cn('flex items-center gap-3 rounded-lg border p-3', className)}>
      <StatusIndicator status={isConnected ? 'active' : 'error'} size="md" />
      <div className="flex-1">
        <p className="text-sm font-medium">{isConnected ? 'Connected' : 'Disconnected'}</p>
        {lastSync && (
          <p className="text-xs text-gray-500">Last sync: {new Date(lastSync).toLocaleString()}</p>
        )}
      </div>
      {!isConnected && (
        <Badge variant="destructive" className="text-xs">
          Reconnecting...
        </Badge>
      )}
    </div>
  );
}

interface SystemStatusProps {
  services: {
    name: string;
    status: 'operational' | 'degraded' | 'down';
    latency?: number;
  }[];
  className?: string;
}

export function SystemStatus({ services, className }: SystemStatusProps) {
  const statusMap: Record<string, Status> = {
    operational: 'success',
    degraded: 'warning',
    down: 'error',
  };

  return (
    <div className={cn('space-y-3', className)}>
      {services.map((service) => (
        <div key={service.name} className="flex items-center justify-between rounded-lg border p-3">
          <div className="flex items-center gap-3">
            <StatusIndicator status={statusMap[service.status] ?? 'info'} size="sm" />
            <span className="text-sm font-medium">{service.name}</span>
          </div>
          <div className="flex items-center gap-2">
            {service.latency !== undefined && (
              <span className="text-xs text-gray-500">{service.latency}ms</span>
            )}
            <StatusBadge status={statusMap[service.status] ?? 'info'} label={service.status} />
          </div>
        </div>
      ))}
    </div>
  );
}
