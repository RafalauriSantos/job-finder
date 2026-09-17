# Job Finder — Mapa do Projeto

O Job Finder está evoluindo de um radar Python para uma plataforma Java de busca, avaliação e acompanhamento de vagas, integrada ao Hermes.

## Fluxo principal

[[Job]] → [[001 Java Job Evaluation]] → persistência PostgreSQL → API Java → Hermes

## Fontes de verdade

- Código e histórico: Git.
- Requisitos e tarefas: `.specwright/changes/`.
- Conhecimento e aprendizado: este vault Obsidian.
- Relações entre componentes: Graphify.

## Estado atual

- Núcleo Python legado funcional.
- Fundação Java e avaliador determinístico implementados.
- PostgreSQL, Docker e JDK 21 preparados.
- Hermes ainda será integrado após a API Java.

## Próximo marco

Persistir vagas e avaliações no PostgreSQL e expor uma API mínima em Spring Boot.
