# Plano de projeto — Job Finder Java integrado ao Hermes

Versão: 1.0 · Revisão: 2026-09-16
Status: plano de execução proposto; implementação Java ainda não iniciada.
Responsáveis: Rafael (produto, aprendizado e validação) e assistente de desenvolvimento (implementação acompanhada, testes e revisão).

## 1. Objetivo e resultado esperado

Construir uma aplicação Java que encontre e organize oportunidades compatíveis com Rafael, reduzindo o tempo gasto na busca e permitindo concentrar o estudo em Java e IA aplicada. O projeto também deve demonstrar engenharia compreensível, testada e reproduzível no portfólio.

O Hermes Agent já instalado será um consumidor das ferramentas da aplicação. As regras de negócio, persistência, coleta definitiva e controle de ações pertencem ao sistema Java. O projeto não pressupõe desenvolver outro framework de agentes.

Sucesso inicial significa conseguir importar, avaliar, consultar e revisar vagas em Java, preservando dados após reinício e explicando cada decisão. Conseguir uma entrevista é um resultado desejado, mas não um critério técnico de conclusão.

## 2. Base verificada e limites da revisão

Em 2026-09-16, a leitura do repositório identificou:
- Pipeline Python com coletores Gupy, LinkedIn, RSS, GitHub Issues e Trampos.
- Filtros, scoring, avaliação LLM opcional, Telegram e estado em seen_jobs.json.
- Workflow horário em .github/workflows/monitor.yml.
- 90 testes passando na avaliação anterior desta conversa; isso não comprova disponibilidade das fontes externas.
- Ausência de implementação Java, fila de candidaturas, Kanban e integração efetiva com Hermes.
- Executável Hermes localizado em C:/Users/Rafael lauri/AppData/Local/hermes/bin/hermes.exe. Versão, ferramentas, protocolo e modo de execução ainda precisam ser inspecionados.

Fontes locais: monitor.py, core/scoring.py, models/job.py, storage/state_store.py, profile.json e .github/workflows/monitor.yml. Esta revisão não executou envios nem verificou APIs externas.

Problemas observados que devem ter testes de regressão na transição:
- monitor.py marca a vaga como vista mesmo quando send_job_alert retorna falha.
- StateStore mantém IDs sem namespace de fonte, permitindo colisões entre plataformas.
- StateStore._load não restaura llm_usage e retorna estado vazio em falhas de leitura.
- O workflow não define concorrência e ignora falha de rebase.
- O scoring combina heurística e LLM; a nota resultante não é probabilidade de contratação.

Esses achados são itens de implementação futura; a revisão documental não os corrige no código.

## 3. Escopo do MVP

Incluído:
- Um usuário e um perfil profissional versionado.
- Backend Java com Spring Boot, Maven Wrapper e PostgreSQL.
- Migrações de banco versionadas.
- Importação de um lote de vagas por API e fixtures sintéticas.
- Identificação por fonte, atualização de conteúdo e deduplicação conservadora.
- Filtros explícitos, score determinístico explicado e fila de revisão.
- Registro manual do acompanhamento de candidaturas.
- Testes, CI, instruções de execução e demonstração sem credenciais reais.

Fora do MVP:
- Envio automático de candidaturas, leitura de caixa postal e automação de navegador.
- Integração com múltiplos Kanbans externos.
- RAG, banco vetorial, microserviços e mensageria externa.
- Recomendações de estudo, radar open source e personalização de currículo.
- Interface web completa e migração simultânea de todos os coletores.

O produto final deve operar com o núcleo e os coletores necessários em Java. Python será uma ponte temporária e uma referência de comportamento. O runtime externo do Hermes não precisa ser reimplementado em Java.

## 4. Arquitetura e responsabilidades

Adotar um monólito modular Java. A escolha reduz o número de serviços que precisam ser operados e permite aprender domínio, persistência e integrações em etapas.

