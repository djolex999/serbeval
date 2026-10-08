"""Single-file HTML front end for the gold-verification worksheet.

The page is a nicer way to fill the same sheet, not a second format: its download is the
text sheet `serbeval verify --apply` already reads, and a test runs the page's own
serializer through the Python parser to keep the two in step. Everything is inline (no
network, no build step); marks autosave in the browser's localStorage.
"""

import json
from collections.abc import Sequence
from html import escape

from serbeval.schema import ANSWER_LETTERS, BLANK, ClozeItem, EvalItem

Item = EvalItem | ClozeItem


def _payload(item: Item) -> dict[str, object]:
    if isinstance(item, ClozeItem):
        return {
            "id": item.id, "task": item.task, "category": item.category, "kind": "cloze",
            "question": item.question, "cue": item.cue, "gold": list(item.answers),
            "filled": item.question.replace(BLANK, item.answers[0], 1),
            "explanation": item.explanation,
        }
    return {
        "id": item.id, "task": item.task, "category": item.category, "kind": "mcq",
        "question": item.question, "choices": list(item.choices),
        "gold": [ANSWER_LETTERS[item.answer_index]], "explanation": item.explanation,
    }


def build_verification_html(items: Sequence[Item], *, title: str) -> str:
    data = json.dumps([_payload(item) for item in items], ensure_ascii=False)
    # Inside <script>, "</" could close the block early; JSON allows "<" for "<".
    data = data.replace("<", "\\u003c")
    return _TEMPLATE.replace("__TITLE__", escape(title)).replace("__ITEMS__", data)


