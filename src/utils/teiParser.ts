import fs from 'node:fs';
import path from 'node:path';
import { DOMParser } from '@xmldom/xmldom';

const LANG_NAMES: Record<string, string> = {
  fr: 'French',
  ru: 'Russian',
  de: 'German',
  it: 'Italian',
  la: 'Latin',
  en: 'English',
  es: 'Spanish'
};

const TOC_LANG_ORDER = ['en', 'es', 'ru'] as const;
type TocLang = typeof TOC_LANG_ORDER[number];

type Version = {
  id: string;
  lang: string;
  html: string;
  title: string;
};

type Chapter = {
  n: string;
  title: string;
  html: string;
  versions: Version[];
  toc?: TocLocation;
  id?: string;
  href?: string;
  [key: string]: any;
};

type TocNode = {
  key: string;
  labels: string[];
  labelByLang: Partial<Record<TocLang, string>>;
  children: TocNode[];
  chapter?: Chapter;
};

type TocLocation = {
  kind: 'volume' | 'epilogue';
  volume: number | null;
  part: number;
  chapter: number;
  sortKey: number;
};

type TocSection = {
  kind: 'volume' | 'epilogue';
  volume: number | null;
  part: number;
  count: number;
  start: number;
  end: number;
  sortKey: number;
};

type LanguageFileMap = Partial<Record<TocLang, string>>;

type ParseTeiBookOptions = {
  /**
   * Optional explicit language-file map. Use this when the files are not named
   * like 2600-ru.xml, 2600-en.xml, and 2600-es.xml in the same directory.
   */
  languageFilePaths?: LanguageFileMap;

  /**
   * Auto-discover sibling language XML files beside filePath. Defaults to true.
   * This reads only XML files, never .shtml files.
   */
  discoverSiblingLanguageFiles?: boolean;

  /**
   * Preferred HTML/body language for chapter.html. Defaults to the language of
   * filePath, then Russian, then the first available version.
   */
  preferredLang?: TocLang;
};

const EN_PART_WORDS = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five'];
const ES_PART_WORDS = ['Cero', 'Primera', 'Segunda', 'Tercera', 'Cuarta', 'Quinta'];
const RU_PART_WORDS = ['нулевая', 'первая', 'вторая', 'третья', 'четвертая', 'пятая'];

const WAR_AND_PEACE_SECTIONS: TocSection[] = (() => {
  const raw: Array<Omit<TocSection, 'start' | 'end' | 'sortKey'>> = [
    { kind: 'volume', volume: 1, part: 1, count: 25 },
    { kind: 'volume', volume: 1, part: 2, count: 21 },
    { kind: 'volume', volume: 1, part: 3, count: 19 },

    { kind: 'volume', volume: 2, part: 1, count: 16 },
    { kind: 'volume', volume: 2, part: 2, count: 21 },
    { kind: 'volume', volume: 2, part: 3, count: 26 },
    { kind: 'volume', volume: 2, part: 4, count: 13 },
    { kind: 'volume', volume: 2, part: 5, count: 22 },

    { kind: 'volume', volume: 3, part: 1, count: 23 },
    { kind: 'volume', volume: 3, part: 2, count: 39 },
    { kind: 'volume', volume: 3, part: 3, count: 34 },

    { kind: 'volume', volume: 4, part: 1, count: 16 },
    { kind: 'volume', volume: 4, part: 2, count: 19 },
    { kind: 'volume', volume: 4, part: 3, count: 19 },
    { kind: 'volume', volume: 4, part: 4, count: 20 },

    { kind: 'epilogue', volume: null, part: 1, count: 16 },
    { kind: 'epilogue', volume: null, part: 2, count: 12 }
  ];

  let start = 1;
  return raw.map((section, index) => {
    const current: TocSection = {
      ...section,
      start,
      end: start + section.count - 1,
      sortKey: index + 1
    };
    start = current.end + 1;
    return current;
  });
})();

/**
 * Parse one canonical TEI language file, automatically merging sibling
 * 2600-*.xml files when present. The three XML files are the source of truth;
 * .shtml files are intentionally ignored here.
 */
