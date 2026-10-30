import {expect,test} from '@playwright/test';

for(const slug of ['king-lear','king-richard-iii'])test(`Spanish ${slug} keeps its edition, source terms and drama layout`,async({page})=>{
  await page.goto(`/es/authors/shakespeare/${slug}?ui=en`);
  await expect(page.getByText('CC BY-NC-ND 4.0',{exact:false}).first()).toBeVisible();
  await expect(page.locator('a[href="https://creativecommons.org/licenses/by-nc-nd/4.0/"]').first()).toBeVisible();
  await page.goto(`/es/authors/shakespeare/${slug}/act-1/scene-1?ui=fr`);
  await expect(page.locator('html')).toHaveAttribute('lang','fr');
  await expect(page.locator('.reader-content')).toHaveAttribute('lang','es');
  const entrance=page.locator('.reader-content .tei-stage-entrance').first();
  await expect(entrance).toHaveCSS('text-align','center');
  await expect(entrance).toHaveCSS('font-style','italic');
  await expect(entrance).toHaveText(/^\[[\s\S]*\]$/);
  await expect(entrance.locator('.tei-stage-name').first()).toHaveCSS('font-style','normal');
  if(slug==='king-lear'){
    const exit=page.locator('.reader-content .tei-stage-exit').first();
    await expect(exit).toHaveCSS('text-align','right');
    const inline=page.locator('.tei-speech .tei-paragraph .tei-stage').first();
    await expect(inline).toHaveCSS('display','inline');
  }
  await page.setViewportSize({width:320,height:850});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  await entrance.scrollIntoViewIfNeeded();
  await page.screenshot({path:`tmp/spanish-${slug}-phone.png`});
  await expect(page).toHaveURL(new RegExp(`/es/authors/shakespeare/${slug}/act-1/scene-1`));
});
