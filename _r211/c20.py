# -*- coding: utf-8 -*-
"""R211 c20：律 W 的因果方向反控 —— 若 V 真由 BCA 决定，则
  (a) 同一 CHD 的两条 COL 记录不可能有「同 pTD 但不同 mdisp」（pTD→mdisp 函数性）
  (b) BCA 记录的 (pTD,mdisp) 必须能在同 CHD 的 COL 记录里逐一找到（闭环）
  (c) 反向：COL 记录的 mdisp 必须逐条出现在 BCA 里（无幽灵视图）
  (d) 用「本类 CHD 前一条 CHD」的 BCA 去套本类 V ⇒ 应大面积失配（序列错位反控）
以上四条同时成立才说明 W 不是巧合。
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
own={}
for a in CHD:
    for c in G[a]:
        if c==a+16: own[a]=COL[c]
V={a:set(COL[c]['mdisp'] for c in G[a])-{0} for a in CHD}
NM={a:own[a]['name'] for a in CHD}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
ALLR={a:[rec(b) for b in BCA[a]] for a in CHD}
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
# (a) pTD → mdisp 函数性（在 COL 记录层面）
pairs=collections.defaultdict(set)
for v in COL.values(): pairs[v['pTD']].add(v['mdisp'])
multi={k:v for k,v in pairs.items() if len(v)>1}
ck('a1 COL 层面 pTD→mdisp 单值', len(multi)==0, '多值 pTD %d 个'%len(multi))
for k,v in list(multi.items())[:5]: print('     %#x %s → %s'%(k,tdn(k),sorted(v)))
# (b) BCA (pTD,mdisp) 闭环到 COL
miss=[]
for a in CHD:
    cp={(COL[c]['pTD'],COL[c]['mdisp']) for c in G[a]}
    for r in ALLR[a]:
        if r['mdisp']!=0 and (r['pTD'],r['mdisp']) not in cp: miss.append((hex(a),hex(r['pTD']),r['mdisp'],tdn(r['pTD'])))
ck('b1 BCA 非零 (pTD,mdisp) 全在 COL 记录里', len(miss)==0, '缺失 %d / 387'%len(miss))
for m in miss[:8]: print('     MISS %s pTD=%s mdisp=%d %s'%m)
# (c) COL mdisp 全部出现在 BCA
ghost=[]
for a in CHD:
    bs=set(r['mdisp'] for r in ALLR[a])
    for c in G[a]:
        if COL[c]['mdisp'] not in bs: ghost.append((hex(a),hex(COL[c]['mdisp']),hex(COL[c]['pTD'])))
ck('c1 COL 记录的 mdisp 全在 BCA 里（无幽灵视图）', len(ghost)==0, '幽灵 %d / 1214'%len(ghost))
for g_ in ghost[:8]: print('     GHOST cls=%s mdisp=%s pTD=%s'%g_)
# (d) 序列错位反控：用相邻 CHD 的 BCA 套本类
def W_of(a):
    return set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and (tdn(r['pTD']).startswith('.?AU') or r['pTD'] in set(v['pTD'] for v in own.values())))
TDOWN=set(v['pTD'] for v in own.values())
def W_(a): return set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and (tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN))
ok=sum(1 for i,a in enumerate(CHD) if W_(CHD[(i+1)%len(CHD)])==V[a])
ck('d1 相邻 CHD 错位反控', ok==0, '成立 %d / 954'%ok)
ok0=sum(1 for a in CHD if W_(a)==V[a])
ck('W 自洽复算', ok0==954, '成立 %d / 954'%ok0)
print('\n汇总：COL %d / CHD %d / BCA 记录 %d / 非零 %d / 幽灵 %d / 闭环缺失 %d'%(
  len(COL),len(CHD),sum(len(v) for v in ALLR.values()),sum(1 for a in CHD for r in ALLR[a] if r['mdisp']!=0),len(ghost),len(miss)))
json.dump({'col':len(COL),'chd':len(CHD),'bca':sum(len(v) for v in ALLR.values()),
 'nz':sum(1 for a in CHD for r in ALLR[a] if r['mdisp']!=0),'ghost':len(ghost),'miss':len(miss),
 'ptd_multi':len(multi),'shift_ok':ok,'self_ok':ok0},
 open('/home/t628/projects/ra2-campaign-forge/_r211/c20.json','w'),indent=1)
print('断言 %d / FAIL %d'%(NA,len(fails)))
