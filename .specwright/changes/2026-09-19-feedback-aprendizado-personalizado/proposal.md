---
feature: feedback-aprendizado-personalizado
created: 2026-09-19
status: pending
shipped: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Feedback e Aprendizado Personalizado — Proposal

## Purpose

Permitir que as decisões do Rafael sobre vagas ajustem o radar de forma gradual e auditável.

## Motivation

O usuário já encontrou e se candidatou a vagas que o bot não enviou, inclusive oportunidades Pleno com requisitos próximos de Júnior. Sem registrar esse feedback, o sistema repete os mesmos filtros estreitos.

## Non-Goals

- Treinar um modelo estatístico antes de haver volume mínimo de feedback.
- Tomar decisões de candidatura no lugar do usuário.
- Armazenar credenciais de plataformas.

## Acceptance Criteria

- [ ] **AC-1** O sistema aceita, para cada vaga, os eventos “interessante”, “candidatei”, “ignorar”, “fora do perfil” e “já vista”.
- [ ] **AC-2** Cada evento registra data, vaga, fonte e contexto de pontuação que estava vigente no momento da decisão.
- [ ] **AC-3** O ranking usa feedback acumulado para ajustar pesos ou consultas somente depois de um limiar configurado e documentado.
- [ ] **AC-4** O relatório mostra quais termos, senioridades e fontes geraram vagas marcadas como interessantes ou candidatadas.
- [ ] **AC-5** O usuário consegue desfazer um feedback sem apagar o histórico original do evento.

## Decisions and discoveries

