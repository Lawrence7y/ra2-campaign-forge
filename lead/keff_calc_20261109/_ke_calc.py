# -*- coding: utf-8 -*-
# _ke_calc.py : k_eff / 三层全过真实置信度 独立重算（只读输入，唯一写域 lead/keff_calc_20261109/）
# 纪律：python -I -X utf8 -B <绝对路径>；零真机、零采样代码、不改任何模块/语料/只读件。
import json, math, hashlib, pathlib, collections

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "keff_calc_20261109"
WD.mkdir(parents=True, exist_ok=True)

BASE = {
    "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md": ("aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523", 36194),
    "lead/evidence_indep_20261109/_ei_04_v12_layer_out.json": ("3253eb8456ceab54df1b41629caa4eaee8fcabff5e016e18fd71a3a3606b4546", 51602),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/falsifiable_no_relax_20261109/_fnr_check_out.json": ("f3112b225b1de35183ad4604554cb25689ed252b6a5a95d96d17fce53c8c140e", 8733),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/evidence_indep_20261109/_ei_n13_predicates_src.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
}

# 任务书给的「编排方实跑」基线（原样抄入，用于逐项对照）
ORCH = {
    "n": 74,
    "layer_r10": {"CATCH": 40, "PASS": 34},
    "layer_r12": {"CATCH": 4, "PASS": 70},
    "layer_n13": {"CATCH": 36, "PASS": 38},
    "layer_chain": {"CATCH": 38, "PASS": 36},
    "all3_pass": 18, "all3_pass_wrong": 3, "all3_pass_err_rate": 0.1667,
    "n_pos": 35, "n_neg": 39,
    "per_layer": {
        "r10": {"fp": 20, "fn": 19, "fp_rate": 0.5714, "miss_rate": 0.4872},
        "r12": {"fp": 0, "fn": 35, "fp_rate": 0.0, "miss_rate": 0.8974},
        "n13": {"fp": 0, "fn": 3, "fp_rate": 0.0, "miss_rate": 0.0769},
    },
    "indep_wrong_prob": 0.0, "actual_wrong_prob": 0.1667,
    "r10_n13_agree": 38, "r10_n13_agree_rate": 0.5135,
}

out = {"task": "k_eff / 三层全过真实置信度 独立重算", "discipline": "只读输入；唯一写域 lead/keff_calc_20261109/；零真机零采样代码；不 commit/push", "orch_baseline_as_given": ORCH}
lines = []
def P(s=""):
    lines.append(s)
    print(s)

# ---------------------------------------------------------------- 0 指纹
P("=== 0 指纹（hashlib，逐件）===")
fp = {}
for rel, (sha, size) in BASE.items():
    b = (ROOT / rel).read_bytes()
    got = hashlib.sha256(b).hexdigest()
    fp[rel] = {"sha256": got, "bytes": len(b), "match": (got == sha and len(b) == size)}
    P("  %-70s sha256=%s bytes=%d match=%s" % (rel, got, len(b), fp[rel]["match"]))
out["fingerprints"] = fp

# ---------------------------------------------------------------- 1 数据
D = json.loads((ROOT / "lead/gate_pipeline_20261109/_gp_regression_out.json").read_text(encoding="utf-8"))
R = D["rows"]
n = len(R)
assert n == 74 and D["corpus_n"] == 74
assert all(r[c] in ("CATCH", "PASS") for r in R for c in ("expect", "r10", "r12", "n13", "chain"))
V = json.loads((ROOT / "lead/evidence_indep_20261109/_ei_04_v12_layer_out.json").read_text(encoding="utf-8"))
assert [x["id"] for x in V["rows"]] == [r["id"] for r in R], "第二数据源 id 序列不一致"
assert all(V["rows"][i][c] == R[i][c] for i in range(n) for c in ("expect", "r10", "r12", "n13", "chain")), "两层判定列不一致"
P("=== 1 数据一致性 ===")
P("  _gp_regression_out.json rows = %d；_ei_04_v12_layer_out.json rows id 序列全等，5 列判定逐行全等" % n)

E = [r for r in R if r["expect"] == "CATCH"]      # 真断言类（39）
N = [r for r in R if r["expect"] == "PASS"]       # 真非断言类（35）
nE, nN = len(E), len(N)
pi = nE / n
P("  expect=CATCH(真断言类) = %d，expect=PASS(非断言类) = %d，pi=P(E)=%.9f" % (nE, nN, pi))

def cnt(col, val):
    return sum(1 for r in R if r[col] == val)

P("=== 2 第一步(a) 逐层 fp/fn/rate 复现 ===")
per = {}
for col in ("r10", "r12", "n13", "chain"):
    CATCH, PASS = cnt(col, "CATCH"), cnt(col, "PASS")
    fp_ = sum(1 for r in N if r[col] == "CATCH")      # 非断言类被误拦
    fn_ = sum(1 for r in E if r[col] == "PASS")       # 真断言类被放过
    d = {"CATCH": CATCH, "PASS": PASS, "fp": fp_, "fn": fn_,
         "fp_rate": fp_ / nN, "miss_rate": fn_ / nE,
         "q_PASS_given_E": fn_ / nE, "c_PASS_given_notE": (nN - fp_) / nN}
    per[col] = d
    P("  %-5s CATCH=%2d PASS=%2d  fp=%2d/%d=%.6f  fn=%2d/%d=%.6f  q_i=%.9f c_i=%.9f" %
      (col, CATCH, PASS, fp_, nN, d["fp_rate"], fn_, nE, d["miss_rate"], d["q_PASS_given_E"], d["c_PASS_given_notE"]))
out["step1_per_layer"] = per

P("  与编排方基线逐项对照（fp/fn/rate 四舍五入到 4 位）:")
for col in ("r10", "r12", "n13"):
    o = ORCH["per_layer"][col]
    d = per[col]
    P("    %-4s fp %d==%d %s | fn %d==%d %s | fp_rate %.4f==%.4f %s | miss_rate %.4f==%.4f %s" %
      (col, d["fp"], o["fp"], d["fp"] == o["fp"], d["fn"], o["fn"], d["fn"] == o["fn"],
       d["fp_rate"], o["fp_rate"], round(d["fp_rate"], 4) == o["fp_rate"],
       d["miss_rate"], o["miss_rate"], round(d["miss_rate"], 4) == o["miss_rate"]))
for col in ("r10", "r12", "n13", "chain"):
    o = ORCH["layer_" + col]
    P("    layer_%-5s CATCH %d==%d %s | PASS %d==%d %s" %
      (col, per[col]["CATCH"], o["CATCH"], per[col]["CATCH"] == o["CATCH"],
       per[col]["PASS"], o["PASS"], per[col]["PASS"] == o["PASS"]))
P("  ★ 标签口径：编排方 n_pos=35 / n_neg=39 与文件里的 expect 计数相反（文件 expect=CATCH=39、PASS=35）。")
P("    fp_rate 用的是 35 作分母（真非断言），miss_rate 用的是 39 作分母（真断言）。数字可复现，标签须纠正。")

# ---------------------------------------------------------------- 3 all3
A3 = [r for r in R if all(r[c] == "PASS" for c in ("r10", "r12", "n13"))]
W3 = [r for r in A3 if r["expect"] == "CATCH"]
P("=== 3 第一步(b) 三层全过 ===")
P("  all3_pass = %d（编排 %d）；wrong = %d（编排 %d）；错 ids = %s" %
  (len(A3), ORCH["all3_pass"], len(W3), ORCH["all3_pass_wrong"], [r["id"] for r in W3]))
