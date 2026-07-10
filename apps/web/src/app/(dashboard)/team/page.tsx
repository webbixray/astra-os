'use client';

import { useState } from 'react';
import { Users, UserPlus, Trash2, Shield, Mail, X, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import {
  useMembers,
  useInvitations,
  useInviteMember,
  useCancelInvitation,
  useChangeMemberRole,
  useRemoveMember,
} from '@/features/organizations/api/useOrganizations';
import { useOrg } from '@/lib/org';
import { ErrorBoundary } from '@/components/ui/error-boundary';

const ROLE_COLORS: Record<string, string> = {
  owner: 'bg-amber-500/10 text-amber-500',
  admin: 'bg-blue-500/10 text-blue-500',
  member: 'bg-emerald-500/10 text-emerald-500',
  viewer: 'bg-muted text-muted-foreground',
};

const INVITE_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-500/10 text-yellow-500',
  accepted: 'bg-green-500/10 text-green-500',
  rejected: 'bg-red-500/10 text-red-500',
  expired: 'bg-muted text-muted-foreground',
};

export default function TeamPage() {
  const { orgId } = useOrg();
  const { data: members, isLoading } = useMembers(orgId);
  const { data: invitations } = useInvitations(orgId);
  const inviteMember = useInviteMember();
  const cancelInvitation = useCancelInvitation();
  const changeRole = useChangeMemberRole();
  const removeMember = useRemoveMember();

  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');

  const handleInvite = () => {
    if (!inviteEmail.trim()) return;
    inviteMember.mutate(
      { orgId, email: inviteEmail.trim(), role: inviteRole },
      { onSuccess: () => { setShowInvite(false); setInviteEmail(''); setInviteRole('member'); } },
    );
  };

  return (
    <ErrorBoundary>
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="h-6 w-6" />
          <div>
            <h1 className="text-2xl font-semibold">Team</h1>
            <p className="text-sm text-muted-foreground">Manage your team members and invitations</p>
          </div>
        </div>
        <Button onClick={() => setShowInvite(!showInvite)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Invite Member
        </Button>
      </div>

      {showInvite && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex flex-col gap-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Email address"
                className="pl-10"
                aria-label="Email address"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <Select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              options={[
                { value: 'admin', label: 'Admin' },
                { value: 'member', label: 'Member' },
                { value: 'viewer', label: 'Viewer' },
              ]}
            />
            <div className="flex gap-2">
              <Button onClick={handleInvite} disabled={!inviteEmail}>Send Invite</Button>
              <Button variant="ghost" onClick={() => setShowInvite(false)}>Cancel</Button>
            </div>
          </div>
        </div>
      )}

      {/* Members */}
      <div className="rounded-lg border bg-card">
        <div className="border-b px-6 py-3">
          <h2 className="text-sm font-medium">Members ({members?.length ?? 0})</h2>
        </div>
        {isLoading ? (
          <div className="p-6 text-center text-sm text-muted-foreground">Loading...</div>
        ) : (
          <>
            <div className="grid grid-cols-12 gap-4 border-b px-6 py-3 text-xs font-medium text-muted-foreground">
              <div className="col-span-3">Name</div>
              <div className="col-span-3">Email</div>
              <div className="col-span-2">Role</div>
              <div className="col-span-2">Joined</div>
              <div className="col-span-2" />
            </div>
            {members?.map((member) => (
              <div key={member.id} className="grid grid-cols-12 gap-4 border-b px-6 py-4 text-sm last:border-0 items-center">
                <div className="col-span-3 flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-medium">
                    {member.name ? member.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() : '?'}
                  </div>
                  <span className="font-medium">{member.name}</span>
                </div>
                <div className="col-span-3 text-muted-foreground">{member.email}</div>
                <div className="col-span-2">
                  <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', ROLE_COLORS[member.role])}>
                    <Shield className="mr-1 h-3 w-3" />
                    {member.role}
                  </span>
                </div>
                <div className="col-span-2 text-muted-foreground text-xs">
                  {member.joined_at ? new Date(member.joined_at).toLocaleDateString() : '—'}
                </div>
                <div className="col-span-2 flex items-center justify-end gap-1">
                  {member.role !== 'owner' && (
                    <>
                      <Select
                        value={member.role}
                        onChange={(e) => changeRole.mutate({ orgId, memberId: member.id, role: e.target.value })}
                        options={[
                          { value: 'admin', label: 'Admin' },
                          { value: 'member', label: 'Member' },
                          { value: 'viewer', label: 'Viewer' },
                        ]}
                        className="h-8 text-xs"
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-red-500"
                        aria-label="Delete"
                        onClick={() => removeMember.mutate({ orgId, memberId: member.id })}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
            {(!members || members.length === 0) && (
              <div className="p-6 text-center text-sm text-muted-foreground">No members yet</div>
            )}
          </>
        )}
      </div>

      {/* Pending Invitations */}
      {invitations && invitations.length > 0 && (
        <div className="rounded-lg border bg-card">
          <div className="border-b px-6 py-3">
            <h2 className="text-sm font-medium">Pending Invitations ({invitations.length})</h2>
          </div>
          <div className="grid grid-cols-12 gap-4 border-b px-6 py-3 text-xs font-medium text-muted-foreground">
            <div className="col-span-4">Email</div>
            <div className="col-span-2">Role</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2">Sent</div>
            <div className="col-span-2" />
          </div>
          {invitations.map((inv) => (
            <div key={inv.id} className="grid grid-cols-12 gap-4 border-b px-6 py-4 text-sm last:border-0 items-center">
              <div className="col-span-4 font-medium">{inv.email}</div>
              <div className="col-span-2 capitalize">{inv.role}</div>
              <div className="col-span-2">
                <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', INVITE_STATUS_COLORS[inv.status])}>
                  <Clock className="mr-1 h-3 w-3" />
                  {inv.status}
                </span>
              </div>
              <div className="col-span-2 text-muted-foreground text-xs">
                {new Date(inv.created_at).toLocaleDateString()}
              </div>
              <div className="col-span-2 flex justify-end">
                {inv.status === 'pending' && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-red-500"
                    aria-label="Close"
                    onClick={() => cancelInvitation.mutate({ orgId, invitationId: inv.id })}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}
