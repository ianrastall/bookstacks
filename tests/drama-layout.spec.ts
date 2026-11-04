import {expect,test} from '@playwright/test';

for(const locale of ['en','fr'])test(`Shakespeare movement cues have distinct alignment and name styles: ${locale}`,async({page})=>{
 await page.setViewportSize({width:1440,height:1000});
 const scene=locale==='en'?'act-01/scene-01':'act-1/scene-1';
 await page.goto(`/${locale}/authors/shakespeare/a-midsummer-nights-dream/${scene}?ui=en`);
 const entrance=page.locator('.reader-content .tei-stage-entrance').first();
 const exit=page.locator('.reader-content .tei-stage-exit').first();
 for(const [cue,align] of [[entrance,'center'],[exit,'right']] as const){
  await expect(cue).toHaveCSS('text-align',align);
  await expect(cue).toHaveCSS('text-align-last',align);
  await expect(cue).toHaveCSS('font-style','italic');
  await expect(cue).toHaveText(/^\[[\s\S]*\]$/);
  for (const bracket of await cue.locator('.tei-stage-bracket').all()) {
   await expect(bracket).toHaveCSS('font-style','normal');
  }
  await expect(cue.locator('.tei-stage-bracket')).toHaveCount(2);
  const name=cue.locator('.tei-stage-name').first();
  await expect(name).toHaveCSS('font-style','normal');
  const label=(await name.textContent())!;expect(label).toBe(label.toLocaleUpperCase(locale));
 }
 await entrance.scrollIntoViewIfNeeded();await page.screenshot({path:`tmp/drama-${locale}-desktop.png`});
 await page.setViewportSize({width:320,height:850});
 await expect(exit).toHaveCSS('text-align','right');
 const edge=await exit.evaluate(element=>{
  const walker=document.createTreeWalker(element,NodeFilter.SHOW_TEXT);const rects:DOMRect[]=[];
  while(walker.nextNode())if(walker.currentNode.textContent?.trim()){
   const range=document.createRange();range.selectNodeContents(walker.currentNode);
   rects.push(...Array.from(range.getClientRects()).filter(rect=>rect.width>0));
  }
  return {inkEnd:Math.max(...rects.map(rect=>rect.right)),edge:element.getBoundingClientRect().right};
 });
 expect(Math.abs(edge.edge-edge.inkEnd)).toBeLessThan(2);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 await exit.scrollIntoViewIfNeeded();await page.screenshot({path:`tmp/drama-${locale}-phone.png`});
});

test('Hugo entrances are centered and directions belong to the character’s part',async({page})=>{
 await page.goto('/fr/authors/shakespeare/the-two-noble-kinsmen/act-1/scene-1?ui=en');
 const opening=page.locator('.reader-content .tei-stage-entrance').first();
 await expect(opening).toContainText('Musique. Entre HYMEN');
 await expect(opening).toHaveCSS('text-align','center');
 const direction=page.locator('.tei-speech > .tei-paragraph > .tei-stage-business').first();
 await expect(direction).toHaveText('[à THÉSÉE.]');
 await expect(direction).toHaveCSS('display','inline');
 await expect(direction).toHaveCSS('font-style','italic');
 await expect(direction.locator('.tei-stage-bracket').first()).toHaveCSS('font-style','normal');
 await expect(direction.locator('.tei-stage-name')).toHaveCSS('font-style','normal');
});

test('Spanish scene introductions italicize the words around character names',async({page})=>{
 await page.goto('/es/authors/shakespeare/as-you-like-it/act-1/scene-1?ui=en');
 const cue=page.locator('.tei-drama-stage.tei-stage-setting').first();
 await expect(cue).toHaveCSS('font-style','italic');
 await expect(cue).toHaveCSS('text-align','center');
 await expect(cue).toContainText('Entran ORLANDO y ADAM');
 await expect(cue.locator('.tei-stage-name').filter({hasText:'ORLANDO'})).toHaveCSS('font-style','normal');
});

