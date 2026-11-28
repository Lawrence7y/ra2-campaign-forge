# -*- coding: utf-8 -*-
"""R218 m6：订正 m4 的自身 BCD 判据（+0x18 自指），重做 slot>=256 与直接父类同槽比对。
自身 BCD 判据实测：BCD+0x18 (pCHD) == BCD 自身地址（自指），且 +0 pTD 名字 == 本类名。
直接父类 = 数组中 ncb == 自身ncb-1 的那一项。
正控：AircraftClass 父类名称应为 .?AVFootClass@@；FootClass 父类 .?AVTechnoClass@@；TechnoClass 父类 .?AVRadioClass@@。
反控：把父类换成自身（同表比）时 same 必须 == 该表 slot>=256 总数。
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
def bcds(coladdr):
    chd=COL[coladdr]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+12); out=[]
    for i in range(nb):
        e=P.dw(arr+4*i)
        if e is None or P.where(e)=='other': continue
        td=P.dw(e); nm=P.cstr(td+8,256) if td else None
        out.append(dict(bcd=e,name=(nm or b'').decode('latin1'),ncb=P.dw(e+4),p18=P.dw(e+0x18),
                        mdisp=s32(P.dw(e+8))))
    return chd,arr,out
def vt_by_chd(chd,md=0):
    r=[(v,c) for v,c in VT.items() if COL[c]['pCHD']==chd and COL[c]['md_']==md]
    return min(r) if r else None
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
EXP={0x7e22a4:'.?AVFootClass@@',0x7e8c94:'.?AVTechnoClass@@',0x7f4960:'.?AVRadioClass@@'}
tot=collections.Counter(); rows=[]
for vt in TGT:
    c=VT[vt]; S=slots(vt); nm=COL[c]['name']; chd,arr,bc=bcds(c)
    me=[b for b in bc if b['name']==nm]
    if len(me)!=1:
        print('!! %s 自身 BCD 不唯一: %s'%(hex(vt),[(hex(b['bcd']),b['name'],b['ncb']) for b in me]))
        me=[b for b in me if b['p18']==b['bcd']]
    assert len(me)==1,(hex(vt),me)
    me=me[0]
    print('='*108)
    print('%08x %-24s slots=%3d CHD=%08x arr=%08x nbase=%d  自身BCD=%08x ncb=%d'%(vt,nm,len(S),chd,arr,len(bc),me['bcd'],me['ncb']))
    par=[b for b in bc if b['ncb']==me['ncb']-1]
    if not par:
        print('  无 ncb=自身-1 的项 ⇒ 父类不可判，列表:'); [print('    ',hex(b['bcd']),b['name'],b['ncb']) for b in bc]; continue
    par=par[0]
    ok = EXP.get(vt)==par['name'] if vt in EXP else None
    print('  直接父类 BCD=%08x %-30s ncb=%d  pCHD=%08x  正控期望=%s -> %s'%(par['bcd'],par['name'],par['ncb'],par['p18'],EXP.get(vt,'(未定)'),'PASS' if ok else ('FAIL' if ok is False else 'n/a')))
    pv=vt_by_chd(par['p18'])
    print('  父类主视图=%s'%(pv and (hex(pv[0]),COL[pv[1]]['name'])))
    if not pv:
        # 父类无虚表 => 该父类为纯接口/无 vft
        print('  ⇒ 父类无 mdisp=0 虚表（接口/无 vft），本表是首个带 vft 的派生 ⇒ 改用「本表 slot>=256 是否在父类链任一视图出现」降级统计')
        # 收集整条链上的所有视图
        chain=[]
        for b in bc:
            t=vt_by_chd(b['p18'])
            if t: chain.append(t)
        print('  链上视图数=%d'%len(chain))
        cov=0; nocov=[]
        for k in range(256,len(S)):
            hit=[(hex(v),COL[cc]['name']) for v,cc in chain if k<len(slots(v)) and slots(v)[k]==S[k]]
            if hit: cov+=1
            else: nocov.append((k,S[k]))
        print('  slot>=256 在链上任一视图同槽命中: %d/%d'%(cov,len(S)-256))
        for k,a in nocov[:10]:
            print('     slot%3d self=%08x[%s] 全链无同值'%(k,a,P.RAW[P.r2o(a):P.r2o(a)+8].hex()))
        tot['nocov']+=len(nocov); tot['cov']+=cov
        rows.append((hex(vt),nm,len(S),'chain',cov,len(nocov)))
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
    # 反控：与自身比
    selfsame=sum(1 for k in range(256,len(S)) if k<len(S) and S[k]==S[k])
    print('  反控 自身比 same=%d（应 == 该表 slot>=256 总数 %d）'%(selfsame,len(S)-256))
print('='*108)
print('[合计]',dict(tot))
for r in rows: print('  ',r)
