'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Home, Bug } from 'lucide-react';
import Link from 'next/link';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Global error caught:', error);

    // Could send to Sentry, LogRocket, etc.
    if (typeof window !== 'undefined' && window.__ERROR_REPORTER__) {
      window.__ERROR_REPORTER__.captureException(error);
    }
  }, [error]);

  return (
    <html lang="en">
      <head>
        <title>Error - ASTRA OS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-screen bg-background flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center space-y-6">
          <div className="mx-auto w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertCircle className="w-10 h-10 text-destructive" />
          </div>

          <div>
            <h1 className="text-2xl font-bold text-foreground">Application Error</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              An unexpected error occurred. The error has been logged and our team has been notified.
            </p>
          </div>

          {process.env.NODE_ENV === 'development' && (
            <details className="text-left bg-muted p-4 rounded-lg text-sm space-y-2">
              <summary className="font-mono cursor-pointer">Error Details (Development)</summary>
              <pre className="whitespace-pre-wrap text-xs overflow-auto max-h-60">
                {error.toString()}
                {error.stack && `\n\n${error.stack}`}
              </pre>
            </details>
          )}

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button onClick={reset} className="w-full sm:w-auto">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
            <Button variant="outline" asChild className="w-full sm:w-auto">
              <Link href="/">
                <Home className="mr-2 h-4 w-4" />
                Go Home
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full sm:w-auto">
              <Link href="mailto:support@astra-os.com?subject=Global Error Report">
                <Bug className="mr-2 h-4 w-4" />
                Report Issue
              </Link>
            </Button>
          </div>

          <p className="text-xs text-muted-foreground pt-4 border-t">
            Error ID: {error.digest ?? 'unknown'}
          </p>
        </div>
      </body>
    </html>
  );
}