| Componente | Responsabilidade |
| --- | --- |
| Java: profile | Perfil e restrições configuráveis, versões e atualização |
| Java: jobs | Vagas, proveniência, importação e identidade |
| Java: matching | Elegibilidade, evidências, score e explicações |
| Java: applications | Revisão e histórico de candidaturas |
| Java: integrations | Coletores, Telegram e adaptadores de IA |
| PostgreSQL | Estado de negócio, avaliações e auditoria |
| Hermes instalado | Consultar ferramentas Java e executar rotinas dentro de permissões explícitas |
| Python temporário | Fornecer dados durante a migração, sem se tornar dependência final |

Organizar pacotes por funcionalidade; dentro deles separar domínio, casos de uso e adaptadores quando necessário. Regras determinísticas devem poder ser testadas sem Spring e sem rede.

O Hermes acessará a API através de um adaptador compatível com a instalação real. HTTP direto, CLI ou MCP são alternativas a verificar no marco M0, não capacidades presumidas.

Definir versões compatíveis do JDK, Spring Boot e PostgreSQL no início da implementação, conferir documentação oficial e registrar as versões exatas no build e no README. Evitar versões flutuantes. O plano não exige dependência de um provedor específico de IA.

## 5. Modelo e invariantes

| Registro | Dados mínimos e regra |
| --- | --- |
| Profile | ID, versão, competências atuais, interesses de aprendizado, regiões e restrições |
| Job | UUID, título, empresa, descrição, modalidade, local, datas de descoberta/atualização e situação |
| JobSource | Fonte, ID externo, URL e Job associado; unicidade por (fonte, ID externo) |
| Evaluation | Job, versão do perfil, versão das regras, hash do conteúdo, elegibilidade, score e motivos |
| Review | Job, estado da triagem e data da mudança |
| Application | Job, canal, estado, datas e evidência de envio quando disponível |
| AuditEvent | Entidade, ação, autor, data e referência ao resultado, sem segredos |

Regras:
1. Reimportar o mesmo ID na mesma fonte atualiza o registro; não duplica.
2. IDs iguais em fontes distintas podem representar vagas diferentes.
3. Similaridade de título e empresa produz uma sugestão de duplicidade; não autoriza fusão destrutiva automática.
4. Mudança de conteúdo ou perfil pode gerar nova avaliação, preservando o histórico anterior.
5. Informações ausentes ficam como desconhecidas. Modalidade ou senioridade não podem assumir valores favoráveis por padrão.
6. Interesse em aprender Java/IA não equivale a experiência já comprovada.
7. Vaga vista, vaga avaliada, alerta entregue e candidatura enviada são fatos distintos.
8. Datas persistidas em UTC; apresentação no fuso America/Sao_Paulo.
9. A aplicação deve rejeitar transições inválidas e registrar o motivo.

## 6. Avaliação e ordenação

Primeiro aplicar restrições do perfil. Classificar a elegibilidade como ELIGIBLE, INELIGIBLE ou NEEDS_REVIEW. Uma ausência de informação necessária exige revisão; empresa prioritária não anula uma restrição.

Proposta de score v1 para vagas elegíveis:
- Competências atuais: até 40 pontos.
- Senioridade compatível: até 30 pontos.
- Localização/modalidade: até 20 pontos.
- Preferências de carreira e empresa: até 10 pontos.

Antes de implementar, detalhar uma tabela de pontuação por evidência e aprová-la com exemplos reais rotulados por Rafael. Os pesos são hipótese inicial de produto; não são uma estimativa de aprovação em seleção.

Ordenar a fila elegível por score decrescente, descoberta crescente e UUID como desempate. Manter uma fila separada para NEEDS_REVIEW; vagas encerradas saem da fila ativa sem perda de histórico. Não usar 75 ou 90 como limiares obrigatórios sem validação.

