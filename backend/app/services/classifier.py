from functools import lru_cache
import logging

import joblib
import numpy as np
from sklearn.preprocessing import normalize

from preprocess import limpar_texto
from backend.app.core.config import MODEL_DIR
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import MLResult, CategoryProbability, MLCoverage

logger = logging.getLogger("talentmatch.classifier")

ROTULOS_COMPATIBILIDADE = {
    "compatibilidade_fraca": "Fraca",
    "compatibilidade_media": "Média",
    "compatibilidade_forte": "Forte",
}


@lru_cache(maxsize=1)
def _load_artifacts():
    try:
        modelo_area = joblib.load(MODEL_DIR / "classificador_area.joblib")
        metadata_area = joblib.load(MODEL_DIR / "ml_metadata_area.joblib")
        modelo_match = joblib.load(
            MODEL_DIR / "classificador_compatibilidade.joblib"
        )
        metadata_match = joblib.load(
            MODEL_DIR / "ml_metadata_compatibilidade.joblib"
        )

        if not hasattr(modelo_area, "predict_proba"):
            raise ValueError("Classificador de área inválido.")

        if not hasattr(modelo_match, "predict_proba"):
            raise ValueError("Classificador de compatibilidade inválido.")

        campos = {"classes", "class_centroids", "ood_threshold"}

        if not campos.issubset(metadata_area):
            raise ValueError("Metadados do classificador de área incompletos.")

        return modelo_area, metadata_area, modelo_match, metadata_match

    except Exception:
        raise ServiceError(
            "model_unavailable",
            (
                "Classificadores indisponíveis. Execute python train.py para gerar "
                "os quatro arquivos necessários em models/."
            ),
            503,
        ) from None


def load_model():
    modelo_area, _, _, _ = _load_artifacts()
    return modelo_area


def _vetor_normalizado(vetorizador, texto: str):
    vetor = vetorizador.transform([texto])
    return vetor, normalize(vetor)


def _incerteza(probabilidades):
    probabilidades = np.asarray(probabilidades, dtype=float)
    probabilidades = probabilidades / probabilidades.sum()

    ordenadas = np.sort(probabilidades)[::-1]
    probabilidade_top1 = float(ordenadas[0])
    probabilidade_top2 = (
        float(ordenadas[1]) if len(ordenadas) > 1 else 0.0
    )

    margem = probabilidade_top1 - probabilidade_top2

    valores = probabilidades[probabilidades > 0]
    entropia = float(-(valores * np.log(valores)).sum())
    entropia_maxima = (
        float(np.log(len(probabilidades))) if len(probabilidades) > 1 else 1.0
    )
    entropia_normalizada = (
        entropia / entropia_maxima if entropia_maxima > 0 else 0.0
    )

    return {
        "probabilidade_top1": probabilidade_top1,
        "probabilidade_top2": probabilidade_top2,
        "margem_top1_top2": float(margem),
        "entropia_normalizada": entropia_normalizada,
    }


def _nivel_confianca(margem, entropia_normalizada):
    if margem >= 0.30 and entropia_normalizada <= 0.50:
        return "alta"

    if margem >= 0.10 and entropia_normalizada <= 0.75:
        return "media"

    return "baixa"


