#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 EXEC A: 主虚表前缀继承一致性普查（全静态，单次运行输出全部证据）。"""
import sys, os, json, struct, collections, hashlib, time, traceback
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT  = ROOT + '/_r199/exec_a'
T0 = time.time()
ASS = []

def A(desc, cond, detail=''):
    ok = bool(cond)
    ASS.append({'desc': desc, 'pass': ok, 'detail': str(detail)})
    print(('PASS' if ok else 'FAIL') + ' | ' + desc + ' | ' + str(detail))

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def in_sec(va, name):
    if va is None:
        return False
    s = P.B.get(name)
    return s is not None and s['lo'] <= va < s['hi_file']

TD_LO, TD_HI = 0x401000, 0x7E1000
def is_text_ptr(v):
    return v is not None and TD_LO <= v < TD_HI

def cname(ptd):
    if ptd is None:
        return None
    b = P.cstr(ptd + 8, 400)
    return None if b is None else b.decode('latin1', 'replace')

def hexbytes(va, n):
    o = P.r2o(va)
    if o is None:
        return None
    return P.RAW[o:o + n].hex()

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
def icount_until_ret(va, limit=200):
    o = P.r2o(va)
    if o is None:
        return None, None
    code = P.RAW[o:o + limit]
    n = 0
    for ins in MD.disasm(code, va):
        n += 1
        if ins.mnemonic.startswith('ret'):
            return n, ins.mnemonic
    return n, None

print('=' * 100)
print('R199 EXEC A | exe=%s' % (ROOT + '/ra2bench/gamemd.exe'))
print('EXE_SHA256=' + sha(ROOT + '/ra2bench/gamemd.exe'))
print('SECTIONS=' + json.dumps([{k: s[k] for k in ('name', 'lo', 'hi_file', 'rawsize')} for s in P.SECS]))
print('=' * 100)

# ---------- P1: COL 扫描 ----------
cols = {}
scan_secs = ['.rdata', '.data']
for sn in scan_secs:
    s = P.B[sn]
    for va in range(s['lo'], s['hi_file'], 4):
        d0 = P.dw(va)
        if d0 is None or d0 > 2:
            continue
        if P.dw(va + 8) != 0:
            continue
        ptd = P.dw(va + 12)
        if not in_sec(ptd, '.data'):
            continue
        chd = P.dw(va + 16)
        if not in_sec(chd, '.rdata'):
            continue
        cols[va] = {'col': va, 'sig': d0, 'mdisp': P.dw(va + 4),
                    'ptd': ptd, 'chd': chd, 'name': cname(ptd)}
COL_N = len(cols)
print('P1 COL_N=%d' % COL_N)

# ---------- P2: VT 扫描 ----------
vts = {}
def add_vt(va, d):
    c = P.dw(va - 4)
    if c is None or c not in cols:
        return False
    n = 0
    while True:
        q = P.dw(va + 4 * n)
        if q is None or not (TD_LO <= q < TD_HI):
            break
        n += 1
        if n >= 8192:
            break
    vts[va] = {'vt': va, 'col': c, 'nslot': n, 'capped': n >= 8192, 'first': d}
    return True

for sn in scan_secs:
    s = P.B[sn]
    for va in range(s['lo'], s['hi_file'], 4):
        d = P.dw(va)
        if is_text_ptr(d):
            add_vt(va, d)
VT_N = len(vts)
SLOT_TOTAL = sum(x['nslot'] for x in vts.values())
CAPN = sum(1 for x in vts.values() if x['capped'])
print('P2 VT_N=%d SLOT_TOTAL=%d capped=%d' % (VT_N, SLOT_TOTAL, CAPN))

# 段外补充扫描（只报告，不改变主统计）
extra_vt = []
for s in P.SECS:
    if s['name'] in scan_secs or s['rawsize'] == 0:
        continue
    for va in range(s['lo'], s['hi_file'], 4):
        d = P.dw(va)
        if is_text_ptr(d):
            c = P.dw(va - 4)
            if c is not None and c in cols:
                extra_vt.append(va)
print('P2 EXTRA_VT_OUTSIDE_RDATA_DATA=%d %s' % (len(extra_vt), [hex(x) for x in extra_vt[:10]]))

# ---------- P3: 主表 ----------
main = sorted(v for v in vts if cols[vts[v]['col']]['mdisp'] == 0)
MAIN_N = len(main)
main_ptds = set(cols[vts[v]['col']]['ptd'] for v in main)
ptd2vt = collections.defaultdict(list)
for v in main:
    ptd2vt[cols[vts[v]['col']]['ptd']].append(v)
