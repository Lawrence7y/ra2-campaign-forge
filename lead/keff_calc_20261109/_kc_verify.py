# -*- coding: utf-8 -*-
# 本任务独立校验脚本：只做计算与推导，不修改任何模块/语料/只读件。
# 用法：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/keff_calc_20261109/_kc_verify.py
import hashlib, json, math
from pathlib import Path

R = Path('D:/Project/ra2-campaign-forge')
WD = R / 'lead/keff_calc_20261109'
GP = R / 'lead/gate_pipeline_20261109/_gp_regression_out.json'
EI = R / 'lead/evidence_indep_20261109/_ei_04_v12_layer_out.json'

FP = {
 'lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md': ('aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523', 36194),
 'lead/gate_pipeline_20261109/_gp_regression_out.json': ('d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe', 38575),
 'lead/evidence_indep_20261109/_ei_04_v12_layer_out.json': ('3253eb8456ceab54df1b41629caa4eaee8fcabff5e016e18fd71a3a3606b4546', 51602),
 'lead/evidence_indep_20261109/_ei_n13_predicates_src.py': ('e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079', 16649),
 'lead/gate_v1v2_20261109/_v12_rule.py': ('15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0', 9148),
 'lead/gate_fp7_20261108/_g7_predicates.py': ('02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120', 11743),
 'lead/falsifiable_no_relax_20261109/_fnr_check_out.json': ('f3112b225b1de35183ad4604554cb25689ed252b6a5a95d96d17fce53c8c140e', 8733),
 'lead/PENDING_DECISIONS.md': ('3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7', 52419),
 'lead/GOAL_THREE_TARGETS_20261018.md': ('2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede', 759518),
}

out = []
def p(s=''):
    out.append(str(s))

p('=== A 指纹（hashlib 现盘重算，9 件只读件）===')
fp_ok = True
for rel, (sha, byt) in FP.items():
    b = (R / rel).read_bytes()
    h = hashlib.sha256(b).hexdigest()
    m = (h == sha and len(b) == byt)
    fp_ok &= m
    p('  %s sha256=%s bytes=%d %s' % (m, h, len(b), rel))
p('FP_ALL_MATCH %s count %d' % (fp_ok, len(FP)))

g = json.loads(GP.read_text(encoding='utf-8'))['rows']
e = json.loads(EI.read_text(encoding='utf-8'))['rows']
p('')
p('=== B 数据一致性 ===')
p('  GP rows=%d EI rows=%d' % (len(g), len(e)))
ids_eq = [x['id'] for x in g] == [x['id'] for x in e]
cols = ['r10', 'r12', 'n13', 'chain', 'expect']
col_eq = all(all(a[c] == b[c] for c in cols) for a, b in zip(g, e))
p('  id 序列全等=%s 5 列逐行全等=%s' % (ids_eq, col_eq))

n = len(g)
nE = sum(x['expect'] == 'CATCH' for x in g)   # 真断言类
nN = sum(x['expect'] == 'PASS' for x in g)    # 非断言类
pi = nE / n
p('  expect=CATCH(真断言类)=%d PASS(非断言类)=%d pi=%.9f' % (nE, nN, pi))

p('')
p('=== C 逐层 fp/fn/rate（fp 分母=%d 非断言，fn 分母=%d 真断言）===' % (nN, nE))
per = {}
for L in ['r10', 'r12', 'n13', 'chain']:
    C = sum(x[L] == 'CATCH' for x in g)
    P = sum(x[L] == 'PASS' for x in g)
    fp = sum(x[L] == 'CATCH' and x['expect'] == 'PASS' for x in g)
    fn = sum(x[L] == 'PASS' and x['expect'] == 'CATCH' for x in g)
    per[L] = dict(CATCH=C, PASS=P, fp=fp, fn=fn, fp_rate=fp / nN, miss_rate=fn / nE, q=fn / nE, c=(nN - fp) / nN)
    p('  %-5s CATCH=%2d PASS=%2d fp=%2d/%d=%.6f fn=%2d/%d=%.6f q=%.6f c=%.6f' %
      (L, C, P, fp, nN, fp / nN, fn, nE, fn / nE, fn / nE, (nN - fp) / nN))

