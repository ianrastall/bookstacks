import {test,expect} from '@playwright/test';

test('the French Shakespeare set includes Hugo’s complete Two Noble Kinsmen',async({page})=>{
 await page.goto('/fr/authors/shakespeare/the-two-noble-kinsmen?ui=en');
 await expect(page.locator('.edition-source-note')).toContainText('François-Victor Hugo');
 await expect(page.locator('.edition-source-note')).toContainText('John Fletcher');
 await page.goto('/fr/authors/shakespeare/the-two-noble-kinsmen/act-1/scene-1?ui=en');
 await expect(page.locator('.reader-content')).toHaveAttribute('lang','fr');
 await expect(page.locator('.tei-line-group')).not.toHaveCount(0);
 await expect(page.locator('.reader-content')).toContainText('Roses, dénuées d’épines aiguës');
 await page.goto('/fr/authors/shakespeare/the-two-noble-kinsmen/epilogue-01?ui=en');
 await page.locator('.tei-note-ref').first().click();
 await expect(page.locator('.tei-note-popover:visible')).toContainText('La légende de');
 await page.locator('#interface-language').selectOption('es');
 await expect(page).toHaveURL(/\/fr\/authors\/shakespeare\/the-two-noble-kinsmen\/epilogue-01\?ui=es$/);
 await expect(page.locator('.reader-content')).toHaveAttribute('lang','fr');
});

test('French translation credits and the visited Richard II scene remain accessible',async({page})=>{
 await page.goto('/fr/authors/shakespeare/king-richard-ii?ui=en');
 await expect(page.locator('.edition-source-note')).toContainText('French translation: François Guizot');
 await expect(page.locator('.edition-source-note')).toContainText('Project Gutenberg eBook #21277');
 await page.goto('/fr/authors/shakespeare/king-richard-ii/act-3/scene-3?ui=en');
 const article=page.locator('.reader-content');
 await expect(article).toHaveAttribute('lang','fr');
 await expect(article).toContainText('La trompette sonne pour demander un pourparler');
 await article.locator('.tei-note-ref').first().click();
 await expect(page.locator('.tei-note-popover:visible')).toContainText('Le jeu de mots entre civil et uncivil');
 await page.locator('#interface-language').selectOption('es');
 await expect(page).toHaveURL(/\/fr\/authors\/shakespeare\/king-richard-ii\/act-3\/scene-3\?ui=es$/);
 await expect(article).toHaveAttribute('lang','fr');
});

test('older source credits and links fit a narrow book page',async({page})=>{
 await page.setViewportSize({width:320,height:900});
 await page.goto('/es/authors/austen/sense-and-sensibility?ui=es');
 await expect(page.locator('.edition-source-credits')).toContainText('Anónima');
 await expect(page.locator('.edition-source-note a[href="https://es.wikisource.org/wiki/Sentido_y_sensibilidad"]')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
});
