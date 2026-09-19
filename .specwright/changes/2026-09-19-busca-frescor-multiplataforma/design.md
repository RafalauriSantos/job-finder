---
feature: busca-frescor-multiplataforma
---
# Busca com Frescor Multiplataforma — Design

## Architecture

Estender o `QueryPlanner` para produzir consultas com intenção, senioridade e janela temporal sem duplicar lógica entre coletores. Cada coletor recebe uma consulta normalizada, registra sua execução e devolve resultados brutos; a normalização de publicação converte datas disponíveis para `published_at`, mantendo desconhecido quando a fonte não informa. A deduplicação continua centralizada no fluxo existente e passa a preferir o registro com data e descrição mais completas.

## File Structure

- Modify: `core/query_planner.py` — variantes, senioridades e janela temporal.
- Modify: `config.json` — famílias de consultas e filtros recentes.
- Modify: `collectors/linkedin.py` — aplicação de janela, paginação e telemetria por consulta.
- Modify: `collectors/gupy.py` — aplicação de variantes e telemetria por consulta.
- Modify: `models/job.py` — metadados de descoberta e publicação, se necessário.
- Modify: `core/metrics.py` — métricas por consulta e idade no alerta.
- Create: `tests/test_query_planner_freshness.py` — contrato do planejador.
- Modify: `tests/test_collectors.py` — contratos de filtros e resultados vazios/falhas.

## Phase Ordering

1. Testes do planejador e do contrato temporal.
2. Implementação das consultas e propagação aos coletores.
3. Consolidação de publicação e telemetria.
4. Execução do conjunto completo de testes e ciclo controlado.

## Constraints

- Respeitar limites, autenticação e termos das plataformas.
- Não transformar data desconhecida em data recente.
- Preservar o limite de ciclo de 180 segundos já configurado.
- Usar somente interfaces determinísticas e explicáveis nesta mudança.

