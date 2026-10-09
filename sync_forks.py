#!/usr/bin/env python3
"""
sync_forks.py — bulk-sync every fork in your GitHub account with its upstream.

GitHub's own "Sync fork" button works one repository at a time. This does all of
them in one pass, using the REST API:

  * check mode (default) — read-only. Reports how far behind upstream each fork is.
  * apply mode (--apply) — actually syncs, via POST /repos/{owner}/{repo}/merge-upstream.

Auth: a token with the `repo` scope (classic) or Contents read/write (fine-grained).
Supply it with --token, or set GITHUB_TOKEN / GH_TOKEN in the environment.

Examples
--------
    # what is out of date? (safe, makes no changes)
    python sync_forks.py

    # sync everything that is behind
    python sync_forks.py --apply

    # just a couple of repos, and show a machine-readable summary
    python sync_forks.py --only ComfyUI,iptv --json

    # what would happen, without touching anything
    python sync_forks.py --apply --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from gh_token import resolve_token

API = "https://api.github.com"
UA = "sync-forks/1.0"

# Console output on Windows defaults to cp1252; force UTF-8 so the symbols survive.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover - older interpreters / redirected streams
    pass

MARK = {"ok": "=", "behind": "v", "synced": "+", "skip": "-", "error": "!", "warn": "?"}


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
class ApiError(Exception):
    def __init__(self, status, message, payload=None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.payload = payload or {}


class Client:
    def __init__(self, token: str, timeout: int = 30):
        self.token = token
        self.timeout = timeout
        self.remaining = None

    def _request(self, method: str, path: str, body=None):
        url = path if path.startswith("http") else API + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": UA,
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                self._note_limits(resp.headers)
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw = e.read()
            self._note_limits(e.headers)
            try:
                payload = json.loads(raw)
                msg = payload.get("message", e.reason)
            except Exception:
                payload, msg = {}, str(e.reason)
            raise ApiError(e.code, msg, payload) from None
        except urllib.error.URLError as e:
            raise ApiError(0, f"network error: {e.reason}") from None

    def _note_limits(self, headers):
        try:
            self.remaining = int(headers.get("X-RateLimit-Remaining"))
        except (TypeError, ValueError):
            self.remaining = None

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, body=None):
        return self._request("POST", path, body or {})

    def paginate(self, path, key=None):
        """Yield every item from a paginated list endpoint."""
        page, sep = 1, ("&" if "?" in path else "?")
        while True:
            data = self.get(f"{path}{sep}per_page=100&page={page}")
            if key:
                data = data.get(key, [])
            if not data:
                return
            yield from data
            if len(data) < 100:
                return
            page += 1


# --------------------------------------------------------------------------- #
# Core logic
# --------------------------------------------------------------------------- #
def list_forks(client: Client, login: str) -> list[dict]:
    """All repos owned by `login`, filtered to forks."""
    repos = list(client.paginate(f"/users/{login}/repos?type=owner"))
    return [r for r in repos if r.get("fork")]


def inspect_fork(client: Client, repo: dict, override_branch: str | None) -> dict:
    """Fetch upstream details for one fork. The list endpoint omits `parent`."""
    full = repo["full_name"]
    try:
        detail = client.get(f"/repos/{full}")
    except ApiError as e:
        return {"full": full, "name": repo["name"], "status": "error",
                "detail": f"cannot read repo ({e.status} {e.message})"}

    parent = detail.get("parent") or detail.get("source")
    branch = override_branch or detail.get("default_branch") or "main"

    if detail.get("archived"):
        return {"full": full, "name": repo["name"], "branch": branch,
                "status": "skip", "detail": "archived fork"}
    if not parent:
        return {"full": full, "name": repo["name"], "branch": branch,
                "status": "skip", "detail": "no upstream (not a fork)"}

    upstream = parent["full_name"]
    upstream_branch = parent.get("default_branch") or "main"

    if upstream_branch != branch and not override_branch:
        return {"full": full, "name": repo["name"], "branch": branch,
                "upstream": upstream, "status": "warn",
                "detail": f"branch mismatch: yours '{branch}' vs upstream '{upstream_branch}'"}

    return {"full": full, "name": repo["name"], "branch": branch,
            "upstream": upstream, "upstream_branch": upstream_branch, "status": "ready"}


def check_fork(client: Client, item: dict) -> dict:
    """Read-only: how far behind upstream is this fork?"""
    if item["status"] != "ready":
        return item
    owner = item["upstream"].split("/")[0]
    base = f"{owner}:{item['upstream_branch']}"
    try:
        cmp_ = client.get(f"/repos/{item['full']}/compare/{base}...{item['branch']}")
    except ApiError as e:
        if e.status == 404:
            return {**item, "status": "skip", "detail": "branch not found upstream or locally"}
        return {**item, "status": "error", "detail": f"compare failed ({e.status} {e.message})"}

    behind = cmp_.get("behind_by", 0)
    ahead = cmp_.get("ahead_by", 0)
    item = {**item, "behind": behind, "ahead": ahead}
    if behind == 0:
        return {**item, "status": "ok", "detail": "up to date"}
    return {**item, "status": "behind",
            "detail": f"behind by {behind}" + (f", {ahead} local commit(s)" if ahead else "")}


def sync_fork(client: Client, item: dict) -> dict:
    """Apply: ask GitHub to fast-forward the fork's branch from upstream."""
    if item["status"] != "ready":
        return item

    try:
        res = client.post(f"/repos/{item['full']}/merge-upstream",
                          {"branch": item["branch"]})
    except ApiError as e:
        if e.status == 409:
            return {**item, "status": "warn", "detail": "conflict — manual merge needed"}
        if e.status == 404:
            return {**item, "status": "skip", "detail": "upstream branch not found"}
        if e.status == 403 and client.remaining == 0:
            return {**item, "status": "error", "detail": "rate limit hit — re-run later"}
        return {**item, "status": "error", "detail": f"{e.status} {e.message}"}

    merge_type = res.get("merge_type", "unknown")
    if merge_type == "none":
        return {**item, "status": "ok", "detail": "already up to date"}
    return {**item, "status": "synced", "detail": f"synced ({merge_type})"}


