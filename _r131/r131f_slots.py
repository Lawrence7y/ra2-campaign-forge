#!/usr/bin/env python3
# R131 r131f: focused print of the loop's IAT slots + the "why LoadLibrary" hypothesis test.
# Also verify the branch condition bytes: test al,0x14 / je, and control that an
# unrelated flag value would take the OTHER path (byte-level only).
import json
import pefile
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
pe=pefile.PE(EXE)
imp={}
for e in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]):
    for i in e.imports:
        if i.address: imp[i.address]=(e.dll.decode(errors='replace'), (i.name.decode() if i.name else '#%d'%i.ordinal))
for s in (0x7e1220,0x7e1224,0x7e1250,0x7e1254,0x7e124c,0x7e1600,0x7e15fc,0x7e15f8):
    print(hex(s), imp.get(s))
