'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
  scopes: string[];
}

interface ApiKeyManagerProps {
  keys: ApiKey[];
  onRefresh: () => void;
}

export function ApiKeyManager({ keys, onRefresh }: ApiKeyManagerProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyScopes, setNewKeyScopes] = useState(['read']);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await api.post<{ key: string }>('/api-keys', {
        name: newKeyName,
        scopes: newKeyScopes,
      });
      setCreatedKey(result.key);
      setNewKeyName('');
      setNewKeyScopes(['read']);
      onRefresh();
    } catch {
      alert('Failed to create API key');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    try {
      await api.delete(`/api-keys/${keyId}`);
      onRefresh();
    } catch {
      alert('Failed to delete API key');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
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
          <h3 className="text-lg font-medium">API Keys</h3>
          <p className="text-sm text-muted-foreground">
            Manage API keys for programmatic access to your account
          </p>
        </div>
        <Button onClick={() => setIsCreating(true)}>Create API Key</Button>
      </div>

      {createdKey && (
        <div className="rounded-lg border border-green-500/50 bg-green-50 p-4 dark:bg-green-950">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-medium text-green-900 dark:text-green-100">
                API Key Created
              </h4>
              <p className="mt-1 text-sm text-green-700 dark:text-green-300">
                Make sure to copy your API key now. You won&apos;t be able to see it again.
              </p>
              <div className="mt-3 flex items-center gap-2">
                <code className="rounded bg-green-100 px-2 py-1 text-sm dark:bg-green-900">
                  {createdKey}
                </code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(createdKey)}
                >
                  Copy
                </Button>
              </div>
            </div>
            <button
              onClick={() => setCreatedKey(null)}
              className="text-green-500 hover:text-green-700"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {isCreating && !createdKey && (
        <form onSubmit={handleCreate} className="rounded-lg border p-4">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="key-name">Key Name</Label>
              <Input
                id="key-name"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production API Key"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Permissions</Label>
              <div className="flex gap-4">
                {['read', 'write', 'admin'].map((scope) => (
                  <label key={scope} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={newKeyScopes.includes(scope)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewKeyScopes([...newKeyScopes, scope]);
                        } else {
                          setNewKeyScopes(newKeyScopes.filter((s) => s !== scope));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm capitalize">{scope}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create'}
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
        {keys.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-muted-foreground">No API keys yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Create an API key to access your account programmatically
            </p>
          </div>
        ) : (
          keys.map((key) => (
            <div
              key={key.id}
              className="flex items-center justify-between rounded-lg border p-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{key.name}</span>
                  <span className="rounded bg-muted px-2 py-0.5 text-xs">
                    {key.key_prefix}...
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>Created: {formatDate(key.created_at)}</span>
                  {key.last_used_at && (
                    <span>Last used: {formatDate(key.last_used_at)}</span>
                  )}
                  {key.expires_at && (
                    <span>Expires: {formatDate(key.expires_at)}</span>
                  )}
                </div>
                <div className="flex gap-1">
                  {key.scopes.map((scope) => (
                    <span
                      key={scope}
                      className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                    >
                      {scope}
                    </span>
                  ))}
                </div>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleDelete(key.id)}
              >
                Delete
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
