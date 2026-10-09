#!/usr/bin/env python3
"""One-shot maintenance pass for the repo browser.

  1. sync_forks.py --apply   fast-forward every fork that is behind upstream
  2. fetch_repos.py --check-drift   re-record drift + repo metadata
  3. build_page.py           rebuild the self-contained index.html

Step 1 is skipped with --skip-sync, and --dry-run passes through to
sync_forks.py so nothing is changed on GitHub.

Needs GITHUB_TOKEN (or GH_TOKEN) in the environment.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from gh_token import resolve_token

HERE = Path(__file__).resolve().parent
PY = sys.executable


def step(title: str) -> None:
    print(f"\n=== {title} ===", flush=True)


def run(args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY] + args,
        cwd=str(HERE),
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="pass through to sync_forks.py; reports what would change")
    ap.add_argument("--skip-sync", action="store_true",
                    help="refresh drift data and rebuild only; never touch forks")
    ap.add_argument("--jobs", type=int, default=10, help="parallel requests (default: 10)")
    ap.add_argument("--only", help="comma-separated repo names to sync (the rest are left alone)")
    ap.add_argument("--exclude", help="comma-separated repo names to skip")
    args = ap.parse_args(argv)

    token, token_source = resolve_token()
    if not token:
        print("error: no token. Set GITHUB_TOKEN / GH_TOKEN, or run "
              "'python gh_token.py --install'.", file=sys.stderr)
        return 2

    sync_counts: dict[str, int] = {}
    synced_names: list[str] = []
    sync_failed = False

    if not args.skip_sync:
        scope = ""
        if args.only:
            scope = f" [only: {args.only}]"
        elif args.exclude:
            scope = f" [exclude: {args.exclude}]"
        step("1/3  syncing forks" + (" (dry run)" if args.dry_run else "") + scope)
        cmd = ["sync_forks.py", "--apply", "--jobs", str(args.jobs), "--json"]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.only:
            cmd += ["--only", args.only]
        if args.exclude:
            cmd += ["--exclude", args.exclude]
        p = run(cmd, capture=True)
        try:
            data = json.loads(p.stdout)
            sync_counts = data.get("counts", {})
            synced_names = [f["name"] for f in data.get("forks", [])
                            if f.get("status") == "synced"]
            print(f"  synced {len(synced_names)} · " + " · ".join(
                f"{v} {k}" for k, v in sync_counts.items()))
            if synced_names:
                for n in synced_names:
                    print(f"    + {n}")
        except (json.JSONDecodeError, TypeError):
            print(p.stdout[-2000:] if p.stdout else "(no output)", flush=True)
            print(p.stderr[-2000:] if p.stderr else "", file=sys.stderr)
            sync_failed = True
    else:
        step("1/3  syncing forks — skipped")

    step("2/3  refreshing drift data")
    rc = run(["fetch_repos.py", "--check-drift", "--jobs", str(args.jobs)]).returncode
    fetch_failed = rc != 0

    step("3/3  rebuilding index.html")
    rc = run(["build_page.py"]).returncode
    build_failed = rc != 0

    # --- summary -----------------------------------------------------------
    step("summary")
    try:
        data = json.loads((HERE / "repos.json").read_text(encoding="utf-8"))
        repos = data["repos"]
        counts: dict[str, int] = {}
        for r in repos:
            counts[r["drift_status"]] = counts.get(r["drift_status"], 0) + 1
        behind = sorted([r for r in repos if r["drift_status"] == "behind"],
                        key=lambda r: -(r["behind"] or 0))
        print(f"  data as of   : {data['generated_at']}")
        print(f"  repositories : {len(repos)}")
        print(f"  up to date   : {counts.get('ok', 0)}")
        print(f"  still behind : {counts.get('behind', 0)}")
        if behind:
            for r in behind[:10]:
                tail = f" · {r['ahead']} ahead" if r.get("ahead") else ""
                print(f"      {r['name']:<26} {r['behind']} behind{tail}")
            if len(behind) > 10:
                print(f"      … and {len(behind) - 10} more")
        if counts.get("warn"):
            print(f"  needs manual : {counts['warn']} (conflict or branch mismatch)")
        if counts.get("error"):
            print(f"  errored      : {counts['error']}")
    except Exception as e:
        print(f"  could not summarise repos.json: {e}")

    print(f"  synced this run: {len(synced_names)}")
    print(f"  token source : {token_source}")
    bad = sync_failed or fetch_failed or build_failed
    print("\n" + ("FAILED — see output above" if bad else "OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
