"""C01 census classifier -> coverage_delta.tsv + statistics.
Evidence priority:
  1) KB22 explicit vtable-slot names (hardcoded [proven] table)
  2) YRpp JMP_THIS/JMP_STD address-name (established name source)
  3) KB markdown address-name candidates
  4) RTTI vftable class -> subsystem
  5) strings / imports keyword -> subsystem
  6) call-graph propagation from named neighbors
  7) weak address-region prior (low)
Grades: high->[已证], med->[静态推断], low->[未证].
"""
import os, json, re, collections
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID=os.path.join(BASE,'EVIDENCE'); ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB=chr(9)

with open(ATLAS,encoding='utf-8',errors='replace') as f: lines=f.read().splitlines()
sl=lines[1:1293]
rows=[]
for ln in sl:
    p=ln.split(TAB)
    rows.append(dict(entry=int(p[0],16), entryhex=p[0], size=int(p[1]), ninstr=int(p[2]),
                     ncallers=int(p[3]), ncallees=int(p[4]), strings=p[8]))
yrpp=json.load(open(os.path.join(HERE,'yrpp_names.json'),encoding='utf-8'))
yin={int(k):v for k,v in yrpp.items()}
kbnm=json.load(open(os.path.join(HERE,'kb_names.json'),encoding='utf-8'))
kbn={int(k):v for k,v in kbnm.items()}
vf=json.load(open(os.path.join(HERE,'rtti_vtables.json'),encoding='utf-8'))['func_map']
vfin={int(k):v for k,v in vf.items()}
ev=json.load(open(os.path.join(EVID,'evidence_raw.json'),encoding='utf-8'))
cg=json.load(open(os.path.join(EVID,'callgraph.json'),encoding='utf-8'))

# KB22 vtable explicit names (proven, re_atlas/kb/22_abstractclass_vtable_slots.md)
KB22={
 0x00410260:('AbstractClass::QueryInterface','S05','COM IUnknown QueryInterface'),
 0x00410300:('AbstractClass::AddRef','S05','COM IUnknown AddRef (constant 1)'),
 0x00410310:('AbstractClass::Release','S05','COM IUnknown Release (constant 1)'),
 0x00410450:('AbstractClass::IsDirty','S05','returns !Dirty flag [+0x20]'),
 0x004103E0:('AbstractClass::GetSizeMax','S05','COM GetSizeMax with E_POINTER guard'),
 0x004105A0:('AbstractClass::~AbstractClass','S05','scalar deleting destructor, writes 4 vptrs'),
 0x00410470:('AbstractClass::Init','S05','empty Init stub'),
 0x00410480:('AbstractClass::PointerExpired','S05','empty PointerExpired stub (ret 8)'),
 0x00410410:('AbstractClass::Save','S17','serialize +0x10 dword and +0x20 bool to IStream'),
 0x00410490:('AbstractClass::CalculateChecksum','S05','returns -1 constant'),
 0x004104A0:('AbstractClass::GetOwningHouseIndex','S05','returns 0 (debated -1)'),
 0x004104B0:('AbstractClass::GetOwningHouse','S05','returns nullptr'),
 0x00410440:('AbstractClass::IsDead','S05','returns true constant'),
 0x004104C0:('AbstractClass::GetCoords','S05','default coords copy from .data template'),
 0x004104F0:('AbstractClass::GetDestination','S05','forwards slot 18 then copies 12 bytes'),
 0x00410520:('AbstractClass::IsOnFloor','S05','returns false'),
 0x00410530:('AbstractClass::IsInAir','S05','returns false'),
 0x00410540:('AbstractClass::GetAltCoords','S05','forwards slot 18 (ret 4)'),
 0x00410570:('AbstractClass::Update','S05','empty Update stub'),
}

