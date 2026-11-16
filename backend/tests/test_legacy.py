"""Optional compatibility checks when root requirements are installed."""
import pytest

streamlit = pytest.importorskip('streamlit')
from streamlit.testing.v1 import AppTest
from backend.app.core.config import ROOT


def test_original_streamlit_startup():
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
    assert not app.exception
    assert app.title[0].value == 'Analise Inteligente de Curriculos'
    assert len(app.checkbox) == 1


def test_original_streamlit_missing_authorization():
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
    app.button[0].click().run()
    assert not app.exception
    assert 'autorização' in app.error[0].value


def test_streamlit_handles_score_abstention_and_empty_ml(monkeypatch):
    import llm
    from backend.app.schemas.analysis import GroundedLLMResponse
    from backend.app.services.grounding import ground
    draft = GroundedLLMResponse(habilidades=[], experiencia_profissional=[], anos_experiencia=None,
        evidencia_anos_experiencia=None, requisitos_atendidos=[], requisitos_sem_evidencia=['Python'])
    calls = []
    def fake(resume, job, area, confidence):
        calls.append((area, confidence))
        return ground(draft, resume, job, False).model_dump()
    monkeypatch.setattr(llm, 'analisar', fake)
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=20)
    app.text_area[0].set_value('zzqxv zzqxv')
    app.text_area[1].set_value('Python')
    app.checkbox[0].check()
    app.button[0].click().run()
    assert not app.exception
    assert calls == [(None, None)]
    assert any('Abstenção de pontuação' in item.value for item in app.info)
    assert not any('Perguntas' in item.value for item in app.markdown)
