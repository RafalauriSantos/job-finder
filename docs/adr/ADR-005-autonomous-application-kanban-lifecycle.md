# ADR-005: Autonomous Application & Kanban Tracking Lifecycle

- **Status**: Proposed (Em Análise)
- **Decision Date**: 2026-09-16
- **Context Link**: [`hermes-auto-apply-strategy.md`](file:///c:/Users/Rafael%20lauri/Downloads/job-finder/docs/engineering/hermes-auto-apply-strategy.md)

## Context
O sistema opera como um buscador e notificador de vagas passivo via Telegram. Para maximizar a conversão de oportunidades e liberar o candidato para foco em aprendizado e nivelamento técnico, surge a necessidade de transformar o sistema em um agente autônomo de aplicação e rastreamento ("Hermes"). Contudo, candidaturas em massa sem limites geram risco severo de banimento em plataformas e ATS, queima de reputação do candidato e perda de contexto sobre as vagas aplicadas.

## Decision
1. **Pacing & Quota Segura**:
   - Limitar candidaturas a um teto nominal de **~20 aplicações por janela de 24 horas**.
   - Introduzir atrasos estocásticos (*human jitter* de 45 a 180s) entre ações automatizadas.
2. **Captação Contínua & Fila de Prioridade (Priority Queue)**:
   - A descoberta e pontuação de vagas **não é interrompida** quando a cota diária é atingida.
   - Vagas qualificadas (Score 75% a 89%) descobertas após a cota são armazenadas em fila persistente (`storage/priority_queue.json`) e ordenadas por relevância decrescente (`Score DESC, created_at DESC`).
   - No próximo ciclo diário, as vagas acumuladas na fila de prioridade são processadas antes de novas vagas.
3. **VIP Override (Vaga Diamante)**:
   - Vagas com Score $\ge 90\%$ ou com empresa prioritária + stack core contornam o limite diário e disparam aplicação imediata, sujeitas a um teto rígido de segurança (+5 overrides/dia máx).
4. **Desacoplamento de Kanban & Feedback Loop**:
   - Registrar candidaturas em quadro Kanban modular (`BaseKanban` com suporte a GitHub Projects / Notion / Trello).
   - Ouvir respostas de recrutadores por e-mail (IMAP) para avançar status para `[Entrevista/Teste]` ou `[Rejeitado]`.
5. **Priorização de Fontes de Baixa Concorrência**:
   - Priorizar a coleta em canais de nicho dev (ex: repositórios de vagas do GitHub Brasil), onde a concorrência média é de 15 a 30 inscritos (contra 500 a 800 em plataformas generalistas de massa).
6. **Radar de Voluntariado & Open Source Comunitário**:
   - Monitorar demandas e issues comunitárias acessíveis (`good first issue`, `help wanted`) na stack do candidato, promovendo ganho de experiência prática em equipe e construção de portfólio no GitHub sem a pressão de metas corporativas.

## Consequences

### Positive
- Protege o candidato contra suspensões de conta e filtros anti-bot.
- Garante que oportunidades de altíssimo fit (vagas diamante) não sejam perdidas por causa de cotas pré-atingidas.
- Aumenta drasticamente a taxa de leitura do currículo ao focar em vagas com poucos concorrentes.
- Gera experiência real comprovável no GitHub por meio de colaborações voluntárias orientadas.
- Elimina a sobrecarga mental de preenchimento manual repetitivo e acompanhamento de status.

### Negative & Trade-offs
- Requer gestão de estado mais complexa (controle de cota deslizante e fila com prioridade).
- Mecanismos de automação de formulários (ex: Playwright para LinkedIn) exigem manutenção contínua devido a mudanças de interface externa.

