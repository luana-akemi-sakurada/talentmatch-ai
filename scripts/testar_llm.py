"""Teste rapido da conexao com o LLM (usa a configuracao do .env). Execute: python scripts/testar_llm.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.core.errors import ServiceError  # noqa: E402
from llm import analisar  # noqa: E402

CURRICULO = ("Desenvolvedora de software com 3 anos de experiencia em Python, SQL e Git. "
             "Desenvolveu dashboards em Power BI. Atuou em equipes de dados.")
VAGA = "Vaga: Analista de dados\nRequisitos:\n- Python\n- SQL\n- Power BI\n- AWS"

try:
    resultado = analisar(CURRICULO, VAGA, None)
except ServiceError as erro:
    sys.exit(f"FALHOU: {erro.code} - {erro.message}")
print("OK: o LLM respondeu e a resposta passou na validacao.")
print("Habilidades:", resultado["habilidades"])
print("Requisitos com evidencia:", [item["requisito"] for item in resultado["requisitos_atendidos"]])
print("Sem evidencia:", resultado["requisitos_sem_evidencia"])
