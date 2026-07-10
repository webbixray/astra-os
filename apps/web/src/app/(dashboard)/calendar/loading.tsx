import { Skeleton } from "@/components/ui/skeleton";

export default function CalendarLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="h-6 w-6" />
          <Skeleton className="h-8 w-32" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-8 w-8" />
        </div>
      </div>
      <div className="flex gap-4">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-28" />
      </div>
      <div className="grid grid-cols-7 gap-px rounded-lg border bg-muted">
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div key={i} className="bg-background px-3 py-2">
            <Skeleton className="h-3 w-8 mx-auto" />
          </div>
        ))}
        {Array.from({ length: 35 }).map((_, i) => (
          <div key={i} className="bg-background p-2 min-h-24">
            <Skeleton className="h-6 w-6 rounded-full mb-1" />
            <Skeleton className="h-3 w-full mb-1" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        ))}
      </div>
    </div>
  );
}
