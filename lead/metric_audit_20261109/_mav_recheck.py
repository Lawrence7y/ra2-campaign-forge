# -*- coding: utf-8 -*-
"""_mav_recheck.py — 口径审计独立复核（复核员自写；唯一写域 lead/metric_audit_20261109/）
python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/metric_audit_20261109/_mav_recheck.py
零真机 / 零采样代码；只读 JSON + 纯统计。绝不 import 或采信 _ma_verify.py。
"""
import hashlib, json, math, pathlib, re
from fractions import Fraction as F

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
GP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json"

# 用 collections.Counter 逐格重数，不复用上游任何摘要
from collections import Counter
data = json.loads(GP.read_text(encoding="utf-8"))
rows = data["rows"]
print("A0 rows =", len(rows), " corpus_n =", data.get("corpus_n"))
cnt = Counter(r["expect"] for r in rows)
print("A0 expect counts =", dict(cnt))
assert set(cnt) == {"CATCH", "PASS"}
E = [r for r in rows if r["expect"] == "CATCH"]
N = [r for r in rows if r["expect"] == "PASS"]
nE, nN, n = len(E), len(N), len(rows)

# 两种口径，各自显式定义事件与条件类
def raw_fn(layer):   # 分子：真断言类里被放过的行数
    return sum(1 for r in E if r[layer] == "PASS")
def raw_fp(layer):   # 分子：非断言类里被误拦的行数
    return sum(1 for r in N if r[layer] == "CATCH")
def raw_cp(layer):   # 分子：非断言类里被放过的行数
    return sum(1 for r in N if r[layer] == "PASS")
def q_i(layer):   # P(PASS|E) = 漏报 / 真断言类
    return F(raw_fn(layer), nE)
def fp_rate(layer):  # P(CATCH|notE) = 误拦 / 非断言类
    return F(raw_fp(layer), nN)
def c_i(layer):   # P(PASS|notE)
    return F(raw_cp(layer), nN)

print("\nA1 逐层（原始计数 / 分母显式 / 约分后分数）")
for lay in ("r10", "r12", "n13", "chain"):
    print("  %-6s q_i=P(PASS|E)=%2d/%d=%s=%.9f  fp_rate=P(CATCH|notE)=%2d/%d=%s=%.9f  c_i=%2d/%d=%s" %
          (lay, raw_fn(lay), nE, q_i(lay), float(q_i(lay)),
           raw_fp(lay), nN, fp_rate(lay), float(fp_rate(lay)),
           raw_cp(lay), nN, c_i(lay)))

q10, q12, q13 = (q_i(k) for k in ("r10", "r12", "n13"))
f10, f12, f13 = (fp_rate(k) for k in ("r10", "r12", "n13"))
c10, c12, c13 = (c_i(k) for k in ("r10", "r12", "n13"))
P2, P3 = q10 * q13, q10 * q12 * q13
print("\nA2 q_r10*q_n13      =", P2, "=", float(P2))
print("A2 q_r10*q_r12*q_n13=", P3, "=", float(P3))
print("A2 差 pp            =", float((P2 - P3) * 100))
prod_fp = f10 * f12 * f13
print("A2 fp_rate 乘积      =", prod_fp, "=", float(prod_fp), " 因子 =", [str(x) for x in (f10,f12,f13)])
# 独立断言：不采信上游，直接检查 0 的来源
r12_catch = [r for r in rows if r["r12"] == "CATCH"]
print("A3 r12=CATCH 行数 =", len(r12_catch), "ids =", [r["id"] for r in r12_catch])
print("A3 r12=CATCH 全在 expect=CATCH ?", all(r["expect"] == "CATCH" for r in r12_catch))
print("A3 这些行全 r10=PASS ?", all(r["r10"] == "PASS" for r in r12_catch))
print("A3 n13=CATCH 且 expect=PASS 行数 =", sum(1 for r in N if r["n13"] == "CATCH"))

