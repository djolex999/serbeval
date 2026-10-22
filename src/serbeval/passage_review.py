"""Single-file HTML page for the maintainer's review of v2 passages, and its sheet parser.

Same idea as verify_page for v1: the page is a nicer way to fill a text sheet, and its
download ("[n] id" / "PROVERA: mark") is what `parse_passage_review` reads; a test runs the
page's own serializer through this parser. Marks: ok, x <note>, ?, -.
"""

import json
import re
from collections.abc import Mapping, Sequence
from html import escape
from typing import Any

from serbeval.passage import Site, parse_markup
from serbeval.translit import cyrillic_to_latin

Row = Mapping[str, Any]


def _cite(row: Row, site: Site) -> str:
    cites: Mapping[str, str] = row.get("pravopis_2010", {})
    keyed = cites.get(f"{site.wrong} → {'/'.join(site.alternatives)}")
    if keyed:
        return keyed
    right = cyrillic_to_latin(site.alternatives[0]).lower()
    return next((c for k, c in cites.items() if " → " not in k and k in right), "")


def review_rows(rows: Sequence[Row]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        p = parse_markup(str(row["markup"]))
        natural = set(row.get("natural_errors", []))
        sites: list[dict[str, Any]] = []
        parts: list[dict[str, Any]] = []
        for part in p.parts:
            if isinstance(part, Site):
                parts.append({"s": len(sites)})
                sites.append({
                    "wrong": part.wrong, "right": list(part.alternatives), "free": part.free,
                    "natural": part.wrong in natural, "cite": _cite(row, part),
                })
            elif part:
                parts.append({"t": part})
        source = str(row.get("source", ""))
        out.append({
            "id": row["id"], "set": "gov" if "-gov-" in str(row["id"]) else "draft",
            "script": row.get("script", ""), "errors": row.get("errors", 0),
            "origin": " · ".join(str(row[k]) for k in ("body", "doc_type") if row.get(k)),
            "link": source if source.startswith("http") else "",
            "source": p.source, "gold": p.gold, "sites": sites, "parts": parts,
        })
    return out


_MARK = re.compile(r"^PROVERA:\s*(.*)$")
_ID = re.compile(r"^\[\d+\]\s+(\S+)")


def parse_passage_review(text: str) -> dict[str, tuple[str, str]]:
    """{passage id: (mark, note)} for every marked passage; blank marks are skipped."""
    marks: dict[str, tuple[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if m := _ID.match(line):
            current = m.group(1)
            continue
        if (m := _MARK.match(line)) and current:
            value = m.group(1).strip()
            head, _, note = value.partition(" ")
            if not value:
                pass
            elif head.lower() in ("ok", "?", "-") and not note:
                marks[current] = (head.lower(), "")
            elif head.lower() == "x":
                if not note.strip():
                    raise ValueError(f"{current}: „x“ needs a note saying what is wrong")
                marks[current] = ("x", note.strip())
            else:
                raise ValueError(f"{current}: unknown mark {value!r} (use ok, x <note>, ?, -)")
            current = None
    return marks


def build_passage_review_html(rows: Sequence[Mapping[str, Any]], *, title: str) -> str:
    data = json.dumps(list(rows), ensure_ascii=False).replace("<", "\\u003c")
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
  --ok: #2f7d4f; --fix: #b4542d; --unsure: #a07a12; --drop: #8a2d3b;
  --wrong-bg: #fbe3dc; --right-bg: #d9efe2; --free-bg: #e7e4f6;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #161614; --panel: #1f1f1c; --ink: #ecebe6; --muted: #a29f95; --line: #34332e;
    --accent: #7fbfa6; --accent-ink: #10201a; --gold-bg: #1d2e26; --gold-line: #3f6b57;
    --ok: #6fcf97; --fix: #f0936a; --unsure: #e8c35a; --drop: #e58a9a;
    --wrong-bg: #4a261c; --right-bg: #1f3d2c; --free-bg: #2e2a48;
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
.meta a { color: var(--accent); }
.status { font-weight: 650; }
.label { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin-top: 14px; }
.text { font-size: 19px; line-height: 1.6; margin: 4px 0 0; }
.gold { background: var(--gold-bg); border: 1px solid var(--gold-line); border-radius: 10px; padding: 10px 14px; margin-top: 4px; }
.w { background: var(--wrong-bg); border-radius: 4px; padding: 0 3px; }
.r { background: var(--right-bg); border-radius: 4px; padding: 0 3px; font-weight: 600; }
.f { background: var(--free-bg); border-radius: 4px; padding: 0 3px; }
.sites { list-style: none; padding: 0; margin: 10px 0 0; display: grid; gap: 4px; font-size: 14px; }
.sites li { border-left: 3px solid var(--line); padding: 2px 10px; }
.sites .cite { color: var(--muted); }
.clean { color: var(--muted); font-size: 14px; margin-top: 8px; }
.actions { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 16px; }
.actions button { padding: 10px 6px; font-weight: 600; }
.actions kbd { display: block; font: 12px ui-monospace, monospace; color: var(--muted); font-weight: 400; }
.a-ok { color: var(--ok); } .a-x { color: var(--fix); } .a-unsure { color: var(--unsure); } .a-drop { color: var(--drop); }
.actions button.on { outline: 2px solid currentColor; }
.editor { display: none; gap: 8px; margin-top: 12px; align-items: center; flex-wrap: wrap; }
.editor.open { display: flex; }
.editor input { flex: 1 1 240px; }
.note { margin-top: 8px; font-size: 14px; color: var(--fix); }
.nav { display: flex; justify-content: space-between; gap: 8px; margin-top: 14px; }
.dots { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 18px; }
.dots button { width: 14px; height: 14px; padding: 0; border-radius: 4px; background: var(--line); border: 0; }
.dots button.cur { outline: 2px solid var(--ink); }
.dots .k-ok { background: var(--ok); } .dots .k-x { background: var(--fix); }
.dots .k-unsure { background: var(--unsure); } .dots .k-drop { background: var(--drop); }
.help { font-size: 13px; color: var(--muted); margin-top: 14px; }
.toast { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%); background: var(--ink); color: var(--bg);
  padding: 8px 14px; border-radius: 8px; opacity: 0; transition: opacity .2s; pointer-events: none; }
.toast.show { opacity: 1; }
@media (max-width: 560px) { .actions { grid-template-columns: repeat(2, minmax(0, 1fr)); } .text { font-size: 17px; } }
</style>
</head>
<body>
<header>
  <div class="bar">
    <h1>Provera v2 pasusa</h1>
    <div class="progress" aria-hidden="true"><div id="progress"></div></div>
    <span class="counts" id="counts"></span>
  </div>
  <div class="bar" style="margin-top:8px">
    <select id="filter" aria-label="Skup">
      <option value="">Svi pasusi</option><option value="draft">Moji nacrti</option><option value="gov">Zvanični tekstovi</option>
    </select>
    <label class="counts"><input type="checkbox" id="onlyOpen"> samo neoznačeni</label>
    <span style="flex:1"></span>
    <button id="importBtn">Učitaj fajl</button>
    <button id="exportBtn" class="primary">Preuzmi ocene</button>
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
  <div class="dots" id="dots" aria-label="Svi pasusi"></div>
  <p class="help">Tastatura: <b>1</b> ok · <b>2</b> x (napiši šta ne valja) · <b>3</b> nisam siguran · <b>4</b> izbaci ·
    <b>0</b> poništi · <b>←/→</b> kretanje · <b>Enter</b> potvrdi napomenu. Sve se čuva automatski u ovom browseru.
    <br>Crveno = greška koju model vidi · zeleno = tačan oblik · ljubičasto = oba oblika važe · 🟢 = prava greška iz originalnog teksta institucije.</p>
</main>
<div class="toast" id="toast"></div>
<script type="application/json" id="items">__ITEMS__</script>
<script>
/* LOGIC-START */
// The sheet `parse_passage_review` reads: "[n] id" then "PROVERA: ok | x <note> | ? | -".
function markText(m) {
  if (!m) return "";
  if (m.kind === "ok") return "ok";
  if (m.kind === "unsure") return "?";
  if (m.kind === "drop") return "-";
  if (m.kind === "x") return "x " + String(m.note || "").replace(/\s+/g, " ").trim();
  return "";
}
function serializeMarks(items, marks) {
  const out = ["# serbeval v2 — provera pasusa (izvezeno iz HTML-a)", ""];
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
      const v = check[1].trim();
      const head = v.split(/\s+/)[0].toLowerCase();
      const rest = v.slice(head.length).trim();
      if (head === "ok") marks[current] = { kind: "ok" };
      else if (head === "?") marks[current] = { kind: "unsure" };
      else if (head === "-") marks[current] = { kind: "drop" };
      else if (head === "x" && rest) marks[current] = { kind: "x", note: rest };
      current = null;
    }
  }
  return marks;
}
/* LOGIC-END */

