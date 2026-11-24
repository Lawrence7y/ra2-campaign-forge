# -*- coding: utf-8 -*-
# _pv_final_checks.py — 设计效应显著性阈值、绑定行格式自检、只读域零漂移复核
import math, hashlib, re, os

BASE = 'D:/Project/ra2-campaign-forge/'
print('=== A. 设计效应下「保持名义 p<0.05」所需 rho 上界 ===')
# p_two(n) = 2*2^-n（连续外推，仅作说明）；需 2*2^-n_eff < 0.05
n = 18
ne_needed = math.log2(2 / 0.05)   # 2^-ne < 0.025 -> ne > log2(40)
print('2*2^-n_eff < 0.05  =>  n_eff > log2(40) =', ne_needed)
rho_cont = (n / ne_needed - 1) / (n - 1)
print('连续外推: rho < (18/%.6f - 1)/17 =' % ne_needed, rho_cont)
# 离散 n_eff 取整（floor）下需 n_eff>=6
ne_int = 6
rho_int = (n / ne_int - 1) / (n - 1)
print('离散 n_eff>=6: rho <= (18/6 - 1)/17 =', rho_int, '= 2/17')
for rho in (0.0, 0.1176, 0.14, 0.3, 0.5, 0.8, 0.9, 1.0):
    ne = 18 / (1 + 17 * rho)
    p_cont = min(1.0, 2 * 2.0 ** (-ne))
    print('  rho=%.4f  deff=%.4f  n_eff=%.4f  floor(n_eff)=%d  p(floor)=%s  p(连续外推)=%.6g'
          % (rho, 1 + 17 * rho, ne, math.floor(ne), min(1.0, 2 * 2.0 ** (-math.floor(ne))), p_cont))

print()
print('=== B. 三口径 p 的关键量汇总 ===')
for nn in (18, 16, 3, 2, 1):
    print('n=%2d  p_two=2*2^-%d=%.12g  log10(p)=%.6f' % (nn, nn, min(1.0, 2 * 2.0 ** -nn), math.log10(min(1.0, 2 * 2.0 ** -nn))))
print('族级/全单元 倍数 =', 0.25 / (2 * 2.0 ** -18), ' log10 差 =', math.log10(0.25) - math.log10(2 * 2.0 ** -18))

print()
print('=== C. 复核回件绑定行格式自检 ===')
# 从本会话实算指纹构造（全部 hashlib 实算，见 D 段）
pairs = [
    ('lead/score_decomp_20261109/SCORE_DECOMP.md', 'dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb', 42573),
    ('lead/score_decomp_20261109/_sd_report.md', '58e71cefc024d6874b353cde69d1b39b450f4a79ad08c35e9d235c01dbd725ff', 49202),
    ('lead/comparability_20261109/COMPARABILITY_AUDIT.md', 'c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1', 51927),
    ('lead/gate_pipeline_20261109/_gp_regression_out.json', 'd3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe', 38575),
    ('lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json', '68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358', 37461),
    ('lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md', '3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2', 49850),
    ('lead/PENDING_DECISIONS.md', '3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7', 52419),
    ('lead/GOAL_THREE_TARGETS_20261018.md', '2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede', 759518),
]
pat = re.compile(r'^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$')
ok = 0
for rel, sha, byt in pairs:
    b = open(BASE + rel, 'rb').read()
    h = hashlib.sha256(b).hexdigest()
    line = '被核对象 SHA256 = %s，字节数 = %d' % (h, len(b))
    m = pat.match(line)
    good = (m is not None) and (h == sha) and (len(b) == byt)
    ok += 1 if good else 0
    print(('OK  ' if good else 'FAIL') + ' ' + rel + '  MATCH=' + str(h == sha) + ' BYTES=' + str(len(b) == byt))
    print('     ' + line)
print('compliant =', ok, '/', len(pairs))

print()
print('=== D. 只读域零漂移：会话末再算 8 件指纹 ===')
for rel, sha, byt in pairs:
    b = open(BASE + rel, 'rb').read()
    print(('MATCH ' if (hashlib.sha256(b).hexdigest() == sha and len(b) == byt) else 'DRIFT ') + rel)
print()
print('=== E. 写域文件清单（唯一写域） ===')
wd = BASE + 'lead/pvalue_recalc_20261109/'
for f in sorted(os.listdir(wd)):
    p = wd + f
    print(f, os.path.getsize(p), 'B', 'sha256=' + hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16])