multi_vt_ptd = {hex(k): [hex(x) for x in v] for k, v in ptd2vt.items() if len(v) > 1}
print('P3 MAIN_N=%d distinct_ptd=%d ptd_with_multiple_main_vt=%d' % (MAIN_N, len(main_ptds), len(multi_vt_ptd)))

U = 0x7F5C70
unit_present = U in vts
unit_name = cols[vts[U]['col']]['name'] if unit_present else None
unit_nslot = vts[U]['nslot'] if unit_present else None
print('Q1 0x7F5C70 present=%s name=%s nslot=%s col=%s mdisp=%s' % (
    unit_present, unit_name, unit_nslot,
    hex(vts[U]['col']) if unit_present else None,
    cols[vts[U]['col']]['mdisp'] if unit_present else None))

A('P1 COL == 1214', COL_N == 1214, COL_N)
A('P2 VT == 1214', VT_N == 1214, VT_N)
A('P2 slot total == 14044', SLOT_TOTAL == 14044, SLOT_TOTAL)
A('P3 main == 954', MAIN_N == 954, MAIN_N)
A('.text 文件区间 == 0x401000..0x7E1000',
  P.B['.text']['lo'] == TD_LO and P.B['.text']['hi_file'] == TD_HI,
  '%s..%s' % (hex(P.B['.text']['lo']), hex(P.B['.text']['hi_file'])))
A('unit vt 0x7F5C70 存在', unit_present, unit_present)
A('unit class name == .?AVUnitClass@@', unit_name == '.?AVUnitClass@@', unit_name)
A('unit nslot == 344', unit_nslot == 344, unit_nslot)
A('无 VT 槽数触顶(8192)', CAPN == 0, CAPN)
A('VT 段外补充计数为 0', len(extra_vt) == 0, len(extra_vt))

# ---------- CHD / BCD ----------
def read_chd(col):
    chd = cols[col]['chd']
    if P.dw(chd) != 0:
        return None
    n = P.dw(chd + 8)
    pb = P.dw(chd + 12)
    if n is None or pb is None or n > 4096:
        return None
    nodes = []
    for i in range(n):  # BCD 数组恰 n 项: 结点0(自身) + (n-1) 个基类(已展开的扁平表)
        bcd = P.dw(pb + 4 * i)
        if bcd is None or not in_sec(bcd, '.rdata'):
            return None
        ptd = P.dw(bcd)
        ncb = P.dw(bcd + 4)
        md = P.dw(bcd + 8)
        if ptd is None or ncb is None or md is None:
            return None
        mds = md - (1 << 32) if md >= (1 << 31) else md
        nodes.append({'bcd': bcd, 'ptd': ptd, 'ncb': ncb, 'mdisp': mds,
                      'name': cname(ptd)})
    return nodes

def direct_children(nodes, i=0):
    res = []
    j = i + 1
    lim = i + nodes[i]['ncb']
    while j <= lim and j < len(nodes):
        res.append(j)
        j = j + nodes[j]['ncb'] + 1
    return res

# ---------- Q2 ----------
cat = collections.Counter()
d2_list = []
no_base_names = []
pairs = []          # (vt_d, vt_b, cname, bname, ptd_b)
unpaired_vts = []
for vt in main:
    col = vts[vt]['col']
    cn = cols[col]['name']
    nodes = read_chd(col)
    if nodes is None:
        cat['a'] += 1
        unpaired_vts.append(vt)
        continue
    ch = direct_children(nodes)
    if not ch:
        cat['b'] += 1
        no_base_names.append(cn)
        unpaired_vts.append(vt)
        continue
    zeros = [nodes[j] for j in ch if nodes[j]['mdisp'] == 0]
    if not zeros:
        cat['c'] += 1
        unpaired_vts.append(vt)
        continue
    if len(zeros) > 1:
        cat['multi'] += 1
        unpaired_vts.append(vt)
        continue
    b = zeros[0]
    if b['ptd'] in main_ptds:
        cat['d1'] += 1
        vb = ptd2vt[b['ptd']][0]
        pairs.append({'vt_d': vt, 'vt_b': vb, 'cname': cn, 'bname': b['name'],
                      'b_ptd': b['ptd'], 'b_ncb': b['ncb']})
    else:
        cat['d2'] += 1
        d2_list.append({'cname': cn, 'bname': b['name'], 'b_ptd': hex(b['ptd'])})
        unpaired_vts.append(vt)