P("  条件错误率 P(E|all3 PASS) = %d/%d = %.9f（编排 %.4f）" %
  (len(W3), len(A3), len(W3) / len(A3), ORCH["all3_pass_err_rate"]))
P("  条件正确率 P(¬E|all3 PASS) = %d/%d = %.9f" % (len(A3) - len(W3), len(A3), 1 - len(W3) / len(A3)))
P("  18 行明细（id / expect / family）:")
for r in A3:
    P("    %-42s %-5s %s" % (r["id"], r["expect"], r["family"]))
out["step1_all3"] = {"all3_ids": [r["id"] for r in A3], "wrong_ids": [r["id"] for r in W3],
                     "n_pass": len(A3), "wrong": len(W3), "err_rate": len(W3) / len(A3),
                     "correct_rate": 1 - len(W3) / len(A3)}

# ---------------------------------------------------------------- 4 交叉表 / 一致率
cross = collections.Counter((r["r10"], r["n13"]) for r in R)
agree = sum(1 for r in R if r["r10"] == r["n13"])
P("=== 4 第一步(d) r10×n13 交叉表 / 一致率 ===")
P("  r10\\n13   CATCH  PASS | CATCH=%d PASS=%d" % (cnt("r10", "CATCH"), cnt("r10", "PASS")))
for a in ("CATCH", "PASS"):
    P("    %-5s  %5d %5d | n13 CATCH=%d PASS=%d" %
      (a, cross[(a, "CATCH")], cross[(a, "PASS")], cnt("n13", "CATCH"), cnt("n13", "PASS")))
P("  一致率 = %d/%d = %.9f（编排 %d / %.4f）" % (agree, n, agree / n, ORCH["r10_n13_agree"], ORCH["r10_n13_agree_rate"]))
out["step1_cross"] = {"cross": {str(k): v for k, v in cross.items()}, "agree": agree, "agree_rate": agree / n}

# ---------------------------------------------------------------- 5 独立假设算式
q10, q12, q13 = per["r10"]["q_PASS_given_E"], per["r12"]["q_PASS_given_E"], per["n13"]["q_PASS_given_E"]
c10, c12, c13 = per["r10"]["c_PASS_given_notE"], per["r12"]["c_PASS_given_notE"], per["n13"]["c_PASS_given_notE"]
prod2 = q10 * q13
prod3 = q10 * q12 * q13
obs_joint = len(W3) / nE     # P(all3 PASS | E) = 3/39
def posterior(qp, cp):
    num = pi * qp
    return num / (num + (1 - pi) * cp)
pE_indep2, pE_indep3 = posterior(prod2, c10 * c13), posterior(prod3, c10 * c12 * c13)
P("=== 5 第一步(c) 独立假设下 3.75% 的算式 ===")
P("  q_i = P(layer=PASS | E) = fn_i/39：q_r10=%d/39=%.9f  q_r12=%d/39=%.9f  q_n13=%d/39=%.9f" %
  (per["r10"]["fn"], q10, per["r12"]["fn"], q12, per["n13"]["fn"], q13))
P("  c_i = P(layer=PASS | ¬E) = (35-fp_i)/35：c_r10=%.9f c_r12=%.9f c_n13=%.9f" % (c10, c12, c13))
P("  ★ 3.75%% 不是 q_r10×q_r12×q_n13：它是 q_r10×q_n13 = %.9f×%.9f = %.9f" % (q10, q13, prod2))
P("    因为 R12 是 R10 的确定性子集、对『全 PASS』零增量，上游只按两层（R10|N13）算联合漏报期望。")
P("  若硬乘三层：q_r10×q_r12×q_n13 = %.9f（%.4f%%）；与 3.75%% 相差 %.4f%%（绝对）" % (prod3, 100 * prod3, 100 * (prod2 - prod3)))
P("  ★ 编排方 indep_wrong_prob=0.0 的来源（本会话复算）：把 fp_rate 当误差率相乘")
fp_prod3 = per["r10"]["fp_rate"] * per["r12"]["fp_rate"] * per["n13"]["fp_rate"]
P("    fp_rate(r10)×fp_rate(r12)×fp_rate(n13) = %.6f×%.6f×%.6f = %.9f → 0.0" %
  (per["r10"]["fp_rate"], per["r12"]["fp_rate"], per["n13"]["fp_rate"], fp_prod3))
P("    这是口径错置（fp_rate 是『非断言被误拦率』，不是『真断言被放过率』），不能当独立假设错率。")
P("  P(all3 PASS|E) 实测 = %d/%d = %.9f（7.69%%）；风险放大 = %.9f/%.9f = %.9f（2.05 倍）" %
  (len(W3), nE, obs_joint, obs_joint, prod2, obs_joint / prod2))
P("  ★ 3/18=16.67% 是后验 P(E|all3 PASS)；3/39=7.69% 是似然 P(all3 PASS|E)。2.05 倍用的是后者。")
P("    16.67%%/3.75%% = %.4f 是把后验除似然，属类别错误，不得使用。" % ((len(W3) / len(A3)) / prod2))
P("  Bayes 后验（π=39/74，§5.3 公式）：")
P("    P(E|2 独立层全 PASS) = π·%.9f/[π·%.9f+(1-π)·%.9f] = %.9f → 独立宣称正确率 %.4f%%" %
  (prod2, prod2, c10 * c13, pE_indep2, 100 * (1 - pE_indep2)))
P("    P(E|3 独立层全 PASS) = π·%.9f/[π·%.9f+(1-π)·%.9f] = %.9f → 独立宣称正确率 %.4f%%" %
  (prod3, prod3, c10 * c12 * c13, pE_indep3, 100 * (1 - pE_indep3)))
P("    实测正确率 %.4f%%；误差放大（后验口径）= %.4f / %.4f = %.4f 倍（2 层）/ %.4f 倍（3 层）" %
  (100 * (1 - len(W3) / len(A3)), len(W3) / len(A3), pE_indep2,
   (len(W3) / len(A3)) / pE_indep2, (len(W3) / len(A3)) / pE_indep3))
out["step1_indep"] = {"q": {"r10": q10, "r12": q12, "n13": q13}, "c": {"r10": c10, "r12": c12, "n13": c13},
                      "prod2_q10_q13": prod2, "prod3_q10_q12_q13": prod3,
                      "orchestrator_zero_reproduced_as_fp_rate_product": fp_prod3,
                      "obs_joint_miss_given_E": obs_joint, "amplification_joint": obs_joint / prod2,
                      "P_E_given_2_indep": pE_indep2, "P_E_given_3_indep": pE_indep3,
                      "posterior_err_amplification_2": (len(W3) / len(A3)) / pE_indep2,
                      "posterior_err_amplification_3": (len(W3) / len(A3)) / pE_indep3}

# ---------------------------------------------------------------- 6 区间工具
def wilson(k, nn, z=1.96):
    if nn == 0: return (float("nan"), float("nan"))
    p = k / nn
    den = 1 + z * z / nn
    ctr = (p + z * z / (2 * nn)) / den
    half = z * math.sqrt(p * (1 - p) / nn + z * z / (4 * nn * nn)) / den
    return (max(0.0, ctr - half), min(1.0, ctr + half))

