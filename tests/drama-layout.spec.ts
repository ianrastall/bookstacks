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
