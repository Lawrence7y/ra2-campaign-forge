# -*- coding: utf-8 -*-
"""S02-K2 / T3: SBH / CRT memory pool globals. Find xrefs/writers of heap-handle globals,
HeapCreate, and nearby descriptor globals; dump heap init region."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C
import bisect

pe=C.pe_obj; TEXT=pe.sections[0]
tva=C.rva2va(TEXT.VirtualAddress); tb=pe.__data__[TEXT.PointerToRawData:TEXT.PointerToRawData+TEXT.SizeOfRawData]

atlas=[]
with open(C.ATL,encoding='utf-8',errors='replace') as f:
    f.readline()
    for ln in f:
        p=ln.rstrip().split('\t')
        if len(p)>=2 and p[1].strip().isdigit(): atlas.append((int(C.norm(p[0]),16),int(p[1])))
atlas.sort(); starts=[a for a,_ in atlas]
def owner(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and va<starts[i]+atlas[i][1]: return "0x%08X"%starts[i]
    return "GAP"

# globals of interest from CRT heap code
GLOB = {
 0x00B782C4:"heap_handle(malloc)", 0x00B78298:"crt_locale/lock?",
 0x00822D80:"fp_rounding_word", 0x008A3008:"sbh?", 
}
IAT = {0x7E1298:"HeapCreate",0x7E1278:"HeapAlloc",0x7E127C:"HeapFree",
       0x7E12A0:"HeapSize",0x7E12A4:"HeapReAlloc",0x7E1190:"HeapDestroy"}

out=[]
out.append("=== T3: full .text sweep for heap globals / HeapCreate xrefs ===")
hits=collections.defaultdict(list); n=0
for ins in C.md.disasm(tb,tva):
    n+=1
    ops=ins.op_str.lower()
    for g,name in GLOB.items():
        if ("0x%x"%g) in ops:
            hits[name].append((ins.address,ins.mnemonic,ins.op_str,owner(ins.address)))
    for g,name in IAT.items():
        if ("[0x%x]"%g) in ops:
            hits[name].append((ins.address,ins.mnemonic,ins.op_str,owner(ins.address)))
out.append("instructions: %d"%n)
for name,hl in hits.items():
    out.append("\n-- %s : %d refs --"%(name,len(hl)))
    for ad,m,o,own in hl[:40]:
        out.append("  0x%08X %-8s %-40s fn=%s"%(ad,m,o,own))

msg="\n".join(out)
print(msg[:6000])
with open(os.path.join(C.CARD,"EVIDENCE","T3_heap_globals.txt"),"w",encoding="utf-8") as f:
    f.write(msg+"\n")
