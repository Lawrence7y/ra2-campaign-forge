# -*- coding: utf-8 -*-
"""_n4g_writer_verify.py — N4 判定件撰写员本轮独立实跑验证。
覆盖：十件指纹（母本逐位）、逐字历史门禁内联复跑、候选集、四条 FAIL
原句/语境/计数、R9/R10/R11/R12 改进谓词复判、改后哈希（四种口径）、引用面。
零真机、零采样代码；只读受保护件；唯一写入 = 本文件与 _n4g_writer_out.json。
"""
import sys
sys.dont_write_bytecode = True
import pathlib, json, hashlib, re

ROOT = pathlib.Path('D:/Project/ra2-campaign-forge')
WD = ROOT / 'lead/n4_gate_verdict_20261109'
DOC_REL = 'lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md'
FULL = '1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b'
HEX = 'ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e'
NAME = 'CANDIDATE_RESIGN_YES_V2.md'

# 编排方基线（当前 ask【编排方指纹】十件）；lines 为「换行数 + 1」口径
BASE = {
 'lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md': ('1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b', 23129, 174),
 'lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md': ('c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801', 28897, 211),
 'lead/n4_yi_final_20261108/B_EXECUTION_SPEC_V2_YI.md': ('27f31bf560e9a71c5e9603d81a860233e7fc7b19e504eed4a15ea24a2077b067', 35486, 238),
 'lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md': ('ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e', 11948, 85),
 'out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py': ('517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636', 399508, 7292),
 'lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py': ('ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2', 412759, 7534),
 'lead/b2b_design_20261106/STATE_MATRIX.json': ('1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016', 3558, 17),
 'lead/direction_ruling_20261108/RULING_DIRECTION.md': ('0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653', 16514, 97),
 'lead/PENDING_DECISIONS.md': ('3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7', 52419, 382),
 'lead/GOAL_THREE_TARGETS_20261018.md': ('2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede', 759518, 9758),
}

o = {}

# ---- 1. 十件指纹：sha256 / bytes 逐位核对 ----
fps = {}
for rel, (sha, by, ln) in BASE.items():
    b = (ROOT / rel).read_bytes()
    s = hashlib.sha256(b).hexdigest()
    fps[rel] = {
        'sha256': s, 'bytes': len(b),
        'newline_plus1': b.count(b'\n') + 1,
        'splitlines': len(b.decode('utf-8').splitlines()),
        'sha_match': s == sha, 'bytes_match': len(b) == by,
        'lines_match_nlplus1': (b.count(b'\n') + 1) == ln,
    }
o['ten_fingerprints'] = fps
o['ten_all_sha_bytes_match'] = all(v['sha_match'] and v['bytes_match'] for v in fps.values())
o['mother_sha_full'] = fps['out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py']['sha256']

# ---- 2. 逐字历史 GATE_CODE 的四个判据（本脚本内联实现，与 _n4g_gate_verbatim.py:10-21 同源） ----
t = (ROOT / DOC_REL).read_text(encoding='utf-8')
REQ = ['逐行', '十四行', '九 hunk', '语义层 YES', '甲不再绑定', '不签 APPROVE_SCOPE', '未验']
BAN = ['可应用母本', '放行 N-5', '已应用', '已签 APPROVE_SCOPE']
P = []
for s6 in ['## 1', '## 2', '## 3', '## 4', '## 5', '## 6']:
    if s6 not in t:
        P.append('缺小节 ' + s6)
missing = []
for k in REQ:
    if k not in t:
        P.append('缺要素 ' + k)
        missing.append(k)
overreach = []
for bad in BAN:
    if bad in t:
        P.append('含越权断言 ' + bad)
        overreach.append(bad)
rows = len(re.findall(r'^\|\s*(R\d+|\d+)\s*\|', t, re.M))
hunks = len(re.findall(r'H0[1-9]', t))
B = re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?', t)
if not B:
    P.append('缺 SHA256 绑定行')
o['inline_naive_gate'] = {'problems': P, 'missingElements': missing,
                          'overreachHits': overreach, 'rows': rows, 'hunks': hunks, 'bindings': len(B)}

