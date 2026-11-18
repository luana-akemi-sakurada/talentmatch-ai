"""Local PT->EN normalization for the English ML baseline.
Not used for LLM evidence. No document/result cache and no translation API.
Language detection is heuristic, restricted to the supported pair PT/EN.
"""
import os
import re
from functools import lru_cache
from threading import RLock

MODEL = 'Helsinki-NLP/opus-mt-ROMANCE-en'
LOCK = RLock()


@lru_cache(maxsize=1)
def _identifier():
    from langid.langid import LanguageIdentifier, model
    identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
    identifier.set_languages(['en', 'pt'])
    return identifier


def identify(text: str) -> str:
    # Short technical terms are left intact to avoid translating product names.
    if len(re.findall(r'[^\W\d_]+', text, flags=re.UNICODE)) < 4:
        return 'und'
    with LOCK:
        language, _ = _identifier().classify(text)
    return language


@lru_cache(maxsize=1)
def _translator():
    from transformers import MarianMTModel, MarianTokenizer
    offline = os.getenv('HF_HUB_OFFLINE', '').lower() in {'1', 'true'}
    tokenizer = MarianTokenizer.from_pretrained(MODEL, local_files_only=offline)
    model = MarianMTModel.from_pretrained(MODEL, local_files_only=offline)
    model.eval()
    return tokenizer, model


def translate_portuguese(text: str) -> str:
    import torch
    with LOCK:
        tokenizer, model = _translator()
        # Token chunks prevent silently dropping the end of a long curriculum.
        ids = tokenizer.encode(text, add_special_tokens=False)
        limit = min(int(getattr(model.config, 'max_position_embeddings', 512)), 512) - 16
        output = []
        for start in range(0, len(ids), limit):
            chunk = ids[start:start + limit]
            inputs = tokenizer.prepare_for_model(chunk, add_special_tokens=True, return_tensors='pt', return_attention_mask=True)
            with torch.inference_mode():
                generated = model.generate(**inputs, num_beams=4, do_sample=False, max_new_tokens=512)
            tokens = generated[0].tolist()
            eos = model.config.eos_token_id
            if eos is not None and eos not in tokens:
                raise RuntimeError('Tradução incompleta. Reduza o documento; o ML não utilizará uma tradução truncada.')
            value = tokenizer.decode(tokens, skip_special_tokens=True).strip()
            if not value:
                raise RuntimeError('Tradução vazia. Não foi emitida previsão ML.')
            output.append(value)
        return '\n'.join(output)


def to_english(text: str) -> str:
    if not text.strip():
        return text
    return translate_portuguese(text) if identify(text) == 'pt' else text


if __name__ == '__main__':
    # Downloads weights only, without processing any personal document.
    _translator()
    print(f'Modelo de tradução disponível localmente: {MODEL}')
