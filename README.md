# Job Finder - Monitor Minimalista de Vagas 🚀

Monitor ultra-leve para detectar vagas na Gupy assim que são publicadas, alertando no **Telegram** ou **Discord**.

## ⚙️ Configuração Rápida

### 1. Configure as Notificações no `.env`
Crie ou edite o arquivo `.env`:

```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
# ou DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

> **Como pegar o token do Telegram (leva 1 minuto):**
> 1. No Telegram, abra conversa com `@BotFather` e envie `/newbot` para pegar o **token**.
> 2. Envie uma mensagem para o seu bot e depois fale com `@userinfobot` para pegar o seu **ID**.

### 2. Configure o que quer monitorar no `config.json`

```json
{
  "check_interval_minutes": 10,
  "monitors": [
    {
      "description": "Goomer (Todas as vagas)",
      "companyId": 2245,
      "careerPageName": "goomer"
    },
    {
      "description": "Dev Python Remoto",
      "term": "python",
      "workplaceTypes": "remote"
    }
  ]
}
```

---

## 🚀 Como Executar

* **Checar uma única vez:**
  ```bash
  python monitor.py --once
  ```

* **Deixar rodando continuamente (a cada 10 min):**
  ```bash
  python monitor.py
  ```

* **Rodar 24/7 de graça na nuvem (GitHub Actions):**
  Basta subir este repositório para o seu GitHub e cadastrar em `Settings > Secrets and variables > Actions`:
  * `TELEGRAM_BOT_TOKEN`
  * `TELEGRAM_CHAT_ID`
  O GitHub Actions executará o script a cada 15 minutos sem consumir nada do seu PC.
