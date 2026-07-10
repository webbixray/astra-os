import { Skeleton } from "@/components/ui/skeleton";

export default function NewWorkflowLoading() {
  return (
    <div className="space-y-6 p-6 max-w-3xl">
      <Skeleton className="h-8 w-40" />
      <div className="rounded-lg border bg-card p-6 space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-10 w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-24 w-full" />
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-28" />
          {[1, 2].map((i) => (
            <div key={i} className="flex items-center gap-3 rounded-md border p-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <Skeleton className="h-3 flex-1" />
              <Skeleton className="h-6 w-6" />
            </div>
          ))}
          <Skeleton className="h-8 w-32" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-24" />
        </div>
      </div>
    </div>
  );
}