base = {'r10': (20, 19, 0.5714, 0.4872), 'r12': (0, 35, 0.0, 0.8974), 'n13': (0, 3, 0.0, 0.0769)}
p('  对照编排方 per_layer：')
for L, (bfp, bfn, bfr, bmr) in base.items():
    d = per[L]
    p('    %-5s fp %d==%d %s | fn %d==%d %s | fp_rate %.4f==%.4f %s | miss_rate %.4f==%.4f %s' %
      (L, d['fp'], bfp, d['fp'] == bfp, d['fn'], bfn, d['fn'] == bfn,
       d['fp_rate'], bfr, round(d['fp_rate'], 4) == bfr, d['miss_rate'], bmr, round(d['miss_rate'], 4) == bmr))

p('')
p('=== D 三层全过 ===')
a3 = [x for x in g if x['r10'] == 'PASS' and x['r12'] == 'PASS' and x['n13'] == 'PASS']
w3 = [x['id'] for x in a3 if x['expect'] == 'CATCH']
p('  all3_pass=%d wrong=%d ids=%s' % (len(a3), len(w3), w3))
p('  P(E|all3 PASS)=3/18=%.9f  P(正确|all3 PASS)=15/18=%.9f' % (len(w3) / len(a3), (len(a3) - len(w3)) / len(a3)))
p('  18 行 chain 是否全 PASS=%s' % all(x['chain'] == 'PASS' for x in a3))

p('')
p('=== E 独立假设错率算式 ===')
q10, q12, q13 = per['r10']['q'], per['r12']['q'], per['n13']['q']
c10, c12, c13 = per['r10']['c'], per['r12']['c'], per['n13']['c']
prod2 = q10 * q13
prod3 = q10 * q12 * q13
p('  q10=%.9f q12=%.9f q13=%.9f' % (q10, q12, q13))
p('  3.75%% = q10*q13 = %.9f ; 硬乘三层 q10*q12*q13 = %.9f' % (prod2, prod3))
p('  编排 indep_wrong_prob=0.0 来源 fp_rate 乘积 = %.9f*%.9f*%.9f = %.9f （口径错置：非断言被误拦率，非真断言被放过率）' %
  (per['r10']['fp_rate'], per['r12']['fp_rate'], per['n13']['fp_rate'],
   per['r10']['fp_rate'] * per['r12']['fp_rate'] * per['n13']['fp_rate']))
obs_joint = sum(all(x[L] == 'PASS' for L in ['r10', 'r12', 'n13']) and x['expect'] == 'CATCH' for x in g) / nE
p('  P(all3 PASS|E) 实测=3/39=%.9f ; 放大 0.076923/0.037475=%.9f（2.05 倍，似然口径）' % (obs_joint, obs_joint / prod2))
p('  3/18 / 3.75%% = %.6f （后验÷似然，类别错误，不得用）' % ((len(w3) / len(a3)) / prod2))

def bayes(qprod, cprod):
    return pi * qprod / (pi * qprod + (1 - pi) * cprod)
pe2 = bayes(prod2, c10 * c13)
pe3 = bayes(prod3, c10 * c12 * c13)
p('  Bayes 2 层独立 P(E|全PASS)=%.9f 宣称正确=%.6f%%' % (pe2, (1 - pe2) * 100))
p('  Bayes 3 层独立 P(E|全PASS)=%.9f 宣称正确=%.6f%%' % (pe3, (1 - pe3) * 100))
pc = (len(a3) - len(w3)) / len(a3)
p('  实测正确=%.6f%% → 低 %.4f pp(2层)/%.4f pp(3层) ; 后验错误率放大 %.4f×/%.4f×' %
  (pc * 100, (1 - pe2) * 100 - pc * 100, (1 - pe3) * 100 - pc * 100,
   (len(w3) / len(a3)) / pe2, (len(w3) / len(a3)) / pe3))

p('')
p('=== F r10×n13 交叉表 / 一致率 / k_eff 自洽 ===')
ct = {}
for x in g:
    ct[(x['r10'], x['n13'])] = ct.get((x['r10'], x['n13']), 0) + 1
p('  交叉 (r10,n13): CATCH/CATCH=%d CATCH/PASS=%d PASS/CATCH=%d PASS/PASS=%d' %
  (ct.get(('CATCH', 'CATCH'), 0), ct.get(('CATCH', 'PASS'), 0), ct.get(('PASS', 'CATCH'), 0), ct.get(('PASS', 'PASS'), 0)))
