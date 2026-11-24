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
    await expect(sketch).toHaveCSS('mix-blend-mode', theme === 'light' ? 'multiply' : 'normal');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await page.screenshot({ path: `tmp/christie-reader-mobile-${theme}.png` });
  }
  await page.goto('/authors/christie');
  await expect(page.getByRole('link', { name: 'Giants’ Bread', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'The Plymouth Express Affair', exact: true })).toBeVisible();
});

test('Poirot Investigates switches to its own photos with scene descriptions', async ({ page }) => {
  await page.goto('/en/authors/christie/poirot-investigates/story-1?ui=en');
  const sketch = page.locator('.chapter-sidebar .tei-engraving img');
  const photo = page.locator('.chapter-sidebar .reader-photo img');
  const style = page.getByLabel('Illustrations', { exact: true });
  await expect(sketch).toBeVisible();
  await expect(photo).toBeHidden();

  await page.locator('#appearance-open').click();
  await style.selectOption('photos');
  await page.keyboard.press('Escape');
  await expect(sketch).toBeHidden();
  await expect(photo).toBeVisible();
  await expect(photo).toHaveAttribute('src', '/tei/christie/img/poirot-investigates-001-photo.jpg');
  await expect(photo).toHaveAttribute('alt', /woman looks up at a London terrace/);
  await photo.scrollIntoViewIfNeeded();
  await expect.poll(() => photo.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBe(640);

  await page.locator('.chapter-navigation a[rel="next"]').click();
  await expect(photo).toBeVisible();
  await expect(photo).toHaveAttribute('src', '/tei/christie/img/poirot-investigates-002-photo.jpg');
  await expect(photo).toHaveAttribute('alt', /Poirot fastens a leather valise/);
});
