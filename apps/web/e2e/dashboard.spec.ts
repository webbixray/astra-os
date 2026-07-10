import { expect } from '@playwright/test';
import { test, setupAuth, mockApi } from './fixtures';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuth(page);
    await mockApi(page);
  });

  test('renders dashboard with key elements', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page.getByText('Test User')).toBeVisible();
    await expect(page.getByText('Dashboard')).toBeVisible();
  });

  test('app shell sidebar navigation is visible', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page.getByRole('link', { name: /campaigns/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /content/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /analytics/i })).toBeVisible();
  });

  test('navigates to campaigns page', async ({ page }) => {
    await page.goto('/dashboard');

    await page.getByRole('link', { name: /campaigns/i }).first().click();
    await page.waitForURL(/\/campaigns/);
  });

  test('navigates to content page', async ({ page }) => {
    await page.goto('/dashboard');

    await page.getByRole('link', { name: /content/i }).first().click();
    await page.waitForURL(/\/content/);
  });

  test('theme toggle works', async ({ page }) => {
    await page.goto('/dashboard');

    const html = page.locator('html');
    const initialClass = await html.getAttribute('class');

    const toggleButton = page.locator('button[aria-label*="theme" i], button svg.lucide-sun, button svg.lucide-moon').first();
    if (await toggleButton.isVisible()) {
      await toggleButton.click();
      const newClass = await html.getAttribute('class');
      expect(newClass).not.toBe(initialClass);
    }
  });

  test('command palette opens with Cmd+K', async ({ page }) => {
    await page.goto('/dashboard');

    await page.keyboard.press('Meta+k');
    await expect(page.getByPlaceholder(/search|command/i)).toBeVisible();
  });

  test('notification bell is visible', async ({ page }) => {
    await page.goto('/dashboard');

    const bellButton = page.locator('button svg.lucide-bell').first();
    await expect(bellButton).toBeVisible();
  });

  test('shows org name in sidebar', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page.getByText('starter')).toBeVisible();
  });
});