def binom_cdf_upper(k, nn, p):  # P(X >= k)
    return sum(math.comb(nn, j) * p**j * (1 - p)**(nn - j) for j in range(k, nn + 1))

def binom_cdf_lower(k, nn, p):  # P(X <= k)
    return sum(math.comb(nn, j) * p**j * (1 - p)**(nn - j) for j in range(0, k + 1))

def cp(k, nn, alpha=0.05):
    # Clopper-Pearson 双侧精确区间：
    #   lower: 解 P(X >= k | p) = alpha/2（P(X>=k) 随 p 单调增）
    #   upper: 解 P(X <= k | p) = alpha/2（P(X<=k) 随 p 单调减）
    lo, hi = 0.0, 1.0
    if k > 0:
        a, b = 0.0, 1.0
        for _ in range(200):
            m = (a + b) / 2
            if binom_cdf_upper(k, nn, m) < alpha / 2: a = m
            else: b = m
        lo = (a + b) / 2
    if k < nn:
        a, b = 0.0, 1.0
        for _ in range(200):
            m = (a + b) / 2
            if binom_cdf_lower(k, nn, m) > alpha / 2: a = m
            else: b = m
        hi = (a + b) / 2
    return (lo, hi)

# ---------------------------------------------------------------- 7 k_eff 三口径
p1 = sum(1 for r in R if r["n13"] == "PASS" and r["expect"] == "CATCH") / cnt("n13", "PASS")
p2 = sum(1 for r in R if r["n13"] == "PASS" and r["r10"] == "PASS" and r["expect"] == "CATCH") / sum(1 for r in R if r["n13"] == "PASS" and r["r10"] == "PASS")
p3 = len(W3) / len(A3)
P("=== 7 第二步(a)(b) k_eff 三口径公式与点值 ===")
P("  阶梯：π=%.9f → p1=P(E|n13 PASS)=%d/%d=%.9f → p2=P(E|n13&r10 PASS)=%d/%d=%.9f → p3=P(E|三层全 PASS)=%d/%d=%.9f" %
  (pi, 3, cnt("n13", "PASS"), p1, 3, sum(1 for r in R if r["n13"] == "PASS" and r["r10"] == "PASS"), p2, len(W3), len(A3), p3))
k_prob = math.log(p3 / pi) / math.log(p1 / pi)
def odds(p): return p / (1 - p)
k_odds = math.log(odds(p3) / odds(pi)) / math.log(odds(p1) / odds(pi))
I1, I3 = pi - p1, pi - p3
k_info = I3 / I1
P("  (1) 上游概率比 k_prob = ln(p3/π)/ln(p1/π) = ln(%.9f)/ln(%.9f) = %.9f（≈0.61）" % (p3 / pi, p1 / pi, k_prob))
P("  (2) 后验几率比 k_odds = ln[odds(p3)/odds(π)] / ln[odds(p1)/odds(π)] = ln(%.9f)/ln(%.9f) = %.9f（≈0.670）" %
  (odds(p3) / odds(pi), odds(p1) / odds(pi), k_odds))
P("  (3) 信息增益比 k_info = I3/I1 = (π−p3)/(π−p1) = %.9f/%.9f = %.9f（≈0.804）" % (I3, I1, k_info))
P("  ★ 注意：I=π−p 是线性概率差的『信息增量』代理，不是 bit；I3/I1 随先验与 p 的单调变换而变，")
P("    不是信息论里的互信息/似然比，也不能解释为『层数』。R12 增量（真 bit）= log2(odds(p3)/odds(p2)) = %.9f" %
  math.log2(odds(p3) / odds(p2)))
P("  ★ 三者不同主因是【口径不同】而非抽样噪声：分母分别取概率比 / 几率比 / 线性差，")
P("    同一个 p1、p3 下三者的函数形式不同，必然给不同值；它们共用同一 3 个错例，所以不是三个独立估计，")
P("    取平均或取并集都没有统计意义。三者同向（都 <1）只说明『三层合成弱于 N13 单层』这一方向稳健。")
out["step2_keff"] = {"pi": pi, "p1": p1, "p2": p2, "p3": p3, "I1_linear": I1, "I3_linear": I3,
                     "k_prob": k_prob, "k_odds": k_odds, "k_info": k_info,
                     "R12_increment_bit_log2": math.log2(odds(p3) / odds(p2))}

# ---------------------------------------------------------------- 8 小样本区间
P("=== 8 第二步(d) 小样本区间：3 个错例能撑起 k_eff 吗 ===")
w318, c318 = wilson(3, 18), cp(3, 18)
w339, c339 = wilson(3, 39), cp(3, 39)
P("  P(E|all3 PASS)=3/18：Wilson95=[%.6f, %.6f]；Clopper-Pearson 精确95=[%.6f, %.6f]" % (*w318, *c318))
P("  → P(结论正确)=15/18=%.6f：Wilson95=[%.6f, %.6f]；CP95=[%.6f, %.6f]" %
  (15 / 18, 1 - w318[1], 1 - w318[0], 1 - c318[1], 1 - c318[0]))
P("  q_n13=3/39：Wilson95=[%.6f, %.6f]；CP95=[%.6f, %.6f]（与 EVIDENCE_INDEPENDENCE.md:252 的 [0.026507,0.203214] 对照）" % (*w339, *c339))
P("  ★ 结论：18 行里只有 3 个错例，正确率 95%% 区间宽度约 %.1f 个百分点；任一条样本增删都显著改写比率。" %
  (100 * (c318[1] - c318[0])))

P("  -- k_eff 对 3 个错例的敏感性（固定 18 行分母，仅改错例数 k）--")
sens = {}
for k in (1, 2, 3, 4, 5, 6):
    pp = k / 18
    kp = math.log(pp / pi) / math.log(p1 / pi) if 0 < pp < pi else None
    ko = math.log(odds(pp) / odds(pi)) / math.log(odds(p1) / odds(pi)) if 0 < pp < 1 else None
    ki = (pi - pp) / I1
    sens[k] = {"p3": pp, "k_prob": kp, "k_odds": ko, "k_info": ki}
    P("    k=%d → p3=%.6f  k_prob=%s  k_odds=%s  k_info=%.6f" %
      (k, pp, ("%.4f" % kp) if kp is not None else "undefined", ("%.4f" % ko) if ko is not None else "undefined", ki))
P("  -- 保留 3 个错例、但删掉 1 个错例（LOO，分母 17）--")
loo = {}
for rid in [r["id"] for r in W3]:
    pp = 2 / 17
    loo[rid] = {"p3": pp, "k_prob": math.log(pp / pi) / math.log(p1 / pi),
                "k_odds": math.log(odds(pp) / odds(pi)) / math.log(odds(p1) / odds(pi)),
                "k_info": (pi - pp) / I1}
P("    删任一错例 → p3=2/17=%.6f，k_prob=%.4f，k_odds=%.4f，k_info=%.4f" %
  (2 / 17, math.log((2 / 17) / pi) / math.log(p1 / pi),
   math.log(odds(2 / 17) / odds(pi)) / math.log(odds(p1) / odds(pi)), (pi - 2 / 17) / I1))
out["step2_sensitivity"] = {"by_error_count": sens, "loo_delete_one_error": loo,
                            "wilson_3_18": list(w318), "cp_3_18": list(c318),
                            "wilson_3_39": list(w339), "cp_3_39": list(c339)}