IA entra após o MVP: extrai requisitos e sugere explicações com trechos de evidência, retorna estrutura validada e tem orçamento e timeout configuráveis. Em falha, preservar avaliação determinística e identificar a indisponibilidade. Não copiar automaticamente a ponderação Python 30/70.

## 7. Estados e ações

Triagem da vaga:
NEW -> REVIEWED -> SHORTLISTED ou DISMISSED.
Permitir reabertura explícita com auditoria.

Acompanhamento manual:
PREPARING -> APPLIED -> IN_REVIEW -> INTERVIEW -> OFFER.
Permitir REJECTED ou WITHDRAWN a partir de estados ativos apropriados, e APPLIED -> INTERVIEW quando não houver confirmação intermediária.
Oferta não significa contratação; fechamento pode ser registrado posteriormente.

No MVP, APPLIED é informação registrada pelo usuário, com data e canal. A API não envia candidatura.

Quando o envio assistido for implementado, manter um estado técnico separado:
DRAFT -> AWAITING_APPROVAL -> APPROVED -> SENDING -> SENT, FAILED ou UNKNOWN.

- Aprovação se vincula ao destinatário, vaga e versão exata dos documentos.
- Alterações nesses dados invalidam a aprovação.
- SENT exige evidência do provedor; não promete leitura nem aceite pelo recrutador.
- Timeout após possível envio gera UNKNOWN e exige reconciliação antes de nova tentativa.
- Uma chave idempotente por operação e reserva transacional impedem disparos concorrentes duplicados.
- Prioridade alta altera ordem e alerta; não ultrapassa limites nem autorização.

## 8. Contrato inicial da API

Prefixo proposto: /api/v1. Documentar esquemas em OpenAPI durante M1.

| Operação | Finalidade | Critério |
| --- | --- | --- |
| PUT /profile | Atualizar perfil | Validar campos e incrementar versão |
| POST /jobs/import | Importar lote | Responder por item: criado, atualizado ou inválido |
| GET /jobs | Consultar e ordenar | Paginação, filtros e ordenação estável |
| GET /jobs/{id} | Consultar detalhe | Fontes, evidências e última avaliação |
| POST /jobs/{id}/evaluations | Avaliar novamente | Deduplicar avaliação da mesma versão de conteúdo/perfil/regras |
| PATCH /jobs/{id}/review | Atualizar triagem | Validar estado e auditar |
| POST /applications | Registrar candidatura manual | Identificar origem manual; rejeitar duplicação ativa involuntária |
| PATCH /applications/{id}/status | Atualizar acompanhamento | Validar transição e preservar histórico |

Definir erros estruturados e consistentes: validação, registro inexistente e conflito. Limitar tamanho de lote e de conteúdo. Atualizações concorrentes devem detectar versão desatualizada.

No desenvolvimento, expor localmente. Antes de acesso pelo Hermes fora do processo local, implementar autenticação e permissões por operação; segredos via ambiente, fora do Git. A integração deve testar tanto acesso permitido quanto negado.

## 9. Backlog ordenado com critérios de aceite

Cada linha é uma entrega revisável. Uma etapa só termina com sua evidência de conclusão.

