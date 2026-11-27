# -*- coding: utf-8 -*-
"""R154 · 复算外部 triage 产物 _ext/f_partial_triage/TRIAGE.tsv 的机械主张。
只判「机械可判」的三件事：
  (1) 覆盖集：32 条是否恰等于 FACT_INDEX V542 里 34 条部分失联项减去 {F23,F35}；
  (2) lost_primary 的每个路径是否都在主会话独立算出的 16 条失联路径集内；
  (3) alive_paths 的每个路径是否都在盘（含反控：自造路径必须 NOT 在盘）。
档位（仍可核验/需重建/不可核验）是判断，不做机械判定，只做计数闭合。
"""
import csv, io, os, re, sys, json

ROOT = '/home/t628/projects/ra2-campaign-forge'
P = ROOT + '/lead/next_re_20261117_r14/'
FI = P + 'R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'
TR = ROOT + '/_ext/f_partial_triage/TRIAGE.tsv'

def resolve(p):
    p = p.strip().replace('\\', '/')
    if not p: return None
    if p.startswith('lead/'):
        for base in (ROOT + '/',):
            if os.path.isfile(base + p): return base + p
    for base in (ROOT + '/', ROOT + '/lead/', P):
        if os.path.isfile(base + p): return base + p
    return None

def split_entries(cell):
    return [x for x in re.split(r';', cell) if x.strip()]

def ev_path(entry):
    return re.sub(r'\((?:[^()]|\([^()]*\))*\)\s*$', '', entry.strip()).strip()

# ---------- 主会话独立算（不复用 triage 的中间量） ----------
rows = list(csv.reader(io.open(FI, encoding='utf-8'), delimiter='\t'))
hdr, data = rows[0], rows[1:]
assert hdr == ['fact_id','statement','grade','evidence_paths','limitations'], hdr
per, miss_paths, all_paths, n_entries = {}, set(), set(), 0
for r in data:
    fid = r[0]; miss, live = [], []
    for e in split_entries(r[3]):
        pp = ev_path(e); n_entries += 1; all_paths.add(pp)
        (live if resolve(pp) else miss).append(pp)
    per[fid] = {'n': len(split_entries(r[3])), 'live': live, 'miss': miss}
    miss_paths.update(miss)
partial = sorted([f for f, d in per.items() if d['miss']], key=lambda x: int(x[1:]))
zero_live = sorted([f for f, d in per.items() if d['miss'] and not d['live']], key=lambda x: int(x[1:]))

FAILS, NOTES = [], []
def chk(cond, msg):
    (NOTES if cond else FAILS).append(('PASS ' if cond else 'FAIL ') + msg)

chk(len(data) == 54, 'FACT_INDEX data rows = %d (expect 54)' % len(data))
chk(n_entries == 178, 'evidence entries = %d (expect 178)' % n_entries)
chk(len(miss_paths) == 16, 'distinct lost paths = %d (expect 16)' % len(miss_paths))
chk(len(partial) == 34, 'fact rows with >=1 lost entry = %d (expect 34)' % len(partial))
chk(zero_live == ['F23'], 'zero-live rows = %s (expect exactly [F23])' % zero_live)

# ---------- triage 侧 ----------
trows = [l.rstrip('\n').split('\t') for l in io.open(TR, encoding='utf-8')]
thdr, tbody = trows[0], [r for r in trows[1:] if r and any(x.strip() for x in r)]
chk(thdr == ['fid','lost_primary','lost_side','alive_paths','verdict','basis'], 'TRIAGE header = %r' % (thdr,))
chk(len(tbody) == 32, 'TRIAGE rows = %d (expect 32)' % len(tbody))

triage_fids = [r[0] for r in tbody]
expect32 = [f for f in partial if f not in ('F23', 'F35')]
chk(sorted(triage_fids, key=lambda x: int(x[1:])) == sorted(expect32, key=lambda x: int(x[1:])),
    'TRIAGE fid set == (34 partial) - {F23,F35} ; got %d, diff %r'
    % (len(triage_fids), sorted(set(triage_fids) ^ set(expect32))))

# (2) lost_primary 全在 16 条失联集内
bad_lost, n_lost = [], 0
for r in tbody:
    for e in split_entries(r[1]):
        n_lost += 1
        pp = ev_path(e)
        # S-387: TRIAGE.tsv 用正斜杠、FACT_INDEX 用反斜杠；比较必须归一，否则 36/36 假 FAIL
        if pp.replace('\\', '/') not in set(x.replace('\\', '/') for x in miss_paths):
            bad_lost.append((r[0], pp))
chk(not bad_lost, 'every TRIAGE lost_primary path is in the 16-path lost set ; %d entries, offenders=%r'
    % (n_lost, bad_lost[:5]))

# (3) alive_paths 全在盘
bad_alive, n_alive = [], 0
for r in tbody:
    for e in split_entries(r[3]):
        n_alive += 1
        pp = ev_path(e)
        if not resolve(pp): bad_alive.append((r[0], pp))
chk(not bad_alive, 'every TRIAGE alive_paths path resolves on disk ; %d entries, offenders=%r'
    % (n_alive, bad_alive[:5]))

# 档位计数闭合
import collections
tier = collections.Counter(r[4].strip() for r in tbody)
chk(tier == {'需重建': 18, '不可核验': 9, '仍可核验': 5},
    'tier census = %r (expect 需重建18 / 不可核验9 / 仍可核验5)' % dict(tier))
chk(sum(tier.values()) == 32, 'tier arithmetic closes to 32 (%d)' % sum(tier.values()))

# 档位与机械事实的交叉：仍可核验 的项必须有 >=1 活路径（机械必要条件）
viol = []
for r in tbody:
    if r[4].strip() == '仍可核验' and per[r[0]]['live'] == []:
        viol.append(r[0])
chk(not viol, 'every 仍可核验 row has >=1 live path mechanically ; offenders=%r' % viol)

# ---------- 反控 ----------
ctrl_path = 'lead/next_re_20261117_r14/ZZZ_R154_NOT_EXIST_QQQ.md'
chk(resolve(ctrl_path) is None, 'NEGCTRL self-made path resolves to None (a checker that finds it is broken)')
chk(resolve('lead/next_re_20261117_r14/R14_COMMON.md') is not None, 'POSCTRL R14_COMMON.md resolves (resolver has power)')
# 反控2：把 resolution 强制指向错根，必须 0 命中（证明 lost 集不是「全 miss」的恒真式）
none_hit = sum(1 for p in all_paths if resolve('no_such_root/' + p))
chk(none_hit == 0, 'NEGCTRL joined with bogus root -> %d hits (expect 0)' % none_hit)
chk(len(miss_paths) < len(all_paths), 'lost set is a proper subset: %d < %d (so "missing" is not vacuous)'
    % (len(miss_paths), len(all_paths)))

out = {
    'fact_rows': len(data), 'evidence_entries': n_entries,
    'distinct_paths': len(all_paths), 'lost_paths': len(miss_paths),
    'partial_rows': len(partial), 'zero_live': zero_live,
    'triage_rows': len(tbody), 'triage_lost_entries': n_lost, 'triage_alive_entries': n_alive,
    'tier': dict(tier),
    'pass': len(NOTES), 'fail': len(FAILS),
    'fails': FAILS, 'notes': NOTES,
}
print(json.dumps(out, ensure_ascii=False, indent=1))
io.open(ROOT + '/_r154/r154b_triage_recheck.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
sys.exit(1 if FAILS else 0)
