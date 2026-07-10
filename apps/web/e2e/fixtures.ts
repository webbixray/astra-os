import { test as base, type Page } from '@playwright/test';

export const MOCK_USER = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'test@astra.ai',
  name: 'Test User',
  avatar_url: null,
};

export const MOCK_ORG = {
  id: '223e4567-e89b-12d3-a456-426614174001',
  name: 'Test Org',
  slug: 'test-org',
  plan_tier: 'starter',
};

export const MOCK_TOKENS = {
  access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.test',
  refresh_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyZWZyZXNoIn0.test',
};

export const MOCK_CAMPAIGNS = [
  { id: '1', name: 'Summer Sale', status: 'active', budget_amount: 5000, budget_currency: 'USD', channel: 'email' },
  { id: '2', name: 'Brand Awareness', status: 'draft', budget_amount: 10000, budget_currency: 'USD', channel: 'social' },
];

export const MOCK_NOTIFICATIONS = [
  { id: '1', title: 'Campaign completed', message: 'Summer Sale campaign completed', is_read: false, created_at: '2026-07-10T00:00:00Z' },
  { id: '2', title: 'New lead', message: 'You have a new lead from your website', is_read: true, created_at: '2026-07-09T00:00:00Z' },
];

export type MockOptions = {
  mockAuth: boolean;
};

export const test = base.extend<MockOptions>({
  mockAuth: [true, { option: true }],
});

export async function setupAuth(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem('astra_access_token', MOCK_TOKENS.access_token);
    window.localStorage.setItem('astra_refresh_token', MOCK_TOKENS.refresh_token);
    window.localStorage.setItem('astra_user', JSON.stringify(MOCK_USER));
  });
}

export async function mockApi(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    if (url.includes('/auth/me') && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_USER) });
    }
    if (url.includes('/auth/signin') && method === 'POST') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...MOCK_TOKENS, user: MOCK_USER }) });
    }
    if (url.includes('/auth/refresh') && method === 'POST') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...MOCK_TOKENS, user: MOCK_USER }) });
    }
    if (url.includes('/organizations') && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([MOCK_ORG]) });
    }
    if (url.includes('/campaigns') && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_CAMPAIGNS) });
    }
    if (url.includes('/campaigns') && method === 'POST') {
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(MOCK_CAMPAIGNS[0]) });
    }
    if (url.includes('/notifications') && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_NOTIFICATIONS) });
    }
    if (url.includes('/ai/content/generate') && method === 'POST') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ content: '# Mock Generated Content\n\nThis is test content.', sections: { body: 'Test content' } }) });
    }
    if (url.includes('/agents') && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    }
    if (url.includes('/agents/tools') && method === 'GET') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    }

    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
  });
}
