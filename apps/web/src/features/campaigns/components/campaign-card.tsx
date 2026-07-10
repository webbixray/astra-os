import type { Campaign } from '../types';
import { cn } from '@/lib/utils';
import { CAMPAIGN_STATUS_COLORS } from '@/lib/constants';

const statusColors = CAMPAIGN_STATUS_COLORS;

interface CampaignCardProps {
  campaign: Campaign;
}

export function CampaignCard({ campaign }: CampaignCardProps) {
  return (
    <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm transition-colors hover:bg-accent/50">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-1">
          <h3 className="font-medium leading-none">{campaign.name}</h3>
          {campaign.description && (
            <p className="text-sm text-muted-foreground line-clamp-1">
              {campaign.description}
            </p>
          )}
        </div>
        <span
          className={cn(
            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
            statusColors[campaign.status],
          )}
        >
          {campaign.status.replace('_', ' ')}
        </span>
      </div>
      <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
        {campaign.budget_amount && (
          <span>
            {campaign.budget_currency} {campaign.budget_amount.toLocaleString()}
          </span>
        )}
        {campaign.channels.length > 0 && (
          <span>{campaign.channels.join(', ')}</span>
        )}
        {campaign.objective && <span>{campaign.objective}</span>}
      </div>
    </div>
  );
}
