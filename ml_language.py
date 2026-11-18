"""Local PT->EN ML normalization, never used as original evidence."""
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


def token_chunks(ids, size):
    if size < 1:
        raise ValueError('Limite de tokens inválido.')
    for start in range(0, len(ids), size):
        yield ids[start:start + size]


def translation_inputs(tokenizer, chunk, device, maximum):
    import torch
    prepared = tokenizer.build_inputs_with_special_tokens(chunk)
    if not prepared or len(prepared) > maximum:
        raise ValueError('Bloco de tradução excede o limite de entrada.')
    # Explicit batch dimension: [1, sequence_length], not [sequence_length].
    input_ids = torch.tensor([prepared], dtype=torch.long, device=device)
    return {'input_ids': input_ids, 'attention_mask': torch.ones_like(input_ids)}


def translate_portuguese(text: str) -> str:
    if not text.strip():
        return text
    import torch
    with LOCK:
        tokenizer, model = _translator()
        maximum = min(int(getattr(model.config, 'max_position_embeddings', 512)), 512)
        special = tokenizer.num_special_tokens_to_add(pair=False)
        budget = min(496, maximum - special)
        if budget < 1 or maximum < 4:
            raise ValueError('Configuração de tamanho do tradutor inválida.')
        # Obtain all IDs, then split BEFORE sending any tensor to the model.
        # verbose=False avoids a misleading whole-document length warning.
        ids = tokenizer.encode(text, add_special_tokens=False, truncation=False, verbose=False)
        output = []
        max_output = maximum - 1
        for chunk in token_chunks(ids, budget):
            inputs = translation_inputs(tokenizer, chunk, model.device, maximum)
            with torch.inference_mode():
                generated = model.generate(**inputs, num_beams=4, do_sample=False, max_new_tokens=max_output)
            tokens = generated[0].tolist()
            eos = model.config.eos_token_id
            end_ids = set(eos) if isinstance(eos, (list, tuple)) else {eos}
            # A forced EOS at the length cap is not proof of complete translation.
            if len(tokens) >= max_output + 1 or not any(t in end_ids for t in tokens[1:]):
                raise RuntimeError('Tradução atingiu o limite de saída. Nenhuma previsão foi emitida; reduza o documento.')
            value = tokenizer.decode(tokens, skip_special_tokens=True).strip()
            if not value:
                raise RuntimeError('Tradução vazia. Não foi emitida previsão ML.')
            output.append(value)
        if not output:
            raise RuntimeError('Nenhum token utilizável para tradução.')
        return '\n'.join(output)


def to_english(text: str) -> str:
    if not text.strip():
        return text
    return translate_portuguese(text) if identify(text) == 'pt' else text


if __name__ == '__main__':
    _translator()
    print(f'Modelo de tradução disponível localmente: {MODEL}')
