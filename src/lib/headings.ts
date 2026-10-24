import type { EditionLanguage } from './i18n';

// The English minor-word list follows the existing PDF exporter's heading style.
const MINOR_WORDS = new Set('a an and as at but by en for from if in into nor of off on or over per the to up upon v via vs with yet'.split(' '));
const INITIALISMS = new Set('AI DNA EU HTML PDF TEI UK UN US USA USSR XML'.split(' '));
const STRUCTURAL_WORDS = new Set('act book chapter part scene section stave volume acte chapitre livre partie scène tome acto capítulo escena estrofa libro parte sección tomo глава действие книга раздел том часть βιβλίον κεφάλαιον μέρος πρᾶξις σκηνή τμῆμα τόμος'.split(' '));
const ROMAN = /^(?=[MDCLXVI]+$)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$/;
const WORDS = /[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu;

interface Edit { start: number; end: number; value: string }

function headingEdits(value: string, language: EditionLanguage): Edit[] {
  const words = [...value.matchAll(WORDS)];
  return words.map((match, index) => {
    const original = match[0];
    const start = match.index!;
    const separator = value.slice(index ? words[index - 1].index! + words[index - 1][0].length : 0, start);
    const lower = original.toLocaleLowerCase(language);
    let replacement: string;
    const upper = original.toLocaleUpperCase(language);
    const structuralNumeral = index > 0 && STRUCTURAL_WORDS.has(words[index - 1][0].toLocaleLowerCase(language)) && ROMAN.test(upper);
    if (/\p{N}/u.test(value[start - 1] ?? '') || /\p{N}/u.test(value[start + original.length] ?? '')) replacement = original;
    else if (structuralNumeral) replacement = upper;
    else if (INITIALISMS.has(original) || ROMAN.test(original)) replacement = original;
    else if (language === 'en' && MINOR_WORDS.has(lower) && index > 0 && index < words.length - 1 && !/[.!?:—–]/u.test(separator)) replacement = lower;
    else {
      // Keep meaningful internal capitals in already mixed-case proper names.
      const base = original === original.toLocaleUpperCase(language) ? lower : original;
      replacement = base.replace(/^\p{L}/u, letter => letter.toLocaleUpperCase(language));
      if (/^[dlo]['’]/iu.test(replacement)) replacement = replacement.replace(/(?<=['’])\p{L}/u, letter => letter.toLocaleUpperCase(language));
    }
    return { start, end: start + original.length, value: replacement };
  });
}

export function headingTitleCase(value: string, language: EditionLanguage): string {
  const edits = headingEdits(value, language);
  let result = '', offset = 0;
  for (const edit of edits) {
    result += value.slice(offset, edit.start) + edit.value;
    offset = edit.end;
  }
  return result + value.slice(offset);
}

/** Format only heading text in the parsed display DOM, retaining all markup.
 * Source XML on disk, division IDs, notes and routing attributes are untouched.
 */
export function normalizeHeadingNode(heading: any, language: EditionLanguage): void {
  for (let ancestor = heading.parentNode; ancestor; ancestor = ancestor.parentNode) {
    if (ancestor.localName === 'note') return;
  }
  const leaves: Array<{ node: any; start: number; end: number }> = [];
  let source = '';
  function collect(node: any) {
    if (node.nodeType === 1 && node.localName === 'note') return;
    if (node.nodeType === 3 || node.nodeType === 4) {
      const start = source.length;
      source += node.nodeValue ?? '';
      leaves.push({ node, start, end: source.length });
    } else for (let child = node.firstChild; child; child = child.nextSibling) collect(child);
  }
  collect(heading);
  const edits = headingEdits(source, language);
  for (const leaf of leaves) {
    let result = '', offset = leaf.start;
    for (const edit of edits) {
      if (edit.end <= leaf.start || edit.start >= leaf.end) continue;
      const start = Math.max(edit.start, leaf.start), end = Math.min(edit.end, leaf.end);
      result += source.slice(offset, start);
      result += edit.value.slice(start - edit.start, end === edit.end ? undefined : end - edit.start);
      offset = end;
    }
    leaf.node.nodeValue = result + source.slice(offset, leaf.end);
  }
}
