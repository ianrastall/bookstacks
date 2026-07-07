import fs from 'node:fs';
import path from 'node:path';
import { DOMParser } from '@xmldom/xmldom';

const REPO_ROOT = process.cwd();
const DEFAULT_SOURCE_ROOT = path.join(
  process.env.LOCALAPPDATA || process.env.TMP || '',
  'Temp',
  'bookstacks-canonical-greekLit'
);

const sourceRoot = path.resolve(readArg('--source') || process.env.PERSEUS_GREEK_ROOT || DEFAULT_SOURCE_ROOT);
const outDir = path.join(REPO_ROOT, 'tei-source');

const ARISTOTLE_WORKS = [
  {
    author: 'Aristotle',
    authorSlug: 'aristotle',
    authorDates: '385 BCE-323 BCE',
    authorTlg: 'tlg0086',
    workTlg: 'tlg034',
    title: 'Aristotle on the Art of Poetry',
    slug: 'aristotle-on-the-art-of-poetry'
  },
  {
    author: 'Aristotle',
    authorSlug: 'aristotle',
    authorDates: '385 BCE-323 BCE',
    authorTlg: 'tlg0086',
    workTlg: 'tlg035',
    title: 'Politics: A Treatise on Government',
    slug: 'politics-a-treatise-on-government'
  },
  {
    author: 'Aristotle',
    authorSlug: 'aristotle',
    authorDates: '385 BCE-323 BCE',
    authorTlg: 'tlg0086',
    workTlg: 'tlg010',
    title: 'The Nicomachean Ethics of Aristotle',
    slug: 'the-nicomachean-ethics-of-aristotle'
  }
];

function main() {
  if (!fs.existsSync(sourceRoot)) {
    throw new Error(`Missing canonical Greek source checkout: ${sourceRoot}`);
  }

  fs.mkdirSync(outDir, { recursive: true });

  const works = [
    ...ARISTOTLE_WORKS,
    ...discoverPlatoWorks()
  ];

  const written = [];
  for (const work of works) {
    const sourcePath = findGreekSource(work.authorTlg, work.workTlg);
    const sourceDoc = parseXmlFile(sourcePath);
    const sourceMeta = readCtsMetadata(path.dirname(sourcePath), ctsUrnFromSource(sourcePath));
    const title = work.title || sourceMeta.englishTitle;
    const greekTitle = sourceMeta.greekLabel || firstGreekTitle(sourceDoc) || title;
    const body = buildBody(sourceDoc);
    const tei = buildSiteTei({
      ...work,
      title,
      slug: work.slug || slugify(title),
      greekTitle,
      sourcePath,
      sourceMeta,
      body
    });
    const outPath = path.join(outDir, `${work.authorSlug}_${work.slug || slugify(title)}_grc.xml`);
    fs.writeFileSync(outPath, tei, 'utf8');
    written.push({ outPath, chapters: body.chapters, title });
  }

  for (const item of written) {
    console.log(`${path.relative(REPO_ROOT, item.outPath)} (${item.chapters} chapters)`);
  }
}

function discoverPlatoWorks() {
  const platoRoot = path.join(sourceRoot, 'data', 'tlg0059');
  const dirs = fs.readdirSync(platoRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^tlg\d+$/i.test(entry.name))
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b));

  return dirs.map((workTlg) => {
    const workDir = path.join(platoRoot, workTlg);
    const sourcePath = findGreekSource('tlg0059', workTlg);
    const metadata = readCtsMetadata(workDir, ctsUrnFromSource(sourcePath));
    const title = metadata.englishTitle || workTlg;
    return {
      author: 'Plato',
      authorSlug: 'plato',
      authorDates: '427 BCE-347 BCE',
      authorTlg: 'tlg0059',
      workTlg,
      title,
      slug: slugify(title)
    };
  });
}

function findGreekSource(authorTlg, workTlg) {
  const workDir = path.join(sourceRoot, 'data', authorTlg, workTlg);
  if (!fs.existsSync(workDir)) {
    throw new Error(`Missing source work directory: ${workDir}`);
  }

  const files = fs.readdirSync(workDir)
    .filter((file) => /\.perseus-grc\d*\.xml$/i.test(file))
    .sort((a, b) => {
      const aScore = a.includes('grc2') ? 0 : 1;
      const bScore = b.includes('grc2') ? 0 : 1;
      return aScore - bScore || a.localeCompare(b);
    });

  if (files.length === 0) {
    throw new Error(`No Perseus Greek XML found in ${workDir}`);
  }

  return path.join(workDir, files[0]);
}

