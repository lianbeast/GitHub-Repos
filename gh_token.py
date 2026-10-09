#!/usr/bin/env python3
"""Resolve a GitHub token, in order of precedence:

  1. an explicit --token argument
  2. $GITHUB_TOKEN
  3. $GH_TOKEN
  4. a token file — $GITHUB_TOKEN_FILE, else ~/.github-token,
     else ~/.config/github-token

The token file holds a bare token, or ``GITHUB_TOKEN=...``; blank lines and
``#`` comments are ignored. Prefer the file for anything that runs unattended:
unlike an exported variable it does not depend on how the parent process was
launched.

    python gh_token.py            # show where a token would come from (masked)
    python gh_token.py --install  # write $GITHUB_TOKEN to ~/.github-token

The token value is never printed.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ENV_VARS = ("GITHUB_TOKEN", "GH_TOKEN")
KEYS = ("GITHUB_TOKEN", "GH_TOKEN", "TOKEN")


def default_file() -> Path:
    return Path.home() / ".github-token"


def token_files() -> list[Path]:
    override = os.environ.get("GITHUB_TOKEN_FILE")
    if override:
        return [Path(override).expanduser()]
    home = Path.home()
    return [home / ".github-token", home / ".config" / "github-token"]


def read_token_file(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            if key.strip().upper() not in KEYS:
                continue
            line = value
        line = line.strip().strip("'\"")
        if line:
            return line
    return None


def resolve_token(cli_token: str | None = None) -> tuple[str | None, str | None]:
    """Return ``(token, source)``; both are ``None`` when nothing is available."""
    if cli_token and cli_token.strip():
        return cli_token.strip(), "--token"
    for var in ENV_VARS:
        val = os.environ.get(var)
        if val and val.strip():
            return val.strip(), "$" + var
    for path in token_files():
        val = read_token_file(path)
        if val:
            return val, str(path)
    return None, None


def masked(token: str | None) -> str:
    if not token:
        return "(none)"
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}…{token[-4:]} ({len(token)} chars)"


def mode_of(path: Path) -> str:
    try:
        return oct(path.stat().st_mode & 0o777)[2:].rjust(3, "0")
    except OSError:
        return "???"


def install() -> int:
    val = None
    for var in ENV_VARS:
        if os.environ.get(var, "").strip():
            val = os.environ[var].strip()
            break
    if not val:
        print(f"error: neither {' nor '.join(ENV_VARS)} is set — nothing to install.",
              file=sys.stderr)
        return 2

    target = default_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(val + "\n", encoding="utf-8")

    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    mode = mode_of(target)

    print(f"Wrote {masked(val)} to {target}")
    if mode == "600":
        print("  permissions: 600")
    else:
        print(f"  permissions: {mode} — could NOT be restricted to 600.")
        print("  Windows/Wine does not enforce POSIX modes: chmod is a no-op and")
        print("  icacls does nothing either. The file is only as private as the")
        print("  directory it lives in, so keep it out of anything synced or shared.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--install", action="store_true",
                    help="write the token from the environment to ~/.github-token")
    args = ap.parse_args(argv)

    if args.install:
        return install()

    token, source = resolve_token()
    print(f"home        : {Path.home()}")
    for path in token_files():
        exists = "exists" if path.is_file() else "missing"
        print(f"token file  : {path}  [{exists}]")
    print(f"env         : " + ", ".join(
        f"{v}={'set' if os.environ.get(v) else 'unset'}" for v in ENV_VARS))
    if token:
        print(f"resolved    : {masked(token)}  from  {source}")
    else:
        print("resolved    : none — set GITHUB_TOKEN, or run: python gh_token.py --install")
    return 0


if __name__ == "__main__":
    sys.exit(main())
