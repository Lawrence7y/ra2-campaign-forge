# -*- coding: utf-8 -*-
"""_nnv_counterexamples.py — 独立构造「不该被归一化合并」的样本，测撰写人方案。
不 import 撰写人模块；L1 按 REPORT:190-205 规格独立重写；角色判定用
_rs_carrier_scan.py:164-189 的原函数（importlib 直导，不改文件）。
只读，纯内存，stdout。python -I -X utf8。
"""
import sys, re, importlib.util
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SCAN = r"D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py"
spec = importlib.util.spec_from_file_location("rs_scan_nnv", SCAN)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
classify_line = m.classify_line

CANON = "只能判「不可复现」"
QOPEN = "「『“‘"; QCLOSE = "」』”’"; QSYM = "`\"'"

def l1(s):
    o = []
    for c in s:
        if c in QOPEN: o.append("\x01")
        elif c in QCLOSE: o.append("\x02")
        elif c in QSYM: o.append("\x03")
        else: o.append(c)
    return "".join(o)

def find_norm(line, nd):
    n, q = l1(line), l1(nd)
    return n.find(q) >= 0

SUPP = re.compile(r"只能判[「『“(]?不可复现[」』”)]?")
W4 = re.compile(r"只能判.{0,3}不可复现")

def role(L, needles=None):
    if needles is None: needles = [CANON]
    # 用原文行 + 原文 needle（撰写人方案：角色判定一律在原始行）
    # 为让角色判定能跑，needle 需在该行内；对不含精确 needle 的变体，
    # 采用「把变体本身也作为 needle」= 宽候选阶段实际会给 pos 的做法。
    c = classify_line(L, needles, "")
    return c["role"] if c else "<classify_line returned None>"

print("### 独立反例：撰写人 L1 方案是否把不同意思的句子当成同一句")
print("L1 canon key =", repr(l1(CANON)))
print("")

# ---- 3 个主反例（ask ⑤ 要求）+ 2 个补充 ----
# 每个 CASE: (id, A, B, 两句为何不同, A 应属角色, B 应属角色)
CASES = [
 ("V1 核心汉字不同命题", "只能判「不可复现」", "只能判「不可复原」",
  "不可复现=数值复算不出；不可复原=历史现场无法还原（真实语料 5 行）。不同命题。",
  "QUOTED", "QUOTED"),
 ("V2 引号内 vs 引号外（断言 vs 引述否定）",
  "**只能判「不可复现」、不能定位当年错误步骤**",
  "其边界句「只能判『不可复现』、不能定位当年错误步骤」自本节起不再成立",
  "A 是 §607 裸断言(needs_fix 候选)；B 是 §609 引 A 来否定它(REFUTING_QUOTE)。不同 role。",
  "ASSERTION", "REFUTING_QUOTE"),
 ("V3 无引号裸串 vs 带引号",
  "只能判不可复现、不能定位当年错误步骤",
  "只能判「不可复现」、不能定位当年错误步骤",
  "B 的 needle 落在成对引号跨度内(QUOTED)，A 无跨度(非 QUOTED)；删引号后才同键。",
  "ASSERTION", "QUOTED"),
 ("V4 半错配引号（左『右」）",
  "只能判「不可复现」",
  "只能判『不可复现」",
  "B 引号不成对，spans_of_quotes 找不到跨度 → 按 REPORT:250 应报 UNKNOWN，不得猜成 ASSERTION。",
  "QUOTED", "UNKNOWN/不得猜"),
 ("V5 单弯引号 ‘’（不在 _rs_carrier_scan.py:79 PAIRS 里）",
  "只能判「不可复现」",
  "只能判‘不可复现’",
  "B 的 ‘’ 不在 PAIRS=[「」,『』,``,“”] 中 → 原文 R5 判不出 quote span，会掉到 ASSERTION。",
  "QUOTED", "QUOTED(但 R5 会给 ASSERTION)"),
 ("V6 整句被引号罩住 vs 只罩核心词",
  "只能判「不可复现」、不能定位当年错误步骤",
  "只能判「不可复现、不能定位当年错误步骤」",
  "A 引号 span 只盖 4 字；B 盖整句。CE2 同型：span 不同 ⇒ role 不同。",
  "QUOTED", "QUOTED(span 不同)"),
]

