import { Skeleton } from "@/components/ui/skeleton";

export default function EmailSettingsLoading() {
  return (
    <div className="space-y-6 p-6 max-w-2xl">
      <Skeleton className="h-8 w-40" />
      <div className="rounded-lg border bg-card p-6 space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-10 w-full" />
          </div>
        ))}
        <div className="space-y-2">
          <Skeleton className="h-4 w-36" />
          <div className="flex gap-3">
            <Skeleton className="h-10 flex-1" />
            <Skeleton className="h-10 flex-1" />
          </div>
        </div>
        <Skeleton className="h-10 w-32" />
      </div>
    </div>
  );
}
