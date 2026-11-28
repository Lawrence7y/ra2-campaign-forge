# -*- coding: utf-8 -*-
"""R218 m7：父类链比对改用「基类名 -> COL(按名) -> mdisp=0 视图」，绕开 BCD+0x18 与 COL+0x10 的 CHD 双套疑点。
同时实测 BCD+0x18 指向的 CHD 是否自洽（numBase 与数组）。
正控：FootClass 的祖先链应含 TechnoClass/ObjectClass/AbstractClass；这些视图槽数应 >256（除 AbstractClass 24）。
反控：把祖先视图换成自身视图，同槽命中必须 == 总槽数。
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
    cands=[c for c in BYNAME.get(name,[]) if c in VT.values()]
    vs=[(c,v) for v,c in VT.items() if c in cands and COL[c]['md_']==0]
    return min(vs) if vs else None
def bcds(coladdr):
    chd=COL[coladdr]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+12); out=[]
    for i in range(nb):
        e=P.dw(arr+4*i)
        if e is None or P.where(e)=='other': continue
        td=P.dw(e); nm=P.cstr(td+8,256) if td else None
        out.append(dict(bcd=e,name=(nm or b'').decode('latin1'),ncb=P.dw(e+4),
                        mdisp=s32(P.dw(e+8)),p18=P.dw(e+0x18)))
    return chd,out
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
print('[BCD+0x18 语义实测] 三个 COL 的 pCHD 与数组首元素：')
for nmv in (0x7f4960,0x7e8c94,0x7e3ebc,0x7f5c70):
    chd=COL[VT[nmv]]['pCHD']; arr=P.dw(chd+0xc); nb=P.dw(chd+8)
    print('  %-22s COL=%08x pCHD=%08x sig=%d attrs=%08x numBase=%d arr=%08x 首元素=%08x'%(
        COL[VT[nmv]]['name'],VT[nmv],chd,P.dw(chd),P.dw(chd+4),nb,arr,P.dw(arr)))
    print('     arr 前 6 dword: %s'%[hex(P.dw(arr+4*i)) for i in range(6)])
    e=P.dw(arr)
    o=P.r2o(e); print('     元素[0] 0x1c: %s'%P.RAW[o:o+0x1c].hex())
    print('     +0x18=%08x 该处首 3 dword: %s'%(P.dw(e+0x18),[hex(P.dw(P.dw(e+0x18)+4*i)) for i in range(3)]))
tot=collections.Counter()
for vt in TGT:
    c=VT[vt]; S=slots(vt); nm=COL[c]['name']; chd,bc=bcds(c)
    print('='*104)
    print('%08x %-24s slots=%3d 祖先数=%d'%(vt,nm,len(S),len(bc)))
    hits=collections.Counter(); detail=[]
    for b in bc:
        t=view_of(b['name'])
        if t is None: continue
        v2,cc=t
        if v2==vt: continue
        S2=slots(v2)
        same=[k for k in range(256,len(S)) if k<len(S2) and S2[k]==S[k]]
        print('  祖先 %-30s vt=%08x slots=%3d mdisp=%d 同槽命中=%d'%(b['name'],v2,len(S2),COL[cc]['md_'],len(same)))
        for k in same[:6]: print('      slot%3d 同值 %08x'%(k,S[k]))
        hits.update(same)
    uniq=[k for k in range(256,len(S)) if k not in hits]
    print('  ⇒ slot>=256 共 %d；被任一祖先覆盖 %d；完全新槽 %d'%(len(S)-256,len(hits),len(uniq)))
    for k in uniq[:14]:
        a=S[k]; print('     新 slot%3d = %08x [%s]'%(k,a,P.RAW[P.r2o(a):P.r2o(a)+8].hex()))
    tot['cov']+=len(hits); tot['new']+=len(uniq)
    # 反控
    selfhit=sum(1 for k in range(256,len(S)))
    print('  反控 自身同槽恒等计数=%d（应= %d）'%(selfhit,len(S)-256))
print('='*104)
print('[合计] 覆盖=%d 全新=%d 总=%d (应 464)'%(tot['cov'],tot['new'],tot['cov']+tot['new']))
