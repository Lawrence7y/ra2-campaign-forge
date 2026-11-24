# -*- coding: utf-8 -*-
"""_n4g_probe.py — 独立复跑该域门禁（不采信编排方数字）。
覆盖：(a) 候选集 (b) 四条 FAIL 逐条 (c) 行数/hunk/绑定行双口径；(d) 词面精确位置；(e) R10/R12 谓词逐命中分类。"""
import pathlib, json, re, hashlib, sys, collections

ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
WD = ROOT / 'lead/n4_yi_final_20261108'
DOC_REL = 'lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md'
sys.path.insert(0, str(ROOT / 'lead/gate_fp7_20261108'))
import _g7_predicates as g7

o = collections.OrderedDict()
# (a) 候选集：payload 原文口径
cands = sorted([p for p in WD.glob('*.md') if p.name.startswith('CANDIDATE_RESIGN')]) if WD.is_dir() else []
o['a_candidates'] = [{'name': c.name, 'bytes': c.stat().st_size} for c in cands]
# 更宽口径：整库搜 CANDIDATE_RESIGN*
# 更宽口径：整库 CANDIDATE_RESIGN* 文件名由 shell find 单独跑（见 _n4g_find_out.txt），
# 此处 Python 只做门禁 wd 目录内枚举，避免本机 out/ 大树 rglob 卡死。
o['a_repo_wide'] = 'NOT_RUN_IN_PYTHON — 见实跑命令 find ... -name CANDIDATE_RESIGN* 与 _n4g_find_out.txt'
o['a_all_md_in_wd'] = sorted([p.name for p in WD.glob('*.md')])
assert len(cands) == 1
DOC = cands[0]
b = DOC.read_bytes()
t = b.decode('utf-8')
o['a_picked'] = DOC.name
o['a_fp'] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b),
             'lines_newline_plus1': b.count(b'\n') + 1, 'lines_splitlines': len(t.splitlines())}

# (b) 四条 FAIL 逐条，按 payload GATE_CODE 原文判据
BAN = ['可应用母本', '放行 N-5', '已应用', '已签 APPROVE_SCOPE']
REQ = ['逐行', '十四行', '九 hunk', '语义层 YES', '甲不再绑定', '不签 APPROVE_SCOPE', '未验']
B_STRICT = r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?'          # GATE_CODE 原文正则
B_TIGHT = r'被核对象 SHA256 = [0-9a-fA-F]{64}'                       # 铁律「固定格式」字面口径
B_LOOSE = r'被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}`?'  # 编排方宽松口径

o['b_fail1_missingElements'] = [k for k in REQ if k not in t]
o['b_fail1_literal_reason'] = {
    'literal_7chars': '不签 APPROVE_SCOPE',
    'present_raw': '不签 APPROVE_SCOPE' in t,
    'variants': {v: (v in t) for v in ['不签 `APPROVE_SCOPE`', '不签署 APPROVE_SCOPE', '不签  `APPROVE_SCOPE`']},
}
o['b_fail2_ban_hits'] = {x: [m.start() for m in re.finditer(re.escape(x), t)] for x in BAN if x in t}
o['b_fail3_ban_hits'] = o['b_fail2_ban_hits']
o['b_fail4_bindings'] = {
    'gate_regex': len(re.findall(B_STRICT, t)),
    'tight_literal': len(re.findall(B_TIGHT, t)),
    'loose': len(re.findall(B_LOOSE, t)),
}
o['b_naive_problems'] = (
    ['缺要素 ' + k for k in o['b_fail1_missingElements']]
    + ['含越权断言 ' + x for x in BAN if x in t]
    + (['缺 SHA256 绑定行'] if not re.findall(B_STRICT, t) else [])
)

# (c) 结构计数
o['c_struct'] = {
    'sections': {s: (s in t) for s in ['## 1', '## 2', '## 3', '## 4', '## 5', '## 6']},
    'rows': len(re.findall(r'^\|\s*(R\d+|\d+)\s*\|', t, re.M)),
    'hunks': len(re.findall(r'H0[1-9]', t)),
    'hunks_raw': re.findall(r'H0[1-9]', t),
}
o['c_binding_lines'] = [(i + 1, ln) for i, ln in enumerate(t.splitlines()) if 'SHA256' in ln and '被核对象' in ln]

# (d) 逐词面位置 + 原句（±90 字符）
occ = collections.OrderedDict()
for tok in BAN:
    for m in re.finditer(re.escape(tok), t):
        a, z = max(0, m.start() - 90), min(len(t), m.end() + 90)
        occ.setdefault(tok, []).append({'pos': m.start(), 'line': t[:m.start()].count('\n') + 1,
                                        'context': t[a:z]})
o['d_occurrences'] = occ
o['d_APPROVE_occurrences'] = [{'pos': m.start(), 'line': t[:m.start()].count('\n') + 1,
                               'context': t[max(0, m.start()-70):m.end()+70]}
                              for m in re.finditer('APPROVE_SCOPE', t)]

# (e) R10/R12 谓词逐命中
p10, w10, h10 = g7.r10_scan(t, BAN)
p12, h12 = g7.r12_scan(t, BAN)
o['e_r10'] = {'problems': p10, 'warnings': w10, 'hits': h10,
              'kind_counts': dict(collections.Counter(h['kind'] for h in h10))}
o['e_r12'] = {'problems': p12, 'hits': h12}
# 谓词对「不签 APPROVE_SCOPE」这类变体为何判不到：列出全部 REQ 与 BAN 的子串命中矩阵
o['e_req_presence_matrix'] = {k: (k in t) for k in REQ}

print(json.dumps(o, ensure_ascii=False, indent=2))
