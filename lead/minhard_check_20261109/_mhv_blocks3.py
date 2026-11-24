# -*- coding: utf-8 -*-
# 独立复核 ③（v3）：精确块配对 / 正文段身份 / 旧指纹登记面
# 路径统一用 os.path.abspath + normpath，避免 D:/ 盘符解析差异
import hashlib
import os

BASE = os.path.normpath(os.path.abspath("D:/Project/ra2-campaign-forge"))

def P(rel):
    return os.path.normpath(os.path.join(BASE, *rel.split("/")))

def L(rel):
    with open(P(rel), "r", encoding="utf-8", newline="") as f:
        return f.read().split("\n")

print("BASE =", repr(BASE), "isdir =", os.path.isdir(BASE))
for rel in ["lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
            "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md"]:
    print("  PROBE", repr(P(rel)), "exists =", os.path.exists(P(rel)))

G1 = L("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md")[122]
G2 = L("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md")[214]

START_SET = [
 "<!-- ============ 草案正文 1 逐字转录开始 ============ -->",
 "<!-- ============ 草案正文 2 逐字转录开始 ============ -->",
 "<!-- ============ 草案正文 3 逐字转录开始 ============ -->",
 "<!-- ============ 草案正文 4 逐字转录开始 ============ -->",
 "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
 "#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓",
]
END_SET = [
 "<!-- ============ 草案正文 1 逐字转录结束 ============ -->",
 "<!-- ============ 草案正文 2 逐字转录结束 ============ -->",
 "<!-- ============ 草案正文 3 逐字转录结束 ============ -->",
 "<!-- ============ 草案正文 4 逐字转录结束 ============ -->",
 "## ↑↑↑ 草案正文结束 ↑↑↑",
 "#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑",
]

def blocks(ls):
    out, cur = [], None
    for i, s in enumerate(ls, 1):
        t = s.strip()
        if cur is None and t in START_SET:
            cur = i
        elif cur is not None and t in END_SET:
            out.append((cur, i)); cur = None
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
print("\n== A. 精确块配对 + 组①/组② 句子所在块 ==")
for rel in FILES:
    ls = L(rel)
    bl = blocks(ls)
    h1 = [i for i, s in enumerate(ls, 1) if s == G1]
    h2 = [i for i, s in enumerate(ls, 1) if s == G2]
    print(f"-- {rel}")
    print(f"   blocks = {bl}")
    print(f"   G1(边界句) lines={h1}  IN_BLOCK={[bool([(s,e) for s,e in bl if s<h<e]) for h in h1]}")
    print(f"   G2(§6.3句) lines={h2}  IN_BLOCK={[bool([(s,e) for s,e in bl if s<h<e]) for h in h2]}")

print("\n== B. §607 正文段（:13-26 / :111-124）与两件合订本对应区逐字比对 ==")
src = "\n".join(L("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md")[12:26])
asm = "\n".join(L("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md")[110:124])
for tag, t in [("src :13-26", src), ("asm :111-124", asm)]:
    print(f"  {tag}: bytes={len(t.encode())} sha256={hashlib.sha256(t.encode()).hexdigest()}")
print("  src == asm ?", src == asm)
for rel, s, e in [("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 184, 197),
                  ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", 117, 130)]:
    seg = "\n".join(L(rel)[s-1:e])
    print(f"  {rel}:{s}-{e}: bytes={len(seg.encode())} sha256={hashlib.sha256(seg.encode()).hexdigest()} == src ? {seg==src}")

print("\n== C. 旧指纹登记面（改 :25 后失效的登记值所在文件:行） ==")
for rel in ["lead/ledger_bound_20261109/_lb_build.py",
            "lead/ledger_bound_20261109/_lb2_TEMPLATE.md",
            "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
            "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",
            "lead/ledger_bound_20261109/_lb_VERIFY.md",
            "lead/ledger_bound_20261109/_lb_fp_out.txt"]:
    ls = L(rel)
    hit = [(i, s[:150]) for i, s in enumerate(ls, 1) if ("d5dc8f97" in s or "e9842d41" in s)]
    print(f"  {rel}: 命中 {len(hit)} 行 -> {[i for i,_ in hit]}")
    for i, s in hit[:5]:
        print(f"    [{i}] {s}")

print("\n== D. §609 正文副本（_ve:13-25 与合订本第 5 笔块）是否含『自本节起不再成立』 ==")
ve_body = "\n".join(L("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md")[12:25])
print("  _ve:13-25 bytes =", len(ve_body.encode()), "sha =", hashlib.sha256(ve_body.encode()).hexdigest())
print("  含过时关系句 ?", "自本节起不再成立" in ve_body)
for rel, s, e in [("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 259, 273),
                  ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", 190, 204)]:
    seg = "\n".join(L(rel)[s-1:e])
    print(f"  {rel}:{s}-{e} 含过时关系句 ? {'自本节起不再成立' in seg}, == ve_body ? {seg==ve_body}")
print("\nDONE")
