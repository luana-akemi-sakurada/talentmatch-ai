"""Features de RELAÇÃO entre currículo e vaga (compartilhadas por treino e inferência).

O matching anterior concatenava os dois textos num único TF-IDF e deixava a
regressão logística adivinhar a classe só pelo vocabulário. Aqui medimos a
relação currículo↔vaga explicitamente (similaridade, habilidades em comum, área,
cargo, anos, formação) e o modelo aprende o score a partir desses sinais.
"""
import json
import re
import unicodedata
from dataclasses import dataclass

import numpy as np
from sklearn.preprocessing import normalize

from preprocess import limpar_texto

FEATURES = [
    'cos_tfidf', 'cos_lsa',
    'n_job_skills', 'n_resume_skills', 'n_common_skills', 'skill_recall', 'skill_jaccard',
    'area_dot', 'resume_prob_at_job_area', 'job_area_conf', 'resume_area_conf',
    'title_overlap', 'title_any',
    'resume_years', 'job_years', 'years_gap',
    'resume_edu', 'job_edu', 'edu_gap',
]
FEATURE_LABELS = {
    'cos_tfidf': 'Similaridade lexical (TF-IDF)',
    'cos_lsa': 'Similaridade temática (LSA)',
    'skill_recall': 'Habilidades da vaga encontradas no currículo',
    'skill_jaccard': 'Sobreposição de habilidades',
    'area_dot': 'Concordância de área',
    'title_overlap': 'Termos do cargo no currículo',
    'years_gap': 'Anos de experiência (currículo − vaga)',
    'edu_gap': 'Formação (currículo − vaga)',
}
STOP_TITLE = {'and', 'of', 'the', 'for', 'a', 'an', 'in', 'at', 'to', 'de', 'da', 'do', 'e', 'senior', 'junior', 'jr', 'sr', 'ii', 'iii', 'i'}

EDU_PATTERNS = [
    (4, r'\b(ph\.?d|doctorate|doutorado|doutor)\b'),
    (3, r'\b(master|masters|m\.?sc|mba|mestrado|mestre|m\.?tech|post.?graduate|pos.?graduacao|especializacao)\b'),
    (2, r'\b(bachelor|bachelors|b\.?sc|b\.?tech|b\.?e\.|undergraduate|degree in|graduacao|bacharel|bacharelado|licenciatura|engenharia|superior completo)\b'),
    (1, r'\b(associate|diploma|tecnico|tecnologo|technical school|high school|ensino medio|certificate)\b'),
]
NUMBER_WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                'um': 1, 'dois': 2, 'tres': 3, 'quatro': 4, 'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10}
OPEN_END = r'(?:atual(?:mente)?|presente|present|current(?:ly)?|hoje|now|ate o momento|till date|to date)'


def _plain(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', str(text).casefold()) if not unicodedata.combining(c))


def education_level(raw: str) -> int:
    text = _plain(raw)
    for level, pattern in EDU_PATTERNS:
        if re.search(pattern, text):
            return level
    return 0


def explicit_years(raw: str) -> float:
    """Maior duração citada explicitamente ('5 anos', '3+ years', '5-8 years')."""
    text = _plain(raw)
    values = []
    for m in re.finditer(r'(\d{1,2})\s*\+?\s*(?:-|a|to|ate)?\s*(\d{1,2})?\s*\+?\s*(?:anos?|years?|yrs?)\b', text):
        values.append(float(m.group(1)))
    for m in re.finditer(r'\b(' + '|'.join(NUMBER_WORDS) + r')\s+(?:anos?|years?)\b', text):
        values.append(float(NUMBER_WORDS[m.group(1)]))
    return max([v for v in values if v <= 45], default=float('nan'))


def date_range_years(raw: str, current_year: int = 2026) -> float:
    """Anos cobertos pela união dos períodos 'AAAA – AAAA/atual' do currículo."""
    text = _plain(raw)
    spans = []
    for m in re.finditer(r'\b((?:19|20)\d{2})\s*(?:-|–|—|a|ate|to)\s*((?:19|20)\d{2}|' + OPEN_END + r')', text):
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2)[:2] in ('19', '20') and m.group(2).isdigit() else current_year
        if 1970 <= start <= end <= current_year + 1:
            spans.append((start, end))
    if not spans:
        return float('nan')
    spans.sort()
    total, (cs, ce) = 0, spans[0]
    for s, e in spans[1:]:
        if s <= ce:
            ce = max(ce, e)
        else:
            total, (cs, ce) = total + (ce - cs), (s, e)
    return float(min(total + (ce - cs), 45))


def resume_years(raw: str) -> float:
    values = [v for v in (explicit_years(raw), date_range_years(raw)) if v == v]
    return max(values) if values else float('nan')


