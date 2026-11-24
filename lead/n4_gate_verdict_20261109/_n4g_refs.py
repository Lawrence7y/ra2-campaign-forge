# -*- coding: utf-8 -*-
"""_n4g_refs.py — 逐文件分类「谁引用了重签件指纹」，区分硬绑定 / 审计快照 / 文件名引用 / 沙箱副本。"""
import pathlib, json, hashlib
R = pathlib.Path('D:/Project/ra2-campaign-forge')
FULL = '1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b'
NAME = 'CANDIDATE_RESIGN_YES_V2.md'
SKIP = {'_dnv_sandbox36', '_dnw_sandbox', '_dnw_hardened', '__pycache__', '.git'}

def scan(base, pat):
    hits = []
    for p in base.rglob('*'):
        if not p.is_file() or any(x in p.parts for x in SKIP):
            continue
        try:
            txt = p.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        if pat in txt:
            hits.append(str(p.relative_to(R)).replace('\\', '/'))
    return sorted(hits)

full_hits = scan(R / 'lead', FULL)
mjs = [str(p.relative_to(R)).replace('\\', '/') for p in (R / '.zcode/workflow-runs').glob('*.mjs')
       if FULL in p.read_text(encoding='utf-8', errors='replace')]
mjs_name = [str(p.relative_to(R)).replace('\\', '/') for p in (R / '.zcode/workflow-runs').glob('*.mjs')
            if NAME in p.read_text(encoding='utf-8', errors='replace')]

# 活绑定判据：文件为 .py/.json 且把该 hash 作为「期望值」参与比对（含 MATCH/sha256 期望键）
LIVE_EXT = {'.py', '.json'}
live, audit = [], []
for rel in full_hits:
    p = R / rel
    txt = p.read_text(encoding='utf-8', errors='replace')
    is_live = p.suffix in LIVE_EXT and any(k in txt for k in ['MATCH', 'expected', 'expect', 'fp', 'sha256', 'sha_head', 'docSha256'])
    (live if is_live else audit).append(rel)

# 短哈希引用（12/16 位截断）
short_hits = []
for p in (R / 'lead').rglob('*'):
    if not p.is_file() or any(x in p.parts for x in SKIP):
        continue
    try:
        txt = p.read_text(encoding='utf-8', errors='replace')
    except Exception:
        continue
    if '1950d3f3' in txt and FULL not in txt:
        short_hits.append(str(p.relative_to(R)).replace('\\', '/'))

print(json.dumps({
    'full_hash_refs_lead_nonsandbox': {'count': len(full_hits), 'files': full_hits},
    'live_binding_candidates': {'count': len(live), 'files': live,
                                'note': '扩展名 .py/.json 且含比对语义键；是否真在运行时读取需逐件看（未逐件验）'},
    'audit_snapshot_refs': {'count': len(audit), 'files': audit},
    'short_hash_refs': {'count': len(short_hits), 'files': sorted(short_hits)},
    'mjs_refs_full_hash': {'count': len(mjs), 'files': mjs},
    'mjs_refs_filename_only': {'count': len(mjs_name), 'files': sorted(mjs_name)},
    'sandbox_copies': [str(p.relative_to(R)).replace('\\', '/') for p in (R / 'lead').rglob('CANDIDATE_RESIGN*')
                       if p.is_file() and any(x in p.parts for x in ('_dnv_sandbox36', '_dnw_sandbox'))],
}, ensure_ascii=False, indent=2))
