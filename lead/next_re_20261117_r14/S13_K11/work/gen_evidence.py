# -*- coding: utf-8 -*-
import json, os
BASE=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K11"
EV=os.path.join(BASE,'EVIDENCE')
A=json.load(open(os.path.join(BASE,'work','ANALYSIS.json'),'r',encoding='utf-8'))
D=json.load(open(os.path.join(BASE,'work','EVIDENCE_DETAIL.json'),'r',encoding='utf-8'))
CONF=json.load(open(os.path.join(BASE,'work','CONFLICT_SCAN.json'),'r',encoding='utf-8'))
ROOT=r"D:\Project\ra2-campaign-forge"

ROWS={
 "0040B820":("VectorClass<BombClass*>",".?AV?$VectorClass@PAVBombClass@@@@","0x8168F0","0x7E17EC",4,"0x7E17FC","0x40B60A",True,"0x87F5D8"),
 "0040F5E0":("DynamicVectorClass<WarheadTypeClass*>",".?AV?$DynamicVectorClass@PAVWarheadTypeClass@@@@","0x817660","0x7E1E84",3,"0x7E1E90","0x40F4AD",True,"0x8874C0"),
 "0040F760":("VectorClass<WarheadTypeClass*>",".?AV?$VectorClass@PAVWarheadTypeClass@@@@","0x817628","0x7E1EA4",4,"0x7E1EB4","0x40F4D8",True,"0x8874C0"),
 "0040FD30":("VectorClass<WeaponTypeClass*>",".?AV?$VectorClass@PAVWeaponTypeClass@@@@","0x8176A8","0x7E1EF4",4,"0x7E1F04","0x40FB78",True,"0x887568"),
 "0046B780":("VectorClass<BulletClass*>",".?AV?$VectorClass@PAVBulletClass@@@@","0x81AF10","0x7E4698",4,"0x7E46A8","0x46632E",True,"0x89DE18"),
 "0048AE90":("VectorClass<DamageGroup*>",".?AV?$VectorClass@PAUDamageGroup@@@@","0x81D170","0x7E5144",4,"0x7E5154","0x489B1E",False,"-"),
 "0054EA10":("VectorClass<KamikazeControl*>",".?AV?$VectorClass@PAUKamikazeControl@@@@","0x829678","0x7ECE9C",4,"0x7ECEAC","0x54E31D",True,"0xABC604"),
 "0062B1F0":("VectorClass<ParasiteClass*>",".?AV?$VectorClass@PAVParasiteClass@@@@","0x8365E0","0x7EF844",4,"0x7EF854","0x6291D8",True,"0xAC4910"),
 "0065C070":("VectorClass<RadSiteClass*>",".?AV?$VectorClass@PAVRadSiteClass@@@@","0x8395A0","0x7F07C4",4,"0x7F07D4","0x65B1A8",True,"0xB04BD0"),
}
ORDER=list(ROWS.keys())
def hx(a): return "0x%08X"%a

s="# S13-K11 bodies, capstone 5.0.7 skipdata=True, independent script work/k11_detail.py\n"
s+="# exe ra2youli\\gamemd.exe SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476\n\n"
for e in ORDER:
    m=ROWS[e]; r=D['rows'][e]
    meth='Clear' if r['kind']=='Clear' else 'FindItemIndex'
    s+="## %s  %s::%s  slot%d\n"%(e,m[0],meth,r['slot'])
    for b in r['body']:
        s+="  %s  %-16s %-6s %s\n"%(hx(b['addr']),b['bytes'],b['mn'],b['op'])
    s+="\n"
open(os.path.join(EV,'BODIES.txt'),'w',encoding='utf-8').write(s)

s="entry\tmethod\tslot\trtti_string_va\trtti_string\tclass\tvtable\ttd\tslot_entry_va\tall_occurrences\tn_valid_rtti_vtables\n"
for e in ORDER:
    m=ROWS[e]; r=D['rows'][e]
    s+="%s\t%s::%s\tslot%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t1\n"%(
       e,m[0],r['kind'],r['slot'],m[2],m[1],m[0],m[3],r['vtdump'][0]['td'],m[5],','.join(o['hit'] for o in r['occurrences_context']))
open(os.path.join(EV,'RTTI_VT.tsv'),'w',encoding='utf-8').write(s)

s="entry\tvtable\tform\tprimary_install\tprimary_global\tall_installs\tdirect_call_count\n"
for e in ORDER:
    m=ROWS[e]; a=A['rows'][e]
    allinst=' ; '.join("%s(%s %s)"%(i['insn'],i['mn'],i['op']) for i in a['installs'])
    form='C7 05 global' if m[7] else 'stack/this vptr write'
    s+="%s\t%s\t%s\t%s\t%s\t%s\t%d\n"%(e,m[3],form,m[6],m[8],allinst,a['direct_call_count'])
