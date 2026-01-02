import { test as base, Page } from '@playwright/test';
import { DashboardPage } from '../pages/dashboard.page';
import { EtlPage } from '../pages/etl.page';
import { SettingsPage } from '../pages/settings.page';

/**
 * Custom test fixtures para ETL Dashboard
 * Authentication is handled via storageState in playwright.config.ts
 */
type Pages = {
  dashboardPage: DashboardPage;
  etlPage: EtlPage;
  settingsPage: SettingsPage;
  authenticatedPage: Page;
};

export const test = base.extend<Pages>({
  // Authenticated page fixture - already authenticated via storageState
  authenticatedPage: async ({ page }, use) => {
    await use(page);
  },

  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },

  etlPage: async ({ page }, use) => {
    const etlPage = new EtlPage(page);
    await use(etlPage);
  },

  settingsPage: async ({ page }, use) => {
    const settingsPage = new SettingsPage(page);
    await use(settingsPage);
  },
});

export { expect } from '@playwright/test';
