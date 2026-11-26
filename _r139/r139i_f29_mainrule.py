#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话：校验 F29 limitations 里那句**此前从未被验证过**的限定语。

待验原句（v5.33/v5.34 的 F29 limitations 已写，R139 之前无人复算）：
  「主表规则（槽数最多 / mdisp==0）会改变 11/77 个产品的**槽地址**，
    但「双槽皆桩 = 63」两规则相同，故计数对规则不敏感、地址不能脱规则单引。」

三个可分别失败的主张：
  M1  两个规则（槽数最多 / mdisp==0）给出的主虚表在 **11/77** 个产品上不同
  M2  两条规则下的「两槽皆桩」计数**都等于 63**
  M3  结论「计数对规则不敏感、地址不能脱规则单引」⇒ M1 与 M2 同时成立即得

口径（写进代码）
  * 槽数 = 从 vt 起连续落在 .text 的 dword 个数（虚表槽必须是代码指针），上限 256
  * mdisp = dword[COL+4]；mdisp==0 即「该虚表是自己的主表」
  * 「两槽皆桩」= dword[vt+4] 与 dword[vt+8] **各自**在 40 个 8 字节桩的起始 VA 集合里
"""
import os
import re
import json
import struct
import collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
raw = open(os.path.join(ROOT, 'ra2bench', 'gamemd.exe'), 'rb').read()

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, e + 6)[0]
osz = struct.unpack_from('<H', raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
S = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', raw, o + 8)
    S.append(dict(name=nm, rva=va, rsize=rs, rptr=rp))

fails, out = [], []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def off(va):
    r = va - IB
    for s in S:
        if s['rva'] <= r < s['rva'] + s['rsize']:
            return s['rptr'] + (r - s['rva'])
    return None


def d32(va):
    o = off(va)
    return None if o is None or o + 4 > len(raw) else struct.unpack_from('<I', raw, o)[0]


STUB = bytes.fromhex('B801000000C20400')
stub = set()
for s in S:
    b = raw[s['rptr']:s['rptr'] + s['rsize']]
    i = b.find(STUB)
    while i != -1:
        stub.add(IB + s['rva'] + i)
        i = b.find(STUB, i + 1)
ck('0.1 桩集合 40', len(stub) == 40, len(stub))

TEXTSEC = [s for s in S if s['name'] == '.text'][0]
TLO, THI = IB + TEXTSEC['rva'], IB + TEXTSEC['rva'] + TEXTSEC['rsize']

# ---- RTTI -> COL -> 虚表（与 r139e 同一判据，但此处保留**全部**虚表，不挑一张）----
DATA = [s for s in S if s['name'] in ('.data', '.rdata')]
sd = [s for s in S if s['name'] == '.data'][0]
b = raw[sd['rptr']:sd['rptr'] + sd['rsize']]
bs = IB + sd['rva']
td = [(bs + m.start() - 8, m.group(1).decode('latin1'))
      for m in re.finditer(rb'\.\?AV([A-Za-z0-9_@?$<>:,\-]+?)@@', b)]
ref = collections.defaultdict(list)
for s in DATA:
    sb = raw[s['rptr']:s['rptr'] + s['rsize']]
    bb = IB + s['rva']
    for t, _ in td:
        n = struct.pack('<I', t)
        i = sb.find(n)
        while i != -1:
            ref[t].append(bb + i)
            i = sb.find(n, i + 4)
cols = collections.defaultdict(list)
for t, nm in td:
    for r in ref.get(t, []):
        c = r - 12
        if d32(c) == 0 and d32(c + 12) == t and c not in cols[nm]:
            cols[nm].append(c)
vts = collections.defaultdict(list)
for s in DATA:
    sb = raw[s['rptr']:s['rptr'] + s['rsize']]
    bb = IB + s['rva']
    for nm, cs in cols.items():
        for c in cs:
            n = struct.pack('<I', c)
            i = sb.find(n)
            while i != -1:
                v = bb + i + 4
                if d32(v - 4) == c and v not in vts[nm]:
                    vts[nm].append(v)
                i = sb.find(n, i + 4)

args = sorted(set(m.group(1).decode('latin1')
                  for m in re.finditer(rb'\.\?AV\?\$TClassFactory@V([A-Za-z0-9_]+)@@@', raw)))
ck('1.1 77 个 TClassFactory 实参', len(args) == 77, len(args))
ck('1.2 每个实参都有虚表', all(vts[a] for a in args),
   [a for a in args if not vts[a]])


def mdisp(c):
    return d32(c + 4)


def slotcount(vt):
    n = 0
    while n < 256:
        v = d32(vt + 4 * n)
        if v is None or not (TLO <= v < THI):
            break
        n += 1
    return n


bothA = bothB = 0
diff = []
for a in args:
    L = vts[a]
    m0 = [v for v in L if mdisp(d32(v - 4)) == 0]
    mainB = m0[0] if m0 else None
    mainA = sorted(L, key=lambda v: (-slotcount(v), v))[0]
    sA = (d32(mainA + 4), d32(mainA + 8))
    sB = (d32(mainB + 4), d32(mainB + 8)) if mainB is not None else None
    if sA[0] in stub and sA[1] in stub:
        bothA += 1
    if sB and sB[0] in stub and sB[1] in stub:
        bothB += 1
    if mainA != mainB:
        diff.append((a, hex(mainA), slotcount(mainA), hex(mainB),
                     slotcount(mainB) if mainB else 0))

print('\n=== M1 两个规则的主表是否不同 ===')
print('  不同 %d / 77' % len(diff))
for d in diff:
    print('    %-26s 槽数最多=%-10s(%d 槽)  mdisp0=%-10s(%d 槽)' % d)
ck('M1.1 两规则主表不同的产品恰为 11 个', len(diff) == 11, len(diff))
ck('M1.2 不同者不是空集也不是全部（判据有分辨力）', 0 < len(diff) < 77, len(diff))

print('\n=== M2 两条规则下的 63 计数 ===')
print('  槽数最多规则 = %d / 77' % bothA)
print('  mdisp==0 规则 = %d / 77' % bothB)
ck('M2.1 槽数最多规则 == 63', bothA == 63, bothA)
ck('M2.2 mdisp==0 规则 == 63', bothB == 63, bothB)
ck('M2.3 两规则计数相同（F29 正文「计数对规则不敏感」）', bothA == bothB, (bothA, bothB))

print('\n=== M3 结论 ===')
ck('M3.1 「改变 11/77 个产品的槽地址」与「63 两规则相同」同时成立 ⇒ 原句可保留',
   len(diff) == 11 and bothA == 63 and bothB == 63, (len(diff), bothA, bothB))

print('\n=== 反控 ===')
# N1: 若把 mdisp 判据换成「地址最小」，主表变化数必须不为 11
d2 = []
for a in args:
    L = vts[a]
    m0 = [v for v in L if mdisp(d32(v - 4)) == 0]
    mainB = m0[0] if m0 else None
    mainLow = min(L)
    if mainB is not None and mainLow != mainB:
        d2.append(a)
ck('N1 反控：把规则换成「地址最小」时分歧数 != 11（说明 11 这个数对规则敏感）',
   len(d2) != 11, len(d2))
# N2: 若槽数口径改成「不检查是否落在 .text」，分歧数必须变化
def slotcount2(vt):
    n = 0
    while n < 256:
        v = d32(vt + 4 * n)
        if v is None or v == 0:
            break
        n += 1
    return n
d3 = 0
for a in args:
    L = vts[a]
    m0 = [v for v in L if mdisp(d32(v - 4)) == 0]
    mainB = m0[0] if m0 else None
    mainA = sorted(L, key=lambda v: (-slotcount2(v), v))[0]
    if mainB is not None and mainA != mainB:
        d3 += 1
ck('N2 反控：槽数口径不校验「落 .text」时分歧数变化（槽数定义承重）',
   d3 != len(diff), '%d vs %d' % (d3, len(diff)))
# N3: 桩集合置空 => 两个计数都必须为 0
EMPTY = set()
n3 = 0
for a in args:
    mainA = sorted(vts[a], key=lambda v: (-slotcount(v), v))[0]
    if d32(mainA + 4) in EMPTY and d32(mainA + 8) in EMPTY:
        n3 += 1
ck('N3 反控：桩集合置空则两计数必为 0（不是恒 63）', n3 == 0, n3)

out = dict(diff_count=len(diff), diff=diff, both_slotcount=bothA, both_mdisp=bothB,
           fails=fails)
open(os.path.join(ROOT, '_r139', 'r139i_f29_mainrule.json'), 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print('\n汇总：%d FAIL' % len(fails))
raise SystemExit(1 if fails else 0)
