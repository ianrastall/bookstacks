import {describe,it,expect} from 'vitest';
import {preferredLocale,text} from './interface';
describe('interface locale negotiation',()=>{
 it('uses supported browser preferences in order with regional fallbacks',()=>{
  expect(preferredLocale(['de-DE','fr-CA','en'])).toBe('fr');
  expect(preferredLocale(['es-419','ru'])).toBe('es');
  expect(preferredLocale(['grc'])).toBe('grc');
  expect(preferredLocale(['el-GR','en'])).toBe('en');
  expect(preferredLocale(['zh-CN'])).toBe('zh-Hans');
  expect(preferredLocale(['zh-Hans-SG'])).toBe('zh-Hans');
  expect(preferredLocale(['zh-Hant','ru'])).toBe('ru');
  expect(preferredLocale(['zh-TW'])).toBe('en');
  expect(preferredLocale([])).toBe('en');
 });
 it('formats changing counts and interface labels in the requested locale',()=>{
  expect(text('fr','editionCount',[1])).toBe('1 édition');
  expect(text('ru','editionCount',[22])).toBe('22 издания');
  expect(text('es','c.3')).toBe('Idioma del libro');
 });
});