# ---- 3. 候选集（门禁 wd 内） ----
wd = ROOT / 'lead/n4_yi_final_20261108'
all_md = sorted(p.name for p in wd.glob('*.md'))
cands = sorted(p.name for p in wd.glob('*.md') if p.name.startswith('CANDIDATE_RESIGN'))
o['candidate_set'] = {'all_md_in_wd': all_md, 'cands_startswith': cands,
                      'picked_by_max_size': max((p for p in wd.glob('*.md') if p.name.startswith('CANDIDATE_RESIGN')), key=lambda p: p.stat().st_size).name}

# ---- 4. 四条 FAIL 逐条：原句（文件:行）/ 计数 / 语境 ----
lines = t.splitlines()
def line(n):
    return lines[n - 1]
o['fail1'] = {
    'literal_7chars': '不签 APPROVE_SCOPE',
    'present_raw': '不签 APPROVE_SCOPE' in t,
    'with_backticks_count': t.count('不签 `APPROVE_SCOPE`'),
    'line15': line(15), 'line150': line(150),
}
o['fail2_fail3'] = {
    "count_可应用母本": t.count('可应用母本'),
    "count_不应用母本": t.count('不应用母本'),
    "可应用母本_in_不应用母本": '可应用母本' in '不应用母本',
    "count_放行N5": t.count('放行 N-5'),
    "count_不放行N5": t.count('不放行 N-5'),
    'line17': line(17), 'line130': line(130), 'line148': line(148), 'line150': line(150), 'line155': line(155),
    'ban_token_line_map': {tok: [i + 1 for i, L in enumerate(lines) if tok in L]
                           for tok in ['可应用母本', '放行 N-5']},
}
ln122 = line(122)
infix = '（审阅回件 `lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md`）'
STRICT = r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?'
TIGHT = r'被核对象 SHA256 = [0-9a-fA-F]{64}'
LOOSE = r'被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}`?'
o['fail4'] = {
    'line122': ln122,
    'infix': infix, 'infix_len': len(infix),
    'space_between_被核对象_and_SHA256': '被核对象 SHA256' in ln122,
    'hex_backticks': ('`' + HEX + '`') in ln122,
    'gate_strict_count': len(re.findall(STRICT, t)),
    'iron_tight_count': len(re.findall(TIGHT, t)),
    'loose_count': len(re.findall(LOOSE, t)),
    'binding_file_sha_recomputed': hashlib.sha256((ROOT / 'lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md').read_bytes()).hexdigest(),
    'binding_file_bytes': (ROOT / 'lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md').stat().st_size,
}

# ---- 5. 改进谓词 R9/R10/R11/R12 独立调用（设 dont_write_bytecode，不写 __pycache__） ----
sys.path.insert(0, str(ROOT / 'lead/gate_fp7_20261108'))
import _g7_predicates as g7
p9, w9 = g7.r9_check(t, REQ)
r9_each = {k: list(g7.r9_element_present(t, k)) for k in REQ}
p10, w10, h10 = g7.r10_scan(t, BAN)
p12, h12 = g7.r12_scan(t, BAN)
p11, w11, binds11 = g7.r11_scan(t, ROOT / 'lead/n4_yi_final_20261108', root=ROOT)
o['improved_predicates'] = {
    'r9_problems': p9, 'r9_warnings': w9, 'r9_each': r9_each,
    'r10_problems': p10, 'r10_warnings': w10,
    'r10_kinds': {k: sum(1 for h in h10 if h['kind'] == k) for k in ['negation', 'quote_mention', 'assertion', 'double_neg']},
    'r12_problems': p12,
    'r11_problems': p11, 'r11_bindings': binds11,
    'naive_gate_problems': P,
    'improved_gate_problems': p9 + p10 + p12 + p11,
}

# ---- 6. 改后 SHA256（四种落地口径，均仅内存计算，不落盘到被核件） ----
CANON = '被核对象 SHA256 = ' + HEX + '，字节数 = 11948'
def sha_of(newt):
    b = newt.encode('utf-8')
    return hashlib.sha256(b).hexdigest(), len(b), len(re.findall(STRICT, newt)), len(re.findall(TIGHT, newt))
