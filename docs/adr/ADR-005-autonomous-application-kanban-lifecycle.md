# ADR-005: Núcleo Java de carreira integrado ao Hermes instalado

- Status: Proposto revisado; substitui o conteúdo da proposta anterior deste ADR.
- Data original e revisão: 2026-09-16.
- Implementação: não iniciada.
- Referência operacional: [Plano de projeto](../engineering/hermes-java-project-plan.md).

## Contexto

O Job Finder atual é um radar Python. Rafael pretende aprender Java e IA aplicada construindo um produto útil para encontrar vagas e acompanhar candidaturas. O Hermes instalado será integrado como consumidor de ferramentas. A proposta anterior não exigia Java e apresentava cotas e promessas de proteção contra bloqueios sem validação.

## Direção proposta

1. Construir um monólito modular Java com Spring Boot e PostgreSQL.
2. Manter domínio, avaliação, histórico e autorização de ações no Java.
3. Verificar o contrato real de ferramentas do Hermes no marco M0.
4. Migrar gradualmente o Python e concluir o caminho principal em Java.
5. Começar com importação, ranking, triagem e candidaturas registradas manualmente.
6. Adicionar IA e envio assistido após validar a fundação.
7. Separar prioridade de autorização; score alto não ultrapassa limites.
8. Usar banco, idempotência e reconciliação para fila e envio.
9. Manter Kanban interno como fonte de verdade; integrações externas são opcionais.

## Alternativas consideradas

- Apenas Python: preserva operação, mas não atende ao objetivo Java.
- Reescrita integral imediata: aumenta risco de interromper o radar.
- Candidaturas automáticas primeiro: depende de infraestrutura e regras ausentes.
- Microserviços: complexidade operacional sem necessidade demonstrada.

## Consequências

Exige banco, migrações, contrato de integração e aprendizado gradual. A transição terá dois runtimes temporariamente. Permite entregas pequenas e regras testáveis.

Não garante contratação, disponibilidade das fontes ou proteção contra bloqueios. Limites e canais serão validados antes de implementar envio.

## Validação

O plano operacional contém backlog, critérios de aceite, testes e migração. Registrar aceite deste ADR e versões de tecnologia em M0.3. A proposta original permanece no histórico Git; ficam retirados 20+5 envios universais, bypass VIP, simulação humana e estatísticas de concorrência sem fonte.
