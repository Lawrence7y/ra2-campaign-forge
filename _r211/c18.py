# -*- coding: utf-8 -*-
"""R211 c18：律 W 的排除集 5 个 pTD 与 R207「13 个 onlysec pTD」的关系。
onlysec pTD 定义：type descriptor 位于 .data 且没有任何 COL 记录引用它（即没有类的表头）。
一次输出：全部 type descriptor 数 / 被 COL 引用的 / 未被引用的（onlysec）；
          5 个被排除 pTD 是否 are onlysec；以及它们各自的 BCD 记录数与引用它们的类数。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
# 枚举全部 type descriptor：.data 里 形如 vftable_ptr + 0 + name 的结构
# R206 已证 TD 布局：+0 pVFTable, +4 spare(0), +8 name
TD={}
for sn in ('.data','.rdata'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-2):
        if w[i+1]!=0: continue
        nm=P.cstr(base+4*i+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        TD[base+4*i+8-8]=dict(addr=base+4*i,name=nm.decode('latin1'),vf=w[i])
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
REF=collections.Counter(v['pTD'] for v in COL.values())
# BCD 中引用
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
BCREF=collections.Counter(rec(b)['pTD'] for a in CHD for b in BCA[a])
print('TD 总数(含 .?A 名)=%d ; COL 引用的 pTD 数=%d'%(len(TD),len(REF)))
print('TD 中名以 .?AU 开头的=%d ; .?AV 开头=%d'%(
  sum(1 for v in TD.values() if v['name'].startswith('.?AU')),
  sum(1 for v in TD.values() if v['name'].startswith('.?AV'))))
only=[a for a in TD if a not in REF]
print('\n【未被任何 COL 引用】的 TD（onlysec 口径）= %d 个：'%len(only))
for a in sorted(only):
    print('   %#010x %-58s 被 BCA 引用 %d 次'%(a,TD[a]['name'],BCREF.get(a,0)))
EXC=[0x817ab8,0x817ad8,0x845e30,0x84a838,0x84a860]
print('\n律 W 的 5 个排除 pTD 是否 onlysec：')
for e in EXC:
    print('   %#010x %-52s onlysec=%-5s BCA引用=%d COL引用=%d'%(e,TD[e]['name'],e not in REF,BCREF.get(e,0),REF.get(e,0)))
json.dump({'td_total':len(TD),'col_ref_ptd':len(REF),
  'onlysec':[{'addr':hex(a),'name':TD[a]['name'],'bcd_ref':BCREF.get(a,0)} for a in sorted(only)],
  'onlysec_count':len(only),
  'excluded':[{'addr':hex(e),'name':TD[e]['name'],'onlysec':e not in REF,'bcd':BCREF.get(e,0)} for e in EXC]},
  open('/home/t628/projects/ra2-campaign-forge/_r211/c18.json','w'),indent=1,ensure_ascii=False)
