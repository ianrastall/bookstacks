import { expect, test } from '@playwright/test';

test('book paragraphs, internal headings and scene breaks follow prose typography', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/en/authors/christie/giants-bread/book-1/chapter-1');
  const article = page.locator('.reader-content');
  const paragraphs = article.locator(':scope > .tei-paragraph');
  await expect(paragraphs.first()).toHaveCSS('text-indent', '0px');
  const next = paragraphs.nth(1);
  const style = await next.evaluate(el => {
    const s = getComputedStyle(el);
    return { indent: parseFloat(s.textIndent), size: parseFloat(s.fontSize), leading: parseFloat(s.lineHeight), margin: s.marginBlockEnd, align: s.textAlign, hyphens: s.hyphens };
  });
  expect(style.indent / style.size).toBeCloseTo(1.5);
  expect(style.leading / style.size).toBeCloseTo(1.55);
  expect(style.margin).toBe('0px');
  expect(style.align).toBe('justify');
  expect(style.hyphens).toBe('auto');
  const subheading = article.locator('h2.tei-subheading').first();
  await expect(subheading).toBeVisible();
  await expect(subheading.locator('+ p')).toHaveCSS('text-indent', '0px');
  await page.screenshot({ path: 'tmp/typography-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(next).toHaveCSS('text-align', 'start');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.goto('/en/authors/christie/giants-bread/book-5/chapter-4');
  const sceneBreak = page.locator('.tei-scene-break').first();
  await expect(sceneBreak).toBeVisible();
  await expect(sceneBreak.locator('+ p')).toHaveCSS('text-indent', '0px');
});

test('dark sketches remove the paper instead of displaying a white vignette', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/en/authors/christie/the-mysterious-affair-at-styles/chapter-3');
  const diagram = page.locator('.reader-content img').first();
  expect(await diagram.evaluate(el => parseFloat(getComputedStyle(el).marginTop))).toBeGreaterThan(0);
  const image = page.locator('.reader-illustration img');
  await image.scrollIntoViewIfNeeded();
  await expect.poll(() => image.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  for (const theme of ['dark', 'light']) {
    await page.evaluate(theme => document.documentElement.dataset.theme = theme, theme);
    await expect(image).toHaveCSS('mix-blend-mode', theme === 'dark' ? 'screen' : 'multiply');
    const filter = await image.evaluate(el => getComputedStyle(el).filter);
    expect(filter.includes('invert(1)')).toBe(theme === 'dark');
    await page.screenshot({ path: `tmp/sketch-${theme}-desktop.png` });
    await page.setViewportSize({ width: 390, height: 844 });
    await image.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `tmp/sketch-${theme}-phone.png` });
    await page.setViewportSize({ width: 1440, height: 1000 });
  }
});
