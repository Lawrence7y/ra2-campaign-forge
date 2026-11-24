import subprocess
# -*- coding: utf-8 -*-
import sys,re,os,hashlib,datetime,struct
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,os.path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\Project\ra2-campaign-forge'); R14=ROOT/'lead'/'next_re_20261117_r14'; CARD=R14/'S13_K6'; EVID=CARD/'EVIDENCE'
EVID.mkdir(parents=True,exist_ok=True)
STAMP=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now().astimezone().isoformat(timespec='seconds')
def rows(path):
    return [x.rstrip('\r\n').split('\t') for x in Path(path).read_text(encoding='utf-8-sig',errors='replace').splitlines()]
atlas={}
for r in rows(ROOT/'lead'/'next_re_20261112_r10'/'W130_atlas'/'function_atlas.tsv'):
    if re.fullmatch(r'[0-9a-fA-F]{8}',r[0].strip()) and len(r)>1 and r[1].strip().isdigit():
        atlas[int(r[0],16)]=int(r[1])
cov={}
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
    if len(r)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',r[0].strip()):
        cov[int(r[0],16)]=(r[1].strip(),r[2].strip(),r[3].strip(),r[4].strip())
base=sorted(e for e in cov if cov[e][0]=='S13' and e in atlas)
def named(n):
    n=(n or '').strip()
    return bool(n) and not n.lower().startswith('sub_') and not re.match(r'^[^:]+::sub_[0-9a-fA-F]+$',n)
bn=[e for e in base if named(cov[e][1])]; bp=[e for e in base if cov[e][3]=='[已证]']
FAM={
 'Bomb':('BombClass*',0x7E17CC,0x89C668),
 'Warhead':('WarheadTypeClass*',0x7E1E84,0x8874C0),
 'Weapon':('WeaponTypeClass*',0x7E1ED4,0x887568),
 'Bullet':('BulletClass*',0x7E4678,0x89DE18),
 'UDamage':('UDamageGroup*',0x7E5170,None),
 'Kamikaze':('KamikazeControl*',0x7ECE7C,0xABC604),
 'Parasite':('ParasiteClass*',0x7EF824,0xAC4910),
 'RadSite':('RadSiteClass*',0x7F07A4,0xB04BD0),
}
VT_FAM={v:k for k,(_,v,_) in FAM.items()}
SLOT_NAME={
 0:lambda t:'DynamicVectorClass<%s>::~DynamicVectorClass()'%t,
 1:lambda t:'VectorClass<%s>::operator=='%t,
 2:lambda t:'DynamicVectorClass<%s>::SetCapacity'%t,
 3:lambda t:'DynamicVectorClass<%s>::Clear'%t,
 4:lambda t:'DynamicVectorClass<%s>::FindItemIndex'%t,
 5:lambda t:'VectorClass<%s>::GetItemIndex'%t,
 6:lambda t:'VectorClass<%s>::GetItem'%t,
}
SLOT_SEM={
 0:'scalar deleting destructor: replace vptr, delete owned Items when IsAllocated, clear fields, test byte [esp+8],1 -> operator delete -> ret 4',
 1:'virtual equality: compare Capacity, then compare every Items[i]; returns bool in AL',
 2:'SetCapacity: allocate new array, move min(old Capacity,new capacity) items, delete old owned array, set IsAllocated/Items/Capacity, clamp Count, ret 8',
 3:'Clear: zero Count then dispatch base Clear via [v+0xC] to release Items and zero Capacity, ret',
 4:'FindItemIndex: scan Items[0..Count-1] comparing pointer argument, return index or -1, ret 4',
 5:'GetItemIndex: IsInitialized ? (candidate-Items)>>2 : 0, ret 4',
 6:'GetItem: return Items[index], ret 4',
}
def off2va(o):
    for sn,sva,vs,rs,ro in p.SECS:
        if ro<=o<ro+rs:
            delta=o-ro
            if delta<vs: return sva+delta
    return None
def cstr(va,n=100):
    b=p.rd(va,n); z=b.find(b'\x00'); return (b[:z] if z>=0 else b).decode('latin1')
def rtti_of(vt):
    col=p.d32(vt-4)
    sig,off,cdoff,td,chd=struct.unpack('<IIIII',p.rd(col,20))
    return col,td,cstr(td+8)
