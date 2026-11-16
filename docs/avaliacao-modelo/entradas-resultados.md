# Entradas e resultados completos

Gerado por scripts/avaliar_modelo.py. Exemplos sintéticos; não constituem avaliação representativa.

| ID | Palavras | Esperada | Prevista | P(esperada) | Top 3 | Atributos ativos |
|---|---:|---|---|---:|---|---:|
| software-short-pt | 30 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 2,00% | BUSINESS-DEVELOPMENT 58,00%; AVIATION 6,33%; CONSULTANT 3,67% | 5 |
| software-short-en | 30 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 6,67% | BUSINESS-DEVELOPMENT 38,67%; ENGINEERING 9,00%; AVIATION 8,00% | 14 |
| software-medium-pt | 103 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 2,00% | BUSINESS-DEVELOPMENT 58,00%; AVIATION 6,33%; CONSULTANT 4,00% | 7 |
| software-medium-en | 89 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 11,33% | BUSINESS-DEVELOPMENT 25,67%; INFORMATION-TECHNOLOGY 11,33%; CONSULTANT 7,67% | 47 |
| software-long-pt | 231 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 2,00% | BUSINESS-DEVELOPMENT 57,33%; AVIATION 6,33%; CONSULTANT 4,00% | 10 |
| software-long-en | 214 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 12,00% | BUSINESS-DEVELOPMENT 12,33%; INFORMATION-TECHNOLOGY 12,00%; ENGINEERING 7,67% | 79 |
| hr-medium-pt | 71 | HR | BUSINESS-DEVELOPMENT | 0,33% | BUSINESS-DEVELOPMENT 62,00%; AVIATION 6,67%; ARTS 3,00% | 3 |
| hr-medium-en | 60 | HR | HR | 30,33% | HR 30,33%; BUSINESS-DEVELOPMENT 18,00%; ADVOCATE 5,67% | 44 |
| finance-medium-pt | 72 | FINANCE | BUSINESS-DEVELOPMENT | 0,67% | BUSINESS-DEVELOPMENT 62,00%; AVIATION 6,67%; ARTS 3,00% | 1 |
| finance-medium-en | 62 | FINANCE | BUSINESS-DEVELOPMENT | 17,67% | BUSINESS-DEVELOPMENT 22,33%; FINANCE 17,67%; BANKING 13,00% | 35 |
| health-medium-pt | 70 | HEALTHCARE | BUSINESS-DEVELOPMENT | 1,67% | BUSINESS-DEVELOPMENT 62,00%; AVIATION 6,67%; ARTS 3,00% | 2 |
| health-medium-en | 61 | HEALTHCARE | HEALTHCARE | 46,33% | HEALTHCARE 46,33%; BUSINESS-DEVELOPMENT 13,67%; ADVOCATE 9,67% | 35 |
| sales-medium-pt | 70 | SALES | BUSINESS-DEVELOPMENT | 0,67% | BUSINESS-DEVELOPMENT 62,00%; AVIATION 6,67%; ARTS 3,00% | 3 |
| sales-medium-en | 54 | SALES | SALES | 28,67% | SALES 28,67%; BUSINESS-DEVELOPMENT 24,00%; AVIATION 6,00% | 37 |
| software-repeated8-pt | 240 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 2,00% | BUSINESS-DEVELOPMENT 58,00%; AVIATION 6,33%; CONSULTANT 3,67% | 5 |
| software-repeated8-en | 240 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 6,67% | BUSINESS-DEVELOPMENT 38,67%; ENGINEERING 9,00%; AVIATION 8,00% | 14 |
| zero-oov | 2 | sem rótulo | BUSINESS-DEVELOPMENT | n/a | BUSINESS-DEVELOPMENT 62,67%; AVIATION 6,67%; ARTS 3,00% | 0 |
| zero-stopwords | 5 | sem rótulo | BUSINESS-DEVELOPMENT | n/a | BUSINESS-DEVELOPMENT 62,67%; AVIATION 6,67%; ARTS 3,00% | 0 |
| technical-terms-only | 9 | INFORMATION-TECHNOLOGY | BUSINESS-DEVELOPMENT | 1,00% | BUSINESS-DEVELOPMENT 62,33%; AVIATION 6,67%; CONSULTANT 3,33% | 3 |

