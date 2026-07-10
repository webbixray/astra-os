import { test as setup } from '@playwright/test';
import { MOCK_TOKENS, MOCK_USER } from './fixtures';

const AUTH_FILE = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');

  await page.route('**/api/v1/auth/signin', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ...MOCK_TOKENS, user: MOCK_USER }),
    });
  });

  await page.fill('#email', 'test@astra.ai');
  await page.fill('#password', 'test-password');
  await page.click('button[type="submit"]');

  await page.waitForURL('/dashboard');

  await page.context().storageState({ path: AUTH_FILE });
});
