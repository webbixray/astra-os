'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Plus, Mail, Send, Clock, Loader2, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  useEmailCampaigns,
  useCreateEmailCampaign,
  useSendEmailCampaign,
  useDeleteEmailCampaign,
  useEmailProviders,
  useEmailAnalytics,
} from '@/features/email/api/useEmail';
import { cn } from '@/lib/utils';
import { useOrg } from '@/lib/org';
import { EMAIL_STATUS_COLORS } from '@/lib/constants';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const STATUSES = ['all', 'draft', 'scheduled', 'sending', 'sent', 'failed'] as const;

const STATUS_COLORS = EMAIL_STATUS_COLORS;

export default function EmailCampaignsPage() {
  const { orgId } = useOrg();
  const [status, setStatus] = useState<string>('all');
  const [showNew, setShowNew] = useState(false);
  const { data: campaigns, isLoading } = useEmailCampaigns(orgId, status === 'all' ? undefined : status);
  const { data: providers } = useEmailProviders(orgId);
  const { data: analytics } = useEmailAnalytics(orgId);
  const createCampaign = useCreateEmailCampaign();
  const sendCampaign = useSendEmailCampaign();
  const deleteCampaign = useDeleteEmailCampaign();

  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [providerId, setProviderId] = useState('');

  const [fromEmail, setFromEmail] = useState('');

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-5xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Email Campaigns</h1>
          <p className="text-sm text-muted-foreground">
            Create, send, and track email campaigns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/email/settings">
            <Button variant="outline" size="sm">
              Provider Settings
            </Button>
          </Link>
          <Button onClick={() => setShowNew(!showNew)}>
            <Plus className="mr-2 h-4 w-4" />
            New Campaign
          </Button>
        </div>
      </div>

      {analytics && (
        <div className="grid gap-4 sm:grid-cols-4">
          <div className="rounded-lg border bg-card p-4">
            <p className="text-[11px] text-muted-foreground uppercase">Campaigns</p>
            <p className="text-xl font-bold">{analytics.total_campaigns}</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-[11px] text-muted-foreground uppercase">Sent</p>
            <p className="text-xl font-bold">{analytics.total_sent.toLocaleString()}</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-[11px] text-muted-foreground uppercase">Open Rate</p>
            <p className="text-xl font-bold">{analytics.avg_open_rate.toFixed(1)}%</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-[11px] text-muted-foreground uppercase">Click Rate</p>
            <p className="text-xl font-bold">{analytics.avg_click_rate.toFixed(1)}%</p>
          </div>
        </div>
      )}

      {showNew && (
        <div className="rounded-lg border bg-card p-4 space-y-3">
          <h3 className="text-sm font-medium">New Email Campaign</h3>
          <label htmlFor="email-campaign-name" className="text-xs font-medium text-muted-foreground">Campaign name</label>
          <Input
            id="email-campaign-name"
            placeholder="Campaign name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <label htmlFor="email-campaign-subject" className="text-xs font-medium text-muted-foreground">Subject</label>
          <Input
            id="email-campaign-subject"
            placeholder="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          />
          <label htmlFor="email-campaign-body" className="text-xs font-medium text-muted-foreground">Email body</label>
          <Textarea
            id="email-campaign-body"
            placeholder="Email body (plain text or HTML)"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={4}
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="email-campaign-provider" className="text-xs font-medium text-muted-foreground">Provider</label>
              <Select
                id="email-campaign-provider"
                value={providerId}
                onChange={(e) => {
                  setProviderId(e.target.value);
                  const p = providers?.find((pr) => pr.id === e.target.value);
                  if (p) setFromEmail(p.from_email);
                }}
                placeholder="Select provider"
                options={(providers || []).map((p) => ({ value: p.id, label: `${p.name} (${p.provider_type})` }))}
              />
            </div>
            <div>
              <label htmlFor="email-campaign-from" className="text-xs font-medium text-muted-foreground">From email</label>
              <Input
                id="email-campaign-from"
                type="email"
                placeholder="From email"
                value={fromEmail}
                onChange={(e) => setFromEmail(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              disabled={createCampaign.isPending || !name || !subject || !body || !providerId}
              onClick={async () => {
                await createCampaign.mutateAsync({
                  organization_id: orgId,
                  provider_id: providerId,
                  name,
                  subject,
                  body,
                  from_email: fromEmail,
                });
                setShowNew(false);
                setName('');
                setSubject('');
                setBody('');
                setProviderId('');
                setFromEmail('');
              }}
            >
              {createCampaign.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : null}
              Create
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowNew(false)}>Cancel</Button>
          </div>
        </div>
      )}

      <div className="flex gap-2 border-b pb-2">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={cn(
              'rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
              status === s ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent',
            )}
          >
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : campaigns && campaigns.length > 0 ? (
        <div className="rounded-lg border divide-y">
          {campaigns.map((c) => (
            <div key={c.id} className="flex items-start gap-4 px-4 py-3 hover:bg-accent/30 transition-colors">
              <Mail className="mt-1 h-4 w-4 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{c.name}</span>
                  <span className={cn('rounded-full px-2 py-0.5 text-[10px] font-medium', STATUS_COLORS[c.status])}>
                    {c.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{c.subject}</p>
                <div className="flex items-center gap-3 mt-1 text-[11px] text-muted-foreground">
                  <span>Sent: {c.sent_count}</span>
                  <span>Opens: {c.open_count}</span>
                  <span>Clicks: {c.click_count}</span>
                  {c.bounce_count > 0 && <span className="text-red-500">Bounces: {c.bounce_count}</span>}
                  {c.scheduled_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(c.scheduled_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-1 shrink-0">
                {c.status === 'draft' && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs"
                      onClick={() => {
                        const r = prompt('Enter recipient emails (comma-separated)');
                        if (r) {
                          sendCampaign.mutate({
                            campaign_id: c.id,
                            recipients: r.split(',').map((e) => e.trim()),
                          });
                        }
                      }}
                    >
                      <Send className="mr-1 h-3 w-3" />
                      Send
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-xs text-red-500"
                      onClick={() => deleteCampaign.mutate(c.id)}
                    >
                      Delete
                    </Button>
                  </>
                )}
                {c.status === 'sent' && (
                  <Link href={`/email/campaigns/${c.id}`}>
                    <Button size="sm" variant="ghost" className="h-7 text-xs">
                      <BarChart3 className="mr-1 h-3 w-3" />
                      Stats
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Mail className="h-12 w-12 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No email campaigns yet</p>
          <p className="text-sm text-muted-foreground">
            Create your first email campaign to get started
          </p>
          <Button variant="outline" onClick={() => setShowNew(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Campaign
          </Button>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
