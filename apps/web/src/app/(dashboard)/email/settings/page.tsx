'use client';

import { useState } from 'react';
import { Plus, Loader2, Server, Trash2, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  useEmailProviders,
  useCreateEmailProvider,
  useDeleteEmailProvider,
} from '@/features/email/api/useEmail';
import { PROVIDER_TYPES } from '@/features/email/types';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

export default function EmailSettingsPage() {
  const { orgId } = useOrg();
  const { data: providers, isLoading } = useEmailProviders(orgId);
  const createProvider = useCreateEmailProvider();
  const deleteProvider = useDeleteEmailProvider();

  const [showNew, setShowNew] = useState(false);
  const [providerType, setProviderType] = useState('sendgrid');
  const [name, setName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [fromEmail, setFromEmail] = useState('');
  const [fromName, setFromName] = useState('');

  const handleCreate = async () => {
    await createProvider.mutateAsync({
      organization_id: orgId,
      provider_type: providerType,
      name,
      api_key: apiKey,
      from_email: fromEmail,
      from_name: fromName,
    });
    setShowNew(false);
    setName('');
    setApiKey('');
    setFromEmail('');
    setFromName('');
  };

  return (
    <ErrorBoundary>
    <div className="mx-auto max-w-3xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Email Provider Settings</h1>
          <p className="text-sm text-muted-foreground">
            Configure your email sending providers
          </p>
        </div>
        <Button onClick={() => setShowNew(!showNew)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Provider
        </Button>
      </div>

      {showNew && (
        <div className="rounded-lg border bg-card p-4 space-y-3">
          <h3 className="text-sm font-medium">New Email Provider</h3>
          <div>
            <label htmlFor="provider-type" className="text-xs font-medium text-muted-foreground">Provider type</label>
            <Select
              id="provider-type"
              value={providerType}
              onChange={(e) => setProviderType(e.target.value)}
              options={PROVIDER_TYPES.map((t) => ({ value: t, label: t.toUpperCase() }))}
            />
          </div>
          <div>
            <label htmlFor="provider-name" className="text-xs font-medium text-muted-foreground">Provider name</label>
            <Input
              id="provider-name"
              placeholder="Provider name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="provider-api-key" className="text-xs font-medium text-muted-foreground">API Key</label>
            <Input
              id="provider-api-key"
              type="password"
              placeholder="API Key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="provider-from-email" className="text-xs font-medium text-muted-foreground">From email</label>
            <Input
              id="provider-from-email"
              type="email"
              placeholder="From email"
              value={fromEmail}
              onChange={(e) => setFromEmail(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="provider-from-name" className="text-xs font-medium text-muted-foreground">From name</label>
            <Input
              id="provider-from-name"
              placeholder="From name (optional)"
              value={fromName}
              onChange={(e) => setFromName(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              disabled={createProvider.isPending || !name || !apiKey || !fromEmail}
              onClick={handleCreate}
            >
              {createProvider.isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
              Save
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowNew(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : providers && providers.length > 0 ? (
        <div className="space-y-2">
          {providers.map((p) => (
            <div key={p.id} className="flex items-center gap-4 rounded-lg border bg-card p-4">
              <Server className="h-5 w-5 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{p.name}</span>
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] uppercase">
                    {p.provider_type}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {p.from_email}{p.from_name ? ` (${p.from_name})` : ''}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {p.is_verified ? (
                  <span className="flex items-center gap-1 text-xs text-green-500">
                    <CheckCircle2 className="h-3 w-3" /> Verified
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-yellow-500">
                    <XCircle className="h-3 w-3" /> Unverified
                  </span>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 w-7 p-0 text-muted-foreground hover:text-red-500"
                  onClick={() => deleteProvider.mutate(p.id)}
                  aria-label="Delete"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Server className="h-12 w-12 text-muted-foreground/40" />
          <p className="text-lg text-muted-foreground">No providers configured</p>
          <p className="text-sm text-muted-foreground">
            Add a SendGrid, SES, or SMTP provider to start sending emails
          </p>
          <Button variant="outline" onClick={() => setShowNew(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Provider
          </Button>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
