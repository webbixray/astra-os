export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const badge = (color: string) => `bg-${color}-500/10 text-${color}-500`;
const muted = 'bg-muted text-muted-foreground';

export const CAMPAIGN_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  pending_approval: badge('yellow'),
  active: badge('green'),
  paused: badge('blue'),
  completed: muted,
  archived: muted,
};

export const CONTENT_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  review: badge('yellow'),
  approved: badge('green'),
  published: badge('blue'),
  archived: muted,
};

export const WORKFLOW_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  active: badge('green'),
  paused: badge('blue'),
  completed: muted,
  archived: muted,
};

export const AD_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  active: badge('green'),
  paused: badge('yellow'),
  completed: badge('blue'),
  archived: muted,
};

export const EMAIL_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  scheduled: badge('blue'),
  sending: badge('yellow'),
  sent: badge('green'),
  partially_sent: badge('orange'),
  failed: badge('red'),
};

export const JOB_STATUS_COLORS: Record<string, string> = {
  completed: badge('green'),
  running: badge('blue'),
  queued: badge('yellow'),
  failed: badge('red'),
  cancelled: muted,
};

export const REPORT_STATUS_COLORS: Record<string, string> = {
  delivered: badge('green'),
  failed: badge('red'),
  pending: badge('yellow'),
};

export const CREATIVE_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  approved: badge('green'),
  rejected: badge('red'),
  active: badge('blue'),
};

export const AB_TEST_STATUS_COLORS: Record<string, string> = {
  draft: muted,
  running: badge('green'),
  completed: badge('blue'),
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
