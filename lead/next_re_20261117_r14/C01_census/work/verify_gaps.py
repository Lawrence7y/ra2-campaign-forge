"""Verify the 2 atlas gaps + sanity-check known example 0x4824D4."""
import os, json, struct
import pefile, capstone
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID=os.path.join(BASE,'EVIDENCE'); EXE=os.path.join(PROJECT,'ra2youli','gamemd.exe')
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.decode(errors='replace').rstrip('\0')=='.text':
        TR= s.PointerToRawData; TV= IB+s.VirtualAddress; TS=s.SizeOfRawData
DATA=pe.__data__
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
d=json.load(open(os.path.join(EVID,'atlas_gap_verdicts.json'),encoding='utf-8'))
targets=[r['target'] for r in d if r['verdict']=='TRUE_FUNC_ENTRY']+[0x4824D4]
print('=== VERIFY TRUE GAPS + KNOWN EXAMPLE ===')
for t in targets:
    print('\nTARGET %08X'%t)
    # decode at target
    off=TR+(t-TV); buf=DATA[off:off+48]
    ins=list(md.disasm(buf,t))[:8]
    print(' body:', ' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins if i.id!=0))
    # find all E8/E9 rel32 sites pointing here (byte channel: scan raw for E8/E9, verify via capstone boundary)
    raw=S0=DATA[TR:TR+TS]
    sites=[]
    for i in range(0,len(raw)-5):
        op=raw[i]
        if op in (0xE8,0xE9):
            rel=struct.unpack_from('<i',raw,i+1)[0]
            src=TV+i
            if src+5+rel==t:
                # verify src is an instruction boundary by disassembling from src-16
                sites.append(src)
    print(' E8/E9 rel32 sites (byte scan):', [('%08X'%s) for s in sites])
    # verify each site is instruction boundary via capstone from site-8
    for s in sites[:5]:
        chk=list(md.disasm(DATA[TR+(s-8-TV):TR+(s-TV)+16],s-8))
        ok=any(insn.address==s for insn in chk if insn.id!=0)
        print('   site %08X boundary=%s'%(s,ok))
