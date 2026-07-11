'use client';

import { cn } from '@/lib/utils';

interface ProgressProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  label?: string;
  className?: string;
  indicatorClassName?: string;
}

export function Progress({
  value,
  max = 100,
  size = 'md',
  showLabel = false,
  label,
  className,
  indicatorClassName,
}: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={cn('w-full', className)}>
      {(showLabel || label) && (
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label || 'Progress'}
          </span>
          {showLabel && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div className={cn('w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700', sizeClasses[size])}>
        <div
          className={cn(
            'rounded-full bg-blue-600 transition-all duration-300 ease-in-out',
            sizeClasses[size],
            indicatorClassName,
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}

interface StepIndicatorProps {
  steps: { label: string; description?: string }[];
  currentStep: number;
  className?: string;
}

export function StepIndicator({ steps, currentStep, className }: StepIndicatorProps) {
  return (
    <nav aria-label="Progress" className={cn('flex', className)}>
      <ol className="space-y-4">
        {steps.map((step, index) => (
          <li key={index} className="flex items-start gap-3">
            <div
              className={cn(
                'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full',
                index < currentStep && 'bg-green-600 text-white',
                index === currentStep && 'bg-blue-600 text-white',
                index > currentStep && 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
              )}
            >
              {index < currentStep ? (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <span className="text-sm font-medium">{index + 1}</span>
              )}
            </div>
            <div className="flex flex-col">
              <span
                className={cn(
                  'text-sm font-medium',
                  index <= currentStep ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400',
                )}
              >
                {step.label}
              </span>
              {step.description && (
                <span className="text-sm text-gray-500 dark:text-gray-400">{step.description}</span>
              )}
            </div>
          </li>
        ))}
      </ol>
    </nav>
  );
}

interface CircularProgressProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

export function CircularProgress({
  value,
  max = 100,
  size = 64,
  strokeWidth = 4,
  className,
}: CircularProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="text-blue-600 transition-all duration-300 ease-in-out"
        />
      </svg>
      <span className="absolute text-sm font-medium text-gray-900 dark:text-white">
        {Math.round(percentage)}%
      </span>
    </div>
  );
}
