# -*- coding: utf-8 -*-
import sys, pefile, capstone, struct, csv, random, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
DATA=open(P,'rb').read()
pe=pefile.PE(P,fast_load=True)
IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip('\x00'), IMG+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
TEXT=[s for s in SECS if s[0]=='.text'][0]
def sec_of(va):
    for n,b,vs,ptr,rs in SECS:
        if b<=va<b+vs: return n,b,vs,ptr,rs
    return None
def rd(va,n):
    s=sec_of(va)
    if not s: return b''
    _,b,vs,ptr,rs=s; return DATA[ptr+(va-b):ptr+(va-b)+n]
def u32(va):
    d=rd(va,4); return struct.unpack('<I',d)[0] if len(d)==4 else None
def cstr(va,lim=120):
    out=b''
    for i in range(lim):
        c=rd(va+i,1)
        if not c or c==b'\x00': break
        out+=c
    return out.decode('latin1')
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.skipdata=True; MD.detail=True

# --- TDs / COLs ---
tds={}
for nm,b,vs,ptr,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')): continue
    for va in range(b, b+vs-8, 4):
        if rd(va,4) in (b'.?AV', b'.?AU'):
            name=cstr(va,120)
            if len(name)>4 and name.endswith('@@'): tds[va-8]=name
tdset=set(tds)
def rtti_at_vt(vt):
    cp=u32(vt-4)
    if cp is None or cp==0: return None,None
    td=u32(cp+0xC)
    return (cp,tds[td]) if td in tdset else (None,None)

