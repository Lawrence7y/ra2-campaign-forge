# -*- coding: utf-8 -*-
"""R211 c15：独立源复核（正确口径）。
COL 记录只有 1 条/视图，其 mdisp 就是视图偏移 ⇒ 用 COL 记录的 (pCHD → mdisp 多重集) 重建 V，
再与 q3 的 vftable-scan 结果比对；另核 CHD 数量与 COL 记录数。
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
print('COL 记录 %d ; CHD %d'%(len(COL),len(CHD)))
# 每 CHD 的 COL 记录 mdisp 集合
Vc={a:set(COL[c]['mdisp'] for c in G[a]) for a in CHD}
empty=[a for a in CHD if not (Vc[a]-{0})]
print('COL 侧非零 mdisp 为空的 CHD = %d'%len(empty))
# q3 侧
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
Vq={a:set(VS[a].keys()) for a in d3 and VS}
print('q3 侧 CHD %d ; 非零集合为空 %d'%(len(VS),sum(1 for a in VS if not (Vq[a]-{0}))))
# 比对：q3 的 V（含0）与 COL 的 mdisp 集合
mis=[(hex(a),sorted(Vq[a]),sorted(Vc[a])) for a in sorted(VS) if Vq[a]!=Vc[a]]
print('两源视图偏移集合（含 0）逐类比对：失配 %d / %d'%(len(mis),len(VS)))
for m in mis[:10]: print('   %s q3=%s col=%s'%m)
# 若失配，找出原因：q3 的 view 列表首元素是否恒 0
nz0=dict(collections.Counter(sorted(VS[a])[0] for a in VS))
print('q3 每类最小偏移分布：%s'%nz0)
json.dump({'col':len(COL),'chd':len(CHD),'mismatch':len(mis),'mis':mis[:20],
  'empty_col':len(empty),'min_off':{str(k):v for k,v in nz0.items()}},
  open('/home/t628/projects/ra2-campaign-forge/_r211/c15.json','w'),indent=1)
