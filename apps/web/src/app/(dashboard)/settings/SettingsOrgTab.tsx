'use client';

import { useState } from 'react';
import { z } from 'zod';
import { Building2, ChevronDown, ChevronRight, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCreateSubOrg } from '@/features/organizations/api/useOrganizations';

const subOrgSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name is too long'),
  slug: z.string().min(1, 'Slug is required').regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'Slug must be lowercase alphanumeric with hyphens'),
});

interface SettingsOrgTabProps {
  orgId: string;
  orgTree: any;
}

export function SettingsOrgTab({ orgId, orgTree }: SettingsOrgTabProps) {
  const [showCreateSub, setShowCreateSub] = useState(false);
  const [subName, setSubName] = useState('');
  const [subSlug, setSubSlug] = useState('');
  const [subErrors, setSubErrors] = useState<{ name?: string; slug?: string }>({});
  const [expandedOrgs, setExpandedOrgs] = useState<Set<string>>(new Set());

  const createSubOrg = useCreateSubOrg();

  const toggleOrg = (id: string) => {
    setExpandedOrgs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleCreateSub = () => {
    const result = subOrgSchema.safeParse({ name: subName.trim(), slug: subSlug.trim() });
    if (!result.success) {
      const fieldErrors = result.error.flatten().fieldErrors;
      setSubErrors({
        name: fieldErrors.name?.[0],
        slug: fieldErrors.slug?.[0],
      });
      return;
    }
    setSubErrors({});
    createSubOrg.mutate(
      { orgId, name: result.data.name, slug: result.data.slug },
      { onSuccess: () => { setShowCreateSub(false); setSubName(''); setSubSlug(''); setSubErrors({}); } },
    );
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Organization Hierarchy</h2>
        <p className="text-sm text-muted-foreground">Manage parent/child orgs</p>
      </div>

      <div className="rounded-lg border bg-card p-4">
        {orgTree && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <button onClick={() => toggleOrg(orgTree.id)} className="cursor-pointer" aria-label="Toggle">
                {expandedOrgs.has(orgTree.id)
                  ? <ChevronDown className="h-4 w-4" />
                  : <ChevronRight className="h-4 w-4" />}
              </button>
              <Building2 className="h-4 w-4" />
              <span className="font-medium">{orgTree.name}</span>
              <span className="text-xs text-muted-foreground">({orgTree.plan_tier})</span>
            </div>
            {expandedOrgs.has(orgTree.id) && orgTree.children.length > 0 && (
              <div className="ml-6 space-y-1 border-l pl-4">
                {orgTree.children.map((child: any) => (
                  <div key={child.id} className="flex items-center gap-2 py-1 text-sm">
                    <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>{child.name}</span>
                    <span className="text-xs text-muted-foreground">({child.plan_tier})</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {showCreateSub ? (
          <div className="mt-4 space-y-3 rounded-md border p-3">
            <div className="space-y-1">
              <Input
                placeholder="Organization name"
                aria-label="Organization name"
                value={subName}
                onChange={(e) => { setSubName(e.target.value); setSubErrors((prev) => ({ ...prev, name: undefined })); }}
                error={subErrors.name}
              />
              {subErrors.name && <p className="text-xs text-destructive">{subErrors.name}</p>}
            </div>
            <div className="space-y-1">
              <Input
                placeholder="slug (e.g., my-org)"
                aria-label="Organization slug"
                value={subSlug}
                onChange={(e) => { setSubSlug(e.target.value); setSubErrors((prev) => ({ ...prev, slug: undefined })); }}
                error={subErrors.slug}
              />
              {subErrors.slug && <p className="text-xs text-destructive">{subErrors.slug}</p>}
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreateSub} disabled={createSubOrg.isPending}>
                Create Sub-Org
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setShowCreateSub(false)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button size="sm" variant="outline" className="mt-4" onClick={() => setShowCreateSub(true)}>
            <Plus className="mr-1 h-3.5 w-3.5" />
            Create Sub-Organization
          </Button>
        )}
      </div>

      <div className="rounded-lg border bg-card p-4">
        <h3 className="text-sm font-medium mb-2">Current Organization</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span>{orgTree?.name ?? '—'}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Slug</span><span>{orgTree?.slug ?? '—'}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Plan</span><span className="capitalize">{orgTree?.plan_tier ?? '—'}</span></div>
        </div>
      </div>
    </div>
  );
}
