'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Plus, Target, Globe, LayoutTemplate, Copy, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { CampaignCard } from '@/features/campaigns/components/campaign-card';
import { useCampaigns } from '@/features/campaigns/api/useCampaigns';
import { useCampaignOverview } from '@/features/calendar/api/useCalendar';
import {
  useTemplates,
  useCreateTemplate,
  useCloneFromTemplate,
  useDeleteTemplate,
} from '@/features/campaigns/api/useAdvancedCampaigns';
import { useOrg } from '@/lib/org';
import { SkeletonCard } from '@/components/ui/skeleton';

const STATUSES = ['all', 'draft', 'pending_approval', 'active', 'paused', 'completed', 'archived'];

export default function CampaignsPage() {
  const [status, setStatus] = useState<string>('all');
  const [tab, setTab] = useState<'campaigns' | 'templates'>('campaigns');
  const { orgId } = useOrg();
  const { data: campaigns, isLoading, isError: campaignsError, refetch: refetchCampaigns } = useCampaigns(orgId, status === 'all' ? undefined : status);
  const { data: overview } = useCampaignOverview(orgId);
  const { data: templates, isError: templatesError, refetch: refetchTemplates } = useTemplates(orgId);
  const createTemplate = useCreateTemplate();
  const cloneFromTemplate = useCloneFromTemplate();
  const deleteTemplate = useDeleteTemplate();

  const [showNewTemplate, setShowNewTemplate] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDesc, setTemplateDesc] = useState('');
  const [cloneName, setCloneName] = useState('');
  const [cloneTemplateId, setCloneTemplateId] = useState<string | null>(null);

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Campaigns</h1>
          <p className="text-sm text-muted-foreground">
            Manage your marketing campaigns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg border bg-card p-0.5">
            <button
              onClick={() => setTab('campaigns')}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === 'campaigns' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
              }`}
            >
              Campaigns
            </button>
            <button
              onClick={() => setTab('templates')}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === 'templates' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
              }`}
            >
              Templates
            </button>
          </div>
          {tab === 'campaigns' ? (
            <Link href="/campaigns/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Campaign
              </Button>
            </Link>
          ) : (
            <Button onClick={() => setShowNewTemplate(!showNewTemplate)}>
              <Plus className="mr-2 h-4 w-4" />
              New Template
            </Button>
          )}
        </div>
      </div>

      {tab === 'campaigns' ? (
        <>
          {overview && (
            <div className="grid grid-cols-4 gap-4">
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Target className="h-4 w-4" />
                  Campaigns
                </div>
                <p className="mt-1 text-2xl font-semibold">{overview.total_campaigns}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Globe className="h-4 w-4" />
                  Ad Campaigns
                </div>
                <p className="mt-1 text-2xl font-semibold">{overview.total_ad_campaigns}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Target className="h-4 w-4" />
                  Combined
                </div>
                <p className="mt-1 text-2xl font-semibold">{overview.combined_total}</p>
              </div>
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Globe className="h-4 w-4" />
                  Platforms
                </div>
                <p className="mt-1 text-2xl font-semibold">
                  {Object.keys(overview.ad_platform_breakdown || {}).length}
                </p>
                <p className="text-xs text-muted-foreground">
                  {Object.entries(overview.ad_platform_breakdown || {}).map(([p, c]) => `${p}: ${c}`).join(', ')}
                </p>
              </div>
            </div>
          )}

          <div className="flex gap-2 border-b pb-2">
            {STATUSES.map((s) => (
              <button
                key={s}
                onClick={() => setStatus(s)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  status === s
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                {s.replace('_', ' ')}
              </button>
            ))}
          </div>

          {campaignsError ? (
            <div className="flex flex-col items-center gap-4 rounded-lg border border-destructive/50 bg-destructive/5 py-16 text-center">
              <p className="text-sm text-destructive">Failed to load campaigns</p>
              <Button variant="outline" size="sm" onClick={() => refetchCampaigns()}>
                Try Again
              </Button>
            </div>
          ) : isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : campaigns && campaigns.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {campaigns.map((campaign) => (
                <Link key={campaign.id} href={`/campaigns/${campaign.id}`}>
                  <CampaignCard campaign={campaign} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-20 text-center">
              <p className="text-lg text-muted-foreground">No campaigns yet</p>
              <p className="text-sm text-muted-foreground">
                Create your first campaign to get started
              </p>
              <Link href="/campaigns/new">
                <Button variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Campaign
                </Button>
              </Link>
            </div>
          )}
        </>
      ) : (
        <div className="space-y-4">
          {showNewTemplate && (
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium">New Template</h3>
              <label htmlFor="template-name" className="text-xs font-medium text-muted-foreground">Template name</label>
              <Input
                id="template-name"
                placeholder="Template name"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
              />
              <label htmlFor="template-desc" className="text-xs font-medium text-muted-foreground">Description</label>
              <Textarea
                id="template-desc"
                placeholder="Description"
                value={templateDesc}
                onChange={(e) => setTemplateDesc(e.target.value)}
                className="min-h-[40px]"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  disabled={createTemplate.isPending || !templateName}
                  onClick={async () => {
                    await createTemplate.mutateAsync({
                      organization_id: orgId,
                      name: templateName,
                      description: templateDesc,
                    });
                    setShowNewTemplate(false);
                    setTemplateName('');
                    setTemplateDesc('');
                  }}
                >
                  {createTemplate.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
                  Save Template
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowNewTemplate(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {templatesError ? (
            <div className="flex flex-col items-center gap-4 rounded-lg border border-destructive/50 bg-destructive/5 py-16 text-center">
              <p className="text-sm text-destructive">Failed to load templates</p>
              <Button variant="outline" size="sm" onClick={() => refetchTemplates()}>
                Try Again
              </Button>
            </div>
          ) : templates && templates.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {templates.map((t) => (
                <div key={t.id} className="rounded-lg border bg-card p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <LayoutTemplate className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-sm">{t.name}</span>
                      </div>
                      {t.description && (
                        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{t.description}</p>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-6 w-6 p-0 text-muted-foreground hover:text-red-500"
                      aria-label="Delete"
                      onClick={() => deleteTemplate.mutate(t.id)}
                    >
                      ×
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {t.channels.map((ch) => (
                      <span key={ch} className="rounded-full bg-secondary px-2 py-0.5 text-[10px]">
                        {ch}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    {t.objective && <span>{t.objective}</span>}
                    {t.budget_amount && <span>{t.budget_currency} {t.budget_amount.toLocaleString()}</span>}
                  </div>
                  <div className="flex gap-2 pt-1">
                    <label htmlFor={`clone-name-${t.id}`} className="sr-only">Campaign name</label>
                    <Input
                      id={`clone-name-${t.id}`}
                      placeholder="Campaign name"
                      value={cloneTemplateId === t.id ? cloneName : ''}
                      onChange={(e) => {
                        setCloneTemplateId(t.id);
                        setCloneName(e.target.value);
                      }}
                      className="flex-1 h-7 text-xs"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs"
                      disabled={cloneFromTemplate.isPending || cloneTemplateId !== t.id || !cloneName}
                      onClick={() => {
                        if (cloneName) {
                          cloneFromTemplate.mutate({
                            template_id: t.id,
                            organization_id: orgId,
                            name: cloneName,
                          });
                          setCloneTemplateId(null);
                          setCloneName('');
                        }
                      }}
                    >
                      <Copy className="mr-1 h-3 w-3" />
                      Clone
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4 py-20 text-center">
              <LayoutTemplate className="h-10 w-10 text-muted-foreground/40" />
              <p className="text-lg text-muted-foreground">No templates yet</p>
              <p className="text-sm text-muted-foreground">
                Save successful campaigns as reusable templates
              </p>
              <Button variant="outline" onClick={() => setShowNewTemplate(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Template
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
