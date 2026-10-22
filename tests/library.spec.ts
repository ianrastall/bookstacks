import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{await page.route('https://www.googletagmanager.com/**',r=>r.abort());await page.route('https://fonts.googleapis.com/**',r=>r.abort());});
for(const locale of ['en','fr','es','grc','ru','zh-Hans']) test(`library, edition and reading workflow: ${locale}`,async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/'+locale+'?ui='+locale);await expect(page.locator('html')).toHaveAttribute('lang',locale);await expect(page.locator('[data-book-row]')).toHaveCount(257);await page.locator('.library-nav a[href="/authors"]').click();await expect(page.locator('.author-card')).toHaveCount(18);
 for(const width of [1440,1024,768,390,320]){await page.setViewportSize({width,height:900});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`library overflow ${width}`).toBe(true);}
 await page.locator('.author-card').first().click();await page.locator('.book-card-main').first().click();await expect(page.locator('.toc-tree')).toBeVisible();await page.locator('.edition-actions a').first().click();await expect(page.locator('.reader-content')).toBeVisible();
 for(const width of [1440,1024,768,390,320]){await page.setViewportSize({width,height:900});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),{message:`reader overflow ${width}`}).toBe(true);}
 expect(errors).toEqual([]);
});
test('catalogue combines title, author and language filters with URL restoration',async({page})=>{
 await page.goto('/');await expect(page.locator('[data-book-row]:visible')).toHaveCount(16);await page.locator('#book-search').fill('Shakespeare');await page.locator('#book-language').selectOption('fr');await expect(page.locator('[data-book-row]:visible')).not.toHaveCount(0);await expect(page).toHaveURL(/language=fr/);await page.reload();await expect(page.locator('#book-search')).toHaveValue('Shakespeare');await expect(page.locator('#book-language')).toHaveValue('fr');await page.locator('#book-search').fill('no-book-xyz');await expect(page.locator('#book-empty')).toBeVisible();
});
test('catalogue paginates and author discovery filters titles',async({page})=>{
 await page.goto('/');const first=await page.locator('[data-book-row]:visible').first().innerText();await page.locator('#book-next').click();expect(await page.locator('[data-book-row]:visible').first().innerText()).not.toBe(first);await page.goto('/authors');await page.locator('#author-search').fill('Pride and Prejudice');await expect(page.locator('.author-card:visible')).toHaveCount(1);await expect(page.locator('.author-card:visible')).toContainText('Austen');
});
test('reading size, fonts, notes and chapter navigation remain usable',async({page})=>{
 await page.goto('/en/authors/aristotle/poetics/chapter-1');const article=page.locator('.reader-content');const before=await article.evaluate(el=>parseFloat(getComputedStyle(el).fontSize));
 for(let i=0;i<12;i++)await page.locator('[data-reader-action="larger"]').click();expect(await article.evaluate(el=>parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThan(before*1.4);
 await page.locator('[data-reader-font="serif"]').selectOption('platform');await page.reload();await expect(page.locator('[data-reader-font="serif"]')).toHaveValue('platform');expect(await article.evaluate(el=>parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThan(before*1.4);
 const note=page.locator('.tei-note-ref').first();await note.focus();await page.keyboard.press('Enter');await expect(page.locator('.tei-note-popover:visible')).toHaveCount(1);await page.keyboard.press('Escape');await expect(page.locator('.tei-note-popover:visible')).toHaveCount(0);
 await page.locator('.chapter-navigation a[rel="next"]').click();await expect(page).not.toHaveURL(/chapter-1$/);await expect(article).toBeVisible();
});
test('phone reader controls collapse while text stays visible',async({page})=>{
 await page.setViewportSize({width:390,height:900});await page.goto('/en/authors/bronte-anne/agnes-grey/chapter-1');await expect(page.locator('.reader-controls')).not.toHaveAttribute('open','');await page.locator('.reader-controls summary').click();await expect(page.locator('[data-reader-action="larger"]')).toBeVisible();await page.locator('.reader-controls summary').click();await expect(page.locator('.reader-content')).toBeVisible();
});
test('appearance supports theme, custom accent, reset and migrated palette',async({page})=>{
 await page.addInitScript(()=>{if(!localStorage.getItem('test-migration')){localStorage.setItem('bookstacks-palette','green');localStorage.setItem('test-migration','1');}});await page.goto('/');await page.locator('#appearance-open').click();await expect(page.locator('#accent-picker')).toHaveValue('#527052');await page.locator('#accent-reset').click();await page.keyboard.press('Escape');await page.reload();await page.locator('#appearance-open').click();await expect(page.locator('input[value="system"][name="accent-mode"]')).toBeChecked();await page.locator('input[value="custom"][name="accent-mode"]').check();await page.locator('#accent-picker').fill('#663399');await page.locator('#theme-choice').selectOption('light');await page.keyboard.press('Escape');await page.reload();await expect(page.locator('html')).toHaveAttribute('data-theme','light');expect(await page.evaluate(()=>localStorage.getItem('bookstacks-accent'))).toBe('#663399');await page.emulateMedia({forcedColors:'active'});await expect(page.locator('h1')).toBeVisible();
});
test('reading and notes work when browser storage is disabled',async({page})=>{
 await page.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage unavailable');}}));const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/en/authors/aristotle/poetics/chapter-1');await page.locator('[data-reader-action="larger"]').click();await page.locator('.tei-note-ref').first().click();await expect(page.locator('.tei-note-popover:visible')).toHaveCount(1);expect(errors).toEqual([]);
});
test('legacy reading links redirect to the same canonical edition',async({page})=>{
 await page.goto('/authors/bronte-anne/agnes-grey/en/chapter-1');await expect(page).toHaveURL(/\/en\/authors\/bronte-anne\/agnes-grey\/chapter-1/);await expect(page.locator('.reader-content')).toBeVisible();
});
for(const locale of ['en','fr','es','grc','ru','zh-Hans'])test(`downloads retain canonical TEI links: ${locale}`,async({page})=>{
 await page.goto('/'+locale+'/downloads');const link=page.locator(`tr:has(td[lang="${locale}"]) a[download$=".xml"]`).first();await expect(link).toBeVisible();const href=await link.getAttribute('href');const response=await page.request.get(href!);expect(response.status()).toBe(200);expect(await response.text()).toContain('http://www.tei-c.org/ns/1.0');
});
test('catalogue and book text are available without JavaScript',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false});const page=await context.newPage();await page.goto('http://127.0.0.1:4323/');expect(await page.locator('[data-book-row]').count()).toBeGreaterThan(200);await page.locator('.read-link').first().click();await expect(page.locator('.reader-content')).toBeVisible();await context.close();
});

