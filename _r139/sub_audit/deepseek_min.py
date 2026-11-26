#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 审计最小复算器：一行一数，只读 gamemd.exe。用法 python3 min.py"""
import struct, re, collections, math
raw = open('/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe', 'rb').read()
e = struct.unpack_from('<I', raw, 0x3c)[0]
opt = e + 24
nsec = struct.unpack_from('<H', raw, e + 6)[0]
optsz = struct.unpack_from('<H', raw, e + 20)[0]
IB = struct.unpack_from('<I', raw, opt + 28)[0]
S = []
for i in range(nsec):
    o = opt + optsz + i * 40
    vs, va, rs, rp = struct.unpack_from('<IIII', raw, o + 8)
    S.append((raw[o:o + 8].rstrip(b'\0').decode(), IB + va, vs, rp, rs,
              struct.unpack_from('<I', raw, o + 36)[0]))
def off(va):
    for n, b, vs, rp, rs, ch in S:
        if b <= va < b + rs:
            return rp + va - b
def d32(va):
    o = off(va)
    return None if o is None or o + 4 > len(raw) else struct.unpack_from('<I', raw, o)[0]
def xc(va):
    for n, b, vs, rp, rs, ch in S:
        if b <= va < b + vs:
            return bool(ch & 0x20000000)
D = [x for x in S if x[0] in ('.data', '.rdata')]
td = {}
for n, b, vs, rp, rs, ch in S:
    for m in re.finditer(rb'\.\?AV([A-Za-z0-9_@?$<>:,\-]+?)@@', raw[rp:rp + rs]):
        td[b + m.start() - 8] = m.group(1).decode()
VI = collections.defaultdict(list)
for n, b, vs, rp, rs, ch in D:
    for i in range(rs - 3):
        VI[struct.unpack_from('<I', raw, rp + i)[0]].append(b + i)
COL = collections.defaultdict(set)
for t, nm in td.items():
    for r in VI.get(t, ()):
        if d32(r - 12) == 0:
            COL[nm].add(r - 12)
CAND = collections.defaultdict(list)
for nm, cs in COL.items():
    for c in cs:
        for p in VI.get(c, ()):
            if d32(p) == c:
                CAND[nm].append((p + 4, d32(c + 4)))
SS = {b + i for n, b, vs, rp, rs, ch in S for i in [m.start() for m in re.finditer(re.escape(bytes.fromhex('B801000000C20400')), raw[rp:rp + rs])]}
ARGS = sorted(set(m.group(1).decode() for n, b, vs, rp, rs, ch in S
                  for m in re.finditer(rb'\.\?AV\?\$TClassFactory@V([A-Za-z0-9_]+)@@@', raw[rp:rp + rs])))
def stub2(vt): return d32(vt + 4) in SS and d32(vt + 8) in SS
def main_vt(a):
    return max([x for x in CAND[a] if x[1] == 0], key=lambda x: (
        sum(1 for k in range(300) if xc(d32(x[0] + 4 * k) or 0)), -x[0]))
def fol(va, b81, b83, d=0):
    if va is None or d > 6 or va in SS: return va
    o = off(va)
    if o is None: return va
    q = raw[o:o + 24]
    if q[0] == 0x81 and q[1:4] == b'\x6c\x24\x04' and q[8] == 0xE9:
        return fol(va + b81 + struct.unpack_from('<i', raw, o + 9)[0], b81, b83, d + 1)
    if q[0] == 0x83 and q[1:4] == b'\x6c\x24\x04' and q[5] == 0xE9:
        return fol(va + b83 + struct.unpack_from('<i', raw, o + 6)[0], b81, b83, d + 1)
    if q[0] == 0xE9: return fol(va + 5 + struct.unpack_from('<i', raw, o + 1)[0], b81, b83, d + 1)
    if q[:5] == bytes.fromhex('8B44240450') and q[5] == 0xE8:
        return fol(va + 10 + struct.unpack_from('<i', raw, o + 6)[0], b81, b83, d + 1)
    return va