function parseXmlFile(filePath) {
  const xml = fs.readFileSync(filePath, 'utf8');
  return new DOMParser({
    onError(level, message) {
      if (level === 'fatalError') throw new Error(`${filePath}: ${message}`);
    }
  }).parseFromString(xml, 'text/xml');
}

function readCtsMetadata(workDir, editionUrn) {
  const ctsPath = path.join(workDir, '__cts__.xml');
  if (!fs.existsSync(ctsPath)) return {};

  const doc = parseXmlFile(ctsPath);
  const titles = elementsByLocalName(doc, 'title');
  const englishTitle = textOf(titles.find((node) => /^eng?$/i.test(xmlLang(node))) || titles[0]);
  const editions = elementsByLocalName(doc, 'edition');
  const edition = editions.find((node) => getAttr(node, 'urn') === editionUrn)
    || editions.find((node) => /^grc$/i.test(xmlLang(node)))
    || editions[0];

  const labels = edition ? childElements(edition, 'label') : [];
  const descriptions = edition ? childElements(edition, 'description') : [];
  const greekLabel = textOf(labels.find((node) => /^grc$/i.test(xmlLang(node))) || labels[0]);
  const description = textOf(descriptions[0]);

  return { englishTitle, greekLabel, description, editionUrn };
}

function ctsUrnFromSource(sourcePath) {
  const id = path.basename(sourcePath, '.xml');
  return `urn:cts:greekLit:${id}`;
}

function firstGreekTitle(doc) {
  const titles = elementsByLocalName(doc, 'title');
  return textOf(titles.find((node) => /^grc$/i.test(xmlLang(node))) || titles[0]);
}

function buildBody(sourceDoc) {
  const body = firstElement(sourceDoc, 'body');
  if (!body) throw new Error('Source TEI has no body.');

  const container = childElements(body, 'div').find((node) => getAttr(node, 'type') === 'edition') || body;
  const topParts = textpartChildren(container);
  if (topParts.length === 0) throw new Error('Source TEI has no textpart divisions.');

  let chapterSeq = 0;
  const chunks = [];
  const firstSubtype = getAttr(topParts[0], 'subtype');
  const topPartsAreChapters = firstSubtype === 'chapter';
  const hasNestedParts = topParts.some((part) => textpartChildren(part).length > 0);

  if (!hasNestedParts || topPartsAreChapters) {
    for (const part of topParts) {
      chapterSeq += 1;
      chunks.push(chapterXml(part, chapterSeq, partLabel(part, chapterSeq)));
    }
  } else {
    for (const [groupIndex, group] of topParts.entries()) {
      const groupN = getAttr(group, 'n') || String(groupIndex + 1);
      const groupLabel = partLabel(group, groupIndex + 1);
      const childChunks = [];
      for (const part of leafTextparts(group)) {
        chapterSeq += 1;
        childChunks.push(chapterXml(part, chapterSeq, partLabel(part, chapterSeq)));
      }
      chunks.push(
        `<div type="volume" n="${escapeAttr(groupN)}">\n` +
        `<head>${escapeXml(groupLabel)}</head>\n` +
        childChunks.join('\n') +
        `\n</div>`
      );
    }
  }

  return {
    xml: chunks.join('\n'),
    chapters: chapterSeq
  };
}

function chapterXml(part, n, heading) {
  const content = renderTextpartContent(part).trim();
  return `<div type="chapter" n="${n}">\n<head>${escapeXml(heading)}</head>\n${content}\n</div>`;
}

function partLabel(part, fallbackNumber) {
  const subtype = getAttr(part, 'subtype') || 'section';
  const n = getAttr(part, 'n') || String(fallbackNumber);
  if (subtype === 'book') return `Book ${toRomanIfNumber(n)}`;
  if (subtype === 'letter') return `Letter ${toRomanIfNumber(n)}`;
  if (subtype === 'chapter') return `Chapter ${n}`;
  if (subtype === 'bekker_page') return `Bekker Page ${n}`;
  if (subtype === 'subchapter') return `Section ${n}`;
  return `${titleCase(subtype)} ${n}`;
}

