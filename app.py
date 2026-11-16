import streamlit as st, pandas as pd
from llm import analisar
from backend.app.services.files import extract
from backend.app.services.privacy import minimize
from backend.app.core.errors import ServiceError
from backend.app.core.config import MAX_FILE_BYTES
from backend.app.services.classifier import load_model, predict

st.set_page_config(page_title="Analise Inteligente de Curriculos", layout="wide")
st.title("Analise Inteligente de Curriculos")
st.caption("Apoio a recrutamento: a decisao final e sempre humana.")

@st.cache_resource
def carregar(): return load_model()
try:
    modelo = carregar()
except Exception:
    st.error('Classificador indisponível. Verifique models/ e a versão do scikit-learn.'); st.stop()

c1, c2 = st.columns(2)
with c1:
    arq = st.file_uploader("Curriculo (PDF ou TXT)", type=["pdf", "txt"])
    texto = st.text_area("...ou cole o texto do curriculo", height=150)
with c2:
    vaga = st.text_area("Descricao da vaga", height=250)
st.caption('O modo LLM envia textos minimizados ao provedor externo. Revise dados pessoais antes do envio; a minimização automática é limitada.')
consentimento = st.checkbox('Tenho autorização para processar estes dados e enviá-los ao provedor LLM.')

if st.button("Analisar", type="primary"):
    if not consentimento: st.error('Confirme a autorização de processamento.'); st.stop()
    if arq:
        try: texto = extract(arq.read(MAX_FILE_BYTES + 1), arq.name, arq.type)
        except ServiceError as e: st.error(e.message); st.stop()
    if not texto.strip() or not vaga.strip(): st.error("Informe curriculo e vaga."); st.stop()
    texto_ml, _ = minimize(texto, resume=True)
    ml = predict(texto_ml)
    top = pd.Series({item.category: item.probability for item in ml.top_categories}, dtype=float)
    st.subheader("1) Classificacao (Machine Learning)")
    for warning in ml.warnings: st.warning(warning)
    if not top.empty:
        st.bar_chart(top)
        st.write(f"Area prevista: **{top.index[0]}** ({top.iloc[0]:.0%})")
    else:
        st.write('Classificação indeterminada: vetor TF-IDF vazio.')
    with st.spinner("Consultando o LLM..."):
        try: r = analisar(texto, vaga, top.index[0] if not top.empty else None, float(top.iloc[0]) if not top.empty else None)
        except ServiceError as e: st.error(f"Falha no LLM ({e.code}): {e.message}"); st.stop()
        except Exception: st.error('Falha inesperada na análise contextual. O resultado ML foi preservado.'); st.stop()
    st.subheader("2) Analise (LLM)")
    nota = r['nota_aderencia']
    if nota is None:
        st.info('Abstenção de pontuação: sem método validado para converter evidências em nota. Isto não significa aderência zero.')
    else:
        st.metric("Aderencia a vaga", f"{nota}/100")
        st.progress(nota / 100)
    st.write(r["resumo"]); st.write("**Habilidades:**", ", ".join(r["habilidades"]))
    perfil = r.get('perfil_profissional')
    if perfil:
        st.write('**Perfil contextual (LLM):**', perfil['descricao'])
        st.caption(perfil['evidencia'])
    st.write('**Requisitos com evidências:**')
    for item in r['requisitos_atendidos']:
        st.write(item['requisito'], '—', item['evidencia'])
    st.write('**Requisitos sem evidência suficiente:**', ', '.join(r['requisitos_sem_evidencia']))
    a, b = st.columns(2)
    a.success("Pontos fortes\n\n" + "\n".join(f"- {x}" for x in r["pontos_fortes"]))
    b.warning("Lacunas\n\n" + "\n".join(f"- {x}" for x in r["lacunas"]))
    st.info("Justificativa: " + r["justificativa"])
    rel = f"RELATORIO\nArea: {ml.predicted_area}\nAderencia: {nota if nota is not None else 'não pontuada'}\n{r['justificativa']}"
    st.download_button("Baixar relatorio", rel, "relatorio.txt")
    st.caption("Aviso: resultado automatico, sujeito a erros e vieses. Revisao humana obrigatoria.")
