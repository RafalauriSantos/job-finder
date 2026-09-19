---
delivery: radar-inteligente
created: 2026-09-19
---
# Radar Inteligente de Vagas — Delivery

## Purpose

Transformar o Job Finder em um radar multiplataforma capaz de encontrar vagas recentes, interpretar variações reais dos cargos e priorizar oportunidades coerentes com o perfil do Rafael, incluindo posições Júnior e Pleno.

## Motivation

O radar já possui coleta, deduplicação, enriquecimento, entrega e métricas básicas. Ainda há espaço para encontrar vagas que aparecem sob títulos diferentes, reduzir atraso entre publicação e alerta, distinguir aderência de interesse de aprendizado e aprender com as decisões reais do usuário.

## Success Criteria

Uma execução do radar consulta buscas recentes em todas as fontes configuradas, identifica vagas novas sem depender de um único título, ordena os resultados por frescor e aderência, entrega apenas oportunidades dentro dos limites definidos e registra dados suficientes para explicar por que cada vaga foi ou não priorizada.

## Non-Goals

- Candidatar-se automaticamente a vagas.
- Burlar autenticação, CAPTCHA, limites ou regras das plataformas.
- Usar IA generativa como substituta de regras determinísticas sem rastreabilidade.
- Prometer precisão estatística antes de existir feedback humano suficiente.

## Changes

| Order | Change | Depends on |
|---|---|---|
| 1 | 2026-09-19-busca-frescor-multiplataforma | — |
| 2 | 2026-09-19-entendimento-ranking-vagas | 2026-09-19-busca-frescor-multiplataforma |
| 3 | 2026-09-19-feedback-aprendizado-personalizado | 2026-09-19-entendimento-ranking-vagas |
| 4 | 2026-09-19-observabilidade-e-calibracao | 2026-09-19-busca-frescor-multiplataforma |

## Dispatch log

## Blockers

