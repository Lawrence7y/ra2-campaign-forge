"""Step 3: verify ④ direct-call sites for the chosen 8 rows.
Full .text E8 sweep (skipdata) + CFG extent containment (function interval, not entry_at_or_before),
non-self, E8 boundary, rel32==entry. Emit EVIDENCE/DIRECT_SITES_8.tsv.
"""
import json
from pathlib import Path
from s09lib import full_e8_sweep, direct_sites_for, cfg_extent, decode_one, u32

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4')
WORK, EV = OUT/'work', OUT/'EVIDENCE'

CHOSEN = ['004E2830','00557830','00565B00','00577920','006568A0','006A7D70','00723EC0','006D02B0']

insns, calls = full_e8_sweep()
print('.text instructions=',len(insns),' E8@boundary=',len(calls))

# capstone self-check: op.index trap (must detect known positive call [reg+disp])
from capstone.x86 import X86_OP_MEM
pos = decode_one(0x4386AB)
print('capstone selfcheck 0x4386AB:', pos.mnemonic, pos.op_str if pos else None)
assert pos and pos.mnemonic=='call'
m = [o for o in pos.operands if o.type==X86_OP_MEM][0]
print('  mem base=',pos.reg_name(m.mem.base),'index=',m.mem.index,'disp=',m.mem.disp,'(index 0 != None trap present)')

rows=[]
per={}
for eh in CHOSEN:
    e=int(eh,16)
    lo,hi,sites = direct_sites_for(e,calls)
    per[eh]=dict(lo='%08X'%lo,hi='%08X'%hi,n=len(sites),ok=sum(1 for s in sites if s['ok']),sites=sites)
    for s in sites:
        rows.append((eh,s))
    print('%s body=[%08X,%08X) sites=%d ok=%d'%(eh,lo,hi,len(sites),sum(1 for s in sites if s['ok'])))
    for s in sites:
        print('   site=%08X raw=%s rel=%d in_body=%s self=%s ok=%s'%(s['site'],s['raw'],s['rel'],s['in_body'],s['selfloop'],s['ok']))

json.dump(per,open(WORK/'direct_sites.json','w'),indent=1)
with (EV/'DIRECT_SITES_8.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tsite\trel32\traw\tbody_lo\tbody_hi\tin_body\tselfloop\tok\n')
    for eh,s in rows:
        f.write('%s\t%08X\t%d\t%s\t%s\t%s\t%d\t%d\t%d\n'%(
            eh,s['site'],s['rel'],s['raw'],per[eh]['lo'],per[eh]['hi'],
            int(s['in_body']),int(s['selfloop']),int(s['ok'])))
