# Ética e uso responsável

Esta versão implementa apoio à leitura, nunca rejeição ou contratação automática.
A comparação não ordena candidatos por nota e preserva a ordem dos documentos.
O indicador contextual é heurístico; a probabilidade ML só classifica uma área.

## Dados pessoais

Não há retenção permanente de documentos pelo aplicativo, banco ou histórico.
Arquivos podem passar por armazenamento temporário do framework. O resultado
individual é mantido em memória no navegador; um relatório baixado passa a estar
sob responsabilidade de quem o salvou.

Minimização por regras ocorre antes da chamada externa para currículo e vaga.
Testes conferem o payload recebido por mock e o conteúdo da chamada ao SDK.
As regras não identificam todas as pessoas, dados sensíveis ou identificadores
indiretos em texto livre. Revise o documento antes de enviar. O próprio contexto
profissional pode identificar alguém. O provedor externo tem políticas próprias.

## Transparência e vieses

Dataset em inglês e categorias fixas limitam a generalização. Não há validação em
português nem estudo de equidade entre grupos. O modelo selecionado atingiu 75,05%
de acurácia e 0,6896 F1 macro na avaliação original, sem teste independente final.
Essas métricas não validam seleção de pessoas ou notas do LLM.

O prompt orienta a ignorar atributos pessoais. Regex e instruções não garantem
ausência de discriminação. Citações são verificadas por presença literal, mas isso
não garante interpretação correta. Pessoas podem omitir competências relevantes;
ausência de evidência deve gerar perguntas, não exclusão automática.

## Limites e medidas

Sem OCR. Textos longos podem ser truncados na etapa contextual com aviso. LLM pode
alucinar. Separação de instruções e dados, saída validada e ausência de ferramentas
reduzem riscos de instruções maliciosas, sem imunidade garantida.

Logs do aplicativo registram códigos técnicos, sem currículos ou chaves. Erros
não devolvem payloads privados. A API é local, sem autenticação: uso organizacional
exige análise própria de acesso, retenção, base de tratamento e governança do
provedor. Os documentos éticos originais na raiz foram preservados como histórico;
esta página descreve os controles e limites efetivos da versão 2.0.
