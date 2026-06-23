import fs from 'node:fs';
import path from 'node:path';
import { DOMParser } from '@xmldom/xmldom';

export function parseTeiBook(filePath: string) {
  const xml = fs.readFileSync(path.resolve(filePath), 'utf-8');
  const doc = new DOMParser().parseFromString(xml, 'text/xml');

  // Metadata
  const titleNode = doc.getElementsByTagName('title')[0];
  const authorNode = doc.getElementsByTagName('author')[0]?.getElementsByTagName('persName')[0];
  const title = titleNode?.textContent || 'Unknown Title';
  const author = authorNode?.textContent || 'Unknown Author';

  // Registries
  const persons: Record<string, any> = {};
  const listPerson = doc.getElementsByTagName('listPerson')[0];
  if (listPerson) {
    const personNodes = listPerson.getElementsByTagName('person');
    for (let i = 0; i < personNodes.length; i++) {
      const p = personNodes[i];
      const id = p.getAttribute('xml:id');
      const name = p.getElementsByTagName('persName')[0]?.textContent;
      const note = p.getElementsByTagName('note')[0]?.textContent;
      if (id) persons[id] = { name, note };
    }
  }

  const places: Record<string, any> = {};
  const listPlace = doc.getElementsByTagName('listPlace')[0];
  if (listPlace) {
    const placeNodes = listPlace.getElementsByTagName('place');
    for (let i = 0; i < placeNodes.length; i++) {
      const p = placeNodes[i];
      const id = p.getAttribute('xml:id');
      const name = p.getElementsByTagName('placeName')[0]?.textContent;
      const note = p.getElementsByTagName('note')[0]?.textContent;
      if (id) places[id] = { name, note };
    }
  }

  // Chapters
  const chapters = [];
  const divNodes = doc.getElementsByTagName('div');
  for (let i = 0; i < divNodes.length; i++) {
    const div = divNodes[i];
    if (div.getAttribute('type') === 'chapter') {
      const n = div.getAttribute('n');
      const head = div.getElementsByTagName('head')[0]?.textContent || `Chapter ${n}`;
      
      // Convert TEI body to HTML
      let html = '';
      const childNodes = div.childNodes;
      for (let j = 0; j < childNodes.length; j++) {
        const node = childNodes[j];
        if (node.nodeName !== 'head') {
          html += convertNodeToHtml(node, persons, places);
        }
      }

      chapters.push({
        n,
        title: head,
        html: html.trim()
      });
    }
  }

  return { title, author, persons, places, chapters };
}

export function slugify(text: string): string {
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')           // Replace spaces with -
    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
    .replace(/\-\-+/g, '-')         // Replace multiple - with single -
    .replace(/^-+/, '')             // Trim - from start of text
    .replace(/-+$/, '');            // Trim - from end of text
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
  if (node.nodeType === 3) { // Text node
    return escapeHtml(node.nodeValue || '');
  }
  if (node.nodeType === 1) { // Element node
    const tag = node.nodeName;
    let innerHtml = '';
    for (let i = 0; i < node.childNodes.length; i++) {
      innerHtml += convertNodeToHtml(node.childNodes[i], persons, places);
    }

    if (tag === 'p') return `<p>${innerHtml}</p>`;
    if (tag === 'said') {
      const who = node.getAttribute('who') || '';
      return `<span class="tei-said" data-who="${who}">&ldquo;${innerHtml}&rdquo;</span>`;
    }
    if (tag === 'emph') return `<em>${innerHtml}</em>`;
    if (tag === 'title') return `<cite>${innerHtml}</cite>`;
    if (tag === 'foreign') return `<i class="tei-foreign" lang="${node.getAttribute('xml:lang') || ''}">${innerHtml}</i>`;
    if (tag === 'rs' || tag === 'persName' || tag === 'placeName') {
      const ref = node.getAttribute('ref') || '';
      const id = ref.replace('#', '');
      let title = '';
      if (persons[id]) title = `${persons[id].name}${persons[id].note ? ': ' + persons[id].note : ''}`;
      else if (places[id]) title = `${places[id].name}${places[id].note ? ': ' + places[id].note : ''}`;
      
      const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
      return `<span class="tei-rs" data-ref="${ref}"${titleAttr}>${innerHtml}</span>`;
    }
    if (tag === 'pb') {
      const n = node.getAttribute('n');
      return `<span class="tei-pb" data-n="${n}"></span>`;
    }
    if (tag === 'q') {
      return `<q>${innerHtml}</q>`;
    }
    if (tag === 'quote') {
      return `<blockquote>${innerHtml}</blockquote>`;
    }
    if (tag === 'hi') {
      return `<span>${innerHtml}</span>`;
    }
    if (tag === 'lg') { // line group (poetry)
      return `<div class="tei-lg">${innerHtml}</div>`;
    }
    if (tag === 'l') { // line
      return `<div class="tei-l">${innerHtml}</div>`;
    }
    if (tag === 'floatingText') {
      return `<div class="tei-floating-text">${innerHtml}</div>`;
    }
    if (tag === 'body') {
      return innerHtml;
    }
    
    // Fallback for unknown elements: just return the inner html
    return innerHtml;
  }
  return '';
}

function escapeHtml(unsafe: string) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;");
}
