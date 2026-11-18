import logging
from contextlib import asynccontextmanager
from typing import Annotated, Literal
from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from backend.app.core.config import MODEL_DIR, MAX_FILE_BYTES, MAX_CANDIDATES, allowed_origins
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import AnalysisResponse, ComparisonResponse
from backend.app.services.analysis import analyze
from backend.app.services.classifier import load_model
from backend.app.services.experiments import metrics, categories
from backend.app.services.files import extract

logger = logging.getLogger('talentmatch')

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await run_in_threadpool(load_model)
    except ServiceError:
        logger.warning('model_unavailable_at_startup')
    yield

app = FastAPI(title='TalentMatch AI', version='2.0.0', lifespan=lifespan, description='Apoio à análise com revisão humana. Sem ranking ou rejeição automática.')
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(), allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

@app.middleware('http')
async def privacy_headers(request: Request, call_next):
    limit = MAX_FILE_BYTES * MAX_CANDIDATES + 100000
    chunks = []
    length = 0
    async for chunk in request.stream():
        length += len(chunk)
        if length > limit:
            return JSONResponse(status_code=413, content={'error': {'code': 'request_too_large', 'message': 'Envio excede 25 MB mais metadados.'}}, headers={'Cache-Control': 'no-store'})
        chunks.append(chunk)
    request._body = b''.join(chunks)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.exception_handler(ServiceError)
async def service_error(request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status, content={'error': {'code': exc.code, 'message': exc.message}})

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={'error': {'code': 'invalid_request', 'message': 'Campos inválidos. Verifique arquivo, modo, currículo e vaga.'}})

@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.error('unhandled_error type=%s', type(exc).__name__)
    return JSONResponse(status_code=500, content={'error': {'code': 'internal_error', 'message': 'Falha interna ao processar a solicitação.'}})

@app.get('/api/health')
def health():
    try:
        model = load_model()
    except ServiceError:
        return JSONResponse(status_code=503, content={'status': 'degraded', 'model_loaded': False})
    # Model metadata must not turn a successful load into HTTP 500.
    estimators = getattr(model, 'calibrated_classifiers_', [])
    estimator = getattr(estimators[0], 'estimator', None) if len(estimators) else model
    classifier = getattr(estimator, 'named_steps', {}).get('clf', model)
    return {'status': 'ok', 'model_loaded': True, 'model_type': type(classifier).__name__}

ERROR_RESPONSES = {413: {'description': 'Tamanho excedido'}, 415: {'description': 'Formato inválido'}, 422: {'description': 'Entrada inválida'}, 503: {'description': 'Classificador indisponível'}}

async def read_resume(file: UploadFile) -> str:
    try:
        data = await file.read(MAX_FILE_BYTES + 1)
        return await run_in_threadpool(extract, data, file.filename or '', file.content_type)
    finally:
        await file.close()

@app.post('/api/analyze', response_model=AnalysisResponse, responses=ERROR_RESPONSES)
async def analyze_resume(job_description: Annotated[str, Form(min_length=1, max_length=16000)], mode: Annotated[Literal['live', 'demo'], Form()] = 'live', resume_text: Annotated[str, Form(max_length=40000)] = '', file: Annotated[UploadFile | None, File()] = None):
    if file is not None and resume_text.strip():
        await file.close()
        raise ServiceError('ambiguous_resume', 'Envie um arquivo ou cole texto, apenas uma das opções.')
    text = await read_resume(file) if file else resume_text
    return await run_in_threadpool(analyze, text, job_description, mode, 'Candidato 1')

@app.post('/api/compare', response_model=ComparisonResponse, responses=ERROR_RESPONSES)
async def compare(job_description: Annotated[str, Form(min_length=1, max_length=16000)], files: Annotated[list[UploadFile], File()], mode: Annotated[Literal['live', 'demo'], Form()] = 'live'):
    if not 2 <= len(files) <= MAX_CANDIDATES:
        for file in files:
            await file.close()
        raise ServiceError('invalid_batch', 'Envie entre 2 e 5 currículos.')
    results, failures = [], []
    try:
        for index, file in enumerate(files, 1):
            identifier = f'Candidato {index}'
            try:
                text = await read_resume(file)
                results.append(await run_in_threadpool(analyze, text, job_description, mode, identifier))
            except ServiceError as exc:
                failures.append({'candidate_id': identifier, 'code': exc.code, 'message': exc.message})
    finally:
        for file in files:
            await file.close()
    return ComparisonResponse(results=results, failures=failures)

@app.get('/api/models/metrics')
def model_metrics():
    return metrics()

@app.get('/api/models/categories')
def model_categories():
    return categories()

@app.get('/api/models/confusion-matrix', responses={200: {'content': {'image/png': {}}}})
def confusion_matrix():
    path = MODEL_DIR / 'matriz_confusao.png'
    if not path.exists():
        raise ServiceError('matrix_unavailable', 'A matriz de confusão original não está disponível.', 404)
    return FileResponse(path, media_type='image/png')
