"""Prepare delivery JPEGs and thumbnails from generated Holmes PNG masters.

Noncreative format conversion only. Generated masters are cached under the
ignored assets/source-holmes-art directory and remain in Codex's generated
image directory as well. Run after generation, before build_holmes.py.
"""
from pathlib import Path
from PIL import Image
import hashlib, json

BASE=Path(__file__).resolve().parent/'doyle'
MASTER_ROOT=BASE.parents[1]/'assets/source-holmes-art'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 plan=json.loads((BASE/'holmes/illustration-plan.json').read_text(encoding='utf8'))
 records=[]
 for item in plan:
  target=BASE/'img/holmes'/f'{item["slug"]}.jpg'
  master=target.with_suffix('.png')
  cached_master=MASTER_ROOT/master.name
  if not master.exists():master=cached_master
  record_path=BASE/'holmes/art-records'/f'{item["slug"]}.json'
  record=json.loads(record_path.read_text(encoding='utf8'))
  with Image.open(master) as im:
   delivery=im.convert('RGB')
   delivery.thumbnail((1200,1200),Image.Resampling.LANCZOS)
   delivery.save(target,quality=88,optimize=True,subsampling=0)
   preview=target.with_name(target.stem+'.preview.jpg')
   im.thumbnail((640,640),Image.Resampling.LANCZOS)
   im.convert('RGB').save(preview,quality=88,optimize=True,subsampling=0)
  with Image.open(target) as im:width,height=im.size
  master_hash=sha(master)
  if master!=cached_master:
   MASTER_ROOT.mkdir(parents=True,exist_ok=True)
   assert not cached_master.exists(),f'Master already cached: {cached_master}'
   master.replace(cached_master)
  record.update(file=target.relative_to(BASE).as_posix(),sha256=sha(target),width=width,height=height,masterSha256=master_hash,masterFile=cached_master.relative_to(BASE.parents[1]).as_posix(),preview=dict(file=preview.relative_to(BASE).as_posix(),sha256=sha(preview)))
  record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  records.append(record)
 (BASE/'holmes/illustrations.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(f'Prepared {len(records)} full plates and previews.')
if __name__=='__main__':main()
