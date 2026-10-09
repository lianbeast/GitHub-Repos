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
<meta name="color-scheme" content="dark light">
<meta name="theme-color" content="#0a0d14">
<meta name="description" content="Browse, search and filter every public GitHub repository on the __LOGIN__ account.">
<title>__TITLE__ · Repository Browser</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%236f8cff'%3E%3Cpath d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z'/%3E%3C/svg%3E">
<script>
/* Resolve the colour scheme before first paint so there is no flash. */
(function () {
  try {
    var t = localStorage.getItem("ghb.theme");
    if (t !== "light" && t !== "dark") {
      t = (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) ? "light" : "dark";
    }
    document.documentElement.setAttribute("data-theme", t);
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "dark");
  }
})();
</script>
<style>
/* ==========================================================================
   1. Design tokens
   ========================================================================== */
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto,
               "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
               "Liberation Mono", monospace;

  --r-xs: 6px;  --r-sm: 9px;  --r-md: 13px; --r-lg: 18px; --r-full: 999px;

  --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px; --sp-5: 20px;
  --sp-6: 24px; --sp-7: 32px; --sp-8: 44px; --sp-9: 64px;

  --dur-fast: .13s;
  --dur: .2s;
  --ease: cubic-bezier(.4, 0, .2, 1);
}

html[data-theme="dark"] {
  --bg: #0a0d14;
  --glow-1: rgba(111, 140, 255, .16);
  --glow-2: rgba(167, 139, 250, .12);
  --surface: #121826;
  --surface-2: #18202f;
  --surface-3: #1d2637;
  --card: #111725;
  --card-hover: #172033;
  --border: #232d40;
  --border-2: #33405a;
  --text: #e9eff8;
  --muted: #a6b5cc;
  --faint: #8394ac;
  --accent: #6f8cff;
  --accent-2: #a78bfa;
  --accent-soft: rgba(111, 140, 255, .14);
  --accent-line: rgba(111, 140, 255, .30);
  --ok: #4ac463;
  --ok-soft: rgba(63, 185, 80, .12);
  --ok-line: rgba(63, 185, 80, .34);
  --warn: #e8ad1a;
  --warn-soft: rgba(227, 160, 8, .12);
  --warn-line: rgba(227, 160, 8, .38);
  --on-accent: #0a0d14;
  --shadow-1: 0 1px 2px rgba(0, 0, 0, .50);
  --shadow-2: 0 12px 32px -14px rgba(0, 0, 0, .78);
  --ring: rgba(111, 140, 255, .55);
}

html[data-theme="light"] {
  --bg: #f5f7fb;
  --glow-1: rgba(59, 91, 219, .10);
  --glow-2: rgba(112, 72, 232, .08);
  --surface: #ffffff;
  --surface-2: #f3f6fc;
  --surface-3: #e9eef8;
  --card: #ffffff;
  --card-hover: #fbfcff;
  --border: #dde3ee;
  --border-2: #b7c3d8;
  --text: #0f1622;
  --muted: #48566a;
  --faint: #5c6a7e;
  --accent: #2f4fc4;
  --accent-2: #6b3fd4;
  --accent-soft: rgba(47, 79, 196, .09);
  --accent-line: rgba(47, 79, 196, .28);
  --ok: #14702f;
  --ok-soft: rgba(26, 127, 55, .09);
  --ok-line: rgba(26, 127, 55, .30);
  --warn: #7d5800;
  --warn-soft: rgba(154, 103, 0, .10);
  --warn-line: rgba(154, 103, 0, .32);
  --on-accent: #ffffff;
  --shadow-1: 0 1px 2px rgba(16, 24, 40, .06);
  --shadow-2: 0 14px 34px -16px rgba(16, 24, 40, .30);
  --ring: rgba(47, 79, 196, .40);
}

/* ==========================================================================
   2. Base
   ========================================================================== */
*, *::before, *::after { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  letter-spacing: -0.005em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(920px 520px at 10% -10%, var(--glow-1), transparent 62%),
    radial-gradient(820px 500px at 95% -14%, var(--glow-2), transparent 64%);
}

h1, h2, h3 { margin: 0; font-weight: 700; letter-spacing: -0.022em; line-height: 1.22; }
p { margin: 0; }
a { color: inherit; }
button, input, select { font: inherit; color: inherit; }
svg { display: block; }

:where(a, button, input, select, [tabindex]):focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: var(--r-xs);
}

.sr-only {
  position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}

.skip-link {
  position: absolute; top: var(--sp-3); left: var(--sp-3);
  z-index: 100;
  transform: translateY(-200%);
  padding: 10px 16px;
  background: var(--accent);
  color: var(--on-accent);
  font-weight: 650; font-size: .9rem;
  border-radius: var(--r-sm);
  text-decoration: none;
  transition: transform var(--dur) var(--ease);
}
.skip-link:focus { transform: none; }

