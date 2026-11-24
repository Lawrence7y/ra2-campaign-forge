#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108a_branchmap.py —— 全 .text 直接分支目标图（lite 解码 + 64KB 分块，不带 detail）

目的：为 6 张 AMBIGUOUS 表准备「直接 jmp/jcc 目标」证据，并检验 R107 判据
「S 到 H 之间 ret 必须为 0」是否成立。
产物：_r108/branchmap.bin（结构见 dump）+ _r108/r108a_branchmap.json（断言）
"""
import array, hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

raw = open(EXE, 'rb').read()
h = hashlib.sha256(raw).hexdigest()
ck('S0 exe sha256', h == EXE_SHA, h[:16])
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
    secs.append((nm, IB + rva, vs, ra, rs))
def off(va):
    for nm, sv, vs, ra, rs in secs:
        if sv <= va < sv + max(vs, rs):
            return ra + (va - sv)
    return None
tn, TS, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TE = TS + tvs
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True

starts = array.array('I')
calls = []      # (insn_va, tgt)
branches = []   # (insn_va, tgt)   direct jmp/jcc
rets = array.array('I')
pos = TS
n_undec = 0
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            calls.append((a, int(o, 16)))
        elif m[0] == 'j' and o.startswith('0x'):
            branches.append((a, int(o, 16)))
        elif m.startswith('ret'):
            rets.append(a)
    if last <= pos:
        n_undec += 1
        last = pos + 1
    pos = last
ns = len(starts)
ck('S1 指令数 > 1,300,000（与前几轮 1,392,592 同口径 ±2%）',
   1300000 <= ns <= 1420000, ns)
ck('S2 停滞位置数 == 0', n_undec == 0, n_undec)
n_ct = len(set(t for _, t in calls))
ck('S3 distinct call 目标数 == 6728（R106/R107 同口径；R107 的 6728 是去重目标数不是 call 条数）',
   n_ct == 6728, (len(calls), n_ct))
ck('S4 直接分支（jmp/jcc）数 > 100,000', len(branches) > 100000, len(branches))

SSET = set(starts)
out = {'starts': starts, 'calls': array.array('I'), 'calls_t': array.array('I'),
       'br': array.array('I'), 'br_t': array.array('I'), 'rets': rets}
for a, t in calls:
    out['calls'].append(a); out['calls_t'].append(t)
for a, t in branches:
    out['br'].append(a); out['br_t'].append(t)
with open('_r108/branchmap.bin', 'wb') as f:
    for k in ('starts', 'calls', 'calls_t', 'br', 'br_t', 'rets'):
        arr = out[k]
        f.write(struct.pack('<II', len(arr), {'starts': 0, 'calls': 1, 'calls_t': 2,
                                              'br': 3, 'br_t': 4, 'rets': 5}[k]))
        arr.tofile(f)
ck('S5 branchmap.bin 落盘（>=6 MB）', os.path.getsize('_r108/branchmap.bin') >= 6_000_000,
   os.path.getsize('_r108/branchmap.bin'))
ck('S6 全部指令起点互不相同（lite 无重复）', len(SSET) == ns, (len(SSET), ns))
json.dump({'checks': checks, 'n_starts': ns, 'n_calls': len(calls), 'n_call_tgts': n_ct,
           'n_branches': len(branches), 'n_rets': len(rets)},
          open('_r108/r108a_branchmap.json', 'w'), ensure_ascii=False, indent=1)
nbad = sum(1 for c in checks if not c['ok'])
print('FAILS', nbad)
sys.exit(1 if nbad else 0)