# --- working set ---
BC=BASE+r'\S13_K5\EVIDENCE\byte_census.tsv'
exK9=set('0040B880 0040B930 0040F7C0 0040FD90 0040FE40 0046B7E0 0046B890 0062B250 0062B300 0065C0D0 0065C180 0048AD60 0054E8E0 0048AD70'.split())
W=[]
with open(BC,encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        if r['判定'].startswith('不可证') and r['entry'].upper() not in exK9:
            W.append({'ea':r['entry'].upper(),'va':int(r['entry'],16),'name':r['name'],'oldgrade':r['grade'],'missing':r['缺哪一环'],'bytes':r['字节依据']})
eset=set(w['va'] for w in W)

# --- find vt slots for each entry (aligned dwords in rdata/data) ---
slotmap=collections.defaultdict(list)  # va -> [(slot_addr, vt, slot, col, cname)]
for nm,b,vs,ptr,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')): continue
    for sa in range(b, b+vs-4, 4):
        raw=rd(sa,4)
        if len(raw)<4: continue
        v=struct.unpack('<I',raw)[0]
        if v not in eset: continue
        best=None
        for slot in range(0,300):
            vt=sa-4*slot
            col,cname=rtti_at_vt(vt)
            if col is not None:
                best=(sa,vt,slot,col,cname); break
        slotmap[v].append(best if best else (sa,None,None,None,None))

# --- direct call sites: scan .text E8 rel32 and FF /2 (call [reg]) not needed for direct ---
# Build set of all E8 call targets at instruction boundaries via linear disasm of .text
tname,tva,tvs,tptr,trs=TEXT
textbytes=DATA[tptr:tptr+trs]
calltargets=collections.defaultdict(list)
for ins in MD.disasm(textbytes, tva):
    if ins.mnemonic=='call' and ins.operands and ins.operands[0].type==capstone.x86.X86_OP_IMM:
        calltargets[ins.operands[0].imm & 0xffffffff].append(ins.address)

# --- vtable install sites: C7 05 <abs32> <imm32> = mov dword[abs],imm32 ; also C7 0x / r ---
# scan raw bytes for pattern C7 05 X X X X V V V V where VV==vt
instpat=collections.defaultdict(list)
raw=DATA
for i in range(len(raw)-10):
    if raw[i]==0xC7 and raw[i+1]==0x05:
        dest=struct.unpack('<I',raw[i+2:i+6])[0]
        imm=struct.unpack('<I',raw[i+6:i+10])[0]
        if imm>0x400000:  # candidate VA write
            instpat[imm].append((IMG+0x1000+i, dest))  # approximate VA; refine later
# refine VA: find which section the file offset belongs to
def fileoff_to_va(fo):
    for n,b,vs,ptr,rs in SECS:
        if ptr<=fo<ptr+rs: return b+(fo-ptr)
    return None
instpat2=collections.defaultdict(list)
for i in range(len(raw)-10):
    if raw[i]==0xC7 and raw[i+1]==0x05:
        dest=struct.unpack('<I',raw[i+2:i+6])[0]
        imm=struct.unpack('<I',raw[i+6:i+10])[0]
        va=fileoff_to_va(i)
        if va is not None and imm>0x400000:
            instpat2[imm].append((va,dest))

# --- body features ---
def body_features(va, maxbytes=1200):
    code=rd(va,maxbytes)
    ins=list(MD.disasm(code,va))
    # stop at first ret for feature extraction (but include branches)
    feats={'nins':len(ins),'call_targets':[],'vptr_writes':[],'ret4':False,'test_al1':False,
           'operator_delete':0,'push_esi_mov_esi_ecx':False,'strings':[]}
    for x in ins[:80]:
        m=x.mnemonic; o=x.op_str
        if m=='call' and x.operands and x.operands[0].type==capstone.x86.X86_OP_IMM:
            feats['call_targets'].append(x.operands[0].imm & 0xffffffff)
        if m in ('ret','retf') and o.strip()=='4': feats['ret4']=True
        if m=='test' and '1' in o and ('al' in o or 'byte ptr' in o): feats['test_al1']=True
        if m=='call' and o.strip()=='0x7c8b3d': feats['operator_delete']+=1
        # vptr writes: mov dword ptr [esi/edi/reg], 0x7e.... / 0x7f....
        if m=='mov' and 'dword ptr [' in o and ', 0x7' in o:
            feats['vptr_writes'].append(o)
    if len(ins)>=2 and ins[0].mnemonic=='push' and ins[0].op_str=='esi' and ins[1].mnemonic=='mov' and ins[1].op_str=='esi, ecx':
        feats['push_esi_mov_esi_ecx']=True
    return feats

# --- classify semantics ---
def classify(w, feats, slots):
    name=w['name']
    # scalar deleting destructor pattern
    is_sdd = (feats['ret4'] and feats['operator_delete']>=1 and 
              (feats['push_esi_mov_esi_ecx'] or any('[' in v for v in feats['vptr_writes'])))
    if is_sdd:
        return 'scalar_deleting_dtor'
    if any(s[2]==0 for s in slots if s[1]) and feats['operator_delete']>=2 and feats['ret4']:
        return 'container_scalar_deleting_dtor'
    # tiny accessors
    if feats['nins']<=10 and feats['ret4']:
        return 'tiny_ret4'
    return 'other'

# --- main loop: produce rows ---
results=[]
for w in W:
    va=w['va']; ea=w['ea']
    # ring1 entry
    aligned=(va%16==0)
    fb=rd(va,1)[0] if rd(va,1) else 0
    firstbad = fb in (0xE8,0xE9,0xEB)
    pre=rd(va-2,2).hex() if va>=IMG+0x1000 else ''
    slots=slotmap.get(va,[])
    has_vt=any(s[1] is not None for s in slots)
    # ring2 class
    cnames=sorted(set(s[4] for s in slots if s[4]))
    # ring3
    feats=body_features(va)
    sem=classify(w,feats,slots)
    # ring4
    dcs=calltargets.get(va,[])
    vts=set(s[1] for s in slots if s[1])
    installs=[]
    for vt in vts:
        for site,dest in instpat2.get(vt,[]):
            installs.append((site,dest,vt))
    r1 = aligned and not firstbad and (has_vt or feats['nins']>=2)
    r2 = bool(cnames)
    r3 = sem in ('scalar_deleting_dtor','container_scalar_deleting_dtor') or (feats['nins']>=2 and bool(feats['call_targets']))
    r4 = bool(dcs) or bool(installs)
    results.append({'ea':ea,'name':w['name'],'oldgrade':w['oldgrade'],'missing':w['missing'],
                    'aligned':aligned,'firstbad':firstbad,'pre':pre,
                    'slots':slots,'cnames':cnames,'feats':{k:v for k,v in feats.items() if k!='vptr_writes'},
                    'vptr_writes':feats['vptr_writes'],'sem':sem,
                    'direct_calls':len(dcs),'direct_call_sites':dcs[:8],
                    'installs':installs[:8],
                    'r1':r1,'r2':r2,'r3':r3,'r4':r4})

# --- DETECTION POWER BASELINE: 150 random 16B-aligned .text starts, run same predicate ---
random.seed(20261118)
tname2,tva2,tvs2,tptr2,trs2=TEXT
lo=tva2; hi=tva2+tvs2
base_pass=0; base_tried=0; base_examples=[]
for _ in range(1500):
    va=(lo+random.randrange(0, hi-lo-0x800)) & ~0xf
    if va in eset: continue
    base_tried+=1
    # ring1
    aligned=True; fb=rd(va,1)[0] if rd(va,1) else 0; firstbad=fb in (0xE8,0xE9,0xEB)
    sl=[]
    for sa in range(va-4*250, va+4, 4):
        col,cname=rtti_at_vt(sa)
        if col is not None and sa+4*((va-sa)//4)==va:
            sl.append((sa,sa,(va-sa)//4,col,cname)); break
    has_vt=bool(sl)
    feats=body_features(va, maxbytes=400)
    fw={'va':va,'name':'RANDOM','oldgrade':'','missing':'','aligned':True,'firstbad':firstbad,'pre':rd(va-2,2).hex(),
        'slots':sl,'cnames':[s[4] for s in sl if s[4]],'feats':{k:v for k,v in feats.items() if k!='vptr_writes'},
        'vptr_writes':feats['vptr_writes'],'sem':classify({'name':'RANDOM'},feats,sl),
        'direct_calls':len(calltargets.get(va,[])),'direct_call_sites':calltargets.get(va,[])[:8],
        'installs':[(s,d,vt) for vt in set(x[1] for x in sl if x[1]) for s,d in instpat2.get(vt,[])][:8]}
    r1=aligned and not firstbad and (has_vt or feats['nins']>=2)
    r2=has_vt and bool(fw['cnames'])
    r3=fw['sem'] in ('scalar_deleting_dtor','container_scalar_deleting_dtor') or (feats['nins']>=2 and bool(feats['call_targets']))
    r4=bool(calltargets.get(va)) or bool(fw['installs'])
    fw.update({'r1':r1,'r2':r2,'r3':r3,'r4':r4})
    if r1 and r2 and r3 and r4:
        base_pass+=1
        if len(base_examples)<10: base_examples.append(va)
    if base_tried>=150: break

# --- assign grades ---
def grade(r):
    n=sum([r['r1'],r['r2'],r['r3'],r['r4']])
    if n==4: return '[已证]'
    if n==3: return '[静态推断]'
    return '[未证]'
for r in results: r['grade']=grade(r)
counts=collections.Counter(r['grade'] for r in results)
baseline={'tried':base_tried,'pass':base_pass,'rate':base_pass/max(base_tried,1),'examples':base_examples}

out={'working_set':len(W),'counts':dict(counts),'baseline':baseline,'results':results}
fn=BASE+r'\S13_K8\EVIDENCE\analysis_full.json'
open(fn,'w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=1))
print('working_set',len(W),'counts',dict(counts))
print('BASELINE tried',base_tried,'pass',base_pass,'rate %.4f%%'%(100*base_pass/max(base_tried,1)))
# audit18 grades
a18=set('0075E510 0065BED0 0040BBC0 0040BC10 0040F8A0 0040F8F0 0040FE70 0040FEC0 0046B8C0 0046B910 0048AFD0 0048B020 0054EB50 0054EBA0 0062B330 0062B380 0065C1B0 0065C200'.split())
print('AUDIT18:')
for r in results:
    if r['ea'] in a18:
        print(' ',r['ea'],r['grade'],'r1-4',r['r1'],r['r2'],r['r3'],r['r4'],'sem',r['sem'],'cname',r['cnames'][:1],'dc',r['direct_calls'],'inst',len(r['installs']))
print('wrote',fn)
