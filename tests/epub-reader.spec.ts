import {test,expect} from '@playwright/test';
const scarlet='/en/authors/doyle/a-study-in-scarlet/part-1/chapter-1';
test.beforeEach(async({page})=>{await page.route('https://www.googletagmanager.com/**',r=>r.abort());});
async function ready(page:import('@playwright/test').Page){await expect(page.locator('[data-epub-pane]')).toHaveAttribute('data-epub-ready','true',{timeout:30000});}
const frame=(page:import('@playwright/test').Page)=>page.frameLocator('.epub-reading-frame');

test('EPUB replaces the same reading column and returns to the original HTML chapter',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));await page.goto(scarlet);
  const online=page.locator('[data-online-content]'),before=await online.boundingBox(),original=await online.innerText();
  await page.locator('[data-reading-mode=epub]').click();await ready(page);
  const after=await page.locator('[data-epub-pane]').boundingBox();expect(Math.abs(before!.x-after!.x)).toBeLessThan(1);expect(Math.abs(before!.width-after!.width)).toBeLessThan(1);
  await expect(page.locator('.chapter-sidebar')).toBeVisible();expect(new URL(page.url()).pathname).toBe(scarlet);expect(await page.evaluate(()=>document.fullscreenElement)).toBeNull();
  await expect(frame(page).locator('body')).toContainText('In the year 1878');
  expect(await page.locator('.epub-reading-frame').getAttribute('sandbox')).toBe('allow-same-origin');
  await page.locator('[data-reading-mode=pdf]').click();await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-ready','true',{timeout:30000});await expect(page.locator('[data-epub-pane]')).toBeHidden();
  await page.locator('[data-reading-mode=online]').click();await expect(online).toBeVisible();expect(await online.innerText()).toBe(original);expect(errors).toEqual([]);
});
test('EPUB contents, search, text size, themes and saved chapter work without replacing the file',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  const requests:string[]=[];page.on('request',r=>{if(r.url().includes('.epub?'))requests.push(r.url());});
  await page.goto(scarlet+'?view=epub');await ready(page);const firstHeight=await page.locator('.epub-reading-frame').evaluate(el=>el.clientHeight);
  await page.locator('[data-epub-larger]').click();await expect(frame(page).locator('html')).toHaveCSS('font-size','22px');await expect.poll(()=>page.locator('.epub-reading-frame').evaluate(el=>el.clientHeight)).toBeGreaterThan(firstHeight);
  await page.locator('#appearance-open').click();await page.locator('#theme-choice').selectOption('light');await page.keyboard.press('Escape');await expect(frame(page).locator('html')).toHaveAttribute('data-theme','light');expect(requests).toHaveLength(1);
  await page.locator('[data-epub-next]').click();await expect(frame(page).locator('h1')).toContainText('Chapter II.');await expect(frame(page).locator('em').first()).toHaveCSS('font-style','italic');
  await page.reload();await ready(page);await expect(frame(page).locator('h1')).toContainText('Chapter II.');
  await page.locator('[data-epub-find]').fill('Populus me sibilat');await page.locator('[data-epub-find]').press('Enter');await expect(frame(page).locator('mark')).toContainText('Populus me sibilat');
  await expect(frame(page).locator('.tei-line-group').filter({hasText:'Ipse domi'}).first()).toBeVisible();
  await page.locator('[data-epub-contents]').selectOption('EPUB/chapter-0001.xhtml');await expect(frame(page).locator('h1')).toContainText('Chapter I.');
  await page.evaluate(()=>{const el=document.querySelector('.epub-reading-frame')!;scrollTo({top:scrollY+el.getBoundingClientRect().top+(el as HTMLElement).offsetHeight*.35,behavior:'instant'});});
  await expect.poll(()=>page.evaluate(()=>{const key=Object.keys(localStorage).find(k=>k.startsWith('bookstacks-epub-location:'));return key?JSON.parse(localStorage.getItem(key)!).fraction:0;})).toBeCloseTo(.35,1);
  await page.reload();await ready(page);await expect.poll(()=>page.locator('.epub-reading-frame').evaluate(el=>-el.getBoundingClientRect().top/(el as HTMLElement).offsetHeight)).toBeCloseTo(.35,1);
  expect(errors).toEqual([]);
});
test('EPUB reflows on a phone and an interface locale change leaves the English edition selected',async({page})=>{
  await page.setViewportSize({width:320,height:850});await page.goto(scarlet+'?view=epub');await ready(page);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  expect(await frame(page).locator('html').evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
  await page.locator('#interface-language').selectOption('fr');await expect(page.locator('html')).toHaveAttribute('lang','fr');await expect(frame(page).locator('html')).toHaveAttribute('lang','en');
  await expect(frame(page).locator('body')).toContainText('In the year 1878');
});
test('a failed EPUB load leaves online reading available',async({page})=>{
  await page.route('**/*.epub?*',r=>r.abort());await page.goto(scarlet+'?view=epub');await expect(page.locator('[data-epub-error]')).toBeVisible();
  await page.locator('[data-reading-mode=online]').click();await expect(page.locator('[data-online-content]')).toContainText('In the year 1878');
});
test('the catalogue exposes EPUB for the chronological collection and downloads one themed file',async({page})=>{
  await page.goto('/');await page.locator('#book-search').fill('Chronological Sherlock Holmes');const row=page.locator('[data-book-row]:visible').first();
  const online=await row.getByRole('link',{name:'Read online',exact:true}).getAttribute('href');expect(await row.getByRole('link',{name:'Read EPUB',exact:true}).getAttribute('href')).toBe(online+'?view=epub');
  await row.getByRole('link',{name:'Read EPUB',exact:true}).click();await ready(page);await expect(frame(page).locator('body')).toContainText('Gloria Scott');
  const download=page.locator('[data-epub-pane] a[download]');expect(await download.getAttribute('href')).toMatch(/_eng\.epub\?revision=/);expect(await download.getAttribute('download')).not.toMatch(/-(light|dark)/);
});
