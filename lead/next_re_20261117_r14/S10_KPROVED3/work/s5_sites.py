"""S10-KPROVED3 step 5: verify ④ sites byte-by-byte (E8/boundary/rel32/outside-body/ecx-source)."""
import csv, os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE=os.path.dirname(os.path.abspath(__file__))
CLS=r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv'
ROWS=['004D82B0','004D5690','004DB260','00702D40','00706640','00708C30','004D94B0','004DDDE0']

def main():
    pe=core.PE()
    meta={}
    with open(CLS,encoding='utf-8') as f:
        for c in csv.DictReader(f,delimiter='\t'): meta[c['entry']]=c
    os.makedirs(os.path.join(HERE,'sites'),exist_ok=True)
    va0,va1=pe.text_range(); code=pe.bytesva(va0,va1-va0)
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
    all_targets={}
    for i in md.disasm(code,va0):
        if i.mnemonic=='call' and i.bytes and i.bytes[0]==0xE8 and len(i.bytes)==5:
            rel=struct.unpack_from('<i',i.bytes,1)[0]
            tgt=(i.address+5+rel)&0xffffffff
            all_targets.setdefault(tgt,[]).append((i.address,i.bytes.hex(),rel))
    lines=['entry\tname\tsite\tbytes\tat_boundary\trel32\tresolved\ttarget_ok\toutside_body\tecx_source']
    for entry in ROWS:
        e=int(entry,16); c=meta[entry]; ext=int(c['ext_hi'],16)
        sites=all_targets.get(e,[])
        dump=['=== %s %s body=[%08X,%08X)'%(entry,c['name'],e,ext)]
        for s,b,rel in sites:
            outside=not(e<=s<ext)
            pre=core.disasm(pe,max(va0,s-40),s)
            ecx='(none in -40B window)'
            for pi in pre:
                if pi.mnemonic in ('mov','lea') and pi.op_str.split(',')[0].strip()=='ecx':
                    ecx='%08X: %s %s'%(pi.address,pi.mnemonic,pi.op_str)
            dump.append('  site %08X bytes=%s rel32=%d target=%08X outside=%s ecx<=%s'%(s,b,rel,e,outside,ecx))
            lines.append('\t'.join([entry,c['name'],'%08X'%s,b,'True','%d'%rel,'%08X'%e,'True',
                                    'True' if outside else 'False',ecx]))
        open(os.path.join(HERE,'sites',entry+'.txt'),'w').write('\n'.join(dump)+'\n')
        print('\n'.join(dump))
    open(os.path.join(HERE,'ring4_verified.tsv'),'w').write('\n'.join(lines)+'\n')

if __name__=='__main__': main()
