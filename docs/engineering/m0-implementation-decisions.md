# M0.3 — Decisões de implementação propostas

Status: PREPARADA PARCIALMENTE. Não atende ainda ao aceite de M0.3.

## Base proposta

- Módulo Java em backend/, dentro deste repositório; mantém histórico e migração próximos.
- Pacote raiz br.com.jobfinder; módulos profile, jobs, matching, applications e integrations.
- Java 21 LTS com JDK Temurin 21.0.12.1+1: executáveis java e javac verificados na preparação.
- Spring Boot 4.1.1 como candidato, conforme requisitos oficiais consultados em 2026-09-16; confirmar resolução no build.
- Maven Wrapper e migrações Flyway: fixar versões ao gerar e executar M1.1. PostgreSQL 17.11 já verificado em compose.java.yml, com digest fixado.
- REST para clientes e adaptador MCP para Hermes. Não adicionar MCP antes dos casos de uso.
- Execução de desenvolvimento local; serviço não tem promessa de disponibilidade com a máquina desligada.

Fontes oficiais: [Spring Boot — requisitos](https://docs.spring.io/spring-boot/system-requirements.html), [Temurin — versões](https://adoptium.net/temurin/releases/).
As versões candidatas não constituem um build testado.

## Proposta detalhada de regras v1

Aplicar elegibilidade antes de score; dados decisivos desconhecidos exigem revisão.
- Elegível: vaga técnica aberta, nível estágio/trainee/júnior, região permitida ou remoto explicitamente permitido no Brasil, sem restrição incompatível comprovada.
- Inelegível: cargo não técnico, senioridade bloqueada, localização incompatível, exclusividade PCD incompatível ou graduação completa obrigatória.
- Revisar: nível/modalidade/país desconhecido, exigência de experiência não comprovada, estágio com vínculo acadêmico incerto ou requisitos contraditórios.
- Pleno vai para revisão até decisão de Rafael.
- Requisitos obrigatórios de stack sem evidência de competência vão para revisão; não preencher competência a partir de interesse em aprender.
- Vaga encerrada é arquivada; não entra no ranking ativo.

Para vagas elegíveis:
| Componente | Regra proposta |
| --- | --- |
| Stack (0–40) | 40 × proporção de competências explícitas requeridas cobertas pelo perfil; ausência de requisitos explícitos gera revisão |
| Nível (0–30) | 30 para júnior, estágio ou trainee aceito; outros não entram no ranking elegível |
| Local (0–20) | 20 para remoto Brasil ou presencial/híbrido em região aceita |
| Preferência (0–10) | 5 por empresa prioritária + 5 por foco explícito Java ou IA aplicada |

Compatibilidade textual não prova proficiência. Perfil atual e interesses de aprendizado permanecem separados. Java básico pode atender estágio introdutório; não comprova anos de experiência com Spring.

Identidade: chave única (fonte, ID externo). Similaridade entre fontes apenas sugere relação. Novo conteúdo mantém identidade e cria avaliação versionada.

## Contrato Hermes candidato

Ferramentas iniciais: list_jobs, get_job e get_evaluation. Ferramenta de triagem posterior: review_job, com versão esperada e auditoria. Todas reutilizam os mesmos casos de uso Java da API.

Autenticação por segredo de ambiente e allowlist no Hermes; validação efetiva e permissões no servidor Java. Configuração pessoal só será alterada no marco de integração.

## Condições para concluir M0.3

- Dataset revisado por Rafael.
- Regras de pleno, estágio e experiência obrigatória resolvidas.
- JDK operacional e versões exatas registradas: CONCLUÍDO para JDK; build Maven pendente.
- Docker Engine e PostgreSQL de desenvolvimento verificados: CONCLUÍDO.
- Contrato MCP proposto registrado como decisão de arquitetura, distinguindo suporte do cliente de integração end-to-end.
