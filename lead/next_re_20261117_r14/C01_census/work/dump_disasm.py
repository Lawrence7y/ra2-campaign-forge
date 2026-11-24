"""Dump full disassembly of all 1292 slice functions to EVIDENCE/slice_disasm.txt (untruncated).
Uses capstone skipdata=True; function boundaries from function_atlas.tsv entry+size.
"""
import os
import pefile, capstone
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID=os.path.join(BASE,'EVIDENCE'); ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
EXE=os.path.join(PROJECT,'ra2youli','gamemd.exe'); TAB=chr(9)
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.decode(errors='replace').rstrip('\0')=='.text':
        TR=s.PointerToRawData; TV=IB+s.VirtualAddress
DATA=pe.__data__
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
lines=open(ATLAS,encoding='utf-8',errors='replace').read().splitlines()[1:1293]
with open(os.path.join(EVID,'slice_disasm.txt'),'w',encoding='utf-8') as f:
    f.write('# C01 full disassembly dump — capstone 5.0.7 x86-32 skipdata=True\n')
    f.write('# source ra2youli/gamemd.exe sha256 73201CC0...F67476 ImageBase 0x400000\n')
    f.write('# function boundaries: function_atlas.tsv entry+size (slice rows 1-1292)\n\n')
    for ln in lines:
        p=ln.split(TAB); e=int(p[0],16); sz=int(p[1])
        f.write('===== %08X size=%d ninstr=%s =====\n'%(e,sz,p[2]))
        off=TR+(e-TV)
        for insn in md.disasm(DATA[off:off+sz],e):
            f.write('%08X  %-8s %s\n'%(insn.address,insn.mnemonic,insn.op_str))
            if insn.id==0: f.write('  [skipdata .byte]\n')
        f.write('\n')
print('disasm dump complete')
