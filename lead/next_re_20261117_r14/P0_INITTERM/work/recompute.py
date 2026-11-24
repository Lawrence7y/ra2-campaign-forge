#!/usr/bin/env python3
"""P0-INITTERM independent recompute of the 4 core numbers (auditor-facing).
Read-only. deps: pefile 2024.8.26, capstone 5.0.7 (skipdata=True unused here but flag set).
"""
import hashlib, struct, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
COV = ROOT + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL = ROOT + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
assert hashlib.sha256(open(EXE,"rb").read()).hexdigest().upper() == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE,"rb").read()
def dword(va):
    rva=va-IB
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return struct.unpack_from("<I", data, s.PointerToRawData+(rva-s.VirtualAddress))[0]
    raise ValueError(hex(va))

# 1) table count
BEGIN, END = 0x812000, 0x815DA4
slots = (END-BEGIN)//4
assert dword(BEGIN)==0
n = sum(1 for i in range(1,slots) if dword(BEGIN+4*i)!=0)
print("1) slots=%d  null0=%d  FUNC(non-null)=%d  (audit 3944: %s)"%(slots, dword(BEGIN)==0, n, n==3944))

# 2) coverage / atlas membership
cov=set(); atl=set()
for f,out in ((COV,cov),(ATL,atl)):
    for line in open(f,encoding="utf-8"):
        p=line.split("\t")
        if p and p[0]: out.add(p[0].strip().upper())
n_cov=n_atl=0
for i in range(1,slots):
    t="%08X"%dword(BEGIN+4*i)
    if t in cov: n_cov+=1
    if t in atl: n_atl+=1
print("2) in_coverage=%d (audit 22: %s)  in_atlas=%d (audit 2: %s)"%(n_cov,n_cov==22,n_atl,n_atl==2))
print("   not_in_coverage=%d (audit 3922: %s)"%(n-n_cov, n-n_cov==3922))

# 3) current coverage data rows
rows=sum(1 for _ in open(COV,encoding="utf-8"))-1
print("3) coverage data rows=%d"%rows)

# 4) two denominators
print("4) caliber A (contains thunks) = %d + %d = %d"%(rows, n-n_cov, rows+n-n_cov))
print("   caliber B (excludes thunks) = %d - %d = %d"%(rows, n_cov, rows-n_cov))
