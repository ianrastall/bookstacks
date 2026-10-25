import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { DOMParser } from '@xmldom/xmldom';
import { expect, it } from 'vitest';
import { getCatalogueLibrary, getLibrary, localizedUnitHref } from './library';

const selection = JSON.parse(fs.readFileSync('tei/doyle/holmes/selection.json', 'utf8'));
const reports = JSON.parse(fs.readFileSync('tei/doyle/holmes/import-report.json', 'utf8'));

it('retains the source paragraph text after serializing both collected TEI files', () => {
  const verification = JSON.parse(fs.readFileSync('tei/doyle/holmes/text-verification.json', 'utf8'));
  for (const report of reports) {
    const doc = new DOMParser().parseFromString(fs.readFileSync(`tei/doyle/${report.file}`, 'utf8'), 'application/xml');
    const divisions = Array.from(doc.getElementsByTagNameNS('http://www.tei-c.org/ns/1.0', 'div'));
    for (const expected of verification) {
      const story = selection.stories.find((story: { slug: string }) => story.slug === expected.slug);
      const division = divisions.find(div => div.getAttribute('xml:id') === `${story.slug}-${story.sourceId}`)!;
      const paragraphs = Array.from(division.getElementsByTagNameNS('http://www.tei-c.org/ns/1.0', 'p'))
        .map(p => (p.textContent ?? '').replace(/\s+/gu, ' ').trim());
      expect(createHash('sha256').update(paragraphs.join('\n')).digest('hex'), `${report.file}: ${story.slug}`).toBe(expected.textSha256);
    }
  }
});

it('collects exactly the same 63 works in publication and career orders without removing source editions', () => {
  const author = getLibrary().authors.find(author => author.slug === 'doyle')!;
  const catalogue = getCatalogueLibrary().authors.find(author => author.slug === 'doyle')!;
  expect(author.works.find(work => work.slug === 'a-study-in-scarlet')).toBeDefined();
  expect(catalogue.works.find(work => work.slug === 'a-study-in-scarlet')).toBeUndefined();
  const collections = ['the-complete-sherlock-holmes', 'the-chronological-sherlock-holmes']
    .map(slug => catalogue.works.find(work => work.slug === slug)!);
  expect(collections.every(Boolean)).toBe(true);
  expect(new Set(reports[0].order)).toEqual(new Set(reports[1].order));
  expect(reports[0].order).toHaveLength(63);
  expect(reports[0].order[0]).toBe('a-study-in-scarlet');
  expect(reports[0].order.at(-1)).toBe('the-adventure-of-shoscombe-old-place');
  expect(reports[1].order[0]).toBe('the-adventure-of-the-gloria-scott');
  expect(reports[1].order.at(-1)).toBe('his-last-bow');
  for (const [index, field] of ['publication', 'career'].entries()) {
    const dates = reports[index].order.map((slug: string) => selection.stories.find((s: { slug: string }) => s.slug === slug)[field]);
    expect(dates).toEqual([...dates].sort());
  }
  for (const work of collections) {
    const edition = work.editions[0];
    expect(edition.code).toBe('en');
    expect(edition.units).toHaveLength(115);
    expect(edition.units.filter(unit => unit.path.startsWith('story-'))).toHaveLength(59);
    expect(edition.units.filter(unit => unit.path.startsWith('part-stud/'))).toHaveLength(14);
    expect(edition.units.filter(unit => unit.path.startsWith('part-sign/'))).toHaveLength(12);
    expect(edition.units.filter(unit => unit.path.startsWith('part-houn/'))).toHaveLength(15);
    expect(edition.units.filter(unit => unit.path.startsWith('part-vall/'))).toHaveLength(15);
    expect(edition.units.some(unit => unit.title === 'The Story of the Lost Special')).toBe(true);
    expect(edition.units.filter(unit => /Cardboard Box/.test(unit.title))).toHaveLength(1);
    for (const [i, unit] of edition.units.entries()) {
      expect(unit.previousPath).toBe(edition.units[i - 1]?.path);
      expect(unit.nextPath).toBe(edition.units[i + 1]?.path);
      expect(unit.illustration).toBeDefined();
      expect(fs.existsSync(path.resolve(unit.illustration!.src.slice(1)))).toBe(true);
      expect(fs.existsSync(path.resolve(unit.illustration!.previewSrc!.slice(1)))).toBe(true);
      expect(localizedUnitHref(work, edition, unit)).toContain(`/en/authors/doyle/${work.slug}/`);
    }
    expect(new Set(edition.units.map(unit => unit.illustration!.src)).size).toBe(115);
    expect(edition.sourceLinks.some(link => link.href.includes('gutenberg.org'))).toBe(true);
  }
  for (const [filename, hash] of Object.entries(selection.sources)) {
    expect(createHash('sha256').update(fs.readFileSync(`tei/doyle/${filename}`)).digest('hex')).toBe(hash);
  }
});