.wrap {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 clamp(16px, 4vw, 32px) var(--sp-9);
}

/* ==========================================================================
   3. Hero
   ========================================================================== */
.hero { padding: clamp(32px, 6vw, 60px) 0 var(--sp-6); }

.hero-top {
  display: flex;
  align-items: flex-start;
  gap: clamp(14px, 2.4vw, 22px);
  flex-wrap: wrap;
}

.avatar {
  width: clamp(56px, 8vw, 72px);
  height: clamp(56px, 8vw, 72px);
  border-radius: 50%;
  flex: 0 0 auto;
  border: 1px solid var(--border-2);
  box-shadow: 0 0 0 5px var(--accent-soft), var(--shadow-1);
}

.hero-text { flex: 1 1 320px; min-width: 0; }

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-bottom: var(--sp-2);
  font-family: var(--font-mono);
  font-size: .76rem;
  font-weight: 600;
  letter-spacing: .09em;
  text-transform: uppercase;
  color: var(--accent);
  text-decoration: none;
}
.eyebrow:hover { text-decoration: underline; text-underline-offset: 3px; }
.eyebrow svg { width: 14px; height: 14px; fill: currentColor; }

h1 { font-size: clamp(1.65rem, 1.15rem + 2vw, 2.35rem); }

.lede {
  margin-top: var(--sp-3);
  max-width: 64ch;
  font-size: clamp(.94rem, .9rem + .2vw, 1.06rem);
  color: var(--muted);
}

/* ==========================================================================
   4. Stat cards
   ========================================================================== */
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  gap: var(--sp-3);
  margin-top: var(--sp-6);
  list-style: none;
  padding: 0;
}

.stat {
  padding: var(--sp-4) var(--sp-5);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-1);
}

.stat-n {
  font-size: clamp(1.25rem, 1.05rem + .6vw, 1.55rem);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.stat-l {
  margin-top: 2px;
  font-size: .73rem;
  font-weight: 600;
  letter-spacing: .07em;
  text-transform: uppercase;
  color: var(--faint);
}

/* ==========================================================================
   5. Toolbar
   ========================================================================== */
.toolbar {
  position: sticky;
  top: 0;
  z-index: 30;
  margin-bottom: var(--sp-5);
  padding: var(--sp-3);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-1);
  transition: box-shadow var(--dur) var(--ease), border-color var(--dur) var(--ease);
}
@supports (backdrop-filter: blur(4px)) {
  .toolbar {
    background: color-mix(in srgb, var(--bg) 88%, transparent);
    backdrop-filter: blur(16px) saturate(140%);
    -webkit-backdrop-filter: blur(16px) saturate(140%);
  }
}
.toolbar.is-stuck {
  border-color: var(--border-2);
  box-shadow: var(--shadow-2);
}

.field-row {
  display: flex;
  gap: var(--sp-2);
  flex-wrap: wrap;
  align-items: stretch;
}

.search-box { position: relative; flex: 1 1 300px; min-width: 200px; }

.search-ico {
  position: absolute;
  left: 13px; top: 50%;
  transform: translateY(-50%);
  width: 16px; height: 16px;
  fill: var(--faint);
  pointer-events: none;
}

#search {
  width: 100%;
  height: 44px;
  padding: 0 74px 0 38px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  color: var(--text);
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
#search::placeholder { color: var(--faint); }
#search:hover { border-color: var(--border-2); }
#search:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--ring);
}
#search::-webkit-search-cancel-button { display: none; }

.clear-input {
  position: absolute;
  right: 42px; top: 50%;
  transform: translateY(-50%);
  display: grid; place-items: center;
  width: 24px; height: 24px;
  padding: 0;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--r-full);
  color: var(--muted);
  cursor: pointer;
  transition: background var(--dur-fast), color var(--dur-fast);
}
.clear-input:hover { background: var(--surface-3); color: var(--text); }
.clear-input svg { width: 11px; height: 11px; fill: currentColor; }

.kbd {
  position: absolute;
  right: 12px; top: 50%;
  transform: translateY(-50%);
  padding: 2px 7px;
  font-family: var(--font-mono);
  font-size: .7rem;
  color: var(--faint);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--r-xs);
  pointer-events: none;
}

select {
  height: 44px;
  padding: 0 34px 0 13px;
  appearance: none;
  background-color: var(--bg);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%238394ac'%3E%3Cpath d='M4.4 6.2 8 9.8l3.6-3.6.9.9L8 11.6 3.5 7.1z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 11px center;
  background-size: 15px;
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  color: var(--text);
  cursor: pointer;
  max-width: 100%;
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
select:hover { border-color: var(--border-2); }
select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--ring); }

