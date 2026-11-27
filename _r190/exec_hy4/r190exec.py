#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 executor (hy4): one-shot recomputation of same-name vtable group layout."""
import sys, os, json, struct, hashlib, math, random, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P

TARGET = {'col': 1214, 'vt': 1214, 'slots': 14044,
          'tight': 979, 'zero': 186, 'data': 4, 'scatter': 45}

def sec(va):
    return P.sec_of(va)

def is_col(c):
    if c is None:
        return False
    d = [P.dw(c + 4*i) for i in range(5)]
    if any(x is None for x in d):
        return False
    if d[0] not in (0, 1) or d[2] != 0:
        return False
    if sec(d[3]) != '.data' or sec(d[4]) != '.rdata':
        return False
    s = P.cstr(d[3] + 8, 300)
    if not s or not s.startswith(b'.?A') or not s.endswith(b'@@'):
        return False
    return True

col_cache = {}
def col_info(c):
    if c not in col_cache:
        if not is_col(c):
            col_cache[c] = None
        else:
            d = [P.dw(c + 4*i) for i in range(5)]
            nm = P.cstr(d[3] + 8, 300).decode('latin1')
            col_cache[c] = {'d': d, 'name': nm}
    return col_cache[c]

# ---------- enumerate COL records and vtables ----------
all_cols = set()
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    for c in range(s['lo'], s['hi_file'] - 20, 4):
        if is_col(c):
            all_cols.add(c)

tables = []
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    for b in range(s['lo'], s['hi_file'] - 4, 4):
        v = P.dw(b)
        if v is None or sec(v) != '.text':
            continue
        c = P.dw(b - 4)
        ci = col_info(c)
        if ci is None:
            continue
        n = 0
        a = b
        while True:
            x = P.dw(a)
            if x is None or sec(x) != '.text':
                break
            n += 1
            a += 4
        tables.append({'vt': b, 'col': c, 'name': ci['name'],
                       'mdisp': ci['d'][1], 'd': ci['d'], 'slots': n, 'end': a})

tables.sort(key=lambda t: t['vt'])
table_cols = {t['col'] for t in tables}
slots_total = sum(t['slots'] for t in tables)

# ---------- Q1 grouping ----------
groups = collections.defaultdict(list)
for t in tables:
    groups[t['name']].append(t)
for g in groups.values():
    g.sort(key=lambda t: t['vt'])
size_dist = collections.Counter(len(g) for g in groups.values())

# ---------- Q2 mdisp rule ----------
def signed32(u):
    return u - (1 << 32) if u >= (1 << 31) else u

def rule(seq):
    return len(seq) > 1 and all(seq[i] > seq[i+1] for i in range(len(seq)-1)) and seq[-1] == 0

multi = {k: g for k, g in groups.items() if len(g) > 1}
q2_pass, q2_fail = [], []
for k, g in multi.items():
    seq = [t['mdisp'] for t in g]
    (q2_pass if rule(seq) else q2_fail).append(
        {'name': k, 'mdisp_u': seq, 'mdisp_s': [signed32(x) for x in seq],
         'vts': [t['vt'] for t in g]})

# ---------- Q3 block gaps ----------
gaps = []
for k, g in multi.items():
    for i in range(len(g)-1):
        gaps.append({'name': k, 'prev_vt': g[i]['vt'], 'next_vt': g[i+1]['vt'],
                     'gap': g[i+1]['vt'] - (g[i]['vt'] + 4*g[i]['slots'])})
gap_dist = collections.Counter(x['gap'] for x in gaps)

# ---------- Q4 non-contiguous groups ----------
order = [t['name'] for t in tables]
occ = collections.defaultdict(list)
for i, nm in enumerate(order):
    occ[nm].append(i)
