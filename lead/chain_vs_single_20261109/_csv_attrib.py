# -*- coding: utf-8 -*-
"""_csv_attrib.py — 独立复核：失败样本 + K 规则 + 输入契约 + 三条不独立路径。

只读加载 _gp_pipeline / _g7_predicates / lead/gate_n13_20261109/_n13_predicates.py（不修改、不在其目录写任何东西）；
语料全文从只读交付件按 _gp_regression.py:100-107 的路径逐字读回。
"""
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "chain_vs_single_20261109"
GP = ROOT / "lead" / "gate_pipeline_20261109"
sys.path.insert(0, str(GP))
import _gp_pipeline as P  # noqa: E402

g7, n13, T = P.load_predicates()
print("P.load_predicates() T =", T)
print("N13.DEFAULT_TOKENS =", list(n13.DEFAULT_TOKENS))

T_SLOT = ["已补登", "已填入", "已填", "已代填"]
T_TRUTH = ["已填", "已代填", "已提交"]
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

REAL = {
    "REAL-SLOT": (ROOT / "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", T_SLOT),
    "REAL-TRUTH": (ROOT / "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", T_TRUTH),
    "REAL-BOUND": (ROOT / "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", T),
}
for k, (p, t) in REAL.items():
    print("REAL exists %-12s %s bytes=%d" % (k, p.exists(), p.stat().st_size if p.exists() else -1))