.icon-btn {
  display: grid; place-items: center;
  width: 44px; height: 44px;
  flex: 0 0 auto;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  color: var(--muted);
  cursor: pointer;
  transition: background var(--dur-fast), color var(--dur-fast), border-color var(--dur-fast);
}
.icon-btn:hover { background: var(--surface-2); color: var(--text); border-color: var(--border-2); }
.icon-btn svg { width: 17px; height: 17px; fill: currentColor; }
html[data-theme="dark"] .i-moon { display: none; }
html[data-theme="light"] .i-sun { display: none; }

/* ==========================================================================
   6. Filter chips
   ========================================================================== */
.chips {
  display: flex;
  gap: var(--sp-2);
  flex-wrap: wrap;
  align-items: center;
  margin-top: var(--sp-3);
}

.chips-sep { width: 1px; height: 22px; background: var(--border); flex: 0 0 auto; }

.chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r-full);
  color: var(--muted);
  font-size: .84rem;
  font-weight: 550;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  transition: background var(--dur-fast), color var(--dur-fast),
              border-color var(--dur-fast), transform var(--dur-fast);
}
.chip:hover { color: var(--text); border-color: var(--border-2); background: var(--surface-2); }
.chip:active { transform: scale(.97); }
.chip[aria-pressed="true"] {
  color: var(--on-accent);
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border-color: transparent;
  box-shadow: 0 4px 14px -7px var(--accent);
}
.chip .cnt { font-variant-numeric: tabular-nums; font-size: .78rem; opacity: .72; }
.chip .dot { width: 9px; height: 9px; border-radius: 50%; flex: 0 0 auto; }

/* ==========================================================================
   7. Result count + notices
   ========================================================================== */
.result-count { margin: 0 var(--sp-1) var(--sp-3); font-size: .9rem; color: var(--muted); }
.result-count b { color: var(--text); font-variant-numeric: tabular-nums; }

.meta-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
  margin: 0 var(--sp-1) var(--sp-4);
}

.notice {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  font-size: .79rem;
  color: var(--muted);
  background: var(--warn-soft);
  border: 1px solid var(--warn-line);
  border-radius: var(--r-full);
}
.notice .dot { width: 7px; height: 7px; flex: 0 0 auto; border-radius: 50%; background: var(--warn); }
.notice[hidden] { display: none; }

.reset-btn {
  margin-left: auto;
  padding: 7px 14px;
  font-size: .84rem;
  font-weight: 550;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-line);
  border-radius: var(--r-full);
  cursor: pointer;
  transition: background var(--dur-fast);
}
.reset-btn:hover { background: var(--surface-3); }
.reset-btn[hidden] { display: none; }

/* ==========================================================================
   8. Card grid
   ========================================================================== */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 330px), 1fr));
  gap: var(--sp-4);
  list-style: none;
  padding: 0;
  margin: 0;
}

.card {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--sp-5);
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-1);
  overflow: hidden;
  transition: transform var(--dur) var(--ease), border-color var(--dur) var(--ease),
              background var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}

.card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

@media (hover: hover) {
  .card:hover {
    transform: translateY(-3px);
    background: var(--card-hover);
    border-color: var(--border-2);
    box-shadow: var(--shadow-2);
  }
  .card:hover::before { opacity: 1; }
}
.card:focus-within { border-color: var(--border-2); box-shadow: var(--shadow-2); }
.card:focus-within::before { opacity: 1; }

.card-head { display: flex; align-items: flex-start; gap: var(--sp-3); }

.repo-title {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.02rem;
}
.repo-title .ico { width: 16px; height: 16px; fill: var(--faint); flex: 0 0 auto; }
.repo-title a {
  min-width: 0;
  color: var(--text);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.repo-title a:hover { color: var(--accent); text-decoration: underline; text-underline-offset: 3px; }
.repo-title a::after {
  /* Stretched link: the whole card is clickable without adding a second tab stop. */
  content: "";
  position: absolute;
  inset: 0;
}

.card-actions {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
}

.badge {
  padding: 3px 9px;
  font-size: .68rem;
  font-weight: 650;
  letter-spacing: .05em;
  text-transform: uppercase;
  color: var(--faint);
  border: 1px solid var(--border);
  border-radius: var(--r-full);
}
.badge.fork { color: var(--accent-2); border-color: var(--accent-line); background: var(--accent-soft); }
.badge.archived { color: var(--warn); border-color: var(--warn-line); background: var(--warn-soft); }

.fav-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--r-full);
  color: var(--faint);
  font-size: .73rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background var(--dur-fast), color var(--dur-fast), border-color var(--dur-fast);
}
.fav-btn svg { width: 12px; height: 12px; fill: currentColor; }
.fav-btn:hover { color: var(--warn); border-color: var(--warn-line); background: var(--warn-soft); }
.fav-btn[aria-pressed="true"] {
  color: var(--warn);
  border-color: var(--warn-line);
  background: var(--warn-soft);
}

