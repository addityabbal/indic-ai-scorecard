// Indic AI Scorecard leaderboard. Reads data/latest.json (+ explorer). No framework, no build step.

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const pct = (v) => (v == null ? "—" : `${Math.round(v * 100)}`);
const usd = (v) => (v == null ? "n/a" : v < 0.1 ? `$${v.toFixed(3)}` : `$${v.toFixed(2)}`);

const state = { data: null, explorer: null, sort: { key: "score", asc: false }, lang: "", task: "" };

async function load() {
  try {
    state.data = await (await fetch("data/latest.json", { cache: "no-cache" })).json();
  } catch {
    $("#headline").textContent = "Results could not be loaded.";
    return;
  }
  const d = state.data;
  $("#headline").textContent = d.headline;
  const ranked = d.models.filter((m) => !m.is_judge).length;
  $("#sub").textContent = `${ranked} models, ${d.cases.public} test cases, run ${d.month}. Scores are 0–100; cost is what 1,000 answers would cost on each model's paid plan.`;
  if (d.cases.reviewed < d.cases.public || d.cases.public < 300) {
    $("#pilot").hidden = false;
    $("#pilot").textContent = `Pilot: ${d.cases.public} of the planned 300 cases, ${Object.values(d.languages).join(", ")} only, ${d.cases.reviewed} reviewed by a native speaker so far, and the AI judge is ${d.calibration.status}. With this few cases, read the ranges, not the ranks.`;
  }
  for (const [k, v] of Object.entries(d.languages)) $("#f-lang").insertAdjacentHTML("beforeend", `<option value="${esc(k)}">${esc(v)}</option>`);
  for (const t of d.cases.tasks) $("#f-task").insertAdjacentHTML("beforeend", `<option value="${esc(t)}">${esc(d.tasks[t] || t)}</option>`);
  renderChart();
  renderTable();
  renderGallery();
  renderMethod();
  try {
    state.explorer = await (await fetch("data/explorer.json", { cache: "no-cache" })).json();
    renderExplorerPicker();
  } catch { $("#case-body").textContent = "Answers could not be loaded."; }
}

// ---------------------------------------------------------------- chart

function renderChart() {
  const models = state.data.models.filter((m) => m.score != null && m.usd_per_1000 != null);
  const svg = $("#chart");
  const W = 760, H = 380, L = 56, R = 150, T = 20, B = 46;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  if (!models.length) { svg.innerHTML = `<text x="20" y="40">No priced results yet.</text>`; return; }
  const costs = models.map((m) => m.usd_per_1000);
  const lo = Math.log10(Math.min(...costs) / 1.6), hi = Math.log10(Math.max(...costs) * 1.6);
  const x = (c) => L + ((Math.log10(c) - lo) / (hi - lo)) * (W - L - R);
  const y = (s) => T + (1 - s) * (H - T - B);
  let out = "";
  for (let s = 0; s <= 1.0001; s += 0.25) out += `<line class="grid" x1="${L}" x2="${W - R}" y1="${y(s)}" y2="${y(s)}"/><text x="${L - 8}" y="${y(s) + 4}" text-anchor="end">${Math.round(s * 100)}</text>`;
  for (let e = Math.ceil(lo); e <= Math.floor(hi); e++) {
    for (const k of [1, 2, 5]) {
      const v = k * 10 ** e;
      if (Math.log10(v) < lo || Math.log10(v) > hi) continue;
      out += `<line class="grid" x1="${x(v)}" x2="${x(v)}" y1="${T}" y2="${H - B}"/><text x="${x(v)}" y="${H - B + 16}" text-anchor="middle">$${v >= 1 ? v : v.toPrecision(1)}</text>`;
    }
  }
  out += `<text x="${(L + W - R) / 2}" y="${H - 6}" text-anchor="middle">US$ per 1,000 answers (log scale) →</text>`;
  out += `<text x="14" y="${(T + H - B) / 2}" transform="rotate(-90 14 ${(T + H - B) / 2})" text-anchor="middle">Quality score →</text>`;
  const placed = [];
  for (const m of models) {
    const cx = x(m.usd_per_1000), cy = y(m.score);
    if (m.range) out += `<line class="bar" x1="${cx}" x2="${cx}" y1="${y(m.range[1])}" y2="${y(m.range[0])}"/>`;
    out += `<circle class="dot${m.is_judge ? " judge" : ""}" cx="${cx}" cy="${cy}" r="6"><title>${esc(m.id)}: ${pct(m.score)}, ${usd(m.usd_per_1000)}/1k</title></circle>`;
    let ly = cy + 4;
    while (placed.some((p) => Math.abs(p - ly) < 13)) ly += 13;
    placed.push(ly);
    out += `<text class="label" x="${cx + 10}" y="${ly}">${esc(m.id)}${m.is_judge ? " (judge)" : ""}</text>`;
  }
  svg.innerHTML = out;
}

