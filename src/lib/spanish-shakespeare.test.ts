import {expect,it} from 'vitest';
import {getLibrary,localizedEditionHref} from './library';

it('adds the Spanish EMOTHE plays with their independent text, credits, licences and scene structures',()=>{
  const works=getLibrary().authors.find(author=>author.slug==='shakespeare')!.works;
  expect(works.flatMap(work=>work.editions).filter(edition=>edition.code==='es')).toHaveLength(11);
  for(const [slug,translator,scenes] of [['king-lear','Montoliu, Cipriano',26],['king-richard-iii','Sanderson, John D.',25]] as const){
    const work=works.find(work=>work.slug===slug)!;
    const edition=work.editions.find(edition=>edition.code==='es')!;
    expect(localizedEditionHref(work,edition)).toBe(`/es/authors/shakespeare/${slug}`);
    expect(edition.sourceCredits).toContain(`translator: ${translator}`);
    expect(edition.sourceDescription).toContain('CC BY-NC-ND 4.0');
    expect(edition.sourceLinks).toContainEqual({label:'CC BY-NC-ND 4.0',href:'https://creativecommons.org/licenses/by-nc-nd/4.0/'});
    expect(edition.units.filter(unit=>/^act-\d\/scene-\d+$/.test(unit.path))).toHaveLength(scenes);
    expect(edition.units.some(unit=>unit.path.startsWith('publication-note'))).toBe(true);
    const cast=edition.units.find(unit=>unit.path.startsWith('characters'))!;
    expect(cast.html).not.toContain('Alb-Corn');
    expect(cast.html).not.toContain('FANTASMA DE ENRIQUE IV');
    const opening=edition.units.find(unit=>unit.path==='act-1/scene-1')!;
    expect(opening.html).toContain('tei-stage-entrance');
    expect(opening.html).toContain('tei-stage-name');
  }
  const lear=works.find(work=>work.slug==='king-lear')!.editions.find(edition=>edition.code==='es')!;
  expect(lear.units.map(unit=>unit.html).join('')).toContain('tei-line-group');
  expect(lear.units.find(unit=>unit.path.startsWith('publication-note'))!.html).toContain('Rosa Durá Celma');
  const richard=works.find(work=>work.slug==='king-richard-iii')!.editions.find(edition=>edition.code==='es')!;
  expect(richard.units.find(unit=>unit.path.startsWith('publication-note'))!.html).toContain('John Strasberg');
  expect(richard.units.find(unit=>unit.path==='act-1/scene-1')!.html).toContain('Ya el invierno de nuestro descontento');
});