.desc {
  margin-top: var(--sp-3);
  font-size: .9rem;
  color: var(--muted);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.desc.is-empty { color: var(--faint); font-style: italic; }

.topics { display: flex; gap: 6px; flex-wrap: wrap; margin-top: var(--sp-3); }
.topic {
  padding: 2px 9px;
  font-size: .72rem;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-line);
  border-radius: var(--r-full);
}

.card-foot {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: var(--sp-4);
  font-size: .79rem;
  color: var(--muted);
}

.foot-item { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
.foot-item svg { width: 13px; height: 13px; fill: currentColor; opacity: .8; }

.lang-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex: 0 0 auto;
  box-shadow: inset 0 0 0 1px rgba(127, 127, 127, .35);
}

.live {
  position: relative;
  z-index: 1;
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  font-size: .78rem;
  font-weight: 650;
  color: var(--ok);
  background: var(--ok-soft);
  border: 1px solid var(--ok-line);
  border-radius: var(--r-full);
  text-decoration: none;
  transition: background var(--dur-fast);
}
.live:hover { background: var(--surface-3); }
.live svg { width: 12px; height: 12px; fill: currentColor; }

/* ==========================================================================
   9. Empty state
   ========================================================================== */
.empty {
  grid-column: 1 / -1;
  padding: var(--sp-9) var(--sp-5);
  text-align: center;
  color: var(--muted);
  background: var(--surface);
  border: 1px dashed var(--border-2);
  border-radius: var(--r-lg);
  list-style: none;
}
.empty svg { width: 40px; height: 40px; fill: var(--faint); margin: 0 auto var(--sp-4); opacity: .7; }
.empty h2 { font-size: 1.05rem; margin-bottom: 6px; }
.empty p { font-size: .9rem; }

/* ==========================================================================
   10. Footer
   ========================================================================== */
.site-foot {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
  margin-top: var(--sp-8);
  padding-top: var(--sp-5);
  border-top: 1px solid var(--border);
  font-size: .83rem;
  color: var(--faint);
}
.site-foot a { color: var(--muted); text-decoration: none; }
.site-foot a:hover { color: var(--accent); text-decoration: underline; text-underline-offset: 3px; }

/* ==========================================================================
   11. Back to top
   ========================================================================== */
.to-top {
  position: fixed;
  right: clamp(14px, 3vw, 26px);
  bottom: clamp(14px, 3vw, 26px);
  z-index: 40;
  display: grid; place-items: center;
  width: 46px; height: 46px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border: none;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 10px 26px -10px var(--accent);
  opacity: 0;
  pointer-events: none;
  transform: translateY(10px);
  transition: opacity var(--dur) var(--ease), transform var(--dur) var(--ease);
}
.to-top.is-visible { opacity: 1; pointer-events: auto; transform: none; }
.to-top svg { width: 18px; height: 18px; fill: var(--on-accent); }

/* ==========================================================================
   12. Responsive
   ========================================================================== */
@media (max-width: 900px) {
  .grid { grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr)); }
}

@media (max-width: 720px) {
  .field-row { gap: 10px; }
  .search-box { flex: 1 1 100%; }
  #search { padding-right: 40px; }
  .kbd { display: none; }
  .clear-input { right: 12px; }
  select { flex: 1 1 140px; }
  .chips { gap: 7px; }
  .chips-sep { display: none; }
  .chip { padding: 6px 12px; font-size: .8rem; }
  .reset-btn { margin-left: 0; }
}

