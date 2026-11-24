# -*- coding: utf-8 -*-
import sys,pefile,struct,json
sys.stdout.reconfigure(encoding='utf-8')
P=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8'
D=open(P,'rb').read();pe=pefile.PE(P,fast_load=True);IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.decode().rstrip('\x00'),IMG+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def rd(va,n):
    for nm,b,vs,pt,rs in SECS:
        if b<=va<b+vs:return D[pt+(va-b):pt+(va-b)+n]
    return b''
def u32(va):
    d=rd(va,4);return struct.unpack('<I',d)[0] if len(d)==4 else None
def cstr(va,lim=100):
    o=b''
    for i in range(lim):
        c=rd(va+i,1)
        if not c or c==b'\x00':break
        o+=c
    return o.decode('latin1')
def secn(va):
    for nm,b,vs,pt,rs in SECS:
        if b<=va<b+vs:return nm
    return '?'
# TDs
tds={}
for nm,b,vs,pt,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')):continue
    for va in range(b,b+vs-8,4):
        if rd(va,4) in (b'.?AV',b'.?AU'):
            name=cstr(va,120)
            if len(name)>4 and name.endswith('@@'):tds[va-8]=name
# vtable bases: scan rdata for [vt-4] that is a COL ptr pointing to TD
vtbases=[]
for nm,b,vs,pt,rs in SECS:
    if not (nm.startswith('.rdata') or nm.startswith('.data')):continue
    for va in range(b+4,b+vs-4,4):
        cp=u32(va-4)  # candidate COL ptr at vt-4
        if cp in tds:  # cp points directly to a TD? no; cp is COL, [cp+0xC]=TD
            pass
        if cp is None:continue
        td=u32(cp+0xC)
        if td in tds:
            vt=va
            # collect slots
            slots=[]
            for i in range(0,300):
                t=u32(vt+4*i)
                if t is None or t==0:break
                if secn(t)=='.text':slots.append((i,t))
                elif not slots and i<2:break
                elif slots:break
            if slots:vtbases.append((vt,cp,tds[td],tuple(slots)))
lines=['# vtable registry: VT base / COL ptr / RTTI name / slots (from .rdata COL scan)','']
for vt,cp,nm,slots in sorted(set(vtbases)):
    lines.append('VT %08X COL %08X NAME %s NSLOTS %d'%(vt,cp,nm,len(slots)))
    for i,t in slots:lines.append('  slot %-3d -> %08X'%(i,t))
open(BASE+r'\EVIDENCE\vt_rtti_registry.txt','w',encoding='utf-8').write('\n'.join(lines)+'\n')
print('vt_rtti_registry lines',len(lines),'vtbases',len(set(vtbases)))
