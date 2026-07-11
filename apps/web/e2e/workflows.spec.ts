import { expect } from '@playwright/test';
import { test, setupAuth, mockApi } from './fixtures';

test.describe('Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('workflow list page renders', async ({ page }) => {
    await page.goto('/workflows');

    await expect(page.getByText(/workflows/i)).toBeVisible();
  });

  test('workflow builder page renders', async ({ page }) => {
    await page.goto('/workflows/new');

    await expect(page.getByText(/workflow builder/i)).toBeVisible();
  });
});

test.describe('Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('analytics page renders', async ({ page }) => {
    await page.goto('/analytics');

    await expect(page.getByText(/analytics/i)).toBeVisible();
  });
});

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('settings page renders', async ({ page }) => {
    await page.goto('/settings');

    await expect(page.getByText(/settings/i)).toBeVisible();
  });
});

test.describe('Team', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('team page renders', async ({ page }) => {
    await page.goto('/team');

    await expect(page.getByText(/team/i)).toBeVisible();
  });
});
