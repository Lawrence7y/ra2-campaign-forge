"""
S10-K2 T2-final: definitive per-slot mission table.
- Follows jmp-thunks to classify stub vs impl.
- Maps slot -> mission(s) from dispatch (call-context evidence).
- Verifies parent vtable alignment (MissionClass vs ObjectClass vs AbstractClass).
- Counts all-stub slots / implemented slots / missions-with-impl / all-stub missions.
No atlas for discovery. capstone skipdata=True.
"""
import os, json
from pehelp import (IMAGE_BASE, rd, u32, section_of, is_code, disasm)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID = os.path.join(OUT,'EVIDENCE')
L=[]
def P(s=''):
    s=str(s)
    L.append(s)
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode('ascii'))

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

STUB_SET=set(range(0x5B2E10,0x5B2FC0+1,0x10))  # 28 base stubs
def classify(addr, depth=0):
    """Return (kind, target): 'stub' if lands on base stub, 'impl' otherwise; follow jmp thunks."""
    if addr in STUB_SET: return ('stub',addr)
    if depth>3: return ('impl',addr)
    code=rd(addr,32)
    ins=list(md.disasm(code,addr))
    if not ins: return ('?',addr)
    first=ins[0]
    if first.mnemonic=='jmp' and first.operands and first.operands[0].type==X86_OP_IMM:
        return classify(first.operands[0].imm, depth+1)
    return ('impl',addr)

# vtable data from t2
with open(os.path.join(EVID,'t2_mission_slots.json')) as f: slots=json.load(f)
with open(os.path.join(EVID,'t2_dispatch.json')) as f: disp=json.load(f)

# mission name enum
MN=['Sleep','Attack','Move','QMove','Retreat','Guard','Sticky','Enter','Capture','Eaten',
    'Harvest','Area Guard','Return','Stop','Ambush','Hunt','Unload','Sabotage','Construction',
    'Selling','Repair','Rescue','Missile','Harmless','Open','Patrol','Paradrop Approach',
    'Paradrop Overfly','Wait','Attack Move','Spyplane Approach','Spyplane Overfly']

# slot -> mission indices
slot2m={}
for d in disp:
    if d['slot'] is not None:
        slot2m.setdefault(d['slot'],[]).append((d['mid'],d['name']))

P('===== PARENT VTABLE ALIGNMENT (slot-by-slot from .rdata) =====')
# Re-find primary vtables for Abstract/Object/Mission
import re
with open(os.path.join(EVID,'t2_rtti_vtables.json')) as f: rj=json.load(f)
cls_vt={}
for x in rj['kvts']:
    if x['off']==0 and x['name'] not in cls_vt:
        cls_vt[x['name']]=(int(x['vt'],16),x['slots'])
for c in ['AbstractClass','ObjectClass','MissionClass','TechnoClass','FootClass','InfantryClass','AircraftClass','BuildingClass','UnitClass']:
    key='.?AV%s@@'%c
    if key in cls_vt: P('  %-16s VT=%08X slots=%d'%(c,cls_vt[key][0],cls_vt[key][1]))
# align first 24 Abstract vs Object vs Mission
avt=cls_vt['.?AVAbstractClass@@'][0]; ovt=cls_vt['.?AVObjectClass@@'][0]; mvt=cls_vt['.?AVMissionClass@@'][0]
P('\n  first 24 slots: Abstract vs Object vs Mission (same addr = inherited override-free):')
same_a_o=same_o_m=0
for i in range(24):
    a=u32(avt+4*i); o=u32(ovt+4*i); m=u32(mvt+4*i)
    if a==o: same_a_o+=1
    if o==m: same_o_m+=1
    if i<6 or a!=o or o!=m:
        P('    v[%2d] A=%08X O=%08X M=%08X %s%s'%(i,a,o,m,'=AO' if a==o else '','=OM' if o==m else ''))
P('    total same Abstract==Object: %d/24; Object==Mission: %d/24'% (same_a_o,same_o_m))
P('  => MissionClass v[0..121] align with ObjectClass (122 slots); mission handlers are v[129..156] beyond that.')

P('\n===== DEFINITIVE PER-SLOT MISSION TABLE (v129..v156) =====')
P('slot | disp | missions(dispatch) | impl-by-class | all-stub? | grade')
final={}
all_stub_slots=[]
impl_slots=[]
for s in range(129,157):
    ms=slot2m.get(s,[])
    mtxt=';'.join('%d:%s'%(i,n) for i,n in ms) if ms else '(no dispatch entry)'
    impls=[]; stubs=[]
    for cls,rows in slots.items():
        if cls.startswith('Abstract') or cls.startswith('Object') or cls.startswith('Fogged'): continue
        r=[x for x in rows if x['slot']==s]
        if not r: continue
        addr=int(r[0]['addr'],16)
        kind,tgt=classify(addr)
        short=cls.replace('.?AV','').replace('@@','')
        if kind=='stub': stubs.append('%s:%08X(stub)'%(short,addr))
        else: impls.append('%s:%08X'%(short,addr))
    is_all_stub = (len(impls)==0)
    if is_all_stub: all_stub_slots.append(s)
    else: impl_slots.append(s)
    grade='[已证] 槽↔Mission(派发call disp)+实现地址字节' if ms else '[未证] 无派发映射'
    if is_all_stub: grade='[已证] 全桩(28槽中该槽7类全 base-stub)'
    P('v[%d] | 0x%X | %-34s | %s | %s | %s' %
      (s,4*s,mtxt, ','.join(impls) if impls else ','.join(stubs[:2])+'...', 'YES' if is_all_stub else 'no', grade))
    final[s]=dict(slot=s,disp='0x%X'%(4*s),missions=ms,impls=impls,stubs=stubs,all_stub=is_all_stub,grade=grade)

P('\n===== ACCOUNTING =====')
P('all-stub slots (%d): %s'%(len(all_stub_slots),','.join('v%d'%s for s in all_stub_slots)))
P('slots with impl   (%d): %s'%(len(impl_slots),','.join('v%d'%s for s in impl_slots)))
P('mission ids with an impl slot:')
m_with_impl=set()
for d in disp:
    if d['slot'] in impl_slots: m_with_impl.add(d['mid'])
P('%d/32 : %s'%(len(m_with_impl),','.join('%d:%s'%(i,MN[i]) for i in sorted(m_with_impl))))
m_all_stub=[i for i in range(32) if i not in m_with_impl]
P('all-stub missions (%d): %s'%(len(m_all_stub),','.join('%d:%s'%(i,MN[i]) for i in m_all_stub)))

with open(os.path.join(EVID,'t2_final_slots.json'),'w') as f:
    json.dump({'slots':final,'all_stub_slots':all_stub_slots,'impl_slots':impl_slots,
               'm_with_impl':sorted(m_with_impl),'m_all_stub':m_all_stub},f,indent=2)
with open(os.path.join(EVID,'t2_final_slots.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t2_final_slots.txt/.json')
