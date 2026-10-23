import {describe,it,expect} from 'vitest';
import '../i18n/catalogues';
import en from '../i18n/locales/en';
import type {Message} from '../i18n/types';
import {EDITION_LANGUAGES,INTERFACE_LOCALES,localeDirection} from './i18n';
import {hasMessages,preferredLocale,text} from './interface';
const catalogues=import.meta.glob<{default:Record<string,Message>}>('../i18n/locales/*.ts',{eager:true});
const placeholders=(message:Message)=>(typeof message==='string'?[message]:Object.values(message)).flatMap(value=>value.match(/\{\d+(?:\|\w+)?\}/g)??[]).sort();
describe('interface locale negotiation',()=>{
 it('uses supported browser preferences in order with regional fallbacks',()=>{
  expect(preferredLocale(['de-DE','fr-CA','en'])).toBe('de');
  expect(preferredLocale(['xx','fr-CA','en'])).toBe('fr');
  expect(preferredLocale(['es-419','ru'])).toBe('es');
  expect(preferredLocale(['grc'])).toBe('grc');
  expect(preferredLocale(['el-GR','en'])).toBe('el');
  expect(preferredLocale(['zh-CN'])).toBe('zh-Hans');
  expect(preferredLocale(['zh-Hans-SG'])).toBe('zh-Hans');
  expect(preferredLocale(['zh'])).toBe('zh-Hans');
  expect(preferredLocale(['zh-Hant','ru'])).toBe('zh-Hant');
  expect(preferredLocale(['zh-TW'])).toBe('zh-Hant');
  expect(preferredLocale(['zh-HK'])).toBe('zh-Hant');
  expect(preferredLocale(['pt'])).toBe('pt-BR');
  expect(preferredLocale(['pt-PT'])).toBe('pt-PT');
  expect(preferredLocale(['pt-AO'])).toBe('pt-PT');
  expect(preferredLocale(['no'])).toBe('nb');
  expect(preferredLocale(['nn-NO'])).toBe('nb');
  expect(preferredLocale(['iw-IL'])).toBe('he');
  expect(preferredLocale(['tl-PH'])).toBe('fil');
  expect(preferredLocale(['not a tag','ja-JP'])).toBe('ja');
  expect(preferredLocale([])).toBe('en');
 });
 it('formats changing counts and interface labels in the requested locale',()=>{
  expect(text('fr','editionCount',[1])).toBe('1 édition');
  expect(text('ru','editionCount',[22])).toBe('22 издания');
  expect(text('ru','editionCount',[25])).toBe('25 изданий');
  expect(text('pl','bookCount',[5])).toBe('5 książek');
  expect(text('es','bookLanguage')).toBe('Idioma del libro');
  expect(text('en','registries',[1,3])).toBe('TEI registries (1 person, 3 places)');
  expect(text('grc','bookCount',[1])).toBe('1 βιβλίον');
  expect(text('de','byAuthor',['Jane Austen'])).toBe('Von Jane Austen');
 });
 it('declares direction for right-to-left interface locales',()=>{
  expect(localeDirection('ar')).toBe('rtl');
  expect(localeDirection('he')).toBe('rtl');
  expect(localeDirection('en')).toBe('ltr');
 });
});
describe('interface catalogues',()=>{
 it('provides one complete catalogue for every declared interface locale',()=>{
  const files=Object.keys(catalogues).map(file=>file.replace('../i18n/locales/','').replace('.ts','')).sort();
  expect(files).toEqual(INTERFACE_LOCALES.map(locale=>locale.code).sort());
  for(const language of EDITION_LANGUAGES)expect(hasMessages(language.code)).toBe(true);
 });
 for(const [file,{default:catalogue}] of Object.entries(catalogues))it(`keeps every message and placeholder: ${file}`,()=>{
  expect(Object.keys(catalogue).sort()).toEqual(Object.keys(en).sort());
  for(const [key,message] of Object.entries(catalogue)){
   const source=en[key as keyof typeof en];
   expect(typeof message,key).toBe(typeof source);
   if(typeof message==='string')expect(message.trim(),key).not.toBe('');
   else{expect(message.other,key).toBeTruthy();for(const form of Object.values(message))expect(form,key).toContain('#');}
   expect(placeholders(message),key).toEqual(placeholders(source));
  }
 });
});
