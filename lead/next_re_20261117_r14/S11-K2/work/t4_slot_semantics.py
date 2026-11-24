"""
S11-K2 T4: vtable slot semantics for Locomotion classes.
For each class, dump each slot's target with first-insn signature; grade conservatively.
Cross-check: off0 slot9 = GetSize (already proven by T2), off4 slot 6/16/17/18 = known anchors (S11-K1).
"""
import json
from pehelp import u32, disasm, fmt, section_of

J=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.json'
obj=json.load(open(J,encoding='utf-8'))
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t4_slot_semantics.txt'
L=[]
def P(s=''):
    L.append(str(s)); print(s)

# focus: Drive off0 (10) + off4 slots of interest + DropPod off0 for cross-check
for cls,offs in [('.?AVDriveLocomotionClass@@',[0,4]),('.?AVLocomotionClass@@',[0,4])]:
    P('\n===== '+cls+' =====')
    for s in obj['classes'][cls]:
        if s['off'] not in offs: continue
        vt=s['vt']; n=min(s['slots'],50)
        P('\n-- iface off=%d vt=%08X slots=%d --'%(s['off'],vt,s['slots']))
        for i in range(n):
            a=u32(vt+4*i)
            if not section_of(a)=='.text':
                P(' slot%-2d %08X noncode'%(i,a)); continue
            ins=disasm(a,10)
            sig=' | '.join(x.mnemonic+' '+x.op_str for x in ins[:3])
            P(' slot%-2d %08X  %s'%(i,a,sig))
with open(OUT,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE',OUT)
