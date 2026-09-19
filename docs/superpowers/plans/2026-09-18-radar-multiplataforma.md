# Radar Multiplataforma Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aumentar o recall de vagas recentes sem perder precisão, incluindo Pleno como faixa padrão e garantindo que nenhuma vaga aprovada seja perdida por falha de entrega.

**Architecture:** O radar será dividido em planejamento de consultas, coleta paginada, enriquecimento/normalização, avaliação por faixas e entrega confiável. Cada etapa produzirá evidências e métricas; fontes frágeis continuarão substituíveis por adaptadores independentes.

**Tech Stack:** Python existente, `pytest`, configuração JSON, PostgreSQL/estado atual quando aplicável, Telegram e adaptadores HTTP atuais.

**Spec:** Este plano é a especificação operacional derivada da auditoria do radar e das decisões discutidas nesta conversa.

## Global Constraints

- Não usar bypass de CAPTCHA, simulação de pessoa ou credenciais persistentes.
- Respeitar limites, termos e endpoints oficiais/disponíveis de cada plataforma.
- Pleno não será bloqueado apenas pelo título; liderança explícita continua bloqueada.
- RSS será descoberta/enriquecimento auxiliar, não evidência suficiente isolada para alerta.
- Toda mudança relevante deve ter teste automatizado e feature flag reversível.
- Não marcar vaga como vista antes de confirmar a entrega ou registrar pendência de retry.

---

## Subprojeto 1: Entrega confiável

**Arquivos:** `monitor.py`, `storage/state_store.py`, `notify/telegram_notifier.py`, novos testes em `tests/`.

- [ ] Escrever testes para: falha do Telegram não marcar vaga como vista; retry não duplicar mensagem; sucesso registrar `DELIVERED`.
- [ ] Criar estados `DISCOVERED`, `APPROVED`, `PENDING_DELIVERY`, `DELIVERED`, `DELIVERY_FAILED` e uma chave idempotente por fingerprint.
- [ ] Alterar o fluxo para marcar `seen` somente após sucesso ou após persistir uma pendência recuperável.
- [ ] Adicionar retry com limite, backoff e registro do erro sem bloquear o restante do ciclo.
- [ ] Validar com `python -m pytest -q` e commit isolado: `fix: make job delivery durable`.

**Pronto quando:** uma indisponibilidade temporária do Telegram não elimina uma vaga aprovada nem gera alertas duplicados.

## Subprojeto 2: Instrumentação e auditoria em sombra

**Arquivos:** `monitor.py`, `core/`, `storage/state_store.py`, `config.json`, testes de qualidade.

- [ ] Registrar por consulta: fonte, parâmetros, horário, candidatos encontrados, novos, descartados, motivo, páginas e latência.
- [ ] Persistir `query_id`, `query_family`, data de publicação, evidência e fonte de descoberta junto da decisão.
- [ ] Executar uma semana em `shadow_mode`, sem ampliar alertas, comparando amostra manual com vagas encontradas e perdidas.
- [ ] Criar relatório diário de saúde: recall estimado, precisão, duplicatas, falhas por fonte, idade média e alertas enviados.

**Pronto quando:** for possível explicar por que cada vaga foi encontrada, descartada, não enviada ou não entregue.

## Subprojeto 3: Planejador de consultas recentes

**Arquivos:** novo `core/query_planner.py`, `config.json`, `gupy_collector.py`, `linkedin_collector.py`, `trampos_collector.py`.

- [ ] Definir famílias de busca: `dev`, `desenvolvedor`, `developer`, `programador`, `analista de sistemas`, `software`, `Java`, `React`, `Node`, `Full Stack`, além das combinações por senioridade.
- [ ] Modelar consulta com `source`, `keywords`, localização, remoto, contrato, nível, janela temporal, página e prioridade.
- [ ] LinkedIn: aceitar `f_TPR` configurável (`r3600`, `r21600`, `r43200`, `r86400`), filtros equivalentes à UI, paginação e parada por vagas antigas/duplicadas. `currentJobId` não será tratado como filtro.
- [ ] Gupy: testar e usar somente parâmetros realmente aceitos pelo contrato `search_jobs`, com ordenação/data quando suportadas; registrar explicitamente limitações e não fingir filtros não suportados.
- [ ] Executar janelas curtas em cada ciclo e uma janela de recuperação menos restritiva, evitando dependência de uma única consulta.
- [ ] Adicionar testes de montagem de parâmetros e de paginação.

**Pronto quando:** cada ciclo consulta vagas recentes em múltiplas famílias e mostra nos logs exatamente quais parâmetros foram enviados.

## Subprojeto 4: Enriquecimento, normalização e deduplicação

**Arquivos:** `core/deduplicator.py`, `core/normalizer.py`, `core/url_resolver.py`, coletores, novos testes.

