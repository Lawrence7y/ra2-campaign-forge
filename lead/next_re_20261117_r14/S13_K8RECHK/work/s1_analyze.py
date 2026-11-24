# -*- coding: utf-8 -*-
"""S13-K8RECHK step1: full ㉓ analysis.
For each of the 18 entries: RTTI walk (COL/TD/name), all C7 05 <global>,<vt> writes
at instruction boundaries, containing function, ctor-vs-atexit-dtor classification.
Writes only under S13_K8RECHK\work and \EVIDENCE."""
import sys, struct, json
import pefile, capstone
sys.stdout.reconfigure(encoding='utf-8')

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DATA = open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IMG = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append(dict(name=nm, va=IMG+s.VirtualAddress, vs=s.Misc_VirtualSize,
                     raw=s.PointerToRawData, rs=s.SizeOfRawData,
                     end=IMG+s.VirtualAddress+s.Misc_VirtualSize))
def sec_of(va):
    for s in SECS:
        if s['va'] <= va < s['end']: return s
    return None
def va2fo(va):
    s=sec_of(va); return None if s is None else s['raw']+(va-s['va'])
def u32va(va):
    fo=va2fo(va); return None if fo is None else struct.unpack('<I',DATA[fo:fo+4])[0]
def rdva(va,n):
    s=sec_of(va)
    if s is None: return b''
    fo=s['raw']+(va-s['va']); return DATA[fo:fo+n]
def cstr(va,maxn=200):
    b=rdva(va,maxn); z=b.find(b'\x00'); return (b[:z] if z>=0 else b).decode('latin1','replace')

TEXT=[s for s in SECS if s['name']=='.text'][0]
TA, TE = TEXT['va'], TEXT['va']+TEXT['rs']
TB = DATA[TEXT['raw']:TEXT['raw']+TEXT['rs']]
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
INSNS=list(MD.disasm(TB,TA))
addr2ins={i.address:i for i in INSNS}

# ---------- atexit dtors ----------
ATEXIT=0x7C978A
atexit_pairs=[]
for k,ins in enumerate(INSNS):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try: tgt=int(ins.op_str,16)
        except: continue
        if tgt==ATEXIT:
            for j in range(max(0,k-6),k):
                p=INSNS[j]
                if p.mnemonic=='push':
                    try: pv=int(p.op_str,16)
                    except: continue
                    if TA<=pv<TE:
                        atexit_pairs.append((ins.address,p.address,pv))
ATEXIT_DTOR={pv for _,_,pv in atexit_pairs}
# map dtor function -> the atexit call site that registers it
atexit_reg={}
for call_a,push_a,pv in atexit_pairs:
    atexit_reg.setdefault(pv,[]).append((hex(push_a),hex(call_a)))

# ---------- ctor set from .data initterm table ----------
# table detected at 0x812004 with 3944 entries; find all runs, take the big one
CTORS=set()
initterm_tables=[]
for sec in SECS:
    if sec['name'] not in ('.data','.rdata'): continue
    n=sec['rs']//4; run=[]
    for i in range(n+1):
        fo=sec['raw']+i*4
        v=struct.unpack('<I',DATA[fo:fo+4])[0] if fo+4<=len(DATA) else 0
        if TA<=v<TE: run.append((sec['va']+i*4,v))
        else:
            if len(run)>=2: initterm_tables.append(run)
            run=[]
for run in initterm_tables:
    if len(run)>=100:  # the global ctor array
        for _,v in run: CTORS.add(v)
print('CTORS',len(CTORS),'big tables',[ (hex(r[0][0]),len(r)) for r in initterm_tables if len(r)>=100])

# ---------- function-start set: union of ctors, atexit dtors, 16B-aligned prologues ----------
FSTART=set(CTORS)|set(ATEXIT_DTOR)
# add 16B aligned .text addresses whose bytes begin with common prologue
for va in range(TA,TE,16):
    b=rdva(va,3)
    if len(b)>=2 and (b[:2] in (b'\x55\x8b', b'\x53\x8b', b'\x51\x8b', b'\x83\xec', b'\x81\xec', b'\x6a', b'\x68', b'\x8b\xff', b'\x55\x8d', b'\x53\x57', b'\x56\x57', b'\x8b\x44', b'\x8b\x4c')):
        FSTART.add(va)
# also all 18 entries and known funcs from card
extra=[0x004393F0,0x0046B5C0,0x0046C890,0x0062AF70,0x007730F0,0x438550,0x438590]
for x in extra: FSTART.add(x)
FS=sorted(FSTART)
import bisect
def containing_func(w):
    k=bisect.bisect_right(FS,w)-1
    return FS[k] if k>=0 else None

