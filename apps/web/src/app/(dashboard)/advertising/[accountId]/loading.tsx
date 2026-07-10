import { Skeleton } from "@/components/ui/skeleton";

export default function AccountDetailLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-lg border bg-card p-4 space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-7 w-20" />
          </div>
        ))}
      </div>
      <div className="rounded-lg border bg-card p-4">
        <Skeleton className="h-5 w-36 mb-4" />
        <Skeleton className="h-[280px] w-full" />
      </div>
      <div className="rounded-lg border bg-card">
        <div className="p-4">
          <Skeleton className="h-5 w-40" />
        </div>
        <div className="space-y-1 px-4 pb-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-4 py-3">
              <Skeleton className="h-3 w-32" />
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-3 w-20" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