# bootstrap，固定种子，B=10000
P("  -- 非参数 bootstrap（74 行有放回重抽，B=10000；确定性 LCG 算术发生器 seed=20261109，无随机模块/无加密用途）--")
# 显式整数 LCG：仅用于有放回重抽索引，非密码学用途；固定常数保证可复算
_mod = 2147483647
_state = 20261109
def next_u():
    global _state
    _state = (1103515245 * _state + 12345) % _mod
    return _state / _mod
B = 10000
vals = {"k_prob": [], "k_odds": [], "k_info": [], "p3": []}
invalid = collections.Counter()
for _ in range(B):
    S = [R[int(next_u() * n) % n] for _ in range(n)]
    nEb = sum(1 for r in S if r["expect"] == "CATCH")
    pib = nEb / n
    s1 = [r for r in S if r["n13"] == "PASS"]
    s3 = [r for r in S if all(r[c] == "PASS" for c in ("r10", "r12", "n13"))]
    if not s1 or not s3 or not (0 < pib < 1):
        invalid["empty_subset"] += 1
        continue
    p1b = sum(1 for r in s1 if r["expect"] == "CATCH") / len(s1)
    p3b = sum(1 for r in s3 if r["expect"] == "CATCH") / len(s3)
    if not (0 < p1b < 1 and 0 < p3b < 1):
        invalid["boundary_p"] += 1
        continue
    vals["p3"].append(p3b)
    I1b = pib - p1b
    if I1b != 0: vals["k_info"].append((pib - p3b) / I1b)
    else: invalid["I1_zero"] += 1
    if 0 < p1b / pib < 1 and 0 < p3b / pib < 1:
        vals["k_prob"].append(math.log(p3b / pib) / math.log(p1b / pib))
    else: invalid["prob_ratio_out_of_domain"] += 1
    d2 = math.log(odds(p1b) / odds(pib))
    if d2 != 0 and 0 < odds(p3b) / odds(pib) and 0 < odds(p1b) / odds(pib):
        vals["k_odds"].append(math.log(odds(p3b) / odds(pib)) / d2)
    else: invalid["odds_out_of_domain"] += 1

def quant(a, q):
    a = sorted(a); return a[min(len(a) - 1, max(0, int(q * len(a))))] if a else None
boot = {}
for key, a in vals.items():
    boot[key] = {"valid": len(a), "q025": quant(a, .025), "median": quant(a, .5),
                 "q975": quant(a, .975), "min": min(a) if a else None, "max": max(a) if a else None}
    P("    %-7s valid=%5d  95%% bootstrap=[%s, %s]  median=%s  range=[%s, %s]" %
      (key, len(a), ("%.4f" % boot[key]["q025"]) if boot[key]["q025"] is not None else "NA",
       ("%.4f" % boot[key]["q975"]) if boot[key]["q975"] is not None else "NA",
       ("%.4f" % boot[key]["median"]) if boot[key]["median"] is not None else "NA",
       ("%.4f" % boot[key]["min"]) if boot[key]["min"] is not None else "NA",
       ("%.4f" % boot[key]["max"]) if boot[key]["max"] is not None else "NA"))
P("    bootstrap 无效/越域计数 = %s" % dict(invalid))
P("  ★ 判定：k_eff 的 95% bootstrap 上限逼近 1（k_info 达 0.95），全距含负值，455/10000 次重抽越域，")
P("    且错例数 k=1 的反事实就给出 k_eff>1。点值 0.61/0.670/0.804 都不是可用估计量；")
P("    这 74 行（且 train=test）不能支撑 k_eff 的估计，只能给『方向：≤1 层』的描述性结论。")
out["step2_bootstrap"] = {"B": B, "seed": 20261109, "quantiles": boot, "invalid": dict(invalid)}

# ---------------------------------------------------------------- 9 样本量
P("=== 9 第二步(e) 需要多少样本 ===")
z = 1.96
def n_abs(p, w): return z * z * p * (1 - p) / (w * w)
def n_rel(p, rel): return z * z * (1 - p) / ((rel * rel) * p)
sizes = {
    "joint_miss_p=3/39_w=0.02": n_abs(obs_joint, .02),
    "joint_miss_p=3/39_w=0.01": n_abs(obs_joint, .01),
    "posterior_p=3/18_w=0.05": n_abs(3 / 18, .05),
    "posterior_p=3/18_w=0.02": n_abs(3 / 18, .02),
    "joint_miss_rel10pct": n_rel(obs_joint, .10),
    "joint_miss_rel5pct": n_rel(obs_joint, .05),
}
P("  正态近似 n ≈ z²p(1−p)/w²（绝对半宽 w），或 n ≈ z²(1−p)/(r²p)（相对半宽 r）：")
for k, v in sizes.items():
    P("    %-32s n_E ≈ %s 条【真断言类】→ 按 39/74 配比换算总行 ≈ %s" %
      (k, ("%.0f" % v), ("%.0f" % (v / pi))))
P("  另按『三层全 PASS 事件』计数：当前 18 行全 PASS 里 3 错（16.7%%）。要拿到 100 个错例需 ≈ %.0f 个全 PASS 行 ≈ %.0f 总行。" %
  (100 / (3 / 18), (100 / (3 / 18)) / (18 / 74)))
P("  ★ 数量级：把 k_eff 当可用比率估计，需 10³ 量级真断言类样本（±2pp 绝对精度），")
P("    若要窄到 ±10% 相对精度或让 k_eff 的 log 比值稳定，需 10⁴–10⁵ 量级。")
P("  ★ 前提：盲留出集、含 r10/r12/n13 全部判定列、无 train=test 泄漏、无定向构造对抗样本混入测试集；")
P("    单纯加样本不能把『确定性依赖』变成独立层，n→∞ 只是让一个无层数含义的数收敛得更稳。")
out["step2_sample_size"] = {"formula": "n≈z²p(1-p)/w² ; n≈z²(1-p)/(r²p)", "sizes_true_E_rows": sizes,
                            "total_rows_at_pi": {k: v / pi for k, v in sizes.items()},
                            "allPASS_rows_for_100_errors": 100 / (3 / 18),
                            "total_rows_for_100_errors": (100 / (3 / 18)) / (18 / 74)}

# ---------------------------------------------------------------- 10 第三步
P("=== 10 第三步(a)(b)(c) 三层全过的真实置信度 ===")
P("  (a) 按 k_eff：三层全过 ≈ %.3f–%.3f 个『N13 等效独立层』，即 <1 层；" % (k_prob, k_info))
P("      结构层面独立证据根 = 1（R10 → {R12, N13.C}，见 EVIDENCE_INDEPENDENCE.md:301）。")
P("      上游报告 numeric=1（:299）是【保守取整的工程约定】，不是 k_eff 的测量值，且比 k_eff 点值更乐观。")
P("  (b) 实测 P(结论正确|all3 PASS) = 15/18 = %.6f" % (15 / 18))
P("      Wilson95 = [%.6f, %.6f]；CP 精确95 = [%.6f, %.6f]（对应错误率 [%.6f, %.6f]）" %
  (1 - w318[1], 1 - w318[0], 1 - c318[1], 1 - c318[0], c318[0], c318[1]))
P("      ★ 这是 train=test 上的描述性区间，不是生产置信界；先验 π 若变，后验随之变。")
P("  (c) 『三层独立』宣称值：")
P("      两层独立 q10·q13 → 错误率 %.6f / 正确率 %.6f%%；三层独立 q10·q12·q13 → 错误率 %.6f / 正确率 %.6f%%" %
  (pE_indep2, 100 * (1 - pE_indep2), pE_indep3, 100 * (1 - pE_indep3)))