function renderTextpartContent(part) {
  let xml = '';
  for (let i = 0; i < part.childNodes.length; i += 1) {
    const child = part.childNodes[i];
    if (isTextpart(child)) {
      xml += renderTextpartContent(child);
    } else {
      xml += renderNode(child);
    }
  }
  return xml;
}

function renderNode(node) {
  if (node.nodeType === 3) {
    const value = node.nodeValue || '';
    if (!value.trim()) return '';
    return escapeXml(value.replace(/\s+/g, ' '));
  }

  if (node.nodeType !== 1) return '';

  const tag = localName(node);
  if (isTextpart(node)) return renderTextpartContent(node);
  if (tag === 'head') return '';
  if (tag === 'lb') return ' ';
  if (tag === 'milestone') return renderMilestone(node);
  if (tag === 'pb') {
    const n = getAttr(node, 'n');
    return n ? `<pb n="${escapeAttr(n)}"/>` : '';
  }
  if (tag === 'gap') return '<note>gap in source</note>';
  if (tag === 'choice') return renderChoice(node);
  if (tag === 'sp') return renderSpeech(node);
  if (tag === 'speaker') return tagWrap('emph', renderChildren(node).trim());
  if (tag === 'stage') {
    const inner = renderChildren(node).trim();
    return inner ? `<p><emph>${inner}</emph></p>\n` : '';
  }

  const inner = renderChildren(node);
  if (!inner.trim() && !['p', 'l', 'lg'].includes(tag)) return '';

  if (tag === 'p') return `<p>${inner.trim()}</p>\n`;
  if (tag === 'l') return `<l>${inner.trim()}</l>\n`;
  if (tag === 'lg') return `<lg>\n${inner.trim()}\n</lg>\n`;
  if (tag === 'q' || tag === 'quote') return `<q>${inner.trim()}</q>`;
  if (tag === 'note') return `<note>${inner.trim()}</note>`;
  if (tag === 'foreign') {
    const lang = getAttr(node, 'xml:lang') || getAttr(node, 'lang');
    return lang
      ? `<foreign xml:lang="${escapeAttr(lang)}">${inner.trim()}</foreign>`
      : `<foreign>${inner.trim()}</foreign>`;
  }
  if (tag === 'title') return `<title>${inner.trim()}</title>`;
  if (tag === 'hi') {
    const rend = getAttr(node, 'rend');
    return rend ? `<hi rend="${escapeAttr(rend)}">${inner.trim()}</hi>` : inner;
  }
  if (tag === 'emph') return `<emph>${inner.trim()}</emph>`;
  if (tag === 'name' || tag === 'persName' || tag === 'placeName') return `<name>${inner.trim()}</name>`;
  if (tag === 'said') return inner;
  if (tag === 'add' || tag === 'del' || tag === 'unclear' || tag === 'sic' || tag === 'corr' || tag === 'orig' || tag === 'reg') {
    return inner;
  }

  return inner;
}

function renderChildren(node) {
  let inner = '';
  for (let i = 0; i < node.childNodes.length; i += 1) {
    inner += renderNode(node.childNodes[i]);
  }
  return inner;
}

function renderMilestone(node) {
  const unit = getAttr(node, 'unit');
  const n = getAttr(node, 'n');
  if (!n) return '';
  if (unit === 'page') return `<pb n="${escapeAttr(n)}"/>`;
  return '';
}

function renderChoice(node) {
  const preferred = childElements(node, 'corr')[0]
    || childElements(node, 'reg')[0]
    || childElements(node, 'expan')[0]
    || firstChildElement(node);
  return preferred ? renderChildren(preferred) : '';
}

function renderSpeech(node) {
  const speaker = childElements(node, 'speaker')[0];
  const speakerText = textOf(speaker);
  let body = '';

  for (let i = 0; i < node.childNodes.length; i += 1) {
    const child = node.childNodes[i];
    if (child === speaker) continue;
    body += renderNode(child);
  }

  if (!speakerText) return body;
  return `<p><emph>${escapeXml(speakerText)}</emph></p>\n${body}`;
}

