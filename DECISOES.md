# Decisões do projeto Kadu

Registro do que foi decidido e por quê, para não reabrir à toa.

## Base e cérebro
- **Base: isair/jarvis.** Assistente de voz aberto, com app de desktop em Python/PyQt6 que dava para personalizar a fundo.
- **Cérebro no servidor, gratuito.** O notebook (i5-4210U, 8 GB, vídeo de 2 GB) não roda modelo local. Escolhido o Gemini pela API compatível com OpenAI.
- **Chave nunca no código nem no chat.** O instalador lê com `Read-Host -AsSecureString` e grava só no `config.json` do usuário.
- **Português e personalidade de parceiro brincalhão**, definidos no prompt do sistema.

## Identidade visual
- **Expressão só pelos olhos.** Olhos ovais escuros com brilho. Sem boca, sem sobrancelhas, sem bochechas.
- **Orelhas perto da pose natural** em quase todas as reações (as poses extremas foram reprovadas).
- **Catálogo de olhos aprovado** (`kadu/design/kadu-olhos.html`). Refeitas a pedido: Marejado, Ideia ("olhos acendem"), Fominha (sem cenoura), Exausto (as linhas pareciam sobrancelhas), Pidão (olhar para cima com ângulo 3D), Música (os dois olhos pulam juntos, independentes do corpo), Choro (estilo emoji, a correntezinha termina na borda do corpo).
- **Óculos escuros** acompanham o olhar e escondem os olhos por baixo.
- **Versão 3D abandonada** (nov/2026). O protótipo em massinha não ficou fiel às referências; ficou o 2D.

## Interface
- **Prévia HTML é a fonte da verdade.** A página de produção e a do site são geradas dela por script, nunca editadas à mão.
- **Janela transparente com clique atravessando.** Só as áreas do Kadu e dos menus recebem o mouse; o resto passa para a área de trabalho.
- **Menu da bandeja abre acima do ponto clicado**, para não ficar atrás da janelinha de ícones ocultos do Windows.
- **Acessórios como balõezinhos embaixo dele**, sem retângulo de fundo, na altura dele, com o contador de cenouras acima.
- **Ao mover o Kadu, menus e balões acompanham** (balão de pensamento com leve atraso).

## Desempenho
- **Sem voz.** A voz saía muito atrasada e travava o PC; ficou só o balão.
- **Janela pequena em volta dele**, que só vira tela cheia quando abre menu, diário ou arraste.
- **Abre com `pythonw.exe`** (sem console), porque o runtime Intel Fortran derrubava o app ao fechar o console.

## Comportamento
- **Respostas do chat silencioso também são publicadas**, senão ele ficava "pensando" para sempre.
- **Trava de segurança de 75 s** no estado "pensando".
- **Easter egg da Linda é local e determinístico**: o modelo de reserva ignorava a regra do prompt.

## Site
- **Embutido por iframe transparente** (`kadu-embed.js`) com as mesmas regiões clicáveis do desktop: a página continua clicável e o CSS dela não interfere no Kadu.
- **No site não tem chat, microfone nem diário.** O menu tem só cuidar do bichinho e o visual.
- **Estado do bichinho salvo no navegador** de cada visitante.
