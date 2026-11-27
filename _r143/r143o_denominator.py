#!/usr/bin/env python3
"""R143 O：口径分歧定点复算 —— 「ptr-like 分母」的三种定义，以及它们对 0/4 倍比的影响。

审计员（deepseek #316）报 rate_given_ptrlike0 = 0.9422、rate_given_ptrlike4 = 0.0729，
主会话（r143n）报 0.9354 / 0.1982 —— 同一对数字差 2.7 倍。本脚本把分母的三种定义都算出来，
判定分歧来自定义还是来自错：
  D-A 「最近定义」法：装载后该寄存器未被任何写者改写（含 call 破坏 eax/ecx/edx）直到被用作内存基址
  D-B 「窗口」法：装载后 <=12 条指令内该寄存器被用作内存基址（不改写检查）
  D-C 「全程序」法：该装载的目的寄存器在整个 .text 内至少被用作一次内存基址（最宽）
判据：三分母下 0 位的 feed 率是否都显著高于 4 位；以及 4 位的分母差多少。
"""
import sys, json, collections
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()

def parse(a, sz, mn, op):
    if not op: return ('nop', None)
    if mn in ('call', 'jmp'):
        m = L.RE_CALL.match(op)
        if m and m.group(1) in L.GEN: return ('disp', (m.group(1), L.disp_of(m.group(2)), mn))
        return ('callother', None)
    m = L.RE_LOAD.match(op)
    if m and mn == 'mov':
        base = m.group(2)
        cls = 'obj' if base in L.GEN else ('stack' if base in L.STK else 'other')
        return ('load', (m.group(1), base, L.disp_of(m.group(3)), cls))
    ms = L.RE_STORE.match(op)
    if ms and mn in ('mov', 'movl'):
        base = ms.group(1)
        cls = 'obj' if base in L.GEN else ('stack' if base in L.STK else 'other')
        return ('store', (base, L.disp_of(ms.group(2)), cls))
    if mn in L.W_MN: return ('write', op.partition(',')[0])
    if mn in ('ret', 'retn'): return ('ret', None)
    return ('other', None)

ins = list(B.sweep(md)); P = [parse(*x) for x in ins]; N = len(P)

# 收集全部对象类装载
L_obj = []   # (idx, va, dst, disp)
for i, (k, d) in enumerate(P):
    if k == 'load' and d[3] == 'obj':
        L_obj.append((i, ins[i][0], d[0], d[2]))
pos = {va: (i, dst, disp) for i, va, dst, disp in L_obj}

# D-A：最近定义法（严格，遇 call 清 eax/ecx/edx；遇任何写者清该寄存器）
fedA = set(); ptrA = set()
last = {}
for i, (k, d) in enumerate(P):
    if k == 'disp':
        base = d[0]; l = last.get(base)
        if l:
            ptrA.add(l)
            fedA.add(l)   # 该装载被用作派发基址
        for x in ('eax', 'ecx', 'edx'): last.pop(x, None)
    elif k == 'callother':
        for x in ('eax', 'ecx', 'edx'): last.pop(x, None)
    elif k in ('store',):
        base = d[0]
        if base in L.GEN:
            l = last.get(base)
            if l: ptrA.add(l)
    elif k == 'load':
        dst, base, ds, cls = d
        if base in L.GEN:
            l = last.get(base)
            if l: ptrA.add(l)
        if dst in L.GEN: last[dst] = ins[i][0]
    elif k == 'write':
        last.pop(d, None)

# D-B：窗口法（<=12 条）
ptrB = set(); fedB = set(fedA)
for i, va, dst, disp in L_obj:
    for j in range(i + 1, min(N, i + 13)):
        k, d = P[j]
        if k == 'load' and d[1] == dst: ptrB.add(va); break
        if k == 'disp' and d[0] == dst: ptrB.add(va); break
        if k == 'store' and d[0] == dst: ptrB.add(va); break
        if k == 'ret': break

# D-C：全程序法（只要该寄存器名在任一内存操作数里出现作基址）
regisbase = set()
for k, d in P:
    if k == 'disp': regisbase.add(d[0])
    elif k == 'load': regisbase.add(d[1])
    elif k == 'store': regisbase.add(d[0])
ptrC = {va for i, va, dst, disp in L_obj if dst in regisbase}

def rate(num_set, den_set, disp, cls='obj'):
    tot = [x for x in L_obj if x[3] == disp]
    den = [x for x in tot if den_set is None or x[1] in den_set]
    num = [x for x in tot if x[1] in num_set]
    return len(den), len(num), (round(len(num) / len(den), 4) if den else None)

rows = {}
for tag, den in (('A_recent_def', ptrA), ('B_window12', ptrB), ('C_any_base', ptrC)):
    rows[tag] = {str(d): rate(fedA, den, d) for d in (0, 4, 8, 12, 16)}
res = {'obj_loads_total': len(L_obj),
       'disp_hist': dict(collections.Counter(x[3] for x in L_obj)),
       'n_ptrA': len(ptrA), 'n_ptrB': len(ptrB), 'n_ptrC': len(ptrC),
       'n_fedA': len(fedA), 'rows': rows}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143o_denominator.json', 'w'), ensure_ascii=False, indent=1)
