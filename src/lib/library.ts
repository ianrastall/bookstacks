import fs from 'node:fs';
import path from 'node:path';
import { DOMParser } from '@xmldom/xmldom';
import authorProfileData from '../data/author-profiles.json';
import { isLocale, ui, type Locale } from './i18n';

const XML_NS = 'http://www.w3.org/XML/1998/namespace';
const TEI_NS = 'http://www.tei-c.org/ns/1.0';
const READING_KIND_PRIORITY = ['scene', 'section', 'chapter', 'stave', 'bekker_page', 'part'];
const SUPPLEMENTARY_KINDS = new Set([
  'front',
  'preface',
  'translator-preface',
  'authorial-note',
  'colophon',
  'credits',
  'postscript',
  'prologue',
  'epilogue',
  'introduction',
  'dedication',
  'characters',
  'notes',
  'publication-note',
  'suppressed-chapter',
  'title-page',
]);
const WRAPPER_KINDS = new Set(['edition', 'translation']);
const RELEASE_PDF_INDEX_PATH = path.resolve(process.cwd(), 'tmp', 'release-pdfs.json');
const EXPORT_ROOT = path.resolve(process.env.BOOKSTACKS_EXPORT_ROOT || path.join(process.cwd(), 'public', 'downloads'));

function loadReleasePdfHrefs(): Record<string, string> {
  if (!fs.existsSync(RELEASE_PDF_INDEX_PATH)) return {};
  const values = JSON.parse(fs.readFileSync(RELEASE_PDF_INDEX_PATH, 'utf8')) as Record<string, unknown>;
  return Object.fromEntries(Object.entries(values).filter((entry): entry is [string, string] => (
    entry[0].toLowerCase().endsWith('.pdf')
    && typeof entry[1] === 'string'
    && entry[1].startsWith('https://github.com/')
  )));
}

const RELEASE_PDF_HREFS = loadReleasePdfHrefs();

const AUTHOR_PROFILE_DATA = authorProfileData as Record<string, Omit<Author, 'slug' | 'works'>>;

export const PUBLISHED_AUTHOR_SLUGS = new Set(Object.keys(AUTHOR_PROFILE_DATA));

const AUTHOR_PROFILES = Object.fromEntries(
  Object.entries(AUTHOR_PROFILE_DATA).map(([slug, profile]) => [slug, { slug, ...profile }]),
) as Record<string, Omit<Author, 'works'>>;

const WORK_TITLES: Record<string, string> = {
  'a-study-in-scarlet': 'A Study in Scarlet',
  'alcibiades-1': 'Alcibiades I',
  'alcibiades-2': 'Alcibiades II',
  'apology': 'Apology',
  'charmides': 'Charmides',
  'cleitophon': 'Cleitophon',
  'cratylus': 'Cratylus',
  'critias': 'Critias',
  'crito': 'Crito',
  'epinomis': 'Epinomis',
  'euthydemus': 'Euthydemus',
  'euthyphro': 'Euthyphro',
  'greater-hippias': 'Greater Hippias',
  'hipparchus': 'Hipparchus',
  'ion': 'Ion',
  'laches': 'Laches',
  'laws': 'Laws',
  'lesser-hippias': 'Lesser Hippias',
  'letters': 'Letters',
  'lovers': 'Lovers',
  'lysis': 'Lysis',
  'menexenus': 'Menexenus',
  'minos': 'Minos',
  'parmenides': 'Parmenides',
  'phaedo': 'Phaedo',
  'philebus': 'Philebus',
  'protagoras': 'Protagoras',
  'sophist': 'Sophist',
  'statesman': 'Statesman',
  'theaetetus': 'Theaetetus',
  'theages': 'Theages',
  'a-christmas-carol': 'A Christmas Carol',
  'a-short-history-of-england': 'A Short History of England',
  'a-tale-of-two-cities': 'A Tale of Two Cities',
  'anna-karenina': 'Anna Karenina',
  'barnaby-rudge': 'Barnaby Rudge',
  'bleak-house': 'Bleak House',
  'brothers-karamazov': 'The Brothers Karamazov',
  'crime-and-punishment': 'Crime and Punishment',
  'david-copperfield': 'David Copperfield',
  'demons': 'Demons',
  'emma': 'Emma',
  'his-last-bow': 'His Last Bow',
  'gorgias': 'Gorgias',
  'jane-eyre-an-autobiography': 'Jane Eyre: An Autobiography',
  'mansfield-park': 'Mansfield Park',
  'martin-chuzzlewit': 'Martin Chuzzlewit',
  'middlemarch': 'Middlemarch',
  'meno': 'Meno',
  'metaphysics': 'Metaphysics',
  'nicholas-nickleby': 'Nicholas Nickleby',
  'nicomachean-ethics': 'Nicomachean Ethics',
  'northanger-abbey': 'Northanger Abbey',
  'notes-from-underground': 'Notes from Underground',
  'oliver-twist': 'Oliver Twist',
  'persuasion': 'Persuasion',
  'phaedrus': 'Phaedrus',
  'poetics': 'Poetics',
  'politics': 'Politics',
  'pride-and-prejudice': 'Pride and Prejudice',
  'republic': 'The Republic',
  'resurrection': 'Resurrection',
  'sense-and-sensibility': 'Sense and Sensibility',
  'symposium': 'Symposium',
  'the-adolescent': 'The Adolescent',
  'the-adventures-of-sherlock-holmes': 'The Adventures of Sherlock Holmes',
  'the-case-book-of-sherlock-holmes': 'The Case-Book of Sherlock Holmes',
  'the-double': 'The Double',
  'the-hound-of-the-baskervilles': 'The Hound of the Baskervilles',
  'the-idiot': 'The Idiot',
  'the-man-who-was-thursday-a-nightmare': 'The Man Who Was Thursday: A Nightmare',
  'the-memoirs-of-sherlock-holmes': 'The Memoirs of Sherlock Holmes',
  'the-return-of-sherlock-holmes': 'The Return of Sherlock Holmes',
  'the-sign-of-the-four': 'The Sign of the Four',
  'the-valley-of-fear': 'The Valley of Fear',
  'timaeus': 'Timaeus',
  'war-and-peace': 'War and Peace',
};

