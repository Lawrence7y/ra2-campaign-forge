#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atlas_toc.py - Lead-owned TOC generator/validator for docs/re/ARCHITECTURE_ATLAS.md

Modes: --check (default, report drift, exit 1 on drift) | --write (rewrite the TOC block)
Slug rule (reverse-engineered from the frozen atlas, self-validated against its own entries):
  lowercase; drop [.  section-sign / en-dash em-dash : ( )] and CJK enumeration commas; spaces -> "-".
"""
import argparse, os, re, sys

HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TOC_RE = re.compile(r"^(\s*)[-*]\s+\[(.+?)\]\(#(.+?)\)\s*$")
DROP = set(".\u00a7/\u2013\u2014:()\u3001\uff0c\uff08\uff09")


def slug(text):
    out = []
    for ch in text.strip().lower():
        if ch in DROP:
            continue
        out.append("-" if ch.isspace() else ch)
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().splitlines()


def norm(text):
    """TOC entries use the short title: drop trailing (English) parentheticals and [grade] tags."""
    t = re.sub(r"\s*\[[^\]]*\]\s*$", "", text.strip())
    t = re.sub(r"\([^()]*\)\s*$", "", t).strip()
    return t


def headings(lines):
    h2, cur = [], None
    for i, ln in enumerate(lines, 1):
        m = HEAD_RE.match(ln)
        if not m:
            continue
        lvl, text = len(m.group(1)), m.group(2).strip()
        if lvl == 2:
            cur = {"line": i, "text": text, "h3": []}
            h2.append(cur)
        elif lvl == 3 and cur is not None:
            cur["h3"].append({"line": i, "text": text})
    return h2


def toc_block(h2, with_h3=True):
    out = ["## 目录", ""]
    for s in [x for x in h2 if x["text"] != "目录"]:
        out.append("- [%s](#%s)" % (s["text"], slug(s["text"])))
        if with_h3:
            for sub in s["h3"]:
                out.append("  - [%s](#%s)" % (sub["text"], slug(sub["text"])))
    return out


def existing_block(lines):
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## 目录":
            start = i
            break
    if start is None:
        return None, None
    end = start + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    return start, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default=os.path.join("docs", "re", "ARCHITECTURE_ATLAS.md"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--no-h3", action="store_true")
    ap.add_argument("--report", default=os.path.join("out", "re_work", "atlas_rev", "lead", "atlas_toc_report.md"))
    args = ap.parse_args()

    lines = read(args.atlas)
    h2 = headings(lines)
    start, end = existing_block(lines)
    if start is None:
        print("FAIL: no TOC heading found")
        return 1

    ent = []
    for ln in lines[start:end]:
        m = TOC_RE.match(ln)
        if m:
            ent.append({"text": m.group(2), "anchor": m.group(3), "indent": len(m.group(1))})

    bad_slug = [e for e in ent if slug(e["text"]) != e["anchor"]]
    body = [s for s in h2 if s["text"] != "目录"]
    known = set()
    for s in body:
        known.add(norm(s["text"]))
        for sub in s["h3"]:
            known.add(norm(sub["text"]))
    toc_norm = [norm(e["text"]) for e in ent]
    missing = [s["text"] for s in body if norm(s["text"]) not in toc_norm]
    missing_h3 = [sub["text"] for s in body for sub in s["h3"] if norm(sub["text"]) not in toc_norm]
    stale = [e["text"] for e in ent if norm(e["text"]) not in known]

    new = toc_block(h2, with_h3=not args.no_h3)
    old = lines[start:end]
    identical = [x.rstrip() for x in old] == [x.rstrip() for x in new]

    md = []
    md.append("# ATLAS 目录(TOC)一致性报告 (tools/atlas_toc.py)")
    md.append("")
    md.append("- atlas: %s" % os.path.abspath(args.atlas))
    md.append("- 现有目录条目: %d | H2 实有 %d 节 | H3 实有 %d 小节" % (len(ent), len(h2), sum(len(s["h3"]) for s in h2)))
    md.append("- **slug 规则自证**: 现有条目重算锚点不一致数 = **%d** (0 = 规则已被冻结文本验证)" % len(bad_slug))
    md.append("- 目录缺失 H2: %d %s" % (len(missing), missing[:8]))
    md.append("- 目录缺失 H3: %d (by design: 冻结目录只展开 §0 的 H3; 重建版将全展开)" % len(missing_h3))
    md.append("- 目录 stale 条目: %d %s" % (len(stale), stale[:8]))
    md.append("- 与全展开(含 H3)结构完全一致: %s" % identical)
    md.append("")
    if bad_slug:
        md.append("| 标题 | 现有锚点 | 重算锚点 |")
        md.append("|---|---|---|")
        for e in bad_slug[:20]:
            md.append("| %s | %s | %s |" % (e["text"], e["anchor"], slug(e["text"])))
        md.append("")
    d = os.path.dirname(args.report)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))

    drift = bool(bad_slug or missing or stale or not identical)
    if args.write:
        out = lines[:start] + new + lines[end:]
        with open(args.atlas, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out) + "\n")
        print("WROTE %s: 目录 %d 行 -> %d 行" % (args.atlas, len(old), len(new)))
        return 0
    print("DRIFT" if drift else "IN SYNC")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())