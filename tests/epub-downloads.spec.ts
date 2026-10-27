import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const publications=JSON.parse(fs.readFileSync(new URL('../src/data/epub-publications.json',import.meta.url),'utf8'));

test.beforeEach(async({page})=>{await page.route('https://www.googletagmanager.com/**',r=>r.abort());});

test('EPUB stays a working download while reading choices remain online and PDF',async({page})=>{
  for(const route of ['/','/authors/doyle','/en/authors/doyle/the-chronological-sherlock-holmes']){
    await page.goto(route);await expect(page.getByRole('link',{name:'Read EPUB',exact:true})).toHaveCount(0);
    await expect(page.locator('[data-reading-mode=epub],[data-epub-pane]')).toHaveCount(0);
  }
  await page.goto('/en/authors/doyle/a-study-in-scarlet');
  const link=page.locator('#downloads a[download$=".epub"]');await expect(link).toHaveText('EPUB');
  const pending=page.waitForEvent('download');await link.click();const download=await pending;
  expect(download.suggestedFilename()).toBe('doyle_a-study-in-scarlet_eng.epub');
  const bytes=fs.readFileSync((await download.path())!);
  expect(createHash('sha256').update(bytes).digest('hex')).toBe(publications['doyle_a-study-in-scarlet_eng'].revision);
  await page.goto('/downloads');await expect(page.locator('a[download$=".epub"]')).toHaveCount(Object.keys(publications).length);
});

test('old EPUB reading links return to online reading in the same chapter and locale',async({page})=>{
  const route='/en/authors/doyle/a-study-in-scarlet/part-1/chapter-1';
  await page.goto(route+'?view=epub&ui=fr#epub-reader');
  await expect(page).toHaveURL(new RegExp(route+'\\?ui=fr$'));
  await expect(page.locator('html')).toHaveAttribute('lang','fr');
  await expect(page.locator('[data-online-content]')).toBeVisible();
  await expect(page.locator('[data-online-content]')).toContainText('In the year 1878');
  await expect(page.locator('.reader-display')).toBeVisible();
  await expect(page.locator('button[data-reading-mode=online]')).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('button[data-reading-mode=pdf]')).toBeVisible();
  await expect(page.locator('html')).not.toHaveAttribute('aria-pressed');
  await expect(page.locator('iframe,[data-epub-pane],[data-reading-mode=epub]')).toHaveCount(0);
});
