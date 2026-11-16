"""Offline diagnostics only: no fit(), provider calls or writes to models/.

Run from any directory: .venv/Scripts/python.exe scripts/avaliar_modelo.py
Inputs are frozen in model_cases.json. All outputs are synthetic-case observations,
not an estimate of population accuracy. Existing experiment artifacts stay intact.
"""
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sklearn
from scipy.sparse import csr_matrix
from backend.app.services.classifier import load_model, predict
from backend.app.services.privacy import minimize
from backend.app.services.analysis import demo_analysis
from preprocess import limpar_texto

OUT = ROOT / 'docs/avaliacao-modelo'
INPUT = Path(__file__).with_name('model_cases.json')


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / 'models').rglob('*')) if path.is_file()}


def percent(value):
    return f'{100 * value:.2f}%'.replace('.', ',')


def main():
    before = hashes()
    fixture = json.loads(INPUT.read_text(encoding='utf-8'))
    model = load_model()
    tfidf, forest = model.named_steps['tfidf'], model.named_steps['clf']
    labels = [str(label) for label in model.classes_]
    analyzer = tfidf.build_analyzer()
    feature_names = tfidf.get_feature_names_out()
    zero = csr_matrix((1, forest.n_features_in_))
    zero_leaves = forest.apply(zero)[0]

    def inspect(case, control=False):
        raw = case['text']
        minimized, redactions = minimize(raw, resume=True)
        cleaned = limpar_texto(minimized)
        vector = tfidf.transform([cleaned])
        probability = forest.predict_proba(vector)[0]
        full = dict(zip(labels, map(float, probability)))
        ranking = sorted(full.items(), key=lambda item: item[1], reverse=True)
        unigrams = {term for term in analyzer(cleaned) if ' ' not in term}
        known = unigrams & tfidf.vocabulary_.keys()
        active = sorted(zip(vector.indices, vector.data), key=lambda pair: -pair[1])
        raw_probability = model.predict_proba([raw])[0]
        cleaned_probability = model.predict_proba([limpar_texto(raw)])[0]
        if not control:
            endpoint_prediction = predict(minimized)
            assert endpoint_prediction.predicted_area == ranking[0][0]
            assert np.allclose([p.probability for p in endpoint_prediction.top_categories], [p for _, p in ranking[:3]])
        return {**case, 'control': control, 'words': len(raw.split()), 'characters': len(raw),
                'minimized_text': minimized, 'cleaned_text_at_tfidf': cleaned,
                'redactions': redactions, 'prediction': ranking[0][0],
                'top3': [{'category': category, 'probability': value} for category, value in ranking[:3]],
                'expected_probability': full.get(case['expected']),
                'it_probability': full['INFORMATION-TECHNOLOGY'],
                'probabilities': full, 'active_features': int(vector.nnz),
                'analyzed_unique_unigrams': len(unigrams), 'known_unique_unigrams': len(known),
                'unigram_coverage': len(known) / len(unigrams) if unigrams else None,
                'unknown_unigrams': sorted(unigrams - tfidf.vocabulary_.keys()),
                'all_active_tfidf': [{'feature': str(feature_names[index]), 'weight': float(weight)} for index, weight in active],
                'trees_with_different_leaf_vs_zero': int(np.count_nonzero(forest.apply(vector)[0] != zero_leaves)),
                'raw_vs_clean_probability_l1': float(np.abs(raw_probability - cleaned_probability).sum()),
                'clean_vs_minimized_probability_l1': float(np.abs(cleaned_probability - probability).sum())}

    results = [inspect(case) for case in fixture['cases']]
    controls = []
    for language in ('pt', 'en'):
        case = next(c for c in fixture['cases'] if c['id'] == f'software-short-{language}')
        controls.append(inspect({**case, 'id': f'software-repeated8-{language}',
                                 'detail': 'repeat8', 'text': '\n'.join([case['text']] * 8)}, control=True))
    for identifier, text in [('zero-oov', 'zzqxv zzqxv'), ('zero-stopwords', 'the and or the and')]:
        controls.append(inspect({'id': identifier, 'area': 'control', 'language': 'n/a',
                                 'detail': 'none', 'expected': None, 'text': text}, control=True))
    controls.append(inspect({'id': 'technical-terms-only', 'area': 'software', 'language': 'n/a',
        'detail': 'keywords', 'expected': 'INFORMATION-TECHNOLOGY',
        'text': 'Java, Spring Boot, PostgreSQL, APIs REST, Git, JUnit, Docker.'}, control=True))

    root_proportions = np.array([tree.tree_.value[0, 0] / tree.tree_.value[0, 0].sum() for tree in forest.estimators_])
    terms = ['Java', 'Spring Boot', 'PostgreSQL', 'APIs REST', 'Git', 'JUnit', 'Docker',
             'C++', 'C#', '.NET', 'dois anos', 'two years', '2 years']
    probes = []
    for term in terms:
        cleaned = limpar_texto(term)
        tokens = analyzer(cleaned)
        probes.append({'term': term, 'cleaned': cleaned, 'analyzed_terms': tokens,
                       'known_terms': [t for t in tokens if t in tfidf.vocabulary_],
                       'missing_terms': [t for t in tokens if t not in tfidf.vocabulary_]})
    top_importance = np.argsort(forest.feature_importances_)[::-1][:20]
    after = hashes()
    assert before == after, 'Original artifacts changed during read-only diagnostics'
    output = {'method': fixture['notice'], 'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
              'python': platform.python_version(), 'sklearn': sklearn.__version__,
              'model_type': type(forest).__name__, 'n_classes': len(labels), 'n_estimators': len(forest.estimators_),
              'vectorizer': {k: tfidf.get_params()[k] for k in ['max_features', 'ngram_range', 'stop_words', 'sublinear_tf', 'token_pattern', 'norm']},
              'vocabulary_size': len(tfidf.vocabulary_), 'class_weight': forest.class_weight,
              'dataset_present': (ROOT / 'data/Resume.csv').exists(),
              'training_rows_internal': getattr(forest, '_n_samples', None),
              'bootstrap_root_proportions_mean': dict(zip(labels, map(float, root_proportions.mean(axis=0)))),
              'root_weighted_samples': sorted({float(t.tree_.weighted_n_node_samples[0]) for t in forest.estimators_}),
              'global_impurity_importance_top20': [{'feature': str(feature_names[i]), 'importance': float(forest.feature_importances_[i])} for i in top_importance],
              'technical_term_probes': probes, 'job': fixture['job'],
              'original_demo_result': demo_analysis(results[0]['minimized_text'], fixture['job']).model_dump(),
              'results': results, 'controls': controls, 'original_hashes_before': before, 'original_hashes_after': after}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'resultados.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    with (OUT / 'resultados.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id', 'control', 'language', 'detail', 'words', 'expected', 'prediction', 'expected_probability', 'it_probability', 'active_features', 'unigram_coverage', 'top1', 'p1', 'top2', 'p2', 'top3', 'p3'])
        for r in results + controls:
            writer.writerow([r[k] for k in ['id', 'control', 'language', 'detail', 'words', 'expected', 'prediction', 'expected_probability', 'it_probability', 'active_features', 'unigram_coverage']]
                            + [value for item in r['top3'] for value in (item['category'], item['probability'])])
    lines = ['# Entradas e resultados completos', '', 'Gerado por scripts/avaliar_modelo.py. Exemplos sintéticos; não constituem avaliação representativa.', '',
             '| ID | Palavras | Esperada | Prevista | P(esperada) | Top 3 | Atributos ativos |', '|---|---:|---|---|---:|---|---:|']
    for r in results + controls:
        top = '; '.join(f"{item['category']} {percent(item['probability'])}" for item in r['top3'])
        p_expected = percent(r['expected_probability']) if r['expected_probability'] is not None else 'n/a'
        lines.append(f"| {r['id']} | {r['words']} | {r['expected'] or 'sem rótulo'} | {r['prediction']} | {p_expected} | {top} | {r['active_features']} |")
    for r in results + controls:
        lines.extend(['', f"## {r['id']}", '', '**Entrada fictícia:**', '', r['text'], '', '**Texto efetivamente entregue ao TF-IDF:**', '', r['cleaned_text_at_tfidf'], '',
                      f"Minimização: {r['redactions']} remoções. Cobertura de unigramas únicos: {r['known_unique_unigrams']}/{r['analyzed_unique_unigrams']}. Atributos não nulos (unigramas e bigramas): {r['active_features']}."])
    (OUT / 'entradas-resultados.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    plot(results, controls)
    for r in results + controls:
        print(r['id'], r['words'], r['prediction'], percent(r['top3'][0]['probability']), 'P(expected)=', r['expected_probability'], 'active=', r['active_features'])
    print('Artifacts unchanged:', before == after, 'Output:', OUT)


def plot(results, controls):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False,
                         'axes.spines.right': False, 'figure.facecolor': 'white', 'axes.axisbelow': True})
    colors = {'pt': '#287c63', 'en': '#5267a0'}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7), layout='constrained')
    lengths = ['short', 'medium', 'long']
    names = ['Curto', 'Médio', 'Longo']
    for ax, key, title in zip(axes, ['it_probability', 'active_features'], ['Probabilidade atribuída a Information Technology', 'Atributos TF-IDF não nulos']):
        for offset, language in [(-.2, 'pt'), (.2, 'en')]:
            group = [next(r for r in results if r['area'] == 'software' and r['detail'] == size and r['language'] == language) for size in lengths]
            values = [(100 if key == 'it_probability' else 1) * r[key] for r in group]
            bars = ax.bar(np.arange(3) + offset, values, .36, color=colors[language], label=language.upper())
            ax.bar_label(bars, labels=[f'{v:.2f}%' if key == 'it_probability' else str(int(v)) for v in values], fontsize=9, padding=3)
        ax.set_xticks(range(3), names); ax.set_title(title, fontsize=12); ax.grid(axis='y', alpha=.2)
        ax.set_ylim(0, 100 if key == 'it_probability' else max(r['active_features'] for r in results if r['area'] == 'software') * 1.2)
        ax.set_ylabel('Saída do classificador (%)' if key == 'it_probability' else 'Contagem por documento'); ax.legend()
    fig.suptitle('Diagnóstico sintético: idioma e detalhamento, mesmas competências', fontsize=14)
    fig.savefig(OUT / 'idioma-detalhamento.png', dpi=180)
    fig.savefig(OUT / 'idioma-detalhamento.svg'); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
    areas = ['software', 'hr', 'finance', 'health', 'sales']
    for offset, language in [(-.2, 'pt'), (.2, 'en')]:
        group = [next(r for r in results if r['area'] == area and r['detail'] == 'medium' and r['language'] == language) for area in areas]
        values = [100 * r['expected_probability'] for r in group]
        bars = ax.bar(np.arange(5) + offset, values, .36, color=colors[language], label=language.upper())
        ax.bar_label(bars, labels=[f'{v:.2f}%' for v in values], fontsize=9, padding=3)
    ax.set_xticks(range(5), ['Software / IT', 'RH / HR', 'Finanças / FINANCE', 'Saúde / HEALTHCARE', 'Vendas / SALES'])
    ax.set_ylim(0, 100); ax.set_ylabel('Probabilidade da categoria esperada (%)'); ax.grid(axis='y', alpha=.2); ax.legend()
    ax.set_title('Cinco pares sintéticos: probabilidade da categoria esperada\nNão é acurácia populacional ou taxa de contratação', fontsize=13)
    fig.savefig(OUT / 'areas-idiomas.png', dpi=180); fig.savefig(OUT / 'areas-idiomas.svg'); plt.close(fig)

    chosen = [next(r for r in results if r['id'] == f'software-short-{lang}') for lang in ('pt', 'en')]
    chosen += [next(r for r in controls if r['id'] == f'software-repeated8-{lang}') for lang in ('pt', 'en')]
    chosen += [next(r for r in controls if r['id'] == 'zero-oov')]
    fig, ax = plt.subplots(figsize=(10, 4.5), layout='constrained')
    x = np.arange(len(chosen))
    for offset, category, color in [(-.2, 'BUSINESS-DEVELOPMENT', '#b47b35'), (.2, 'INFORMATION-TECHNOLOGY', '#5267a0')]:
        values = [100 * r['probabilities'][category] for r in chosen]
        bars = ax.bar(x + offset, values, .36, label=category, color=color)
        ax.bar_label(bars, labels=[f'{v:.2f}%' for v in values], fontsize=9, padding=3)
    ax.set_xticks(x, ['Curto PT', 'Curto EN', 'Repetido 8× PT', 'Repetido 8× EN', 'Vetor zero / OOV'])
    ax.set_ylim(0, 100); ax.set_ylabel('Saída do classificador (%)'); ax.grid(axis='y', alpha=.2); ax.legend()
    ax.set_title('Controles: repetição não acrescenta experiência; OOV não é currículo válido', fontsize=12)
    fig.savefig(OUT / 'controles.png', dpi=180); fig.savefig(OUT / 'controles.svg'); plt.close(fig)


if __name__ == '__main__':
    main()
