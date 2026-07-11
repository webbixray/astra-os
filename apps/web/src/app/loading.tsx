import { Command } from 'lucide-react';

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background" role="status">
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-2">
          <Command className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">ASTRA OS</span>
        </div>
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <span className="sr-only">Loading...</span>
      </div>
    </div>
  );
}
