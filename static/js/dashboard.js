/* Dashboard Q-Learning — Clássico × Quântico (JS puro, sem dependências) */
(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const NS = "http://www.w3.org/2000/svg";
  const ACOES = ["↑", "→", "↓", "←"];
  const BASE = ["|00⟩", "|01⟩", "|10⟩", "|11⟩"];
  const COR = { classico: "#2a78d6", quantico: "#6250d6" };
  const tooltip = $("#tooltip");
  const dados = {};

  const fmt = (v, d = 2) => (v === null || v === undefined ? "—" : Number(v).toLocaleString("pt-BR", { maximumFractionDigits: d }));

  // ------------------------------------------------------------------ abas
  $$(".aba").forEach((b) => b.addEventListener("click", () => {
    $$(".aba").forEach((x) => { x.classList.toggle("ativa", x === b); x.setAttribute("aria-selected", x === b); });
    $$(".painel").forEach((p) => p.classList.toggle("visivel", p.id === "painel-" + b.dataset.alvo));
    const modo = b.dataset.alvo;
    if (dados[modo]) desenharGraficos(modo); // redimensiona ao trocar de aba
  }));

  // ------------------------------------------------------------------ tooltip
  function mostrarTip(html, x, y) {
    tooltip.innerHTML = html; tooltip.style.opacity = 1;
    const w = tooltip.offsetWidth;
    tooltip.style.left = Math.min(x + 14, innerWidth - w - 8) + "px";
    tooltip.style.top = y + 14 + "px";
  }
  const esconderTip = () => { tooltip.style.opacity = 0; };

  // ------------------------------------------------------------------ gráfico de linhas (SVG)
  function el(tag, attrs = {}, pai) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (pai) pai.appendChild(e);
    return e;
  }

  function graficoLinhas(container, series, opcoes = {}) {
    container.innerHTML = "";
    const W = container.clientWidth || 400, Hh = (container.clientHeight || 250) - 24;
    const m = { t: 10, r: 14, b: 26, l: 44 };
    const svg = el("svg", { viewBox: `0 0 ${W} ${Hh}`, role: "img", "aria-label": opcoes.titulo || "gráfico" }, container);
    const n = series[0].valores.length;
    const todos = series.flatMap((s) => s.valores);
    let min = Math.min(...todos), max = Math.max(...todos);
    if (opcoes.zero) min = Math.min(0, min);
    if (min === max) { max += 1; min -= 1; }
    const pad = (max - min) * 0.05; min -= pad; max += pad;
    const x = (i) => m.l + (i / Math.max(1, n - 1)) * (W - m.l - m.r);
    const y = (v) => m.t + (1 - (v - min) / (max - min)) * (Hh - m.t - m.b);

    // grade + eixos (recessivos)
    const g = el("g", { class: "grade" }, svg), ex = el("g", { class: "eixo" }, svg);
    for (let k = 0; k <= 4; k++) {
      const v = min + (k / 4) * (max - min), yy = y(v);
      el("line", { x1: m.l, x2: W - m.r, y1: yy, y2: yy }, g);
      el("text", { x: m.l - 6, y: yy + 4, "text-anchor": "end" }, ex).textContent = fmt(v, Math.abs(max - min) < 5 ? 2 : 0);
    }
    for (let k = 0; k <= 4; k++) {
      const i = Math.round((k / 4) * (n - 1));
      el("text", { x: x(i), y: Hh - 6, "text-anchor": "middle" }, ex).textContent = i + 1;
    }
    if (min < 0 && max > 0) el("line", { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: "base" }, svg);

    series.forEach((s) => {
      const d = s.valores.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
      el("path", { d, fill: "none", stroke: s.cor, "stroke-width": s.largura || 2, "stroke-opacity": s.opacidade ?? 1,
        "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    });

    // camada de hover: crosshair + marcadores + tooltip
    const cross = el("line", { y1: m.t, y2: Hh - m.b, stroke: "#7a7974", "stroke-dasharray": "3 3", opacity: 0 }, svg);
    const pontos = series.map((s) => el("circle", { r: 4, fill: s.cor, stroke: "#fcfcfb", "stroke-width": 2, opacity: 0 }, svg));
    const hit = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: Hh - m.t - m.b, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", (ev) => {
      const r = svg.getBoundingClientRect();
      const px = ((ev.clientX - r.left) / r.width) * W;
      const i = Math.max(0, Math.min(n - 1, Math.round(((px - m.l) / (W - m.l - m.r)) * (n - 1))));
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.setAttribute("opacity", 1);
      series.forEach((s, j) => { pontos[j].setAttribute("cx", x(i)); pontos[j].setAttribute("cy", y(s.valores[i])); pontos[j].setAttribute("opacity", 1); });
      mostrarTip(`<b>Episódio ${i + 1}</b><br>` + series.map((s) => `${s.nome}: ${fmt(s.valores[i])}`).join("<br>"), ev.clientX, ev.clientY);
    });
    hit.addEventListener("mouseleave", () => { cross.setAttribute("opacity", 0); pontos.forEach((p) => p.setAttribute("opacity", 0)); esconderTip(); });

    if (series.length > 1) {
      const leg = document.createElement("div");
      leg.className = "legenda";
      leg.innerHTML = series.map((s) => `<span><i style="background:${s.cor};opacity:${s.opacidade ?? 1}"></i>${s.nome}</span>`).join("");
      container.appendChild(leg);
    }
  }

  function desenharGraficos(modo) {
    const r = dados[modo], cor = COR[modo];
    graficoLinhas($(`#g-recompensa-${modo}`), [
      { nome: "Recompensa", valores: r.recompensas, cor, opacidade: 0.28, largura: 1.5 },
      { nome: "Média móvel (20)", valores: r.recompensas_media, cor },
    ], { titulo: "Recompensa por episódio" });
    graficoLinhas($(`#g-passos-${modo}`), [
      { nome: "Passos", valores: r.passos, cor, opacidade: 0.28, largura: 1.5 },
      { nome: "Média móvel (20)", valores: r.passos_media, cor },
    ], { titulo: "Passos por episódio", zero: true });
    graficoLinhas($(`#g-exploracao-${modo}`), [
      { nome: modo === "classico" ? "ε" : "Entropia (bits)", valores: r.exploracao, cor },
    ], { titulo: "Exploração", zero: true });
  }

  // ------------------------------------------------------------------ KPIs
  function kpis(modo) {
    const r = dados[modo], mt = r.metricas, av = r.avaliacao;
    const res = { objetivo: "✅ chegou ao objetivo", armadilha: "❌ caiu na armadilha", limite: "⏱️ esgotou os passos" }[av.resultado];
    const itens = [
      ["Taxa de sucesso (últimos 10%)", fmt(mt.taxa_sucesso_final, 1) + "%", "episódios que chegaram ao objetivo"],
      ["Recompensa média final", fmt(mt.recompensa_media_final), "últimos 10% dos episódios"],
      ["Passos médios final", fmt(mt.passos_medios_final, 1), "rota ótima = 10 passos"],
      ["1º sucesso", mt.primeiro_sucesso ? "ep. " + mt.primeiro_sucesso : "—", "primeira vez no objetivo"],
      ["Política final", av.passos + " passos", res],
      modo === "quantico"
        ? ["Medições quânticas", fmt(mt.medicoes, 0), `treino em ${fmt(mt.tempo_ms, 0)} ms`]
        : ["Tempo de treino", fmt(mt.tempo_ms, 0) + " ms", "Python + NumPy"],
    ];
    $(`#kpis-${modo}`).innerHTML = itens.map(([a, b, c]) =>
      `<div class="kpi"><div class="rotulo">${a}</div><div class="valor">${b}</div><div class="sub">${c}</div></div>`).join("");
  }

  // ------------------------------------------------------------------ mundo (grid)
  function misturar(hex, t) { // branco → cor (rampa sequencial de um só matiz)
    const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
    const w = [252, 252, 251];
    return `rgb(${c.map((v, i) => Math.round(w[i] + (v - w[i]) * t)).join(",")})`;
  }

  function mundo(modo) {
    const r = dados[modo], amb = r.ambiente, cont = $(`#mundo-${modo}`);
    cont.style.gridTemplateColumns = `repeat(${amb.colunas}, 1fr)`;
    const livres = r.valor.filter((_, s) => amb.celulas[Math.floor(s / amb.colunas)][s % amb.colunas] === "livre" || amb.celulas[Math.floor(s / amb.colunas)][s % amb.colunas] === "inicio");
    const vmin = Math.min(...livres), vmax = Math.max(...livres);
    const noCaminho = new Set(r.avaliacao.caminho.map(([i, j]) => i * amb.colunas + j));
    cont.innerHTML = "";
    for (let i = 0; i < amb.linhas; i++) for (let j = 0; j < amb.colunas; j++) {
      const s = i * amb.colunas + j, tipo = amb.celulas[i][j];
      const c = document.createElement("div");
      c.className = `celula ${tipo}` + (noCaminho.has(s) ? " caminho" : "");
      c.dataset.s = s;
      if (tipo === "parede") { cont.appendChild(c); continue; }
      if (tipo === "objetivo") c.innerHTML = "🏁";
      else if (tipo === "armadilha") c.innerHTML = "☠";
      else {
        const t = 0.08 + 0.82 * ((r.valor[s] - vmin) / (vmax - vmin || 1));
        c.style.background = misturar(COR[modo], t);
        c.style.color = t > 0.55 ? "#fff" : "#0b0b0b";
        c.innerHTML = `${r.politica_simbolos[s]}<small>${fmt(r.valor[s], 1)}</small>`;
      }
      c.addEventListener("mouseenter", (ev) => mostrarTip(`(${i},${j}) · ${tipo} · V=${fmt(r.valor[s])}`, ev.clientX, ev.clientY));
      c.addEventListener("mouseleave", esconderTip);
      c.addEventListener("click", () => {
        $$(".celula", cont).forEach((x) => x.classList.remove("selecionada"));
        c.classList.add("selecionada");
        detalhe(modo, s, i, j, tipo);
      });
      cont.appendChild(c);
    }
    const ini = cont.querySelector('.celula[data-s="0"]');
    if (ini) ini.style.boxShadow = "inset 0 0 0 2px #eb6834";
  }

  function detalhe(modo, s, i, j, tipo) {
    const r = dados[modo], box = $(`#detalhe-${modo}`);
    if (tipo === "objetivo" || tipo === "armadilha") {
      box.innerHTML = `<p>Célula (${i},${j}) é <strong>${tipo}</strong> — estado terminal, o episódio acaba aqui.</p>`;
      return;
    }
    let linhas, cab;
    if (modo === "classico") {
      const q = r.q_table[s], mx = Math.max(...q), mn = Math.min(...q, 0);
      cab = `<p>Estado ${s} · célula (${i},${j}) · V(s) = max Q = <b>${fmt(r.valor[s])}</b></p>`;
      linhas = q.map((v, a) => {
        const w = ((v - mn) / (mx - mn || 1)) * 100;
        return `<div class="barra"><span>${ACOES[a]} Q(s,${a})</span><div class="trilho"><div class="enchimento" style="width:${w}%"></div></div><span class="valor-num">${fmt(v)}</span></div>`;
      });
    } else {
      const p = r.probabilidades[s], amp = r.amplitudes[s];
      const ket = amp.map((c, a) => `${fmt(c, 3)}${BASE[a]}`).join(" + ");
      cab = `<p>Estado ${s} · célula (${i},${j}) · V(s) = <b>${fmt(r.valor[s])}</b></p><p class="nota">|ψ⟩ = ${ket}</p>`;
      linhas = p.map((v, a) => `<div class="barra"><span>${BASE[a]} ${ACOES[a]}</span><div class="trilho"><div class="enchimento" style="width:${v * 100}%"></div></div><span class="valor-num">${fmt(v * 100, 1)}%</span></div>`);
    }
    box.innerHTML = cab + linhas.join("");
  }

  function tabela(modo) {
    const r = dados[modo], amb = r.ambiente;
    const M = modo === "classico" ? r.q_table : r.probabilidades;
    let h = `<thead><tr><th>Estado (lin,col)</th>${ACOES.map((a, k) => `<th>${modo === "quantico" ? BASE[k] + " " : ""}${a}</th>`).join("")}</tr></thead><tbody>`;
    M.forEach((linha, s) => {
      const i = Math.floor(s / amb.colunas), j = s % amb.colunas, tipo = amb.celulas[i][j];
      if (tipo === "parede") return;
      const mx = Math.max(...linha);
      h += `<tr><td>${s} (${i},${j})${tipo !== "livre" ? " · " + tipo : ""}</td>` +
        linha.map((v) => `<td class="${v === mx && tipo !== "objetivo" && tipo !== "armadilha" ? "melhor" : ""}">${modo === "classico" ? fmt(v) : fmt(v * 100, 1) + "%"}</td>`).join("") + "</tr>";
    });
    $(`#tabela-${modo}`).innerHTML = h + "</tbody>";
  }

  // ------------------------------------------------------------------ treino
  async function treinar(form) {
    const modo = form.dataset.modo, btn = $("button", form), st = $(".status", form);
    const corpo = Object.fromEntries(new FormData(form).entries());
    btn.disabled = true; st.textContent = "Treinando…";
    try {
      const resp = await fetch(`/api/${modo}/treinar`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      dados[modo] = await resp.json();
      kpis(modo); desenharGraficos(modo); mundo(modo); tabela(modo);
      $(`#t-exploracao-${modo}`).textContent = modo === "classico" ? "Exploração: ε por episódio" : "Exploração: entropia média da medição";
      $(`#detalhe-${modo}`).innerHTML = '<p class="nota">Clique em uma célula do mundo para ver os detalhes.</p>';
      st.textContent = `Concluído: ${corpo.episodios} episódios.`;
    } catch (e) {
      st.textContent = "Erro ao treinar: " + e.message;
    } finally { btn.disabled = false; }
  }
  $$("form.parametros").forEach((f) => f.addEventListener("submit", (e) => { e.preventDefault(); treinar(f); }));

  // ------------------------------------------------------------------ laboratório Grover
  async function grover() {
    const marcado = $("#grover-marcado").value;
    const r = await (await fetch(`/api/quantico/grover?marcado=${marcado}`)).json();
    $("#grover-etapas").innerHTML = r.etapas.map((e) => `
      <div class="etapa"><h4>${e.nome}</h4>
        <div class="barras">${e.probabilidades.map((p, k) => `<div class="col ${k === r.marcado ? "marcado" : ""}" title="${r.rotulos[k]}: ${fmt(p * 100, 1)}%"><span>${fmt(p * 100, 0)}%</span><div style="height:${p * 85}%"></div></div>`).join("")}</div>
        <div class="rotulos">${r.rotulos.map((l, k) => `<span>${l} ${r.acoes[k]}</span>`).join("")}</div>
        <div class="amp">amplitudes: [${e.amplitudes.map((a) => fmt(a, 2)).join(", ")}]</div>
      </div>`).join("");
  }
  $("#grover-marcado").addEventListener("change", grover);

  let timer;
  addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(() => Object.keys(dados).forEach((m) => { if ($("#painel-" + m).classList.contains("visivel")) desenharGraficos(m); }), 150); });

  // treina os dois agentes ao abrir
  $$("form.parametros").forEach((f) => treinar(f));
  grover();
})();
