# -*- coding: utf-8 -*-
"""R217 m3：律V —— 类主视图 slot0（QueryInterface）写出的子对象偏移，必须落在
{0} ∪ {该类 mdisp!=0 子视图的 mdisp 集合} 内。
构造：按 pCHD 分组视图（同 CHD = 同一继承层级的视图族 = 同一"类"的 MI 视图）。
正控：AbstractClass 组 mdisp 集合应为 {0,4,8,12}，QI 写出偏移只能是 0 与 4，且 4 在集合内。
反控：把判据改成「偏移 ∈ 全局 mdisp 集合」时，应出现违例（说明类内约束更强）。
"""
import sys,struct,collections,json,re
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
# 组：同 pCHD
G=collections.defaultdict(list)
for v,col in VT.items(): G[COL[col]['pCHD']].append(v)
MULTI={g:vs for g,vs in G.items() if len({COL[VT[v]]['md_'] for v in vs})>1}
print('[组] 视图族总数=%d  含多 mdisp 的族=%d'%(len(G),len(MULTI)))
GLOBAL_MD={COL[c]['md_'] for c in COL}
# 主视图 = 该族 mdisp==0 的视图
def qi_offsets(fnva,limit=0x400):
    offs=set(); imm=set()
    o=P.r2o(fnva); code=P.RAW[o:o+limit]
    for ins in md.disasm_lite(code,fnva):
        addr,size,mnem,ops=ins
        if mnem=='ret': break
        if mnem=='lea':
            m=re.search(r'\+ (0x[0-9a-f]+)',ops)
            if m: offs.add(int(m.group(1),16))
        if mnem=='add':
            m=re.search(r', (0x[0-9a-f]+)',ops)
            if m and 'esp' not in ops: offs.add(int(m.group(1),16))
    return offs
rows=[]; ok=bad=0; badrows=[]
for g,vs in sorted(G.items()):
    zero=[v for v in vs if COL[VT[v]]['md_']==0]
    if not zero: continue
    mdset={COL[VT[v]]['md_'] for v in vs}
    prim=zero[0]
    if not SL[prim]: continue
    qifn=SL[prim][0]
    offs=qi_offsets(qifn)
    if not offs: continue
    allowed={0}|mdset
    extra=offs-allowed
    rows.append(dict(cls=COL[VT[prim]]['name'],vt=hex(prim),qifn=hex(qifn),mdset=sorted(mdset),offs=sorted(hex(x) for x in offs),extra=sorted(hex(x) for x in extra)))
    if extra: bad+=1; badrows.append(rows[-1])
    else: ok+=1
print('[律V] 可测类=%d 成立=%d 违例=%d'%(len(rows),ok,bad))
for b in badrows[:12]: print('   VIOL',b['cls'],'mdset',b['mdset'],'offs',b['offs'],'extra',b['extra'])
print('   正控 AbstractClass:',[r for r in rows if 'AbstractClass' in r['cls']])
# 反控：全局 mdisp 判据下的违例数
bad2=sum(1 for r in rows if {int(x,16) for x in r['offs']}-(GLOBAL_MD|{0}))
print('[反控V] 若判据改为全局 mdisp 集合，违例=%d（应 > 类内违例数 %d）'%(bad2,bad))
json.dump(dict(groups=len(G),multi=len(MULTI),measurable=len(rows),ok=ok,bad=bad,badrows=badrows[:20],alt_bad=bad2),open('_r217/m3.json','w'),indent=1)
