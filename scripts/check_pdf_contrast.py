"""Reject opaque black text in newly generated dark PDF editions.

Uses PDFium text objects, excluding images, rules and invisible text. Run with
the PDF inspection runtime; the site build does not author or alter any PDFs.
"""
from concurrent.futures import ProcessPoolExecutor,as_completed
import argparse
import ctypes
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw


def check(path:Path):
    document=pdfium.PdfDocument(path)
    failures=[]
    for index in range(len(document)):
        page=document[index];count=0
        for obj in page.get_objects(filter=[raw.FPDF_PAGEOBJ_TEXT]):
            if raw.FPDFTextObj_GetTextRenderMode(obj.raw)==3:continue
            rgba=[ctypes.c_uint() for _ in range(4)]
            if raw.FPDFPageObj_GetFillColor(obj.raw,*[ctypes.byref(value) for value in rgba]):
                red,green,blue,alpha=[value.value for value in rgba]
                if alpha>0 and max(red,green,blue)<=8:count+=1
        if count:failures.append({'page':index+1,'black_text_objects':count})
        page.close()
    document.close()
    return path,failures


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths',nargs='+',type=Path)
    args=parser.parse_args()
    files=[]
    for path in args.paths:
        files.extend(sorted(path.rglob('*-dark.pdf')) if path.is_dir() else [path])
    if not files:raise ValueError('No dark PDF editions found')
    failures=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for result in as_completed([pool.submit(check,path) for path in files]):
            path,pages=result.result()
            if pages:failures.append((path,pages));print('FAIL',path.name,pages,flush=True)
            else:print('OK',path.name,flush=True)
    print(f'Checked {len(files)} dark PDFs; {len(failures)} failed.',flush=True)
    return 1 if failures else 0


if __name__=='__main__':raise SystemExit(main())
