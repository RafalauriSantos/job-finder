# WorkHunter LinkedIn Capture

Extensão local para Chrome/Chromium. Ela lê somente cards visíveis no LinkedIn e
manda sinais de posts de recrutamento para `127.0.0.1:8765`. Não recebe senhas,
cookies nem envia dados para um servidor externo.

## Instalação local

1. Inicie `workhunter-linkedin-ingest.service`.
2. Abra `chrome://extensions`.
3. Ative o modo desenvolvedor.
4. Escolha **Carregar sem compactação** e selecione esta pasta.
5. Abra o feed do LinkedIn e mantenha a página visível.

O Playwright é complementar e opcional; não é necessário para a extensão.

O receptor aceita somente conexões de loopback. A extensão não faz login, não lê cookies e não tenta contornar desafios do LinkedIn.