@media (max-width: 480px) {
  .grid { grid-template-columns: 1fr; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .stat { padding: var(--sp-3) var(--sp-4); }
  .card { padding: var(--sp-4); }
  .fav-btn span { display: none; }
  .fav-btn { padding: 5px 8px; }
  .card-foot { gap: var(--sp-3); }
  .live { margin-left: 0; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .001ms !important;
    scroll-behavior: auto !important;
  }
  .card:hover { transform: none; }
}
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to repositories</a>

<div class="wrap">
  <header class="hero">
    <div class="hero-top">
      <img class="avatar" src="https://avatars.githubusercontent.com/u/213338141?v=4"
           alt="" width="72" height="72" loading="lazy" decoding="async">
      <div class="hero-text">
        <a class="eyebrow" href="https://github.com/__LOGIN__" target="_blank" rel="noopener">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
          github.com/__LOGIN__
        </a>
        <h1>Repository Browser</h1>
        <p class="lede" id="lede"></p>
      </div>
    </div>
    <ul class="stats" id="stats"></ul>
  </header>

  <section class="toolbar" id="toolbar" aria-label="Search and filters">
    <div class="field-row">
      <div class="search-box">
        <svg class="search-ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M10.68 11.74a6 6 0 0 1-7.922-8.982 6 6 0 0 1 8.982 7.922l3.04 3.04a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215ZM11.5 7a4.499 4.499 0 1 0-8.997 0A4.499 4.499 0 0 0 11.5 7Z"/></svg>
        <label class="sr-only" for="search">Search repositories</label>
        <input id="search" type="search" placeholder="Search by name, description or topic…"
               autocomplete="off" spellcheck="false">
        <button class="clear-input" id="clearSearch" type="button" aria-label="Clear search" hidden>
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"/></svg>
        </button>
        <span class="kbd" aria-hidden="true">/</span>
      </div>
      <label class="sr-only" for="lang">Filter by language</label>
      <select id="lang"><option value="">All languages</option></select>
      <label class="sr-only" for="sort">Sort repositories</label>
      <select id="sort">
        <option value="updated">Recently updated</option>
        <option value="pushed">Recently pushed</option>
        <option value="name">Name (A–Z)</option>
        <option value="stars">Most stars</option>
        <option value="size">Largest</option>
      </select>
      <button class="icon-btn" id="themeToggle" type="button" aria-label="Switch to light theme" title="Toggle colour theme">
        <svg class="i-sun" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm0-1.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5ZM8 0a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0V.75A.75.75 0 0 1 8 0Zm0 13a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 8 13ZM2.34 2.34a.75.75 0 0 1 1.06 0l1.06 1.06a.75.75 0 0 1-1.06 1.06L2.34 3.4a.75.75 0 0 1 0-1.06Zm9.2 9.2a.75.75 0 0 1 1.06 0l1.06 1.06a.75.75 0 1 1-1.06 1.06l-1.06-1.06a.75.75 0 0 1 0-1.06ZM16 8a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 16 8ZM3 8a.75.75 0 0 1-.75.75H.75a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 3 8Zm10.6-5.66a.75.75 0 0 1 0 1.06l-1.06 1.06a.75.75 0 1 1-1.06-1.06l1.06-1.06a.75.75 0 0 1 1.06 0ZM5.46 10.54a.75.75 0 0 1 0 1.06L4.4 12.66a.75.75 0 0 1-1.06-1.06l1.06-1.06a.75.75 0 0 1 1.06 0Z"/></svg>
        <svg class="i-moon" viewBox="0 0 16 16" aria-hidden="true"><path d="M9.6 1.2a.75.75 0 0 1 .2.83 5.5 5.5 0 0 0 6.77 7.2.75.75 0 0 1 .93 1A7 7 0 1 1 8.77.28a.75.75 0 0 1 .83.92Z"/></svg>
      </button>
    </div>

    <div class="chips" id="typeChips" role="group" aria-label="Repository type filters">
      <button type="button" class="chip" data-type="all" aria-pressed="true">All <span class="cnt"></span></button>
      <button type="button" class="chip" data-type="owned" aria-pressed="false">Mine <span class="cnt"></span></button>
      <button type="button" class="chip" data-type="fork" aria-pressed="false">Forks <span class="cnt"></span></button>
      <button type="button" class="chip" data-type="pages" aria-pressed="false">Has Pages <span class="cnt"></span></button>
      <button type="button" class="chip" data-type="fav" aria-pressed="false">★ Favorites <span class="cnt"></span></button>
      <span class="chips-sep" aria-hidden="true"></span>
      <span id="langChips" role="group" aria-label="Quick language filters"></span>
    </div>
  </section>

  <p class="result-count" id="count" role="status" aria-live="polite"></p>

  <div class="meta-row">
    <span class="notice" id="storageNotice" hidden><span class="dot" aria-hidden="true"></span><span id="storageNoticeText"></span></span>
    <button class="reset-btn" id="reset" type="button" hidden>Reset filters</button>
  </div>

  <main id="main">
    <ul class="grid" id="grid" aria-label="Repositories"></ul>
  </main>

  <footer class="site-foot">
    <span>Generated <span id="gen"></span> · <span id="total"></span> public repositories</span>
    <span><a href="https://github.com/__LOGIN__?tab=repositories" target="_blank" rel="noopener">Open on GitHub ↗</a></span>
  </footer>
</div>

<button class="to-top" id="toTop" type="button" aria-label="Back to top">
  <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3.5 2.5 9l1.1 1.1L8 5.7l4.4 4.4L13.5 9z"/></svg>
</button>

<script>
"use strict";

const DATA = __REPOS_JSON__;
const REPOS = DATA.repos;

const LANG_COLORS = {
  "Python":"#3572A5","TypeScript":"#3178b6","JavaScript":"#e8c547","HTML":"#e34c26",
  "Rust":"#dea584","Shell":"#89e051","Swift":"#F05138","PHP":"#4F5D95","C++":"#f34b7d",
  "QML":"#44a51c","C#":"#178600","Go":"#00ADD8","CSS":"#563d7c","Vue":"#41b883",
  "Java":"#b07219","Ruby":"#701516","C":"#6e6e6e","Jupyter Notebook":"#DA5B0B",
  "Kotlin":"#A97BFF","Dart":"#00B4AB","Astro":"#ff5a03","Svelte":"#ff3e00",
  "SCSS":"#c6538c","Lua":"#4b6bb5","Perl":"#0298c3","Elixir":"#6e4a7e"
};
const langColor = (l) => LANG_COLORS[l] || "#8b949e";

const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.prototype.slice.call((r || document).querySelectorAll(s));

const grid = $("#grid");
const searchInput = $("#search");
const state = { q: "", lang: "", type: "all", sort: "updated" };

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
try { favs = new Set(JSON.parse(localStorage.getItem(FAV_KEY) || "[]")); } catch (e) { favs = new Set(); }

function saveFavs() {
  try { localStorage.setItem(FAV_KEY, JSON.stringify(Array.from(favs))); return true; }
  catch (e) { return false; }
}
function setNotice(text) {
  const el = $("#storageNotice");
  if (!el) return;
  $("#storageNoticeText").textContent = text || "";
  el.hidden = !text;
}
function syncFavUI() {
  const chip = $('.chip[data-type="fav"]', $("#typeChips"));
  if (chip) $(".cnt", chip).textContent = favs.size;
}
function toggleFav(name) {
  if (favs.has(name)) favs.delete(name); else favs.add(name);
  setNotice(saveFavs()
    ? "Favorites saved on this device only — cloud sync is not enabled"
    : "Could not save — this browser's local storage is unavailable");
  syncFavUI();
  render();
}

/* ---------- helpers ---------- */
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function timeAgo(iso) {
  if (!iso) return "—";
  const s = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);   if (m < 60) return m + "m ago";
  const h = Math.floor(m / 60);   if (h < 24) return h + "h ago";
  const d = Math.floor(h / 24);   if (d < 30) return d + "d ago";
  const mo = Math.floor(d / 30);  if (mo < 12) return mo + "mo ago";
  return Math.floor(mo / 12) + "y ago";
}
const fmtDate = (iso) => iso
  ? new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
  : "";

