# Operacao do Job Finder

## Executar

```powershell
python monitor.py --once
```

O processo normal usa `check_interval_minutes` do `config.json`. O limite de uma rodada é `max_cycle_seconds`; ultrapassá-lo gera alerta no relatório, mas não interrompe uma coleta em andamento.

## Configuração

- `config.json`: fontes, consultas, filtros, janelas recentes e limites.
- `profile.json`: formação, localização, stack e empresas prioritárias.
- `.env`: credenciais locais, nunca commitadas.
- `seen_jobs.json`: estado operacional local, ignorado pelo Git.
- `cycle_health.json`: resumo da última rodada, com duração, saúde das fontes,
  funil de descarte e entregas; é regenerado ao final de cada ciclo bem-sucedido.

### Fallback de entrega

O Telegram é o canal primário. Quando o envio retorna falha, o monitor tenta
enviar o mesmo alerta pela API do Resend usando `RESEND_API_KEY`,
`ALERT_EMAIL_FROM` e `ALERT_EMAIL_TO`. Se os dois canais falharem, a vaga não é
marcada como entregue e permanece disponível para retry com backoff. Sem as três
variáveis de e-mail configuradas, o fallback fica desativado de forma segura.

### Consultas recentes

Cada monitor pode declarar `query_variants`, `seniority_variants` e `recent_window_hours`.
O planejador gera uma consulta para cada combinação e o ciclo registra o termo,
a senioridade, a janela aplicada e o resultado por consulta. No LinkedIn, a janela
é convertida para `f_TPR` em segundos; um `time_range` explícito tem prioridade.
No Gupy, os parâmetros seguem para a busca sem o `query_id` interno.

## Rollback

Cada alteração de código é publicada em commit separado. Para voltar a uma versão anterior, primeiro identifique o commit e use uma reversão explícita:

```powershell
git log --oneline -10
git revert <commit>
python -m pytest -q
```

Mudanças de configuração podem ser revertidas restaurando o commit anterior de `config.json`, sempre rodando a suíte depois.

## Verificação

```powershell
python -m pytest -q
git status --short
```

O arquivo `seen_jobs.json` pode mudar após uma execução real e deve permanecer local. Falhas de entrega ficam registradas para retry com backoff e limite de tentativas.

## Métricas

O relatório de cada ciclo mostra descoberta bruta, vagas únicas, duplicatas implícitas, descartes por motivo, alertas entregues, chamadas LLM, duração e saúde por fonte. Precisão e recall reais exigem feedback humano sobre relevância e candidaturas; o sistema não os inventa a partir de contagens de filtro.
