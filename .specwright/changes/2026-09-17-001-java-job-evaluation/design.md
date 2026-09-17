---
feature: 001-java-job-evaluation
---
# Java Job Evaluation — Design

**Proposal:** see `proposal.md` for the purpose, acceptance criteria and boundaries.

## Architecture

Implementar um núcleo Java puro, sem Spring, banco ou rede nesta feature. O domínio será organizado por responsabilidade: modelos imutáveis para vaga e perfil, tipos explícitos para classificação e evidência, e um serviço determinístico para avaliação. Essa abordagem permite testar as regras rapidamente e evita acoplar a decisão de negócio à futura API ou infraestrutura.

O fluxo será `Job` + `CandidateProfile` → `JobEvaluator` → `EvaluationResult`. O avaliador aplicará primeiro restrições duras; se uma restrição incompatível for encontrada, retornará `INELIGIBLE`. Se um dado essencial estiver ausente, retornará `NEEDS_REVIEW`. Caso contrário, calculará o score v1 por componentes e retornará `ELIGIBLE`.

O score será limitado aos componentes definidos no plano existente: competências (40), senioridade (30), localização/modalidade (20) e preferências (10). Cada componente produzirá uma evidência; o resultado exporá a soma e as razões. A avaliação não chamará IA e não fará chamadas de rede.

## File Structure

- Create: `backend/pom.xml` — build Maven Java 21 e configuração de testes.
- Create: `backend/src/main/java/com/jobfinder/matching/Job.java` — dados normalizados da vaga.
- Create: `backend/src/main/java/com/jobfinder/matching/CandidateProfile.java` — perfil e restrições do candidato.
- Create: `backend/src/main/java/com/jobfinder/matching/EvaluationStatus.java` — estados possíveis da avaliação.
- Create: `backend/src/main/java/com/jobfinder/matching/Evidence.java` — justificativa observável de uma regra.
- Create: `backend/src/main/java/com/jobfinder/matching/EvaluationResult.java` — resultado, score e evidências.
- Create: `backend/src/main/java/com/jobfinder/matching/JobEvaluator.java` — contrato do caso de uso.
- Create: `backend/src/main/java/com/jobfinder/matching/DeterministicJobEvaluator.java` — implementação das regras v1.
- Create: `backend/src/test/java/com/jobfinder/matching/DeterministicJobEvaluatorTest.java` — testes unitários dos critérios.

## Phase Ordering

1. Configurar o módulo Maven e os tipos do domínio.
2. Escrever testes para elegibilidade, revisão, score, evidências e determinismo.
3. Implementar o avaliador mínimo até os testes passarem.
4. Executar a suíte Java e registrar a conclusão da feature.

## Constraints

- Java 21 é a versão de compilação.
- O módulo deve compilar sem depender de Maven instalado globalmente além do wrapper futuro.
- Não adicionar Spring Boot, PostgreSQL, Hermes ou IA nesta feature.
- Regras de negócio devem ser testáveis sem rede, relógio do sistema ou credenciais.
- Valores desconhecidos não podem ser tratados como favoráveis por padrão.
- Interesse em aprender uma tecnologia não equivale a experiência comprovada.
- O resultado deve preservar a ordem estável das evidências e ser repetível.
