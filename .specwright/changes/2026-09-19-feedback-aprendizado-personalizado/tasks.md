---
feature: feedback-aprendizado-personalizado
created: 2026-09-19
scope: high
branch: codex/feedback-aprendizado-personalizado
worktree: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Feedback e Aprendizado Personalizado — Tasks

## Tasks

### T1: Persistir eventos humanos de vaga

**AC:** AC-1, AC-2, AC-5
**Files:**
- Modify: `storage/state_store.py`
- Create: `core/feedback.py`
- Create: `tests/test_feedback.py`
- Modify: `tests/test_state_store.py`
**Validation:** `pytest -q tests/test_feedback.py tests/test_state_store.py`

- [ ] Escrever testes para os cinco eventos, contexto, data e desfazer.
- [ ] Executar os testes e confirmar a falha da persistência.
- [ ] Implementar eventos append-only e leitura compatível com estado antigo.
- [ ] Executar os testes e confirmar aprovação.
- [ ] Commitar a alteração.

### T2: Agregar sinais sem alterar o ranking

**AC:** AC-4
**Files:**
- Modify: `core/feedback.py`
- Create: `tests/test_feedback_summary.py`
**Validation:** `pytest -q tests/test_feedback_summary.py`

- [ ] Escrever teste de resumo por termo, senioridade e fonte.
- [ ] Executar o teste e confirmar a falha da agregação.
- [ ] Implementar resumo reproduzível e ordenado.
- [ ] Executar o teste e confirmar aprovação.
- [ ] Commitar a alteração.

### T3: Aplicar ajuste limitado após limiar

**AC:** AC-3
**Files:**
- Modify: `core/feedback.py`
- Modify: `core/scoring.py`
- Modify: `tests/test_scoring.py`
**Validation:** `pytest -q tests/test_feedback.py tests/test_scoring.py`

- [ ] Escrever testes abaixo e acima do limiar configurado.
- [ ] Executar os testes e confirmar a falha do comportamento adaptativo.
- [ ] Implementar ajuste limitado com versão do perfil aprendido.
- [ ] Executar os testes e confirmar aprovação.
- [ ] Commitar a alteração.