export function parseTeiBook(filePath: string, options: ParseTeiBookOptions = {}) {
  try {
    const absolutePath = path.resolve(filePath);
    const primaryDoc = parseXmlFile(absolutePath);
    const primaryLang = getDocumentLang(primaryDoc, absolutePath);

    const languageFilePaths = collectLanguageFilePaths(absolutePath, primaryLang, options);
    const parsedBooks: ParsedBook[] = [];

    for (const lang of TOC_LANG_ORDER) {
      const langPath = languageFilePaths[lang];
      if (!langPath || !fs.existsSync(langPath)) continue;
      const doc = langPath === absolutePath ? primaryDoc : parseXmlFile(langPath);
      parsedBooks.push(parseSingleLanguageBook(doc, langPath, lang));
    }

    if (parsedBooks.length === 0) {
      parsedBooks.push(parseSingleLanguageBook(primaryDoc, absolutePath, primaryLang || 'ru'));
    }

    const primaryBook = parsedBooks.find((book) => book.filePath === absolutePath) || parsedBooks[0];
    const title = primaryBook.title || 'Unknown Title';
    const author = primaryBook.author || 'Unknown Author';
    const persons = mergeRegistries(parsedBooks.map((book) => book.persons));
    const places = mergeRegistries(parsedBooks.map((book) => book.places));
    const preferredLang = options.preferredLang || primaryBook.lang || primaryLang || 'ru';
    const chapters = mergeLanguageChapters(parsedBooks, preferredLang);
    const tocTree = buildTocTree(chapters);

    return { title, author, persons, places, chapters, tocTree };
  } catch (error) {
    console.error(`Failed to parse TEI file at ${filePath}:`, error);
    throw error;
  }
}

/**
 * Explicit multi-file entry point. This is useful for build scripts that want
 * to be very clear that the canonical source is ru/en/es XML rather than one
 * combined XML file.
 */
export function parseTeiBookSet(languageFilePaths: LanguageFileMap, preferredLang: TocLang = 'ru') {
  const firstPath = languageFilePaths[preferredLang]
    || languageFilePaths.ru
    || languageFilePaths.en
    || languageFilePaths.es;

  if (!firstPath) {
    throw new Error('parseTeiBookSet requires at least one language XML file.');
  }

  return parseTeiBook(firstPath, {
    languageFilePaths,
    discoverSiblingLanguageFiles: false,
    preferredLang
  });
}

type ParsedBook = {
  filePath: string;
  lang: TocLang;
  title: string;
  author: string;
  persons: Record<string, any>;
  places: Record<string, any>;
  chapters: Chapter[];
};

function parseXmlFile(filePath: string): any {
  const xml = fs.readFileSync(filePath, 'utf-8');
  return new DOMParser({
    onError: (level: string, msg: string) => {
      if (level === 'warning') {
        console.warn(`XML Warning in ${filePath}: ${msg}`);
      } else if (level === 'fatalError') {
        throw new Error(`Fatal XML parsing error in ${filePath}: ${msg}`);
      } else {
        console.error(`XML Error in ${filePath}: ${msg}`);
      }
    }
  }).parseFromString(xml, 'text/xml');
}

function parseSingleLanguageBook(doc: any, filePath: string, fallbackLang: TocLang): ParsedBook {
  const lang = getDocumentLang(doc, filePath) || fallbackLang;
  const titleNode = doc.getElementsByTagName('title')[0];
  const authorNode = doc.getElementsByTagName('author')[0]?.getElementsByTagName('persName')[0];
  const title = titleNode?.textContent?.trim() || 'Unknown Title';
  const author = authorNode?.textContent?.trim() || 'Unknown Author';
  const persons = parsePersonRegistry(doc);
  const places = parsePlaceRegistry(doc);
  const chapters = parseChapters(doc, persons, places, lang);

  return { filePath: path.resolve(filePath), lang, title, author, persons, places, chapters };
}

function collectLanguageFilePaths(absolutePath: string, primaryLang: TocLang | null, options: ParseTeiBookOptions): LanguageFileMap {
  const result: LanguageFileMap = {};

  if (primaryLang) result[primaryLang] = absolutePath;

  for (const lang of TOC_LANG_ORDER) {
    const explicit = options.languageFilePaths?.[lang];
    if (explicit) result[lang] = path.resolve(explicit);
  }

  if (options.discoverSiblingLanguageFiles !== false) {
    const discovered = discoverSiblingXmlLanguageFiles(absolutePath);
    for (const lang of TOC_LANG_ORDER) {
      if (!result[lang] && discovered[lang]) result[lang] = discovered[lang];
    }
  }

  if (primaryLang && !result[primaryLang]) result[primaryLang] = absolutePath;

  return result;
}

