#!/usr/bin/env python3
"""Evidence gatherer for S19: IAT map, per-function import calls + string xrefs, range containment."""
import os, struct, re, csv, json
import pefile
from capstone import *
from capstone.x86 import *

ROOT = r'D:\Project\ra2-campaign-forge'
EXE = os.path.join(ROOT, r'ra2youli\gamemd.exe')
ATL = os.path.join(ROOT, r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
TGT = os.path.join(ROOT, r'lead\next_re_20261117_r14\S19-K2\TARGETS.tsv')
OUTJ = os.path.join(ROOT, r'lead\next_re_20261117_r14\S19-K2\work\s19_evidence.json')

pe = pefile.PE(EXE, fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE,'rb').read()

# --- IAT map: VA -> 'DLL!API' or 'DLL!#ordinal' ---
iat = {}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode('ascii','replace')
    for imp in entry.imports:
        va = imp.address
        if imp.name:
            iat[va] = f'{dll}!{imp.name.decode("ascii","replace")}'
        else:
            iat[va] = f'{dll}!#{imp.ordinal}'
# also delay imports
if hasattr(pe,'DIRECTORY_ENTRY_DELAY_IMPORT'):
    for entry in pe.DIRECTORY_ENTRY_DELAY_IMPORT:
        dll = entry.dll.decode('ascii','replace')
        for imp in entry.imports:
            va = imp.address
            if imp.name:
                iat[va] = f'{dll}!{imp.name.decode("ascii","replace")}'
            else:
                iat[va] = f'{dll}!#{imp.ordinal}'
print('IAT entries =',len(iat))
for k,v in sorted(iat.items()):
    if any(s in v.lower() for s in ('dsound','bink','acm','wave','mci','winmm','sound','audio')):
        print(f'  0x{k:X} -> {v}')

def sec_of(va):
    for s in pe.sections:
        a=IB+s.VirtualAddress
        if a<=va<a+s.Misc_VirtualSize:
            return s.Name.rstrip(b'\0').decode('ascii','replace')
    return '?'

def read_va(va,n):
    off=va-IB
    return data[off:off+n]

def cstr_at(va,maxn=128):
    b=read_va(va,maxn)
    z=b.find(b'\0')
    if z<0: z=maxn
    s=b[:z]
    # printable ascii
    if len(s)>=3 and all(32<=c<127 for c in s):
        return s.decode('ascii','replace')
    return None

# --- function ranges from atlas (for containment) ---
funcs=[]
with open(ATL,encoding='utf-8') as f:
    r=csv.DictReader(f,delimiter='\t')
    for row in r:
        funcs.append((int(row['entry'],16),int(row['size'])))
funcs.sort()
starts=[x[0] for x in funcs]
import bisect
def containing(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and funcs[i][0]<=va<funcs[i][0]+funcs[i][1]:
        return funcs[i][0]
    return None

# --- S19 targets ---
tgts=[]
with open(TGT,encoding='utf-8') as f:
    r=csv.DictReader(f,delimiter='\t')
    for row in r:
        tgts.append(row)

md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=True
results={}
for row in tgts:
    va=int(row['entry'],16); sz=int(row['atlas_size'])
    raw=read_va(va,sz)
    calls=set(); import_calls=[]; strops=[]; immrefs=[]
    for ins in md.disasm(raw,va):
        if ins.id==X86_INS_CALL:
            o=ins.op_str.strip()
            m=re.fullmatch(r'0x([0-9a-fA-F]+)',o)
            if m: calls.add(int(m.group(1),16))
            # call [abs] via FF 15
            m2=re.fullmatch(r'dword ptr \[0x([0-9a-fA-F]+)\]',o)
            if m2:
                iava=int(m2.group(1),16)
                if iava in iat:
                    import_calls.append([ins.address,iat[iava]])
        if ins.id==X86_INS_JMP:
            o=ins.op_str.strip()
            m2=re.fullmatch(r'dword ptr \[0x([0-9a-fA-F]+)\]',o)
            if m2:
                iava=int(m2.group(1),16)
                if iava in iat:
                    import_calls.append([ins.address,'JMP:'+iat[iava]])
        # string/pointer immediates: push imm32, mov reg,imm32
        if ins.id in (X86_INS_PUSH,X86_INS_MOV) and ins.operands:
            op=ins.operands[-1]
            if op.type==X86_OP_IMM:
                v=op.imm & 0xFFFFFFFF
                if IB<=v<IB+0xB00000:  # within image
                    s=cstr_at(v)
                    strops.append([ins.address,v,s])
    results[row['entry']]={
        'entry':row['entry'],'size':sz,'name':row['name'],'grade':row['grade'],
        'calls':sorted(calls),'import_calls':import_calls,
        'strops':strops,
    }
with open(OUTJ,'w',encoding='utf-8') as f:
    json.dump(results,f,indent=1)
print('wrote',OUTJ,'entries',len(results))
# quick summary: functions calling EVA QueueVoice 0x752700
print('--- callers of 0x752700 (EVA QueueVoice) in S19 ---')
for e,r in results.items():
    if 0x752700 in r['calls']:
        print(e,r['name'],'strops=',[x[2] for x in r['strops'] if x[2]])