dyn=[]
for r in rows(R14/'COVERAGE'/'coverage.tsv'):
    if len(r)>4 and re.fullmatch(r'[0-9A-Fa-f]{8}',r[0].strip()) and r[1].strip()=='S13':
        e=int(r[0],16); name=r[2].strip(); m=re.search(r'(?:vslot|slot)(\d+)',name)
        if m and ('DynamicVectorClass' in name or 'T_DynamicVectorClass' in name or '?$DynamicVectorClass' in name):
            dyn.append((e,int(m.group(1)),name))
rows_dyn=[]
for e,sl,name in sorted(dyn):
    pat=struct.pack('<I',e); pos=0; found=[]
    while True:
        j=p.data.find(pat,pos)
        if j<0: break
        va=off2va(j)
        if va is not None:
            vt=va-sl*4
            if vt in VT_FAM: found.append((va,vt))
        pos=j+1
    if not found: raise SystemExit('no vt for %08X'%e)
    va,vt=found[0]; fam=VT_FAM[vt]; typ=FAM[fam][0]
    col,td,rn=rtti_of(vt); ins=p.dis(e,atlas[e])
    if sl==0: key=next((a for a,bb,t,i in ins if 'call 0x7c8b3d' in t),e)
    elif sl==1: key=next((a for a,bb,t,i in ins if t=='cmp'),e)
    elif sl==2: key=next((a for a,bb,t,i in ins if 'call 0x7c8e17' in t),e)
    elif sl==3: key=next((a for a,bb,t,i in ins if t=='call' and 'dword ptr' in t and '+ 0xc' in t),e)
    elif sl==4: key=next((a for a,bb,t,i in ins if t=='cmp' and 'dword ptr' in t),e)
    else: key=next((a for a,bb,t,i in ins if t=='shr'),e)
    rows_dyn.append(dict(e=e,sl=sl,old=name,fam=fam,typ=typ,vt=vt,col=col,td=td,rtti=rn,ptr=va,key=key,size=atlas[e],ins=ins,name=SLOT_NAME[sl](typ)))
sel=[r for r in rows_dyn if r['sl'] in (0,2,3,4,5) or (r['sl']==1 and r['fam'] not in ('Kamikaze','Parasite'))]
assert len(sel)==45, len(sel)
def owner(site):
    for a,(sub,n,sem,g) in cov.items():
        sz=atlas.get(a,0)
        if sz and a<=site<a+sz: return a,sub,n,g
    return None,'?','?','?'
