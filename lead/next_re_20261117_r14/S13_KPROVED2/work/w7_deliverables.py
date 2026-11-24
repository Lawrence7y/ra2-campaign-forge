"""Generate final deliverables for S13-KPROVED2.
- coverage_delta.tsv: 0 data rows (header only) -- honest 0-row outcome.
- EVIDENCE/candidate_pool.tsv: 46 candidates + per-ring flags.
- EVIDENCE/core_numbers.json: the four required core numbers.
Card S13-KPROVED2.
"""
import json, csv, os

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_KPROVED2"
pool = json.load(open(BASE + r'\work\pool.json', encoding='utf-8'))
scan = json.load(open(BASE + r'\work\ring4_scan.json', encoding='utf-8'))
base = json.load(open(BASE + r'\EVIDENCE\baselines.json', encoding='utf-8'))
dword = json.load(open(BASE + r'\work\dword_va_scan.json', encoding='utf-8'))
equiv = json.load(open(BASE + r'\work\ring4_equiv.json', encoding='utf-8'))

cands = pool['candidates']

# ---- 1. coverage_delta.tsv : HEADER ONLY (0 rows) ----
# delta contract format (8 cols): entry subsystem name one_line_semantics grade evidence_path name_kind 缺环说明
hdr = "entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\t缺环说明\n"
with open(BASE + r'\coverage_delta.tsv','w',encoding='utf-8',newline='') as f:
    f.write(hdr)
print('wrote coverage_delta.tsv (0 data rows)')

# ---- 2. EVIDENCE/candidate_pool.tsv ----
cols = ['entry','subsystem','name','grade','has2_rtti','has2_yrpp','has4_strict','has4_loose',
        'n_direct_all','direct_hit','dword_vslot','E9_tailjmp','verdict','reason']
with open(BASE + r'\EVIDENCE\candidate_pool.tsv','w',encoding='utf-8',newline='') as f:
    f.write('\t'.join(cols)+'\n')
    for r in cands:
        e = r['entry']
        dh = '1' if e.lower() in scan['channelA']['targets_hit'] else '0'
        vh = '1' if dword['per_entry'].get(e,{}).get('vtable_slot_hits',0)>0 else '0'
        ej = '1' if any(int(k,16)==int(e,16) for k in equiv['e9']) else '0'
        f.write('\t'.join([e, r['subsystem'], r['name'], r['grade'], r['has2_rtti'], r['has2_yrpp'],
                           r['has4_strict'], r['has4_loose'], r['n_direct_all'], dh, vh, ej,
                           'FAIL', '缺④:无E8 direct call且无静态global活vtable派发; vtable槽引用与②同源(D-39)'
                           ])+'\n')
print('wrote EVIDENCE/candidate_pool.tsv (46 rows)')

# ---- 3. EVIDENCE/core_numbers.json ----
s126 = base['s13_static_pool_126']['tiers']
c46 = base['candidate_pool_47']['tiers']
core = {
  'card': 'S13-KPROVED2',
  'candidate_rows': pool['candidate_pool'],
  'candidate_pool_derivation': {
     's13_static_pool': pool['static_pool'],
     'excluded_M26_whitelist': ['0040F870','0054E890','0054EA70'],
     'excluded_K8_D39_dtors': len(pool['excluded_k8_dtors']),
     'excluded_K9_already_merged': 11,
     'excluded_container_slot1_6_per_8_4': len(pool['excluded_container_slot16']),
     'note': '3 M26 + 11 K9 rows already [已证] hence not in 126 static pool; K8 18 + container 62 excluded from 126',
  },
  'four_ring_complete_rows': 0,
  'delta_rows': 0,
  's13_proved_calibers': {
     'caliber_240': {'proved': pool['caliber240']['proved'],'denominator':240,
                     'pct': round(pool['caliber240']['pct'],4)},
     'caliber_148': {'proved': pool['caliber148']['proved'],'denominator':148,
                     'pct': round(pool['caliber148']['pct'],4),
                     'note':'exclude 92 container-template rows (D-37); 89-14 container-proved=75'},
  },
  'third_b_base_rate': {
     'seed': 20261119, 'trials': 2000, 'sample': 8,
     'S13_static_pool_126': {
        'strict': {k:s126['strict'][k] for k in ('N','K','p','E8','mc_mean')},
        'loose':  {k:s126['loose'][k]  for k in ('N','K','p','E8','mc_mean')},
        'operationalization': 'strict=jumptable OR falsifiable-errcode OR memshape(>=2vt or>=10 fields) OR full-io-loop(write+cmp+advance); loose=strict OR D42细则#1 guard-chain(>=3 distinct jcc targets)',
     },
     'candidate_pool_46': {
        'strict': {k:c46['strict'][k] for k in ('N','K','p','E8','mc_mean')},
        'loose':  {k:c46['loose'][k]  for k in ('N','K','p','E8','mc_mean')},
     },
     'identity_note': 'K=N*p and E[8]=8*p are identities, not a check (M3; §8.7 判据3)',
  },
  'ring4_verification': {
     'channelA_capstone': {'insns': scan['channelA']['n_insns'], 'candidate_targets_hit': len(scan['channelA']['targets_hit']),
                           'distinct_e8_targets_total': scan['distinct_e8_targets_total']},
     'channelB_raw_e8': {'raw_e8_bytes': scan['channelB']['n_raw_e8'], 'boundaries': scan['channelB']['n_boundaries'],
                         'candidate_targets_hit': len(scan['channelB']['targets_hit'])},
     'A_equals_B': scan['A_equals_B'],
     'livevt_loose_candidates': len(scan['survey_loose4_candidates']),
     'E9_tailjmp_equiv': {k: len(v) for k,v in equiv.items()},
     'E9_note': '0x46B990/0x46B9A0 are sub [esp+4],4; jmp thunks (candidate->candidate aliases), not E8 direct call and not vtable dispatch; D-40 ④ requires E8 or live-vt-slot.',
  },
}
json.dump(core, open(BASE + r'\EVIDENCE\core_numbers.json','w',encoding='utf-8'), indent=2, ensure_ascii=False)
print('wrote EVIDENCE/core_numbers.json')
print(json.dumps({k:core[k] for k in ('candidate_rows','four_ring_complete_rows','delta_rows')},ensure_ascii=False))
