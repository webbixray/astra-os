'use client';

import { Button } from '@/components/ui/button';

export default function OfflinePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8 text-center">
      <div className="mb-6 rounded-full bg-gray-100 p-6 dark:bg-gray-800">
        <svg
          className="h-16 w-16 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M18.364 5.636a9 9 0 010 12.728m-2.829-2.829a5 5 0 00-7.072 0m7.072 0l-1.414 1.414M9.636 9.636a5 5 0 000 7.072m-2.829-2.829L4.222 4.222m1.414 1.414L4.222 4.222m14.142 14.142l-1.414-1.414M4.222 4.222l1.414 1.414"
          />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4l16 16" />
        </svg>
      </div>
      <h1 className="mb-2 text-3xl font-bold text-gray-900 dark:text-white">
        You're offline
      </h1>
      <p className="mb-8 max-w-md text-gray-600 dark:text-gray-400">
        It looks like you've lost your internet connection. Some features may not be available until
        you're back online.
      </p>
      <div className="flex gap-4">
        <Button onClick={() => window.location.reload()} variant="outline">
          Try Again
        </Button>
        <Button onClick={() => window.location.assign('/')}>Go Home</Button>
      </div>
      <div className="mt-12 max-w-sm rounded-lg border bg-gray-50 p-6 dark:bg-gray-800/50">
        <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-white">
          What you can do offline:
        </h2>
        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li className="flex items-center gap-2">
            <span className="text-green-500">✓</span>
            View previously loaded pages
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-500">✓</span>
            Access saved drafts
          </li>
          <li className="flex items-center gap-2">
            <span className="text-green-500">✓</span>
            Queue actions for when you're back online
          </li>
        </ul>
      </div>
    </div>
  );
}