| ID | Dependência | Entrega | Critério de aceite |
| --- | --- | --- | --- |
| M0.1 | Nenhuma | Inventário Hermes e ambiente Java | Registrar versão, execução, ferramentas suportadas, autenticação e restrições sem copiar segredos |
| M0.2 | Nenhuma | Dataset de aceitação | Pelo menos 20 fixtures sintéticas/anonimizadas com avaliação de Rafael: compatível, incompatível, ambígua e duplicada |
| M0.3 | M0.1–2 | Decisões de implementação | Registrar versões, localização do módulo Java, contrato Hermes e tabela de score; listar pendências |
| M1.1 | M0.3 | Esqueleto Java e banco | Build reproduzível, health check, migração inicial e CI em PR |
| M1.2 | M1.1 | Perfil, importação e identidade | Reimportação idempotente, IDs entre fontes sem colisão e dados preservados após reinício |
| M1.3 | M1.2 | Avaliação e fila | Restrições testadas, score explicado, desconhecidos em revisão e ordenação estável |
| M1.4 | M1.3 | Triagem e candidaturas manuais | Histórico recuperável e transições inválidas rejeitadas |
| M1.5 | M1.4 | Demonstração MVP | Clone limpo -> banco -> testes -> lote -> ranking -> candidatura manual, seguindo apenas README |
| M2.1 | M1.5 | Primeiro coletor Java | GitHub Issues como proposta inicial; paginação limitada, timeout, erros e mapeamento testados com mocks |
| M2.2 | M2.1 | Alertas confiáveis | Outbox no banco; falha não marca entrega; retries limitados e pendências consultáveis |
| M2.3 | M2.2 | Ferramentas Hermes | Consulta e triagem via contrato confirmado; repetir operação não duplica efeitos; negação de acesso testada |
| M3.1 | M2.3 | IA aplicada | Saída validada, evidências, orçamento, fallback e comparação com baseline no dataset rotulado |
| M3.2 | M3.1 | Candidatura assistida | Rascunho revisável, aprovação vinculada à versão e envio em ambiente de teste; nenhum envio real no teste |
| M3.3 | M3.2 | Primeiro canal de envio | Canal escolhido e validado, idempotência, limite, reconciliação de UNKNOWN e desligamento operacional |
| M4.1 | M3.3 | Feedback de respostas | Correlação por candidatura/remetente/thread; mensagens ambíguas pedem revisão e não alteram status sozinhas |
| M4.2 | M2.1 | Conclusão da migração | Fontes necessárias portadas ou descontinuadas com motivo; caminho principal funciona sem Python |

MVP corresponde a M1.5. Hermes funcional corresponde a M2.3. Produto com candidatura assistida corresponde a M3.3. M4 não bloqueia o uso diário das versões anteriores.

Recomendações de estudo e radar open source ficam no backlog posterior. Adicioná-los apenas quando o fluxo de vagas estiver estável e houver necessidade validada.

## 10. Estratégia de testes e operação

- Unitários: restrições, score, identidade, transições e ordenação.
- Integração PostgreSQL: migrações, unicidade, rollback e persistência após reinício; Testcontainers é a opção proposta, sujeita à disponibilidade de Docker.
- Contrato: importação Python/Java enquanto necessária, ferramentas Hermes e saídas de IA.
- Adaptadores externos: respostas simuladas de timeout, erro, rate limit e payload inválido; CI sem credenciais reais.
- Aceitação: dataset rotulado e roteiro completo do MVP.
- Futuro envio: duas execuções concorrentes, aprovação revogada, falha antes/depois do envio e estado UNKNOWN.

Registrar contagens por fonte (coletadas, inválidas, elegíveis), duração, última coleta bem-sucedida e falhas. Falha parcial não deve aparecer como saúde total. Alertas precisam distinguir tentativa e entrega.

Implementar backup e recuperação do PostgreSQL antes de substituir a persistência atual em produção. Testar restauração em banco separado. Logs não devem conter currículo completo, tokens ou conteúdo privado de e-mail.

## 11. Migração e execução diária

1. Preservar o radar atual durante M0/M1.
2. Construir e demonstrar Java com fixtures.
3. Se necessário, adicionar exportação estruturada ao Python; não usar o histórico limitado de seen_jobs.json como catálogo completo de vagas.
4. Executar Java em modo paralelo de comparação, com notificações desabilitadas, sobre os mesmos lotes.
5. Revisar diferenças no dataset e em pelo menos três ciclos de coleta bem-sucedidos.
6. Eleger um único responsável pelos alertas ao ativar o Java.
7. Em rollback, interromper alertas Java antes de reativar Python e reconciliar registros de entrega.
8. Migrar coletores e encerrar dependência Python após M4.2.

