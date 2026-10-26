// The bundled Mozilla viewer runs in a same-origin frame, not the browser's
// PDF plugin. Its text layer, find bar, outline and keyboard controls stay intact.
interface PdfFile { theme: string; href: string; revision: string }
interface ViewerWindow extends Window {
  PDFViewerApplicationOptions: { set(name: string, value: unknown): void };
  PDFViewerApplication: {
    page: number;
    initializedPromise: Promise<void>;
    eventBus: { on(name: string, callback: (event: { pageNumber: number }) => void): void };
  };
}
const root = document.documentElement;
const read = (key: string) => { try { return localStorage.getItem(key); } catch { return null; } };
const save = (key: string, value: string) => { try { localStorage.setItem(key, value); } catch { /* Optional storage. */ } };

for (const panel of document.querySelectorAll<HTMLDetailsElement>('[data-pdf-files]')) {
  const files: PdfFile[] = JSON.parse(panel.dataset.pdfFiles!);
  const frame = panel.querySelector<HTMLIFrameElement>('[data-pdf-frame]')!;
  const choice = panel.querySelector<HTMLSelectElement>('[data-pdf-theme]');
  const download = panel.querySelector<HTMLAnchorElement>('[data-pdf-download]')!;
  const pageKey = `bookstacks-pdf-page:${files.map(file => file.revision).join(':')}`;
  const savedPage = Number(read(pageKey));
  let page = Number.isSafeInteger(savedPage) && savedPage > 0 ? savedPage : 1;
  let explicitTheme = read('bookstacks-pdf-theme');
  let active: PdfFile;
  let loaded = false;
  const viewer = () => (frame.contentWindow as ViewerWindow | null)?.PDFViewerApplication;
  const remember = () => {
    const current = viewer()?.page;
    if (current && Number.isSafeInteger(current) && current > 0) page = current;
    save(pageKey, String(page));
  };
  function styleViewer() {
    const doc = frame.contentDocument;
    if (!doc) return;
    const pages = doc.querySelector('#viewer');
    pages?.setAttribute('lang', frame.dataset.pdfLanguage || 'en');
    pages?.setAttribute('translate', 'no');
    const styles = getComputedStyle(root);
    doc.documentElement.style.colorScheme = root.dataset.theme === 'light' ? 'light' : 'dark';
    for (const [target, source] of Object.entries({
      '--body-bg-color': '--panel-muted', '--toolbar-bg-color': '--panel',
      '--main-color': '--text', '--toolbar-icon-bg-color': '--text',
      '--field-bg-color': '--input', '--field-color': '--text',
      '--button-primary-bg-color': '--accent', '--button-primary-fg-color': '--on-accent',
    })) doc.documentElement.style.setProperty(target, styles.getPropertyValue(source));
  }
  function open(force = false) {
    const desired = explicitTheme || root.dataset.theme;
    const file = files.find(file => file.theme === desired) ?? files[0];
    if (choice) { choice.value = file.theme; choice.disabled = false; }
    download.href = file.href;
    download.download = file.href.split('/').pop()!;
    if (!panel.open) return;
    if (loaded && active === file && !force) { styleViewer(); return; }
    remember();
    active = file;
    loaded = true;
    const url = new URL('/vendor/pdfjs/web/viewer.html', location.origin);
    url.searchParams.set('file', file.href);
    // A locale change must reload the viewer document, not just its page hash.
    url.searchParams.set('bookstacksLocale', root.lang);
    url.hash = `page=${page}&zoom=page-width`;
    frame.hidden = false;
    frame.src = url.href;
  }
  document.addEventListener('webviewerloaded', event => {
    const source = (event as CustomEvent<{ source: ViewerWindow }>).detail.source;
    if (source !== frame.contentWindow) return;
    const options = source.PDFViewerApplicationOptions;
    options.set('disablePreferences', true);
    options.set('disableHistory', true);
    options.set('disablePageLabels', true);
    options.set('sidebarViewOnLoad', 0);
    options.set('enableScripting', false);
    options.set('annotationEditorMode', -1);
    options.set('externalLinkTarget', 2);
    options.set('defaultUrl', '');
    options.set('localeProperties', { lang: root.lang });
    source.document.documentElement.lang = root.lang;
    options.set('viewerCssTheme', root.dataset.theme === 'light' ? 1 : 2);
    styleViewer();
    void source.PDFViewerApplication.initializedPromise.then(() => {
      source.PDFViewerApplication.eventBus.on('pagechanging', event => {
        page = event.pageNumber;
        save(pageKey, String(page));
      });
    });
  });
  choice?.addEventListener('change', () => {
    explicitTheme = choice.value;
    save('bookstacks-pdf-theme', explicitTheme);
    open();
  });
  panel.addEventListener('toggle', () => {
    if (panel.open) {
      open();
      history.replaceState(null, '', `${location.pathname}${location.search}#pdf-reader`);
    } else if (location.hash === '#pdf-reader') {
      history.replaceState(null, '', `${location.pathname}${location.search}`);
    }
  });
  new MutationObserver(() => open()).observe(root, { attributes: true, attributeFilter: ['data-theme', 'style'] });
  document.addEventListener('interfacechange', () => { if (loaded) open(true); });
  window.addEventListener('pagehide', remember);
  window.addEventListener('hashchange', () => { if (location.hash === '#pdf-reader') panel.open = true; });
  if (location.hash === '#pdf-reader') panel.open = true;
  open();
}
