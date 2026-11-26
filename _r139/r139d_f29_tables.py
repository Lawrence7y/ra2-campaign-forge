#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话：F29 的 63/77、64/77、74/77 第一次用**盘上字节**独立复算。

背景：F29 正文的这三个比例一直只有二手转述（triage 把 F29 判为「需重建」，
理由是 PANEL.md M71 披露不在盘）。本轮先按 RTTI 链把 77 张 TClassFactory 的
主虚表定位出来，再逐表读 slot1(+4)/slot2(+8) 的字节，看它们是否指向
那 40 处 8 字节桩（mov eax,1 / ret 4）。

链路（每步都可失败，不做任何假设）：
  TD(类型描述符 VA) --[.data 里出现该 VA 的 DWORD]--> COL_va = ref_va - 12
  COL 布局: +0 signature(0) / +4 offset / +8 cdOffset / +12 pTypeDescriptor / +16 pClassDescriptor
  校验 COL+12 == TD_va，并校验 signature == 0
  vtable 指针 --[.data/.rdata 里出现 COL_va 的 DWORD]--> vt_va = ref_va + 4
  slot1 = dword at vt_va+4, slot2 = dword at vt_va+8

产物：_r139/r139d_f29_tables.json + 控制台逐表一行。
"""
import os
import re
import json
import struct

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
raw = open(EXE, 'rb').read()

# ---- 节表 ----
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, e + 6)[0]
opt_size = struct.unpack_from('<H', raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + opt_size + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', raw, o + 8)
    secs.append(dict(name=nm, vsize=vs, rva=va, rsize=rs, rptr=rp))


def secof_va(va):
    rva = va - IB
    for s in secs:
        if s['rva'] <= rva < s['rva'] + s['rsize']:
            return s
    return None


def off_of_va(va):
    s = secof_va(va)
    return None if s is None else s['rptr'] + (va - IB - s['rva'])


def d32(va):
    o = off_of_va(va)
    return None if o is None or o + 4 > len(raw) else struct.unpack_from('<I', raw, o)[0]


def u8(va):
    o = off_of_va(va)
    return None if o is None else raw[o]


def u16(va):
    o = off_of_va(va)
    return None if o is None else struct.unpack_from('<H', raw, o)[0]


fails = []
out = {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


# ---- 1. 77 张 TClassFactory 的 TD VA + 类名 ----
pat = re.compile(rb'\.\?AV\?\$TClassFactory@([^\x00]*?)@@')
tds = []
for s in secs:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base_va = IB + s['rva']
    for m in pat.finditer(seg):
        arg = m.group(1).decode('latin1')
        # MSVC 名字里 V<Name>@@ 表示类 Name；取最后一个 V 到 @@ 之间的名字
        str_va = base_va + m.start()
        # MSVC RTTI: struct TypeDescriptor { void* pVFTable; void* spare; char name[]; }
        # 名字串是**内联**的 name[]，故 TypeDescriptor 本体在 str_va-8，而不是 str_va。
        tds.append(dict(td_va=str_va - 8, str_va=str_va, arg=arg,
                        rtti=m.group().decode('latin1')))
print('TD 候选 %d 个' % len(tds))
ck('1.1 TD 77 个', len(tds) == 77, len(tds))

# 校验 TypeDescriptor 布局：+0 pVFTable 必须落在 .data/.rdata，+4 spare 必须为 0，
# 且 +8 起的字节必须就是 .?AV... 串（内联，不是指针）
data_ranges = [(IB + s['rva'], IB + s['rva'] + s['rsize']) for s in secs if s['name'] in ('.data', '.rdata')]


def in_data(va):
    return va is not None and any(lo <= va < hi for lo, hi in data_ranges)


bad_td = []
for t in tds:
    vf, sp = d32(t['td_va']), d32(t['td_va'] + 4)
    o = off_of_va(t['td_va'] + 8)
    inline_ok = o is not None and raw[o:o + 5] == b'.?AV?'
    if not (in_data(vf) and sp == 0 and inline_ok):
        bad_td.append((hex(t['td_va']),
                       None if vf is None else hex(vf), sp, inline_ok))
ck('1.2 77 个 TypeDescriptor 都满足 +0 在 .data/.rdata、+4==0、+8 内联 .?AV? 前缀',
   not bad_td, bad_td[:4])

# ---- 2. 找 COL：.data 里出现 TD_va 的 DWORD，COL = ref - 12 ----
data_secs = [s for s in secs if s['name'] in ('.data', '.rdata')]
refs = {}
for s in data_secs:
    seg = raw[s['rptr']:s['rptr'] + s['rsize']]
    base_va = IB + s['rva']
    for t in tds:
        needle = struct.pack('<I', t['td_va'])
        i = seg.find(needle)
        while i != -1:
            refs.setdefault(t['td_va'], []).append(base_va + i)
            i = seg.find(needle, i + 4)
print('有引用的 TD = %d / 77' % len(refs))
ck('2.1 每个 TD 至少被 .data/.rdata 里一个 DWORD 引用', len(refs) == 77, len(refs))

cols = {}
for td, rs_ in refs.items():
    cand = []
    for r in rs_:
        c = r - 12
        if d32(c) == 0 and d32(c + 12) == td:
            cand.append(c)
    cols[td] = sorted(set(cand))
ncol = {k: len(v) for k, v in cols.items()}
print('COL 唯一命中 %d / 77 ; 多解 %d ; 零解 %d'
      % (sum(1 for v in ncol.values() if v == 1),
         sum(1 for v in ncol.values() if v > 1),
         sum(1 for v in ncol.values() if v == 0)))
ck('2.2 77 个 TD 各得 1 个 COL（signature==0 且 +12==TD）',
   all(v == 1 for v in ncol.values()),
   {'uniq': sum(1 for v in ncol.values() if v == 1),
    'multi': [hex(k) for k, v in ncol.items() if v > 1],
    'zero': [hex(k) for k, v in ncol.items() if v == 0]})

# ---- 3. 找 vtable：出现 COL_va 的 DWORD，vt = ref + 4 ----
vts = {}
for td, cl in cols.items():
    if len(cl) != 1:
        continue
    c = cl[0]
    hits = []
    for s in data_secs:
        seg = raw[s['rptr']:s['rptr'] + s['rsize']]
        base_va = IB + s['rva']
        needle = struct.pack('<I', c)
        i = seg.find(needle)
        while i != -1:
            hits.append(base_va + i + 4)
            i = seg.find(needle, i + 4)
    vts[td] = sorted(set(hits))
nv = {k: len(v) for k, v in vts.items()}
print('vtable 唯一命中 %d / %d ; 多解 %d ; 零解 %d'
      % (sum(1 for v in nv.values() if v == 1), len(nv),
         sum(1 for v in nv.values() if v > 1), sum(1 for v in nv.values() if v == 0)))
ck('3.1 每张表的主虚表唯一', all(v == 1 for v in nv.values()),
   {'uniq': sum(1 for v in nv.values() if v == 1),
    'multi': [hex(k) for k, v in nv.items() if v > 1],
    'zero': [hex(k) for k, v in nv.items() if v == 0]})

# ---- 4. 读 slot1 / slot2，并按 8 字节桩 / 17 字节序列分类 ----
STUB = bytes.fromhex('B801000000C20400')
SEQ = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')


def classify(va):
    """该 VA 处是哪种形态：stub（8B 桩）/ seq（17B 序列）/ other"""
    if va is None or va == 0:
        return 'null'
    o = off_of_va(va)
    if o is None:
        return 'outofrange'
    b = raw[o:o + 17]
    if b[:8] == STUB:
        return 'stub'
    if b[:17] == SEQ:
        return 'seq'
    return 'other'


rows = []
for t in sorted(tds, key=lambda x: x['td_va']):
    td = t['td_va']
    cl = cols.get(td, [])
    vt = vts.get(td, [])
    cls_name = t['arg']
    if len(cl) != 1 or len(vt) != 1:
        rows.append(dict(td=hex(td), name=cls_name, col='multi', vt='multi',
                         s1=None, s2=None, k1='?', k2='?'))
        continue
    vt_va = vt[0]
    s1 = d32(vt_va + 4)
    s2 = d32(vt_va + 8)
    rows.append(dict(td=hex(td), name=cls_name, col=hex(cl[0]), vt=hex(vt_va),
                     s1=hex(s1) if s1 is not None else None,
                     s2=hex(s2) if s2 is not None else None,
                     k1=classify(s1), k2=classify(s2)))

print('\n  逐表（名字 / vt / slot1+形态 / slot2+形态）：')
for r in rows:
    print('    %-34s vt=%-10s s1=%-10s %-5s s2=%-10s %-5s'
          % (r['name'][:34], r['vt'], r['s1'], r['k1'], r['s2'], r['k2']))

both_stub = [r for r in rows if r['k1'] == 'stub' and r['k2'] == 'stub']
either_seq = [r for r in rows if r['k1'] == 'seq' or r['k2'] == 'seq']
other = [r for r in rows if r not in both_stub]
out['rows'] = rows
out['both_stub'] = len(both_stub)
out['both_stub_names'] = [r['name'] for r in both_stub]
out['neither_names'] = [r['name'] for r in other]
out['seq_any'] = [r['name'] for r in either_seq]

print('\n两槽皆 8 字节桩 = %d / %d' % (len(both_stub), len(rows)))
print('任一槽 = 17 字节序列 = %d' % len(either_seq))
print('非「两槽皆桩」的表 = %d 张：%s' % (len(other), [r['name'] for r in other]))
ck('4.1 逐表可判的表数 == 77', len([r for r in rows if r['k1'] != '?']) == 77,
   len([r for r in rows if r['k1'] != '?']))
# 这是本体测值，先如实落盘；是否等于主张的 63/77 由调用方比对
out['fails'] = fails
open(os.path.join(ROOT, '_r139', 'r139d_f29_tables.json'), 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print('\n汇总：%d FAIL ; json -> _r139/r139d_f29_tables.json' % len(fails))
raise SystemExit(1 if fails else 0)
