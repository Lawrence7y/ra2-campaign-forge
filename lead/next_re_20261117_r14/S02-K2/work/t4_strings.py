# -*- coding: utf-8 -*-
"""S02-K2 / T4: find except.txt string(s), xrefs, exception handler installation APIs."""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

pe = C.pe_obj
data = pe.__data__

def find_ascii(s):
    """find all file offsets of an ascii/bytes string"""
    b = s.encode('latin-1') if isinstance(s,str) else s
    out=[]; i=0
    while True:
        j=data.find(b,i)
        if j<0: break
        out.append(j); i=j+1
    return out

def off2va(off):
    for sec in pe.sections:
        if sec.PointerToRawData <= off < sec.PointerToRawData+sec.SizeOfRawData:
            return C.rva2va(sec.VirtualAddress + (off-sec.PointerToRawData)), sec.Name.decode('latin-1')
    return None,None

out=[]
out.append("=== T4: except.txt / crash-log string search ===")
for needle in ["except.txt","except", "EXCEPT", "crash", "access violation", "Access violation",
               "Exception", "exception", ".dmp", "minidump", "fatal error", "FATAL"]:
    offs = find_ascii(needle)
    out.append("needle %-20r : %d hit(s)" % (needle, len(offs)))
    for o in offs[:20]:
        va,sec=off2va(o)
        out.append("   off=0x%X va=%s sec=%s ctx=%r" % (o, ('0x%08X'%va) if va else '?', sec, data[max(0,o-40):o+60]))

# exception-related imports
out.append("\n=== exception-related IAT imports ===")
iat=C.build_iat_map()
for va,(dll,fn) in sorted(iat.items()):
    if any(k in fn.lower() for k in ['exception','unhandled','vectored','raise','terminate','abort','debugbreak','unwind','stackwalk','minidump','fatal']):
        out.append("  0x%08X %s!%s" % (va,dll,fn))

msg="\n".join(out)
print(msg)
with open(os.path.join(C.CARD,"EVIDENCE","T4_string_search.txt"),"w",encoding="utf-8") as f:
    f.write(msg+"\n")
