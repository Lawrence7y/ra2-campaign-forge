# -*- coding: utf-8 -*-
"""_mc_crosscheck.py — 精确判定「现盘是否真有消费方会收到 merged 并崩」（只读）。
检查：
  1) 哪些 .py 真正装载 _re_linked.py（唯一能产 merged 的模块）；
  2) 这些件是否把 merged rec 喂给任何 r11 消费表达式；
  3) 现盘所有 r11/联查 rec 的「直接下标」读（KeyError -prone）逐条列出；
  4) 交叉：同时调用 link 家族 与 r11_scan_plus 的件。
"""
import os
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
DEPTH_CAP = 6
PRUNE = {".git", "__pycache__", ".mimosa", "node_modules", ".tmp"}
MAXB = 400000

LOAD_RELINKED = re.compile(r"(_re_linked|r33e_merge[^\n]*_re_linked)")
LOAD_R11 = re.compile(r"r11_scan_plus|_f2_r11plus")
CALL_LINK = re.compile(r"(?<![A-Za-z_])(?:SL|RE|sl|m|mod|plus)?\.?link(?:_triple)?\s*\(")
DIRECT = re.compile(r"""\[\s*['"](verified_path|recomputed|bytes)['"]\s*\]""")

def files():
    base = len(LEAD.parts)
    for dp, dns, fns in os.walk(LEAD):
        d = Path(dp)
        dns[:] = [x for x in dns if x not in PRUNE]
        if len(d.parts) - base > DEPTH_CAP:
            dns[:] = []
            continue
        for fn in fns:
            if fn.endswith(".py"):
                p = d / fn
                try:
                    if p.stat().st_size <= MAXB:
                        yield p
                except OSError:
                    pass

print("=== 1) 装载 _re_linked.py（唯一产 merged 的模块）的件 ===")
re_loaders = []
for p in files():
    t = p.read_text(encoding="utf-8", errors="replace")
    if LOAD_RELINKED.search(t) and ("import _re_linked" in t or "spec_from_file_location" in t and "_re_linked" in t):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        loads_r11 = bool(LOAD_R11.search(t))
        calls_r11 = "r11_scan_plus(" in t
        re_loaders.append(rel)
        print("  %s | loads_r11_module=%s calls_r11_scan_plus=%s" % (rel, loads_r11, calls_r11))
print("  COUNT=%d" % len(re_loaders))

print("\n=== 2) 直接下标读 verified_path / recomputed / bytes（KeyError-prone，非 .get）的件 ===")
print("    （merged rec 不含这三键 → 直接下标即 KeyError）")
for p in files():
    t = p.read_text(encoding="utf-8", errors="replace")
    hits = []
    for i, ln in enumerate(t.splitlines(), 1):
        for mm in DIRECT.finditer(ln):
            hits.append((i, mm.group(1), ln.strip()[:110]))
    if hits:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        loads_relinked = rel in re_loaders
        print("  --- %s | loads_RE_LINKED=%s ---" % (rel, loads_relinked))
        for i, k, s in hits[:8]:
            print("      L%d [%s]: %s" % (i, k, s))

print("\n=== 3) 交叉：同时出现 link 家族调用 与 r11_scan_plus 调用的件 ===")
for p in files():
    t = p.read_text(encoding="utf-8", errors="replace")
    has_link = bool(re.search(r"(?:SL|RE|sl|m|plus)\.link\(|(?:SL|RE|sl|m)\.link_triple\(", t))
    has_r11call = bool(re.search(r"\br11_scan_plus\s*\(", t))
    if has_link and has_r11call:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        print("  %s | has_link_call=%s has_r11_scan_plus_call=%s" % (rel, has_link, has_r11call))
