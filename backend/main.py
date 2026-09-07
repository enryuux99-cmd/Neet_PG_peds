from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json, time, shutil, os
from .parser import parse_pdf

BASE=Path(__file__).resolve().parents[1]
DATA=BASE/'data'; UPLOADS=BASE/'uploads'; FRONT=BASE/'frontend'
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True)
app=FastAPI(title='NEET-PG QBank')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

ACTIVE=DATA/'pediatrics.json'
ACTIVE_SOURCE=UPLOADS/'pediatrics_source.pdf'

@app.get('/api/qbank')
def qbank():
    if not ACTIVE.exists(): raise HTTPException(404,'No question bank imported.')
    return json.loads(ACTIVE.read_text(encoding='utf-8'))

@app.get('/api/source-page/{page}.png')
def source_page(page:int):
    if page<1: raise HTTPException(400,'Invalid page')
    try:
        import fitz
        doc=fitz.open(ACTIVE_SOURCE)
        if page>len(doc): raise HTTPException(404,'Page not found')
        pix=doc[page-1].get_pixmap(matrix=fitz.Matrix(1.25,1.25), alpha=False)
        return Response(pix.tobytes('png'), media_type='image/png', headers={'Cache-Control':'public, max-age=86400'})
    except HTTPException: raise
    except Exception as e: raise HTTPException(500, f'Could not render page: {e}')

@app.get('/api/source/{page}')
def source_pdf(page:int):
    if not ACTIVE_SOURCE.exists(): raise HTTPException(404,'Source PDF unavailable')
    return FileResponse(ACTIVE_SOURCE, media_type='application/pdf', filename=ACTIVE_SOURCE.name)

@app.post('/api/upload')
async def upload(file: UploadFile=File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400,'Please upload a PDF file.')
    dest=UPLOADS/f'{int(time.time())}_{Path(file.filename).name}'
    with dest.open('wb') as out: shutil.copyfileobj(file.file,out)
    try:
        parsed=parse_pdf(str(dest))
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(500,f'Could not parse PDF: {e}')
    stamp=int(time.time())
    out=DATA/f'uploaded_{stamp}.json'
    out.write_text(json.dumps(parsed,ensure_ascii=False),encoding='utf-8')
    # Make uploaded qbank the active bank for this browser/server instance.
    ACTIVE.write_text(json.dumps(parsed,ensure_ascii=False),encoding='utf-8')
    shutil.copy2(dest, ACTIVE_SOURCE)
    return parsed

@app.get('/')
def index(): return FileResponse(FRONT/'index.html')
@app.get('/app.js')
def js(): return FileResponse(FRONT/'app.js')
@app.get('/styles.css')
def css(): return FileResponse(FRONT/'styles.css')
