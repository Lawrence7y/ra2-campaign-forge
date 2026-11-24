# -*- coding: utf-8 -*-
"""_ma_verify.py — 口径审计独立重算（只读输入；唯一写域 lead/metric_audit_20261109/）
python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/metric_audit_20261109/_ma_verify.py
零真机 / 零采样代码；仅读 JSON + 纯统计（math / fractions / json / hashlib）。
"""
import hashlib, json, math, pathlib, statistics
from fractions import Fraction as F

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
GP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json"
EV = ROOT / "lead" / "evidence_indep_20261109" / "_eind_verify_out.json"

rows = json.loads(GP.read_text(encoding="utf-8"))["rows"]
E = [r for r in rows if r["expect"] == "CATCH"]
N = [r for r in rows if r["expect"] == "PASS"]
n, nE, nN = len(rows), len(E), len(N)

print("=== A. 逐层分子分母（独立实算，不采信上游摘要）===")
print("n =", n, " nE (expect=CATCH) =", nE, " nN (expect=PASS) =", nN,
      " pi =", F(nE, n), "=", nE / n)
per = {}
for lay in ("r10", "r12", "n13", "chain"):
    fp = sum(1 for r in N if r[lay] == "CATCH")
    fn = sum(1 for r in E if r[lay] == "PASS")
    c_pass = sum(1 for r in N if r[lay] == "PASS")
    per[lay] = {
        "fp": fp, "fn": fn,
        "fp_rate": F(fp, nN), "q": F(fn, nE), "c": F(c_pass, nN),
    }
    d = per[lay]
    print("  %-5s fp=%2d fp_rate=%-8s=%.6f | fn=%2d q_i=%-8s=%.6f | c_i=%-8s=%.6f" %
          (lay, fp, str(d["fp_rate"]), float(d["fp_rate"]), fn, str(d["q"]), float(d["q"]),
           str(d["c"]), float(d["c"])))

q10, q12, q13 = per["r10"]["q"], per["r12"]["q"], per["n13"]["q"]
f10, f12, f13 = per["r10"]["fp_rate"], per["r12"]["fp_rate"], per["n13"]["fp_rate"]
c10, c12, c13 = per["r10"]["c"], per["r12"]["c"], per["n13"]["c"]

print()
print("=== B. 正确口径乘积 vs 错误口径乘积 ===")
P2 = q10 * q13
P3 = q10 * q12 * q13
print("  q10*q13       =", str(P2), "=", float(P2))
print("  q10*q12*q13   =", str(P3), "=", float(P3))
print("  fp_rate(r10)*fp_rate(r12)*fp_rate(n13) =",
      "%.9f * %.9f * %.9f = %.9f" % (float(f10), float(f12), float(f13), float(f10 * f12 * f13)))
print("  零来自 fp_rate(r12)=0 与 fp_rate(r13)=0；其分母是 nN=35 且方向是 P(CATCH|notE)")

A3 = [r for r in rows if all(r[k] == "PASS" for k in ("r10", "r12", "n13"))]
W3 = [r for r in A3 if r["expect"] == "CATCH"]
A3E = [r for r in E if all(r[k] == "PASS" for k in ("r10", "r12", "n13"))]
A2 = {r["id"] for r in rows if r["r10"] == "PASS" and r["n13"] == "PASS"}
S3 = {r["id"] for r in A3}
print()
print("=== C. 观测事件 / 2 层 vs 3 层 / R12 下游 ===")
print("  all3PASS =", len(A3), " 其中 expect=CATCH =", len(W3), [r["id"] for r in W3])
print("  r10&n13 双 PASS 集合 == 三层 PASS 集合 ?", A2 == S3, "（|A2|=%d |S3|=%d）" % (len(A2), len(S3)))
print("  P(r12=PASS|n13=PASS) =", F(38, 38), " n13=PASS 中 r12=CATCH 行数 =",
      sum(1 for r in rows if r["n13"] == "PASS" and r["r12"] == "CATCH"))
print("  r12=CATCH 的 4 行全部 r10=PASS ?",
      all(r["r10"] == "PASS" for r in rows if r["r12"] == "CATCH"))
