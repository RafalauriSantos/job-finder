# M0.2 — Revisão do conjunto de aceitação

Status: preparação concluída; aceite de produto pendente.
Os 24 exemplos são sintéticos, não são anúncios reais nem candidaturas.
Os rótulos abaixo foram propostos pelo assistente com base no perfil existente e nesta conversa.

ELIGIBLE significa passar pelos filtros iniciais, não estar garantidamente apto à contratação.
NEEDS_REVIEW preserva a oportunidade quando falta informação ou existe ambiguidade.
INELIGIBLE impede entrada na fila ativa, preservando o histórico.

| Caso | Cenário | Proposta | Motivo |
| --- | --- | --- | --- |
| J01 | Java estágio introdutório | ELIGIBLE | Java em nível básico atende requisitos explicitamente introdutórios. |
| J02 | React júnior remoto | ELIGIBLE | Stack atual compatível. |
| J03 | Java sênior remoto | INELIGIBLE | Senioridade bloqueada. |
| J04 | Backend júnior São Paulo presencial | INELIGIBLE | Fora da região aceita. |
| J05 | Java júnior afirmativa PCD | INELIGIBLE | Exclusividade incompatível com perfil. |
| J06 | Java júnior com inclusão geral | ELIGIBLE | Inclusão não equivale a vaga exclusiva. |
| J07 | Java júnior graduação obrigatória | INELIGIBLE | Requisito obrigatório não atendido. |
| J08 | Java júnior graduação desejável | ELIGIBLE | Desejável não deve virar veto. |
| J09 | Java júnior local não informado | NEEDS_REVIEW | Não inferir remoto. |
| J10 | Java júnior remoto exterior | INELIGIBLE | Remoto não significa elegibilidade mundial. |
| J11 | Backend júnior Sorocaba | ELIGIBLE | Cidade aceita. |
| J12 | Backend pleno remoto | NEEDS_REVIEW | Pleno não tem política definitiva no perfil. |
| J13 | Atendente júnior | INELIGIBLE | Júnior isoladamente não torna a vaga técnica. |
| J14 | Goomer sênior | INELIGIBLE | Empresa prioritária não remove restrição. |
| J15 | Java júnior com três anos Spring | NEEDS_REVIEW | Experiência não comprovada; sinalizar incompatibilidade sem inventar currículo. |
| J16 | Estágio exclusivo Ciência da Computação | NEEDS_REVIEW | GTI não deve ser declarado equivalente sem validação. |
| J17 | Java sem senioridade | NEEDS_REVIEW | Não assumir júnior. |
| J18 | Estágio IA com Java introdutório | ELIGIBLE | Interesse é suficiente porque o anúncio não exige experiência prévia com IA. |
| J19 | Engenheiro IA experiente | INELIGIBLE | Interesse em IA não equivale a experiência profissional. |
| J20 | Vaga encerrada | INELIGIBLE | Arquivar, preservando histórico. |
| J21 | Java estágio introdutório | ELIGIBLE | Manter um registro, sem nova avaliação se conteúdo/perfil/regras não mudaram. |
| J22 | Mesmo ID em outra fonte | ELIGIBLE | ID igual de fonte diferente não pode suprimir vaga. |
| J23 | Java estágio introdutório | ELIGIBLE | Atualizar conteúdo; preservar identidade e histórico. |
| J24 | Java estágio introdutório | ELIGIBLE | Sugerir duplicidade entre fontes; sem fusão destrutiva automática. |

## Decisões que precisam de Rafael

- J12: manter vagas pleno em uma fila separada de revisão ou descartá-las?
- J15: requisitos obrigatórios de anos de experiência acima da comprovada devem permanecer para revisão ou ser descartados?
- J16: manter estágio restrito a outro curso em revisão para checar aceitação de GTI ou descartar?

Os demais casos seguem o perfil atual e ainda precisam de confirmação. Resposta sugerida: "Aprovo os casos, com estas alterações: ...".
Isso valida regras de triagem; não autoriza envio de candidaturas.

## Critério de conclusão

Após a revisão, registrar decisões do usuário, ajustar JSON e regras e trocar review.status somente nos casos efetivamente aprovados.
As relações J21–J24 são critérios técnicos de identidade, distintos do rótulo de elegibilidade.
