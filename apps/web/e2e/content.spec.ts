import { expect } from '@playwright/test';
import { test, setupAuth, mockApi } from './fixtures';

test.describe('Content', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('content list page renders', async ({ page }) => {
    await page.goto('/content');

    await expect(page.getByText(/content/i)).toBeVisible();
  });

  test('AI content composer page renders', async ({ page }) => {
    await page.goto('/ai-content');

    await expect(page.getByText(/ai content/i)).toBeVisible();
  });
});

test.describe('Advertising', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('advertising page renders', async ({ page }) => {
    await page.goto('/advertising');

    await expect(page.getByText(/advertising/i)).toBeVisible();
  });
});

test.describe('Reports', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('reports page renders', async ({ page }) => {
    await page.goto('/reports');

    await expect(page.getByText(/reports/i)).toBeVisible();
  });
});

test.describe('Calendar', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('calendar page renders', async ({ page }) => {
    await page.goto('/calendar');

    await expect(page.getByText(/calendar/i)).toBeVisible();
  });
});
