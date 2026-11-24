# -*- coding: utf-8 -*-
"""_n4g_r10gap.py — 实测 R10 谓词漏掉哪一类语境：清单/词表声明、反引号代码跨度、无「」且否定词出窗。"""
import pathlib, json, sys
ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
sys.path.insert(0, str(ROOT / 'lead/gate_fp7_20261108'))
import _g7_predicates as g7
BAN = ['可应用母本', '放行 N-5', '已应用', '已签 APPROVE_SCOPE']

SAMPLES = {
    'S1_原件排除清单（「」+「无/不」）': '3. **无越权断言**：审阅/复核回件不出现「可应用母本 / 放行 N-5 / APPROVE_SCOPE 已签」类断言；',
    'S2_清单无「」且否定词在 24 字窗内': '本件禁用词：不得出现 可应用母本。',
    'S3_清单无「」否定词出 24 字窗': '本件附条件第 3 条要求：审阅回件与复核回件均须逐字排查下列越权表述，凡出现任一表述则本 YES 立即作废：可应用母本 / 放行 N-5。',
    'S4_反引号代码跨度内的词表声明': '门禁 BAN 清单为 `可应用母本`、`放行 N-5`、`已签 APPROVE_SCOPE`，均不得出现。',
    'S5_无标记的项目符号清单': '- 越权词表：可应用母本；放行 N-5；APPROVE_SCOPE 已签。',
    'S6_真断言对照': '本 YES 已获批准，可应用母本，放行 N-5。',
}
out = {}
for name, s in SAMPLES.items():
    p, w, h = g7.r10_scan(s, BAN)
    p12, h12 = g7.r12_scan(s, BAN)
    out[name] = {'text': s, 'r10_problems': p, 'r10_warnings': w,
                 'r10_hits': h, 'r12_problems': p12}
print(json.dumps(out, ensure_ascii=False, indent=2))