const LANGUAGE_DATA: Record<string, { code: string; name: string }> = {
  eng: { code: 'en', name: 'English' },
  fra: { code: 'fr', name: 'French' },
  spa: { code: 'es', name: 'Spanish' },
  grc: { code: 'grc', name: 'Ancient Greek' },
  rus: { code: 'ru', name: 'Russian' },
};

export interface Library {
  authors: Author[];
  workCount: number;
  editionCount: number;
  unitCount: number;
}

export interface Author {
  slug: string;
  name: string;
  dates: string;
  portrait: string;
  works: Work[];
}

export interface Work {
  slug: string;
  title: string;
  authorSlug: string;
  editions: Edition[];
}

export interface Edition {
  code: string;
  language: string;
  languageName: string;
  sourceTitle: string;
  sourceFile: string;
  pdfFile?: string;
  pdfHref?: string;
  kind: string;
  unitKind: string;
  units: ReadingUnit[];
  toc: TocNode[];
  persons: RegistryEntry[];
  places: RegistryEntry[];
}

export interface ReadingUnit {
  path: string;
  segments: string[];
  title: string;
  context: string[];
  html: string;
  previousPath?: string;
  nextPath?: string;
}

export interface TocNode {
  label: string;
  kind: string;
  href?: string;
  children: TocNode[];
}

export interface RegistryEntry {
  id: string;
  name: string;
  description: string;
}

interface ParsedEdition extends Edition {
  authorSlug: string;
  workSlug: string;
}

interface EntityMaps {
  persons: Map<string, RegistryEntry>;
  places: Map<string, RegistryEntry>;
  notes: Map<string, any>;
  referencedNoteIds: Set<string>;
}

interface RenderContext {
  locale: Locale;
  noteIndex: number;
  assetBase: string;
}

let libraryCache: Library | undefined;

export function getLibrary(): Library {
  if (libraryCache) return libraryCache;

  const teiRoot = path.resolve(process.cwd(), 'tei');
  const files = findXmlFiles(teiRoot);
  const parsed = files.map(parseEdition)
    .filter((edition) => PUBLISHED_AUTHOR_SLUGS.has(edition.authorSlug));
  const authors = new Map<string, Author>();

  for (const edition of parsed) {
    const profile = AUTHOR_PROFILES[edition.authorSlug] ?? {
      slug: edition.authorSlug,
      name: titleFromSlug(edition.authorSlug),
      dates: '',
      portrait: `${edition.authorSlug}.png`,
    };
    let author = authors.get(edition.authorSlug);
    if (!author) {
      author = { ...profile, works: [] };
      authors.set(edition.authorSlug, author);
    }

    let work = author.works.find((item) => item.slug === edition.workSlug);
    if (!work) {
      work = {
        slug: edition.workSlug,
        title: WORK_TITLES[edition.workSlug] ?? titleFromSlug(edition.workSlug),
        authorSlug: edition.authorSlug,
        editions: [],
      };
      author.works.push(work);
    }
    work.editions.push(edition);
  }

  const authorList = [...authors.values()].sort((a, b) => a.name.localeCompare(b.name));
  for (const author of authorList) {
    author.works.sort((a, b) => a.title.localeCompare(b.title));
    for (const work of author.works) {
      work.editions.sort((a, b) => languageOrder(a.code) - languageOrder(b.code));
    }
  }

  libraryCache = {
    authors: authorList,
    workCount: authorList.reduce((sum, author) => sum + author.works.length, 0),
    editionCount: parsed.length,
    unitCount: parsed.reduce((sum, edition) => sum + edition.units.length, 0),
  };
  return libraryCache;
}

export function authorHref(author: Pick<Author, 'slug'>): string {
  return `/authors/${author.slug}`;
}

export function workHref(work: Pick<Work, 'authorSlug' | 'slug'>): string {
  return `/authors/${work.authorSlug}/${work.slug}`;
}

export function editionHref(work: Pick<Work, 'authorSlug' | 'slug'>, edition: Pick<Edition, 'code'>): string {
  return `${workHref(work)}/${edition.code}`;
}

export function unitHref(work: Pick<Work, 'authorSlug' | 'slug'>, edition: Pick<Edition, 'code'>, unit: Pick<ReadingUnit, 'path'>): string {
  return `${editionHref(work, edition)}/${unit.path}`;
}

export function localizedAuthorHref(author: Pick<Author, 'slug'>, locale: Locale): string {
  return `/${locale}/authors/${author.slug}`;
}

export function localizedWorkHref(work: Pick<Work, 'authorSlug' | 'slug'>, locale: Locale): string {
  return `${localizedAuthorHref({ slug: work.authorSlug }, locale)}/${work.slug}`;
}

export function localizedEditionHref(work: Pick<Work, 'authorSlug' | 'slug'>, edition: Pick<Edition, 'code'>): string {
  const locale = isLocale(edition.code) ? edition.code : 'en';
  return localizedWorkHref(work, locale);
}

export function localizedUnitHref(work: Pick<Work, 'authorSlug' | 'slug'>, edition: Pick<Edition, 'code'>, unit: Pick<ReadingUnit, 'path'>): string {
  return `${localizedEditionHref(work, edition)}/${unit.path}`;
}

