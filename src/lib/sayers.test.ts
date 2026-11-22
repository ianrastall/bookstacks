import { expect, it } from 'vitest';
import { getLibrary } from './library';

it('adds the Lord Peter Wimsey books published through 1930', () => {
  const author = getLibrary().authors.find(item => item.slug === 'sayers')!;
  expect(author.portrait).toBe('sayers-dorothy.png');
  expect(author.works.map(work => work.slug).sort()).toEqual([
    'clouds-of-witness', 'lord-peter-views-the-body', 'strong-poison',
    'the-unpleasantness-at-the-bellona-club', 'unnatural-death', 'whose-body',
  ]);
  const edition = (slug: string) => author.works.find(work => work.slug === slug)!.editions[0];

  const whoseBody = edition('whose-body');
  expect(whoseBody.units.filter(unit => unit.path.startsWith('chapter-'))).toHaveLength(13);
  expect(whoseBody.units.map(unit => unit.html).join(' ')).toContain('tei-note-ref');

  const clouds = edition('clouds-of-witness');
  expect(clouds.units[0].title).toBe('Clouds of Witness');
  expect(clouds.units[0].html).toContain('the Riddlesdale Mystery');
  const chapterOne = clouds.units.find(unit => unit.path === 'chapter-1')!;
  expect(chapterOne.title).toBe('Chapter I. Of His Malice Aforethought');
  expect(chapterOne.html).toContain('O, who hath done this deed?');
  expect(chapterOne.html).toContain('/tei/sayers/img/clouds-of-witness-figure-1.png');

  const unnatural = edition('unnatural-death');
  expect(unnatural.units[0].title).toBe('Part I. The Medical Problem');
  expect(unnatural.units[0].html).toContain('whereof it is born');
  expect(unnatural.units.at(-1)!.title).toBe('Genealogical Table');

  const lordPeter = edition('lord-peter-views-the-body');
  expect(lordPeter.units.filter(unit => unit.path.startsWith('story-'))).toHaveLength(12);
  expect(lordPeter.units.at(-1)!.html).toContain('lord-peter-views-the-body-figure-4.png');

  expect(edition('the-unpleasantness-at-the-bellona-club').units.filter(unit => unit.path.startsWith('chapter-'))).toHaveLength(23);
  const strongPoison = edition('strong-poison');
  expect(strongPoison.units).toHaveLength(23);
  expect(strongPoison.sourceDescription).toContain('First published in 1930');
});
