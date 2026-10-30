import rules from '../data/drama-layout-rules.json';
import index from '../data/drama-layout-index.json';

export interface DramaLayout { names: RegExp; locale: 'en'|'fr'|'es' }
const escapePattern=(value:string)=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
export function dramaLayout(file:string,sha256:string,locale:string):DramaLayout {
 const record=(index as Record<string,{source_sha256:string;names:string[]}>)[file];
 if(!record||record.source_sha256!==sha256)throw new Error(`Refresh the explicit drama layout index for ${file}`);
 const alternatives=record.names.map(name=>name.split(/\s+/).map(escapePattern).join('\\s+')).join('|');
 return {locale:locale as DramaLayout['locale'],names:new RegExp(`(?<![${rules.wordCharacters}])(?:${alternatives})(?![${rules.wordCharacters}])`,'giu')};
}
export function stageKind(value:string,declared:string,layout:DramaLayout):string {
 if(['entrance','exit','setting'].includes(declared))return declared;
 const normalized=value.trim().replace(/^[[(]\s*/u,'').replace(layout.names,'@').replace(/\s+/g,' ');
 for(const kind of ['exit','entrance'] as const)if(new RegExp(rules[kind][layout.locale],'iu').test(normalized))return kind;
 return 'business';
}
const elements=(node:any)=>Array.from(node.childNodes??[]).filter((n:any)=>n.nodeType===1) as any[];
function cueText(node:any):string{
 if(node.nodeType===3)return node.nodeValue??'';
 if(['note','ref'].includes(node.localName))return '';
 return Array.from(node.childNodes??[]).map(cueText).join('');
}
function stageParts(stage:any):any[]{
 const parts:any[]=[];let current=stage.cloneNode(false),breakSeen=false;
 for(const child of Array.from(stage.childNodes) as any[]){
  const isBreak=child.nodeType===1&&child.localName==='lb';
  if(isBreak&&breakSeen){
   while(current.lastChild){const last=current.lastChild;current.removeChild(last);if(last.nodeType===1&&last.localName==='lb')break;}
   if(current.textContent?.trim())parts.push(current);
   current=stage.cloneNode(false);breakSeen=false;continue;
  }
  current.appendChild(child.cloneNode(true));
  if(isBreak)breakSeen=true;else if(child.nodeType!==3||child.nodeValue?.trim())breakSeen=false;
 }
 if(current.textContent?.trim())parts.push(current);
 return parts.length>1?parts:[stage];
}
function target(node:any,last=false):any {
 if(node.localName==='p')return node;
 if(node.localName==='lg'){
  const lines=Array.from(node.getElementsByTagNameNS('*','l')) as any[];
  return last?lines.at(-1):lines[0];
 }
}
/** Move only directions already attributed to a speech into its prose/verse. */
export function prepareDrama(document:any,layout:DramaLayout):void {
 const stages=Array.from(document.getElementsByTagNameNS('*','stage')) as any[];
 for(const stage of stages){
  const parts=stageParts(stage),declared=stage.getAttribute('type')??'';
  for(const part of parts){
   let kind=stageKind(cueText(part),parts.length>1?'business':declared,layout);
   if(parts.length>1&&kind==='business'&&['entrance','exit','setting'].includes(declared))kind=declared;
   part.setAttribute('data-bookstacks-stage-kind',kind);
   if(parts.length>1)stage.parentNode.insertBefore(part,stage);
  }
  if(parts.length>1)stage.parentNode.removeChild(stage);
 }
 // A singular action immediately following its speech stays in that part.
 // Leave ensemble/unattributed scene actions in their original position.
 for(const division of Array.from(document.getElementsByTagNameNS('*','div')) as any[]){
  let previous:any;
  for(const child of elements(division)){
   if(child.localName==='stage'&&child.getAttribute('data-bookstacks-stage-kind')==='business'&&previous?.localName==='sp'){
    const value=cueText(child).trim().replace(/^[[(]\s*/u,'');
    const label=elements(previous).find(n=>n.localName==='speaker')?.textContent?.split(',')[0]?.replace(/[.\s]+$/u,'')??'';
    const named=label&&value.toLocaleLowerCase(layout.locale).startsWith(label.toLocaleLowerCase(layout.locale));
    if(named||/^(?:il|elle|he|she|él|ella)\b/iu.test(value)){previous.appendChild(child);continue;}
   }
   previous=child;
  }
 }
 for(const speech of Array.from(document.getElementsByTagNameNS('*','sp')) as any[]){
  let pending:any[]=[];let previous:any;
  const append=()=>{if(previous)for(const stage of pending){previous.appendChild(document.createTextNode(' '));previous.appendChild(stage);}pending=[];};
  for(const child of elements(speech)){
   if(child.localName==='stage'&&child.getAttribute('data-bookstacks-stage-kind')==='business'){pending.push(child);continue;}
   const first=target(child);
   if(first){const reference=first.firstChild;for(const stage of pending){first.insertBefore(stage,reference);first.insertBefore(document.createTextNode(' '),reference);}pending=[];previous=target(child,true);}
   else append();
  }
  append();
 }
}
/** Strip source wrapper punctuation in a clone, retaining all markup and note links. */
export function stageClone(node:any):any {
 const clone=node.cloneNode(true);const leaves:any[]=[];
 function collect(n:any){if(n.nodeType===3)leaves.push(n);else if(!['note','ref'].includes(n.localName))for(const c of Array.from(n.childNodes??[]))collect(c);}
 collect(clone);const nonempty=leaves.filter(n=>n.nodeValue?.trim());
 const first=nonempty[0],last=nonempty.at(-1);
 if(first&&last){
  const opening=first.nodeValue.match(/^\s*([[(])/u)?.[1];
  const closing=last.nodeValue.match(/([\])])([.,;:]?)\s*$/u)?.[1];
  if((opening==='('&&closing===')')||(opening==='['&&closing===']')){
   first.nodeValue=first.nodeValue.replace(/^\s*[[(]\s*/u,'');
   last.nodeValue=last.nodeValue.replace(/[\])]([.,;:]?)\s*$/u,'$1');
  }
  first.nodeValue=first.nodeValue.replace(/^\s*,\s*/u,'');
 }
 return clone;
}
