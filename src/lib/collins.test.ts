import { expect, it } from 'vitest';
import { getLibrary } from './library';

it('adds the eight Wilkie Collins novels from Standard Ebooks', () => {
  const library = getLibrary();
  const author = library.authors.find(item => item.slug === 'collins')!;
  expect(author.name).toBe('Wilkie Collins');
  expect(author.portrait).toBe('');
  expect(author.works.map(work => work.slug).sort()).toEqual([
    'basil', 'man-and-wife', 'no-name', 'the-dead-secret', 'the-haunted-hotel',
    'the-law-and-the-lady', 'the-moonstone', 'the-woman-in-white',
  ]);
  const edition = (slug: string) => author.works.find(work => work.slug === slug)!.editions[0];

  // Epochs contain narratives, which contain chapters.
  const woman = edition('the-woman-in-white');
  expect(woman.units).toHaveLength(64);
  const opening = woman.units.find(unit => unit.path === 'part-1/narrative-01/chapter-1')!;
  expect(opening.context).toEqual(['The First Epoch', 'The Story Begun by Walter Hartright of Clement’s Inn, Teacher of Drawing']);
  expect(opening.html).toContain('what a woman’s patience can endure');
  expect(woman.toc.map(node => node.label)).toEqual(['Dedication', 'Preface to the Present Edition', 'The First Epoch', 'The Second Epoch', 'The Third Epoch']);

  // A period's narrator line opens its first chapter.
  const moonstone = edition('the-moonstone');
  const firstPeriod = moonstone.units.find(unit => unit.path === 'part-1/chapter-1')!;
  expect(firstPeriod.html).toContain('The events related by Gabriel Betteredge');
  expect(moonstone.units.at(-1)!.title).toBe('Chapter III. The Statement of Mr. Murthwaite (1850)');

  // Scenes keep the novel's continuous chapter numbering; subchapters stay on the chapter page.
  const manAndWife = edition('man-and-wife');
  expect(manAndWife.units).toHaveLength(61);
  const manuscript = manAndWife.units.find(unit => unit.title === 'Chapter LIV. The Manuscript')!;
  expect(manuscript.path).toBe('book-01/part-16/chapter-54');
  expect(manuscript.html).toContain('Arrived at that point in the narrative, Geoffrey looked up');

  // Chapter numbering restarts in each scene; place names open each scene.
  const noName = edition('no-name');
  expect(noName.units).toHaveLength(115);
  expect(noName.units.find(unit => unit.path === 'part-1/chapter-1')!.html).toContain('Combe-Raven, Somersetshire.');
  expect(noName.units.map(unit => unit.html).join(' ')).toContain('Private Surplus on the Week');

  expect(edition('basil').units).toHaveLength(30);
  expect(edition('the-dead-secret').units.at(-1)!.path).toBe('part-6/chapter-6');
  expect(edition('the-haunted-hotel').units.at(-1)!.title).toBe('Postscript');
  const law = edition('the-law-and-the-lady');
  expect(law.units).toHaveLength(51);
  expect(law.units.map(unit => unit.html).join(' ')).toContain('/tei/collins/img/the-law-and-the-lady-figure-1.png');
}, 120000);

it('shows text a container holds before its subdivisions', () => {
  const idiot = getLibrary().authors.find(item => item.slug === 'dostoevsky')!
    .works.find(work => work.slug === 'the-idiot')!.editions[0];
  expect(idiot.units.find(unit => unit.path === 'part-3/chapter-5/section-1')!.html)
    .toContain('Hippolyte, who had fallen asleep');
}, 120000);
