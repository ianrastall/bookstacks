import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { expect, it } from 'vitest';
import { getLibrary, localizedUnitHref } from './library';
import selection from '../../tei/christie/selection.json';
import illustrations from '../../tei/christie/illustrations.json';

it('publishes all pinned Christie editions with complete navigation and original source figures', () => {
  const author = getLibrary().authors.find(author => author.slug === 'christie')!;
  expect(author.portrait).toBe('christie-agatha.png');
  expect(author.works).toHaveLength(17);
  for (const item of selection) {
    const work = author.works.find(work => work.slug === item.slug)!;
    expect(work).toBeDefined();
    expect(work.title).toBe(item.title);
    expect(work.editions).toHaveLength(1);
    const edition = work.editions[0];
    expect(edition.code).toBe('en');
    expect(edition.pdfVariants ?? []).toHaveLength(0);
    expect(edition.pdfHref).toBeUndefined();
    expect(edition.units).toHaveLength(item.sections);
    expect(edition.sourceLinks.some(source => source.href === `https://www.gutenberg.org/ebooks/${item.id}`)).toBe(true);
    for (const unit of edition.units) {
      expect(unit.html).not.toContain('tei-engraving');
      expect(unit.html).not.toContain('PROJECT GUTENBERG LICENSE');
      expect(unit.illustration?.src).toMatch(/^\/tei\/christie\/img\/.+\.jpg$/);
      expect(localizedUnitHref(work, edition, unit)).toContain(`/en/authors/christie/${item.slug}/`);
    }
    for (const figure of item.figures) {
      expect(edition.units.some(unit => unit.html.includes(figure.file))).toBe(true);
      const bytes = fs.readFileSync(path.join('tei/christie', figure.file));
      expect(createHash('sha256').update(bytes).digest('hex')).toBe(figure.sha256);
    }
  }
  const giants = author.works.find(work => work.slug === 'giants-bread')!.editions[0];
  expect(giants.toc.filter(node => node.kind === 'book')).toHaveLength(5);
  expect(giants.sourceDescription).toContain('Mary Westmacott');
  expect(giants.units.some(unit => unit.path === 'book-1/chapter-1')).toBe(true);
  expect(giants.units.some(unit => unit.path === 'book-5/chapter-5')).toBe(true);
  expect(giants.units.at(-1)!.html).toContain('There was nothing now to come between him and his work.');
  for (const slug of ['the-secret-adversary', 'the-man-in-the-brown-suit']) {
    expect(author.works.find(work => work.slug === slug)!.editions[0].units[1].path).toBe('chapter-1');
  }
});

it('provides a distinct checksum-verified sketch and preview for every Christie reading page', () => {
  const author = getLibrary().authors.find(author => author.slug === 'christie')!;
  const units = author.works.flatMap(work => work.editions.flatMap(edition => edition.units));
  expect(units).toHaveLength(363);
  expect(new Set(units.map(unit => unit.illustration!.src)).size).toBe(363);
  expect(illustrations).toHaveLength(363);
  expect(new Set(illustrations.map(illustration => illustration.sha256)).size).toBe(363);
  for (const unit of units) {
    expect(fs.existsSync(path.resolve(unit.illustration!.src.slice(1)))).toBe(true);
    expect(unit.illustration?.previewSrc).toMatch(/\.preview\.jpg$/);
  }
  for (const illustration of illustrations) {
    for (const file of [illustration, illustration.preview]) {
      const bytes = fs.readFileSync(path.join('tei/christie', file.file));
      expect(createHash('sha256').update(bytes).digest('hex')).toBe(file.sha256);
    }
  }
});
