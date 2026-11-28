# -*- coding: utf-8 -*-
"""R218 m2：6 张 >256 表的尾部物理布局。
同时打印：表中最后 6 槽、其后 12 个 dword（含落段/是否 COL 指针/最近 COL 指针位置）。
正控：0x7e1f50 尾部应立刻遇到非 .text 或下一表。
"""
import sys,struct
sys.path.insert(0,'_r185'); import pe185 as P
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL)
# 重建 VT 映射：vftable 地址 -> COL 地址
VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
COLADDR=sorted(COL)
import bisect
def nearest_col(va,dirn):
    i=bisect.bisect_left(COLADDR,va)
    if dirn>0: return COLADDR[i] if i<len(COLADDR) else None
    return COLADDR[i-1] if i>0 else None
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
def nslots(vt):
    n=0
    while n<65536 and P.where(P.dw(vt+4*n))=='.text': n+=1
    return n
for vt in TGT:
    n=nslots(vt); name=COL[VT[vt]]['name']
    print('='*100)
    print('%08x  slots=%d  %s  mdisp=%d'%(vt,n,name,COL[VT[vt]]['md_']))
    print('  表内末 6 槽:')
    for k in range(max(0,n-6),n):
        t=P.dw(vt+4*k)
        print('    slot%3d @%08x = %08x %-8s %s'%(k,vt+4*k,t,P.where(t),''))
    print('  其后 12 dword:')
    for k in range(n,n+12):
        v=P.dw(vt+4*k); a=vt+4*k
        print('    +%3d @%08x = %08x %-10s %s'%(k,a,v,P.where(v),('COL:'+COL[v]['name'] if v in CS else '')))
    pr=nearest_col(vt,-1); nx=nearest_col(vt+4*n,1)
    print('  最近 COL: 前=%s(+%s)  后=%s(-%s)'%(pr and hex(pr),pr and (vt-pr)//4,nx and hex(nx),nx and (nx-vt-4*n)//4))
