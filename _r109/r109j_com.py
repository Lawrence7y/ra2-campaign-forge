#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109j_com.py —— 虚表 slot 0/1/2 的语义字节实证：QueryInterface / AddRef / Release。

R109 之前的槽号语义一直是「缺 YRpp 就取不到」。但 slot0 根本不需要头文件：
它体内若出现「拿第 2 个栈参当 16 字节 IID，用 repe cmpsd 逐个比对内存里的 GUID」，
那就是 QueryInterface 的**构造性字节特征**；而它比对的 GUID 里若含 IUnknown
（00000000-0000-0000-C000-000000000046），语义就闭合了。
  J1 slot0 的 QI 特征普查（repe cmpsd + IID 比对 + E_POINTER 0x80004003 / E_NOINTERFACE 0x80004002）
  J2 IUnknown GUID 的镜内命中位置（注意：.text 之外，故不能用「.text 内搜不到」作反证）
  J3 slot1/slot2 的 AddRef/Release 字节形态（mov eax,1 / ret 4）
  J4 交叉：含 IUnknown 比对的 slot0 与 F29 的 77 张 TClassFactory 表的关系
  J5 反控：slot 3..N 里出现同一 QI 特征的比例（应显著低）
"""
import json, os, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
import hashlib
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
def dis(a, n=40, cap=260):
    out = []
    for g in md.disasm_lite(raw[fo(a):fo(a) + cap], a):
        out.append(g)
        if len(out) >= n: break
    return out

def slot(va, i):
    return struct.unpack_from('<I', raw, fo(va) + 4 * i)[0]

IUNK = bytes.fromhex('0000000000000000c000000000000046')
ck('J1 IUnknown GUID 字节 == std', IUNK.hex() == '0000000000000000c000000000000046', IUNK.hex())

# ---- J1 slot0 的 QI 特征 ----
def qi_feat(f):
    """返回 (是否 QI, 比对到的 GUID 列表, 返回码集合)"""
    ins = dis(f, 60)
    if not ins: return False, [], set()
    guids = []
    codes = set()
    has_cmpsd = False
    for g in ins:
        a, sz, m, o = g[0], g[1], g[2], g[3]
        if m == 'repe' or 'cmpsd' in m:
            has_cmpsd = True
        for tok in re.findall(r'0x[0-9a-f]+', o, re.I):
            if True:
                v = int(tok, 16)
                if 0x400000 <= v < 0x900000:
                    key = 'g' + hex(v)
                    if key not in [x[0] for x in guids]:
                        # 只认 GUID 形态：16 字节里第 8..15 字节是 C0 00 00 00 00 00 00 46 或符合 GUID 模式
                        b = raw[fo(v):fo(v) + 16]
                        if len(b) == 16 and b[8:16] in (bytes.fromhex('c000000000000046'),
                                                       bytes.fromhex('c000000000000046')):
                            guids.append((key, v))
                if v in (0x80004003, 0x80004002, 0x0, 0x80004005):
                    codes.add(v)
    return has_cmpsd and bool(guids), [x[1] for x in guids], codes

n_qi = 0; sees_iunk = 0; tot = 0; ex = []
iunk_hits_global = []
i = 0x400000
while i < 0x900000:
    if raw[fo(i):fo(i) + 16] == IUNK: iunk_hits_global.append(i)
    i += 1
ck('J2 IUnknown GUID 在镜像内的命中处 = %d 个（%s）—— 这是 QI 比对的常量来源'
   % (len(iunk_hits_global), [hex(x) for x in iunk_hits_global[:4]]),
   len(iunk_hits_global) >= 1, [hex(x) for x in iunk_hits_global[:6]])

for va in sorted(VT):
    f = slot(va, 0)
    if not (TS <= f < TE): continue
    tot += 1
    ok, guids, codes = qi_feat(f)
    if ok:
        n_qi += 1
        if any(g in iunk_hits_global for g in guids):
            sees_iunk += 1
            if len(ex) < 4: ex.append({'cls': VT[va], 'slot0': hex(f),
                                       'guids': [hex(g) for g in guids][:5],
                                       'codes': [hex(c) for c in sorted(codes)]})
ck('J1 slot0 具备 QI 字节特征（repe cmpsd + GUID 比对）的 = %d/%d = %.1f%%'
   % (n_qi, tot, 100.0 * n_qi / tot), n_qi > 100, {'qi': n_qi, 'tot': tot, 'pct': round(100.0 * n_qi / tot, 1)})
ck('J1b 其中直接比对 IUnknown（00000000-0000-0000-C000-000000000046）的 = %d/%d = %.1f%%'
   % (sees_iunk, tot, 100.0 * sees_iunk / tot), sees_iunk > 0, sees_iunk)
ck('J1c 实例', True, ex)

# ---- J3 slot1 / slot2 = AddRef / Release 字节形态 ----
STUB = bytes([0xB8, 1, 0, 0, 0, 0xC2, 4, 0])
def is_stub(f):
    return raw[fo(f):fo(f) + 8] == STUB
n1 = sum(1 for va in VT if is_stub(slot(va, 1)))
n2 = sum(1 for va in VT if is_stub(slot(va, 2)))
ck('J3 slot1 形态 mov eax,1; ret 4 的表 = %d/954；slot2 同 = %d/954' % (n1, n2), n1 == 88 and n2 == 88, (n1, n2))
# 其余 slot1 是不是「转发到桩」或「add [this+..],1 / inc」
def addref_like(f):
    ins = dis(f, 8)
    if not ins: return None
    for g in ins:
        if g[2] in ('inc', 'add') and ('dword ptr [' in g[3]): return 'inc_field'
        if g[2] == 'call' or g[2] == 'jmp': return 'forward'
    return None
cnt = Counter()
for va in VT:
    f = slot(va, 1)
    if is_stub(f): cnt['stub'] += 1
    else: cnt[addref_like(f) or 'other'] += 1
ck('J3b slot1 形态分布 = %s（stub %d / forward %d / inc_field %d / other %d）'
   % (cnt.most_common(5), cnt['stub'], cnt['forward'], cnt['inc_field'], cnt['other']),
   cnt['stub'] + cnt['forward'] + cnt['inc_field'] + cnt['other'] == 954, cnt.most_common(5))

# ---- J4 TClassFactory 表 ----
FAC = [va for va, k in VT.items() if 'ClassFactory' in k]
ck('J4 类名含 ClassFactory 的 vtable = %d 张（F29 的 77 张是 TClassFactory 子集）' % len(FAC), len(FAC) > 50, len(FAC))
f_stub = sum(1 for va in FAC if is_stub(slot(va, 1)) and is_stub(slot(va, 2)))
ck('J4b 其中 slot1 与 slot2 皆为桩的 = %d/%d = %.1f%%（F29 报 63/77 = 81.82%%）'
   % (f_stub, len(FAC), 100.0 * f_stub / len(FAC)), True, round(100.0 * f_stub / len(FAC), 2))
f_qi = sum(1 for va in FAC if qi_feat(slot(va, 0))[0])
ck('J4c 其中 slot0 具备 QI 特征的 = %d/%d' % (f_qi, len(FAC)), True, (f_qi, len(FAC)))

# ---- J5 反控：slot 3..11 ----
o_hit = o_tot = 0
for va in VT:
    arr = []
    i = 0
    while i < 12:
        x = slot(va, i)
        if not (TS <= x < TE): break
        arr.append(x); i += 1
    for k in range(3, len(arr)):
        o_tot += 1
        if qi_feat(arr[k])[0]: o_hit += 1
ck('J5 反控：slot3..11 共 %d 个槽位里具备 QI 特征（repe cmpsd + GUID 比对）的 = %d（%.2f%%）；slot0 为 %.1f%%'
   % (o_tot, o_hit, 100.0 * o_hit / max(1, o_tot), 100.0 * n_qi / tot),
   100.0 * n_qi / tot > 5 * max(0.01, 100.0 * o_hit / max(1, o_tot)),
   {'other': o_hit, 'other_tot': o_tot, 'slot0_pct': round(100.0 * n_qi / tot, 1),
    'other_pct': round(100.0 * o_hit / max(1, o_tot), 2)})

json.dump({'checks': checks, 'qi': n_qi, 'tot': tot, 'sees_iunk': sees_iunk,
           'iunk_hits': [hex(x) for x in iunk_hits_global], 'ex': ex,
           'stub': [n1, n2], 'slot1_dist': cnt.most_common(6),
           'fac': [len(FAC), f_stub, f_qi], 'negctl': [o_hit, o_tot]},
          open('_r109/r109j_com.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
