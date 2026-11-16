# Cobertura documental dos requisitos identificados

O backend calcula `100 × com_evidencia / total`, sem pesos. Não utiliza uma
nota do LLM. `llm.nota_aderencia` permanece null no fluxo real. O novo campo
`cobertura_requisitos` é independente da classificação Random Forest.

## Lista fechada e verificável

A extração é determinística e conservadora, antes da chamada ao provedor.
Para certificar a lista, a vaga deve organizar todas as exigências em seções
`Requisitos:`, `Requisitos obrigatórios:`, `Desejáveis:` ou equivalentes em inglês,
com itens iniciados por hífen/bullet/numeração ou separados por ponto e vírgula
na mesma linha do título. Metadados explícitos `Vaga:`, `Cargo:`, `Empresa:` e
`Local:` são descritivos. O exemplo do formulário usa esse formato.

Cada item mantém referências literais na vaga e um identificador SHA-256 de
seu texto normalizado (Unicode NFC, caixa e espaços). Retira-se apenas o ponto
final delimitador; preservam-se qualificadores, números, acentos e pontuação
interna. Só duplicações dessa identidade são unidas; não há sinônimos ou stemming.
Os IDs são estáveis para a mesma identidade, independentemente da ordem.

Cada bullet ou unidade separada por ponto e vírgula conta como **um requisito**.
Vírgulas e conjunções `e/and/&` dentro dele delimitam componentes obrigatórios
em conjunto: `Python e SQL` só entra no numerador se ambos tiverem evidências.
Sua interpretação é declarada, não uma inferência semântica do LLM.
Itens equivalentes com redações diferentes podem permanecer separados;
revise a lista exibida antes de interpretar o número.

## Avaliação

O adaptador envia a lista com IDs e componentes ao LLM, sem nova chamada.
Ele deve avaliar todos os componentes nos campos existentes. O validador de
fundamentação continua rejeitando citações inventadas, negativas ou incompletas
e requisitos sem referência na vaga. Nenhuma regra existente foi enfraquecida.

A cobertura confere novamente as passagens e as associações literais. Duas
citações do mesmo requisito não aumentam o numerador. Os estados são:

- **Evidência verificada:** todos os componentes têm citações completas válidas.
- **Sem evidência suficiente:** avaliação explícita sem evidência para pelo menos
  um componente, sem componentes omitidos ou contraditórios.
- **Indeterminado:** avaliação omitida, inconsistente, indisponível ou não suportada.

Ausência de evidência nunca significa ausência de competência. Um currículo
incompatível, mas com experiência independente verificada, pode resultar em 0%.
Uma resposta sem qualquer suporte contextual não autoriza publicar 0%.

## Quando há abstenção

O percentual só existe com lista completa, denominador positivo e todas as
avaliações válidas. Omissões do LLM não reduzem o denominador. Texto livre não
catalogado, seções vazias, agrupamento inline ambíguo, listas hierárquicas,
alternativas/condições/negações, requisitos fora da lista, respostas inválidas,
falha do provedor, currículo truncado e ausência de evidências contextuais
mantêm o estado indeterminado. Contagens e itens continuam disponíveis.
O modo demo não publica cobertura documental como se fosse validação real.

Não é possível garantir completude semântica de qualquer vaga em prosa usando
este extrator. Completo significa completo **dentro do formato explícito aceito**,
não certificação de que o redator incluiu todas as exigências pretendidas.
Não há equivalência semântica, validação factual de experiência nem medida de
adequação profissional. Requisitos qualitativos podem exigir abstenção.

## Evidência dos testes locais

Fixtures fictícias reproduzem 2/2 = 100%, 1/2 = 50% e 0/2 = 0%. Testam também
duplicações, IDs estáveis, itens compostos, múltiplas citações, omissões,
contradições, extração ambígua, citação inventada/incompleta, falta de suporte,
texto truncado e falha contextual. Integrações SDK → fundamentação → API usam
`httpx.MockTransport`, sem rede externa. Playwright verifica contagens, fórmula,
percentual, barra acessível, abstenção e preservação dos resultados anteriores.

O comportamento com o provedor real ainda exige teste manual autorizado:
ele pode omitir avaliações ou usar rótulos diferentes, levando à abstenção
conservadora, sem publicação de uma porcentagem injustificada.

Validação local desta entrega (15/11/2026): **254 testes Python aprovados**,
**17 testes Playwright aprovados** e **build TypeScript/Vite aprovado**.
O Python emitiu somente o aviso de depreciação existente de Starlette/httpx.
Servidores de testes foram iniciados com dotenv desabilitado, credenciais vazias
e endpoint externo substituído por localhost sem serviço. Nenhuma chamada paga
foi executada. Os SHA-256 do pipeline, CSV de métricas e matriz originais
permaneceram iguais aos valores anteriores à alteração.
