---
feature: observabilidade-e-calibracao
created: 2026-09-19
status: pending
shipped: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Observabilidade e Calibração — Proposal

## Purpose

Medir se o radar está encontrando, selecionando e entregando vagas úteis, permitindo recalibrar o comportamento com evidências.

## Motivation

Quantidade de resultados e quantidade de alertas não provam qualidade. É necessário distinguir falha de busca, duplicação, baixa aderência, atraso de entrega e ausência de feedback humano.

## Non-Goals

- Declarar melhoria de precisão sem amostra de feedback.
- Criar painel web nesta etapa.
- Medir conversão em entrevista sem dados fornecidos pelo usuário.

## Acceptance Criteria

- [ ] **AC-1** Cada ciclo gera métricas por fonte, consulta, quantidade bruta, deduplicada, filtrada, entregue, falha e tempo de execução.
- [ ] **AC-2** O relatório informa explicitamente quando precisão e recall não podem ser calculados por falta de feedback.
- [ ] **AC-3** O sistema identifica consultas sem resultado por ciclos consecutivos e as diferencia de falhas técnicas.
- [ ] **AC-4** O sistema registra a idade da vaga no momento da descoberta e no momento do alerta.
- [ ] **AC-5** Um relatório de calibração permite comparar um período anterior e posterior por vagas úteis marcadas pelo usuário, sem usar apenas volume como indicador.

## Decisions and discoveries