/* ---------- language filter options ---------- */
const langCounts = {};
REPOS.forEach((r) => { if (r.language) langCounts[r.language] = (langCounts[r.language] || 0) + 1; });
const langsSorted = Object.entries(langCounts)
  .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

const langSel = $("#lang");
langsSorted.forEach(([l, c]) => {
  const o = document.createElement("option");
  o.value = l;
  o.textContent = l + " (" + c + ")";
  langSel.appendChild(o);
});

const langChips = $("#langChips");
langsSorted.slice(0, 6).forEach(([l, c]) => {
  const el = document.createElement("button");
  el.type = "button";
  el.className = "chip";
  el.dataset.lang = l;
  el.setAttribute("aria-pressed", "false");
  el.innerHTML = '<span class="dot" style="background:' + langColor(l) + '"></span>'
    + esc(l) + ' <span class="cnt">' + c + "</span>";
  langChips.appendChild(el);
});

/* ---------- hero stats ---------- */
(function () {
  const total = REPOS.length;
  const owned = REPOS.filter((r) => !r.fork).length;
  const forks = REPOS.filter((r) => r.fork).length;
  const stars = REPOS.reduce((a, r) => a + r.stars, 0);

  $("#lede").textContent = "Browse, search and filter all " + total
    + " public repositories on this account. Save the ones you want to come back to.";

  const stats = [
    [total, "Repositories"], [owned, "Original"], [forks, "Forks"],
    [langsSorted.length, "Languages"], [stars, "Total stars"]
  ];
  $("#stats").innerHTML = stats.map(([n, l]) =>
    '<li class="stat"><div class="stat-n">' + n + '</div><div class="stat-l">' + l + "</div></li>"
  ).join("");

  $("#total").textContent = total;
  $("#gen").textContent = fmtDate(DATA.generated_at) || "—";

  $$('.chip[data-type]', $("#typeChips")).forEach((ch) => {
    const t = ch.dataset.type;
    const c = t === "all" ? total
      : t === "owned" ? owned
      : t === "fork" ? forks
      : t === "fav" ? favs.size
      : REPOS.filter((r) => r.has_pages).length;
    $(".cnt", ch).textContent = c;
  });
})();

