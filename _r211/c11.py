# -*- coding: utf-8 -*-
"""R211 c11：律 W 定稿验证（954 类逐类）+ HouseClass mdisp=4 记录身份 + 【4】独立附加项成因。
律 W：V(c) == { mdisp(r) : r ∈ BCA(c), mdisp≠0, pTD(r)∈INTERFACE ∪ TD_OWN }
      INTERFACE = pTD 名为 .?AU 前缀
反控：
  R1 去掉 pTD 过滤 ⇒ 失配 15
  R2 把条件换成 pTD∈TD_OWN only ⇒ 失配 91
  R3 把条件换成 .?AU only ⇒ 失配 159
  R4 随机 shuffle 类-视图配对 ⇒ 0 成立
附：8 个【4】独立附加项类的 mdisp=4 记录逐条（pTD 名 / nc / pdisp / vdisp / attr）
"""
import sys,struct,collections,json,random
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
TDOWN=set(v['pTD'] for v in own.values())
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a].keys())-{0} for a in VS}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(a=b,pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
ALLR={a:[rec(b) for b in BCA[a]] for a in CHD}
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def nmof(a): return NM.get(VS[a][0],'?') if a in VS and 0 in VS[a] else own[a]['name']
def test(f,label,show=0):
    bad=[]
    for a in sorted(V):
        s=set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and f(r))
        if s!=V[a]: bad.append((nmof(a),hex(a),sorted(V[a]),sorted(s)))
    ck(label,len(bad)==0,'失配 %d / 954'%len(bad))
    for x in bad[:show]: print('     %-32s %s V=%s S=%s'%x)
    return bad
cands={
 'BASE 无过滤（全部非零 mdisp）': lambda r: True,
 'U1 仅 pTD∈TD_OWN': lambda r: r['pTD'] in TDOWN,
 'U2 仅 .?AU 前缀': lambda r: tdn(r['pTD']).startswith('.?AU'),
 'W  律 W：.?AU ∨ TD_OWN': lambda r: tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN,
 'W2 等价式 ¬.?AV ∨ TD_OWN': lambda r: not tdn(r['pTD']).startswith('.?AV') or r['pTD'] in TDOWN,
 'W3 .?AU ∨ (tdown ∧ pdisp==-1)': lambda r: tdn(r['pTD']).startswith('.?AU') or (r['pTD'] in TDOWN and r['pdisp']==-1),
}
print('=== 954 类逐类检验 ===')
for k,f in cands.items(): test(f,k,show=4 if k.startswith('W') else 0)
# R4 随机配对反控
random.seed(211)
keys=sorted(V); perm=keys[:]; random.shuffle(perm)
ok=sum(1 for a,b in zip(keys,perm) if V[a]=={r['mdisp'] for r in ALLR[b] if r['mdisp']!=0 and (tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN)})
ck('R4 反控：类-视图随机错配', ok==0, '碰巧成立 %d / 954'%ok)
# 8 类 mdisp=4 记录身份
EIGHT=[0x802a18,0x7fb4b0,0x7ffea0,0x800098,0x804ce0,0x8093f8,0x80c1d0,0x80d298]
print('\n=== 8 个【4】独立附加项类：BCA 中 mdisp=4 的记录逐条 ===')
out8={}
for a in EIGHT:
    rs=[r for r in ALLR[a] if r['mdisp']==4]
    out8[hex(a)]={'name':nmof(a),'n4':len(rs),'recs':[{'pTD':hex(r['pTD']),'tdname':tdn(r['pTD']),'nc':r['nc'],'pdisp':r['pdisp'],'vdisp':r['vdisp'],'attr':hex(r['attr'])} for r in rs]}
    print('  %-36s V=%-28s mdisp=4 记录 %d 条'%(nmof(a),str(sorted(V[a])),len(rs)))
    for r in rs: print('      pTD=%#010x %-32s nc=%d pdisp=%d vdisp=%d attr=%#x'%(r['pTD'],tdn(r['pTD']),r['nc'],r['pdisp'],r['vdisp'],r['attr']))
# HouseClass 全 BCA
print('\n=== HouseClass(0x802a18) 全 BCA 记录 ===')
for r in ALLR[0x802a18]:
    print('   mdisp=%-6d pTD=%#010x %-32s nc=%-3d pdisp=%-3d vdisp=%-2d attr=%#x'%(r['mdisp'],r['pTD'],tdn(r['pTD']),r['nc'],r['pdisp'],r['vdisp'],r['attr']))
# 5 个被排除的 pTD 全局统计
EXC=set()
for a in V:
    for r in ALLR[a]:
        if r['mdisp']!=0 and not (tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN): EXC.add(r['pTD'])
print('\n=== 被排除的 pTD（%d 个）==='%len(EXC))
for t in sorted(EXC):
    n=sum(1 for a in V for r in ALLR[a] if r['pTD']==t)
    inown=t in TDOWN
    print('   %#010x %-46s BCD 记录 %d 条 ; ∈TD_OWN=%s ; pTD 有 vftable?=%s'%(t,tdn(t),n,inown, P.dw(t+12)!=0))
json.dump({'perfect':'律 W（.?AU ∨ TD_OWN）','eight':out8,
  'excluded_ptd':{hex(t):tdn(t) for t in sorted(EXC)},
  'classes':len(V),'records':sum(len(v) for v in ALLR.values())},
  open('/home/t628/projects/ra2-campaign-forge/_r211/c11.json','w'),indent=1)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