test('phone footnotes stay within the viewport',async({page})=>{await page.setViewportSize({width:320,height:900});await page.goto('/en/authors/aristotle/poetics/chapter-1');await page.locator('.tei-note-ref').first().click();const note=page.locator('.tei-note-popover:visible');await expect(note).toBeVisible();const box=await note.boundingBox();expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(320);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);});


test('browser language localizes the entire catalogue without filtering books',async({browser})=>{
 const context=await browser.newContext({locale:'fr-CA'});const page=await context.newPage();
 await page.goto('http://127.0.0.1:4323/');await expect(page.locator('html')).toHaveAttribute('lang','fr');
 await expect(page.locator('h1')).toHaveText('Bibliothèque');await expect(page.locator('#book-language')).toHaveValue('');
 await expect(page.locator('[data-book-row]')).toHaveCount(257);await expect(page.locator('.library-languages')).toHaveCount(0);
 await page.locator('.library-nav a[href="/downloads"]').click();await expect(page.locator('h1')).toHaveText('Téléchargements');await expect(page.locator('[data-download-table] tbody tr')).toHaveCount(257);
 await context.close();
});

test('interface changes preserve the selected edition, chapter, contents and text',async({page})=>{
 await page.goto('/en/authors/aristotle/poetics/chapter-1');
 const article=page.locator('.reader-content');const original=await article.innerText();const next=await page.locator('a[rel="next"]').getAttribute('href');
 await page.locator('#interface-language').selectOption('ru');await expect(page.locator('html')).toHaveAttribute('lang','ru');
 await expect(page).toHaveURL(/\/en\/authors\/aristotle\/poetics\/chapter-1\?ui=ru$/);
 await expect(article).toHaveAttribute('lang','en');await expect(article).toHaveAttribute('translate','no');expect(await article.innerText()).toBe(original);
 await expect(page.locator('a[rel="next"]')).toContainText('Далее');expect(await page.locator('a[rel="next"]').getAttribute('href')).toBe(next);
 await page.locator('a[rel="next"]').click();await expect(page.locator('html')).toHaveAttribute('lang','ru');await expect(page).toHaveURL(/\/en\/authors\/aristotle\/poetics\/chapter-2/);
 await page.reload();await expect(page.locator('#interface-language')).toHaveValue('ru');
 await page.locator('#interface-language').selectOption('auto');await expect(page.locator('html')).toHaveAttribute('lang','en');expect(await page.evaluate(()=>localStorage.getItem('bookstacks-interface-language'))).toBeNull();
});