/* ---------- filtering / sorting ---------- */
function matches(r) {
  if (state.type === "fav" && !favs.has(r.full_name)) return false;
  if (state.type === "owned" && r.fork) return false;
  if (state.type === "fork" && !r.fork) return false;
  if (state.type === "pages" && !r.has_pages) return false;
  if (state.lang && r.language !== state.lang) return false;
  if (state.q) {
    const hay = (r.name + " " + (r.description || "") + " " +
      (r.topics || []).join(" ") + " " + (r.language || "")).toLowerCase();
    if (!hay.includes(state.q.toLowerCase())) return false;
  }
  return true;
}
function sortFn(a, b) {
  switch (state.sort) {
    case "name":   return a.name.toLowerCase().localeCompare(b.name.toLowerCase());
    case "stars":  return b.stars - a.stars || a.name.localeCompare(b.name);
    case "size":   return b.size - a.size;
    case "pushed": return new Date(b.pushed_at || 0) - new Date(a.pushed_at || 0);
    default:       return new Date(b.updated_at || 0) - new Date(a.updated_at || 0);
  }
}

/* ---------- rendering ---------- */
function card(r) {
  const topics = (r.topics || []).slice(0, 4)
    .map((t) => '<span class="topic">' + esc(t) + "</span>").join("");

  const badge = r.archived
    ? '<span class="badge archived">Archived</span>'
    : r.fork ? '<span class="badge fork">Fork</span>' : "";

  const isFav = favs.has(r.full_name);
  const favBtn = '<button class="fav-btn" type="button" data-fav="' + esc(r.full_name) + '"'
    + ' aria-pressed="' + (isFav ? "true" : "false") + '"'
    + ' aria-label="' + (isFav ? "Remove " : "Save ") + esc(r.name) + (isFav ? " from" : " to") + ' favorites"'
    + ' title="' + (isFav ? "Remove from favorites" : "Add to favorites") + '">'
    + '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>'
    + "<span>" + (isFav ? "Saved" : "Save") + "</span></button>";

  const live = r.homepage
    ? '<a class="live" href="' + esc(r.homepage) + '" target="_blank" rel="noopener">'
      + '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.75 2h3.5a.75.75 0 0 1 0 1.5h-3.5a.25.25 0 0 0-.25.25v8.5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-3.5a.75.75 0 0 1 1.5 0v3.5A1.75 1.75 0 0 1 12.25 14h-8.5A1.75 1.75 0 0 1 2 12.25v-8.5C2 2.784 2.784 2 3.75 2Zm6.5-.25h3.5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0V3.56L9.28 7.28a.751.751 0 0 1-1.06-1.06L11.94 2.5h-1.69a.75.75 0 0 1 0-1.5Z"/></svg>'
      + "Live</a>"
    : "";

  const star = r.stars > 0
    ? '<span class="foot-item" title="' + r.stars + ' stars"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>'
      + "<span>" + r.stars + '</span><span class="sr-only"> stars</span></span>'
    : "";

  const fork = r.forks > 0
    ? '<span class="foot-item" title="' + r.forks + ' forks"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/></svg>'
      + "<span>" + r.forks + '</span><span class="sr-only"> forks</span></span>'
    : "";

  const lang = r.language
    ? '<span class="foot-item"><span class="lang-dot" style="background:' + langColor(r.language)
      + '" aria-hidden="true"></span><span>' + esc(r.language) + "</span></span>"
    : "";

  const upd = '<span class="foot-item" title="Last updated ' + fmtDate(r.updated_at) + '">'
    + '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 8a6.5 6.5 0 1 1 13 0 6.5 6.5 0 0 1-13 0ZM8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0Zm.5 4.75a.75.75 0 0 0-1.5 0v3.5c0 .199.079.39.22.53l2.25 2.25a.751.751 0 0 0 1.06-1.06L8.5 7.94Z"/></svg>'
    + "<span>" + timeAgo(r.updated_at) + '</span><span class="sr-only"> (last updated)</span></span>';

  return '<li class="card">'
    + '<div class="card-head">'
    + '<h2 class="repo-title">'
    + '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"/></svg>'
    + '<a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.name) + "</a>"
    + "</h2>"
    + '<div class="card-actions">' + badge + favBtn + "</div>"
    + "</div>"
    + '<p class="desc' + (r.description ? "" : " is-empty") + '">'
    + (r.description ? esc(r.description) : "No description provided.") + "</p>"
    + (topics ? '<div class="topics">' + topics + "</div>" : "")
    + '<div class="card-foot">' + lang + star + fork + upd + live + "</div>"
    + "</li>";
}

