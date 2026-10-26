"""Validate every PDF pair and publish its source-pinned catalogue snapshot."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://ianrastall.github.io/bookstacks-pdf/'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_text(path: Path) -> tuple[int, str, int]:
    digest = hashlib.sha256()
    length = 0
    document = pdfium.PdfDocument(path)
    pages = len(document)
    for index in range(pages):
        page = document[index]
        textpage = page.get_textpage()
        value = textpage.get_text_range()
        digest.update(value.encode('utf-8'))
        digest.update(b'\f')
        length += len(value)
        textpage.close()
        page.close()
    document.close()
    assert length > 100, f'Empty PDF text: {path}'
    return pages, digest.hexdigest(), length


def validate_pair(source: Path, books: Path) -> dict:
    source_hash = sha256(source)
    files = []
    results = []
    manifests = []
    for theme in ('light', 'dark'):
        name = f'{source.stem}-{theme}.pdf'
        pdf = books / source.parent.name / source.stem / name
        metadata = json.loads(pdf.with_suffix('.manifest.json').read_text(encoding='utf-8'))
        assert metadata['source_sha256'] == source_hash, f'Stale source: {pdf}'
        assert metadata['source_tei'] == source.name, f'Wrong edition: {pdf}'
        digest = sha256(pdf)
        assert digest == metadata['files'][0]['sha256'], f'Wrong PDF checksum: {pdf}'
        assert pdf.stat().st_size < 100 * 1024 * 1024, f'PDF exceeds GitHub file limit: {pdf}'
        result = pdf_text(pdf)
        assert result[0] == metadata['validations']['pdf']['pages'], f'Wrong page count: {pdf}'
        results.append(result)
        relative = Path('books') / source.parent.name / source.stem / name
        files.append({'theme': theme, 'file': name, 'path': relative.as_posix(), 'bytes': pdf.stat().st_size,
                      'sha256': digest, 'pages': result[0], 'text_sha256': result[1]})
        manifests.append(metadata)
    assert results[0] == results[1], f'Light/dark pagination or text differs: {source.name}'
    first = manifests[0]
    return {'edition_key': source.stem, 'edition_id': first['edition_id'], 'source_tei': source.name,
            'source_path': source.relative_to(ROOT).as_posix(), 'source_sha256': source_hash,
            'title': first['title'], 'author': first['author'], 'language': first['language'],
            'canonical_url': first['canonical_url'], 'files': files}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=ROOT.parent / 'bookstacks-pdf')
    args = parser.parse_args()
    repository = args.repository.resolve()
    books = repository / 'books'
    sources = sorted((ROOT / 'tei').glob('*/*.xml'))
    editions = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(validate_pair, source, books): source for source in sources}
        for index, job in enumerate(as_completed(jobs), 1):
            editions.append(job.result())
            print(f'[{index}/{len(sources)}] verified {jobs[job].stem}', flush=True)
    editions.sort(key=lambda item: item['edition_key'])
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest = {'schema_version': 1, 'source_repository': 'https://github.com/ianrastall/bookstacks',
                'source_commit': commit, 'base_url': BASE_URL, 'editions': editions}
    (repository / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    snapshot = {edition['edition_key']: {'source_sha256': edition['source_sha256'], 'variants': [
        {'theme': file['theme'], 'file': file['file'], 'href': BASE_URL + file['path'], 'revision': file['sha256']}
        for file in edition['files']]} for edition in editions}
    (ROOT / 'src/data/pdf-publications.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Validated {len(editions)} editions / {len(editions)*2} PDFs; website snapshot updated.', flush=True)


if __name__ == '__main__':
    main()
