'use client';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {icon && (
        <div className="mb-4 rounded-full bg-gray-100 p-4 dark:bg-gray-800">{icon}</div>
      )}
      <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
      {description && (
        <p className="mb-6 max-w-sm text-sm text-gray-500 dark:text-gray-400">{description}</p>
      )}
      <div className="flex gap-3">
        {action && (
          <Button onClick={action.onClick}>{action.label}</Button>
        )}
        {secondaryAction && (
          <Button variant="outline" onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </Button>
        )}
      </div>
    </div>
  );
}

interface EmptyCampaignStateProps {
  onCreateCampaign?: () => void;
}

export function EmptyCampaignState({ onCreateCampaign }: EmptyCampaignStateProps) {
  return (
    <EmptyState
      icon={
        <svg
          className="h-8 w-8 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          />
        </svg>
      }
      title="No campaigns yet"
      description="Create your first campaign to start tracking your marketing efforts."
      action={{
        label: 'Create Campaign',
        onClick: onCreateCampaign || (() => {}),
      }}
    />
  );
}

interface EmptyContentStateProps {
  onCreateContent?: () => void;
}

export function EmptyContentState({ onCreateContent }: EmptyContentStateProps) {
  return (
    <EmptyState
      icon={
        <svg
          className="h-8 w-8 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      }
      title="No content yet"
      description="Start creating content to engage your audience."
      action={{
        label: 'Create Content',
        onClick: onCreateContent || (() => {}),
      }}
    />
  );
}

interface EmptySearchStateProps {
  query: string;
}

export function EmptySearchState({ query }: EmptySearchStateProps) {
  return (
    <EmptyState
      icon={
        <svg
          className="h-8 w-8 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      }
      title={`No results for "${query}"`}
      description="Try adjusting your search or filter to find what you're looking for."
    />
  );
}
