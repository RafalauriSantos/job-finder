# Checklist de Conclusão da Refatoração TDD

Esta lista define quando a refatoração do Job Finder está concluída. Um item só é marcado quando existe teste ou evidência operacional correspondente.

## Base e processo

- [x] Suíte automatizada executa sem falhas.
- [x] Ciclo TDD aplicado em novos módulos críticos.
- [ ] Todos os módulos críticos possuem testes unitários isolados.
- [ ] Cada mudança futura começa por um teste que falha.

## Entrega e persistência

- [x] Falha do Telegram não marca vaga como entregue.
- [x] Entrega bem-sucedida marca vaga como vista.
- [x] Resultado da entrega fica auditado.
- [x] Retry persistente com limite e backoff implementado.
- [x] Alertas têm idempotência comprovada contra duplicação entre processos.

## Coleta e consultas

- [x] LinkedIn suporta filtros e paginação.
- [x] Gupy registra parâmetros e resultados por consulta.
- [x] Famílias de termos são configuráveis.
- [x] Erro de fonte é distinguido de resultado vazio.
- [x] Cada coletor possui contrato de teste com resposta válida, vazia e erro.
- [x] Saúde das fontes é persistida para relatório histórico.

## Enriquecimento e dados

- [x] URLs RSS podem ser resolvidas e canonizadas.
- [x] LinkedIn possui enriquecimento limitado de detalhes.
- [x] Deduplicador preserva o registro mais rico.
- [x] Merge de campos conflitantes possui política completa e testes por campo.
- [x] Data de publicação e idade da vaga são normalizadas entre fontes.

## Decisão e ranking

- [x] Junior, Pleno e Senior possuem classificação testada.
- [x] Pleno compatível pode passar pelo funil.
- [x] Senioridade explícita incompatível continua bloqueada.
- [x] Veto, score baixo e aprovado estão centralizados.
- [x] Localização e evidência são decisões testáveis e separadas do monitor.
- [x] Score, elegibilidade e interesse de aprendizado permanecem campos distintos.

## Operação e qualidade

- [x] Suíte atual está verde.
- [x] Teste de integração cobre um ciclo completo sem rede real.
- [x] Teste de contrato cobre LinkedIn, Gupy, RSS, GitHub e Trampos.
- [x] Relatório do ciclo mostra recall aproximado, precisão, duplicatas e falhas por fonte.
- [x] Execução real dentro do limite operacional definido.
- [x] Documentação de configuração e rollback atualizada.
- [x] Estado operacional não é commitado junto com código.

## Critério final

- [ ] Todos os itens obrigatórios acima estão marcados.
- [x] `python -m pytest -q` passa integralmente.
- [x] Um ciclo real do radar termina sem erro e com métricas interpretáveis.
- [ ] Uma revisão final confirma que não houve regressão de comportamento.
