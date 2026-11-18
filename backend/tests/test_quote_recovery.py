import pytest
from backend.app.core.errors import ServiceError
from backend.app.services.grounding import resolve_quote, quote


def test_unique_excerpt_returns_full_original():
    source = {'Desenvolvo interfaces com React.'}
    assert resolve_quote('interfaces com React', source) == 'Desenvolvo interfaces com React.'


def test_whitespace_only_preserves_original():
    source = {'Desenvolvo  interfaces com React.'}
    assert resolve_quote('Desenvolvo interfaces com React.', source) in source


def test_ambiguous_excerpt_not_completed():
    source = {'Uso React no trabalho.', 'Estudo React na faculdade.'}
    resolved = resolve_quote('React', source)
    assert resolved == 'React'
    with pytest.raises(ServiceError):
        quote(resolved, source)


def test_negation_not_hidden_by_completion():
    source = {'Não tenho experiência com React.'}
    resolved = resolve_quote('experiência com React', source)
    assert resolved == 'Não tenho experiência com React.'
    with pytest.raises(ServiceError):
        quote(resolved, source)


def test_invented_text_rejected():
    source = {'Desenvolvo interfaces com React.'}
    with pytest.raises(ServiceError):
        quote(resolve_quote('Desenvolvo com Kubernetes.', source), source)


def test_no_word_fragment_or_translation():
    source = {'Uso JavaScript.', 'Desenvolvimento de software.'}
    assert resolve_quote('Java', source) == 'Java'
    assert resolve_quote('Software development', source) == 'Software development'
