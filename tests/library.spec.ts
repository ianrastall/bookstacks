import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{await page.route('https://www.googletagmanager.com/**',r=>r.abort());await page.route('https://fonts.googleapis.com/**',r=>r.abort());});
for(const locale of ['en','fr','es','grc','ru','zh-Hans']) test(`library, edition and reading workflow: ${locale}`,async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/'+locale+'?ui='+locale);await expect(page.locator('html')).toHaveAttribute('lang',locale);await expect(page.locator('[data-book-row]')).toHaveCount(258);await page.locator('.library-nav a[href="/authors"]').click();await expect(page.locator('.author-card')).toHaveCount(18);
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


test('browser language initializes the book filter while the catalogue stays unified',async({browser})=>{
 const context=await browser.newContext({locale:'fr-CA'});const page=await context.newPage();
 await page.goto('http://127.0.0.1:4323/');await expect(page.locator('html')).toHaveAttribute('lang','fr');
 await expect(page.locator('h1')).toHaveText('Bibliothèque');await expect(page.locator('#book-language')).toHaveValue('fr');
 await expect(page.locator('[data-book-row]')).toHaveCount(258);await expect(page.locator('.library-languages')).toHaveCount(0);
 await page.locator('.library-nav a[href="/downloads"]').click();await expect(page.locator('h1')).toHaveText('Téléchargements');await expect(page.locator('[data-download-table] tbody tr')).toHaveCount(258);
 await context.close();
});

test('interface changes preserve the selected edition, chapter, contents and text',async({page})=>{
 await page.goto('/en/authors/aristotle/poetics/chapter-1');
 const article=page.locator('.reader-content');const original=await article.innerText();const next=await page.locator('a[rel="next"]').getAttribute('href');
 await page.locator('#interface-language').selectOption('ru');await expect(page.locator('html')).toHaveAttribute('lang','ru');
 await expect(page).toHaveURL(/\/en\/authors\/aristotle\/poetics\/chapter-1\?ui=ru$/);
 await expect(article).toHaveAttribute('lang','en');await expect(article).toHaveAttribute('translate','no');expect(await article.innerText()).toBe(original);
 await expect(page.locator('.tei-note-ref').first()).toHaveAttribute('lang','ru');await expect(page.locator('a[rel="next"]')).toContainText('Далее');expect(await page.locator('a[rel="next"]').getAttribute('href')).toBe(next);
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
 for(const path of ['/?ui=fr','/authors?ui=ru','/authors/shakespeare?ui=es','/downloads?ui=fr','/?ui=ta','/authors?ui=ar','/en/authors/aristotle/poetics/chapter-1?ui=ar','/downloads?ui=de']){
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

test('browser preferences select interface locales beyond the edition languages',async({browser})=>{
 for(const [preference,locale,heading] of [['de-DE','de','Bibliothek'],['zh-TW','zh-Hant','圖書館'],['pt','pt-BR','Biblioteca'],['ja-JP','ja','ライブラリ']]){
  const context=await browser.newContext({locale:preference});const page=await context.newPage();
  await page.goto('http://127.0.0.1:4323/');await expect(page.locator('html')).toHaveAttribute('lang',locale);
  await expect(page.locator('h1')).toHaveText(heading);await expect(page.locator('#interface-language')).toHaveValue('auto');
  await expect(page.locator('[data-book-row]')).toHaveCount(258);await context.close();
 }
});

test('right-to-left interfaces keep edition text left-to-right',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/en/authors/aristotle/poetics/chapter-1');const article=page.locator('.reader-content');const original=await article.innerText();
 await page.locator('#interface-language').selectOption('ar');
 await expect(page.locator('html')).toHaveAttribute('dir','rtl');await expect(page.locator('html')).toHaveAttribute('lang','ar');
 await expect(article).toHaveAttribute('dir','ltr');await expect(article).toHaveAttribute('lang','en');expect(await article.innerText()).toBe(original);
 await expect(page.locator('a[rel="next"]')).toContainText('التالي');
 expect(await article.evaluate(el=>getComputedStyle(el).direction)).toBe('ltr');
 await page.locator('#interface-language').selectOption('he');await expect(page.locator('html')).toHaveAttribute('lang','he');await expect(page.locator('html')).toHaveAttribute('dir','rtl');
 await page.locator('#interface-language').selectOption('de');await expect(page.locator('html')).toHaveAttribute('dir','ltr');await expect(page.locator('a[rel="next"]')).toContainText('Weiter');
 expect(errors).toEqual([]);
});

test('localized homepages for every interface locale work without JavaScript',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false});const page=await context.newPage();
 await page.goto('http://127.0.0.1:4323/de');await expect(page.locator('html')).toHaveAttribute('lang','de');await expect(page.locator('h1')).toHaveText('Bibliothek');
 expect(await page.locator('[data-book-row]').count()).toBe(258);
 await page.goto('http://127.0.0.1:4323/ar');await expect(page.locator('html')).toHaveAttribute('dir','rtl');await expect(page.locator('h1')).toHaveText('المكتبة');
 await expect(page.locator('.book-title').first()).toHaveAttribute('dir','ltr');
 expect(await page.locator('link[rel="alternate"][hreflang]').count()).toBe(41);
 await context.close();
});


