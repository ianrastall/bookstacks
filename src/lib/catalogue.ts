export function foldSearch(value:string):string {return value.normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();}
export function matchesSearch(haystack:string,query:string):boolean {const value=foldSearch(haystack);return foldSearch(query).split(/\s+/).every(word=>value.includes(word));}