agree = ct.get(('CATCH', 'CATCH'), 0) + ct.get(('PASS', 'PASS'), 0)
p('  一致率 = %d/%d = %.9f（51.35%%）；低标签一致 ≠ 误差独立，3 错 100%% 落在共同盲区' % (agree, n, agree / n))

p('')
p('=== G k_eff 三口径 ===')
p1 = sum(x['n13'] == 'PASS' and x['expect'] == 'CATCH' for x in g) / sum(x['n13'] == 'PASS' for x in g)
p2 = sum(x['n13'] == 'PASS' and x['r10'] == 'PASS' and x['expect'] == 'CATCH' for x in g) / sum(x['n13'] == 'PASS' and x['r10'] == 'PASS' for x in g)
p3 = len(w3) / len(a3)
p('  pi=%.9f p1=P(E|n13 PASS)=%.9f p2=P(E|n13&r10 PASS)=%.9f p3=P(E|三层全PASS)=%.9f' % (pi, p1, p2, p3))
odds = lambda p: p / (1 - p)
kp = math.log(p3 / pi) / math.log(p1 / pi)
ko = math.log(odds(p3) / odds(pi)) / math.log(odds(p1) / odds(pi))
ki = (pi - p3) / (pi - p1)
p('  (1) 概率比 k_prob  = ln(p3/pi)/ln(p1/pi) = %.9f (≈0.61)' % kp)
p('  (2) 后验几率比 k_odds = ln[odds(p3)/odds(pi)]/ln[odds(p1)/odds(pi)] = %.9f (≈0.670)' % ko)
p('  (3) 信息增益比 k_info = (pi-p3)/(pi-p1) = %.9f (≈0.804)' % ki)
p('  R12 真 bit 增量 log2(odds(p3)/odds(p2)) = %.9f' % math.log2(odds(p3) / odds(p2)))

p('')
p('=== H 小样本区间（scipy norm.ppf / beta.ppf，独立实现）===')
from scipy.stats import beta, norm
z = norm.ppf(0.975)
p('  z=norm.ppf(0.975)=%.9f' % z)
def wilson(k, N, zz):
    ph = k / N
    d = 1 + zz * zz / N
    c = (ph + zz * zz / (2 * N)) / d
    h = zz * math.sqrt(ph * (1 - ph) / N + zz * zz / (4 * N * N)) / d
    return (c - h, c + h)
def cp(k, N):
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, N - k + 1)
    hi = 1.0 if k == N else beta.ppf(0.975, k + 1, N - k)
    return (lo, hi)
for lbl, k, N in [('P(E|全PASS)=3/18', 3, 18), ('P(正确)=15/18', 15, 18), ('q_n13=3/39', 3, 39)]:
    w = wilson(k, N, z); c = cp(k, N)
    p('  %-20s Wilson95=[%.6f, %.6f] CP95=[%.6f, %.6f] 宽度=%.2f pp / %.2f pp' %
      (lbl, w[0], w[1], c[0], c[1], (w[1] - w[0]) * 100, (c[1] - c[0]) * 100))
# P(正确)=15/18 的 CP 由补集关系：1-CP_upper(3/18), 1-CP_lower(3/18)
ce = cp(3, 18)
p('  补集核对 P(正确) CP95=[1-%.6f, 1-%.6f]=[%.6f, %.6f]' % (ce[1], ce[0], 1 - ce[1], 1 - ce[0]))

p('')
p('=== I 敏感性（固定 18 行分母，仅改错例数 k）===')
for k in range(1, 7):
    pp = k / 18
    kpx = math.log(pp / pi) / math.log(p1 / pi)
    kox = math.log(odds(pp) / odds(pi)) / math.log(odds(p1) / odds(pi))
    kix = (pi - pp) / (pi - p1)
    p('  k=%d p3=%.6f k_prob=%.4f k_odds=%.4f k_info=%.6f' % (k, pp, kpx, kox, kix))
p('  LOO 删任一错例 → 2/17=%.6f k_prob=%.4f' % (2 / 17, math.log((2 / 17) / pi) / math.log(p1 / pi)))

