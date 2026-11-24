"""Scan all 49 A-set rows for 3b structural features to select the best 8."""
from re_core import PE
from func_analyze import load_a_rows, disasm_range
import re

pe=PE()
rows=load_a_rows()

def feats(entry, ext_hi):
    insns=disasm_range(pe,entry,ext_hi)
    indir_jmp=[]; backward=[]
    calls=0; jcc=0
    for ins in insns:
        off=ins.address-entry; m=ins.mnemonic; ops=ins.op_str
        if m=='call': calls+=1
        if m.startswith('j') and m!='jmp': jcc+=1
        if m=='jmp':
            if '[' in ops:
                indir_jmp.append((off,ops))
            mm=re.search(r'0x([0-9a-fA-F]+)',ops)
            if mm and int(mm.group(1),16)<=ins.address:
                backward.append(off)
    return len(insns),indir_jmp,len(backward),calls,jcc

print('entry\tname\tn\tindir_jmp\tn_back\tcalls\tjcc')
for r in sorted(rows,key=lambda x:int(x['entry'],16)):
    e=int(r['entry'],16); hi=int(r['ext_hi'],16)
    n,ij,nb,c,jc=feats(e,hi)
    jmps=';'.join(f'+{hex(o)}:{ops}' for o,ops in ij)
    print(f'{r["entry"]}\t{r["name"]}\t{n}\t{jmps}\t{nb}\t{c}\t{jc}')
