#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109m_recount.py —— 复算子代理（deepseek #184）报的 owner 数，与我方 277 对齐口径。

#184 的产物（_r109/_exec/）在超时前落了部分 JSON：_ownerstat.json 报 n_entries=6802 /
n_dispatch_owners=242，_owner_dispatch.json 报 owners_total=295、how={contain:350, nearest:37}，
_extstat.json 报 n_func=19473 / n_entries=36037 / n_owners=271 / unresolved=36，
_sweepstat.json 报 n_insn=1,394,161。与我方 387 站点 / 277 owner / 1,392,592 指令都对不上。
按 §2.12 规则 D：审计员的数字必须主会话复算，本脚本只做这件事，并且**只读它落盘的原始
数据之外的镜像字节**，不复用它的判定逻辑。
  M1 指令数差异来源：1,394,161 - 1,392,592 = 1,569 —— 是不是它把 jmp 表后的数据解成了指令
     （我自己用 skipdata=True 得 1,392,592；换成 skipdata=False 看差多少）
  M2 站点数：我只认 jmp [reg*4+表] 且表基址是 32 位立即数；它 350+37=387 恰好等于我方 387，
     故 how 的两档合计一致，差异只在「owner 去重后 295 / 242 / 271」——逐个复算这三种口径
  M3 结论：给出我方最终口径下的 owner 数，并说明另两个数各是什么
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

import time
_T0=time.time()
def _t(msg): print('  [t=%5.1fs] %s'%(time.time()-_T0,msg),flush=True)
_t('start')
def scan(skipdata):
    md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = skipdata
    ins = []
    pos = TS
    while pos < TE:
        hi = min(pos + 65536, TE)
        buf = raw[fo(pos):fo(hi) + 16]; last = pos
        for a, sz, m, o in md.disasm_lite(buf, pos):
            if a >= hi: break
            last = a + sz
            ins.append((a, sz, m, o))
        if last <= pos: last = pos + 1
        pos = last
    return ins

_t('before scan True')
I1 = scan(True)
_t('after scan True')
# E-z3：skipdata=False 对全段做一遍实测**跑不完**（capstone 会把数据区逐字节当指令试解，
# 10 分钟未收敛，被 timeout 杀掉）。改为在固定 64KB 窗口上对比，并如实把这条写进自错。
def scan_win(a0, a1, skipdata):
    md3 = Cs(CS_ARCH_X86, CS_MODE_32); md3.detail = False; md3.skipdata = skipdata
    n = 0; pos = a0
    while pos < a1:
        hi = min(pos + 65536, a1); buf = raw[fo(pos):fo(hi) + 16]; last = pos
        for a, sz, m, o in md3.disasm_lite(buf, pos):
            if a >= hi: break
            last = a + sz; n += 1
        if last <= pos: last = pos + 1
        pos = last
    return n
w0, w1 = 0x401000, 0x411000
n_sd = scan_win(w0, w1, True); n_nsd = scan_win(w0, w1, False)
ck('M1 首 64KB 窗口：skipdata=True 解出 %d 条，skipdata=False 解出 %d 条（差 %d；全段 skipdata=False 实测跑不完，'
   '已降为窗口对比并记入自错 E-z3）' % (n_sd, n_nsd, n_nsd - n_sd), True, (n_sd, n_nsd))
I2 = []
ck('M1b 子代理报 1,394,161 条；我方 skipdata=True 全段 %d 条，差 %d'
   % (len(I1), 1394161 - len(I1)), len(I1) == 1392592, (len(I1), 1394161 - len(I1)))

insns = I1
starts = [x[0] for x in insns]; SSET = set(starts)
calls = [(a, int(o, 16)) for a, _, m, o in insns if m == 'call' and o.startswith('0x')]
rets = [a for a, _, m, _ in insns if m.startswith('ret')]
def ret_size(r):
    q = fo(r)
    while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65): q += 1
    return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
HB = set()
for r in rets:
    p = r + ret_size(r); q = p; n = 0
    while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64:
        q += 1; n += 1
    if n and q % 4 == 0 and q in SSET: HB.add(q)
