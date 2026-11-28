# -*- coding: utf-8 -*-
"""R212 d1：§2.12 规则 D —— 主会话亲自复算审计员 #545 的全部新数字。"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def S(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] in (0,1,2) and w[i+2]==0 and P.where(w[i+3])=='.data' and P.where(w[i+4])=='.rdata':
            m=P.cstr(w[i+3]+8,400)
            if m and m.startswith(b'.?A') and m.endswith(b'@@'):
                COL[base+4*i]=dict(mdisp=S(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=m.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={a+16:COL[a+16] for a in CHD if a+16 in COL}
def N(t):
    c=P.cstr(t+8,400) if t else None
    return c.decode('latin1') if c else ''
per=collections.defaultdict(list)
for a in CHD:
    for j,e in enumerate(BCA[a]):
        per[a].append(dict(idx=j,pTD=P.dw(e),nc=P.dw(e+4),mdisp=S(P.dw(e+8)),
                           pdisp=S(P.dw(e+12)),vdisp=P.dw(e+16),attr=P.dw(e+20),addr=e))
POOL=[]
s=P.B['.data']; n=s['rawsize']//4; base=s['lo']
w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
for i in range(n-2):
    if w[i]==0x7f9594:
        nm=P.cstr(base+4*i+8,400)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'):
            POOL.append((base+4*i,nm.decode('latin1')))
print('全 RTTI TD 池 = %d  (.?AV %d / .?AU %d)'%(len(POOL),
  sum(1 for _,x in POOL if x.startswith('.?AV')),sum(1 for _,x in POOL if x.startswith('.?AU'))))
COLPTD={v['pTD'] for v in COL.values()}
POOLPTD={a for a,_ in POOL}
print('COL 引用 distinct pTD = %d ; 其中 .?AU = %d %s'%(len(COLPTD),
  sum(1 for p in COLPTD if N(p).startswith('.?AU')),
  sorted(N(p) for p in COLPTD if N(p).startswith('.?AU'))))
TD_OWN={v['pTD'] for v in own.values()}
print('TD_OWN=%d ; TD_OWN==COLPTD ? %s'%(len(TD_OWN),TD_OWN==COLPTD))
INTERFACE={p for p in POOLPTD if N(p).startswith('.?AU')}
print('INTERFACE(全池口径)=%d'%len(INTERFACE))
NA=0;FAILS=[]
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: FAILS.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
ck('D1 全池 988 = 962 + 26', len(POOL)==988 and sum(1 for _,x in POOL if x.startswith('.?AV'))==962)
ck('D2 COL 引用池 954 == TD_OWN', len(COLPTD)==954 and TD_OWN==COLPTD)
ck('D3 COL 引用池里 .?AU 仅 2 个（INIEntry/INISection）',
   sorted(N(p) for p in COLPTD if N(p).startswith('.?AU'))==['.?AUINIEntry@INIClass@@','.?AUINISection@INIClass@@'])
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a])-{0} for a in VS}
emp=set(a for a in CHD if not V.get(a))
nz=set(a for a in CHD if any(r['mdisp']!=0 for r in per[a]))
print('V 空类 %d / 含非零记录类 %d / 交集 %d / 平凡 %d'%(
  len(emp),len(nz),len(emp&nz),len(CHD)-len(emp|nz)))
ck('D4 V空 860 / 非零 99 / V非空∧非零 94 / V空∧无非零(平凡) 855', len(emp)==860 and len(nz)==99
   and len(nz-set(emp))==94 and len(set(emp)-set(nz))==855,
   (len(emp),len(nz),len(nz-set(emp)),len(set(emp)-set(nz))))
dif=collections.Counter()
for a in CHD:
    r8=[r for r in per[a] if r['mdisp']==8]; r12=[r for r in per[a] if r['mdisp']==12]
    if r8 and r12: dif[r8[0]['addr']-r12[0]['addr']]+=1
ck('D5 b8 - b12 恒 +24（78/78）', dif=={24:78}, dict(dif))
a9=[(a,r) for a in CHD for r in per[a] if r['attr']==9]
print('attr==9 全池 %d 条：%s'%(len(a9),[(N(r['pTD']),r['mdisp'],hex(a)) for a,r in a9]))
ck('D6 attr==9 全局 6 条', len(a9)==6, len(a9))
ck('D7 attr==9 中 3 条 mdisp=21784', sum(1 for a,r in a9 if r['mdisp']==21784)==3)
print('  另 3 条：%s'%sorted((N(r['pTD']),r['mdisp']) for a,r in a9 if r['mdisp']!=21784))
loaded=sorted({N(r['pTD']) for a in CHD for r in per[a] if r['mdisp']!=0 and N(r['pTD']).startswith('.?AU')})
print('实载 .?AU 类型 %d 个：%s'%(len(loaded),loaded))
ck('D8 实载 .?AU 类型 9 个', len(loaded)==9, len(loaded))
excl=sorted(POOLPTD-INTERFACE-TD_OWN)
cnt=collections.Counter()
for a in CHD:
    for r in per[a]:
        if r['pTD'] in set(excl) and r['mdisp']!=0: cnt[r['pTD']]+=1
print('被排除 TD %d 个；被载 %s；零命中 %s'%(len(excl),
  [(N(p),c) for p,c in cnt.items()],[N(p) for p in excl if p not in cnt]))
ck('D9 被排除 10 个中 5 被载 / 5 零命中 / 共 26 条',
   len(excl)==10 and len(cnt)==5 and sum(cnt.values())==26,(len(excl),len(cnt),sum(cnt.values())))
ck('D10 5 个 sink 的 own COL 存在、mdisp=0、视图集 V 为空（仅主视图 mdisp=0）', all(
   (a+16 in COL and COL[a+16]['mdisp']==0 and V.get(a)==set() and 0 in VS.get(a,{}))
   for a in (0x80e680,0x80e740,0x80e780,0x80e7c0,0x80e998)))
print('pdisp 取值集 %s ; vdisp 取值集 %s'%(
  {r['pdisp'] for a in CHD for r in per[a]},{r['vdisp'] for a in CHD for r in per[a]}))
ck('D11 全池 pdisp 恒 -1 且 vdisp 恒 0', all(r['pdisp']==-1 for a in CHD for r in per[a])
   and all(r['vdisp']==0 for a in CHD for r in per[a]))
def mis(S_):
    return sum(1 for a in CHD if set(r['mdisp'] for r in per[a] if r['mdisp']!=0 and r['pTD'] in S_)!=V.get(a,set()))
loaded_set={r['pTD'] for a in CHD for r in per[a] if N(r['pTD']).startswith('.?AU')}
r_pre=sum(1 for a in CHD if set(r['mdisp'] for r in per[a] if r['mdisp']!=0
   and (N(r['pTD']).startswith('.?AU') or r['pTD'] in TD_OWN))!=V.get(a,set()))
print('三写法失配：前缀∪TDOWN=%d / 全池26∪TDOWN=%d / 实载9∪TDOWN=%d'%(
  r_pre,mis(INTERFACE|TD_OWN),mis(loaded_set|TD_OWN)))
print('反控：无过滤=%d / 仅TDOWN=%d / 仅INTERFACE=%d'%(
  mis(set()),mis(TD_OWN),mis(INTERFACE)))
ck('D12 三种 INTERFACE 写法给出相同失配 0',r_pre==0 and mis(INTERFACE|TD_OWN)==0 and mis(loaded_set|TD_OWN)==0)
json.dump(dict(pool=len(POOL),colptd=len(COLPTD),emp=len(emp),nz=len(nz),
  inter=len(emp&nz),trivial=len(CHD)-len(emp|nz),
  bdiff=dict(dif),attr9=len(a9),loaded=loaded,excl=[N(p) for p in excl],
  nassert=NA,fails=FAILS),open('/home/t628/projects/ra2-campaign-forge/_r212/d1.json','w'),indent=1)
print('\n断言 %d / FAIL %d %s'%(NA,len(FAILS),FAILS))