kb = t.splitlines(keepends=True)
variants = {
    'original': t,
    'replace_line122': t.replace(ln122, CANON, 1),
    'insert_after_line122': ''.join(kb[:122] + [CANON + '\n'] + kb[122:]),
    'append_at_eof': t + '\n' + CANON + '\n',
    # 复核员另一种「文件尾追加」口径：尾空元素前插入
    'append_before_trailing_blank': ''.join(kb[:-1] + [CANON + '\n'] + kb[-1:]),
    # A+B 同时改（上游标未验，本轮实算）
    'A_plus_B': t.replace('不签 `APPROVE_SCOPE`', '不签 APPROVE_SCOPE').replace(ln122, CANON, 1),
}
o['post_edit_hashes'] = {}
for k, v in variants.items():
    sh, n, gs, it = sha_of(v)
    o['post_edit_hashes'][k] = {'sha256': sh, 'bytes': n, 'gate_strict': gs, 'iron_tight': it}

# ---- 7. 引用面：逐个排查（排除沙箱；标注本轮写域新增件） ----
SKIP_DIRS = {'_dnv_sandbox36', '_dnw_sandbox', '_dnw_hardened', '__pycache__', '.git'}
full_hits, short_hits = [], []
for p in (ROOT / 'lead').rglob('*'):
    if not p.is_file() or any(x in p.parts for x in SKIP_DIRS):
        continue
    try:
        txt = p.read_text(encoding='utf-8', errors='replace')
    except Exception:
        continue
    rel = str(p.relative_to(ROOT)).replace('\\', '/')
    if FULL in txt:
        full_hits.append(rel)
    elif '1950d3f3' in txt:
        short_hits.append(rel)
full_hits.sort(); short_hits.sort()
mjs_full, mjs_name = [], []
for p in (ROOT / '.zcode/workflow-runs').glob('*.mjs'):
    txt = p.read_text(encoding='utf-8', errors='replace')
    rel = str(p.relative_to(ROOT)).replace('\\', '/')
    if FULL in txt: mjs_full.append(rel)
    if NAME in txt: mjs_name.append(rel)
ledgers = {}
for rel in ['lead/PENDING_DECISIONS.md', 'lead/GOAL_THREE_TARGETS_20261018.md']:
    txt = (ROOT / rel).read_text(encoding='utf-8', errors='replace')
    ledgers[rel] = {'full_hash': FULL in txt, 'short_hash': '1950d3f3' in txt, 'name': NAME in txt}
sandbox = sorted(str(p.relative_to(ROOT)).replace('\\', '/')
                 for p in (ROOT / 'lead').rglob('CANDIDATE_RESIGN*')
                 if p.is_file() and any(x in p.parts for x in ('_dnv_sandbox36', '_dnw_sandbox')))
o['refs'] = {
    'full_hash_refs_lead_nonsandbox': {'count': len(full_hits), 'files': full_hits},
    'short_hash_refs': {'count': len(short_hits), 'files': short_hits},
    'mjs_full_hash': {'count': len(mjs_full), 'files': sorted(mjs_full)},
    'mjs_name_only': {'count': len(mjs_name), 'files': sorted(mjs_name)},
    'ledgers': ledgers,
    'sandbox_copies': sandbox,
    'note': '本轮扫描时写域已含本脚本与本输出件及 N4_GATE_VERDICT.md（含完整 hash），故计数高于判定员 41 件基线；逐件见 files 列表，新增件单独可辨。',
}

(WD / '_n4g_writer_out.json').write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({
    'ten_all_sha_bytes_match': o['ten_all_sha_bytes_match'],
    'mother_sha_full': o['mother_sha_full'],
    'inline_naive_gate': o['inline_naive_gate'],
    'candidate_set': o['candidate_set'],
    'fail2_fail3_counts': {k: v for k, v in o['fail2_fail3'].items() if k.startswith('count') or k.endswith('_母本')},
    'fail4': {k: o['fail4'][k] for k in ['infix_len', 'space_between_被核对象_and_SHA256', 'hex_backticks', 'gate_strict_count', 'iron_tight_count', 'loose_count']},
    'improved_gate_problems': o['improved_predicates']['improved_gate_problems'],
    'r10_kinds': o['improved_predicates']['r10_kinds'],
    'post_edit_hashes': {k: v['sha256'] + '/' + str(v['bytes']) for k, v in o['post_edit_hashes'].items()},
    'refs_counts': {'full': len(full_hits), 'short': len(short_hits), 'mjs_full': len(mjs_full), 'mjs_name': len(mjs_name), 'sandbox': len(sandbox)},
}, ensure_ascii=False, indent=2))
