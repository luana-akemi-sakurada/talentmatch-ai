from backend.app.core.errors import ServiceError
from backend.app.services import classifier


def test_health_metrics_categories_and_matrix(client):
    assert client.get('/api/health').json()['model_loaded'] is True
    data = client.get('/api/models/metrics').json()
    winner = next(m for m in data['models'] if m['name'] == 'RandomForest')
    assert winner['accuracy'] == .7505 and winner['f1_macro'] == .6896
    assert winner['precision_macro'] is None
    cats = client.get('/api/models/categories').json()
    assert cats['categories'] and cats['counts'] is None
    response = client.get('/api/models/confusion-matrix')
    assert response.content.startswith(b'\x89PNG')
    assert response.headers['cache-control'] == 'no-store'


def test_analysis_demo_and_no_persistence(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = client.post('/api/analyze', data={'resume_text': 'Python SQL developer', 'job_description': 'Python SQL AWS', 'mode': 'demo'})
    assert response.status_code == 200
    result = response.json()
    assert result['mode'] == 'demo' and 'SIMULADA' in result['llm']['resumo']
    assert result['privacy']['stored_permanently'] is False
    assert len(result['ml']['top_categories']) == 3
    assert list(tmp_path.iterdir()) == []


def test_live_unconfigured_preserves_ml(client, caplog):
    response = client.post('/api/analyze', data={'resume_text': 'private-name Python SQL', 'job_description': 'Python', 'mode': 'live'})
    result = response.json()
    assert result['ml'] and result['llm'] is None
    assert result['llm_error'] == 'llm_not_configured'
    assert 'private-name' not in caplog.text


def test_validation_does_not_echo_private_input(client):
    response = client.post('/api/analyze', data={'resume_text': 'private-data', 'job_description': 'Python', 'mode': 'secret-key'})
    assert response.status_code == 422 and 'secret-key' not in response.text
    assert client.post('/api/analyze', data={'job_description': 'Python'}).status_code == 422
    assert client.post('/api/analyze', data={'resume_text': 'Python', 'job_description': ' '}).status_code == 422


def test_file_errors_and_ambiguous_input(client):
    assert client.post('/api/analyze', data={'job_description': 'Python'}, files={'file': ('a.exe', b'xx', 'application/octet-stream')}).status_code == 415
    assert client.post('/api/analyze', data={'job_description': 'Python', 'resume_text': 'SQL'}, files={'file': ('a.txt', b'Python', 'text/plain')}).status_code == 422


def test_model_failure(client, monkeypatch):
    def unavailable():
        raise ServiceError('model_unavailable', 'Modelo indisponível.', 503)
    monkeypatch.setattr(classifier, 'load_model', unavailable)
    response = client.post('/api/analyze', data={'resume_text': 'Python', 'job_description': 'Python'})
    assert response.status_code == 503


def test_openapi_contract(client):
    schema = client.get('/openapi.json').json()
    assert '/api/compare' not in schema['paths']
    assert 'multipart/form-data' in schema['paths']['/api/analyze']['post']['requestBody']['content']
