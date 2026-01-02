import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * ETL Execution Page Object
 */
export class EtlPage extends BasePage {
  readonly systemsGrid: Locator;
  readonly periodSelector: Locator;
  readonly dataInicialInput: Locator;
  readonly dataFinalInput: Locator;
  readonly executeButton: Locator;
  readonly cancelButton: Locator;
  readonly dryRunSwitch: Locator;
  readonly statusIndicator: Locator;
  readonly logsContainer: Locator;

  constructor(page: Page) {
    super(page);
    this.systemsGrid = page.locator('[data-testid="systems-grid"], .systems-grid');
    this.periodSelector = page.locator('[data-testid="period-selector"]');
    this.dataInicialInput = page.locator('input[name="data_inicial"], input[placeholder*="inicial"]');
    this.dataFinalInput = page.locator('input[name="data_final"], input[placeholder*="final"]');
    this.executeButton = page.getByRole('button', { name: /executar|execute/i });
    this.cancelButton = page.getByRole('button', { name: /cancelar|cancel/i });
    this.dryRunSwitch = page.locator('[data-testid="dry-run-switch"], input[name="dryRun"]');
    this.statusIndicator = page.locator('[data-testid="status"], .status-indicator');
    this.logsContainer = page.locator('[data-testid="logs"], .logs-container');
  }

  async goto() {
    await super.goto('/etl');
  }

  /**
   * Seleciona um sistema pelo nome
   */
  async selectSystem(systemName: string) {
    const checkbox = this.page.getByRole('checkbox', { name: new RegExp(systemName, 'i') });
    if (!(await checkbox.isChecked())) {
      await checkbox.check();
    }
  }

  /**
   * Desmarca um sistema pelo nome
   */
  async deselectSystem(systemName: string) {
    const checkbox = this.page.getByRole('checkbox', { name: new RegExp(systemName, 'i') });
    if (await checkbox.isChecked()) {
      await checkbox.uncheck();
    }
  }

  /**
   * Seleciona múltiplos sistemas
   */
  async selectSystems(systemNames: string[]) {
    for (const name of systemNames) {
      await this.selectSystem(name);
    }
  }

  /**
   * Define o período de execução
   */
  async setPeriod(dataInicial: string, dataFinal?: string) {
    await this.dataInicialInput.fill(dataInicial);
    if (dataFinal) {
      await this.dataFinalInput.fill(dataFinal);
    }
  }

  /**
   * Ativa/desativa dry run
   */
  async setDryRun(enabled: boolean) {
    const isChecked = await this.dryRunSwitch.isChecked();
    if (enabled !== isChecked) {
      await this.dryRunSwitch.click();
    }
  }

  /**
   * Clica no botão executar
   */
  async clickExecute() {
    await this.executeButton.click();
  }

  /**
   * Clica no botão cancelar
   */
  async clickCancel() {
    await this.cancelButton.click();
  }

  /**
   * Executa pipeline completo
   */
  async executePipeline(systems: string[], dataInicial: string, dataFinal?: string) {
    await this.selectSystems(systems);
    await this.setPeriod(dataInicial, dataFinal);
    await this.clickExecute();
  }

  /**
   * Verifica se está executando
   */
  async isExecuting(): Promise<boolean> {
    const runningText = this.page.getByText(/executando|running/i);
    return await runningText.isVisible();
  }

  /**
   * Espera execução completar
   */
  async waitForExecutionComplete(timeout: number = 60000) {
    await this.page.waitForFunction(
      () => {
        const text = document.body.innerText.toLowerCase();
        return text.includes('concluído') ||
               text.includes('completed') ||
               text.includes('erro') ||
               text.includes('error');
      },
      { timeout }
    );
  }

  /**
   * Retorna sistemas selecionados
   */
  async getSelectedSystems(): Promise<string[]> {
    const checkboxes = this.page.getByRole('checkbox').filter({ hasNot: this.page.locator(':not(:checked)') });
    const labels = await checkboxes.evaluateAll((els) =>
      els.map(el => el.getAttribute('aria-label') || el.getAttribute('name') || '')
    );
    return labels.filter(Boolean);
  }

  /**
   * Verifica se página ETL carregou
   */
  async verifyLoaded() {
    await expect(this.executeButton).toBeVisible();
    await this.waitForLoadingComplete();
  }
}