// ---------------------------------------------------------------- table

function scoreFor(m) {
  const d = state.data;
  if (state.task) return m.by_task[state.task] ?? null;
  if (state.lang) return m.by_lang[state.lang] ?? null;
  return m.score;
}

function columns() {
  const d = state.data;
  return [
    { key: "rank", label: "#", num: true, get: (m) => m.rank ?? null, show: (m) => m.rank ?? "—" },
    { key: "id", label: "Model", get: (m) => m.id, show: (m) => `${esc(m.id)}${m.is_judge ? '<span class="tag">judge, not ranked</span>' : ""}<div class="range">${esc(m.maker || "")}</div>` },
    { key: "score", label: state.task ? d.tasks[state.task] : state.lang ? d.languages[state.lang] : "Overall", num: true, get: scoreFor,
      show: (m) => { const s = scoreFor(m); return s == null ? "—" : `${pct(s)}<span class="cell-bar" style="width:${Math.round(s * 50)}px"></span>${!state.task && !state.lang && m.range ? `<div class="range">${pct(m.range[0])}–${pct(m.range[1])}</div>` : ""}`; } },
    ...Object.entries(d.languages).map(([k, v]) => ({ key: `lang:${k}`, label: v, num: true, get: (m) => m.by_lang[k] ?? null, show: (m) => pct(m.by_lang[k]) })),
    { key: "script_match", label: "Same script", num: true, get: (m) => m.script_match, show: (m) => (m.script_match == null ? "—" : `${pct(m.script_match)}%`) },
    { key: "usd_per_1000", label: "$ / 1k answers", num: true, get: (m) => m.usd_per_1000, show: (m) => usd(m.usd_per_1000) },
    { key: "median_seconds", label: "Median s", num: true, get: (m) => m.median_seconds, show: (m) => (m.median_seconds ?? "—") },
  ];
}

function renderTable() {
  const cols = columns();
  $("#table thead tr").innerHTML = cols.map((c) => `<th data-key="${c.key}" class="${c.num ? "num" : ""}" aria-sort="${state.sort.key === c.key ? (state.sort.asc ? "ascending" : "descending") : "none"}">${esc(c.label)}</th>`).join("");
  const col = cols.find((c) => c.key === state.sort.key) || cols[2];
  const rows = [...state.data.models].sort((a, b) => {
    const va = col.get(a), vb = col.get(b);
    if (va == null) return 1;
    if (vb == null) return -1;
    return (va < vb ? -1 : va > vb ? 1 : 0) * (state.sort.asc ? 1 : -1);
  });
  $("#table tbody").innerHTML = rows.map((m) => `<tr>${cols.map((c) => `<td class="${c.num ? "num" : ""}">${c.show(m)}</td>`).join("")}</tr>`).join("");
  const pending = state.data.models.reduce((n, m) => n + (m.pending_judge || 0), 0);
  $("#table-note").textContent = `Scores 0–100. Each task counts equally. "Same script" = share of free-text replies written in the user's script. Speed is measured on free tiers.${pending ? ` ${pending} answers are still waiting for the judge and are left out for now.` : ""}`;
}

// ---------------------------------------------------------------- gallery

function renderGallery() {
  const items = state.data.failures;
  $("#gallery").innerHTML = items.length ? items.map((f) => `
    <article class="fail">
      <h3>${esc(f.what)}</h3>
      <div class="who">${esc(f.model_id)} · ${esc(state.data.tasks[f.task] || f.task)} · ${esc(f.detail)}</div>
      <div class="bubble user">${esc(f.input)}</div>
      <div class="bubble model">${esc(f.answer)}</div>
    </article>`).join("") : '<p class="muted">No failures caught yet.</p>';
}

// ---------------------------------------------------------------- explorer

function renderExplorerPicker() {
  const ids = Object.keys(state.explorer).sort();
  $("#case").innerHTML = ids.map((id) => `<option value="${esc(id)}">${esc(id)}</option>`).join("");
  $("#case").addEventListener("change", renderCase);
  renderCase();
}

