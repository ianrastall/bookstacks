import fs from 'node:fs';
import path from 'node:path';
import { DOMParser } from '@xmldom/xmldom';
import { expect, it } from 'vitest';
import { getLibrary, localizedUnitHref } from './library';

it('publishes the selected Poe volume with complete Pym navigation and local illustrated plates', () => {
  const author = getLibrary().authors.find(author => author.slug === 'poe')!;
  expect(author.portrait).toBe('poe-edgar-allan.png');
  expect(author.works).toHaveLength(1);
  const work = author.works[0];
  expect(work.title).toBe('Collected Works of Mystery and Horror');
  expect(work.editions).toHaveLength(1);
  const edition = work.editions[0];
  expect(edition.code).toBe('en');
  expect(edition.sourceLinks).toHaveLength(6);
  const pym = edition.units.filter(unit => unit.path.startsWith('part-pym/'));
  expect(pym).toHaveLength(27);
  expect(pym.filter(unit => /\/chapter-\d+$/.test(unit.path))).toHaveLength(25);
  expect(pym.some(unit => unit.path.endsWith('/chapter-25'))).toBe(true);
  expect(pym.some(unit => unit.path.endsWith('/notes-notes'))).toBe(true);
  expect(edition.units.filter(unit => unit.path.startsWith('story-'))).toHaveLength(34);
  const plates = edition.units.map(unit => unit.illustration!);
  expect(plates).toHaveLength(61);
  expect(new Set(plates.map(plate => plate.src)).size).toBe(36);
  for (const plate of plates) {
    expect(fs.existsSync(path.resolve(process.cwd(), plate.src.slice(1)))).toBe(true);
  }
  expect(pym.find(unit => unit.path.endsWith('/chapter-1'))?.illustration?.src).toContain('pym-grampus.png');
  expect(pym.find(unit => unit.path.endsWith('/chapter-25'))?.illustration?.src).toContain('the-narrative-of-arthur-gordon-pym');
  for (const unit of edition.units) {
    expect(unit.html).not.toContain('tei-engraving');
    expect(localizedUnitHref(work, edition, unit)).toContain('/en/authors/poe/collected-works-of-mystery-and-horror/');
  }
  const source = fs.readFileSync('tei/poe/poe_collected-works-of-mystery-and-horror_eng.xml', 'utf8');
  const doc = new DOMParser().parseFromString(source, 'application/xml');
  expect(doc.getElementsByTagName('graphic').length).toBe(43);
  for (const graphic of Array.from(doc.getElementsByTagName('graphic'))) {
    expect(fs.existsSync(path.resolve('tei/poe', graphic.getAttribute('url')!))).toBe(true);
  }
  expect(pym.find(unit => unit.path.endsWith('/chapter-23'))?.html).toContain('pym-source-1.jpg');
  expect(pym.find(unit => unit.path.endsWith('/notes-notes'))?.html).toContain('pym-source-7.jpg');
  expect(doc.getElementsByTagName('text')[0].getAttribute('xml:lang')).toBe('en');
});
