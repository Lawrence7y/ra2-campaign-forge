# -*- coding: utf-8 -*-
"""_n4g_writer_refs41.py — 对判定员「指纹引用面 41 件」逐件排查并分类，
同时登记本轮复扫时新增件（后续会话继续写入导致计数增长）。"""
import sys
sys.dont_write_bytecode = True
import pathlib, json, hashlib
R = pathlib.Path('D:/Project/ra2-campaign-forge')
W = R / 'lead/n4_gate_verdict_20261109'
FULL = '1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b'
SHORT = '1950d3f3'
NAME = 'CANDIDATE_RESIGN_YES_V2.md'
SKIP = {'_dnv_sandbox36', '_dnw_sandbox', '_dnw_hardened', '__pycache__', '.git'}

base = json.loads((W / '_n4g_refs_out.json').read_text(encoding='utf-8'))
live = set(base['live_binding_candidates']['files'])
audit = set(base['audit_snapshot_refs']['files'])
full41 = base['full_hash_refs_lead_nonsandbox']['files']
short41 = base['short_hash_refs']['files']

rows = []
for rel in full41:
    p = R / rel
    txt = p.read_text(encoding='utf-8', errors='replace') if p.is_file() else ''
    role = '硬绑定候选(live)' if rel in live else ('审计/文字快照' if rel in audit else '未分类')
    # 本轮逐件复核：是否仍含完整 hash；给出首个命中行号
    ln = next((i + 1 for i, L in enumerate(txt.splitlines()) if FULL in L), None)
    rows.append({'n': len(rows) + 1, 'file': rel, 'role': role,
                 'hash_kind': 'full',
                 'hash_present_now': FULL in txt, 'first_hit_line': ln,
                 'in_verdict_write_domain': 'n4_gate_verdict_20261109' in rel})
for rel in short41:
    p = R / rel
    txt = p.read_text(encoding='utf-8', errors='replace') if p.is_file() else ''
    ln = next((i + 1 for i, L in enumerate(txt.splitlines()) if SHORT in L), None)
    rows.append({'n': len(rows) + 1, 'file': rel, 'role': '短哈希截断引用',
                 'hash_kind': 'short',
                 'hash_present_now': SHORT in txt, 'first_hit_line': ln,
                 'in_verdict_write_domain': False})

# 本轮复扫全量（排除沙箱）
cur_full, cur_short = [], []
for p in (R / 'lead').rglob('*'):
    if not p.is_file() or any(x in p.parts for x in SKIP):
        continue
    try:
        txt = p.read_text(encoding='utf-8', errors='replace')
    except Exception:
        continue
    rel = str(p.relative_to(R)).replace('\\', '/')
    if FULL in txt: cur_full.append(rel)
    elif SHORT in txt: cur_short.append(rel)
cur_full.sort(); cur_short.sort()
new_full = sorted(set(cur_full) - set(full41))
new_short = sorted(set(cur_short) - set(short41))

# mjs / 台账 / 沙箱
mjs_full = sorted(str(p.relative_to(R)).replace('\\', '/') for p in (R / '.zcode/workflow-runs').glob('*.mjs') if FULL in p.read_text(encoding='utf-8', errors='replace'))
mjs_name = sorted(str(p.relative_to(R)).replace('\\', '/') for p in (R / '.zcode/workflow-runs').glob('*.mjs') if NAME in p.read_text(encoding='utf-8', errors='replace'))
ledgers = {}
for rel in ['lead/PENDING_DECISIONS.md', 'lead/GOAL_THREE_TARGETS_20261018.md']:
    txt = (R / rel).read_text(encoding='utf-8', errors='replace')
    ledgers[rel] = {'full': FULL in txt, 'short': SHORT in txt, 'name': NAME in txt}
sandbox = []
for p in (R / 'lead').rglob('CANDIDATE_RESIGN*'):
    if p.is_file() and any(x in p.parts for x in ('_dnv_sandbox36', '_dnw_sandbox')):
        b = p.read_bytes()
        sandbox.append({'file': str(p.relative_to(R)).replace('\\', '/'),
                        'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)})

out = {
    'baseline_41': {'count': len(rows), 'live': len(live), 'audit': len(audit), 'short': len(short41),
                    'rows': rows,
                    'all_hash_references_still_present': all(r['hash_present_now'] for r in rows)},
    'rescan_now': {'full_count': len(cur_full), 'short_count': len(cur_short),
                   'new_full_vs_baseline': new_full, 'new_short_vs_baseline': new_short,
                   'non_verdict_domain_full': len([x for x in cur_full if 'n4_gate_verdict_20261109' not in x]),
                   'verdict_domain_full': len([x for x in cur_full if 'n4_gate_verdict_20261109' in x])},
    'mjs': {'full_hash': mjs_full, 'name_only_count': len(mjs_name), 'name_only': mjs_name},
    'ledgers': ledgers,
    'sandbox_copies': sandbox,
}
(W / '_n4g_writer_refs41.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({
    'baseline_41_count': len(rows), 'all_41_hash_refs_still_present': out['baseline_41']['all_hash_references_still_present'],
    'live': len(live), 'audit': len(audit), 'short': len(short41),
    'rescan_full': len(cur_full), 'rescan_short': len(cur_short),
    'new_full': new_full, 'new_short': new_short,
    'mjs_full': len(mjs_full), 'mjs_name': len(mjs_name),
    'ledgers_clean': all(not any(v.values()) for v in ledgers.values()),
    'sandbox': len(sandbox),
}, ensure_ascii=False, indent=2))
