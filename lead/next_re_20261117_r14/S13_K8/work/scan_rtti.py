# -*- coding: utf-8 -*-
import sys, pefile, struct
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
DATA=open(P,'rb').read()
pe=pefile.PE(P,fast_load=True)
IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip('\x00'), IMG+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def sec_of(va):
    for n,b,vs,ptr,rs in SECS:
        if b<=va<b+vs: return n,b,vs,ptr,rs
    return None
def rd(va,n):
    s=sec_of(va)
    if not s: return b''
    n0,b,vs,ptr,rs=s
    off=ptr+(va-b)
    return DATA[off:off+n]
def u32(va):
    d=rd(va,4)
    return struct.unpack('<I',d)[0] if len(d)==4 else None
def cstr(va,lim=200):
    out=b''
    for i in range(lim):
        c=rd(va+i,1)
        if not c or c==b'\x00': break
        out+=c
    return out.decode('latin1')

# Finding TDs: scan all 4-aligned addresses in rdata/data for name at +8 starting .?AV/.?AU
tds={} # td_va -> name
for nm,b,vs,ptr,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')): continue
    for va in range(b, b+vs-8, 4):
        pat=rd(va,4)
        if pat in (b'.?AV', b'.?AU'):
            name=cstr(va,120)
            if len(name)>4 and name.endswith('@@'):
                tds[va-8]=name
print('TD candidates',len(tds))
# COLs point to TDs via [col+0xC]=td; col in rdata aligned 4
# Build reverse: for each td, find col by scanning rdata dwords
import collections
tdset=set(tds)
cols={} # col -> td
for nm,b,vs,ptr,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')): continue
    for va in range(b, b+vs-0x10, 4):
        x=u32(va+0xC)
        if x in tdset:
            cols[va]=x
print('COL candidates',len(cols))
vt_info={}
for col,td in cols.items():
    vt=col+4
    slots=[]
    for i in range(0,300):
        t=u32(vt+4*i)
        if t is None or t==0: break
        tb=sec_of(t)
        if tb and tb[0]=='.text':
            slots.append((i,t))
        elif not slots and i<3:
            # early data slot before text slots - unlikely for vtable; stop
            break
        elif slots and len(slots)>3:
            break
        else:
            if slots: break
    if slots:
        vt_info[vt]=(col,tds[td],slots)
print('vt_info count',len(vt_info))
out=[]
for vt,(col,nm,slots) in sorted(vt_info.items()):
    out.append('VT %08X COL %08X NAME %s NSLOTS %d'%(vt,col,nm,len(slots)))
    for i,t in slots:
        out.append('  slot %-3d -> %08X'%(i,t))
fn=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8\EVIDENCE\vt_rtti_registry.txt'
open(fn,'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('wrote',fn,'lines',len(out))