def norm_skill(text: str) -> str:
    text = re.sub(r'[^a-zA-ZÀ-ÿ\s+#.]', ' ', str(text).lower())
    return ' '.join(t.strip('.') for t in text.split() if t.strip('.'))


def build_skill_vocabulary(columns, minimum=3):
    from collections import Counter
    counter = Counter()
    for column in columns:
        for value in column:
            try:
                items = json.loads(value) if isinstance(value, str) else []
            except ValueError:
                continue
            counter.update({norm_skill(s) for s in items if norm_skill(s)})
    return {s for s, n in counter.items() if n >= minimum and len(s) >= 2 and len(s.split()) <= 4}


def extract_skills(cleaned: str, vocabulary: set) -> frozenset:
    tokens = [t.strip('.') for t in cleaned.split()]
    tokens = [t for t in tokens if t]
    found = set()
    for n in (1, 2, 3, 4):
        for i in range(len(tokens) - n + 1):
            gram = ' '.join(tokens[i:i + n])
            if gram in vocabulary:
                found.add(gram)
    return frozenset(found)


def title_tokens(title) -> frozenset:
    if not isinstance(title, str):
        return frozenset()
    tokens = {t.strip('.') for t in limpar_texto(title).split()}
    return frozenset(t for t in tokens if t and t not in STOP_TITLE and len(t) > 1)


def guess_title(job_raw: str):
    """Cargo da vaga a partir da primeira linha curta (None se não houver)."""
    for line in str(job_raw).splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'^(?:vaga|cargo|t[ií]tulo(?: da vaga)?|job title|position|title)\s*[:\-–]\s*', '', line, flags=re.I)
        return line if 2 <= len(line) <= 100 else None
    return None


@dataclass
class Docs:
    """Representação vetorizada de N textos (currículos OU vagas)."""
    tfidf: object
    lsa: np.ndarray
    skills: list
    years: np.ndarray
    edu: np.ndarray
    area: np.ndarray
    length: np.ndarray
    titles: list
    words: list


class MatchFeaturizer:
    """Estado ajustado no treino; usado sem alteração na inferência."""

    def __init__(self, vectorizer, svd, skill_vocabulary, resume_area_model, job_area_model):
        if list(resume_area_model.classes_) != list(job_area_model.classes_):
            raise ValueError('Modelos de área do currículo e da vaga precisam das mesmas classes.')
        self.vectorizer = vectorizer
        self.svd = svd
        self.skill_vocabulary = skill_vocabulary
        self.resume_area_model = resume_area_model
        self.job_area_model = job_area_model
        self.feature_names = list(FEATURES)

    def _docs(self, cleaned, raws, years, titles, area) -> Docs:
        x = normalize(self.vectorizer.transform(cleaned))
        lsa = normalize(self.svd.transform(x))
        skills = [extract_skills(c, self.skill_vocabulary) for c in cleaned]
        edu = np.array([education_level(r) for r in raws], dtype=float)
        length = np.log1p(np.array([len(c) for c in cleaned], dtype=float))
        words = [frozenset(t.strip('.') for t in c.split()) for c in cleaned]
        return Docs(x, lsa, skills, np.asarray(years, dtype=float), edu, np.asarray(area, dtype=float), length, titles, words)

    def resume_docs(self, cleaned, raws, years=None, area=None) -> Docs:
        if years is None:
            years = [resume_years(r) for r in raws]
        if area is None:
            area = self.resume_area_model.predict_proba(cleaned)
        return self._docs(cleaned, raws, years, [frozenset()] * len(cleaned), area)

    def job_docs(self, cleaned, raws, years=None, titles=None, area=None) -> Docs:
        if years is None:
            years = [explicit_years(r) for r in raws]
        if titles is None:
            titles = [title_tokens(guess_title(r)) for r in raws]
        if area is None:
            area = self.job_area_model.predict_proba(cleaned)
        return self._docs(cleaned, raws, years, titles, area)

    def pair_matrix(self, R: Docs, J: Docs, ri, ji, title_dropout=0.0, seed=0) -> np.ndarray:
        ri, ji = np.asarray(ri), np.asarray(ji)
        n = len(ri)
        cos_tfidf = np.asarray(R.tfidf[ri].multiply(J.tfidf[ji]).sum(axis=1)).ravel()
        cos_lsa = np.einsum('ij,ij->i', R.lsa[ri], J.lsa[ji])
        nj, nr, nc = np.zeros(n), np.zeros(n), np.zeros(n)
        overlap, any_ = np.full(n, np.nan), np.full(n, np.nan)
        rng = np.random.default_rng(seed)
        for k, (a, b) in enumerate(zip(ri, ji)):
            rs, js = R.skills[a], J.skills[b]
            nj[k], nr[k], nc[k] = len(js), len(rs), len(rs & js)
            tokens = J.titles[b]
            # Em produção o cargo pode não ser identificável; o treino simula isso.
            if tokens and not (title_dropout and rng.random() < title_dropout):
                hit = len(tokens & R.words[a])
                overlap[k], any_[k] = hit / len(tokens), float(hit > 0)
        recall = np.divide(nc, nj, out=np.full(n, np.nan), where=nj > 0)
        union = nj + nr - nc
        jaccard = np.divide(nc, union, out=np.zeros(n), where=union > 0)
        pr, pj = R.area[ri], J.area[ji]
        area_dot = np.einsum('ij,ij->i', pr, pj)
        p_at = pr[np.arange(n), pj.argmax(axis=1)]
        ry, jy = R.years[ri], J.years[ji]
        columns = [cos_tfidf, cos_lsa, nj, nr, nc, recall, jaccard, area_dot, p_at, pj.max(axis=1), pr.max(axis=1),
                   overlap, any_, ry, jy, ry - jy, R.edu[ri], J.edu[ji], R.edu[ri] - J.edu[ji]]
        return np.column_stack(columns)


