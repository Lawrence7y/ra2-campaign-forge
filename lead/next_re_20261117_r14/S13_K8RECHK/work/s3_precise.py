# -*- coding: utf-8 -*-
"""S13-K8RECHK step3: PRECISE function map + all mov[mem],imm writes.
Function starts = initterm ctors U all call/push .text targets U 16B-aligned prologues.
For each of 18 vts: all mov [mem],imm writes -> containing function -> ctor/dtor/other."""
import sys, struct, json, bisect, re
import pefile, capstone
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DATA=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append(dict(name=nm,va=IMG+s.VirtualAddress,raw=s.PointerToRawData,rs=s.SizeOfRawData,
        end=IMG+s.VirtualAddress+s.Misc_VirtualSize))
def sec_of(va):
    for s in SECS:
        if s['va']<=va<s['end']: return s
def va2fo(va):
    s=sec_of(va); return None if s is None else s['raw']+(va-s['va'])
def u32va(va):
    fo=va2fo(va); return struct.unpack('<I',DATA[fo:fo+4])[0] if fo is not None else None
def rdva(va,n):
    s=sec_of(va); return b'' if s is None else DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+n]
TEXT=[s for s in SECS if s['name']=='.text'][0]; TA=TEXT['va']; TE=TA+TEXT['rs']
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
INSNS=list(MD.disasm(DATA[TEXT['raw']:TEXT['raw']+TEXT['rs']],TA))

# initterm ctors (3944 @ 0x812004)
CTORS=set(); v=0x812004
for _ in range(3944):
    x=u32va(v)
    if x and TA<=x<TE: CTORS.add(x)
    v+=4
# atexit dtors via push;call 0x7C978A with WIDE window (12)
ATEXIT=0x7C978A; OPDEL=0x7C8B3D; atexit_reg={}
for k,ins in enumerate(INSNS):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try: t=int(ins.op_str,16)
        except: continue
        if t==ATEXIT:
            for j in range(max(0,k-14),k):
                p=INSNS[j]
                if p.mnemonic=='push':
                    try: pv=int(p.op_str,16)
                    except: continue
                    if TA<=pv<TE:
                        atexit_reg.setdefault(pv,[]).append((hex(p.address),hex(ins.address)))
                        break
ATEXIT_DTOR=set(atexit_reg)
# function starts: initterm U atexit dtors U all call/push .text targets U 16B prologues
FS=set(CTORS)|set(ATEXIT_DTOR)
for ins in INSNS:
    if ins.mnemonic in ('call','push') and ins.op_str.startswith('0x'):
        try: t=int(ins.op_str,16)
        except: continue
        if TA<=t<TE: FS.add(t)
for va in range(TA,TE,16):
    b=rdva(va,2)
    if b[:1] in (b'\x55',b'\x53',b'\x56',b'\x57',b'\x6a',b'\x68',b'\x81',b'\x83',b'\xa1',b'\xa3',b'\x8b') or b==b'\x8b\xff':
        FS.add(va)
FS=sorted(FS)
def func_of(w):
    k=bisect.bisect_right(FS,w)-1
    return FS[k] if k>=0 else None
def func_next(f):
    k=bisect.bisect_right(FS,f); return FS[k] if k<len(FS) else f+64

# ALL mov [mem],imm at instruction boundaries (capstone op_str e.g. 'dword ptr [0x87f5d8], 0x7e17ec'
#   or 'dword ptr [eax+4], 0x7f6b30')
MEMRE=re.compile(r'\[([^\]]+)\]')
ALLW={}
for ins in INSNS:
    if ins.mnemonic!='mov' or 'ptr [' not in ins.op_str or ',' not in ins.op_str: continue
    imm=ins.op_str.rsplit(',',1)[1].strip()
    if not imm.startswith('0x'): continue
    try: immi=int(imm,16)
    except: continue
    m=MEMRE.search(ins.op_str)
    mem=m.group(1) if m else '?'
    ALLW.setdefault(immi,[]).append((ins.address,mem,ins.bytes.hex()))

