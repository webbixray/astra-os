'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface Activity {
  id: string;
  type: 'campaign' | 'content' | 'analytics' | 'team' | 'system';
  action: string;
  description: string;
  timestamp: string;
  user?: string;
  metadata?: Record<string, unknown>;
}

const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'campaign',
    action: 'created',
    description: 'Created campaign "Summer Sale 2024"',
    timestamp: '2024-03-15T10:30:00Z',
    user: 'John Doe',
  },
  {
    id: '2',
    type: 'content',
    action: 'published',
    description: 'Published blog post "AI in Marketing"',
    timestamp: '2024-03-15T09:15:00Z',
    user: 'Jane Smith',
  },
  {
    id: '3',
    type: 'analytics',
    action: 'report_generated',
    description: 'Generated weekly analytics report',
    timestamp: '2024-03-15T08:00:00Z',
    user: 'System',
  },
  {
    id: '4',
    type: 'team',
    action: 'member_added',
    description: 'Added new team member bob@example.com',
    timestamp: '2024-03-14T16:45:00Z',
    user: 'Admin',
  },
  {
    id: '5',
    type: 'system',
    action: 'backup_completed',
    description: 'Database backup completed successfully',
    timestamp: '2024-03-14T03:00:00Z',
    user: 'System',
  },
];

const typeColors: Record<Activity['type'], string> = {
  campaign: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  content: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  analytics: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
  team: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
  system: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
};

export function ActivityLog() {
  const [filter, setFilter] = useState<string>('all');
  const [activities, setActivities] = useState<Activity[]>(mockActivities);

  const filteredActivities = filter === 'all'
    ? activities
    : activities.filter((a) => a.type === filter);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Activity Log</CardTitle>
            <CardDescription>Recent activity in your workspace</CardDescription>
          </div>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Activity</SelectItem>
              <SelectItem value="campaign">Campaigns</SelectItem>
              <SelectItem value="content">Content</SelectItem>
              <SelectItem value="analytics">Analytics</SelectItem>
              <SelectItem value="team">Team</SelectItem>
              <SelectItem value="system">System</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {filteredActivities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start gap-4 rounded-lg border p-4 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
            >
              <div className={cn('rounded-full px-2 py-1 text-xs font-medium', typeColors[activity.type])}>
                {activity.type}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">{activity.description}</p>
                <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                  <span>{activity.user}</span>
                  <span>·</span>
                  <span>{formatTimestamp(activity.timestamp)}</span>
                </div>
              </div>
            </div>
          ))}
          {filteredActivities.length === 0 && (
            <p className="py-8 text-center text-sm text-gray-500">
              No activity found for this filter.
            </p>
          )}
        </div>
        {filteredActivities.length > 0 && (
          <div className="mt-4 text-center">
            <Button variant="ghost" size="sm">
              Load More
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
