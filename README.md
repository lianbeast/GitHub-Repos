# GitHub Repo Browser

A single-page, self-contained browser for every public repository on the
[lianbeast](https://github.com/lianbeast) GitHub account — 143 repos at the time of
generation (7 original, 136 forks).

`index.html` is a **standalone file**: the repository data is embedded, so it opens
directly from disk with no server, no build step and no dependencies.

## Features

- Instant search across name, description, topics and language (press `/` to focus, `Esc` to clear)
- Filters: All / Mine / Forks / Has Pages / ★ Favorites, plus a language dropdown and quick-pick chips
- Sorting: recently updated, recently pushed, name, stars, size
- Each card shows language (with a GitHub-style color dot), stars, forks, last-updated time,
  a direct link, and a **Live** badge when the repo has a homepage
- **Favorites** — save repos with the Save/Saved toggle and filter down to your list
- Responsive grid, collapses to a single column on mobile

## Files

| File | Purpose |
|---|---|
| `index.html` | The page — generated, self-contained, open it directly |
| `repos.json` | Raw repo data pulled from the GitHub API |
| `fetch_repos.py` | Refreshes `repos.json` from the GitHub REST API |
| `build_page.py` | Injects `repos.json` into the HTML template → `index.html` |
| `sync_forks.py` | Bulk-syncs every fork in the account with its upstream |

## Refreshing the data

```bash
python fetch_repos.py   # re-fetch all public repos -> repos.json
python build_page.py    # regenerate index.html from repos.json
```

No third-party packages are needed — both scripts use only the standard library.

> Note: the GitHub search API only indexes a handful of these repos, so
> `fetch_repos.py` reads the paginated `/users/<user>/repos` REST endpoint instead.

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
> It is read from the environment and never written to disk.


## Favorites storage

Favorites are stored in the browser's `localStorage` under the key `ghb.favorites.v1`.
They are **device-scoped** — saved on the machine you're using, not synced across
devices, and there is no login identity. Cloud sync is not enabled in this build.
