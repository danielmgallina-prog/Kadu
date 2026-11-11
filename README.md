# Kadu

O Kadu é um assistente digital em português que vive na tela como um mascote animado. Ele é um derivado do **[Jarvis](https://github.com/isair/jarvis)** (de Baris Sencan), um assistente de voz de código aberto, personalizado do zero: nome, personalidade, visual, expressões e conversa em PT-BR.

> O README original do Jarvis está em [`README.jarvis.md`](README.jarvis.md).

## O que mudou em relação ao Jarvis

| | Jarvis | Kadu |
|---|---|---|
| Interface | Janela do app e ícone na bandeja | Mascote flutuante, transparente, sempre por cima, que dá para arrastar |
| Respostas | Voz | Balão de fala (a voz foi desligada, pesava demais no notebook) |
| Cérebro | Modelo local (Ollama) | Gemini por API compatível com OpenAI (o notebook não roda IA local) |
| Idioma e jeito | Inglês, neutro | Português, parceiro brincalhão |
| Extras | — | Bichinho virtual (fome, energia, banho, acessórios), diário técnico, Pomodoro, comentários espontâneos, 43 expressões só com os olhos |

## Estrutura

```
src/                      código do Jarvis com as mudanças do Kadu
  desktop_app/kadu_web.py     janela do Kadu (PyQt6 WebEngine) e ponte com a página
  desktop_app/kadu_vida.py    comentários espontâneos, monitores (bateria, CPU, música)
  desktop_app/kadu_pagina/    página do Kadu já construída (gerada, não editar à mão)
  desktop_app/kadu_widget.py  versão antiga, usada se o WebEngine faltar
  jarvis/kadu_ponte.py        emoções das respostas e falas locais especiais
kadu/
  design/   prévia interativa (fonte da verdade das animações) e catálogo de olhos
  web/      construir.py + ponte.js: geram src/desktop_app/kadu_pagina/kadu.html
  site/     versão para colocar em qualquer site (kadu-embed.js) — ver kadu/site/LEIA-ME.md
  instalador/  instalar-kadu.ps1 (Windows)
DECISOES.md        por que cada coisa é do jeito que é
CHANGELOG-KADU.md  o que foi feito, em ordem
```

## Como gerar a página depois de mexer nas animações

```bash
python3 kadu/web/construir.py kadu/design/kadu-interacoes.html src/desktop_app/kadu_pagina/kadu.html
cd kadu/site && python3 construir_site.py ../design/kadu-interacoes.html kadu.html
```

Edite sempre `kadu/design/kadu-interacoes.html` e gere de novo; as outras duas páginas são derivadas.

## Instalar no Windows

Rode `kadu/instalador/instalar-kadu.ps1` no PowerShell. Ele pede a chave do Gemini sem mostrar na tela e grava só no `config.json` do usuário. **Nenhuma chave fica no repositório.**

## Licença

Derivado do Jarvis, sob a mesma licença: **uso não comercial**. Veja [`LICENSE`](LICENSE) e [`NOTICE.md`](NOTICE.md).
