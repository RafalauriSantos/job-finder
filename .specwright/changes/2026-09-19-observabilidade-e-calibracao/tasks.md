---
feature: observabilidade-e-calibracao
created: 2026-09-19
scope: medium
branch: codex/observabilidade-e-calibracao
worktree: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Observabilidade e Calibração — Tasks

## Tasks

### T1: Definir funil e métricas honestas

**AC:** AC-1, AC-2, AC-4
**Files:**
- Modify: `core/metrics.py`
- Create: `tests/test_calibration_metrics.py`
**Validation:** `pytest -q tests/test_calibration_metrics.py`

- [ ] Escrever testes para contadores do funil, idade e N/D.
- [ ] Executar os testes e confirmar a falha das métricas novas.
- [ ] Implementar o resumo sem alterar métricas existentes incompatíveis.
- [ ] Executar o teste e confirmar aprovação.
- [ ] Commitar a alteração.

### T2: Persistir histórico de ciclos e consultas

**AC:** AC-1, AC-3, AC-4
**Files:**
- Modify: `storage/state_store.py`
- Modify: `monitor.py`
- Modify: `tests/test_state_store.py`
**Validation:** `pytest -q tests/test_state_store.py tests/test_monitor.py`

- [ ] Escrever teste para dois ciclos, consulta sem resultado e falha técnica.
- [ ] Executar os testes e confirmar a falha da persistência histórica.
- [ ] Implementar histórico limitado e rotação configurável.
- [ ] Executar os testes e confirmar aprovação.
- [ ] Commitar a alteração.

### T3: Comparar períodos de calibração

**AC:** AC-5
**Files:**
- Modify: `core/metrics.py`
- Modify: `docs/OPERATIONS.md`
- Modify: `tests/test_calibration_metrics.py`
**Validation:** `pytest -q tests/test_calibration_metrics.py`

- [ ] Escrever teste com período anterior, posterior e feedback insuficiente.
- [ ] Executar o teste e confirmar a falha da comparação.
- [ ] Implementar comparação por vagas úteis marcadas, sem chamar volume de precisão.
- [ ] Executar o teste e confirmar aprovação.
- [ ] Commitar a alteração.