A execução horária é periódica, não garantia de tempo real. Definir no M0 onde Java, PostgreSQL e Hermes ficarão ativos; uma máquina desligada não executa o agente. Hospedagem e custos permanecem decisão pendente.

## 12. Segurança e autonomia do agente

Conteúdo de vagas e e-mails é dado externo, não instrução para o agente. Ferramentas devem validar argumentos e permissões no Java, independentemente do texto gerado pelo modelo.

Na primeira integração, habilitar consulta e triagem. Candidaturas começam assistidas, conforme o fluxo de aprovação da seção 7. Autonomia de envio posterior exige política explícita de escopo, canais, documentos permitidos, limite, auditoria e interrupção.

Nenhum número de envios ou atraso aleatório garante ausência de bloqueio. Quando houver canal automatizado, verificar documentação e regras oficiais desse canal e registrar a decisão antes da implementação. Backoff serve para lidar com erros e limites documentados, não para simular comportamento humano.

Limite futuro: configurável, sem valor universal neste plano. Proposta semântica: janela móvel de 24 horas em UTC, contabilizando envios confirmados e reservando capacidade para operações em andamento/UNKNOWN. A reserva deve ser atômica. Descoberta e ranking continuam quando a capacidade de envio se esgota.

## 13. Como trabalharemos e aprenderemos

- Rafael valida exemplos de vagas, prioridades e resultados; também implementa exercícios e explica decisões Java.
- O assistente prepara tarefas pequenas, explica conceitos, revisa código e verifica os critérios.
- Cada tarefa registra problema, escopo, dependências, critérios, testes e demonstração.
- Trabalhar em uma entrega vertical por vez: entrada -> regra -> persistência -> consulta.
- Revisar semanalmente o que foi entregue e ajustar a próxima etapa, sem prazo fictício para contratação.
- Associar M1 a Java, orientação a objetos, Collections, exceções, JUnit, HTTP e SQL; M2 a integração e confiabilidade; M3 a avaliação e ferramentas de IA.

Definition of Done: comportamento demonstrável, critérios satisfeitos, testes relevantes passando, migração/contrato documentados quando aplicável, sem segredos no diff e explicação por Rafael do fluxo e das principais escolhas.

## 14. Medidas de progresso e decisões pendentes

Medir tempo semanal de triagem, fração de recomendações que Rafael considera úteis, duplicações, falhas de entrega e custo de IA. Registrar numerador, denominador e período; estabelecer metas depois de uma linha de base de duas semanas. Amostrar também vagas rejeitadas para detectar oportunidades perdidas.

Pendências que bloqueiam apenas suas respectivas etapas:
- M0: capacidades do Hermes, ambiente Java/Docker e local de execução.
- M1: tabela de score e dataset aceito.
- M2: limites atuais e contrato da primeira fonte externa.
- M3: provedor/orçamento de IA e primeiro canal de candidatura.
- M4: provedor de e-mail, permissões e correlação de respostas.

## 15. Correções em relação à proposta anterior

- Java passa a ser requisito central do produto.
- Hermes instalado é uma integração a verificar, não um componente presumido.
- Removidas estimativas de 15–30 versus 500–800 candidatos por falta de evidência.
- Removidas promessas de proteção contra banimento e de aumento garantido de leitura.
- Retirados limites fixos 20+5, bypass VIP e simulação humana.
- Separados score, elegibilidade, prioridade e autorização de envio.
- PostgreSQL substitui a proposta de priority_queue.json para o novo sistema.
- Kanban começa como estado interno; provedores externos são opcionais.
- Incluídos idempotência, estados ambíguos, testes, migração, rollback e critérios de conclusão.
- Confirmação humana é uma decisão deste plano, não uma funcionalidade já implementada nos documentos antigos.

Este arquivo é a referência operacional. O ADR-005 registra a direção arquitetural; mudanças de arquitetura devem atualizá-lo. Alterações de prioridade e backlog são registradas aqui.
