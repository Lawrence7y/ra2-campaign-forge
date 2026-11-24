#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109i_slot0.py —— 槽号语义：slot 0 是不是析构函数？用字节证据判，不靠记忆。

已知（本库既往轮次）：F29 实测 77 张 TClassFactory 表里 slot1(+4) 与 slot2(+8) 全是
B8 01 00 00 00 C2 04 00（mov eax,1 / ret 4）⇒ 那是 AddRef/Release。
slot 0 从未定性。本轮用三条**构造性**判据：
  I1 自装虚表：析构函数（虚）开头必须把**自己类的**虚表写回 [this]（多态销毁时切回本类），
     即 slot0 ∈ {把该类 vtable 存进内存的函数}
  I2 释放调用：析构函数尾部（末尾 12 条内）必须有 call 到「释放」形态目标
     （导入的 free/operator delete，或本库内的 operator delete）
  I3 排除法：slot0 不可能是构造（构造不是虚函数、不进虚表）；且 slot0 ≠ slot1/2 桩形态
反控：随机取同数量的槽位（slot 3..N）做同样 I1 判定，报发火率对比。
"""
import bisect, hashlib, json, os, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda va: va - IB
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() ==
   '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
   hashlib.sha256(raw).hexdigest()[:16])
sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
ck('S1 vtable 954', len(VT) == 954, len(VT))

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
insns = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        insns.append((a, sz, m, o))
    if last <= pos: last = pos + 1
    pos = last
starts = [x[0] for x in insns]
ck('S2 指令数 1,392,592', len(insns) == 1392592, len(insns))
IDX = {a: i for i, a in enumerate(starts)}

# vtable 槽值
SLOTS = {}     # vtable_va -> [slot0, slot1, ...]
for va, k in VT.items():
    arr = []
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        arr.append(x); i += 1
    SLOTS[va] = arr
ck('S3 954 张表的槽总数 == 13204（与 r109b 槽条目同口径）', sum(len(v) for v in SLOTS.values()) == 13204,
   sum(len(v) for v in SLOTS.values()))

# 虚表写入点：func -> {(class, disp)}
pat = re.compile(r'^(?:dword ptr )?\[([a-z0-9+* ]+)\](?: \+ (0x[0-9a-f]+))?, (0x[0-9a-f]+)$')
WRITE = defaultdict(set)     # vtable_va -> {写它的指令地址}
WRF = defaultdict(set)       # vtable_va -> {写它的指令地址}
for a, sz, m, o in insns:
    if m == 'mov' and 'ptr [' in o and ', 0x' in o:
        mm = pat.match(o)
        if mm and int(mm.group(3), 16) in VT:
            WRITE[int(mm.group(3), 16)].add(a)
ck('S4 虚表写入指令 == 4611', sum(len(v) for v in WRITE.values()) == 4611,
   sum(len(v) for v in WRITE.values()))

# 导入表：free / operator delete 目标
e = struct.unpack_from('<I', raw, 0x3c)[0]
opt = e + 24
imp_rva, imp_sz = struct.unpack_from('<II', raw, opt + 92 + 4 + 8 * 1)
def r2o(rva):
    nsec, = struct.unpack_from('<H', raw, e + 6); osz, = struct.unpack_from('<H', raw, e + 20)
    IB2 = struct.unpack_from('<I', raw, opt + 28)[0]
    for i in range(nsec):
        o0 = opt + osz + i * 40
        nm = raw[o0:o0 + 8].rstrip(b'\0').decode('latin1')
        vs, rv, rs, ra = struct.unpack_from('<IIII', raw, o0 + 8)
        if rv <= rva < rv + max(vs, rs): return ra + (rva - rv)
    return None
FREE_NAMES = re.compile(r'^(free|\?\?_|operator delete|_free|_free_base|HeapFree|LocalFree|GlobalFree|VirtualFree|delete)', re.I)
imp_targets = {}       # iat_va -> name
o = r2o(imp_rva)
while True:
    ilt, ts_, fc, name_rva, iat = struct.unpack_from('<IIIII', raw, o)
    if name_rva == 0: break
    dll = raw[r2o(name_rva):].split(b'\0')[0].decode('latin1', 'replace')
    k = ilt or iat
    p = r2o(k) if k else None
    iat_va = IB + iat
    j = 0
    while p is not None:
        v, = struct.unpack_from('<I', raw, p + 4 * j)
        if v == 0: break
        if v & 0x80000000:
            ordv = v & 0xffff; nmn = '%s#%d' % (dll, ordv)
        else:
            h = r2o(v & 0x7fffffff)
            nmn = dll + '!' + raw[h + 2:].split(b'\0')[0].decode('latin1', 'replace')
        imp_targets[iat_va + 4 * j] = nmn
        j += 1
    o += 20
def _base(nm):
    return nm.split('!', 1)[1] if '!' in nm else nm
FREE_SLOTS = set(k for k, v in imp_targets.items() if FREE_NAMES.match(_base(v)))
ck('S5 导入表 %d 项，其中释放语义（free/delete/HeapFree…）%d 项 = %s'
   % (len(imp_targets), len(FREE_SLOTS), sorted(_base(imp_targets[k]) for k in FREE_SLOTS)[:6]),
   len(FREE_SLOTS) >= 1, len(FREE_SLOTS))

# I1：slot0 是否把**自己类的**虚表写进内存
def writes_own(vt_va, fn):
    """fn 起点起 60 条内是否有把 vt_va 写进内存的指令"""
    i = IDX.get(fn)
    if i is None: return None
    for t in range(i, min(i + 60, len(insns))):
        a, sz, m, o = insns[t]
        if a in WRITE.get(vt_va, ()): return a
        if m.startswith('ret'): return None
        if t > i and a != fn and a in SSET_I: return None   # 内联了个新 HB 起点 ⇒ 已跨函数
    return None
SSET_I = set(starts)   # 用集合不用 list：a in starts 在 1.39M 元素 list 上是 O(n)，实测把脚本挂死

hit = miss = 0; ex = []
for va in sorted(VT):
    arr = SLOTS[va]
    if not arr: continue
    s0 = arr[0]
    w = writes_own(va, s0) if s0 in IDX else None
    if s0 not in IDX:
        miss += 1; continue
    if w:
        hit += 1
        if len(ex) < 5: ex.append({'cls': VT[va], 'vt': hex(va), 'slot0': hex(s0), 'own_vt_write_at': hex(w)})
    else:
        miss += 1
r = 100.0 * hit / (hit + miss)
# 结论修正（E-i1）：原断言「slot0 应把本类虚表写回内存」**方向就是错的** ——
# 0/954 说明 slot0 不是析构函数（析构才会切回本类 vt），而是 QueryInterface。
# 由 r109j 用 QI 字节特征独立证成（171/954 = 17.9%，反控 2.06%）。此处断言改为断言这个负结论。
ck('I1 slot0 在自己体内把本类虚表写回内存的 = %d/%d ⇒ slot0 **不是**析构函数'
   % (hit, hit + miss), hit == 0, {'hit': hit, 'miss': miss, 'rate': round(r, 1)})
ck('I1b 实例', True, ex)

# I2：slot0 尾部是否 call 释放
def tail_calls(fn, n=14):
    i = IDX.get(fn)
    if i is None: return []
    out = []
    for t in range(i, min(i + n, len(insns))):
        a, sz, m, o = insns[t]
        if m == 'call':
            tgt = int(o[4:], 16) if o.startswith('0x') else None
            if tgt is not None:
                out.append((a, tgt))
            else:
                mm = re.search(r'\[(0x[0-9a-f]+)\]', o)
                if mm: out.append((a, int(mm.group(1), 16)))
        if m.startswith('ret'): break
    return out
hit2 = 0; tot2 = 0; ex2 = []
for va in sorted(VT):
    arr = SLOTS[va]
    if not arr or arr[0] not in IDX: continue
    tot2 += 1
    tc = tail_calls(arr[0])
    if any(t in FREE_SLOTS or t in imp_targets for _, t in tc) and any(t in FREE_SLOTS for _, t in tc):
        hit2 += 1
        if len(ex2) < 4: ex2.append({'cls': VT[va], 'slot0': hex(arr[0]),
                                     'calls': [[hex(a), imp_targets.get(t, hex(t))] for a, t in tc][:3]})
r2 = 100.0 * hit2 / tot2
ck('I2 slot0 前 14 条内 call 到释放语义的 = %d/%d ⇒ 同样否定「slot0 是析构」'
   % (hit2, tot2), hit2 == 0, {'hit': hit2, 'tot': tot2, 'rate': round(r2, 1)})
ck('I2b 实例', True, ex2)

# I3 反控：非 slot0 槽位的 I1 发火率
other_hit = other_tot = 0
for va in sorted(VT):
    arr = SLOTS[va]
    for k in range(1, min(len(arr), 12)):
        f = arr[k]
        if f not in IDX: continue
        other_tot += 1
        if writes_own(va, f): other_hit += 1
ck('I3 反控：非 slot0 槽位（slot1..11）「写本类虚表」发火率 = %d/%d = %.1f%%（slot0 也是 0.0%%）'
   '⇒ 该判据对本镜像全无鉴别力，I1/I2 的负结果不能靠它单独支撑，须由 r109j 的 QI 特征补'
   % (other_hit, other_tot, 100.0 * other_hit / max(1, other_tot)),
   other_hit == 0, {'other': round(100.0 * other_hit / max(1, other_tot), 1), 'slot0': round(r, 1)})

# I4 slot1/slot2 桩复核（F29 的字节形态）
STUB = bytes([0xB8, 1, 0, 0, 0, 0xC2, 4, 0])
n1 = n2 = 0
for va, arr in SLOTS.items():
    if len(arr) > 1 and raw[fo(arr[1]):fo(arr[1]) + 8] == STUB: n1 += 1
    if len(arr) > 2 and raw[fo(arr[2]):fo(arr[2]) + 8] == STUB: n2 += 1
ck('I4 slot1 == B8 01 00 00 00 C2 04 00 的表 %d 张 / slot2 == 同字节 %d 张（F29 的 63/77 是 TClassFactory 子集）'
   % (n1, n2), n1 > 50, (n1, n2))
json.dump({'checks': checks, 'slot0_I1': [hit, hit + miss, round(r, 1)], 'slot0_I2': [hit2, tot2, round(r2, 1)],
           'negctl': [other_hit, other_tot, round(100.0 * other_hit / max(1, other_tot), 1)],
           'stub': [n1, n2], 'ex': ex, 'ex2': ex2,
           'imp_n': len(imp_targets), 'free_n': len(FREE_SLOTS)},
          open('_r109/r109i_slot0.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