function discoverSiblingXmlLanguageFiles(absolutePath: string): LanguageFileMap {
  const dir = path.dirname(absolutePath);
  const base = path.basename(absolutePath);
  const match = base.match(/^(.*?)(?:[-_.](en|es|ru))?\.xml$/i);
  const prefix = match?.[1] || base.replace(/\.xml$/i, '');
  const result: LanguageFileMap = {};

  for (const lang of TOC_LANG_ORDER) {
    const candidateNames = [
      `${prefix}-${lang}.xml`,
      `${prefix}_${lang}.xml`,
      `${prefix}.${lang}.xml`
    ];

    for (const name of candidateNames) {
      const candidate = path.join(dir, name);
      if (fs.existsSync(candidate)) {
        result[lang] = candidate;
        break;
      }
    }
  }

  return result;
}

function getDocumentLang(doc: any, filePath: string): TocLang | null {
  const root = doc.documentElement;
  const rootLang = root?.getAttribute?.('xml:lang') || root?.getAttribute?.('lang') || '';
  if (isTocLang(rootLang)) return rootLang;

  const fileLang = detectLangFromFileName(filePath);
  if (fileLang) return fileLang;

  return null;
}

function parsePersonRegistry(doc: any): Record<string, any> {
  const persons: Record<string, any> = {};
  const listPerson = doc.getElementsByTagName('listPerson')[0];
  if (!listPerson) return persons;

  const personNodes = listPerson.getElementsByTagName('person');
  for (let i = 0; i < personNodes.length; i++) {
    const p = personNodes[i];
    const id = p.getAttribute('xml:id');
    const name = p.getElementsByTagName('persName')[0]?.textContent?.trim();
    const note = p.getElementsByTagName('note')[0]?.textContent?.trim();
    if (id) persons[id] = { name, note };
  }
  return persons;
}

function parsePlaceRegistry(doc: any): Record<string, any> {
  const places: Record<string, any> = {};
  const listPlace = doc.getElementsByTagName('listPlace')[0];
  if (!listPlace) return places;

  const placeNodes = listPlace.getElementsByTagName('place');
  for (let i = 0; i < placeNodes.length; i++) {
    const p = placeNodes[i];
    const id = p.getAttribute('xml:id');
    const name = p.getElementsByTagName('placeName')[0]?.textContent?.trim();
    const note = p.getElementsByTagName('note')[0]?.textContent?.trim();
    if (id) places[id] = { name, note };
  }
  return places;
}

function mergeRegistries(registries: Array<Record<string, any>>): Record<string, any> {
  const merged: Record<string, any> = {};
  for (const registry of registries) {
    for (const [key, value] of Object.entries(registry)) {
      if (!merged[key]) merged[key] = value;
    }
  }
  return merged;
}

function parseChapters(doc: any, persons: Record<string, any>, places: Record<string, any>, sourceLang: TocLang): Chapter[] {
  const divNodes = doc.getElementsByTagName('div');
  const byN = new Map<string, Chapter>();

  for (let i = 0; i < divNodes.length; i++) {
    const div = divNodes[i];
    if (div.getAttribute('type') !== 'chapter') continue;

    const parsed = parseChapter(div, persons, places, sourceLang, i + 1);
    if (!parsed.n) continue;

    const existing = byN.get(parsed.n);
    if (!existing) byN.set(parsed.n, parsed);
    else byN.set(parsed.n, mergeDuplicateSameLanguageChapter(existing, parsed, sourceLang));
  }

  return Array.from(byN.values()).sort(compareChaptersForReadingOrder);
}