ROWS=[
 ('0075E510','WarheadTypeClass',0x007F6B30,8,'plain'),
 ('0065BED0','RadSiteClass',0x007F0810,8,'plain'),
 ('0040BBC0','VectorClass<BombClass*>',0x007E17EC,0,'base'),
 ('0040BC10','DynamicVectorClass<BombClass*>',0x007E17CC,0,'derived'),
 ('0040F8A0','VectorClass<WarheadTypeClass*>',0x007E1EA4,0,'base'),
 ('0040F8F0','DynamicVectorClass<WarheadTypeClass*>',0x007E1E84,0,'derived'),
 ('0040FE70','VectorClass<WeaponTypeClass*>',0x007E1EF4,0,'base'),
 ('0040FEC0','DynamicVectorClass<WeaponTypeClass*>',0x007E1ED4,0,'derived'),
 ('0046B8C0','VectorClass<BulletClass*>',0x007E4698,0,'base'),
 ('0046B910','DynamicVectorClass<BulletClass*>',0x007E4678,0,'derived'),
 ('0048AFD0','VectorClass<DamageGroup*>',0x007E5144,0,'base'),
 ('0048B020','DynamicVectorClass<DamageGroup*>',0x007E5170,0,'derived'),
 ('0054EB50','VectorClass<KamikazeControl*>',0x007ECE9C,0,'base'),
 ('0054EBA0','DynamicVectorClass<KamikazeControl*>',0x007ECE7C,0,'derived'),
 ('0062B330','VectorClass<ParasiteClass*>',0x007EF844,0,'base'),
 ('0062B380','DynamicVectorClass<ParasiteClass*>',0x007EF824,0,'derived'),
 ('0065C1B0','VectorClass<RadSiteClass*>',0x007F07C4,0,'base'),
 ('0065C200','DynamicVectorClass<RadSiteClass*>',0x007F07A4,0,'derived'),
]
rep=[]
for ea,nm,vt,slot,kind in ROWS:
    ws=ALLW.get(vt,[])
    wout=[]
    for site,mem,bb in ws:
        f=func_of(site)
        cls=[]
        if f in CTORS: cls.append('CTOR')
        if f in ATEXIT_DTOR: cls.append('ATEXIT_DTOR')
        # scan function for atexit reg (push dtor;call atexit) and opdel
        fn=func_next(f) if f else site+1
        reg_here=[]; opdel=0; areg=0
        if f:
            for ins in MD.disasm(rdva(f,min(fn-f,200)),f):
                if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
                    try:
                        t=int(ins.op_str,16)
                        if t==OPDEL: opdel+=1
                        if t==ATEXIT: areg+=1
                    except: pass
        wout.append(dict(site=hex(site),mem=mem,bytes=bb,func=hex(f) if f else None,
                         cls='+'.join(cls) or 'OTHER',atexit_reg=atexit_reg.get(f,[]),
                         opdel=opdel,atexit_calls=areg))
    rep.append(dict(entry=ea,name=nm,vt=hex(vt),slot=slot,kind=kind,writes=wout,n=len(wout)))
json.dump({'ctors':len(CTORS),'atexit_dtors':len(ATEXIT_DTOR),
           'atexit_reg':{hex(k):v for k,v in atexit_reg.items()},'rep':rep},
    open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\s3_report.json','w'),indent=1)
for r in rep:
    print('\n== %s %s kind=%s vt=%s writes=%d'%(r['entry'],r['name'],r['kind'],r['vt'],r['n']))
    for w in r['writes']:
        print('   site=%s mem=[%s] func=%s cls=%s reg=%s opdel=%d atexitcall=%d'%(
          w['site'],w['mem'],w['func'],w['cls'],w['atexit_reg'],w['opdel'],w['atexit_calls']))
print('\nDONE step3')
