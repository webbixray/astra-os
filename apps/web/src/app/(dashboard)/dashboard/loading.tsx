import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLoading() {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-5 w-28" />
        </div>
        <Skeleton className="h-8 w-20" />
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="hidden md:block w-56 shrink-0 border-r p-3">
          <Skeleton className="h-3 w-24 mb-3" />
          <div className="space-y-1">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        </div>
        <div className="flex-1 p-6">
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-3 rounded-lg border bg-card p-4 space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-8 w-16" />
            </div>
            <div className="col-span-3 rounded-lg border bg-card p-4 space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-8 w-16" />
            </div>
            <div className="col-span-3 rounded-lg border bg-card p-4 space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-8 w-16" />
            </div>
            <div className="col-span-3 rounded-lg border bg-card p-4 space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-8 w-16" />
            </div>
            <div className="col-span-8 rounded-lg border bg-card p-4">
              <Skeleton className="h-5 w-32 mb-4" />
              <Skeleton className="h-[250px] w-full" />
            </div>
            <div className="col-span-4 rounded-lg border bg-card p-4">
              <Skeleton className="h-5 w-28 mb-4" />
              <Skeleton className="h-[250px] w-full" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
