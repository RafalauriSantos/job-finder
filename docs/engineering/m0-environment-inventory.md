# M0.1 — Inventário do ambiente e Hermes

Status: CONCLUÍDO (levantamento). Data: 2026-09-16.
Conclusão do inventário não significa que o ambiente Java esteja pronto.

## Evidências

| Item | Resultado observado | Consequência |
| --- | --- | --- |
| Hermes CLI | v0.20.5 (2026.8.19), Python 3.11.16, OpenAI SDK 2.24.0 | Instalação identificada; não atualizada |
| Fonte Hermes | checkout f751a8c546; CLI informa upstream ead7e91d | Registrar ambas as identificações; não presumir checkout idêntico ao upstream |
| MCP | Código e documentação locais suportam stdio e HTTP, headers, OAuth e allowlist | Preferência técnica: adaptador Java MCP sobre casos de uso do backend |
| JDK / javac | Não encontrados no PATH, JAVA_HOME nem diretórios comuns consultados | Preparar JDK antes de M1.1; não alegar ausência em todo o disco |
| Maven | Não encontrado no PATH | Projeto deverá incluir Maven Wrapper |
| Docker CLI | 29.6.1, API 1.55, contexto desktop-linux | Cliente instalado |
| Docker Compose | v5.3.0 | Disponível |
| Docker Engine | Pipe dockerDesktopLinuxEngine indisponível | Banco em container e Testcontainers ainda não executáveis |
| PostgreSQL | psql e serviço não encontrados na consulta | Não foi validada uma instância local |
| Python do projeto | pytest: 90 passed, 2.73s | Baseline verificado na worktree |

## Execução reproduzível

O launcher hermes --version demorou sem produzir saída e a chamada criada nesta tarefa foi interrompida. A execução direta pelo ambiente da instalação retornou a versão:

```powershell
& "$env:LOCALAPPDATA/hermes/hermes-agent/venv/Scripts/python.exe" -m hermes_cli.main --version
Get-Command java,javac,mvn,docker,hermes -ErrorAction SilentlyContinue
docker version
docker compose version
pytest -q
```

A consulta de versão anunciou atualização disponível. Nenhuma atualização do Hermes foi realizada.

## Integração confirmada por inspeção

Na instalação local, foram consultados:
- pyproject.toml e hermes_cli/__init__.py: versão.
- hermes_cli/subcommands/mcp.py: add, test, list, configure; opções de URL, comando e autenticação.
- website/docs/reference/mcp-config-reference.md: HTTP/stdio, headers, OAuth, interpolação de ambiente e ferramentas permitidas.
- website/docs/guides/use-mcp-with-hermes.md: descoberta e integração.

Autenticação suportada não significa credenciais configuradas ou conexão validada. Não foram lidos .env, auth.json, tokens, sessões, e-mails ou o conteúdo da configuração pessoal.

O contrato inicial proposto é MCP HTTP com ferramentas de consulta, implementado no Java quando a API já estiver testada. REST sozinho não é MCP. A biblioteca, transporte efetivo e handshake serão comprovados em M2.3, incluindo acesso negado e repetição de chamadas.

## Pendências operacionais

1. Instalar ou disponibilizar JDK e fixar a versão do build.
2. Iniciar Docker Engine e comprovar execução de um PostgreSQL isolado de desenvolvimento.
3. Definir execução local inicial; disponibilidade permanente fica para implantação.
4. Testar integração Hermes–Java quando existir serviço Java.

## Preparação realizada após o inventário

- JDK Temurin 21.0.12.1+1 portátil em work/toolchains/jdk-21.0.12.1+1 na área desta tarefa Codex; PATH global não alterado. java -version e javac -version responderam.
- Arquivo oficial OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.zip, SHA-256 f9d6e191ab098c0d416e7d588a24420a8621cd2f4720dab2459b8b7b2d2d8b4e, comparado com metadata da API Adoptium antes da extração.
- Docker Desktop iniciado; Docker Engine 29.6.1 operacional.
- compose.java.yml criou ambiente jobfinder-java-dev, banco jobfinder, usuário jobfinder_dev, porta somente 127.0.0.1:5433 e volume dedicado java_pgdata.
- PostgreSQL 17.11 confirmado por SELECT version(), current_database(); healthcheck saudável.
- Imagem fixada por digest: sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73.
- A senha no Compose é demonstrativa, exclusivamente local. Não usar esse Compose como configuração de produção.

Reprodução, a partir da raiz do repositório:

```powershell
docker compose -f compose.java.yml up -d --wait
docker compose -f compose.java.yml exec -T postgres psql -U jobfinder_dev -d jobfinder -c 'SELECT version();'
docker compose -f compose.java.yml stop
```

O JDK não está versionado. Em outra máquina, disponibilizar JDK 21 e configurar JAVA_HOME para essa instalação. A etapa M1.1 incluirá Maven Wrapper e comandos de build.

Referências: [Temurin](https://adoptium.net/temurin/releases/), [PostgreSQL 17.11](https://www.postgresql.org/docs/17/).
