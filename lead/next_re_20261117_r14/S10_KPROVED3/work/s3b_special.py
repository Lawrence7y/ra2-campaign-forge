"""Scan candidate rows with atlas-based body for switches/backward loops/HRESULT."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

CLS = r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
SPECIAL = ['004D82B0','004DBAD0','004DDED0','004D8F40','004DBED0','004DB1A0','004D55F0','006F3AD0','006F3D60','006FBDC0','006FDA00','0070E1A0']

pe=core.PE()
meta={}
with open(CLS,encoding='utf-8') as f:
    for c in csv.DictReader(f,delimiter='\t'): meta[c['entry']]=c
for entry in SPECIAL:
    c=meta[entry]; e=int(entry,16); hi=e+int(c['atlas_size'])
    ins=core.disasm(pe,e,hi); by={i.address:i for i in ins}; addrs=sorted(by)
    print('=== %s %s atlas=%d n=%d' % (entry,c['name'],int(c['atlas_size']),len(ins)))
    for a in addrs:
        i=by[a]
        if i.mnemonic=='jmp' and i.bytes and i.bytes[0]==0xFF and i.operands and i.operands[0].type==X86_OP_MEM:
            tg=core._switch_targets(pe,i)
            if len(set(tg))>=3:
                print('  SWITCH @+%X n=%d'%(a-e,len(set(tg))))
        if i.mnemonic.startswith('j') and i.operands and i.operands[0].type==X86_OP_IMM:
            t=i.operands[0].imm & 0xffffffff
            if t<a and t>=e:
                ok,why=core.has_complete_loop(by,a,t)
                if ok: print('  LOOP @+%X -> +%X %s'%(a-e,t-e,why))
        if i.mnemonic=='cmp' and len(i.operands)==2 and i.operands[1].type==X86_OP_IMM:
            imm=i.operands[1].imm & 0xffffffff
            if imm in core.HRESULT: print('  HRESULT @+%X %08X'%(a-e,imm))
