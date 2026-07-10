import { expect } from '@playwright/test';
import { test, mockApi, MOCK_USER, MOCK_TOKENS } from './fixtures';

test.describe('Login', () => {
  test('renders login form', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.route('**/api/v1/auth/signin', async (route) => {
      await route.fulfill({ status: 401, body: 'Invalid credentials' });
    });

    await page.fill('#email', 'wrong@email.com');
    await page.fill('#password', 'wrong-password');
    await page.click('button[type="submit"]');

    await expect(page.getByText('Invalid email or password')).toBeVisible();
  });

  test('redirects to dashboard on successful login', async ({ page }) => {
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
  });

  test('has link to signup', async ({ page }) => {
    await page.goto('/login');

    const signupLink = page.getByRole('link', { name: /sign up/i });
    await expect(signupLink).toBeVisible();
    await expect(signupLink).toHaveAttribute('href', '/signup');
  });
});

test.describe('Signup', () => {
  test('renders signup form', async ({ page }) => {
    await page.goto('/signup');

    await expect(page.getByRole('heading', { name: /create.*account/i })).toBeVisible();
    await expect(page.getByLabel('Name')).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
  });
});
