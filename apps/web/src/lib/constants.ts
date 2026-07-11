export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const muted = 'bg-muted text-muted-foreground';

export const CAMPAIGN_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  pending_approval: 'bg-yellow-500/10 text-yellow-500',
  active: 'bg-green-500/10 text-green-500',
  paused: 'bg-blue-500/10 text-blue-500',
  completed: muted,
  archived: muted,
};

export const CONTENT_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  review: 'bg-yellow-500/10 text-yellow-500',
  approved: 'bg-green-500/10 text-green-500',
  published: 'bg-blue-500/10 text-blue-500',
  archived: muted,
};

export const WORKFLOW_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  active: 'bg-green-500/10 text-green-500',
  paused: 'bg-blue-500/10 text-blue-500',
  completed: muted,
  archived: muted,
};

export const AD_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  active: 'bg-green-500/10 text-green-500',
  paused: 'bg-yellow-500/10 text-yellow-500',
  completed: 'bg-blue-500/10 text-blue-500',
  archived: muted,
};

export const EMAIL_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  scheduled: 'bg-blue-500/10 text-blue-500',
  sending: 'bg-yellow-500/10 text-yellow-500',
  sent: 'bg-green-500/10 text-green-500',
  partially_sent: 'bg-orange-500/10 text-orange-500',
  failed: 'bg-red-500/10 text-red-500',
};

export const JOB_STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-500/10 text-green-500',
  running: 'bg-blue-500/10 text-blue-500',
  queued: 'bg-yellow-500/10 text-yellow-500',
  failed: 'bg-red-500/10 text-red-500',
  cancelled: muted,
};

export const REPORT_STATUS_COLORS: Record<string, string> = {
  delivered: 'bg-green-500/10 text-green-500',
  failed: 'bg-red-500/10 text-red-500',
  pending: 'bg-yellow-500/10 text-yellow-500',
};

export const CREATIVE_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  approved: 'bg-green-500/10 text-green-500',
  rejected: 'bg-red-500/10 text-red-500',
  active: 'bg-blue-500/10 text-blue-500',
};

export const AB_TEST_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  running: 'bg-green-500/10 text-green-500',
  completed: 'bg-blue-500/10 text-blue-500',
  archived: muted,
};

export const NOTIFICATION_TYPE_ICONS: Record<string, string> = {
  campaign: 'megaphone',
  content: 'file-text',
  workflow: 'git-branch',
  analytics: 'bar-chart-3',
  system: 'settings',
  billing: 'credit-card',
};

export function getStatusColor(status: string, domain?: string): string {
  const maps: Record<string, Record<string, string>> = {
    campaign: CAMPAIGN_STATUS_COLORS,
    content: CONTENT_STATUS_COLORS,
    workflow: WORKFLOW_STATUS_COLORS,
    ad: AD_STATUS_COLORS,
    email: EMAIL_STATUS_COLORS,
    job: JOB_STATUS_COLORS,
    report: REPORT_STATUS_COLORS,
    creative: CREATIVE_STATUS_COLORS,
    ab_test: AB_TEST_STATUS_COLORS,
  };

  if (domain && maps[domain]) {
    return maps[domain][status] || muted;
  }

  for (const map of Object.values(maps)) {
    if (status in map) return map[status];
  }
  return muted;
}
