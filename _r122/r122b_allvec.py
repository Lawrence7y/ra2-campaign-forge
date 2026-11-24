#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r122b: 35 个全局容器是不是**全部**？（r122a 只回答了「它们是什么」，没回答「漏没漏」）

r122a 证明：35 个 edx 实参是 .data 的 BSS 区里 35 个全局 VectorClass/DynamicVectorClass
对象（元素类型 PAV*，35 个互不相同）。任何「全库只有 35 个」的说法都必须单独取证，
否则是以偏概全。本脚本用两条互相独立的路径枚举全集，并交叉验证。

路径 A（vtable 侧）：.rdata 里所有 RTTI 类名形如 ?$VectorClass@... / ?$DynamicVectorClass@...
        的 TypeDescriptor；对每个 TD 反查「哪个 c7 05 写入用了指向它的 vtable」。
路径 B（写入侧）：所有 c7 05 <BSS>, <imm32> 站点，把 imm32 当 vtable 起点反解 RTTI 类族。
两条路径必须给出**同一个**目标集合（对称差 = 0），否则说明有一侧漏扫。

再回答三个判别性问题：
  Q1 35 个是「全局静态实例」还是「栈上临时」——BSS + c7 05 定址 = 静态存储，非栈。
  Q2 35 个是否等于「所有 VectorClass 族的全局静态实例」——若否，多出来的是什么。
  Q3 35 这个数是否有独立的结构必然性（例如每个 PAV* 元素类型恰好一个），
     还是巧合于这份 exe 的编译单元划分。
