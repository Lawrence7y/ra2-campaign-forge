# -*- coding: utf-8 -*-
"""R218 m4：6 张 >256 表 slot>=256 与「直接父类」同槽比对（修 m3 两个 bug：period 取 k<n；父类定位用 pCHD 反查 COL）。
直接父类判定：CHD 基类数组中 ncb 最大的那个非自身项（ncb = numContainedBases，越大越靠上/越派生）。
正控：AircraftClass 父类应为 FootClass；FootClass 父类应为 TechnoClass；BuildingClass 父类应为 TechnoClass。
反控：把父类改成自身时 same 应等于 464 总数（自比恒等）。
"""
import sys,struct,collections
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
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
def slots(vt,cap=65536):
    out=[]
    while len(out)<cap and P.where(P.dw(vt+4*len(out)))=='.text': out.append(P.dw(vt+4*len(out)))
    return out
def period(s):
    n=len(s); best=0
    for k in range(1,n):
        if s[n-k:]==s[:k]: best=k
    return best
def bcds(coladdr):
    chd=COL[coladdr]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+12); out=[]
    for i in range(nb):
        e=P.dw(arr+4*i)
        if e is None or P.where(e)=='other': continue
        td=P.dw(e); nm=P.cstr(td+8,256) if td else None
        out.append(dict(bcd=e,name=(nm or b'').decode('latin1'),ncb=P.dw(e+4),pCHD=P.dw(e+0x18),
                        mdisp=s32(P.dw(e+8))))
    return chd,out
def vts_of_chd(chd):
    return [(v,c) for v,c in VT.items() if COL[c]['pCHD']==chd and COL[c]['md_']==0]
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
print('[正控] 0x7e1f50 period(k<n)=%d (期望 0)  slots=%d'%(period(slots(0x7e1f50)),len(slots(0x7e1f50))))
tot_same=tot_diff=tot_oob=0
for vt in TGT:
    c=VT[vt]; S=slots(vt); nm=COL[c]['name']
    chd,bc=bcds(c)
    self_b=[b for b in bc if b['pCHD']==chd and b['ncb']==len(bc)-1]
    others=[b for b in bc if b not in self_b]
    parent=max(others,key=lambda b:b['ncb']) if others else None
    print('='*104)
    print('%08x %-26s slots=%3d  period=%3d  CHD=%08x nbase=%d'%(vt,nm,len(S),period(S),chd,len(bc)))
    print('  自身BCD=%s  直接父类=%s (ncb=%s)'%([hex(b['bcd']) for b in self_b],parent and parent['name'],parent and parent['ncb']))
    if parent:
        pv=vts_of_chd(parent['pCHD'])
        print('  父类视图候选=%s'%[(hex(v),COL[cc]['name'],COL[cc]['md_']) for v,cc in pv])
        if pv:
            pv=sorted(pv,key=lambda x:COL[x[1]]['md_'])[0][0]
            P2=slots(pv)
            same=diff=oob=0; difflist=[]
            for k in range(256,len(S)):
                if k>=len(P2): oob+=1
                elif S[k]==P2[k]: same+=1
                else: diff+=1; difflist.append((k,S[k],P2[k]))
            print('  vs 父类 %08x slots=%3d : same=%3d diff=%3d oob=%3d'%(pv,len(P2),same,diff,oob))
            for k,a,b in difflist[:12]:
                ba=P.RAW[P.r2o(a):P.r2o(a)+8].hex(); bb=P.RAW[P.r2o(b):P.r2o(b)+8].hex()
                print('     slot%3d self=%08x[%s] parent=%08x[%s]'%(k,a,ba,b,bb))
            if len(difflist)>12: print('     ... 共 %d 条不同'%len(difflist))
            tot_same+=same; tot_diff+=diff; tot_oob+=oob
    # 低槽内重复
    low=set(S[:256]); inlow=sum(1 for t in S[256:] if t in low)
    print('  slot>=256 目标在本表低 256 槽内已出现: %d/%d'%(inlow,len(S)-256))
print('='*104)
print('[合计] same=%d diff=%d oob=%d (总 464) => %s'%(tot_same,tot_diff,tot_oob,tot_same+tot_diff+tot_oob))
