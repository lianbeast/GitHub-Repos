# GitHub Repo Browser

A single-page, self-contained browser for every public repository on the
[lianbeast](https://github.com/lianbeast) GitHub account — 147 repos at the time of
generation (8 original, 139 forks).

`index.html` is a **standalone file**: the repository data is embedded, so it opens
directly from disk with no server, no build step and no dependencies.

## Features

- Instant search across name, description, topics and language (press `/` to focus, `Esc` to clear)
- Filters: All / Mine / Forks / Has Pages / Stale / ★ Favorites, plus a language dropdown and quick-pick chips
- Sorting: recently updated, recently pushed, name, stars, size, most behind upstream
- Each card shows language (with a GitHub-style color dot), stars, forks, last-updated time,
  a direct link, and a **Live** badge when the repo has a homepage
- **Fork drift** — every fork shows how far behind its upstream it is, with a one-click link
  to the exact compare view (see [Fork sync status](#fork-sync-status-in-the-browser))
- **Report panel** — one button summarises fork health, lists everything behind, and turns
  your tick-box selection into the exact `refresh_forks.py` command to run
- **Favorites** — save repos with the Save/Saved toggle and filter down to your list
- Responsive grid, collapses to a single column on mobile

## Files

| File | Purpose |
|---|---|
| `index.html` | The page — generated, self-contained, open it directly |
| `repos.json` | Raw repo data pulled from the GitHub API |
| `fetch_repos.py` | Refreshes `repos.json` from the GitHub REST API (add `--check-drift` for fork sync status) |
| `build_page.py` | Injects `repos.json` into the HTML template → `index.html` |
| `sync_forks.py` | Bulk-syncs every fork in the account with its upstream |
| `refresh_forks.py` | One-shot pass: sync forks → refresh drift → rebuild the page |
| `gh_token.py` | Resolves the GitHub token; `--install` stores it in `~/.github-token` |

## Refreshing the data

```bash
python fetch_repos.py   # re-fetch all public repos -> repos.json
python build_page.py    # regenerate index.html from repos.json
```

`generated_at` is stamped when the data is *fetched*, and it is what the page
footer shows — so the footer date always describes the data, not the last build.

No third-party packages are needed — both scripts use only the standard library.

> Note: the GitHub search API only indexes a handful of these repos, so
> `fetch_repos.py` reads the paginated `/users/<user>/repos` REST endpoint instead.

## Fork sync status in the browser

139 of the 147 repos here are forks, so drift is the question that actually
matters. Plain `fetch_repos.py` does not answer it — the list endpoint omits the
`parent` relationship entirely. Run the opt-in pass instead:

```bash
GITHUB_TOKEN=… python fetch_repos.py --check-drift
python build_page.py
```

Every fork card then gains a pill:

| Pill | Meaning |
|---|---|
| `Up to date` | fork matches upstream |
| `42 behind` | upstream has 42 commits the fork does not — links to the exact compare view |
| `3 behind · 2 ahead` | the fork also carries local commits of its own |
| `Needs attention` | merge conflict, or a default branch that differs from upstream's |
| `Check failed` | the compare call errored (rate limit, permissions) |

The pass costs **two API requests per fork** (one for `parent`, one for the
comparison), so it is deliberately opt-in: plain `fetch_repos.py` stays fast and
needs no token. It reuses `sync_forks.py` for auth, parallelism and the compare
call rather than duplicating that logic, so it takes the same `--token` /
`GITHUB_TOKEN` / `GH_TOKEN` and `--jobs` arguments.

When the pass has never been run, the **Stale** filter, the **Most behind** sort
and the **Behind upstream** stat stay hidden and a note appears above the grid —
no dead controls. The footer records when the drift data was last checked.

The browser stays read-only. To actually *sync* a fork, use `sync_forks.py` below.

## Syncing your forks with upstream

`sync_forks.py` does in one pass what GitHub's "Sync fork" button does one repo at a
time. It needs a token — pass `--token`, or set `GITHUB_TOKEN` / `GH_TOKEN`.

```bash
# 1. What is out of date? Read-only, changes nothing.
python sync_forks.py

# 2. See exactly what would happen.
python sync_forks.py --apply --dry-run

# 3. Do it.
python sync_forks.py --apply
```

| Flag | Effect |
|---|---|
| *(none)* | **Check only** — reports how far behind upstream each fork is |
| `--apply` | Actually sync, via `POST /repos/{owner}/{repo}/merge-upstream` |
| `--dry-run` | With `--apply`, report what would change without changing it |
| `--only a,b` / `--exclude a,b` | Limit to / skip named repos |
| `--branch <name>` | Sync a specific branch instead of each fork's default |
| `--limit N` | Stop after N forks |
| `--jobs N` | Parallel requests (default 6) |
| `--json` | Machine-readable summary |

**Reading the output**

| Mark | Meaning |
|---|---|
| `+` | Synced successfully |
| `v` | Behind upstream (check mode) / would sync (dry run) |
| `=` | Already up to date |
| `?` | Branch mismatch — your default branch differs from upstream's, so it is skipped |
| `-` | Skipped — archived, or the branch does not exist upstream |
| `!` | Error — e.g. a merge conflict that needs resolving by hand |

A fork with local commits of its own will still sync (GitHub merges rather than
fast-forwards), but a conflicting one comes back as `!` and is left untouched.

> The token needs the `repo` scope (classic) or Contents read/write (fine-grained).
> See [Tokens](#tokens) for how it is resolved; it is never written into the
> repository, a commit, git config or a remote URL.


## Keeping it current

Drift on this account accumulates fast — the behind count went 7 → 14 in two
hours on one occasion, because several upstreams (transformers, mastra,
obsidian-releases) are very active. `refresh_forks.py` wraps the whole cycle:

```bash
python refresh_forks.py                       # sync behind forks, refresh data, rebuild
python refresh_forks.py --dry-run             # report what would sync; changes nothing
python refresh_forks.py --skip-sync           # refresh data + rebuild only (read-only)
python refresh_forks.py --only mastra,orca    # sync just these, leave the rest
python refresh_forks.py --exclude watermelon-platform
```

It runs, in order, `sync_forks.py --apply` → `fetch_repos.py --check-drift` →
`build_page.py`, then prints a summary: how many forks it synced and which,
what is still behind, and anything needing manual attention.

### Report first, sync on request

Three scheduled runs a day — **00:00, 06:00 and 12:00** — invoke it with
`--skip-sync`, so they are strictly read-only. They refresh the drift data,
rebuild the page, and report what is behind. Nothing is synced, committed or
pushed on a schedule.

Acting on a report is explicit:

```bash
python refresh_forks.py --only OfficeCLI,mastra   # just these
python refresh_forks.py                           # everything that is behind
```

Three automations rather than one, because the scheduler takes a single hour
per rule — `BYHOUR=0,6,12` is rejected.

The same report is available without leaving the page. The **Report** button in
the toolbar summarises fork health, lists everything behind worst-first with a
compare link on each row, and separates out the forks that need manual
attention. Tick the ones you want and it builds the matching command —
`python refresh_forks.py --only …` — ready to copy. With nothing ticked it
offers the sync-everything command instead. It can also download the whole
report as Markdown.

The page stays read-only: it holds no token, so it can report but never sync.

> A run aborts without touching anything if no token can be found — see
> [Tokens](#tokens) for where it looks.
>
> Under Wine this is the only sane route — Windows Task Scheduler isn't
> available, and a dotfile in the Wine prefix is not the same file as the one
> in your Linux home.

## Tokens

Every script resolves the GitHub token the same way, in this order:

1. `--token <value>`
2. `$GITHUB_TOKEN`
3. `$GH_TOKEN`
4. a token file — `$GITHUB_TOKEN_FILE`, else `~/.github-token`,
   else `~/.config/github-token`

The file holds a bare token, or `GITHUB_TOKEN=...`; blank lines and `#` comments
are ignored. Store the token you already have in the environment with:

```bash
python gh_token.py --install    # writes ~/.github-token, mode 600
python gh_token.py              # report which source wins (token masked)
```

**Prefer the file for anything unattended.** An exported variable only reaches a
process if the shell that launched it exported it — fragile for a scheduled job.
The file is read directly by the script, so it does not matter how the parent
process was started.

The token needs the `repo` scope (classic) or Contents read/write (fine-grained),
and is never written into the repository, a commit, git config or a remote URL.

> On Windows/Wine the `600` mode is cosmetic — NTFS ACLs, not the POSIX mode,
> govern who can read the file. Keep it in a home directory that isn't synced
> or shared.

## Favorites storage

Favorites are stored in the browser's `localStorage` under the key `ghb.favorites.v1`.
They are **device-scoped** — saved on the machine you're using, not synced across
devices, and there is no login identity. Cloud sync is not enabled in this build.
