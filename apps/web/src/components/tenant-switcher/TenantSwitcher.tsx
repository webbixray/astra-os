'use client';

import { useEffect } from 'react';
import { ChevronDownIcon } from '@radix-ui/react-icons';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectIcon,
} from '@/components/ui/select';
import { Loader2, Building2, CheckIcon } from 'lucide-react';
import { useTenantStore, useCurrentTenantId } from '@/stores/tenant-store';
import type { OrganizationResponse } from '@/lib/api/generated';

interface TenantSwitcherProps {
  className?: string;
  showLabel?: boolean;
  compact?: boolean;
}

export function TenantSwitcher({
  className = '',
  showLabel = true,
  compact = false,
}: TenantSwitcherProps) {
  const {
    currentTenant: _currentTenant,
    availableTenants,
    isLoading,
    fetchTenants,
    switchTenant,
  } = useTenantStore();

  const currentTenantId = useCurrentTenantId();

  // Fetch tenants on mount
  useEffect(() => {
    if (availableTenants.length === 0 && !isLoading) {
      fetchTenants();
    }
  }, [availableTenants.length, isLoading, fetchTenants]);

  const handleTenantChange = (value: string) => {
    if (value && value !== currentTenantId) {
      switchTenant(value);
    }
  };

  if (compact) {
    return (
      <Select
        value={currentTenantId ?? ''}
        onValueChange={handleTenantChange}
        disabled={isLoading || availableTenants.length <= 1}
      >
        <SelectTrigger className="w-[200px] h-8">
          <SelectValue placeholder="Select tenant..." />
          <SelectIcon>
            <ChevronDownIcon className="h-4 w-4" />
          </SelectIcon>
        </SelectTrigger>
        <SelectContent>
          {isLoading ? (
            <SelectItem disabled value="__loading__">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading tenants...
            </SelectItem>
          ) : (
            <>
              {availableTenants.map((tenant) => (
                <SelectItem key={tenant.id} value={tenant.id}>
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <span>{tenant.name}</span>
                    {tenant.id === currentTenantId && (
                      <CheckIcon className="ml-auto h-4 w-4 text-primary" />
                    )}
                  </div>
                </SelectItem>
              ))}
            </>
          )}
        </SelectContent>
      </Select>
    );
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {showLabel && <span className="text-sm font-medium text-muted-foreground">Tenant:</span>}

      <Select
        value={currentTenantId ?? ''}
        onValueChange={handleTenantChange}
        disabled={isLoading || availableTenants.length <= 1}
      >
        <SelectTrigger className="w-[280px] h-9">
          <SelectValue placeholder="Select tenant..." />
          <SelectIcon>
            <ChevronDownIcon className="h-4 w-4" />
          </SelectIcon>
        </SelectTrigger>
        <SelectContent position="popper">
          {isLoading ? (
            <SelectItem disabled value="__loading__" className="flex items-center gap-2 px-2 py-3">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading tenants...
            </SelectItem>
          ) : availableTenants.length === 0 ? (
            <SelectItem disabled value="__no_tenants__" className="px-2 py-3 text-muted-foreground">
              No tenants available
            </SelectItem>
          ) : (
            <>
              {availableTenants.map((tenant) => (
                <SelectItem key={tenant.id} value={tenant.id}>
                  <div className="flex items-center gap-2 px-2 py-2">
                    <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{tenant.name}</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {tenant.slug} • {tenant.plan_tier}
                      </p>
                    </div>
                    {tenant.id === currentTenantId && (
                      <CheckIcon className="h-4 w-4 text-primary flex-shrink-0" />
                    )}
                  </div>
                </SelectItem>
              ))}
            </>
          )}
        </SelectContent>
      </Select>
    </div>
  );
}

// Simplified version for header usage
export function HeaderTenantSwitcher() {
  const { currentTenant: _currentTenant, availableTenants, isLoading, fetchTenants, switchTenant } =
    useTenantStore();
  const currentTenantId = useCurrentTenantId();

  useEffect(() => {
    if (availableTenants.length === 0 && !isLoading) {
      fetchTenants();
    }
  }, [availableTenants.length, isLoading, fetchTenants]);

  if (availableTenants.length <= 1 && !isLoading) {
    return null;
  }

  return (
    <div className="hidden md:flex items-center gap-2">
      <Select
        value={currentTenantId ?? ''}
        onValueChange={switchTenant}
        disabled={isLoading || availableTenants.length <= 1}
      >
        <SelectTrigger className="w-56 h-8 bg-background border-border">
          <SelectValue placeholder="Select tenant..." />
          <SelectIcon>
            <ChevronDownIcon className="h-4 w-4" />
          </SelectIcon>
        </SelectTrigger>
        <SelectContent>
          {isLoading ? (
            <SelectItem disabled value="__loading__" className="flex items-center gap-2 px-2 py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading...
            </SelectItem>
          ) : (
            availableTenants.map((tenant: OrganizationResponse) => (
              <SelectItem key={tenant.id} value={tenant.id} className="relative">
                <div className="flex items-center gap-2 px-2 py-2">
                  <span className="font-medium truncate">{tenant.name}</span>
                  {tenant.id === currentTenantId && (
                    <span className="absolute right-2 text-primary text-sm">✓</span>
                  )}
                </div>
              </SelectItem>
            ))
          )}
        </SelectContent>
      </Select>
    </div>
  );
}

export { useTenantStore, useCurrentTenantId } from '@/stores/tenant-store';