noncontig = []
for k, idx in occ.items():
    if len(idx) < 2:
        continue
    if any(order[j] != k for j in range(idx[0], idx[-1]+1)):
        between = collections.Counter(order[j] for j in range(idx[0]+1, idx[-1]))
        noncontig.append({'name': k, 'n': len(idx), 'first': tables[idx[0]]['vt'],
                          'last': tables[idx[-1]]['vt'],
                          'interleaved': {kk: vv for kk, vv in between.items()}})

# ---------- classification of tails (variants) ----------
def tail_class(t, nxt):
    e = t['end']
    tight = (nxt is not None and e == nxt['vt'] - 4)
    zero = (P.dw(e) == 0)
    dv = (sec(P.dw(e)) == '.data')
    if tight: return 'tight'
    if zero: return 'zero'
    # 4 张「终点落 .data」实为终点 dword 指向 .data（R189 原始语义）
    if dv: return 'data'
    return 'scatter'

variant_counts = {'base': None}
tails = collections.defaultdict(list)
for i, t in enumerate(tables):
    tails[tail_class(t, tables[i+1] if i+1 < len(tables) else None)].append(t)
best_mode = 'base'
variant_counts['base'] = {k: len(v) for k, v in tails.items()}

# ---------- Q5 scattered tails ----------
def is_print(b):
    return 0x20 <= b <= 0x7e or b in (9, 10, 13)

def nearest_string(va, radius=512, minlen=4):
    o = P.r2o(va)
    if o is None:
        return None
    best = None
    for d in range(0, radius+1):
        for oo in (o-d, o+d):
            if oo < 0 or oo >= len(P.RAW) or not is_print(P.RAW[oo]):
                continue
            j = oo
            while j < len(P.RAW) and is_print(P.RAW[j]) and j - oo < 300:
                j += 1
            if j - oo >= minlen:
                cand = {'offset': oo - o, 'ascii': P.RAW[oo:j].decode('latin1')}
                if best is None or abs(oo-o) < abs(best['offset']):
                    best = cand
        if best is not None and abs(best['offset']) <= d:
            break
    return best

def classify_val(v):
    s = sec(v)
    if s == '.text':
        return 'text'
    if s == '.rdata' and P.r2o(v) is not None:
        o = P.r2o(v)
        b0 = P.RAW[o] if o < len(P.RAW) else 0
        prev = P.RAW[o-1] if o > 0 else 0
        if is_print(b0) and (prev == 0 or o == P.B['.rdata']['rawptr']):
            return 'rdata_string_ptr'
    exp = (v >> 23) & 0xff
    if 1 <= exp <= 254:
        return 'float_const'
    return 'other'

q5 = []
q5_kind = collections.Counter()
q5_text_targets = []
for t in tails['scatter']:
    e = t['end']
    v = P.dw(e)
    raw8 = [P.dw(e + 4*i) for i in range(8)]
    kind = classify_val(v)
    q5_kind[kind] += 1
    item = {'vt': t['vt'], 'name': t['name'], 'slots': t['slots'],
            'end': e, 'end_sec': sec(e), 'val': v, 'val_sec': sec(v),
            'kind': kind, 'raw8': raw8}
    q5.append(item)
    if kind == 'text':
        o = P.r2o(v)
        item['target16'] = P.RAW[o:o+16].hex() if o is not None else None
        item['near_string'] = nearest_string(v)
        q5_text_targets.append(item)

# ---------- Q6 independent recount ----------
recount_cols = set()
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    for a in range(s['lo'], s['hi_file'] - 20, 4):
        if is_col(a):
            recount_cols.add(a)
recount = {'col_scan': len(recount_cols), 'col_from_tables': len(table_cols),
           'col_set_equal': recount_cols == table_cols,
           'vt_count': len(tables), 'slot_sum': slots_total}

