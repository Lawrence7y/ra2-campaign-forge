# -*- coding: utf-8 -*-
import sys,struct
sys.stdout.reconfigure(encoding="utf-8")
import pefile
from capstone import *
from capstone.x86 import X86_INS_CALL
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=ROOT+r"\lead\next_re_20261117_r14\S03_DIRECT"
BIN=ROOT+r"\ra2youli\gamemd.exe"
data=open(BIN,"rb").read()
pe=pefile.PE(BIN)
sec=[s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text"][0]
BASE=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress
NB=sec.Misc_VirtualSize
code=data[sec.PointerToRawData:sec.PointerToRawData+NB]
# rebuild boundary set fresh
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=False
boundaries=set()
for insn in md.disasm(code,BASE):
    boundaries.add(insn.address)
lines=open(OUT+r"\EVIDENCE\direct_call_sites_clean.tsv",encoding="utf8").read().splitlines()[1:]
bad=0; notboundary=0
for l in lines:
    c=l.split("\t")
    site=int(c[0],16)
    # cols: site caller caller_grade bytes5 rel32 target status
    tgt=int(c[5],16); status=c[6]
    off=site-BASE
    b=code[off:off+5]
    rel=struct.unpack("<i",b[1:5])[0]
    if b[0]!=0xE8 or site+5+rel!=tgt: bad+=1
    if site not in boundaries: notboundary+=1
print("re-verify sites",len(lines),"byte-mismatch",bad,"not-at-boundary",notboundary)
