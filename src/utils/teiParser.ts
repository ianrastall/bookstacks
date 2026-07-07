import fs from 'node:fs';
import path from 'node:path';
import { DOMParser } from '@xmldom/xmldom';

const LANG_NAMES: Record<string, string> = {
  grc: 'Ancient Greek',
  fr: 'French',
  ru: 'Russian',
  de: 'German',
  it: 'Italian',
  la: 'Latin',
  en: 'English',
  es: 'Spanish',
  pt: 'Portuguese'
};

const TOC_LANG_ORDER = ['grc', 'en', 'es', 'fr', 'pt', 'it', 'la', 'ru', 'de'] as const;
type TocLang = typeof TOC_LANG_ORDER[number];

type Version = {
  id: string;
  lang: string;
  subtype?: string;
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
  slugPath?: string;
  sortKey?: number;
  chapterN?: string;
  chapterTitle?: string;
  chapterTitleByLang?: Partial<Record<TocLang, string>>;
  groupPath?: Array<{ key: string; label: string }>;
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
   * like tolstoy-leo_war-and-peace_ru.xml, tolstoy-leo_war-and-peace_en.xml,
   * and tolstoy-leo_war-and-peace_es.xml in the same directory.
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

// War and Peace gets a bespoke volume/part/chapter table of contents. Its source
// files are named tolstoy-leo_war-and-peace_<lang>.xml, so detect the work by that
// filename prefix.
const WAR_AND_PEACE_FILE_PREFIX = 'tolstoy-leo_war-and-peace';

function isWarAndPeaceFile(filePath: string): boolean {
  return path.basename(filePath).startsWith(WAR_AND_PEACE_FILE_PREFIX);
}

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
 * language files when present (e.g. tolstoy-leo_war-and-peace_*.xml). The XML
 * files are the source of truth; .shtml files are intentionally ignored here.
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
    // Author life-dates may only be recorded in one language file (e.g. the
    // German source for Mann); fall back to any sibling that has them.
    const authorDates = primaryBook.authorDates
      || parsedBooks.find((book) => book.authorDates)?.authorDates
      || '';
    const persons = mergeRegistries(parsedBooks.map((book) => book.persons));
    const places = mergeRegistries(parsedBooks.map((book) => book.places));
    const preferredLang = options.preferredLang || primaryBook.lang || primaryLang || 'ru';
    const chapters = mergeLanguageChapters(parsedBooks, preferredLang);
    const isWarAndPeace = isWarAndPeaceFile(absolutePath);
    const tocTree = buildTocTree(chapters, isWarAndPeace);

    return { title, author, authorDates, persons, places, chapters, tocTree };
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
  authorDates: string;
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

// Extract author life-dates from <author><note type="dates">…</note></author>,
// e.g. "1875-1955". Returns '' when no such note is present.
function findAuthorDates(authorEl: any): string {
  if (!authorEl) return '';
  const notes = authorEl.getElementsByTagName('note');
  for (let i = 0; i < notes.length; i++) {
    const note = notes[i];
    if (note.getAttribute?.('type') === 'dates') {
      const text = note.textContent?.trim();
      if (text) return text;
    }
  }
  return '';
}

// The author display name is the persName's own text only. Some converted files
// nest <note type="dates"> inside <persName>; textContent would otherwise glue the
// life-dates onto the name (e.g. "Shakespeare, William1564-1616").
function personNameText(persNameEl: any): string {
  if (!persNameEl) return '';
  let text = '';
  for (let i = 0; i < persNameEl.childNodes.length; i++) {
    const child = persNameEl.childNodes[i];
    if (child.nodeType === 3) text += child.nodeValue || '';
  }
  return text.trim();
}

function parseSingleLanguageBook(doc: any, filePath: string, fallbackLang: TocLang): ParsedBook {
  const lang = getDocumentLang(doc, filePath) || fallbackLang;
  const titleNode = doc.getElementsByTagName('title')[0];
  const authorEl = doc.getElementsByTagName('author')[0];
  const authorNode = authorEl?.getElementsByTagName('persName')[0];
  const title = titleNode?.textContent?.trim() || 'Unknown Title';
  const author = personNameText(authorNode) || authorNode?.textContent?.trim() || 'Unknown Author';
  const authorDates = findAuthorDates(authorEl);
  const persons = parsePersonRegistry(doc);
  const places = parsePlaceRegistry(doc);
  const isWarAndPeace = isWarAndPeaceFile(filePath);
  const chapters = isDramaDoc(doc)
    ? parseDramaChapters(doc, persons, places, lang)
    : isVolumeGroupedDoc(doc)
    ? parseVolumeGroupedChapters(doc, persons, places, lang)
    : parseChapters(doc, persons, places, lang, isWarAndPeace);

  return { filePath: path.resolve(filePath), lang, title, author, authorDates, persons, places, chapters };
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
  const match = base.match(/^(.*?)(?:[-_.](grc|en|es|fr|pt|ru|de|it|la))?\.xml$/i);
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

// A play encodes speeches as <sp>; prose works never do. When present we treat
// acts as the table-of-contents grouping and scenes as the reading unit, reusing
// the same "sectioned chapter" machinery War and Peace uses for volume/part.
function isDramaDoc(doc: any): boolean {
  return doc.getElementsByTagName('sp').length > 0;
}

// A book whose reading chapters are nested inside <div type="volume"> (and
// optionally <div type="book">) gets a nested Volume → Book → Chapter table of
// contents. Magic Mountain also uses <div type="volume">, but its reading units
// are <div type="section"> inside chapter divs; the no-section guard keeps the
// generic grouped path off it (and off any future section-based book).
function isVolumeGroupedDoc(doc: any): boolean {
  const divs = doc.getElementsByTagName('div');
  let hasVolume = false;
  let hasSection = false;
  for (let i = 0; i < divs.length; i++) {
    const type = divs[i].getAttribute('type');
    if (type === 'volume') hasVolume = true;
    else if (type === 'section') hasSection = true;
  }
  return hasVolume && !hasSection;
}

const GROUPING_DIV_TYPES = new Set(['volume', 'book', 'part']);

// Walk the division hierarchy, emitting one flat reading-unit Chapter per leaf
// <div type="chapter"> and recording its ancestor volume/book labels as
// `groupPath` (used by buildGroupedTocTree to nest the table of contents). Front
// matter (a chapter div that is not under any grouping div) gets an empty
// groupPath and renders as a top-level entry.
function parseVolumeGroupedChapters(doc: any, persons: Record<string, any>, places: Record<string, any>, sourceLang: TocLang): Chapter[] {
  const body = doc.getElementsByTagName('body')[0];
  if (!body) return [];

  const chapters: Chapter[] = [];
  let seq = 0;

  const walk = (node: any, groupPath: Array<{ key: string; label: string }>) => {
    for (const child of directChildElements(node)) {
      if (child.nodeName !== 'div') continue;
      const type = child.getAttribute('type') || '';

      if (type === 'chapter') {
        seq += 1;
        const n = String(seq);
        const title = directChildText(child, 'head') || syntheticFullHeading(sourceLang, null, n);
        const kicker = groupPath.length > 0
          ? `<p class="chapter-context">${groupPath.map((g) => escapeHtml(g.label)).join(' · ')}</p>`
          : '';
        const html = (kicker + renderChildren(child, persons, places)).trim();
        chapters.push({
          n,
          title,
          html,
          versions: [{ id: sourceLang, lang: sourceLang, html, title }],
          slugPath: `chapter-${n}`,
          sortKey: seq,
          groupPath: groupPath.slice()
        });
        continue;
      }

      if (GROUPING_DIV_TYPES.has(type)) {
        const label = directChildText(child, 'head') || titleCaseWord(type);
        const key = slugify(label) || `${type}-${groupPath.length + 1}`;
        walk(child, [...groupPath, { key, label }]);
        continue;
      }

      // Unknown wrapper (e.g. a plain <div> grouping title-page matter): recurse
      // without contributing a grouping level.
      walk(child, groupPath);
    }
  };

  walk(body, []);
  return chapters;
}

type DramaChapterInput = {
  chapterKey: string;
  chapterTitle: string;
  title: string;
  slugPath: string;
  sortKey: number;
  headHtml: string;
  contentNode: any;
  sourceLang: TocLang;
  persons: Record<string, any>;
  places: Record<string, any>;
};

function makeDramaChapter(input: DramaChapterInput): Chapter {
  const html = (input.headHtml + renderChildren(input.contentNode, input.persons, input.places)).trim();
  const n = input.slugPath.replace(/^chapter-/, '').replace(/\//g, '.');
  return {
    n,
    title: input.title,
    html,
    versions: [{ id: input.sourceLang, lang: input.sourceLang, html, title: input.title }],
    slugPath: input.slugPath,
    sortKey: input.sortKey,
    chapterN: input.chapterKey,
    chapterTitle: input.chapterTitle,
    chapterTitleByLang: { [input.sourceLang]: input.chapterTitle }
  };
}

function parseDramaChapters(doc: any, persons: Record<string, any>, places: Record<string, any>, sourceLang: TocLang): Chapter[] {
  const body = doc.getElementsByTagName('body')[0];
  if (!body) return [];

  const chapters: Chapter[] = [];
  let order = 0;
  let actSeq = 0;
  let standaloneSeq = 0;

  for (const div of directChildElements(body)) {
    if (div.nodeName !== 'div') continue;
    const type = div.getAttribute('type') || '';

    if (type === 'act') {
      actSeq += 1;
      const actN = div.getAttribute('n') || String(actSeq);
      const actKey = slugify(actN) || String(actSeq);
      const actHead = directChildText(div, 'head') || `Act ${actN}`;
      const scenes = directChildElements(div).filter(
        (c: any) => c.nodeName === 'div' && c.getAttribute('type') === 'scene'
      );

      if (scenes.length === 0) {
        chapters.push(makeDramaChapter({
          chapterKey: actKey, chapterTitle: actHead, title: actHead,
          slugPath: `chapter-${actKey}`, sortKey: (order += 1),
          headHtml: '', contentNode: div, sourceLang, persons, places
        }));
        continue;
      }

      scenes.forEach((scene: any, idx: number) => {
        const sceneHead = directChildText(scene, 'head') || `Scene ${idx + 1}`;
        chapters.push(makeDramaChapter({
          chapterKey: actKey, chapterTitle: actHead, title: sceneHead,
          slugPath: `chapter-${actKey}/${slugify(sceneHead) || `scene-${idx + 1}`}`,
          sortKey: (order += 1),
          headHtml: `<h2 class="navchap tei-act-head">${escapeHtml(actHead)}</h2>`,
          contentNode: scene, sourceLang, persons, places
        }));
      });
      continue;
    }

    // Front/back matter or a scene without an enclosing act (prologue, epilogue,
    // dramatis personae, induction, …). Each is its own single-item section.
    standaloneSeq += 1;
    const head = directChildText(div, 'head') || titleCaseWord(type) || `Section ${standaloneSeq}`;
    const key = slugify(head) || slugify(type) || `section-${standaloneSeq}`;
    chapters.push(makeDramaChapter({
      chapterKey: key, chapterTitle: head, title: head,
      slugPath: `chapter-${key}`, sortKey: (order += 1),
      headHtml: '', contentNode: div, sourceLang, persons, places
    }));
  }

  return chapters.sort(compareChaptersForReadingOrder);
}

function titleCaseWord(word: string): string {
  if (!word) return '';
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function parseChapters(doc: any, persons: Record<string, any>, places: Record<string, any>, sourceLang: TocLang, isWarAndPeace: boolean): Chapter[] {
  const divNodes = doc.getElementsByTagName('div');
  const byN = new Map<string, Chapter>();

  for (let i = 0; i < divNodes.length; i++) {
    const div = divNodes[i];
    if (div.getAttribute('type') !== 'chapter') continue;

    for (const parsed of parseChapterUnits(div, persons, places, sourceLang, i + 1, isWarAndPeace)) {
      if (!parsed.n) continue;

      const existing = byN.get(parsed.n);
      if (!existing) byN.set(parsed.n, parsed);
      else byN.set(parsed.n, mergeDuplicateSameLanguageChapter(existing, parsed, sourceLang));
    }
  }

  return Array.from(byN.values()).sort(compareChaptersForReadingOrder);
}

function parseChapterUnits(div: any, persons: Record<string, any>, places: Record<string, any>, sourceLang: TocLang, fallbackIndex: number, isWarAndPeace: boolean): Chapter[] {
  const versionNodes = directChildElements(div).filter((c: any) => {
    return c.nodeName === 'div' && c.getAttribute('type') === 'version';
  });
  const sectionNodes = directChildElements(div).filter((c: any) => {
    return c.nodeName === 'div' && c.getAttribute('type') === 'section';
  });

  if (!isWarAndPeace && versionNodes.length === 0 && sectionNodes.length > 0) {
    return sectionNodes.map((section: any, index: number) => {
      return parseChapterSection(div, section, persons, places, sourceLang, fallbackIndex, index + 1);
    });
  }

  return [parseChapter(div, persons, places, sourceLang, fallbackIndex, isWarAndPeace)];
}

function parseChapter(div: any, persons: Record<string, any>, places: Record<string, any>, sourceLang: TocLang, fallbackIndex: number, isWarAndPeace: boolean): Chapter {
  const n = div.getAttribute('n') || String(fallbackIndex);
  const globalNumber = Number.parseInt(n, 10);
  const toc = (isWarAndPeace && Number.isFinite(globalNumber)) ? locationFromSequentialIndex(globalNumber) : null;
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
      const subtype = normalizedVersionSubtype(v);
      const id = uniqueVersionId(versionBaseId(v, lang, subtype, versions.length), versions);
      const vhead = directChildText(v, 'head') || titleForLang(lang, toc, title);
      let vhtml = '';

      if (!directChildText(v, 'head')) {
        vhtml += `<h2 class="navchap">${escapeHtml(vhead)}</h2>`;
      }

      for (let k = 0; k < v.childNodes.length; k++) {
        vhtml += convertNodeToHtml(v.childNodes[k], persons, places);
      }

      versions.push({
        id,
        lang,
        subtype: subtype || undefined,
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
    toc: toc || undefined,
    slugPath: `chapter-${slugify(n)}`,
    sortKey: toc?.sortKey ?? numericSortKey(n, fallbackIndex)
  };
}

function parseChapterSection(
  chapterDiv: any,
  sectionDiv: any,
  persons: Record<string, any>,
  places: Record<string, any>,
  sourceLang: TocLang,
  fallbackIndex: number,
  sectionIndex: number
): Chapter {
  const chapterN = chapterDiv.getAttribute('n') || String(fallbackIndex);
  const chapterTitle = directChildText(chapterDiv, 'head') || syntheticFullHeading(sourceLang, null, chapterN);
  const title = directChildText(sectionDiv, 'head') || `${chapterTitle}, Section ${sectionIndex}`;
  const n = `${chapterN}.${sectionIndex}`;

  let html = '';
  for (let j = 0; j < sectionDiv.childNodes.length; j++) {
    html += convertNodeToHtml(sectionDiv.childNodes[j], persons, places);
  }

  return {
    n,
    title,
    html: html.trim(),
    versions: [{
      id: sourceLang,
      lang: sourceLang,
      html: html.trim(),
      title
    }],
    slugPath: `chapter-${slugify(chapterN)}/${slugify(title) || `section-${sectionIndex}`}`,
    sortKey: numericSortKey(chapterN, fallbackIndex) * 1000 + sectionIndex,
    chapterN,
    chapterTitle,
    chapterTitleByLang: { [sourceLang]: chapterTitle }
  };
}

function mergeDuplicateSameLanguageChapter(a: Chapter, b: Chapter, preferredLang: TocLang): Chapter {
  const versions = mergeVersions(a.versions, b.versions);
  const preferred = choosePreferredVersion(versions, preferredLang);
  const chapterTitleByLang = mergeLangLabels(a.chapterTitleByLang, b.chapterTitleByLang);

  return {
    ...a,
    title: chooseBetterTitle(a.title, b.title),
    html: preferred?.html || a.html || b.html,
    versions,
    toc: a.toc || b.toc,
    slugPath: chooseBetterSlugPath(a, b, preferred),
    sortKey: Math.min(a.sortKey ?? Number.MAX_SAFE_INTEGER, b.sortKey ?? Number.MAX_SAFE_INTEGER),
    chapterN: a.chapterN || b.chapterN,
    chapterTitle: chapterTitleByLang?.[preferredLang] || a.chapterTitle || b.chapterTitle,
    chapterTitleByLang
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
      const chapterTitleByLang = mergeLangLabels(existing.chapterTitleByLang, chapter.chapterTitleByLang);
      byN.set(chapter.n, {
        ...existing,
        title: preferred?.title || chooseBetterTitle(existing.title, chapter.title),
        html: preferred?.html || existing.html || chapter.html,
        versions,
        toc: existing.toc || chapter.toc,
        slugPath: chooseBetterSlugPath(existing, chapter, preferred),
        sortKey: Math.min(existing.sortKey ?? Number.MAX_SAFE_INTEGER, chapter.sortKey ?? Number.MAX_SAFE_INTEGER),
        chapterN: existing.chapterN || chapter.chapterN,
        chapterTitle: chapterTitleByLang?.[preferredLang] || existing.chapterTitle || chapter.chapterTitle,
        chapterTitleByLang
      });
    }
  }

  return Array.from(byN.values()).sort(compareChaptersForReadingOrder);
}

function mergeVersions(...versionLists: Version[][]): Version[] {
  const versionByKey = new Map<string, Version>();

  for (const version of versionLists.flat()) {
    const key = version.id || version.lang;
    const existing = versionByKey.get(key);
    if (!existing || scoreVersion(version) > scoreVersion(existing)) {
      versionByKey.set(key, version);
    }
  }

  return sortVersions(Array.from(versionByKey.values()));
}

function chooseBetterSlugPath(a: Chapter, b: Chapter, preferred?: Version): string | undefined {
  if (preferred?.lang) {
    const preferredTitle = preferred.title || '';
    if (preferredTitle && b.title === preferredTitle && b.slugPath) return b.slugPath;
    if (preferredTitle && a.title === preferredTitle && a.slugPath) return a.slugPath;
    if (preferred.lang === firstVersionLang(b) && b.slugPath) return b.slugPath;
    if (preferred.lang === firstVersionLang(a) && a.slugPath) return a.slugPath;
  }

  return a.slugPath || b.slugPath;
}

function firstVersionLang(chapter: Chapter): string {
  return chapter.versions?.[0]?.lang || '';
}

function mergeLangLabels(
  a?: Partial<Record<TocLang, string>>,
  b?: Partial<Record<TocLang, string>>
): Partial<Record<TocLang, string>> | undefined {
  const merged = { ...(a || {}), ...(b || {}) };
  return Object.keys(merged).length > 0 ? merged : undefined;
}

function choosePreferredVersion(versions: Version[], preferredLang: TocLang): Version | undefined {
  return versions.find((version) => version.lang === preferredLang)
    || versions.find((version) => version.lang === 'ru')
    || versions[0];
}

export function buildTocTree(chapters: Chapter[], isWarAndPeace: boolean = false): TocNode[] {
  if (!isWarAndPeace) {
    const hasGroupedChapters = chapters.some(
      (chapter) => Array.isArray(chapter.groupPath) && chapter.groupPath.length > 0
    );
    if (hasGroupedChapters) return buildGroupedTocTree(chapters);

    const hasSectionedChapters = chapters.some((chapter) => chapter.chapterN);
    if (hasSectionedChapters) return buildSectionedTocTree(chapters);

    return chapters.map((chapter) => {
      const langs = availableTocLangs(chapter);
      const labelByLang: Partial<Record<TocLang, string>> = {};
      for (const lang of langs) {
        const version = chapter.versions.find((v) => v.lang === lang);
        if (version && version.title) labelByLang[lang] = version.title;
      }
      return {
        key: `chapter-${chapter.n}`,
        labels: langs.map((lang) => labelByLang[lang] || chapter.title),
        labelByLang,
        children: [],
        chapter
      };
    });
  }

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

// Nest a flat reading list into Volume → Book → Chapter (any depth) using each
// chapter's groupPath. Grouping nodes carry no chapter; leaf nodes reference the
// shared Chapter object (so content.config's later id assignment links them).
function buildGroupedTocTree(chapters: Chapter[]): TocNode[] {
  const roots: TocNode[] = [];
  const nodeByPath = new Map<string, TocNode>();

  for (const chapter of chapters) {
    let siblings = roots;
    let cumulativeKey = '';

    for (const group of chapter.groupPath || []) {
      cumulativeKey += `/${group.key}`;
      let node = nodeByPath.get(cumulativeKey);
      if (!node) {
        node = { key: cumulativeKey, labels: [group.label], labelByLang: {}, children: [] };
        nodeByPath.set(cumulativeKey, node);
        siblings.push(node);
      }
      siblings = node.children;
    }

    siblings.push({
      key: `chapter-${chapter.n}`,
      labels: [chapter.title],
      labelByLang: {},
      children: [],
      chapter
    });
  }

  return roots;
}

function buildSectionedTocTree(chapters: Chapter[]): TocNode[] {
  const tocNodes: TocNode[] = [];
  const chapterNodes = new Map<string, TocNode>();

  for (const chapter of chapters) {
    const chapterKey = chapter.chapterN || chapter.n;
    let chapterNode = chapterNodes.get(chapterKey);

    if (!chapterNode) {
      const labelByLang = chapter.chapterTitleByLang || {};
      const labels = TOC_LANG_ORDER.map((lang) => labelByLang[lang]).filter(Boolean) as string[];
      chapterNode = {
        key: `chapter-${chapterKey}`,
        labels: labels.length > 0 ? labels : [chapter.chapterTitle || `Chapter ${chapterKey}`],
        labelByLang,
        children: []
      };
      chapterNodes.set(chapterKey, chapterNode);
      tocNodes.push(chapterNode);
    }

    const langs = availableTocLangs(chapter);
    const labelByLang: Partial<Record<TocLang, string>> = {};
    for (const lang of langs) {
      const version = chapter.versions.find((v) => v.lang === lang);
      if (version && version.title) labelByLang[lang] = version.title;
    }

    chapterNode.children.push({
      key: `section-${chapter.n}`,
      labels: langs.map((lang) => labelByLang[lang] || chapter.title),
      labelByLang,
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
  const aSortKey = a.sortKey ?? Number.MAX_SAFE_INTEGER;
  const bSortKey = b.sortKey ?? Number.MAX_SAFE_INTEGER;
  if (aSortKey !== bSortKey) return aSortKey - bSortKey;

  const aKey = a.toc?.sortKey ?? Number.MAX_SAFE_INTEGER;
  const bKey = b.toc?.sortKey ?? Number.MAX_SAFE_INTEGER;
  if (aKey !== bKey) return aKey - bKey;

  const aN = Number.parseFloat(a.n || '0');
  const bN = Number.parseFloat(b.n || '0');
  return aN - bN;
}

function numericSortKey(n: string, fallback: number): number {
  const parsed = Number.parseFloat(n || '');
  return Number.isFinite(parsed) ? parsed : fallback;
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
    if (normalizedA !== normalizedB) return normalizedA - normalizedB;
    return (a.id || '').localeCompare(b.id || '');
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
  const match = base.match(/(?:^|[-_.])(grc|en|es|fr|pt|ru|de|it|la)(?:[-_.]|$)/);
  return match && isTocLang(match[1]) ? match[1] : null;
}

function normalizedVersionLang(node: any, sourceLang: TocLang): string {
  const lang = node.getAttribute('xml:lang') || node.getAttribute('lang') || sourceLang;
  return lang || sourceLang;
}

function normalizedVersionSubtype(node: any): string {
  return (node.getAttribute('subtype') || '').trim();
}

function versionBaseId(node: any, lang: string, subtype: string, fallbackIndex: number): string {
  const explicit = (node.getAttribute('xml:id') || node.getAttribute('id') || '').trim();
  if (explicit) return slugify(explicit) || explicit;

  const safeLang = slugify(lang || 'version');
  const safeSubtype = slugify(subtype || '');

  if (safeLang && safeSubtype) return `${safeLang}-${safeSubtype}`;
  if (safeLang) return safeLang;
  return `version-${fallbackIndex + 1}`;
}

function uniqueVersionId(baseId: string, existingVersions: Version[]): string {
  const fallback = `version-${existingVersions.length + 1}`;
  const base = baseId || fallback;
  const taken = new Set(existingVersions.map((version) => version.id));

  if (!taken.has(base)) return base;

  let counter = 2;
  let candidate = `${base}-${counter}`;
  while (taken.has(candidate)) {
    counter += 1;
    candidate = `${base}-${counter}`;
  }
  return candidate;
}

function renderChildren(node: any, persons: Record<string, any>, places: Record<string, any>): string {
  let html = '';
  for (let i = 0; i < node.childNodes.length; i++) {
    html += convertNodeToHtml(node.childNodes[i], persons, places);
  }
  return html;
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
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
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
    if (tag === 'p') {
      // A paragraph that is wholly wrapped in [ ] is a stage direction the
      // converter left inline (entrances became <stage>, but exits/movements
      // stayed as bracketed <p>). Promote it so exits align right like the rest.
      const text = (node.textContent || '').trim();
      if (text.startsWith('[') && text.endsWith(']')) {
        const isExit = /\b(Exit|Exeunt)\b/i.test(text);
        return `<div class="tei-stage ${isExit ? 'tei-stage-exit' : 'tei-stage-enter'}">${innerHtml.trim()}</div>`;
      }
      return `<p>${innerHtml}</p>`;
    }
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
    if (tag === 'hi') {
      const rend = node.getAttribute('rend') || '';
      if (rend === 'italic') return `<i>${innerHtml}</i>`;
      if (rend === 'bold') return `<strong>${innerHtml}</strong>`;
      return `<span>${innerHtml}</span>`;
    }
    if (tag === 'lg') return `<div class="tei-lg">${innerHtml}</div>`;
    if (tag === 'l') return `<div class="tei-l">${innerHtml}</div>`;
    // Drama markup (Shakespeare et al.): sp / speaker / stage / castList.
    if (tag === 'sp') return `<div class="tei-sp">${innerHtml}</div>`;
    if (tag === 'speaker') return `<span class="tei-speaker">${innerHtml.trim()}</span>`;
    if (tag === 'name') return `<span class="tei-name">${innerHtml}</span>`;
    if (tag === 'stage') {
      // Inside the brackets: character <name>s stay roman/caps (handled in CSS);
      // every other word is italicised. Entrances centre, exits go right; a stage
      // direction sitting inside a speech renders inline.
      let stageInner = '';
      for (let i = 0; i < node.childNodes.length; i++) {
        const c = node.childNodes[i];
        if (c.nodeType === 3) {
          const text = escapeHtml(c.nodeValue || '');
          stageInner += text.trim() ? `<i>${text}</i>` : text;
        } else {
          stageInner += convertNodeToHtml(c, persons, places);
        }
      }
      stageInner = stageInner.trim();
      // Faithful to the source: scenedesc -> entrance (centered), p.right -> exit
      // (right). A scene-setting blurb gets its own un-bracketed line. Anything
      // else (a direction inside a speech) renders inline.
      const stype = node.getAttribute('type') || '';
      if (stype === 'setting') return `<div class="tei-setting">${stageInner}</div>`;
      if (stype === 'exit') return `<div class="tei-stage tei-stage-exit">[${stageInner}]</div>`;
      if (stype === 'entrance') return `<div class="tei-stage tei-stage-enter">[${stageInner}]</div>`;
      if (!stype && node.parentNode?.nodeName === 'div') {
        // Untyped block-level direction (older files): fall back to keyword.
        const isExit = /^(Exit|Exeunt)\b/i.test((node.textContent || '').trim());
        return `<div class="tei-stage ${isExit ? 'tei-stage-exit' : 'tei-stage-enter'}">[${stageInner}]</div>`;
      }
      return `<span class="tei-stage tei-stage-inline">[${stageInner}]</span>`;
    }
    if (tag === 'role') return `<span class="tei-role">${innerHtml}</span>`;
    if (tag === 'castList') {
      // The Gutenberg→TEI pass sometimes mis-encoded a speech as a castList
      // (an ALL-CAPS speaker castItem followed by the spoken lines). Render that
      // as a speech; otherwise fall back to a plain cast list.
      const items = directChildElements(node).filter((c: any) => c.nodeName === 'castItem');
      const firstText = items[0]?.textContent?.trim() || '';
      const looksLikeSpeech = items.length >= 2
        && /[A-Za-z]/.test(firstText)
        && firstText === firstText.toUpperCase();
      if (looksLikeSpeech) {
        const speaker = `<span class="tei-speaker">${escapeHtml(firstText)}</span>`;
        const lines = items.slice(1)
          .map((item: any) => `<p>${renderChildren(item, persons, places)}</p>`)
          .join('');
        return `<div class="tei-sp">${speaker}${lines}</div>`;
      }
      return `<div class="tei-castlist">${innerHtml}</div>`;
    }
    if (tag === 'castItem') return `<div class="tei-castitem">${innerHtml}</div>`;
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
