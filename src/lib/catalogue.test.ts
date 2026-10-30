import {expect,it} from 'vitest';
import {foldSearch,matchesSearch} from './catalogue';
it('matches author and translated titles without depending on accents or punctuation',()=>{expect(matchesSearch('Dostoevsky · Преступление и наказание','преступление')).toBe(true);expect(matchesSearch('Les Misérables','miserables')).toBe(true);expect(matchesSearch('Wu Cheng’en 西游记','西游记')).toBe(true);expect(matchesSearch('Jane Austen Pride and Prejudice','austen pride')).toBe(true);expect(matchesSearch('Jane Austen Emma','dickens')).toBe(false);expect(foldSearch('Ἑλληνική')).toBe('ελληνικη');});
