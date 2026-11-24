# -*- coding: utf-8 -*-
"""S13-K8RECHK step4: verify pivotal cases - DamageGroup (both), KamikazeControl base, plain dtors."""
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

def dis(va,n,label=''):
    print('\n--- %s @ 0x%X (%d bytes) ---'%(label,va,n))
    for ins in MD.disasm(rdva(va,n),va):
        print('  %08X  %-22s %-7s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))

# DamageGroup: derived 0x7e5170 installed at 0x4892aa [esp+0x38] func 0x489280
# base 0x7e5144 installed at 0x489b1e [esp+0x38] func 0x489ae0 + 0x48a491/4bb func 0x48a410
dis(0x489240,0x120,'DamageGroup derived-ctor region 0x489280')
dis(0x489ae0,0x90,'DamageGroup base-ctor region 0x489ae0')
dis(0x48a410,0xd0,'DamageGroup base-ctor region 0x48a410')

# KamikazeControl base write 0x54e31d: confirm enclosing atexit DTOR (push 0x54e2d0 @0x54e293)
dis(0x54e2c0,0x90,'KamikazeControl ctor tail / dtor head')
dis(0x54e2d0,0xb0,'KamikazeControl DTOR (0x54e2d0)')
# check push 0x54e2d0 and call atexit
for target in (0x54e2d0,):
    b=struct.pack('<I',target); i=0; occ=[]
    while True:
        j=DATA.find(b,i)
        if j<0:break
        va=None
        for s in SECS:
            if s['raw']<=j<s['raw']+s['rs']:
                va=s['va']+(j-s['raw']); break
        occ.append((hex(j),hex(va) if va else None))
        i=j+1
    print('\n0x%X ptr occurrences:'%target,occ)

# plain dtors: 0075E510 body + who installs 0x7f6b30 (WarheadTypeClass)
dis(0x75e4a0,0xa0,'WarheadTypeClass install func 0x75e4a0 (writes 0x7f6b30 @0x75e516)')
dis(0x75e510,0x70,'0075E510 scalar dtor body')
# 0065BED0 and 0x7f0810 install
dis(0x65b1e0,0x70,'RadSiteClass install func 0x65b1e0 (writes 0x7f0810 @0x65b228)')
dis(0x65bed0,0x40,'0065BED0 scalar dtor body')
print('\nDONE step4')