const KINDS = { ok: { label: "ok", key: "1" }, x: { label: "x — ne valja", key: "2" },
  unsure: { label: "nisam siguran", key: "3" }, drop: { label: "izbaci", key: "4" } };
const ITEMS = JSON.parse(document.getElementById("items").textContent);
const STORE = "serbeval-v2-review:" + document.title;
let marks = {};
try { marks = JSON.parse(localStorage.getItem(STORE) || "{}"); } catch (e) { marks = {}; }
let pos = 0;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function save() { try { localStorage.setItem(STORE, JSON.stringify(marks)); } catch (e) { /* keep in memory */ } }
function toast(msg) { const t = $("toast"); t.textContent = msg; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 1400); }

function visible() {
  const set = $("filter").value, open = $("onlyOpen").checked;
  return ITEMS.map((_, i) => i).filter((i) => (!set || ITEMS[i].set === set) && (!open || !marks[ITEMS[i].id] || i === pos));
}
function renderCounts() {
  const c = { ok: 0, x: 0, unsure: 0, drop: 0 };
  let done = 0;
  ITEMS.forEach((it) => { const m = marks[it.id]; if (m) { done++; c[m.kind]++; } });
  $("progress").style.width = (100 * done / ITEMS.length) + "%";
  $("counts").textContent = done + "/" + ITEMS.length + " · ok " + c.ok + " · x " + c.x + " · ? " + c.unsure + " · izbaci " + c.drop;
}
function textHtml(it, gold) {
  return it.parts.map((p) => {
    if (p.t !== undefined) return esc(p.t);
    const s = it.sites[p.s];
    if (s.free) return '<span class="f">' + esc(gold ? s.right.join(" / ") : s.wrong) + "</span>";
    return gold ? '<span class="r">' + esc(s.right.join(" / ")) + "</span>" : '<span class="w">' + esc(s.wrong) + "</span>";
  }).join("");
}
function render() {
  const it = ITEMS[pos], m = marks[it.id];
  const kind = it.errors ? it.errors + " greš." : "čist pasus";
  let body = '<div class="meta"><span>[' + (pos + 1) + "] " + esc(it.id) + "</span><span>" +
    esc(it.origin || (it.set === "gov" ? "zvanični tekst" : "nacrt")) + " · " + esc(it.script) + " · " + kind +
    (it.link ? ' · <a href="' + esc(it.link) + '" target="_blank" rel="noopener">original</a>' : "") +
    '</span><span class="status">' + (m ? "označeno: " + esc(markText(m)) : "neoznačeno") + "</span></div>";
  body += '<div class="label">Šta model vidi</div><div class="text">' + textHtml(it, false) + "</div>";
  if (it.sites.length) {
    body += '<div class="label">Tačno</div><div class="text gold">' + textHtml(it, true) + "</div>";
    body += '<ul class="sites">' + it.sites.map((s) => "<li>" + (s.natural ? "🟢 " : "") + (s.free ? "⚖ " : "") +
      "„" + esc(s.wrong) + "“ → <b>" + esc(s.right.join(" / ")) + '</b> <span class="cite">· ' + esc(s.cite || "bez citata") +
      "</span></li>").join("") + "</ul>";
  } else {
    body += '<div class="clean">Pasus je tačan i model ne sme ništa da menja. Proveri da u njemu zaista nema greške.</div>';
  }
  if (m && m.kind === "x") body += '<div class="note">Napomena: ' + esc(m.note) + "</div>";
  body += '<div class="actions">' + Object.entries(KINDS).map(([k, v]) =>
    '<button class="a-' + k + (m && m.kind === k ? " on" : "") + '" data-kind="' + k + '">' + v.label +
    "<kbd>" + v.key + "</kbd></button>").join("") + "</div>";
  body += '<div class="editor" id="editor"></div>';
  $("card").innerHTML = body;
  $("card").querySelectorAll(".actions button").forEach((b) => b.addEventListener("click", () => choose(b.dataset.kind)));
  renderDots(); renderCounts();
}
function renderDots() {
  $("dots").innerHTML = ITEMS.map((it, i) => {
    const m = marks[it.id];
    return '<button title="[' + (i + 1) + "] " + esc(it.id) + '" class="' + (m ? "k-" + m.kind : "") +
      (i === pos ? " cur" : "") + '" data-i="' + i + '"></button>';
  }).join("");
  $("dots").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => go(Number(b.dataset.i))));
}
function setMark(kind, note) {
  marks[ITEMS[pos].id] = note === undefined ? { kind } : { kind, note };
  save(); render(); advance();
}
function choose(kind) {
  if (kind !== "x") return setMark(kind);
  const ed = $("editor"), prior = marks[ITEMS[pos].id];
  ed.classList.add("open");
  ed.innerHTML = '<span>Šta ne valja:</span><input type="text" id="noteValue" value="' +
    esc(prior && prior.kind === "x" ? prior.note : "") + '"><button class="primary" id="noteOk">Potvrdi</button>';
  const input = $("noteValue");
  input.focus(); input.select();
  const commit = () => { const v = input.value.trim(); if (v) setMark("x", v); else toast("Upiši šta ne valja."); };
  $("noteOk").addEventListener("click", commit);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") commit(); if (e.key === "Escape") render(); e.stopPropagation(); });
}
function go(i) { pos = Math.max(0, Math.min(ITEMS.length - 1, i)); render(); }
function step(d) { const v = visible(), n = v[v.indexOf(pos) + d]; if (n !== undefined) go(n); }
function advance() {
  const v = visible().filter((i) => !marks[ITEMS[i].id]);
  const after = v.find((i) => i > pos);
  if (after !== undefined) go(after); else if (v.length) go(v[0]); else toast("Sve je označeno — preuzmi ocene.");
}
$("filter").addEventListener("change", () => { const v = visible(); if (v.length) go(v[0]); });
$("onlyOpen").addEventListener("change", render);
$("prev").addEventListener("click", () => step(-1));
$("next").addEventListener("click", () => step(1));
$("nextOpen").addEventListener("click", advance);
$("exportBtn").addEventListener("click", () => {
  const blob = new Blob([serializeMarks(ITEMS, marks)], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = document.title + ".txt"; a.click(); URL.revokeObjectURL(a.href);
});
$("importBtn").addEventListener("click", () => $("importFile").click());
$("importFile").addEventListener("change", async (e) => {
  const file = e.target.files[0]; if (!file) return;
  const loaded = parseMarks(await file.text());
  Object.assign(marks, loaded); save(); render();
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
