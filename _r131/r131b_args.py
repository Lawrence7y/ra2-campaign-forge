#!/usr/bin/env python3
# R131 r131b: exact stack model of wrapper 0x6bedb0 (ret 0xc => 3 stack params),
# read the GUID at 0x817bc0, resolve the two IAT slots, and count ALL call sites of
# CoCreateInstance / OleRun in .text (e8 rel32 byte scan + capstone cross-check).
import json, struct, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131b_args.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()

def raw(va,n):
    for nm,(lo,hi,s) in secs.items():
        if lo<=va<hi:
            o=va-(base+s.VirtualAddress); r=s.SizeOfRawData; d=s.get_data()
            if o<0 or o+n>min(r,len(d)): return None
            return d[o:o+n]
    return None

R={}
# 1) GUID at 0x817bc0
g=raw(0x817bc0,16)
R['guid_0x817bc0']={'hex':g.hex() if g else None}
if g:
    d1,d2,d3=struct.unpack('<IHH',g[:8])
    R['guid_0x817bc0'].update({'Data1':'%08X'%d1,'Data2':'%04X'%d2,'Data3':'%04X'%d3,
        'Data4':'-'.join('%02X'%b for b in g[8:]),
        'str':'{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,g[8:10].hex().upper(),g[10:].hex().upper())})
    R['guid_0x817bc0']['iid_iunknown'] = g==bytes.fromhex('0000000000000000C000000000000046')
    R['guid_0x817bc0']['iid_iclassfactory'] = g==bytes.fromhex('0100000000000000C000000000000046')
    R['guid_0x817bc0']['section']=[nm for nm,(lo,hi,s) in secs.items() if lo<=0x817bc0<hi]

# 2) resolve IAT slots by reading the import directory (bytes -> name)
pe2=pefile.PE(EXE)
imp={}
for e in getattr(pe2,'DIRECTORY_ENTRY_IMPORT',[]):
    for i in e.imports:
        if i.address: imp[i.address]=(e.dll.decode(errors='replace'), (i.name.decode() if i.name else '#%d'%i.ordinal))
R['iat']={hex(k):v for k,v in imp.items() if k in (0x7e15fc,0x7e1600,0x7e15f8,0x7e1604,0x7e1370,0x7e1384)}

# 3) every .text reference to these IAT slots: `ff 15 <abs32>` (call) / `ff 25` (jmp).
# SELF-ERROR S-207 (kept): the first version tested data[i-2] against (0x15,0x25,...) -- but
# for the form ff 15 <imm32> the byte at i-2 is 0xff and the 0x15 is at i-1. Testing the wrong
# index made every slot report ZERO references (0x7e15fc has 22). A "0 references" result on a
# slot the disassembly plainly calls is the signal that the byte-window is off by one.
def absrefs(slot):
    pat = struct.pack('<I', slot)
    hits = []
    i = data.find(pat)
    while i >= 0:
        if i >= 2 and data[i - 2] == 0xff and data[i - 1] in (0x15, 0x25, 0x35, 0x05):
            hits.append({'va': tlo + i - 2, 'form': '%02x%02x' % (data[i - 2], data[i - 1])})
        i = data.find(pat, i + 1)
    return hits
R['refs']={hex(s):absrefs(s) for s in (0x7e15fc,0x7e1600)}
R['refs_counts']={k:len(v) for k,v in R['refs'].items()}

# 4) capstone cross-check of the same refs (bounded: only windows around raw hits, detail=False)
md=Cs(CS_ARCH_X86, CS_MODE_32)
def dis_at(va,n=4):
    o=va-tlo; out=[]
    for i in md.disasm(data[o:o+40], va):
        out.append({'va':hex(i.address),'mn':i.mnemonic,'op':i.op_str,'bytes':i.bytes.hex()})
        if len(out)>=n: break
    return out
R['capstone_check']={hex(h['va']):dis_at(h['va']) for k in R['refs'] for h in R['refs'][k]}

# 5) stack model: walk the wrapper linearly tracking esp delta, record params at ret
WRAP=0x6bedb0
md.detail=True
def stack_model():
    o=WRAP-tlo; esp=0; depth=0; rows=[]; rets=[]; branches=[]
    body={}
    for i in md.disasm(data[o:o+0x100], WRAP):
        body[i.address]=i
    # linear walk following fallthrough; keep it simple: walk address order, track esp
    for va in sorted(body):
        i=body[va]; mn=i.mnemonic; ops=i.op_str
        d=0; ev=None
        if mn=='push': d=4
        elif mn=='pop': d=-4
        elif mn=='ret':
            ev={'ret':ops,'esp_before':esp}
            rets.append(ev)
            n=int(ops,16) if ops.startswith('0x') else 0
            d=4+n
        elif mn=='call': d=0
        elif mn in ('mov','lea'):
            # mov eax,[esp+N]  -> record param index
            m=re.match(r'^(\w+), dword ptr \[esp \+ (0x[0-9a-f]+)\]$', ops)
            if m: rows.append({'va':hex(va),'kind':'load','dst':m.group(1),'esp_off':int(m.group(2),16),'argidx':(int(m.group(2),16)-4)//4 if int(m.group(2),16)>=4 else None})
            m2=re.match(r'^(\w+), \[esp \+ (0x[0-9a-f]+)\]$', ops)
            if m2: rows.append({'va':hex(va),'kind':'load','dst':m2.group(1),'esp_off':int(m2.group(2),16),'argidx':(int(m2.group(2),16)-4)//4})
        esp+=d
        rows.append({'va':hex(va),'mn':mn,'op':ops,'esp_after':esp})
    return rows,rets
rows,rets=stack_model()
R['stack_model']=rows
R['rets']=rets
print('GUID@0x817bc0:',R['guid_0x817bc0'])
print('IAT:',R['iat'])
print('ref counts:',R['refs_counts'])
for k,h in R['refs'].items():
    print(k,'->',[('0x%x'%x['va'],x['form']) for x in h])
print('rets:',rets)
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
