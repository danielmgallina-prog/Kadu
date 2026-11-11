# Kadu no site

Três arquivos fazem tudo funcionar:

| Arquivo | O que é |
|---|---|
| `kadu.html` | O Kadu completo (o mesmo das animações aprovadas), em versão para site |
| `kadu-embed.js` | O "encaixe": coloca o Kadu flutuando por cima da sua página |
| `exemplo.html` | Página de teste com todos os recursos ligados |

## 1. Copiar
Coloque `kadu.html` e `kadu-embed.js` numa pasta do site, por exemplo `kadu/`.

## 2. Ligar (uma linha, antes do `</body>`)
```html
<script src="kadu/kadu-embed.js" data-src="kadu/kadu.html" defer></script>
```
Pronto. Ele entra com a animação de chegada, dá oi e fica no canto inferior direito.

> Precisa abrir por um servidor (http:// ou https://). Abrindo o arquivo direto com duplo clique, o navegador bloqueia a conversa entre a página e o Kadu. Para testar no PC: `python -m http.server` dentro da pasta e abra `http://localhost:8000/exemplo.html`.

## 3. Opções no próprio script
```html
<script src="kadu/kadu-embed.js" data-src="kadu/kadu.html"
        data-saudacao="E aí! Eu sou o Kadu, mascote do DG."
        data-comentarios="true" data-intervalo="45,90"
        data-celular="true" defer></script>
```
- `data-saudacao`: primeira fala (vazio = não fala).
- `data-comentarios="false"`: desliga as falas soltas.
- `data-intervalo="45,90"`: de quantos em quantos segundos ele comenta algo.
- `data-celular="false"`: não aparece em telas pequenas.
- `data-manual="true"`: não inicia sozinho; você chama `Kadu.iniciar({...})`.

Para trocar as frases soltas, inicie manualmente:
```html
<script src="kadu/kadu-embed.js" data-manual="true"></script>
<script>
  Kadu.iniciar({ src: 'kadu/kadu.html', saudacao: 'Oi!', frases: ['Frase 1', 'Frase 2'], intervalo: [40, 80] });
</script>
```

## 4. Fazer ele reagir à página (sem programar)
```html
<section data-kadu-fala="Esses são os meus projetos!" data-kadu-emo="animado">...</section>
<div class="card" data-kadu-olhar data-kadu-emo="encantado">...</div>
```
- `data-kadu-fala`: quando a seção aparece na tela, ele fala (uma vez; `data-kadu-repetir` para sempre).
- `data-kadu-olhar`: ao passar o mouse no elemento, ele olha para ele (e faz a expressão de `data-kadu-emo`).

## 5. Comandos por JavaScript
```js
Kadu.falar('Bem-vindo!', 'feliz');      // texto, expressão, duração em ms (opcional)
Kadu.expressao('apaixonado', 3000);
Kadu.pular();
Kadu.mostrar(); Kadu.esconder(); Kadu.alternar();
Kadu.olhar(document.querySelector('#contato'));  // Kadu.olhar(null) volta ao normal
Kadu.pronto(() => Kadu.falar('Carreguei!'));
Kadu.expressoes().then(console.log);   // lista de nomes
```

Expressões: neutro, feliz, animado, encantado, apaixonado, piada, zoando, surpreso, desconfiado, tedio, bravo, triste, chorando, tonto, erro, ouvindo, pensando, segurado, sono, dormindo, comendo, carinho, focado, calor, fraco, banho, confuso, assustado, orgulhoso, envergonhado, determinado, pidao, marejado, carregando, ideia, pesquisando, musica, fominha, glitch, indiferente, zen, fogo, exausto.

## O que o visitante consegue fazer
- Olhos e orelhas seguem o mouse; ele pisca, respira, cochila se ficar parado e acorda quando o mouse chega perto.
- Clique: reage. Arrastar: leva ele pela tela (no celular também, com o dedo).
- Esfregar o mouse na cabeça: carinho.
- Botão direito nele: menu com Alimentar, Carinho, Bolinha, Banho, Dormir e Visual (acessórios).
- Fome, energia, acessórios e posição ficam salvos no navegador de cada visitante.

## Como funciona por baixo
O Kadu roda num iframe transparente do tamanho da tela. O `kadu-embed.js` deixa o clique atravessar para a sua página, menos exatamente em cima do Kadu e dos menus dele, e repassa o mouse para os olhos seguirem. A rodinha do mouse em cima dele continua rolando a página. Nada do seu CSS ou JS interfere nele, e vice-versa.