test('page size combines with filters, restores from URL and remembers all languages', async ({page}) => {
 await page.goto('/?language=all');
 await page.locator('#book-page-size').selectOption('32');
 await expect(page.locator('[data-book-row]:visible')).toHaveCount(32);
 await page.locator('#book-next').click();
 await page.locator('#book-page-size').selectOption('64');
 await expect(page.locator('#book-page')).toHaveText('1 / 5');
 await page.reload();await expect(page.locator('#book-page-size')).toHaveValue('64');
 await page.locator('#book-page-size').selectOption('all');
 await expect(page.locator('[data-book-row]:visible')).toHaveCount(258);
 await expect(page.locator('#book-pagination')).toBeHidden();
 await page.locator('#book-language').selectOption('zh-Hans');
 await expect(page.locator('[data-book-row]:visible')).toHaveCount(3);
 await page.locator('#book-language').selectOption('');await page.reload();
 await expect(page.locator('#book-language')).toHaveValue('');
 await expect(page.locator('[data-book-row]:visible')).toHaveCount(258);
 await page.goto('/?language=all');await expect(page.locator('#book-page-size')).toHaveValue('all');
});

test('interface overrides never change the initial browser book preference or explicit filter', async ({browser}) => {
 const context=await browser.newContext({locale:'fr-CA'});const page=await context.newPage();
 await page.goto('http://127.0.0.1:4323/?ui=ru');await expect(page.locator('#book-language')).toHaveValue('fr');
 await page.locator('#interface-language').selectOption('en');await expect(page.locator('#book-language')).toHaveValue('fr');
 await page.goto('http://127.0.0.1:4323/?language=all');await expect(page.locator('#book-language')).toHaveValue('');
 await context.close();
 const unsupported=await browser.newContext({locale:'ja-JP'});const other=await unsupported.newPage();
 await other.goto('http://127.0.0.1:4323/');await expect(other.locator('#book-language')).toHaveValue('');await unsupported.close();
});

test('sans cascade and width persist through reloads in the same tab', async ({page}) => {
 await page.setViewportSize({width:1920,height:1080});
 await page.goto('/en/authors/aristotle/poetics/chapter-1');
 const article=page.locator('.reader-content');
 const before=await article.evaluate(el=>getComputedStyle(el).fontFamily);expect(before).toMatch(/^Constantia/);
 await page.locator('[data-reader-font="sans"]').selectOption('screen');
 const after=await article.evaluate(el=>getComputedStyle(el).fontFamily);expect(after).not.toBe(before);expect(after).toMatch(/^Verdana/);
 await expect(page.locator('[data-reader-font="serif"]')).toHaveValue('');
 const width=(await article.boundingBox())!.width;
 for(let i=0;i<8;i++)await page.locator('[data-reader-action="wide"]').click();
 expect((await article.boundingBox())!.width).toBeGreaterThan(width+200);
 await page.reload();expect(await article.evaluate(el=>getComputedStyle(el).fontFamily)).toBe(after);
 await expect(page.locator('[data-reader-font="serif"]')).toHaveValue('');
 await expect(page.locator('[data-reader-font="sans"]')).toHaveValue('screen');
 expect((await article.boundingBox())!.width).toBeGreaterThan(width+200);
});

