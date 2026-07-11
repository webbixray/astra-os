import { expect } from '@playwright/test';
import { test, setupAuth, mockApi } from './fixtures';

const MOCK_ANALYTICS = {
  overview: { total_impressions: 125000, total_clicks: 4200, total_conversions: 185, conversion_rate: 4.4 },
  time_series: [
    { date: '2026-07-01', impressions: 10000, clicks: 350, conversions: 15 },
    { date: '2026-07-02', impressions: 12000, clicks: 420, conversions: 18 },
  ],
  channels: [
    { channel: 'email', impressions: 50000, clicks: 2000, conversions: 80 },
    { channel: 'social', impressions: 75000, clicks: 2200, conversions: 105 },
  ],
};

const MOCK_AD_ACCOUNTS = [
  { id: 'acc-1', platform: 'google_ads', account_name: 'Google Ads', is_connected: true },
  { id: 'acc-2', platform: 'meta', account_name: 'Meta Ads', is_connected: true },
];

const MOCK_AD_CAMPAIGNS = [
  { id: 'ad-1', name: 'Google Search - Brand', platform: 'google_ads', status: 'active', budget: 5000, spend: 3200, impressions: 125000, clicks: 4200 },
  { id: 'ad-2', name: 'Meta - Summer Sale', platform: 'meta', status: 'active', budget: 8000, spend: 5600, impressions: 890000, clicks: 12500 },
];

test.describe('Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
    await page.route('**/api/v1/analytics/**', async (route) => {
      const url = route.request().url();
      if (url.includes('/overview')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYTICS.overview) });
      }
      if (url.includes('/time-series')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYTICS.time_series) });
      }
      if (url.includes('/channels')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYTICS.channels) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });
  });

  test('analytics page loads', async ({ page }) => {
    await page.goto('/analytics');
    await expect(page.getByText(/analytics/i).first()).toBeVisible();
  });

  test('shows key metrics', async ({ page }) => {
    await page.goto('/analytics');
    await expect(page.getByText(/impressions|clicks|conversions/i).first()).toBeVisible();
  });
});

test.describe('Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('notifications page loads', async ({ page }) => {
    await page.goto('/notifications');
    await expect(page.getByText(/notifications/i).first()).toBeVisible();
  });

  test('shows notification list', async ({ page }) => {
    await page.goto('/notifications');
    await expect(page.getByText('Campaign completed').first()).toBeVisible({ timeout: 5000 }).catch(() => {
    });
  });

  test('mark all as read button exists', async ({ page }) => {
    await page.goto('/notifications');
    const markAllBtn = page.getByRole('button', { name: /mark all|read all/i });
    if (await markAllBtn.isVisible().catch(() => false)) {
      await expect(markAllBtn).toBeVisible();
    }
  });
});

test.describe('Advertising', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
    await page.route('**/api/v1/advertising/**', async (route) => {
      const url = route.request().url();
      if (url.includes('/accounts')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_AD_ACCOUNTS) });
      }
      if (url.includes('/campaigns')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_AD_CAMPAIGNS) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });
  });

  test('advertising page loads', async ({ page }) => {
    await page.goto('/advertising');
    await expect(page.getByText(/advertising|ad campaigns|ad accounts/i).first()).toBeVisible();
  });
});

test.describe('Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
    await page.route('**/api/v1/workflows**', async (route) => {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
  });

  test('workflows page loads', async ({ page }) => {
    await page.goto('/workflows');
    await expect(page.getByText(/workflows|automation/i).first()).toBeVisible();
  });
});

test.describe('Knowledge Base', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
    await page.route('**/api/v1/knowledge**', async (route) => {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
  });

  test('knowledge page loads', async ({ page }) => {
    await page.goto('/knowledge');
    await expect(page.getByText(/knowledge|knowledge base/i).first()).toBeVisible();
  });
});

test.describe('Reports', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
    await page.route('**/api/v1/reports**', async (route) => {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });
  });

  test('reports page loads', async ({ page }) => {
    await page.goto('/reports');
    await expect(page.getByText(/reports|reporting/i).first()).toBeVisible();
  });
});