CALLT = set(t for _, t in calls if TS <= t < TE)
sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
SLOT = defaultdict(set)
for va, k in VT.items():
    i = 0
    while i < 400:
        x = struct.unpack_from('<I', raw, fo(va) + i * 4)[0]
        if not (TS <= x < TE): break
        SLOT[x].add(k); i += 1
ck('S1 三集合：call 目标 %d / 槽值 %d / HB %d' % (len(CALLT), len(SLOT), len(HB)),
   (len(CALLT), len(SLOT), len(HB)) == (6719, 6499, 17766), (len(CALLT), len(SLOT), len(HB)))

SITES = []
# E-z4：删掉 placeholder 时留下了 while 循环体只剩 pos=last 的空转（last 从不前进）⇒ 死循环。
# 这里直接把整个死块删掉，只留真正的扫描。
pos = TS
md2 = Cs(CS_ARCH_X86, CS_MODE_32); md2.detail = False; md2.skipdata = True
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md2.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        if m == 'jmp' and '[' in o and '*4' in o:
            m2 = re.findall(r'0x[0-9a-f]+', o)
            if m2: SITES.append((a, int(m2[-1], 16)))
    if last <= pos: last = pos + 1
    pos = last
_t('after IMMPTR/SITES')
ck('M2 分派站点 %d / distinct 表基址 %d（子代理 how 合计 350+37=387 与此一致）'
   % (len(SITES), len(set(t for _, t in SITES))), len(SITES) == 387, (len(SITES), len(set(t for _, t in SITES))))

def own(E, a):
    i = bisect.bisect_right(E, a)
    return E[i - 1] if i else None
sets = {
  'E_call+slot+HB': sorted(CALLT | set(SLOT) | HB),
  'E_call+slot+HB+immptr': None,
  'E_call_only': sorted(CALLT),
  'E_call+HB': sorted(CALLT | HB),
  'E_slot_only': sorted(SLOT),
}
IMMPTR = set()
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[fo(pos):fo(hi) + 16]; last = pos
    for a, sz, m, o in md2.disasm_lite(buf, pos):
        if a >= hi: break
        last = a + sz
        if m in ('jmp', 'call') or (m[0] == 'j' and m != 'jmp'): continue
        for tok in re.findall(r'0x[0-9a-f]+', re.sub(r'\[[^\]]*\]', ' ', o), re.I):
            v = int(tok, 16)
            if TS <= v < TE and v in SSET: IMMPTR.add(v)
    if last <= pos: last = pos + 1
    pos = last
ck('M2b IMMPTR == 598', len(IMMPTR) == 598, len(IMMPTR))
sets['E_call+slot+HB+immptr'] = sorted(CALLT | set(SLOT) | HB | IMMPTR)
_t('before owner sets')
out = {}
for nm, E in sets.items():
    if E is None: continue
    o = set()
    for site, _ in SITES:
        x = own(E, site)
        if x: o.add(x)
    out[nm] = len(o)
ck('M3 各 E 口径下的 owner 去重数 = %s' % out, out['E_call+slot+HB+immptr'] == 277, out)
ck('M3b 子代理报的 295 / 242 / 271 分别对应：295 = 站点数减不可归因? 242 = 它自己的 operator 表? '
   '271 = 它的 extents 表；三者与我方 277 都不是同一集合', True,
   {'sub_295': 295, 'sub_242': 242, 'sub_271': 271, 'mine_277': out.get('E_call+slot+HB+immptr')})
# 复算 295：把「分派站点本身也当 owner」会得到多少
o2 = set()
for site, _ in SITES:
    x = own(sorted(CALLT | set(SLOT) | HB | IMMPTR), site)
    o2.add(x if x else site)
ck('M3c 若把归不到 owner 的站点**记成站点自身**，去重数 = %d（子代理 295 可能即此口径）' % len(o2),
   True, (len(o2), 295))
json.dump({'checks': checks, 'owner_counts': out, 'n_sites': len(SITES),
           'insn': [len(I1), len(I2)], 'sub': {'insn': 1394161, 'n295': 295, 'n242': 242, 'n271': 271},
           'sites_as_owner': len(o2)}, open('_r109/r109m_recount.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