export function editionForLocale(work: Pick<Work, 'editions'>, locale: Locale): Edition | undefined {
  return work.editions.find((edition) => edition.code === locale);
}

export function readingOrganizationLabel(kind: string, locale: Locale): string {
  const labels: Record<Locale, Record<string, string>> = {
    en: { scene: 'scene', section: 'section', chapter: 'chapter', stave: 'stave', bekker_page: 'Bekker page', part: 'part' },
    fr: { scene: 'scène', section: 'section', chapter: 'chapitre', stave: 'strophe', bekker_page: 'page de Bekker', part: 'partie' },
    es: { scene: 'escena', section: 'sección', chapter: 'capítulo', stave: 'estrofa', bekker_page: 'página de Bekker', part: 'parte' },
    grc: { scene: 'σκηνή', section: 'τμῆμα', chapter: 'κεφάλαιον', stave: 'στροφή', bekker_page: 'σελίδα Bekker', part: 'μέρος' },
    ru: { scene: 'сцены', section: 'разделы', chapter: 'главы', stave: 'части', bekker_page: 'страницы Беккера', part: 'части' },
  };
  return labels[locale][kind] ?? kind.replaceAll('_', ' ');
}

export function localizedWorkTitle(work: Work, locale: Locale): string {
  return editionForLocale(work, locale)?.sourceTitle ?? work.title;
}

export function editionTeiHref(
  author: Pick<Author, 'slug'>,
  edition: Pick<Edition, 'sourceFile'>,
): string {
  return `/tei/${author.slug}/${edition.sourceFile}`;
}

export function editionPdfHref(
  author: Pick<Author, 'slug'>,
  edition: Pick<Edition, 'pdfFile' | 'pdfHref'>,
): string | undefined {
  if (!edition.pdfFile) return undefined;
  return edition.pdfHref ?? `/tei/${author.slug}/${edition.pdfFile}`;
}

function findXmlFiles(root: string): string[] {
  if (!fs.existsSync(root)) throw new Error(`TEI directory not found: ${root}`);
  return fs.readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .flatMap((entry) => fs.readdirSync(path.join(root, entry.name), { withFileTypes: true })
      .filter((file) => file.isFile() && file.name.endsWith('.xml'))
      .map((file) => path.join(root, entry.name, file.name)))
    .sort();
}

function parseEdition(filePath: string): ParsedEdition {
  const fileName = path.basename(filePath);
  const stem = fileName.replace(/\.xml$/i, '');
  const pdfName = fileName.replace(/\.xml$/i, '.pdf');
  const match = fileName.match(/^([^_]+)_(.+)_([a-z]{3})\.xml$/);
  if (!match) throw new Error(`Unexpected TEI filename: ${fileName}`);
  const [, authorSlug, workSlug, fileLanguage] = match;
  const repositoryPdfPath = path.join(path.dirname(filePath), pdfName);
  const generatedPdfPath = path.join(EXPORT_ROOT, authorSlug, stem, pdfName);
  const pdfHref = fs.existsSync(repositoryPdfPath)
    ? `/tei/${authorSlug}/${pdfName}`
    : fs.existsSync(generatedPdfPath)
      ? `/downloads/${authorSlug}/${stem}/${pdfName}`
      : RELEASE_PDF_HREFS[pdfName];
  const language = LANGUAGE_DATA[fileLanguage] ?? { code: fileLanguage, name: fileLanguage };
  const locale: Locale = isLocale(language.code) ? language.code : 'en';
  const source = fs.readFileSync(filePath, 'utf8');
  const document = new DOMParser().parseFromString(source, 'application/xml');
  const parseError = descendants(document, 'parsererror')[0];
  if (parseError) throw new Error(`Invalid XML in ${fileName}: ${cleanText(parseError.textContent)}`);
  if (authorSlug === 'shakespeare' && fileLanguage === 'fra') repairConvertedDrama(document);

  const titleStmt = descendants(document, 'titleStmt')[0];
  const directTitles = directElementChildren(titleStmt).filter((node) => node.localName === 'title');
  const sourceTitleNode = directTitles.find((node) => cleanText(node.getAttribute?.('type')) === 'main') ?? directTitles[0];
  const sourceTitle = cleanText(sourceTitleNode?.textContent)
    || WORK_TITLES[workSlug]
    || titleFromSlug(workSlug);
  const entities = parseRegistries(document);
  const text = descendants(document, 'text')[0];
  if (!text) throw new Error(`No TEI text element in ${fileName}`);

  const allDivs = descendants(text, 'div');
  const kindCounts = new Map<string, number>();
  for (const div of allDivs) {
    const kind = kindOf(div);
    kindCounts.set(kind, (kindCounts.get(kind) ?? 0) + 1);
  }
  const unitKind = READING_KIND_PRIORITY.find((kind) => kindCounts.has(kind)) ?? 'div';
  const unitPriority = READING_KIND_PRIORITY.indexOf(unitKind);
  const fallbackKinds = new Set(READING_KIND_PRIORITY.slice(unitPriority + 1));
  const selected = new Set<any>();
  for (const div of allDivs) {
    const kind = kindOf(div);
    const containsPrimaryUnits = descendants(div, 'div').some((child) => kindOf(child) === unitKind);
    const containsFallbackUnits = descendants(div, 'div').some((child) => fallbackKinds.has(kindOf(child)));
    if (
      kind === unitKind
      || (fallbackKinds.has(kind) && !containsPrimaryUnits && !containsFallbackUnits)
      || (SUPPLEMENTARY_KINDS.has(kind) && !containsPrimaryUnits)
    ) selected.add(div);
  }
  if (selected.size === 0) {
    for (const div of allDivs.filter((candidate) => directDivChildren(candidate).length === 0)) selected.add(div);
  }

  const segmentCache = new Map<any, string>();
  const usedPaths = new Set<string>();
  const units: ReadingUnit[] = [];
  for (const div of allDivs) {
    if (!selected.has(div)) continue;
    if (hasSelectedAncestor(div, selected)) continue;
    const segments = divisionPath(div, text, segmentCache);
    const finalSegments = [...segments];
    let pathValue = finalSegments.join('/');
    let suffix = 2;
    while (usedPaths.has(pathValue)) {
      finalSegments[finalSegments.length - 1] = `${segments[segments.length - 1]}-${suffix++}`;
      pathValue = finalSegments.join('/');
    }
    usedPaths.add(pathValue);
    const title = divisionLabel(div, segmentCache, locale);
    const context = divisionAncestors(div, text)
      .filter((ancestor) => !WRAPPER_KINDS.has(kindOf(ancestor)))
      .map((ancestor) => divisionLabel(ancestor, segmentCache, locale));
    units.push({
      path: pathValue,
      segments: finalSegments,
      title,
      context,
      html: renderDivision(div, entities, locale, `/tei/${authorSlug}`),
    });
  }

  for (let index = 0; index < units.length; index += 1) {
    units[index].previousPath = units[index - 1]?.path;
    units[index].nextPath = units[index + 1]?.path;
  }

  const kind = allDivs.map(kindOf).find((item) => item === 'edition' || item === 'translation') ?? 'edition';
  const routeBase = `/${locale}/authors/${authorSlug}/${workSlug}`;
  const toc = buildDocumentToc(text, selected, units, segmentCache, routeBase, locale);

  return {
    authorSlug,
    workSlug,
    code: language.code,
    language: fileLanguage,
    languageName: language.name,
    sourceTitle,
    sourceFile: fileName,
    pdfFile: pdfHref ? pdfName : undefined,
    pdfHref,
    kind,
    unitKind,
    units,
    toc,
    persons: [...entities.persons.values()].sort((a, b) => a.name.localeCompare(b.name)),
    places: [...entities.places.values()].sort((a, b) => a.name.localeCompare(b.name)),
  };
}

