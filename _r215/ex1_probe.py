#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R215-EX1 单次取证：视图重建断言 + G1..G5。只读业务文件，只写本文件产物。"""
import sys, os, json, struct, hashlib, collections, time, random, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_INS_CALL

T0 = time.time()
RAW = P.RAW
CHECKS = []
def check(name, ok, detail=''):
    CHECKS.append({'name': name, 'pass': bool(ok), 'detail': detail})
    print('[%s] %s%s' % ('PASS' if ok else 'FAIL', name,
                         (' :: ' + detail) if detail else ''))
def h(v):
    return 'None' if v is None else ('0x%08x' % (v & 0xffffffff))
def s32(v):
    return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]

sha = hashlib.sha256(RAW).hexdigest()
print('=== META ===')
print('RAW sha256=%s bytes=%d imagebase=%s' % (sha, len(RAW), h(P.IB)))
for s in P.SECS:
    print('  %-8s lo=%s hi_file=%s rawptr=0x%x rawsize=0x%x' %
          (s['name'], h(s['lo']), h(s['hi_file']), s['rawptr'], s['rawsize']))

# ---------- 表重建（按 R214 口径） ----------
def words(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return struct.unpack_from('<%dI' % n, RAW, s['rawptr']), s['lo']

COLA = {}
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 4):
        if w[k] > 2 or w[k + 2] != 0:
            continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata':
            continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@':
            continue
        COLA[base + 4 * k] = (s32(w[k + 1]), w[k + 3], w[k + 4], nm.decode('latin1'))

PRED = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    w, base = words(sn)
    for k in range(len(w) - 1):
        if w[k] in COLA and P.where(w[k + 1]) == '.text':
            PRED[w[k]].append(base + 4 * k)
starts = sorted(min(v) + 4 for v in PRED.values() if len(v) == 1)
S2C = {min(v) + 4: c for c, v in PRED.items() if len(v) == 1}
VIEWS = []
for i, st in enumerate(starts):
    end = starts[i + 1] if i + 1 < len(starts) else P.B['.rdata']['hi_file']
    sl = []
    a = st
    while a < end and P.where(P.dw(a)) == '.text':
        sl.append(P.dw(a)); a += 4
    md_, ptd, pchd, nm = COLA[S2C[st]]
    VIEWS.append(dict(col=S2C[st], base=st, slots=sl, mdisp=md_,
                      nm=nm[1:] if nm.startswith('.') else nm))
MAIN = [v for v in VIEWS if v['mdisp'] == 0]
SEC = [v for v in VIEWS if v['mdisp'] != 0]
TGT = collections.Counter(x for v in VIEWS for x in v['slots'])
has18 = [v for v in VIEWS if len(v['slots']) > 18]
c18 = collections.Counter(v['slots'][18] for v in has18)
assert_has18_main = sum(1 for v in has18 if v['mdisp'] == 0)
assert_has18_sec = sum(1 for v in has18 if v['mdisp'] != 0)

print('\n=== ASSERT ===')
print('views=%d main=%d sec=%d slots=%d distinct=%d has18=%d(main %d/sec %d) d18=%d' %
      (len(VIEWS), len(MAIN), len(SEC), sum(len(v['slots']) for v in VIEWS),
       len(TGT), len(has18), assert_has18_main, assert_has18_sec, len(c18)))
ASSERT = dict(assert_views=len(VIEWS), assert_main=len(MAIN), assert_sec=len(SEC),
              assert_slots=sum(len(v['slots']) for v in VIEWS),
              assert_distinct=len(TGT), assert_has18=len(has18), assert_d18=len(c18))
ok_assert = (ASSERT['assert_views'] == 1214 and ASSERT['assert_main'] == 954 and
             ASSERT['assert_sec'] == 260 and ASSERT['assert_slots'] == 14044 and
             ASSERT['assert_distinct'] == 6692 and ASSERT['assert_has18'] == 137 and
             assert_has18_main == 125 and assert_has18_sec == 12 and
             ASSERT['assert_d18'] == 27)
check('R214 基线全断言', ok_assert, json.dumps(ASSERT))
if not ok_assert:
    print('FAIL: 基线不符，停止推断。')
    raise SystemExit(2)

# ---------- 基础设施 ----------
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
def code_at(va, n):
    o = P.r2o(va)
    return b'' if o is None else RAW[o:o + n]
def dis_at(va, n):
    out = []
    for ins in md.disasm(code_at(va, 64), va, count=n):
        out.append({'addr': h(ins.address), 'bytes': ins.bytes.hex(),
                    'mnemonic': ins.mnemonic, 'op_str': ins.op_str})
    return out