p('')
p('=== J 独立 bootstrap（numpy PCG64 seed=90210, B=10000，与作者 LCG 不同实现）===')
import numpy as np
rng = np.random.default_rng(90210)
N, B = n, 10000
idx = rng.integers(0, N, size=(B, N))
arr_expect = np.array([1 if x['expect'] == 'CATCH' else 0 for x in g])
arr_n13 = np.array([1 if x['n13'] == 'PASS' else 0 for x in g])
arr_r10 = np.array([1 if x['r10'] == 'PASS' else 0 for x in g])
arr_r12 = np.array([1 if x['r12'] == 'PASS' else 0 for x in g])
E = arr_expect[idx]; N13 = arr_n13[idx]; R10 = arr_r10[idx]; R12 = arr_r12[idx]
pib = E.mean(axis=1)
n13m = (N13 == 1)
all3m = (N13 == 1) & (R10 == 1) & (R12 == 1)
p1b = np.divide((E * N13).sum(axis=1), n13m.sum(axis=1), out=np.full(B, np.nan), where=n13m.sum(axis=1) > 0)
p3b = np.divide((E * all3m).sum(axis=1), all3m.sum(axis=1), out=np.full(B, np.nan), where=all3m.sum(axis=1) > 0)
with np.errstate(divide='ignore', invalid='ignore'):
    kpb = np.log(p3b / pib) / np.log(p1b / pib)
    kob = np.log((p3b / (1 - p3b)) / (pib / (1 - pib))) / np.log((p1b / (1 - p1b)) / (pib / (1 - pib)))
    kib = (pib - p3b) / (pib - p1b)
for nm, v in [('k_prob', kpb), ('k_odds', kob), ('k_info', kib), ('p3', p3b)]:
    good = np.isfinite(v) & (v > -1) & (v < 2)
    q = np.percentile(v[good], [2.5, 50, 97.5])
    p('  %-7s valid=%d 95%%=[%.4f, %.4f] median=%.4f range=[%.4f, %.4f]' %
      (nm, good.sum(), q[0], q[2], q[1], v[good].min(), v[good].max()))
p('  ★ 点值 0.61/0.670/0.804 共用同一 3 错例，上限逼近 1、全距含负值 → 描述性、不可靠、不可用于放行')

p('')
p('=== K 样本量（正态近似）===')
def nabs(p_, w_):
    return z * z * p_ * (1 - p_) / (w_ * w_)
def nrel(p_, r_):
    return z * z * (1 - p_) / (r_ * r_ * p_)
for lbl, pp, w_, kind in [('joint_miss 3/39 ±2pp', 3 / 39, 0.02, 'abs'), ('joint_miss 3/39 ±1pp', 3 / 39, 0.01, 'abs'),
                           ('posterior 3/18 ±5pp', 3 / 18, 0.05, 'abs'), ('posterior 3/18 ±2pp', 3 / 18, 0.02, 'abs')]:
    ne = nabs(pp, w_)
    p('  %-24s n_E≈%d 条真断言类 → 总行≈%d' % (lbl, math.ceil(ne), math.ceil(ne / pi)))
for lbl, r_ in [('joint_miss 相对 ±10%', 0.10), ('joint_miss 相对 ±5%', 0.05)]:
    ne = nrel(3 / 39, r_)
    p('  %-24s n_E≈%d 条真断言类 → 总行≈%d' % (lbl, math.ceil(ne), math.ceil(ne / pi)))
p('  100 个全PASS错例需 ≈600 全PASS行 ≈%d 总行' % math.ceil(600 / (len(a3) / n)))

p('')
p('=== L R12 零增量 ===')
n13p = [x for x in g if x['n13'] == 'PASS']
r12c_in = [x['id'] for x in n13p if x['r12'] == 'CATCH']
p('  n13=PASS 行数=%d 其中 r12=CATCH 行数=%d → P(r12=PASS|n13=PASS)=%d/%d=1.000（观测，非定理）' %
  (len(n13p), len(r12c_in), len(n13p) - len(r12c_in), len(n13p)))
p('  零命中 38 次单侧精确 95%% 上界 1-0.05^(1/38)=%.6f ; 双侧 1-0.025^(1/38)=%.6f' %
  (1 - 0.05 ** (1 / 38), 1 - 0.025 ** (1 / 38)))
p('  Wilson 双侧 95%% 上界=%.6f ; rule-of-three 单侧近似 3/38=%.6f（口径须标注，不可混列）' %
  (wilson(0, 38, z)[1], 3 / 38))
