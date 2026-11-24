"""s6: sanity-check ③b detector on prior accepted rows + compute base rate."""
import sys, os, json, random, struct
sys.path.insert(0, os.path.dirname(__file__))
from core import Bin, build_rtti, sweep_calls, FuncMap, disasm_range
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

HERE=os.path.dirname(__file__); R14=os.path.dirname(os.path.dirname(HERE))
b=Bin(); rtti=build_rtti(b); sw=sweep_calls(b); fm=FuncMap(b,rtti,sw)

# Sanity: prior accepted rows should be classified as ③b
ACCEPTED = {
 '004D74E0':('③b①','jump table 13'), '004D7D50':('③b①','jump table 11'),
 '004D7170':('③b④','loop write'), '004D85D0':('③b④','loop write'),
 '004DB3C0':('③b④','loop write'), '004D9960':('③b④','loop write'),
 '004DF040':('③b④','stack acc'), '004DB690':('③b②','HRESULT'),
 '004D82B0':('③b④','loop write'), '004D5690':('③b④','loop write'),
 '004DB260':('③b④','loop write'), '00702D40':('③b①','jump table'),
 '00706640':('③b①','jump table'), '00708C30':('③b①','jump table'),
 '004D94B0':('③b②','HRESULT'),
}

def detect(ea):
    st,en=fm.extent(ea); insns=disasm_range(b,st,en)
    jt=[]; lp=[]; ep=[]
    for i,x in enumerate(insns):
        if x.mnemonic=='jmp' and x.operands and x.operands[0].type==X86_OP_MEM and x.operands[0].mem.index:
            jt.append(x.address-ea)
        if x.mnemonic.startswith('j') and x.mnemonic!='jmp' and x.operands and x.operands[0].type==X86_OP_IMM:
            tgt=x.operands[0].imm
            if st<=tgt<x.address:
                body=[y for y in insns if tgt<=y.address<=x.address]
                nw=sum(1 for y in body if y.mnemonic in ('mov','inc','dec','add','sub','and','or','xor') and y.operands and y.operands[0].type==X86_OP_MEM and '[esp' not in y.op_str and '[ebp' not in y.op_str)
                lp.append((tgt-ea,x.address-ea,nw))
        if x.mnemonic in ('cmp','test'):
            for o in x.operands:
                if o.type==X86_OP_IMM and (o.imm & 0xffffffff) in (0x80004002,0x80004003,0x80004005,0xffffffff):
                    ep.append((x.address-ea,f'{o.imm&0xffffffff:#x}'))
    return jt,lp,ep

print('=== SANITY on accepted rows (detector should find signals) ===')
for e,(exp,desc) in ACCEPTED.items():
    jt,lp,ep=detect(int(e,16))
    print(f'{e} exp={exp}({desc}) jt={len(jt)} loops={len(lp)} ep={len(ep)} | lp={lp[:2]} ep={ep[:2]}')

# Base rate: S10 [static inference] pool. Determine from classification.tsv
import csv
cls=os.path.join(R14,'SURVEY_RING24','EVIDENCE','classification.tsv')
pool=[]
with open(cls,encoding='utf-8') as f:
    rdr=csv.DictReader(f,delimiter='\t')
    print('cls fields', rdr.fieldnames[:12])
    for row in rdr:
        if row.get('subsystem')=='S10':
            pool.append(row)
print('S10 pool size', len(pool))