_TEMPLATE = r"""<!doctype html>
<html lang="sr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root {
  --bg: #f6f5f1; --panel: #ffffff; --ink: #1d1c1a; --muted: #6b6860; --line: #e3e0d8;
  --accent: #2f5d50; --accent-ink: #ffffff; --gold-bg: #eaf3ee; --gold-line: #9cc4b0;
  --ok: #2f7d4f; --fix: #b4542d; --add: #2d6fb4; --unsure: #a07a12; --drop: #8a2d3b;
  --blank: #fff3c4;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #161614; --panel: #1f1f1c; --ink: #ecebe6; --muted: #a29f95; --line: #34332e;
    --accent: #7fbfa6; --accent-ink: #10201a; --gold-bg: #1d2e26; --gold-line: #3f6b57;
    --ok: #6fcf97; --fix: #f0936a; --add: #7db4f0; --unsure: #e8c35a; --drop: #e58a9a;
    --blank: #4a3f12;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
header { position: sticky; top: 0; z-index: 2; background: var(--panel);
  border-bottom: 1px solid var(--line); padding: 12px 16px; }
.bar { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; max-width: 900px; margin: 0 auto; }
h1 { font-size: 16px; margin: 0; font-weight: 650; }
.progress { flex: 1 1 200px; height: 8px; background: var(--line); border-radius: 99px; overflow: hidden; }
.progress > div { height: 100%; background: var(--accent); width: 0; transition: width .2s; }
.counts { font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }
select, button, input { font: inherit; color: inherit; }
select, input[type=text] { background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; max-width: 100%; min-width: 0; }
button { cursor: pointer; border: 1px solid var(--line); background: var(--panel); border-radius: 8px; padding: 6px 12px; }
button:hover { border-color: var(--muted); }
button.primary { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
main { max-width: 900px; margin: 0 auto; padding: 16px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 20px; }
.meta { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; color: var(--muted); flex-wrap: wrap; }
.status { font-weight: 650; }
.sentence { font-size: 22px; line-height: 1.45; margin: 14px 0 6px; }
.sentence mark { background: var(--blank); color: inherit; border-radius: 4px; padding: 0 4px; }
.original { color: var(--muted); font-size: 14px; }
.cue { display: inline-block; border: 1px solid var(--line); border-radius: 99px; padding: 1px 10px; margin-left: 6px; }
.choices { list-style: none; padding: 0; margin: 12px 0; display: grid; gap: 6px; }
.choices li { border: 1px solid var(--line); border-radius: 10px; padding: 8px 12px; }
.choices li.gold { background: var(--gold-bg); border-color: var(--gold-line); font-weight: 600; }
.gold-box { background: var(--gold-bg); border: 1px solid var(--gold-line); border-radius: 10px; padding: 10px 14px; margin: 12px 0; }
.gold-box b { font-size: 18px; }
.explain { color: var(--muted); }
.actions { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; margin-top: 16px; }
.actions button { padding: 10px 6px; font-weight: 600; }
.actions kbd { display: block; font: 12px ui-monospace, monospace; color: var(--muted); font-weight: 400; }
.a-ok { color: var(--ok); } .a-fix { color: var(--fix); } .a-add { color: var(--add); }
.a-unsure { color: var(--unsure); } .a-drop { color: var(--drop); }
.actions button.on { outline: 2px solid currentColor; }
.editor { display: none; gap: 8px; margin-top: 12px; align-items: center; flex-wrap: wrap; }
.editor.open { display: flex; }
.editor input { flex: 1 1 240px; }
.letters button { min-width: 44px; }
.nav { display: flex; justify-content: space-between; gap: 8px; margin-top: 14px; }
.dots { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 18px; }
.dots button { width: 14px; height: 14px; padding: 0; border-radius: 4px; background: var(--line); border: 0; }
.dots button.cur { outline: 2px solid var(--ink); }
.dots .k-ok { background: var(--ok); } .dots .k-fix { background: var(--fix); } .dots .k-add { background: var(--add); }
.dots .k-unsure { background: var(--unsure); } .dots .k-drop { background: var(--drop); }
.help { font-size: 13px; color: var(--muted); margin-top: 14px; }
.toast { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%); background: var(--ink); color: var(--bg);
  padding: 8px 14px; border-radius: 8px; opacity: 0; transition: opacity .2s; pointer-events: none; }
.toast.show { opacity: 1; }
@media (max-width: 560px) {
  .actions { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .sentence { font-size: 19px; }
}
</style>
</head>
<body>
<header>
  <div class="bar">
    <h1>Provera tačnih odgovora</h1>
    <div class="progress" aria-hidden="true"><div id="progress"></div></div>
    <span class="counts" id="counts"></span>
  </div>
  <div class="bar" style="margin-top:8px">
    <select id="filter" aria-label="Kategorija"></select>
    <label class="counts"><input type="checkbox" id="onlyOpen"> samo neoznačeni</label>
    <span style="flex:1"></span>
    <button id="importBtn">Učitaj fajl</button>
    <button id="exportBtn" class="primary">Preuzmi za --apply</button>
    <input type="file" id="importFile" accept=".txt" hidden>
  </div>
</header>
<main>
  <div class="card" id="card"></div>
  <div class="nav">
    <button id="prev">← Prethodni</button>
    <button id="nextOpen">Sledeći neoznačen</button>
    <button id="next">Sledeći →</button>
  </div>
  <div class="dots" id="dots" aria-label="Svi itemi"></div>
  <p class="help">Tastatura: <b>1</b> ok · <b>2</b> ispravka · <b>3</b> dodaj oblik · <b>4</b> sporno · <b>5</b> loš item ·
    <b>0</b> poništi · <b>←/→</b> kretanje · <b>Enter</b> potvrdi unos. Sve se čuva automatski u ovom browseru.</p>
</main>
<div class="toast" id="toast"></div>
<script type="application/json" id="items">__ITEMS__</script>
<script>
/* LOGIC-START */
const KINDS = {
  ok: { label: "ok", key: "1" }, fix: { label: "ispravka", key: "2" }, add: { label: "+ oblik", key: "3" },
  unsure: { label: "sporno", key: "4" }, drop: { label: "loš item", key: "5" },
};
// The exact sheet format `serbeval verify --apply` parses: "[n] id" then "PROVERA: mark".
function markText(m) {
  if (!m) return "";
  if (m.kind === "ok") return "ok";
  if (m.kind === "unsure") return "?";
  if (m.kind === "drop") return "-";
  if (m.kind === "fix") return "x " + m.value;
  if (m.kind === "add") return "+ " + m.value;
  return "";
}
function serializeMarks(items, marks) {
  const out = ["# serbeval — provera (izvezeno iz HTML-a)", ""];
  items.forEach((it, i) => {
    out.push("[" + (i + 1) + "] " + it.id);
    out.push("PROVERA: " + markText(marks[it.id]));
    out.push("");
  });
  return out.join("\n");
}
function parseMarks(text) {
  const marks = {};
  let current = null;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    const id = line.match(/^\[\d+\]\s+(\S+)/);
    if (id) { current = id[1]; continue; }
    const check = line.match(/^PROVERA:\s*(.*)$/);
    if (check && current) {
      const mark = check[1].split("#")[0].trim();
      const head = mark.split(/\s+/)[0].toLowerCase();
      const rest = mark.slice(head.length).trim();
      if (head === "ok") marks[current] = { kind: "ok" };
      else if (head === "?") marks[current] = { kind: "unsure" };
      else if (head === "-") marks[current] = { kind: "drop" };
      else if (head === "x" && rest) marks[current] = { kind: "fix", value: rest };
      else if (head === "+" && rest) marks[current] = { kind: "add", value: rest };
      current = null;
    }
  }
  return marks;
}
/* LOGIC-END */

const ITEMS = JSON.parse(document.getElementById("items").textContent);
const STORE = "serbeval-verify:" + document.title;
let marks = {};
try { marks = JSON.parse(localStorage.getItem(STORE) || "{}"); } catch (e) { marks = {}; }
let pos = 0;
let editing = null;

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function save() { try { localStorage.setItem(STORE, JSON.stringify(marks)); } catch (e) { /* private mode: keep in memory */ } }
function toast(msg) { const t = $("toast"); t.textContent = msg; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 1400); }

function visible() {
  const cat = $("filter").value;
  const open = $("onlyOpen").checked;
  return ITEMS.map((it, i) => i).filter((i) =>
    (!cat || ITEMS[i].task + " · " + ITEMS[i].category === cat) && (!open || !marks[ITEMS[i].id] || i === pos));
}

function renderCounts() {
  const n = ITEMS.length;
  const c = { ok: 0, fix: 0, add: 0, unsure: 0, drop: 0 };
  Object.values(marks).forEach((m) => { if (c[m.kind] !== undefined) c[m.kind]++; });
  const done = Object.keys(marks).filter((id) => ITEMS.some((it) => it.id === id)).length;
  $("progress").style.width = (100 * done / n) + "%";
  $("counts").textContent = done + "/" + n + " · ok " + c.ok + " · ispravka " + c.fix + " · +oblik " + c.add +
    " · sporno " + c.unsure + " · loš " + c.drop;
}

function sentenceHtml(it) {
  if (it.kind === "mcq") return esc(it.question);
  const parts = it.question.split("____");
  return esc(parts[0]) + "<mark>" + esc(it.gold[0]) + "</mark>" + esc(parts.slice(1).join("____"));
}

function render() {
  const it = ITEMS[pos];
  const m = marks[it.id];
  let body = '<div class="meta"><span>[' + (pos + 1) + "] " + esc(it.id) + "</span><span>" + esc(it.task) + " · " +
    esc(it.category) + '</span><span class="status">' + (m ? "označeno: " + esc(markText(m)) : "neoznačeno") + "</span></div>";
  body += '<div class="sentence">' + sentenceHtml(it) + "</div>";
  if (it.kind === "cloze") {
    body += '<div class="original">' + esc(it.question) + '<span class="cue">' + esc(it.cue) + "</span></div>";
    body += '<div class="gold-box">Tačno: <b>' + it.gold.map(esc).join(" / ") + "</b></div>";
  } else {
    body += '<ol class="choices">' + it.choices.map((c, i) => '<li class="' + ("ABCD"[i] === it.gold[0] ? "gold" : "") +
      '">' + "ABCD"[i] + ") " + esc(c) + "</li>").join("") + "</ol>";
  }
  body += '<div class="explain">' + esc(it.explanation) + "</div>";
  body += '<div class="actions">' + Object.entries(KINDS).map(([k, v]) =>
    '<button class="a-' + k + (m && m.kind === k ? " on" : "") + '" data-kind="' + k + '">' + v.label +
    "<kbd>" + v.key + "</kbd></button>").join("") + "</div>";
  body += '<div class="editor" id="editor"></div>';
  $("card").innerHTML = body;
  $("card").querySelectorAll(".actions button").forEach((b) => b.addEventListener("click", () => choose(b.dataset.kind)));
  renderDots();
  renderCounts();
  editing = null;
}

function renderDots() {
  $("dots").innerHTML = ITEMS.map((it, i) => {
    const m = marks[it.id];
    return '<button title="[' + (i + 1) + "] " + esc(it.id) + '" class="' + (m ? "k-" + m.kind : "") +
      (i === pos ? " cur" : "") + '" data-i="' + i + '"></button>';
  }).join("");
  $("dots").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => go(Number(b.dataset.i))));
}

function setMark(kind, value) {
  const id = ITEMS[pos].id;
  marks[id] = value === undefined ? { kind } : { kind, value };
  save();
  render();
  advance();
}

function choose(kind) {
  const it = ITEMS[pos];
  if (kind === "ok" || kind === "unsure" || kind === "drop") return setMark(kind);
  const ed = $("editor");
  ed.classList.add("open");
  editing = kind;
  if (it.kind === "mcq") {
    if (kind === "add") { ed.innerHTML = '<span class="explain">„+ oblik“ važi samo za dopunu; za ponuđene odgovore koristi ispravku.</span>'; return; }
    ed.innerHTML = '<span>Tačno slovo:</span><span class="letters">' + "ABCD".split("").map((l) =>
      '<button data-l="' + l + '">' + l + "</button>").join(" ") + "</span>";
    ed.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => setMark("fix", b.dataset.l)));
    return;
  }
  const prior = marks[it.id] && marks[it.id].kind === kind ? marks[it.id].value : (kind === "fix" ? it.gold.join(" / ") : "");
  ed.innerHTML = '<span>' + (kind === "fix" ? "Ispravni oblici (odvoji „ / “):" : "Dodatni tačan oblik:") +
    '</span><input type="text" id="editValue" value="' + esc(prior) + '"><button class="primary" id="editOk">Potvrdi</button>';
  const input = $("editValue");
  input.focus(); input.select();
  const commit = () => { const v = input.value.trim(); if (v) setMark(kind, v); };
  $("editOk").addEventListener("click", commit);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") commit(); if (e.key === "Escape") render(); e.stopPropagation(); });
}

function go(i) { pos = Math.max(0, Math.min(ITEMS.length - 1, i)); render(); }
function step(d) {
  const v = visible();
  const at = v.indexOf(pos);
  const next = v[at + d];
  if (next !== undefined) go(next);
}
function advance() {
  const v = visible().filter((i) => !marks[ITEMS[i].id]);
  const after = v.find((i) => i > pos);
  if (after !== undefined) go(after);
  else if (v.length) go(v[0]);
  else toast("Sve je označeno — preuzmi fajl.");
}

function exportSheet() {
  const blob = new Blob([serializeMarks(ITEMS, marks)], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = document.title + ".txt";
  a.click();
  URL.revokeObjectURL(a.href);
}

$("filter").innerHTML = '<option value="">Sve kategorije (' + ITEMS.length + ")</option>" +
  [...new Set(ITEMS.map((it) => it.task + " · " + it.category))].map((c) =>
    '<option value="' + esc(c) + '">' + esc(c) + " (" + ITEMS.filter((it) => it.task + " · " + it.category === c).length +
    ")</option>").join("");
$("filter").addEventListener("change", () => { const v = visible(); if (v.length) go(v[0]); });
$("onlyOpen").addEventListener("change", render);
$("prev").addEventListener("click", () => step(-1));
$("next").addEventListener("click", () => step(1));
$("nextOpen").addEventListener("click", advance);
$("exportBtn").addEventListener("click", exportSheet);
$("importBtn").addEventListener("click", () => $("importFile").click());
$("importFile").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const loaded = parseMarks(await file.text());
  Object.assign(marks, loaded);
  save(); render();
  toast("Učitano " + Object.keys(loaded).length + " oznaka.");
});
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.metaKey || e.ctrlKey) return;
  const kind = Object.keys(KINDS).find((k) => KINDS[k].key === e.key);
  if (kind) { e.preventDefault(); choose(kind); }
  else if (e.key === "0") { delete marks[ITEMS[pos].id]; save(); render(); }
  else if (e.key === "ArrowRight" || e.key === "j") step(1);
  else if (e.key === "ArrowLeft" || e.key === "k") step(-1);
});
const firstOpen = ITEMS.findIndex((it) => !marks[it.id]);
go(firstOpen === -1 ? 0 : firstOpen);
</script>
</body>
</html>
"""
