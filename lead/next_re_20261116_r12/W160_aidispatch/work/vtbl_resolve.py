import json, os, struct
import pefile
R=r"D:\Project\ra2-campaign-forge"
BIN=os.path.join(R,'ra2youli','gamemd.exe')
pe=pefile.PE(BIN,fast_load=True)
secs=[]
for s in pe.sections:
    secs.append((0x400000+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData, s.Name.rstrip(b'\0').decode()))
def readva(va,n):
    for v,vs,raw,rs,nm in secs:
        if v<=va<v+min(vs,rs):
            off=raw+(va-v)
            return open(BIN,'rb').read()[off:off+n]
    return b''
def u32(va):
    b=readva(va,4)
    return struct.unpack('<I',b)[0] if len(b)==4 else None
for va in [0x87F778,0x87F77C,0x87F780,0x87F784,0x87F788,0x87F78C,0xA83E00,0xA83E04,0xA83E10,0xA83E30,0xA83E34,0xA83E40,0x887324,0x8B40D8,0x8B40CC,0x8B40E8,0x8B40F8,0xA8B230]:
    try:
        b=readva(va,0x14); v=u32(va)
        print(f'{va:08X}: {b.hex()}  [va]={v:08X}' if v is not None else f'{va:08X}: {b.hex()}  [va]=<BSS>')
    except Exception as e: print(va,e)
# vtable COL map
for path in ['vtables_canonical.json','class_atlas_v2.json']:
    p=os.path.join(R,'lead','next_re_20261112_r10','W130_atlas',path)
    print(path,os.path.getsize(p))
vt=json.load(open(os.path.join(R,'lead','next_re_20261112_r10','W130_atlas','vtables_canonical.json'),encoding='utf-8'))
print('vt type',type(vt), list(vt)[:6] if isinstance(vt,dict) else vt[:1])