print('P5 chain: total_direct_children=%d sampled=%d' % (sum(len(direct_children(read_chd(vts[v]['col']))) for v in main), len(main)))
print('Q2 categories a=%d b=%d c=%d d1=%d d2=%d multi_zero=%d sum=%d' % (
    cat['a'], cat['b'], cat['c'], cat['d1'], cat['d2'], cat['multi'],
    cat['a'] + cat['b'] + cat['c'] + cat['d1'] + cat['d2'] + cat['multi']))
print('Q2 d2_list(total=%d) first30=%s' % (len(d2_list), json.dumps(d2_list[:30], ensure_ascii=False)))
A('Q2 六类计数合计 == 954',
  cat['a'] + cat['b'] + cat['c'] + cat['d1'] + cat['d2'] + cat['multi'] == MAIN_N,
  sum(cat.values()))
A('Q2 d1 == 配对数', cat['d1'] == len(pairs), len(pairs))
A('Q2 配对 vt_d 与 vt_b 不同', all(p['vt_d'] != p['vt_b'] for p in pairs),
  sum(1 for p in pairs if p['vt_d'] == p['vt_b']))

# ---------- Q3 ----------
slot_bad = collections.Counter()
slot_den = collections.Counter()
tot_cmp = tot_mat = tot_bad = 0
zero_bad_pairs = 0
pos_bad_pairs = 0
shorter = 0
for ps in pairs:
    nd = vts[ps['vt_d']]['nslot']
    nb = vts[ps['vt_b']]['nslot']
    L = min(nd, nb)
    ps['nd'], ps['nb'], ps['L'] = nd, nb, L
    if nd < nb:
        shorter += 1
    bad = []
    for k in range(L):
        a = P.dw(ps['vt_d'] + 4 * k)
        b = P.dw(ps['vt_b'] + 4 * k)
        slot_den[k] += 1
        tot_cmp += 1
        if a == b:
            tot_mat += 1
        else:
            bad.append(k)
            slot_bad[k] += 1
            tot_bad += 1
    ps['bad'] = bad
    if bad:
        pos_bad_pairs += 1
    else:
        zero_bad_pairs += 1
real_rate = 100.0 * tot_mat / tot_cmp if tot_cmp else 0.0
top_slots = sorted(slot_bad.keys(), key=lambda k: (-slot_bad[k], k))[:25]
print('Q3 pairs=%d zero_bad=%d pos_bad=%d compared=%d match=%d mismatch=%d rate=%.2f%% shorter=%d' % (
    len(pairs), zero_bad_pairs, pos_bad_pairs, tot_cmp, tot_mat, tot_bad, real_rate, shorter))
print('Q3 TOP25 slot|bad_pairs|denominator|pct:')
for k in top_slots:
    print('   %4d | %4d | %4d | %6.2f' % (k, slot_bad[k], slot_den[k], 100.0 * slot_bad[k] / slot_den[k]))
A('Q3 compared == match + mismatch', tot_cmp == tot_mat + tot_bad, (tot_cmp, tot_mat, tot_bad))
A('Q3 zero_bad + pos_bad == pairs', zero_bad_pairs + pos_bad_pairs == len(pairs),
  (zero_bad_pairs, pos_bad_pairs))
A('Q3 所有比较槽 dword 均非 None',
  all(P.dw(p['vt_d'] + 4 * k) is not None and P.dw(p['vt_b'] + 4 * k) is not None
      for p in pairs for k in range(p['L'])), 'checked')

# ---------- Q4 ----------
samples = []
for k in top_slots[:5]:
    ps = next((p for p in pairs if k in p['bad']), None)
    if ps is None:
        samples.append({'slot': k, 'status': 'no_pair'})
        continue
    td = P.dw(ps['vt_d'] + 4 * k)
    tb = P.dw(ps['vt_b'] + 4 * k)
    nd, md = icount_until_ret(td, 200)
    nb, mb = icount_until_ret(tb, 200)
    samples.append({'slot': k, 'cname': ps['cname'], 'bname': ps['bname'],
                    'vt_d': hex(ps['vt_d']), 'vt_b': hex(ps['vt_b']),
                    'target_d': hex(td), 'target_b': hex(tb),
                    'body16_d': hexbytes(td, 16), 'body16_b': hexbytes(tb, 16),
                    'insn_to_ret_d': nd, 'first_ret_d': md,
                    'insn_to_ret_b': nb, 'first_ret_b': mb})