# 事件/集合
A3 = [r for r in rows if r["r10"] == r["r12"] == r["n13"] == "PASS"]
A2 = [r for r in rows if r["r10"] == "PASS" and r["n13"] == "PASS"]
W3 = [r for r in A3 if r["expect"] == "CATCH"]
n13P = [r for r in rows if r["n13"] == "PASS"]
print("\nA4 |all3PASS| =", len(A3), " 其中 expect=CATCH =", len(W3), [r["id"] for r in W3])
print("A4 |r10&n13 双PASS| =", len(A2), " 集合相等 ?", {r["id"] for r in A2} == {r["id"] for r in A3})
print("A4 |n13=PASS| =", len(n13P), " 其中 r12=CATCH =", sum(1 for r in n13P if r["r12"] == "CATCH"))
print("A4 P(r12=PASS|n13=PASS) =", F(sum(1 for r in n13P if r["r12"] == "PASS"), len(n13P)))
print("A4 P(all3PASS|E) =", F(sum(1 for r in E if r in A3), nE))
print("A4 P(E|allPASS)  =", F(len(W3), len(A3)))
print("A4 FRECHET min(q10,q12,q13) =", min(q10, q12, q13),
      " == 实测联合漏报 ?", min(q10,q12,q13) == F(len([r for r in E if r in A3]), nE))

# Bayes 换底（自带实现，不用上游函数）
pi = F(nE, n)
def bayes(qprod, cprod):
    return pi * qprod / (pi * qprod + (1 - pi) * cprod)
post2 = bayes(P2, c10 * c13)
post3 = bayes(P3, c10 * c12 * c13)
obs_post, obs_like = F(len(W3), len(A3)), F(len([r for r in E if r in A3]), nE)
print("\nA5 pi =", pi, " P(E|2独立层全PASS) =", float(post2), " P(E|3独立层全PASS) =", float(post3))
print("A5 宣称正确率 2层 =", float(1 - post2), " 3层 =", float(1 - post3), " 实测 =", float(1 - obs_post))
print("A5 pp gaps =", float((post2 - obs_post)*100), float((post3 - obs_post)*100))

print("\nA6 四倍数 + 附项（分子分母都写全）")
R = {
 "1.8772 后验/Bayes2层": obs_post / post2,
 "2.0526 似然/2层乘积": obs_like / P2,
 "2.0727 后验/Bayes3层": obs_post / post3,
 "2.2872 似然/3层乘积": obs_like / P3,
 "4.4474 后验/2层乘积(禁用)": obs_post / P2,
}
for k, v in R.items():
    print("   %-34s = %s = %.9f" % (k, v, float(v)))
print("   4.4474/2.0526 =", float(R["4.4474 后验/2层乘积(禁用)"]/R["2.0526 似然/2层乘积"]),
      " P(E|allPASS)/P(allPASS|E) =", float(obs_post/obs_like))
print("   2.0727/2.0526 =", float(R["2.0727 后验/Bayes3层"]/R["2.0526 似然/2层乘积"]))

# _eind_verify_out.json 的 observed_over_indep 到底怎么算
EV = ROOT / "lead" / "evidence_indep_20261109" / "_eind_verify_out.json"
ev = json.loads(EV.read_text(encoding="utf-8"))
print("\nA7 _eind_verify_out.json posterior keys =", list(ev["posterior"].keys()))
print("A7 q_n13 =", ev["posterior"]["q_n13"], " q_r10 =", ev["posterior"]["q_r10"])
print("A7 q13/(q13*q10) =", ev["posterior"]["q_n13"]/(ev["posterior"]["q_n13"]*ev["posterior"]["q_r10"]),
      " 1/q10 =", 1/ev["posterior"]["q_r10"], " JSON observed_over_indep =", ev["posterior"]["observed_over_indep"])
# c_confidence 键名
AD = ROOT / "lead" / "evidence_indep_20261109" / "_ei_05_admission_out.json"
ad = json.loads(AD.read_text(encoding="utf-8"))
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + "/" + k)
    else:
        yield path, o
hits = [(p, v) for p, v in walk(ad) if "n_independent_2_error_bound" in p or "bound" in p.lower()]
print("A8 _ei_05_admission_out.json 含 bound 的键 =", hits[:8])

# CHAIN_VS_SINGLE 后验比 vs 真 LR（自己写）
print("\nA9 后验阶梯 vs 真似然比")
p0 = nE / n
s1 = [r for r in rows if r["n13"] == "PASS"]
s2 = [r for r in s1 if r["r10"] == "PASS"]
p1 = sum(1 for r in s1 if r["expect"] == "CATCH") / len(s1)
p2 = sum(1 for r in s2 if r["expect"] == "CATCH") / len(s2)
p3 = sum(1 for r in [r for r in s2 if r["r12"] == "PASS"] if r["expect"] == "CATCH") / len([r for r in s2 if r["r12"] == "PASS"])
print("   后验 p0,p1,p2,p3 =", p0, p1, p2, p3)
print("   后验比 p1/p0,p2/p1,p3/p2 =", p1/p0, p2/p1, p3/p2)
def LR(lay, subset):
    ee = [r for r in subset if r["expect"] == "CATCH"]
    nn = [r for r in subset if r["expect"] == "PASS"]
    a = sum(1 for r in ee if r[lay] == "PASS") / len(ee)
    b = sum(1 for r in nn if r[lay] == "PASS") / len(nn)
    return a, b, a/b
