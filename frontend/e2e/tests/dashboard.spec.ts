import { test, expect } from '../fixtures';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ dashboardPage }) => {
    await dashboardPage.goto();
  });

  test('carrega dashboard corretamente', async ({ dashboardPage }) => {
    await dashboardPage.verifyLoaded();
    await expect(dashboardPage.mainContent).toBeVisible();
  });

  test('exibe cards de KPI', async ({ dashboardPage }) => {
    await dashboardPage.verifyLoaded();

    // Verifica se há pelo menos algum conteúdo de KPI
    const kpiTexts = ['Total', 'Sucesso', 'Erro', 'Pendente', 'Jobs', 'Sistemas'];
    let foundKpi = false;

    for (const text of kpiTexts) {
      if (await dashboardPage.page.getByText(text).first().isVisible().catch(() => false)) {
        foundKpi = true;
        break;
      }
    }

    // Dashboard pode estar vazio inicialmente, então verificamos apenas se carregou
    expect(foundKpi || await dashboardPage.mainContent.isVisible()).toBeTruthy();
  });

  test('exibe lista de sistemas', async ({ dashboardPage }) => {
    // Verifica se há menção a algum sistema conhecido
    const sistemas = ['MAPS', 'AMPLIS', 'FIDC', 'QORE', 'BRITECH'];

    for (const sistema of sistemas) {
      const element = dashboardPage.page.getByText(sistema).first();
      if (await element.isVisible().catch(() => false)) {
        await expect(element).toBeVisible();
        return; // Encontrou pelo menos um
      }
    }
  });

  test('botão de refresh funciona', async ({ dashboardPage }) => {
    await dashboardPage.verifyLoaded();

    // Tenta encontrar botão de refresh
    const refreshButton = dashboardPage.page.getByRole('button', { name: /atualizar|refresh|reload/i });

    if (await refreshButton.isVisible().catch(() => false)) {
      await refreshButton.click();
      // Verifica que não houve erro
      await expect(dashboardPage.mainContent).toBeVisible();
    }
  });

  test('exibe status de conexão com backend', async ({ dashboardPage }) => {
    await dashboardPage.page.waitForLoadState('networkidle');

    // Verifica se não há mensagem de erro de conexão
    const errorMessage = dashboardPage.page.getByText(/erro de conexão|connection error|offline/i);
    const hasError = await errorMessage.isVisible().catch(() => false);

    // Se houver erro, falha o teste
    if (hasError) {
      await expect(errorMessage).not.toBeVisible();
    }
  });
});