test('fullscreen provides an exit and preserves book text and notes', async ({page}) => {
 await page.goto('/en/authors/aristotle/poetics/chapter-1');
 const article=page.locator('.reader-content');const original=await article.innerText();
 const toggle=page.locator('.reader-fullscreen');await toggle.click();
 await expect(toggle).toHaveAttribute('aria-pressed','true');await expect(toggle).toHaveText('Exit fullscreen');
 await expect(page.locator('.chapter-container')).toHaveClass(/reader-expanded/);
 expect(await article.innerText()).toBe(original);
 await page.locator('.tei-note-ref').first().click();await expect(page.locator('.tei-note-popover:visible')).toHaveCount(1);
 await toggle.click();await expect(toggle).toHaveAttribute('aria-pressed','false');
 await page.evaluate(()=>Object.defineProperty(document,'fullscreenEnabled',{value:false,configurable:true}));
 await toggle.click();await page.keyboard.press('Escape');await expect(toggle).toHaveAttribute('aria-pressed','false');
});

test('Legge English edition has all 81 chapters and independent Chinese edition links',async({page})=>{
 await page.goto('/en/authors/laozi/tao-te-ching');
 await expect(page.locator('.edition-source-note')).toContainText('James Legge');
 const chapters=page.locator('.toc-tree a');
 expect(await chapters.count()).toBe(81);
 await chapters.first().click();await expect(page.locator('.reader-content')).toContainText('The Tao that can be trodden');
 await expect(page.locator('.reader-content .tei-line')).not.toHaveCount(0);
 await expect(page.locator('.other-editions a')).toHaveAttribute('href','/zh-Hans/authors/laozi/tao-te-ching');
});


test('both font menus apply to book paragraphs and clear the inactive selection', async ({page}) => {
 await page.addInitScript(()=>{
  localStorage.setItem('bookstacks-reader-serif','garamond');
  localStorage.setItem('bookstacks-reader-sans','trebuchet');
 });
 await page.goto('/en/authors/bronte-anne/agnes-grey/chapter-1');
 const serif=page.locator('[data-reader-font="serif"]');const sans=page.locator('[data-reader-font="sans"]');
 const paragraph=page.locator('.reader-content .tei-paragraph').first();
 const family=()=>paragraph.evaluate(el=>getComputedStyle(el).fontFamily);
 const cdp=await page.context().newCDPSession(page);
 await cdp.send('DOM.enable');await cdp.send('CSS.enable');
 const {root}=await cdp.send('DOM.getDocument');
 const {nodeId}=await cdp.send('DOM.querySelector',{nodeId:root.nodeId,selector:'.reader-content .tei-paragraph'});
 const renderedFonts=async()=>{
  const {fonts}=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});
  return fonts.filter((font:{glyphCount:number})=>font.glyphCount>0).map((font:{familyName:string})=>font.familyName).sort();
 };
 const defaultFonts=await renderedFonts();expect(defaultFonts.length).toBeGreaterThan(0);
 await sans.selectOption('screen');await expect.poll(renderedFonts).not.toEqual(defaultFonts);
 await serif.selectOption('classic');await expect.poll(renderedFonts).toEqual(defaultFonts);
 await expect(serif).toHaveValue('classic');await expect(sans).toHaveValue('');expect(await family()).toMatch(/^Constantia/);
 for(const [choice,font] of [['office','Segoe UI'],['screen','Verdana'],['trebuchet','Trebuchet MS']]) {
  await sans.selectOption(choice);await expect(serif).toHaveValue('');expect(await family()).toContain(font);
 }
 await serif.selectOption('times');await expect(sans).toHaveValue('');expect(await family()).toMatch(/^"Times New Roman"/);
 await serif.selectOption('classic');expect(await family()).toMatch(/^Constantia/);
 await sans.selectOption('screen');await page.locator('a[rel="next"]').click();
 await expect(serif).toHaveValue('');await expect(sans).toHaveValue('screen');expect(await family()).toMatch(/^Verdana/);
 await serif.selectOption('times');
 await page.goBack();await expect(serif).toHaveValue('times');await expect(sans).toHaveValue('');expect(await family()).toMatch(/^"Times New Roman"/);
 await page.goForward();await expect(serif).toHaveValue('times');await expect(sans).toHaveValue('');expect(await family()).toMatch(/^"Times New Roman"/);
 const fresh=await page.context().newPage();
 await fresh.route('https://www.googletagmanager.com/**',route=>route.abort());
 await fresh.goto('/en/authors/bronte-anne/agnes-grey/chapter-1');
 await expect(fresh.locator('[data-reader-font="serif"]')).toHaveValue('classic');
 await expect(fresh.locator('[data-reader-font="sans"]')).toHaveValue('');
 expect(await fresh.locator('.reader-content').evaluate(el=>getComputedStyle(el).fontFamily)).toMatch(/^Constantia/);
 await fresh.close();
});

