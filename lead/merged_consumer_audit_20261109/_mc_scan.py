# -*- coding: utf-8 -*-
"""_mc_scan.py — 消费方独立普查（只读扫描，绝不改被扫件）。
遍历 lead/ 下全部 .py，带剪枝与深度上限。检测：
  A. 谁 import / 调用 _re_linked.py（产出 merged 的并入版）、_sl_link.py（原件）、_f2_r11plus.py（r11 生产）
  B. 谁调用 link() / link_triple() / r11_scan_plus()
  C. 谁读 rec['path'] / rec['verified_path'] / ['recomputed'] / ['bytes'] / ['match'] / ['tier'] 下标
  D. 「match=True ⇒ path 非空」危险模式（match 与 path 同读、或 if rec['match'] 后用 rec['path']）
只打印，不改任何被扫件。
"""
import os
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
DEPTH_CAP = 6                 # 深度上限（lead/ 相对层数）
PRUNE_DIRS = {".git", "__pycache__", ".mimosa", "node_modules", ".tmp"}
MAX_BYTES = 400_000          # 单文件体积剪枝（防超大 json 化 .py）

# 关键字
RE_IMPORT_RE = re.compile(r"_re_linked|r33e_merge")
RE_IMPORT_SL = re.compile(r"_sl_link|samedoc_link")
RE_IMPORT_R11 = re.compile(r"_f2_r11plus|r11_scan_plus|r11_f2_fix")
CALL_LINK = re.compile(r"(?<![A-Za-z_])link\s*\(")
CALL_TRIPLE = re.compile(r"link_triple\s*\(")
CALL_R11 = re.compile(r"r11_scan_plus\s*\(")
# rec 字段下标读（单/双引号）
FIELD = re.compile(r"""\[\s*['"](path|verified_path|recomputed|bytes|match|tier|members|anchors|reverify|eq|verdict|samedoc_link|problems|warnings)['"]\s*\]""")
# .get("path") 形态
GETFIELD = re.compile(r"""\.get\(\s*['"](path|verified_path|recomputed|bytes|match|tier|members)['"]""")


def walk():
    out = []
    base_depth = len(LEAD.parts)
    visited_dirs = 0
    pruned = []
    for dirpath, dirnames, filenames in os.walk(LEAD):
        d = Path(dirpath)
        rel_depth = len(d.parts) - base_depth
        # 剪枝：跳过豁免目录
        keep = []
        for dn in dirnames:
            if dn in PRUNE_DIRS:
                pruned.append(str(d / dn))
            else:
                keep.append(dn)
        dirnames[:] = keep
        visited_dirs += 1
        if rel_depth > DEPTH_CAP:
            dirnames[:] = []
            pruned.append(str(d) + " [DEPTH_CAP]")
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = d / fn
            try:
                if p.stat().st_size > MAX_BYTES:
                    pruned.append(str(p) + " [MAX_BYTES]")
                    continue
            except OSError:
                continue
            out.append(p)
    return out, visited_dirs, pruned


def main():
    files, dirs_visited, pruned = walk()
    rows = []
    for p in files:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = txt.splitlines()
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        imp_re = bool(RE_IMPORT_RE.search(txt))
        imp_sl = bool(RE_IMPORT_SL.search(txt))
        imp_r11 = bool(RE_IMPORT_R11.search(txt))
        c_link = len(CALL_LINK.findall(txt))
        c_triple = len(CALL_TRIPLE.findall(txt))
        c_r11 = len(CALL_R11.findall(txt))
        fields = {}
        for m in FIELD.finditer(txt):
            fields[m.group(1)] = fields.get(m.group(1), 0) + 1
        for m in GETFIELD.finditer(txt):
            k = m.group(1)
            fields[k] = fields.get(k, 0) + 1
        # 危险模式粗筛：match 与 path/verified_path 同文件出现
        danger = ("match" in fields) and (("path" in fields) or ("verified_path" in fields))
        rows.append({
            "file": rel, "bytes": p.stat().st_size,
            "imp_re_linked": imp_re, "imp_sl_link": imp_sl, "imp_r11": imp_r11,
            "call_link": c_link, "call_triple": c_triple, "call_r11": c_r11,
            "fields": fields, "danger_coarse": danger, "nlines": len(lines),
        })
    # 汇总
    print("=== SCAN_META ===")
    print("ROOT=%s" % ROOT)
    print("dirsVisited=%d scannedPy=%d prunedItems=%d depthCap=%d maxBytes=%d" %
          (dirs_visited, len(files), len(pruned), DEPTH_CAP, MAX_BYTES))
    # A: 调用 link()/link_triple() 的返回值的件（含直接调用或 import 后间接）
    callers = [r for r in rows if r["call_link"] > 0 or r["call_triple"] > 0]
    print("\n=== A. 调用 link()/link_triple() 的件 (n=%d) ===" % len(callers))
    for r in sorted(callers, key=lambda x: x["file"]):
        print("%s | link=%d triple=%d | imp_re=%s imp_sl=%s imp_r11=%s | fields=%s" %
              (r["file"], r["call_link"], r["call_triple"],
               r["imp_re_linked"], r["imp_sl_link"], r["imp_r11"], r["fields"]))
    # B: 读 path / verified_path 的件
    pathreaders = [r for r in rows if ("path" in r["fields"] or "verified_path" in r["fields"]) and (r["call_link"] or r["call_triple"] or r["call_r11"] or r["imp_r11"] or r["imp_sl_link"] or r["imp_re_linked"])]
    print("\n=== B. 读 rec['path']/rec['verified_path'] 且与联查/r11 相关的件 (n=%d) ===" % len(pathreaders))
    for r in sorted(pathreaders, key=lambda x: x["file"]):
        print("%s | path=%d verified_path=%d match=%d tier=%d | danger=%s" %
              (r["file"], r["fields"].get("path", 0), r["fields"].get("verified_path", 0),
               r["fields"].get("match", 0), r["fields"].get("tier", 0), r["danger_coarse"]))
    # C: 危险粗筛
    dangers = [r for r in rows if r["danger_coarse"]]
    print("\n=== C. 「match 与 path 同读」粗筛件 (n=%d) ===" % len(dangers))
    for r in sorted(dangers, key=lambda x: x["file"]):
        print("%s | fields=%s | call_link=%d call_triple=%d call_r11=%d" %
              (r["file"], r["fields"], r["call_link"], r["call_triple"], r["call_r11"]))
    # D: import 精确归类：谁真的 import _re_linked（产出 merged 的并入版）
    re_linked_importers = [r for r in rows if r["imp_re_linked"]]
    print("\n=== D. 引用 _re_linked / r33e_merge 的件 (n=%d) ===" % len(re_linked_importers))
    for r in sorted(re_linked_importers, key=lambda x: x["file"]):
        print("%s | fields=%s" % (r["file"], r["fields"]))
    print("\n=== PRUNED (first 20) ===")
    for x in pruned[:20]:
        print("  " + x)


if __name__ == "__main__":
    main()
