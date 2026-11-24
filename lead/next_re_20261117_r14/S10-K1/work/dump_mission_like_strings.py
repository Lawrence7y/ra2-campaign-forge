#!/usr/bin/env python3
"""S10-K1: dump strings from .rdata that look like mission names / a mission enum name table."""
import re
import pefile

EXE = r"ra2youli\gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE,'rb').read()

sections=[]
for s in pe.sections:
    n=s.Name.decode(errors='replace').rstrip('\x00')
    sections.append((n, IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

def off_to_va(o):
    for n,v,vs,r,rs in sections:
        if r<=o<r+rs: return v+(o-r)
    return None

for secname in ('.rdata','.data'):
    for n,v,vs,r,rs in sections:
        if n!=secname: continue
        blob=data[r:r+rs]
        strings=[]
        for m in re.finditer(rb'[ -~]{3,}', blob):
            s=m.group().decode('ascii')
            strings.append((r+m.start(), s))
        print("=== %s : %d strings ===" % (secname, len(strings)))
        kws=['mission','sleep','hunt','unload','sabotage','construct']
        names=['move','attack','guard','harvest','return','stop','capture','enter','fire']
        for o,s in strings:
            low=s.lower()
            isname = (low in names) or any(('mission' in low and len(s)<30) for _ in [0])
            iskw = any(k in low for k in kws)
            if (isname or iskw) and len(s)<50:
                print("  0x%08X: %r" % (off_to_va(o) or 0, s))
