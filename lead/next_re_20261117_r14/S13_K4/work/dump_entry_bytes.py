#!/usr/bin/env python3
"""Dump all 240 S13 entries: entry bytes, classify stub patterns. Read-only."""
import csv, os, struct
import pefile
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
TARGETS = os.path.join(ROOT, r"lead\next_re_20261117_r14\S13_K4\TARGETS.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\S13_K4\EVIDENCE\entry_bytes.tsv")

pe = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = pe.OPTIONAL_HEADER.ImageBase
def rva2off(rva):
    return pe.get_offset_from_rva(rva)
def read_va(va, n):
    rva = va - IMAGE_BASE
    off = rva2off(rva)
    return open(EXE,"rb").read()[off:off+n]
# faster: load whole file once
f = open(EXE,"rb"); DATA = f.read(); f.close()
def rd(va,n):
    off = pe.get_offset_from_rva(va-IMAGE_BASE)
    return DATA[off:off+n]

rows=[]
with open(TARGETS,encoding="utf-8",errors="replace") as fh:
    for r in csv.DictReader(fh,delimiter="\t"):
        rows.append(r)

def classify(b):
    # b = bytes at entry
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3:
        imm=struct.unpack("<I",b[1:5])[0]
        return ("B8imm_C3", imm)
    if len(b)>=2 and b[0]==0xC3:
        return ("C3",0)
    if len(b)>=3 and b[0]==0x33 and b[1]==0xC0 and b[2]==0xC3:
        return ("xor_eax,eax_C3",0)
    if len(b)>=3 and b[:3]==b'\x32\xC0\xC3':
        return ("xor_al,al_C3",0)
    if len(b)>=5 and b[0]==0x6A and b[2]==0xC3:  # not typical
        pass
    return ("other", None)

with open(OUT,"w",encoding="utf-8",newline="") as fh:
    w=csv.writer(fh,delimiter="\t",lineterminator="\n")
    w.writerow(["entry","name","grade","proved","atlas_size","n_instr","bytes16","pattern","imm","semantics"])
    for r in rows:
        va=int(r["entry"],16)
        b=rd(va,16)
        pat,imm=classify(b)
        w.writerow([r["entry"],r["name"],r["grade"],r["proved"],r["atlas_size"],r["n_instr"],b.hex(),pat,("" if imm is None else hex(imm)),r["semantics"]])
print("wrote", OUT)
# summary
from collections import Counter
ct=Counter()
imm_list=[]
with open(OUT,encoding="utf-8",errors="replace") as fh:
    for r in csv.DictReader(fh,delimiter="\t"):
        ct[r["pattern"]]+=1
        if r["pattern"]=="B8imm_C3": imm_list.append((r["entry"],r["name"],r["imm"],r["grade"]))
print("pattern counts:", dict(ct))
print("\nB8imm_C3 entries (", len(imm_list),"):")
for e in imm_list: print("  ", e)