print("=== 逐例：L1 键 / 召回 / 原文角色 ===")
for cid, A, B, why, ra, rb in CASES:
    ka, kb = l1(A), l1(B)
    full_key_merged = (ka == kb)
    ha, hb = find_norm(A, CANON), find_norm(B, CANON)
    sa, sb = bool(SUPP.search(A)), bool(SUPP.search(B))
    wa, wb = bool(W4.search(A)), bool(W4.search(B))
    # 角色：把该行自身出现的变体串也作为 needle，模拟「宽候选给 pos」后 classify_line(原文)
    needle_variants = [CANON, "只能判『不可复现』", "只能判“不可复现”",
                       "只能判不可复现", "只能判‘不可复现’", "只能判『不可复现」"]
    ga = role(A, needle_variants)
    gb = role(B, needle_variants)
    # quote span 检测（原文，直接调 spans_of_quotes）
    spa = m.spans_of_quotes(A)
    spb = m.spans_of_quotes(B)
    print("-- %s --" % cid)
    print("   A = %r" % A)
    print("   B = %r" % B)
    print("   L1 全行 key(A)=%r" % ka)
    print("   L1 全行 key(B)=%r ; FULL_LINE_KEY_MERGED=%s" % (kb, full_key_merged))
    print("   find_norm(canon) 命中 A=%s B=%s ; W4 命中 A=%s B=%s ; 补充轨命中 A=%s B=%s" %
          (ha, hb, wa, wb, sa, sb))
    print("   spans_of_quotes(原文A)=%s" % spa)
    print("   spans_of_quotes(原文B)=%s" % spb)
    print("   classify_line(原文A)=%s  classify_line(原文B)=%s  (期望 A≈%s / B≈%s)" % (ga, gb, ra, rb))
    print("   语义差异：%s" % why)
    print("")

print("=== 判定口径 ===")
print("  1) 若把『同一归一 key』当成 merge 判据：V1/V2/V3/V6 的 L1 全行 key 不同 → 不合并。")
print("  2) 但 L1 是召回键(find_norm(canon))，不是全行 key：只要 B 被 canon 召回，")
print("     就以 canon 身份进入 carriers。检查 V4/V5 是否被 canon 召回且原文 span 无效：")
for cid, A, B, why, ra, rb in CASES:
    if cid.startswith(("V4","V5")):
        print("     %s: B 被 canon 召回=%s ; B 原文 span=%s ; B 原文 classify_line=%s" %
              (cid, find_norm(B,CANON), m.spans_of_quotes(B), role(B,[CANON,"只能判『不可复现」","只能判‘不可复现’"])))
print("")
print("=== 附：撰写人 CE1-CE7 的 L1_MERGED 断言是否成立（全行 key 口径） ===")
CE = [
 ("CE1","只能判「不可复现」、不能定位当年错误步骤","只能判不可复现、不能定位当年错误步骤"),
 ("CE2","只能判「不可复现」、不能定位当年错误步骤","只能判「不可复现、不能定位当年错误步骤」"),
 ("CE3","只能判「不可复现」","只能判「不可复原」"),
 ("CE4","规则 APPROVE_SCOPE 已生效","规则 ＡＰＰＲＯＶＥ＿ＳＣＯＰＥ 已生效"),
 ("CE5","**只能判「不可复现」、不能定位当年错误步骤**","其边界句「只能判『不可复现』、不能定位当年错误步骤」自本节起不再成立"),
 ("CE6","| 只能判 | 不可复现 |","只能判不可复现"),
 ("CE7","只能判「不可复现」","只能判』不可复现『"),
]
for cid,A,B in CE:
    print("  %s L1_MERGED=%s ; find_norm(canon) A=%s B=%s" % (cid,l1(A)==l1(B),find_norm(A,CANON),find_norm(B,CANON)))
