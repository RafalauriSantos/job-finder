---
feature: feedback-aprendizado-personalizado
---
# Feedback e Aprendizado Personalizado — Design

## Architecture

Adicionar um registro append-only de eventos humanos no `StateStore`, com comandos explícitos para registrar e desfazer uma decisão. O ranking consumirá apenas um resumo derivado e versionado, permitindo reproduzir qual feedback alterou um peso. O aprendizado será inicialmente baseado em contagens e ajustes limitados, ativado somente após o limiar configurado; não haverá modelo opaco nesta etapa.

## File Structure

- Modify: `storage/state_store.py` — persistência de eventos e resumo.
- Create: `core/feedback.py` — validação, agregação e ajuste limitado.
- Modify: `core/scoring.py` — consumo do perfil aprendido.
- Modify: `monitor.py` — registro e exposição do contexto.
- Modify: `notify/telegram.py` — ações de feedback.
- Create: `tests/test_feedback.py` — eventos, desfazer e limiar.
- Modify: `tests/test_state_store.py` — compatibilidade e persistência.

## Phase Ordering

1. Persistência e contrato dos eventos.
2. Comandos de feedback e resumo agregado.
3. Aplicação limitada no ranking.
4. Verificação de reversão e auditoria.

## Constraints

- Eventos originais não são apagados ao desfazer.
- Nenhum ajuste entra em vigor antes do limiar configurado.
- O estado continua local e não contém credenciais.

