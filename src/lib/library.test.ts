import {expect,it} from 'vitest';
import {getLibrary,localizedEditionHref,localizedUnitHref} from './library';
import {isEditionLanguage,EDITION_LANGUAGES} from './i18n';
it('discovers named light and dark PDFs without losing legacy PDFs',()=>{
  const authors=getLibrary().authors;
  const scarlet=authors.find(author=>author.slug==='doyle')!.works.find(work=>work.slug==='a-study-in-scarlet')!.editions.find(edition=>edition.code==='en')!;
  expect(scarlet.pdfVariants?.map(pdf=>pdf.theme)).toEqual(['light','dark']);
  for(const pdf of scarlet.pdfVariants!){
    expect(pdf.file).toBe(`doyle_a-study-in-scarlet_eng-${pdf.theme}.pdf`);
    expect(pdf.href).toBe(`/downloads/doyle/doyle_a-study-in-scarlet_eng/${pdf.file}`);
    expect(pdf.revision).toMatch(/^[a-f0-9]{64}$/);
  }
  expect(scarlet.pdfHref).toMatch(/-dark\.pdf$/);
  const emma=authors.find(author=>author.slug==='austen')!.works.find(work=>work.slug==='emma')!.editions.find(edition=>edition.code==='en')!;
  expect(emma.pdfHref).toMatch(/austen_emma_eng\.pdf$/);
});
it('keeps every published edition, reading unit and language target addressable',()=>{const library=getLibrary();let editions=0,units=0;const targets=new Set<string>();for(const author of library.authors){for(const work of author.works){for(const edition of work.editions){editions++;expect(isEditionLanguage(edition.code)).toBe(true);expect(edition.units.length).toBeGreaterThan(0);const editionHref=localizedEditionHref(work,edition);expect(targets.has(editionHref)).toBe(false);targets.add(editionHref);for(const unit of edition.units){units++;expect(unit.html.length).toBeGreaterThan(0);const href=localizedUnitHref(work,edition,unit);expect(targets.has(href)).toBe(false);targets.add(href);}}}}expect(editions).toBe(library.editionCount);expect(units).toBe(library.unitCount);for(const language of EDITION_LANGUAGES)expect(library.authors.some(author=>author.works.some(work=>work.editions.some(edition=>edition.code===language.code)))).toBe(true);console.log(JSON.stringify({authors:library.authors.length,works:library.workCount,editions,units}));});
