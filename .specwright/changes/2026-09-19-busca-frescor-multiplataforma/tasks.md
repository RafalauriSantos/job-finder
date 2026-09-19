---
feature: busca-frescor-multiplataforma
created: 2026-09-19
scope: high
branch: codex/busca-frescor-multiplataforma
worktree: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Busca com Frescor Multiplataforma — Tasks

## Tasks

### T1: Planejar consultas com intenção, senioridade e frescor

**AC:** AC-1, AC-2
**Files:**
- Modify: `core/query_planner.py`
- Modify: `config.json`
- Create: `tests/test_query_planner_freshness.py`
**Validation:** `pytest -q tests/test_query_planner_freshness.py`

- [x] Escrever testes para variantes de cargo, Júnior/Pleno e janela temporal.
- [x] Executar os testes e confirmar a falha por ausência dos novos campos.
- [x] Implementar o modelo normalizado de consulta sem remover compatibilidade com a configuração atual.
- [x] Executar `pytest -q tests/test_query_planner_freshness.py` e confirmar aprovação.
- [x] Commitar a alteração.

### T2: Aplicar filtros temporais nos coletores

**AC:** AC-1, AC-3, AC-5
**Files:**
- Modify: `collectors/linkedin.py`
- Modify: `collectors/gupy.py`
- Modify: `tests/test_collectors.py`
**Validation:** `pytest -q tests/test_linkedin_collector.py tests/test_gupy_collector.py`

- [x] Escrever testes de payload com filtro recente, resultado vazio, erro HTTP e erro de transporte.
- [x] Executar os testes e confirmar a falha nos contratos temporais.
- [x] Implementar a propagação dos filtros e o registro por consulta.
- [x] Executar `pytest -q tests/test_linkedin_collector.py tests/test_gupy_collector.py` e confirmar aprovação.
- [x] Commitar a alteração.

### T3: Normalizar publicação e idade da descoberta

**AC:** AC-3, AC-4
**Files:**
- Modify: `models/job.py`
- Modify: `core/metrics.py`
- Modify: `tests/test_metrics.py`
**Validation:** `pytest -q tests/test_publication_dates.py tests/test_deduplicator_richness.py`

- [x] Escrever testes para data ISO, timestamp, data ausente e conflito entre fontes.
- [x] Executar os testes e confirmar a falha nos casos novos.
- [x] Implementar a classificação recente/antiga/desconhecida e a preferência pela melhor evidência.
- [x] Executar `pytest -q tests/test_publication_dates.py tests/test_deduplicator_richness.py` e confirmar aprovação.
- [x] Commitar a alteração.

### T4: Validar o ciclo completo de busca

**AC:** AC-1, AC-2, AC-4, AC-5
**Files:**
- Modify: `monitor.py`
- Modify: `tests/test_monitor.py`
- Modify: `docs/OPERATIONS.md`
**Validation:** `pytest -q`

- [ ] Adicionar teste de ciclo com múltiplas consultas, duplicata entre fontes e uma fonte indisponível.
- [ ] Executar o teste isolado e confirmar a falha antes da integração.
- [ ] Integrar telemetria e regras sem ultrapassar o orçamento de ciclo.
- [ ] Executar `pytest -q` e `python -m compileall -q core collectors models notify storage monitor.py`.
- [ ] Commitar a alteração.
