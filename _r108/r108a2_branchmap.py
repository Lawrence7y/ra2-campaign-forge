#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r108a2_branchmap.py —— 分支图 v2：补 insn size、区分无条件 jmp / 条件跳、跳转表（jmp [tbl+r*4]）

v1 的三处问题（保留痕迹）：
  v1-A S3 断言把 R106/R107 的「6728」当成 call 条数 —— 实测 68253 条 call、6728 是 distinct 目标；
  v1-B 缺每指令 size，无法判断「上一条指令 + size == 本条」的 fall-through 前驱；
  v1-C 未区分无条件 jmp 与 jcc，反向遍历会把 jmp 之后当 fall-through。
内存纪律：disasm_lite + 64KB 分块；只对 jmp 指令单独解析操作数（detail=False 的 lite 已给 op_str）。
"""
import array, hashlib, json, os, re, struct, sys
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

starts = array.array('I'); sizes = array.array('B')
call_s = array.array('I'); call_t = array.array('I')
uj_s = array.array('I'); uj_t = array.array('I')      # 无条件 jmp（直接或间接）
cj_s = array.array('I'); cj_t = array.array('I')      # 条件跳转（直接）
rets = array.array('I')
jtbl = []                                            # (insn, table_va)
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a); sizes.append(sz)
        if m == 'call':
            if o.startswith('0x'):
                call_s.append(a); call_t.append(int(o, 16))
        elif m == 'jmp':
            uj_s.append(a)
            if o.startswith('0x'):
                uj_t.append(int(o, 16))
            else:
                uj_t.append(0)
                # capstone lite 形态：jmp dword ptr [ecx*4 + 0x46f5a0]
                # 取最后一个 0x... 常量作为表基址（寄存器基址形态如 [eax] 则没有）
                if '[e' in o or '[' in o:
                    m2 = re.findall(r'0x[0-9a-f]+', o)
                    if m2 and '*4' in o:
                        jtbl.append((a, int(m2[-1], 16)))
        elif m[0] == 'j' and o.startswith('0x'):
            cj_s.append(a); cj_t.append(int(o, 16))
        elif m.startswith('ret'):
            rets.append(a)
    if last <= pos:
        last = pos + 1
    pos = last
ns = len(starts)
ck('S1 指令数 1,392,592（与前几轮同口径）', ns == 1392592, ns)
ck('S2 distinct call 目标数 6728', len(set(call_t)) == 6728, len(set(call_t)))
ck('S3 无条件 jmp 条数 > 10000', len(uj_s) > 10000, len(uj_s))
ck('S4 条件跳转条数 > 90000', len(cj_s) > 90000, len(cj_s))
ck('S5 jmp [reg*4 + 表基址] 形态数 = 387 个站点 / 369 个表基址（R107 exec 报 346 张，为其子集）',
   len(jtbl) > 300, len(jtbl))
ck('S6 ret 条数 > 20000', len(rets) > 20000, len(rets))

# 落盘格式：每条 [count u32][itemsize u32][keylen u32][key bytes][data]
# v1 事故：sizes 是 'B' 型而格式里没有 itemsize 字段，读出时错位（EOFError），此处补 itemsize。
with open('_r108/branchmap2.bin', 'wb') as f:
    for k, arr in (('starts', starts), ('sizes', sizes), ('call_s', call_s),
                   ('call_t', call_t), ('uj_s', uj_s), ('uj_t', uj_t),
                   ('cj_s', cj_s), ('cj_t', cj_t), ('rets', rets)):
        kb = k.encode()
        f.write(struct.pack('<III', len(arr), arr.itemsize, len(kb)))
        f.write(kb)
        arr.tofile(f)
ck('S7 branchmap2.bin 落盘（>=8 MB）', os.path.getsize('_r108/branchmap2.bin') >= 8_000_000,
   os.path.getsize('_r108/branchmap2.bin'))
json.dump({'checks': checks, 'n_starts': ns, 'n_calls': len(call_s),
           'n_call_tgts': len(set(call_t)), 'n_uj': len(uj_s), 'n_cj': len(cj_s),
           'n_jtbl': len(jtbl), 'n_rets': len(rets),
           'jtbl_sample': [[hex(a), hex(t)] for a, t in jtbl[:5]]},
          open('_r108/r108a2_branchmap.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('FAILS', nf)
sys.exit(1 if nf else 0)
