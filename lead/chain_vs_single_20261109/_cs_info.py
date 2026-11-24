# -*- coding: utf-8 -*-
# _cs_info.py : 「三层都过」的有效独立层数定量（似然比法）+ 词表共享面统计
import os, json, pathlib, math, collections
ROOT = r"D:\Project\ra2-campaign-forge"
os.chdir(ROOT)
WD = pathlib.Path(ROOT) / "lead" / "gate_pipeline_20261109"
O = json.loads((WD / "_gp_regression_out.json").read_text(encoding="utf-8"))
R = O["rows"]

def p_catch_given(pred):
    sub = [r for r in R if pred(r)]
    k = sum(1 for r in sub if r["expect"] == "CATCH")
    return k, len(sub), (k / len(sub) if sub else float("nan"))

base = p_catch_given(lambda r: True)
print("先验 P(expect=CATCH) = %d/%d = %.4f" % base)
cases = [
    ("n13=PASS", lambda r: r["n13"] == "PASS"),
    ("n13=PASS & r10=PASS", lambda r: r["n13"] == "PASS" and r["r10"] == "PASS"),
    ("n13=PASS & r10=PASS & r12=PASS", lambda r: r["n13"] == "PASS" and r["r10"] == "PASS" and r["r12"] == "PASS"),
    ("四层全 PASS", lambda r: all(r[c] == "PASS" for c in ("naive", "r10", "r12", "n13"))),
]
for name, pred in cases:
    k, n, p = p_catch_given(pred)
    print("  %-38s P(CATCH|条件)=%d/%d=%.4f  信息增益(相对先验)=%.4f" %
          (name, k, n, p, base[2] - p))

# 似然比：每加一层，把「真断言却全 PASS」的概率压低多少
p0 = base[2]
p1 = p_catch_given(cases[0][1])[2]
p2 = p_catch_given(cases[1][1])[2]
p3 = p_catch_given(cases[2][1])[2]
print("\n逐层后验: 先验=%.4f → N13=%.4f → +R10=%.4f → +R12=%.4f" % (p0, p1, p2, p3))
print("  每层似然比(后验压低倍数): N13=%.3f, +R10=%.3f, +R12=%.3f" %
      (p1 / p0, p2 / p1, p3 / p2))
# 若 k 个真正独立、且每层单独压低倍数 = p1/p0，则 k 层应给 (p1/p0)^k
lr1 = p1 / p0
if 0 < lr1 < 1:
    k_eff = math.log(p3 / p0) / math.log(lr1)
    print("  等效独立层数 k_eff = ln(%.4f)/ln(%.4f) = %.2f （相对 N13 单层的信息量倍数）" %
          (p3 / p0, lr1, k_eff))
print("  R12 加入后 P 完全不变（%.4f→%.4f）⇒ R12 对「都过」事件的增量信息 = 0 bit" % (p2, p3))
print("  ⇒ 三层里至少一层是纯冗余；有效独立层数 ≈ 1～1.5 层，不是 3 层。")

# 误差相关性：三层全 PASS 仍漏 3 条，占全部 CATCH 类的比例
fn_all = [r["id"] for r in R if all(r[c] == "PASS" for c in ("r10", "r12", "n13")) and r["expect"] == "CATCH"]
print("\n三层全 PASS 仍漏: %s（共 %d 条，占该层条件样本 %.1f%%）" %
      (fn_all, len(fn_all), 100.0 * p3))

# 词表共享面
c = collections.Counter(tuple(r["tokens"]) for r in R)
print("\n词表共享面（74 行）:")
for k, v in c.most_common():
    print("  %2d 行 tokens=%s %s" % (v, list(k), "<== 与 N13.DEFAULT_TOKENS 完全相同" if list(k) == ["已入账", "已追加", "已生效"] else ""))
print("  → %d/74 = %.1f%% 的行，提取器 / R10 / R12 / N13 用的是同一套三词字面词表" %
      (c[("已入账", "已追加", "已生效")], 100.0 * c[("已入账", "已追加", "已生效")] / 74))

# 「层间冲突」与正确性
conf = [r for r in R if r["layer_conflicts"] > 0]
print("\n层间冲突行 = %d/74，其中 chain 判对 = %d，判错 = %d" %
      (len(conf), sum(1 for r in conf if r["chain"] == r["expect"]),
       sum(1 for r in conf if r["chain"] != r["expect"])))
print("无冲突行 = %d/74，其中 chain 判错 = %d (%s)" %
      (74 - len(conf), sum(1 for r in R if r["layer_conflicts"] == 0 and r["chain"] != r["expect"]),
       [r["id"] for r in R if r["layer_conflicts"] == 0 and r["chain"] != r["expect"]]))
