import { Skeleton } from '@/components/ui/skeleton';

export default function WorkflowDetailLoading() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <Skeleton className="h-4 w-32" />
      <div className="space-y-2">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>
      <Skeleton className="h-[400px] w-full rounded-lg" />
    </div>
  );
}
