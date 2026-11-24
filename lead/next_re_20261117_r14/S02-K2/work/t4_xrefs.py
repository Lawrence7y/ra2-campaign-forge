# -*- coding: utf-8 -*-
"""S02-K2 / T4: full .text capstone sweep (skipdata) -> xrefs to exception strings and IAT."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

pe=C.pe_obj; TEXT=pe.sections[0]
tva=C.rva2va(TEXT.VirtualAddress); tb=pe.__data__[TEXT.PointerToRawData:TEXT.PointerToRawData+TEXT.SizeOfRawData]

# addresses of interest
INTEREST = {
    0x008221F8:"STR_except.txt", 0x00821F78:"STR_context_eip_bad",
    0x00821FE4:"STR_Exceptionoccurred", 0x00822074:"STR_FoundExcDesc",
    0x008220B4:"STR_SymInit_failed", 0x008220C1:"STR_access_violation",
    0x008205A:"STR_AccessAddress", 0x0082219C:"STR_Dump_exception_info",
    0x008221BF:"STR_Exception_Dialog", 0x00821CD2:"STR_Recursive_exception",
    0x00820F09:"STR_ErrorCode_table",
    0x007E1144:"IAT_SetUnhandledExceptionFilter", 0x007E12C0:"IAT_RaiseException",
    0x007E1268:"IAT_RtlUnwind", 0x007E12EC:"IAT_UnhandledExceptionFilter",
    0x007E11B0:"IAT_TerminateProcess", 0x007E134C:"IAT_FatalAppExitA",
    0x007E1278:"IAT_HeapAlloc", 0x007E127C:"IAT_HeapFree",
}

# atlas for function attribution via interval containment
atlas=[]
with open(C.ATL,encoding='utf-8',errors='replace') as f:
    f.readline()
    for ln in f:
        p=ln.rstrip('\n').split('\t')
        if len(p)>=2 and p[1].strip().isdigit():
            atlas.append((int(C.norm(p[0]),16), int(p[1])))
atlas.sort()
import bisect
starts=[a for a,_ in atlas]
def owner(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and va<starts[i]+atlas[i][1]:
        return "0x%08X"%starts[i]
    return "ATLAS_GAP"

hits=[]
nins=0
for ins in C.md.disasm(tb,tva):
    nins+=1
    ops=ins.op_str
    found=[]
    # immediate operand equal to interest, or memory [imm]
    for imm,name in INTEREST.items():
        pat="0x%x"%imm
        if pat in ops.lower() or ("0x%08x"%imm) in ops.lower():
            found.append(name)
    if found:
        hits.append((ins.address,ins.mnemonic,ops,found,owner(ins.address)))

print("total instructions:",nins)
print("xref hits:",len(hits))
for ad,m,o,f,own in hits:
    print("0x%08X  %-8s %-40s  %-40s fn=%s"%(ad,m,o[:40],",".join(f),own))

with open(os.path.join(C.CARD,"EVIDENCE","T4_xrefs.txt"),"w",encoding="utf-8") as fo:
    fo.write("total instructions: %d\nxref hits: %d\n"%(nins,len(hits)))
    for ad,m,o,f,own in hits:
        fo.write("0x%08X\t%s\t%s\t%s\t%s\n"%(ad,m,o,",".join(f),own))
