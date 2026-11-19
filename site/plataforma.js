/* Caminho dos Direitos · plataforma demonstrativa por cargo
   Território: dados públicos reais (dados/saida, dados/saida_modelo).
   Uso do app: SIMULADO (dados/saida_app). Pessoas da equipe: fictícias. */
(function () {
  const { ic, fmt, pct, esc, COR, desenharMapa, legendaMapa, observar, guardar, ler } = CDS;
  const D = CD.distritos;
  const q = new URLSearchParams(location.search);
  const $ = id => document.getElementById(id);
  const titulo = s => s.toLowerCase().replace(/(^|\s|\/)(\S)/g, (m, a, b) => a + b.toUpperCase()).replace(/\b(Da|De|Do|Dos|Das|E)\b/g, w => w.toLowerCase()).replace(/^Ubs|\bUbs\b/g, 'UBS').replace(/\bAma\b/g, 'AMA').replace(/\bCras\b/g, 'CRAS');
  const ORDEM_CL = { urgente: 0, alta: 1, 'média': 2, baixa: 3 };
  const todos = Object.keys(D).map(Number);
  const subs = [...new Set(todos.map(k => D[k].s))].sort((a, b) => a.localeCompare(b, 'pt'));

  /* ---------- perfil e escopo ---------- */
  let perfil = q.get('perfil');
  if (!['sec', 'sub', 'coord', 'agente'].includes(perfil)) perfil = 'sec';
  let SUB = q.get('sub'); if (!subs.includes(SUB)) SUB = "M'Boi Mirim";
  let UNI = q.get('uni'); if (!CD.unidades[UNI]) UNI = '410';
  const uni = CD.unidades[UNI];

  const escopo = perfil === 'sec' ? new Set(todos)
    : perfil === 'sub' ? new Set(todos.filter(k => D[k].s === SUB))
    : new Set([uni.d]);
  const noEscopo = [...escopo].sort((a, b) => D[b].idx - D[a].idx);

  const PERFIS = {
    sec: { nome: 'Secretaria municipal', cargo: 'Assistência Social · cidade', av: 'S', cor: 'var(--azul)', chip: 'Perfil: Secretaria',
      menu: [['visao', 'Visão da cidade', 'grafico'], ['ranking', 'Onde agir primeiro', 'alvo'], ['campanhas', 'Campanhas', 'sino'], ['subprefeituras', 'Subprefeituras', 'pin'], ['insights', 'Insights do modelo', 'raio'], ['painel', 'Painel completo', 'tela']] },
    sub: { nome: 'Subprefeitura', cargo: 'Gestão · ' + SUB, av: 'G', cor: 'var(--laranja)', chip: 'Perfil: Subprefeitura · RLS',
      menu: [['visao', 'Visão do território', 'pin'], ['campanhas', 'Campanhas', 'sino'], ['alertas', 'Alertas cruzados', 'alerta'], ['unidades', 'Unidades', 'predio'], ['painel', 'Painel da subprefeitura', 'tela']] },
    coord: { nome: 'Coordenação', cargo: titulo(uni.n), av: 'C', cor: 'var(--verde-esc)', chip: 'Perfil: Coordenação',
      menu: [['visao', 'Minha unidade', 'casa'], ['acessos', 'Pedidos de acesso', 'cadeado'], ['equipe', 'Equipe e casos', 'pessoas'], ['campanhas', 'Campanhas do território', 'sino'], ['painel', 'Painel da unidade', 'tela']] },
    agente: { nome: 'Agente de campo', cargo: 'ACS · ' + titulo(CD.unidades['410'].n), av: 'A', cor: '#8A6200', chip: 'Perfil: Agente',
      menu: [['hoje', 'Visitas de hoje', 'calendario'], ['telas', 'Telas do app', 'celular'], ['ia', 'IA em ação', 'mic']] }
  };
  const P = PERFIS[perfil];
  document.title = P.nome + ' · Caminho dos Direitos';
  $('perfil-nome').textContent = P.nome;
  $('perfil-tag').textContent = perfil === 'sec' ? 'cidade' : perfil === 'sub' ? 'RLS' : perfil === 'coord' ? 'unidade' : 'campo';
  $('u-av').textContent = P.av; $('u-av').style.background = P.cor;
  $('u-cargo').textContent = P.cargo;
  $('chip-perfil').textContent = P.chip;

  /* ---------- estado guardado (só conveniência deste navegador) ---------- */
  const EST = ler('estado', { camp: {}, acessos: null, equipe: null });

  /* ---------- menu ---------- */
  const menu = $('menu');
  function badge(v) {
    if (v === 'acessos') { const n = pedidos().filter(p => !p.st).length; return n ? `<span class="badge">${n}</span>` : ''; }
    if (v === 'alertas') { const n = CD.alertas.filter(a => escopo.has(a.d)).length; return n ? `<span class="badge">${n}</span>` : ''; }
    return '';
  }
  function montarMenu(atual) {
    menu.innerHTML = P.menu.map(([v, t, i]) => `<button type="button" data-v="${v}"${v === atual ? ' aria-current="page"' : ''}>${ic(i)}${t}${badge(v)}</button>`).join('');
    menu.querySelectorAll('button').forEach(b => b.onclick = () => { location.hash = b.dataset.v; fecharMenu(); });
  }
  const lat = $('lateral'), mb = $('menu-btn');
  mb.onclick = () => { const a = lat.classList.toggle('aberta'); mb.setAttribute('aria-expanded', a); };
  function fecharMenu() { lat.classList.remove('aberta'); mb.setAttribute('aria-expanded', false); }
  document.addEventListener('click', e => { if (lat.classList.contains('aberta') && !lat.contains(e.target) && !mb.contains(e.target)) fecharMenu(); });

  const toastEl = $('toast'); let tt;
  function toast(t) { toastEl.textContent = t; toastEl.classList.add('on'); clearTimeout(tt); tt = setTimeout(() => toastEl.classList.remove('on'), 2600); }

  /* ---------- peças reutilizáveis ---------- */
  const vista = $('vista');
  const kpi = (v, rot, i, cor, origem, dec = 0, suf = '') =>
    `<div class="kpi" style="--c:${cor}">${ic(i)}<span>${rot}</span><b data-conta="${v}" data-dec="${dec}" data-suf="${suf}">0</b><small class="${origem === 'Simulado' ? 'sim' : ''}">${origem}</small></div>`;
  const cab = (sup, t, p, extra = '') => `<div class="cab-vista"><div><small>${sup}</small><h1>${t}</h1><p>${p}</p></div>${extra}</div>`;
  const rls = () => perfil === 'sub'
    ? `<div class="rls">${ic('escudo')}<div><b>Segurança por linha aplicada.</b> Você vê só a Subprefeitura ${esc(SUB)} (${escopo.size} distrito${escopo.size > 1 ? 's' : ''}). No Power BI, isso vem do login no Microsoft Entra ID.</div></div>`
    : perfil === 'coord' ? `<div class="rls">${ic('escudo')}<div><b>Acesso da unidade.</b> Você vê os casos da ${esc(titulo(uni.n))}. Nome e CPF das pessoas atendidas não aparecem no painel.</div></div>` : '';
  const soma = (ks, f) => ks.reduce((s, k) => s + f(D[k]), 0);

  function detalheDistrito(cod) {
    const d = D[cod];
    const recs = CD.recs.filter(r => r.d === cod);
    const barra = (rot, real, esp) => `<div><div class="rot"><span>${rot}</span><b>${pct(real, 1)} <span style="font-weight:400">· esperado ${pct(esp, 1)}</span></b></div>
      <div class="trilho"><div class="real" style="width:0" data-w="${Math.min(100, real * 100 / Math.max(real, esp, .0001) * .9)}"></div><span class="esp" style="left:${Math.min(100, esp * 100 / Math.max(real, esp, .0001) * .9)}%" title="Esperado para o perfil"></span></div></div>`;
    return `<div class="det">
      <span class="cl ${d.cl}">${d.cl}</span>
      <h3>${esc(d.n)}</h3><div class="onde">Subprefeitura ${esc(d.s)} · ${fmt(d.pop)} habitantes</div>
      <div class="idx"><b>${fmt(d.idx, 1)}</b><span>índice de prioridade<br>(0 a 100)</span></div>
      <div class="mini-kpis">
        <div><b>${fmt(d.lac)}</b><span>direito provável sem benefício</span></div>
        <div><b>${fmt(d.r34)}</b><span>setores de risco R3/R4</span></div>
        <div><b>${fmt(d.dcras, 1)} km</b><span>distância média ao CRAS</span></div>
      </div>
      <div class="compar">
        ${barra('Cobertura do Bolsa Família', d.cobPbf, d.cobPbfEsp)}
        ${barra('Cobertura do BPC idoso', d.txBpc, d.txBpcEsp)}
      </div>
      <div class="acoes">${recs.length ? recs.map(r => `<div class="acao">${ic('sino')}<div><b>${esc(r.a)}</b>${esc(r.m)}${r.pub ? ` · público ${fmt(r.pub)}` : ''}</div></div>`).join('')
        : `<div class="acao">${ic('check')}<div><b>Sem campanha recomendada</b>As campanhas vão só para distritos de prioridade urgente ou alta.</div></div>`}</div>
    </div>`;
  }
  function animarBarras(el) { requestAnimationFrame(() => el.querySelectorAll('[data-w]').forEach(b => b.style.width = b.dataset.w + '%')); }

  function blocoMapa(selecionado, zoom) {
    const box = document.createElement('div');
    box.className = 'grade';
    box.innerHTML = `<div class="bloco"><div class="bloco-cab"><div><h2>Mapa de prioridade</h2><p class="sub">${perfil === 'sec' ? 'Clique em um distrito para ver o detalhe.' : 'Distritos fora do seu acesso aparecem apagados.'}</p></div><div class="legenda">${legendaMapa()}</div></div><div class="mapa-box"><svg id="mapa"></svg></div></div>
      <div class="bloco" id="det"></div>`;
    const sel = c => {
      if (!escopo.has(c)) { toast('Fora do seu acesso: ' + D[c].n + ' é de outra subprefeitura.'); return; }
      $('det').innerHTML = detalheDistrito(c); animarBarras($('det'));
      box.querySelectorAll('#mapa path').forEach(p => p.classList.toggle('sel', +p.dataset.cod === c));
    };
    requestAnimationFrame(() => {
      desenharMapa($('mapa'), { destaque: perfil === 'sec' ? null : escopo, zoom, aoClicar: sel, selecionado });
      sel(selecionado);
    });
    return box;
  }

  function tabelaDistritos(ks, opts = {}) {
    const max = Math.max(...ks.map(k => D[k].lac), 1);
    return `<div class="tab-wrap"><table class="tab"><thead><tr><th>#</th><th>Distrito</th>${opts.semSub ? '' : '<th>Subprefeitura</th>'}<th>Prioridade</th><th class="n">Índice</th><th>Direito provável sem benefício</th><th class="n">R3/R4</th></tr></thead><tbody>
      ${ks.map((k, i) => { const d = D[k]; return `<tr data-cod="${k}"><td class="pos">${i + 1}</td><td><b>${esc(d.n)}</b></td>${opts.semSub ? '' : `<td>${esc(d.s)}</td>`}<td><span class="cl ${d.cl}">${d.cl}</span></td><td class="n"><b>${fmt(d.idx, 1)}</b></td>
      <td><div class="barrinha"><i style="width:${Math.max(2, d.lac / max * 120)}px;background:${COR[d.cl] === '#EAECF0' ? '#B8BFCC' : COR[d.cl] === '#FEDF89' ? '#E9B949' : COR[d.cl]}"></i>${fmt(d.lac)}</div></td><td class="n">${fmt(d.r34)}</td></tr>`; }).join('')}
      </tbody></table></div>`;
  }
  function ligarLinhas(raiz) {
    raiz.querySelectorAll('tr[data-cod]').forEach(tr => tr.onclick = () => { VISTA_DIST = +tr.dataset.cod; location.hash = 'visao'; });
  }
  let VISTA_DIST = null;

  /* ---------- campanhas (aprovar / confirmar) ---------- */
  function vistaCampanhas() {
    const lista = CD.recs.filter(r => escopo.has(r.d)).sort((a, b) => ORDEM_CL[D[a.d].cl] - ORDEM_CL[D[b.d].cl] || D[b.d].idx - D[a.d].idx);
    const verbo = perfil === 'coord' ? 'Confirmar indicação' : 'Aprovar campanha';
    const feito = perfil === 'coord' ? 'Indicação confirmada' : 'Campanha aprovada';
    vista.innerHTML = cab(perfil === 'sec' ? 'Cidade' : perfil === 'sub' ? SUB : titulo(uni.n), 'Campanhas recomendadas',
      'O modelo recomenda campanhas só para distritos de prioridade urgente ou alta, com o motivo e o público estimado.') + rls() +
      `<div class="resumo" id="resumo"></div><div class="camps" id="camps"></div>
       <p class="fonte">Origem: ESTIMATIVA DO MODELO (Modelo_GS_v4). A aprovação é só uma simulação e fica guardada neste navegador.</p>`;
    const id = r => r.d + '|' + r.a;
    function desenhar() {
      $('camps').innerHTML = lista.length ? lista.map(r => {
        const ok = !!EST.camp[id(r)], d = D[r.d];
        return `<div class="camp${ok ? ' ok' : ''}"><div class="topo-c"><span class="cl ${d.cl}">${d.cl}</span><span class="chip az">${esc(r.p)}</span></div>
          <h3>${esc(r.a)}</h3><p><b style="color:var(--texto)">${esc(d.n)}</b> · ${esc(d.s)}</p><p>${esc(r.m)}</p>
          ${r.pub ? `<div class="pub"><b>${fmt(r.pub)}</b> pessoas ou famílias no público estimado</div>` : ''}
          <button type="button" class="bt ${ok ? 'feito' : 'pri'}" data-id="${esc(id(r))}">${ic(ok ? 'check' : 'sino')}${ok ? feito : verbo}</button></div>`;
      }).join('') : `<div class="vazio">Nenhuma campanha recomendada no seu acesso. As campanhas vão só para distritos urgentes ou de prioridade alta.</div>`;
      $('camps').querySelectorAll('button[data-id]').forEach(b => b.onclick = () => {
        const k = b.dataset.id; EST.camp[k] = !EST.camp[k]; guardar('estado', EST);
        toast(EST.camp[k] ? feito + '.' : 'Aprovação desfeita.'); desenhar();
      });
      const apr = lista.filter(r => EST.camp[id(r)]);
      $('resumo').innerHTML = `<div><b>${lista.length}</b> <span>recomendadas</span></div><div><b>${apr.length}</b> <span>${perfil === 'coord' ? 'confirmadas' : 'aprovadas'}</span></div>
        <div><b>${fmt(apr.reduce((s, r) => s + (r.pub || 0), 0))}</b> <span>no público das aprovadas</span></div>`;
    }
    desenhar();
  }

  /* ---------- painel embutido ---------- */
  function vistaPainel() {
    // coordenador de unidade abre na aba Operação; secretaria e subprefeitura, na aba Gestão
    const qs = perfil === 'sub' ? `?sub=${encodeURIComponent(SUB)}&travar=1&aba=gestao` : perfil === 'coord' ? `?uni=${UNI}&travar=1&aba=operacao` : '?aba=gestao';
    vista.innerHTML = cab('Power BI · versão HTML', P.menu.find(m => m[0] === 'painel')[1],
      perfil === 'sec' ? 'O painel completo, sem restrição: os 96 distritos e todas as unidades. Abre na aba Gestão (metas, evolução e onde agir); a aba Operação mostra a fila de trabalho das unidades.' : perfil === 'coord' ? 'O mesmo painel, com o filtro travado na sua unidade. Abre na aba Operação: fila de trabalho, quem espera há mais tempo e o próximo passo de cada caso.' : 'O mesmo painel, com o filtro travado no seu acesso. Abre na aba Gestão: metas, evolução no tempo e onde agir primeiro.',
      `<a class="btn btn-contorno btn-sm" href="../dashboard/index.html${qs}" target="_blank" rel="noopener">${ic('olho')}Abrir em tela cheia</a>`) + rls() +
      `<div class="painel-frame"><iframe src="../dashboard/index.html${qs}" title="Painel do monitoramento"></iframe></div>`;
  }

  /* =====================================================================
     SECRETARIA
     ===================================================================== */
  function secVisao() {
    const urg = todos.filter(k => D[k].cl === 'urgente').length, alt = todos.filter(k => D[k].cl === 'alta').length;
    vista.innerHTML = cab('Secretaria municipal · Assistência Social', 'Visão da cidade',
      'Onde estão as pessoas com direito provável a BPC idoso ou Bolsa Família que ainda não recebem, e onde agir primeiro.') +
      `<div class="kpis">${kpi(soma(todos, d => d.lac), 'Pessoas com direito provável sem benefício', 'pessoas', 'var(--p-urgente)', 'Estimativa do modelo')}
        ${kpi(urg, `Distritos urgentes (+ ${alt} de prioridade alta)`, 'alerta', 'var(--laranja)', 'Estimativa do modelo')}
        ${kpi(CD.kpi.cad, 'Famílias no CadÚnico', 'lista', 'var(--azul)', 'Real · SMADS')}
        ${kpi(CD.app.concl, 'Encaminhamentos concluídos pelo app', 'check', 'var(--verde-esc)', 'Simulado')}</div>`;
    vista.appendChild(blocoMapa(VISTA_DIST || noEscopo[0], false));
    const t = document.createElement('div'); t.className = 'bloco';
    t.innerHTML = `<div class="bloco-cab"><div><h2>Os 10 distritos mais prioritários</h2><p class="sub">Concentram 55% das pessoas com direito provável sem benefício. Clique para ver o detalhe.</p></div><button class="bt" type="button" id="ver-todos">${ic('lista')}Ver os 96</button></div>${tabelaDistritos(noEscopo.slice(0, 10))}`;
    vista.appendChild(t);
    t.querySelectorAll('tr[data-cod]').forEach(tr => tr.onclick = () => { VISTA_DIST = +tr.dataset.cod; secVisao(); scrollTo({ top: 0, behavior: 'smooth' }); });
    $('ver-todos').onclick = () => location.hash = 'ranking';
    VISTA_DIST = null;
  }
  function secRanking() {
    let cl = 'todas', busca = '', sub = '';
    vista.innerHTML = cab('Secretaria municipal', 'Onde agir primeiro', 'Os 96 distritos ordenados pelo índice de prioridade. Filtre por classe, subprefeitura ou nome.') +
      `<div class="explica">${ic('alvo')}<div><b>O que é o índice de prioridade?</b>Uma nota de 0 a 100 que diz onde a busca ativa rende mais. Quanto maior, mais urgente: pesa principalmente quantas pessoas têm direito provável e ainda não recebem o benefício, e também a distância até o CRAS, as áreas de risco e o peso do CadÚnico no distrito.</div></div>
      <div class="bloco"><div class="filtros" id="fcl" style="margin-bottom:14px"></div><div id="tab"></div></div>
       <p class="fonte">Índice (0 a 100): soma ponderada, normalizada, de pessoas com direito provável sem benefício (45%), distância ao CRAS (25%), setores de risco R3/R4 (15%) e CadÚnico por mil habitantes (15%). Origem: ESTIMATIVA DO MODELO (Modelo_GS_v4).</p>`;
    function desenhar() {
      $('fcl').innerHTML = ['todas', 'urgente', 'alta', 'média', 'baixa'].map(c => `<button type="button" data-c="${c}" aria-pressed="${c === cl}">${c === 'todas' ? 'Todas' : c[0].toUpperCase() + c.slice(1)}</button>`).join('') +
        `<select id="fsub" aria-label="Subprefeitura"><option value="">Todas as subprefeituras</option>${subs.map(s => `<option${s === sub ? ' selected' : ''}>${esc(s)}</option>`).join('')}</select>
         <input id="fbusca" type="search" placeholder="Buscar distrito" value="${esc(busca)}" aria-label="Buscar distrito">`;
      $('fcl').querySelectorAll('button').forEach(b => b.onclick = () => { cl = b.dataset.c; desenhar(); });
      $('fsub').onchange = e => { sub = e.target.value; desenhar(); };
      const fb = $('fbusca'); fb.oninput = e => { busca = e.target.value; tabela(); };
      tabela();
    }
    function tabela() {
      const n = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
      const ks = noEscopo.filter(k => (cl === 'todas' || D[k].cl === cl) && (!sub || D[k].s === sub) && (!busca || n(D[k].n).includes(n(busca))));
      $('tab').innerHTML = ks.length ? tabelaDistritos(ks) : '<div class="vazio">Nenhum distrito com esses filtros.</div>';
      ligarLinhas($('tab'));
    }
    desenhar();
  }
  function secSubs() {
    const linhas = subs.map(s => {
      const ks = todos.filter(k => D[k].s === s);
      return { s, n: ks.length, lac: soma(ks, d => d.lac), urg: ks.filter(k => D[k].cl === 'urgente').length, alt: ks.filter(k => D[k].cl === 'alta').length, max: Math.max(...ks.map(k => D[k].idx)), top: ks.sort((a, b) => D[b].idx - D[a].idx)[0] };
    }).sort((a, b) => b.lac - a.lac);
    const mx = linhas[0].lac;
    vista.innerHTML = cab('Secretaria municipal', 'Subprefeituras', 'As 32 subprefeituras pela lacuna total. Clique para ver o painel como o gestor daquela subprefeitura veria.') +
      `<div class="bloco"><div class="tab-wrap"><table class="tab"><thead><tr><th>Subprefeitura</th><th class="n">Distritos</th><th>Direito provável sem benefício</th><th class="n">Urgentes</th><th class="n">Alta</th><th>Distrito mais prioritário</th></tr></thead><tbody>
      ${linhas.map(l => `<tr data-s="${esc(l.s)}"><td><b>${esc(l.s)}</b></td><td class="n">${l.n}</td><td><div class="barrinha"><i style="width:${Math.max(2, l.lac / mx * 140)}px;background:var(--azul)"></i>${fmt(l.lac)}</div></td>
        <td class="n">${l.urg || '–'}</td><td class="n">${l.alt || '–'}</td><td>${esc(D[l.top].n)} <span class="cl ${D[l.top].cl}">${fmt(l.max, 1)}</span></td></tr>`).join('')}
      </tbody></table></div></div>`;
    vista.querySelectorAll('tr[data-s]').forEach(tr => tr.onclick = () => location.href = 'plataforma.html?perfil=sub&sub=' + encodeURIComponent(tr.dataset.s));
  }
  function secInsights() {
    const m = CD.app;
    vista.innerHTML = cab('Secretaria municipal', 'Insights do modelo', 'O que os dados mostram e como isso muda a decisão.') +
      `<div class="kpis">${kpi(0.81, 'R² do modelo de BPC idoso (Random Forest, validação cruzada)', 'alvo', 'var(--azul)', 'Modelo', 2)}
        ${kpi(55, 'das pessoas com direito sem benefício estão em 10 distritos', 'pin', 'var(--p-urgente)', 'Estimativa do modelo', 0, '%')}
        ${kpi(m.lemComp / m.lem * 100, 'de comparecimento com lembrete no WhatsApp', 'msg', 'var(--verde-esc)', 'Simulado', 1, '%')}
        ${kpi(m.semLemComp / m.semLem * 100, 'de comparecimento sem lembrete', 'x', 'var(--texto-2)', 'Simulado', 1, '%')}</div>
      <div class="alertas">${CD.insights.map((t, i) => `<div class="alerta"><span class="cl alta num">${i + 1}</span><p>${esc(t)}</p></div>`).join('')}</div>
      <p class="fonte">Insights 1 a 5: Modelo_GS_v4 (testes de Spearman e de diferença de proporções). Comparecimento: dados do app SIMULADOS, só para mostrar o indicador.</p>`;
  }

  /* =====================================================================
     SUBPREFEITURA
     ===================================================================== */
  function subVisao() {
    const ks = noEscopo;
    const unis = Object.values(CD.unidades).filter(u => escopo.has(u.d));
    vista.innerHTML = cab('Subprefeitura · ' + esc(SUB), 'Visão do território', 'Os distritos da sua subprefeitura, com o que o modelo recomenda e o que o app registrou.') + rls() +
      `<div class="kpis">${kpi(soma(ks, d => d.lac), 'Pessoas com direito provável sem benefício', 'pessoas', 'var(--p-urgente)', 'Estimativa do modelo')}
        ${kpi(soma(ks, d => d.pop), 'Habitantes', 'casa', 'var(--azul)', 'Real · Censo 2022')}
        ${kpi(soma(ks, d => d.r34), 'Setores de risco R3/R4', 'alerta', 'var(--laranja)', 'Real · GeoSampa')}
        ${kpi(unis.reduce((s, u) => s + u.casos, 0), `Casos no app em ${unis.length} unidades`, 'lista', 'var(--verde-esc)', 'Simulado')}</div>`;
    vista.appendChild(blocoMapa(VISTA_DIST && escopo.has(VISTA_DIST) ? VISTA_DIST : ks[0], true));
    const t = document.createElement('div'); t.className = 'bloco';
    t.innerHTML = `<h2>Distritos da subprefeitura</h2><p class="sub">Posição de cada um entre os 96 da cidade.</p>${tabelaDistritos(ks, { semSub: true })}`;
    vista.appendChild(t);
    const pos = Object.fromEntries(Object.keys(D).map(Number).sort((a, b) => D[b].idx - D[a].idx).map((k, i) => [k, i + 1]));
    t.querySelectorAll('tr[data-cod]').forEach(tr => { tr.querySelector('.pos').textContent = pos[tr.dataset.cod] + 'º'; tr.onclick = () => { VISTA_DIST = +tr.dataset.cod; subVisao(); scrollTo({ top: 0, behavior: 'smooth' }); }; });
    VISTA_DIST = null;
  }
  function subAlertas() {
    const al = CD.alertas.filter(a => escopo.has(a.d));
    vista.innerHTML = cab('Subprefeitura · ' + esc(SUB), 'Alertas cruzados', 'Quando o que o território mostra e o que o app registra apontam para o mesmo problema.') + rls() +
      (al.length ? `<div class="alertas">${al.map(a => `<div class="alerta ${a.g}">${ic('alerta')}<div><b>${esc(a.r)} · gravidade ${esc(a.g)}</b><p>${esc(a.t)}</p></div></div>`).join('')}</div>`
        : '<div class="vazio">Nenhum alerta cruzado na sua subprefeitura agora.</div>') +
      '<p class="fonte">Origem: SIMULADO + TERRITÓRIO. As regras cruzam a prioridade do distrito com o que os agentes registraram.</p>';
  }
  function subUnidades() {
    const us = Object.entries(CD.unidades).filter(([k, u]) => escopo.has(u.d)).sort((a, b) => b[1].casos - a[1].casos);
    const mx = Math.max(...us.map(([, u]) => u.casos), 1);
    vista.innerHTML = cab('Subprefeitura · ' + esc(SUB), 'Unidades', `As ${us.length} UBS e CRAS que usam o app no seu território.`) + rls() +
      `<div class="bloco"><div class="tab-wrap"><table class="tab"><thead><tr><th>Unidade</th><th>Tipo</th><th>Distrito</th><th>Casos no app</th><th class="n">Em área R3/R4</th><th class="n">Aceitam lembrete</th></tr></thead><tbody>
      ${us.map(([k, u]) => `<tr data-u="${k}"><td><b>${esc(titulo(u.n))}</b></td><td><span class="chip ${u.t === 'CRAS' ? 'vd' : 'az'}">${u.t}</span></td><td>${esc(D[u.d].n)}</td>
        <td><div class="barrinha"><i style="width:${Math.max(2, u.casos / mx * 110)}px;background:var(--verde)"></i>${u.casos}</div></td><td class="n">${u.risco}</td><td class="n">${pct(u.lem / Math.max(1, u.casos))}</td></tr>`).join('')}
      </tbody></table></div></div><p class="fonte">Casos: SIMULADO. Clique em uma unidade para ver a visão da coordenação.</p>`;
    vista.querySelectorAll('tr[data-u]').forEach(tr => tr.onclick = () => location.href = 'plataforma.html?perfil=coord&uni=' + tr.dataset.u);
  }

  /* =====================================================================
     COORDENAÇÃO
     ===================================================================== */
  const AGENTES_BASE = [['Ana Paula S.', 'ACS'], ['Rogério T.', 'ACS'], ['Juliana M.', 'Assistente social'], ['Marcos V.', 'ACS']];
  function equipe() {
    if (EST.equipe && EST.equipe.uni === UNI) return EST.equipe.l;
    const n = uni.casos, l = AGENTES_BASE.map(([nome, f], i) => ({ nome, f, casos: Math.floor(n / 4) + (i < n % 4 ? 1 : 0) }));
    EST.equipe = { uni: UNI, l }; return l;
  }
  function pedidos() {
    if (EST.acessos && EST.acessos.uni === UNI) return EST.acessos.l;
    const l = [{ nome: 'Beatriz L.', f: 'ACS', cpf: '***.***.***-41', quando: 'hoje, 08:12', via: 'PIN' },
      { nome: 'Carlos E.', f: 'Assistente social', cpf: '***.***.***-07', quando: 'ontem, 17:40', via: 'Código no WhatsApp' },
      { nome: 'Denise R.', f: 'ACS', cpf: '***.***.***-93', quando: 'ontem, 09:05', via: 'PIN' }];
    EST.acessos = { uni: UNI, l }; return l;
  }
  const corSit = { 'Já recebe': '#12B76A', 'Precisa atualizar': '#FEC84B', 'Ainda não pediu': '#F79009', 'Falta documento': '#F97066', 'Bloqueado': '#B42318' };
  const corRes = { 'Concluído': '#12B76A', 'Compareceu': '#84ADFF', 'Agendado': '#9B9FA6', 'Faltou': '#F04438' };
  function pilha(obj, cores) {
    const tot = Object.values(obj).reduce((s, v) => s + v, 0) || 1;
    const ks = Object.keys(cores).filter(k => obj[k]);
    return `<div class="pilha">${ks.map(k => `<div style="flex:${obj[k]};background:${cores[k]};color:${k === 'Precisa atualizar' ? '#101828' : '#fff'}" title="${k}: ${obj[k]}">${obj[k] / tot > .08 ? pct(obj[k] / tot) : ''}</div>`).join('')}</div>
      <div class="leg-pilha">${ks.map(k => `<span><i style="background:${cores[k]}"></i>${k} (${obj[k]})</span>`).join('')}</div>`;
  }
  function coordVisao() {
    const d = D[uni.d];
    const enc = Object.values(uni.res).reduce((s, v) => s + v, 0);
    vista.innerHTML = cab('Coordenação · ' + uni.t, esc(titulo(uni.n)), `${esc(d.n)} · Subprefeitura ${esc(d.s)} · distrito de prioridade <span class="cl ${d.cl}">${d.cl}</span>`) + rls() +
      `<div class="kpis">${kpi(uni.ativos, 'Casos ativos na unidade', 'lista', 'var(--azul)', 'Simulado')}
        ${kpi(enc, 'Encaminhamentos registrados', 'pin', 'var(--laranja)', 'Simulado')}
        ${kpi((uni.res['Concluído'] || 0) + (uni.res['Compareceu'] || 0), 'Pessoas que compareceram', 'check', 'var(--verde-esc)', 'Simulado')}
        ${kpi(pedidos().filter(p => !p.st).length, 'Pedidos de acesso esperando você', 'cadeado', 'var(--p-urgente)', 'Demonstração')}</div>
      <div class="grade">
        <div class="bloco"><h2>Situação dos direitos nos planos</h2><p class="sub">Cada caso tem até 7 programas no Plano de Direitos.</p>${pilha(uni.sit, corSit)}</div>
        <div class="bloco"><h2>Resultado dos encaminhamentos</h2><p class="sub">Do agendamento até a conclusão.</p>${pilha(uni.res, corRes)}</div>
      </div>
      <div class="bloco"><h2>O território da unidade</h2><p class="sub">O que o modelo diz sobre ${esc(d.n)}.</p>${detalheDistrito(uni.d)}</div>`;
    animarBarras(vista);
  }
  function coordAcessos() {
    const l = pedidos();
    vista.innerHTML = cab('Coordenação · ' + esc(titulo(uni.n)), 'Pedidos de acesso', 'O agente pede acesso com CPF e a unidade, sem gov.br. Só entra depois que você aprova.') + rls() +
      `<div class="bloco"><h2>Esperando aprovação</h2><p class="sub">Pessoas fictícias, para demonstração.</p><div class="lista-p" id="pend"></div></div>
       <div class="bloco" style="margin-top:18px"><h2>Já decididos</h2><div class="lista-p" id="feitos"></div></div>`;
    function desenhar() {
      const pend = l.filter(p => !p.st), feitos = l.filter(p => p.st);
      const linha = (p, i) => `<div class="lp"><span class="av" style="background:${['var(--azul)', 'var(--verde-esc)', 'var(--laranja)'][i % 3]}">${p.nome[0]}</span>
        <div class="info"><b>${esc(p.nome)} · ${esc(p.f)}</b><span>CPF ${p.cpf} · pediu ${p.quando} · entrada por ${p.via}</span></div>
        ${p.st ? `<span class="chip ${p.st === 'ok' ? 'vd' : 'vm'}">${p.st === 'ok' ? 'Aprovado' : 'Recusado'}</span>`
          : `<div class="bts"><button class="bt sim" data-i="${l.indexOf(p)}" data-a="ok">${ic('check')}Aprovar</button><button class="bt nao" data-i="${l.indexOf(p)}" data-a="no">${ic('x')}Recusar</button></div>`}</div>`;
      $('pend').innerHTML = pend.length ? pend.map(linha).join('') : '<div class="vazio">Nenhum pedido esperando. Tudo em dia.</div>';
      $('feitos').innerHTML = feitos.length ? feitos.map(linha).join('') : '<div class="vazio">Nada decidido ainda.</div>';
      vista.querySelectorAll('button[data-a]').forEach(b => b.onclick = () => {
        const p = l[+b.dataset.i]; p.st = b.dataset.a; guardar('estado', EST);
        if (p.st === 'ok') { equipe().push({ nome: p.nome, f: p.f, casos: 0 }); guardar('estado', EST); }
        toast(p.st === 'ok' ? `${p.nome} aprovado. O PIN foi enviado por WhatsApp.` : `Pedido de ${p.nome} recusado.`);
        desenhar(); montarMenu('acessos');
      });
    }
    desenhar();
  }
  function coordEquipe() {
    const l = equipe();
    vista.innerHTML = cab('Coordenação · ' + esc(titulo(uni.n)), 'Equipe e casos', 'Quem atende cada caso. Quando um agente sai ou entra de férias, os casos são transferidos sem perder o histórico.') + rls() +
      `<div class="bloco"><h2>Agentes da unidade</h2><p class="sub">Nomes fictícios. Os casos são os da unidade no app (simulado).</p><div class="lista-p" id="eq"></div>
       <div class="transf"><label>De<select id="de"></select></label><label>Para<select id="para"></select></label><label>Casos<input id="qtd" type="number" min="1" value="1" style="width:80px"></label>
       <button class="bt pri" id="transferir" type="button">${ic('troca')}Transferir</button></div></div>`;
    function desenhar() {
      const mx = Math.max(...l.map(a => a.casos), 1);
      $('eq').innerHTML = l.map((a, i) => `<div class="lp"><span class="av" style="background:${['var(--azul)', 'var(--verde-esc)', 'var(--laranja)', '#8A6200', '#5B3FD1'][i % 5]}">${a.nome[0]}</span>
        <div class="info"><b>${esc(a.nome)}</b><span>${esc(a.f)}</span></div><div style="flex:1;min-width:140px" class="hbar"><span>${a.casos} caso${a.casos === 1 ? '' : 's'}</span><div class="t"><i style="width:${a.casos / mx * 100}%"></i></div><span></span></div></div>`).join('');
      const op = l.map((a, i) => `<option value="${i}">${esc(a.nome)}</option>`).join('');
      $('de').innerHTML = op; $('para').innerHTML = op; $('para').value = Math.min(1, l.length - 1);
    }
    desenhar();
    $('transferir').onclick = () => {
      const de = +$('de').value, para = +$('para').value, n = Math.max(1, +$('qtd').value || 1);
      if (de === para) { toast('Escolha agentes diferentes.'); return; }
      const m = Math.min(n, l[de].casos);
      if (!m) { toast(l[de].nome + ' não tem casos para transferir.'); return; }
      l[de].casos -= m; l[para].casos += m; guardar('estado', EST);
      toast(`${m} caso${m > 1 ? 's' : ''} transferido${m > 1 ? 's' : ''} de ${l[de].nome} para ${l[para].nome}, com o histórico`); desenhar();
    };
  }

  /* =====================================================================
     AGENTE
     ===================================================================== */
  const TELAS = [['login', 'Login do agente'], ['casos', 'Meus casos'], ['formulario', 'Novo atendimento'], ['plano', 'Plano de direitos'], ['encaminhamento', 'Encaminhamento'], ['dona-cida', 'Acompanhamento do caso'], ['anotacao-ia', 'Anotação por voz com IA'], ['equipe', 'Equipe do coordenador']];
  function agHoje() {
    const vis = [['09:00', 'Família Souza', 'Jardim Ângela · 1ª visita', 'Novo atendimento', 'az'], ['10:30', 'Sr. Antônio', 'Atualizar CadÚnico vencido', 'Precisa atualizar', 'am'],
      ['14:00', 'Dona Cida', 'Conferir se foi ao Poupatempo (18/11)', 'Lembrete enviado', 'vd'], ['15:30', 'Família Lima', 'Setor de risco R3 · prioridade', 'Área de risco', 'vm']];
    vista.innerHTML = cab('Agente de campo · ' + esc(titulo(CD.unidades['410'].n)), 'Visitas de hoje', 'O que o agente vê no celular. Os nomes são fictícios.') +
      `<div class="agente-grid"><div>
        <div class="kpis" style="grid-template-columns:repeat(3,1fr)">${kpi(4, 'Visitas hoje', 'calendario', 'var(--azul)', 'Demonstração')}${kpi(13, 'Casos da unidade', 'lista', 'var(--verde-esc)', 'Simulado')}${kpi(2, 'Lembretes enviados', 'msg', 'var(--laranja)', 'Demonstração')}</div>
        ${vis.map(v => `<div class="visita"><span class="hora">${v[0]}</span><div class="info"><b>${v[1]}</b><span>${v[2]}</span></div><span class="chip ${v[4]}">${v[3]}</span></div>`).join('')}
        <div class="acao" style="margin-top:14px">${ic('sino')}<div><b>Campanha no seu território</b>Busca ativa do Bolsa Família no Jardim Ângela: cobertura de 36,9% contra 41,7% esperada.</div></div>
      </div>
      <div><div class="celular"><img id="cel-img" src="../assets/telas/${TELAS[0][0]}.png" alt="${TELAS[0][1]}"></div>
        <div class="cel-ctrl"><button type="button" id="ant" aria-label="Tela anterior">‹</button><span id="cel-leg">${TELAS[0][1]}</span><button type="button" id="prox" aria-label="Próxima tela">›</button></div></div></div>`;
    let i = 0; const img = $('cel-img');
    const ir = n => { i = (n + TELAS.length) % TELAS.length; img.style.opacity = 0; setTimeout(() => { img.src = `../assets/telas/${TELAS[i][0]}.png`; img.alt = TELAS[i][1]; $('cel-leg').textContent = TELAS[i][1]; img.style.opacity = 1; }, 180); };
    $('ant').onclick = () => ir(i - 1); $('prox').onclick = () => ir(i + 1);
  }
  function agTelas() {
    vista.innerHTML = cab('Agente de campo', 'Telas do app', 'Protótipo de ideação feito no Figma.') +
      `<div class="telas-g">${TELAS.map(([f, t]) => `<figure><img src="../assets/telas/${f}.png" alt="${t}" loading="lazy"><figcaption>${t}</figcaption></figure>`).join('')}</div>`;
  }
  function agIA() {
    vista.innerHTML = cab('Agente de campo', 'IA em ação', 'As funções de IA já funcionam em Python. Os vídeos mostram o resultado real.') +
      `<div class="videos-g">
        <div class="video-item"><video controls preload="none" poster="../assets/videos/anotacao_app.jpg"><source src="../assets/videos/anotacao_app.mp4" type="video/mp4"></video><div><h3>Anotação por voz com IA · 29 s</h3><p>Transcreve, remove o dado de saúde e sugere marcações que o agente confirma.</p></div></div>
        <div class="video-item"><video controls preload="none" poster="../assets/videos/lembrete_whatsapp.jpg"><source src="../assets/videos/lembrete_whatsapp.mp4" type="video/mp4"></video><div><h3>Lembrete por WhatsApp · 36 s</h3><p>Chegando em um celular de verdade, em texto e em mensagem de voz.</p></div></div>
      </div>`;
  }

  /* ---------- roteamento por #hash ---------- */
  const VISTAS = {
    sec: { visao: secVisao, ranking: secRanking, campanhas: vistaCampanhas, subprefeituras: secSubs, insights: secInsights, painel: vistaPainel },
    sub: { visao: subVisao, campanhas: vistaCampanhas, alertas: subAlertas, unidades: subUnidades, painel: vistaPainel },
    coord: { visao: coordVisao, acessos: coordAcessos, equipe: coordEquipe, campanhas: vistaCampanhas, painel: vistaPainel },
    agente: { hoje: agHoje, telas: agTelas, ia: agIA }
  }[perfil];
  function rota() {
    let v = location.hash.slice(1);
    if (!VISTAS[v]) v = P.menu[0][0];
    montarMenu(v);
    const item = P.menu.find(m => m[0] === v);
    $('trilha').innerHTML = `${esc(P.nome)} / <b>${esc(item[1])}</b>`;
    VISTAS[v]();
    observar(vista);
    vista.focus({ preventScroll: true });
    if (!VISTA_DIST) scrollTo(0, 0);
  }
  addEventListener('hashchange', rota);
  rota();
})();
