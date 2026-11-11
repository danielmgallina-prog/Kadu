/*!
 * Kadu no site — kadu-embed.js
 * Coloca o Kadu flutuando por cima de qualquer página.
 *
 * Uso mínimo (antes do </body>):
 *   <script src="kadu/kadu-embed.js" data-src="kadu/kadu.html" defer></script>
 *
 * Opções pelo próprio <script> (todas opcionais):
 *   data-src="kadu/kadu.html"        caminho da página do Kadu
 *   data-saudacao="Oi! ..."          primeira fala ("" para não falar nada)
 *   data-comentarios="false"         desliga as falas soltas de tempos em tempos
 *   data-intervalo="45,90"           intervalo (segundos) entre as falas soltas
 *   data-celular="false"             não mostra o Kadu em telas pequenas
 *   data-z="2147483000"              z-index do Kadu
 *   data-manual="true"               não inicia sozinho (chame Kadu.iniciar({...}))
 *
 * Na página (atributos HTML):
 *   data-kadu-fala="texto"           quando a seção aparece na tela, ele fala (uma vez)
 *   data-kadu-emo="feliz"            expressão usada junto com a fala/olhar
 *   data-kadu-repetir                fala toda vez que a seção voltar a aparecer
 *   data-kadu-olhar                  ao passar o mouse no elemento, ele olha para ele
 *
 * API (window.Kadu):
 *   Kadu.falar(texto, emocao?, ms?)  Kadu.expressao(nome, ms?)  Kadu.pular()
 *   Kadu.mostrar()  Kadu.esconder()  Kadu.alternar()  Kadu.olhar(elementoOuNull)
 *   Kadu.expressoes().then(lista => ...)   Kadu.pronto(fn)
 */
