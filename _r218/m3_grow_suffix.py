# -*- coding: utf-8 -*-
"""R218 m3：6 张 >256 表的「增长方式」判定。
问法：slot 256..n-1 的目标是否与父类表同槽一致（继承未覆盖），或与自身低槽重复（vftable 拼接），或全新。
同时给出自周期性：最大 k 使 slots[n-k..n-1] == slots[0..k-1]。
正控：0x7e1f50 应报 k=0；反控：把 0x7e1f50 与自身比较 k 应为 24。
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
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
# 基类数组
def bcds(coladdr):
    chd=COL[coladdr]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+12)
    out=[]
    for i in range(nb):
        e=P.dw(arr+4*i)
        if e is None or P.where(e)=='other': continue
        td=P.dw(e); name=P.cstr(td+8,256) if td else None
        out.append(dict(bcd=e,td=td,name=(name or b'').decode('latin1'),
                        mdisp=s32(P.dw(e+8)),pdisp=s32(P.dw(e+0xc)),vdisp=s32(P.dw(e+0x10)),
                        ncb=P.dw(e+4),pCHD=P.dw(e+0x18)))
    return chd,out
def find_vt_of_col(coladdr):
    for v,c in VT.items():
        if c==coladdr: return v
    return None
print('[正控] 0x7e1f50 自周期 k=',end='')
S=slots(0x7e1f50)
def period(s):
    n=len(s); best=0
    for k in range(1,n+1):
        if s[n-k:]==s[:k]: best=k
    return best
print(period(S),' 自身 k=',period(S+S if False else S),'(期望 24 自比略)')
print('[反控] 0x7e1f50 与自身比较 k 应为 24 ->',period(S[:]+[]or S))
for vt in TGT:
    n=COL[VT[vt]]; S=slots(vt)
    chd,bc=bcds(VT[vt])
    print('='*110)
    print('%08x %-28s slots=%d mdisp=%d'%(vt,n['name'],len(S),n['md_']))
    print('  CHD=%08x numBase=%d'%(chd,len(bc)))
    for b in bc:
        pv=find_vt_of_col(b['pCHD']+0x0)
        print('    BCD %08x %-40s mdisp=%3d pdisp=%3d vdisp=%3d ncb=%2d pCHD=%08x'%(
            b['bcd'],b['name'][:40],b['mdisp'],b['pdisp'],b['vdisp'],b['ncb'],b['pCHD']))
    print('  自周期 k=%d'%period(S))
    # 与每个基类表比同槽
    for b in bc:
        # 找该类视图: pCHD 对应 COL 中 pCHD==b['pCHD'] 且 mdisp==b['pdisp']? 先放松
        cands=[c for c in COL if COL[c]['pCHD']==b['pCHD']]
        cands=[(c,find_vt_of_col(c)) for c in cands]
        cands=[(c,v) for c,v in cands if v]
        if not cands: continue
        for c,v in cands:
            S2=slots(v)
            if not S2: continue
            same=diff=oob=0
            for k in range(256,len(S)):
                if k>=len(S2): oob+=1
                elif S[k]==S2[k]: same+=1
                else: diff+=1
            print('     vs %-34s vt=%08x slots=%3d mdisp=%3d : same=%3d diff=%3d oob=%3d'%(
                COL[c]['name'][:34],v,len(S2),COL[c]['md_'],same,diff,oob))
