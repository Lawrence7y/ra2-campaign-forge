"""S10-KPROVED3 step 3: thorough ③b feature inventory for all 41 remaining rows."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_ESP, X86_REG_EBP

HERE = os.path.dirname(os.path.abspath(__file__))
CLS = r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
MERGED = set('004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690'.split())

def main():
    pe = core.PE()
    rows = []
    with open(CLS, encoding='utf-8') as f:
        for c in csv.DictReader(f, delimiter='\t'):
            if c['subsystem']=='S10' and c['has4_strict']=='1' and c['has2_rtti']=='1' and c['entry'] not in MERGED:
                rows.append(c)
    out = []
    for c in sorted(rows, key=lambda x:int(x['entry'],16)):
        e=int(c['entry'],16); ext=int(c['ext_hi'],16); atlas=int(c['atlas_size'])
        hi = ext if ext <= e+max(atlas,16)+64 else e+max(atlas,16)
        ins=core.disasm(pe,e,hi); by={i.address:i for i in ins}; addrs=sorted(by)
        L=[]
        L.append('=== %s %s atlas=%d body=[%08X,%08X) n=%d' % (c['entry'],c['name'],atlas,e,hi,len(ins)))
        for a in addrs:
            i=by[a]
            if i.mnemonic=='jmp' and i.bytes and i.bytes[0]==0xFF and i.operands and i.operands[0].type==X86_OP_MEM:
                tg=core._switch_targets(pe,i)
                idx=addrs.index(a); pre=' | '.join('%s %s'%(by[x].mnemonic,by[x].op_str) for x in addrs[max(0,idx-4):idx])
                L.append('  SWITCH @+%X: %s ; n_targets=%d ; targets=%s' % (a-e, pre, len(set(tg)), ','.join('%08X'%t for t in tg[:8])))
        for a in addrs:
            i=by[a]
            if i.mnemonic.startswith('j') and i.operands and i.operands[0].type==X86_OP_IMM:
                t=i.operands[0].imm & 0xFFFFFFFF
                if t<a and t>=e:
                    ok,why=core.has_complete_loop(by,a,t)
                    L.append('  BACKJMP @+%X -> +%X m=%s complete=%s (%s)' % (a-e,t-e,i.mnemonic,ok,why))
        for a in addrs:
            i=by[a]
            if i.mnemonic=='cmp' and len(i.operands)==2 and i.operands[1].type==X86_OP_IMM:
                imm=i.operands[1].imm & 0xffffffff
                if imm in core.HRESULT:
                    L.append('  HRESULT @+%X: cmp ...,%08X' % (a-e,imm))
        fs=set(); vi=set()
        for a in addrs:
            i=by[a]
            if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==X86_OP_MEM and i.operands[1].type==X86_OP_IMM:
                if not (i.operands[0].mem.base in (X86_REG_ESP,X86_REG_EBP)):
                    fs.add((i.operands[0].mem.base,i.operands[0].mem.disp))
                    imm=i.operands[1].imm & 0xffffffff
                    if pe.va2off(imm): vi.add(imm)
        L.append('  SHAPE: field_stores=%d vt_installs=%d' % (len(fs),len(vi)))
        out.append('\n'.join(L))
    txt='\n'.join(out)
    open(os.path.join(HERE,'feature_inventory.txt'),'w').write(txt)
    print('wrote feature_inventory.txt')

if __name__=='__main__':
    main()