test('Chinese sans reading text retains its script fonts independently of interface language',async({page})=>{
 await page.goto('/zh-Hans/authors/laozi/tao-te-ching/part-1/chapter-1?ui=en');
 const article=page.locator('.reader-content');
 expect(await article.evaluate(el=>getComputedStyle(el).fontFamily)).toContain('SimSun');
 await page.locator('[data-reader-font="sans"]').selectOption('screen');
 const sans=await article.evaluate(el=>getComputedStyle(el).fontFamily);expect(sans).toContain('Microsoft YaHei');expect(sans).toContain('Verdana');expect(sans).not.toContain('SimSun');
 await page.locator('#interface-language').selectOption('ru');expect(await article.evaluate(el=>getComputedStyle(el).fontFamily)).toBe(sans);
 await page.locator('[data-reader-font="serif"]').selectOption('classic');expect(await article.evaluate(el=>getComputedStyle(el).fontFamily)).toContain('SimSun');
});


test('structural titles use title case in contents, reader headings and context without changing routes or TEI',async({page})=>{
 await page.goto('/en/authors/bronte-anne/agnes-grey');
 const first=page.locator('.toc-link').filter({hasText:'Chapter I. The Parsonage'});
 await expect(first).toHaveCount(1);await expect(first).toHaveAttribute('href','/en/authors/bronte-anne/agnes-grey/chapter-1');
 await first.click();await expect(page.locator('.chapter-header h1')).toHaveText('Chapter I. The Parsonage');
 await expect(page).toHaveTitle('Chapter I. The Parsonage · Agnes Grey · Bookstacks');
 await page.goto('/en/authors/dostoevsky/crime-and-punishment');
 await expect(page.locator('.toc-section-title').filter({hasText:/^\s*Part II\s*$/})).toHaveCount(1);
 const partChapter=page.locator('.toc-group').filter({has:page.locator('.toc-section-title').filter({hasText:/^\s*Part II\s*$/})}).last().locator('.toc-link').first();
 await partChapter.click();await expect(page.locator('.reader-context')).toContainText('Part II');
 expect(await page.locator('.reader-context').evaluate(el=>getComputedStyle(el).textTransform)).toBe('none');
 await page.locator('#interface-language').selectOption('fr');await expect(page.locator('.reader-context')).toContainText('Part II');
 const source=await page.request.get('/tei/bronte-anne/bronte-anne_agnes-grey_eng.xml');
 expect(await source.text()).toContain('<head>CHAPTER I.<lb/> THE PARSONAGE</head>');
});


test('session font storage can be unavailable or invalid without breaking the reader',async({browser})=>{
 for(const blocked of [true,false]){
  const context=await browser.newContext();const page=await context.newPage();const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('https://www.googletagmanager.com/**',route=>route.abort());
  await page.addInitScript(block=>{
   if(block)Object.defineProperty(window,'sessionStorage',{get(){throw new Error('Unavailable');}});
   else if(!sessionStorage.getItem('bookstacks-reader-font'))sessionStorage.setItem('bookstacks-reader-font','sans:invalid-cascade');
  },blocked);
  await page.goto('http://127.0.0.1:4323/en/authors/aristotle/poetics/chapter-1');
  await expect(page.locator('[data-reader-font="serif"]')).toHaveValue('classic');
  expect(await page.locator('.reader-content').evaluate(el=>getComputedStyle(el).fontFamily)).toMatch(/^Constantia/);
  await page.locator('[data-reader-font="sans"]').selectOption('screen');
  expect(await page.locator('.reader-content').evaluate(el=>getComputedStyle(el).fontFamily)).toMatch(/^Verdana/);
  if(!blocked){
   await page.reload();await expect(page.locator('[data-reader-font="sans"]')).toHaveValue('screen');
  }
  expect(errors).toEqual([]);await context.close();
 }
});
