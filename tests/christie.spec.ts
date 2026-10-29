import { expect, test } from '@playwright/test';

test('Christie sketches sit below the right navigation and source diagrams remain in the text', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/en/authors/christie/the-mysterious-affair-at-styles/chapter-3');
  await expect(page.locator('.reader-content')).toContainText('To make this part of my story clear');
  const sketch = page.locator('.chapter-sidebar .reader-illustration img');
  await sketch.scrollIntoViewIfNeeded();
  await expect.poll(() => sketch.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  const article = await page.locator('.reader-content').boundingBox();
  const sidebar = await page.locator('.chapter-sidebar').boundingBox();
  expect(sidebar!.x).toBeGreaterThan(article!.x + article!.width);
  expect(await sketch.evaluate(img => !!img.closest('.reader-illustration')?.previousElementSibling)).toBe(true);
  for (const image of await page.locator('.reader-content img').all()) {
    await image.scrollIntoViewIfNeeded();
    await expect.poll(() => image.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  }
  await page.screenshot({ path: 'tmp/christie-reader-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  for (const theme of ['light', 'dark']) {
    await page.evaluate(theme => document.documentElement.dataset.theme = theme, theme);
    await sketch.scrollIntoViewIfNeeded();
    await expect(sketch).toHaveCSS('mix-blend-mode', theme === 'light' ? 'multiply' : 'screen');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await page.screenshot({ path: `tmp/christie-reader-mobile-${theme}.png` });
  }
  await page.goto('/authors/christie');
  await expect(page.getByRole('link', { name: 'Giants’ Bread', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'The Plymouth Express Affair', exact: true })).toBeVisible();
});
