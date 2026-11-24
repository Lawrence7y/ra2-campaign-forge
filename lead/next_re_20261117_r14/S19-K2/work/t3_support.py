#!/usr/bin/env python3
"""T3 support: RTTI audio class names, static vtable init chains, plus naming candidate checks."""
import os,re,struct,csv,json
import pefile
from capstone import *
from capstone.x86 import *
ROOT=r'D:\Project\ra2-campaign-forge'; EXE=os.path.join(ROOT,r'ra2youli\gamemd.exe')
pe=pefile.PE(EXE,fast_load=False); IB=pe.OPTIONAL_HEADER.ImageBase; data=open(EXE,'rb').read()
def va2off(va): return va-IB
# --- RTTI: scan .rdata for type descriptor name '.?AV...@@' and demangle-ish ---
rdata=None
for s in pe.sections:
    if s.Name.rstrip(b'\0')==b'.rdata': rdata=s;break
rva0=rdata.VirtualAddress; rsize=rdata.Misc_VirtualSize
blob=data[va2off(IB+rva0):va2off(IB+rva0)+rsize]
audio_re=re.compile(rb'\.\?AV\??([A-Za-z0-9_@$?]+)@@')
found=[]
for m in audio_re.finditer(blob):
    name=m.group(1).decode('ascii','replace')
    if re.search(r'voc|audio|sound|music|theme|mixer|stream|eva|wave|bink|voice|snd',name,re.I):
        va=IB+rva0+m.start()
        found.append((va,name))
print('=== RTTI audio-related type descriptors ===')
for va,n in found: print(f'  0x{va:X} .?AV{n}@@')
# also template names VectorClass<VocClass*> etc
for m in re.finditer(rb'\.\?AV\?\$([A-Za-z0-9_]+)@(PAV)?([A-Za-z0-9_]+)@@',blob):
    s=m.group(0).decode('ascii','replace')
    if re.search(r'voc|audio|sound|wave',s,re.I):
        print(f'  0x{IB+rva0+m.start():X} {s}')
# --- static vtable init chains C7 05 <obj><vt> where vt points into .rdata near audio fn range ---
# collect vtable pointer candidates from .rdata: dword in [0x7E0000,0x800000] whose value in .text 0x40xxxx-0x7Exxxx
# focus: find C7 05 writes with obj in .data and value in .rdata
print()
print('=== static vtable init (C7 05) in audio function address region 0x406000-0x408000 ===')
md=Cs(CS_ARCH_X86,CS_MODE_32);md.skipdata=True;md.detail=True
raw=data[0x406000-IB:0x408500-IB]
for ins in md.disasm(raw,0x406000):
    if ins.id==X86_INS_MOV and ins.mnemonic=='mov' and len(ins.bytes)>=10 and ins.bytes[0:2]==b'\xC7\x05':
        # C7 05 <abs32 obj> <abs32 imm>
        obj=struct.unpack_from('<I',ins.bytes,2)[0]; val=struct.unpack_from('<I',ins.bytes,6)[0]
        print(f'  0x{ins.address:X}: mov dword [0x{obj:X}], 0x{val:X}')
# --- naming candidate: is 0x449C30 in TARGETS? ---
tg=set()
with open(os.path.join(ROOT,r'lead\next_re_20261117_r14\S19-K2\TARGETS.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'): tg.add(row['entry'])
print()
for e in ['00449C30','00752B70','00406B10','00405170','00432E40','00432C70']:
    print(f'  target {e} in TARGETS: {e in tg}')
# --- Bink small functions call/import summary ---
ev=json.load(open(os.path.join(ROOT,r'lead\next_re_20261117_r14\S19-K2\work\s19_evidence.json'),encoding='utf-8'))
atlas={}
with open(os.path.join(ROOT,r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'): atlas[row['entry'].upper()]=int(row['size'])
print()
print('=== Bink fns import calls ===')
for e in ['00432700','00432750','00432A60','00432BD0','00432C30','00432E40','00433020','004331F0','00432C70']:
    r=ev.get(e)
    if r:
        print(f"  {e} sz={atlas.get(e)} imports={[x[1] for x in r['import_calls']]}")
