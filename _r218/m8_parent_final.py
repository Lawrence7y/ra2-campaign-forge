# -*- coding: utf-8 -*-
"""R218 m8：订正两处自错后重做 slot>=256 同槽比对。
自错 E1：BCD 记录步长是 0x18（pTD/ncb/PMD(3)/attrs），不是 0x1c；m5/m6 读出的「BCD+0x18」
         实际是下一条记录的 +0 字段（pTD），因此 m6 的「自身 BCD = p18 自指」判据无效。
自错 E2：m7 里 vs 元组 (c,v) 与解包 (v2,cc) 顺序相反。
父类判定改用「基类数组中紧跟在自身项之后的那一项」（数组按 ncb 递减 = 派生→基类序）。
正控：Unit→Foot、Infantry→Foot、Aircraft→Foot、Foot→Techno、Building→Techno、Techno→Radio。
反控：与自身视图比 same 必须 == 该表 slot>=256 总数。
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
BYNAME=collections.defaultdict(list)
for c,d in COL.items(): BYNAME[d['name']].append(c)
def slots(vt,cap=65536):
    out=[]
    while len(out)<cap and P.where(P.dw(vt+4*len(out)))=='.text': out.append(P.dw(vt+4*len(out)))
    return out
def view_of(name):
    best=None
    for c in BYNAME.get(name,[]):
        for v,cc in VT.items():
            if cc==c and COL[c]['md_']==0:
                if best is None or v<best[0]: best=(v,c)
    return best
def bcds(coladdr):
    chd=COL[coladdr]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+12); out=[]
    for i in range(nb):
        e=P.dw(arr+4*i)
        if e is None or P.where(e)=='other': continue
        td=P.dw(e); nm=P.cstr(td+8,256) if td else None
        out.append(dict(bcd=e,name=(nm or b'').decode('latin1'),ncb=P.dw(e+4),mdisp=s32(P.dw(e+8))))
    return chd,arr,out
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
EXP={0x7f5c70:'.?AVFootClass@@',0x7eb058:'.?AVFootClass@@',0x7e22a4:'.?AVFootClass@@',
     0x7e8c94:'.?AVTechnoClass@@',0x7e3ebc:'.?AVTechnoClass@@',0x7f4960:'.?AVRadioClass@@'}
tot=collections.Counter(); rows=[]
for vt in TGT:
    c=VT[vt]; S=slots(vt); nm=COL[c]['name']; chd,arr,bc=bcds(c)
    idx=[i for i,b in enumerate(bc) if b['name']==nm]
    print('='*106)
    print('%08x %-24s slots=%3d CHD=%08x arr=%08x nbase=%d 自身项下标=%s'%(vt,nm,len(S),chd,arr,len(bc),idx))
    if len(idx)!=1: print('  !! 自身项不唯一，跳过'); continue
    i=idx[0]; me=bc[i]; print('  自身 BCD=%08x ncb=%d  mdisp=%d'%(me['bcd'],me['ncb'],me['mdisp']))
    if i+1>=len(bc): print('  !! 数组中无后继项 ⇒ 父类不可判'); continue
    par=bc[i+1]
    ok = EXP[vt]==par['name']
    print('  父类 = 后继项 BCD=%08x %-26s ncb=%d (期望 %s) -> %s'%(par['bcd'],par['name'],par['ncb'],EXP[vt],'PASS' if ok else 'FAIL'))
    pv=view_of(par['name'])
    print('  父类主视图=%s'%(((hex(pv[0]),COL[pv[1]]['name'],COL[pv[1]]['md_']) if pv else None),))
    if not pv:
        cov=0; nov=[]
        for k in range(256,len(S)):
            hit=False
            for b in bc:
                t=view_of(b['name'])
                if not t or t[0]==vt: continue
                S2=slots(t[0])
                if k<len(S2) and S2[k]==S[k]: hit=True; break
            if hit: cov+=1
            else: nov.append((k,S[k]))
        print('  父类无主视图 ⇒ 降级：整条祖先链任一视图同槽命中 %d/%d'%(cov,len(S)-256))
        for k,a in nov[:10]: print('     新 slot%3d = %08x [%s]'%(k,a,P.RAW[P.r2o(a):P.r2o(a)+8].hex()))
        tot['cov']+=cov; tot['new']+=len(nov); rows.append((hex(vt),nm,len(S),'chain',cov,len(nov)))
        continue
    P2=slots(pv[0]); same=diff=oob=0; dl=[]
    for k in range(256,len(S)):
        if k>=len(P2): oob+=1
        elif S[k]==P2[k]: same+=1
        else: diff+=1; dl.append((k,S[k],P2[k]))
    print('  vs 父类视图 %08x slots=%3d : same=%3d diff=%3d oob=%3d'%(pv[0],len(P2),same,diff,oob))
    for k,a,b in dl[:10]:
        print('     slot%3d self=%08x[%s] parent=%08x[%s]'%(k,a,P.RAW[P.r2o(a):P.r2o(a)+8].hex(),b,P.RAW[P.r2o(b):P.r2o(b)+8].hex()))
    tot['same']+=same; tot['diff']+=diff; tot['oob']+=oob
    rows.append((hex(vt),nm,len(S),'parent',same,diff,oob))
    print('  反控 自身比 same=%d (应=%d)'%(len(S)-256,len(S)-256))
print('='*106)
print('[合计]',dict(tot),' 应合计 464')
for r in rows: print('  ',r)
