# Alertas compactos e qualidade da análise

## Entregue em 23/09/2026

- Telegram e e-mail compartilham o mesmo cartão: cargo, empresa, modalidade,
  até quatro tecnologias, justificativa curta, ressalvas e um link de candidatura.
- Notas, potencial, contas de pontuação e links repetidos ficam fora do cartão.
- Salário ausente é omitido. CLT/PJ só aparece com evidência explícita na descrição
  e consistência com o campo coletado; estágio não herda o CLT padrão.
- Caracteres HTML são tratados e campos longos são limitados antes da montagem.
- Formação e idioma são procurados independentemente dos três primeiros motivos.
  São apresentados como trechos a conferir, sem presumir que o candidato não
  atende ao requisito. A extração continua heurística, não exaustiva.
- Status periódico passa de diário para semanal. Alertas de falha continuam separados.
- Análise de escopo usa limites de palavras: JavaScript não conta como Java,
  digital não conta como Git, 15 anos não conta como 5 anos.
- Requisitos inline são preservados; descrições achatadas são divididas antes
  de separar obrigações e diferenciais. Intern é reconhecido como nível de entrada.
- Calibração conta uma avaliação de relevância por vaga. Rejeição e ausência de
  candidatura são neutras; somente irrelevância explícita é negativa. Eventos
  continuam no histórico e pesos não são alterados automaticamente.

## Validação

193 testes passam sem rede. Prévia local de dez vagas entregues, sem reenviar
notificações nem alterar o banco de produção. Prévia fica em `.tools/`, ignorada
pelo Git. Não há evidência de aumento de precisão apenas por passar nos testes.

## Próximas etapas de inteligência

1. Feedback acessível: registrar relevante, irrelevante, candidatei e entrevista
   com a identidade da vaga, contexto e possibilidade de correção. Hoje o registro
   existe pelo CLI; botões no Telegram ainda exigem tratamento de callbacks,
   validação do usuário e persistência idempotente dos eventos.
2. Avaliação rotulada: construir uma amostra de ao menos 20 vagas distintas
   avaliadas pelo usuário; separar relevância de resultado do processo seletivo.
   Esse limiar é operacional, não uma garantia estatística.
3. Aprendizado limitado: propor ajustes pequenos de ranking por tecnologia,
   senioridade e fonte, com versão, comparação e reversão. Não relaxar restrições
   obrigatórias nem presumir experiência pelo interesse de aprendizado.
4. Agrupamento: até três alertas individuais por ciclo e resumo para o restante,
   separando progressão. Persistir associação entre lote e vagas; confirmar
   entrega somente após resposta do canal e tratar resposta incerta sem reenvio
   automático. Validar recuperação após falha antes de ativar essa política.
5. Medição: acompanhar avaliações por vaga e falsos positivos, sem confundir
   menos mensagens com maior qualidade. Revisar também anúncios remotos com
   títulos iguais e cidades diferentes antes de mudar sua identidade: podem
   ser duplicatas ou posições distintas.

A migração Java/Hermes é uma frente independente. Estas alterações melhoram o
radar Python em operação e não representam integração com Hermes ou candidaturas
automáticas. O runner local inicia um processo por ciclo, carregando as mudanças
na próxima execução; mensagens já recebidas não são editadas.
