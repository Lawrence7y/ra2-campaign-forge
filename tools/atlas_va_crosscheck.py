#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atlas_va_crosscheck.py - cross-check every VA cited in the atlas against the
machine-rerunnable byte-assertion libraries, and between those libraries themselves.

Reports:
  1. dangling VAs   : cited in the atlas but asserted by no library  (= evidence hole)
  2. byte conflicts : same VA asserted with different bytes in different libraries
  3. per-section coverage: VAs / asserted / dangling

Inputs: docs/re/ARCHITECTURE_ATLAS.md, docs/re/anchor_claims.txt, out/re_work/asm_scan/claims.txt,
        plus any --claims extra files (e.g. teammate claims).
Outputs: out/re_work/atlas_rev/lead/atlas_va_crosscheck.md / .json
Usage: python tools/atlas_va_crosscheck.py [--strict] [--claims FILE ...]
"""
import argparse, datetime, json, os, re, sys

CLAIM_RE = re.compile(r"(0x[0-9A-Fa-f]{6,8})\s*=\s*([0-9A-Fa-f]{2}(?:\s+[0-9A-Fa-f]{2})*)")
VA_RE = re.compile(r"0x[0-9A-Fa-f]{6,8}")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def canon(va):
    """Canonical 0x%08x key: atlas writes 0x6D3D99, libraries write 0x006D3D99."""
    return "0x%08x" % int(va, 16)


def is_address(v):
    """gamemd.exe ImageBase 0x400000; treat only plausibly mapped VAs as addresses."""
    n = int(v, 16)
    return 0x00400000 <= n <= 0x00A00000


def parse_claims(path):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for i, ln in enumerate(fh, 1):
            if ln.lstrip().startswith("#"):
                continue
            for m in CLAIM_RE.finditer(ln):
                if not is_address(m.group(1)):
                    continue
                va = canon(m.group(1))
                byt = " ".join(m.group(2).upper().split())
                out.setdefault(va, []).append({"bytes": byt, "line": i, "raw": ln.strip()[:140]})
    return out


def atlas_va_map(path):
    cur_h2 = cur_h3 = ""
    seen = {}
    noise = set()
    with open(path, "r", encoding="utf-8") as fh:
        for i, ln in enumerate(fh, 1):
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
                if not is_address(va):
                    noise.add(va.lower())
                    continue
                k = canon(va)
                e = seen.setdefault(k, {"lines": [], "section": cur_h2, "subsection": cur_h3})
                e["lines"].append(i)
    return seen, noise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default=os.path.join("docs", "re", "ARCHITECTURE_ATLAS.md"))
    ap.add_argument("--anchors", default=os.path.join("docs", "re", "anchor_claims.txt"))
    ap.add_argument("--asm-scan", default=os.path.join("out", "re_work", "asm_scan", "claims.txt"))
    ap.add_argument("--claims", nargs="*", default=[])
    ap.add_argument("--md-out", default=os.path.join("out", "re_work", "atlas_rev", "lead", "atlas_va_crosscheck.md"))
    ap.add_argument("--json-out", default=os.path.join("out", "re_work", "atlas_rev", "lead", "atlas_va_crosscheck.json"))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    libs = {"anchor_claims": parse_claims(args.anchors), "asm_scan": parse_claims(args.asm_scan)}
    for extra in args.claims:
        libs["extra:" + os.path.basename(extra)] = parse_claims(extra)
    atlas, noise = atlas_va_map(args.atlas)

    dangling, covered = [], []
    for va, meta in sorted(atlas.items()):
        holders = [name for name, lib in libs.items() if va in lib]
        row = {"va": va, "lines": meta["lines"][:6], "section": meta["section"][:70], "subsection": meta["subsection"][:70], "asserted_in": holders}
        (covered if holders else dangling).append(row)

    conflicts = []
    variants_report = []
    for va in sorted(atlas):
        holders = {name: lib[va] for name, lib in libs.items() if va in lib}
        if len(holders) < 2:
            continue
        variants = {}
        for name, entries in holders.items():
            for e in entries:
                variants.setdefault(e["bytes"], []).append(name)
        if len(variants) < 2:
            continue
        # A shorter byte string that is a prefix of a longer one is a window-length
        # variant of the SAME instruction stream, not a contradiction.
        seqs = sorted(variants)
        genuine = False
        for i, a in enumerate(seqs):
            for b in seqs[i + 1:]:
                if not (b == a or b.startswith(a + " ") or a.startswith(b + " ")):
                    genuine = True
        entry = {"va": va, "atlas_lines": atlas[va]["lines"][:4],
                 "kind": "MISMATCH" if genuine else "prefix-variant",
                 "variants": [{"bytes": b, "libs": sorted(set(l))} for b, l in variants.items()]}
        variants_report.append(entry)
        if genuine:
            conflicts.append(entry)

    sec = {}
    for va, meta in atlas.items():
        s = meta["section"] or "(no section)"
        d = sec.setdefault(s, {"total": 0, "asserted": 0, "dangling": 0})
        d["total"] += 1
        if any(va in lib for lib in libs.values()):
            d["asserted"] += 1
        else:
            d["dangling"] += 1

    summary = {
        "atlas": os.path.abspath(args.atlas),
        "atlas_mtime": datetime.datetime.fromtimestamp(os.path.getmtime(args.atlas)).isoformat(timespec="seconds"),
        "atlas_unique_va": len(atlas),
        "non_address_tokens": len(noise),
        "libraries": {name: {"assertions_parsed": sum(len(v) for v in lib.values()), "unique_va": len(lib)} for name, lib in libs.items()},
        "covered": len(covered),
        "dangling": len(dangling),
        "coverage_pct": round(100.0 * len(covered) / max(1, len(atlas)), 2),
        "byte_conflicts": len(conflicts),
        "prefix_variants": len(variants_report),
        "sections": sec,
    }

    for p in (args.md_out, args.json_out):
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
    with open(args.json_out, "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "dangling": dangling, "conflicts": conflicts, "variants": variants_report, "covered_sample": covered[:200]}, fh, ensure_ascii=False, indent=2)

    md = []
    md.append("# ATLAS VA 证据交叉核验 (tools/atlas_va_crosscheck.py)")
    md.append("")
    md.append("- atlas: %s (mtime %s)" % (summary["atlas"], summary["atlas_mtime"]))
    md.append("- atlas 非地址字面量(已剔除, 如 0x00000001 常量): %d" % len(noise))
    md.append("- 同址多源字节串: %d 组,其中 **真实不一致 %d 组**,其余为前缀/窗口长度变体" % (len(variants_report), len(conflicts)))
    md.append("- atlas 唯一 VA: **%d** | 有断言支撑: **%d** (%.2f%%) | **证据悬空: %d** | 字节冲突: %d" % (
        summary["atlas_unique_va"], summary["covered"], summary["coverage_pct"], summary["dangling"], summary["byte_conflicts"]))
    md.append("- 断言库: " + ", ".join("%s(%d 条/%d VA)" % (k, v["assertions_parsed"], v["unique_va"]) for k, v in summary["libraries"].items()))
    md.append("")
    md.append("## 1. 证据悬空 VA(atlas 引用但断言库无覆盖) —— 按章节")
    md.append("")
    md.append("| 章节 | VA 数 | 有断言 | 悬空 |")
    md.append("|---|---|---|---|")
    for s, d in sorted(sec.items(), key=lambda kv: -kv[1]["dangling"]):
        md.append("| %s | %d | %d | %d |" % (s.replace("|", "/")[:80], d["total"], d["asserted"], d["dangling"]))
    if dangling:
        md.append("")
        md.append("### 悬空明细(前 120 条)")
        md.append("")
        md.append("| VA | atlas 行 | 小节 |")
        md.append("|---|---|---|")
        for r in dangling[:120]:
            md.append("| %s | %s | %s |" % (r["va"], ",".join(str(x) for x in r["lines"]), (r["subsection"] or r["section"]).replace("|", "/")[:70]))
    md.append("")
    md.append("## 2. 断言库之间的字节冲突")
    md.append("")
    if not conflicts:
        md.append("无(所有多源同址断言字节一致)")
    else:
        md.append("| VA | atlas 行 | 变体 |")
        md.append("|---|---|---|")
        for c in conflicts:
            v = " vs ".join("`%s`(%s)" % (x["bytes"], "/".join(x["libs"])) for x in c["variants"])
            md.append("| %s | %s | %s |" % (c["va"], ",".join(str(x) for x in c["atlas_lines"]), v))
    with open(args.md_out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")

    print("\n".join(md[:30]))
    print("")
    print("MD  : %s" % os.path.abspath(args.md_out))
    print("JSON: %s" % os.path.abspath(args.json_out))
    print("dangling=%d covered=%d conflicts=%d" % (len(dangling), len(covered), len(conflicts)))
    return 1 if (args.strict and dangling) else 0


if __name__ == "__main__":
    sys.exit(main())