#!/usr/bin/env python3
# W61: check ra2md.csf / ra2.csf for TUT1 / Tutorial / BootCamp labels (Q4).
import os,struct,re
sys_path=r"D:\Project\ra2-campaign-forge"
import sys; sys.path.insert(0,sys_path)
from ra2forge.mixlib import MixFile
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W61_third_badge_route\work"
for mix in ["langmd.mix","language.mix"]:
    m=MixFile(os.path.join(r"D:\Project\ra2-campaign-forge\ra2bench",mix))
    for e in m.entries:
        b=m.read_entry(e)
        if b[:4] in (b" FSC",b" FSC"[::-1]) or b[:4]==b" FSC":
            print("=== %s entry %08X size=%d (CSF) ==="%(mix,e.id,len(b)))
            open(os.path.join(OUT,"%s_%08X.csf"%(mix,e.id)),"wb").write(b)
            # CSF label = ASCII NUL-terminated string right after 'LBL ' marker
            for mm in re.finditer(rb"LBL ",b):
                s=b[mm.end():b.find(b"\x00",mm.end())]
                if re.search(rb"(?i)tut|boot|camp|desc",s):
                    print("   label=%r"%s)
            # raw context around TUT1 / Tutorial / BootCamp
            for kw in [b"TUT1",b"Tutorial",b"BootCamp",b"DESC:"]:
                for mm in re.finditer(re.escape(kw),b,re.I):
                    lo=max(0,mm.start()-40); hi=min(len(b),mm.end()+60)
                    print("   ctx %-10s @0x%X : %r"%(kw.decode(),mm.start(),b[lo:hi]))
    m.close()
