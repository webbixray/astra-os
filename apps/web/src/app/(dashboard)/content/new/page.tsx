'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { useFormValidation } from '@/lib/validation';
import { useCreateContent } from '@/features/content/api/useContent';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const CONTENT_TYPES = ['blog', 'social', 'email', 'ad', 'landing', 'video_desc'] as const;

const CONTENT_TYPE_OPTIONS = CONTENT_TYPES.map((t) => ({
  value: t,
  label: t.charAt(0).toUpperCase() + t.slice(1).replace('_', ' '),
}));

const contentSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200, 'Title is too long'),
  content_type: z.enum(CONTENT_TYPES),
  body: z.string().max(50000, 'Content is too long').optional().default(''),
});

type ContentFormData = z.infer<typeof contentSchema>;

export default function NewContentPage() {
  const router = useRouter();
  const { orgId } = useOrg();
  const createContent = useCreateContent();
  const { formData, errors, handleChange, handleSubmit: withValidation } = useFormValidation(contentSchema, {
    title: '',
    content_type: 'blog',
    body: '',
  });

  const onSubmit = useCallback(async (data: ContentFormData) => {
    await createContent.mutateAsync({
      organization_id: orgId,
      title: data.title,
      content_type: data.content_type,
      body: data.body,
    });
    router.push('/content');
  }, [createContent, orgId, router]);

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold">New Content</h1>
        <p className="text-sm text-muted-foreground">
          Create marketing content with AI assistance
        </p>
      </div>

      <form onSubmit={withValidation(onSubmit)} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            placeholder="10 Ways AI Transforms Marketing"
            error={errors.title}
          />
          {errors.title && <p className="text-xs text-destructive">{errors.title}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="content_type">Content Type</Label>
          <Select
            id="content_type"
            options={CONTENT_TYPE_OPTIONS}
            value={formData.content_type}
            onChange={(e) => handleChange('content_type', e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="body">Content</Label>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground"
            >
              Generate with AI
            </Button>
          </div>
          <Textarea
            id="body"
            value={formData.body}
            onChange={(e) => handleChange('body', e.target.value)}
            placeholder="Write your content here..."
            className="min-h-[300px]"
          />
        </div>

        <div className="flex gap-4 pt-4">
          <Button type="submit" disabled={createContent.isPending}>
            {createContent.isPending ? 'Creating...' : 'Create Content'}
          </Button>
          <Button type="button" variant="outline" onClick={() => router.back()}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
    </ErrorBoundary>
  );
}
