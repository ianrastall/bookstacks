import fs from 'node:fs';
import path from 'node:path';
import { DOMParser } from '@xmldom/xmldom';

const XML_NS = 'http://www.w3.org/XML/1998/namespace';
const READING_KIND_PRIORITY = ['section', 'chapter', 'stave', 'bekker_page', 'part'];
const SUPPLEMENTARY_KINDS = new Set([
  'preface',
  'postscript',
  'prologue',
  'epilogue',
  'introduction',
  'dedication',
  'characters',
  'suppressed-chapter',
]);
const WRAPPER_KINDS = new Set(['edition', 'translation']);

export const PUBLISHED_AUTHOR_SLUGS = new Set([
  'aristotle',
  'austen',
  'dickens',
  'dostoevsky',
  'plato',
  'tolstoy',
]);

const AUTHOR_PROFILES: Record<string, Omit<Author, 'works'>> = {
  aristotle: { slug: 'aristotle', name: 'Aristotle', dates: '384–322 BCE', portrait: 'aristotle.png' },
  austen: { slug: 'austen', name: 'Jane Austen', dates: '1775–1817', portrait: 'austen-jane.png' },
  dickens: { slug: 'dickens', name: 'Charles Dickens', dates: '1812–1870', portrait: 'dickens-charles.png' },
  dostoevsky: { slug: 'dostoevsky', name: 'Fyodor Dostoevsky', dates: '1821–1881', portrait: 'dostoevsky-fyodor.png' },
  plato: { slug: 'plato', name: 'Plato', dates: 'c. 428–348 BCE', portrait: 'plato.png' },
  tolstoy: { slug: 'tolstoy', name: 'Leo Tolstoy', dates: '1828–1910', portrait: 'tolstoy-leo.png' },
};

const WORK_TITLES: Record<string, string> = {
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
  'a-tale-of-two-cities': 'A Tale of Two Cities',
  'anna-karenina': 'Anna Karenina',
  'barnaby-rudge': 'Barnaby Rudge',
  'bleak-house': 'Bleak House',
  'brothers-karamazov': 'The Brothers Karamazov',
  'crime-and-punishment': 'Crime and Punishment',
  'david-copperfield': 'David Copperfield',
  'demons': 'Demons',
  'emma': 'Emma',
  'gorgias': 'Gorgias',
  'mansfield-park': 'Mansfield Park',
  'martin-chuzzlewit': 'Martin Chuzzlewit',
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
  'the-double': 'The Double',
  'the-idiot': 'The Idiot',
  'timaeus': 'Timaeus',
  'war-and-peace': 'War and Peace',
};

