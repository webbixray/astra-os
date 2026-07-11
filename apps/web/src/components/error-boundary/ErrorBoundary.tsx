'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Home, Bug } from 'lucide-react';
import Link from 'next/link';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState;
  public static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ error, errorInfo });

    // Log to error reporting service
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call optional onError callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Could send to Sentry, LogRocket, etc.
    if (typeof window !== 'undefined' && window.__ERROR_REPORTER__) {
      window.__ERROR_REPORTER__.captureException(error, { extra: errorInfo });
    }
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      // If custom fallback provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="max-w-md w-full text-center space-y-6">
            <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-destructive" />
            </div>

            <div>
              <h2 className="text-xl font-semibold text-foreground">Something went wrong</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                We encountered an unexpected error. Please try again or contact support if the problem persists.
              </p>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="text-left bg-muted p-4 rounded-lg text-sm space-y-2">
                <summary className="font-mono cursor-pointer">Error Details (Development)</summary>
                <pre className="whitespace-pre-wrap text-xs overflow-auto max-h-60">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack && `\n\n${this.state.errorInfo.componentStack}`}
                </pre>
              </details>
            )}

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={this.handleRetry}
                className="w-full sm:w-auto"
              >
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
                <Link href="mailto:support@astra-os.com?subject=Error Report">
                  <Bug className="mr-2 h-4 w-4" />
                  Report Issue
                </Link>
              </Button>
            </div>
          </div>
        </div>
      );
    }
  }
}

// Specialized error boundaries for different parts of the app

export class PageErrorBoundary extends ErrorBoundary {
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[60vh] flex items-center justify-center p-8">
          <div className="max-w-2xl w-full">
            <h1 className="text-2xl font-bold text-center mb-4">Page Error</h1>
            <p className="text-muted-foreground text-center mb-6">
              This page couldn't load properly. The error has been logged.
            </p>
            <Button onClick={this.handleRetry} className="w-full">
              Reload Page
            </Button>
          </div>
        </div>
      );
    }
  }
}

export class WidgetErrorBoundary extends ErrorBoundary {
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 border border-destructive/20 rounded-lg bg-destructive/5">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <span className="font-medium text-destructive">Widget Error</span>
          </div>
          <p className="text-sm text-muted-foreground mb-3">
            This widget failed to load. Try refreshing the page.
          </p>
          <Button variant="outline" size="sm" onClick={this.handleRetry}>
            <RefreshCw className="mr-1 h-3 w-3" />
            Retry
          </Button>
        </div>
      );
    }
  }
}

export class AsyncErrorBoundary extends ErrorBoundary {
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-destructive/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">Failed to Load</h3>
          <p className="text-muted-foreground mb-4">
            An error occurred while loading this content.
          </p>
          <Button onClick={this.handleRetry}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>
      );
    }
  }
}

// Hook for programmatic error boundary reset
export function useErrorBoundary() {
  const [, forceUpdate] = useState({});

  const resetErrorBoundary = () => {
    forceUpdate({});
  };

  return { resetErrorBoundary };
}

// Client-side error reporting
declare global {
  interface Window {
    __ERROR_REPORTER__?: {
      captureException: (error: Error, context?: Record<string, unknown>) => void;
      captureMessage: (message: string, level?: 'info' | 'warning' | 'error') => void;
    };
  }
}

// Initialize error reporter (can be replaced with Sentry, LogRocket, etc.)
export function initErrorReporter() {
  if (typeof window === 'undefined') return;

  window.__ERROR_REPORTER__ = {
    captureException: (error: Error, context?: Record<string, unknown>) => {
      console.error('[Error Reporter]', error, context);
      // In production, send to Sentry, LogRocket, etc.
    },
    captureMessage: (message: string, level: 'info' | 'warning' | 'error' = 'error') => {
      console[level](`[Error Reporter] ${message}`);
    },
  };
}

// Auto-initialize on client
if (typeof window !== 'undefined') {
  initErrorReporter();
}

import { useState } from 'react';