# --------------------------------------------------------------------------- #
# Presentation
# --------------------------------------------------------------------------- #
def render(results: list[dict], mode: str, login: str) -> str:
    width = max((len(r["name"]) for r in results), default=10)
    width = min(width, 34)
    lines = []
    for r in sorted(results, key=lambda x: (x["status"] != "behind", x["name"].lower())):
        mark = MARK.get(r["status"], "?")
        name = r["name"][:width].ljust(width)
        up = (r.get("upstream") or "").ljust(30)
        lines.append(f"  {mark}  {name}  {up}  {r.get('detail', '')}")
    return "\n".join(lines)


def summarize(results: list[dict]) -> dict:
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Sync every forked repository in your account with its upstream.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples")[1] if "Examples" in __doc__ else None,
    )
    ap.add_argument("--token", help="GitHub token (else $GITHUB_TOKEN / $GH_TOKEN)")
    ap.add_argument("--apply", action="store_true",
                    help="actually sync forks (default: read-only check)")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --apply, show what would change without changing it")
    ap.add_argument("--only", help="comma-separated repo names to include")
    ap.add_argument("--exclude", help="comma-separated repo names to skip")
    ap.add_argument("--branch", help="sync this branch instead of each fork's default")
    ap.add_argument("--limit", type=int, help="stop after N forks (useful for a trial run)")
    ap.add_argument("--jobs", type=int, default=6, help="parallel requests (default 6)")
    ap.add_argument("--json", action="store_true", help="emit a JSON summary instead")
    args = ap.parse_args(argv)

    token, token_source = resolve_token(args.token)
    if not token:
        print("error: no token. Pass --token, set GITHUB_TOKEN / GH_TOKEN, or run "
              "'python gh_token.py --install'.", file=sys.stderr)
        return 2

    client = Client(token)
    try:
        login = client.get("/user")["login"]
    except ApiError as e:
        print(f"error: token rejected ({e.status} {e.message})", file=sys.stderr)
        return 2

    mode = "apply" if (args.apply and not args.dry_run) else ("dry-run" if args.apply else "check")

    forks = list_forks(client, login)
    if args.only:
        want = {s.strip().lower() for s in args.only.split(",") if s.strip()}
        forks = [f for f in forks if f["name"].lower() in want]
    if args.exclude:
        drop = {s.strip().lower() for s in args.exclude.split(",") if s.strip()}
        forks = [f for f in forks if f["name"].lower() not in drop]
    forks.sort(key=lambda f: f["name"].lower())
    if args.limit:
        forks = forks[: args.limit]

    if not args.json:
        print(f"\nFork sync — {login}")
        print(f"mode: {mode}"
              + ("  (no changes will be made)" if mode != "apply" else "")
              + f"   forks found: {len(forks)}\n")

    started = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        inspected = list(pool.map(lambda f: inspect_fork(client, f, args.branch), forks))
        if args.apply and not args.dry_run:
            results = list(pool.map(lambda i: sync_fork(client, i), inspected))
        else:
            # Read-only: find what is actually behind first, so a dry run
            # reports real work rather than assuming every fork needs syncing.
            results = list(pool.map(lambda i: check_fork(client, i), inspected))
            if args.apply:
                results = [
                    {**r, "detail": "would sync (dry run)"} if r["status"] == "behind" else r
                    for r in results
                ]

    counts = summarize(results)
    elapsed = time.time() - started

    if args.json:
        print(json.dumps({
            "login": login, "mode": mode, "count": len(results),
            "counts": counts, "elapsed_s": round(elapsed, 1),
            "forks": results,
        }, indent=2, ensure_ascii=False))
        return 0

    if results:
        print(render(results, mode, login))
        print()

    order = ["synced", "behind", "ok", "warn", "skip", "error"]
    parts = [f"{counts[k]} {k}" for k in order if counts.get(k)]
    print("summary: " + " · ".join(parts) + f"   ({elapsed:.1f}s)")

    if mode == "check" and counts.get("behind"):
        print(f"\n{counts['behind']} fork(s) are behind. Run with --apply to sync them.")
    if counts.get("error"):
        print("\nSome repos failed — see the ! rows above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