print('Q4 SAMPLES=' + json.dumps(samples, ensure_ascii=False))
A('Q4 五个热点槽均找到具体配对', all(s.get('cname') for s in samples), len(samples))
A('Q4 所有样本函数体前16字节可读',
  all(s.get('body16_d') and len(s['body16_d']) == 32 and s.get('body16_b') and len(s['body16_b']) == 32
      for s in samples), 'checked')

# ---------- Q5 ----------
q5 = {}
for k in (0, 1, 2):
    cd = collections.Counter()
    cb = collections.Counter()
    for ps in pairs:
        if ps['L'] > k:
            cd[P.dw(ps['vt_d'] + 4 * k)] += 1
            cb[P.dw(ps['vt_b'] + 4 * k)] += 1
    q5[str(k)] = {
        'bad_pairs': slot_bad[k], 'denominator': slot_den[k],
        'top3_derived': [[hex(a), c] for a, c in cd.most_common(3)],
        'top3_base': [[hex(a), c] for a, c in cb.most_common(3)],
    }
    print('Q5 slot=%d bad=%d denom=%d topD=%s topB=%s' % (
        k, slot_bad[k], slot_den[k], json.dumps(q5[str(k)]['top3_derived']),
        json.dumps(q5[str(k)]['top3_base'])))
A('Q5 槽0/1/2 分母 == 该槽实际有比较的配对数',
  all(slot_den[k] == sum(1 for p in pairs if p['L'] > k) for k in (0, 1, 2)),
  [slot_den[k] for k in (0, 1, 2)])

# ---------- Q6 ----------
unpaired_slot0_text = sum(1 for v in unpaired_vts if is_text_ptr(P.dw(v)))
print('Q6 unpaired_total=%d slot0_in_text=%d no_base_names(total=%d) first20=%s' % (
    len(unpaired_vts), unpaired_slot0_text, len(no_base_names),
    json.dumps(no_base_names[:20], ensure_ascii=False)))
A('Q6 未配对数 == 954 - 配对数', len(unpaired_vts) == MAIN_N - len(pairs), len(unpaired_vts))
A('Q6 未配对主表槽0全部落 .text', unpaired_slot0_text == len(unpaired_vts),
  (unpaired_slot0_text, len(unpaired_vts)))

# ---------- R1 打乱对照 ----------
M = len(main)
r1_cmp = r1_mat = 0
r1_three_cmp = r1_three_mat = 0
for i, ps in enumerate(pairs):
    vs = main[(i * 137 + 11) % M]
    nd = ps['nd']
    ns = vts[vs]['nslot']
    L = min(nd, ns)
    for k in range(L):
        a = P.dw(ps['vt_d'] + 4 * k)
        b = P.dw(vs + 4 * k)
        r1_cmp += 1
        if a == b:
            r1_mat += 1
    for k in range(3):
        if k < L:
            a = P.dw(ps['vt_d'] + 4 * k)
            b = P.dw(vs + 4 * k)
            r1_three_cmp += 1
            if a == b:
                r1_three_mat += 1
r1_rate = 100.0 * r1_mat / r1_cmp if r1_cmp else 0.0
r1_three_rate = 100.0 * r1_three_mat / r1_three_cmp if r1_three_cmp else 0.0
print('R1 real_rate=%.2f%% shuffled_rate=%.2f%% (cmp=%d mat=%d) delta=%.2f' % (
    real_rate, r1_rate, r1_cmp, r1_mat, real_rate - r1_rate))
A('R1 打乱匹配率显著低于真实匹配率', r1_rate < real_rate - 10.0,
  '%.2f vs %.2f' % (r1_rate, real_rate))

# ---------- R2 长度 L / L+1 / L-1 ----------
def rate_with_extra(extra):
    cmp = mat = skipped = forced = 0
    for ps in pairs:
        vb = ps['vt_b']
        L = max(0, ps['L'] + extra)
        for k in range(L):
            a = P.dw(ps['vt_d'] + 4 * k)
            b = P.dw(vb + 4 * k)
            if a is None or b is None:
                skipped += 1
                if (a is None) != (b is None):
                    forced += 1
                continue
            cmp += 1
            if a == b:
                mat += 1
    return {'extra': extra, 'compared': cmp, 'match': mat,
            'rate': 100.0 * mat / cmp if cmp else 0.0,
            'skipped': skipped, 'forced_mismatch_if_none_sentinel': forced}

