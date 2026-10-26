import { test, expect } from '@playwright/test';
import path from 'node:path';

const book = '/en/authors/doyle/a-study-in-scarlet';
test('homepage exposes PDF reading directly and chapter readers link back to it', async ({ page }) => {
  await page.goto('/');
  await page.locator('#book-search').fill('Poetics');
  await expect(page.locator('[data-book-row]:visible').first().getByRole('link',{name:'Read online',exact:true})).toBeVisible();
  const pdf=page.locator('[data-book-row]:visible').first().getByRole('link',{name:'Read PDF',exact:true});
  await expect(pdf).toBeVisible();
  for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:900});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  }
  await pdf.click();
  await expect(page.locator('#pdf-reader')).toHaveAttribute('open','');
  await expect(page.frameLocator('[data-pdf-frame]').locator('#numPages')).not.toBeEmpty({timeout:30000});
  await page.goto('/en/authors/aristotle/poetics/chapter-1');
  await expect(page.locator('.reader-controls a[href$="#pdf-reader"]')).toHaveAttribute('href','/en/authors/aristotle/poetics#pdf-reader');
});
test.beforeEach(async ({ page }) => {
  await page.route('https://www.googletagmanager.com/**', route => route.abort());
  // Local checks can exercise newly generated publications before git push.
  // CI fetches the committed files from GitHub with their actual CORS headers.
  if(!process.env.CI) await page.route('https://ianrastall.github.io/bookstacks-pdf/books/**',route=>{
    const relative=new URL(route.request().url()).pathname.split('/bookstacks-pdf/books/')[1];
    return route.fulfill({path:path.resolve('../bookstacks-pdf/books',relative),contentType:'application/pdf',headers:{'access-control-allow-origin':'*'}});
  });
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
    const result=await page.evaluate(async href=>{const r=await fetch(href);return {status:r.status,signature:new TextDecoder().decode((await r.arrayBuffer()).slice(0,5))};},(await link.getAttribute('href'))!);
    expect(result).toEqual({status:200,signature:'%PDF-'});
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
  await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  await page.locator('#appearance-open').click();
  await page.locator('#theme-choice').selectOption('dark');
  await page.keyboard.press('Escape');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.locator('[data-pdf-frame]')).toHaveAttribute('src', /-dark\.pdf/);
  await page.locator('[data-pdf-theme]').selectOption('light');
  await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  await page.locator('#appearance-open').click();
  await page.locator('#theme-choice').selectOption('dark');
  await page.keyboard.press('Escape');
  await expect(page.locator('[data-pdf-theme]')).toHaveValue('dark');
  await expect(page.locator('[data-pdf-frame]')).toHaveAttribute('src',/-dark\.pdf/);
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

for(const [language,route] of [
  ['zh-Hans','/zh-Hans/authors/lu-xun/call-to-arms'],
  ['grc','/grc/authors/aristotle/poetics'],
  ['ru','/ru/authors/turgenev/mumu'],
])test(`published PDF text retains its edition language: ${language}`,async({page})=>{
  await page.goto(`${route}?ui=en#pdf-reader`);
  const frame=page.frameLocator('[data-pdf-frame]');
  await expect(page.locator('html')).toHaveAttribute('lang','en');
  await expect(frame.locator('html')).toHaveAttribute('lang','en');
  await expect(frame.locator('#pageNumber')).toHaveAttribute('max',/^[1-9]\d*$/,{timeout:30000});
  await frame.locator('#pageNumber').fill('5');
  await frame.locator('#pageNumber').press('Enter');
  await expect(frame.locator('.page[data-page-number="5"] .textLayer')).not.toBeEmpty({timeout:30000});
  await expect(frame.locator('#viewer')).toHaveAttribute('lang',language);
  await page.locator('[data-pdf-theme]').selectOption('light');
  await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  await expect(frame.locator('#pageNumber')).toHaveValue('5',{timeout:30000});
  await expect(frame.locator('.page[data-page-number="5"] canvas')).toBeVisible();
});