def predict(text: str) -> MLResult:
    modelo_area, metadata_area, _, _ = _load_artifacts()
    texto_limpo = limpar_texto(text)

    try:
        vetorizador = modelo_area.calibrated_classifiers_[0].estimator.named_steps["tfidf"]
        classificador = modelo_area.calibrated_classifiers_[0].estimator.named_steps["clf"]

        features, features_normalizadas = _vetor_normalizado(
            vetorizador,
            texto_limpo,
        )

        unigramas = {
            termo
            for termo in vetorizador.build_analyzer()(texto_limpo)
            if " " not in termo
        }
        conhecidos = len(unigramas & vetorizador.vocabulary_.keys())
        total = len(unigramas)

        coverage = MLCoverage(
            active_features=features.nnz,
            analyzed_unigrams=total,
            known_unigrams=conhecidos,
            unknown_unigrams=total - conhecidos,
            unigram_coverage=conhecidos / total if total else None,
            zero_vector=features.nnz == 0,
        )

        if coverage.zero_vector:
            return MLResult(
                predicted_area="INDETERMINADA",
                model_name=type(classificador).__name__,
                top_categories=[],
                status="abstained",
                coverage=coverage,
                warnings=[
                    "Abstenção ML: o TF-IDF gerou um vetor vazio. "
                    "Nenhuma categoria ou probabilidade foi emitida."
                ],
            )

        probabilidades = modelo_area.predict_proba(features)[0]
        ordenados = sorted(
            zip(modelo_area.classes_, probabilidades),
            key=lambda par: par[1],
            reverse=True,
        )[:3]

        incerteza = _incerteza(probabilidades)

        classes = metadata_area["classes"]
        centroides = np.vstack(
            [metadata_area["class_centroids"][categoria] for categoria in classes]
        )
        similaridades = features_normalizadas @ centroides.T
        similaridade_maxima = float(np.max(similaridades))
        classe_mais_proxima = classes[int(np.argmax(similaridades))]
        limiar_ood = float(metadata_area["ood_threshold"])
        possivel_ood = similaridade_maxima < limiar_ood

        nivel_confianca = (
            "baixa"
            if possivel_ood
            else _nivel_confianca(
                incerteza["margem_top1_top2"],
                incerteza["entropia_normalizada"],
            )
        )

        avisos = []

        if conhecidos < total:
            avisos.append(
                f"Cobertura lexical TF-IDF: {conhecidos}/{total} unigramas únicos "
                f"reconhecidos ({100 * conhecidos / total:.2f}%). "
                f"{total - conhecidos} termos foram ignorados."
            )

        if possivel_ood:
            avisos.append(
                "Possível texto fora da distribuição de treino: similaridade máxima "
                f"ao centróide ({similaridade_maxima:.4f}) abaixo do limiar "
                f"validado ({limiar_ood:.4f})."
            )

        if nivel_confianca == "baixa":
            avisos.append(
                "Baixa confiança estatística: margem pequena entre as classes "
                "mais prováveis ou entropia alta."
            )

        return MLResult(
            predicted_area=str(ordenados[0][0]),
            model_name=type(classificador).__name__,
            top_categories=[
                CategoryProbability(
                    category=str(categoria),
                    probability=float(probabilidade),
                )
                for categoria, probabilidade in ordenados
            ],
            coverage=coverage,
            warnings=avisos,
        )

    except Exception:
        raise ServiceError(
            "prediction_failed",
            "Não foi possível executar a classificação.",
            503,
        ) from None


def _prever_compatibilidade(texto_curriculo: str, texto_vaga: str) -> dict:
    _, _, modelo_match, _ = _load_artifacts()
    texto_combinado = (
        limpar_texto(texto_curriculo)
        + " [SEP] "
        + limpar_texto(texto_vaga)
    )

    probabilidades = modelo_match.predict_proba([texto_combinado])[0]
    ordenados = sorted(
        zip(modelo_match.classes_, probabilidades),
        key=lambda par: par[1],
        reverse=True,
    )

    incerteza = _incerteza(probabilidades)

    return {
        "disponivel": True,
        "compatibilidade_prevista": ROTULOS_COMPATIBILIDADE.get(
            str(ordenados[0][0]),
            str(ordenados[0][0]),
        ),
        "rotulo_bruto": str(ordenados[0][0]),
        "probabilidade_calibrada": incerteza["probabilidade_top1"],
        "nivel_confianca": _nivel_confianca(
            incerteza["margem_top1_top2"],
            incerteza["entropia_normalizada"],
        ),
        "margem_top1_top2": incerteza["margem_top1_top2"],
        "entropia_normalizada": incerteza["entropia_normalizada"],
        "alternativas": [
            {
                "compatibilidade": ROTULOS_COMPATIBILIDADE.get(
                    str(categoria),
                    str(categoria),
                ),
                "probabilidade_calibrada": float(probabilidade),
            }
            for categoria, probabilidade in ordenados[1:]
        ],
    }


