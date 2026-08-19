#!/usr/bin/env python3
"""Publish an Obsidian vault note to this Jekyll (al-folio) blog.

Workflow (explored manually once, now scripted):

  1. Convert an Obsidian note into a Jekyll post under _posts/:
     - map vault frontmatter (time/tags) to the al-folio post template
     - strip the leading H1 (the theme renders the title from frontmatter)
     - turn [N] citations in the body into links jumping to the reference
       list, and add <a id="ref-N"></a> anchors to reference entries
     - wrap bare URLs in the reference list with <...> so kramdown links them
  2. Format the file with the repo's pinned prettier.
  3. Optionally commit + push and poll the GitHub Actions "Deploy site" run.

Usage:
  # publish a vault note (writes _posts/, no git unless --push)
  bin/publish_obsidian_note.py --source ~/obsidianVault/Inbox/发布-xxx.md \
      --slug my-post-slug [--date 2026-07-20] [--desc "..."] [--push]

  # (re)apply citation linking to an existing post, e.g. after editing
  bin/publish_obsidian_note.py --relink _posts/2026-07-20-xxx.md [--push]

Stdlib only; idempotent (safe to re-run relink).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO / "_posts"
PRETTIER = REPO / "node_modules" / ".bin" / "prettier"
SITE_URL = "https://yulong-ge.github.io"
ACTIONS_API = "https://api.github.com/repos/yulong-ge/yulong-ge.github.io/actions/runs?per_page=8"

DEFAULT_CATEGORIES = "research-notes"
DEFAULT_LANG = "zh-CN"
TZ = "+0800"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, cwd=REPO, **kw)


# ---------------------------------------------------------------- frontmatter

def parse_vault_frontmatter(text: str) -> tuple[dict, str]:
    """Return (meta, body). Vault notes start with '---' YAML frontmatter."""
    m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)(.*)", text, re.S)
    if not m:
        die("note has no closed frontmatter ('---' ... '---') at the top")
    raw, body = m.group(1), m.group(2).lstrip("\n")
    meta: dict = {}
    current_key: str | None = None
    for line in raw.splitlines():
        fm = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if fm:
            current_key = fm.group(1)
            meta[current_key] = fm.group(2).strip()
        elif current_key and re.match(r"^\s+-\s+\S", line):
            item = line.strip()[1:].strip()
            if isinstance(meta.get(current_key), list):
                meta[current_key].append(item)
            elif meta.get(current_key) == "":
                meta[current_key] = [item]
    return meta, body


def parse_tags(meta: dict) -> list[str]:
    """Handles vault block-list tags ('- x' lines) and inline [a, b] alike."""
    raw = meta.get("tags", "")
    if isinstance(raw, list):
        return [t for t in raw if t]
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
        return [t.strip() for t in raw.split(",") if t.strip()]
    return [raw] if raw else []


def parse_note_date(meta: dict) -> str | None:
    # vault 'time' format: 2026-07-20-W30 10:00
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?:-W\d+)?\s+(\d{1,2}:\d{2})", meta.get("time", ""))
    if m:
        return f"{m.group(1)} {m.group(2).zfill(5)}:00 {TZ}"
    m = re.match(r"(\d{4}-\d{2}-\d{2})", meta.get("time", ""))
    return f"{m.group(1)} 09:00:00 {TZ}" if m else None


def yaml_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------------------------------------------------------------- conversions

def strip_h1(body: str) -> tuple[str, str]:
    """Remove the first '# ' heading; return (title, body)."""
    m = re.search(r"^#\s+(.+?)\s*$", body, re.M)
    if not m:
        die("no H1 ('# title') found in note body")
    return m.group(1), body[: m.start()] + body[m.end() :] .lstrip("\n")


def first_paragraph(body: str, limit: int = 160) -> str:
    for block in re.split(r"\n\s*\n", body):
        t = block.strip()
        if t and not t.startswith(("#", ">", "|", "-", "!", "[!")):
            t = re.sub(r"[*_`>\[\]]", "", t)
            t = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", t)
            t = re.sub(r"\s+", " ", t).strip()
            return t[: limit - 1] + "…" if len(t) > limit else t
    return ""


def split_refs_section(text: str) -> tuple[str, list[str], str]:
    """Split into (before, ref_lines, after) around the 参考文献 heading."""
    m = re.search(r"^#{2,6}\s*(参考文献|References|references)\s*$", text, re.M)
    if not m:
        return text, [], ""
    after_start = len(text)
    for stop in re.finditer(r"^(?:#{1,6} .*|---+)\s*$", text[m.end() :], re.M):
        after_start = m.end() + stop.start()
        break
    before = text[: m.start()]
    refs = text[m.end() :after_start].splitlines()
    after = text[after_start:]
    return before, refs, after


def link_citations(text: str) -> str:
    """Body [N] -> jump links; reference entries get anchors. Idempotent."""
    before, refs, after = split_refs_section(text)

    def body_line(line: str) -> str:
        return re.sub(
            r"\[(\d{1,2})\]",
            lambda m: f"[\\[{m.group(1)}\\]](#ref-{m.group(1)})",
            line,
        )

    lines, in_fence = [], False
    for line in before.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        lines.append(line if in_fence else body_line(line))
    before = "\n".join(lines)

    out = []
    for line in refs:
        m = re.match(r"^\[(\d{1,2})\]\s", line)
        if m and f'id="ref-{m.group(1)}"' not in line:
            line = f'<a id="ref-{m.group(1)}"></a>{line}'
        out.append(line)
    return before + "\n".join(out) + after


def wrap_bare_urls_in_refs(text: str) -> str:
    before, refs, after = split_refs_section(text)
    out = []
    for line in refs:
        if re.match(r"^\[\d{1,2}\]\s", line):
            line = re.sub(
                r"(?<![<(])(https?://[^\s<>()，。；、'\"]+)",
                lambda m: "<" + m.group(1).rstrip(".,;") + ">",
                line,
            )
        out.append(line)
    return before + "\n".join(out) + after


def check_no_wikilinks(body: str) -> None:
    for m in re.finditer(r"\[\[([^\]]+)\]\]", body):
        print(f"warning: vault wikilink [[{m.group(1)}]] will not render on the blog; "
              f"convert it to plain text or a real link", file=sys.stderr)


# ---------------------------------------------------------------- git / CI

def git_commit_push(path: Path, msg: str) -> str:
    run(["git", "add", "--", str(path.relative_to(REPO))])
    run(["git", "commit", "-m", msg])
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         check=True, capture_output=True, text=True, cwd=REPO).stdout.strip()
    run(["git", "push", "origin", "main"])
    return sha


def ensure_prettier() -> None:
    if not PRETTIER.exists():
        print("prettier not installed; running npm ci once …")
        run(["npm", "ci", "--no-audit", "--no-fund"])


def poll_deploy(sha: str, timeout_s: int = 1800) -> bool:
    print(f"polling Actions for {sha} (Deploy site) …")
    deadline = time.time() + timeout_s
    seen: set[str] = set()
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(ACTIONS_API, timeout=30) as r:
                runs = json.load(r)["workflow_runs"]
        except Exception as e:  # transient network errors are fine
            print(f"  api error: {e}")
            time.sleep(15)
            continue
        interesting = [x for x in runs if x["head_sha"].startswith(sha)
                       and x["name"] in ("Deploy site", "Prettier code formatter")]
        for x in interesting:
            key = f'{x["name"]}:{x["status"]}:{x.get("conclusion")}'
            if key not in seen:
                seen.add(key)
                print(f'  {x["name"]}: {x["status"]}'
                      + (f' ({x["conclusion"]})' if x.get("conclusion") else ""))
        dep = next((x for x in interesting if x["name"] == "Deploy site"), None)
        if dep and dep["status"] == "completed":
            ok = dep.get("conclusion") == "success"
            checks = [x for x in interesting if x["status"] == "completed"]
            print("deploy " + ("succeeded ✓" if ok else "FAILED ✗")
                  + ("" if all(c.get("conclusion") == "success" for c in checks)
                     else " (note: some checks failed)"))
            return ok
        time.sleep(30)
    print("timed out waiting for Deploy site")
    return False


# ---------------------------------------------------------------- main

def cmd_publish(args) -> None:
    src = Path(args.source).expanduser()
    if not src.is_file():
        die(f"note not found: {src}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.slug):
        die(f"invalid slug: {args.slug!r} (lowercase letters/digits/hyphens only)")

    meta, body = parse_vault_frontmatter(src.read_text(encoding="utf-8"))
    title, body = strip_h1(body)
    check_no_wikilinks(body)

    date = args.date or parse_note_date(meta) or datetime.now().strftime("%Y-%m-%d")
    if not re.match(r"\d{4}-\d{2}-\d{2}$", date):
        die(f"invalid --date: {date!r} (expected YYYY-MM-DD)")
    if not parse_note_date(meta):
        print("warning: no parsable 'time' in frontmatter; using "
              + (args.date or "today"), file=sys.stderr)
    time_part = (parse_note_date(meta) or f"{date} 09:00:00 {TZ}").split(" ")[1]

    tags = args.tags.split(",") if args.tags else parse_tags(meta)
    desc = args.desc or first_paragraph(body)

    body = wrap_bare_urls_in_refs(link_citations(body))
    front = "\n".join([
        "---",
        "layout: post",
        f"title: {yaml_quote(title)}",
        f"date: {date} {time_part} {TZ}",
        f"description: {yaml_quote(desc)}",
        f"tags: [{', '.join(tags)}]",
        f"categories: [{args.categories}]",
        f"lang: {args.lang}",
        "giscus_comments: true",
        "---",
        "",
    ])

    dest = POSTS_DIR / f"{date}-{args.slug}.md"
    if dest.exists() and not args.force:
        die(f"{dest.relative_to(REPO)} already exists (use --force to overwrite)")
    POSTS_DIR.mkdir(exist_ok=True)
    dest.write_text(front + body.strip() + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(REPO)}")

    ensure_prettier()
    run([str(PRETTIER), "--write", str(dest.relative_to(REPO))])

    if args.push:
        sha = git_commit_push(dest, f"Publish blog post: {title}")
        poll_deploy(sha)
        print(f"\nURL: {SITE_URL}/blog/{date[:4]}/{args.slug}/")
    else:
        print("dry-run: file written and formatted, not committed (add --push)")


def cmd_relink(args) -> None:
    p = (REPO / args.relink) if not Path(args.relink).is_absolute() else Path(args.relink)
    if not p.is_file():
        die(f"post not found: {p}")
    text = p.read_text(encoding="utf-8")
    new = wrap_bare_urls_in_refs(link_citations(text))
    if new != text:
        p.write_text(new, encoding="utf-8")
        print(f"relinked {p.relative_to(REPO)}")
    else:
        print("nothing to change")
    ensure_prettier()
    run([str(PRETTIER), "--write", str(p.relative_to(REPO))])
    if args.push:
        sha = git_commit_push(p, f"style: link citations to references in {p.name}")
        poll_deploy(sha)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", help="path to the Obsidian vault note (.md)")
    ap.add_argument("--slug", help="url slug for the post, e.g. my-post-slug")
    ap.add_argument("--date", help="override date YYYY-MM-DD (default: note 'time')")
    ap.add_argument("--desc", help="override description (default: first paragraph)")
    ap.add_argument("--tags", help="comma-separated tags (default: from frontmatter)")
    ap.add_argument("--categories", default=DEFAULT_CATEGORIES)
    ap.add_argument("--lang", default=DEFAULT_LANG)
    ap.add_argument("--force", action="store_true", help="overwrite existing post file")
    ap.add_argument("--push", action="store_true", help="commit, push and poll CI")
    ap.add_argument("--relink", metavar="POST",
                    help="(re)apply citation linking to an existing post file")
    args = ap.parse_args()

    if args.relink:
        cmd_relink(args)
    elif args.source and args.slug:
        cmd_publish(args)
    else:
        die("need --source and --slug (or --relink POST); see --help")


if __name__ == "__main__":
    main()