function renderCase() {
  const id = $("#case").value;
  const answers = state.explorer[id] || {};
  const sample = Object.values(answers)[0];
  $("#case-body").innerHTML = `<strong>${esc(id)}</strong>`;
  fetchCase(id).then((c) => {
    if (!c) return;
    $("#case-body").innerHTML = `<strong>${esc(state.data.tasks[c.task] || c.task)}</strong> · ${esc(state.data.languages[c.lang] || c.lang)}\n${c.context ? `<span class="muted">Passage:</span> ${esc(c.context)}\n` : ""}<span class="muted">User:</span> ${esc(c.input)}${c.instruction ? `\n<span class="muted">Instruction:</span> ${esc(c.instruction)}` : ""}`;
  });
  const order = state.data.models.map((m) => m.id).filter((m) => answers[m]);
  $("#answers").innerHTML = order.map((mid) => {
    const a = answers[mid];
    const checks = Object.entries(a.checks).map(([k, v]) => v.pass == null ? `<span class="check">${esc(k)} ${v.score ?? ""}</span>` : `<span class="check ${v.pass ? "pass" : "fail"}" title="${esc(v.detail)}">${v.pass ? "✓" : "✗"} ${esc(k)}</span>`).join("");
    const j = a.judge ? `<span class="check">judge ${a.judge.grade.helpful}/${a.judge.grade.correct}/${a.judge.grade.natural}</span>` : "";
    return `<article class="answer"><h3><span>${esc(mid)}</span><span>${a.score == null ? "—" : pct(a.score)}</span></h3>
      <div class="text">${esc(a.text ?? a.error ?? "")}</div>
      <div class="checks">${checks}${j}</div>
      ${a.judge?.grade?.reason ? `<div class="reason">Judge: ${esc(a.judge.grade.reason)}</div>` : ""}</article>`;
  }).join("");
}

let casesCache = null;
async function fetchCase(id) {
  if (!casesCache) {
    try {
      const text = await (await fetch("data/cases.jsonl")).text();
      casesCache = Object.fromEntries(text.split("\n").filter(Boolean).map((l) => { const c = JSON.parse(l); return [c.id, c]; }));
    } catch { casesCache = {}; }
  }
  return casesCache[id];
}

// ---------------------------------------------------------------- method

function renderMethod() {
  const d = state.data;
  const cal = d.calibration;
  const calText = cal.status === "calibrated"
    ? Object.entries(cal.by_lang).map(([l, v]) => `${d.languages[l] || l}: judge within 1 point of people ${Math.round(v.within_1 * 100)}% of the time${v.low_confidence ? " (low confidence)" : ""}`).join("; ")
    : `${cal.note || "Not calibrated yet."}`;
  const judge = d.judge ? `${d.judge.id} (${d.judge.model}, ${d.judge.maker}). It grades blind and in random order, at temperature 0, and is never ranked, because AI judges favour their own answers.` : "None";
  const last = d.runs[d.runs.length - 1];
  $("#method-body").innerHTML = `<dl>
    <dt>Test set</dt><dd>${d.cases.public} public cases (${Object.entries(d.cases.by_lang).map(([l, n]) => `${d.languages[l] || l} ${n}`).join(", ")}), ${d.cases.reviewed} reviewed by a native speaker. Real tasks: support replies, scheme questions from a passage, pulling data from a message, intent, plain-language rewrites, and saying "I don't know".</dd>
    <dt>Scoring</dt><dd>Code checks first (JSON fields, labels, key facts, no invented numbers, a don't-know phrase, same script as the user). An AI judge scores open answers 1–5 on helpful, correct and natural. Each case scores 0–1; each task counts equally; ranges are 95% bootstrap intervals (1,000 resamples).</dd>
    <dt>Judge</dt><dd>${esc(judge)}</dd>
    <dt>Judge vs people</dt><dd>${esc(calText)}</dd>
    <dt>Same prompt</dt><dd>Every model gets the same system prompt: reply in the user's language and script, say you don't know if the passage doesn't say, return only JSON when asked. Temperature 0.</dd>
    <dt>Cost</dt><dd>What 1,000 answers would cost on each model's paid plan. Workers AI is measured from the neurons each call used ($0.011 per 1,000 neurons); others from list prices per token (checked ${esc(d.prices_checked)}). The runs themselves use free tiers and cost ₹0.</dd>
    <dt>Limits</dt><dd>Small samples: overlapping ranges are ties. Speed is measured on free tiers. Hidden held-out cases (to catch training on the public set) start with the full 300-case set.</dd>
    <dt>Last run</dt><dd>${last ? `${esc(last.at)}: ${last.called} new answers, ${last.cached} reused from cache, ${Math.round(last.neurons)} Workers AI neurons${last.stopped ? `, stopped: ${esc(last.stopped)}` : ""}` : "—"}</dd>
    <dt>Method doc</dt><dd><a href="https://github.com/addityabbal/indic-ai-scorecard/blob/main/docs/METHOD.md">docs/METHOD.md</a></dd>
  </dl>`;
}

// ---------------------------------------------------------------- wiring

$("#table thead").addEventListener("click", (e) => {
  const key = e.target.closest("th")?.dataset.key;
  if (!key) return;
  state.sort = state.sort.key === key ? { key, asc: !state.sort.asc } : { key, asc: key === "rank" || key === "id" || key === "usd_per_1000" || key === "median_seconds" };
  renderTable();
});
$("#f-lang").addEventListener("change", (e) => { state.lang = e.target.value; state.sort = { key: "score", asc: false }; renderTable(); });
$("#f-task").addEventListener("change", (e) => { state.task = e.target.value; state.sort = { key: "score", asc: false }; renderTable(); });
load();
