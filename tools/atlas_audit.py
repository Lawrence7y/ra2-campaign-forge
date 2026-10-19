#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atlas_audit.py - Lead-side structural & compliance gate for docs/re/ARCHITECTURE_ATLAS.md

Mechanical checks (no judgement calls):
  F1 code-fence balance (fenced blocks must pair up)
  F2 heading tree sanity (H2 sections numbered 0..N monotonic & unique)
  F3 TOC <-> H2 heading consistency
  F4 every ### subsection carries an evidence grade tag in title or next 3 lines
  F5 stale-threshold guard: no uncorrected reference to retired unique-colour thresholds
  F6 VA inventory: every 0x address grouped by owning section -> CSV (anchor + quick-reference source)

Exit 0 = ALL PASS, 1 = FAIL. Markdown report to file+stdout, JSON summary alongside.
Usage: python tools/atlas_audit.py [--atlas PATH] [--md-out PATH] [--json-out PATH] [--va-out PATH]
"""
import argparse, datetime, json, os, re, sys

TICK = chr(96)
FENCE_RE = re.compile(r"^(\s*)(" + TICK + "{3,})")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
VA_RE = re.compile(r"0x[0-9A-Fa-f]{6,8}")
GRADES = ("[实证]", "[推演]", "[待实测]")
TOC_RE = re.compile(r"^\s*\d+\.\s*\[([^\]]+)\]")
STALE_PATTERNS = [
    (re.compile(r"≥\s*2,?000\s*种"), "retired sampled threshold >=2000"),
    (re.compile(r"≥\s*20,?000"), "retired full-frame threshold >=20000"),
    (re.compile(r"色数\s*≥\s*2,?000"), "retired colour-count threshold >=2000"),
]
CORRECTION_HINT = re.compile(r"勘误|订正|作废|已改|新口径|原文保留|不可达")
NEW_CALIBER = re.compile(r"≥\s*800|>=\s*800|≥\s*600|>=\s*600")


def load(atlas):
    with open(atlas, "r", encoding="utf-8") as fh:
        return fh.read().splitlines()


def check_fences(lines):
    open_fence = None
    unclosed = []
    pairs = 0
    for i, ln in enumerate(lines, 1):
        m = FENCE_RE.match(ln)
        if not m:
            continue
        ticks = m.group(2)
        if open_fence is None:
            open_fence = (i, len(ticks))
        elif len(ticks) >= open_fence[1]:
            pairs += 1
            open_fence = None
    if open_fence is not None:
        unclosed.append({"line": open_fence[0], "issue": "unclosed fence opened here"})
    return {"pairs": pairs, "unclosed": unclosed, "pass": not unclosed}


def check_headings(lines):
    h1, h2, h3 = [], [], []
    for i, ln in enumerate(lines, 1):
        m = HEAD_RE.match(ln)
        if not m:
            continue
        lvl, text = len(m.group(1)), m.group(2).strip()
        if lvl == 1:
            h1.append((i, text))
        elif lvl == 2:
            h2.append((i, text))
        elif lvl == 3:
            h3.append((i, text))
    nums = []
    for _, t in h2:
        m = re.match(r"(\d+)\.", t)
        if m:
            nums.append(int(m.group(1)))
    monotonic = nums == sorted(nums) and len(set(nums)) == len(nums)
    return {"h1": h1, "h2": h2, "h3": h3, "section_numbers": nums, "monotonic": monotonic}


def check_toc(lines, h2):
    toc_start = None
    for i, ln in enumerate(lines, 1):
        if ln.strip() in ("## 目录", "## Table of Contents"):
            toc_start = i
            break
    entries = []
    if toc_start:
        for ln in lines[toc_start:min(len(lines), toc_start + 80)]:
            if ln.strip().startswith("## ") and ln.strip() != "## 目录":
                break
            m = TOC_RE.match(ln)
            if m:
                entries.append(m.group(1).strip())
    h2_texts = [t for _, t in h2]
    missing = [e for e in entries if not any(e in t or t.startswith(e) for t in h2_texts)]
    return {"toc_start_line": toc_start, "toc_entries": len(entries), "anchors_missing_from_body": missing}


def check_grades(lines, h3):
    missing = []
    for line_no, text in h3:
        window = " ".join(lines[max(0, line_no - 1):line_no + 3])
        if not any(g in window for g in GRADES):
            missing.append({"line": line_no, "heading": text[:70]})
    counts = {g: 0 for g in GRADES}
    for ln in lines:
        for g in GRADES:
            counts[g] += ln.count(g)
    return {"counts": counts, "subsections_without_grade": missing}


def check_thresholds(lines):
    hits = []
    for i, ln in enumerate(lines, 1):
        for pat, why in STALE_PATTERNS:
            if pat.search(ln):
                ctx = " ".join(lines[max(0, i - 4):i + 3])
                corrected = bool(CORRECTION_HINT.search(ctx)) or bool(NEW_CALIBER.search(ctx))
                hits.append({"line": i, "why": why, "corrected_nearby": corrected, "text": ln.strip()[:110]})
    uncorrected = [h for h in hits if not h["corrected_nearby"]]
    return {"hits": hits, "uncorrected": uncorrected, "pass": not uncorrected}


def build_va_index(lines):
    cur_h2 = cur_h3 = ""
    rows = []
    for i, ln in enumerate(lines, 1):
        m = HEAD_RE.match(ln)
        if m:
            lvl, text = len(m.group(1)), m.group(2).strip()
            if lvl == 1:
                cur_h2 = cur_h3 = ""
            elif lvl == 2:
                cur_h2, cur_h3 = text, ""
            elif lvl == 3:
                cur_h3 = text
        for va in VA_RE.findall(ln):
            rows.append({"va": va.lower(), "line": i, "section": cur_h2[:60], "subsection": cur_h3[:60], "snippet": ln.strip()[:150]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default=os.path.join("docs", "re", "ARCHITECTURE_ATLAS.md"))
    ap.add_argument("--md-out", default=os.path.join("out", "re_work", "atlas_rev", "lead", "atlas_audit_report.md"))
    ap.add_argument("--json-out", default=os.path.join("out", "re_work", "atlas_rev", "lead", "atlas_audit.json"))
    ap.add_argument("--va-out", default=os.path.join("out", "re_work", "atlas_rev", "lead", "atlas_va_index.csv"))
    args = ap.parse_args()

    lines = load(args.atlas)
    fences = check_fences(lines)
    heads = check_headings(lines)
    toc = check_toc(lines, heads["h2"])
    grades = check_grades(lines, heads["h3"])
    thr = check_thresholds(lines)
    va_rows = build_va_index(lines)
    uniq_va = sorted({r["va"] for r in va_rows})

    fails = []
    if not fences["pass"]:
        fails.append("F1 fence balance")
    if not heads["monotonic"]:
        fails.append("F2 section numbering not monotonic/unique")
    if toc["anchors_missing_from_body"]:
        fails.append("F3 TOC anchors missing: " + ", ".join(toc["anchors_missing_from_body"][:5]))
    if not thr["pass"]:
        fails.append("F5 uncorrected retired threshold x%d" % len(thr["uncorrected"]))

    summary = {
        "atlas": os.path.abspath(args.atlas),
        "lines": len(lines),
        "bytes": os.path.getsize(args.atlas),
        "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(args.atlas)).isoformat(timespec="seconds"),
        "fences": fences,
        "headings": {"h1": len(heads["h1"]), "h2": len(heads["h2"]), "h3": len(heads["h3"]),
                     "sections": heads["section_numbers"], "monotonic": heads["monotonic"]},
        "toc": toc,
        "grades": grades,
        "thresholds": thr,
        "va_index": {"occurrences": len(va_rows), "unique": len(uniq_va),
                     "csv": os.path.abspath(args.va_out), "json": os.path.abspath(args.json_out)},
        "verdict": "ALL PASS" if not fails else "FAIL",
        "fails": fails,
    }

    for path in (args.md_out, args.json_out, args.va_out):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
    with open(args.va_out, "w", encoding="utf-8") as fh:
        fh.write("va,line,section,subsection,snippet\n")
        for r in va_rows:
            fh.write('%s,%d,"%s","%s","%s"\n' % (r["va"], r["line"], r["section"].replace('"', "'"), r["subsection"].replace('"', "'"), r["snippet"].replace('"', "'")))
    with open(args.json_out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    md = []
    md.append("# ATLAS 结构与合规审计报告 (tools/atlas_audit.py)")
    md.append("")
    md.append("- atlas: %s" % summary["atlas"])
    md.append("- 行数 / 字节 / mtime: %d / %d / %s" % (summary["lines"], summary["bytes"], summary["mtime"]))
    md.append("- **裁决: %s**" % summary["verdict"])
    md.append("")
    md.append("| 检查 | 结果 | 细节 |")
    md.append("|---|---|---|")
    md.append("| F1 代码围栏配对 | %s | %d 对, 未闭合 %d |" % ("PASS" if fences["pass"] else "FAIL", fences["pairs"], len(fences["unclosed"])))
    md.append("| F2 章节编号单调唯一 | %s | %s |" % ("PASS" if heads["monotonic"] else "FAIL", heads["section_numbers"]))
    md.append("| F3 目录锚点 | %s | 目录 %d 条, 缺失 %d |" % ("PASS" if not toc["anchors_missing_from_body"] else "FAIL", toc["toc_entries"], len(toc["anchors_missing_from_body"])))
    md.append("| F4 小节证据等级标注 | INFO | 无等级小节 %d |" % len(grades["subsections_without_grade"]))
    md.append("| F5 作废阈值残留 | %s | 命中 %d, 未更正 %d |" % ("PASS" if thr["pass"] else "FAIL", len(thr["hits"]), len(thr["uncorrected"])))
    md.append("| F6 VA 清单 | INFO | 出现 %d 次, 唯一 %d 个 |" % (len(va_rows), len(uniq_va)))
    md.append("")
    md.append("## H2 章节锚点表(补丁目标锚点用)")
    md.append("")
    md.append("| 行号 | 标题 |")
    md.append("|---|---|")
    for i, t in heads["h2"]:
        md.append("| %d | %s |" % (i, t[:100]))
    if grades["subsections_without_grade"]:
        md.append("")
        md.append("## 无证据等级标签的 ### 小节 (INFO)")
        md.append("")
        for r in grades["subsections_without_grade"]:
            md.append("- L%d: %s" % (r["line"], r["heading"]))
    if thr["hits"]:
        md.append("")
        md.append("## 作废阈值命中明细")
        md.append("")
        for r in thr["hits"]:
            md.append("- L%d [%s] corrected_nearby=%s: %s" % (r["line"], r["why"], r["corrected_nearby"], r["text"]))
    with open(args.md_out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")

    print("\n".join(md[:36]))
    print("")
    print("JSON: %s" % os.path.abspath(args.json_out))
    print("VA  : %s" % os.path.abspath(args.va_out))
    print("MD  : %s" % os.path.abspath(args.md_out))
    print("Verdict: %s%s" % (summary["verdict"], "" if not fails else " -> " + "; ".join(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())