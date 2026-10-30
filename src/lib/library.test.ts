import {expect,it} from 'vitest';
import {getLibrary,localizedEditionHref,localizedUnitHref} from './library';
import {isEditionLanguage,EDITION_LANGUAGES} from './i18n';
import fs from 'node:fs';
import publications from '../data/pdf-publications.json';
import shakespearePlays from '../data/shakespeare-plays.json';
it('keeps complete, separate English and French Shakespeare collections',()=>{
  const works=getLibrary().authors.find(author=>author.slug==='shakespeare')!.works;
  expect(shakespearePlays).toHaveLength(38);
  expect(works.map(work=>work.slug).sort()).toEqual(shakespearePlays.map(play=>play.slug).sort());
  for(const play of shakespearePlays){
    const work=works.find(work=>work.slug===play.slug)!;
    for(const [code,suffix] of [['en','eng'],['fr','fra']]){
      const editions=work.editions.filter(edition=>edition.code===code);
      expect(editions,`${play.title}: ${code}`).toHaveLength(1);
      expect(editions[0].sourceFile).toBe(`shakespeare_${play.slug}_${suffix}.xml`);
      expect(editions[0].units.length).toBeGreaterThan(5);
    }
  }
});
it('retains the Hugo Kinsmen edition hierarchy, verse, collaborators and linked translator notes',()=>{
  const edition=getLibrary().authors.find(author=>author.slug==='shakespeare')!.works.find(work=>work.slug==='the-two-noble-kinsmen')!.editions.find(edition=>edition.code==='fr')!;
  expect(edition.sourceCredits).toContain('French translation and notes: François-Victor Hugo');
  expect(edition.sourceDescription).toContain('John Fletcher');
  expect(edition.units.filter(unit=>/^act-\d\/scene-\d+$/.test(unit.path))).toHaveLength(23);
  expect(edition.units.some(unit=>unit.path==='prologue-01')).toBe(true);
  expect(edition.units.some(unit=>unit.path==='epilogue-01')).toBe(true);
  const html=edition.units.map(unit=>unit.html).join('');
  expect(html).toContain('tei-line-group');
  expect(html).toContain('La légende de');
  expect(html).toContain('Palémon et Arcite');
  const epilogue=edition.units.find(unit=>unit.path==='epilogue-01')!.html;
  expect(epilogue).toContain('tei-note-ref');
  expect(epilogue).toContain('La légende de');
  expect(edition.units.find(unit=>unit.path==='prologue-01')!.html).toContain('irréalisable');
  const opening=edition.units.find(unit=>unit.path==='act-1/scene-1')!.html;
  expect(opening).not.toContain('::::::::');
  expect(opening).toContain('Le cortége jette des fleurs.');
});
it('exposes translation credits and source references from older TEI headers',()=>{
  const authors=getLibrary().authors;
  const french=authors.find(a=>a.slug==='shakespeare')!.works.find(w=>w.slug==='king-richard-ii')!.editions.find(e=>e.code==='fr')!;
  expect(french.sourceCredits).toContain('French translation: François Guizot');
  expect(french.sourceDescription).toContain('Project Gutenberg eBook #21277');
  expect(french.sourceLinks).toContainEqual({label:'Project Gutenberg #21277',href:'https://www.gutenberg.org/ebooks/21277'});
  const spanish=authors.find(a=>a.slug==='austen')!.works.find(w=>w.slug==='sense-and-sensibility')!.editions.find(e=>e.code==='es')!;
  expect(spanish.sourceCredits).toContain('translator: Anónima');
  expect(spanish.sourceLinks.some(s=>s.href==='https://es.wikisource.org/wiki/Sentido_y_sensibilidad')).toBe(true);
  const plato=authors.find(a=>a.slug==='plato')!.works.find(w=>w.slug==='theaetetus')!.editions.find(e=>e.code==='en')!;
  expect(plato.sourceCredits).toContain('translator: Harold North Fowler');
  expect(plato.sourceLinks.some(s=>s.href==='https://archive.org/details/b2900049x_0007')).toBe(true);
});
it('renders the visited French Richard II scene with stage directions and its translator note',()=>{
  const edition=getLibrary().authors.find(a=>a.slug==='shakespeare')!.works.find(w=>w.slug==='king-richard-ii')!.editions.find(e=>e.code==='fr')!;
  const scene=edition.units.find(u=>u.path==='act-3/scene-3')!;
  expect(scene.html).toContain('La trompette sonne pour demander un pourparler');
  expect(scene.html).not.toContain('tei-speaker">(L.');
  expect(scene.html).toContain('Fanfares.--Ils sortent.');
  expect(scene.html.replace(/<[^>]*>/g,'')).toContain('forteresse.--Fanfare.--RICHARD');
  expect(scene.html).toContain('Le jeu de mots entre civil et uncivil');
  expect(scene.previousPath).toBe('act-3/scene-2');
  expect(scene.nextPath).toBe('act-3/scene-4');
});
it('discovers named light and dark PDFs without losing legacy PDFs',()=>{
  const authors=getLibrary().authors;
  const scarlet=authors.find(author=>author.slug==='doyle')!.works.find(work=>work.slug==='a-study-in-scarlet')!.editions.find(edition=>edition.code==='en')!;
  expect(scarlet.pdfVariants?.map(pdf=>pdf.theme)).toEqual(['light','dark']);
  for(const pdf of scarlet.pdfVariants!){
    expect(pdf.file).toBe(`doyle_a-study-in-scarlet_eng-${pdf.theme}.pdf`);
    expect(pdf.href).toBe(`https://ianrastall.github.io/bookstacks-pdf/books/doyle/doyle_a-study-in-scarlet_eng/${pdf.file}`);
    expect(pdf.revision).toMatch(/^[a-f0-9]{64}$/);
  }
  expect(scarlet.pdfHref).toMatch(/-dark\.pdf$/);
  const emma=authors.find(author=>author.slug==='austen')!.works.find(work=>work.slug==='emma')!.editions.find(edition=>edition.code==='en')!;
  expect(emma.pdfHref).toMatch(/austen_emma_eng-dark\.pdf$/);
  expect(fs.existsSync('public/downloads/austen/austen_emma_eng/austen_emma_eng.pdf')).toBe(true);
});
it('offers source-matched light and dark PDFs for every indexed publication',()=>{
  let checked=0;
  for(const author of getLibrary().authors)for(const work of author.works)for(const edition of work.editions){
    if (!Object.hasOwn(publications, edition.sourceFile.replace(/^.*[\\/]/, '').replace(/\.xml$/, ''))) continue;
    checked++;
    expect(edition.pdfVariants?.map(pdf=>pdf.theme),edition.sourceFile).toEqual(['light','dark']);
    for(const pdf of edition.pdfVariants!)expect(pdf.href).toMatch(/^https:\/\/ianrastall\.github\.io\/bookstacks-pdf\/books\//);
  }
  expect(checked).toBeGreaterThan(0);
});
it('keeps every published edition, reading unit and language target addressable',()=>{const library=getLibrary();let editions=0,units=0;const targets=new Set<string>();for(const author of library.authors){for(const work of author.works){for(const edition of work.editions){editions++;expect(isEditionLanguage(edition.code)).toBe(true);expect(edition.units.length).toBeGreaterThan(0);const editionHref=localizedEditionHref(work,edition);expect(targets.has(editionHref)).toBe(false);targets.add(editionHref);for(const unit of edition.units){units++;expect(unit.html.length).toBeGreaterThan(0);const href=localizedUnitHref(work,edition,unit);expect(targets.has(href)).toBe(false);targets.add(href);}}}}expect(editions).toBe(library.editionCount);expect(units).toBe(library.unitCount);for(const language of EDITION_LANGUAGES)expect(library.authors.some(author=>author.works.some(work=>work.editions.some(edition=>edition.code===language.code)))).toBe(true);console.log(JSON.stringify({authors:library.authors.length,works:library.workCount,editions,units}));});
