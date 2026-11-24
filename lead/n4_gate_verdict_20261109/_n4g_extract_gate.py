# -*- coding: utf-8 -*-
"""_n4g_extract_gate.py — 从历史 payload 逐字抽取 GATE_CODE，替换 JS 拼接占位为 live hashlib 实算值，
落盘为可复跑的 python 源码（本任务写域）。只读历史 mjs，不改任何受保护件。"""
import pathlib, json, hashlib, re, sys

ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
OUT = ROOT / 'lead/n4_gate_verdict_20261109'
HIST = ROOT / '.zcode/workflow-runs/dwfrun-af6f3c87-7d72-4587-8e0d-07c4b878337c.mjs'

s = HIST.read_text(encoding='utf-8')
i = s.find('export const payload = ') + len('export const payload = ')
obj, _ = json.JSONDecoder().raw_decode(s[i:])
lo = obj['lowered']

k = lo.find('const GATE_CODE = [')
j = lo.find('].join', k)
assert k >= 0 and j > k, 'GATE_CODE block not found'
arr_src = lo[k + len('const GATE_CODE = '):j + 1]

# FP_CODE 的 12 件路径（历史 payload 原文），live 实算，供 JS 拼接占位替换
T = ['out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py',
     'lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py',
     'lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff',
     'lead/b2b_design_20261106/B2B_DESIGN.md',
     'lead/b2b_design_20261106/STATE_MATRIX.json',
     'lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md',
     'lead/n4_yi_final_20261108/B_EXECUTION_SPEC_V2_YI.md',
     'lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md',
     'lead/direction_ruling_20261108/RULING_DIRECTION.md',
     'lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md',
     'lead/PENDING_DECISIONS.md',
     'lead/GOAL_THREE_TARGETS_20261018.md']
fps = {}
for t in T:
    p = ROOT / t
    fps[t] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'

vals = {
    'motherSha': fps['out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py'],
    'candSha': fps['lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py'],
    'v2Sha': fps['lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md'],
    'matSha': fps['lead/b2b_design_20261106/STATE_MATRIX.json'],
    'headSha': fps['lead/PENDING_DECISIONS.md'],
    'goalSha': fps['lead/GOAL_THREE_TARGETS_20261018.md'],
}

# 把 JS 字符串拼接 `" + varName + "` 替换为变量值（无引号）
def sub_concat(m):
    name = m.group(1)
    assert name in vals, 'unknown concat var: ' + name
    return vals[name]

arr_src2, n = re.subn(r'" \+ (\w+) \+ "', sub_concat, arr_src)
# JS 数组末元素后有尾逗号（合法 JS、非法 JSON）：去掉紧邻 ] 前的逗号
arr_src2, n_comma = re.subn(r',(\s*)\]\s*$', r'\1]', arr_src2)
lines = json.loads(arr_src2)
gate_py = '\n'.join(lines)
(OUT / '_n4g_gate_verbatim.py').write_text(gate_py, encoding='utf-8')

print(json.dumps({
    'payload': str(HIST.relative_to(ROOT)).replace('\\', '/'),
    'gateBlockRange': [k, j + 1],
    'concatSubstitutions': n,
    'gatePyLines': len(lines),
    'gatePySha256': hashlib.sha256(gate_py.encode('utf-8')).hexdigest(),
    'liveFingerprints': {kk: vv for kk, vv in vals.items()},
    'bindingRegexLine': [ln for ln in lines if 'B=re.findall' in ln],
}, ensure_ascii=False, indent=2))
