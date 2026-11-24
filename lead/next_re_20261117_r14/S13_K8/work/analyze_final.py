# -*- coding: utf-8 -*-
import sys,pefile,capstone,struct,csv,random,re,json,collections
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
D=open(P,'rb').read(); pe=pefile.PE(P,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip('\x00'),IMG+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def sec_of(va):
    for n,b,vs,pt,rs in SECS:
        if b<=va<b+vs:return n,b,vs,pt,rs
def rd(va,n):
    s=sec_of(va)
    if not s:return b''
    _,b,vs,pt,rs=s; return D[pt+(va-b):pt+(va-b)+n]
def u32(va):
    d=rd(va,4); return struct.unpack('<I',d)[0] if len(d)==4 else None
def cstr(va,lim=120):
    out=b''
    for i in range(lim):
        c=rd(va+i,1)
        if not c or c==b'\x00':break
        out+=c
    return out.decode('latin1')
def fo2va(fo):
    for n,b,vs,pt,rs in SECS:
        if pt<=fo<pt+rs:return b+(fo-pt)
    return None
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.skipdata=True; MD.detail=True
TEXT=[s for s in SECS if s[0]=='.text'][0]
tname,tva,tvs,tptr,trs=TEXT

# TDs
tds={}
for nm,b,vs,pt,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')):continue
    for va in range(b,b+vs-8,4):
        if rd(va,4) in (b'.?AV',b'.?AU'):
            name=cstr(va,120)
            if len(name)>4 and name.endswith('@@'):tds[va-8]=name
tdset=set(tds)
def rtti_at_vt(vt):
    cp=u32(vt-4)
    if cp is None or cp==0:return None,None
    td=u32(cp+0xC)
    return (cp,tds[td]) if td in tdset else (None,None)

# working set
BC=BASE+r'\S13_K5\EVIDENCE\byte_census.tsv'
exK9=set('0040B880 0040B930 0040F7C0 0040FD90 0040FE40 0046B7E0 0046B890 0062B250 0062B300 0065C0D0 0065C180 0048AD60 0054E8E0 0048AD70'.split())
W=[]
with open(BC,encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        if r['判定'].startswith('不可证') and r['entry'].upper() not in exK9:
            W.append({'ea':r['entry'].upper(),'va':int(r['entry'],16),'name':r['name'],'oldgrade':r['grade'],'missing':r['缺哪一环'],'bytes':r['字节依据']})
eset=set(w['va'] for w in W)

# vtable slots (rdata/data aligned dwords == entry)
slotmap=collections.defaultdict(list)
for nm,b,vs,pt,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')):continue
    for sa in range(b,b+vs-4,4):
        raw=rd(sa,4)
        if len(raw)<4:continue
        v=struct.unpack('<I',raw)[0]
        if v not in eset:continue
        best=None
        for slot in range(0,300):
            vt=sa-4*slot; col,cname=rtti_at_vt(vt)
            if col is not None:best=(sa,vt,slot,col,cname);break
        slotmap[v].append(best if best else (sa,None,None,None,None))

# direct calls (instruction-boundary E8)
textbytes=D[tptr:tptr+trs]
calltargets=collections.defaultdict(list)
for ins in MD.disasm(textbytes,tva):
    if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==capstone.x86.X86_OP_IMM:
        calltargets[ins.operands[0].imm & 0xffffffff].append(ins.address)

# vtable install sites: ALL C7 /0 imm32 register forms + absolute
found=collections.defaultdict(list)
# Robust: any imm32 reference to a vtable VA (0x7e0000..0x820000) in .text bytes.
# This covers C7 /0 writes (all modrm/SIB forms), push imm32, mov r32,imm32.
for i in range(len(textbytes)-4):
    imm=struct.unpack('<I',textbytes[i:i+4])[0]
    if 0x7e0000<=imm<=0x820000:
        va=fo2va(tptr+i)
        prev=textbytes[max(0,i-2):i].hex()
        found[imm].append((va,'IMM_ref_prev='+prev))

def body_features(va,maxbytes=1200):
    code=rd(va,maxbytes)
    ins=[]
    for x in MD.disasm(code,va):
        ins.append(x)
        if x.mnemonic in ('ret','retf'): break
    feats={'nins':len(ins),'calls':[],'vptr_writes':[],'ret4':False,'test_al1':False,'opdel':0,'pushmov':False}
    for x in ins[:250]:
        m=x.mnemonic;o=x.op_str
        if m=='call' and x.operands and x.operands[0].type==capstone.x86.X86_OP_IMM:
            feats['calls'].append(x.operands[0].imm & 0xffffffff)
        if m in ('ret','retf') and o.strip()=='4':feats['ret4']=True
        if m=='test' and ('al' in o or 'byte ptr' in o) and o.strip().endswith(', 1'):feats['test_al1']=True
        if m=='call' and o.strip()=='0x7c8b3d':feats['opdel']+=1
        if m=='mov' and 'dword ptr [' in o and ', 0x7' in o:feats['vptr_writes'].append(o)
    if len(ins)>=2 and ins[0].mnemonic=='push' and ins[1].mnemonic=='mov' and ins[1].op_str=='esi, ecx':feats['pushmov']=True
    return feats

def classify(w,feats,slots):
    name=w['name']
    vts=set(s[1] for s in slots if s[1])
    # vptr write must match one of the entry's vtables (byte-level self-install) - strong SDD
    self_vptr=any(any(hex(vt)[2:].lower().rjust(8,'0') in vw.lower() for vt in vts) for vw in feats['vptr_writes'])
    if feats['ret4'] and feats['opdel']>=1 and (self_vptr or feats['pushmov']):
        return ('scalar_deleting_dtor', self_vptr)
    if feats['ret4'] and feats['opdel']>=2:
        return ('scalar_deleting_dtor', self_vptr)
    if feats['nins']<=10 and feats['ret4']:
        return ('tiny_ret4', False)
    return ('other', False)

results=[]
for w in W:
    va=w['va']
    aligned=(va%16==0)
    fb=rd(va,1)[0] if rd(va,1) else 0
    firstbad=fb in (0xE8,0xE9,0xEB)
    slots=slotmap.get(va,[])
    has_vt=any(s[1] is not None for s in slots)
    cnames=sorted(set(s[4] for s in slots if s[4]))
    feats=body_features(va)
    sem,selfvptr=classify(w,feats,slots)
    dcs=calltargets.get(va,[])
    vts=set(s[1] for s in slots if s[1])
    installs=[]
    for vt in vts:
        for site,tag in found.get(vt,[]): installs.append((site,tag,vt))
    # rings
    r1=has_vt or (aligned and not firstbad and feats['nins']>=2)
    r2=bool(cnames)
    r3=(sem=='scalar_deleting_dtor')
    r4=bool(dcs) or bool(installs)
    results.append({'ea':w['ea'],'name':w['name'],'oldgrade':w['oldgrade'],'missing':w['missing'],
        'aligned':aligned,'firstbad':firstbad,'pre':rd(va-2,2).hex(),'slots':slots,'cnames':cnames,
        'feats':{k:v for k,v in feats.items() if k!='vptr_writes'},'vptr_writes':feats['vptr_writes'],
        'sem':sem,'selfvptr':selfvptr,'direct_calls':len(dcs),'direct_call_sites':dcs[:8],
        'installs':installs[:10],'r1':r1,'r2':r2,'r3':r3,'r4':r4})

# baseline
random.seed(20261118)
base_pass=0;base_tried=0;base_ex=[]
for _ in range(3000):
    va=(tva+random.randrange(0,tvs-0x800))&~0xf
    if va in eset:continue
    base_tried+=1
    sl=[]
    for sa in range(va-4*250,va+4,4):
        col,cn=rtti_at_vt(sa)
        if col is not None and (va-sa)%4==0:sl.append((sa,sa,(va-sa)//4,col,cn));break
    hv=bool(sl); feats=body_features(va,maxbytes=400)
    sem,sv=classify({'name':'RANDOM'},feats,sl)
    dcs=calltargets.get(va,[])
    vts=set(s[1] for s in sl if s[1]); inst=[(s,t,vt) for vt in vts for s,t in found.get(vt,[])]
    r1=hv or (not feats['firstbad'] if 'firstbad' in feats else True) and feats['nins']>=2
    r2=hv and any(s[4] for s in sl)
    r3=(sem=='scalar_deleting_dtor') or (feats['nins']>=2 and bool(feats['calls']) and bool(feats['vptr_writes']))
    r4=bool(dcs) or bool(inst)
    if r1 and r2 and r3 and r4:
        base_pass+=1
        if len(base_ex)<8:base_ex.append(va)
    if base_tried>=150:break

def grade(r):
    n=sum([int(r['r1']),int(r['r2']),int(r['r3']),int(r['r4'])])
    return '[已证]' if n==4 else ('[静态推断]' if n==3 else '[未证]')
for r in results:r['grade']=grade(r)
cnt=collections.Counter(r['grade'] for r in results)
out={'working_set':len(W),'counts':dict(cnt),'baseline':{'tried':base_tried,'pass':base_pass,'rate':base_pass/max(base_tried,1),'examples':base_ex},'results':results}
fn=BASE+r'\S13_K8\EVIDENCE\analysis_full.json'
open(fn,'w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=1))
print('working_set',len(W),'counts',dict(cnt))
print('BASELINE',base_tried,base_pass,'%.3f%%'%(100*base_pass/max(base_tried,1)))
a18=set('0075E510 0065BED0 0040BBC0 0040BC10 0040F8A0 0040F8F0 0040FE70 0040FEC0 0046B8C0 0046B910 0048AFD0 0048B020 0054EB50 0054EBA0 0062B330 0062B380 0065C1B0 0065C200'.split())
print('AUDIT18 grades:')
for r in results:
    if r['ea'] in a18:print(' ',r['ea'],r['grade'],[r['r1'],r['r2'],r['r3'],r['r4']],r['sem'],'selfvptr',r['selfvptr'],'inst',len(r['installs']))
print('SDD count',sum(1 for r in results if r['sem']=='scalar_deleting_dtor'))