test('all author editions remain available regardless of interface or legacy author URL',async({page})=>{
 await page.goto('/grc/authors/aristotle?ui=es');await expect(page.locator('html')).toHaveAttribute('lang','es');
 const links=page.locator('.edition-list a');expect(await links.count()).toBeGreaterThan(1);
 const hrefs=await links.evaluateAll(links=>links.map(link=>link.getAttribute('href')));
 expect(hrefs.some(href=>href?.startsWith('/en/'))).toBe(true);expect(hrefs.some(href=>href?.startsWith('/grc/'))).toBe(true);
 await page.locator('#interface-language').selectOption('zh-Hans');expect(await links.evaluateAll(links=>links.map(link=>link.getAttribute('href')))).toEqual(hrefs);
});

test('explicit language works across navigation with unavailable storage',async({page})=>{
 await page.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new Error('Unavailable');}}));
 await page.goto('/?language=fr&q=Shakespeare');await page.locator('#interface-language').selectOption('es');
 await expect(page.locator('#book-language')).toHaveValue('fr');await expect(page.locator('#book-search')).toHaveValue('Shakespeare');
 await page.locator('.read-link:visible').first().click();await expect(page.locator('html')).toHaveAttribute('lang','es');await expect(page.locator('.reader-content')).toHaveAttribute('lang','fr');
 await page.reload();await expect(page.locator('html')).toHaveAttribute('lang','es');
});


test('unified pages fit narrow screens with long interface labels',async({page})=>{
 for(const path of ['/?ui=fr','/authors?ui=ru','/authors/shakespeare?ui=es','/downloads?ui=fr']){
  await page.goto(path);
  for(const width of [1440,390,320]){
   await page.setViewportSize({width,height:900});
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${path} overflow ${width}`).toBe(true);
  }
 }
 await page.setViewportSize({width:1440,height:1000});await page.goto('/?ui=fr');await page.screenshot({path:'tmp/i18n-library-desktop.png'});
 await page.setViewportSize({width:390,height:844});await page.goto('/authors/shakespeare?ui=es');await page.screenshot({path:'tmp/i18n-author-phone.png'});
});


test('book typography follows edition language independently of interface language',async({page})=>{
 await page.goto('/en/authors/aristotle/poetics/chapter-1?ui=en');
 const article=page.locator('.reader-content');const englishFont=await article.evaluate(el=>getComputedStyle(el).fontFamily);
 await page.locator('#interface-language').selectOption('zh-Hans');expect(await article.evaluate(el=>getComputedStyle(el).fontFamily)).toBe(englishFont);
 await page.goto('/?language=zh-Hans&ui=en');await page.locator('.read-link:visible').first().click();await expect(article).toHaveAttribute('lang','zh-Hans');
 const chineseFont=await article.evaluate(el=>getComputedStyle(el).fontFamily);expect(chineseFont).toContain('SimSun');
 await page.locator('#interface-language').selectOption('ru');expect(await article.evaluate(el=>getComputedStyle(el).fontFamily)).toBe(chineseFont);
});
