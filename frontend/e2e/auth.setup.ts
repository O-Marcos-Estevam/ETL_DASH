import { test as setup, expect } from '@playwright/test';

const authFile = 'e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // Monitor network requests
  page.on('response', async response => {
    if (response.url().includes('/auth/login')) {
      console.log(`Login API Response: ${response.status()}`);
      try {
        const body = await response.json();
        console.log('Login response body:', JSON.stringify(body));
      } catch (e) {
        console.log('Could not parse response body');
      }
    }
  });

  // Navigate to login page
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // Fill form
  const usernameField = page.locator('#username');
  const passwordField = page.locator('#password');

  await usernameField.waitFor({ state: 'visible', timeout: 10000 });
  await usernameField.fill('admin');
  await passwordField.fill('Admin123!');

  // Screenshot before submit
  await page.screenshot({ path: 'e2e/.auth/debug-before-submit.png' });

  // Click submit
  const submitButton = page.locator('button[type="submit"]');
  await submitButton.click();

  // Wait for response
  await page.waitForTimeout(3000);

  // Screenshot after submit
  await page.screenshot({ path: 'e2e/.auth/debug-after-submit.png' });

  // Check for error messages on page
  const pageContent = await page.content();
  if (pageContent.includes('Usuário ou senha inválidos') || pageContent.includes('Invalid')) {
    console.log('Found invalid credentials message');
    throw new Error('Login failed: Invalid credentials');
  }
  if (pageContent.includes('locked') || pageContent.includes('bloqueada')) {
    console.log('Found account locked message');
    throw new Error('Login failed: Account locked');
  }

  const currentUrl = page.url();
  console.log(`Final URL: ${currentUrl}`);

  if (currentUrl.includes('/login')) {
    throw new Error('Login failed: still on login page');
  }

  await page.waitForSelector('main', { timeout: 10000 });
  await page.context().storageState({ path: authFile });
  console.log('Authentication successful');
});
