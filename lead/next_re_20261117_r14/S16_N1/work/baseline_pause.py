# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_N1\work")
import re_tools as R
# pattern for 0x6CE280: 56 8B 31 83 FE FF 74 ?? 8B 41 08 83 FE FF 74 ?? 8B 15 ... 2B D6 3B D0 7D ?? 2B C2 C7 01 FF FF FF FF 89 41 08 5E C3
pat = bytes.fromhex("568b3183feff748b410883feff748b1584eda8002bd63bd07d2bc2c701ffffffff8941085ec3")
# more robust: use regex over .text raw bytes allowing ?? for branch offsets
import re
rx = re.compile(rb'\x56\x8b\x31\x83\xfe\xff\x74.\x8b\x41\x08\x83\xfe\xff\x74.\x8b\x15\x84\xed\xa8\x00\x2b\xd6\x3b\xd0\x7d.\x2b\xc2\xc7\x01\xff\xff\xff\xff\x89\x41\x08\x5e\xc3', re.S)
for va,vs,rs,ptr,nm in R.SECTS:
    if '.text' not in nm: continue
    with open(R.PE_PATH,'rb') as f: f.seek(ptr); data=f.read(min(vs,rs))
    hits=[va+m.start() for m in rx.finditer(data)]
    print(nm,'signature hits',len(hits),[hex(x) for x in hits[:20]])
# control: how many functions in .text have the same first 8 bytes
rx2 = re.compile(rb'\x56\x8b\x31\x83\xfe\xff\x74.\x8b\x41\x08', re.S)
for va,vs,rs,ptr,nm in R.SECTS:
    if '.text' not in nm: continue
    with open(R.PE_PATH,'rb') as f: f.seek(ptr); data=f.read(min(vs,rs))
    hits=[va+m.start() for m in rx2.finditer(data)]
    print('prefix-8 hits',len(hits),[hex(x) for x in hits[:30]])
