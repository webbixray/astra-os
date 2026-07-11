'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';

interface Integration {
  id: string;
  name: string;
  description: string;
  category: 'advertising' | 'analytics' | 'crm' | 'email' | 'social' | 'ecommerce' | 'other';
  icon: string;
  logo?: string;
  status: 'connected' | 'available' | 'coming_soon';
  popular?: boolean;
  features?: string[];
  connectedAt?: string;
}

interface IntegrationCardProps {
  integration: Integration;
  onConnect?: (integration: Integration) => void;
  onDisconnect?: (integration: Integration) => void;
  onConfigure?: (integration: Integration) => void;
  className?: string;
}

export function IntegrationCard({ integration, onConnect, onDisconnect, onConfigure, className }: IntegrationCardProps) {
  const categoryColors: Record<Integration['category'], string> = {
    advertising: 'bg-red-100 text-red-800',
    analytics: 'bg-blue-100 text-blue-800',
    crm: 'bg-green-100 text-green-800',
    email: 'bg-purple-100 text-purple-800',
    social: 'bg-pink-100 text-pink-800',
    ecommerce: 'bg-orange-100 text-orange-800',
    other: 'bg-gray-100 text-gray-800',
  };

  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-800">
              <span className="text-2xl">{integration.icon}</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg">{integration.name}</CardTitle>
                {integration.popular && (
                  <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 text-xs">
                    Popular
                  </Badge>
                )}
              </div>
              <Badge variant="secondary" className={cn('text-xs capitalize', categoryColors[integration.category])}>
                {integration.category}
              </Badge>
            </div>
          </div>
          {integration.status === 'connected' && (
            <Badge variant="default" className="bg-green-100 text-green-800">
              Connected
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">{integration.description}</p>

        {integration.features && integration.features.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {integration.features.map((feature) => (
              <Badge key={feature} variant="outline" className="text-xs">
                {feature}
              </Badge>
            ))}
          </div>
        )}

        <div className="flex gap-2 pt-2">
          {integration.status === 'connected' ? (
            <>
              <Button variant="outline" size="sm" className="flex-1" onClick={() => onConfigure?.(integration)}>
                Configure
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDisconnect?.(integration)}
                className="text-red-600"
              >
                Disconnect
              </Button>
            </>
          ) : integration.status === 'available' ? (
            <Button size="sm" className="flex-1" onClick={() => onConnect?.(integration)}>
              Connect
            </Button>
          ) : (
            <Button size="sm" disabled className="flex-1">
              Coming Soon
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface IntegrationListProps {
  integrations: Integration[];
  onConnect?: (integration: Integration) => void;
  onDisconnect?: (integration: Integration) => void;
  onConfigure?: (integration: Integration) => void;
  className?: string;
}

export function IntegrationList({ integrations, onConnect, onDisconnect, onConfigure, className }: IntegrationListProps) {
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredIntegrations = integrations.filter((integration) => {
    const matchesSearch =
      integration.name.toLowerCase().includes(search.toLowerCase()) ||
      integration.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || integration.category === categoryFilter;
    const matchesStatus = statusFilter === 'all' || integration.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const connectedCount = integrations.filter((i) => i.status === 'connected').length;

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold">Integrations</h2>
          <p className="text-sm text-gray-500">
            {connectedCount} connected · {integrations.length} available
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          placeholder="Search integrations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:w-[300px]"
        />
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="advertising">Advertising</SelectItem>
            <SelectItem value="analytics">Analytics</SelectItem>
            <SelectItem value="crm">CRM</SelectItem>
            <SelectItem value="email">Email</SelectItem>
            <SelectItem value="social">Social</SelectItem>
            <SelectItem value="ecommerce">E-commerce</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="connected">Connected</SelectItem>
            <SelectItem value="available">Available</SelectItem>
            <SelectItem value="coming_soon">Coming Soon</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredIntegrations.map((integration) => (
          <IntegrationCard
            key={integration.id}
            integration={integration}
            onConnect={onConnect}
            onDisconnect={onDisconnect}
            onConfigure={onConfigure}
          />
        ))}
      </div>

      {filteredIntegrations.length === 0 && (
        <div className="py-12 text-center text-gray-500">
          No integrations match your filters.
        </div>
      )}
    </div>
  );
}

interface ConnectedIntegrationsProps {
  integrations: Integration[];
  className?: string;
}

export function ConnectedIntegrations({ integrations, className }: ConnectedIntegrationsProps) {
  const connected = integrations.filter((i) => i.status === 'connected');

  if (connected.length === 0) return null;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Connected Integrations</CardTitle>
        <CardDescription>Your active integrations</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {connected.map((integration) => (
            <div key={integration.id} className="flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-3">
                <span className="text-xl">{integration.icon}</span>
                <div>
                  <div className="font-medium">{integration.name}</div>
                  <div className="text-xs text-gray-500">
                    Connected {integration.connectedAt && new Date(integration.connectedAt).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <Switch checked />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
