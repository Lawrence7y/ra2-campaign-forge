# -*- coding: utf-8 -*-
"""S13-K8RECHK step2: correct ctor set (only 3944-entry _initterm array @0x812004),
and dump disassembly of each write-site's containing function for manual ctor/dtor judgment."""
import sys, struct, json, bisect, re
import pefile, capstone
sys.stdout.reconfigure(encoding='utf-8')

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DATA = open(EXE,'rb').read()
pe=pefile.PE(EXE,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
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
    fo=va2fo(va); return struct.unpack('<I',DATA[fo:fo+4])[0] if fo else None
def rdva(va,n):
    s=sec_of(va)
    return b'' if s is None else DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+n]
TEXT=[s for s in SECS if s['name']=='.text'][0]
TA=TEXT['va']; TE=TA+TEXT['rs']
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
INSNS=list(MD.disasm(DATA[TEXT['raw']:TEXT['raw']+TEXT['rs']],TA))

# ---- _initterm ctor table: ONLY the 3944-entry run starting 0x812004 ----
CTORS=set()
init_lo=0x812004; init_hi=init_lo+3944*4
va=init_lo
while va<init_hi:
    v=u32va(va)
    if v is not None and TA<=v<TE: CTORS.add(v)
    va+=4
print('_initterm CTORS',len(CTORS))

# atexit dtors
ATEXIT=0x7C978A
atexit_reg={}
for k,ins in enumerate(INSNS):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try: t=int(ins.op_str,16)
        except: continue
        if t==ATEXIT:
            for j in range(max(0,k-6),k):
                p=INSNS[j]
                if p.mnemonic=='push':
                    try: pv=int(p.op_str,16)
                    except: continue
                    if TA<=pv<TE:
                        atexit_reg.setdefault(pv,[]).append((hex(p.address),hex(ins.address)))
ATEXIT_DTOR=set(atexit_reg)

# function starts: initterm ctors + atexit dtors + 16B aligned prologues + known funcs
FS=set(CTORS)|set(ATEXIT_DTOR)
for va in range(TA,TE,16):
    b=rdva(va,2)
    if b[:1] in (b'\x55',b'\x53',b'\x56',b'\x57',b'\x6a',b'\x68',b'\x81',b'\x83') or b==b'\x8b\xff':
        FS.add(va)
for x in [0x004393F0,0x0046B5C0,0x0046C890,0x0062AF70,0x007730F0]: FS.add(x)
FS=sorted(FS)
def containing(w):
    k=bisect.bisect_right(FS,w)-1
    return FS[k] if k>=0 else None

# vptr writes (C7 05 abs,imm) -- from step1 report, recompute
ABS=re.compile(r'\[(0x[0-9A-Fa-f]+)\]')
WRITES={}
for ins in INSNS:
    if ins.mnemonic!='mov' or 'dword ptr [' not in ins.op_str: continue
    m=ABS.search(ins.op_str)
    if not m or ',' not in ins.op_str: continue
    imm=ins.op_str.rsplit(',',1)[1].strip()
    if not imm.startswith('0x'): continue
    try: immi=int(imm,16)
    except: continue
    WRITES.setdefault(immi,[]).append((ins.address,int(m.group(1),16)))

ROWS=[
 ('0075E510',0x007F6B30,8),('0065BED0',0x007F0810,8),
 ('0040BBC0',0x007E17EC,0),('0040BC10',0x007E17CC,0),
 ('0040F8A0',0x007E1EA4,0),('0040F8F0',0x007E1E84,0),
 ('0040FE70',0x007E1EF4,0),('0040FEC0',0x007E1ED4,0),
 ('0046B8C0',0x007E4698,0),('0046B910',0x007E4678,0),
 ('0048AFD0',0x007E5144,0),('0048B020',0x007E5170,0),
 ('0054EB50',0x007ECE9C,0),('0054EBA0',0x007ECE7C,0),
 ('0062B330',0x007EF844,0),('0062B380',0x007EF824,0),
 ('0065C1B0',0x007F07C4,0),('0065C200',0x007F07A4,0),
]
OPDEL=0x7C8B3D

def disasm_range(va,n=120):
    out=[]
    for ins in MD.disasm(rdva(va,n),va):
        extra=''
        if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
            try:
                t=int(ins.op_str,16)
                if t in CTORS: extra+=' [->CTOR]'
                if t in ATEXIT_DTOR: extra+=' [->ATEXIT_DTOR]'
                if t==OPDEL: extra+=' [->op_delete]'
                if t==ATEXIT: extra+=' [->ATEXIT]'
            except: pass
        if ins.address in CTORS: extra+=' <FUNC_IS_CTOR>'
        if ins.address in ATEXIT_DTOR: extra+=' <FUNC_IS_ATEXIT_DTOR>'
        out.append('%08X  %-20s %-8s %s%s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,extra))
    return out

report=[]
for ea,vt,slot in ROWS:
    ws=WRITES.get(vt,[])
    entry={'entry':ea,'vt':hex(vt),'writes':[]}
    for site,g in ws:
        f=containing(site)
        # detect function extent: next FSTART after f
        nxt=None
        if f is not None:
            k=bisect.bisect_right(FS,f)
            if k<len(FS): nxt=FS[k]
        flen=(nxt-f) if (f is not None and nxt) else 96
        calls_opdel=0; calls_atexit=0
        if f is not None:
            for ins in MD.disasm(rdva(f,min(flen,256)),f):
                if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
                    try:
                        t=int(ins.op_str,16)
                        if t==OPDEL: calls_opdel+=1
                        if t==ATEXIT: calls_atexit+=1
                    except: pass
        entry['writes'].append({'site':hex(site),'global':hex(g),'func':hex(f) if f else None,
            'func_in_initterm': f in CTORS if f else False,
            'func_is_atexit_dtor': f in ATEXIT_DTOR if f else False,
            'atexit_reg_of_func':atexit_reg.get(f,[]),
            'func_len':flen,'calls_op_delete':calls_opdel,'calls_atexit':calls_atexit,
            'disasm':disasm_range(f,min(flen,128)) if f else []})
    report.append(entry)

json.dump(report,open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\s2_report.json','w'),indent=1)

for e in report:
    print('\n############ entry %s vt=%s writes=%d'%(e['entry'],e['vt'],len(e['writes'])))
    for w in e['writes']:
        print('  site=%s global=%s func=%s initterm=%s atexitdtor=%s reg=%s opdel=%d atexitcalls=%d flen=%d'%(
          w['site'],w['global'],w['func'],w['func_in_initterm'],w['func_is_atexit_dtor'],
          w['atexit_reg_of_func'],w['calls_op_delete'],w['calls_atexit'],w['func_len']))
        for ln in w['disasm'][:40]:
            print('    '+ln)
print('\nDONE step2')
