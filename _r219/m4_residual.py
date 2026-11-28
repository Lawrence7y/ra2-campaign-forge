# -*- coding: utf-8 -*-
"""R219 m4：11 处残余 C_neither 位点（s 在 273..337，属合法槽域但前驱读不到 vftable）逐点定性。

方法：对每个位点，向后最多 200 条指令跟踪 base 寄存器的「最后一次定义」，
用寄存器数据流（不做全 CFG），分类：
  - from_vtable_load : mov base, dword ptr [obj+0]         （已在 m2/m3 覆盖，本类应 0）
  - from_indirect_ld : mov base, dword ptr [obj+X] X!=0    （读对象的二级指针/内嵌子对象 vftable 槽）
  - from_imm         : mov/lea base, imm32 / [reg+disp] 常量基址
  - from_arg         : mov base, dword ptr [ebp+8] 等（函数参数）
  - from_call_ret    : base 由 call 返回值（eax）得到
  - from_pop/other   : 其余

正控：把同一规则跑在 0x414471 上必须得 from_vtable_load（前驱 mov edx,[esi]）。
反控：把窗口缩到 1 条指令时，正控必须变成 not_found（证明窗口确实在起作用）。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
T = P.B['.text']; LO, RAWOFF, RAWSZ = T['lo'], T['rawptr'], T['rawsize']
raw = P.RAW[RAWOFF:RAWOFF + RAWSZ]
insns = []
pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        insns.append((a, mn, ops)); pos += sz; got = True; break
    if not got: pos += 1
IDX = {a: i for i, (a, _, _) in enumerate(insns)}
print('[0] insns=%d' % len(insns))

SITES = [0x43e2ff, 0x43e36f, 0x43e40a, 0x43e5c6, 0x43e759,
         0x50d97e, 0x519286,
         0x759f90, 0x759fa0, 0x75a3c9, 0x75a3d1]
GPR = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')
BASE_RE = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)
MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)

def base_of(ops):
    mm = MEM_RE.search(ops)
    if not mm: return None, None
    m = BASE_RE.match(mm.group(1).strip())
    if not m: return None, None
    return m.group(1).lower(), (int(m.group(2), 0) if m.group(2) else 0)

def trace(idx, base, win=200):
    lo = max(0, idx - win)
    for a2, m2, o2 in reversed(insns[lo:idx]):
        dst = o2.split(',')[0].strip() if ',' in o2 else o2.strip()
        # only count if this instruction writes `base`
        writes_base = False
        if m2 in ('mov', 'lea', 'xor', 'and', 'or', 'add', 'sub', 'inc', 'dec', 'pop', 'movzx', 'movsx', 'imul'):
            if m2 in ('pop',):
                writes_base = (o2.strip() == base)
            elif m2 in ('inc', 'dec'):
                writes_base = (dst == base)
            else:
                writes_base = (dst == base)
        if not writes_base:
            continue
        src = o2.split(',', 1)[1].strip() if ',' in o2 else ''
        if m2 == 'mov' and 'dword ptr [' in src:
            bb, dd = base_of(src)
            if bb in GPR:
                return ('from_vtable_load' if dd == 0 else 'from_indirect_ld'),
                '%#x %s %s' % (a2, m2, o2)
        if m2 == 'mov' and re.match(r'^0x[0-9a-f]+$', src, re.I):
            return 'from_imm', '%#x %s %s' % (a2, m2, o2)
        if m2 == 'lea' and '[' in src:
            return 'from_lea', '%#x %s %s' % (a2, m2, o2)
        if m2 == 'mov' and '[' in src:
            return 'from_mem_other', '%#x %s %s' % (a2, m2, o2)
        if m2 == 'xor' and src == base:
            return 'from_zero', '%#x %s %s' % (a2, m2, o2)
        if m2 == 'pop':
            return 'from_pop', '%#x %s %s' % (a2, m2, o2)
        return 'from_reg_%s' % m2, '%#x %s %s' % (a2, m2, o2)
    return 'not_found', None

print('\n[1] residual C_neither sites (%d):' % len(SITES))
rows = []
for a in SITES:
    i = IDX[a]
    _, mn, ops = insns[i]
    base, disp = base_of(ops)
    if base is None:
        print('   %#x  base unparsable: %s %s' % (a, mn, ops)); continue
    kind, ev = trace(i, base)
    print('   %#x %-26s base=%s disp=0x%03x s=%3d -> %-18s %s'
          % (a, mn + ' ' + ops, base, disp, disp // 4, kind, ev))
    rows.append(dict(addr=hex(a), insn=mn + ' ' + ops, base=base, disp=hex(disp),
                     s=disp // 4, kind=kind, ev=ev))

print('\n[2] positive control 0x414471 with window=200 / win=1:')
i = IDX[0x414471]
print('   win=200 ->', trace(i, 'edx', 200))
print('   win=1   ->', trace(i, 'edx', 1))

# --- extra: are these 11 reached from the same 5 functions? report containing func start ---
def func_start(a, window=4096):
    o = P.r2o(a); lo = max(P.r2o(LO), o - window); i = o - 1
    while i > lo:
        if P.RAW[i - 1] == 0xCC and P.RAW[i] == 0xCC:
            j = i
            while j < o and P.RAW[j] == 0xCC: j += 1
            return j + (LO - P.B['.text']['rawptr'])
        i -= 1
    return None
print('\n[3] containing function start (CC-padding rule, window 4096):')
fs = collections.Counter()
for a in SITES:
    f = func_start(a); fs[f] += 1
    print('   %#x -> %s' % (a, hex(f) if f else None))
print('   distinct funcs = %d' % len(fs))

json.dump(rows, open('/home/t628/projects/ra2-campaign-forge/_r219/m4.json', 'w'), indent=1)
print('\n[done] -> _r219/m4.json')