fam = lambda a: 'Locomotion' if a.endswith('LocomotionClass') else ('TypeClass' if a.endswith('TypeClass') else 'Other')
lab = {a: stub2(main_vt(a)[0]) for a in ARGS}
print('A1  TD=str-8 且+4==0 :', sum(1 for t in td if d32(t + 4) == 0), '/', len(td),
      '| 反证(str-16)+12自指:', sum(1 for t in td if d32(t - 8 + 12) == t + 8))
print('A2  COL类(.?AV)=', len(COL), ' 每类mdisp==0候选数分布=', dict(collections.Counter(sum(1 for x in CAND[n] if x[1] == 0) for n in COL)),
      ' 候选vt唯一=', sum(1 for n in COL if len(CAND[n]) == 1), ' 候选vt总数=', sum(len(v) for v in CAND.values()))
print('A3  63/77 双槽皆桩(真实主表)=', sum(lab.values()), '/', len(ARGS))
print('A4  AircraftClass 主表 0x%08X slot1=0x%08X %s slot2=0x%08X %s ; fix跟终点=%s,%s' % (
    main_vt('AircraftClass')[0], d32(main_vt('AircraftClass')[0] + 4),
    raw[off(d32(main_vt('AircraftClass')[0] + 4)):off(d32(main_vt('AircraftClass')[0] + 4)) + 13].hex(),
    d32(main_vt('AircraftClass')[0] + 8),
    raw[off(d32(main_vt('AircraftClass')[0] + 8)):off(d32(main_vt('AircraftClass')[0] + 8)) + 13].hex(),
    hex(fol(d32(main_vt('AircraftClass')[0] + 4), 13, 10)), hex(fol(d32(main_vt('AircraftClass')[0] + 8), 13, 10))))
eff = lambda b81, b83: sum(1 for a in ARGS if fol(d32(main_vt(a)[0] + 4), b81, b83) in SS and fol(d32(main_vt(a)[0] + 8), b81, b83) in SS)
print('A4  有效桩 正确基址(+13/+10)=%d  主会话基址(+12/+8)=%d' % (eff(13, 10), eff(12, 8)))
print('A4  81形态基址差: 0x41C680 main跳=', hex(fol(0x41C680, 12, 8)), ' fix跳=', hex(fol(0x41C680, 13, 10)),
      ' | capstone: 81 6C 24 04 imm32 长 8 + E9 长 5 = 13')
g = collections.defaultdict(lambda: [0, 0])
for a in ARGS:
    g[fam(a)][0 if lab[a] else 1] += 1
print('A5  族 (n,桩,非桩) =', {k: (v[0] + v[1], v[0], v[1]) for k, v in g.items()},
      ' 多数派=', sum(max(v) for v in g.values()))
sz = [g[k][0] + g[k][1] for k in ('Locomotion', 'TypeClass', 'Other')]
print('A6  解析 P(stat>=74)=%.3e ; 该统计量在块 %s、非桩14 下的全域最大值=%d' % (
    math.comb(11, 11) * math.comb(66, 3) / math.comb(77, 14), sz,
    max(max(k1, 11 - k1) + max(k2, 22 - k2) + max(14 - k1 - k2, 44 - (14 - k1 - k2))
        for k1 in range(12) for k2 in range(15 - k1) if 14 - k1 - k2 <= 44)))
print('A6  stat 只依赖三个 (n_f,k_f) 数对：74 = 11 + 22 + 41 = 上限')
dm = [va for va in SS if raw[off(va) - 4:off(va)] != b'\x90' * 4 or raw[off(va) + 8:off(va) + 12] != b'\x90' * 4]
print('A7  40 桩中「非独立函数体」(前后非 90909090) =', len(dm), '/', len(SS), ' 例:', [hex(v) for v in sorted(dm)[:3]])
pc = collections.Counter()
for a in ARGS:
    for vt, md in CAND[a]:
        if stub2(vt): pc[(d32(vt + 4), d32(vt + 8))] += 1
print('A7  63 用的桩对 =', [(hex(k[0]), hex(k[1]), v) for k, v in pc.most_common()])
print('A7  候选虚表 298 个中 slot 落非 .text =', sum(1 for a in ARGS for vt, md in CAND[a] if not xc(d32(vt + 4) or 0) or not xc(d32(vt + 8) or 0)))