# class -> subsystem mapping (substring match on RTTI class name, most specific first)
def class_to_subsys(cls):
    c=cls
    cl=c.lower()
    if 'vocclass' in cl or 'audiostream' in cl or 'audiocontroller' in cl: return 'S19'
    if 'bink' in cl: return 'S19'
    if any(k in cl for k in ('ccfileclass','cdfileclass','bufferiofileclass','rawfileclass','mixfileclass','ccinifile','ccini')): return 'S03'
    if any(k in cl for k in ('ainottrigger','aitrigger','houseclass','housetype','teamclass','teamtype','scriptclass','taskforce')): return 'S14'
    if any(k in cl for k in ('teventclass','tactionclass','tagclass','triggerclass')): return 'S15'
    if any(k in cl for k in ('animclass','animtype','voxelanim','particleclass','particlesystem')): return 'S20'
    if any(k in cl for k in ('buildinglight','alphalight','lightconvert','alpha shape','alphashape')): return 'S07'
    if any(k in cl for k in ('cellclass','mapclass','isometrictile','overlaytype','tiberiumclass','theatertype')): return 'S06'
    if any(k in cl for k in ('shroud','visibility','radarclass')): return 'S08'
    if any(k in cl for k in ('bulletclass','bullet type','warhead','weapontype','weaponclass')): return 'S13'
    if 'bombclass' in cl: return 'S13'
    if any(k in cl for k in ('footclass','jumpjet','locomotor','pathfind','subzone')): return 'S11'
    if any(k in cl for k in ('factoryclass','buildingclass','buildingtype','construction','production')): return 'S12'
    if any(k in cl for k in ('abstractclass','objectclass','technoclass','type class','typeclass','aircraftclass','unitclass','infantryclass','abstracttype')): return 'S05'
    if any(k in cl for k in ('vectorclass','dynamicvectorclass','genericlist','genericnode','listclass','list::','queue','stack','hash')): return 'S22'
    if any(k in cl for k in ('inotice','ipersist','iunknown','streamclass')): return 'S22'
    return None

# method/name keyword -> subsystem
def name_to_subsys(name):
    n=name.lower()
    if any(k in n for k in ('loadfromini','savetoini','readini','writeini','parseini')): return 'S04'
    if any(k in n for k in ('detonate','disarm','warhead','bullet','weapon','targetselect','verses')): return 'S13'
    if any(k in n for k in ('goonline','gooffline','getpower','enablepower','repair','percentbuilt')): return 'S12'
    if any(k in n for k in ('evabeacon','eva_','playsound','playspeech','audio','vocclass','wave','bink')): return 'S19'
    if any(k in n for k in ('ai:', 'aitrigger','register','conditionmet','housecredits','ironcurtain','chronosphere')): return 'S14'
    if any(k in n for k in ('save','load','serialize','swizzle','persist','stream')): return 'S17'
    if any(k in n for k in ('draw','blit','render','palette','shp','vxl','sprite')): return 'S07'
    if any(k in n for k in ('jumpjet','locomotor','findpath','move')): return 'S11'
    return None

# string/import keyword -> subsystem
def signal_to_subsys(strs, imports):
    txt=(' '.join(strs)+' '+' '.join(imports)).lower()
    if any(k in txt for k in ('eva_','audio','.wav','.idx','.bag','.mix','bink','vocclass')): return 'S19'
    if any(k in txt for k in ('aitrigger','aitriggertypes')): return 'S14'
    if any(k in txt for k in ('findfirstfile','findnextfile','findclose','readfile','writefile','createfile')): return 'S03'
    if any(k in txt for k in ('ini','uiname','abs')): return 'S04'
    if any(k in txt for k in ('percentbuilt','nodecount','buildingon')): return 'S12'
    if any(k in txt for k in ('criticalsection','getcurrentthreadid','sleep')): return 'S02'
    if any(k in txt for k in ('timegettime','queryperformance','clock')): return 'S01'
    if any(k in txt for k in ('cocreateinstance','sysallocstring','multibytetowidechar','setrect')): return 'S22'
    if any(k in txt for k in (' shield','rotor','aircraft','landable','airportbound','fighter','carryall')): return 'S05'
    if any(k in txt for k in ('terrain','overlay','shadow','theater','newtheater','scorch','crater','tile')): return 'S06'
    if any(k in txt for k in ('shroud','fog','radar')): return 'S08'
    if any(k in txt for k in ('game.fnt','font','sprite','palette')): return 'S07'
    if any(k in txt for k in ('base64','abcdefghijklmnopqrstuvwxyz0123456789+/')): return 'S22'
    return None

# source-file string -> subsystem (source file name implies owning module)
def srcfile_to_subsys(strs):
    for s in strs:
        m=re.search(r'([A-Za-z0-9_]+)\.(?:cpp|CPP|c|C)\b',s)
        if m:
            f=m.group(1).lower()
            if 'abs' in f or 'type' in f: return 'S05'
            if 'beacon' in f: return 'S16'
            if 'audio' in f or 'voc' in f: return 'S19'
            if 'ini' in f: return 'S04'
            if 'bink' in f or 'video' in f: return 'S19'
    return None

SUBSYS_NAMES={
 'S01':'Startup/MainLoop/Clock','S02':'CRT/Memory/Exceptions','S03':'FileSystem/MIX','S04':'INI/Rules',
 'S05':'ObjectModel/Vtables','S06':'Map/Cell/Terrain','S07':'Render/Blit/SHP/VXL','S08':'Shroud/Radar',
 'S09':'UI/Input/Commands','S10':'Mission/UnitAI','S11':'Locomotion/Pathfind','S12':'Production/Economy',
 'S13':'Combat/Weapons','S14':'House/AI/Team','S15':'Triggers/TAction','S16':'Superweapons',
 'S17':'Save/Serialize','S18':'Network','S19':'Audio/EVA/Video','S20':'Particles/Anim',
 'S21':'Campaign/Score','S22':'Math/String/ExtDLL'}

