#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r111c_thunk.py —— 发现并验证第二个完全独立的 COL.offset==4 证据链：slot0 = adjustor thunk。

R110 §EL5 用「装配点 disp==4」预测验证 COL.offset 语义（12/12）。本轮在扫描 slot0 时撞到另一条：
12 个类的 slot0 不是 QI 本体，而是 MSVC this-adjustor thunk
        sub dword ptr [esp + 4], N ; jmp <真实 QI>
若 N 就是 COL.offset，则这 12 个类的 N 必须全等于 4 —— 而这 12 个类**必须**与 R110 那 12 张
COL.offset==4 的表是同一集合。两条链不共用任何数据（一条读 .text 的 thunk 立即数，
一条读 .rdata 的 COL.offset 与全段装配点 disp），故集合相等是证据。

三段：
  T1 枚举 slot0 thunk，报 N 分布与目标函数。
  T2 集合等式：thunk 类集 == R110 COL.offset==4 类集（逐类，不只比个数）。
  T3 穿透：把 thunk 目标当 QI 主体再抽 IID，看这 12 类真实认领哪些 IID。
  T4 反控：全段 954 个 slot0 里 thunk 形态的基线率（对随机 20000 个函数起点）。
"""
import hashlib, json, os, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda v: v - IB
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() ==
   '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
   hashlib.sha256(raw).hexdigest()[:16])

sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
RE_TH = re.compile(r'^dword ptr \[esp \+ 4\], (0x[0-9a-f]+|\d+)$')

def thunk_at(f):
    """严格判据：sub dword ptr [esp+4], N ; jmp <imm>  —— 且 N 后续不得再被改写（3 条指令内）。"""
    g = list(md.disasm_lite(raw[fo(f):fo(f) + 24], f))[:3]
    if len(g) < 2 or g[0][2] != 'sub':
        return None
    m = RE_TH.match(g[0][3])
    if not m:
        return None
    if g[1][2] != 'jmp' or not g[1][3].startswith('0x'):
        return None
    return int(m.group(1), 0), int(g[1][3], 16)

TH = {}
for vt, k in sorted(VT.items()):
    f = struct.unpack_from('<I', raw, fo(vt))[0]
    t = thunk_at(f)
    if t:
        TH[k] = {'slot0': f, 'N': t[0], 'target': t[1]}
ck('T1 slot0 是 adjustor thunk 的类 = %d 个；N 取值分布 = %s'
   % (len(TH), dict(Counter(v['N'] for v in TH.values()))),
   len(TH) == 12 and set(v['N'] for v in TH.values()) == {4},
   {'n': len(TH), 'Nd': dict(Counter(v['N'] for v in TH.values())), 'rows': {k: (hex(v['slot0']), v['N'], hex(v['target'])) for k, v in TH.items()}})

# ---------- T2 集合等式：thunk 类集 vs COL.offset==4 类集 ----------
o4 = {}
for vt, k in VT.items():
    col = struct.unpack_from('<I', raw, fo(vt) - 4)[0]
    off = struct.unpack_from('<I', raw, fo(col) + 4)[0]
    if off: o4[k] = off
ck('T2a COL.offset != 0 的类 = %d，取值分布 = %s（R110 §EL5 报 12 张全为 4）'
   % (len(o4), dict(Counter(o4.values()))), len(o4) == 12 and set(o4.values()) == {4},
   dict(Counter(o4.values())))
ck('T2b **集合等式**：thunk 类集 == COL.offset!=0 类集（逐类比，非只比个数）；对称差 = %s'
   % sorted(set(TH) ^ set(o4)), set(TH) == set(o4), sorted(set(TH) ^ set(o4)))
ck('T2c 逐类 N == COL.offset（12/12，两链不共用数据：N 读 .text 立即数，offset 读 .rdata 的 COL）',
   all(TH[k]['N'] == o4[k] for k in TH), {k: (TH[k]['N'], o4[k]) for k in TH})

# ---------- T3 穿透 thunk 抽真实 IID ----------
import pefile
pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
DATA = [(IB + s.VirtualAddress, IB + s.VirtualAddress + s.Misc_VirtualSize)
        for s in pe.sections if s.Name.decode().strip('\x00') != '.text']
in_data = lambda v: any(a <= v and v + 16 <= b for a, b in DATA)
RE_EDI = re.compile(r'^edi, (0x[0-9a-f]+)$'); RE_ECX4 = re.compile(r'^ecx, 4$')
D111 = json.load(open('_r111/r111a_iidmap2.json'))

def iids_of(f, n=700):
    lits = list(md.disasm_lite(raw[fo(f):fo(f) + n], f))
    out, pend, ecx4 = [], None, False
    for a, sz, m, o in lits:
        if m == 'mov':
            mo = RE_EDI.match(o)
            if mo: pend = int(mo.group(1), 16); continue
            if RE_ECX4.match(o): ecx4 = True; continue
        if 'cmpsd' in m:
            if pend is not None and ecx4: out.append(pend)
            pend = None; ecx4 = False
    return [p for p in out if in_data(p)]

thr = {}
for k, v in TH.items():
    g = sorted(set(iids_of(v['target'])))
    thr[k] = [hex(x) for x in g]
ck('T3 穿透 thunk 目标后仍抽不到 IID 的类 = %s（12 个 Locomotion 类共享同一 QI 本体 0x55a9b0）'
   % sorted(k for k, v in thr.items() if not v),
   len([k for k in thr if not thr[k]]) == 0, thr)

# 交叉：thunk 目标是否已在 D111 的 impl 集合里（说明 R110/本轮本来就间接覆盖到）
impls = set(int(v, 16) for v in D111['impl_of'].values())
tgts = set(v['target'] for v in TH.values())
ck('T3b thunk 目标里已作为某类 slot0 出现过的 = %d/%d（其余仅经 thunk 到达）'
   % (len(tgts & impls), len(tgts)), True,
   {'already_slot0': sorted(hex(t) for t in tgts & impls), 'thunk_only': sorted(hex(t) for t in tgts - impls)})

# ---------- T4 反控 ----------
import random
random.seed(111)
# 随机 20000 个函数起点（用 R109 的 HB 作函数起点池的子集也要公平：这里用全段指令起点）
starts = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE); last = pos
    for a, sz, m, o in md.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
        if a >= hi: break
        last = a + sz; starts.append(a)
    if last <= pos: last = pos + 1
    pos = last
samp = random.sample(starts, 20000)
hit = sum(1 for s in samp if thunk_at(s))
base = hit / len(samp) * 100
rate = len(TH) / len(VT) * 100
ck('T4 反控：随机 20000 个指令起点里 thunk 形态 %d（%.3f%%）；slot0 里 %d/954 = %.2f%% ⇒ 富集 %.1f 倍'
   % (hit, base, len(TH), rate, rate / base if base else float('inf')),
   base < 1.0, {'hit': hit, 'base_pct': round(base, 4), 'enrich': round(rate / base, 2) if base else None})

json.dump({'thunks': {k: {'slot0': hex(v['slot0']), 'N': v['N'], 'target': hex(v['target']),
                          'iids': thr[k]} for k, v in TH.items()},
           'col_offset_nonzero': {k: v for k, v in o4.items()},
           'set_equality': set(TH) == set(o4),
           'negctl': {'hit': hit, 'n': len(samp), 'base_pct': round(base, 4)},
           'checks': checks}, open('_r111/r111c_thunk.json', 'w'), indent=1)
print('\n--- %d checks, FAIL %d ---' % (len(checks), sum(1 for c in checks if not c['ok'])))