function parseRegistries(document: any): EntityMaps {
  const persons = new Map<string, RegistryEntry>();
  const places = new Map<string, RegistryEntry>();
  const notes = new Map<string, any>();
  const referencedNoteIds = new Set<string>();

  for (const node of [...descendants(document, 'person'), ...descendants(document, 'personGrp')]) {
    const id = xmlId(node);
    if (!id) continue;
    const nameNode = descendants(node, 'persName')[0] ?? descendants(node, 'name')[0];
    const name = cleanText(nameNode?.textContent) || id;
    const description = registryDescription(node, nameNode);
    persons.set(id, { id, name, description });
  }
  for (const node of descendants(document, 'place')) {
    const id = xmlId(node);
    if (!id) continue;
    const nameNode = descendants(node, 'placeName')[0] ?? descendants(node, 'name')[0];
    const name = cleanText(nameNode?.textContent) || id;
    const description = registryDescription(node, nameNode);
    places.set(id, { id, name, description });
  }
  for (const node of descendants(document, 'note')) {
    const id = xmlId(node);
    if (id) notes.set(id, node);
  }
  for (const node of descendants(document, 'ref')) {
    const target = cleanText(node.getAttribute?.('target'));
    if (target.startsWith('#') && notes.has(target.slice(1))) {
      referencedNoteIds.add(target.slice(1));
    }
  }
  return { persons, places, notes, referencedNoteIds };
}

