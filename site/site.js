/* Caminho dos Direitos · utilidades compartilhadas do site (sem dependências) */
(function () {
  const CD = window.CD || {};
  const fmt = (n, dec = 0) => Number(n).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec });
  const pct = (n, dec = 0) => fmt(n * 100, dec) + '%';
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const COR = { urgente: '#B42318', alta: '#F79009', 'média': '#FEDF89', baixa: '#EAECF0' };
  const reduz = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- números que crescem ----------
     <b data-conta="99915" data-dec="0" data-pre="" data-suf="">0</b> */
  function animarNumero(el) {
    if (el.dataset.feito) return;
    el.dataset.feito = 1;
    const alvo = parseFloat(el.dataset.conta), dec = +(el.dataset.dec || 0);
    const pre = el.dataset.pre || '', suf = el.dataset.suf || '';
    const dur = +(el.dataset.dur || 1800);
    if (reduz) { el.textContent = pre + fmt(alvo, dec) + suf; return; }
    const t0 = performance.now();
    const passo = t => {
      const p = Math.min(1, (t - t0) / dur);
      const e = 1 - Math.pow(1 - p, 4);
      el.textContent = pre + fmt(alvo * e, dec) + suf;
      if (p < 1) requestAnimationFrame(passo);
    };
    requestAnimationFrame(passo);
  }

  /* ---------- revelar e contar quando aparece na tela ---------- */
  function observar(raiz = document) {
    const els = raiz.querySelectorAll('.rv:not(.in), [data-conta]:not([data-feito])');
    if (!('IntersectionObserver' in window)) { els.forEach(el => { el.classList.add('in'); if (el.dataset.conta) animarNumero(el); }); return; }
    const io = new IntersectionObserver(ents => ents.forEach(en => {
      if (!en.isIntersecting) return;
      const el = en.target;
      el.classList.add('in');
      if (el.dataset.conta) animarNumero(el);
      io.unobserve(el);
    }), { threshold: .15, rootMargin: '0px 0px -40px 0px' });
    els.forEach(el => io.observe(el));
  }

  /* ---------- dica flutuante ---------- */
  let dica;
  function mostrarDica(e, html) {
    if (!dica) { dica = document.createElement('div'); dica.className = 'dica'; document.body.appendChild(dica); }
    dica.innerHTML = html; dica.style.display = 'block'; moverDica(e);
  }
  function moverDica(e) {
    if (!dica) return;
    const w = dica.offsetWidth, h = dica.offsetHeight;
    let x = e.clientX + 14, y = e.clientY + 14;
    if (x + w > innerWidth - 8) x = e.clientX - w - 14;
    if (y + h > innerHeight - 8) y = e.clientY - h - 14;
    dica.style.left = Math.max(8, x) + 'px'; dica.style.top = Math.max(8, y) + 'px';
  }
  function esconderDica() { if (dica) dica.style.display = 'none'; }
  const lin = (a, b) => `<div class="lin"><span>${a}</span><b>${b}</b></div>`;

  /* ---------- mapa dos 96 distritos ----------
     opts: {destaque:Set(cod)|null, zoom:boolean, aoClicar(cod), selecionado:cod} */
  function desenharMapa(svg, opts = {}) {
    if (!CD.mapa) return;
    const { w, h, p } = CD.mapa;
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    svg.classList.add('mapa-svg');
    svg.setAttribute('role', 'img');
    svg.innerHTML = '';
    const ns = 'http://www.w3.org/2000/svg';
    const g = document.createElementNS(ns, 'g');
    svg.appendChild(g);
    const ordem = Object.keys(p).map(Number).sort((a, b) => (opts.destaque && opts.destaque.has(a)) - (opts.destaque && opts.destaque.has(b)));
    for (const cod of ordem) {
      const d = CD.distritos[cod]; if (!d) continue;
      const el = document.createElementNS(ns, 'path');
      el.setAttribute('d', p[cod]);
      el.setAttribute('fill', COR[d.cl] || '#ddd');
      el.dataset.cod = cod;
      if (opts.destaque && !opts.destaque.has(cod)) el.classList.add('fora');
      if (opts.selecionado === cod) el.classList.add('sel');
      el.addEventListener('mouseenter', e => mostrarDica(e,
        `<b>${esc(d.n)}</b><div style="color:#5B6271;margin-bottom:4px">${esc(d.s)}</div>` +
        lin('Prioridade', `<span class="cl ${d.cl}">${d.cl}</span>`) + lin('Índice', fmt(d.idx, 1)) +
        lin('Direito provável sem benefício', fmt(d.lac) + ' pessoas')));
      el.addEventListener('mousemove', moverDica);
      el.addEventListener('mouseleave', esconderDica);
      if (opts.aoClicar) el.addEventListener('click', () => opts.aoClicar(cod));
      g.appendChild(el);
    }
    if (opts.zoom && opts.destaque && opts.destaque.size) {
      requestAnimationFrame(() => {
        let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
        g.querySelectorAll('path').forEach(el => {
          if (!opts.destaque.has(+el.dataset.cod)) return;
          const b = el.getBBox();
          x0 = Math.min(x0, b.x); y0 = Math.min(y0, b.y); x1 = Math.max(x1, b.x + b.width); y1 = Math.max(y1, b.y + b.height);
        });
        if (!isFinite(x0)) return;
        const m = Math.max(x1 - x0, y1 - y0) * .25;
        svg.setAttribute('viewBox', `${x0 - m} ${y0 - m} ${x1 - x0 + 2 * m} ${y1 - y0 + 2 * m}`);
      });
    }
  }
  function legendaMapa() {
    return ['urgente', 'alta', 'média', 'baixa'].map(c => `<span><i style="background:${COR[c]}"></i>${c[0].toUpperCase() + c.slice(1)}</span>`).join('');
  }

  /* ---------- cabeçalho com sombra ao rolar ---------- */
  function cabecalho() {
    const t = document.querySelector('.topo');
    if (!t) return;
    const f = () => t.classList.toggle('rolou', scrollY > 8);
    addEventListener('scroll', f, { passive: true }); f();
  }

  /* ---------- armazenamento local à prova de falha ---------- */
  const guardar = (k, v) => { try { localStorage.setItem('cd_' + k, JSON.stringify(v)); } catch (e) { } };
  const ler = (k, padrao) => { try { const v = localStorage.getItem('cd_' + k); return v ? JSON.parse(v) : padrao; } catch (e) { return padrao; } };

  /* ---------- ícones (sprite SVG, traço) ---------- */
  const ICONES = {
    seta: '<path d="M5 12h14M13 6l6 6-6 6"/>', check: '<path d="M20 6 9 17l-5-5"/>',
    doc: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    msg: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
    escudo: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    grafico: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    pessoas: '<circle cx="9" cy="8" r="4"/><path d="M2 21c0-4 3-6 7-6s7 2 7 6M16 4a4 4 0 0 1 0 8M22 21c0-3-2-5-4-5.6"/>',
    pin: '<path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    alvo: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    camadas: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    banco: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    cpu: '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    entrada: '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
    tela: '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    cadeado: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    predio: '<path d="M3 21h18M5 21V9l7-5 7 5v12M9 21v-6h6v6"/>',
    sino: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8M10 20a2 2 0 0 0 4 0"/>',
    play: '<path d="M7 4v16l13-8z"/>', celular: '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/>',
    olho: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    entrar: '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/>',
    sair: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    raio: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>', x: '<path d="M18 6 6 18M6 6l12 12"/>',
    casa: '<path d="M3 11 12 4l9 7M5 10v10h14V10"/>', troca: '<path d="M7 7h13l-4-4M17 17H4l4 4"/>',
    lista: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    calendario: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    alerta: '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17h.01"/>',
    lupa: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>'
  };
  const sprite = '<svg width="0" height="0" style="position:absolute" aria-hidden="true">' +
    Object.entries(ICONES).map(([k, v]) => `<symbol id="i-${k}" viewBox="0 0 24 24">${v}</symbol>`).join('') + '</svg>';
  if (document.body) document.body.insertAdjacentHTML('afterbegin', sprite);
  const ic = (n, cls = '') => `<svg class="ic ${cls}" aria-hidden="true"><use href="#i-${n}"/></svg>`;

  window.CDS = { ic, fmt, pct, esc, COR, lin, animarNumero, observar, desenharMapa, legendaMapa, mostrarDica, moverDica, esconderDica, guardar, ler };
  document.addEventListener('DOMContentLoaded', () => { cabecalho(); observar(); });
})();
