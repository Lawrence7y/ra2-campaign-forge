# -*- coding: utf-8 -*-
"""R211 c7：律 W 的方向性 + PMD 语义检验。
MSVC RTTI BCD 24B = {pTD, numContainedBases, PMD{mdisp,pdisp,vdisp}, attributes}。
PMD 语义：pdisp == -1 ⇒ 非虚基，位移 = mdisp；pdisp != -1 ⇒ 虚基，(pdisp,vdisp) 描述 vbtable。
检验：
  L1  V(c) ⊆ nonzero{mdisp}   954/954 ？
  L2  V(c) == nonzero{mdisp : pdisp == -1} ？
  L3  extras = B\V 的记录 pdisp 是否恒 != -1（虚基）？
  L4  反向：B\V 非空的类里，extras 的 mdisp 是否出现在「本类或基类的其它视图」？
一次输出全部 15 类的逐记录 (nc,pdisp,vdisp,attr)，并给全局 pdisp 分布。
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
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a].keys())-{0} for a in VS}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(a=b,pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
allr=[rec(b) for a in CHD for b in BCA[a]]
print('BCA 记录总数=%d'%len(allr))
for k in ('nc','pdisp','vdisp','attr'):
    print('  %-6s 分布 %s'%(k,collections.Counter(r[k] for r in allr).most_common(8)))
nz=[r for r in allr if r['mdisp']!=0]
print('  非零 mdisp 记录=%d 其中 pdisp!=-1 的=%d'%(len(nz),sum(1 for r in nz if r['pdisp']!=-1)))
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
# L1 包含关系
notsub=[(NM.get(VS[a][0],'?'),hex(a),sorted(V[a]),sorted(set(r['mdisp'] for r in (rec(b) for b in BCA[a]) if r['mdisp']))) for a in sorted(V) if not V[a] <= set(r['mdisp'] for r in (rec(b) for b in BCA[a]) if r['mdisp'])]
ck('L1 V(c) ⊆ nonzero{mdisp of BCA}', len(notsub)==0, '不满足 %d 类'%len(notsub))
for x in notsub[:8]: print('    NOT-SUBSET %-30s %s V=%s B=%s'%x)
# L2 pdisp==-1 过滤
def sel(f):
    bad=[]
    for a in sorted(V):
        s=set(r['mdisp'] for r in (rec(b) for b in BCA[a]) if r['mdisp']!=0 and f(r))
        if s!=V[a]: bad.append((NM.get(VS[a][0],'?') if a in VS else own[a]['name'],hex(a),sorted(V[a]),sorted(s)))
    return bad
for nm_,f in [('L2 pdisp==-1', lambda r:r['pdisp']==-1),
              ('L2b pdisp==-1 ∧ nc>=-1', lambda r:r['pdisp']==-1 and r['nc']>=-1),
              ('L2c pdisp==-1 ∧ vdisp>=0', lambda r:r['pdisp']==-1 and r['vdisp']>=0)]:
    b=sel(f); ck('%s 时 V 逐类相等'%nm_, len(b)==0, '失配 %d'%len(b))
    for x in b[:6]: print('     %-30s %s V=%s S=%s'%x)
# extras 结构
print('\n=== extras（B 中不在 V 的 mdisp）逐条 ===')
tot=0
for a in sorted(V):
    rs=[rec(b) for b in BCA[a]]
    ex=[r for r in rs if r['mdisp']!=0 and r['mdisp'] not in V[a]]
    if ex:
        print('%s %s'%(hex(a),NM.get(VS[a][0],'?') if a in VS else own[a]['name']))
        for r in ex:
            tot+=1
            print('    extra mdisp=%-6d BCD=%#010x pTD=%#010x nc=%d pdisp=%d vdisp=%d attr=%#x'%(r['mdisp'],r['a'],r['pTD'],r['nc'],r['pdisp'],r['vdisp'],r['attr']))
print('extras 总数=%d'%tot)
json.dump({'extras_total':tot,'in_subset':len(notsub),
           'dist':{k:collections.Counter(r[k] for r in allr).most_common(10) for k in ('nc','pdisp','vdisp','attr')},
           'records':len(allr)},
          open('/home/t628/projects/ra2-campaign-forge/_r211/c7.json','w'),indent=1)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