const LANGUAGE_DATA: Record<string, { code: string; name: string }> = {
  eng: { code: 'en', name: 'English' },
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

export function unitHref(work: Pick<Work, 'authorSlug' | 'slug'>, edition: Pick<Edition, 'code'>, unit: Pick<ReadingUnit, 'path'>): string {
  return `${workHref(work)}/${edition.code}/${unit.path}`;
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
  const match = fileName.match(/^([^_]+)_(.+)_([a-z]{3})\.xml$/);
  if (!match) throw new Error(`Unexpected TEI filename: ${fileName}`);
  const [, authorSlug, workSlug, fileLanguage] = match;
  const language = LANGUAGE_DATA[fileLanguage] ?? { code: fileLanguage, name: fileLanguage };
  const source = fs.readFileSync(filePath, 'utf8');
  const document = new DOMParser().parseFromString(source, 'application/xml');
  const parseError = descendants(document, 'parsererror')[0];
  if (parseError) throw new Error(`Invalid XML in ${fileName}: ${cleanText(parseError.textContent)}`);

  const titleStmt = descendants(document, 'titleStmt')[0];
  const sourceTitle = cleanText(descendants(titleStmt, 'title')[0]?.textContent)
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
  const selected = new Set<any>();
  for (const div of allDivs) {
    const kind = kindOf(div);
    const containsPrimaryUnits = descendants(div, 'div').some((child) => kindOf(child) === unitKind);
    if (kind === unitKind || (SUPPLEMENTARY_KINDS.has(kind) && !containsPrimaryUnits)) selected.add(div);
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
    const title = divisionLabel(div, segmentCache);
    const context = divisionAncestors(div, text)
      .filter((ancestor) => !WRAPPER_KINDS.has(kindOf(ancestor)))
      .map((ancestor) => divisionLabel(ancestor, segmentCache));
    units.push({
      path: pathValue,
      segments: finalSegments,
      title,
      context,
      html: renderDivision(div, entities),
    });
  }

  for (let index = 0; index < units.length; index += 1) {
    units[index].previousPath = units[index - 1]?.path;
    units[index].nextPath = units[index + 1]?.path;
  }

  const kind = allDivs.map(kindOf).find((item) => item === 'edition' || item === 'translation') ?? 'edition';
  const routeBase = `/authors/${authorSlug}/${workSlug}/${language.code}`;
  const toc = buildDocumentToc(text, selected, units, segmentCache, routeBase);

  return {
    authorSlug,
    workSlug,
    code: language.code,
    language: fileLanguage,
    languageName: language.name,
    sourceTitle,
    sourceFile: fileName,
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
): TocNode[] {
  const unitByPath = new Map(units.map((unit) => [unit.path, unit]));
  const sections: TocNode[] = [];
  for (const areaName of ['front', 'body', 'back']) {
    const area = directElementChildren(text).find((child) => child.localName === areaName);
    if (!area) continue;
    const children = buildTocChildren(area, text, selected, unitByPath, segmentCache, routeBase);
    if (!children.length) continue;
    if (areaName === 'body') sections.push(...children);
    else sections.push({ label: areaName === 'front' ? 'Front matter' : 'Back matter', kind: areaName, children });
  }
  if (!sections.length) {
    sections.push(...buildTocChildren(text, text, selected, unitByPath, segmentCache, routeBase));
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
    const children = buildTocChildren(div, text, selected, unitByPath, segmentCache, routeBase);
    if (!children.length) continue;
    const kind = kindOf(div);
    if (WRAPPER_KINDS.has(kind) && !directHead(div)) nodes.push(...children);
    else nodes.push({ label: divisionLabel(div, segmentCache), kind, children });
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

function divisionLabel(div: any, segmentCache: Map<any, string>): string {
  const head = directHead(div);
  if (head) return truncate(cleanText(head.textContent), 180);
  const kind = kindOf(div);
  const n = cleanText(div.getAttribute?.('n'));
  if (n && !/^urn:/i.test(n)) return `${displayKind(kind)} ${n}`;
  const segment = divisionSegment(div, segmentCache);
  const ordinal = segment.match(/-(\d+)$/)?.[1]?.replace(/^0+/, '') || '';
  return ordinal ? `${displayKind(kind)} ${ordinal}` : displayKind(kind);
}

function renderDivision(div: any, entities: EntityMaps): string {
  let html = '';
  for (const child of directChildNodes(div)) {
    if (child.nodeType === 1 && child.localName === 'head') continue;
    html += renderNode(child, entities, 2);
  }
  return html;
}

function renderNode(node: any, entities: EntityMaps, headingLevel: number): string {
  if (!node) return '';
  if (node.nodeType === 3 || node.nodeType === 4) return escapeHtml(node.nodeValue ?? '');
  if (node.nodeType !== 1) return '';

  const name = node.localName;
  const children = () => directChildNodes(node).map((child) => renderNode(child, entities, headingLevel)).join('');
  const text = () => cleanText(node.textContent);
  const lang = node.getAttribute?.('xml:lang') || node.getAttributeNS?.(XML_NS, 'lang');
  const langAttr = lang ? ` lang="${escapeAttr(lang)}"` : '';

  switch (name) {
    case 'div': {
      const kind = kindOf(node);
      const content = directChildNodes(node).map((child) => renderNode(child, entities, headingLevel + 1)).join('');
      return `<section class="tei-division tei-${escapeAttr(slugify(kind))}">${content}</section>`;
    }
    case 'head':
      return `<h${Math.min(6, headingLevel)}>${children()}</h${Math.min(6, headingLevel)}>`;
    case 'p': {
      const firstClass = isFirstParagraph(node) ? ' tei-first-paragraph' : '';
      return `<p class="tei-paragraph${firstClass}">${children()}</p>`;
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
      return block ? `<blockquote>${children()}</blockquote>` : `<q>${children()}</q>`;
    }
    case 'persName':
    case 'placeName':
    case 'rs':
    case 'name': {
      const reference = node.getAttribute?.('ref') || node.getAttribute?.('key');
      const map = name === 'placeName' ? entities.places : entities.persons;
      const detail = referencedEntities(reference, map, true);
      return `<span class="tei-entity"${detail ? ` title="${escapeAttr(detail)}"` : ''}>${children()}</span>`;
    }
    case 'note': {
      const id = xmlId(node);
      if (id && entities.referencedNoteIds.has(id)) return '';
      return renderInlineNote(node, entities, headingLevel);
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
      if (rend.includes('bold')) return `<strong>${children()}</strong>`;
      if (rend.includes('sup')) return `<sup>${children()}</sup>`;
      if (rend.includes('sub')) return `<sub>${children()}</sub>`;
      if (rend.includes('small')) return `<span class="tei-smallcaps">${children()}</span>`;
      return `<em>${children()}</em>`;
    }
    case 'lg':
      return `<div class="tei-line-group">${children()}</div>`;
    case 'l':
      return `<span class="tei-line">${children()}</span>`;
    case 'label':
      return `<span class="tei-label">${children()}</span>`;
    case 'ref': {
      const target = cleanText(node.getAttribute?.('target'));
      const note = target.startsWith('#') ? entities.notes.get(target.slice(1)) : undefined;
      if (note) return renderInlineNote(note, entities, headingLevel);
      return /^(https?:\/\/|#)/.test(target)
        ? `<a href="${escapeAttr(target)}">${children()}</a>`
        : children();
    }
    case 'choice': {
      const preferred = ['corr', 'reg', 'expan', 'orig', 'sic', 'abbr']
        .map((tag) => directElementChildren(node).find((child) => child.localName === tag))
        .find(Boolean);
      return preferred ? renderNode(preferred, entities, headingLevel) : children();
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
      return `<figure>${children()}</figure>`;
    case 'graphic':
      return '';
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

function renderInlineNote(note: any, entities: EntityMaps, headingLevel: number): string {
  const content = directChildNodes(note).map((child) => {
    if (child.nodeType === 1 && child.localName === 'p') {
      return directChildNodes(child).map((part) => renderNode(part, entities, headingLevel)).join('');
    }
    return renderNode(child, entities, headingLevel);
  }).join('');
  const alreadyBracketed = /^\s*\[.*\]\s*$/s.test(cleanText(note.textContent));
  return content.trim()
    ? `<span class="tei-note${alreadyBracketed ? ' tei-note-bracketed' : ''}" role="note" title="Note">${content}</span>`
    : '';
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

function displayKind(kind: string): string {
  const labels: Record<string, string> = {
    bekker_page: 'Bekker page',
    suppressed_chapter: 'Suppressed chapter',
    'suppressed-chapter': 'Suppressed chapter',
  };
  return labels[kind] ?? kind.replaceAll('_', ' ').replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}

function titleFromSlug(slug: string): string {
  const small = new Set(['a', 'an', 'and', 'of', 'the', 'from']);
  return slug.split('-').map((word, index) => {
    if (index > 0 && small.has(word)) return word;
    return word.charAt(0).toUpperCase() + word.slice(1);
  }).join(' ');
}

function languageOrder(code: string): number {
  return ['en', 'grc', 'ru'].indexOf(code) === -1 ? 99 : ['en', 'grc', 'ru'].indexOf(code);
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
