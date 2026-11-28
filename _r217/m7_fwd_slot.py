# -*- coding: utf-8 -*-
"""R217 m7：转发桩（0x410210 型）在表里的槽序号分布 + 它 call 的 [edx+0x2c] 落到主视图第几槽。
判据：0x2c/4 = 11 => 主视图 slot 11。
正控：AbstractClass 主视图 slot11 应 = 0x4c9150（33c0c3）。
反控：把 K 从 0x2c 改成 0x28（slot10）后，命中主视图 slot10 的桩数应变化。
"""
import sys,struct,collections,json
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; TLO=t['lo']; THI=TLO+t['rawsize']
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
        COL[base+4*k]=dict(md_=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
def slots(vt,cap=256):
    out=[]
    for i in range(cap):
        v=P.dw(vt+4*i)
        if not (TLO<=v<THI): break
        out.append(v)
    return out
SL={v:slots(v) for v in VT}
FW=0x410210
rows=[]
for v in sorted(VT):
    for i,fn in enumerate(SL[v]):
        if fn==FW: rows.append((v,i,COL[VT[v]]['md_'],COL[VT[v]]['name']))
print('[转发桩槽位] 出现次数=%d 涉及表=%d'%(len(rows),len({r[0] for r in rows})))
print('  槽序号分布',dict(sorted(collections.Counter(r[1] for r in rows).items())))
print('  所在表 mdisp 分布',dict(collections.Counter(r[2] for r in rows)))
# 主视图（同 pCHD 且 mdisp==0）的 slot11
FAM=collections.defaultdict(list)
for v,c in VT.items(): FAM[COL[c]['pCHD']].append(v)
K=0x2c//4
hit=collections.Counter(); detail=[]
for v,i,mdv,name in rows:
    fam=FAM[COL[VT[v]]['pCHD']]
    zero=[x for x in fam if COL[VT[x]]['md_']==0]
    if not zero: continue
    p=zero[0]; s=SL[p]
    tgt=s[K] if len(s)>K else None
    hit[tgt]+=1; detail.append((hex(v),name,mdv,i,hex(p),hex(tgt) if tgt else None))
print('[转发目标] 主视图 slot %d 的落点分布:'%K,{ (hex(k) if k else None):n for k,n in hit.most_common(8)})
print('  AbstractClass 正控: 主视图 0x7e1f50 slot%d = %s bytes=%s'%(K,hex(SL[0x7e1f50][K]),P.RAW[P.r2o(SL[0x7e1f50][K]):P.r2o(SL[0x7e1f50][K])+3].hex()))
# 反控：K=0x28
hit2=collections.Counter()
for v,i,mdv,name in rows:
    fam=FAM[COL[VT[v]]['pCHD']]; zero=[x for x in fam if COL[VT[x]]['md_']==0]
    if not zero: continue
    s=SL[zero[0]]; hit2[s[0x28//4] if len(s)>10 else None]+=1
print('[反控] 改用 slot10 落点分布:',{(hex(k) if k else None):n for k,n in hit2.most_common(5)})
json.dump(dict(n=len(rows),tables=len({r[0] for r in rows}),slot=dict(collections.Counter(r[1] for r in rows)),
  mdisp=dict(collections.Counter(r[2] for r in rows)),tgt={str(k):v for k,v in hit.items()}),open('_r217/m7.json','w'),indent=1)
