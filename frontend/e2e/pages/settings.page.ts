import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Settings Page Object
 */
export class SettingsPage extends BasePage {
  readonly credentialsSection: Locator;
  readonly pathsSection: Locator;
  readonly fundosSection: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    super(page);
    this.credentialsSection = page.locator('[data-testid="credentials-section"]');
    this.pathsSection = page.locator('[data-testid="paths-section"]');
    this.fundosSection = page.locator('[data-testid="fundos-section"]');
    this.saveButton = page.getByRole('button', { name: /salvar|save/i });
    this.cancelButton = page.getByRole('button', { name: /cancelar|cancel/i });
  }

  async goto() {
    await super.goto('/settings');
  }

  /**
   * Abre aba de credenciais de um sistema
   */
  async openCredentialsTab(systemName: string) {
    const tab = this.page.getByRole('tab', { name: new RegExp(systemName, 'i') });
    await tab.click();
  }

  /**
   * Preenche campo de credencial
   */
  async fillCredential(fieldName: string, value: string) {
    const input = this.page.locator(`input[name="${fieldName}"], input[placeholder*="${fieldName}"]`);
    await input.fill(value);
  }

  /**
   * Preenche username e password de um sistema
   */
  async fillSystemCredentials(username: string, password: string) {
    await this.fillCredential('username', username);
    await this.fillCredential('password', password);
  }

  /**
   * Salva configurações
   */
  async save() {
    await this.saveButton.click();
    await this.waitForToast();
  }

  /**
   * Verifica se senha está mascarada
   */
  async isPasswordMasked(): Promise<boolean> {
    const passwordInputs = this.page.locator('input[type="password"]');
    const count = await passwordInputs.count();
    return count > 0;
  }

  /**
   * Preenche campo de path
   */
  async fillPath(pathName: string, value: string) {
    const input = this.page.locator(`input[name="${pathName}"]`);
    await input.fill(value);
  }

  /**
   * Verifica se settings carregou
   */
  async verifyLoaded() {
    await expect(this.saveButton).toBeVisible();
    await this.waitForLoadingComplete();
  }
}
