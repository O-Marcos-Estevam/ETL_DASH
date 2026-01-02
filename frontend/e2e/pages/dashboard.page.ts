import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Dashboard Page Object
 */
export class DashboardPage extends BasePage {
  readonly kpiCards: Locator;
  readonly systemCards: Locator;
  readonly refreshButton: Locator;

  constructor(page: Page) {
    super(page);
    this.kpiCards = page.locator('[data-testid="kpi-card"], .kpi-card');
    this.systemCards = page.locator('[data-testid="system-card"], .system-card');
    this.refreshButton = page.getByRole('button', { name: /atualizar|refresh/i });
  }

  async goto() {
    await super.goto('/');
  }

  /**
   * Retorna número de KPI cards visíveis
   */
  async getKpiCardCount(): Promise<number> {
    return await this.kpiCards.count();
  }

  /**
   * Retorna número de system cards visíveis
   */
  async getSystemCardCount(): Promise<number> {
    return await this.systemCards.count();
  }

  /**
   * Verifica se KPI card com título existe
   */
  async hasKpiCard(title: string): Promise<boolean> {
    const card = this.page.locator(`text=${title}`);
    return await card.isVisible();
  }

  /**
   * Clica no botão de refresh
   */
  async refresh() {
    if (await this.refreshButton.isVisible()) {
      await this.refreshButton.click();
      await this.waitForLoadingComplete();
    }
  }

  /**
   * Verifica se dashboard carregou corretamente
   */
  async verifyLoaded() {
    await expect(this.mainContent).toBeVisible();
    await this.waitForLoadingComplete();
  }
}