CLASS_NAMES = ('compatibilidade_fraca', 'compatibilidade_media', 'compatibilidade_forte')
THRESHOLDS = (0.58, 0.68)  # cortes do dataset: fraco < 0,58 <= médio < 0,68 <= forte

SIGNAL_GROUPS = {
    'Similaridade textual': ['cos_tfidf', 'cos_lsa'],
    'Habilidades em comum': ['n_job_skills', 'n_resume_skills', 'n_common_skills', 'skill_recall', 'skill_jaccard'],
    'Área profissional': ['area_dot', 'resume_prob_at_job_area', 'job_area_conf', 'resume_area_conf'],
    'Cargo da vaga': ['title_overlap', 'title_any'],
    'Anos de experiência': ['resume_years', 'job_years', 'years_gap'],
    'Formação': ['resume_edu', 'job_edu', 'edu_gap'],
}


class MatchModel:
    """Regressor do score de matching + distribuição empírica dos resíduos.

    As probabilidades de faixa NÃO vêm de um classificador: são a fração dos
    resíduos de calibração (currículos e vagas inéditos) que colocariam o score
    previsto em cada faixa. Assim o score, a faixa e a incerteza são coerentes.
    """

    def __init__(self, featurizer, regressor, residuals, medians):
        self.featurizer = featurizer
        self.regressor = regressor
        self.residuals = np.sort(np.asarray(residuals, dtype=float))
        self.medians = np.asarray(medians, dtype=float)
        self.classes_ = np.array(CLASS_NAMES)

    def class_probabilities(self, scores) -> np.ndarray:
        scores = np.atleast_1d(np.asarray(scores, dtype=float))
        n = len(self.residuals)
        weak = np.searchsorted(self.residuals, THRESHOLDS[0] - scores, side='left') / n
        not_strong = np.searchsorted(self.residuals, THRESHOLDS[1] - scores, side='left') / n
        probs = np.column_stack([weak, not_strong - weak, 1 - not_strong])
        return np.clip(probs, 0, 1)

    def interval(self, score: float, level: float = 0.8):
        low, high = np.quantile(self.residuals, [(1 - level) / 2, 1 - (1 - level) / 2])
        return float(score + low), float(score + high)

    def predict_pair(self, resume_clean, resume_raw, job_clean, job_raw) -> dict:
        f = self.featurizer
        R = f.resume_docs([resume_clean], [resume_raw])
        J = f.job_docs([job_clean], [job_raw])
        x = f.pair_matrix(R, J, [0], [0])
        score = float(self.regressor.predict(x)[0])
        probs = self.class_probabilities(score)[0]
        names = f.feature_names
        contributions = []
        for label, members in SIGNAL_GROUPS.items():
            occluded = x.copy()
            for name in members:
                occluded[0, names.index(name)] = self.medians[names.index(name)]
            contributions.append({'sinal': label, 'contribuicao': score - float(self.regressor.predict(occluded)[0])})
        values = dict(zip(names, x[0].tolist()))
        return {'score': score, 'probabilidades': probs, 'intervalo': self.interval(score), 'contribuicoes': contributions,
                'valores': {k: (None if v != v else v) for k, v in values.items()},
                'habilidades_em_comum': sorted(R.skills[0] & J.skills[0]),
                'habilidades_da_vaga_ausentes': sorted(J.skills[0] - R.skills[0])}
