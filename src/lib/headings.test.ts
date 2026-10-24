import { expect, it } from 'vitest';
import { DOMParser } from '@xmldom/xmldom';
import { headingTitleCase, normalizeHeadingNode } from './headings';

it('formats structural and descriptive titles, retaining numerals and English minor words', () => {
  expect(headingTitleCase('CHAPTER I. THE PARSONAGE', 'en')).toBe('Chapter I. The Parsonage');
  expect(headingTitleCase('CHAPTER II. FIRST LESSONS IN THE ART OF INSTRUCTION', 'en')).toBe('Chapter II. First Lessons in the Art of Instruction');
  expect(headingTitleCase('VOLUME III', 'en')).toBe('Volume III');
  expect(headingTitleCase('Part iv: a tale of two cities', 'en')).toBe('Part IV: A Tale of Two Cities');
  expect(headingTitleCase('the story of McDonald and O’NEILL', 'en')).toBe('The Story of McDonald and O’Neill');
  expect(headingTitleCase('XML: THE BEGINNING AND THE END', 'en')).toBe('XML: The Beginning and the End');
  expect(headingTitleCase('THE DEVIL—AND OTHER STORIES', 'en')).toBe('The Devil—And Other Stories');
  expect(headingTitleCase('Bekker page 1288b', 'en')).toBe('Bekker Page 1288b');
});

it('uses edition language casing and leaves Chinese text intact', () => {
  expect(headingTitleCase('CAPÍTULO II', 'es')).toBe('Capítulo II');
  expect(headingTitleCase('ACTE DEUXIÈME', 'fr')).toBe('Acte Deuxième');
  expect(headingTitleCase('ЧАСТЬ ПЕРВАЯ', 'ru')).toBe('Часть Первая');
  expect(headingTitleCase('第一章', 'zh-Hans')).toBe('第一章');
});

it('preserves inline markup, notes and attributes when a word crosses text nodes', () => {
  const source = '<head xml:id="original"><hi rend="italic">CHAP</hi>TER IV. THE <hi>PARSONAGE</hi><note>DO NOT CHANGE THIS NOTE</note></head>';
  const document = new DOMParser().parseFromString(source, 'application/xml');
  const heading = document.documentElement!;
  normalizeHeadingNode(heading, 'en');
  expect(heading.getAttribute('xml:id')).toBe('original');
  expect(document.getElementsByTagName('hi')[0].textContent).toBe('Chap');
  expect(document.getElementsByTagName('hi')[0].getAttribute('rend')).toBe('italic');
  expect(document.getElementsByTagName('hi')[1].textContent).toBe('Parsonage');
  expect(document.getElementsByTagName('note')[0].textContent).toBe('DO NOT CHANGE THIS NOTE');
  expect(heading.textContent).toBe('Chapter IV. The ParsonageDO NOT CHANGE THIS NOTE');
});
