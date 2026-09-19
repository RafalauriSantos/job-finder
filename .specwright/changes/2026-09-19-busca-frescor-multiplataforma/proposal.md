---
feature: busca-frescor-multiplataforma
created: 2026-09-19
status: in-progress
shipped: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Busca com Frescor Multiplataforma — Proposal

## Purpose

Garantir que cada fonte seja consultada com variações de termos e filtros de publicação recente, preservando a data original da vaga quando disponível.

## Motivation

Vagas relevantes podem usar títulos diferentes de “desenvolvedor júnior”. LinkedIn, Gupy e outras plataformas também expõem filtros temporais que precisam ser usados de forma explícita para que a oportunidade chegue enquanto ainda está ativa.

## Non-Goals

- Criar scraping que contorne bloqueios da plataforma.
- Garantir que toda vaga publicada seja encontrada.
- Alterar automaticamente o perfil profissional do usuário.

## Acceptance Criteria

- [ ] **AC-1** Cada execução registra, por fonte e consulta, o termo usado, o filtro temporal aplicado, o horário de início e a quantidade de resultados retornados.
- [ ] **AC-2** O planejador executa consultas para Júnior, Pleno e títulos equivalentes definidos no perfil, incluindo pelo menos variações de desenvolvedor, developer, backend, full stack e Java.
- [ ] **AC-3** Uma vaga com data de publicação disponível é classificada como recente, antiga ou desconhecida usando uma regra documentada e testada.
- [ ] **AC-4** Uma vaga recente encontrada em duas consultas ou fontes é consolidada em um único registro, preservando a melhor data, descrição e origem observadas.
- [ ] **AC-5** Quando uma fonte falhar ou retornar vazio, o relatório diferencia esses casos e a execução continua nas demais fontes.

## Decisions and discoveries
