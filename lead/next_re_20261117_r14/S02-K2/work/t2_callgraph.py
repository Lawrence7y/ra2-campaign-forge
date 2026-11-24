# -*- coding: utf-8 -*-
"""S02-K2 / T2: build call graph among atlas functions; find unnamed S02 targets that are
called by >=2 named CRT anchors, or that call named anchors, as evidence for naming."""
import os, sys, re, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C
import pefile

# build atlas map entry->size (data lines), and identify S02 targets / CRT anchors
ATL = C.ATL
atlas = {}
with open(ATL, encoding='utf-8', errors='replace') as f:
    f.readline()
    for ln in f:
        p=ln.rstrip('\n').split('\t')
        if len(p)>=2:
            atlas[C.norm(p[0])] = int(p[1]) if p[1].strip().isdigit() else 0

targets = {r['entry']:r for r in C.load_targets()}
named = {a for a,r in targets.items() if r['named_L']=='1'}
crt_named = {a for a in named if targets[a]['cov_name'].startswith('CRT::')}

# read whole .text bytes once
pe = C.pe_obj
TEXT = pe.sections[0]
text_va = C.rva2va(TEXT.VirtualAddress)
text_bytes = pe.__data__[TEXT.PointerToRawData:TEXT.PointerToRawData+TEXT.SizeOfRawData]

def calls_in(va, size):
    """return set of direct call/jmp rel32 targets within a function body"""
    off = va - text_va
    if off < 0 or off >= len(text_bytes): return set()
    b = text_bytes[off:off+min(size, 4096)]
    out=set()
    for ins in C.md.disasm(b, va):
        if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
            try: out.add(int(ins.op_str,16))
            except: pass
    return out

# For each S02 target, get its direct callees
callees = {}
for a,r in targets.items():
    size = atlas.get(a,0)
    if size<=0: continue
    callees[a] = calls_in(int(a,16), size)

# reverse: who calls each address
callers = collections.defaultdict(set)
for a, cs in callees.items():
    for c in cs:
        callers[C.norm('%08X'%c)].add(a)

print("S02 targets with atlas size:",len(callees))
print("CRT named anchors:",len(crt_named))
print("\n=== unnamed S02 targets CALLED BY named CRT anchors ===")
res=[]
for a,r in targets.items():
    if r['named_L']!='0': continue
    crt_callers = sorted(callers.get(a,set()) & crt_named)
    if crt_callers:
        res.append((a,crt_callers,callees.get(a,set())))
        print("0x%s called by CRT anchors %s  callees=%s" %
              (a, ['0x%s(%s)'%(c,targets[c]['cov_name']) for c in crt_callers],
               sorted('0x%X'%c for c in callees.get(a,set()) if C.norm('%08X'%c) in targets)[:8]))
print("\ntotal such:",len(res))

print("\n=== named CRT anchors' direct callees that are unnamed S02 ===")
for a in sorted(crt_named):
    un = sorted(c for c in callees.get(a,set()) if C.norm('%08X'%c) in targets and targets[C.norm('%08X'%c)]['named_L']=='0')
    if un:
        print("0x%s(%s) -> %s" % (a, targets[a]['cov_name'], [('0x%X'%c) for c in un]))
