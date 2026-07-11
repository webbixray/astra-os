'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Avatar } from '@/components/avatar';
import { cn } from '@/lib/utils';

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer';
  avatar?: string;
  status: 'active' | 'invited' | 'inactive';
  lastActive?: string;
  campaigns?: number;
  content?: number;
}

interface TeamMemberCardProps {
  member: TeamMember;
  onEdit?: (member: TeamMember) => void;
  onRemove?: (member: TeamMember) => void;
  onResendInvite?: (member: TeamMember) => void;
  className?: string;
}

export function TeamMemberCard({ member, onEdit, onRemove, onResendInvite, className }: TeamMemberCardProps) {
  const roleColors: Record<TeamMember['role'], string> = {
    owner: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
    admin: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    editor: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    viewer: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  };

  const statusColors: Record<TeamMember['status'], string> = {
    active: 'bg-green-100 text-green-800',
    invited: 'bg-yellow-100 text-yellow-800',
    inactive: 'bg-gray-100 text-gray-800',
  };

  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Avatar src={member.avatar} alt={member.name} fallback={member.name.charAt(0)} />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{member.name}</span>
                <Badge variant="secondary" className={cn('text-xs', roleColors[member.role])}>
                  {member.role}
                </Badge>
              </div>
              <div className="text-sm text-gray-500">{member.email}</div>
              {member.lastActive && (
                <div className="text-xs text-gray-400">
                  Last active: {new Date(member.lastActive).toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={cn('text-xs', statusColors[member.status])}>
              {member.status}
            </Badge>
            {member.status === 'invited' && onResendInvite && (
              <Button variant="ghost" size="sm" onClick={() => onResendInvite(member)}>
                Resend
              </Button>
            )}
            {onEdit && (
              <Button variant="ghost" size="sm" onClick={() => onEdit(member)}>
                Edit
              </Button>
            )}
            {onRemove && member.role !== 'owner' && (
              <Button variant="ghost" size="sm" onClick={() => onRemove(member)} className="text-red-600 hover:text-red-700">
                Remove
              </Button>
            )}
          </div>
        </div>
        {(member.campaigns !== undefined || member.content !== undefined) && (
          <div className="mt-4 flex gap-6 border-t pt-4 text-sm">
            {member.campaigns !== undefined && (
              <div>
                <span className="text-gray-500">Campaigns: </span>
                <span className="font-medium">{member.campaigns}</span>
              </div>
            )}
            {member.content !== undefined && (
              <div>
                <span className="text-gray-500">Content: </span>
                <span className="font-medium">{member.content}</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface TeamListProps {
  members: TeamMember[];
  onInvite?: () => void;
  onEdit?: (member: TeamMember) => void;
  onRemove?: (member: TeamMember) => void;
  onResendInvite?: (member: TeamMember) => void;
  className?: string;
}

export function TeamList({ members, onInvite, onEdit, onRemove, onResendInvite, className }: TeamListProps) {
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');

  const filteredMembers = members.filter((member) => {
    const matchesSearch =
      member.name.toLowerCase().includes(search.toLowerCase()) ||
      member.email.toLowerCase().includes(search.toLowerCase());
    const matchesRole = roleFilter === 'all' || member.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold">Team Members</h2>
          <p className="text-sm text-gray-500">{members.length} members in your organization</p>
        </div>
        {onInvite && (
          <Button onClick={onInvite}>
            <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
            Invite Member
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          placeholder="Search members..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:w-[300px]"
        />
        <Select value={roleFilter} onValueChange={setRoleFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="owner">Owner</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="editor">Editor</SelectItem>
            <SelectItem value="viewer">Viewer</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-4">
        {filteredMembers.map((member) => (
          <TeamMemberCard
            key={member.id}
            member={member}
            onEdit={onEdit}
            onRemove={onRemove}
            onResendInvite={onResendInvite}
          />
        ))}
      </div>

      {filteredMembers.length === 0 && (
        <div className="py-12 text-center text-gray-500">
          No team members match your filters.
        </div>
      )}
    </div>
  );
}

interface TeamStatsProps {
  stats: {
    totalMembers: number;
    activeMembers: number;
    pendingInvites: number;
    roleDistribution: { role: string; count: number }[];
  };
  className?: string;
}

export function TeamStats({ stats, className }: TeamStatsProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Team Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.totalMembers}</div>
            <div className="text-sm text-gray-500">Total Members</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.activeMembers}</div>
            <div className="text-sm text-gray-500">Active</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{stats.pendingInvites}</div>
            <div className="text-sm text-gray-500">Pending</div>
          </div>
        </div>
        <div className="mt-6 space-y-3">
          {stats.roleDistribution.map((item) => (
            <div key={item.role} className="flex items-center justify-between">
              <span className="text-sm capitalize text-gray-600">{item.role}</span>
              <div className="flex items-center gap-2">
                <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                  <div
                    className="h-full rounded-full bg-blue-600"
                    style={{ width: `${(item.count / stats.totalMembers) * 100}%` }}
                  />
                </div>
                <span className="w-8 text-right text-sm text-gray-500">{item.count}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
