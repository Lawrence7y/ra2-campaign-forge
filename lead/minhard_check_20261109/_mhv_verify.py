# -*- coding: utf-8 -*-
# 独立复核 ④⑤⑥⑦ 综合：块成员 / §609 正文 / 台账未入账 / 执行顺序 / 越界
import os, hashlib, re
ROOT = r"D:\Project\ra2-campaign-forge"
def L(rel):
    return open(os.path.join(ROOT, rel.replace("/", os.sep)), "r", encoding="utf-8", newline="").read().split("\n")
def sha(rel):
    return hashlib.sha256(open(os.path.join(ROOT, rel.replace("/", os.sep)), "rb").read()).hexdigest()

G1L = L("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md")[122]

print("== A. 组① 边界句逐字同文的全部在盘载体，及是否在「整段复制/逐字照抄」块内 ==")
# 自己定义块判定：对每文件，找所有含「草案正文」并带「开始/照抄/从这里开始」的标记行，和「结束」标记行，配对
CARRIERS = [
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
 "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
 "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",
 "lead/s604_refsync_20261109/S604_REFSYNC_DRAFT.md",
 "lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md",
 "lead/gate_doc_name_fix_20261109/_dnv_sandbox36/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "lead/gate_doc_name_fix_20261109/_dnw_sandbox/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
]
START = ("逐字转录开始", "从这里开始整段复制", "逐字照抄，从下一行起")
END = ("逐字转录结束", "草案正文结束", "逐字照抄结束")
for rel in CARRIERS:
    ls = L(rel)
    hit = [i for i, s in enumerate(ls, 1) if s == G1L]
    starts = [i for i, s in enumerate(ls, 1) if any(m in s for m in START)]
    ends = [i for i, s in enumerate(ls, 1) if any(m in s for m in END)]
    print(f"-- {rel}")
    print(f"   边界句命中行={hit}  开始标记={starts}  结束标记={ends}")
    for h in hit:
        enclosing = [(s, e) for s, e in zip(starts, ends) if s < h < e]
        print(f"   line {h} IN_BLOCK = {bool(enclosing)}  块={enclosing}")
print("\n== B. §609 正文块自述与其内部过时边界句的关系 ==")
ve = L("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md")
print("  _ve_DRAFT_S609.md:1 =", ve[0])
for i, s in enumerate(ve, 1):
    if "草案正文" in s and ("开始" in s or "结束" in s or "复制" in s):
        print(f"  marker [{i}] {s!r}")
print("  含『自本节起不再成立』的行：", [i for i, s in enumerate(ve, 1) if "自本节起不再成立" in s])
print("  含『本文件本身不是台账』的行：", [i for i, s in enumerate(ve, 1) if "本文件本身不是台账" in s])
lbv = L("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md")
print("  LEDGER_BOUND_VOLUME.md 第 5 笔 §609 块：出处行=[28,30]，正文块标记行=",
      [i for i, s in enumerate(lbv, 1) if i > 255 and any(m in s for m in START + END)])
print("  LEDGER_BOUND_VOLUME.md:34 =", lbv[33])
print("  LEDGER_BOUND_VOLUME.md:10 =", lbv[9])

print("\n== C. 两台账是否已有 §605-§610 / 码形定谳 / dur 字典 / 512655 ==")
pat = re.compile(r"§60[5-9]|§610|码形定谳|dur 字典|512655")
for rel in ("lead/GOAL_THREE_TARGETS_20261018.md", "lead/PENDING_DECISIONS.md"):
    hits = [(i, s[:120]) for i, s in enumerate(L(rel), 1) if pat.search(s)]
    print(f"  {rel}: 命中数={len(hits)}  前 5 = {hits[:5]}")

print("\n== D. 「4 件 / 6 件」件数核算（独立按文件去重） ==")
g1 = ["lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md"]
g2 = ["lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", "lead/ledger_appendix_20261108/_lad_tpl.md"]
g3 = ["lead/s604_attribution_20261108/S604_ATTRIBUTION.md"]
union3 = sorted(set(g1 + g2 + g3))
print("  三组并集 =", len(union3), union3)
print("  严格交集口径（组①）= ", len(g1), g1)
extra = ["lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md"]
print("  + 两件合订本 =", len(set(union3 + extra)), sorted(set(union3 + extra)))
print("  另：_lb2_TEMPLATE.md 是否含 G1 句本体？", G1L in L("lead/ledger_bound_20261109/_lb2_TEMPLATE.md"))
print("      _lb2_TEMPLATE.md:154-158 =", [L("lead/ledger_bound_20261109/_lb2_TEMPLATE.md")[i-1] for i in (154,155,156,157,158)])
print("      _lb2_TEMPLATE.md 登记的正文段指纹行 =", [(i,s) for i,s in enumerate(L("lead/ledger_bound_20261109/_lb2_TEMPLATE.md"),1) if "e9842d41" in s or "d5dc8f97" in s][:6])

print("\n== E. 越界检查：指纹收尾复算（11 件基线） ==")
BASE = {
 "lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md": ("8ccf9866ebd7860f03d71e939960e018fd0cfbbe6b94add04dd50f7004c11ac5", 61819),
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": ("d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703),
 "lead/ledger_appendix_20261108/_lad_tpl.md": ("a2313396db2ad9535ea211daf027d3956d4c84fb9927a138403ff1ee72ec083a", 25723),
 "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": ("8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182),
 "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md": ("47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70", 70587),
 "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md": ("7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43", 60272),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
}
ok = True
for rel, (h0, b0) in BASE.items():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    b = open(p, "rb").read()
    h = hashlib.sha256(b).hexdigest()
    m = (h == h0 and len(b) == b0)
    ok &= m
    print(f"  {'MATCH' if m else 'DIFF '} {rel} sha={h} bytes={len(b)}")
print("  ALL_UNCHANGED =", ok)
