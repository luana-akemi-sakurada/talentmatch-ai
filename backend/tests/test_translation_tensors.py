from types import SimpleNamespace
from unittest.mock import patch
import pytest
from ml_language import token_chunks, translation_inputs, translate_portuguese


def test_all_694_tokens_preserved_in_bounded_chunks():
    ids = list(range(694))
    blocks = list(token_chunks(ids, 496))
    assert [len(b) for b in blocks] == [496, 198]
    assert [token for b in blocks for token in b] == ids


class FakeTokenizer:
    def build_inputs_with_special_tokens(self, ids):
        return list(ids) + [0]
    def num_special_tokens_to_add(self, pair=False):
        return 1
    def encode(self, text, **kwargs):
        assert kwargs.get('truncation') is False
        return list(range(694))
    def decode(self, tokens, **kwargs):
        return 'translated block'


def test_input_and_mask_have_explicit_batch_dimension():
    torch = pytest.importorskip('torch')
    inputs = translation_inputs(FakeTokenizer(), [1, 2, 3], 'cpu', 512)
    assert tuple(inputs['input_ids'].shape) == (1, 4)
    assert inputs['input_ids'].dtype == torch.long
    assert inputs['attention_mask'].shape == inputs['input_ids'].shape


def test_oversized_prepared_input_rejected():
    pytest.importorskip('torch')
    with pytest.raises(ValueError):
        translation_inputs(FakeTokenizer(), list(range(512)), 'cpu', 512)


def test_generation_processes_both_chunks_without_download():
    torch = pytest.importorskip('torch')
    calls = []
    class FakeModel:
        device = 'cpu'
        config = SimpleNamespace(max_position_embeddings=512, eos_token_id=0)
        def generate(self, input_ids, attention_mask, **kwargs):
            assert input_ids.ndim == 2
            assert attention_mask.shape == input_ids.shape
            assert input_ids.shape[1] <= 512
            calls.append(input_ids.shape[1])
            return torch.tensor([[9, 8, 0]])
    with patch('ml_language._translator', return_value=(FakeTokenizer(), FakeModel())):
        assert translate_portuguese('texto de teste') == 'translated block\ntranslated block'
    assert calls == [497, 199]


def test_forced_end_at_output_limit_is_not_accepted():
    torch = pytest.importorskip('torch')
    class FakeModel:
        device = 'cpu'
        config = SimpleNamespace(max_position_embeddings=512, eos_token_id=0)
        def generate(self, **kwargs):
            return torch.tensor([[9] * 511 + [0]])
    with patch('ml_language._translator', return_value=(FakeTokenizer(), FakeModel())):
        with pytest.raises(RuntimeError):
            translate_portuguese('texto de teste')
