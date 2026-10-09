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

## Refreshing the data

```bash
python fetch_repos.py   # re-fetch all public repos -> repos.json
python build_page.py    # regenerate index.html from repos.json
```

No third-party packages are needed — both scripts use only the standard library.

> Note: the GitHub search API only indexes a handful of these repos, so
> `fetch_repos.py` reads the paginated `/users/<user>/repos` REST endpoint instead.

## Favorites storage

Favorites are stored in the browser's `localStorage` under the key `ghb.favorites.v1`.
They are **device-scoped** — saved on the machine you're using, not synced across
devices, and there is no login identity. Cloud sync is not enabled in this build.