function parseChapter(div: any, persons: Record<string, any>, places: Record<string, any>, sourceLang: TocLang, fallbackIndex: number): Chapter {
  const n = div.getAttribute('n') || String(fallbackIndex);
  const globalNumber = Number.parseInt(n, 10);
  const toc = Number.isFinite(globalNumber) ? locationFromSequentialIndex(globalNumber) : null;
  const versionNodes = directChildElements(div).filter((c: any) => {
    return c.nodeName === 'div' && c.getAttribute('type') === 'version';
  });

  const directHead = directChildText(div, 'head');
  const firstVersionHead = firstNonEmpty(versionNodes.map((v: any) => directChildText(v, 'head')));
  const fallbackHead = firstDescendantText(div, 'head');
  const title = directHead || firstVersionHead || fallbackHead || syntheticFullHeading(sourceLang, toc, n);

  const versions: Version[] = [];

  if (versionNodes.length > 0) {
    for (const v of versionNodes) {
      const lang = normalizedVersionLang(v, sourceLang);
      const vhead = directChildText(v, 'head') || titleForLang(lang, toc, title);
      let vhtml = '';

      if (!directChildText(v, 'head')) {
        vhtml += `<h2 class="navchap">${escapeHtml(vhead)}</h2>`;
      }

      for (let k = 0; k < v.childNodes.length; k++) {
        vhtml += convertNodeToHtml(v.childNodes[k], persons, places);
      }

      versions.push({
        id: v.getAttribute('subtype') || lang || `v${versions.length + 1}`,
        lang,
        html: vhtml.trim(),
        title: vhead
      });
    }
  } else {
    let html = '';
    for (let j = 0; j < div.childNodes.length; j++) {
      html += convertNodeToHtml(div.childNodes[j], persons, places);
    }
    versions.push({
      id: sourceLang,
      lang: sourceLang,
      html: html.trim(),
      title: titleForLang(sourceLang, toc, title)
    });
  }

  const sortedVersions = sortVersions(versions);
  const preferred = sortedVersions.find((version) => version.lang === sourceLang) || sortedVersions[0];

  return {
    n,
    title: titleForLang(sourceLang, toc, title),
    html: preferred?.html || '',
    versions: sortedVersions,
    toc: toc || undefined
  };
}

function mergeDuplicateSameLanguageChapter(a: Chapter, b: Chapter, preferredLang: TocLang): Chapter {
  const versions = mergeVersions(a.versions, b.versions);
  const preferred = choosePreferredVersion(versions, preferredLang);

  return {
    ...a,
    title: chooseBetterTitle(a.title, b.title),
    html: preferred?.html || a.html || b.html,
    versions,
    toc: a.toc || b.toc
  };
}

function mergeLanguageChapters(parsedBooks: ParsedBook[], preferredLang: TocLang): Chapter[] {
  const byN = new Map<string, Chapter>();

  for (const book of parsedBooks) {
    for (const chapter of book.chapters) {
      const existing = byN.get(chapter.n);
      if (!existing) {
        byN.set(chapter.n, { ...chapter, versions: [...chapter.versions] });
        continue;
      }

      const versions = mergeVersions(existing.versions, chapter.versions);
      const preferred = choosePreferredVersion(versions, preferredLang);
      byN.set(chapter.n, {
        ...existing,
        title: preferred?.title || chooseBetterTitle(existing.title, chapter.title),
        html: preferred?.html || existing.html || chapter.html,
        versions,
        toc: existing.toc || chapter.toc
      });
    }
  }

  return Array.from(byN.values()).sort(compareChaptersForReadingOrder);
}

function mergeVersions(...versionLists: Version[][]): Version[] {
  const versionByLang = new Map<string, Version>();

  for (const version of versionLists.flat()) {
    const key = version.lang || version.id;
    const existing = versionByLang.get(key);
    if (!existing || scoreVersion(version) > scoreVersion(existing)) {
      versionByLang.set(key, version);
    }
  }

  return sortVersions(Array.from(versionByLang.values()));
}

function choosePreferredVersion(versions: Version[], preferredLang: TocLang): Version | undefined {
  return versions.find((version) => version.lang === preferredLang)
    || versions.find((version) => version.lang === 'ru')
    || versions[0];
}

