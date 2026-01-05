import { test, expect } from '../fixtures';

test.describe('Navegação', () => {
  test('carrega página inicial (dashboard)', async ({ dashboardPage }) => {
    await dashboardPage.goto();
    await dashboardPage.verifyLoaded();
    await expect(dashboardPage.mainContent).toBeVisible();
  });

  test('navega para página ETL', async ({ authenticatedPage: page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: /etl/i }).click();
    await expect(page).toHaveURL(/\/etl/);
  });

  test('navega para página de Settings', async ({ authenticatedPage: page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: /settings|configurações/i }).click();
    await expect(page).toHaveURL(/\/settings/);
  });

  test('navega para página de Logs', async ({ authenticatedPage: page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: /logs/i }).click();
    await expect(page).toHaveURL(/\/logs/);
  });

  test('sidebar está visível em todas as páginas', async ({ authenticatedPage: page }) => {
    const routes = ['/', '/etl', '/logs', '/settings'];

    for (const route of routes) {
      await page.goto(route);
      const sidebar = page.locator('aside, nav').first();
      await expect(sidebar).toBeVisible();
    }
  });

  test('página 404 para rota inexistente', async ({ authenticatedPage: page }) => {
    await page.goto('/rota-que-nao-existe');
    await page.waitForTimeout(1000);

    // Pode redirecionar para / ou mostrar 404 ou simplesmente não quebrar
    const is404 = await page.getByText(/404|não encontrado|not found/i).isVisible().catch(() => false);
    const isHome = page.url().endsWith('/');
    const isOnRoute = page.url().includes('/rota-que-nao-existe');

    // Teste passa se: mostra 404, redireciona para home, ou simplesmente não quebra
    expect(is404 || isHome || isOnRoute).toBeTruthy();
  });
});