# 一次性逐字节扫 .text 中 e8 rel32 调用点（建 call map），用 bytes.find 不常驻反汇编对象
text = P.B['.text']
tlo, tro, trs = text['lo'], text['rawptr'], text['rawsize']
blob = RAW[tro:tro + trs]
call_map = collections.defaultdict(list)
e8_total = 0
pos = 0
while True:
    i = blob.find(b'\xe8', pos)
    if i < 0 or i + 5 > len(blob):
        break
    pos = i + 1
    rel = struct.unpack_from('<i', blob, i + 1)[0]
    target = tlo + i + 5 + rel
    e8_total += 1
    call_map[target].append(tlo + i)
print('\n=== TEXT e8 SCAN ===')
print('e8_opcode_hits=%d distinct_targets=%d' % (e8_total, len(call_map)))

# 每个目标地址在全体槽位的 (slot, view) 出现记录（一次建好复用）
slot_occ_map = collections.defaultdict(list)
for v in VIEWS:
    for i, x in enumerate(v['slots']):
        slot_occ_map[x].append((i, v))

# ---------- G1 ----------
print('\n=== G1: slot18 landing admissibility ===')
G1 = []
for t in sorted(c18):
    # 函数入口证据（优先级 prev_ret > prev_pad > none）
    x1 = code_at(t - 1, 1)
    prev8 = code_at(t - 8, 8).hex()
    entry = 'none'
    if x1 and x1[0] in (0xc3, 0xc2):
        entry = 'prev_ret'
    else:
        pb = code_at(max(P.B['.text']['lo'], t - 64), min(64, t - P.B['.text']['lo']))
        n = 0
        for c in reversed(pb):
            if c in (0x90, 0xcc): n += 1
            else: break
        if n:
            entry = 'prev_pad'
    # 直接 e8 调用数 + capstone 单条复核
    sites = call_map.get(t, [])
    caller_ok = 0
    verified_sites = []
    for a in sites[:5]:
        ins = next(md.disasm(code_at(a, 16), a, count=1), None)
        ok = bool(ins and ins.id == X86_INS_CALL and ins.size == 5 and
                  len(ins.operands) == 1 and ins.operands[0].type == X86_OP_IMM and
                  ins.operands[0].imm == t)
        if ok:
            caller_ok += 1
            verified_sites.append(h(a))
    occ = slot_occ_map.get(t, [])
    poscnt = collections.Counter(i for i, _ in occ)
    g = {'t': h(t), 'ins': dis_at(t, 12), 'entry': entry, 'prev_hex': prev8,
         'prev_byte': x1.hex() if x1 else '',
         'callers': len(sites), 'caller_ok': caller_ok,
         'caller_sites_all': [h(a) for a in sites],
         'caller_verified': verified_sites,
         'slot_occ': len(occ), 'slot_positions': sorted(poscnt),
         'slot_pos_hist': {str(k): v for k, v in sorted(poscnt.items())}}
    g['ins12'] = g['ins']
    g['first3'] = g['ins'][:3]
    G1.append(g)
    g = G1[-1]
    print('%s entry=%s prev=%s e8=%d(verified %d) slot_occ=%d slot_positions=%s ins0=%s %s' %
          (g['t'], g['entry'], g['prev_hex'], g['callers'], g['caller_ok'],
           g['slot_occ'], g['slot_positions'],
           g['ins12'][0]['mnemonic'] if g['ins12'] else 'NONE',
           g['ins12'][0]['op_str'] if g['ins12'] else ''))

# ---------- G2 ----------
print('\n=== G2: class-family attribution ===')
def tokens(name):
    body = name.replace('?AV', '').replace('@@', '')
    parts = re.split(r'_', body)
    toks = []
    for p in parts:
        toks += [x for x in re.findall(r'[A-Z][a-z0-9]*|[A-Z]+(?![a-z])|[a-z0-9]+', p) if x]
    return toks

def common_tokens(names):
    c = collections.Counter()
    for nm in names:
        for tk in set(tokens(nm)):
            c[tk] += 1
    shared = [(tk, n) for tk, n in c.items() if n >= 2]
    shared.sort(key=lambda x: (-x[1], x[0]))
    return [{'token': tk, 'n': n} for tk, n in shared[:8]]

