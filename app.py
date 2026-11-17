import streamlit as st
import pandas as pd

from llm import analisar
from backend.app.services.files import extract
from backend.app.services.privacy import minimize
from backend.app.core.errors import ServiceError
from backend.app.core.config import MAX_FILE_BYTES
from backend.app.services.classifier import load_model, predict, build_ml_context
from backend.app.services.requirement_coverage import inventory

st.set_page_config(
    page_title="Análise Inteligente de Currículos",
    layout="wide",
)

st.title("Análise Inteligente de Currículos")
st.caption("Apoio a recrutamento: a decisão final é sempre humana.")


@st.cache_resource
def carregar():
    return load_model()


try:
    carregar()
except Exception:
    st.error(
        "Classificadores indisponíveis. Execute python train.py e verifique models/."
    )
    st.stop()


c1, c2 = st.columns(2)

with c1:
    arquivo = st.file_uploader(
        "Currículo (PDF ou TXT)",
        type=["pdf", "txt"],
    )
    texto = st.text_area("...ou cole o texto do currículo", height=150)

with c2:
    vaga = st.text_area("Descrição da vaga", height=250)

st.caption(
    "O modo LLM envia textos minimizados ao provedor externo. "
    "Revise dados pessoais antes do envio; a minimização automática é limitada."
)

consentimento = st.checkbox(
    "Tenho autorização para processar estes dados e enviá-los ao provedor LLM."
)

if st.button("Analisar", type="primary"):
    if not consentimento:
        st.error("Confirme a autorização de processamento.")
        st.stop()

    if arquivo:
        try:
            texto = extract(
                arquivo.read(MAX_FILE_BYTES + 1),
                arquivo.name,
                arquivo.type,
            )
        except ServiceError as erro:
            st.error(erro.message)
            st.stop()

    if not texto.strip() or not vaga.strip():
        st.error("Informe currículo e vaga.")
        st.stop()

    texto_ml, _ = minimize(texto, resume=True)
    ml = predict(texto_ml)

    top = pd.Series(
        {
            item.category: item.probability
            for item in ml.top_categories
        },
        dtype=float,
    )

    st.subheader("1) Classificação estatística (Machine Learning)")

    for aviso in ml.warnings:
        st.warning(aviso)

    if not top.empty:
        st.bar_chart(top)
        st.write(
            f"Área prevista: **{top.index}** "[0]
            f"({top.iloc:.1%} de probabilidade calibrada)"[0]
        )
    else:
        st.write("Classificação indeterminada: vetor TF-IDF vazio.")

    catalog = inventory(vaga)
    requisitos = [item.texto for item in catalog.requisitos]

    contexto_ml = build_ml_context(
        texto_ml,
        requisitos,
        vaga,
    )

    if contexto_ml.get("disponivel"):
        compatibilidade = contexto_ml["compatibilidade_curriculo_vaga"]

        st.metric(
            "Compatibilidade prevista",
            compatibilidade["compatibilidade_prevista"],
        )

        st.metric(
            "Confiança da compatibilidade",
            compatibilidade["nivel_confianca"].capitalize(),
        )

        st.metric(
            "Confiança da área",
            contexto_ml["nivel_confianca"].capitalize(),
        )

        st.write(
            f"Probabilidade calibrada da compatibilidade: "
            f"**{compatibilidade['probabilidade_calibrada']:.1%}**"
        )

        st.write(
            f"Margem entre as duas classes mais prováveis: "
            f"**{contexto_ml['margem_top1_top2']:.3f}**"
        )

        st.write(
            f"Entropia normalizada: "
            f"**{contexto_ml['entropia_normalizada']:.3f}** "
            "(0 = distribuição concentrada; 1 = alta incerteza)"
        )

        if contexto_ml["deteccao_fora_distribuicao"]["possivel_ood"]:
            st.warning(
                "O currículo pode estar fora da distribuição dos dados de treino. "
                "A classificação de área deve ser tratada como incerta."
            )

        if contexto_ml["requisitos_priorizados"]:
            st.write("**Requisitos priorizados pelo ML:**")

            prioridade_df = pd.DataFrame(
                contexto_ml["requisitos_priorizados"]
            ).rename(
                columns={
                    "requisito": "Requisito",
                    "similaridade_cosseno": "Similaridade TF-IDF",
                }
            )

            st.dataframe(prioridade_df, use_container_width=True)

    with st.spinner("Consultando o LLM..."):
        try:
            resultado = analisar(
                texto,
                vaga,
                contexto_ml if contexto_ml.get("disponivel") else None,
            )
        except ServiceError as erro:
            st.error(f"Falha no LLM ({erro.code}): {erro.message}")
            st.stop()
        except Exception:
            st.error(
                "Falha inesperada na análise contextual. "
                "O resultado ML foi preservado."
            )
            st.stop()

    st.subheader("2) Análise contextual (LLM)")

    nota = resultado["nota_aderencia"]

    if nota is None:
        st.info(
            "Abstenção de pontuação: sem método validado para converter "
            "evidências em nota. Isto não significa aderência zero."
        )
    else:
        st.metric("Aderência à vaga", f"{nota}/100")
        st.progress(nota / 100)

    st.write(resultado["resumo"])
    st.write(
        "**Habilidades:**",
        ", ".join(resultado["habilidades"]),
    )

    perfil = resultado.get("perfil_profissional")

    if perfil:
        st.write("**Perfil contextual (LLM):**", perfil["descricao"])
        st.caption(perfil["evidencia"])

    st.write("**Requisitos com evidências:**")

    for item in resultado["requisitos_atendidos"]:
        st.write(item["requisito"], "—", item["evidencia"])

    st.write(
        "**Requisitos sem evidência suficiente:**",
        ", ".join(resultado["requisitos_sem_evidencia"]),
    )

    a, b = st.columns(2)

    with a:
        st.success(
            "Pontos fortes\n\n"
            + "\n".join(f"- {item}" for item in resultado["pontos_fortes"])
        )

    with b:
        st.warning(
            "Lacunas\n\n"
            + "\n".join(f"- {item}" for item in resultado["lacunas"])
        )

    st.info("Justificativa: " + resultado["justificativa"])

    compatibilidade_texto = "indisponível"

    if contexto_ml.get("disponivel"):
        compatibilidade_texto = contexto_ml[
            "compatibilidade_curriculo_vaga"
        ]["compatibilidade_prevista"]

    relatorio = (
        "RELATÓRIO\n"
        f"Área prevista pelo ML: {ml.predicted_area}\n"
        f"Compatibilidade prevista pelo ML: {compatibilidade_texto}\n"
        f"Confiança estatística: "
        f"{contexto_ml.get('nivel_confianca', 'indisponível')}\n"
        f"Aderência: {nota if nota is not None else 'não pontuada'}\n"
        f"{resultado['justificativa']}"
    )

    st.download_button(
        "Baixar relatório",
        relatorio,
        "relatorio.txt",
    )

    st.caption(
        "Aviso: resultado automático, sujeito a erros e vieses. "
        "Revisão humana obrigatória."
    )