# FIX: name overrides verified against YRpp headers (see work/verify_name_fixes.py)
# 0x40E320 has two YRpp records (GenericNode::GenericNode and template Node::Node);
# audit prefers the non-template base class GenericNode.
NAME_OVERRIDE={0x40E320:'GenericNode::GenericNode'}
# FIX: 6 rows whose YRpp "name" is a placeholder sub_XXXXXX are NOT established
# names -> downgrade from [已证] to [静态推断] (discipline R13 §6-9 / audit §四).
PLACEHOLDER_RE=re.compile(r'sub_[0-9A-Fa-f]{6}')

def clean_yfull(r):
    full=r.get('full','')
    return full if full else r.get('name','')

def best_yrpp(e):
    rs=yin.get(e,[])
    if not rs: return None
    # prefer entry with class and name
    rs2=sorted(rs,key=lambda r:(bool(r.get('cls') and r.get('name')), len(r.get('full',''))),reverse=True)
    r=rs2[0]
    return clean_yfull(r), r

def best_kb(e):
    rs=kbn.get(e,[])
    if not rs: return None
    for r in rs:
        for c in r['cands']:
            if re.match(r'^[A-Za-z_][A-Za-z0-9_:]{1,40}$',c) and c.lower() not in ('ret','arg','this','mov','eax','true'):
                return c, r['file']
    return None

# address-region priors derived from strong clusters (weak, [未证])
def region_prior(e):
    if e<0x4011C0: return 'S02'  # CRT/entry region
    if 0x4011C0<=e<0x409000: return 'S19'  # VocClass/audio region
    if 0x409000<=e<0x40A000: return 'S01'  # clock/thread primitives
    if 0x40A000<=e<0x410000: return 'S03'  # file/MIX region
    if 0x410000<=e<0x413000: return 'S05'  # AbstractClass/type class region
    if 0x413000<=e<0x41F000: return 'S05'  # type classes (aircraft/anim/etc)
    if 0x41F000<=e<0x422000: return 'S14'  # AITrigger/House region
    if 0x422000<=e<0x42E000: return 'S06'  # anim/terrain/search region
    if 0x42E000<=e<0x432000: return 'S12'  # houses/economy region
    if 0x432000<=e<0x434500: return 'S19'  # Bink video region
    if 0x434500<=e<0x444000: return 'S07'  # UI/font/drawing region
    if 0x444000<=e<0x457000: return 'S19'  # EVA audio region
    return 'S22'

