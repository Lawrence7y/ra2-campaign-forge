#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107h_failmode.py —— 量化 R106 判据（CALLTGT）的系统性失效模式

R106 用「<=H 的最近 call 直接目标」当所属函数入口。本脚本证明它有一个结构性盲区：
  若真正的所属函数是**只经虚表调度、从不被 call 直引**的虚方法，CALLTGT 会静默回退到
  更早的某个 call 目标（往往是构造函数），给出一个错但看起来合理的答案——没有报错信号。

量化三项：
  M1 vtable 槽值总数、其中不在 call 目标集里的比例（= 盲区基率）
  M2 19 张表里，所属函数为「vtable-only（非 call 目标）」的张数
  M3 逐张字节证据：该函数的体在哪里结束（ret 地址），CALLTGT 给出的入口的体又在哪里结束，
     两者是否重叠（不重叠 => CALLTGT 的答案必错，不是"有争议"）
"""
import hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107h_failmode.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))


def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None


def u32(va):
    o = off(va)
    return struct.unpack_from('<I', raw, o)[0] if o is not None else None


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs
mdl = Cs(CS_ARCH_X86, CS_MODE_32)
mdl.detail = False
mdl.skipdata = True

starts = []
calls = {}
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in mdl.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            try:
                calls[a] = int(o, 16)
            except ValueError:
                pass
    if last <= pos:
        last = pos + 1
    pos = last
SSET = set(starts)
CALLT = set(calls.values())
ck('M0 指令 1,392,592 / call 目标 6,728', len(starts) == 1392592 and len(CALLT) == 6728,
   (len(starts), len(CALLT)))

sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {}
for cname, c in sym.items():
    v = c.get('vtable_va')
    if not v:
        continue
    va = int(v, 16)
    slots = []
    for i in range(400):
        x = u32(va + i * 4)
        if x is None or not (TS <= x < TE):
            break
        slots.append(x)
    if slots:
        VT[cname] = slots
slot_owner = {}
for cname, slots in VT.items():
    for i, s in enumerate(slots):
        slot_owner.setdefault(s, []).append((cname, i))

allslots = set(slot_owner)
vonly = allslots - CALLT
ck('M1 vtable 槽值 %d 个，其中非 call 目标 %d 个（盲区基率 %.1f%%）'
   % (len(allslots), len(vonly), 100.0 * len(vonly) / len(allslots)),
   len(allslots) == 6499, (len(allslots), len(vonly), round(100.0 * len(vonly) / len(allslots), 2)))


def body_ret(S, cap=8000):
    """从 S 前向解码，返回第一条 ret 的地址（函数体结束）与指令数；找不到返回 (None, n)"""
    a = S
    n = 0
    while n < cap:
        g = next(mdl.disasm(raw[off(a):off(a) + 16], a), None)
        if g is None:
            return (None, n)
        if g.mnemonic.startswith('ret'):
            return (g.address, n)
        n += 1
        a = g.address + g.size
    return (None, n)


D = json.load(open('_r106/r106f_switchsem.json'))['tables']
OWNER = json.load(open('_r107/r107g_owner.json'))['rows']
ownmap = {r['table']: r for r in OWNER}

ROWS = []
for t in D:
    H = int(t['holder'], 16)
    P1 = int(t['func_by_calltarget'], 16)
    g = ownmap[t['table']]
    O = int(g['owner'], 16) if g['owner'] else None
    oret, oins = body_ret(O) if O else (None, None)
    pret, pins = body_ret(P1)
    # CALLTGT 的体是否覆盖 H
    p1_covers_H = (pret is not None and pret < H)
    # 只在 OWNER 强度足够（g 判 OWNER）时才断言 P1 错
    wrong = (g['owner_status'] == 'OWNER' and O is not None and O != P1 and pret is not None and pret < H)
    ROWS.append({
        'table': t['table'], 'holder': hex(H),
        'R106_entry': hex(P1), 'R106_body_ret': hex(pret) if pret else None,
        'R106_body_covers_holder': p1_covers_H,
        'owner': hex(O) if O else None, 'owner_status': g['owner_status'],
        'owner_body_ret': hex(oret) if oret else None,
        'owner_is_vtable_only': (O in vonly) if O else None,
        'owner_vslot': g['owner_vslot'], 'refuted': wrong,
    })
    print('%-10s H=%08x R106=%08x ret=%-10s covers=%-5s | owner=%s(%s) ret=%-10s vtonly=%-5s %s'
          % (t['table'], H, P1, hex(pret) if pret else '-', p1_covers_H,
             hex(O) if O else '-', g['owner_status'], hex(oret) if oret else '-',
             (O in vonly) if O else '-', '<<REFUTED' if wrong else ''), flush=True)

ref = [r for r in ROWS if r['refuted']]
ck('M2 被硬证据推翻的表数（R106 入口的体在 holder 之前就 ret 了 => 不可能含 holder）',
   len(ref) == 2, [(r['table'], r['R106_entry'], r['R106_body_ret'], r['owner'])
                   for r in ref])
ck('M3 被推翻的这两张，所属函数都是 vtable-only（CALLTGT 结构性看不见）',
   all(r['owner_is_vtable_only'] for r in ref),
   [(r['table'], r['owner'], r['owner_vslot']) for r in ref])
ck('M4 这两张的所属函数在 vtable 里属于同一个类但不同槽（是两个不同虚方法，不是一个函数）',
   len({(v['class'], v['slot']) for r in ref for v in r['owner_vslot']}) == 2,
   [{v['class']: v['slot']} for r in ref for v in r['owner_vslot']])
json.dump({'checks': checks, 'rows': ROWS,
           'slot_total': len(allslots), 'slot_vtable_only': len(vonly)},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