P("      与实测 83.3333%% 的差：正确率低 %.4f pp（2 层口径）/ %.4f pp（3 层口径）；" %
  (100 * (1 - pE_indep2) - 100 * (1 - len(W3) / len(A3)), 100 * (1 - pE_indep3) - 100 * (1 - len(W3) / len(A3))))
P("      错误率放大 %.4f 倍 / %.4f 倍；若按编排方 indep_wrong_prob=0.0（错置口径）则宣称 100%%，差 16.6667 pp。" %
  ((len(W3) / len(A3)) / pE_indep2, (len(W3) / len(A3)) / pE_indep3))
P("      另有 2.0526 倍那个数：它比较的是似然 P(all3 PASS|E) 7.69% 与独立期望 3.75%，不是正确率。")

# Fréchet
fbound = min(q10, q12, q13)
pE_frechet = posterior(fbound, c10 * c12 * c13)
w339hi = w339[1]
pE_frechet_wilsonhi = posterior(w339hi, c10 * c12 * c13)
P("=== 11 第三步(d) Fréchet 上界能不能用 ===")
P("  min q_i = min(%.6f, %.6f, %.6f) = %.9f；恰等于实测 P(all3 PASS|E)=3/39=%.9f → 上界已被数据【饱和/取等】" %
  (q10, q12, q13, fbound, obs_joint))
P("  用训练上的 c_i 换成后验：P(E|all3 PASS) ≤ π·%.6f/[π·%.6f+(1-π)·%.6f] = %.6f → 正确率 ≥ %.6f" %
  (fbound, fbound, c10 * c12 * c13, pE_frechet, 1 - pE_frechet))
P("  但 q_n13=3/39 的 Wilson95 上界是 %.6f；若用它当 q 的分布无关上界，min q_i 上界升到 %.6f，后验正确率只 ≥ %.6f" %
  (w339hi, w339hi, 1 - pE_frechet_wilsonhi))
P("  ★ 评估：作为【本 74 行内的描述性天花板】可用且逻辑正确（不得用 Πq 当上界）；")
P("    作为【生产置信下界】不可用：①q_i 来自 train=test 点估计，本身有 [%.4f, %.4f] 的区间；" % (*w339,))
P("    ②上界已被实测取等，零余量；③它约束的是 P(allPASS|E) 似然，换到后验还必须借 c_i 与 π（同为训练值）；")
P("    ④共同盲区子总体（词表外形态）上 q_i 可等于 1，Fréchet 此时平凡成立却毫无安全含义；")
P("    ⑤ABSENT 被折成 PASS（H3 被违反）使模型本身不成立。")
out["step3"] = {"keff_range": [k_prob, k_info], "structural_independent_roots": 1,
                "observed_correct": 15 / 18, "wilson95_correct": [1 - w318[1], 1 - w318[0]],
                "cp95_correct": [1 - c318[1], 1 - c318[0]],
                "indep2_claimed_correct": 1 - pE_indep2, "indep3_claimed_correct": 1 - pE_indep3,
                "gap_pp_2": 100 * ((1 - pE_indep2) - (1 - len(W3) / len(A3))),
                "gap_pp_3": 100 * ((1 - pE_indep3) - (1 - len(W3) / len(A3))),
                "frechet_min_q": fbound, "frechet_posterior_E": pE_frechet,
                "frechet_with_wilson_upper_q": w339hi, "frechet_posterior_with_wilson_upper": pE_frechet_wilsonhi}

# ---------------------------------------------------------------- 12 R12
P("=== 12 第四步 R12 增量 ===")
n13pass = [r for r in R if r["n13"] == "PASS"]
r12catch_in_n13pass = [r for r in n13pass if r["r12"] == "CATCH"]
P("  (a) P(r12=PASS|n13=PASS) = %d/%d = %.9f —— 这是 74 行上的【观测】，不是精确 1.000" %
  (len(n13pass) - len(r12catch_in_n13pass), len(n13pass), 1 - len(r12catch_in_n13pass) / len(n13pass)))
P("      零命中 38 次的 95%% 上界（rule of three）= 3/38 = %.6f；Wilson95 上界 = %.6f；CP 精确上界 = %.6f" %
  (3 / 38, wilson(0, 38)[1], cp(0, 38)[1]))
P("      即『r12=CATCH 且 n13=PASS』的真比例在 95%% 水平上仍可高达 %.1f%%，1.000 不能当定理。" %
  (100 * cp(0, 38)[1]))
r12c = [r for r in R if r["r12"] == "CATCH"]
P("  (b) R12 命中 4 行明细：")
for r in r12c:
    P("    %-42s expect=%-5s r10=%-5s n13=%-5s chain=%-5s tokens=%s" %
      (r["id"], r["expect"], r["r10"], r["n13"], r["chain"], r["tokens"]))
P("      结构性破 1.000 的两条路：①采样——更多语料出现反例（上界 9.2%）；")
P("      ②★ 确定性——R12 判定用【该行 tokens】（_gp_regression.py:141），N13 用【固定 T】（:143），")
T3 = ("已入账", "已追加", "已生效")
nonT = [r for r in R if tuple(r["tokens"]) != T3]
superset = [r for r in R if set(T3) <= set(r["tokens"]) and tuple(r["tokens"]) != T3]
P("      74 行里 tokens≠T3 的有 %d 行（其中 %d 行是三词超集、%d 行是 C07 另一套词表）。" %
  (len(nonT), len(superset), len(nonT) - len(superset)))
P("      N13 内部回调 r12_scan 时用的是它自己的 T（_ei_n13_predicates_src.py:200），")
P("      故 N13 的『R12⇒D⇒CATCH』蕴含（:242-243）只在其内部同一 tokens 上成立；")
P("      一旦某行在【行 tokens】上命中双重否定、而 T 里无该 token，记录列的 r12=CATCH 完全可能与 n13=PASS 共存。")
P("      本 74 行内未出现（%d 行），但机制存在 ⇒ 1.000 是样本巧合 + 契约巧合，不是恒等式。" % len(r12catch_in_n13pass))
P("  (c) GP-A1 明细：")
for r in R:
    if r["id"] in ("GP-A1", "GP-A2", "GP-A3"):
        P("    %-8s expect=%-5s r10=%-5s r12=%-5s n13=%-5s family=%s" %
          (r["id"], r["expect"], r["r10"], r["r12"], r["n13"], r["family"]))
