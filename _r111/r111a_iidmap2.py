#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r111a_iidmap2.py —— 重做 R110 的 IID 映射，修正其「函数头 120 B 截断」缺陷。

R110 判据：slot0 函数体**头 120 B** 内按序 mov ecx,4 -> mov edi,<imm32> -> ... -> repe cmpsd。
该窗口是为压反控基线（自错 L-02 的补丁）引入的，但它同时**截断了多接口类的后半段 IID**。
本轮改成按**函数真实终点**（HB 边界，R109 §EK9 已证 HB 是唯一可靠边界）抽取，并用同一函数终点
做反控（公平比较），而不是靠缩短窗口压基线。

断言要求：
  A1 逐类：R110 抽到的 IID 集合必须是本轮集合的**子集**（若 R110 有本轮没有的，说明本轮丢了东西）。
  A2 反控 20000 随机起点（同判据、同函数终点）基线率与富集倍数。
  A3 所有 IID 指针必须落 PE 数据节，且 16 字节内容去重与指针去重必须双射。
  A4 正控：0x7f7c90 == IUnknown。
内存纪律：全部 disasm_lite；函数体内按指令迭代，单函数上限 1500 条指令；不 detail。
"""
import bisect, hashlib, json, os, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda v: v - IB
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

ck('S0 exe sha256 == R110 同口径', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])

# ---------- 节表（从 PE 头现读） ----------
pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
SECT = [(s.Name.decode().strip('\x00'), IB + s.VirtualAddress,
         IB + s.VirtualAddress + s.Misc_VirtualSize) for s in pe.sections]
T = [x for x in SECT if x[0] == '.text'][0]
ck('S0b .text = [%s, %s)' % (hex(T[1]), hex(T[2])), T[1] == TS and T[2] == TE, hex(T[2]))
DATA = [x for x in SECT if x[0] != '.text']
def in_data(v):
    return any(a <= v and v + 16 <= b for n, a, b in DATA)
def sec_of(v):
    for n, a, b in SECT:
        if a <= v < b: return n
    return None

sym = json.load(open('out/reverse/symbols.json'))
cls = sym['classes']
VT = {int(c['vtable_va'], 16): k for k, c in cls.items() if c.get('vtable_va')}
ck('S1 vtable 数 954（R107 EI3 同口径）', len(VT) == 954, len(VT))

# ---------- 全段线性扫描（disasm_lite，64 KB 分块）→ 指令起点集合 + ret 集合 ----------
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
starts, rets = [], []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        starts.append(a)
        if m == 'ret': rets.append(a)
        elif m.startswith('ret'): rets.append(a)
    if last <= pos: last = pos + 1
    pos = last
SSET = set(starts)
ck('S2 指令起点 %d / ret %d（全段 disasm_lite 分块）' % (len(starts), len(rets)),
   len(starts) > 1_000_000 and len(rets) > 0, (len(starts), len(rets)))

def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65):
        q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)

HB = set()
for r in sorted(rets):
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET:
        HB.add(q)
ck('S3 HB == 17766（r109e 同构造：ret 后填充对齐到 4 且落在指令起点）', len(HB) == 17766, len(HB))
HBS = sorted(HB)

# ---------- 抽取：按函数真实终点 ----------
RE_EDI = re.compile(r'^edi, (0x[0-9a-f]+)$')
RE_ECX4 = re.compile(r'^ecx, 4$')
def dis_fn(f, cap=1500):
    """从 f 起按指令迭代，遇到 HB 边界（≠f）即停。返回 (lits, 终止原因)。"""
    out = []
    a = f; n = 0
    while a < TE and n < cap:
        if a != f and a in HB:
            return out, 'HB'
        g = list(md.disasm_lite(raw[fo(a):fo(a) + 16], a))[:1]
        if not g:
            return out, 'bad'
        out.append(g[0]); a = g[0][0] + g[0][1]; n += 1
        if g[0][2].startswith('ret'):
            # ret 后若下一条是 HB ⇒ 函数结束；否则继续（早退 ret，R109 §E-f1）
            if a in HB or a >= TE:
                return out, 'ret'
    return out, 'cap'

def iids_from(lits):
    """返回 (iid_ptr_list, 首 cmpsd 指令序)。判据同 R110，但无 120 B 窗口。"""
    out = []; pend = None; ecx4 = False
    for a, sz, m, o in lits:
        if m == 'mov':
            mo = RE_EDI.match(o)
            if mo:
                pend = int(mo.group(1), 16); continue
            if RE_ECX4.match(o):
                ecx4 = True; continue
        if 'cmpsd' in m:
            if pend is not None and ecx4:
                out.append(pend)
            pend = None; ecx4 = False
    return out

R110 = json.load(open('_r110/r110a_iidmap.json'))
r110_rows = {r['cls']: r for r in R110['rows']}

QI = {}
impl_of = {}
for va, k in sorted(VT.items()):
    f = struct.unpack_from('<I', raw, fo(va))[0]
    if not (TS <= f < TE): continue
    lits, why = dis_fn(f)
    g = iids_from(lits)
    if not g: continue
    for p in g:
        if not in_data(p):
            print('  !! non-data IID ptr', k, hex(f), hex(p), sec_of(p))
    g = [p for p in g if in_data(p)]
    if not g: continue
    QI[k] = sorted(set(g))
    impl_of[k] = f

ck('A0 有 QI 的类数（R110 报 172）', len(QI) > 0, len(QI))
n_r110 = R110['n_qi_classes']
n_new = len(QI)
per = Counter(len(v) for v in QI.values())

# A1 R110 子集性
lost = []
for k, r in r110_rows.items():
    old = set(int(x['ptr'], 16) for x in r['iids'])
    new = set(QI.get(k, []))
    if not old <= new:
        lost.append((k, sorted(hex(x) for x in old - new)))
ck('A1 R110 逐类 IID 集合 ⊆ 本轮集合（违例 0；违例说明本轮丢东西）', len(lost) == 0, lost[:5])
gain = [(k, len(QI[k]) - len(r110_rows[k]['iids'])) for k in r110_rows if len(QI[k]) > len(r110_rows[k]['iids'])]
ck('A1b 被 120 B 窗口截断的类数 = %d（差额总和 %d 个 IID 实例）'
   % (len(gain), sum(g for _, g in gain)), len(gain) > 0,
   {'n_truncated': len(gain), 'sum_missing': sum(g for _, g in gain), 'worst': sorted(gain, key=lambda x: -x[1])[:6]})

ALL_IID = Counter()
for k, v in QI.items():
    for p in v: ALL_IID[p] += 1
distinct = sorted(ALL_IID)
def guid(va):
    d1, d2, d3 = struct.unpack_from('<IHH', raw, fo(va))
    b = raw[fo(va) + 8:fo(va) + 16]
    return '%08X-%04X-%04X-%s-%s' % (d1, d2, d3, b[:2].hex().upper(), b[2:].hex().upper())
ck('A2 distinct IID（R110 报 17）', len(distinct) > 0, {'n': len(distinct), 'r110': len(R110['iid_classes'])})
new_iids = [p for p in distinct if hex(p) not in R110['iid_classes']]
ck('A2b R110 漏掉的 distinct IID = %s' % [(hex(p), guid(p), ALL_IID[p]) for p in new_iids],
   True, [hex(p) for p in new_iids])

# A3 指针 vs 内容双射
by_content = defaultdict(list)
for p in distinct: by_content[raw[fo(p):fo(p) + 16]].append(p)
dup = {k.hex(): v for k, v in by_content.items() if len(v) > 1}
ck('A3 IID 指针去重与 16 字节内容去重双射（同内容多指针违例 0）', len(dup) == 0, dup)
ck('A3b 全部 IID 落数据节、0 个在 .text',
   all(in_data(p) for p in distinct) and all(sec_of(p) != '.text' for p in distinct),
   Counter(sec_of(p) for p in distinct))
ck('A4 正控 0x7f7c90 == IUnknown(00000000-0000-0000-C000-000000000046)',
   guid(0x7f7c90) == '00000000-0000-0000-C000-000000000046', guid(0x7f7c90))

# A5 反控：同判据、同函数终点
import random
random.seed(111)
cand = [a for a in starts if TS <= a < TE - 600]
samp = random.sample(cand, 20000)
hit = 0
detail_hits = []
for s in samp:
    lits, why = dis_fn(s, cap=600)
    g = iids_from(lits)
    g = [p for p in g if in_data(p)]
    if g:
        hit += 1
        if len(detail_hits) < 5: detail_hits.append((hex(s), why, [hex(x) for x in g[:3]]))
base = hit / len(samp) * 100
enrich = (n_new / len(VT) * 100) / base if base else float('inf')
ck('A5 反控随机 20000 起点命中 %d（%.3f%%）⇒ 富集 %.1f 倍' % (hit, base, enrich),
   hit < 2000, {'hit': hit, 'base_pct': round(base, 4), 'enrich': round(enrich, 2), 'eg': detail_hits})

out = {
    'n_qi_classes': n_new, 'n_qi_classes_r110': n_r110,
    'n_distinct_impl': len(set(impl_of.values())),
    'per_class_n_new': sorted(per.items()),
    'per_class_n_r110': R110['per_class_n'],
    'truncated': sorted([(k, len(QI[k]), len(r110_rows[k]['iids'])) for k in r110_rows
                         if len(QI[k]) > len(r110_rows[k]['iids'])], key=lambda x: -x[1]),
    'iid_n': {hex(p): ALL_IID[p] for p in distinct},
    'guid_of_ptr': {hex(p): guid(p) for p in distinct},
    'classes': {k: [hex(p) for p in v] for k, v in QI.items()},
    'impl_of': {k: hex(v) for k, v in impl_of.items()},
    'negctl': {'hit': hit, 'n': len(samp), 'base_pct': round(base, 4), 'enrich': round(enrich, 3), 'eg': detail_hits},
    'checks': checks,
}
json.dump(out, open('_r111/r111a_iidmap2.json', 'w'), indent=1)
print('\n--- %d checks, FAIL %d ---' % (len(checks), sum(1 for c in checks if not c['ok'])))
print('classes %d -> %d ; per_class %s -> %s ; distinct IID %d -> %d'
      % (n_r110, n_new, R110['per_class_n'], sorted(per.items()),
         len(R110['iid_classes']), len(distinct)))
print('truncated top:', out['truncated'][:8])
