# -*- coding: utf-8 -*-
"""R211 c14：独立性复核 —— 视图集合完全从 COL 记录重建（不用 q3.json 的 view 列表），
再与 q3.json 的 V 对照，并用独立源重算律 W 全部三个数字。
另测：BCA 记录的 mdisp 是否与「同 pTD 的 COL 记录 mdisp」一致（跨源一致性）。
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
# 独立视图集合：同一 CHD 下全部 COL 记录的 mdisp（含 own 的 0），按 CHD 计
Vind={a:set(COL[c]['mdisp'] for c in G[a]) for a in CHD}
Vind_nz={a:sorted(x for x in Vind[a] if x!=0) for a in CHD}
own={}
for a in CHD:
    for c in G[a]:
        if c==a+16: own[a]=COL[c]
TDOWN=set(v['pTD'] for v in own.values())
# q3 侧
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
Vq={a:set(VS[a].keys())-{0} for a in VS}
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
ck('E0 CHD 集合一致', set(Vq)==set(CHD), '%d vs %d'%(len(Vq),len(CHD)))
mis=[(hex(a),sorted(Vq[a]),sorted(Vind_nz[a])) for a in sorted(Vq) if Vq[a]!=Vind_nz[a]]
ck('E1 两独立源的视图偏移集合逐类相同（q3 槽扫描 vs COL 记录）', len(mis)==0,'失配 %d'%len(mis))
for m in mis[:6]: print('    %s q3=%s col=%s'%m)
# 独立源重算律 W
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
ALLR={a:[rec(b) for b in BCA[a]] for a in CHD}
bad=[]
for a in CHD:
    s=set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and (tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN))
    if s!=Vind_nz[a]: bad.append((hex(a),sorted(Vind_nz[a]),sorted(s)))
ck('E2 律 W 用 COL 源视图集合重算 954/954', len(bad)==0,'失配 %d'%len(bad))
for x in bad[:6]: print('    %s Vcol=%s W=%s'%x)
# 跨源一致性：BCA 记录 (pTD,mdisp) 是否在同 CHD 的某条 COL 记录里出现
stat=collections.Counter(); ex=[]
for a in CHD:
    paircol=set((COL[c]['pTD'],COL[c]['mdisp']) for c in G[a])
    for r in ALLR[a]:
        if r['mdisp']==0: continue
        if (r['pTD'],r['mdisp']) in paircol: stat['hit']+=1
        else:
            stat['miss']+=1; ex.append((hex(a),hex(r['pTD']),r['mdisp'],tdn(r['pTD'])))
print('   BCA 非零记录与 COL(pTD,mdisp) 对：%s'%dict(stat))
for e in ex[:10]: print('     MISS cls=%s pTD=%s(mdisp=%d) %s'%e)
# 记录级样本数复核
rows=[r for a in CHD for r in ALLR[a] if r['mdisp']!=0]
L0=[r for a in CHD for r in ALLR[a] if r['mdisp']!=0 and r['mdisp'] not in Vind_nz[a]]
print('\n  非零记录 %d ; L=0 %d ; classes %d ; CHD %d ; COL %d'%(len(rows),len(L0),len(CHD),len(CHD),len(COL)))
json.dump({'classes':len(CHD),'nz_records':len(rows),'L0':len(L0),'col_records':len(COL),
  'e1_mismatch':len(mis),'e2_mismatch':len(bad),'pair':dict(stat),'ex':ex[:20],
  'independent':True},open('/home/t628/projects/ra2-campaign-forge/_r211/c14.json','w'),indent=1)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
