from io import BytesIO
import pytest
from pypdf import PdfWriter
from preprocess import limpar_texto
from backend.app.core.errors import ServiceError
from backend.app.services.files import extract
from backend.app.services.privacy import minimize
from backend.app.services.classifier import load_model, predict


def test_preprocess_keeps_technical_tokens_and_removes_contacts():
    cleaned = limpar_texto('PYTHON C++ C# test@example.com https://example.com 123')
    assert cleaned == 'python c++ c#'


def test_minimization_both_formats():
    text = 'Ana Silva\nNome: Ana Silva\nana@example.com\n(41) 99999-8888\nCPF: 123.456.789-00\nRua Flores, 10\nPython e SQL'
    safe, count = minimize(text, resume=True)
    assert 'Ana Silva' not in safe and 'example.com' not in safe
    assert '99999' not in safe and '123.456' not in safe and 'Flores' not in safe
    assert 'Python e SQL' in safe and count >= 5


@pytest.mark.parametrize('name,mime,data,code', [
    ('resume.exe', 'application/octet-stream', b'hello', 'unsupported_file'),
    ('resume.pdf', 'application/pdf', b'not a pdf', 'unreadable_file'),
    ('resume.txt', 'image/png', b'hello', 'invalid_mime'),
    ('resume.txt', 'text/plain', b'\xff\x00', 'unreadable_file'),
    ('resume.txt', 'text/plain', b'  ', 'empty_resume'),
    ('resume.txt', 'text/plain', b'a' * (5 * 1024 * 1024 + 1), 'file_too_large'),
    ('resume.txt', 'text/plain', b'a' * 40001, 'text_too_long'),
])
def test_invalid_uploads(name, mime, data, code):
    with pytest.raises(ServiceError) as error:
        extract(data, name, mime)
    assert error.value.code == code


def test_text_and_blank_pdf():
    assert extract(b'Python SQL', 'RESUME.TXT', 'text/plain') == 'Python SQL'
    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    stream = BytesIO()
    writer.write(stream)
    with pytest.raises(ServiceError, match='OCR'):
        extract(stream.getvalue(), 'resume.pdf', 'application/pdf')


def test_minimization_preserves_short_technical_resume():
    assert minimize('Python SQL', resume=True)[0] == 'Python SQL'
    assert minimize('Data Analyst', resume=True)[0] == 'Data Analyst'
    assert 'Ana Silva' not in minimize('Ana Silva\nPython SQL', resume=True)[0]


def test_valid_textual_pdf_extraction():
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(300, 300)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 20 200 Td (Python SQL experience) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    assert 'Python SQL experience' in extract(output.getvalue(), 'a.pdf', 'application/pdf')


def test_real_model_load_and_prediction():
    model = load_model()
    assert type(model.named_steps['clf']).__name__ == 'RandomForestClassifier'
    result = predict('Data analyst with Python SQL pandas financial reporting dashboards')
    assert len(result.top_categories) == 3
    assert result.predicted_area in model.classes_
    probabilities = [item.probability for item in result.top_categories]
    assert probabilities == sorted(probabilities, reverse=True)
    assert all(0 <= p <= 1 for p in probabilities)
