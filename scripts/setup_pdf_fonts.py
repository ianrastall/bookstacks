"""Fetch the hash-pinned open font resources used only by offline PDF exports."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

root = Path(__file__).resolve().parents[1]
for record in json.loads((root / 'scripts/export/fonts.json').read_text(encoding='utf-8')):
    target = (root / record['path']).resolve()
    assert target.is_relative_to(root / '.tools'), target
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == record['sha256']:
        print(f'Verified {target.name}')
        continue
    request = urllib.request.Request(record['url'], headers={'User-Agent': 'Bookstacks PDF exporter'})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if record['url'].endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            name = next(name for name in archive.namelist() if Path(name).name == target.name)
            data = archive.read(name)
    assert hashlib.sha256(data).hexdigest() == record['sha256'], f'Font checksum mismatch: {target.name}'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(f'Fetched and verified {target.name}')