function render() {
  const list = REPOS.filter(matches).sort(sortFn);

  grid.innerHTML = list.length
    ? list.map(card).join("")
    : '<li class="empty">'
      + '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10.68 11.74a6 6 0 0 1-7.922-8.982 6 6 0 0 1 8.982 7.922l3.04 3.04a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215ZM11.5 7a4.499 4.499 0 1 0-8.997 0A4.499 4.499 0 0 0 11.5 7Z"/></svg>'
      + (state.type === "fav" && favs.size === 0
        ? "<h2>No favorites yet</h2><p>Use the Save button on any repository to start your list.</p>"
        : "<h2>No repositories found</h2><p>Try a different search term, or reset the filters.</p>")
      + "</li>";

  $("#count").innerHTML = "<b>" + list.length + "</b> of " + REPOS.length + " repositories";

  const dirty = state.q || state.lang || state.type !== "all" || state.sort !== "updated";
  $("#reset").hidden = !dirty;
  syncFavUI();
}

/* ---------- theme ---------- */
const themeToggle = $("#themeToggle");
function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  try { localStorage.setItem("ghb.theme", t); } catch (e) { /* storage unavailable */ }
  themeToggle.setAttribute("aria-label",
    t === "dark" ? "Switch to light theme" : "Switch to dark theme");
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", t === "dark" ? "#0a0d14" : "#f5f7fb");
}
themeToggle.addEventListener("click", () => {
  applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
});

/* ---------- events ---------- */
let debounceId;
searchInput.addEventListener("input", (e) => {
  $("#clearSearch").hidden = !e.target.value;
  clearTimeout(debounceId);
  const v = e.target.value;
  debounceId = setTimeout(() => { state.q = v.trim(); render(); }, 90);
});
$("#clearSearch").addEventListener("click", () => {
  searchInput.value = "";
  state.q = "";
  $("#clearSearch").hidden = true;
  render();
  searchInput.focus();
});
$("#lang").addEventListener("change", (e) => { state.lang = e.target.value; syncLangChips(); render(); });
$("#sort").addEventListener("change", (e) => { state.sort = e.target.value; render(); });

function syncLangChips() {
  $$("#langChips .chip").forEach((c) => {
    c.setAttribute("aria-pressed", String(c.dataset.lang === state.lang));
  });
}

$("#typeChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip[data-type]");
  if (!chip) return;
  state.type = chip.dataset.type;
  $$('.chip[data-type]', $("#typeChips")).forEach((c) =>
    c.setAttribute("aria-pressed", String(c === chip)));
  render();
});

langChips.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  state.lang = state.lang === chip.dataset.lang ? "" : chip.dataset.lang;
  $("#lang").value = state.lang;
  syncLangChips();
  render();
});

$("#reset").addEventListener("click", () => {
  state.q = ""; state.lang = ""; state.type = "all"; state.sort = "updated";
  searchInput.value = "";
  $("#clearSearch").hidden = true;
  $("#lang").value = "";
  $("#sort").value = "updated";
  $$('.chip[data-type]', $("#typeChips")).forEach((c) =>
    c.setAttribute("aria-pressed", String(c.dataset.type === "all")));
  syncLangChips();
  render();
});

grid.addEventListener("click", (e) => {
  const favBtn = e.target.closest(".fav-btn");
  if (favBtn) { e.preventDefault(); toggleFav(favBtn.dataset.fav); }
});

document.addEventListener("keydown", (e) => {
  const el = document.activeElement;
  const typing = el && /^(INPUT|SELECT|TEXTAREA)$/.test(el.tagName);
  if (e.key === "/" && !typing) { e.preventDefault(); searchInput.focus(); return; }
  if (e.key === "Escape") {
    if (searchInput.value) {
      searchInput.value = ""; state.q = ""; $("#clearSearch").hidden = true; render();
    }
    if (el === searchInput) searchInput.blur();
  }
});

/* ---------- sticky toolbar shadow + back to top ---------- */
const toolbar = $("#toolbar");
const toTop = $("#toTop");
let ticking = false;
addEventListener("scroll", () => {
  if (ticking) return;
  ticking = true;
  requestAnimationFrame(() => {
    toolbar.classList.toggle("is-stuck", toolbar.getBoundingClientRect().top <= 1);
    toTop.classList.toggle("is-visible", window.scrollY > 600);
    ticking = false;
  });
}, { passive: true });

toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

/* ---------- init ---------- */
syncLangChips();
syncFavUI();
applyTheme(document.documentElement.getAttribute("data-theme") || "dark");
setNotice("Favorites saved on this device only — cloud sync is not enabled");
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