export function buildTocTree(chapters: Chapter[]): TocNode[] {
  const volumeNodes = new Map<string, TocNode>();
  const partNodes = new Map<string, TocNode>();
  const tocNodes: TocNode[] = [];

  const chaptersWithLocations = chapters
    .map((chapter, index) => {
      const globalNumber = Number.parseInt(chapter.n || '', 10);
      const location = chapter.toc || (Number.isFinite(globalNumber) ? locationFromSequentialIndex(globalNumber) : null) || locationFromSequentialIndex(index + 1);
      return { chapter, location };
    })
    .filter((entry): entry is { chapter: Chapter; location: TocLocation } => Boolean(entry.location))
    .sort((a, b) => a.location.sortKey - b.location.sortKey);

  for (const { chapter, location } of chaptersWithLocations) {
    const volumeKey = location.kind === 'epilogue'
      ? 'epilogue'
      : `volume-${location.volume}`;

    let volumeNode = volumeNodes.get(volumeKey);
    if (!volumeNode) {
      volumeNode = makeContainerNode(volumeKey, volumeLabels(location));
      volumeNodes.set(volumeKey, volumeNode);
      tocNodes.push(volumeNode);
    }

    const partKey = `${volumeKey}-part-${location.part}`;
    let partNode = partNodes.get(partKey);
    if (!partNode) {
      partNode = makeContainerNode(partKey, partLabels(location));
      partNodes.set(partKey, partNode);
      volumeNode.children.push(partNode);
    }

    const langs = availableTocLangs(chapter);
    partNode.children.push({
      key: `${tocLocationKey(location)}-chapter`,
      labels: langs.map((lang) => chapterLabel(lang, location.chapter)),
      labelByLang: Object.fromEntries(langs.map((lang) => [lang, chapterLabel(lang, location.chapter)])) as Partial<Record<TocLang, string>>,
      children: [],
      chapter
    });
  }

  return tocNodes;
}

function makeContainerNode(key: string, labels: Partial<Record<TocLang, string>>): TocNode {
  return {
    key,
    labels: TOC_LANG_ORDER.map((lang) => labels[lang]).filter(Boolean) as string[],
    labelByLang: labels,
    children: []
  };
}

function volumeLabels(location: TocLocation): Partial<Record<TocLang, string>> {
  if (location.kind === 'epilogue') {
    return {
      en: 'Epilogue',
      es: 'Epílogo',
      ru: 'Эпилог'
    };
  }

  const volume = toRoman(location.volume || 0);
  return {
    en: `Volume ${volume}`,
    es: `Volumen ${volume}`,
    ru: `Том ${volume}`
  };
}

function partLabels(location: TocLocation): Partial<Record<TocLang, string>> {
  return {
    en: `Part ${EN_PART_WORDS[location.part]}`,
    es: `${ES_PART_WORDS[location.part]} Parte`,
    ru: `Часть ${RU_PART_WORDS[location.part]}`
  };
}

function chapterLabel(lang: TocLang, chapter: number): string {
  const roman = toRoman(chapter);
  if (lang === 'es') return `Capítulo ${roman}`;
  if (lang === 'ru') return `Глава ${roman}`;
  return `Chapter ${roman}`;
}

function availableTocLangs(chapter: Chapter): TocLang[] {
  const langs = new Set<TocLang>();
  for (const version of chapter.versions || []) {
    if (isTocLang(version.lang)) langs.add(version.lang);
  }

  if (langs.size === 0) langs.add('ru');
  return sortTocLangs(Array.from(langs));
}

function titleForLang(lang: string, location: TocLocation | null, fallback: string): string {
  if (!isTocLang(lang) || !location) return fallback;

  const volume = volumeLabels(location)[lang];
  const part = partLabels(location)[lang];
  const chapter = chapterLabel(lang, location.chapter);

  if (location.kind === 'epilogue') return `${volume}, ${part}, ${chapter}`;
  return `${volume}, ${part}, ${chapter}`;
}

function syntheticFullHeading(lang: TocLang, location: TocLocation | null, n: string): string {
  if (location) return titleForLang(lang, location, `Chapter ${n}`);
  if (lang === 'es') return `Capítulo ${n}`;
  if (lang === 'ru') return `Глава ${n}`;
  return `Chapter ${n}`;
}

function makeTocLocation(kind: 'volume' | 'epilogue', volume: number | null, part: number, chapter: number): TocLocation | null {
  const section = WAR_AND_PEACE_SECTIONS.find((candidate) => {
    return candidate.kind === kind && candidate.volume === volume && candidate.part === part;
  });

  if (!section || chapter < 1 || chapter > section.count) return null;

  return {
    kind,
    volume,
    part,
    chapter,
    sortKey: section.start + chapter - 1
  };
}

function locationFromSequentialIndex(index: number): TocLocation | null {
  const section = WAR_AND_PEACE_SECTIONS.find((candidate) => index >= candidate.start && index <= candidate.end);
  if (!section) return null;

  return {
    kind: section.kind,
    volume: section.volume,
    part: section.part,
    chapter: index - section.start + 1,
    sortKey: index
  };
}

