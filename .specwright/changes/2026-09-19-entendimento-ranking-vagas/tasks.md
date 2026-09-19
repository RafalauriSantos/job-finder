---
feature: entendimento-ranking-vagas
created: 2026-09-19
scope: high
branch: codex/entendimento-ranking-vagas
worktree: null
delivery: .specwright/deliveries/2026-09-19-radar-inteligente
---
# Entendimento e Ranking de Vagas — Tasks

## Tasks

### T1: Fixar contrato de explicação do ranking

**AC:** AC-1, AC-2, AC-3, AC-4
**Files:**
- Modify: `models/job.py`
- Create: `tests/test_ranking_explanations.py`
**Validation:** `pytest -q tests/test_ranking_explanations.py`

- [x] Escrever testes para componentes separados, evidências e riscos.
- [x] Executar os testes e confirmar a falha por ausência do contrato.
- [x] Implementar os campos estruturados mantendo serialização compatível.
- [x] Executar os testes e confirmar aprovação.
- [x] Commitar a alteração.

### T2: Recalibrar senioridade e aderência

**AC:** AC-1, AC-3, AC-5
**Files:**
- Modify: `core/scoring.py`
- Modify: `core/eligibility.py`
- Modify: `tests/test_scoring.py`
**Validation:** `pytest -q tests/test_scoring.py tests/test_eligibility.py`

- [x] Adicionar testes para Pleno compatível, Pleno incompatível, Sênior e senioridade ausente.
- [x] Executar os testes e confirmar as falhas dos casos novos.
- [x] Implementar regras e evidências sem eliminar oportunidades de aprendizado.
- [x] Executar os testes e confirmar aprovação.
- [x] Commitar a alteração.

### T3: Ordenar e explicar as categorias do alerta

**AC:** AC-2, AC-4, AC-5
**Files:**
- Modify: `monitor.py`
- Modify: `notify/telegram.py`
- Modify: `tests/test_monitor.py`
**Validation:** `pytest -q tests/test_monitor.py`

- [x] Escrever teste de ordem com vaga recente aderente, Pleno plausível e aprendizado.
- [x] Executar o teste e confirmar a falha da ordenação esperada.
- [x] Implementar composição do ranking e texto curto de justificativa.
- [x] Executar os testes e confirmar aprovação.
- [x] Commitar a alteração.