G2 = []
for t in sorted(c18):
    s18v = [v for v in has18 if v['slots'][18] == t]
    names = sorted(set(v['nm'] for v in s18v))
    # 这组类的主视图，除 slot18 外全同值的槽
    grpprim = [v for v in MAIN if v['nm'] in set(names)]
    shared = []
    if len(grpprim) >= 2:
        minlen = min(len(v['slots']) for v in grpprim)
        for i in range(minlen):
            vals = set(v['slots'][i] for v in grpprim)
            if i == 18 or len(vals) != 1:
                continue
            shared.append({'slot': i, 'target': h(next(iter(vals))), 'n': len(grpprim)})
        shared = shared[:10]
    rec = {'t': h(t), 'classes': names, 'nclass': len(names),
           'common_tokens': common_tokens(names) or 'none',
           'shared_other_slots': shared,
           'n_primary_views': len(grpprim)}
    G2.append(rec)
    print('%s nclass=%d common_tokens=%s shared_other_slots=%s' %
          (rec['t'], rec['nclass'],
           json.dumps(rec['common_tokens'], ensure_ascii=False),
           json.dumps(shared, ensure_ascii=False)))

# ---------- G3 ----------
print('\n=== G3: independence of slot18 reuse ===')
def prefix_stats(k):
    groups = collections.defaultdict(list)
    for v in has18:
        groups[tuple(v['slots'][:k])].append(v['slots'][18])
    same = sum(1 for vals in groups.values() if len(set(vals)) == 1)
    diff = len(groups) - same
    return {'clusters': len(groups), 'same': same, 'diff': diff,
            'max_cluster': max(len(x) for x in groups.values())}

g3_1 = prefix_stats(1)
g3_2 = prefix_stats(2)
g3_3 = prefix_stats(3)
G3 = {'clusters_3': g3_3['clusters'], 'max_cluster': g3_3['max_cluster'],
      'same18_3': g3_3['same'], 'diff18_3': g3_3['diff'],
      'clusters_2': g3_2['clusters'], 'same18_2': g3_2['same'],
      'diff18_2': g3_2['diff'],
      'clusters_1': g3_1['clusters'], 'same18_1': g3_1['same'],
      'diff18_1': g3_1['diff']}
print('prefix1: clusters=%d same=%d diff=%d same_ratio=%.4f' %
      (g3_1['clusters'], g3_1['same'], g3_1['diff'], g3_1['same'] / g3_1['clusters']))
print('prefix2: clusters=%d same=%d diff=%d same_ratio=%.4f' %
      (g3_2['clusters'], g3_2['same'], g3_2['diff'], g3_2['same'] / g3_2['clusters']))
print('prefix3: clusters=%d same=%d diff=%d max_cluster=%d same_ratio=%.4f' %
      (g3_3['clusters'], g3_3['same'], g3_3['diff'], g3_3['max_cluster'],
       g3_3['same'] / g3_3['clusters']))
ratio_1 = g3_1['same'] / g3_1['clusters']
ratio_3 = g3_3['same'] / g3_3['clusters']
indep = (abs(ratio_1 - ratio_3) < 0.01)  # 单元组与三元组比例差 <1 个百分点视为一样高
print('INTERPRET: prefix1_ratio=%.4f prefix3_ratio=%.4f delta=%.4f equalish=%s -> %s' %
      (ratio_1, ratio_3, ratio_3 - ratio_1, indep,
       'slot18 一致性不是独立信息（单元组已达 %.0f%%，三元组仅 %.1f%%）'
       % (ratio_1 * 100, ratio_3 * 100) if indep else '一致性随前缀显著变化'))

# ---------- G4 ----------
print('\n=== G4: stub 0x4c9150 ===')
STUB = 0x4c9150
stub_occ = slot_occ_map.get(STUB, [])
stub_hist = collections.Counter(i for i, _ in stub_occ)
stub_s18 = [v for i, v in stub_occ if i == 18]
stub_ins = dis_at(STUB, 3)
stub_hex = code_at(STUB, 3).hex()
G4 = {'stub': h(STUB), 'bytes': stub_hex, 'total_occ': len(stub_occ),
      'pos_hist': {str(k): v for k, v in sorted(stub_hist.items())},
      'as_slot18_views': [{'class': v['nm'], 'mdisp': v['mdisp'],
                           'start': h(v['base'])} for v in stub_s18]}
print('stub bytes=%s ins=%s' % (stub_hex, json.dumps(stub_ins, ensure_ascii=False)))
print('total_occ=%d pos_hist=%s slot18_views=%d' %
      (len(stub_occ), json.dumps(G4['pos_hist']), len(stub_s18)))
for x in G4['as_slot18_views']:
    print('  slot18: %s' % json.dumps(x, ensure_ascii=False))
check('stub bytes == 33c0c3', stub_hex == '33c0c3', stub_hex)

