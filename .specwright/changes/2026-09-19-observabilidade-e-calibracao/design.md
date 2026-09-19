---
feature: observabilidade-e-calibracao
---
# Observabilidade e Calibração — Design

## Architecture

Expandir o resumo de ciclo existente com uma sequência uniforme de contadores e idades: coletado, normalizado, deduplicado, elegível, priorizado, entregue e feedback posterior. A saúde da fonte continuará separada da qualidade da vaga. Um relatório de calibração comparará períodos usando feedback humano e declarará N/D quando a amostra for insuficiente.

## File Structure

- Modify: `core/metrics.py` — métricas de funil, idade e calibração.
- Modify: `storage/state_store.py` — histórico de ciclos e consultas.
- Modify: `monitor.py` — emissão do relatório.
- Modify: `docs/OPERATIONS.md` — interpretação e comandos.
- Create: `tests/test_calibration_metrics.py` — métricas sem feedback e com feedback.
- Modify: `tests/test_monitor.py` — integração do relatório.

## Phase Ordering

1. Definir contratos métricos e casos N/D.
2. Persistir histórico mínimo por ciclo.
3. Criar comparação de períodos.
4. Validar relatório em execução controlada.

## Constraints

- Volume nunca será apresentado como precisão.
- Precisão e recall permanecem N/D sem rótulos humanos suficientes.
- Nenhum dado de credencial será incluído no histórico.

