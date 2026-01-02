import { Page, Locator } from '@playwright/test';

/**
 * Base Page Object - métodos comuns a todas as páginas
 */
export class BasePage {
  readonly page: Page;
  readonly header: Locator;
  readonly sidebar: Locator;
  readonly mainContent: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator('header');
    this.sidebar = page.locator('aside, nav');
    this.mainContent = page.locator('main');
  }

  /**
   * Navega para uma rota específica
   */
  async goto(path: string = '/') {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Espera toast de notificação aparecer
   */
  async waitForToast(text?: string) {
    const toast = this.page.locator('[role="status"], [data-radix-toast-viewport]');
    await toast.waitFor({ state: 'visible', timeout: 5000 });
    if (text) {
      await this.page.getByText(text).waitFor({ state: 'visible' });
    }
  }

  /**
   * Verifica se está carregando
   */
  async isLoading(): Promise<boolean> {
    const spinner = this.page.locator('.animate-spin, [data-loading="true"]');
    return await spinner.isVisible();
  }

  /**
   * Espera carregamento terminar
   */
  async waitForLoadingComplete() {
    await this.page.waitForLoadState('networkidle');
    const spinner = this.page.locator('.animate-spin');
    if (await spinner.isVisible()) {
      await spinner.waitFor({ state: 'hidden', timeout: 30000 });
    }
  }

  /**
   * Navega via sidebar/menu
   */
  async navigateTo(menuItem: string) {
    await this.page.getByRole('link', { name: menuItem }).click();
    await this.page.waitForLoadState('networkidle');
  }
}