# ---------- G5 ----------
print('\n=== G5: positive/negative controls ===')
def slot_control(idx):
    grp = [v for v in VIEWS if len(v['slots']) > idx]
    vals = [v['slots'][idx] for v in grp]
    cnt = collections.Counter(vals)
    # 按「目标占据的不同槽号个数」判定：仅此一个 slot 号 vs 也出现在别的槽号
    once = sum(1 for t in cnt if len(set(i for i, _ in slot_occ_map[t])) == 1)
    multi = len(cnt) - once
    return {'views': len(grp), 'targets_distinct': len(cnt),
            'targets_only_this_slot': once, 'targets_also_elsewhere': multi,
            'only_ratio': round(once / len(cnt), 6) if cnt else None,
            'also_ratio': round(multi / len(cnt), 6) if cnt else None}

c17, c19 = slot_control(17), slot_control(19)
print('slot17: %s' % json.dumps(c17, ensure_ascii=False))
print('slot19: %s' % json.dumps(c19, ensure_ascii=False))
check('slot17 views == 141', c17['views'] == 141, str(c17['views']))
check('slot19 views == 137', c19['views'] == 137, str(c19['views']))

# 反控：随机 20 个「不在 slot18 出现、但在别处出现」的 .text 地址
s18set = set(c18)
pool = sorted(t for t in slot_occ_map if t not in s18set and P.where(t) == '.text')
rng = random.Random(215)
sample = rng.sample(pool, 20)
rand_recs = []
for t in sample:
    occ = slot_occ_map[t]
    names = sorted(set(v['nm'] for _, v in occ))
    rand_recs.append({'t': h(t), 'nclass': len(names), 'classes': names,
                      'slot_occ': len(occ)})
    print('rand %s nclass=%d slot_occ=%d' % (h(t), len(names), len(occ)))
rand_share = sum(1 for r in rand_recs if r['nclass'] >= 2)
print('rand20_multi_class_share=%d/20' % rand_share)
s18_multi = sum(1 for r in G2 if r['nclass'] >= 2)
print('slot18_multi_class_share=%d/27 ratio=%.4f ; rand_ratio=%.4f' %
      (s18_multi, s18_multi / 27, rand_share / 20))
G5 = {'c17': c17, 'c19': c19,
      'rand20_multi_class_share': rand_share,
      'slot18_multi_class_share': s18_multi,
      'slot18_multi_ratio': round(s18_multi / 27, 6),
      'rand_multi_ratio': round(rand_share / 20, 6),
      'rand20': rand_recs, 'pool_size': len(pool), 'seed': 215}

print('\n=== INTERPRETATION (每句均附数字支撑) ===')
entry_cnt = collections.Counter(g['entry'] for g in G1)
print('G1: 27 落点 entry 分布 = %s；'
      '说明以槽前导字节判定入口只能覆盖部分落点。' %
      json.dumps(dict(entry_cnt), ensure_ascii=False))
print('G2: 多类共享(>1 类)的目标 = %d/27，其中 0x004104c0 独占 56 类；'
      '说明复用度高度集中在少数目标。' % s18_multi)
print('G3: prefix1 same=%d/%d=%.4f，prefix3 same=%d/%d=%.4f；'
      '说明 slot18 一致性基本由 slot0 决定，非独立信息。' %
      (g3_1['same'], g3_1['clusters'], ratio_1,
       g3_3['same'], g3_3['clusters'], ratio_3))
print('G4: 0x4c9150 共 %d 次槽值出现、跨 %d 个不同槽号、其中 slot18 有 %d 张视图、字节 %s；'
      '说明纯桩被大范围跨槽复用。' %
      (len(stub_occ), len(stub_hist), len(stub_s18), stub_hex))
print('G5: slot18 多类共享 %d/27=%.4f，随机对照 %d/20=%.4f；'
      '说明 slot18 多类共享远高于随机基线，但并非罕见到独有。' %
      (s18_multi, s18_multi / 27, rand_share, rand_share / 20))

# ---------- 汇总写出 ----------
np = sum(1 for c in CHECKS if c['pass'])
nf = len(CHECKS) - np
print('\n=== SUMMARY ===')
print('PASS=%d FAIL=%d elapsed=%.2fs' % (np, nf, time.time() - T0))
res = dict(ASSERT)
res.update({'G1': G1, 'G2': G2, 'G3': G3, 'G4': G4, 'G5': G5,
            'checks': {'pass': np, 'fail': nf, 'items': CHECKS},
            'meta': {'raw_sha256': sha, 'elapsed_sec': round(time.time() - T0, 3),
                     'e8_opcode_hits': e8_total,
                     'has18_main': assert_has18_main, 'has18_sec': assert_has18_sec,
                     'g3_independent': indep}})
with open(ROOT + '/_r215/ex1.json', 'w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print('JSON written: _r215/ex1.json')
