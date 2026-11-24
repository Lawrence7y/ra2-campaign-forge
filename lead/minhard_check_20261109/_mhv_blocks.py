# -*- coding: utf-8 -*-
# 独立复核 ③（修正版）：按「开始/结束标记严格交替」配对，判块成员
import os, hashlib
ROOT = "D:/Project/ra2-campaign-forge"
def L(rel):
    p = ROOT + "/" + rel
    if not os.path.exists(p):
        print("MISSING_PATH =", repr(p), "cwd =", repr(os.getcwd()), flush=True)
        print("DIR_LIST =", os.listdir(os.path.dirname(p))[:20] if os.path.isdir(os.path.dirname(p)) else "NO_DIR", flush=True)
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read().split("\n")

G1 = L("lead/ledger_appendix_20261108/LEDGER_APPEND_DRAFT.md")[122]
# 精确标记串（从实读取得）
START_SET = [
 "<!-- ============ 草案正文 3 逐字转录开始 ============ -->",
 "<!-- ============ 草案正文 1 逐字转录开始 ============ -->",
 "<!-- ============ 草案正文 2 逐字转录开始 ============ -->",
 "<!-- ============ 草案正文 4 逐字转录开始 ============ -->",
 "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
 "#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓",
]
END_SET = [
 "<!-- ============ 草案正文 3 逐字转录结束 ============ -->",
 "<!-- ============ 草案正文 1 逐字转录结束 ============ -->",
 "<!-- ============ 草案正文 2 逐字转录结束 ============ -->",
 "<!-- ============ 草案正文 4 逐字转录结束 ============ -->",
 "## ↑↑↑ 草案正文结束 ↑↑↑",
 "#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑",
]

def blocks(ls):
    out = []
    cur = None
    for i, s in enumerate(ls, 1):
        st = s.strip()
        if cur is None and st in START_SET:
            cur = i
        elif cur is not None and st in END_SET:
            out.append((cur, i))
            cur = None
    return out

FILES = [
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
 "lead/ledger_appendix_20261108/_lad_tpl.md",
 "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
 "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",
 "lead/ledger_bound_20261109/_lb2_TEMPLATE.md",
 "lead/gate_doc_name_fix_20261109/_dnv_sandbox36/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "lead/gate_doc_name_fix_20261109/_dnw_sandbox/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md",
 "lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md",
 "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
]
print("== 精确块配对 + G1 边界句所在块 ==")
for rel in FILES:
    ls = L(rel)
    bl = blocks(ls)
    g1 = [i for i, s in enumerate(ls, 1) if s == G1]
    print(f"-- {rel}")
    print(f"   blocks = {bl}   G1_lines = {g1}")
    for h in g1:
        enc = [(s, e) for s, e in bl if s < h < e]
        print(f"   G1@{h} IN_BLOCK = {bool(enc)}  enclosing = {enc}")

print("\n== 组② 句子（LEDGER:215）所在块 ==")
G2 = L("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md")[214]
for rel in ["lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", "lead/ledger_appendix_20261108/_lad_tpl.md"]:
    ls = L(rel)
    bl = blocks(ls)
    hits = [i for i, s in enumerate(ls, 1) if s == G2]
    print(f"-- {rel} blocks={bl} G2_lines={hits}")
    for h in hits:
        print(f"   G2@{h} IN_BLOCK = {bool([(s,e) for s,e in bl if s<h<e])}")

print("\n== §607 正文段（:13-26 / :111-124）与两件合订本 §607 块逐字比对 ==")
src = "\n".join(L("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md")[12:26])  # :13-26
asm = "\n".join(L("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md")[110:124])  # :111-124
print("  src bytes =", len(src.encode()), "sha =", hashlib.sha256(src.encode()).hexdigest())
print("  asm bytes =", len(asm.encode()), "sha =", hashlib.sha256(asm.encode()).hexdigest())
print("  src == asm ?", src == asm)
for rel, s, e in [("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 184, 197),
                  ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", 117, 130)]:
    seg = "\n".join(L(rel)[s-1:e])
    print(f"  {rel}:{s}-{e} bytes={len(seg.encode())} sha={hashlib.sha256(seg.encode()).hexdigest()} == src ? {seg == src}")

print("\n== _lb_build.py / _lb2_TEMPLATE.md 中旧指纹登记面（改 :25 后会失效） ==")
for rel in ["lead/ledger_bound_20261109/_lb_build.py", "lead/ledger_bound_20261109/_lb2_TEMPLATE.md",
            "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md"]:
    ls = L(rel)
    hit = [(i, s[:160]) for i, s in enumerate(ls, 1) if ("d5dc8f97" in s or "e9842d41" in s or "7703" in s or "4894" in s)]
    print(f"  {rel}: 命中 {len(hit)} 行")
    for i, s in hit[:8]:
        print(f"    [{i}] {s}")
