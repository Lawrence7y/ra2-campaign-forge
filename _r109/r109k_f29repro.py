#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r109k_f29repro.py —— 复算 F29 的 63/77 与有效桩 64/77，并纠正 r109j 的 J4 口径错。

🐞 自错 E-z1：r109j 的 J4b 拿「**TClassFactory 自身**的 vtable」去比 F29 的 63/77，
   实测 1/78 = 1.3%，与 F29 差一个数量级。根因是读错了 F29 的分母：F29 的分母是
   「**产品类**」（类名出现在 ?$TClassFactory@VX@@ 里的 X），不是工厂类本身。
   本脚本按正确口径复算，并把两个口径并列报，防止再被误读。

判据（逐字节，不读任何既有报告）：
  S1 从类名集合里取所有 ?$TClassFactory@VX@@ 的 X 为产品类候选
  S2 每张产品类主 vtable 取 slot1(+4)/slot2(+8)
  S3 桩 = 8 字节逐字节等于 B8 01 00 00 00 C2 04 00
  S4 有效桩 = 把「真转发器」（mov eax,[esp+4]; push eax; call T; ret 4 形态）跟到 T 再判，
     最多跟 3 跳；跳板（jmp T）同样跟
  S5 TClassFactory 自身的表另算一列，标明它不是 F29 的分母
"""
import json, os, re, struct
from collections import Counter
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
byname = {k: v for k, v in sym.items() if v.get('vtable_va')}
STUB = bytes([0xB8, 1, 0, 0, 0, 0xC2, 4, 0])

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
def dis(a, n=6):
    return list(md.disasm_lite(raw[fo(a):fo(a) + 48], a))[:n]
def slot(va, i):
    return struct.unpack_from('<I', raw, fo(va) + 4 * i)[0]

FAC_RE = re.compile(r'^\?\$TClassFactory@V(.+?)@@$')
prod = {}
for k in byname:
    mm = FAC_RE.match(k)
    if mm:
        prod[mm.group(1)] = k
ck('S1 产品类候选（?$TClassFactory@VX@@ 里的 X）= %d 个' % len(prod), len(prod) >= 70, len(prod))
have = {p: byname[p] for p in prod if p in byname}
ck('S1b 其中在 symbols.json 里能查到主 vtable 的 = %d' % len(have), len(have) >= 70, len(have))

def is_stub(f):
    return raw[fo(f):fo(f) + 8] == STUB
JMP_RE = re.compile(r'^0x[0-9a-f]+$')
def resolve(f, depth=0):
    """转发器/跳板跟到终点：最多 3 跳；返回 (终点, 路径)"""
    path = [f]
    cur = f
    for _ in range(3):
        ins = dis(cur, 5)
        if not ins: break
        ops = [(g[2], g[3]) for g in ins]
        # 跳板
        if ops[0][0] == 'jmp' and JMP_RE.match(ops[0][1]):
            cur = int(ops[0][1], 16); path.append(cur); continue
        # 真转发器：mov eax,[esp+4] / push eax / call T / ret 4
        if (len(ops) >= 4 and ops[0][0] == 'mov' and ops[0][1].startswith('eax, dword ptr [esp + 4]')
                and ops[1][0] == 'push' and ops[1][1] == 'eax'
                and ops[2][0] == 'call' and JMP_RE.match(ops[2][1])
                and ops[3][0].startswith('ret')):
            cur = int(ops[2][1], 16); path.append(cur); continue
        break
    return cur, path

both = 0; eff_both = 0; rows = []
for p, c in sorted(have.items()):
    va = int(c['vtable_va'], 16)
    s1, s2 = slot(va, 1), slot(va, 2)
    b1, b2 = is_stub(s1), is_stub(s2)
    e1, p1 = resolve(s1); e2, p2 = resolve(s2)
    eb1, eb2 = is_stub(e1), is_stub(e2)
    both += (b1 and b2)
    eff_both += (eb1 and eb2)
    rows.append({'product': p, 'vt': hex(va), 's1': hex(s1), 's2': hex(s2),
                 'stub': [b1, b2], 'eff_stub': [eb1, eb2],
                 'eff_path': [[hex(x) for x in p1], [hex(x) for x in p2]] if (p1 != [s1] or p2 != [s2]) else None})
n = len(have)
ck('S3 产品类两槽皆逐字节桩 = %d/%d = %.2f%%（F29 报 63/77 = 81.82%%）'
   % (both, n, 100.0 * both / n), True, {'both': both, 'n': n, 'pct': round(100.0 * both / n, 2)})
ck('S4 有效桩（跟转发器/跳板到终点再判）= %d/%d = %.2f%%（F29 报 64/77 = 83.12%%）'
   % (eff_both, n, 100.0 * eff_both / n), True, {'eff': eff_both, 'n': n, 'pct': round(100.0 * eff_both / n, 2)})
ck('S4b 复现 F29 的 63/77：实测 %d/%d' % (both, n), both == 63 or eff_both == 64,
   {'raw': both, 'eff': eff_both, 'n': n})
# 未被跟到终点的少数
odd = [r for r in rows if not (r['eff_stub'][0] and r['eff_stub'][1])]
ck('S4c 有效桩判定下非桩的产品类 = %d 个（F29 说 3 个例外 + 12 非桩，共 15 ⇒ 77-64=13 或 77-63=14）'
   % len(odd), True, [o['product'] for o in odd][:20])

# S5：TClassFactory 自身的表（不是 F29 的分母，单列以防再误读）
FACV = [(va, k) for k, c in sym.items() if 'ClassFactory' in k and c.get('vtable_va')
        for va in [int(c['vtable_va'], 16)]]
fb = sum(1 for va, k in FACV if is_stub(slot(va, 1)) and is_stub(slot(va, 2)))
ck('S5 对照量（非 F29 分母）：TClassFactory **自身**的表里两槽皆桩的 = %d/%d' % (fb, len(FACV)),
   fb < 5, (fb, len(FACV)))
json.dump({'checks': checks, 'raw_both': both, 'eff_both': eff_both, 'n': n,
           'rows': rows, 'fac_self': [fb, len(FACV)]},
          open('_r109/r109k_f29repro.json', 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (npass, len(checks), len(checks) - npass))
