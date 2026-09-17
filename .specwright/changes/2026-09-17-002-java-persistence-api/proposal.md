---
feature: 002-java-persistence-api
created: 2026-09-17
status: pending
shipped: null
delivery: null
---
# Java Persistence and API — Proposal

## Purpose

Persistir vagas, perfis e avaliações no PostgreSQL e disponibilizar uma API REST mínima para importar, consultar e avaliar vagas.

## Motivation

O avaliador determinístico já existe apenas em memória. Esta feature transforma a regra em um fluxo utilizável: dados sobrevivem ao reinício da aplicação, podem ser consultados por clientes e formam a base futura para Hermes.

## Non-Goals

Esta mudança não inclui coletores externos, Telegram, Hermes, IA generativa, candidatura automática, autenticação externa ou interface web completa.

## Acceptance Criteria

- [ ] **AC-1** A aplicação Spring Boot inicia com PostgreSQL e executa as migrations Flyway sem erro em um banco vazio.
- [ ] **AC-2** `PUT /api/v1/profile` valida um perfil válido, persiste-o e incrementa sua versão.
- [ ] **AC-3** `POST /api/v1/jobs/import` importa um lote válido e informa por item se o registro foi criado, atualizado ou rejeitado.
- [ ] **AC-4** Reimportar a mesma vaga da mesma fonte atualiza seu conteúdo sem criar uma segunda vaga.
- [ ] **AC-5** `GET /api/v1/jobs` retorna vagas persistidas com classificação e score da avaliação mais recente.
- [ ] **AC-6** `POST /api/v1/jobs/{id}/evaluations` avalia a vaga persistida usando o avaliador determinístico e salva o resultado.
- [ ] **AC-7** Reiniciar a aplicação não remove vagas, perfil ou avaliações já persistidos.
- [ ] **AC-8** Erros de validação retornam resposta JSON estruturada com código e status HTTP 4xx.
- [ ] **AC-9** Testes de integração executam com PostgreSQL real via Testcontainers ou ambiente Docker documentado, sem credenciais reais.

## Decisions and discoveries

Nada a registrar neste momento.
