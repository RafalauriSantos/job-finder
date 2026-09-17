---
feature: 001-java-job-evaluation
created: 2026-09-17
scope: medium
branch: feat/java-foundation
worktree: C:/Users/Rafael lauri/Documents/Codex/2026-09-16/que/work/job-finder-java
delivery: null
---
# Java Job Evaluation — Tasks

**Proposal:** `proposal.md` contém o objetivo e os critérios AC-N. **Design:** `design.md` contém a arquitetura.

## Tasks

### T1: Configurar o módulo Java e os tipos de domínio

**AC:** AC-1, AC-4, AC-5
**Files:**
- Create: `backend/pom.xml`
- Create: `backend/src/main/java/com/jobfinder/matching/Job.java`
- Create: `backend/src/main/java/com/jobfinder/matching/CandidateProfile.java`
- Create: `backend/src/main/java/com/jobfinder/matching/EvaluationStatus.java`
- Create: `backend/src/main/java/com/jobfinder/matching/Evidence.java`
- Create: `backend/src/main/java/com/jobfinder/matching/EvaluationResult.java`
- Create: `backend/src/main/java/com/jobfinder/matching/JobEvaluator.java`
**Validation:** `mvn -f backend/pom.xml test -q`

- [x] Criar o `pom.xml` com Java 21, JUnit Jupiter e `maven-surefire-plugin`.
- [x] Criar records imutáveis para vaga, perfil, evidência e resultado, com enums para status.
- [x] Executar `mvn -f backend/pom.xml test -q` e confirmar compilação sem testes.
- [x] Commitar a configuração e os tipos de domínio.

### T2: Definir testes de aceitação do avaliador

**AC:** AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9
**Files:**
- Create: `backend/src/test/java/com/jobfinder/matching/DeterministicJobEvaluatorTest.java`
**Validation:** `mvn -f backend/pom.xml -Dtest=DeterministicJobEvaluatorTest test -q`

- [x] Escrever testes para vaga elegível, incompatibilidade explícita e informação essencial desconhecida.
- [x] Escrever testes para score por componentes, evidências, interesse em aprender e execução repetida.
- [x] Escrever testes que executem apenas objetos em memória e não configurem clientes HTTP ou IA.
- [x] Executar `mvn -f backend/pom.xml -Dtest=DeterministicJobEvaluatorTest test -q` e confirmar falhas por implementação ausente.
- [x] Commitar os testes falhando como contrato executável.

### T3: Implementar o avaliador determinístico

**AC:** AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9
**Files:**
- Create: `backend/src/main/java/com/jobfinder/matching/DeterministicJobEvaluator.java`
- Modify: `backend/src/test/java/com/jobfinder/matching/DeterministicJobEvaluatorTest.java`
**Validation:** `mvn -f backend/pom.xml test -q`

- [x] Implementar a interface `JobEvaluator` aplicando restrições duras antes do score.
- [x] Implementar compatibilidade de competências, senioridade, localização/modalidade e preferências com limites 40/30/20/10.
- [x] Emitir evidência textual para cada decisão e manter ordem determinística.
- [x] Retornar `NEEDS_REVIEW` para modalidade, senioridade ou requisito essencial desconhecido.
- [x] Ignorar frases de interesse em aprender ao calcular experiência comprovada.
- [x] Executar `mvn -f backend/pom.xml test -q` e confirmar todos os testes passando.
- [x] Commitar a implementação do avaliador.

### T4: Verificar o handoff da feature

**AC:** AC-7, AC-8, AC-9
**Files:**
- Modify: `.specwright/changes/2026-09-17-001-java-job-evaluation/proposal.md`
- Modify: `.specwright/changes/2026-09-17-001-java-job-evaluation/tasks.md`
**Validation:** `mvn -f backend/pom.xml test -q`

- [x] Executar a suíte Java completa e registrar o comando e o resultado.
- [x] Marcar os critérios comprovados e as tarefas concluídas somente após a execução passar.
- [x] Registrar em `proposal.md` qualquer descoberta não óbvia encontrada durante os testes.
- [x] Commitar o estado final da feature.
