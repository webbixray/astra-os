import { expect } from '@playwright/test';
import { test, setupAuth, mockApi } from './fixtures';

test.describe('Campaigns', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('campaign list page renders', async ({ page }) => {
    await page.goto('/campaigns');

    await expect(page.getByText(/campaigns/i)).toBeVisible();
  });

  test('new campaign page renders form', async ({ page }) => {
    await page.goto('/campaigns/new');

    await expect(page.getByLabel(/campaign name/i)).toBeVisible();
    await expect(page.getByLabel(/description/i)).toBeVisible();
    await expect(page.getByLabel(/budget/i)).toBeVisible();
  });

  test('new campaign form validates required fields', async ({ page }) => {
    await page.goto('/campaigns/new');

    await page.click('button[type="submit"]');

    await expect(page.getByText(/campaign name is required/i)).toBeVisible();
  });

  test('new campaign creates successfully', async ({ page }) => {
    await page.goto('/campaigns/new');

    await page.route('**/api/v1/campaigns', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-1',
            name: 'Test Campaign',
            status: 'draft',
          }),
        });
      } else {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      }
    });

    await page.fill('#name', 'Test Campaign');
    await page.fill('#description', 'A test campaign');
    await page.click('button[type="submit"]');

    await page.waitForURL(/\/campaigns/);
  });
});
