"""Explicit opt-in HTTP verification against a running LOCAL stand-in only.

Not a pytest module. Run after `postman simulation run ... --port 4010`.
Never loads real credentials and never targets the configured external provider.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import llm
from backend.app.core.errors import ServiceError

os.environ['LLM_API_KEY'] = 'local-test-placeholder'
os.environ['LLM_BASE_URL'] = 'http://127.0.0.1:4010/llm/v1'

for model, expected in [('test-success', None), ('test-invalid', 'invalid_llm_response'),
                        ('test-unavailable', 'llm_unavailable')]:
    os.environ['LLM_MODEL'] = model
    try:
        response = llm.analisar('Nome: Pessoa Fictícia\nPython SQL', 'Python SQL', 'IT', .4)
        assert expected is None and response['nota_aderencia'] is None
        assert response['abstention_reason'] == 'score_not_validated'
        print(model, 'validated')
    except ServiceError as error:
        assert error.code == expected, (model, error.code)
        print(model, error.code)