# ---------- anti-controls ----------
ctrl = {}
ctrl_desc = ctrl['desc'] = {}
seqs_asc = {k: [t['mdisp'] for t in g] for k, g in multi.items()}
seqs_desc = {k: list(reversed(v)) for k, v in seqs_asc.items()}
ctrl['q2_asc_pass'] = sum(rule(v) for v in seqs_asc.values())
ctrl['q2_desc_same_rule_pass'] = sum(rule(v) for v in seqs_desc.values())
ctrl_desc['q2_desc_same_rule_pass'] = '同一判据施加于地址降序序列；若原规则特异应大量失败'
ctrl['q2_desc_mirrored_pass'] = sum(
    (len(v) > 1 and all(v[i] < v[i+1] for i in range(len(v)-1)) and v[0] == 0)
    for v in seqs_desc.values())
ctrl_desc['q2_desc_mirrored_pass'] = '降序序列改用严格递增+首项0；若原规则仅为序关系应等价通过'

field_pass = {}
for fi, label in enumerate(('d0', 'd1_mdisp', 'd2', 'd3', 'd4')):
    field_pass[label] = sum(rule([t['d'][fi] for t in g]) for g in multi.values())
ctrl['field_substitution'] = field_pass
ctrl_desc['field_substitution'] = '把 mdisp 换成 COL 其它 4 个字段后同一判据的通过组数'

rng = random.Random(190)
rand_pass = 0
weak_pass = 0
for k, g in multi.items():
    s = [t['mdisp'] for t in g]
    rng.shuffle(s)
    if rule(s): rand_pass += 1
    weak_pass += int(len(s) > 1 and all(s[i] >= s[i+1] for i in range(len(s)-1)) and s[-1] == 0)
ctrl['random_permutation_pass'] = rand_pass
ctrl_desc['random_permutation_pass'] = '固定种子打乱组内表序后判据通过组数；低值说明排序特异'
ctrl['weak_nonincreasing_pass'] = weak_pass
ctrl_desc['weak_nonincreasing_pass'] = '把严格递减放宽为非增后通过组数；用于检验严格性贡献'
ctrl['tautology_control'] = len(multi)
ctrl_desc['tautology_control'] = '恒真反控：断言末项等于自身，任何输入都通过；登记为无效反控'
ctrl['tautology_valid'] = False

# ---------- assertions ----------
ASS = []
def A(name, cond, detail=''):
    ASS.append({'name': name, 'ok': bool(cond), 'detail': detail})

A('col_independent', recount['col_scan'] == TARGET['col'], recount['col_scan'])
A('col_set_equal', recount['col_set_equal'])
A('vt_count', len(tables) == TARGET['vt'], len(tables))
A('slot_sum', slots_total == TARGET['slots'], slots_total)
A('group_sum', sum(len(g) for g in groups.values()) == len(tables))
A('tail_variant_base', variant_counts['base'] == {k: TARGET[k] for k in ('tight', 'zero', 'scatter', 'data')}, variant_counts['base'])
A('tail_class_total', sum(len(v) for v in tails.values()) == len(tables))
A('q2_partition', len(q2_pass) + len(q2_fail) == len(multi), len(multi))
A('q3_gap_count', sum(gap_dist.values()) == sum(len(g)-1 for g in multi.values()))
A('q4_bound', len(noncontig) <= len(multi))
A('q5_count', len(q5) == TARGET['scatter'], len(q5))
A('q6_counts', len(recount_cols) == len(tables) == TARGET['vt'])
A('q2_order_specific', ctrl['q2_desc_same_rule_pass'] < ctrl['q2_asc_pass'],
   [ctrl['q2_desc_same_rule_pass'], ctrl['q2_asc_pass']])
A('q2_mirror_equivalent', ctrl['q2_desc_mirrored_pass'] == ctrl['q2_asc_pass'],
   [ctrl['q2_desc_mirrored_pass'], ctrl['q2_asc_pass']])
A('tautology_declared', ctrl['tautology_valid'] is False)

ok = sum(a['ok'] for a in ASS)
fail = len(ASS) - ok

