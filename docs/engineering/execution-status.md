# Acompanhamento da execução

Atualizado em 2026-09-16. Plano: [Job Finder Java](hermes-java-project-plan.md).
Regra: marcar concluído somente após verificar o critério; preparação técnica e validação de produto são registradas separadamente.

| Tarefa | Estado | Evidência / próximo passo |
| --- | --- | --- |
| M0.1 | CONCLUÍDA | [Inventário](m0-environment-inventory.md); Hermes identificado; baseline de 90 testes; dependências ausentes documentadas |
| M0.2 | EM VALIDAÇÃO | 24 cenários sintéticos preparados em tests/fixtures/acceptance/jobs-v1.json; classificação proposta pelo assistente, aguardando Rafael |
| M0.3 | PREPARADA PARCIALMENTE | [Decisões propostas](m0-implementation-decisions.md); depende da validação M0.2 e do build Maven |
| M1.1 | PENDENTE | JDK e banco prontos; esqueleto Java aguarda decisões M0.3 |
| M1.2–M1.5 | PENDENTES | Dependem dos marcos anteriores |
| M2.1–M2.3 | PENDENTES | Coleta, alertas e integração |
| M3.1–M3.3 | PENDENTES | IA e candidaturas assistidas |
| M4.1–M4.2 | PENDENTES | Feedback e conclusão da migração |

## Histórico

- M0.1: iniciada inspeção read-only; suporte MCP confirmado no código local; versão confirmada pela CLI.
- Baseline Python: 90 testes passaram na worktree feat/java-foundation.
- M0.1 concluída; iniciada M0.2.
- M0.2: conjunto de aceitação e guia de revisão preparados. Nenhuma classificação é atribuída a Rafael sem sua revisão.
- M0.3: rascunho técnico preparado como trabalho independente; não aprovado nem implementado.
- Preparo independente: JDK portátil 21.0.12.1 com SHA-256 verificado; java e javac respondem. Docker Engine iniciado; PostgreSQL 17.11 saudável e SELECT version() executado. Compose com imagem fixada por digest.
- Validação: 92 testes Python passaram, incluindo integridade e relações de identidade do dataset. Nenhum teste de scoring Java foi executado: ainda não há implementação Java.

## Próxima ação

Rafael revisa os casos de [aceitação](m0-acceptance-review.md), especialmente os marcados para decisão. A autorização genérica para executar o projeto não constitui rótulo individual dos exemplos.