function tocLocationKey(location: TocLocation): string {
  return location.kind === 'epilogue'
    ? `epilogue-p${location.part}-c${location.chapter}`
    : `v${location.volume}-p${location.part}-c${location.chapter}`;
}

function compareChaptersForReadingOrder(a: Chapter, b: Chapter): number {
  const aKey = a.toc?.sortKey ?? Number.MAX_SAFE_INTEGER;
  const bKey = b.toc?.sortKey ?? Number.MAX_SAFE_INTEGER;
  if (aKey !== bKey) return aKey - bKey;

  const aN = Number.parseInt(a.n || '0', 10);
  const bN = Number.parseInt(b.n || '0', 10);
  return aN - bN;
}

function chooseBetterTitle(a: string, b: string): string {
  if (!a) return b;
  if (!b) return a;
  if (/^Chapter\s+\d+$/i.test(a) && !/^Chapter\s+\d+$/i.test(b)) return b;
  if (containsMojibake(a) && !containsMojibake(b)) return b;
  return a;
}

function scoreVersion(version: Version): number {
  return scoreHtml(version.html) + (version.title ? 1000 : 0);
}

function scoreHtml(html: string): number {
  if (!html) return 0;
  return html.length - (containsMojibake(html) ? 1_000_000 : 0);
}

function containsMojibake(text: string): boolean {
  return /[ÐÑÂÃ][\u0080-\u00ff]?|�/.test(text);
}

function sortVersions(versions: Version[]): Version[] {
  return [...versions].sort((a, b) => {
    const aIndex = TOC_LANG_ORDER.indexOf(a.lang as TocLang);
    const bIndex = TOC_LANG_ORDER.indexOf(b.lang as TocLang);
    const normalizedA = aIndex === -1 ? Number.MAX_SAFE_INTEGER : aIndex;
    const normalizedB = bIndex === -1 ? Number.MAX_SAFE_INTEGER : bIndex;
    return normalizedA - normalizedB;
  });
}

function sortTocLangs(langs: TocLang[]): TocLang[] {
  const unique = new Set(langs.filter(isTocLang));
  return TOC_LANG_ORDER.filter((lang) => unique.has(lang));
}

function isTocLang(lang: string): lang is TocLang {
  return (TOC_LANG_ORDER as readonly string[]).includes(lang);
}

function detectLangFromFileName(filePath: string): TocLang | null {
  const base = path.basename(filePath).toLowerCase();
  const match = base.match(/(?:^|[-_.])(en|es|ru)(?:[-_.]|$)/);
  return match && isTocLang(match[1]) ? match[1] : null;
}

function normalizedVersionLang(node: any, sourceLang: TocLang): string {
  const lang = node.getAttribute('xml:lang') || node.getAttribute('lang') || sourceLang;
  return lang || sourceLang;
}

function directChildElements(node: any): any[] {
  const result: any[] = [];
  for (let i = 0; i < node.childNodes.length; i++) {
    const child = node.childNodes[i];
    if (child.nodeType === 1) result.push(child);
  }
  return result;
}

function directChildText(node: any, tagName: string): string {
  const child = directChildElements(node).find((c: any) => c.nodeName === tagName);
  return child?.textContent?.trim() || '';
}

function firstDescendantText(node: any, tagName: string): string {
  const descendant = node.getElementsByTagName(tagName)[0];
  return descendant?.textContent?.trim() || '';
}

function firstNonEmpty(values: string[]): string {
  return values.find((value) => value && value.trim())?.trim() || '';
}

export function slugify(text: string): string {
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '');
}

export function slugifyAuthor(name: string): string {
  const parts = name.trim().split(' ');
  if (parts.length > 1) {
    const lastName = parts.pop();
    return slugify(`${lastName}-${parts.join('-')}`);
  }
  return slugify(name);
}