test('a labeled song has symmetric insets and follows its upright speaker label', async ({ page }) => {
 await page.goto('/en/authors/shakespeare/as-you-like-it/act-05/scene-03?ui=en');
 const song = page.locator('.tei-song').filter({ hasText: 'It was a lover and his lass' });
 const speaker = page.locator('.tei-speaker').filter({ hasText: /^PAGES$/ });
 await expect(speaker).toHaveCSS('font-style', 'normal');
 await expect(speaker).toHaveCSS('margin-bottom', '0px');
 await expect(song).toHaveCSS('font-style', 'italic');
 await expect(song).toHaveCSS('text-align', 'left');
 await expect(song).toHaveCSS('margin-top', '0px');
 const insets = await song.evaluate(element => {
  const style = getComputedStyle(element);
  const size = parseFloat(style.fontSize);
  return [parseFloat(style.marginLeft) / size, parseFloat(style.marginRight) / size];
 });
 expect(insets).toEqual([2, 2]);
 await expect(song.locator('.tei-line').first()).toHaveCSS('padding-inline-start', '0px');
});

test('As You Like It shares plates across editions and accounts for the French scene split', async ({ page }) => {
 const cases = [
  ['en', 'act-01/scene-01', 'orchard', /orchard/],
  ['es', 'act-1/scene-1', 'orchard', /huerto/],
  ['fr', 'act-3/scene-3', 'rosalind-reading', /Rosalinde.*poème/],
  ['es', 'act-2/scene-2', 'arden', /sendero/],
 ] as const;
 await page.setViewportSize({ width: 390, height: 844 });
 for (const [locale, route, plate, alt] of cases) {
  await page.goto(`/${locale}/authors/shakespeare/as-you-like-it/${route}?ui=en`);
  const figure = page.locator('.chapter-sidebar .chapter-navigation + .reader-illustration');
  await expect(figure).toHaveAttribute('lang', locale);
  const image = figure.locator('img');
  await expect(image).toHaveAttribute('src', `/tei/shakespeare/img/as-you-like-it/${plate}.jpg`);
  await expect(image).toHaveAttribute('alt', alt);
  await image.scrollIntoViewIfNeeded();
  await expect.poll(() => image.evaluate((element: HTMLImageElement) => element.naturalWidth)).toBe(640);
 }
});

test('the saved photo preference replaces the sketch and falls back where needed', async ({ page }) => {
 const scene = '/fr/authors/shakespeare/as-you-like-it/act-3/scene-3?ui=en';
 await page.goto(scene);
 await page.evaluate(() => document.documentElement.dataset.theme = 'dark');
 const engraving = page.locator('.reader-illustration.tei-engraving img');
 await expect(engraving).toHaveCSS('filter', 'grayscale(1)');
 await expect(engraving).toHaveCSS('mix-blend-mode', 'normal');
 const variant = page.locator('.reader-photo');
 const photo = variant.locator('img');
 await expect(variant).toHaveAttribute('lang', 'fr');
 await expect(variant.locator('figcaption')).toHaveText('Interprétation photographique (générée par IA)');
 await expect(photo).toBeHidden();
 await page.locator('#appearance-open').click();
 const setting = page.getByLabel('Illustrations', { exact: true });
 await expect(setting).toHaveValue('sketches');
 await setting.selectOption('photos');
 await page.keyboard.press('Escape');
 await expect(engraving).toBeHidden();
 await expect(photo).toBeVisible();
 await expect(photo).toHaveAttribute('src', /rosalind-reading-photo\.jpg$/);
 await expect(photo).toHaveAttribute('alt', /Rosalinde.*poème/);
 await expect(photo).toHaveCSS('filter', 'none');
 await photo.scrollIntoViewIfNeeded();
 await expect.poll(() => photo.evaluate((element: HTMLImageElement) => element.naturalWidth)).toBe(640);
 await page.reload();
 await expect(photo).toBeVisible();
 await page.locator('.chapter-navigation a[rel="next"]').click();
 await expect(photo).toHaveAttribute('src', /country-wedding-photo\.jpg$/);
 await expect(photo).toBeVisible();
 await page.route('**/arden-photo.jpg', route => route.abort());
 await page.goto('/es/authors/shakespeare/as-you-like-it/act-2/scene-2?ui=en');
 await page.locator('.chapter-navigation').scrollIntoViewIfNeeded();
 await expect(engraving).toBeVisible();
 await expect(engraving).toHaveAttribute('src', /\/arden\.jpg$/);
 await expect(variant).toHaveCount(0);
 await page.goto('/en/authors/christie/the-mysterious-affair-at-styles/chapter-3?ui=en');
 await expect(engraving).toBeVisible();
 await expect(variant).toHaveCount(0);
 await page.locator('#appearance-open').click();
 await expect(setting).toHaveValue('photos');
 await setting.selectOption('sketches');
 await page.keyboard.press('Escape');
 await page.goto(scene);
 await expect(engraving).toBeVisible();
 await expect(photo).toBeHidden();
});
