'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';

interface Webhook {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  created_at: string;
  last_triggered_at: string | null;
  secret: string;
}

interface WebhookManagerProps {
  webhooks: Webhook[];
  onRefresh: () => void;
}

const AVAILABLE_EVENTS = [
  { value: 'campaign.created', label: 'Campaign Created' },
  { value: 'campaign.updated', label: 'Campaign Updated' },
  { value: 'campaign.completed', label: 'Campaign Completed' },
  { value: 'content.published', label: 'Content Published' },
  { value: 'content.generated', label: 'Content Generated' },
  { value: 'team.member_added', label: 'Team Member Added' },
  { value: 'team.member_removed', label: 'Team Member Removed' },
  { value: 'ad.spend_alert', label: 'Ad Spend Alert' },
];

export function WebhookManager({ webhooks, onRefresh }: WebhookManagerProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [newWebhook, setNewWebhook] = useState({
    url: '',
    events: [] as string[],
  });
  const [loading, setLoading] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.post('/webhooks', newWebhook);
      setNewWebhook({ url: '', events: [] });
      setIsCreating(false);
      onRefresh();
    } catch {
      alert('Failed to create webhook');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (webhookId: string) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return;

    try {
      await api.delete(`/webhooks/${webhookId}`);
      onRefresh();
    } catch {
      alert('Failed to delete webhook');
    }
  };

  const handleToggle = async (webhookId: string, active: boolean) => {
    try {
      await api.patch(`/webhooks/${webhookId}`, { active: !active });
      onRefresh();
    } catch {
      alert('Failed to update webhook');
    }
  };

  const handleTest = async (webhookId: string) => {
    try {
      const result = await api.post<{ success: boolean }>(`/webhooks/${webhookId}/test`);
      if (result.success) {
        alert('Webhook test successful!');
      } else {
        alert('Webhook test failed');
      }
    } catch {
      alert('Failed to test webhook');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Webhooks</h3>
          <p className="text-sm text-muted-foreground">
            Receive notifications when events happen in your account
          </p>
        </div>
        <Button onClick={() => setIsCreating(true)}>Add Webhook</Button>
      </div>

      {isCreating && (
        <form onSubmit={handleCreate} className="rounded-lg border p-4">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="webhook-url">Endpoint URL</Label>
              <Input
                id="webhook-url"
                value={newWebhook.url}
                onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                placeholder="https://your-server.com/webhook"
                required
              />
              <p className="text-xs text-muted-foreground">
                We&apos;ll send a POST request to this URL with event data
              </p>
            </div>
            <div className="space-y-2">
              <Label>Events</Label>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_EVENTS.map((event) => (
                  <label key={event.value} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={newWebhook.events.includes(event.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewWebhook({
                            ...newWebhook,
                            events: [...newWebhook.events, event.value],
                          });
                        } else {
                          setNewWebhook({
                            ...newWebhook,
                            events: newWebhook.events.filter((ev) => ev !== event.value),
                          });
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">{event.label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create Webhook'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreating(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </form>
      )}

      <div className="space-y-3">
        {webhooks.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-muted-foreground">No webhooks configured</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Add a webhook to receive notifications about events
            </p>
          </div>
        ) : (
          webhooks.map((webhook) => (
            <div
              key={webhook.id}
              className="flex items-center justify-between rounded-lg border p-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      webhook.active ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                  />
                  <span className="font-mono text-sm">{webhook.url}</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>Created: {formatDate(webhook.created_at)}</span>
                  {webhook.last_triggered_at && (
                    <span>Last triggered: {formatDate(webhook.last_triggered_at)}</span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1">
                  {webhook.events.map((event) => (
                    <span
                      key={event}
                      className="rounded-full bg-muted px-2 py-0.5 text-xs"
                    >
                      {event}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleTest(webhook.id)}
                >
                  Test
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleToggle(webhook.id, webhook.active)}
                >
                  {webhook.active ? 'Disable' : 'Enable'}
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(webhook.id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