## software-short-pt

**Entrada fictícia:**

Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.

**Texto efetivamente entregue ao TF-IDF:**

desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais.

Minimização: 0 remoções. Cobertura de unigramas únicos: 5/22. Atributos não nulos (unigramas e bigramas): 5.

## software-short-en

**Entrada fictícia:**

Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.

**Texto efetivamente entregue ao TF-IDF:**

software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems.

Minimização: 0 remoções. Cobertura de unigramas únicos: 13/19. Atributos não nulos (unigramas e bigramas): 14.

## software-medium-pt

**Entrada fictícia:**

Desenvolvedora de software com dois anos de experiência no desenvolvimento e na manutenção de sistemas empresariais. Utiliza Java e Spring Boot para implementar funcionalidades e APIs REST. Trabalha com PostgreSQL para consultar e persistir os dados utilizados pelos sistemas. Utiliza Git para registrar alterações e colaborar na revisão do código. Escreve testes unitários com JUnit e utiliza Docker para executar os sistemas em ambientes consistentes. Suas responsabilidades incluem compreender solicitações dos usuários, implementar alterações no software, investigar defeitos e verificar o comportamento das funcionalidades. Participa da manutenção de módulos existentes e acompanha a integração entre as APIs REST e os dados em PostgreSQL.

**Texto efetivamente entregue ao TF-IDF:**

desenvolvedora de software com dois anos de experiência no desenvolvimento e na manutenção de sistemas empresariais. utiliza java e spring boot para implementar funcionalidades e apis rest. trabalha com postgresql para consultar e persistir os dados utilizados pelos sistemas. utiliza git para registrar alterações e colaborar na revisão do código. escreve testes unitários com junit e utiliza docker para executar os sistemas em ambientes consistentes. suas responsabilidades incluem compreender solicitações dos usuários implementar alterações no software investigar defeitos e verificar o comportamento das funcionalidades. participa da manutenção de módulos existentes e acompanha a integração entre as apis rest e os dados em postgresql.

Minimização: 0 remoções. Cobertura de unigramas únicos: 7/62. Atributos não nulos (unigramas e bigramas): 7.

## software-medium-en

**Entrada fictícia:**

Software developer with two years of experience developing and maintaining enterprise systems. Uses Java and Spring Boot to implement features and REST APIs. Works with PostgreSQL to query and persist data used by the systems. Uses Git to record changes and collaborate on code reviews. Writes unit tests with JUnit and uses Docker to run systems in consistent environments. Responsibilities include understanding user requests, implementing software changes, investigating defects and checking feature behavior. Participates in maintaining existing modules and follows the integration between REST APIs and data in PostgreSQL.

**Texto efetivamente entregue ao TF-IDF:**

software developer with two years of experience developing and maintaining enterprise systems. uses java and spring boot to implement features and rest apis. works with postgresql to query and persist data used by the systems. uses git to record changes and collaborate on code reviews. writes unit tests with junit and uses docker to run systems in consistent environments. responsibilities include understanding user requests implementing software changes investigating defects and checking feature behavior. participates in maintaining existing modules and follows the integration between rest apis and data in postgresql.

Minimização: 0 remoções. Cobertura de unigramas únicos: 44/52. Atributos não nulos (unigramas e bigramas): 47.

## software-long-pt

**Entrada fictícia:**