r2 = [rate_with_extra(x) for x in (0, 1, -1)]
for x in r2:
    print('R2 L%+d: compared=%d match=%d rate=%.2f%% skipped=%d forced_mismatch=%d' % (
        x['extra'], x['compared'], x['match'], x['rate'], x['skipped'],
        x['forced_mismatch_if_none_sentinel']))
A('R2 L+1 恰好增加 603 个比较槽且匹配率下降',
  r2[1]['compared'] - r2[0]['compared'] == len(pairs) and r2[1]['rate'] < r2[0]['rate'],
  (r2[0]['compared'], r2[1]['compared'], r2[0]['rate'], r2[1]['rate']))
A('R2 L-1 比较槽减少', r2[2]['compared'] < r2[0]['compared'],
  (r2[0]['compared'], r2[2]['compared']))

# ---------- R3 三槽 ----------
r3_cmp = r3_mat = 0
for ps in pairs:
    for k in range(3):
        if ps['L'] > k:
            r3_cmp += 1
            if P.dw(ps['vt_d'] + 4 * k) == P.dw(ps['vt_b'] + 4 * k):
                r3_mat += 1
r3_rate = 100.0 * r3_mat / r3_cmp if r3_cmp else 0.0
print('R3 three-slot real=%.2f%% (%d/%d) shuffled=%.2f%% (%d/%d)' % (
    r3_rate, r3_mat, r3_cmp, r1_three_rate, r1_three_mat, r1_three_cmp))
A('R3 三槽打乱率低于真实率', r1_three_rate < r3_rate,
  '%.2f vs %.2f' % (r1_three_rate, r3_rate))
A('断言总数 >= 12', len(ASS) >= 12, len(ASS))

# ---------- 输出 ----------
R = {
    'meta': {
        'exe': ROOT + '/ra2bench/gamemd.exe',
        'exe_sha256': sha(ROOT + '/ra2bench/gamemd.exe'),
        'image_base': '0x400000', 'text_range': ['0x401000', '0x7E1000'],
        'elapsed_sec': round(time.time() - T0, 2),
        'scan_sections': scan_secs,
    },
    'q1': {'col_n': COL_N, 'vt_n': VT_N, 'slot_total': SLOT_TOTAL,
           'main_n': MAIN_N, 'capped': CAPN,
           'extra_vt_outside': [hex(x) for x in extra_vt[:100]],
           'extra_vt_outside_n': len(extra_vt),
           'unit_vt': {'present': unit_present, 'name': unit_name,
                       'nslot': unit_nslot, 'col': hex(vts[U]['col']) if unit_present else None}},
    'q2': {'a': cat['a'], 'b': cat['b'], 'c': cat['c'], 'd1': cat['d1'],
           'd2': cat['d2'], 'multi_zero': cat['multi'],
           'd2_total': len(d2_list), 'd2_first30': d2_list[:30],
           'pairs_n': len(pairs),
           'ptd_with_multiple_main_vt': multi_vt_ptd},
    'q3': {'pairs': len(pairs), 'zero_bad_pairs': zero_bad_pairs,
           'pos_bad_pairs': pos_bad_pairs, 'compared': tot_cmp,
           'match': tot_mat, 'mismatch': tot_bad,
           'mismatch_rate_pct': round(100.0 * tot_bad / tot_cmp, 2) if tot_cmp else None,
           'match_rate_pct': round(real_rate, 2),
           'shorter_pairs': shorter,
           'top25_slots': [{'slot': k, 'bad_pairs': slot_bad[k],
                            'denominator': slot_den[k],
                            'bad_pct': round(100.0 * slot_bad[k] / slot_den[k], 2)}
                           for k in top_slots]},
    'q4': samples,
    'q5': q5,
    'q6': {'unpaired_total': len(unpaired_vts),
           'unpaired_slot0_in_text': unpaired_slot0_text,
           'no_base_total': len(no_base_names), 'no_base_first20': no_base_names[:20]},
    'r1': {'real_rate_pct': round(real_rate, 2), 'shuffled_rate_pct': round(r1_rate, 2),
           'shuffled_compared': r1_cmp, 'shuffled_match': r1_mat,
           'delta_pct': round(real_rate - r1_rate, 2)},
    'r2': [{'extra': x['extra'], 'compared': x['compared'], 'match': x['match'],
            'rate_pct': round(x['rate'], 2), 'skipped': x['skipped'],
            'forced_mismatch_if_none_sentinel': x['forced_mismatch_if_none_sentinel']} for x in r2],
    'r3': {'real_rate_pct': round(r3_rate, 2), 'real_match': r3_mat, 'real_compared': r3_cmp,
           'shuffled_rate_pct': round(r1_three_rate, 2),
           'shuffled_match': r1_three_mat, 'shuffled_compared': r1_three_cmp},
    'assertions': {'total': len(ASS), 'pass': sum(1 for a in ASS if a['pass']),
                   'fail': sum(1 for a in ASS if not a['pass']), 'items': ASS},
}
jp = OUT + '/prefix.json'
tp = OUT + '/prefix.txt'
with open(jp, 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2)
    f.write('\n')