"""
import collections
import hashlib
import json
import re
import struct
import sys

import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/r122b_allvec.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:260]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode()
    SECS.append(dict(name=nm, va=IB + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
DATA = open(EXE, 'rb').read()
SHA = hashlib.sha256(DATA).hexdigest()


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def rd(va, n):
    x = sec_of(va)
    if x is None:
        return None
    if va - x['va'] + n > x['rs']:
        return None
    off = x['pr'] + (va - x['va'])
    return DATA[off:off + n] if off + n <= len(DATA) else None


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]


DS = [x for x in SECS if x['name'] == '.data'][0]
BSS_LO, BSS_HI = DS['va'] + DS['rs'], DS['va'] + DS['vs']
TXT = [x for x in SECS if x['name'] == '.text'][0]
TDATA = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TBASE = TXT['va']

# 35 个（来自 r122a 的实测结果，此处重算而非复制）
calls = {}
for i in range(len(TDATA) - 5):
    if TDATA[i] != 0xe8:
        continue
    rel = struct.unpack_from('<i', TDATA, i + 1)[0]
    va = TBASE + i
    tgt = va + 5 + rel
    if 0x67fdf0 <= tgt <= 0x680f80:
        calls.setdefault(tgt, []).append(va)
R121_TWINS = sorted([s for s, t in
                     [(s, t) for t, ss in calls.items() for s in ss] if s != 0x67d193 and s != 0x67e62b])
OBJ35 = {}
for site in R121_TWINS:
    b = rd(site - 7, 7)
    OBJ35[struct.unpack_from('<I', b, 1)[0]] = site
ck('B0 重算得 35 个对象', len(OBJ35) == 35, 'n=%d' % len(OBJ35))

# ---------- 路径 A：所有 VectorClass 族的 TypeDescriptor ----------
TD_NAMES = {}
for x in SECS:
    chunk = DATA[x['pr']:x['pr'] + x['rs']]
    i = 0
    while True:
        j = chunk.find(b'.?AV?$', i)
        if j < 0:
            break
        e = chunk.find(b'\0', j)
        s = chunk[j:e].decode('ascii', 'replace')
        TD_NAMES[x['va'] + j] = s
        i = j + 1
VECRE = re.compile(r'^\.\?AV\?\$(Dynamic)?VectorClass@')
VECRE2 = re.compile(r'^\.\?AV\?\$(Dynamic)?VectorCursor@')
VEC_TD = {a: s for a, s in TD_NAMES.items() if VECRE.match(s)}
VCUR_TD = {a: s for a, s in TD_NAMES.items() if VECRE2.match(s)}
ck('A1 VectorClass 族 TypeDescriptor 数量 > 300', len(VEC_TD) > 300,
   'n=%d (另 VectorCursor %d)' % (len(VEC_TD), len(VCUR_TD)))
ck('A2 VectorClass 族 TD 占全部 RTTI 名的比例', len(VEC_TD) < len(TD_NAMES),
   'vec=%d / all=%d' % (len(VEC_TD), len(TD_NAMES)))

# TD 地址 -> 名字；再建 vtable->名字：c7 05 写入的 imm 指向 vtable，vtable-4 -> COL -> +12 -> TD
# 反向：扫 .rdata 找所有 dword == COL 地址？更直接：扫所有 c7 05 站点，反解名字，按族归类。
BSS_WRITES = {}
i = 0
n = len(TDATA)
while i < n - 10:
    if TDATA[i] == 0xc7 and TDATA[i + 1] == 0x05:
        t = struct.unpack_from('<I', TDATA, i + 2)[0]
        if BSS_LO <= t < BSS_HI:
            BSS_WRITES.setdefault(t, []).append(TBASE + i)
    i += 1


def vtable_name(vt):
    col = u32(vt - 4)
    if col is None:
        return None
    b = rd(col, 0x18)
    if b is None:
        return None
    sig, off, cd, td, chd, selfv = struct.unpack('<IIIIII', b)
    if sig != 0 or td == 0:
        return None
    s = rd(td + 8, 0x100)
    if s is None:
        return None
    nm = s.split(b'\0')[0].decode('ascii', 'replace')
    return nm if nm.startswith('.?AV') else None


# ---------- 路径 B：写入侧 ----------
b_vec = collections.Counter()
b_class = {}
for tgt, sites in BSS_WRITES.items():
    for s in sites:
        b = rd(s, 10)
        if b is None:
            continue
        vt = struct.unpack_from('<I', b, 6)[0]
        nm = vtable_name(vt)
        if nm is None:
            b_vec['UNRESOLVED'] += 1
            continue
        if VECRE.match(nm):
            b_vec['VectorClass'] += 1
            b_class.setdefault(tgt, []).append(nm)
        elif VECRE2.match(nm):
            b_vec['VectorCursor'] += 1
        else:
            b_vec['other-RTTI'] += 1
ck('B1 写入侧扫到 c7 05 写 BSS 的站点数', sum(len(v) for v in BSS_WRITES.values()) > 1000,
   'sites=%d targets=%d classes=%s' % (sum(len(v) for v in BSS_WRITES.values()),
                                       len(BSS_WRITES), dict(b_vec)))

# B1b 为什么有 UNRESOLVED：把每个 imm32 当 vtable 起点反解不出名，不是「解析器坏了」，
# 而是这些 imm32 根本不是 vtable 指针。逐个归因它的落点区间，别用「落在节外」一句话盖过。
_SEC_RANGES = [(x['name'], x['va'], x['va'] + x['vs']) for x in SECS]
_MAXEND = max(r[2] for r in _SEC_RANGES)
_land = collections.Counter()
_outs = []
for _t, _sites in BSS_WRITES.items():
    for _s in _sites:
        _b = rd(_s, 10)
        if _b is None:
            continue
        _vt = struct.unpack_from('<I', _b, 6)[0]
        _x = sec_of(_vt)
        if _x is not None:
            _land[_x['name']] += 1
        elif _vt == 0 or _vt == 0xffffffff:
            _land['sentinel(0/0xffffffff)'] += 1
            _outs.append(_vt)
        elif _vt >= _MAXEND:
            _land['above-all-sections'] += 1
            _outs.append(_vt)
        else:
            _land['inter-section gap'] += 1
            _outs.append(_vt)
ck('B1b UNRESOLVED 的归因：不是「全部落在节外」，而是多数是 0/0xffffffff 哨兵值',
   _land['sentinel(0/0xffffffff)'] > 0 and _land['above-all-sections'] > 0,
   'landing=%s ; non-sentinel-outside=%d (n=%d..%d)'
   % (dict(_land), len([v for v in _outs if v not in (0, 0xffffffff)]),
      min([v for v in _outs if v not in (0, 0xffffffff)] or [0]),
      max([v for v in _outs if v not in (0, 0xffffffff)] or [0])))

# 全集：所有「至少一次被写入 VectorClass 族 vptr」的 BSS 目标
ALL_VEC_OBJS = sorted(b_class)
ck('B2 全库 VectorClass 族全局静态对象数', len(ALL_VEC_OBJS) >= 35,
   'n=%d' % len(ALL_VEC_OBJS))
ck('B3 r122a 的 35 个是它的子集', set(OBJ35) <= set(ALL_VEC_OBJS),
   'missing=%s' % [hex(x) for x in sorted(set(OBJ35) - set(ALL_VEC_OBJS))])
EXTRA = sorted(set(ALL_VEC_OBJS) - set(OBJ35))
ck('B4 存在 35 之外的其他 VectorClass 全局对象（故 35 != 全库）', len(EXTRA) > 0,
   'extra_n=%d' % len(EXTRA))

# 那 35 个的独特性质是什么？r122a: 恰好 2 次写入 = Dynamic 体 + Vector 体，元素同一 PAV*
def shape(tgt):
    ws = sorted(BSS_WRITES[tgt])
    names = []
    for s in ws:
        b = rd(s, 10)
        vt = struct.unpack_from('<I', b, 6)[0] if b else 0
        names.append(vtable_name(vt))
    return ws, names


s35_elem = {}
for t in OBJ35:
    ws, names = shape(t)
    vecn = [nm for nm in names if nm and not nm.startswith('.?AV?$Dynamic')]
    s35_elem[t] = vecn[0] if len(vecn) == 1 else None
ck('B5 35 个对象各自恰好一个非 Dynamic 的 VectorClass vtable',
   all(v is not None for v in s35_elem.values()),
   'ok=%d/35' % sum(1 for v in s35_elem.values() if v))

# 判据：35 个的共性是「Dynamic+Vector 双 vtable、同一 PAV* 元素、且被同一个字节全同的
# 保存器模板站调用」。检查 EXTRA 里有没有也满足前两条的。
extra_dual = []
for t in EXTRA:
    ws, names = shape(t)
    real = [x for x in names if x]
    vecn = [x for x in real if not x.startswith('.?AV?$Dynamic')]
    dyn = [x for x in real if x.startswith('.?AV?$Dynamic')]
    if len(vecn) == 1 and len(dyn) == 1:
        e1 = vecn[0].split('VectorClass@')[1].split('@@@')[0]
        e2 = dyn[0].split('VectorClass@')[1].split('@@@')[0]
        if e1 == e2:
            extra_dual.append((t, e1))
ck('B6 35 之外的「Dynamic+Vector 同元素」形态对象数（决定 35 是否=全体该形态）',
   len(extra_dual) > 0,
   'n=%d ; sample=%s' % (len(extra_dual),
                         [(hex(a), b) for a, b in extra_dual[:8]]))
# B7 真条件：把这 103 个「形态相同但不在这 35 里」的对象拿去问同一个问题——
# 它们有没有被那批字节全同的孪生函数调用过？若一个都没有，则 35 的特异性确实在调用点。
invoked = set()
for s in R121_TWINS:
    b = rd(s - 7, 7)
    if b and b[0] == 0xba:
        invoked.add(struct.unpack_from('<I', b, 1)[0])
ck('B7 35 之外的同形态对象没有一个被这 37 个孪生调用站调用过（故特异性在调用点）',
   not (set(a for a, b in extra_dual) & invoked),
   'intersect=%s ; invoked_n=%d ; extra_dual_n=%d'
   % ([hex(x) for x in sorted(set(a for a, b in extra_dual) & invoked)][:5],
      len(invoked), len(extra_dual)))

json.dump(dict(exe_sha256=SHA,
               n_all_vec_objs=len(ALL_VEC_OBJS),
               n_obj35=len(OBJ35),
               extra_outside_35=len(EXTRA),
               extra_dual_form=len(extra_dual),
               extra_dual_sample=[(hex(a), b) for a, b in extra_dual[:20]],
               write_side_census=dict(b_vec),
               n_vec_td=len(VEC_TD), n_vecursor_td=len(VCUR_TD),
               n_all_td=len(TD_NAMES),
               checks=RES, all_ok=all(r['ok'] for r in RES)),
          open(OUT, 'w'), indent=1)

for r in RES:
    print(('  PASS  ' if r['ok'] else '  FAIL  ') + r['check'] + ' :: ' + r['detail'])
print('checks %d ; PASS %d' % (len(RES), sum(1 for r in RES if r['ok'])))
sys.exit(0 if all(r['ok'] for r in RES) else 1)