Desenvolvedora de software com dois anos de experiência no desenvolvimento e na manutenção de sistemas empresariais. Sua atuação utiliza Java, Spring Boot, PostgreSQL, APIs REST, Git, testes unitários JUnit e Docker. No cotidiano, compreende solicitações dos usuários, lê o código existente e implementa mudanças nas funcionalidades. Investiga defeitos, reproduz situações relatadas e verifica se as correções preservam o comportamento esperado. No projeto fictício de um sistema de solicitações internas, participou da implementação de funcionalidades em Java e Spring Boot. As APIs REST recebem e retornam os dados usados pelos módulos. O PostgreSQL mantém os registros consultados e atualizados pelo sistema. Os testes unitários JUnit verificam o comportamento das partes alteradas. O Git registra o histórico das mudanças e permite a revisão do código com a equipe. O Docker é utilizado para executar o sistema em ambientes consistentes. Em outro projeto fictício, participou da manutenção de um sistema empresarial existente. Leu os módulos em Java, ajustou funcionalidades em Spring Boot e acompanhou as chamadas às APIs REST. Consultou e persistiu dados em PostgreSQL para verificar solicitações e seus resultados. Acrescentou testes unitários JUnit para as alterações, registrou as mudanças no Git e conferiu a execução com Docker. Suas responsabilidades incluem explicar as mudanças realizadas, revisar o comportamento das funcionalidades e acompanhar a integração dos módulos. Esses projetos descrevem a mesma experiência de dois anos, sem acrescentar períodos de trabalho ou tecnologias diferentes.

**Texto efetivamente entregue ao TF-IDF:**

desenvolvedora de software com dois anos de experiência no desenvolvimento e na manutenção de sistemas empresariais. sua atuação utiliza java spring boot postgresql apis rest git testes unitários junit e docker. no cotidiano compreende solicitações dos usuários lê o código existente e implementa mudanças nas funcionalidades. investiga defeitos reproduz situações relatadas e verifica se as correções preservam o comportamento esperado. no projeto fictício de um sistema de solicitações internas participou da implementação de funcionalidades em java e spring boot. as apis rest recebem e retornam os dados usados pelos módulos. o postgresql mantém os registros consultados e atualizados pelo sistema. os testes unitários junit verificam o comportamento das partes alteradas. o git registra o histórico das mudanças e permite a revisão do código com a equipe. o docker é utilizado para executar o sistema em ambientes consistentes. em outro projeto fictício participou da manutenção de um sistema empresarial existente. leu os módulos em java ajustou funcionalidades em spring boot e acompanhou as chamadas às apis rest. consultou e persistiu dados em postgresql para verificar solicitações e seus resultados. acrescentou testes unitários junit para as alterações registrou as mudanças no git e conferiu a execução com docker. suas responsabilidades incluem explicar as mudanças realizadas revisar o comportamento das funcionalidades e acompanhar a integração dos módulos. esses projetos descrevem a mesma experiência de dois anos sem acrescentar períodos de trabalho ou tecnologias diferentes.

Minimização: 0 remoções. Cobertura de unigramas únicos: 10/119. Atributos não nulos (unigramas e bigramas): 10.

## software-long-en

**Entrada fictícia:**

Software developer with two years of experience developing and maintaining enterprise systems. Her work uses Java, Spring Boot, PostgreSQL, REST APIs, Git, JUnit unit tests and Docker. In daily work, she understands user requests, reads existing code and implements feature changes. She investigates defects, reproduces reported situations and checks that corrections preserve expected behavior. In the fictional project for an internal request system, she participated in implementing features in Java and Spring Boot. REST APIs receive and return data used by the modules. PostgreSQL stores the records queried and updated by the system. JUnit unit tests check the behavior of the modified parts. Git records the history of changes and enables code review with the team. Docker is used to run the system in consistent environments. In another fictional project, she participated in maintaining an existing enterprise system. She read the Java modules, adjusted Spring Boot features and followed calls to REST APIs. She queried and persisted data in PostgreSQL to check requests and their results. She added JUnit unit tests for the changes, recorded the changes in Git and checked execution with Docker. Her responsibilities include explaining the changes made, reviewing feature behavior and following module integration. These projects describe the same two years of experience, without adding employment periods or different technologies.

**Texto efetivamente entregue ao TF-IDF:**