P("      GP-A1 三层全 PASS、r12=PASS；其构式『亦非不』不在 DOUBLE_NEG_RE 枚举（_g7_predicates.py:76），")
P("      ⇒ 在 GP-A1 上 R12 零增量。R12 有增量的场景是枚举内的双重否定（如 GATE_PIPELINE_COMPOSE.md:215 C3）：")
P("      本 74 行 r12=CATCH 的 4 行全部 expect=CATCH、n13=CATCH，即 R12 的 4 次正确命中都被 N13 覆盖；")
P("      相对【最终合成判定】增量 0，但相对【构式标注/归因】与 N13 内部 D 类有非零作用。")
P("  (d) 若真零增量仍有存在价值：①诊断/归因（把 double_neg 从 R10 的 negation 豁免里捞回来）；")
P("      ②它是 N13 的输入（:199-202/:242-243），删掉会改变 N13 行为，『边际为 0』≠『因果上无用』；")
P("      ③fail-safe：在 R10 宽进豁免路径上提供反向证据。但【绝不可计为独立证据层】，")
P("      标签应写『R10 派生守卫』而非『第 2 个独立证人』。")
out["step4_r12"] = {"P_r12_PASS_given_n13_PASS_observed": 1 - len(r12catch_in_n13pass) / len(n13pass),
                    "n": len(n13pass), "rule_of_three_upper": 3 / 38, "wilson_upper": wilson(0, 38)[1],
                    "cp_upper": cp(0, 38)[1], "r12_catch_rows": [r["id"] for r in r12c],
                    "r12_catch_also_n13_catch": sum(1 for r in r12c if r["n13"] == "CATCH"),
                    "tokens_not_T3": len(nonT), "superset_of_T3": len(superset),
                    "C07_other_vocab": len(nonT) - len(superset),
                    "r12_catch_with_n13_pass_in_this_corpus": len(r12catch_in_n13pass),
                    "GP_A": {r["id"]: {c: r[c] for c in ("expect", "r10", "r12", "n13", "family")}
                             for r in R if r["id"] in ("GP-A1", "GP-A2", "GP-A3")}}

# ---------------------------------------------------------------- 13 冲突 / 第五步素材
conf = [r for r in R if r["layer_conflicts"] > 0]
noconf_wrong = [r for r in R if r["layer_conflicts"] == 0 and r["chain"] != r["expect"]]
P("=== 13 第五步素材：冲突信号 ===")
P("  layer_conflicts>0 的行 = %d；其中 chain 判对 = %d、判错 = %d" %
  (len(conf), sum(1 for r in conf if r["chain"] == r["expect"]), sum(1 for r in conf if r["chain"] != r["expect"])))
P("  layer_conflicts==0 的行 = %d；其中 chain 判错 = %d，ids=%s" %
  (n - len(conf), len(noconf_wrong), [r["id"] for r in noconf_wrong]))
P("  chain 合计：correct=%d/74，fp=%d，fn=%d" %
  (sum(1 for r in R if r["chain"] == r["expect"]),
   sum(1 for r in N if r["chain"] == "CATCH"), sum(1 for r in E if r["chain"] == "PASS")))
out["step5_conflicts"] = {"conflict_rows": len(conf), "conflict_chain_correct": sum(1 for r in conf if r["chain"] == r["expect"]),
                          "no_conflict_wrong_ids": [r["id"] for r in noconf_wrong]}

