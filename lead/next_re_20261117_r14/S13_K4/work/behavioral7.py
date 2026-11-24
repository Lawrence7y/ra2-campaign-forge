#!/usr/bin/env python3
"""Verify 7 real-named behavioral funcs via byte evidence: INI key strings, vptr writes,
factory push+new, Verses strtok. Read-only. Emits EVIDENCE/behavioral7.txt"""
import struct, pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K4\EVIDENCE\behavioral7.txt"
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase; DATA=open(EXE,'rb').read()
SECS=[]
for s in pe.sections:
    nm=s.Name.decode('ascii','replace').rstrip('\x00'); lo=IB+s.VirtualAddress
    hi=lo+max(s.Misc_VirtualSize,s.SizeOfRawData); rl=s.PointerToRawData; rh=rl+s.SizeOfRawData
    SECS.append((nm,lo,hi,rl,rh))
def off_of(va):
    for n,lo,hi,rl,rh in SECS:
        if lo<=va<hi:
            o=rl+(va-lo)
            if o<rh: return o
    return None
def sec_of(va):
    for n,lo,hi,rl,rh in SECS:
        if lo<=va<hi: return n
    return None
def u32(va):
    o=off_of(va)
    return struct.unpack_from('<I',DATA,o)[0] if o is not None and o+4<=len(DATA) else None
def cstr(va,cap=80):
    o=off_of(va)
    return DATA[o:o+cap].split(b'\x00')[0].decode('latin1') if o is not None else ''
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def disasm(va,n):
    o=off_of(va)
    return '\n'.join(f'{i.address:08X}: {i.mnemonic} {i.op_str}' for i in md.disasm(DATA[o:o+n],va))

L=[]
def p(x=''): L.append(str(x))
# known INI key string VAs from S13-K1 evidence
# Warhead 0x8183b4='Warhead', Projectile 0x849268='Projectile'
# Scan each function for: push <VA> where cstr(VA) is printable, call 0x528a10 (GetString/INI read),
#   call resolvers (0x75e3b0/0x46c790/0x772940), vptr writes (mov [reg], imm in .rdata range),
#   push 0x1d0/0x2f8 (new size), rep movsd (ctor Verses), strtok calls.
FUNCS={
 0x46BEE0:'BulletTypeClass::LoadFromINI',
 0x46C790:'BulletTypeClass::FindOrMake',
 0x75CEC0:'WarheadTypeClass::Constructor',
 0x75D3A0:'WarheadTypeClass::LoadFromINI',
 0x75E3B0:'WarheadTypeClass::FindOrMake',
 0x771C70:'WeaponTypeClass::Constructor',
 0x772080:'WeaponTypeClass::LoadFromINI',
}
NEW=0x7C8E17; STRTOK_SET={0x524EC0,0x475D70}  # from evidence
for va,nm in FUNCS.items():
    # find size from atlas
    import csv
    sz=None
    for r in csv.DictReader(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K4\TARGETS.tsv",encoding='utf-8',errors='replace'),delimiter='\t'):
        if int(r['entry'],16)==va: sz=int(r['atlas_size']); break
    p(f'========== {nm} @ {hex(va)} size={sz} ==========')
    o=off_of(va); code=DATA[o:o+sz]
    # scan disassembled instructions for evidence
    ini_keys=set(); calls=set(); vptr_writes=set(); push_imm=set(); repmov=0
    for i in md.disasm(code,va):
        # push <VA> where VA points to printable string
        if i.mnemonic=='push' and i.op_str.startswith('0x'):
            try: v=int(i.op_str,16)
            except: v=None
            if v is not None and sec_of(v) in ('.rdata','.data'):
                s=cstr(v,40)
                if s and all(32<=ord(c)<127 for c in s) and 1<len(s)<40:
                    ini_keys.add((i.address,v,s))
        if i.mnemonic=='call' and i.op_str.startswith('0x'):
            try: calls.add(int(i.op_str,16))
            except: pass
        if i.mnemonic=='mov' and 'ptr [' in i.op_str and ', 0x' in i.op_str:
            # vptr write: mov dword ptr [reg+off], 0x7xxxxx (.rdata)
            parts=i.op_str.rsplit(',',1)
            if len(parts)==2:
                try: imm=int(parts[1].strip(),16)
                except: imm=None
                if imm is not None and sec_of(imm)=='.rdata' and 0x7e0000<=imm<0x800000:
                    vptr_writes.add((i.address,imm))
        if i.mnemonic=='push' and i.op_str in ('0x1d0','0x2f8','0x160'):
            push_imm.add((i.address,i.op_str))
        if 'rep movs' in i.mnemonic or i.mnemonic.startswith('rep'):
            repmov+=1
    if ini_keys:
        p('  INI-key-like string pushes:')
        for a,v,s in sorted(ini_keys): p(f'    {a:08X}: push {hex(v)} -> {s!r}')
    INTEREST=set([NEW,0x528a10,0x75e3b0,0x46c790,0x772940,0x7c8d20,0x7c8df0])|STRTOK_SET
    interesting_calls={c:hex(c) for c in calls if c in INTEREST}
    if interesting_calls: p('  calls of interest: '+', '.join(f'{hex(c)}' for c in sorted(interesting_calls)))
    if vptr_writes: p('  vptr writes: '+', '.join(f'{a:08X}->{hex(v)}' for a,v in sorted(vptr_writes)))
    if push_imm: p('  push sizes: '+', '.join(f'{a:08X}:{v}' for a,v in sorted(push_imm)))
    if repmov: p(f'  rep-movs count={repmov}')
    p()
open(OUT,'w',encoding='utf-8').write('\n'.join(L))
print('wrote',OUT,len(L),'lines')