with open(tp, 'w', encoding='utf-8') as f:
    f.write('R199 EXEC A prefix inheritance census\n')
    f.write('EXE_SHA256=%s\n' % R['meta']['exe_sha256'])
    f.write('Q1 COL=%d VT=%d SLOTS=%d MAIN=%d UNIT=%s/%s\n' % (
        COL_N, VT_N, SLOT_TOTAL, MAIN_N, unit_name, unit_nslot))
    f.write('Q2 a=%d b=%d c=%d d1=%d d2=%d multi=%d d2_total=%d\n' % (
        cat['a'], cat['b'], cat['c'], cat['d1'], cat['d2'], cat['multi'], len(d2_list)))
    f.write('Q2 d2_first30=%s\n' % json.dumps(d2_list[:30], ensure_ascii=False))
    f.write('Q3 pairs=%d zero_bad=%d pos_bad=%d compared=%d match=%d mismatch=%d rate=%.2f%% shorter=%d\n' % (
        len(pairs), zero_bad_pairs, pos_bad_pairs, tot_cmp, tot_mat, tot_bad, real_rate, shorter))
    for k in top_slots:
        f.write('Q3 slot=%d bad=%d denom=%d pct=%.2f\n' % (
            k, slot_bad[k], slot_den[k], 100.0 * slot_bad[k] / slot_den[k]))
    f.write('Q4 samples=%s\n' % json.dumps(samples, ensure_ascii=False))
    for k in (0, 1, 2):
        f.write('Q5 slot=%d bad=%d denom=%d topD=%s topB=%s\n' % (
            k, slot_bad[k], slot_den[k], json.dumps(q5[str(k)]['top3_derived']),
            json.dumps(q5[str(k)]['top3_base'])))
    f.write('Q6 unpaired=%d slot0_text=%d no_base_total=%d no_base_first20=%s\n' % (
        len(unpaired_vts), unpaired_slot0_text, len(no_base_names),
        json.dumps(no_base_names[:20], ensure_ascii=False)))
    f.write('R1 real=%.2f%% shuffled=%.2f%% delta=%.2f\n' % (
        real_rate, r1_rate, real_rate - r1_rate))
    for x in r2:
        f.write('R2 L%+d compared=%d match=%d rate=%.2f%% skipped=%d forced=%d\n' % (
            x['extra'], x['compared'], x['match'], x['rate'], x['skipped'],
            x['forced_mismatch_if_none_sentinel']))
    f.write('R3 real=%.2f%% (%d/%d) shuffled=%.2f%% (%d/%d)\n' % (
        r3_rate, r3_mat, r3_cmp, r1_three_rate, r1_three_mat, r1_three_cmp))
    for a in ASS:
        f.write('ASSERT %s | %s | %s\n' % ('PASS' if a['pass'] else 'FAIL', a['desc'], a['detail']))
    f.write('ASSERT total=%d pass=%d fail=%d\n' % (
        len(ASS), sum(1 for a in ASS if a['pass']), sum(1 for a in ASS if not a['pass'])))
    f.write('elapsed_sec=%s\n' % R['meta']['elapsed_sec'])

print('=' * 100)
print('ASSERT total=%d pass=%d fail=%d => %s' % (
    len(ASS), sum(1 for a in ASS if a['pass']), sum(1 for a in ASS if not a['pass']),
    'PASS' if all(a['pass'] for a in ASS) else 'FAIL'))
print('OUTPUT %s sha256=%s lines=%d bytes=%d' % (jp, sha(jp), sum(1 for _ in open(jp)), os.path.getsize(jp)))
print('OUTPUT %s sha256=%s lines=%d bytes=%d' % (tp, sha(tp), sum(1 for _ in open(tp)), os.path.getsize(tp)))
print('ELAPSED_SEC=%.2f' % (time.time() - T0))
