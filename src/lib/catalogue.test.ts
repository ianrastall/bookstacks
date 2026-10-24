import {expect,it} from 'vitest';
import {foldSearch,matchesSearch,preferredBookLanguage} from './catalogue';
it('matches author and translated titles without depending on accents or punctuation',()=>{expect(matchesSearch('Dostoevsky · Преступление и наказание','преступление')).toBe(true);expect(matchesSearch('Les Misérables','miserables')).toBe(true);expect(matchesSearch('Wu Cheng’en 西游记','西游记')).toBe(true);expect(matchesSearch('Jane Austen Pride and Prejudice','austen pride')).toBe(true);expect(matchesSearch('Jane Austen Emma','dickens')).toBe(false);expect(foldSearch('Ἑλληνική')).toBe('ελληνικη');});

it('matches initial book language independently of interface locale, without changing scripts',()=>{
 expect(preferredBookLanguage(['fr-CA','en-US'])).toBe('fr');
 expect(preferredBookLanguage(['de-DE','ru-RU'])).toBe('ru');
 expect(preferredBookLanguage(['ja-JP'])).toBe('');
 expect(preferredBookLanguage(['zh-TW'])).toBe('');
 expect(preferredBookLanguage(['zh-CN'])).toBe('zh-Hans');
 expect(preferredBookLanguage(['el-GR'])).toBe('');
 expect(preferredBookLanguage(['grc'])).toBe('grc');
 expect(preferredBookLanguage(['bad tag'])).toBe('');
});