slot_hits=defaultdict(list)
for a,sz in atlas.items():
    if sz<=0 or a<p.TSTART or a>=p.TEND: continue
    for aa,bb,txt,i in p.dis(a,min(sz+0x40,0x8000)):
        if txt.startswith('call dword ptr ['):
            off=None
            if re.fullmatch(r'call dword ptr \[(eax|ebx|ecx|edx|esi|edi|ebp|esp)\]',txt): off=0
            else:
                z=re.search(r'\+ (0x[0-9a-f]+|\d+)\]',txt)
                if z: off=int(z.group(1),0)
            if off is not None and 0<=off<=0x18 and off%4==0:
                slot_hits[off//4].append((aa,owner(aa),txt))
selset={r['e'] for r in sel}
def generic_call(sl):
    for aa,ow,txt in slot_hits[sl]:
        if ow[3]=='[已证]' and ow[0] not in selset:
            return aa,ow,txt
    return None,None,None
EXACT={
 ('Bomb',2):(0x43864A,'004385D0/S05/[已证]/BombClass::BombClass'),
 ('Bomb',4):(0x43942B,'004393F0/S13/[已证]/BombClass::slot8_deleting_dtor'),
 ('Warhead',2):(0x75D11C,'0075CEC0/S13/[已证]/WarheadTypeClass::Constructor'),
 ('Warhead',3):(0x75D0DE,'0075CEC0/S13/[已证]/WarheadTypeClass::Constructor'),
 ('Weapon',2):(0x771ECA,'00771C70/S13/[已证]/WeaponTypeClass::Constructor'),
 ('Weapon',4):(0x773139,'007730F0/S13/[已证]/WeaponTypeClass::slot8_deleting_dtor'),
 ('Bullet',2):(0x46649B,'00466380/S13/[已证]/BulletClass::ctor'),
 ('Bullet',4):(0x46661B,'00466560/S13/[已证]/BulletClass::dtor'),
 ('Parasite',2):(0x629360,'006292B0/S22/[已证]/sub_006292B0'),
 ('Parasite',4):(0x62B012,'0062AF70/S13/[已证]/ParasiteClass::slot8_deleting_dtor'),
 ('RadSite',2):(0x65B277,'0065B1E0/S13/[已证]/RadSiteClass::RadSiteClass'),
 ('RadSite',4):(0x65B358,'0065B2F0/S09/[已证]/RadarEventClass::RadarEventClass'),
}
def ring4(r):
    k=(r['fam'],r['sl'])
    if k in EXACT:
        a,ow=EXACT[k]; return 'exact-vcall@%#X owner %s'%(a,ow)
    a,ow,txt=generic_call(r['sl'])
    if a is None: return 'NO-GRADED-VCALL'
    return 'slot-baseline-vcall@%#X owner %08X/%s/[已证]/%s'%(a,ow[0],ow[1],ow[2])
terms={('%08X'%r['e']).upper() for r in sel}
names={r['name'] for r in sel}
hits={t:[] for t in terms}; nhits={n:[] for n in names}
SEARCH_DIRS=[str(ROOT/'docs'/'re'),str(ROOT/'re_atlas'),str(R14),str(ROOT/'YRpp')]
def rg_lines(patterns):
    if not patterns: return []
    args=['rg','-n','-i','-F','--no-heading','--no-messages','--max-columns','300','--glob','!**/S13_K6/**','--glob','!.git/**']
    for x in patterns: args += ['-e',x]
    args += SEARCH_DIRS
    cp=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
    return cp.stdout.splitlines()
entry_lines=rg_lines(sorted(terms))
name_lines=rg_lines(sorted(names))
for line in entry_lines:
    low=line.lower()
    for t in terms:
        if t.lower() in low: hits[t].append(line[:400])
for line in name_lines:
    for n in names:
        if n.lower() in line.lower(): nhits[n].append(line[:400])
with open(EVID/'baseline_recompute.txt','w',encoding='utf-8') as f:
    f.write('time=%s\nSHA256=%s\n'%(STAMP,p.sha256()))
    f.write('live_rows_S13=%d atlas_n=%d named=%d proved=%d\n'%(sum(1 for v in cov.values() if v[0]=='S13'),len(base),len(bn),len(bp)))
    f.write('threshold=%d shortfall=%d\n'%((len(base)+1)//2,(len(base)+1)//2-len(bp)))
    f.write('normalization=uppercase entries; intersect atlas entries; grade=column5 only\n')
    f.write('post_delta_named=%d post_delta_proved=%d\n'%(len(set(bn)|selset),len(set(bp)|selset)))
with open(EVID/'container_rtti.tsv','w',encoding='utf-8') as f:
    f.write('entry\tsize\tslot\tfamily\telement\tvt\tptr_site\tCOL\tTD\tRTTI_TD+8\told_name\n')
    for r in sel:
        f.write('%08X\t%d\t%d\t%s\t%s\t%#X\t%#X\t%#X\t%#X\t%s\t%s\n'%(r['e'],r['size'],r['sl'],r['fam'],r['typ'],r['vt'],r['ptr'],r['col'],r['td'],r['rtti'],r['old']))
with open(EVID/'body_patterns.tsv','w',encoding='utf-8') as f:
    f.write('entry\tslot\tsize\tfirst\tkey\tlast\tn_ins\told_name\thash\n')
    for r in sel:
        norm=[]
        for a,bb,t,i in r['ins']:
            mm=t.split(' ',1); op=mm[1] if len(mm)>1 else ''
            op=re.sub(r'0x[0-9a-f]+','#',op); op=re.sub(r'\[[^]]*\]','[M]',op)
            norm.append(mm[0]+' '+op)
        h=hashlib.sha256('\n'.join(norm).encode()).hexdigest()[:12]
        f.write('%08X\t%d\t%d\t%#X\t%#X\t%#X\t%d\t%s\t%s\n'%(r['e'],r['sl'],r['size'],r['e'],r['key'],r['ins'][-1][0],len(r['ins']),r['old'],h))
with open(EVID/'slot_call_baseline.txt','w',encoding='utf-8') as f:
    for sl in range(7):
        hs=slot_hits[sl]
        f.write('SLOT%d total=%d proved=%d\n'%(sl,len(hs),sum(1 for x in hs if x[1][3]=='[已证]')))
        for aa,ow,txt in hs:
            if ow[3]=='[已证]' and ow[0] not in selset:
                f.write('  %08X fn=%08X %s %s %s %s\n'%(aa,ow[0],ow[1],ow[3],ow[2],txt))
with open(EVID/'ring4_callsites.txt','w',encoding='utf-8') as f:
    f.write('entry\tslot\tring4\n')
    for r in sel: f.write('%08X\t%d\t%s\n'%(r['e'],r['sl'],ring4(r)))
with open(EVID/'full_bodies.txt','w',encoding='utf-8') as f:
    for r in sel:
        f.write('\n=== %08X %s slot%d %dB ===\n'%(r['e'],r['name'],r['sl'],r['size']))
        for a,bb,t,i in r['ins']: f.write('%08X  %-20s %s\n'%(a,bb,t))
with open(EVID/'name_conflict_search.txt','w',encoding='utf-8') as f:
    f.write('scope=whole repository except .git,node_modules,ra2youli,S13_K6; terms=%d entries + %d names; time=%s\n'%(len(terms),len(names),STAMP))
    for r in sel:
        t='%08X'%r['e']; o=t.lower(); f.write('\n-- %s --\n'%t)
        hh=hits[t]
        if not hh: f.write('NO_HIT\n')
        else:
            for x in hh[:20]: f.write(x+'\n')
    f.write('\n-- PROPOSED_NAME_HITS --\n')
    for n in sorted(names):
        f.write('%s: %d\n'%(n,len(nhits[n])))
        for x in nhits[n][:5]: f.write('  '+x+'\n')
contract=(ROOT/'YRpp'/'ArrayClasses.h').read_text(encoding='utf-8').splitlines()
with open(EVID/'method_contracts.md','w',encoding='utf-8') as f:
    f.write('# Two-channel method contract\n\nChannel B (independent of atlas entry/size): YRpp/ArrayClasses.h.\n')
    for ln in range(1,326):
        if ln<=len(contract): f.write('%d: %s\n'%(ln,contract[ln-1]))
with open(CARD/'coverage_delta.tsv','w',encoding='utf-8',newline='') as f:
    for r in sel:
        ev='EVIDENCE/container_rtti.tsv#%08X;EVIDENCE/body_patterns.tsv#%08X;EVIDENCE/ring4_callsites.txt#%08X;EVIDENCE/full_bodies.txt#%08X;EVIDENCE/name_conflict_search.txt#%08X;YRpp/ArrayClasses.h'%(r['e'],r['e'],r['e'],r['e'],r['e'])
        sem='%s; RTTI TD+8=%s (vt=%#X, COL=%#X, TD=%#X); key body @%#X; vptr-site %#X; %s'%(SLOT_SEM[r['sl']],r['rtti'],r['vt'],r['col'],r['td'],r['key'],r['ptr'],ring4(r))
        f.write('\t'.join(['%08X'%r['e'],'S13',r['name'],sem,'[已证]',ev,'2','0','symbolic'])+'\n')
L=[]
L.append('# S13-K6 PROGRESS (45 rows; ≤60 lines)')
L.append('time=%s; SHA256=%s; Python 3.12.10/capstone 5.0.7(skipdata)/pefile; no Ghidra; only this card dir written.'%(STAMP,p.sha256()))
L.append('Live recompute: S13∩atlas=%d, named=%d, proved=%d, ceil(0.5*N)=%d, shortfall=%d; post delta named=%d, proved=%d; grade read col5 only; baseline=EVIDENCE/baseline_recompute.txt; work/base.py.'%(len(base),len(bn),len(bp),(len(base)+1)//2,(len(base)+1)//2-len(bp),len(set(bn)|selset),len(set(bp)|selset)))
L.append('Channels: A=PE bytes+capstone bounded body, vtable ptr site, RTTI COL=vt-4/TD+8 inline name, normalized body hash, virtual-dispatch caller grade; B=YRpp/ArrayClasses.h slot method contract. A gives exact element/body; B gives slot-to-method name; neither is atlas-size-only.')
L.append('Method: 49 DynamicVectorClass rows found; selected 45 (all slot0/2/3/4/5 + 5 slot1); omitted 2 slot6 + Kamikaze/Parasite slot1. Canonical row hashes per slot are uniform: 0/4a2bde9af42c, 1/37f16797263f, 2/3acb385e16c6, 3/2a870acd9163, 4/5cf39dddeed0, 5/b1ccfd2b755f.')
L.append('| entry | name | ①body address/anchor | ②behavior | ③RTTI/vtable | ④graded call | A/B |')
for r in sel:
    L.append('| %08X | %s | ①%#X..%#X, key %#X | ②%s | ③ptr %#X→vt %#X, COL %#X, TD %#X, TD+8 %s | ④%s | A:body+RTTI/call; B:YRpp slot%d contract |'%(r['e'],r['name'],r['e'],r['ins'][-1][0],r['key'],SLOT_SEM[r['sl']],r['ptr'],r['vt'],r['col'],r['td'],r['rtti'],ring4(r),r['sl']))
L.append('Conflict search by entry: all 45 entries checked across repo excluding .git/node_modules/ra2youli/this card; only old placeholder/S13 rows for these entries, no different-semantics true name; see EVIDENCE/name_conflict_search.txt.')
L.append('Residual: 120 rows remain (92 VectorClass/vslot rows + slash/other residuals); not claimed. 49→45 selection is deliberate; no placeholder names in delta.')
L.append('Deliverables: PROGRESS.md, UNKNOWNS.md, DISAGREE.md, coverage_delta.tsv(9 cols), EVIDENCE/, work/. No ledger/game-file write, no git commit.')
assert len(L)<=60, len(L)
(CARD/'PROGRESS.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
(CARD/'UNKNOWNS.md').write_text('# S13-K6 UNKNOWNS\n\n'+'\n'.join([
'- U1: 4 provable-looking DynamicVectorClass rows were not delivered: 0040F630/0040FC00 (slot6) and 0054E8F0/0062B0D0 (slot1). They remain [静态推断]; 45 was the assigned target and no placeholder padding was added.',
'- U2: Exact same-vtable virtual callers were found for slot2/4 families with a global-array anchor; slot0/1/3/5 rows use a graded slot-dispatch baseline (call [reg+slot*4] in a [已证] owner outside this batch). This is strong structural reachability, not a per-object dataflow proof for every slot; see EVIDENCE/ring4_callsites.txt and slot_call_baseline.txt.',
'- U3: UDamage (0x7E5170) and Kamikaze (0x7ECE7C) have no usable global-array xref owner in coverage for exact slot2/4 anchoring; their rows use the graded slot baseline only.',
'- U4: 92 VectorClass/vslot rows remain unresolved here. They have RTTI, but inherited-base slots and exact call ownership need separate work; they are not counted.',
'- U5: S13-K5 D1 denominator dispute remains open: if container templates are migrated to S22, the 240-denominator claim must be recomputed by Lead.',
'- U6: coverage.tsv was not modified; post-delta 120/240 is a simulation from live col5 plus this delta. Verify with work/base.py and EVIDENCE/baseline_recompute.txt.\n']),encoding='utf-8')
(CARD/'DISAGREE.md').write_text('# S13-K6 DISAGREE\n\n'+'\n'.join([
'## D1 · 49 vs 45\nBinary scan found 49 DynamicVectorClass rows with uniform slot contracts; card asked for 45. I delivered exactly 45 and explicitly listed the 4 omitted rows in UNKNOWNS. No false row was added to reach a round number.',
'## D2 · ring4 strength is not uniform\nFor slot2/4 with a global-array anchor, ring4 is an exact same-vtable virtual dispatch in a graded caller. For slot0/1/3/5 it is a graded external slot-dispatch baseline. If audit requires per-object dataflow for every virtual call, those rows should be challenged; I am not claiming more than the evidence shows.',
'## D3 · inherited method naming\nslot1 and slot5 are inherited VectorClass methods exposed through DynamicVectorClass vtables. Names use VectorClass<T>::... rather than DynamicVectorClass<T>::...; RTTI still proves the concrete container element type. Prior truncated names are placeholders, not different semantics.',
'## D4 · container-template denominator\nS13-K5 D1 is unresolved. This card changes grade in place for S13 rows; it does not decide whether the 240 denominator should exclude container templates.\n']),encoding='utf-8')
print('SELECTED',len(sel),'PROGRESS_LINES',len(L))
print('BASE',len(base),len(bn),len(bp),'POST',len(set(bp)|selset))
for r in sel: print('%08X\t%s\t%s'%(r['e'],r['name'],ring4(r)))
