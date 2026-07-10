import { Skeleton } from "@/components/ui/skeleton";

export default function MonitoringLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-44" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border bg-card p-4 space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-7 w-16" />
            <Skeleton className="h-2 w-full" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
      <div className="rounded-lg border bg-card p-4">
        <Skeleton className="h-5 w-40 mb-4" />
        <Skeleton className="h-[300px] w-full" />
      </div>
      <div className="rounded-lg border bg-card p-4">
        <Skeleton className="h-5 w-32 mb-3" />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-4 py-2">
            <Skeleton className="h-2 w-2 rounded-full" />
            <Skeleton className="h-3 w-36" />
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-24" />
          </div>
        ))}
      </div>
    </div>
  );
}
