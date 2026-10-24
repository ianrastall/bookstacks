import { expect, test } from '@playwright/test';

test('Poe plates load and fade into both reading appearances, with Pym in the same volume', async ({ page }) => {
  await page.goto('/en/authors/poe/collected-works-of-mystery-and-horror/story-1');
  const image = page.locator('.chapter-sidebar .reader-illustration .tei-graphic');
  await expect(page.locator('.reader-content img')).toHaveCount(0);
  await expect(image).toHaveCount(1);
  await expect(image).toHaveAttribute('alt', /gold scarab/i);
  await expect.poll(() => image.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  const style = await image.evaluate(img => ({ mask: getComputedStyle(img).maskImage, composite: getComputedStyle(img).maskComposite }));
  // Chromium normalizes "to right" to 90deg and omits the default vertical angle.
  expect(style.mask).toMatch(/^linear-gradient\((?:90deg|to right),/);
  expect(style.mask.match(/linear-gradient/g)).toHaveLength(2);
  expect(style.composite).toContain('intersect');
  for (const theme of ['light', 'dark']) {
    await page.evaluate(theme => document.documentElement.dataset.theme = theme, theme);
    await expect(image).toHaveCSS('mix-blend-mode', theme === 'light' ? 'multiply' : 'normal');
    await image.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `tmp/poe/reader-${theme}.png` });
  }
  const sidebar = page.locator('.chapter-sidebar');
  expect(await sidebar.evaluate(el => el.getBoundingClientRect().height <= innerHeight - 30)).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/en/authors/poe/collected-works-of-mystery-and-horror/part-pym/chapter-25');
  await expect(image).toHaveAttribute('src', /the-narrative-of-arthur-gordon-pym/);
  await expect(page.locator('.reader-content')).toContainText('Tekeli-li');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.locator('.chapter-navigation a[rel="next"]').click();
  await expect(page).toHaveURL(/part-pym\/notes-notes$/);
  await expect(page.locator('.reader-content')).toContainText('Mr. Pym');
  await expect(page.locator('.reader-content img')).toHaveCount(3);
  for (const glyph of await page.locator('.reader-content img').all()) {
    await glyph.scrollIntoViewIfNeeded();
    await expect.poll(() => glyph.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  }
  await page.goto('/en/authors/poe/collected-works-of-mystery-and-horror/part-pym/chapter-23');
  await expect(page.locator('.reader-content img')).toHaveCount(4);
  await expect(image).toHaveCount(1);
  for (const diagram of await page.locator('.reader-content img').all()) {
    await diagram.scrollIntoViewIfNeeded();
    await expect.poll(() => diagram.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  }
});