software developer with two years of experience developing and maintaining enterprise systems. her work uses java spring boot postgresql rest apis git junit unit tests and docker. in daily work she understands user requests reads existing code and implements feature changes. she investigates defects reproduces reported situations and checks that corrections preserve expected behavior. in the fictional project for an internal request system she participated in implementing features in java and spring boot. rest apis receive and return data used by the modules. postgresql stores the records queried and updated by the system. junit unit tests check the behavior of the modified parts. git records the history of changes and enables code review with the team. docker is used to run the system in consistent environments. in another fictional project she participated in maintaining an existing enterprise system. she read the java modules adjusted spring boot features and followed calls to rest apis. she queried and persisted data in postgresql to check requests and their results. she added junit unit tests for the changes recorded the changes in git and checked execution with docker. her responsibilities include explaining the changes made reviewing feature behavior and following module integration. these projects describe the same two years of experience without adding employment periods or different technologies.

Minimização: 0 remoções. Cobertura de unigramas únicos: 76/90. Atributos não nulos (unigramas e bigramas): 79.

## hr-medium-pt

**Entrada fictícia:**

Analista de recursos humanos com experiência em recrutamento, seleção e integração de funcionários. Conduz entrevistas, organiza processos seletivos e acompanha a admissão de profissionais. Mantém registros de pessoal, acompanha benefícios e esclarece dúvidas sobre políticas internas. Participa de treinamentos e acompanha o desenvolvimento de funcionários. Apoia gestores na avaliação de desempenho e no acompanhamento das necessidades das equipes. Prepara comunicações internas e mantém os documentos dos processos de recursos humanos organizados.

**Texto efetivamente entregue ao TF-IDF:**

analista de recursos humanos com experiência em recrutamento seleção e integração de funcionários. conduz entrevistas organiza processos seletivos e acompanha a admissão de profissionais. mantém registros de pessoal acompanha benefícios e esclarece dúvidas sobre políticas internas. participa de treinamentos e acompanha o desenvolvimento de funcionários. apoia gestores na avaliação de desempenho e no acompanhamento das necessidades das equipes. prepara comunicações internas e mantém os documentos dos processos de recursos humanos organizados.

Minimização: 0 remoções. Cobertura de unigramas únicos: 3/45. Atributos não nulos (unigramas e bigramas): 3.

## hr-medium-en

**Entrada fictícia:**

Human resources analyst with experience in recruitment, selection and employee onboarding. Conducts interviews, organizes hiring processes and follows the admission of professionals. Maintains personnel records, monitors benefits and answers questions about internal policies. Participates in training and follows employee development. Supports managers in performance reviews and in tracking team needs. Prepares internal communications and keeps human resources process documents organized.

**Texto efetivamente entregue ao TF-IDF:**

human resources analyst with experience in recruitment selection and employee onboarding. conducts interviews organizes hiring processes and follows the admission of professionals. maintains personnel records monitors benefits and answers questions about internal policies. participates in training and follows employee development. supports managers in performance reviews and in tracking team needs. prepares internal communications and keeps human resources process documents organized.

Minimização: 0 remoções. Cobertura de unigramas únicos: 39/41. Atributos não nulos (unigramas e bigramas): 44.

## finance-medium-pt

**Entrada fictícia:**

Analista financeiro com experiência em planejamento financeiro, elaboração de orçamentos e análise de fluxo de caixa. Acompanha receitas e despesas, compara resultados com o orçamento e investiga variações. Prepara projeções financeiras e relatórios para apoiar decisões de gestão. Avalia custos e acompanha indicadores financeiros da operação. Revisa previsões de caixa e consolida informações para o planejamento financeiro periódico. Apresenta análises de resultados, riscos financeiros e necessidades de recursos aos responsáveis pela gestão.

**Texto efetivamente entregue ao TF-IDF:**