T3 = ['已入账', '已追加', '已生效']
diff = [x for x in g if x['tokens'] != T3]
sup = [x for x in diff if set(T3).issubset(set(x['tokens']))]
p('  tokens≠T3 行数=%d 其中三词超集=%d 其它=%d' % (len(diff), len(sup), len(diff) - len(sup)))
r12c = [x for x in g if x['r12'] == 'CATCH']
p('  r12=CATCH 的 4 行 id=%s ; 全部 expect=CATCH 且 n13=CATCH = %s' %
  ([x['id'] for x in r12c], all(x['expect'] == 'CATCH' and x['n13'] == 'CATCH' for x in r12c)))
p('  GP-A1/A2/A3 三层全 PASS 且 r12=PASS = %s' %
  all(x['r12'] == 'PASS' for x in g if x['id'] in ('GP-A1', 'GP-A2', 'GP-A3')))

p('')
p('=== M 冲突信号 ===')
conf = [x for x in g if x['layer_conflicts'] > 0]
noconf = [x for x in g if x['layer_conflicts'] == 0]
def wrong(xs):
    return [x['id'] for x in xs if (x['chain'] == 'PASS') != (x['expect'] == 'PASS')]
p('  conflicts>0 行=%d chain 判错=%s ; conflicts==0 行=%d chain 判错=%d ids=%s' %
  (len(conf), wrong(conf), len(noconf), len(wrong(noconf)), wrong(noconf)))
p('  chain 合计 correct=%d/%d fp=%d fn=%d' %
  (n - len(wrong(g)), n, per['chain']['fp'], per['chain']['fn']))

p('')
p('=== N Fréchet 上界 ===')
qmin = min(q10, q12, q13)
p('  min q_i = %.9f ; 实测 P(allPASS|E)=%.9f → 上界被取等（饱和、零余量）' % (qmin, obs_joint))
post_fb = bayes(qmin, c10 * c12 * c13)
p('  借 c_i,pi 换后验 P(E|全PASS)≤%.9f → 正确率≥%.9f（样本内）' % (post_fb, 1 - post_fb))
q13hi = wilson(3, 39, z)[1]
post_fb2 = bayes(min(q10, q12, q13hi), c10 * c12 * c13)
p('  若用 q_n13 Wilson95 上界 %.6f → 后验正确率仅 ≥%.6f（生产置信下界不可用）' % (q13hi, 1 - post_fb2))

p('')
p('=== O 必现要素自检 ===')
for k in ['k_eff', '0.61', '0.670', '0.804', '16.7%', '3.75%', '2.05', '51.35%', '区间', '样本量', '零增量', 'Fréchet', '置信度声明', '精确表述', '未验']:
    p('  key %-8s present-in-doc-check = (交付文档自行核对)' % k)

txt = '\n'.join(out) + '\n'
(WD / '_kc_verify_stdout.txt').write_text(txt, encoding='utf-8')
(WD / '_kc_verify_out.json').write_text(json.dumps({
    'fp_all_match': fp_ok, 'ids_eq': ids_eq, 'col_eq': col_eq,
    'n': n, 'nE': nE, 'nN': nN, 'pi': pi, 'per': per,
    'all3_pass': len(a3), 'all3_wrong': len(w3), 'wrong_ids': w3,
    'prod2': prod2, 'prod3': prod3, 'obs_joint': obs_joint, 'amplification': obs_joint / prod2,
    'pe2': pe2, 'pe3': pe3, 'agree': agree,
    'p1': p1, 'p2': p2, 'p3': p3, 'kp': kp, 'ko': ko, 'ki': ki,
    'wilson_3_18': wilson(3, 18, z), 'cp_3_18': cp(3, 18),
    'wilson_15_18': wilson(15, 18, z), 'cp_15_18': (1 - cp(3, 18)[1], 1 - cp(3, 18)[0]),
    'wilson_3_39': wilson(3, 39, z), 'cp_3_39': cp(3, 39),
    'n13_pass_n': len(n13p), 'r12catch_among': len(r12c_in),
    'r12_cp_onesided': 1 - 0.05 ** (1 / 38), 'r12_cp_twosided': 1 - 0.025 ** (1 / 38),
    'r12_wilson_upper': wilson(0, 38, z)[1], 'r12_rule3': 3 / 38,
    'tokens_diff_n': len(diff), 'tokens_super3_n': len(sup),
    'conf_n': len(conf), 'conf_wrong': wrong(conf), 'noconf_n': len(noconf), 'noconf_wrong': wrong(noconf),
    'frechet_minq': qmin, 'frechet_post_min_correct': 1 - post_fb, 'frechet_wilson_min_correct': 1 - post_fb2,
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(txt)
