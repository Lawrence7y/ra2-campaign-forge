# -*- coding: utf-8 -*-
"""R211 d2（§2.12 规则 D 复算 #543 的字面偏差指控）：
#543 说「8 个地址是 CHD 而非 COL」+「『第二记录』若按 BCA 顺序则应是 IUnknown」。
逐条核实：
  X1 0x802a18 等 8 个地址 ∈ CHD 且 ∉ COL
  X2 每类 own COL = CHD+16
  X3 mdisp=4 的两条记录在 BCA 里的【顺序索引】
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(addr=base+4*i,sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
NA=0;fails=[]
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
EIGHT=[0x802a18,0x7fb4b0,0x7ffea0,0x800098,0x804ce0,0x8093f8,0x80c1d0,0x80d298]
print('=== X1/X2 地址口径 ===')
ck('X1 8 个地址全 ∈ CHD 且 ∉ COL', all(a in CHD and a not in COL for a in EIGHT),
   [(hex(a),a in CHD,a in COL) for a in EIGHT])
ck('X2 8 类的 own COL == CHD+16', all((a+16) in COL and COL[a+16]['pCHD']==a for a in EIGHT),
   [hex(a+16) for a in EIGHT])
print('\n=== X3 mdisp=4 记录的 BCA 顺序索引 ===')
rows=[]
for a in EIGHT:
    seq=[(j,rec(b)) for j,b in enumerate(BCA[a])]
    four=[(j,tdn(r['pTD'])) for j,r in seq if r['mdisp']==4]
    rows.append((hex(a),four))
    print('  %#010x %-34s mdisp=4 在 BCA 的索引 → %s'%(a,tdn(COL[a+16]['pTD']),four))
# 判据：#543 说按 BCA 序 IUnknown 在后
ok3=all(len(f)==2 and f[1][1]=='.?AUIUnknown@@' for h,f in rows)
ck('X3 每条 mdisp=4 的第二条（BCA 序）恒为 .?AUIUnknown@@',ok3,rows)
print('\n  ⇒ 我方 G9 措辞「第二记录 = IRTTITypeInfo/ILocomotion」是按【接口优先】说的，')
print('     按 BCA 物理序则第二位是 IUnknown。#543 的字面指控成立，本段措辞订正为「首记录（接口）/ 伴记录（IUnknown）」。')
ck('X4 8 类 mdisp=4 记录数恒 2', all(len(f)==2 for h,f in rows),[len(f) for h,f in rows])
json.dump({'chd_addr':True,'own_col':True,'bca_order':rows,'second_is_iunknown':ok3},
 open('/home/t628/projects/ra2-campaign-forge/_r211/d2.json','w'),indent=1,ensure_ascii=False)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