analista financeiro com experiência em planejamento financeiro elaboração de orçamentos e análise de fluxo de caixa. acompanha receitas e despesas compara resultados com o orçamento e investiga variações. prepara projeções financeiras e relatórios para apoiar decisões de gestão. avalia custos e acompanha indicadores financeiros da operação. revisa previsões de caixa e consolida informações para o planejamento financeiro periódico. apresenta análises de resultados riscos financeiros e necessidades de recursos aos responsáveis pela gestão.

Minimização: 0 remoções. Cobertura de unigramas únicos: 1/46. Atributos não nulos (unigramas e bigramas): 1.

## finance-medium-en

**Entrada fictícia:**

Financial analyst with experience in financial planning, budgeting and cash flow analysis. Monitors revenue and expenses, compares results with the budget and investigates variances. Prepares financial forecasts and reports to support management decisions. Evaluates costs and monitors financial indicators for operations. Reviews cash forecasts and consolidates information for periodic financial planning. Presents analyses of results, financial risks and resource needs to management.

**Texto efetivamente entregue ao TF-IDF:**

financial analyst with experience in financial planning budgeting and cash flow analysis. monitors revenue and expenses compares results with the budget and investigates variances. prepares financial forecasts and reports to support management decisions. evaluates costs and monitors financial indicators for operations. reviews cash forecasts and consolidates information for periodic financial planning. presents analyses of results financial risks and resource needs to management.

Minimização: 0 remoções. Cobertura de unigramas únicos: 31/35. Atributos não nulos (unigramas e bigramas): 35.

## health-medium-pt

**Entrada fictícia:**

Enfermeira com experiência no cuidado de pacientes em unidade hospitalar. Acompanha sinais vitais, administra medicamentos prescritos e registra a evolução dos pacientes. Realiza cuidados de enfermagem, orienta pacientes e familiares e comunica alterações à equipe responsável. Participa do planejamento dos cuidados, acompanha a segurança do paciente e organiza a continuidade da assistência. Mantém registros clínicos atualizados e colabora com outros profissionais de saúde no atendimento e na recuperação dos pacientes.

**Texto efetivamente entregue ao TF-IDF:**

enfermeira com experiência no cuidado de pacientes em unidade hospitalar. acompanha sinais vitais administra medicamentos prescritos e registra a evolução dos pacientes. realiza cuidados de enfermagem orienta pacientes e familiares e comunica alterações à equipe responsável. participa do planejamento dos cuidados acompanha a segurança do paciente e organiza a continuidade da assistência. mantém registros clínicos atualizados e colabora com outros profissionais de saúde no atendimento e na recuperação dos pacientes.

Minimização: 0 remoções. Cobertura de unigramas únicos: 2/45. Atributos não nulos (unigramas e bigramas): 2.

## health-medium-en

**Entrada fictícia:**

Nurse with experience caring for patients in a hospital unit. Monitors vital signs, administers prescribed medication and records patient progress. Provides nursing care, guides patients and families and communicates changes to the responsible team. Participates in care planning, monitors patient safety and organizes continuity of care. Keeps clinical records updated and collaborates with other healthcare professionals in patient treatment and recovery.

**Texto efetivamente entregue ao TF-IDF:**

nurse with experience caring for patients in a hospital unit. monitors vital signs administers prescribed medication and records patient progress. provides nursing care guides patients and families and communicates changes to the responsible team. participates in care planning monitors patient safety and organizes continuity of care. keeps clinical records updated and collaborates with other healthcare professionals in patient treatment and recovery.

Minimização: 0 remoções. Cobertura de unigramas únicos: 33/37. Atributos não nulos (unigramas e bigramas): 35.

## sales-medium-pt

**Entrada fictícia:**

Profissional de vendas com experiência no atendimento comercial e na negociação com clientes. Prospecta clientes, identifica necessidades e apresenta produtos e propostas comerciais. Acompanha oportunidades de venda, negocia condições e realiza o acompanhamento de pedidos. Mantém relacionamento com clientes existentes e registra o andamento das negociações. Acompanha metas de vendas e prepara relatórios sobre os resultados comerciais. Atua no atendimento após a venda e no acompanhamento da satisfação dos clientes.

