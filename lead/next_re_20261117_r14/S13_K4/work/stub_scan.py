#!/usr/bin/env python3
"""Enumerate ALL constant-return stub patterns in 240 S13 functions (skipdata=False, fixed size).
Patterns: B8 imm32 C3; B0/B1 imm8 C3; 33C0C3; 32C0C3; B8 imm32 ret variants; A1 moffs C3.
Also dump disasm of all tiny funcs (<=8 bytes) for manual review. Read-only."""
import csv, os, struct
import pefile
from capstone import *
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
TARGETS = os.path.join(ROOT, r"lead\next_re_20261117_r14\S13_K4\TARGETS.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\S13_K4\EVIDENCE\stub_scan.tsv")
pe = pefile.PE(EXE, fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(EXE,'rb').read()
def rd(va,n):
    off=pe.get_offset_from_rva(va-IB); return DATA[off:off+n]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=False

rows=list(csv.DictReader(open(TARGETS,encoding="utf-8",errors="replace"),delimiter="\t"))
results=[]
for r in rows:
    va=int(r["entry"],16); sz=int(r["atlas_size"])
    b=rd(va,min(sz,64))
    # constant-return stub analysis on first bytes
    tag=""; imm=None
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3: tag="B8imm32_C3"; imm=struct.unpack('<I',b[1:5])[0]
    elif len(b)>=3 and b[0] in (0xB0,0xB1,0xB2,0xB3) and b[2]==0xC3: tag="BxImm8_C3"; imm=b[1]
    elif len(b)>=3 and b[:3]==b'\x33\xc0\xc3': tag="xor_eax_C3"; imm=0
    elif len(b)>=3 and b[:3]==b'\x32\xc0\xc3': tag="xor_al_C3"; imm=0
    elif len(b)>=6 and b[0]==0xA1 and b[5]==0xC3: tag="A1_moffs_C3"; imm=struct.unpack('<I',b[1:5])[0]+IB
    elif len(b)>=2 and b[0]==0xC3: tag="C3"
    # disasm first up to 12 instructions
    dis=[]
    for ins in md.disasm(b,va):
        dis.append(f"{ins.address:08X}:{ins.mnemonic} {ins.op_str}")
        if len(dis)>=12: break
    results.append((r["entry"],r["name"],r["grade"],r["proved"],str(sz),tag,"" if imm is None else hex(imm)," | ".join(dis)))

with open(OUT,"w",encoding="utf-8",newline="") as fh:
    w=csv.writer(fh,delimiter="\t",lineterminator="\n")
    w.writerow(["entry","name","grade","proved","atlas_size","pattern","imm","disasm"])
    for x in results: w.writerow(x)
print("wrote",OUT)
from collections import Counter
print("patterns:",dict(Counter(x[5] for x in results)))
# list all non-other stubs
for x in results:
    if x[5]: print(x[0],x[5],x[6],x[1],x[2])
