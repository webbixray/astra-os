'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Clock, Layers, Play, Tag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';
import {
  useWorkflowTemplates,
  useInstantiateTemplate,
} from '@/features/workflows/api/useTemplates';
import { TEMPLATE_CATEGORY_COLORS, NODE_COLORS } from '@/features/workflows/types';
import type { WorkflowTemplateSummary } from '@/features/workflows/types';
import { SkeletonCard } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const CATEGORIES = ['all', 'campaign', 'content', 'optimization', 'compliance'];

export default function WorkflowTemplatesPage() {
  const [category, setCategory] = useState('all');
  const { orgId } = useOrg();
  const router = useRouter();
  const { data: templates, isLoading } = useWorkflowTemplates(
    category === 'all' ? undefined : category,
  );
  const instantiate = useInstantiateTemplate();

  const handleInstantiate = async (template: WorkflowTemplateSummary) => {
    const result = await instantiate.mutateAsync({
      templateId: template.template_id,
      input: { organization_id: orgId },
    });
    router.push(`/workflows/${result.workflow_id}`);
  };

  return (
    <ErrorBoundary>
      <div className="flex flex-col gap-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <Button variant="ghost" asChild className="-ml-3 mb-2">
              <Link href="/workflows">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Workflows
              </Link>
            </Button>
            <h1 className="text-2xl font-semibold">Workflow Templates</h1>
            <p className="text-sm text-muted-foreground">
              Start with a pre-built template and customize it for your needs
            </p>
          </div>
        </div>

        <div className="flex gap-2 border-b pb-2">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={cn(
                'rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
                category === c
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
              )}
            >
              {c}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : templates && templates.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {templates.map((template) => (
              <div
                key={template.template_id}
                className="flex flex-col rounded-lg border bg-card p-5 text-card-foreground shadow-sm transition-colors hover:border-primary/50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium leading-none">{template.name}</h3>
                    <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                      {template.description}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
                      TEMPLATE_CATEGORY_COLORS[template.category] || 'bg-muted text-muted-foreground border-border',
                    )}
                  >
                    {template.category}
                  </span>
                  {template.tags.slice(0, 2).map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                    >
                      <Tag className="h-3 w-3" />
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Layers className="h-3.5 w-3.5" />
                    {template.node_count} nodes
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    ~{template.estimated_duration_minutes} min
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => handleInstantiate(template)}
                    disabled={instantiate.isPending}
                  >
                    <Play className="mr-1 h-3 w-3" />
                    Use Template
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 py-20 text-center">
            <Layers className="h-12 w-12 text-muted-foreground" />
            <p className="text-lg text-muted-foreground">No templates found</p>
            <p className="text-sm text-muted-foreground">
              {category !== 'all'
                ? 'Try a different category'
                : 'Templates will appear here'}
            </p>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