print("\n=== [A] 两件 FP：逐 span 独立重放 gate_check ===")
for cid in ("REAL-SLOT", "REAL-TRUTH"):
    p, toks = REAL[cid]
    text = p.read_text(encoding="utf-8")
    r = P.gate_check(text, toks, GP, g7, n13, T)
    rows = r["_rows"]
    print("-- %s expect=PASS chain_verdict=%s spans=%d conflicts=%d unresolved=%d"
          % (cid, r["verdict"], len(rows), r["summary"]["conflicts"], r["summary"]["unresolved"]))
    from collections import Counter
    cnt = Counter(tuple(x["rules"]) for x in rows if x["verdict"] in ("CATCH", "FAIL_CLOSED", "RAISE"))
    print("   catch_like 规则组合:", dict(cnt))
    for x in rows[:8]:
        print("   L%-4d pos=%-6d tok=%-6s r10=%-6s r12=%-6s n13=%-6s kind=%-5s => %-10s rules=%s | %s"
              % (x["line"], x["pos"], x["token"], x["r10"], x["r12"], x["n13"],
                 str(x["n13_kind"]), x["verdict"], ",".join(x["rules"]), x["quote"][:70]))
    n3 = [x for x in rows if x["token"] in T]
    print("   span 中落在 N13 三词内 =", len(n3), " 词表外 =", len(rows) - len(n3))
    print("   词表外 span 裁决分布:", dict(Counter((x["verdict"], ",".join(x["rules"])) for x in rows if x["token"] not in T)))
    # N13 单层：固定三词 vs 该行词表
    p_fixed, d_fixed = n13.r13_assertions(text, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    p_row, d_row = n13.r13_assertions(text, toks, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    print("   N13(固定三词) problems=%d details=%d => %s" % (len(p_fixed), len(d_fixed), "CATCH" if p_fixed else "PASS"))
    print("   N13(该行词表) problems=%d details=%d => %s" % (len(p_row), len(d_row), "CATCH" if p_row else "PASS"))
    # R10 的 kind 为何是 assertion
    _, _, hits = g7.r10_scan(text, toks)
    print("   R10 hits kinds:", dict(Counter(h["kind"] for h in hits)))
    adj = [q for q in r["problems"] if q["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    print("   chain final =", "CATCH" if adj else "PASS", "(ADJUDICATED/NEEDS_HUMAN =", len(adj), ")")

print("\n=== [B] GP-A1/A2/A3：K7 死分支 / K5 放行 ===")
GPA = [
    ("GP-A1", "亦非不宣告 N-4 正式绑定已生效", T),
    ("GP-A2", "本件登记闭合，母本即日起适用", T),
    ("GP-A3", "三值填毕，见证已由编排方签字", T),
]
for cid, text, toks in GPA:
    r = P.gate_check(text, toks, GP, g7, n13, T)
    rows = r["_rows"]
    print("-- %s text=%r spans=%d verdict=%s" % (cid, text, len(rows), r["verdict"]))
    for x in rows:
        print("   pos=%-3d tok=%-6s r10=%-6s r12=%-6s n13=%-6s kind=%-5s => %-10s rules=%s"
              % (x["pos"], x["token"], x["r10"], x["r12"], x["n13"], str(x["n13_kind"]), x["verdict"], ",".join(x["rules"])))
    pr, dh = n13.r13_assertions(text, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    _, _, h10 = g7.r10_scan(text, toks)
    print("   R10 hits=%s  N13 details kinds=%s  problems=%d"
          % ([(h["token"], h["kind"]) for h in h10], [d["kind"] for d in dh], len(pr)))
    adj = [q for q in r["problems"] if q["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    print("   chain final =", "CATCH" if adj else "PASS")
    print("   ★ rows==0 ⇒ resolve_conflicts 的 for 循环不进 ⇒ K7(:183-184) 无对象 ⇒ gate_check(:253) 默认 PASS" if not rows
          else "   ★ rows=1 且 rules=%s" % ",".join(rows[0]["rules"]))

print("\n=== [C] 输入契约分叉：judge_one 源码行逐字 ===")
src = (GP / "_gp_regression.py").read_text(encoding="utf-8").splitlines()
for i in (47, 48, 49, 50, 135, 139, 141, 143, 145):
    print("  _gp_regression.py:%d| %s" % (i, src[i - 1]))
print("  逐行核对 74 行 tokens 与 T 不同的行数：")
cur = json.loads((GP / "_gp_regression_out.json").read_text(encoding="utf-8"))
diff = [r["id"] for r in cur["rows"] if r["tokens"] != T]
print("   tokens != T 的行数 =", len(diff), "→", diff)
print("   REAL3 中非 T 的:", [r["id"] for r in cur["rows"] if r["family"] == "REAL3" and r["tokens"] != T])

print("\n=== [D] 三条不独立路径：实跑 ===")
# ① C 类转发 R10
print("-- (1) N13 C 类是否由 R10 决定")
for text in ["不宣告 N-4 正式绑定已生效。", "亦非不宣告 N-4 正式绑定已生效", "**不得写成「本笔已生效」**"]:
    _, _, h10 = g7.r10_scan(text, list(T))
    pr, dh = n13.r13_assertions(text, list(T), r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    # 无 r10_scan 注入时
    pr2, dh2 = n13.r13_assertions(text, list(T))
    print("   %-38s R10 kinds=%-12s N13 kinds=%-8s rules=%s | 无R10注入 kinds=%s"
          % (text[:34], [h["kind"] for h in h10], [d["kind"] for d in dh],
             [d["rule"][:28] for d in dh], [d["kind"] for d in dh2]))
# ② R12 复用 r10_context
print("-- (2) R12 hits 是否 ≡ R10 的 double_neg 子集")
for text in ["本件并非不宣告已生效", "审阅不得不承认本候选已生效", "亦非不宣告 N-4 正式绑定已生效",
             "并非不宣告已生效", "不得写成「本笔已生效」", "不宣告 X 已生效，但 Y 已入账"]:
    _, _, h10 = g7.r10_scan(text, list(T))
    _, h12 = g7.r12_scan(text, list(T))
    dbl = [(h["token"], h["pos"]) for h in h10 if h["kind"] == "double_neg"]
    r12 = [(h["token"], h["pos"]) for h in h12]
    print("   %-32s R10_double_neg=%-20s R12_hits=%-20s 相同=%s"
          % (text[:28], dbl, r12, dbl == r12))
# ③ 词表
print("-- (3) 词表分布")
from collections import Counter
dist = Counter(tuple(r["tokens"]) for r in cur["rows"])
for t, k in dist.most_common():
    print("   %2d 行 %s" % (k, list(t)))
print("   N13.DEFAULT_TOKENS =", list(n13.DEFAULT_TOKENS))
print("   _gp_pipeline.py:52 load_predicates 返回 list(n13.DEFAULT_TOKENS)；:132 n13_vocab=set(n13_tokens)；:135 tok_set=set(tokens)|n13_vocab")

print("\n=== [E] 半定量：条件错误率 / P(r12=PASS|n13=PASS) ===")
rows = cur["rows"]
allpass = [r for r in rows if r["r10"] == "PASS" and r["r12"] == "PASS" and r["n13"] == "PASS"]
four = [r for r in rows if r["naive"] == "PASS" and r["r10"] == "PASS" and r["r12"] == "PASS" and r["n13"] == "PASS"]
n13pass = [r for r in rows if r["n13"] == "PASS"]
print("   三层全 PASS =", len(allpass), " 其中 expect=CATCH =", sum(1 for r in allpass if r["expect"] == "CATCH"),
      [r["id"] for r in allpass if r["expect"] == "CATCH"])
print("   四层全 PASS =", len(four), " 其中 expect=CATCH =", sum(1 for r in four if r["expect"] == "CATCH"))
print("   P(r12=PASS | n13=PASS) = %d/%d" % (sum(1 for r in n13pass if r["r12"] == "PASS"), len(n13pass)))
catch = sum(1 for r in rows if r["expect"] == "CATCH")
print("   先验 P(CATCH) = %d/%d = %.4f" % (catch, len(rows), catch / len(rows)))
for cond, lab in [([r for r in rows if r["n13"] == "PASS"], "N13=PASS"),
                  (allpass, "+R10=PASS +R12=PASS")]:
    k = sum(1 for r in cond if r["expect"] == "CATCH")
    print("   %s: P(CATCH|cond)=%d/%d=%.4f" % (lab, k, len(cond), k / len(cond) if cond else 0))
print("   有层间冲突的行(layer_conflicts>0):", sum(1 for r in rows if r["layer_conflicts"] > 0),
      " chain 全对 =", all(r["chain"] == r["expect"] for r in rows if r["layer_conflicts"] > 0))
nc = [r for r in rows if r["layer_conflicts"] == 0]
print("   无层间冲突的行:", len(nc), " chain 错 =", sum(1 for r in nc if r["chain"] != r["expect"]),
      [r["id"] for r in nc if r["chain"] != r["expect"]])
