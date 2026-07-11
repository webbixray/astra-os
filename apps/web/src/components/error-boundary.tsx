'use client';

import { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Home, Bug } from 'lucide-react';
import Link from 'next/link';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ error, errorInfo });
    this.props.onError?.(error, errorInfo);

    // Log to error tracking service
    if (typeof window !== 'undefined') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);

      // Could send to Sentry, LogRocket, etc.
      // if (window.Sentry) window.Sentry.captureException(error);
    }
  }

  reset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // If custom fallback provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-[300px] flex items-center justify-center p-8">
          <div className="max-w-md w-full text-center space-y-6">
            <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-destructive" />
            </div>

            <div>
              <h2 className="text-xl font-semibold text-foreground">Something went wrong</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                We&apos;re sorry, but an unexpected error occurred in this component.
              </p>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="text-left bg-muted p-4 rounded-lg text-sm space-y-2">
                <summary className="font-mono cursor-pointer">Error Details (Development)</summary>
                <pre className="whitespace-pre-wrap text-xs overflow-auto max-h-60 font-mono">
                  {this.state.error.toString()}
                  {this.state.error.stack && `\n\n${this.state.error.stack}`}
                </pre>
                {this.state.errorInfo && (
                  <pre className="whitespace-pre-wrap text-xs overflow-auto max-h-40 font-mono">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </details>
            )}

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={this.reset} className="w-full sm:w-auto">
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
                <Link href="mailto:support@astra-os.com?subject=Component Error Report">
                  <Bug className="mr-2 h-4 w-4" />
                  Report Issue
                </Link>
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Specialized error boundaries for different contexts
export class PageErrorBoundary extends ErrorBoundary {
  render(): ReactNode {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="min-h-screen bg-background flex items-center justify-center p-8">
          <div className="max-w-md w-full text-center space-y-6">
            <div className="mx-auto w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center">
              <AlertCircle className="w-10 h-10 text-destructive" />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-foreground">Page Error</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                This page encountered an error. Try navigating back or refreshing the page.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={this.reset} className="w-full sm:w-auto">
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Page
              </Button>
              <Button variant="outline" asChild className="w-full sm:w-auto">
                <Link href="/">
                  <Home className="mr-2 h-4 w-4" />
                  Go Home
                </Link>
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export class WidgetErrorBoundary extends ErrorBoundary {
  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="bg-muted p-4 rounded-lg border border-border/50">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground">Widget failed to load</p>
              <p className="text-xs text-muted-foreground">
                This widget encountered an error. Try refreshing the page.
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={this.reset}
              className="flex-shrink-0"
            >
              <RefreshCw className="h-4 w-4" />
              Retry
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export class AsyncErrorBoundary extends ErrorBoundary {
  state: State = { hasError: false, error: null, errorInfo: null };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    super.componentDidCatch(error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-destructive" />
            <span className="text-sm font-medium text-destructive">Async operation failed</span>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {this.state.error?.message ?? 'An async error occurred'}
          </p>
          <Button variant="ghost" size="sm" onClick={this.reset} className="mt-2">
            <RefreshCw className="h-3 w-3 mr-1" />
            Retry
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}