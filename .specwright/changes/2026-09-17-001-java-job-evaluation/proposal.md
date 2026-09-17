---
feature: 001-java-job-evaluation
created: 2026-09-17
status: in-progress
shipped: null
delivery: null
---
# Java Job Evaluation — Proposal

## Purpose

Construir o primeiro fluxo vertical do novo núcleo Java: receber uma vaga e um perfil profissional, avaliar a compatibilidade e devolver uma decisão explicada.

## Motivation

Esta feature transforma as regras de negócio já validadas no sistema Python em uma unidade testável de Java. Ela cria a base para persistência, ranking, Hermes e futuras avaliações com IA sem depender de rede ou de serviços externos.

## Non-Goals

Esta mudança não inclui Spring Boot, PostgreSQL, API REST, Hermes, Telegram, IA generativa, coletores externos, candidatura automática ou interface web. A persistência será planejada separadamente.

## Acceptance Criteria

- [ ] **AC-1** Uma vaga válida e um perfil válido produzem uma avaliação com classificação `ELIGIBLE`, `INELIGIBLE` ou `NEEDS_REVIEW`.
- [ ] **AC-2** Uma restrição explícita incompatível do perfil produz `INELIGIBLE` e identifica a restrição responsável.
- [ ] **AC-3** A ausência de uma informação essencial para decidir elegibilidade produz `NEEDS_REVIEW` e identifica o dado desconhecido.
- [ ] **AC-4** Uma vaga compatível com o perfil produz `ELIGIBLE` e um score numérico explicado por componentes de evidência.
- [ ] **AC-5** A avaliação registra evidências compreensíveis para cada regra aplicada, incluindo a origem do dado quando disponível.
- [ ] **AC-6** Interesse em aprender Java ou IA não é contado como experiência profissional comprovada na avaliação.
- [ ] **AC-7** A mesma vaga, o mesmo perfil e as mesmas regras produzem resultado idêntico em execuções repetidas.
- [ ] **AC-8** Os cenários aprovados do dataset de aceitação relacionados à avaliação são cobertos por testes automatizados Java.
- [ ] **AC-9** A avaliação básica executa sem acesso à rede, credenciais ou provedor de IA.

## Decisions and discoveries

Nada a registrar neste momento.
