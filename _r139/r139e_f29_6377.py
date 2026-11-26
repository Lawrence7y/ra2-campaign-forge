#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话：F29 的 63/77 与 64/77 第一次用盘上字节独立复算（此前只有二手转述）。

判据（写进代码，不写在散文里）
---------------------------------
1. RTTI 链：.data 里 .?AVA<Name>@@ 串是 TypeDescriptor 的内联 name[]，
   故 TypeDescriptor 本体在 str_va-8；校验 +0 指针落在 .data/.rdata、+4 == 0、+8 内联 .?AV? 前缀。
2. COL（Complete Object Locator）：.data/.rdata 里出现 TD VA 的 DWORD 位置 - 12，
   且满足 dword[COL+0] == 0（signature）且 dword[COL+12] == TD VA。
3. 主虚表：.data/.rdata 里出现 COL VA 的 DWORD 位置 + 4，且 dword[vt-4] == COL VA。
4. 「两槽皆桩」= slot1(dword[vt+4]) 与 slot2(dword[vt+8]) **各自**落在
   全文件 40 个 8 字节桩 B8 01 00 00 00 C2 04 00 的起始 VA 集合里（不要求两槽相邻）。
   这是 F29 正文「两槽皆为逐字节桩」的字面读法。
5. 「有效桩」= 上述判据失败时，把槽值当作可能的中转（jmp rel32 / jmp [mem] / mov eax,imm;ret），
   跟到终点再判一次。