- [ ] Buscar detalhes quando permitido para LinkedIn/Gupy e resolver links intermediários de RSS; manter fallback do cartão original.
- [ ] Criar uma pontuação de riqueza da vaga baseada em descrição, data, localização, regime, tecnologias, salário e URL final.
- [ ] Fazer merge preservando o registro mais rico e acumulando todas as fontes, consultas e URLs; não deixar RSS raso substituir Gupy/LinkedIn estruturado.
- [ ] Melhorar identidade com URL canônica, identificador da fonte, empresa, título normalizado e localização, sem fundir empresas diferentes.
- [ ] Testar variantes de título, ordem de chegada RSS-primeiro e duplicatas entre plataformas.

**Pronto quando:** a mesma vaga chega uma vez, com a melhor descrição disponível e rastreabilidade de todas as origens.

## Subprojeto 5: Avaliação por faixa, incluindo Pleno

**Arquivos:** `core/scoring.py`, `core/evidence.py`, `profile.json`, testes de scoring/benchmark.

- [ ] Separar `ENTRY_JUNIOR`, `MID_COMPATIBLE`, `MID_STRETCH` e `SENIOR_BLOCKED`.
- [ ] Bloquear apenas sinais explícitos de liderança/senioridade incompatível, como `senior`, `lead`, `staff`, `principal`, gestão ou arquitetura; `pleno` vira alerta avaliável.
- [ ] Criar penalização por requisitos, não por título: anos de experiência, liderança, graduação obrigatória, stack ausente e localização incompatível.
- [ ] Dar bônus a stack central e projetos demonstráveis, mantendo score e elegibilidade separados.
- [ ] Incluir razões visíveis no Telegram: faixa, aderências, lacunas, idade da vaga e nível de risco.
- [ ] Atualizar o benchmark com casos Junior, Pleno compatível, Pleno stretch e Senior bloqueado.

**Pronto quando:** uma vaga Pleno com stack compatível e sem requisito eliminatório pode ser enviada; uma vaga Senior explícita continua fora.

## Subprojeto 6: Expansão controlada de fontes

**Arquivos:** novos/adaptados coletores para Indeed, Sólides e páginas de carreira; `config.json`; testes de contrato.

- [ ] Priorizar Gupy e LinkedIn, depois Indeed/Sólides/Trampos e career pages com fonte estruturada.
- [ ] Dar a cada adaptador o mesmo contrato: consulta, coleta paginada, normalização, evidência, health check e contadores.
- [ ] Colocar RSS em modo descoberta: só alertar após enriquecimento ou confirmação por fonte estruturada.
- [ ] Aplicar quotas por fonte e teto de alertas por ciclo para que aumento de recall não vire ruído.

**Pronto quando:** uma fonte com falha não derruba o ciclo e cada vaga informa sua procedência e nível de confiança.

## Subprojeto 7: Feedback e calibração

**Arquivos:** `notify/telegram_notifier.py`, `storage/state_store.py`, relatório de métricas e testes.

- [ ] Adicionar ações de feedback: relevante, ignorar, já candidatei e falso positivo.
- [ ] Medir por consulta e fonte: vagas úteis, descartes corretos, duplicatas, atraso, taxa de entrega e conversão para candidatura.
- [ ] Revisar semanalmente amostra de vagas não enviadas para detectar falso negativo.
- [ ] Ajustar pesos e famílias de busca somente após evidência, mantendo versão da configuração.

**Pronto quando:** o radar aprende com decisões reais sem alterar silenciosamente o comportamento.

## Ordem de implantação

1. Entrega confiável e instrumentação, mantendo o comportamento atual.
2. Planejador LinkedIn/Gupy em sombra.
3. Enriquecimento e deduplicação corrigida.
4. Faixa Pleno em canário com limite de alertas.
5. Expansão para Indeed, Sólides, Trampos e career pages.
6. Feedback, métricas e ajuste periódico.

## Feature flags e rollback

- `delivery_outbox`
- `query_planner_v2`
- `linkedin_recent_windows`
- `detail_enrichment`
- `mid_compatible_band`
- `source_expansion`

Cada fase deve permitir desligar sua flag e voltar à configuração anterior sem apagar histórico. O rollout começa em sombra, passa por canário e só então vira padrão.

## Critérios finais de sucesso

- Nenhuma vaga aprovada é perdida por falha transitória de notificação.
- O radar busca repetidamente janelas recentes e pagina resultados.
- Pleno compatível aparece sem abrir a porta para Senior explícito.
- Duplicatas e RSS de baixa evidência deixam de dominar os alertas.
- Há métricas para saber quais consultas e fontes realmente trazem candidaturas úteis.
- A suíte de testes permanece verde antes de cada ativação.
