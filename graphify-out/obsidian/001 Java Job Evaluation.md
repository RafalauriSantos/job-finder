# 001 Java Job Evaluation

## Objetivo

Avaliar uma vaga contra o perfil do Rafael e devolver uma decisão explicável.

## Resultado

O avaliador Java determinístico produz:

- `ELIGIBLE`: vaga compatível;
- `INELIGIBLE`: restrição explícita incompatível;
- `NEEDS_REVIEW`: informação essencial desconhecida.

## Conceitos Java praticados

- `record` para modelos imutáveis;
- `enum` para estados controlados;
- interface para o contrato do caso de uso;
- composição de objetos;
- testes unitários com JUnit;
- normalização de texto;
- resultados determinísticos.

## Decisão arquitetural

A avaliação básica não depende de Spring, banco, rede ou IA. Isso mantém a regra de negócio barata, testável e previsível.

## Relações

- Entrada: [[CandidateProfile]] e [[Job]]
- Contrato: [[JobEvaluator]]
- Implementação: [[DeterministicJobEvaluator]]
- Saída: [[EvaluationResult]]
- Próxima evolução: persistência PostgreSQL