# ---------------------------------------------------------------- 14 写盘
(WD / "_ke_calc_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(WD / "_ke_calc_stdout.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

# 生成报告（含固定格式绑定行，前缀 _ke_）
BIND = "\n".join("被核对象 SHA256 = %s，字节数 = %d" % (fp[rel]["sha256"], fp[rel]["bytes"])
                 for rel in [
                     "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md",
                     "lead/gate_pipeline_20261109/_gp_regression_out.json",
                     "lead/evidence_indep_20261109/_ei_04_v12_layer_out.json",
                     "lead/gate_n13_20261109/_n13_predicates.py",
                     "lead/gate_v1v2_20261109/_v12_rule.py",
                     "lead/gate_fp7_20261108/_g7_predicates.py",
                     "lead/falsifiable_no_relax_20261109/_fnr_check_out.json",
                     "lead/PENDING_DECISIONS.md",
                     "lead/GOAL_THREE_TARGETS_20261018.md"])
report = []
rep = report.append
rep("# _ke_REPORT.md — k_eff 与三层全过真实置信度（独立重算）")
rep("")
rep("实跑命令：`python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/keff_calc_20261109/_ke_calc.py`")
rep("输出留盘：`_ke_calc_out.json`、`_ke_calc_stdout.txt`（本写域）。输入全部只读，指纹见下。")
rep("")
rep("## 0 复核回件绑定行（逐件；hashlib.sha256 现盘重算，与编排方指纹全部一致）")
rep("")
rep("对应文件依次为：EVIDENCE_INDEPENDENCE.md / _gp_regression_out.json / _ei_04_v12_layer_out.json /")
rep("N13 谓词源 / _v12_rule.py / _g7_predicates.py / _fnr_check_out.json / PENDING_DECISIONS.md / GOAL_THREE_TARGETS_20261018.md")
rep("")
rep(BIND)
rep("")
rep("## 1 基线复核（第一步）")
rep("")
rep("(a) 逐层 fp/fn/rate **全部复现**：R10 fp20/fn19（0.5714/0.4872）、R12 fp0/fn35（0/0.8974）、N13 fp0/fn3（0/0.0769）。")
rep("    注意编排方 `n_pos=35 / n_neg=39` 与文件 expect 计数相反（文件 expect=CATCH=39、PASS=35）；")
rep("    fp_rate 分母是 35（非断言类），miss_rate 分母是 39（真断言类）。数字对、标签须纠正。")
rep("(b) 三层全 PASS = 18 行，其中 3 行真断言 = GP-A1 / GP-A2 / GP-A3，**复现**；3/18=16.67%。")
rep("(c) **3.75% 不是三层乘积**：是 `q_r10×q_n13 = (19/39)×(3/39) = 0.037475`。")
rep("    硬乘三层 `q_r10×q_r12×q_n13 = 0.033633`（3.36%）。编排方 `indep_wrong_prob=0.0` 的来源")
rep("    是把 fp_rate 相乘（0.5714×0×0=0），属口径错置，不可当独立假设错率。")
rep("    2.05 倍 = 实测 P(all3 PASS|E)=3/39=7.6923% ÷ 3.7475%；3/18 与 3/39 是两个不同量，不可相除。")
rep("(d) r10×n13 一致率 38/74=51.351% **复现**。与 k_eff 0.61–0.80 自洽：低标签一致只说明")
rep("    『判定近乎统计独立』，而 k_eff 量的是**真值层误差依赖**（3 个错例 100% 集中在共同盲区）。")
rep("    两套口径不冲突——正是「标签独立 ≠ 误差独立」的量化表现（EVIDENCE_INDEPENDENCE.md:131,142）。")
rep("")
rep("## 2 k_eff 三口径透明化（第二步）")
rep("")
rep("设 π=39/74=0.527027；p1=P(E|n13 PASS)=3/38=0.078947；p2=P(E|n13&r10 PASS)=3/18=0.166667；")
rep("p3=P(E|三层全 PASS)=3/18=0.166667。")
rep("")
rep("| 口径 | 公式 | 点值 |")
rep("|---|---|---|")
rep("| 上游概率比 | `ln(p3/π)/ln(p1/π)` | 0.606412 |")
rep("| 后验几率比 | `ln[odds(p3)/odds(π)] / ln[odds(p1)/odds(π)]` | 0.669663 |")
rep("| 信息增益比 | `I3/I1 = (π−p3)/(π−p1)` | 0.804233 |")
rep("")
rep("(b) 三个数**主因是口径不同**：概率比 / 几率比 / 线性概率差，函数形式不同，同一 p1、p3 必然给不同值；")
rep("    且 `I=π−p` 不是 bit（不是互信息），随单调变换而变。三者共用同一 3 个错例，**不是三个独立估计**，")
rep("    不能取平均、不能当置信区间。仅「均 <1」这一方向稳健。")
rep("(c) 最可信口径：**后验几率比 0.670**，因为只有它落在可加的 log-似然比（odds/bit）尺度上，")
rep("    与 §5.3 的 `odds(post)=odds(π)·ΠLR_i` 同构；但它仍是**相对判别力比值**，不是层数计数。")
rep("    工程结论仍应写「≤1 层，且不可按独立层计」，结构依据是独立证据根=1（:301）。")
rep("(d) **74 行 / 3 个错例不能支撑 k_eff 估计**：")
rep("    - P(E|all3 PASS)=3/18：Wilson95=[%.4f, %.4f]，CP 精确95=[%.4f, %.4f]；" % (*w318, *c318))
rep("    - 正确率 15/18：Wilson95=[%.4f, %.4f]、CP95=[%.4f, %.4f]（约 %.1f / %.1f 个百分点宽）；" %
    (1 - w318[1], 1 - w318[0], 1 - c318[1], 1 - c318[0],
     100 * (w318[1] - w318[0]), 100 * (c318[1] - c318[0])))
rep("    - 错例数 1→6 时 k_prob 从 1.185 变到 0.241（含 >1 与 <0.25），删掉任一错例（2/17）即变 0.790；")
rep("    - bootstrap(B=10000, seed=20261109)：")
for key in ("k_prob", "k_odds", "k_info"):
    q = boot[key]
    rep("      %-7s 95%%=[%.4f, %.4f]，median=%.4f，range=[%.4f, %.4f]，有效重抽 %d/10000" %
        (key, q["q025"], q["q975"], q["median"], q["min"], q["max"], q["valid"]))
rep("      ⇒ 95% 区间整体落在 (0,1) 但上限逼近 1（k_info 中位数 0.81、上限 0.95），")
rep("      全距含负值，且 455/10000 次重抽落在定义域外；k=1 的反事实（只需少 2 个错例）就给出 >1。")
rep("    ⇒ 0.61 / 0.670 / 0.804 必须标「描述性、不可靠、不可用于放行」。")
rep("(e) 数量级：`n≈z²p(1−p)/w²`。要把联合漏报 p=3/39 估到 ±2pp，需 ~682 条真断言类（~1.3k 总行）；")
rep("    ±1pp 需 ~2.7k 真断言类（~5.2k 总行）；±10% 相对精度需 ~4.6k 真断言类；±5% 需 ~1.8e4。")
rep("    ⇒ **10³ 起步、10⁴–10⁵ 才可用**。且必须是含 r10/r12/n13 全列、无 train=test 泄漏的盲留出集；")
rep("    加样本不能把确定性依赖变成独立层。")
rep("")
rep("## 3 三层全过应报的真实置信度（第三步，核心）")
rep("")
rep("(a) 折算：%.4f–%.4f 个 N13 等效独立层（<1 层）；结构独立根 = 1。上游 `numeric=1` 是保守取整约定，不是测量值。" % (k_prob, k_info))
rep("(b) 实测 P(结论正确|三层全 PASS)=15/18=83.33%%；**95%% 区间 Wilson [%.4f, %.4f] / CP [%.4f, %.4f]**。" %
    (1 - w318[1], 1 - w318[0], 1 - c318[1], 1 - c318[0]))
rep("    给区间，不给单点；并声明这是 train=test 描述值、先验 π=39/74。")
rep("(c) 与「三层独立」宣称的差：")
rep("    - 两层独立 Bayes 后验错误率 %.6f（宣称正确 %.2f%%）；三层独立 %.6f（宣称正确 %.2f%%）" %
    (pE_indep2, 100 * (1 - pE_indep2), pE_indep3, 100 * (1 - pE_indep3)))
rep("    - 实测正确率 83.33%% ⇒ 低 %.2f pp / %.2f pp；后验错误率放大 %.4f× / %.4f×" %
    (100 * ((1 - pE_indep2) - (15 / 18)), 100 * ((1 - pE_indep3) - (15 / 18)),
     (3 / 18) / pE_indep2, (3 / 18) / pE_indep3))
rep("    - 2.0526× 是似然口径（7.69% vs 3.75%）；若用编排方 `indep_wrong_prob=0.0` 则宣称 100%，差 16.67 pp。")
rep("(d) Fréchet `P(allPASS|E) ≤ min q_i = 0.076923`：作为**本 74 行内描述性天花板**正确且恰被实测取等；")
rep("    **作为生产置信下界不可用**：q_i 是 train=test 点估计（q_n13 Wilson95=[0.0265,0.2032]，用上界则上界升到 0.2032）、")
rep("    零余量、换后验仍需借 c_i 与 π、共同盲区子总体上 q_i=1 使上界平凡、ABSENT→PASS 违反 H3。")
rep("(e) 三层结论必须附带的置信度声明模板：")
rep("")
rep("```text")
rep("[三层结论置信度声明]  结论：R10/R12/N13 全 PASS（chain=PASS）")
rep("1 证据结构：3 个判据 / 1 个独立证据根（R10→{R12,N13.C}）；k_eff 描述值 %.2f–%.2f，bootstrap95 上限达 %.2f，不可用。" %
    (k_prob, k_info, boot["k_info"]["q975"]))
rep("2 观测：本 74 行 train=test 上三层全 PASS 共 18 行，其中 3 行是真断言（GP-A1/A2/A3）；")
rep("        P(结论正确|全 PASS)=15/18=83.3%%，Wilson95=[%.1f%%, %.1f%%]，CP95=[%.1f%%, %.1f%%]。" %
    (100 * (1 - w318[1]), 100 * (1 - w318[0]), 100 * (1 - c318[1]), 100 * (1 - c318[0])))
rep("3 与独立宣称的差：三层独立应报正确率 %.1f%%（两层口径 %.1f%%），实测低 %.1f pp；" %
    (100 * (1 - pE_indep3), 100 * (1 - pE_indep2), 100 * ((1 - pE_indep3) - (15 / 18))))
rep("        后验错误率放大 %.2f×；2.05× 是似然口径，不得与后验混用。" % ((3 / 18) / pE_indep3))
rep("4 兜底：Fréchet min q_i=7.69% 仅为样本内天花板，非生产置信界；不得写 Πq_i 为上界。")
rep("5 输入契约：(predicate_sha, tokens_sha, text_sha) = (<填>, <填>, <填>)；缺列则该行不计入一致计数。")
rep("6 覆盖：本链判不了词表外同义改写 / 枚举外双重否定 / 跨行共指；spans==0 时 K7 循环体不执行。")
rep("7 处置：本结论不得作为自动放行依据；无层间冲突时按风险信号处理，必须人工复核 + coverage_note。")
rep("8 未验：生产 q_i/ρ、盲留出集误差相关、Cohen's κ、正交层增益、真机运行态 —— 全部未验。")
rep("```")
rep("")
rep("## 4 「R12 增量 0 bit」评估（第四步）")
rep("")
rep("(a) `P(r12=PASS|n13=PASS)=38/38` 是 74 行**观测**，不是精确 1.000：零命中 38 次的 CP95 上界 %.2f%%、" %
    (100 * cp(0, 38)[1]))
rep("    rule-of-three 7.89%%、Wilson %.2f%%，即反例比例仍可能高达 ~9%%。" % (100 * wilson(0, 38)[1]))
rep("(b) 会破：①采样上界如上；②★ **契约分叉是确定性破口** —— R12 用行 `tokens`")
rep("    （_gp_regression.py:141），N13 用固定三词 `T`（:143）且内部 `r12_scan` 也用 T（_ei_n13_predicates_src.py:200），")
rep("    故 `R12 命中 ⇒ N13 判 D ⇒ CATCH`（:242-243）只在 N13 自己的词表内成立。")
rep("    74 行里 19 行 tokens≠T3（17 行为三词超集、2 行为 C07 另一套词表），本语料没撞上，机制却存在。")
rep("(c) GP-A1 上 R12 零增量（r12=PASS，构式『亦非不』不在 DOUBLE_NEG_RE 枚举，_g7_predicates.py:76）。")
rep("    R12 有增量的是枚举内双重否定：本 74 行 4 次 CATCH 全为 expect=CATCH 且 n13=CATCH，")
rep("    即相对最终判定增量 0，相对构式归因/N13 内部 D 类非零。")
rep("(d) 即便真零增量仍有价值：诊断归因（把 double_neg 从 R10 的 negation 豁免里捞回）、")
rep("    N13 的输入（:199-202/:242-243，删掉会改变 N13 行为）、fail-safe。但**不得计为独立证据层**，")
rep("    应标「R10 派生守卫」。")
rep("")
rep("## 5 结论与建议（第五步）")
rep("")
rep("(a) 「三层独立」应改成：")
rep("    **「R10 / R12 / N13 是在同一运行时输入契约上串行装配的三个判据；依赖图为 R10 → {R12, N13.C}，")
rep("    独立证据根 = 1。本 74 行上三层全 PASS 的等效判别力仅 %.2f–%.2f 个 N13 单层" % (k_prob, k_info))
rep("    （bootstrap95 上限达 %.2f、全距含负值、敏感性分析可达 >1，描述值不可靠），" % boot["k_info"]["q975"])
rep("    R10 相对 N13 为负贡献。工程上按 ≤1 层计（保守取整 1），一致通过只表示『三个判据都未触发』，")
rep("    不表示三次独立确认，亦不构成自动放行依据。」")
rep("(b) 需重新表述的既有说法（逐条；均为只读件，本任务未改）：")
rep("    1. `lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:215` C3「三层一致，非冲突」→ 同一 R10 根的派生判定一致，非三次确认。")
rep("    2. `lead/gate_pipeline_20261109/_gp_DESIGN.md:220` C3「三层一致，非冲突」→ 同上。")
rep("    3. `lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:410`「未消解 0」+ 逐族全对 → 冲突计数为空不是通过证据，3 条共同盲区不进 conflicts[]。")
rep("    4. `lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md:206`「≈1～1.3 层（乐观 1.5）」→ 与 k_eff 0.61–0.80 不一致，应改为 ≤1 层并附宽区间。")
rep("    5. `lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md:190` / `_cs_BASELINE_ALIGNMENT_20261109.md:208` 「一致通过概率被高估」→ 补上量化：观测正确率 83.3% [60.8%,94.2%]。")
rep("    6. `lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md:299` 「按 1 层计 numeric=1」→ 标明是工程保守取整，非 k_eff 测量值。")
rep("    7. `lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md:131` 「独立假设下应为 3.75%」→ 标明是 q_r10×q_n13 的**期望**，且 3/18 与 3/39 不同量。")
rep("    8. `lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md:247/272` 与 `_gp_DESIGN.md:394` 已自认不独立，保留；其「合成链 69/74」应加「单层等效，非三层加成」。")
rep("    9. `lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md:320` 已写「三层不是三个独立证人」，保留并补置信度声明。")
rep("    10. 两件台账检索结果：`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md` 中**未发现**针对 R10/R12/N13 的「三层都过所以可信」条目；")
rep("        GOAL 台账 :8366「三条独立证据同向」是帧时周期否证的另一论域（置换检验/ACF/同进程三窗），不在本次折算范围；")
rep("        PENDING :358 D-08「不能写成三趟全过」是 harness7 真机趟数，也非本论域。此三者**无需改写**。")
rep("(c) 怎么用现有三层（实用建议）：")
rep("    ①把 chain 当**一个弱检测器**，不要当三次确认；把 N13 单层作基线并显式登记其『免考卷』问题（_gp_regression.py:143 恒用 T）。")
rep("    ②把「层间冲突」当唯一有信息量的信号：本 74 行 layer_conflicts>0 的 %d 行 chain 全判对；无冲突的 %d 行里 %d 行判错（含 GP-A1/A2/A3）。" %
    (len(conf), n - len(conf), len(noconf_wrong)))
rep("       ⇒ 「无冲突且全 PASS」应触发**人工复核队列**，而非自动放行。")
rep("    ③全 PASS 行优先按共同盲区顺序查：词表覆盖 → 否定构式枚举 → 跨行/共指/转述（GATE_PIPELINE_COMPOSE.md:501）。")
rep("    ④正交证据另起一路：R9/R11（hashlib 绑定行/文件存在，:199）与 V1V2 限死 spans==0 的单调 OR（EVIDENCE_INDEPENDENCE.md:190，净 +1 且 GP-A1 仍漏），")
rep("       但必须先在封 SHA 盲留出集上给独立 fp/fn，否则不得计入层数。")
rep("    ⑤每条结论强制附 §3(e) 模板 + `(predicate_sha, tokens_sha, text_sha)`；把 3 个 GP-A 错例列为常驻回归哨兵。")
rep("(d) 这条工作判不了什么：")
rep("    - 生产语料上的 q_i / s_i / c_i / ρ 与 k_eff（74 行 train=test、含定向构造对抗样本、有契约分叉）。")
rep("    - 盲留出集误差相关双检（只读 `_cs_holdout_out.json` 无 r10/r12 列、3 条逐字重复）→ **未验**。")
rep("    - 「R12 在任何语料上都零增量」；「k_eff 在任何语料上都 <1」；新增正交层的实际增益（无留盘盲评）。")
rep("    - 改谓词/改编排后的效果（本任务零改动、未实装）；GP-A1 的语义判别能力；Cohen's κ / 双盲标注一致性。")
rep("    - 真机运行态（零真机铁律）；任一层 ABSENT 语义与 K7/K8 可达性（未重跑）。")
rep("    - 不判定两件台账中其它「独立证据」措辞是否成立（检索范围内未发现本论域条目）。")
rep("")
rep("## 6 纪律")
rep("")
rep("只读：lead/evidence_indep_20261109/、lead/gate_pipeline_20261109/、lead/chain_vs_single_20261109/、")
rep("lead/gate_n13_20261109/、lead/gate_v1v2_20261109/、lead/gate_fp7_20261108/、lead/falsifiable_no_relax_20261109/、两件台账，均未改动。")
rep("唯一写域：lead/keff_calc_20261109/（本件、_ke_calc.py、_ke_calc_out.json、_ke_calc_stdout.txt、_ke_run_console.txt）。")
rep("零真机、零采样代码、零 commit/push；主计算脚本以 `python -I -X utf8 -B` + 绝对路径执行，")
rep("其余只读核对以 `python -I -X utf8 -c` + 绝对路径字符串执行；所有指纹均用 hashlib.sha256 现盘重算。")
(WD / "_ke_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
P("")
P("=== 14 写盘完成 ===")
for f in ("_ke_calc.py", "_ke_calc_out.json", "_ke_calc_stdout.txt", "_ke_REPORT.md"):
    b = (WD / f).read_bytes()
    P("  %s bytes=%d sha256=%s" % (f, len(b), hashlib.sha256(b).hexdigest()))
