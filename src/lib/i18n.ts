export const SUPPORTED_LANGUAGES = [
  { code: 'en', teiCode: 'eng', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'fr', teiCode: 'fra', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'grc', teiCode: 'grc', name: 'Ancient Greek', nativeName: 'Ἑλληνική', flag: '🇬🇷' },
  { code: 'ru', teiCode: 'rus', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
] as const;

export type Locale = typeof SUPPORTED_LANGUAGES[number]['code'];

export function isLocale(value: string): value is Locale {
  return SUPPORTED_LANGUAGES.some((language) => language.code === value);
}

export function languageData(locale: Locale) {
  return SUPPORTED_LANGUAGES.find((language) => language.code === locale)!;
}

export interface UiStrings {
  siteDescription: string;
  skipToContent: string;
  library: string;
  home: string;
  siteNetwork: string;
  chooseLanguage: string;
  allLanguages: string;
  chooseColorTheme: string;
  colorThemes: string;
  toggleTheme: string;
  switchToLight: string;
  switchToDark: string;
  curatedLibrary: string;
  support: string;
  librarySummary: (authors: number, books: number, editions: number, units: string) => string;
  booksBy: (name: string) => string;
  byAuthor: (name: string) => string;
  bookCount: (count: number) => string;
  editionCount: (count: number) => string;
  readingUnitCount: (count: number) => string;
  organizedBy: (kind: string) => string;
  availableInLanguage: (language: string) => string;
  startReading: string;
  continueReading: string;
  otherEditions: string;
  contents: string;
  frontMatter: string;
  backMatter: string;
  downloads: string;
  downloadEdition: string;
  downloadFormatsNote: string;
  author: string;
  title: string;
  files: string;
  people: string;
  places: string;
  registries: (people: number, places: number) => string;
  previous: string;
  next: string;
  readingOrder: string;
  readingControls: string;
  textWidth: string;
  textSize: string;
  narrowText: string;
  widenText: string;
  decreaseText: string;
  increaseText: string;
  serifCascade: string;
  sansCascade: string;
  fontNote: string;
  footnote: string;
  closeFootnote: string;
  automaticTranslationNote: string;
  editionStructureNote: string;
  noBooks: string;
  colors: Record<string, string>;
}

function russianPlural(count: number, one: string, few: string, many: string): string {
  const mod10 = Math.abs(count) % 10;
  const mod100 = Math.abs(count) % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

const STRINGS: Record<Locale, UiStrings> = {
  en: {
    siteDescription: 'A curated library of public-domain literature.',
    skipToContent: 'Skip to content',
    library: 'Library',
    home: 'Home',
    siteNetwork: 'Site network',
    chooseLanguage: 'Choose language',
    allLanguages: 'All languages',
    chooseColorTheme: 'Choose color theme',
    colorThemes: 'Color themes',
    toggleTheme: 'Toggle theme',
    switchToLight: 'Switch to light theme',
    switchToDark: 'Switch to dark theme',
    curatedLibrary: 'A curated library of public-domain literature. Bookstacks runs locally in your browser; some tools may make external requests.',
    support: 'If this saved you a few hours of work, consider supporting Bookstacks on Ko-fi.',
    librarySummary: (authors, books, editions, units) => `A curated index with ${authors} authors, ${books} books, ${editions} TEI editions, and ${units} reading units in English.`,
    booksBy: (name) => `Books by ${name}`,
    byAuthor: (name) => `By ${name}`,
    bookCount: (count) => `${count} ${count === 1 ? 'book' : 'books'}`,
    editionCount: (count) => `${count} ${count === 1 ? 'edition' : 'editions'}`,
    readingUnitCount: (count) => `${count} reading ${count === 1 ? 'unit' : 'units'}`,
    organizedBy: (kind) => `organized by ${kind}`,
    availableInLanguage: (language) => `Available in ${language}`,
    startReading: 'Start reading',
    continueReading: 'Continue reading',
    otherEditions: 'Other editions',
    contents: 'Contents',
    frontMatter: 'Front matter',
    backMatter: 'Back matter',
    downloads: 'Downloads',
    downloadEdition: 'Download this edition',
    downloadFormatsNote: 'Download the TEI source for any edition. A PDF is offered only when a matching file is included in the repository.',
    author: 'Author',
    title: 'Title',
    files: 'Files',
    people: 'People',
    places: 'Places',
    registries: (people, places) => `TEI registries (${people} people, ${places} places)`,
    previous: 'Previous',
    next: 'Next',
    readingOrder: 'Reading order',
    readingControls: 'Reading controls and navigation',
    textWidth: 'Text width',
    textSize: 'Text size',
    narrowText: 'Narrow text column',
    widenText: 'Widen text column',
    decreaseText: 'Decrease text size',
    increaseText: 'Increase text size',
    serifCascade: 'Serif cascade',
    sansCascade: 'Sans-serif cascade',
    fontNote: 'Each option is an ordered CSS cascade. The browser uses the first installed font.',
    footnote: 'Footnote',
    closeFootnote: 'Close footnote',
    automaticTranslationNote: 'Automatic browser translation is disabled for this source-language edition.',
    editionStructureNote: 'This is a complete, standalone TEI edition whose own hierarchy is preserved; translations are not forced into artificial chapter-by-chapter alignment.',
    noBooks: 'No books are currently available in this language.',
    colors: { blue: 'Blue', green: 'Green', red: 'Red', orange: 'Ochre', indigo: 'Indigo', brown: 'Brown', coral: 'Coral' },
  },
  fr: {
    siteDescription: 'Une bibliothèque choisie de littérature du domaine public.',
    skipToContent: 'Aller au contenu',
    library: 'Bibliothèque',
    home: 'Accueil',
    siteNetwork: 'Réseau du site',
    chooseLanguage: 'Choisir la langue',
    allLanguages: 'Toutes les langues',
    chooseColorTheme: 'Choisir le thème de couleur',
    colorThemes: 'Thèmes de couleur',
    toggleTheme: 'Changer de thème',
    switchToLight: 'Passer au thème clair',
    switchToDark: 'Passer au thème sombre',
    curatedLibrary: 'Une bibliothèque choisie de littérature du domaine public. Bookstacks fonctionne localement dans votre navigateur ; certains outils peuvent effectuer des requêtes externes.',
    support: 'Si ce site vous a fait gagner quelques heures, vous pouvez soutenir Bookstacks sur Ko-fi.',
    librarySummary: (authors, books, editions, units) => `Un catalogue choisi de ${authors} auteurs, ${books} livres, ${editions} éditions TEI et ${units} unités de lecture en français.`,
    booksBy: (name) => `Livres de ${name}`,
    byAuthor: (name) => `Par ${name}`,
    bookCount: (count) => `${count} ${count === 1 ? 'livre' : 'livres'}`,
    editionCount: (count) => `${count} ${count === 1 ? 'édition' : 'éditions'}`,
    readingUnitCount: (count) => `${count} ${count === 1 ? 'unité de lecture' : 'unités de lecture'}`,
    organizedBy: (kind) => `organisé par ${kind}`,
    availableInLanguage: (language) => `Disponible en ${language}`,
    startReading: 'Commencer la lecture',
    continueReading: 'Continuer la lecture',
    otherEditions: 'Autres éditions',
    contents: 'Sommaire',
    frontMatter: 'Pages liminaires',
    backMatter: 'Pages finales',
    downloads: 'Téléchargements',
    downloadEdition: 'Télécharger cette édition',
    downloadFormatsNote: 'Téléchargez la source TEI de chaque édition. Un PDF est proposé uniquement si le dépôt contient le fichier correspondant.',
    author: 'Auteur',
    title: 'Titre',
    files: 'Fichiers',
    people: 'Personnes',
    places: 'Lieux',
    registries: (people, places) => `Registres TEI (${people} personnes, ${places} lieux)`,
    previous: 'Précédent',
    next: 'Suivant',
    readingOrder: 'Ordre de lecture',
    readingControls: 'Réglages et navigation de lecture',
    textWidth: 'Largeur du texte',
    textSize: 'Taille du texte',
    narrowText: 'Rétrécir la colonne de texte',
    widenText: 'Élargir la colonne de texte',
    decreaseText: 'Réduire la taille du texte',
    increaseText: 'Augmenter la taille du texte',
    serifCascade: 'Police avec empattements',
    sansCascade: 'Police sans empattements',
    fontNote: 'Chaque option est une liste ordonnée de polices. Le navigateur utilise la première police installée.',
    footnote: 'Note',
    closeFootnote: 'Fermer la note',
    automaticTranslationNote: 'La traduction automatique du navigateur est désactivée pour préserver cette édition dans sa langue source.',
    editionStructureNote: 'Il s’agit d’une édition TEI complète et autonome dont la hiérarchie propre est conservée ; les traductions ne sont pas artificiellement alignées chapitre par chapitre.',
    noBooks: 'Aucun livre n’est actuellement disponible dans cette langue.',
    colors: { blue: 'Bleu', green: 'Vert', red: 'Rouge', orange: 'Ocre', indigo: 'Indigo', brown: 'Brun', coral: 'Corail' },
  },
  grc: {
    siteDescription: 'Βιβλιοθήκη ἐκλεκτῶν δημοσίων συγγραμμάτων.',
    skipToContent: 'Ἐπὶ τὸ περιεχόμενον',
    library: 'Βιβλιοθήκη',
    home: 'Οἶκος',
    siteNetwork: 'Δίκτυον',
    chooseLanguage: 'Γλῶτταν ἑλέσθαι',
    allLanguages: 'Πᾶσαι γλῶτται',
    chooseColorTheme: 'Χρῶμα ἑλέσθαι',
    colorThemes: 'Χρώματα',
    toggleTheme: 'Φῶς μεταβάλλειν',
    switchToLight: 'Εἰς φῶς',
    switchToDark: 'Εἰς σκότος',
    curatedLibrary: 'Βιβλιοθήκη ἐκλεκτῶν δημοσίων συγγραμμάτων. Τὸ Bookstacks ἐν τῷ περιηγητῇ λειτουργεῖ.',
    support: 'Εἰ ὠφέλιμον σοι ἐγένετο, δύνασαι τὸ Bookstacks ἐν Ko-fi στηρίζειν.',
    librarySummary: (authors, books, editions, units) => `Κατάλογος ${authors} συγγραφέων, ${books} βιβλίων, ${editions} ἐκδόσεων TEI καὶ ${units} μερῶν Ἑλληνιστί.`,
    booksBy: (name) => `Βιβλία τοῦ ${name}`,
    byAuthor: (name) => `Ὑπὸ ${name}`,
    bookCount: (count) => `${count} ${count === 1 ? 'βιβλίον' : 'βιβλία'}`,
    editionCount: (count) => `${count} ${count === 1 ? 'ἔκδοσις' : 'ἐκδόσεις'}`,
    readingUnitCount: (count) => `${count} ${count === 1 ? 'μέρος' : 'μέρη'}`,
    organizedBy: (kind) => `κατὰ ${kind}`,
    availableInLanguage: (language) => `Ἐν ${language}`,
    startReading: 'Ἄρξασθαι τῆς ἀναγνώσεως',
    continueReading: 'Ἀναγιγνώσκειν',
    otherEditions: 'Ἄλλαι ἐκδόσεις',
    contents: 'Περιεχόμενα',
    frontMatter: 'Προοίμιον',
    backMatter: 'Ἐπίλογος',
    downloads: 'Καταφορτώσεις',
    downloadEdition: 'Τὴν ἔκδοσιν καταφορτῶσαι',
    downloadFormatsNote: 'Τὴν πηγὴν TEI ἑκάστης ἐκδόσεως κατάφορτωσον. PDF παρέχεται μόνον ἐὰν τὸ ἀντίστοιχον ἀρχεῖον ἐν τῇ ἀποθήκῃ ὑπάρχῃ.',
    author: 'Συγγραφεύς',
    title: 'Τίτλος',
    files: 'Ἀρχεῖα',
    people: 'Πρόσωπα',
    places: 'Τόποι',
    registries: (people, places) => `Κατάλογοι TEI (${people} ${people === 1 ? 'πρόσωπον' : 'πρόσωπα'}, ${places} ${places === 1 ? 'τόπος' : 'τόποι'})`,
    previous: 'Πρότερον',
    next: 'Ἑπόμενον',
    readingOrder: 'Τάξις ἀναγνώσεως',
    readingControls: 'Μέτρα καὶ πλοήγησις',
    textWidth: 'Πλάτος λόγου',
    textSize: 'Μέγεθος γραμμάτων',
    narrowText: 'Στενότερον',
    widenText: 'Εὐρύτερον',
    decreaseText: 'Μικρότερα γράμματα',
    increaseText: 'Μείζονα γράμματα',
    serifCascade: 'Γράμματα κερασφόρα',
    sansCascade: 'Γράμματα ἄκερα',
    fontNote: 'Ὁ περιηγητὴς τὴν πρώτην παροῦσαν γραμματοσειρὰν χρῆται.',
    footnote: 'Ὑποσημείωσις',
    closeFootnote: 'Κλεῖσαι τὴν ὑποσημείωσιν',
    automaticTranslationNote: 'Ἡ αὐτόματος μετάφρασις κέκλεισται, ἵνα ἡ γλῶττα σώζηται.',
    editionStructureNote: 'Ἡ ἔκδοσις αὕτη τελεία καὶ αὐτοτελής ἐστι, τὴν οἰκείαν τάξιν φυλάττουσα.',
    noBooks: 'Οὐδὲν βιβλίον ταύτῃ τῇ γλώττῃ πάρεστιν.',
    colors: { blue: 'Κυανοῦν', green: 'Πράσινον', red: 'Ἐρυθρόν', orange: 'Ὦχρα', indigo: 'Ἰνδικόν', brown: 'Φαιόν', coral: 'Κοράλλιον' },
  },
  ru: {
    siteDescription: 'Избранная библиотека литературы общественного достояния.',
    skipToContent: 'Перейти к содержанию',
    library: 'Библиотека',
    home: 'Главная',
    siteNetwork: 'Сайты',
    chooseLanguage: 'Выбрать язык',
    allLanguages: 'Все языки',
    chooseColorTheme: 'Выбрать цветовую тему',
    colorThemes: 'Цветовые темы',
    toggleTheme: 'Сменить тему',
    switchToLight: 'Включить светлую тему',
    switchToDark: 'Включить тёмную тему',
    curatedLibrary: 'Избранная библиотека литературы общественного достояния. Bookstacks работает локально в браузере; некоторые инструменты могут обращаться к внешним службам.',
    support: 'Если сайт сэкономил вам время, вы можете поддержать Bookstacks на Ko-fi.',
    librarySummary: (authors, books, editions, units) => `Избранный каталог: ${authors} авторов, ${books} книг, ${editions} изданий TEI и ${units} частей для чтения на русском языке.`,
    booksBy: (name) => `Книги автора ${name}`,
    byAuthor: (name) => `Автор: ${name}`,
    bookCount: (count) => `${count} ${russianPlural(count, 'книга', 'книги', 'книг')}`,
    editionCount: (count) => `${count} ${russianPlural(count, 'издание', 'издания', 'изданий')}`,
    readingUnitCount: (count) => `${count} ${russianPlural(count, 'часть', 'части', 'частей')} для чтения`,
    organizedBy: (kind) => `структура: ${kind}`,
    availableInLanguage: (language) => `Доступно на языке: ${language}`,
    startReading: 'Начать чтение',
    continueReading: 'Продолжить чтение',
    otherEditions: 'Другие издания',
    contents: 'Содержание',
    frontMatter: 'Начальные материалы',
    backMatter: 'Заключительные материалы',
    downloads: 'Загрузки',
    downloadEdition: 'Скачать это издание',
    downloadFormatsNote: 'Для каждого издания доступен исходный файл TEI. PDF предлагается только тогда, когда соответствующий файл есть в репозитории.',
    author: 'Автор',
    title: 'Название',
    files: 'Файлы',
    people: 'Люди',
    places: 'Места',
    registries: (people, places) => `Реестры TEI (${people} ${russianPlural(people, 'персона', 'персоны', 'персон')}, ${places} ${russianPlural(places, 'место', 'места', 'мест')})`,
    previous: 'Назад',
    next: 'Далее',
    readingOrder: 'Порядок чтения',
    readingControls: 'Настройки чтения и навигация',
    textWidth: 'Ширина текста',
    textSize: 'Размер текста',
    narrowText: 'Сузить колонку текста',
    widenText: 'Расширить колонку текста',
    decreaseText: 'Уменьшить текст',
    increaseText: 'Увеличить текст',
    serifCascade: 'Шрифт с засечками',
    sansCascade: 'Шрифт без засечек',
    fontNote: 'Каждый вариант — упорядоченный список шрифтов. Браузер использует первый установленный шрифт.',
    footnote: 'Примечание',
    closeFootnote: 'Закрыть примечание',
    automaticTranslationNote: 'Автоматический перевод браузера отключён, чтобы сохранить язык исходного издания.',
    editionStructureNote: 'Это полное самостоятельное издание TEI с сохранённой собственной структурой; переводы не выравниваются искусственно по главам.',
    noBooks: 'На этом языке пока нет доступных книг.',
    colors: { blue: 'Синий', green: 'Зелёный', red: 'Красный', orange: 'Охра', indigo: 'Индиго', brown: 'Коричневый', coral: 'Коралловый' },
  },
};

export function ui(locale: Locale): UiStrings {
  return STRINGS[locale];
}
