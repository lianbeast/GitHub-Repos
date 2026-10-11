#!/usr/bin/env python3
"""Fetch all public repositories for a GitHub user and write a compact repos.json.

Pass --check-drift to also record, for every fork, how far behind its upstream it
is. That pass reuses the compare logic in sync_forks.py and needs a token.
"""
import argparse
import datetime
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from gh_token import resolve_token

USER = "lianbeast"
OUT = "repos.json"
MAX_RETRIES = 4
BASE_DELAY = 1.2
TIMEOUT = 30

_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="([^"]+)"')


def _parse_link_next(headers) -> str | None:
    link = headers.get("Link") or headers.get("link") or ""
    if not link:
        return None
    for url, rel in _LINK_RE.findall(link):
        if rel == "next":
            return url
    return None


def _sleep(attempt: int, retry_after: str | None = None):
    if retry_after:
        try:
            delay = int(retry_after)
            time.sleep(min(delay, 60))
            return
        except ValueError:
            pass
        try:
            delay = float(retry_after)
            time.sleep(min(delay, 60))
            return
        except ValueError:
            pass
    delay = (BASE_DELAY ** attempt) + random.uniform(0, 0.6)
    time.sleep(min(delay, 30))


def _request_json(req: urllib.request.Request, max_retries: int = MAX_RETRIES):
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read()
                headers = resp.headers
                remaining = headers.get("X-RateLimit-Remaining")
                reset = headers.get("X-RateLimit-Reset")
                if remaining == "0" and reset:
                    try:
                        wait = int(reset) - int(time.time()) + 1
                        if 0 < wait < 120:
                            time.sleep(wait)
                    except ValueError:
                        pass
                data = json.loads(raw) if raw else []
                return data, headers
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            headers = e.headers or {}
            status = e.code
            retry_after = headers.get("Retry-After")
            remaining = headers.get("X-RateLimit-Remaining")
            reset = headers.get("X-RateLimit-Reset")
            is_rate = status in (429, 403) and (
                "rate limit" in body.lower()
                or "secondary rate" in body.lower()
                or remaining == "0"
                or retry_after
            )
            is_retryable = status in (429, 500, 502, 503, 504) or is_rate
            if is_retryable and attempt < max_retries:
                if remaining == "0" and reset:
                    try:
                        wait = int(reset) - int(time.time()) + 1
                        if 0 < wait < 120:
                            time.sleep(wait)
                            continue
                    except ValueError:
                        pass
                _sleep(attempt, retry_after)
                last_err = e
                continue
            try:
                payload = json.loads(body) if body else {}
                msg = payload.get("message", e.reason)
            except Exception:
                msg = e.reason
            raise RuntimeError(f"GitHub API {status} {msg}") from None
        except urllib.error.URLError as e:
            if attempt < max_retries:
                _sleep(attempt)
                last_err = e
                continue
            raise RuntimeError(f"network error: {e.reason}") from None
    raise RuntimeError(f"request failed after {max_retries} retries: {last_err}")


def fetch_all(user, token=None):
    repos = []
    page = 1
    headers = {
        "User-Agent": "repo-browser",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    url = f"https://api.github.com/users/{user}/repos?per_page=100&page={page}&sort=updated&direction=desc"
    while url:
        req = urllib.request.Request(url, headers=headers)
        data, resp_headers = _request_json(req)
        if not isinstance(data, list):
            raise RuntimeError(f"unexpected response for {url}: {data!r}")
        if not data:
            break
        repos += data
        nxt = _parse_link_next(resp_headers)
        if nxt:
            url = nxt
        else:
            if len(data) < 100:
                break
            page += 1
            url = f"https://api.github.com/users/{user}/repos?per_page=100&page={page}&sort=updated&direction=desc"
    return repos


def simplify(r):
    parent = r.get("parent") or r.get("source") or {}
    return {
        "name": r.get("name"),
        "full_name": r.get("full_name"),
        "description": r.get("description") or "",
        "language": r.get("language"),
        "url": r.get("html_url"),
        "homepage": r.get("homepage") or "",
        "topics": r.get("topics", []),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "open_issues": r.get("open_issues_count", 0),
        "size": r.get("size", 0),
        "fork": bool(r.get("fork")),
        "archived": bool(r.get("archived")),
        "has_pages": bool(r.get("has_pages")),
        "default_branch": r.get("default_branch", "main"),
        "created_at": r.get("created_at"),
        "updated_at": r.get("updated_at"),
        "pushed_at": r.get("pushed_at"),
        "upstream": parent.get("full_name") or "",
        "upstream_branch": parent.get("default_branch") or "",
        "drift_status": "",
        "behind": None,
        "ahead": None,
        "drift_detail": "",
        "drift_checked_at": None,
    }


def check_drift(repos, token, jobs=6):
    """Annotate every fork with its upstream drift."""
    from sync_forks import Client, check_fork, inspect_fork

    client = Client(token)
    forks = [r for r in repos if r.get("fork")]
    if not forks:
        return 0

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        inspected = list(pool.map(lambda r: inspect_fork(client, r, None), forks))
        checked = list(pool.map(lambda i: check_fork(client, i), inspected))

    by_full = {c["full"]: c for c in checked}
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    found = 0
    for r in repos:
        c = by_full.get(r["full_name"])
        if not c:
            continue
        r["upstream"] = c.get("upstream") or r["upstream"]
        r["upstream_branch"] = c.get("upstream_branch") or r["upstream_branch"]
        r["drift_status"] = c.get("status", "")
        r["behind"] = c.get("behind")
        r["ahead"] = c.get("ahead")
        r["drift_detail"] = c.get("detail", "")
        r["drift_checked_at"] = stamp
        found += 1
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--user", default=USER, help=f"GitHub login (default: {USER})")
    ap.add_argument("--out", default=OUT, help=f"output file (default: {OUT})")
    ap.add_argument("--check-drift", action="store_true",
                    help="also record how far behind upstream each fork is (needs a token)")
    ap.add_argument("--token", help="GitHub token (else $GITHUB_TOKEN / $GH_TOKEN)")
    ap.add_argument("--jobs", type=int, default=6, help="parallel drift requests (default: 6)")
    args = ap.parse_args(argv)

    token, token_source = resolve_token(args.token)

    repos = fetch_all(args.user, token)
    out = [simplify(r) for r in repos]

    if args.check_drift:
        if not token:
            print("error: --check-drift needs a token. Pass --token, set "
                  "GITHUB_TOKEN / GH_TOKEN, or run 'python gh_token.py --install'.",
                  file=sys.stderr)
            return 2
        forks = sum(1 for r in out if r["fork"])
        print(f"Checking drift for {forks} forks (~{forks * 2} API requests)…")
        found = check_drift(out, token, args.jobs)
        print(f"  drift recorded for {found} forks")

    payload = {
        "user": args.user,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(out),
        "repos": out,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(out)} repos to {args.out} ({token_source or 'unauthenticated'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
