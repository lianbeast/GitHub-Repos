#!/usr/bin/env python3
"""Fetch all public repositories for a GitHub user and write a compact repos.json."""
import json
import urllib.request
import sys

USER = "lianbeast"
OUT = "repos.json"


def fetch_all(user):
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{user}/repos"
            f"?per_page=100&page={page}&sort=updated&direction=desc"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "repo-browser",
                "Accept": "application/vnd.github+json",
            },
        )
        data = json.load(urllib.request.urlopen(req))
        if not data:
            break
        repos += data
        if len(data) < 100:
            break
        page += 1
    return repos


def simplify(r):
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
    }


def main():
    repos = fetch_all(USER)
    out = [simplify(r) for r in repos]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {"user": USER, "generated_at": None, "count": len(out), "repos": out},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Wrote {len(out)} repos to {OUT}")


if __name__ == "__main__":
    sys.exit(main())
