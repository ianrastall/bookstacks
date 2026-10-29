"""Offline delivery conversion of generated Christie masters; no image generation."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'tei/christie'
MASTERS = ROOT / 'assets/source-christie-art'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    MASTERS.mkdir(parents=True, exist_ok=True)
    records = []
    plan = json.loads((BASE/'illustration-plan.json').read_text(encoding='utf8'))
    for item in plan:
        record_file = BASE/'art-records'/f'{item["slug"]}.json'
        if not record_file.exists():
            continue
        record = json.loads(record_file.read_text(encoding='utf8'))
        record['useCase'] = 'illustration-story'
        target = BASE/item['file']
        if 'generatedFile' in record:
            source = Path(record.pop('generatedFile'))
            master = MASTERS/f'{item["slug"]}.png'
            shutil.copy2(source, master)
            with Image.open(master) as image:
                delivery = image.convert('RGB')
                delivery.thumbnail((1200,1200),Image.Resampling.LANCZOS)
                delivery.save(target,quality=88,optimize=True,subsampling=0)
                preview = target.with_name(target.stem+'.preview.jpg')
                delivery.thumbnail((640,640),Image.Resampling.LANCZOS)
                delivery.save(preview,quality=88,optimize=True,subsampling=0)
            with Image.open(target) as image:
                record.update(width=image.width,height=image.height)
            record.update(sha256=sha(target),masterSha256=sha(master),masterFile=master.relative_to(ROOT).as_posix(),
                          preview=dict(file=preview.relative_to(BASE).as_posix(),sha256=sha(preview)))
        record_file.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        records.append(record)
    (BASE/'illustrations.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(f'{len(records)}/{len(plan)} sketches prepared with full images and previews.')


if __name__ == '__main__':
    prepare()
