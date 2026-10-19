#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atlas_apply_patches.py (v2) - Lead-owned mechanical applier for anchored patch blocks.

Design notes:
  * Every anchor is resolved against the PRISTINE atlas snapshot first (teammates quote
    snapshot line numbers).  Non-append patches are then applied in DESCENDING anchor order
    so earlier line numbers stay valid;  APPEND_SECTION patches are applied last, in stream
    order, immediately before the appendix anchor.
  * Patch grammar is tolerant: bold markers, full-width colons, path:NNN or LNNN anchors,
    and REPLACE_BLOCK ranges written as (cover L242-L249) / (range atlas:968-972).

Usage:
  python tools/atlas_apply_patches.py --dry-run
  python tools/atlas_apply_patches.py --apply [--only R1,R3]
"""
import argparse, datetime, glob, json, os, re, shutil, sys

TICK = chr(96)
PATCH_HEAD = re.compile(r"^#{2,4}\s+PATCH-([A-Za-z0-9]+)-(\d+)\b(.*)$")
ACTION_RE = re.compile(r"\u52a8\u4f5c\s*\**\s*[:\uff1a]\s*\**\s*(APPEND_SECTION|INSERT_AFTER|REPLACE_LINE|REPLACE_BLOCK|ERRATUM)", re.I)
FIELD_TARGET = re.compile(r"\u76ee\u6807\u951a\u70b9|\u951a\u70b9")
LINE_IN = re.compile(r"(?:ARCHITECTURE_ATLAS\.md\s*[:\uff1a]|L)\s*(\d{2,5})|[:\uff1a]\s*(\d{3,5})\s*\u884c?")
RANGE_RE = re.compile(r"(?:\u8986\u76d6|\u66ff\u6362\u8303\u56f4|range)[^0-9]{0,24}(\d{2,5})\s*[\u2013\u2014\-~\uff5e\u81f3]\s*L?(\d{2,5})")
QUOTED = [re.compile(TICK + "([^" + TICK + "]{6,})" + TICK),
          re.compile("\u300c([^\u300d]{6,})\u300d"),
          re.compile("\u300e([^\u300f]{6,})\u300f"),
          re.compile("\u201c([^\u201d]{6,})\u201d")]


def field_value(line):
    """Text between the first and last backtick/quote delimiter on a field line."""
    marks = [i for i, ch in enumerate(line) if ch in TICK + "\u300c\u300d\u201c\u201d"]
    if len(marks) < 2:
        return None
    return line[marks[0] + 1:marks[-1]].strip()


def fence_len(line):
    st = line.strip()
    m = re.match("^(" + TICK + "{3,})(.*)$", st)
    return len(m.group(1)) if m else 0


def parse_patches(path):
    lines = open(path, "r", encoding="utf-8").read().splitlines()
    out, i = [], 0
    while i < len(lines):
        m = PATCH_HEAD.match(lines[i])
        if not m:
            i += 1
            continue
        end = i + 1
        while end < len(lines) and not PATCH_HEAD.match(lines[end]):
            end += 1
        block = lines[i:end]
        body = "\n".join(block)
        act = ACTION_RE.search(body)
        tgt_text = ""
        for ln in block:
            if FIELD_TARGET.search(ln):
                tgt_text = ln
                break
        if not tgt_text:
            tgt_text = body
        lm = LINE_IN.search(tgt_text)
        target = None
        if lm:
            target = int(lm.group(1) or lm.group(2))
        rg = RANGE_RE.search(tgt_text) or RANGE_RE.search(body)
        rng = (int(rg.group(1)), int(rg.group(2))) if rg else None
        atext = None
        for rx in QUOTED:
            qm = rx.search(tgt_text)
            if qm:
                atext = qm.group(1).strip()
                break
        repl, in_fence, flen, started = [], False, 0, False
        for j, ln in enumerate(block):
            if not started:
                if re.search(r"\u66ff\u6362\u6587\u672c|\u66ff\u6362\u6b63\u6587|replacement", ln):
                    started = True
                continue
            fl = fence_len(ln)
            if not in_fence:
                if fl:
                    in_fence, flen = True, fl
                continue
            if fl and ln.strip()[0] == TICK and fl >= flen:
                break
            repl.append(ln)
        before_txt = after_txt = None
        if not repl:
            for ln in block:
                if before_txt is None and re.search(r"\u6539\u524d\u539f\u6587", ln):
                    before_txt = field_value(ln)
                if after_txt is None and re.search(r"\u6539\u540e\u6587\u672c", ln):
                    after_txt = field_value(ln)
            if before_txt and after_txt:
                repl = ["(errata-substitute)"]
        while repl and repl[-1].strip() == "":
            repl.pop()
        act_name = act.group(1).upper() if act else ("APPEND_SECTION" if "APPEND_SECTION" in body else "INSERT_AFTER")
        out.append({"patch": "PATCH-%s-%s" % (m.group(1), m.group(2)), "stream": m.group(1).upper(),
                    "source": os.path.basename(path), "action": act_name, "before": before_txt, "after": after_txt,
                    "target": target, "range": rng, "anchor_text": atext, "replacement": repl,
                    "headline": m.group(3).strip()[:80]})
        i = end
    return out


def resolve(lines, p, append_anchor):
    if p["action"] == "APPEND_SECTION" and p["target"] and 1 <= p["target"] <= len(lines):
        return p["target"] - 1, p["target"] - 1, "insert-before-declared-line"
    if p["action"] == "APPEND_SECTION":
        for idx, ln in enumerate(lines):
            if ln.strip().startswith(append_anchor):
                return idx, idx, "append-anchor-fallback"
        return None, None, "append-anchor-missing"
    if p["anchor_text"]:
        hits = [idx for idx, ln in enumerate(lines) if p["anchor_text"][:38] in ln]
        if len(hits) == 1:
            return hits[0], (hits[0] if not p["range"] else p["range"][0] - 1), "anchor-text"
        if len(hits) > 1 and p["target"]:
            best = min(hits, key=lambda h: abs(h + 1 - p["target"]))
            return best, (best if not p["range"] else p["range"][0] - 1), "anchor-text-nearest-of-%d" % len(hits)
        if len(hits) > 1:
            return None, None, "anchor-ambiguous-%d" % len(hits)
    if p["range"] and 1 <= p["range"][0] <= len(lines):
        return p["range"][0] - 1, p["range"][0] - 1, "line-range"
    if p["target"] and 1 <= p["target"] <= len(lines):
        return p["target"] - 1, p["target"] - 1, "line-hint"
    return None, None, "unresolved"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default=os.path.join("docs", "re", "ARCHITECTURE_ATLAS.md"))
    ap.add_argument("--notes-dir", default=os.path.join("docs", "re", "atlas_rev"))
    ap.add_argument("--pattern", default="R*.md")
    ap.add_argument("--only", default="")
    ap.add_argument("--append-anchor", default="## \u9644\u5f55 DA1")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--ledger", default=os.path.join("out", "re_work", "atlas_rev", "lead", "atlas_apply_ledger.json"))
    ap.add_argument("--backup-dir", default=os.path.join("out", "re_work", "atlas_rev", "lead"))
    args = ap.parse_args()

    only = [x.strip().upper() for x in args.only.split(",") if x.strip()]
    files = sorted(glob.glob(os.path.join(args.notes_dir, args.pattern)))
    if only:
        files = [f for f in files if os.path.basename(f).split("_")[0].upper() in only]
    pristine = open(args.atlas, "r", encoding="utf-8").read().splitlines()

    ops, unresolved = [], []
    for f in files:
        for p in parse_patches(f):
            start, anchor, how = resolve(pristine, p, args.append_anchor)
            e = dict(p, start=start, start_line=(anchor + 1) if anchor is not None else None, resolution=how,
                     agrees_with_target=(p["target"] == (anchor + 1)) if p["target"] else None)
            if start is None or not p["replacement"]:
                e["skip_reason"] = how if start is None else "no-replacement-text"
                unresolved.append(e)
            else:
                ops.append(e)

    order = {"R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5, "R6": 6, "R7": 7, "R8": 8}
    def rank(e):
        return (order.get(e["stream"], 99), int(e["patch"].split("-")[-1]))
    subs = [e for e in ops if e.get("before")]
    structural = [e for e in ops if not e.get("before")]
    structural.sort(key=lambda e: (-e["start"], -rank(e)[0], -rank(e)[1]))

    lines = list(pristine)
    applied = 0
    if args.apply:
        joined = "\n".join(lines)
        for e in subs:
            n = joined.count(e["before"])
            if n != 1:
                e["skip_reason"] = "errata-before-text-hits-%d" % n
                unresolved.append(e)
                continue
            joined = joined.replace(e["before"], e["after"])
            e["applied"] = True
            applied += 1
        lines = joined.split("\n")
        for e in structural:
            repl = list(e["replacement"])
            if e["action"] in ("REPLACE_BLOCK", "REPLACE_LINE") and e["range"]:
                a, b = e["range"][0] - 1, e["range"][1]
                lines[a:b] = repl
                e["replaced_lines"] = [a + 1, b]
            elif e["action"] == "REPLACE_LINE":
                lines[e["start"]:e["start"] + 1] = repl
                e["replaced_lines"] = [e["start"] + 1, e["start"] + 1]
            else:
                pos = e["start"] + 1
                pad = [] if lines[e["start"]].strip() == "" else [""]
                lines[pos:pos] = pad + repl
            e["applied"] = True
            applied += 1
    if args.apply:
        d = os.path.dirname(args.ledger)
        if d:
            os.makedirs(d, exist_ok=True)
        os.makedirs(args.backup_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = os.path.join(args.backup_dir, "atlas_backup_preapply_%s.md" % ts)
        shutil.copyfile(args.atlas, bak)
        with open(args.atlas, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        print("BACKUP: %s" % bak)

    print("=== atlas_apply_patches v2 (%s) ===" % ("APPLIED" if args.apply else "DRY-RUN"))
    print("notes: %d | parsed: %d | ready: %d | blocked: %d | applied: %d" % (
        len(files), len(ops) + len(unresolved), len(ops), len(unresolved), applied))
    for e in sorted(ops, key=rank):
        flag = "" if e.get("agrees_with_target") in (True, None) else "  <== TARGET-MISMATCH"
        print("  %-16s %-15s anchor=%-6s %-26s repl=%3dL %s%s" % (e["patch"], e["action"] or "?", e["start_line"], e["resolution"], len(e["replacement"]), e["source"], flag))
    if unresolved:
        print("-- blocked --")
        for e in unresolved:
            print("  %-16s %-15s target=%-6s %-26s %s" % (e["patch"], e["action"] or "?", e["target"], e["skip_reason"], e["source"]))
    d = os.path.dirname(args.ledger)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(args.ledger, "w", encoding="utf-8") as fh:
        json.dump({"atlas_before_lines": len(pristine), "atlas_after_lines": len(lines),
                   "applied": applied, "ops": ops, "blocked": unresolved}, fh, ensure_ascii=False, indent=2)
    print("ledger: %s" % os.path.abspath(args.ledger))
    return 0 if not unresolved else 2


if __name__ == "__main__":
    sys.exit(main())