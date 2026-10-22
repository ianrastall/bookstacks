import { isLocale, ui, type Locale } from './i18n';
import { jupiterUi } from './jupiter-ui';

// Interface locales are independent of the languages of literary editions.
const copy: Record<Locale, string[]> = {
 en: ['Interface language','Automatic (browser preference)','Authors','Book language','All authors','Title / author','Read','No matching books.','Search authors and titles','Page not found','Return to the library','Applied for this page. Your browser could not save the preference.'],
 fr: ["Langue de l’interface",'Automatique (préférences du navigateur)','Auteurs','Langue du livre','Tous les auteurs','Titre / auteur','Lire','Aucun livre correspondant.','Rechercher un auteur ou un titre','Page introuvable','Revenir à la bibliothèque','Appliqué pour cette page. Le navigateur ne peut pas enregistrer ce choix.'],
 es: ['Idioma de la interfaz','Automático (preferencias del navegador)','Autores','Idioma del libro','Todos los autores','Título / autor','Leer','No hay libros coincidentes.','Buscar autores y títulos','Página no encontrada','Volver a la biblioteca','Aplicado en esta página. El navegador no pudo guardar la preferencia.'],
 grc: ['Γλῶττα τῆς διεπαφῆς','Αὐτόματος ἐκλογή','Συγγραφεῖς','Γλῶττα τοῦ βιβλίου','Πάντες συγγραφεῖς','Τίτλος / συγγραφεύς','Ἀναγιγνώσκειν','Οὐδὲν βιβλίον εὑρέθη.','Ζητεῖν συγγραφεῖς καὶ τίτλους','Ἡ σελὶς οὐχ εὑρέθη','Ἐπὶ τὴν βιβλιοθήκην','Ἡ ἐκλογὴ μόνον ἐν ταύτῃ τῇ σελίδι μένει.'],
 ru: ['Язык интерфейса','Автоматически (настройки браузера)','Авторы','Язык книги','Все авторы','Название / автор','Читать','Книги не найдены.','Поиск авторов и названий','Страница не найдена','Вернуться в библиотеку','Применено на этой странице. Браузер не смог сохранить настройку.'],
 'zh-Hans': ['界面语言','自动（浏览器偏好）','作者','图书语言','所有作者','书名 / 作者','阅读','没有匹配的图书。','搜索作者和书名','未找到页面','返回图书馆','已应用于此页面。浏览器无法保存此偏好。'],
};
export type TranslationArg = string | number;
export function text(locale: Locale, key: string, args: TranslationArg[] = []): string {
 if (key.startsWith('j.')) return jupiterUi(locale)[Number(key.slice(2))] ?? '';
 if (key.startsWith('c.')) return copy[locale][Number(key.slice(2))] ?? '';
 const value = ui(locale)[key as keyof ReturnType<typeof ui>];
 if (typeof value === 'function') return String((value as (...values: TranslationArg[]) => string)(...args));
 return typeof value === 'string' ? value : '';
}
export function preferredLocale(preferences: readonly string[]): Locale {
 for (const preference of preferences) {
  const tag = preference.toLowerCase();
  if (tag === 'zh' || /^zh-(hans(?:-|$)|cn(?:-|$)|sg(?:-|$))/.test(tag)) return 'zh-Hans';
  const base = tag.split('-')[0];
  if (base !== 'zh' && isLocale(base)) return base;
 }
 return 'en';
}
