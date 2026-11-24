
"""K5 shared helpers: PE mapping, disasm, coverage/atlas lookup. Read-only for shared files."""
from pathlib import Path
import csv, hashlib, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
R=Path(r"D:\Project\ra2-campaign-forge")
EXE=R/"ra2youli/gamemd.exe"
COV=R/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL=R/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
CARD=R/"lead/next_re_20261117_r14/S06_K5"
DATA=EXE.read_bytes()
SHA=hashlib.sha256(DATA).hexdigest().upper()
PE=pefile.PE(str(EXE),fast_load=True)
IB=PE.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in PE.sections:
    SECS.append((IB+s.VirtualAddress, IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s.PointerToRawData, s.SizeOfRawData))
def off(va):
    for a,b,p,r in SECS:
        if a<=va<b:
            d=va-a
            return p+d if d<r else None
    return None
def at(va,n):
    o=off(va)
    if o is None or o+n>len(DATA): return None
    return DATA[o:o+n]
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=False
def dis(va,n,count=10000):
    b=at(va,n)
    return [] if b is None else list(MD.disasm(b,va,count=count))
def fmt(ins): return f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}"
def cov_rows(): return list(csv.DictReader(open(COV,encoding='utf-8',newline=''),delimiter='\t'))
def atl_rows(): return list(csv.DictReader(open(ATL,encoding='utf-8',newline=''),delimiter='\t'))
def cov_map(): return {r['entry'].upper():r for r in cov_rows()}
def atl_map(): return {r['entry'].upper():r for r in atl_rows()}
def norm(x): return x.strip().lower()
