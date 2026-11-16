from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from backend.app.core.config import MAX_FILE_BYTES, MAX_TEXT_CHARS
from backend.app.core.errors import ServiceError


def validate_text(text: str) -> str:
    if not text.strip():
        raise ServiceError('empty_resume', 'O currículo está vazio. PDFs digitalizados precisam de OCR externo.')
    if len(text) > MAX_TEXT_CHARS:
        raise ServiceError('text_too_long', f'O currículo excede {MAX_TEXT_CHARS} caracteres.', 413)
    return text.strip()


def extract(data: bytes, filename: str, content_type: str | None = None) -> str:
    if len(data) > MAX_FILE_BYTES:
        raise ServiceError('file_too_large', 'Cada arquivo deve ter no máximo 5 MB.', 413)
    suffix = Path(filename).suffix.lower()
    if suffix not in {'.pdf', '.txt'}:
        raise ServiceError('unsupported_file', 'Envie somente PDF ou TXT.', 415)
    allowed = {'.pdf': {'application/pdf', 'application/octet-stream'},
               '.txt': {'text/plain', 'application/octet-stream'}}
    if content_type and content_type.split(';')[0] not in allowed[suffix]:
        raise ServiceError('invalid_mime', 'O tipo do arquivo não corresponde ao formato permitido.', 415)
    try:
        if suffix == '.pdf':
            if not data.startswith(b'%PDF-'):
                raise ValueError('signature')
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted or len(reader.pages) > 30:
                raise ValueError('encrypted or too many pages')
            text = ''
            for page in reader.pages:
                text += (page.extract_text() or '') + '\n'
                if len(text) > MAX_TEXT_CHARS:
                    raise ServiceError('text_too_long', 'O texto extraído excede 40.000 caracteres.', 413)
        else:
            text = data.decode('utf-8-sig')
            if '\x00' in text:
                raise ValueError('binary')
    except ServiceError:
        raise
    except Exception:
        raise ServiceError('unreadable_file', 'Não foi possível ler o arquivo. Use TXT UTF-8 ou PDF textual, sem senha e até 30 páginas.') from None
    return validate_text(text)