# ---------- find all `mov dword ptr [abs], imm32` (C7 05) writes to each vt ----------
# capstone op_str for C7 05 abs,imm looks like: mov dword ptr [0x89C668], 0x7E17CC
import re
WRITES={}  # vt -> list of (site, global, insbytes)
ABS_RE=re.compile(r'\[(0x[0-9A-Fa-f]+)\]')
for ins in INSNS:
    if ins.mnemonic!='mov': continue
    ops=ins.op_str
    if 'dword ptr [' not in ops: continue
    m=ABS_RE.search(ops)
    if not m: continue
    g=int(m.group(1),16)
    # last operand imm
    if ',' not in ops: continue
    immstr=ops.rsplit(',',1)[1].strip()
    if not immstr.startswith('0x'): continue
    try: imm=int(immstr,16)
    except: continue
    WRITES.setdefault(imm,[]).append((ins.address,g,ins.bytes.hex()))

# ---------- RTTI walk ----------
def rtti(vt):
    col=u32va(vt-4)
    out={'vt':vt,'col':col,'td':None,'name':None,'ok':False}
    if col is None or sec_of(col) is None: return out
    ptd=u32va(col+0xC)
    out['td']=ptd
    if ptd is None or sec_of(ptd) is None: return out
    nm=cstr(ptd+8)
    out['name']=nm
    out['ok']=nm.startswith('.?A') or nm.startswith('.?AU') or nm.startswith('.?AV')
    return out

# ---------- 18 entries ----------
ROWS=[
 ('0075E510','WarheadTypeClass',0x007F6B30,8),
 ('0065BED0','RadSiteClass',0x007F0810,8),
 ('0040BBC0','VectorClass<BombClass*>',0x007E17EC,0),
 ('0040BC10','DynamicVectorClass<BombClass*>',0x007E17CC,0),
 ('0040F8A0','VectorClass<WarheadTypeClass*>',0x007E1EA4,0),
 ('0040F8F0','DynamicVectorClass<WarheadTypeClass*>',0x007E1E84,0),
 ('0040FE70','VectorClass<WeaponTypeClass*>',0x007E1EF4,0),
 ('0040FEC0','DynamicVectorClass<WeaponTypeClass*>',0x007E1ED4,0),
 ('0046B8C0','VectorClass<BulletClass*>',0x007E4698,0),
 ('0046B910','DynamicVectorClass<BulletClass*>',0x007E4678,0),
 ('0048AFD0','VectorClass<DamageGroup*>',0x007E5144,0),
 ('0048B020','DynamicVectorClass<DamageGroup*>',0x007E5170,0),
 ('0054EB50','VectorClass<KamikazeControl*>',0x007ECE9C,0),
 ('0054EBA0','DynamicVectorClass<KamikazeControl*>',0x007ECE7C,0),
 ('0062B330','VectorClass<ParasiteClass*>',0x007EF844,0),
 ('0062B380','DynamicVectorClass<ParasiteClass*>',0x007EF824,0),
 ('0065C1B0','VectorClass<RadSiteClass*>',0x007F07C4,0),
 ('0065C200','DynamicVectorClass<RadSiteClass*>',0x007F07A4,0),
]

def classify(func):
    if func is None: return 'NOFUNC'
    tags=[]
    if func in CTORS: tags.append('CTOR(initterm)')
    if func in ATEXIT_DTOR: tags.append('ATEXIT_DTOR')
    return '+'.join(tags) if tags else 'OTHER'

report=[]
for ea,nm,vt,slot in ROWS:
    ea_i=int(ea,16)
    r=rtti(vt)
    # verify slot value == entry
    slotval=u32va(vt+slot*4)
    ws=WRITES.get(vt,[])
    det=[]
    for site,g,b in ws:
        f=containing_func(site)
        det.append({'site':hex(site),'global':hex(g),'func':hex(f) if f else None,
                    'cls':classify(f),'bytes':b,
                    'atexit_reg':atexit_reg.get(f,[])})
    report.append({'entry':ea,'name':nm,'vt':hex(vt),'slot':slot,
                   'slotval':hex(slotval) if slotval is not None else None,
                   'slot_ok':(slotval==ea_i),
                   'col':hex(r['col']) if r['col'] else None,
                   'td':hex(r['td']) if r['td'] else None,
                   'rtti_name':r['name'],'rtti_ok':r['ok'],
                   'writes':det,'n_writes':len(ws)})

json.dump({'atexit_dtors':[hex(x) for x in sorted(ATEXIT_DTOR)],
           'atexit_reg':{hex(k):v for k,v in atexit_reg.items()},
           'ctors_n':len(CTORS),'report':report},
          open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\s1_report.json','w'),indent=1)

# print summary
for r in report:
    print('\n== %s %s vt=%s slot=%d slot_ok=%s rtti=%s'%(r['entry'],r['name'],r['vt'],r['slot'],r['slot_ok'],r['rtti_name']))
    print('   col=%s td=%s writes=%d'%(r['col'],r['td'],r['n_writes']))
    for w in r['writes']:
        print('     site=%s global=%s func=%s cls=%s atexitreg=%s bytes=%s'%(
            w['site'],w['global'],w['func'],w['cls'],w['atexit_reg'],w['bytes']))
print('\nDONE step1')
