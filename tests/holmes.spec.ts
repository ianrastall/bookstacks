import { expect, test } from '@playwright/test';

test('Holmes catalogue replacements retain legacy readers and a wider illustrated sidebar', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/?language=all&size=all');
  await page.locator('#book-search').fill('A Study in Scarlet');
  await expect(page.locator('[data-book-row]:visible')).toHaveCount(2);
  await page.goto('/authors/doyle');
  await expect(page.getByRole('link', { name: 'The Complete Sherlock Holmes', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'The Chronological Sherlock Holmes', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'A Study in Scarlet', exact: true })).toHaveCount(0);
  await page.getByRole('link', { name: 'The Complete Sherlock Holmes', exact: true }).click();
  await page.locator('.edition-contents a[href*="part-stud/"]').first().click();
  await expect(page.locator('.reader-content')).toContainText('Doctor of Medicine');
  const image = page.locator('.chapter-sidebar .reader-illustration img');
  await expect.poll(() => image.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  const sidebar = await page.locator('.chapter-sidebar').boundingBox();
  const article = await page.locator('.reader-content').boundingBox();
  expect(sidebar!.width).toBeGreaterThanOrEqual(300);
  expect(sidebar!.x).toBeGreaterThan(article!.x + article!.width);
  await page.screenshot({ path: 'tmp/holmes-reader-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.goto('/en/authors/doyle/the-chronological-sherlock-holmes');
  await page.locator('.edition-contents .toc-tree a[href*="story-the-gloria-scott"]').click();
  await expect(page.locator('.chapter-header h1')).toContainText('Gloria Scott');
  await page.goto('/en/authors/doyle/a-study-in-scarlet/part-1/chapter-1');
  await expect(page.locator('.reader-content')).toContainText('Doctor of Medicine');
});

test('both Holmes collections share the color counterpart for the same story', async ({ page }) => {
  const root = '/en/authors/doyle';
  const complete = `${root}/the-complete-sherlock-holmes`;
  await page.goto(`${complete}/story-the-five-orange-pips?ui=en`);
  await page.locator('#appearance-open').click();
  await page.getByLabel('Illustrations', { exact: true }).selectOption('photos');
  await page.keyboard.press('Escape');
  const sketch = page.locator('.reader-illustration.tei-engraving');
  const photo = page.locator('.reader-photo img');
  for (const order of ['complete', 'chronological']) {
    await page.goto(`${root}/the-${order}-sherlock-holmes/story-the-five-orange-pips?ui=en`);
    await expect(sketch).toBeHidden();
    await expect(photo).toBeVisible();
    await expect(photo).toHaveAttribute('src', '/tei/doyle/img/holmes/the-five-orange-pips-photo.jpg');
    await expect(photo).toHaveAttribute('alt', /Holmes and Watson.*envelope/);
    await photo.scrollIntoViewIfNeeded();
    await expect.poll(() => photo.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBe(640);
    await expect(page.locator('.reader-photo figcaption')).toHaveCount(0);
  }
  await page.goto(`${complete}/story-silver-blaze?ui=en`);
  await expect(sketch).toBeVisible();
  await expect(photo).toHaveCount(0);
});
