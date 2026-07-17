'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useFormValidation, getFieldError } from '@/lib/validation';
import { useCreateWorkflow } from '@/features/workflows/api/useWorkflows';
import { useOrg } from '@/lib/org';

const workflowSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name is too long'),
  description: z.string().max(500, 'Description is too long').optional().default(''),
});

type FormData = z.infer<typeof workflowSchema>;

export default function NewWorkflowPage() {
  const router = useRouter();
  const { orgId } = useOrg();
  const createWorkflow = useCreateWorkflow();
  const { formData, errors, handleChange, handleSubmit } = useFormValidation(workflowSchema, {
    name: '',
    description: '',
  });

  const onSubmit = useCallback(async (data: FormData) => {
    const result = await createWorkflow.mutateAsync({
      organization_id: orgId,
      name: data.name,
      description: data.description || undefined,
    });
    router.push(`/workflows/${result.id}`);
  }, [createWorkflow, orgId, router]);

  return (
    <div className="mx-auto max-w-2xl p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">New Workflow</h1>
        <p className="text-sm text-muted-foreground">
          Create an automated marketing workflow
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="name">Workflow Name</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="Campaign Approval Workflow"
            error={getFieldError(errors, 'name')}
          />
          {getFieldError(errors, 'name') && <p className="text-xs text-destructive">{getFieldError(errors, 'name')}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={3}
            placeholder="Describe what this workflow does..."
          />
        </div>

        <div className="flex gap-4 pt-4">
          <Button type="submit">
            Create Workflow
          </Button>
          <Button type="button" variant="outline" onClick={() => router.back()}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
