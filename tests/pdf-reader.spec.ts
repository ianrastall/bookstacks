import {test,expect} from '@playwright/test';
import path from 'node:path';
const reader='/en/authors/doyle/a-study-in-scarlet/part-1/chapter-1';
test.beforeEach(async({page})=>{
 await page.route('https://www.googletagmanager.com/**',r=>r.abort());
 if(!process.env.CI)await page.route('https://ianrastall.github.io/bookstacks-pdf/books/**',route=>{
  const relative=new URL(route.request().url()).pathname.split('/bookstacks-pdf/books/')[1];
  return route.fulfill({path:path.resolve('../bookstacks-pdf/books',relative),contentType:'application/pdf',headers:{'access-control-allow-origin':'*'}});
 });
});
async function openPdf(page:import('@playwright/test').Page){
 await page.locator('[data-reading-mode="pdf"]').click();
 await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-ready','true',{timeout:30000});
}
async function goPage(page:import('@playwright/test').Page,n:number){
 await page.locator('[data-pdf-page]').fill(String(n));await page.locator('[data-pdf-page]').press('Enter');
 await expect(page.locator('.pdf-rendered-page')).toHaveAttribute('data-page-number',String(n),{timeout:30000});
}
test('home reading links lead to the same reading surface in either format',async({page})=>{
 await page.goto('/');await page.locator('#book-search').fill('Poetics');
 const row=page.locator('[data-book-row]:visible').first();
 const online=await row.getByRole('link',{name:'Read online',exact:true}).getAttribute('href');
 const pdf=await row.getByRole('link',{name:'Read PDF',exact:true}).getAttribute('href');
 expect(pdf).toBe(`${online}?view=pdf`);
 await row.getByRole('link',{name:'Read PDF',exact:true}).click();
 await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-ready','true',{timeout:30000});
 await expect(page.locator('.chapter-sidebar')).toBeVisible();
 expect(await page.locator('iframe').count()).toBe(0);
});
test('PDF replaces the online column without moving the sidebar or changing the chapter',async({page})=>{
 await page.setViewportSize({width:1440,height:950});await page.goto(reader);
 const text=await page.locator('[data-online-content]').innerText();
 const before=await page.locator('[data-online-content]').boundingBox();
 const sidebar=await page.locator('.chapter-sidebar').boundingBox();
 await openPdf(page);await expect(page.locator('[data-online-content]')).toBeHidden();
 const after=await page.locator('[data-pdf-pane]').boundingBox();
 expect(Math.abs(before!.x-after!.x)).toBeLessThan(1);expect(Math.abs(before!.width-after!.width)).toBeLessThan(1);
 expect((await page.locator('.chapter-sidebar').boundingBox())!.x).toBe(sidebar!.x);
 expect(new URL(page.url()).pathname).toBe(reader);expect(await page.evaluate(()=>document.fullscreenElement)).toBeNull();
 await page.locator('[data-reading-mode="online"]').click();await expect(page.locator('[data-online-content]')).toBeVisible();
 expect(await page.locator('[data-online-content]').innerText()).toBe(text);expect(new URL(page.url()).pathname).toBe(reader);
 await expect(page.locator('[data-pdf-pane]')).toBeHidden();
});
test('page navigation, contents, search and apostrophe text remain available in the column',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(`${reader}?view=pdf`);
 await expect(page.locator('[data-pdf-page]')).toHaveAttribute('max','102',{timeout:30000});
 await goPage(page,7);await expect(page.locator('.pdf-text-layer')).toContainText('don’t');
 expect(await page.locator('.pdf-text-layer').textContent()).not.toContain('don’ t');
 await page.locator('[data-pdf-next]').click();await expect(page.locator('.pdf-rendered-page')).toHaveAttribute('data-page-number','8');
 await page.locator('[data-pdf-previous]').click();await expect(page.locator('.pdf-rendered-page')).toHaveAttribute('data-page-number','7');
 await page.locator('[data-pdf-outline]').selectOption({label:'— Chapter II. The Science of Deduction.'});
 await expect(page.locator('.pdf-rendered-page')).toHaveAttribute('data-page-number','11');
 await goPage(page,1);await page.locator('[data-pdf-find]').fill('Jezail');await page.locator('[data-pdf-find]').press('Enter');
 await expect(page.locator('.pdf-text-layer')).toContainText('Jezail',{timeout:30000});
 expect(errors).toEqual([]);
});
test('switching from expanded online reading returns PDF to the normal site column',async({page})=>{
 await page.goto(reader);await page.locator('.reader-fullscreen').click();
 await expect(page.locator('.chapter-container')).toHaveClass(/reader-expanded/);
 await openPdf(page);await expect(page.locator('.chapter-container')).not.toHaveClass(/reader-expanded/);
 expect(await page.evaluate(()=>document.fullscreenElement)).toBeNull();
 expect(await page.locator('.site-header').evaluate(el=>(el as HTMLElement).inert)).toBe(false);
});
test('the site theme selects the matching PDF and preserves the page on reload',async({page})=>{
 await page.goto(`${reader}?view=pdf`);await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-theme','dark',{timeout:30000});
 await goPage(page,7);await page.locator('#appearance-open').click();await page.locator('#theme-choice').selectOption('light');await page.keyboard.press('Escape');
 await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-theme','light');await expect(page.locator('.pdf-rendered-page')).toHaveAttribute('data-page-number','7');
 await page.reload();await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-theme','light',{timeout:30000});await expect(page.locator('.pdf-rendered-page')).toHaveAttribute('data-page-number','7');
});
test('phone PDF uses the same column, keeps the mode switch and preserves interface choices',async({page})=>{
 await page.setViewportSize({width:320,height:850});await page.goto(`${reader}?view=pdf`);
 await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-ready','true',{timeout:30000});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 await goPage(page,7);await page.locator('#interface-language').selectOption('fr');
 await expect(page.locator('html')).toHaveAttribute('lang','fr');await expect(page.locator('.pdf-rendered-page')).toHaveAttribute('data-page-number','7');
 await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('lang','en');
 await page.locator('.reader-controls summary').click();await page.locator('[data-reading-mode="online"]').click();await expect(page.locator('[data-online-content]')).toBeVisible();
});
test('legacy book-page PDF links open the inline reader in the same edition',async({page})=>{
 await page.goto('/en/authors/doyle/a-study-in-scarlet?ui=fr#pdf-reader');
 await expect(page).toHaveURL(/part-1\/chapter-1\?view=pdf&ui=fr$/);
 await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-ready','true',{timeout:30000});
});
test('online reading remains usable after PDF loading fails and with storage unavailable',async({page})=>{
 await page.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new Error('Unavailable');}}));
 await page.route('https://ianrastall.github.io/bookstacks-pdf/books/**',r=>r.abort());
 await page.goto(`${reader}?view=pdf`);await expect(page.locator('[data-pdf-error]')).toBeVisible({timeout:30000});
 await page.locator('[data-reading-mode="online"]').click();await expect(page.locator('[data-online-content]')).toContainText('In the year 1878');
});
for(const[language,route]of[['zh-Hans','/zh-Hans/authors/lu-xun/call-to-arms/preface'],['grc','/grc/authors/aristotle/poetics/chapter-1'],['ru','/ru/authors/turgenev/mumu/mumu']])test(`PDF canvas retains source language: ${language}`,async({page})=>{
 // Enter through the book's primary reading link so source-specific chapter paths remain authoritative.
 const book=route.substring(0,route.lastIndexOf('/'));await page.goto(book);
 const start=await page.locator('.edition-actions a').first().getAttribute('href');await page.goto(start!+'?view=pdf&ui=en');
 await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('data-pdf-ready','true',{timeout:30000});await expect(page.locator('[data-pdf-pane]')).toHaveAttribute('lang',language);
 await expect(page.locator('.pdf-text-layer')).not.toBeEmpty();
});