for lay, sub, tag in (("n13", rows, "全74"), ("r10", s1, "n13=PASS"), ("r12", s2, "n13&r10 PASS")):
    a, b, lr = LR(lay, sub)
    print("   真 LR(%s|%s) = P(PASS|E)=%s / P(PASS|notE)=%s = %.9f" % (lay, tag, a, b, lr))

# k_eff 三估计量
kprob = math.log(p3/p0)/math.log(p1/p0)
odds = lambda p: p/(1-p)
kodds = math.log(odds(p3)/odds(p0))/math.log(odds(p1)/odds(p0))
kgain = (p0-p3)/(p0-p1)
print("A10 k_eff 概率比/后验几率比/信息增益比 =", kprob, kodds, kgain)

# 分母 18 vs 68 / pp 分解两种顺序
print("\nA11 Wilson 两个分母")
z = 1.959963984540054
def wilson(k, m):
    p = k/m
    return (p + z*z/(2*m) - z*math.sqrt(p*(1-p)/m + z*z/(4*m*m)))/(1+z*z/m)
print("   Wilson(18,18) lo =", wilson(18,18), " Wilson(18,68) lo =", wilson(18,68))
print("   CP (0.025)^(1/18) =", 0.025**(1/18))
print("A12 pp 分解 A 100*21/72 + 100*(69/74-69/72) =",
      100*21/72, 100*(69/74-69/72), 100*21/72 + 100*(69/74-69/72))
print("A12 pp 分解 B 100*21/74 + 100*(48/74-48/72) =",
      100*21/74, 100*(48/74-48/72), 100*21/74 + 100*(48/74-48/72))
print("A12 总差 100*(69/74-48/72) =", 100*(69/74-48/72))
print("A13 n_eff(ρ_eff=0.8,n=2) =", 2/1.8, " n_eff(标签一致率0.9,n=2) =", 2/1.9,
      " n_eff(ρ̄=1,n=18) =", 18/18)

# 九件指纹（复核员独立 hashlib）
print("\nA14 九件指纹独立重算")
BASE = [
 ("lead/keff_calc_20261109/KEFF_CALC.md", "4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16", 34964),
 ("lead/keff_calc_20261109/_ke_REPORT.md", "a56c9b2aa478ab2fd1ef425f39fecf1b5d933ebe65869d142c0ff9c12aacc042", 14609),
 ("lead/keff_calc_20261109/_ke_calc_stdout.txt", "76cc3f5e60c63b9c2d7a7c6e25a6a6fb0352a5223821fad8ef27441786108d78", 17397),
 ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", "aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523", 36194),
 ("lead/score_decomp_20261109/SCORE_DECOMP.md", "dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
 ("lead/gate_pipeline_20261109/_gp_regression_out.json", "d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
 ("lead/comparability_20261109/COMPARABILITY_AUDIT.md", "c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1", 51927),
 ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
 ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
okall = True
for rel, sha, byt in BASE:
    b = (ROOT/rel).read_bytes()
    got = hashlib.sha256(b).hexdigest()
    ok = got == sha and len(b) == byt
    okall &= ok
    print("  ", "MATCH" if ok else "DRIFT", got, len(b), rel)
    if ok:
        print("被核对象 SHA256 = %s，字节数 = %d" % (got, len(b)))
print("A14 FP_ALL_MATCH =", okall)

# 报告自身绑定行严格格式
AU = ROOT / "lead" / "metric_audit_20261109" / "_ma_METRIC_AUDIT.md"
txt = AU.read_text(encoding="utf-8")
pat = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$")
lines = [(m.group(1), int(m.group(2))) for m in (pat.match(l) for l in txt.splitlines()) if m]
print("A15 报告绑定行 strict-format 条数 =", len(lines), " 与九件基线全等 ?",
      lines == [(s, b) for _, s, b in BASE])
print("DONE")