function convertNodeToHtml(node: any, persons: Record<string, any>, places: Record<string, any>): string {
  if (node.nodeType === 3) {
    return escapeHtml(node.nodeValue || '');
  }

  if (node.nodeType === 1) {
    const tag = node.nodeName;
    let innerHtml = '';
    for (let i = 0; i < node.childNodes.length; i++) {
      innerHtml += convertNodeToHtml(node.childNodes[i], persons, places);
    }

    if (tag === 'head') return `<h2 class="navchap">${innerHtml}</h2>`;
    if (tag === 'p') return `<p>${innerHtml}</p>`;
    if (tag === 'said') {
      const who = node.getAttribute('who') || '';
      const lead = innerHtml.replace(/^\s+/, '');
      const hasOwnPunctuation = /^[—–\-"“«]/.test(lead);
      const body = hasOwnPunctuation ? innerHtml : `&ldquo;${innerHtml}&rdquo;`;
      return `<span class="tei-said" data-who="${escapeAttr(who)}">${body}</span>`;
    }
    if (tag === 'emph') return `<em>${innerHtml}</em>`;
    if (tag === 'title') return `<cite>${innerHtml}</cite>`;
    if (tag === 'foreign') {
      const lang = node.getAttribute('xml:lang') || '';
      const name = LANG_NAMES[lang] || lang;
      const translation = node.getAttribute('n');
      let titleAttr = '';
      if (translation && name) {
        titleAttr = ` title="${escapeAttr(`${name}: [${translation}]`)}"`;
      } else if (name) {
        titleAttr = ` title="${escapeAttr(name)}"`;
      }
      return `<i class="tei-foreign" lang="${escapeAttr(lang)}"${titleAttr}>${innerHtml}</i>`;
    }
    if (tag === 'note') return `<span class="tei-note"> [${innerHtml}]</span>`;
    if (tag === 'seg') {
      const type = node.getAttribute('type') || '';
      if (type.startsWith('orig')) {
        const lang = type.slice(4) || node.getAttribute('xml:lang') || '';
        const name = LANG_NAMES[lang] || 'another language';
        return `<span class="tei-was-fr" title="${escapeAttr(`${name} in the original`)}">${innerHtml}</span>`;
      }
      return innerHtml;
    }
    if (tag === 'rs' || tag === 'persName' || tag === 'placeName') {
      const ref = node.getAttribute('ref') || '';
      const id = ref.replace('#', '');
      let title = '';
      if (persons[id]) title = `${persons[id].name}${persons[id].note ? ': ' + persons[id].note : ''}`;
      else if (places[id]) title = `${places[id].name}${places[id].note ? ': ' + places[id].note : ''}`;

      const titleAttr = title ? ` title="${escapeAttr(title)}"` : '';
      return `<span class="tei-rs" data-ref="${escapeAttr(ref)}"${titleAttr}>${innerHtml}</span>`;
    }
    if (tag === 'pb') {
      const n = node.getAttribute('n') || '';
      return `<span class="tei-pb" data-n="${escapeAttr(n)}"></span>`;
    }
    if (tag === 'q') return `<q>${innerHtml}</q>`;
    if (tag === 'quote') return `<blockquote>${innerHtml}</blockquote>`;
    if (tag === 'hi') return `<span>${innerHtml}</span>`;
    if (tag === 'lg') return `<div class="tei-lg">${innerHtml}</div>`;
    if (tag === 'l') return `<div class="tei-l">${innerHtml}</div>`;
    if (tag === 'floatingText') return `<blockquote class="tei-letter">${innerHtml}</blockquote>`;
    if (tag === 'opener') return `<div class="tei-opener">${innerHtml}</div>`;
    if (tag === 'closer') return `<div class="tei-closer">${innerHtml}</div>`;
    if (tag === 'salute') return `<div class="tei-salute">${innerHtml}</div>`;
    if (tag === 'signed') return `<div class="tei-signed">${innerHtml}</div>`;
    if (tag === 'dateline') return `<div class="tei-dateline">${innerHtml}</div>`;
    if (tag === 'body') return innerHtml;

    return innerHtml;
  }

  return '';
}

function escapeHtml(unsafe: string) {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeAttr(unsafe: string) {
  return escapeHtml(unsafe)
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function toRoman(value: number): string {
  const numerals: Array<[number, string]> = [
    [1000, 'M'], [900, 'CM'], [500, 'D'], [400, 'CD'],
    [100, 'C'], [90, 'XC'], [50, 'L'], [40, 'XL'],
    [10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']
  ];

  let remaining = value;
  let result = '';
  for (const [n, roman] of numerals) {
    while (remaining >= n) {
      result += roman;
      remaining -= n;
    }
  }
  return result;
}
