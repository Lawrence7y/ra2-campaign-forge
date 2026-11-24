# -*- coding: utf-8 -*-
r"""_dgv_struct.py — 复核第二步(c)「结构性证明」是否覆盖被声称的交付形态。
核 4 点：
  S1 一行替换后 r10_context/r12_scan 是否会调用 dg_double_neg / _mask_quotes / _scope /
     DG_SECOND_SUBJ_RE / DG_COORD_RE（用源码 + 函数 __code__.co_names 实查）。
  S2 负向前瞻 veto（PSEUDO_DN / _SECOND）与第二主语/并列 veto 在 T12 上能否触发。
  S3 设计稿 ⑤ 风险表宣称的「随表一起验的单元断言」是否真的存在于代码。
  S4 部件表本身是否真的「不含实词」（MID / NEG2 逐项列出供人工判定）。
零真机、零采样；只读既有件 + 本写域；输出只落写域。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_struct.py
"""
import sys, json, hashlib, importlib.util, re, ast
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dneg_generative_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
assert hashlib.sha256(G7P.read_bytes()).hexdigest() == \
    "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


G7 = _load("_dgvs_g7", G7P)
DG = _load("_dgvs_core", WD / "_dg_core.py")
PS = _load("_dgvs_ps", WD / "_dg_pasteable.py")

print("=== S1 一行替换后，既有函数到底调用了什么 ===")
names = {n: sorted(G7.r10_context.__code__.co_names) for n in ("r10_context",)}
names["r12_scan"] = sorted(G7.r12_scan.__code__.co_names)
for k, v in names.items():
    print("  %s co_names = %s" % (k, v))
guards = ["dg_double_neg", "_mask_quotes", "_scope", "DG_SECOND_SUBJ_RE",
          "DG_COORD_RE", "DG_QUOTE_RE", "DG_BREAK_RE"]
for g in guards:
    print("  guard %-20s 在 r10_context 中 = %-5s ; 在 r12_scan 中 = %-5s ; 在 _dg_core.py 中定义 = %s" %
          (g, g in names["r10_context"], g in names["r12_scan"], hasattr(DG, g)))
# 既有 r10_context 只消费 DOUBLE_NEG_RE（:92）；r12_scan 只经 r10_context 的 kind
print("  → 结论：一行替换只改变 DOUBLE_NEG_RE 对象；dg_double_neg 的 5 个 guard 全部【不被既有调用链引用】")

print("\n=== S2 veto 在 T12 上的可达性 ===")
# T12 的 hit_text = N1·MID·N2，不含 N2 之后的任何字符；第二主语/并列标记典型出现在 N2 之后或之前
t12_hits = []
for s in ["并不否认甲方不宣告已生效", "并不否认本笔不宣告已生效",
          "本件不承认、并不否认均不成立已生效", "并不否认对方不宣告已生效"]:
    r = DG.dg_double_neg(s)
    t12_hits.append({"text": s, "hit": r["hit"], "hit_text": r["hit_text"],
                     "template": r["template"], "reason": r["reason"]})
    print("  text=%r → hit=%s hit_text=%r tmpl=%s reason=%s" %
          (s[:34], r["hit"], r["hit_text"], r["template"], r["reason"][:40]))
# 检查 hit_text 里是否可能含第二主语 / 并列标记（穷举 T12 全部生成串的 hit_text 形态）
print("  第二主语 veto 只检查 hit_text；T12 hit_text 由 NEG1+MID+NEG2 组成。")
print("  _SECOND 词表 =", DG.DG_SECOND_SUBJ_RE.pattern)
print("  _SECOND 中任一项是否可能由 NEG1+MID+NEG2 拼出：",
      [w for w in ["本笔", "本件", "台账", "母本", "本域", "审阅回件", "复核回件"]
       if any(w in (a + b + c) for a in DG.NEG1 for b in DG.MID for c in DG.NEG2)])
print("  并列标记 veto 只检查 hit_text；并列标记是否出现在 MID/NEG1/NEG2 中：",
      [x for x in ["/", "／", "、", "或", "以及", "同时", "并且", "一是", "二是", "其一", "其二"]
       if x in DG.NEG1 or x in DG.MID or x in DG.NEG2])
print("  → 结论：对 T12 而言，dg_double_neg 的两条二次 veto 结构性不可达（hit_text 不含它们）。")

print("\n=== S3 设计稿风险表宣称的「随表一起验的单元断言」 ===")
for name, path in (("core", WD / "_dg_core.py"), ("pasteable", WD / "_dg_pasteable.py")):
    t = path.read_text("utf-8")
    has_assert = "assert" in t
    has_unit = bool(re.search(r"(unit|自检|自验|check_table|validate_table|_check_)", t, re.I))
    print("  %-10s 含 assert=%-5s 含自检/单元函数=%-5s 行数=%d" %
          (name, has_assert, has_unit, len(t.splitlines())))
print("  _dg_DESIGN.md:306 原文声明：把「MID 不得含实词」「COMP ≤4 且排除 BQ/第二主语」"
      "「GOVERN ≤24 且非通配」写成单元断言，随表一起验 —— 代码中未见相应 assert。")

print("\n=== S4 MID / NEG2 是否真的「不含实词」 ===")
print("  MID (%d) = %s" % (len(DG.MID), DG.MID))
print("  NEG2(%d) = %s" % (len(DG.NEG2), DG.NEG2))
real_content = [w for w in DG.NEG2 if len(w) >= 2 and w not in
                ("没有", "毫无", "不是", "不可", "不行", "不成", "不可谓", "不是说")]
print("  NEG2 中 ≥2 字且是「完整否定谓语/实词短语」的项：", real_content)
print("  → 这些项本身就是独立否定谓语（不承认/不认为/不宣告/不出现/否认），"
      "与 _dg_DESIGN.md:150「两个否定之间隔着实词就拼不出」的论证前提不完全一致。")

# 一行替换在这些「实词 NEG2」上的实际表现
print("\n=== S4-b 「NEG1 + ε + 实词NEG2」生成串举例 ===")
samples = []
for n1 in ("并不", "并", "未", "没", "不", "非"):
    for n2 in ("否认", "不承认", "不认为", "不宣告", "不出现"):
        s = n1 + n2
        if DG.DG_DROPIN_RE.search(s):
            samples.append(s)
print("  ", samples[:30])
print("  计数 =", len(samples))

out = {"co_names": names, "guards": guards,
       "guard_in_r10": {g: g in names["r10_context"] for g in guards},
       "guard_in_r12": {g: g in names["r12_scan"] for g in guards},
       "t12_hits": t12_hits,
       "has_assert": {n: "assert" in (WD / f"_dg_{'core' if n == 'core' else 'pasteable'}.py").read_text("utf-8")
                      for n in ("core", "pasteable")},
       "mid": list(DG.MID), "neg2": list(DG.NEG2), "real_content_neg2": real_content,
       "samples": samples}
(WD / "_dgv_struct_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgv_struct_out.json")
