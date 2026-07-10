import { Skeleton } from "@/components/ui/skeleton";

export default function NewCampaignLoading() {
  return (
    <div className="space-y-6 p-6 max-w-3xl">
      <Skeleton className="h-8 w-48" />
      <div className="rounded-lg border bg-card p-6 space-y-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-10 w-full" />
          </div>
        ))}
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-20 w-full" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-24" />
        </div>
      </div>
    </div>
  );
}