function repairConvertedDrama(document: any): void {
  for (const speech of descendants(document, 'sp')) {
    const children = directElementChildren(speech);
    const speaker = children.find((child) => child.localName === 'speaker');
    const stage = children.find((child) => child.localName === 'stage');
    if (!speaker || !stage) continue;

    const speakerText = cleanText(speaker.textContent);
    const stageText = cleanText(stage.textContent);
    const trailingMarker = speakerText.match(/^(.*?)(\d+)$/u);
    if (trailingMarker && /\p{L}/u.test(trailingMarker[1])) {
      replaceElementText(document, speaker, trailingMarker[1]);
      continue;
    }
    if (speakerText.endsWith('(') && stageText.endsWith(')')) {
      replaceElementText(document, speaker, speakerText.slice(0, -1).trimEnd());
      replaceElementText(document, stage, `(${stageText}`);
      continue;
    }

    const letterCount = [...speakerText].filter((character) => /\p{L}/u.test(character)).length;
    const fragmentary = letterCount <= 2 || speakerText.startsWith('(') || /['’]$/u.test(speakerText);
    if (!fragmentary) continue;

    const paragraphs = children.filter((child) => child.localName === 'p');
    const combined = `${speakerText}${stageText}`;
    const parent = speech.parentNode;
    if (!parent) continue;

    if (speakerText.startsWith('(')) {
      const replacement = document.createElementNS(TEI_NS, 'stage');
      replacement.setAttribute('type', stage.getAttribute?.('type') || 'business');
      replacement.appendChild(document.createTextNode([combined, ...paragraphs.map((paragraph) => cleanText(paragraph.textContent))].join(' ')));
      parent.replaceChild(replacement, speech);
      continue;
    }

    const firstParagraph = document.createElementNS(TEI_NS, 'p');
    firstParagraph.appendChild(document.createTextNode(combined));
    parent.insertBefore(firstParagraph, speech);
    for (const paragraph of paragraphs) parent.insertBefore(paragraph, speech);
    parent.removeChild(speech);
  }
}

function replaceElementText(document: any, element: any, value: string): void {
  while (element.firstChild) element.removeChild(element.firstChild);
  element.appendChild(document.createTextNode(value));
}

function registryDescription(node: any, nameNode: any): string {
  const note = descendants(node, 'note')[0] ?? descendants(node, 'desc')[0]
    ?? descendants(node, 'occupation')[0] ?? descendants(node, 'state')[0];
  const text = cleanText(note?.textContent);
  if (!text || text === cleanText(nameNode?.textContent)) return '';
  return text.length > 320 ? `${text.slice(0, 317)}…` : text;
}

function buildDocumentToc(
  text: any,
  selected: Set<any>,
  units: ReadingUnit[],
  segmentCache: Map<any, string>,
  routeBase: string,
  locale: Locale,
): TocNode[] {
  const unitByPath = new Map(units.map((unit) => [unit.path, unit]));
  const sections: TocNode[] = [];
  for (const areaName of ['front', 'body', 'back']) {
    const area = directElementChildren(text).find((child) => child.localName === areaName);
    if (!area) continue;
    const children = buildTocChildren(area, text, selected, unitByPath, segmentCache, routeBase, locale);
    if (!children.length) continue;
    if (areaName === 'body') sections.push(...children);
    else sections.push({ label: areaName === 'front' ? ui(locale).frontMatter : ui(locale).backMatter, kind: areaName, children });
  }
  if (!sections.length) {
    sections.push(...buildTocChildren(text, text, selected, unitByPath, segmentCache, routeBase, locale));
  }
  return sections;
}

function buildTocChildren(
  parent: any,
  text: any,
  selected: Set<any>,
  unitByPath: Map<string, ReadingUnit>,
  segmentCache: Map<any, string>,
  routeBase: string,
  locale: Locale,
): TocNode[] {
  const nodes: TocNode[] = [];
  for (const div of directDivChildren(parent)) {
    const pathValue = divisionPath(div, text, segmentCache).join('/');
    if (selected.has(div) && !hasSelectedAncestor(div, selected)) {
      const unit = unitByPath.get(pathValue);
      if (unit) {
        nodes.push({
          label: unit.title,
          kind: kindOf(div),
          href: `${routeBase}/${unit.path}`,
          children: [],
        });
      }
      continue;
    }
    const children = buildTocChildren(div, text, selected, unitByPath, segmentCache, routeBase, locale);
    if (!children.length) continue;
    const kind = kindOf(div);
    if (WRAPPER_KINDS.has(kind) && !directHead(div)) nodes.push(...children);
    else nodes.push({ label: divisionLabel(div, segmentCache, locale), kind, children });
  }
  return nodes;
}

function divisionPath(div: any, text: any, segmentCache: Map<any, string>): string[] {
  return [...divisionAncestors(div, text), div]
    .filter((node) => !WRAPPER_KINDS.has(kindOf(node)))
    .map((node) => divisionSegment(node, segmentCache));
}

function divisionAncestors(div: any, text: any): any[] {
  const result: any[] = [];
  let parent = div.parentNode;
  while (parent && parent !== text) {
    if (parent.nodeType === 1 && parent.localName === 'div') result.unshift(parent);
    parent = parent.parentNode;
  }
  return result;
}

function divisionSegment(div: any, cache: Map<any, string>): string {
  const cached = cache.get(div);
  if (cached) return cached;
  const kind = slugify(kindOf(div).replaceAll('_', '-')) || 'section';
  const n = cleanText(div.getAttribute?.('n'));
  const usableN = n && /^[\p{L}\p{N}.-]{1,24}$/u.test(n) ? slugify(n) : '';
  const siblings = directDivChildren(div.parentNode).filter((item) => kindOf(item) === kindOf(div));
  const ordinal = Math.max(1, siblings.indexOf(div) + 1).toString().padStart(2, '0');
  const segment = `${kind}-${usableN || ordinal}`;
  cache.set(div, segment);
  return segment;
}

function divisionLabel(div: any, segmentCache: Map<any, string>, locale: Locale): string {
  const head = directHead(div);
  if (head) return truncate(cleanText(head.textContent), 180);
  const kind = kindOf(div);
  const n = cleanText(div.getAttribute?.('n'));
  if (n && !/^urn:/i.test(n)) return `${displayKind(kind, locale)} ${n}`;
  const segment = divisionSegment(div, segmentCache);
  const ordinal = segment.match(/-(\d+)$/)?.[1]?.replace(/^0+/, '') || '';
  return ordinal ? `${displayKind(kind, locale)} ${ordinal}` : displayKind(kind, locale);
}

function renderDivision(div: any, entities: EntityMaps, locale: Locale, assetBase: string): string {
  const context: RenderContext = { locale, noteIndex: 0, assetBase };
  let html = '';
  for (const child of directChildNodes(div)) {
    if (child.nodeType === 1 && child.localName === 'head') continue;
    html += renderNode(child, entities, 2, context);
  }
  return html;
}

function renderNode(node: any, entities: EntityMaps, headingLevel: number, context: RenderContext): string {
  if (!node) return '';
  if (node.nodeType === 3 || node.nodeType === 4) return escapeHtml(node.nodeValue ?? '');
  if (node.nodeType !== 1) return '';

  const name = node.localName;
  const children = () => normalizeInlineSpacing(
    directChildNodes(node).map((child) => renderNode(child, entities, headingLevel, context)).join(''),
  );
  const text = () => cleanText(node.textContent);
  const lang = node.getAttribute?.('xml:lang') || node.getAttributeNS?.(XML_NS, 'lang');
  const langAttr = lang ? ` lang="${escapeAttr(lang)}"` : '';

  switch (name) {
    case 'div': {
      const kind = kindOf(node);
      const content = directChildNodes(node).map((child) => renderNode(child, entities, headingLevel + 1, context)).join('');
      return `<section class="tei-division tei-${escapeAttr(slugify(kind))}">${content}</section>`;
    }
    case 'head':
      return `<h${Math.min(6, headingLevel)}>${children()}</h${Math.min(6, headingLevel)}>`;
    case 'p': {
      const rend = `${node.getAttribute?.('rend') ?? ''} ${node.getAttribute?.('style') ?? ''}`.toLowerCase();
      const firstClass = isFirstParagraph(node) ? ' tei-first-paragraph' : '';
      const rendClasses = [
        /\b(?:noindent|notindent)\b/.test(rend) && 'tei-no-indent',
        /\bcenter\b/.test(rend) && 'tei-align-center',
        /\bright\b/.test(rend) && 'tei-align-right',
        /\b(?:pre|preformatted)\b/.test(rend) && 'tei-preformatted',
        /\bletter\b/.test(rend) && 'tei-letter',
      ].filter(Boolean).join(' ');
      const classAttr = `tei-paragraph${firstClass}${rendClasses ? ` ${rendClasses}` : ''}`;
      if (/\bsubheading\b/.test(rend)) {
        const level = Math.min(6, headingLevel);
        return `<h${level} class="tei-subheading">${children()}</h${level}>`;
      }
      if (/\bblockquote\b/.test(rend)) {
        return `<blockquote class="tei-blockquote"><p class="${classAttr}">${children()}</p></blockquote>`;
      }
      return `<p class="${classAttr}">${children()}</p>`;
    }
    case 'sp':
      return `<section class="tei-speech">${children()}</section>`;
    case 'speaker': {
      const label = text().replace(/[.\s]+$/u, '').toLocaleUpperCase();
      return `<div class="tei-speaker">${escapeHtml(label)}.</div>`;
    }
    case 'stage': {
      const stageType = slugify(cleanText(node.getAttribute?.('type'))) || 'direction';
      const stageRend = cleanText(node.getAttribute?.('rend')).toLowerCase();
      const isSceneIntroduction = /\bscene-introduction\b/.test(stageRend);
      const isBlock = ['entrance', 'exit', 'setting'].includes(stageType);
      const tag = isBlock ? 'div' : 'span';
      const content = children();
      const stageText = text();
      const delimited = /^[([]/u.test(stageText)
        || /[)\]][.,;:]?$/u.test(stageText)
        || hasPairedDelimiters(stageText, [['(', ')'], ['[', ']']]);
      const stageClass = `tei-stage tei-stage-${escapeAttr(stageType)}${isSceneIntroduction ? ' tei-stage-scene-introduction' : ''}`;
      const bracketed = isSceneIntroduction
        ? `<span class="tei-stage-bracket">[</span>${content}<span class="tei-stage-bracket">]</span>`
        : `[${content}]`;
      return `<${tag} class="${stageClass}">${delimited ? content : bracketed}</${tag}>`;
    }
    case 'said': {
      const speaker = referencedEntities(node.getAttribute?.('who'), entities.persons);
      const addressee = referencedEntities(node.getAttribute?.('toWhom'), entities.persons);
      const tooltip = [speaker && `Speaker: ${speaker}`, addressee && `Addressed to: ${addressee}`].filter(Boolean).join(' · ');
      return `<span class="tei-said"${tooltip ? ` title="${escapeAttr(tooltip)}"` : ''}>${children()}</span>`;
    }
    case 'q':
    case 'quote': {
      const block = directElementChildren(node).some((child) => ['p', 'lg', 'sp'].includes(child.localName));
      if (block) return `<blockquote>${children()}</blockquote>`;
      const delimited = hasPairedDelimiters(text(), [['“', '”'], ['‘', '’'], ['«', '»'], ['„', '“'], ['"', '"'], ["'", "'"]]);
      return `<q${delimited ? ' class="tei-quote-delimited"' : ''}>${children()}</q>`;
    }
    case 'persName':
    case 'placeName':
    case 'rs':
    case 'name': {
      const reference = node.getAttribute?.('ref') || node.getAttribute?.('key');
      const map = name === 'placeName' ? entities.places : entities.persons;
      const detail = referencedEntities(reference, map, true);
      const stageNameClass = node.parentNode?.localName === 'stage' ? ' tei-stage-name' : '';
      return `<span class="tei-entity${stageNameClass}"${detail ? ` title="${escapeAttr(detail)}"` : ''}>${children()}</span>`;
    }
    case 'note': {
      const id = xmlId(node);
      if (id && entities.referencedNoteIds.has(id)) return '';
      return renderInlineNote(node, entities, headingLevel, context);
    }
    case 'pb':
    case 'milestone':
      return '';
    case 'lb':
      return '<br />';
    case 'emph':
      return `<em>${children()}</em>`;
    case 'title':
    case 'bibl':
      return `<cite>${children()}</cite>`;
    case 'foreign':
      return `<span class="tei-foreign"${langAttr}>${children()}</span>`;
    case 'hi': {
      const rend = `${node.getAttribute?.('rend') ?? ''} ${node.getAttribute?.('style') ?? ''}`.toLowerCase();
      if (rend.includes('bold') || rend.includes('strong')) return `<strong>${children()}</strong>`;
      if (rend.includes('sup')) return `<sup>${children()}</sup>`;
      if (rend.includes('sub')) return `<sub>${children()}</sub>`;
      if (rend.includes('small') || /\bsc(?:\W|$)/.test(rend)) return `<span class="tei-smallcaps">${children()}</span>`;
      if (rend.includes('razradka')) return `<span class="tei-letterspaced">${children()}</span>`;
      if (rend.includes('span') || rend.includes('normal')) return `<span>${children()}</span>`;
      return `<em>${children()}</em>`;
    }
    case 'lg':
      return `<div class="tei-line-group">${children()}</div>`;
    case 'l':
      return `<span class="tei-line">${children()}</span>`;
    case 'castList':
      return `<div class="tei-cast-list" role="list">${children()}</div>`;
    case 'castItem':
      return `<p class="tei-cast-item" role="listitem">${children()}</p>`;
    case 'role':
      return `<span class="tei-cast-role">${children()}</span>`;
    case 'label':
      return `<span class="tei-label">${children()}</span>`;
    case 'ref': {
      const target = cleanText(node.getAttribute?.('target'));
      const note = target.startsWith('#') ? entities.notes.get(target.slice(1)) : undefined;
      if (note) return renderInlineNote(note, entities, headingLevel, context);
      return /^(https?:\/\/|#)/.test(target)
        ? `<a href="${escapeAttr(target)}">${children()}</a>`
        : children();
    }
    case 'choice': {
      const preferred = ['corr', 'reg', 'expan', 'orig', 'sic', 'abbr']
        .map((tag) => directElementChildren(node).find((child) => child.localName === tag))
        .find(Boolean);
      return preferred ? renderNode(preferred, entities, headingLevel, context) : children();
    }
    case 'del':
      return `<del>${children()}</del>`;
    case 'add':
      return `<ins>${children()}</ins>`;
    case 'gap':
      return '<span class="tei-gap" aria-label="Omitted text">[…]</span>';
    case 'sic':
      return `<span class="tei-sic">${children()}</span>`;
    case 'corr':
      return children();
    case 'table':
      return `<div class="table-scroll"><table>${children()}</table></div>`;
    case 'row':
      return `<tr>${children()}</tr>`;
    case 'cell':
      return `<td>${children()}</td>`;
    case 'figure':
      return `<figure class="tei-figure">${children()}</figure>`;
    case 'graphic': {
      const source = cleanText(node.getAttribute?.('url'));
      const relative = source.replace(/^\.\//, '');
      if (!/^img\/[A-Za-z0-9._/-]+$/.test(relative) || relative.includes('..')) return '';
      const description = cleanText(
        directElementChildren(node.parentNode).find((child) => child.localName === 'figDesc')?.textContent,
      );
      return `<img class="tei-graphic" src="${escapeAttr(`${context.assetBase}/${relative}`)}" alt="${escapeAttr(description)}" loading="lazy" decoding="async" />`;
    }
    case 'figDesc':
      return `<figcaption>${children()}</figcaption>`;
    case 'floatingText':
      return `<aside class="tei-floating-text">${children()}</aside>`;
    case 'opener':
    case 'closer':
    case 'postscript':
    case 'epigraph':
      return `<div class="tei-${name.toLowerCase()}">${children()}</div>`;
    case 'salute':
    case 'signed':
    case 'dateline':
    case 'trailer':
      return `<p class="tei-${name.toLowerCase()}">${children()}</p>`;
    case 'date':
      return `<time>${children()}</time>`;
    case 'seg':
    case 'term':
    case 'gloss':
    case 'objectName':
    case 'orgName':
    case 'forename':
    case 'surname':
    case 'addName':
    case 'roleName':
      return `<span${langAttr}>${children()}</span>`;
    case 'certainty':
    case 'shift':
    case 'metamark':
    case 'fw':
      return '';
    default:
      return children() || escapeHtml(text());
  }
}

function isFirstParagraph(node: any): boolean {
  for (const sibling of directElementChildren(node.parentNode)) {
    if (sibling === node) return true;
    if (sibling.localName === 'p') return false;
  }
  return true;
}

function renderInlineNote(note: any, entities: EntityMaps, headingLevel: number, context: RenderContext): string {
  let content = directChildNodes(note).map((child) => {
    if (child.nodeType === 1 && child.localName === 'p') {
      return directChildNodes(child).map((part) => renderNode(part, entities, headingLevel, context)).join('');
    }
    return renderNode(child, entities, headingLevel, context);
  }).join('').trim();
  const noteText = cleanText(note.textContent);
  if (/^\[(?:\*|\d+)\]\s*/.test(noteText)) {
    content = content.replace(/^\s*\[(?:\*|\d+)\]\s*/, '');
  } else if (/^\*\s+/.test(noteText)) {
    content = content.replace(/^\s*\*\s+/, '');
  } else if (/^\[.*\]$/s.test(noteText)) {
    content = content.replace(/^\s*\[/, '').replace(/\]\s*$/, '');
  }
  if (!content.trim()) return '';
  context.noteIndex += 1;
  const number = context.noteIndex;
  const sourceId = xmlId(note) || `generated-${number}`;
  const popoverId = `note-${slugify(sourceId)}-${number}`;
  const labels = ui(context.locale);
  return `<span class="tei-note"><button class="tei-note-ref" type="button" aria-expanded="false" aria-controls="${escapeAttr(popoverId)}" aria-label="${escapeAttr(`${labels.footnote} ${number}`)}">${number}</button><span class="tei-note-popover" id="${escapeAttr(popoverId)}" role="note" tabindex="-1" hidden><span class="tei-note-label">${escapeHtml(`${labels.footnote} ${number}`)}</span><span class="tei-note-text">${content.trim()}</span><button class="tei-note-close" type="button" aria-label="${escapeAttr(labels.closeFootnote)}">×</button></span></span>`;
}

function normalizeInlineSpacing(value: string): string {
  return value
    .replace(/\s+(?=<span class="tei-note">)/g, '')
    .replace(/(<\/button><\/span><\/span>)\s+([,.;:!?])/g, '$1$2');
}

function hasPairedDelimiters(value: string, pairs: Array<[string, string]>): boolean {
  const normalized = cleanText(value);
  return pairs.some(([opening, closing]) => (
    normalized.startsWith(opening)
    && new RegExp(`${escapeRegExp(closing)}[.,;:]?$`, 'u').test(normalized)
  ));
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function referencedEntities(value: string, registry: Map<string, RegistryEntry>, includeDescription = false): string {
  if (!value) return '';
  return value.split(/\s+/)
    .map((token) => token.replace(/^#/, ''))
    .map((id) => registry.get(id))
    .filter((entry): entry is RegistryEntry => Boolean(entry))
    .map((entry) => includeDescription && entry.description ? `${entry.name}: ${entry.description}` : entry.name)
    .join(', ');
}

function kindOf(node: any): string {
  return cleanText(node?.getAttribute?.('subtype') || node?.getAttribute?.('type')) || 'section';
}

function directHead(node: any): any | undefined {
  return directElementChildren(node).find((child) => child.localName === 'head');
}

function directDivChildren(node: any): any[] {
  return directElementChildren(node).filter((child) => child.localName === 'div');
}

function directElementChildren(node: any): any[] {
  return directChildNodes(node).filter((child) => child.nodeType === 1);
}

function directChildNodes(node: any): any[] {
  return node?.childNodes ? Array.from(node.childNodes as ArrayLike<any>) : [];
}

function descendants(node: any, localName: string): any[] {
  if (!node?.getElementsByTagNameNS) return [];
  const namespaced = Array.from(node.getElementsByTagNameNS('*', localName) as ArrayLike<any>);
  return namespaced.length ? namespaced : Array.from(node.getElementsByTagName(localName) as ArrayLike<any>);
}

function hasSelectedAncestor(node: any, selected: Set<any>): boolean {
  let parent = node.parentNode;
  while (parent) {
    if (selected.has(parent)) return true;
    parent = parent.parentNode;
  }
  return false;
}

function xmlId(node: any): string {
  return node?.getAttributeNS?.(XML_NS, 'id') || node?.getAttribute?.('xml:id') || '';
}

function displayKind(kind: string, locale: Locale): string {
  const normalized = kind.replaceAll('_', '-');
  const labels: Record<Locale, Record<string, string>> = {
    en: { act: 'Act', scene: 'Scene', chapter: 'Chapter', section: 'Section', book: 'Book', volume: 'Volume', part: 'Part', stave: 'Stave', introduction: 'Introduction', preface: 'Preface', prologue: 'Prologue', epilogue: 'Epilogue', 'bekker-page': 'Bekker page', 'suppressed-chapter': 'Suppressed chapter' },
    fr: { act: 'Acte', scene: 'Scène', chapter: 'Chapitre', section: 'Section', book: 'Livre', volume: 'Tome', part: 'Partie', stave: 'Strophe', introduction: 'Introduction', preface: 'Préface', prologue: 'Prologue', epilogue: 'Épilogue', 'bekker-page': 'Page de Bekker', 'suppressed-chapter': 'Chapitre supprimé' },
    es: { act: 'Acto', scene: 'Escena', chapter: 'Capítulo', section: 'Sección', book: 'Libro', volume: 'Tomo', part: 'Parte', stave: 'Estrofa', introduction: 'Introducción', preface: 'Prefacio', prologue: 'Prólogo', epilogue: 'Epílogo', 'bekker-page': 'Página de Bekker', 'suppressed-chapter': 'Capítulo suprimido' },
    grc: { act: 'Πρᾶξις', scene: 'Σκηνή', chapter: 'Κεφάλαιον', section: 'Τμῆμα', book: 'Βιβλίον', volume: 'Τόμος', part: 'Μέρος', stave: 'Στροφή', introduction: 'Εἰσαγωγή', preface: 'Προοίμιον', prologue: 'Πρόλογος', epilogue: 'Ἐπίλογος', 'bekker-page': 'Σελίς Bekker', 'suppressed-chapter': 'Κεφάλαιον ἀφαιρεθέν' },
    ru: { act: 'Действие', scene: 'Сцена', chapter: 'Глава', section: 'Раздел', book: 'Книга', volume: 'Том', part: 'Часть', stave: 'Часть', introduction: 'Введение', preface: 'Предисловие', prologue: 'Пролог', epilogue: 'Эпилог', 'bekker-page': 'Страница Беккера', 'suppressed-chapter': 'Исключённая глава' },
  };
  return labels[locale][normalized]
    ?? normalized.replaceAll('-', ' ').replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}

function titleFromSlug(slug: string): string {
  const small = new Set(['a', 'an', 'and', 'of', 'the', 'from']);
  return slug.split('-').map((word, index) => {
    if (index > 0 && small.has(word)) return word;
    return word.charAt(0).toUpperCase() + word.slice(1);
  }).join(' ');
}

function languageOrder(code: string): number {
  return ['en', 'fr', 'es', 'grc', 'ru'].indexOf(code) === -1 ? 99 : ['en', 'fr', 'es', 'grc', 'ru'].indexOf(code);
}

function cleanText(value: unknown): string {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function truncate(value: string, length: number): string {
  return value.length > length ? `${value.slice(0, length - 1).trim()}…` : value;
}

function slugify(value: string): string {
  return value.normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}

function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

function escapeAttr(value: unknown): string {
  return escapeHtml(value).replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}
