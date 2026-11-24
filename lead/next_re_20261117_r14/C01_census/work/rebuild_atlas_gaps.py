"""FIX round: rebuild atlas_gaps.tsv with two independent discovery channels.

chan=call-jmp  : original capstone full-.text call/jmp rel target sweep (channel B1)
chan=orphan    : independent forward channel (channel B2) — align16 + uncovered
                 + prologue + predecessor terminator/gap, zero-reference orphans
chan=orphan-cand: forward candidate lacking prologue (naked helper), upper bound only

Lower bound = high-confidence hits from both channels (7).
Upper bound = lower + candidate entries (9).
"""
import os, json
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.abspath(os.path.join(HERE,'..'))
EVID=os.path.join(BASE,'EVIDENCE'); TAB=chr(9)

# original call/jmp channel hits (from work/classify_gaps.py, unchanged)
orig=[
 dict(target=0x4039C0,ncall=2,njmp=0,prologue='push-regs',prev_term='',verdict='TRUE_FUNC_ENTRY',conf='high',sites='00403ACD,00403AFF'),
 dict(target=0x42E1C0,ncall=1,njmp=0,prologue='sub-esp',prev_term='',verdict='TRUE_FUNC_ENTRY',conf='high',sites='0042E13E'),
]
# independent orphan forward channel — my own re-run (work/orphan_forward.py)
orph=[
 dict(target=0x4093C0,ncall=0,njmp=0,prologue='sub-esp',prev_term='ret@004093BF',verdict='ORPHAN_ENTRY',conf='high',sites='-'),
 dict(target=0x412280,ncall=0,njmp=0,prologue='param-store',prev_term='ret@0041227F',verdict='ORPHAN_ENTRY',conf='high',sites='-'),
 dict(target=0x427850,ncall=0,njmp=0,prologue='param-store',prev_term='ret4@0042784D',verdict='ORPHAN_ENTRY',conf='high',sites='-'),
 dict(target=0x42E990,ncall=0,njmp=0,prologue='push-regs',prev_term='ret4@0042E98D',verdict='ORPHAN_ENTRY',conf='high',sites='-'),
 dict(target=0x435B50,ncall=0,njmp=0,prologue='push-regs',prev_term='ret4@00435B4D',verdict='ORPHAN_ENTRY',conf='high',sites='-'),
]
# extras independently verified from raw disasm (EVIDENCE/orphan_forward_stdout.txt)
extra=[
 dict(target=0x433060,ncall=0,njmp=1,prologue='sub-esp',prev_term='nop-pad-after-ret@00433051',verdict='ORPHAN_ENTRY',conf='med',sites='-',chan='orphan'),
 dict(target=0x432BF0,ncall=0,njmp=1,prologue='naked-none',prev_term='ret4+nop@00432BEC',verdict='ORPHAN_CANDIDATE',conf='low',sites='-',chan='orphan-cand'),
]

with open(os.path.join(BASE,'atlas_gaps.tsv'),'w',encoding='utf-8') as f:
    f.write('target\tchan\tncall\tnjmp\tprologue\tprev_term\tverdict\tconf\tsites\n')
    for r in orig:
        f.write('%08X\tcall-jmp\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n'%(r['target'],r['ncall'],r['njmp'],r['prologue'],r['prev_term'],r['verdict'],r['conf'],r['sites']))
    for r in orph:
        f.write('%08X\torphan\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n'%(r['target'],r['ncall'],r['njmp'],r['prologue'],r['prev_term'],r['verdict'],r['conf'],r['sites']))
    for r in extra:
        f.write('%08X\t%s\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n'%(r['target'],r['chan'],r['ncall'],r['njmp'],r['prologue'],r['prev_term'],r['verdict'],r['conf'],r['sites']))

lower=len(orig)+len(orph)  # high-conf = 7
upper=lower+len(extra)     # +2 candidates = 9
open(os.path.join(EVID,'gap_bound_counts.txt'),'w',encoding='utf-8').write('lower=%d upper=%d\n'%(lower,upper))
print('atlas_gaps.tsv rebuilt: %d rows (lower=%d upper=%d)'%(len(orig)+len(orph)+len(extra),lower,upper))
