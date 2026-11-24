# -*- coding: utf-8 -*-
"""_n4g_predicates.py — 用已实装的 R9/R10/R11/R12 修正谓词对同一交付件复判，判定四条 FAIL 在改进谓词下的存活情况。"""
import pathlib, json, sys, hashlib
ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
sys.path.insert(0, str(ROOT / 'lead/gate_fp7_20261108'))
import _g7_predicates as g7

t = (ROOT / 'lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md').read_text(encoding='utf-8')
REQ = ['逐行', '十四行', '九 hunk', '语义层 YES', '甲不再绑定', '不签 APPROVE_SCOPE', '未验']
BAN = ['可应用母本', '放行 N-5', '已应用', '已签 APPROVE_SCOPE']

# R9：包裹归一化要素匹配
p9, w9 = g7.r9_check(t, REQ)
r9_each = {k: g7.r9_element_present(t, k) for k in REQ}
norm = g7.r9_normalize(t)
r9_norm_snippet = norm[norm.find('不签') - 5:norm.find('不签') + 60] if '不签' in norm else 'NOT_FOUND'

# R10 / R12
p10, w10, h10 = g7.r10_scan(t, BAN)
p12, h12 = g7.r12_scan(t, BAN)

# R11：绑定行路径隔断容忍 + 引用锚回验
p11, w11, binds11 = g7.r11_scan(t, ROOT / 'lead/n4_yi_final_20261108', root=ROOT)

# 朴素对照（历史 GATE_CODE 的四步）
import re
naive = ([ '缺要素 ' + k for k in REQ if k not in t]
         + ['含越权断言 ' + x for x in BAN if x in t]
         + ([] if re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?', t) else ['缺 SHA256 绑定行']))

print(json.dumps({
    'r9': {'problems': p9, 'warnings': w9, 'each_element': r9_each,
           'normalized_snippet': repr(r9_norm_snippet)},
    'r10': {'problems': p10, 'warnings': w10, 'hits': h10},
    'r12': {'problems': p12, 'hits': h12},
    'r11': {'problems': p11, 'warnings': w11, 'bindings': binds11},
    'naive_gate_problems': naive,
    'improved_gate_problems': p9 + p10 + p12 + p11,
}, ensure_ascii=False, indent=2))