# ---------- stdout report ----------
print('=== R190 EXEC hy4 ===')
print('sha256', hashlib.sha256(P.RAW).hexdigest())
print('sections', [(s['name'], hex(s['lo']), hex(s['hi_file']), hex(s['hi_virt'])) for s in P.SECS])
print('enumerate: cols_scan=%d cols_from_tables=%d set_equal=%s vt=%d slots=%d' %
      (recount['col_scan'], recount['col_from_tables'], recount['col_set_equal'], len(tables), slots_total))
print('Q1 groups=%d dist=%s' % (len(groups), dict(sorted(size_dist.items()))))
print('Q2 multi_groups=%d pass=%d fail=%d' % (len(multi), len(q2_pass), len(q2_fail)))
for c in q2_fail:
    print('Q2-COUNTER %s u=%s s=%s vts=%s' % (c['name'], c['mdisp_u'], c['mdisp_s'],
          [hex(x) for x in c['vts']]))
print('Q3 pairs=%d dist=%s gap4=%d' % (len(gaps), dict(sorted(gap_dist.items())), gap_dist.get(4, 0)))
print('Q4 noncontig=%d' % len(noncontig))
for c in noncontig[:20]:
    print('Q4-EX %s n=%d %s..%s interleaved=%s' % (c['name'], c['n'], hex(c['first']),
          hex(c['last']), {k: v for k, v in list(c['interleaved'].items())[:5]}))
print('tail_variants %s chosen=%s actual=%s' % (variant_counts, best_mode,
      {k: len(v) for k, v in tails.items()}))
print('Q5 kinds=%s text_targets=%d' % (dict(q5_kind), len(q5_text_targets)))
for c in q5:
    print('Q5 %s vt=%s slots=%d end=%s end_sec=%s val=%s val_sec=%s kind=%s raw8=%s' %
          (c['name'], hex(c['vt']), c['slots'], hex(c['end']), c['end_sec'], hex(c['val']),
           c['val_sec'], c['kind'], [hex(x) if x is not None else None for x in c['raw8']]))
for c in q5_text_targets:
    print('Q5-TEXT %s val=%s bytes=%s near=%s' % (c['name'], hex(c['val']), c['target16'], c['near_string']))
print('Q6 %s' % recount)
print('CTRL %s' % {k: v for k, v in ctrl.items() if k != 'desc'})
print('CTRL-DESC %s' % ctrl['desc'])
for a in ASS:
    print('ASSERT %s %s %s' % ('PASS' if a['ok'] else 'FAIL', a['name'], a['detail']))
print('ASSERT ok=%d fail=%d' % (ok, fail))

out = {
    'meta': {'sha256': hashlib.sha256(P.RAW).hexdigest(), 'best_tail_mode': best_mode,
             'sections': [[s['name'], s['lo'], s['hi_file'], s['hi_virt']] for s in P.SECS]},
    'q1': {'groups': len(groups), 'size_dist': dict(sorted(size_dist.items())),
           'group_names_sample': sorted(groups)[:30]},
    'q2': {'multi_groups': len(multi), 'pass': len(q2_pass), 'fail': len(q2_fail),
           'failures': q2_fail, 'passes': q2_pass[:20]},
    'q3': {'pairs': len(gaps), 'dist': dict(sorted(gap_dist.items())),
           'gap4': gap_dist.get(4, 0), 'non4_samples': [x for x in gaps if x['gap'] != 4][:20]},
    'q4': {'noncontig': len(noncontig), 'samples': noncontig[:20]},
    'q5': {'tail_variant_counts': variant_counts, 'kinds': dict(q5_kind),
           'scattered_count': len(q5), 'entries': q5, 'text_targets': q5_text_targets},
    'q6': recount,
    'controls': ctrl,
    'assertions': {'ok': ok, 'fail': fail, 'detail': ASS},
}
js = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
with open(ROOT + '/_r190/exec_hy4/r190exec.json', 'w', encoding='utf-8') as f:
    f.write(js + '\n')
print(js)
