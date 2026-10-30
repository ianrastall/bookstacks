import {expect,it} from 'vitest';
import {DOMParser} from '@xmldom/xmldom';
import {prepareDrama,stageClone,stageKind,type DramaLayout} from './drama';
import {dramaLayout} from './drama';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import cases from '../../tests/fixtures/drama-layout.json';
const layout=(locale:string)=>({locale,names:/\b(?:Thésée|Theseus|Hippolyta|Hippolyte|Hélène|Orlando|Adam|Philostrate|Puck)\b/giu}) as DramaLayout;
it('uses the same movement classifications as the PDF renderer',()=>{
 for(const example of cases)expect(stageKind(example.text,example.declared,layout(example.language)),example.text).toBe(example.expected);
});
it('preserves every character and its order while preparing the entire Shakespeare corpus',()=>{
 const files=fs.readdirSync('tei/shakespeare').filter(file=>file.endsWith('.xml'));
 expect(files.length).toBeGreaterThanOrEqual(85);
 for(const file of files){
  const source=fs.readFileSync(`tei/shakespeare/${file}`,'utf8');
  const doc=new DOMParser().parseFromString(source,'application/xml');
  const before=doc.documentElement!.textContent!.replace(/\s+/g,'');
  const locales:Record<string,string>={eng:'en',fra:'fr',spa:'es'};
  const locale=locales[file.slice(-7,-4)]!;
  prepareDrama(doc,dramaLayout(file,createHash('sha256').update(source).digest('hex'),locale));
  expect(doc.documentElement!.textContent!.replace(/\s+/g,''),file).toBe(before);
 }
});
it('keeps business directions in their speech without changing note links or word order',()=>{
 const doc=new DOMParser().parseFromString('<TEI xmlns="http://www.tei-c.org/ns/1.0"><sp><speaker>Theseus</speaker><stage type="business">, to Hippolyta.</stage><p>Our wedding hour.</p><stage type="exit">Exit Theseus.</stage></sp></TEI>','application/xml');
 prepareDrama(doc,layout('en'));
 const p=doc.getElementsByTagName('p')[0];
 expect(p.textContent).toBe(', to Hippolyta. Our wedding hour.');
 expect(doc.getElementsByTagName('sp')[0].lastChild?.localName).toBe('stage');
 const source=new DOMParser().parseFromString('<stage xmlns="http://www.tei-c.org/ns/1.0">(<hi>Exit Theseus.</hi>)<ref target="#n1">1</ref></stage>','application/xml').documentElement;
 const clone=stageClone(source);
 expect(clone.textContent).toBe('Exit Theseus.1');
 expect(clone.getElementsByTagName('ref')[0].getAttribute('target')).toBe('#n1');
 expect(source?.textContent).toBe('(Exit Theseus.)1');
});
it('splits an imported exit and entrance joined by blank lines into separate aligned cues',()=>{
 const doc=new DOMParser().parseFromString('<TEI xmlns="http://www.tei-c.org/ns/1.0"><div><stage type="entrance">(Ils se retirent.)<lb/><lb/>(Entre Thésée.)</stage></div></TEI>','application/xml');
 prepareDrama(doc,layout('fr'));
 const stages=doc.getElementsByTagName('stage');expect(stages.length).toBe(2);
 expect(stages[0].getAttribute('data-bookstacks-stage-kind')).toBe('exit');
 expect(stages[1].getAttribute('data-bookstacks-stage-kind')).toBe('entrance');
});
it('keeps a singular action with its preceding speaker and leaves unattributed scene actions in place',()=>{
 const doc=new DOMParser().parseFromString('<TEI xmlns="http://www.tei-c.org/ns/1.0"><div><sp><speaker>Thésée</speaker><p>Parlons.</p></sp><stage type="business">(Il se lève.)</stage><stage type="business">(On entend des cors.)</stage></div></TEI>','application/xml');
 prepareDrama(doc,layout('fr'));
 expect(doc.getElementsByTagName('p')[0].textContent).toBe('Parlons. (Il se lève.)');
 expect(doc.getElementsByTagName('div')[0].lastChild?.localName).toBe('stage');
});
