#!/usr/bin/env python3
# W61: extract wdt.mix GraphicMenu INI entries and dump CSF TUT1/Tutorial context.
import sys, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
from ra2forge.mixlib import MixFile
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W61_third_badge_route\work"
m=MixFile(r"D:\Project\ra2-campaign-forge\ra2bench\wdt.mix")
for e in m.entries:
    if e.id in (0xA91DA00A,0xC3F03F0D):
        b=m.read_entry(e)
        p=os.path.join(OUT,"wdt_%08X.txt"%e.id)
        open(p,"wb").write(b)
        print("=== wdt.mix entry %08X size=%d -> %s ===" % (e.id,e.size,p))
        txt=b.decode("latin1")
        print(txt[:6000])
m.close()