print("  P(all3PASS|E) =", F(len(A3E), nE), "=", len(A3E) / nE)
print("  P(E|allPASS)  =", F(len(W3), len(A3)), "=", len(W3) / len(A3))
print("  P(correct|allPASS) =", F(len(A3) - len(W3), len(A3)), "=", (len(A3) - len(W3)) / len(A3))
print("  Fréchet min_i q_i =", min(q10, q12, q13), "= 实测联合漏报 ?", min(q10, q12, q13) == F(len(A3E), nE))

pi = F(nE, n)
def posterior(qp, cp):
    return pi * qp / (pi * qp + (1 - pi) * cp)
C2, C3 = c10 * c13, c10 * c12 * c13
post2, post3 = posterior(P2, C2), posterior(P3, C3)
obs_post, obs_like = F(len(W3), len(A3)), F(len(A3E), nE)

print()
print("=== D. Bayes 后验与四个倍数（全部分子分母显式）===")
print("  P(E|2 独立层全PASS) =", float(post2), " 宣称正确率 =", float(1 - post2))
print("  P(E|3 独立层全PASS) =", float(post3), " 宣称正确率 =", float(1 - post3))
ratios = {
    "1.8772 (后验/2层Bayes)": obs_post / post2,
    "2.0727 (后验/3层Bayes)": obs_post / post3,
    "2.0526 (似然/2层乘积)": obs_like / P2,
    "2.2872 (似然/3层乘积)": obs_like / P3,
    "4.4474 (后验/2层乘积=类别错误)": obs_post / P2,
}
for k, v in ratios.items():
    print("  %-44s = %.9f" % (k, float(v)))
print("  4.4474 / 2.0526 =", float((obs_post / P2) / (obs_like / P2)),
      "= P(E|allPASS)/P(allPASS|E) =", float(obs_post / obs_like),
      "（含 π 与 c_i，非纯放大倍数）")
print("  pp gap 2层 =", float((1 - post2) - (1 - obs_post)) * 100,
      " 3层 =", float((1 - post3) - (1 - obs_post)) * 100)

print()
print("=== E. EVIDENCE_INDEPENDENCE.md:131 的 '乐观 2.0526 倍' 在 JSON 里怎么算 ===")
ev = json.loads(EV.read_text(encoding="utf-8"))
q13j, q10j = ev["posterior"]["q_n13"], ev["posterior"]["q_r10"]
print("  _eind_verify.py:218 observed_over_indep = q13/(q13*q10) =",
      q13j / (q13j * q10j), "= 1/q10 (约掉 q13)")
print("  JSON 记 =", ev["posterior"]["observed_over_indep"])
print("  与似然口径 (3/39)/(q10*q13) =", float(obs_like / P2),
      "数值相等（因 3/39 == q13），但分子分母定义不同")

print()
print("=== F. CHAIN_VS_SINGLE '似然比(后验压低倍数)' 的分子分母 ===")
p0 = len(E) / n
p1 = 3 / 38
p2 = 3 / 18
p3 = 3 / 18
print("  报告 p1/p0 =", p1 / p0, " p2/p1 =", p2 / p1, " p3/p2 =", p3 / p2)
def lr(lay, subset):
    e = [r for r in subset if r["expect"] == "CATCH"]
    nn = [r for r in subset if r["expect"] == "PASS"]
    a = sum(1 for r in e if r[lay] == "PASS") / len(e)
    b = sum(1 for r in nn if r[lay] == "PASS") / len(nn)
    return a, b, a / b
s1 = [r for r in rows if r["n13"] == "PASS"]
s2 = [r for r in s1 if r["r10"] == "PASS"]
print("  真 LR(n13=PASS)              =", lr("n13", rows))
print("  真 LR(r10=PASS | n13=PASS)   =", lr("r10", s1))
print("  真 LR(r12=PASS | n13&r10P)   =", lr("r12", s2))
print("  ⇒ 0.150/2.111/1.000 是后验 P(CATCH|条件) 之比，不是 P(PASS|E)/P(PASS|notE) 的 LR")