function buildSiteTei({ author, authorDates, title, greekTitle, sourcePath, sourceMeta, body }) {
  const sourceRelative = path.relative(sourceRoot, sourcePath).replace(/\\/g, '/');
  const description = sourceMeta.description || 'Perseus Digital Library Greek edition';
  const urn = sourceMeta.editionUrn || ctsUrnFromSource(sourcePath);

  return `<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="grc">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>${escapeXml(title)}</title>
        <author>
          <persName>${escapeXml(author)}<note type="dates">${escapeXml(authorDates)}</note></persName>
        </author>
      </titleStmt>
      <publicationStmt>
        <publisher>Bookstacks</publisher>
        <availability status="free">
          <p>Source text available under a Creative Commons Attribution-ShareAlike 4.0 International License.</p>
        </availability>
      </publicationStmt>
      <sourceDesc>
        <p>Ancient Greek text for ${escapeXml(greekTitle)} derived from the PerseusDL canonical-greekLit repository (${escapeXml(sourceRelative)}), ${escapeXml(urn)}. ${escapeXml(description)}</p>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage>
        <language ident="grc">Ancient Greek</language>
      </langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
${indent(body.xml, 6)}
    </body>
  </text>
</TEI>
`;
}

function textpartChildren(node) {
  return childElements(node, 'div').filter(isTextpart);
}

function leafTextparts(node) {
  const children = textpartChildren(node);
  if (children.length === 0) return [node];
  return children.flatMap((child) => leafTextparts(child));
}

function childElements(node, name) {
  const nodes = [];
  if (!node?.childNodes) return nodes;
  for (let i = 0; i < node.childNodes.length; i += 1) {
    const child = node.childNodes[i];
    if (child.nodeType === 1 && (!name || localName(child) === name)) nodes.push(child);
  }
  return nodes;
}

function firstChildElement(node) {
  return childElements(node)[0];
}

function firstElement(doc, name) {
  return elementsByLocalName(doc, name)[0];
}

function elementsByLocalName(node, name) {
  const result = [];
  const walk = (current) => {
    if (!current) return;
    if (current.nodeType === 1 && localName(current) === name) result.push(current);
    if (!current.childNodes) return;
    for (let i = 0; i < current.childNodes.length; i += 1) walk(current.childNodes[i]);
  };
  walk(node);
  return result;
}

function isTextpart(node) {
  return node?.nodeType === 1
    && localName(node) === 'div'
    && getAttr(node, 'type') === 'textpart';
}

function localName(node) {
  return (node.localName || node.nodeName || '').replace(/^.*:/, '');
}

function getAttr(node, name) {
  return node?.getAttribute?.(name) || '';
}

function xmlLang(node) {
  return getAttr(node, 'xml:lang') || getAttr(node, 'lang');
}

function textOf(node) {
  return (node?.textContent || '').replace(/\s+/g, ' ').trim();
}

function tagWrap(tag, inner) {
  return inner ? `<${tag}>${inner}</${tag}>` : '';
}

function indent(xml, spaces) {
  const prefix = ' '.repeat(spaces);
  return xml.split('\n').map((line) => line ? `${prefix}${line}` : line).join('\n');
}

function slugify(value) {
  return value
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function titleCase(value) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function toRomanIfNumber(value) {
  const n = Number.parseInt(value, 10);
  if (!Number.isFinite(n) || String(n) !== String(value)) return value;
  const numerals = [
    [1000, 'M'],
    [900, 'CM'],
    [500, 'D'],
    [400, 'CD'],
    [100, 'C'],
    [90, 'XC'],
    [50, 'L'],
    [40, 'XL'],
    [10, 'X'],
    [9, 'IX'],
    [5, 'V'],
    [4, 'IV'],
    [1, 'I']
  ];
  let remaining = n;
  let roman = '';
  for (const [amount, numeral] of numerals) {
    while (remaining >= amount) {
      roman += numeral;
      remaining -= amount;
    }
  }
  return roman || value;
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeAttr(value) {
  return escapeXml(value).replace(/"/g, '&quot;');
}

function readArg(name) {
  const index = process.argv.indexOf(name);
  if (index < 0 || index + 1 >= process.argv.length) return '';
  return process.argv[index + 1];
}

main();
