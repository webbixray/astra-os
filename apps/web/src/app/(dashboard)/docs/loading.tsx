import { Skeleton } from '@/components/ui/skeleton';

export default function DocsLoading() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="mb-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72 mt-2" />
      </div>
      <div className="space-y-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border bg-muted/30 p-6">
            <Skeleton className="h-5 w-24 mb-3" />
            <Skeleton className="h-4 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ))}
      </div>
    </div>
  );
}
