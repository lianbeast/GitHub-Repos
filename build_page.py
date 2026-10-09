#!/usr/bin/env python3
"""
Build a self-contained repo browser (index.html) from repos.json.

Run `python fetch_repos.py` first to refresh repos.json, then
`python build_page.py` to regenerate index.html.
"""
import json
import datetime
import html as html_mod

REPOS_FILE = "repos.json"
OUT_FILE = "index.html"


def load():
    with open(REPOS_FILE, encoding="utf-8") as f:
        return json.load(f)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__ · Repository Browser</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23e6edf3'%3E%3Cpath d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z'/%3E%3C/svg%3E">
<style>
  :root{
    --bg:#0b0e14;
    --bg-grad-1:rgba(88,101,242,.14);
    --bg-grad-2:rgba(139,92,246,.10);
    --panel:#111621;
    --panel-2:#151b28;
    --card:#121826;
    --card-hover:#161e30;
    --border:#222b3d;
    --border-soft:#1b2233;
    --text:#e6edf3;
    --text-dim:#9aa7bd;
    --text-faint:#6b7789;
    --accent:#7c8cff;
    --accent-2:#a78bfa;
    --green:#3fb950;
    --amber:#d29922;
    --radius:14px;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
    --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--bg);
    color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
    font-size:15px;
    line-height:1.55;
    -webkit-font-smoothing:antialiased;
    min-height:100vh;
  }
  body::before{
    content:"";
    position:fixed;inset:0;
    background:
      radial-gradient(900px 500px at 12% -8%,var(--bg-grad-1),transparent 60%),
      radial-gradient(800px 480px at 92% -12%,var(--bg-grad-2),transparent 62%);
    pointer-events:none;z-index:0;
  }
  .wrap{position:relative;z-index:1;max-width:1280px;margin:0 auto;padding:0 22px 80px}

  /* ---------- header ---------- */
  header{padding:42px 0 22px}
  .brand{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
  .avatar{
    width:60px;height:60px;border-radius:50%;
    border:1px solid var(--border);
    box-shadow:0 0 0 4px rgba(124,140,255,.10);
    flex:0 0 auto;
  }
  .brand-text h1{margin:0;font-size:1.55rem;font-weight:700;letter-spacing:-.02em;line-height:1.2}
  .brand-text .handle{
    display:inline-flex;align-items:center;gap:7px;
    color:var(--text-dim);font-size:.92rem;font-family:var(--mono);
    text-decoration:none;
  }
  .brand-text .handle:hover{color:var(--accent)}
  .handle svg{width:14px;height:14px;fill:currentColor}

  .stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}
  .stat{
    background:linear-gradient(180deg,var(--panel-2),var(--panel));
    border:1px solid var(--border);
    border-radius:12px;
    padding:10px 15px;
    min-width:92px;
  }
  .stat .n{font-size:1.25rem;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
  .stat .l{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--text-faint)}

  /* ---------- controls ---------- */
  .controls{
    position:sticky;top:0;z-index:20;
    margin:26px 0 20px;
    padding:14px;
    background:rgba(11,14,20,.82);
    backdrop-filter:blur(14px);
    -webkit-backdrop-filter:blur(14px);
    border:1px solid var(--border);
    border-radius:16px;
    box-shadow:var(--shadow);
  }
  .search-row{display:flex;gap:10px;flex-wrap:wrap}
  .search-box{
    position:relative;flex:1 1 320px;min-width:220px;
  }
  .search-box svg{
    position:absolute;left:13px;top:50%;transform:translateY(-50%);
    width:16px;height:16px;fill:var(--text-faint);pointer-events:none;
  }
  #search{
    width:100%;
    padding:11px 40px 11px 38px;
    background:var(--bg);
    border:1px solid var(--border);
    border-radius:10px;
    color:var(--text);
    font-size:.95rem;
    font-family:inherit;
    outline:none;
    transition:border-color .15s,box-shadow .15s;
  }
  #search::placeholder{color:var(--text-faint)}
  #search:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,140,255,.16)}
  .kbd{
    position:absolute;right:11px;top:50%;transform:translateY(-50%);
    font-family:var(--mono);font-size:.7rem;color:var(--text-faint);
    border:1px solid var(--border);border-radius:5px;padding:1px 6px;
    background:var(--panel);
  }
  select{
    appearance:none;
    padding:11px 34px 11px 13px;
    background:var(--bg) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%236b7789'%3E%3Cpath d='M4.4 6.2 8 9.8l3.6-3.6.9.9L8 11.6 3.5 7.1z'/%3E%3C/svg%3E") no-repeat right 11px center;
    background-size:15px;
    border:1px solid var(--border);
    border-radius:10px;
    color:var(--text);
    font-size:.9rem;font-family:inherit;
    cursor:pointer;outline:none;
    transition:border-color .15s;
  }
  select:focus{border-color:var(--accent)}
  select:hover{border-color:#2e3a52}

  .chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;align-items:center}
  .chip{
    display:inline-flex;align-items:center;gap:7px;
    padding:6px 13px;
    background:var(--bg);
    border:1px solid var(--border);
    border-radius:999px;
    color:var(--text-dim);
    font-size:.84rem;font-weight:500;
    cursor:pointer;user-select:none;
    transition:all .15s;
    white-space:nowrap;
  }
  .chip:hover{color:var(--text);border-color:#2e3a52}
  .chip.on{
    color:#fff;
    background:linear-gradient(135deg,var(--accent),var(--accent-2));
    border-color:transparent;
    box-shadow:0 4px 14px -6px rgba(124,140,255,.7);
  }
  .chip .cnt{font-variant-numeric:tabular-nums;opacity:.7;font-size:.78rem}
  .chip.on .cnt{opacity:.9}
  .chip .dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto}
  .divider{width:1px;height:20px;background:var(--border);margin:0 2px}

  .meta-row{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin:0 4px 14px}
  .result-count{color:var(--text-dim);font-size:.88rem}
  .result-count b{color:var(--text)}
  .clear{
    background:none;border:none;color:var(--accent);cursor:pointer;
    font-size:.85rem;font-family:inherit;padding:4px 6px;border-radius:6px;
  }
  .clear:hover{background:rgba(124,140,255,.1)}

  /* ---------- grid ---------- */
  .grid{
    display:grid;
    grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
    gap:14px;
  }
  .card{
    position:relative;
    display:flex;flex-direction:column;
    background:var(--card);
    border:1px solid var(--border-soft);
    border-radius:var(--radius);
    padding:17px 18px 15px;
    cursor:pointer;
    transition:transform .16s ease,border-color .16s,background .16s,box-shadow .16s;
    overflow:hidden;
  }
  .card::after{
    content:"";position:absolute;left:0;top:0;height:2px;width:100%;
    background:linear-gradient(90deg,var(--accent),var(--accent-2));
    opacity:0;transition:opacity .16s;
  }
  .card:hover{
    transform:translateY(-3px);
    background:var(--card-hover);
    border-color:#2e3a52;
    box-shadow:0 12px 30px -14px rgba(0,0,0,.75);
  }
  .card:hover::after{opacity:1}
  .card:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

  .card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
  .repo-name{
    display:flex;align-items:center;gap:9px;min-width:0;
  }
  .repo-name .ico{width:16px;height:16px;fill:var(--text-faint);flex:0 0 auto}
  .repo-name a{
    color:var(--text);font-weight:650;font-size:1.02rem;
    text-decoration:none;letter-spacing:-.01em;
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  }
  .card:hover .repo-name a{color:var(--accent)}
  .badge{
    flex:0 0 auto;
    font-size:.68rem;font-weight:600;letter-spacing:.04em;
    text-transform:uppercase;
    padding:3px 8px;border-radius:999px;
    border:1px solid var(--border);
    color:var(--text-faint);
  }
  .badge.fork{color:var(--accent-2);border-color:rgba(167,139,250,.35);background:rgba(167,139,250,.08)}
  .badge.archived{color:var(--amber);border-color:rgba(210,153,34,.35);background:rgba(210,153,34,.08)}

  .card-actions{display:flex;align-items:center;gap:7px;flex:0 0 auto}
  .fav-btn{
    display:inline-flex;align-items:center;gap:4px;
    background:none;border:1px solid var(--border);
    color:var(--text-faint);
    border-radius:7px;padding:3px 8px;
    font-size:.72rem;font-weight:600;font-family:inherit;cursor:pointer;
    transition:all .15s;white-space:nowrap;
  }
  .fav-btn:hover{color:var(--amber);border-color:rgba(210,153,34,.40);background:rgba(210,153,34,.08)}
  .fav-btn.on{color:var(--amber);border-color:rgba(210,153,34,.45);background:rgba(210,153,34,.12)}
  .fav-btn svg{width:12px;height:12px;fill:currentColor}
  .fav-btn:focus-visible{outline:2px solid var(--amber);outline-offset:1px}

  .notice{
    display:inline-flex;align-items:center;gap:6px;
    font-size:.78rem;color:var(--text-faint);
    background:var(--panel);border:1px solid var(--border);
    border-radius:999px;padding:4px 11px;
  }
  .notice .dot{width:7px;height:7px;border-radius:50%;background:var(--amber);flex:0 0 auto}

  .desc{
    margin:10px 0 0;color:var(--text-dim);font-size:.9rem;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
    overflow:hidden;min-height:2.6em;
  }
  .desc.empty{color:var(--text-faint);font-style:italic}

  .topics{display:flex;gap:6px;flex-wrap:wrap;margin-top:11px}
  .topic{
    font-size:.72rem;color:var(--accent);
    background:rgba(124,140,255,.10);
    border:1px solid rgba(124,140,255,.18);
    padding:2px 8px;border-radius:999px;
  }

  .card-foot{
    display:flex;align-items:center;gap:14px;flex-wrap:wrap;
    margin-top:14px;padding-top:12px;
    border-top:1px solid var(--border-soft);
    font-size:.79rem;color:var(--text-dim);
  }
  .foot-item{display:inline-flex;align-items:center;gap:5px}
  .foot-item svg{width:13px;height:13px;fill:currentColor;opacity:.85}
  .lang-dot{width:10px;height:10px;border-radius:50%;flex:0 0 auto;box-shadow:0 0 0 1px rgba(255,255,255,.06) inset}
  .lang-name{color:var(--text-dim)}
  .live{
    margin-left:auto;
    display:inline-flex;align-items:center;gap:5px;
    color:var(--green);text-decoration:none;font-weight:600;font-size:.79rem;
    padding:3px 9px;border-radius:7px;
    border:1px solid rgba(63,185,80,.28);background:rgba(63,185,80,.08);
  }
  .live:hover{background:rgba(63,185,80,.16)}
  .live svg{width:12px;height:12px;fill:currentColor}

  /* ---------- states ---------- */
  .empty{
    grid-column:1/-1;text-align:center;padding:70px 20px;color:var(--text-dim);
  }
  .empty svg{width:44px;height:44px;fill:var(--text-faint);margin-bottom:14px;opacity:.6}
  .empty h3{margin:0 0 6px;color:var(--text);font-size:1.05rem}
  .empty p{margin:0;font-size:.9rem}

  footer{
    margin-top:44px;padding-top:22px;border-top:1px solid var(--border-soft);
    color:var(--text-faint);font-size:.82rem;
    display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;
  }
  footer a{color:var(--text-dim);text-decoration:none}
  footer a:hover{color:var(--accent)}

  .to-top{
    position:fixed;right:22px;bottom:22px;z-index:30;
    width:44px;height:44px;border-radius:50%;
    background:linear-gradient(135deg,var(--accent),var(--accent-2));
    border:none;cursor:pointer;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 8px 24px -8px rgba(124,140,255,.8);
    opacity:0;pointer-events:none;transform:translateY(10px);
    transition:opacity .2s,transform .2s;
  }
  .to-top.show{opacity:1;pointer-events:auto;transform:none}
  .to-top svg{width:18px;height:18px;fill:#fff}

  @media (max-width:640px){
    .wrap{padding:0 14px 60px}
    header{padding:28px 0 16px}
    .brand-text h1{font-size:1.3rem}
    .grid{grid-template-columns:1fr}
    .controls{padding:11px;border-radius:14px}
    .kbd{display:none}
    .stat{padding:8px 12px;min-width:78px}
    .stat .n{font-size:1.08rem}
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <img class="avatar" src="https://avatars.githubusercontent.com/u/213338141?v=4" alt="__LOGIN__ avatar" loading="lazy">
      <div class="brand-text">
        <h1>Repository Browser</h1>
        <a class="handle" href="https://github.com/__LOGIN__" target="_blank" rel="noopener">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
          github.com/__LOGIN__
        </a>
      </div>
    </div>
    <div class="stats" id="stats"></div>
  </header>

  <div class="controls">
    <div class="search-row">
      <div class="search-box">
        <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10.68 11.74a6 6 0 0 1-7.922-8.982 6 6 0 0 1 8.982 7.922l3.04 3.04a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215ZM11.5 7a4.499 4.499 0 1 0-8.997 0A4.499 4.499 0 0 0 11.5 7Z"/></svg>
        <input id="search" type="search" placeholder="Search repositories by name, description, or topic…" autocomplete="off" spellcheck="false">
        <span class="kbd">/</span>
      </div>
      <select id="lang" aria-label="Filter by language"><option value="">All languages</option></select>
      <select id="sort" aria-label="Sort repositories">
        <option value="updated">Recently updated</option>
        <option value="pushed">Recently pushed</option>
        <option value="name">Name (A–Z)</option>
        <option value="stars">Most stars</option>
        <option value="size">Largest</option>
      </select>
    </div>
    <div class="chips" id="typeChips">
      <span class="chip on" data-type="all">All <span class="cnt"></span></span>
      <span class="chip" data-type="owned">Mine <span class="cnt"></span></span>
      <span class="chip" data-type="fork">Forks <span class="cnt"></span></span>
      <span class="chip" data-type="pages">Has Pages <span class="cnt"></span></span>
      <span class="chip" data-type="fav">★ Favorites <span class="cnt"></span></span>
      <span class="divider"></span>
      <span id="langChips"></span>
    </div>
  </div>

  <div class="meta-row">
    <div class="result-count" id="count"></div>
    <span class="notice" id="storageNotice" hidden><span class="dot"></span><span id="storageNoticeText"></span></span>
    <button class="clear" id="reset" hidden>Reset filters</button>
  </div>

  <main class="grid" id="grid"></main>

  <footer>
    <span>Generated <span id="gen"></span> · <span id="total"></span> public repositories</span>
    <span><a href="https://github.com/__LOGIN__?tab=repositories" target="_blank" rel="noopener">Open on GitHub ↗</a></span>
  </footer>
</div>

<button class="to-top" id="toTop" aria-label="Back to top">
  <svg viewBox="0 0 16 16"><path d="M8 3.5 2.5 9l1.1 1.1L8 5.7l4.4 4.4L13.5 9z"/></svg>
</button>

<script>
const DATA = __REPOS_JSON__;
const REPOS = DATA.repos;

const LANG_COLORS = {
  "Python":"#3572A5","TypeScript":"#3178c6","JavaScript":"#f1e05a","HTML":"#e34c26",
  "Rust":"#dea584","Shell":"#89e051","Swift":"#F05138","PHP":"#4F5D95","C++":"#f34b7d",
  "QML":"#44a51c","C#":"#178600","Go":"#00ADD8","CSS":"#563d7c","Vue":"#41b883",
  "Java":"#b07219","Ruby":"#701516","C":"#555555","Jupyter Notebook":"#DA5B0B",
  "Kotlin":"#A97BFF","Dart":"#00B4AB","Astro":"#ff5a03","Svelte":"#ff3e00",
  "SCSS":"#c6538c","Lua":"#000080","Perl":"#0298c3","Elixir":"#6e4a7e"
};
const langColor = l => LANG_COLORS[l] || "#8b949e";

const $ = s => document.querySelector(s);
const grid = $("#grid");

const state = { q:"", lang:"", type:"all", sort:"updated" };

/* ---------- favorites ---------- *
 * STORAGE MODE: LOCAL (browser localStorage) — device-scoped.
 *
 * Cloud sync is NOT enabled in this build: the cloud-service activation for
 * application wbapp_FxwvCca6OhDZMiPory61mv was not approved, so there is no
 * cloud environment, no cross-device sync and NO user login identity. Favorites
 * therefore live only in this browser on this device and are not per-user.
 *
 * When the cloud environment is activated, swap saveFavs/loadFavs for
 * cloud.database() reads/writes scoped to the signed-in user's id, and drop
 * the "local only" notice. Card markup and filtering below stay unchanged. */
const FAV_KEY = "ghb.favorites.v1";
let favs = new Set();
try { favs = new Set(JSON.parse(localStorage.getItem(FAV_KEY) || "[]")); } catch(e) { favs = new Set(); }

function saveFavs(){
  try { localStorage.setItem(FAV_KEY, JSON.stringify(Array.from(favs))); return true; }
  catch(e){ return false; }
}
function setNotice(text, isError){
  const el = $("#storageNotice");
  if(!el) return;
  $("#storageNoticeText").textContent = text || "";
  el.hidden = !text;
  el.style.borderColor = isError ? "rgba(210,153,34,.55)" : "";
}
function syncFavUI(){
  const chip = document.querySelector('#typeChips > .chip[data-type="fav"]');
  if(chip){ const c = chip.querySelector(".cnt"); if(c) c.textContent = favs.size; }
}
function toggleFav(name){
  if(favs.has(name)) favs.delete(name); else favs.add(name);
  if(saveFavs()) setNotice("Favorites saved on this device only — cloud sync is not enabled", false);
  else setNotice("Could not save — this browser's local storage is unavailable (private mode?)", true);
  syncFavUI();
  render();
}

/* ---------- helpers ---------- */
const esc = s => (s||"").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

function timeAgo(iso){
  if(!iso) return "—";
  const d = new Date(iso), now = new Date();
  const s = Math.floor((now - d)/1000);
  if(s < 60) return "just now";
  const m = Math.floor(s/60); if(m < 60) return m+"m ago";
  const h = Math.floor(m/60); if(h < 24) return h+"h ago";
  const dd = Math.floor(h/24); if(dd < 30) return dd+"d ago";
  const mo = Math.floor(dd/30); if(mo < 12) return mo+"mo ago";
  return Math.floor(mo/12)+"y ago";
}
const fmtDate = iso => iso ? new Date(iso).toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"}) : "";

/* ---------- build language filter options ---------- */
const langCounts = {};
REPOS.forEach(r => { if(r.language) langCounts[r.language] = (langCounts[r.language]||0)+1; });
const langsSorted = Object.entries(langCounts).sort((a,b)=> b[1]-a[1] || a[0].localeCompare(b[0]));

const langSel = $("#lang");
langsSorted.forEach(([l,c]) => {
  const o = document.createElement("option");
  o.value = l; o.textContent = l + " (" + c + ")";
  langSel.appendChild(o);
});

// quick-pick language chips (top 6)
const langChips = $("#langChips");
langsSorted.slice(0,6).forEach(([l,c]) => {
  const el = document.createElement("span");
  el.className = "chip";
  el.dataset.lang = l;
  el.innerHTML = '<span class="dot" style="background:'+langColor(l)+'"></span>'+esc(l)+' <span class="cnt">'+c+'</span>';
  langChips.appendChild(el);
});

/* ---------- header stats ---------- */
(function(){
  const total = REPOS.length;
  const owned = REPOS.filter(r=>!r.fork).length;
  const forks = REPOS.filter(r=>r.fork).length;
  const stars = REPOS.reduce((a,r)=>a+r.stars,0);
  const stats = [
    [total,"Repositories"],[owned,"Original"],[forks,"Forks"],[langsSorted.length,"Languages"],[stars,"Total stars"]
  ];
  $("#stats").innerHTML = stats.map(([n,l]) =>
    '<div class="stat"><div class="n">'+n+'</div><div class="l">'+l+'</div></div>'
  ).join("");
  $("#total").textContent = total;
  $("#gen").textContent = fmtDate(DATA.generated_at) || "—";
  // chip counts
  document.querySelectorAll("#typeChips > .chip").forEach(ch=>{
    const t = ch.dataset.type;
    const c = t==="all" ? total : t==="owned" ? owned : t==="fork" ? forks : REPOS.filter(r=>r.has_pages).length;
    const cnt = ch.querySelector(".cnt"); if(cnt) cnt.textContent = c;
  });
})();

/* ---------- filtering ---------- */
function matches(r){
  if(state.type==="fav" && !favs.has(r.full_name)) return false;
  if(state.type==="owned" && r.fork) return false;
  if(state.type==="fork" && !r.fork) return false;
  if(state.type==="pages" && !r.has_pages) return false;
  if(state.lang && r.language !== state.lang) return false;
  if(state.q){
    const q = state.q.toLowerCase();
    const hay = (r.name+" "+(r.description||"")+" "+(r.topics||[]).join(" ")+" "+(r.language||"")).toLowerCase();
    if(!hay.includes(q)) return false;
  }
  return true;
}
function sortFn(a,b){
  switch(state.sort){
    case "name": return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
    case "stars": return b.stars-a.stars || a.name.localeCompare(b.name);
    case "size": return b.size-a.size;
    case "pushed": return new Date(b.pushed_at||0) - new Date(a.pushed_at||0);
    default: return new Date(b.updated_at||0) - new Date(a.updated_at||0);
  }
}

/* ---------- rendering ---------- */
function card(r){
  const topics = (r.topics||[]).slice(0,4).map(t=>'<span class="topic">'+esc(t)+'</span>').join("");
  const badge = r.archived ? '<span class="badge archived">Archived</span>'
              : r.fork ? '<span class="badge fork">Fork</span>' : "";
  const isFav = favs.has(r.full_name);
  const favBtn = '<button class="fav-btn'+(isFav?" on":"")+'" data-fav="'+esc(r.full_name)+'"'
    + ' aria-pressed="'+(isFav?"true":"false")+'"'
    + ' title="'+(isFav ? "Remove from favorites" : "Add to favorites")+'">'
    + '<svg viewBox="0 0 16 16"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>'
    + (isFav ? "Saved" : "Save") + '</button>';
  const live = r.homepage
    ? '<a class="live" href="'+esc(r.homepage)+'" target="_blank" rel="noopener" title="Live site">'+
        '<svg viewBox="0 0 16 16"><path d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.5-.25h3.5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0V3.56L9.28 7.28a.751.751 0 0 1-1.06-1.06L11.94 2.5h-1.69a.75.75 0 0 1 0-1.5Z"/></svg>Live</a>' : "";

  const star = r.stars>0 ? '<span class="foot-item"><svg viewBox="0 0 16 16"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>'+r.stars+'</span>' : "";
  const fork = r.forks>0 ? '<span class="foot-item"><svg viewBox="0 0 16 16"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/></svg>'+r.forks+'</span>' : "";
  const lang = r.language ? '<span class="foot-item"><span class="lang-dot" style="background:'+langColor(r.language)+'"></span><span class="lang-name">'+esc(r.language)+'</span></span>' : "";
  const upd = '<span class="foot-item" title="Last updated '+fmtDate(r.updated_at)+'"><svg viewBox="0 0 16 16"><path d="M1.5 8a6.5 6.5 0 1 1 13 0 6.5 6.5 0 0 1-13 0ZM8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0Zm.5 4.75a.75.75 0 0 0-1.5 0v3.5c0 .199.079.39.22.53l2.25 2.25a.751.751 0 0 0 1.06-1.06L8.5 7.94Z"/></svg>'+timeAgo(r.updated_at)+'</span>';

  return '<article class="card" tabindex="0" data-url="'+esc(r.url)+'" role="link" aria-label="'+esc(r.name)+'">'
    + '<div class="card-top"><div class="repo-name">'
    + '<svg class="ico" viewBox="0 0 16 16"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/></svg>'
    + '<a href="'+esc(r.url)+'" target="_blank" rel="noopener" title="'+esc(r.name)+'">'+esc(r.name)+'</a>'
    + '</div><div class="card-actions">'+badge+favBtn+'</div></div>'
    + '<p class="desc'+(r.description?'':' empty')+'">'+ (r.description ? esc(r.description) : "No description provided.") +'</p>'
    + (topics ? '<div class="topics">'+topics+'</div>' : "")
    + '<div class="card-foot">'+lang+star+fork+upd+live+'</div>'
    + '</article>';
}

function render(){
  const list = REPOS.filter(matches).sort(sortFn);
  grid.innerHTML = list.length
    ? list.map(card).join("")
    : '<div class="empty"><svg viewBox="0 0 16 16"><path d="M10.68 11.74a6 6 0 0 1-7.922-8.982 6 6 0 0 1 8.982 7.922l3.04 3.04a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215ZM11.5 7a4.499 4.499 0 1 0-8.997 0A4.499 4.499 0 0 0 11.5 7Z"/></svg>'
      + (state.type==="fav" && favs.size===0
          ? '<h3>No favorites yet</h3><p>Click “Save” on any repository to start your list.</p>'
          : '<h3>No repositories found</h3><p>Try a different search term or clear the filters.</p>')
      + '</div>';

  $("#count").innerHTML = '<b>'+list.length+'</b> of '+REPOS.length+' repositories';
  const dirty = state.q || state.lang || state.type!=="all" || state.sort!=="updated";
  $("#reset").hidden = !dirty;
  syncFavUI();
}

/* ---------- events ---------- */
let t;
$("#search").addEventListener("input", e => {
  clearTimeout(t);
  const v = e.target.value;
  t = setTimeout(()=>{ state.q = v.trim(); render(); }, 90);
});
$("#lang").addEventListener("change", e => { state.lang = e.target.value; syncLangChips(); render(); });
$("#sort").addEventListener("change", e => { state.sort = e.target.value; render(); });

function syncLangChips(){
  document.querySelectorAll("#langChips .chip").forEach(c =>
    c.classList.toggle("on", c.dataset.lang === state.lang));
}
document.querySelectorAll("#typeChips > .chip").forEach(ch => {
  ch.addEventListener("click", () => {
    state.type = ch.dataset.type;
    document.querySelectorAll("#typeChips > .chip").forEach(c=>c.classList.toggle("on", c===ch));
    render();
  });
});
langChips.addEventListener("click", e => {
  const chip = e.target.closest(".chip"); if(!chip) return;
  state.lang = (state.lang === chip.dataset.lang) ? "" : chip.dataset.lang;
  $("#lang").value = state.lang;
  syncLangChips(); render();
});
$("#reset").addEventListener("click", () => {
  state.q=""; state.lang=""; state.type="all"; state.sort="updated";
  $("#search").value=""; $("#lang").value=""; $("#sort").value="updated";
  document.querySelectorAll("#typeChips > .chip").forEach(c=>c.classList.toggle("on", c.dataset.type==="all"));
  syncLangChips(); render();
});

// card click / keyboard
grid.addEventListener("click", e => {
  const favBtn = e.target.closest(".fav-btn");
  if(favBtn){ e.preventDefault(); toggleFav(favBtn.dataset.fav); return; }
  const card = e.target.closest(".card"); if(!card) return;
  if(e.target.closest("a")) return;            // let real links work
  window.open(card.dataset.url, "_blank", "noopener");
});
grid.addEventListener("keydown", e => {
  if(e.key !== "Enter" && e.key !== " ") return;
  if(e.target.closest("button") || e.target.closest("a")) return;
  const card = e.target.closest(".card"); if(!card) return;
  e.preventDefault(); window.open(card.dataset.url, "_blank", "noopener");
});

// keyboard shortcuts
document.addEventListener("keydown", e => {
  if(e.key === "/" && document.activeElement !== $("#search")){ e.preventDefault(); $("#search").focus(); }
  if(e.key === "Escape"){ $("#search").blur(); if($("#search").value){ $("#search").value=""; state.q=""; render(); } }
});

// back to top
const toTop = $("#toTop");
addEventListener("scroll", () => toTop.classList.toggle("show", scrollY > 600));
toTop.addEventListener("click", () => scrollTo({top:0,behavior:"smooth"}));

// init: favorites + storage-mode notice
syncFavUI();
setNotice("Favorites saved on this device only — cloud sync is not enabled", false);
render();
</script>
</body>
</html>
"""


def main():
    data = load()
    data["generated_at"] = data.get("generated_at") or datetime.datetime.now().astimezone().isoformat()
    title = data.get("user", "GitHub")
    login = data.get("user", "github")
    payload = json.dumps(
        {"user": login, "generated_at": data["generated_at"], "count": data["count"], "repos": data["repos"]},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    out = (
        TEMPLATE
        .replace("__REPOS_JSON__", payload)
        .replace("__TITLE__", html_mod.escape(title))
        .replace("__LOGIN__", html_mod.escape(login))
    )
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {OUT_FILE} ({len(out):,} bytes, {data['count']} repos embedded)")


if __name__ == "__main__":
    main()
