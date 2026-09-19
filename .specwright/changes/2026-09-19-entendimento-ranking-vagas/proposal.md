---
feature: entendimento-ranking-vagas
created: 2026-09-19
status: pending
shipped: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Entendimento e Ranking de Vagas — Proposal

## Purpose

Interpretar requisitos e senioridade com mais nuance e produzir uma ordem de prioridade explicável para as vagas encontradas.

## Motivation

Uma vaga pode ser anunciada como Pleno e exigir competências compatíveis com uma transição Júnior, enquanto outra pode usar “desenvolvedor” sem informar senioridade. O ranking precisa separar aderência, frescor e interesse de aprendizado para não perder oportunidades sem esconder riscos.

## Non-Goals

- Inferir contratação ou aprovação.
- Rejeitar automaticamente toda vaga Pleno.
- Usar uma pontuação opaca sem evidências textuais.

## Acceptance Criteria

- [ ] **AC-1** Cada vaga recebe senioridade normalizada entre Júnior, Pleno, Sênior ou desconhecida, com evidências textuais registradas.
- [ ] **AC-2** Cada vaga recebe separadamente pontuação de aderência, pontuação de frescor e pontuação de interesse de aprendizado.
- [ ] **AC-3** Requisitos eliminatórios e sinais de risco aparecem separados dos pontos positivos no motivo do ranking.
- [ ] **AC-4** Duas vagas podem ser comparadas por uma explicação que liste os fatores que aumentaram e reduziram sua prioridade.
- [ ] **AC-5** A ordenação prioriza vagas recentes e aderentes, mas mantém uma categoria visível para oportunidades Pleno plausíveis e vagas de aprendizado.

## Decisions and discoveries

