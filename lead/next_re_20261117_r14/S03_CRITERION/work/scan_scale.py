
# -*- coding: utf-8 -*-
# S03-CRITERION: independent scan. No import of other cards' work code.
import json, sys, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
COV = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATL = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'

blob = open(EXE,'rb').read()
print('sha256', hashlib.sha256(blob).hexdigest().upper(), len(blob))
pe = pefile.PE(EXE, fast_load=True)
secs = {}
for s in pe.sections:
    name = s.Name.rstrip(b'\x00').decode('latin1')
    secs[name] = (s.VirtualAddress + pe.OPTIONAL_HEADER.ImageBase, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
print('sections', {k:(hex(v[0]),hex(v[1])) for k,v in secs.items()})
base = pe.OPTIONAL_HEADER.ImageBase
tva, tvsize, tpr, trs = secs['.text']
TEXT_LO, TEXT_HI = tva, tva + tvsize
text = blob[tpr:tpr+trs][:tvsize]
rva = secs.get('.rdata') or secs.get('.data')
RTVA, RVS, RPR, RRS = rva
rdata = blob[RPR:RPR+RRS]
RDATA_LO, RDATA_HI = RTVA, RTVA+RVS
def d32(buf, lo, va):
    off = va - lo
    if off < 0 or off+4 > len(buf): return None
    return struct.unpack_from('<I', buf, off)[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# --- full linear sweep of .text ---
insns = []   # (addr, size, mnemonic, id)
boundaries = set()
e8_at_boundary = []   # (site, rel32, target)
raw_e8 = 0
n_insn = 0
n_skip = 0
for i in range(0, len(text)-5, 1):
    if text[i] == 0xE8: raw_e8 += 1
print('raw E8 bytes in .text region:', raw_e8)

imm_interest = set()
addr = TEXT_LO
for ins in md.disasm(text, TEXT_LO):
    n_insn += 1
    addr = ins.address
    boundaries.add(ins.address)
    if ins.id == 0:
        n_skip += 1
        continue
    if ins.mnemonic == 'call' and ins.size == 5 and text[ins.address-TEXT_LO] == 0xE8:
        rel = struct.unpack_from('<i', text, ins.address-TEXT_LO+1)[0]
        e8_at_boundary.append((ins.address, rel, (ins.address + 5 + rel) & 0xFFFFFFFF))
print('n_insn_total', n_insn, 'n_skipdata', n_skip, 'n_e8_at_boundary', len(e8_at_boundary))
print('text range', hex(TEXT_LO), hex(TEXT_HI), 'last boundary', hex(addr))
json.dump({'sha256':hashlib.sha256(blob).hexdigest().upper(),'size':len(blob),
           'text_lo':TEXT_LO,'text_hi':TEXT_HI,'n_insn':n_insn,'n_skipdata':n_skip,
           'n_e8_boundary':len(e8_at_boundary),'raw_e8':raw_e8},
          open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_CRITERION\work\scan_scale.json','w'), indent=1)