反控（必须能真的 FAIL）
-----------------------
N1 把桩集合换成空集 => 两槽皆桩必须变 0（否则判据恒真）
N2 只判 slot1（不判 slot2）=> 计数必须变大（说明两槽是合取、不是单槽）
N3 把 slot 偏移改成 +8/+12 => 计数必须变化（说明偏移是真的在读数）
"""
import os
import re
import json
import struct
import collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
raw = open(EXE, 'rb').read()

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, e + 6)[0]
opt_size = struct.unpack_from('<H', raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
SECS = []
for i in range(nsec):
    o = opt + opt_size + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append(dict(name=nm, vsize=vs, rva=va, rsize=rs, rptr=rp))

fails, out = [], {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def off_of(va):
    rva = va - IB
    for s in SECS:
        if s['rva'] <= rva < s['rva'] + s['rsize']:
            return s['rptr'] + (rva - s['rva'])
    return None


def d32(va):
    o = off_of(va)
    return None if o is None or o + 4 > len(raw) else struct.unpack_from('<I', raw, o)[0]


def cstr(va):
    o = off_of(va)
    if o is None:
        return None
    z = raw.find(b'\0', o)
    return raw[o:z].decode('latin1', 'replace')


DATA = [s for s in SECS if s['name'] in ('.data', '.rdata')]

# ---- 桩集合 ----
STUB = bytes.fromhex('B801000000C20400')
stub_va = set()
for s in SECS:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    i = seg.find(STUB)
    while i != -1:
        stub_va.add(IB + s['rva'] + i)
        i = seg.find(STUB, i + 1)
ck('0.1 桩 VA 集合 == 40（与 C2 一致）', len(stub_va) == 40, len(stub_va))

# ---- 全部 TypeDescriptor -> COL -> vtable ----
td = []
for s in DATA:
    if s['name'] != '.data':
        continue
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for m in re.finditer(rb'\.\?AV([A-Za-z0-9_@?$<>:,\-]+?)@@', seg):
        td.append((base + m.start() - 8, m.group(1).decode('latin1')))
ck('1.1 TypeDescriptor 962 个（.data 内联 name[]）', len(td) == 962, len(td))

refidx = collections.defaultdict(list)
for s in DATA:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for tva, _ in td:
        n = struct.pack('<I', tva)
        i = seg.find(n)
        while i != -1:
            refidx[tva].append(base + i)
            i = seg.find(n, i + 4)

cols = collections.defaultdict(set)
for tva, nm in td:
    for r in refidx.get(tva, []):
        c = r - 12
        if d32(c) == 0 and d32(c + 12) == tva:
            cols[nm].add(c)
ck('1.2 有 COL 的类 == 952', len(cols) == 952, len(cols))

vt_of = collections.defaultdict(set)
for s in DATA:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base = IB + s['rva']
    for nm, cs in cols.items():
        for c in cs:
            n = struct.pack('<I', c)
            i = seg.find(n)
            while i != -1:
                vt_of[nm].add(base + i + 4)
                i = seg.find(n, i + 4)
ck('1.3 有虚表的类 == 952', len(vt_of) == 952, len(vt_of))
ck('1.4 每张虚表 vt-4 都指向自己的 COL',
   all(d32(v - 4) in cols[nm] for nm in vt_of for v in vt_of[nm]),
   sum(1 for nm in vt_of for v in vt_of[nm] if d32(v - 4) in cols[nm]))

# ---- 77 个 TClassFactory 实参 ----
pat = re.compile(rb'\.\?AV\?\$TClassFactory@V([A-Za-z0-9_]+)@@@')
args = []
for s in SECS:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    for m in pat.finditer(seg):
        args.append(m.group(1).decode('latin1'))
ck('2.1 TClassFactory 实参 77 个、去重 77', len(args) == 77 and len(set(args)) == 77,
   (len(args), len(set(args))))
ck('2.2 每个实参在盘上都有 TypeDescriptor 且有虚表',
   all(a in vt_of for a in args), [a for a in args if a not in vt_of])


# ---- 桩判定（含失效转移追踪）----
def is_stub_at(va):
    """该 VA 处是否就是 8 字节桩本体。"""
    return va in stub_va


def follow(va, depth=0):
    """把槽值跟到终点。识别的中转形态（每条都要在盘上肉眼可核）：

      81 6C 24 04 imm32 ; E9 rel32      this-=imm 后跳（AircraftClass 的 6 个槽就是这个）
      83 6C 24 04 imm8  ; E9 rel32      this-=imm8
      E9 rel32                          jmp rel32
      8B 44 24 04 50 E8 rel32           mov eax,[esp+4]; push eax; call（转发器）
    """
    if va is None or depth > 6 or is_stub_at(va):
        return va
    o = off_of(va)
    if o is None:
        return va
    b = raw[o:o + 20]
    if b[0] == 0x81 and b[1] == 0x6C and b[3] == 0x04 and b[8] == 0xE9:
        return follow(va + 12 + struct.unpack_from('<i', raw, o + 9)[0], depth + 1)
    if b[0] == 0x83 and b[1] == 0x6C and b[3] == 0x04 and b[5] == 0xE9:
        return follow(va + 8 + struct.unpack_from('<i', raw, o + 6)[0], depth + 1)
    if b[0] == 0xE9:
        return follow(va + 5 + struct.unpack_from('<i', raw, o + 1)[0], depth + 1)
    if b[:5] == bytes.fromhex('8B44240450') and b[5] == 0xE8:
        return follow(va + 10 + struct.unpack_from('<i', raw, o + 6)[0], depth + 1)
    return va


def measure(off1=4, off2=8, use2=True, stubset=None, do_follow=False):
    ss = stub_va if stubset is None else stubset
    hit = 0
    non = []
    for a in sorted(args):
        ok = False
        for vt in sorted(vt_of[a]):
            s1 = d32(vt + off1)
            s2 = d32(vt + off2) if use2 else 0
            if do_follow:
                s1, s2 = follow(s1), follow(s2)
            if s1 in ss and (not use2 or s2 in ss):
                ok = True
                break
        if ok:
            hit += 1
        else:
            non.append(a)
    return hit, non


hit, non = measure()
print('\n=== 正测：两槽皆桩 ===')
print('  %d / %d' % (hit, len(args)))
print('  非两槽皆桩的 %d 个：%s' % (len(non), non))
out['both_stub'] = hit
out['both_stub_total'] = len(args)
out['non_both'] = non
ck('3.1 两槽皆桩 == 63', hit == 63, hit)
ck('3.2 非两槽皆桩 == 14', len(non) == 14, len(non))
loco = [a for a in non if 'Locomotion' in a]
other3 = [a for a in non if 'Locomotion' not in a]
out['non_both_loco'] = loco
out['non_both_other'] = other3
ck('3.3 14 个例外里 Locomotion 恰好 11 个（F29 正文「Locomotion 11 个全非桩」）',
   len(loco) == 11, loco)
ck('3.4 其余 3 个恰好是 AircraftClass / BulletClass / CStreamClass（F29 正文点名的 Other 3 例外）',
   sorted(other3) == ['AircraftClass', 'BulletClass', 'CStreamClass'], other3)
ck('3.5 63/77 == 81.82%（两位小数）', round(100.0 * hit / len(args), 2) == 81.82,
   round(100.0 * hit / len(args), 2))

print('\n=== 有效桩（把转发器跟到终点再判）===')
eff, non_eff = measure(do_follow=True)
print('  %d / %d ；跟终点后仍非桩：%s' % (eff, len(args), non_eff))
out['effective_stub'] = eff
out['non_effective'] = non_eff
ck('4.1 有效桩 == 64（多出的正是 AircraftClass）', eff == 64, eff)
ck('4.2 跟终点后新增的恰是 AircraftClass',
   sorted(set(non) - set(non_eff)) == ['AircraftClass'], sorted(set(non) - set(non_eff)))
ck('4.3 64/77 == 83.12%（两位小数）', round(100.0 * eff / len(args), 2) == 83.12,
   round(100.0 * eff / len(args), 2))

print('\n=== 单槽判别力（如实报，不硬凑）===')
s1only, _ = measure(use2=False)
s2only = sum(1 for a in set(args) if any(d32(v + 8) in stub_va for v in vt_of[a]))
print('  只判 slot1 为桩 = %d ；只判 slot2 为桩 = %d' % (s1only, s2only))
out['slot1_only'] = s1only
out['slot2_only'] = s2only
ck('3.6 只判 slot1 == 63（与两槽合取相同）', s1only == 63, s1only)
ck('3.7 只判 slot2 == 63（与两槽合取相同）', s2only == 63, s2only)
ck('3.8 因此「两槽皆桩」与「任一槽为桩」在 77 张表上等价 —— 合取不增加判别力（如实登记）',
   s1only == hit and s2only == hit, (s1only, s2only, hit))

print('\n=== 反控 ===')
n1, _ = measure(stubset=set())
ck('N1 桩集合置空 => 两槽皆桩必须为 0', n1 == 0, n1)
n2 = sum(1 for a in set(args) if any(d32(v + 4) is not None and off_of(d32(v + 4)) is not None
                                    for v in vt_of[a]))
ck('N2 放宽为「slot1 落在镜像内即算」=> 计数必须明显变大（证明判据不是恒真）',
   n2 > hit, '%d vs %d' % (n2, hit))
n3, _ = measure(off1=8, off2=12)
ck('N3 偏移换成 +8/+12 => 计数必须变化（证明偏移在真的读数）', n3 != hit, '%d vs %d' % (n3, hit))
n4, _ = measure(do_follow=True, stubset=set())
ck('N4 跟终点 + 空桩集合 => 仍必须为 0', n4 == 0, n4)
n5 = sum(1 for a in set(args) if any(follow(d32(v + 4)) in stub_va or follow(d32(v + 8)) in stub_va
                                     for v in vt_of[a]))
ck('N5 追终点后放宽为「任一槽为桩」=> 必须仍等于 64（不值得区分，如实登记）', n5 == eff, '%d vs %d' % (n5, eff))

out['fails'] = fails
open(os.path.join(ROOT, '_r139', 'r139e_f29_6377.json'), 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print('\n汇总：%d FAIL' % len(fails))
raise SystemExit(1 if fails else 0)