open(os.path.join(EV,'INSTALLS.tsv'),'w',encoding='utf-8').write(s)

s="entry\tmethod\tdirect_call_count(E8 rel32, insn-boundary)\traw_E8_hits\tconclusion\n"
for e in ORDER:
    m=ROWS[e]; a=A['rows'][e]
    s+="%s\t%s::%s\t%d\t%s\tonly live-vptr-install / virtual dispatch; no direct call (same shape as K8/K10; D-39 applies)\n"%(
       e,m[0],D['rows'][e]['kind'],a['direct_call_count'],','.join(a['raw_e8_hits']) or '0')
open(os.path.join(EV,'DIRECT_CALLS.tsv'),'w',encoding='utf-8').write(s)

s="# 018 entry-address full-library conflict scan (9 addresses)\n"
s+="# roots: docs/re/ + re_atlas/kb/ + lead/GOAL_THREE_TARGETS_20261018.md + COVERAGE/\n"
s+="# match: 8-hex entry (optional 0x, case-insensitive)\n\n"
for e in ORDER:
    hs=[h for h in CONF['hits'] if h['entry']==e]
    real=[h for h in hs if not h['file'].lower().endswith(os.path.join('coverage','coverage.tsv'))]
    s+="%s: total=%d real=%d "%(e,len(hs),len(real))
    if not real: s+="=> no name conflict (only coverage.tsv placeholder row itself)\n"
    else:
        s+="=> REVIEW:\n"
        for h in real: s+="   %s:%d %s\n"%(h['file'].replace(ROOT,'.'),h['line'],h['text'])
open(os.path.join(EV,'CONFLICT_SCAN.txt'),'w',encoding='utf-8').write(s)

lines=[
"# Jiegou zhengju (disanfang dulitongdao): YRpp/ArrayClasses.h shengming xu",
"> wenjian D:/Project/ra2-campaign-forge/YRpp/ArrayClasses.h ; hanghao xianchang dubao hedui.",
"",
"## VectorClass<T> (class hang 13) xu hanshu shengming xu:",
"slot0 = virtual ~VectorClass() noexcept  -- hang 52",
"slot1 = virtual bool operator==(const VectorClass&) const  -- hang 68",
"slot2 = virtual bool SetCapacity(int, T* = nullptr)  -- hang 87",
"slot3 = virtual void Clear()  -- hang 123",
"slot4 = virtual int FindItemIndex(const T&) const  -- hang 129",
"slot5 = virtual int GetItemIndex(const T*) const final  -- hang 143",
"slot6 = virtual T GetItem(int) const final  -- hang 151",
"ziduan: Items hang183(+4), Capacity hang184(+8), IsInitialized hang185(+0xC), IsAllocated hang186(+0xD).",
"FindItemIndex xunhuan shangjie yong Capacity: for(auto i=0;i<this->Capacity;++i) hang 134.",
"GetItem/GetItemIndex biao final => DV bu fugai (⑯) => gui jilei VectorClass<X*>.",
"",
"## DynamicVectorClass<T> : VectorClass<T> (class hang 194)",
"slot2 SetCapacity override hang231 ; slot3 Clear override hang241 ; slot4 FindItemIndex override final hang246",
"ziduan Count hang 338(+0x10), CapacityIncrement hang339.",
"DV Clear额写 this->Count=0 hang 243 ; DV FindItemIndex xunhuan shangjie yong Count hang 251.",
"",
"## Benka jiaocha hedui",
"- 8 ge slot4 hang tinei xunhuan shangjie = [ecx+8] (=Capacity, hang134), fei [ecx+0x10] (=Count, hang251) => yu RTTI .?AV?$VectorClass@.. yizhi => VectorClass<X*>::FindItemIndex.",
"- 0040F5E0 RTTI wei DynamicVectorClass<WarheadTypeClass*>, tinei mov [esi+0x10],ebx @0x40F5E9 = Count=0 (hang243) => DynamicVectorClass<WarheadTypeClass*>::Clear, yuyi han +0x10 xiedian.",
"- Wu U qianzhui leiming: RTTI PAU = zhixiang struct; leiming DamageGroup / KamikazeControl (ying yueshu 1).",
"",
]
open(os.path.join(EV,'STRUCTURE.md'),'w',encoding='utf-8').write("\n".join(lines))

s="# exact dispatch anchors: 0x4386AB call [edx+0x10] then cmp eax,-1 used as index; 0x43942B same.\n"
s+="# slot4=FindItemIndex, returns index / -1=not found; contract form alone has zero discrimination, see PROGRESS.\n\n"
s+=json.dumps(D['dispatch_anchors'],ensure_ascii=False,indent=2)+"\n"
open(os.path.join(EV,'DISPATCH_ANCHORS.txt'),'w',encoding='utf-8').write(s)

print("EVIDENCE written:",sorted(os.listdir(EV)))
