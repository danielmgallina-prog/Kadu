# Histórico do Kadu

## nov/2026

### Base
- Jarvis instalado no Windows com o Gemini como cérebro e respostas em PT-BR.
- Instalador `instalar-kadu.ps1`: reaproveita o ambiente Python, para o Kadu antes de atualizar e cria o atalho `Kadu.vbs`.

### Mascote
- Prévia interativa com expressões, pet virtual (fome, energia, banho, carinho, bolinha), acessórios, diário, Pomodoro e modos (foco, equilibrado, falante, assistente).
- Abertura animada com os passos reais da inicialização e animação de erro (explosão, olho em X).
- Ícone da bandeja desenhado a partir do próprio Kadu, acompanhando a expressão.
- Catálogo de olhos refinado e aplicado à versão de testes e depois à de produção.

### Integração com o app
- `kadu_web.py` substitui a janela do Jarvis: posição, preferências e diário salvos em `kadu.json`.
- Mic, chat e diário técnico ligados de verdade (log do app vira o diário).
- Reações a bateria, CPU e música.

### Correções
- Kadu preso em "pensando" quando a resposta vinha pelo chat.
- App fechando sozinho ao abrir o chat (console + runtime Fortran).
- Menu da bandeja escondido atrás da janelinha de ícones ocultos.
- Instalador falhando com o Kadu aberto.
- Balão saindo antes da voz.

### Desempenho
- Voz desligada e janela pequena em volta do Kadu.

### Site
- Versão para site (`kadu/site`), com falas por seção, olhar acompanhando elementos e API em JavaScript.

### Descartado
- Voz personalizada (ElevenLabs).
- Versão 3D em massinha (Meshy + Three.js).