print()
print("=== G. 90% 框架的两个 n_eff 口径 + pp 分解的非唯一性 ===")
print("  H(0.9) =", -0.9 * math.log2(0.9) - 0.1 * math.log2(0.1))
print("  n_eff(ρ̄=ρ_eff=0.8, n=2) =", 2 / (1 + 0.8), "  n_eff(ρ̄=标签一致率0.9, n=2) =", 2 / (1 + 0.9))
print("  n_eff(ρ̄≈1, n=18) =", 18 / (1 + 17 * 1.0))
print("  两独立 acc=0.95 分类器的标签一致率 =", 0.95 ** 2 + 0.05 ** 2)
pa, pb = 69 / 74, 48 / 72
A_num = 100 * 21 / 72
A_dil = 100 * (69 / 74 - 69 / 72)
B_num = 100 * 21 / 74
B_dil = 100 * (48 / 74 - 48 / 72)
print("  pp 总差 =", 100 * (pa - pb))
print("  分解A(先用72分母) = %.9f + (%.9f) = %.9f" % (A_num, A_dil, A_num + A_dil))
print("  分解B(先用74分母) = %.9f + (%.9f) = %.9f" % (B_num, B_dil, B_num + B_dil))

print()
print("=== H. 配对 b/c / exact p / CI / SE 两口径 ===")
print("  p_two = 2*2^-18 =", 2 * 2.0 ** -18, " p_one =", 2.0 ** -18)
print("  CP lower = (0.025)^(1/18) =", 0.025 ** (1 / 18))
z = statistics.NormalDist().inv_cdf(0.975)
def wilson_lo(k, nn):
    p = k / nn
    return (p + z * z / (2 * nn) - z * math.sqrt(p * (1 - p) / nn + z * z / (4 * nn * nn))) / (1 + z * z / nn)
print("  Wilson lower on discordant-pair p=b/(b+c)=18/18 (n=18) =", wilson_lo(18, 18))
print("  Wilson lower on paired-acc-diff p=18/68 (n=68)          =", wilson_lo(18, 68))
print("  ↑ 两个 Wilson 分母不同：18=不一致对数，68=冻结行数；文档 CP/Wilson 用前者，bootstrap 用后者")
print("  z =", z)
pd_ = 18 / 68
print("  SE sqrt(p(1-p)/n) [p=18/68] =", math.sqrt(pd_ * (1 - pd_) / 68))
deltas = [1] * 18 + [0] * 50
v = statistics.variance(deltas)
print("  SE sqrt(samplevar/n) =", math.sqrt(v / 68), " samplevar =", v)
print("  族级/全单元 倍数 =", 0.25 / (2 * 2.0 ** -18))

print()
print("=== I. 只读取件指纹（hashlib 现盘重算；与编排方 9 件基线对照）===")
BASE = {
 "lead/keff_calc_20261109/KEFF_CALC.md": ("4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16", 34964),
 "lead/keff_calc_20261109/_ke_REPORT.md": ("a56c9b2aa478ab2fd1ef425f39fecf1b5d933ebe65869d142c0ff9c12aacc042", 14609),
 "lead/keff_calc_20261109/_ke_calc_stdout.txt": ("76cc3f5e60c63b9c2d7a7c6e25a6a6fb0352a5223821fad8ef27441786108d78", 17397),
 "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md": ("aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523", 36194),
 "lead/score_decomp_20261109/SCORE_DECOMP.md": ("dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
 "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
 "lead/comparability_20261109/COMPARABILITY_AUDIT.md": ("c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1", 51927),
 "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
allok = True
for rel, (sha, byt) in BASE.items():
    b = (ROOT / rel).read_bytes()
    got = hashlib.sha256(b).hexdigest()
    ok = (got == sha and len(b) == byt)
    allok &= ok
    print(("  MATCH " if ok else "  DRIFT ") + got + " " + str(len(b)) + " " + rel)
    if ok:
        print("被核对象 SHA256 = %s，字节数 = %d" % (got, len(b)))
print("  FP_ALL_MATCH =", allok, " count =", len(BASE))
print("DONE")
