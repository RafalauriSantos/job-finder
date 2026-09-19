---
feature: entendimento-ranking-vagas
---
# Entendimento e Ranking de Vagas — Design

## Architecture

Manter a avaliação determinística existente e separar três dimensões: aderência profissional, frescor e interesse de aprendizado. O classificador de senioridade deve produzir rótulo e evidências; o avaliador combina sinais positivos, requisitos eliminatórios e riscos, mas nunca oculta uma vaga Pleno plausível. O resultado final deve carregar uma explicação estruturada, não apenas uma pontuação numérica.

## File Structure

- Modify: `core/scoring.py` — sinais, pesos e senioridade.
- Modify: `core/eligibility.py` — riscos, eliminatórios e explicações.
- Modify: `models/job.py` — componentes do ranking e evidências.
- Modify: `core/metrics.py` — distribuição de categorias e motivos.
- Create: `tests/test_ranking_explanations.py` — contratos do ranking.
- Modify: `tests/test_scoring.py` — casos Pleno, Júnior, Sênior e desconhecido.

## Phase Ordering

1. Fixar o contrato de explicação e testes de classificação.
2. Implementar componentes separados e composição do ranking.
3. Integrar ordenação e saída do alerta.
4. Validar casos reais anonimizados do ciclo.

## Constraints

- Não misturar interesse de aprendizado com aderência principal.
- Senior explícito continua sendo risco forte, salvo evidência de configuração futura.
- Toda pontuação precisa ser explicável por sinais observados no texto ou metadados.

