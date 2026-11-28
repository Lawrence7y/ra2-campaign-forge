# -*- coding: utf-8 -*-
"""R217 m9：R210 的『主视图 954 表 slot>=3 = 9958』是否受 cap=256 截断影响。
定义主视图 = 每个 pCHD 视图族中 mdisp==0 的那张（R210 口径）。
三口径并排：uncapped / cap256 / cap256+只对 954 主视图。
正控：族数应 = 954（R210 报的族数）。
反控：把主视图定义为『族内任意一张』时，分母会 != 954。
"""
import sys,struct,collections,json
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
def nslots(vt,cap=65536):
    n=0
    while n<cap and P.where(P.dw(vt+4*n))=='.text': n+=1
    return n
ALL={v:nslots(v) for v in VT}
FAM=collections.defaultdict(list)
for v,c in VT.items(): FAM[COL[c]['pCHD']].append(v)
families=[(g,vs) for g,vs in FAM.items() if any(COL[VT[v]]['md_']==0 for v in vs)]
print('[族] 含 mdisp==0 的族数 = %d'%len(families))
prim=[sorted([v for v in vs if COL[VT[v]]['md_']==0])[0] for g,vs in families]
print('[主视图] 张数=%d'%len(prim))
unc=sum(max(0,ALL[v]-3) for v in prim)
cap=sum(max(0,min(ALL[v],256)-3) for v in prim)
print('[9958 复核] 主视图 slot>=3：uncapped=%d  cap256=%d'%(unc,cap))
print('  与 R210 记载 9958 的差: uncapped %+d, cap256 %+d'%(unc-9958,cap-9958))
# 哪些主视图溢出
ov=[(v,ALL[v]) for v in prim if ALL[v]>256]
print('  主视图溢出 256 的张数=%d'%len(ov),[(hex(v),n,COL[VT[v]]['name']) for v,n in ov])
# 无 cap 时总共（全 1218 表）
print('[全表] slot>=3: uncapped=%d cap256=%d'%(sum(max(0,n-3) for n in ALL.values()),sum(max(0,min(n,256)-3) for n in ALL.values())))
# 反控
print('[反控] 若把「族内任意一张」当前口径，主视图张数=%d（应 != 954）'%sum(len(vs) for g,vs in families))
json.dump(dict(fam=len(families),prim=len(prim),unc=unc,cap=cap,diff_unc=unc-9958,diff_cap=cap-9958,
  over=[(hex(v),n,COL[VT[v]]['name']) for v,n in ov]),open('_r217/m9.json','w'),indent=1)
