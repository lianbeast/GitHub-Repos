#!/usr/bin/env python3
"""Fetch all public repositories for a GitHub user and write a compact repos.json.

Pass --check-drift to also record, for every fork, how far behind its upstream it
is. That pass reuses the compare logic in sync_forks.py and needs a token.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

USER = "lianbeast"
OUT = "repos.json"


def fetch_all(user, token=None):
    repos = []
    page = 1
    headers = {
        "User-Agent": "repo-browser",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    while True:
        url = (
            f"https://api.github.com/users/{user}/repos"
            f"?per_page=100&page={page}&sort=updated&direction=desc"
        )
        req = urllib.request.Request(url, headers=headers)
        data = json.load(urllib.request.urlopen(req))
        if not data:
            break
        repos += data
        if len(data) < 100:
            break
        page += 1
    return repos


def simplify(r):
    # The list endpoint omits `parent`, so these stay empty until --check-drift
    # resolves them one repo at a time.
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
        # --- fork sync, filled in by --check-drift ---
        "upstream": parent.get("full_name") or "",
        "upstream_branch": parent.get("default_branch") or "",
        "drift_status": "",          # "" | ok | behind | warn | skip | error
        "behind": None,
        "ahead": None,
        "drift_detail": "",
        "drift_checked_at": None,
    }


def check_drift(repos, token, jobs=6):
    """Annotate every fork with its upstream drift.

    Reuses sync_forks.py rather than reimplementing auth, pagination and the
    compare call. Costs two requests per fork (one for `parent`, one for the
    comparison), so it is deliberately opt-in.
    """
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

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    repos = fetch_all(args.user, token)
    out = [simplify(r) for r in repos]

    if args.check_drift:
        if not token:
            print("error: --check-drift needs a token. Pass --token or set "
                  "GITHUB_TOKEN / GH_TOKEN.", file=sys.stderr)
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
    print(f"Wrote {len(out)} repos to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
