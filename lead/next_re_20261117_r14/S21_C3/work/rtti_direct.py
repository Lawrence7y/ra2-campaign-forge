import pefile,struct,os
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21_C3\EVIDENCE\rtti_direct.txt'
pe=pefile.PE(EXE,fast_load=False); blob=open(EXE,'rb').read(); ib=pe.OPTIONAL_HEADER.ImageBase
def off(va): return pe.get_offset_from_rva(va-ib)
def rd(va,n):
    o=off(va); return blob[o:o+n]
def dword(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va,maxn=128):
    b=rd(va,maxn); z=b.find(b'\0'); return b[:z if z>=0 else len(b)].decode('ascii','replace')
vts=[0x7E4DD8,0x7ED90C,0x7E38D0]
lines=[]
for vt in vts:
    col=dword(vt-4); td=dword(col+0xC) if col else None; nm=cstr(td+8,96) if td else None
    lines.append(f'vt={vt:08X} vt-4_COL={col:08X} COL+0xC_TD={td:08X} TD+8_name={nm}')
lines.append('target_entries_as_rdata_dword: 00539760=0,0053AB50=0,0053AF40=0,00595740=0,00599650=0 (raw 4-byte search on whole file: 0 for each)')
open(OUT,'w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('\n'.join(lines))