**Texto efetivamente entregue ao TF-IDF:**

profissional de vendas com experiência no atendimento comercial e na negociação com clientes. prospecta clientes identifica necessidades e apresenta produtos e propostas comerciais. acompanha oportunidades de venda negocia condições e realiza o acompanhamento de pedidos. mantém relacionamento com clientes existentes e registra o andamento das negociações. acompanha metas de vendas e prepara relatórios sobre os resultados comerciais. atua no atendimento após a venda e no acompanhamento da satisfação dos clientes.

Minimização: 0 remoções. Cobertura de unigramas únicos: 3/42. Atributos não nulos (unigramas e bigramas): 3.

## sales-medium-en

**Entrada fictícia:**

Sales professional with experience in commercial service and customer negotiation. Prospects customers, identifies needs and presents products and commercial proposals. Tracks sales opportunities, negotiates terms and follows orders. Maintains relationships with existing customers and records negotiation progress. Tracks sales targets and prepares reports on commercial results. Works in after-sales service and follows customer satisfaction.

**Texto efetivamente entregue ao TF-IDF:**

sales professional with experience in commercial service and customer negotiation. prospects customers identifies needs and presents products and commercial proposals. tracks sales opportunities negotiates terms and follows orders. maintains relationships with existing customers and records negotiation progress. tracks sales targets and prepares reports on commercial results. works in after sales service and follows customer satisfaction.

Minimização: 0 remoções. Cobertura de unigramas únicos: 29/31. Atributos não nulos (unigramas e bigramas): 37.

## software-repeated8-pt

**Entrada fictícia:**

Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.
Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.
Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.
Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.
Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.
Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.
Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.
Desenvolvedora de software com dois anos de experiência em Java, Spring Boot, PostgreSQL e APIs REST. Experiência com Git, testes unitários JUnit e Docker. Participação no desenvolvimento de sistemas empresariais.

**Texto efetivamente entregue ao TF-IDF:**

desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais. desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais. desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais. desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais. desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais. desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais. desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais. desenvolvedora de software com dois anos de experiência em java spring boot postgresql e apis rest. experiência com git testes unitários junit e docker. participação no desenvolvimento de sistemas empresariais.

Minimização: 0 remoções. Cobertura de unigramas únicos: 5/22. Atributos não nulos (unigramas e bigramas): 5.

## software-repeated8-en

**Entrada fictícia:**

Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.
Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.
Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.
Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.
Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.
Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.
Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.
Software developer with two years of experience in Java, Spring Boot, PostgreSQL and REST APIs. Experience with Git, JUnit unit tests and Docker. Participation in the development of enterprise systems.

**Texto efetivamente entregue ao TF-IDF:**

software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems. software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems. software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems. software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems. software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems. software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems. software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems. software developer with two years of experience in java spring boot postgresql and rest apis. experience with git junit unit tests and docker. participation in the development of enterprise systems.

Minimização: 0 remoções. Cobertura de unigramas únicos: 13/19. Atributos não nulos (unigramas e bigramas): 14.

## zero-oov

**Entrada fictícia:**

zzqxv zzqxv

**Texto efetivamente entregue ao TF-IDF:**

zzqxv zzqxv

Minimização: 0 remoções. Cobertura de unigramas únicos: 0/1. Atributos não nulos (unigramas e bigramas): 0.

## zero-stopwords

**Entrada fictícia:**

the and or the and

**Texto efetivamente entregue ao TF-IDF:**

the and or the and

Minimização: 0 remoções. Cobertura de unigramas únicos: 0/0. Atributos não nulos (unigramas e bigramas): 0.

## technical-terms-only

**Entrada fictícia:**

Java, Spring Boot, PostgreSQL, APIs REST, Git, JUnit, Docker.

**Texto efetivamente entregue ao TF-IDF:**

java spring boot postgresql apis rest git junit docker.

Minimização: 0 remoções. Cobertura de unigramas únicos: 3/9. Atributos não nulos (unigramas e bigramas): 3.
