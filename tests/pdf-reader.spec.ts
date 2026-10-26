import { test, expect } from '@playwright/test';

const book = '/en/authors/doyle/a-study-in-scarlet';
test.beforeEach(async ({ page }) => {
  await page.route('https://www.googletagmanager.com/**', route => route.abort());
});

test('PDF.js stays embedded, restores pages and switches PDF files without losing position', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(book);
  const frame = page.frameLocator('[data-pdf-frame]');
  await expect(page.locator('[data-pdf-frame]')).not.toHaveAttribute('src');
  await page.locator('#pdf-reader summary').click();
  await expect(page.locator('[data-pdf-frame]')).toHaveAttribute('src', /-dark\.pdf/);
  await expect(frame.locator('#numPages')).toContainText('102', { timeout: 30000 });
  await frame.locator('#pageNumber').fill('5');
  await frame.locator('#pageNumber').press('Enter');
  await expect(frame.locator('.page[data-page-number="5"] .textLayer')).toContainText('In the year 1878', { timeout: 30000 });
  await frame.locator('#viewFindButton').click();
  await frame.locator('#findInput').fill('Sherlock');
  await expect(frame.locator('#findResultsCount')).not.toBeEmpty({ timeout: 30000 });
  await frame.locator('#findInput').press('Escape');
  await frame.locator('#pageNumber').fill('5');
  await frame.locator('#pageNumber').press('Enter');
  await page.locator('[data-pdf-theme]').selectOption('light');
  await expect(page.locator('[data-pdf-frame]')).toHaveAttribute('src', /-light\.pdf.*page=5/);
  await expect(frame.locator('#pageNumber')).toHaveValue('5', { timeout: 30000 });
  await expect(frame.locator('.page[data-page-number="5"] canvas')).toBeVisible();
  await page.reload();
  await expect(page.locator('#pdf-reader')).toHaveAttribute('open', '');
  await expect(frame.locator('#pageNumber')).toHaveValue('5', { timeout: 30000 });
  await expect(page).toHaveURL(/a-study-in-scarlet#pdf-reader$/);
  await expect(page.locator('#downloads a[download$="-light.pdf"]')).toHaveCount(1);
  await expect(page.locator('#downloads a[download$="-dark.pdf"]')).toHaveCount(1);
  for (const theme of ['light', 'dark']) {
    const link = page.locator(`#downloads a[download$="-${theme}.pdf"]`);
    const response = await page.request.get((await link.getAttribute('href'))!);
    expect(response.status()).toBe(200);
    expect((await response.body()).subarray(0, 5).toString()).toBe('%PDF-');
  }
  expect(errors).toEqual([]);
});

test('site appearance persists and initially selects the matching PDF', async ({ page }) => {
  await page.goto(book);
  await page.locator('#appearance-open').click();
  await page.locator('#theme-choice').selectOption('light');
  await page.keyboard.press('Escape');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.locator('#pdf-reader summary').click();
  await expect(page.locator('[data-pdf-frame]')).toHaveAttribute('src', /-light\.pdf/);
  await page.locator('#appearance-open').click();
  await page.locator('#theme-choice').selectOption('dark');
  await page.keyboard.press('Escape');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.locator('[data-pdf-frame]')).toHaveAttribute('src', /-dark\.pdf/);
});

test('embedded reader fits a phone and interface changes preserve the edition and page', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${book}#pdf-reader`);
  const frame = page.frameLocator('[data-pdf-frame]');
  await expect(frame.locator('#numPages')).toContainText('102', { timeout: 30000 });
  await frame.locator('#pageNumber').fill('10');
  await frame.locator('#pageNumber').press('Enter');
  await page.locator('#interface-language').selectOption('fr');
  await expect(page).toHaveURL(/\/en\/authors\/doyle\/a-study-in-scarlet\?ui=fr#pdf-reader$/);
  await expect(frame.locator('#pageNumber')).toHaveValue('10', { timeout: 30000 });
  await expect(frame.locator('html')).toHaveAttribute('lang', 'fr');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
});

test('PDF reader works without browser storage', async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(window, 'localStorage', { get() { throw new Error('Unavailable'); } }));
  await page.goto(`${book}#pdf-reader`);
  await expect(page.frameLocator('[data-pdf-frame]').locator('#numPages')).toContainText('102', { timeout: 30000 });
  await page.locator('[data-pdf-theme]').selectOption('light');
  await expect(page.frameLocator('[data-pdf-frame]').locator('#numPages')).toContainText('102', { timeout: 30000 });
});
