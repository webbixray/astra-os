'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { StatusBadge } from '@/components/status-indicator';
import { EmptyCampaignState } from '@/components/empty-state';
import { cn } from '@/lib/utils';

interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  type: 'email' | 'social' | 'ads' | 'content';
  startDate: string;
  endDate?: string;
  budget: number;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
}

interface CampaignCardProps {
  campaign: Campaign;
  onEdit?: (campaign: Campaign) => void;
  onDelete?: (campaign: Campaign) => void;
  onDuplicate?: (campaign: Campaign) => void;
  className?: string;
}

export function CampaignCard({ campaign, onEdit, onDelete, onDuplicate, className }: CampaignCardProps) {
  const roi = campaign.spent > 0 ? ((campaign.revenue - campaign.spent) / campaign.spent) * 100 : 0;
  const ctr = campaign.impressions > 0 ? (campaign.clicks / campaign.impressions) * 100 : 0;
  const conversionRate = campaign.clicks > 0 ? (campaign.conversions / campaign.clicks) * 100 : 0;

  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg">{campaign.name}</CardTitle>
            <CardDescription className="flex items-center gap-2">
              <span className="capitalize">{campaign.type}</span>
              <span>·</span>
              <span>{new Date(campaign.startDate).toLocaleDateString()}</span>
            </CardDescription>
          </div>
          <StatusBadge status={campaign.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-gray-500">Budget</div>
            <div className="font-medium">
              ${campaign.spent.toLocaleString()} / ${campaign.budget.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-gray-500">ROI</div>
            <div className={cn('font-medium', roi >= 0 ? 'text-green-600' : 'text-red-600')}>
              {roi >= 0 ? '+' : ''}{roi.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-gray-500">CTR</div>
            <div className="font-medium">{ctr.toFixed(2)}%</div>
          </div>
          <div>
            <div className="text-gray-500">Conversions</div>
            <div className="font-medium">{campaign.conversions.toLocaleString()}</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-xs text-gray-500">
            <span>Budget spent</span>
            <span>{Math.round((campaign.spent / campaign.budget) * 100)}%</span>
          </div>
          <Progress value={campaign.spent} max={campaign.budget} size="sm" />
        </div>

        <div className="flex gap-2 pt-2">
          <Button asChild variant="outline" size="sm" className="flex-1">
            <Link href={`/campaigns/${campaign.id}`}>View Details</Link>
          </Button>
          {onEdit && (
            <Button variant="ghost" size="sm" onClick={() => onEdit(campaign)}>
              Edit
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface CampaignListProps {
  campaigns: Campaign[];
  onCreateCampaign?: () => void;
  onEdit?: (campaign: Campaign) => void;
  onDelete?: (campaign: Campaign) => void;
  className?: string;
}

export function CampaignList({ campaigns, onCreateCampaign, onEdit, onDelete, className }: CampaignListProps) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const filteredCampaigns = campaigns.filter((campaign) => {
    const matchesSearch = campaign.name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || campaign.status === statusFilter;
    const matchesType = typeFilter === 'all' || campaign.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  if (campaigns.length === 0) {
    return <EmptyCampaignState onCreateCampaign={onCreateCampaign} />;
  }

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-2xl font-bold">Campaigns</h2>
        {onCreateCampaign && (
          <Button onClick={onCreateCampaign}>
            <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Campaign
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          placeholder="Search campaigns..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:w-[300px]"
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="email">Email</SelectItem>
            <SelectItem value="social">Social</SelectItem>
            <SelectItem value="ads">Ads</SelectItem>
            <SelectItem value="content">Content</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredCampaigns.map((campaign) => (
          <CampaignCard
            key={campaign.id}
            campaign={campaign}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>

      {filteredCampaigns.length === 0 && (
        <div className="py-12 text-center text-gray-500">
          No campaigns match your filters.
        </div>
      )}
    </div>
  );
}

interface CampaignStatsProps {
  stats: {
    totalCampaigns: number;
    activeCampaigns: number;
    totalSpent: number;
    totalRevenue: number;
    avgROI: number;
    avgCTR: number;
  };
  className?: string;
}

export function CampaignStats({ stats, className }: CampaignStatsProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Campaign Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-6 md:grid-cols-3">
          <div className="space-y-1">
            <div className="text-sm text-gray-500">Total Campaigns</div>
            <div className="text-2xl font-bold">{stats.totalCampaigns}</div>
          </div>
          <div className="space-y-1">
            <div className="text-sm text-gray-500">Active</div>
            <div className="text-2xl font-bold text-green-600">{stats.activeCampaigns}</div>
          </div>
          <div className="space-y-1">
            <div className="text-sm text-gray-500">Total Spent</div>
            <div className="text-2xl font-bold">${stats.totalSpent.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="text-sm text-gray-500">Total Revenue</div>
            <div className="text-2xl font-bold text-green-600">${stats.totalRevenue.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="text-sm text-gray-500">Average ROI</div>
            <div className={cn('text-2xl font-bold', stats.avgROI >= 0 ? 'text-green-600' : 'text-red-600')}>
              {stats.avgROI >= 0 ? '+' : ''}{stats.avgROI.toFixed(1)}%
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-sm text-gray-500">Average CTR</div>
            <div className="text-2xl font-bold">{stats.avgCTR.toFixed(2)}%</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
