# -*- coding: utf-8 -*-
"""S13-K8RECHK step0: PE map + atexit scanner + ctor-table discovery + vptr write sites.
Read-only on gamemd.exe. Writes only under S13_K8RECHK\work."""
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
def fo2va(fo):
    for s in SECS:
        if s['raw'] <= fo < s['raw']+s['rs']: return s['va']+(fo-s['raw'])
    return None
def va2fo(va):
    s=sec_of(va)
    return None if s is None else s['raw']+(va-s['va'])
def u32va(va):
    fo=va2fo(va)
    return None if fo is None else struct.unpack('<I',DATA[fo:fo+4])[0]
def u32fo(fo): return struct.unpack('<I',DATA[fo:fo+4])[0]

TEXT=[s for s in SECS if s['name']=='.text'][0]
TA, TE = TEXT['va'], TEXT['va']+TEXT['rs']
TB = DATA[TEXT['raw']:TEXT['raw']+TEXT['rs']]

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
MD.skipdata = True

# ---- linear sweep of .text at instruction boundaries ----
INSNS=[]
for ins in MD.disasm(TB, TA):
    INSNS.append(ins)
print('insns', len(INSNS))
idx_by_addr = {i.address:k for k,i in enumerate(INSNS)}

# ---- 1. atexit registration: E8 rel32 -> 0x7C978A, preceding push imm32 ----
ATEXIT_TARGET=0x7C978A
atexit_calls=[]
for k,ins in enumerate(INSNS):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try: tgt=int(ins.op_str,16)
        except: continue
        if tgt==ATEXIT_TARGET:
            # look back up to 6 insns for push imm32
            pushing=[]
            for j in range(max(0,k-6),k):
                p=INSNS[j]
                if p.mnemonic=='push':
                    try: pv=int(p.op_str,16)
                    except: continue
                    if sec_of(pv) and sec_of(pv)['name']=='.text':
                        pushing.append((p.address,pv))
            atexit_calls.append((ins.address, pushing))
atexit_dtors=set(pv for _,pl in atexit_calls for _,pv in pl)
print('atexit call sites', len(atexit_calls), 'distinct dtor targets', len(atexit_dtors))
# save
json.dump({'calls':[[hex(a),[[hex(x),hex(y)] for x,y in pl]] for a,pl in atexit_calls],
           'dtors':[hex(x) for x in sorted(atexit_dtors)]},
          open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\atexit.json','w'),indent=1)

# ---- 2. ctor sets: scan .data/.rdata aligned dword arrays containing .text VAs ----
# find file offset 0x41270c -> VA and neighboring array
cfo=0x41270c
print('ctor-ref fileoff 0x%x -> VA %s'%(cfo, hex(fo2va(cfo)) or 'NA'))
cva=fo2va(cfo)
s=sec_of(cva)
print('  section', s['name'] if s else None)
# dump neighborhood as dwords
base=cva-16
vals=[]
for o in range(0,64,4):
    v=u32va(base+o)
    vals.append((hex(base+o), hex(v) if v is not None else None))
print('  neighborhood:')
for a,v in vals: print('   ',a,v)

# generic: find all 4-byte occurrences of any .text VA in .data/.rdata aligned arrays,
# cluster consecutive ones into 'pointer tables', record which table contains 0x438550
def build_tables():
    tables={}
    for sec in SECS:
        if sec['name'] not in ('.data','.rdata'): continue
        n=sec['rs']//4
        run=[]
        for i in range(n):
            fo=sec['raw']+i*4
            v=u32fo(fo)
            va=sec['va']+i*4
            if v is not None and TA<=v<TE:
                run.append((va,v))
            else:
                if len(run)>=2:
                    tables[run[0][0]]=run
                run=[]
        if len(run)>=2: tables[run[0][0]]=run
    return tables
tables=build_tables()
print('pointer tables (>=2 consecutive .text VAs):',len(tables))
# which table has 0x438550
for st,run in tables.items():
    if any(v==0x438550 for _,v in run):
        print('  0x438550 in table @',hex(st),'len',len(run),'range',hex(run[0][1]),hex(run[-1][1]))
json.dump({hex(st):[[hex(a),hex(v)] for a,v in run] for st,run in tables.items()},
          open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\ptr_tables.json','w'),indent=1)
print('DONE step0')