def build_ml_context(
    texto_curriculo: str,
    requisitos: list[str],
    texto_vaga: str,
) -> dict:
    modelo_area, metadata_area, _, _ = _load_artifacts()
    texto_limpo = limpar_texto(texto_curriculo)

    vetorizador = modelo_area.calibrated_classifiers_[0].estimator.named_steps["tfidf"]
    features, features_normalizadas = _vetor_normalizado(vetorizador, texto_limpo)

    if features.nnz == 0:
        return {
            "disponivel": False,
            "motivo": (
                "Vetor TF-IDF vazio; nenhuma inferência estatística foi emitida."
            ),
        }

    probabilidades = modelo_area.predict_proba(features)[0]
    ordenados = sorted(
        zip(modelo_area.classes_, probabilidades),
        key=lambda par: par[1],
        reverse=True,
    )

    incerteza = _incerteza(probabilidades)

    classes = metadata_area["classes"]
    centroides = np.vstack(
        [metadata_area["class_centroids"][categoria] for categoria in classes]
    )
    similaridades = features_normalizadas @ centroides.T
    similaridade_maxima = float(np.max(similaridades))
    classe_mais_proxima = classes[int(np.argmax(similaridades))]
    limiar_ood = float(metadata_area["ood_threshold"])
    possivel_ood = similaridade_maxima < limiar_ood

    ranking_requisitos = []

    if requisitos:
        vetores_requisitos = vetorizador.transform(requisitos)
        vetores_requisitos_normalizados = normalize(vetores_requisitos)
        similaridades_requisitos = np.asarray(
            features_normalizadas @ vetores_requisitos_normalizados.T
        ).ravel()

        ranking_requisitos = [
            {
                "requisito": requisito,
                "similaridade_cosseno": float(similaridade),
            }
            for requisito, similaridade in zip(
                requisitos,
                similaridades_requisitos,
            )
        ]

        ranking_requisitos.sort(
            key=lambda item: item["similaridade_cosseno"],
            reverse=True,
        )

    compatibilidade = _prever_compatibilidade(texto_curriculo, texto_vaga)

    nivel_confianca = (
        "baixa"
        if possivel_ood
        else _nivel_confianca(
            incerteza["margem_top1_top2"],
            incerteza["entropia_normalizada"],
        )
    )

    return {
        "disponivel": True,
        "area_prevista": str(ordenados[0][0]),
        "probabilidade_area_prevista": incerteza["probabilidade_top1"],
        "nivel_confianca": nivel_confianca,
        "margem_top1_top2": incerteza["margem_top1_top2"],
        "entropia_normalizada": incerteza["entropia_normalizada"],
        "alternativas": [
            {
                "area": str(categoria),
                "probabilidade_calibrada": float(probabilidade),
            }
            for categoria, probabilidade in ordenados[1:3]
        ],
        "deteccao_fora_distribuicao": {
            "possivel_ood": possivel_ood,
            "similaridade_ao_centroide_mais_proximo": similaridade_maxima,
            "classe_centroide_mais_proxima": classe_mais_proxima,
            "limiar_validado": limiar_ood,
        },
        "compatibilidade_curriculo_vaga": compatibilidade,
        "requisitos_priorizados": ranking_requisitos[:10],
        "interpretacao": (
            "Estes valores são sinais estatísticos de apoio. Similaridade alta não "
            "prova atendimento ao requisito; compatibilidade prevista não é decisão "
            "de contratação. Confiança baixa ou OOD exige análise mais cautelosa e "
            "evidência literal."
        ),
    }