(function () {
  'use strict';
  if (window.Kadu && window.Kadu.__ok) return;

  var script = document.currentScript || document.querySelector('script[src*="kadu-embed"]');
  var ds = (script && script.dataset) || {};
  var toque = matchMedia('(hover: none), (pointer: coarse)').matches;

  var iframe = null, pronto = false, filaPronto = [], fila = [], regioes = [], tudo = false, menus = false;
  var ativoToque = false, ultMouse = null, rafMouse = 0, esperaExp = null;

  function manda(cmd, dados) {
    var m = Object.assign({ kaduCmd: cmd }, dados || {});
    if (!pronto && cmd !== 'config') { fila.push(m); return; }
    try { iframe.contentWindow.postMessage(m, '*'); } catch (e) {}
  }
  function dentro(x, y) {
    for (var i = 0; i < regioes.length; i++) {
      var r = regioes[i];
      if (x >= r[0] && y >= r[1] && x <= r[0] + r[2] && y <= r[1] + r[3]) return true;
    }
    return false;
  }
  function capturar(sim) { if (iframe) iframe.style.pointerEvents = sim ? 'auto' : 'none'; }
  function decide(x, y) { if (toque) return; capturar(tudo || dentro(x, y)); }

  function iniciar(opc) {
    if (iframe) return;
    opc = opc || {};
    if (opc.celular === false && Math.min(innerWidth, innerHeight) < 600) return;
    iframe = document.createElement('iframe');
    iframe.src = opc.src || ds.src || 'kadu/kadu.html';
    iframe.title = 'Kadu, o mascote do site';
    iframe.setAttribute('allowtransparency', 'true');
    iframe.setAttribute('scrolling', 'no');
    iframe.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;height:100dvh;border:0;margin:0;padding:0;' +
      'background:transparent;color-scheme:normal;pointer-events:none;z-index:' + (opc.z || ds.z || 2147483000);
    document.body.appendChild(iframe);

    var cfg = {};
    if (opc.saudacao !== undefined) cfg.saudacao = opc.saudacao; else if (ds.saudacao !== undefined) cfg.saudacao = ds.saudacao;
    if (opc.frases) cfg.frases = opc.frases;
    var com = opc.comentarios !== undefined ? opc.comentarios : (ds.comentarios !== undefined ? ds.comentarios !== 'false' : undefined);
    if (com !== undefined) cfg.comentarios = com;
    var iv = opc.intervalo || (ds.intervalo ? ds.intervalo.split(',').map(Number) : null);
    if (iv) cfg.intervalo = iv;
    if (opc.mostrarAoAbrir !== undefined) cfg.mostrarAoAbrir = opc.mostrarAoAbrir;

    addEventListener('message', function (e) {
      if (!iframe || e.source !== iframe.contentWindow) return;
      var m = e.data || {};
      if (m.kadu === 'carregou') { try { iframe.contentWindow.postMessage({ kaduCmd: 'config', cfg: cfg }, '*'); } catch (er) {} }
      else if (m.kadu === 'pronto') {
        pronto = true; fila.splice(0).forEach(function (c) { iframe.contentWindow.postMessage(c, '*'); });
        filaPronto.splice(0).forEach(function (f) { try { f(); } catch (er) {} });
      }
      else if (m.kadu === 'regioes') {
        try { var d = JSON.parse(m.j); regioes = d.r || []; tudo = !!d.tudo; menus = !!d.menus; } catch (er) {}
        if (ultMouse) decide(ultMouse.x, ultMouse.y);
      }
      else if (m.kadu === 'mouse') { ultMouse = { x: m.x, y: m.y }; decide(m.x, m.y); }
      else if (m.kadu === 'rolar') { scrollBy({ top: m.dy, left: m.dx || 0 }); }
      else if (m.kadu === 'expressoes' && esperaExp) { esperaExp(m.lista || []); esperaExp = null; }
    });

    // mouse: os olhos seguem; em cima do Kadu o iframe passa a receber o mouse de verdade
    addEventListener('pointermove', function (e) {
      if (e.pointerType === 'touch') return;
      ultMouse = { x: e.clientX, y: e.clientY }; decide(e.clientX, e.clientY);
      if (!rafMouse) rafMouse = requestAnimationFrame(function () { rafMouse = 0; manda('mouse', ultMouse); });
    }, { passive: true });
    document.documentElement.addEventListener('mouseleave', function () { manda('mouseFora'); });
    addEventListener('pointerdown', function (e) {
      if (e.pointerType !== 'touch' && menus && !dentro(e.clientX, e.clientY)) manda('foraClique');
    }, true);

    // toque (celular): o iframe nunca segura a tela; os toques em cima do Kadu são repassados para ele
    if (toque) {
      var repassa = function (tipo, t) { manda('ponteiro', { tipo: tipo, x: t.clientX, y: t.clientY }); };
      addEventListener('touchstart', function (e) {
        var t = e.touches[0]; if (!t || e.touches.length > 1) return;
        if (!dentro(t.clientX, t.clientY)) { if (menus) manda('foraClique'); return; }
        e.preventDefault(); ativoToque = true; repassa('pointerdown', t);
      }, { passive: false, capture: true });
      addEventListener('touchmove', function (e) {
        if (!ativoToque) return; e.preventDefault(); repassa('pointermove', e.touches[0]);
      }, { passive: false, capture: true });
      var fim = function (e) {
        if (!ativoToque) return; ativoToque = false; e.preventDefault(); repassa('pointerup', e.changedTouches[0]);
      };
      addEventListener('touchend', fim, { passive: false, capture: true });
      addEventListener('touchcancel', fim, { passive: false, capture: true });
    }

    // seções que fazem o Kadu falar quando aparecem
    if ('IntersectionObserver' in window) {
      var vistos = new WeakSet();
      var io = new IntersectionObserver(function (ents) {
        ents.forEach(function (en) {
          var el = en.target; if (!en.isIntersecting) return;
          var repete = el.hasAttribute('data-kadu-repetir');
          if (vistos.has(el) && !repete) return; vistos.add(el);
          api.falar(el.getAttribute('data-kadu-fala'), el.getAttribute('data-kadu-emo') || 'feliz');
        });
      }, { threshold: 0.5 });
      document.querySelectorAll('[data-kadu-fala]').forEach(function (el) { io.observe(el); });
    }
    // elementos que ele acompanha com o olhar
    document.addEventListener('pointerover', function (e) {
      var el = e.target.closest && e.target.closest('[data-kadu-olhar]'); if (!el) return;
      api.olhar(el); var emo = el.getAttribute('data-kadu-emo'); if (emo) api.expressao(emo, 1800);
    });
    document.addEventListener('pointerout', function (e) {
      var el = e.target.closest && e.target.closest('[data-kadu-olhar]'); if (!el) return;
      if (!e.relatedTarget || !el.contains(e.relatedTarget)) api.olhar(null);
    });
  }

  var api = {
    __ok: true,
    iniciar: iniciar,
    falar: function (texto, emo, ms) { if (texto) manda('falar', { texto: String(texto), emo: emo || 'neutro', ms: ms }); },
    expressao: function (nome, ms) { manda('expressao', { nome: nome, ms: ms || 2500 }); },
    pular: function () { manda('pular'); },
    mostrar: function () { manda('mostrar'); },
    esconder: function () { manda('esconder'); },
    alternar: function () { manda('alternar'); },
    olhar: function (el) {
      if (!el) { manda('olhar', { x: null }); return; }
      var r = el.getBoundingClientRect(); manda('olhar', { x: r.left + r.width / 2, y: r.top + r.height / 2 });
    },
    expressoes: function () { return new Promise(function (res) { esperaExp = res; manda('expressoes'); }); },
    pronto: function (fn) { if (pronto) fn(); else filaPronto.push(fn); }
  };
  window.Kadu = api;

  if (ds.manual !== 'true') {
    var vai = function () { iniciar({ celular: ds.celular !== 'false' }); };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', vai); else vai();
  }
})();