results=[]
for row in rows:
    e=row['entry']
    e0=ev.get(str(e),{})
    strs=[x['s'] for x in e0.get('strings',[])] + [s for s in row['strings'].split(';') if s]
    imports=[x['name'] for x in e0.get('imports',[])]
    subsys=None; conf=None; grade=None; name=''; evidence=[]
    # 1) KB22 explicit
    if e in KB22:
        name,subsys,desc=KB22[e]; conf='high'; grade='[已证]'; evidence.append('kb22-slot')
    # 2) YRpp
    y=best_yrpp(e)
    if (conf is None or conf!='high') and y:
        yfull,yr=y
        if e in NAME_OVERRIDE:
            yfull=NAME_OVERRIDE[e]
        name=yfull; ns=name_to_subsys(name)
        # class from vf if available, else from yfull prefix
        cls=None
        if e in vfin: cls=vfin[e][0]['cls']
        cs=class_to_subsys(cls) if cls else None
        subsys=ns or cs or 'S05'
        if PLACEHOLDER_RE.search(name):
            # placeholder name: keep the YRpp class context but NOT [已证]
            conf='med'; grade='[静态推断]'; evidence.append('yrpp-placeholder-downgrade')
        else:
            conf='high'; grade='[已证]'; evidence.append('yrpp')
    # 3) KB name candidates (bare class names are weak -> med only)
    k=best_kb(e)
    if conf is None and k:
        kname,kfile=k
        name=kname; ns=name_to_subsys(kname)
        cs=None
        if e in vfin: cs=class_to_subsys(vfin[e][0]['cls'])
        subsys=ns or cs or region_prior(e)
        if re.search(r'(Class|Struct)$',kname) and '::' not in kname:
            conf='med'; grade='[静态推断]'; evidence.append('kb-weak:'+kfile[:6])
        else:
            conf='high'; grade='[已证]'; evidence.append('kb:'+kfile[:6])
    # 4) vftable class
    if conf is None and e in vfin:
        clss=[m['cls'] for m in vfin[e]]
        cands=[class_to_subsys(c) for c in clss]
        cands=[c for c in cands if c]
        if cands:
            subsys=collections.Counter(cands).most_common(1)[0][0]
            # pick a representative class name
            rep=vfin[e][0]['cls']
            slot=vfin[e][0]['slot']
            name='%s::vslot%d'%(rep[:28],slot)
            conf='med'; grade='[静态推断]'; evidence.append('rtti-vftable')
    # 5) strings/imports/source-file
    if conf is None:
        ssub=signal_to_subsys(strs,imports)
        fsub=srcfile_to_subsys(strs)
        if ssub or fsub:
            subsys=fsub or ssub; conf='med'; grade='[静态推断]'; evidence.append('string/import' if ssub else 'srcfile')
    # 6) call-graph propagation from named/high neighbors (one hop, both directions)
    if conf is None:
        votes=[]
        for c in e0.get('callees',[]):
            t=c['target']
            if t in KB22: votes.append(KB22[t][1])
            elif t in yin:
                nn=best_yrpp(t)
                if nn and nn[0]:
                    cs2=class_to_subsys(vfin[t][0]['cls']) if t in vfin else None
                    v=name_to_subsys(nn[0]) or cs2
                    if v: votes.append(v)
        for c in cg.get(str(e),[]):
            t=c['src']
            if t in KB22: votes.append(KB22[t][1])
            elif t in yin:
                nn=best_yrpp(t)
                if nn and nn[0]:
                    cs2=class_to_subsys(vfin[t][0]['cls']) if t in vfin else None
                    v=name_to_subsys(nn[0]) or cs2
                    if v: votes.append(v)
        votes=[v for v in votes if v]
        if votes:
            subsys=collections.Counter(votes).most_common(1)[0][0]
            conf='med'; grade='[静态推断]'; evidence.append('callgraph')
    # 7) weak region
    if conf is None:
        subsys=region_prior(e); conf='low'; grade='[未证]'; evidence.append('region-prior')
    if not name: name='sub_%08X'%e
    # semantics
    if grade=='[已证]':
        if e in KB22: sem=KB22[e][2]
        elif y: sem='YRpp named: '+(y[0].split('::')[-1])
        else: sem='KB-named '+name
    elif grade=='[静态推断]':
        sem='[静态推断] '+SUBSYS_NAMES.get(subsys,subsys)+' member ('+','.join(evidence)+')'
    else:
        sem='[未证] '+SUBSYS_NAMES.get(subsys,subsys)+' region guess'
    results.append(dict(entry=e,entryhex=row['entryhex'],subsys=subsys,name=name,sem=sem,
                        grade=grade,conf=conf,evidence=';'.join(evidence)))

# write coverage_delta.tsv
with open(os.path.join(BASE,'coverage_delta.tsv'),'w',encoding='utf-8') as f:
    f.write('entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n')
    for r in results:
        # evidence_path = relative evidence file with raw dump
        ep='EVIDENCE/evidence_raw.json#%08X'%r['entry']
        f.write('%s\t%s\t%s\t%s\t%s\t%s\n'%(r['entryhex'],r['subsys'],r['name'],r['sem'],r['grade'],ep))
# write reasons for transparency
with open(os.path.join(EVID,'classification_reasons.tsv'),'w',encoding='utf-8') as f:
    f.write('entry\tsubsys\tconf\tgrade\tevidence\tsource_strings\timports\n')
    for r,row in zip(results,rows):
        e0=ev.get(str(r['entry']),{})
        ss=';'.join(x['s'][:30] for x in e0.get('strings',[])[:4])
        im=';'.join(x['name'].split('!')[-1] for x in e0.get('imports',[])[:4])
        f.write('%08X\t%s\t%s\t%s\t%s\t%s\t%s\n'%(r['entry'],r['subsys'],r['conf'],r['grade'],r['evidence'],ss,im))
json.dump(results,open(os.path.join(EVID,'classification_results.json'),'w',encoding='utf-8'),ensure_ascii=False)

# stats
print('total',len(results))
print('by conf:',dict(collections.Counter(r['conf'] for r in results)))
print('by grade:',dict(collections.Counter(r['grade'] for r in results)))
print('by subsystem:',dict(sorted(collections.Counter(r['subsys'] for r in results).items())))
hi=sum(1 for r in results if r['conf']=='high')
print('high count',hi,'ratio %.3f'%(hi/len(results)))
print('unclassifiable (low conf only):',sum(1 for r in results if r['conf']=='low'))
