# -*- coding: utf-8 -*-
"""R211 d1（§2.12 规则 D 复算 #542）：逐条复算审计员的 12 条断言 + 两个口径澄清。
特别核实 #542 说明①：0x802a18 到底是 CHD 键还是 COL 地址。
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
own={a:[COL[c] for c in G[a] if c==a+16][0] for a in CHD}
TDOWN=set(v['pTD'] for v in own.values())
Vall={a:set(COL[c]['mdisp'] for c in G[a])-{0} for a in CHD}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
ALLR={a:[rec(b) for b in BCA[a]] for a in CHD}
NA=0;fails=[]
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
print('=== #542 G1 口径复算 ===')
nz_bca=sum(1 for a in CHD for r in ALLR[a] if r['mdisp']!=0)
nz_col=sum(1 for v in COL.values() if v['mdisp']!=0)
ck('G1a COL=1214',len(COL)==1214,len(COL))
ck('G1b CHD=954',len(CHD)==954,len(CHD))
ck('G1c BCA 记录=2615',sum(len(v) for v in ALLR.values())==2615,sum(len(v) for v in ALLR.values()))
ck('G1d BCA 非零 mdisp=387',nz_bca==387,nz_bca)
ck('G1e COL 自身非零 mdisp=260（#542 补充口径）',nz_col==260,nz_col)
ck('G1f own COL=954',len(own)==954,len(own))
print('\n=== G2/G3 律 W 与等价式 ===')
def W(a): return set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and (tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN))
def W2(a): return set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and (not tdn(r['pTD']).startswith('.?AV') or r['pTD'] in TDOWN))
ck('G2 律 W 失配 0',sum(1 for a in CHD if W(a)!=Vall[a])==0,sum(1 for a in CHD if W(a)!=Vall[a]))
ck('G3 等价式 失配 0',sum(1 for a in CHD if W2(a)!=Vall[a])==0,sum(1 for a in CHD if W2(a)!=Vall[a]))
print('\n=== G4-G7 反控 ===')
def cnt(f): return sum(1 for a in CHD if set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and f(r))!=Vall[a])
ck('G4 C0 无过滤 = 15',cnt(lambda r:True)==15,cnt(lambda r:True))
ck('G5 C4 仅 TOOWN = 91',cnt(lambda r:r['pTD'] in TDOWN)==91,cnt(lambda r:r['pTD'] in TDOWN))
ck('G6 C5 仅 ?AU = 81',cnt(lambda r:tdn(r['pTD']).startswith('.?AU'))==81,cnt(lambda r:tdn(r['pTD']).startswith('.?AU')))
uni=set(r['mdisp'] for a in CHD for r in ALLR[a] if r['mdisp']!=0)
ck('G7 C1 并集成立类数 0',sum(1 for a in CHD if Vall[a]==uni)==0,sum(1 for a in CHD if Vall[a]==uni))
ck('G7b 并集大小 = 13（#542 数）',len(uni)==13,len(uni))
print('\n=== G8 排除集 ===')
exc=set();n_exc=0
for a in CHD:
    for r in ALLR[a]:
        if r['mdisp']!=0 and not(tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN):
            exc.add(r['pTD']); n_exc+=1
ck('G8a 排除记录 26 条',n_exc==26,n_exc)
ck('G8b 排除 pTD 5 个',len(exc)==5,len(exc))
EXP={0x817ab8:'.?AVStageClass@@',0x817ad8:'.?AVFlasherClass@@',0x845e30:'.?AVBounceClass@@',
     0x84a838:'.?AVCComObjectRootBase@ATL@@',0x84a860:'.?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@'}
ck('G8c 5 个 pTD 地址与名逐一吻合',exc==set(EXP) and all(tdn(k)==v for k,v in EXP.items()),
   {hex(k):tdn(k) for k in sorted(exc)})
REF=set(v['pTD'] for v in COL.values())
ck('G8d 5 个全 onlysec（无 COL 引用）',all(e not in REF for e in exc),all(e not in REF for e in exc))
print('\n=== G9 8 类第二记录 ===')
EIGHT={0x802a18:'House',0x7fb4b0:'Aircraft',0x7ffea0:'Drive',0x800098:'DropPod',
       0x804ce0:'Jumpjet',0x8093f8:'Ship',0x80c1d0:'Teleport',0x80d298:'Walk'}
ok9=True
for a,tag in EIGHT.items():
    r4=[tdn(r['pTD']) for r in ALLR[a] if r['mdisp']==4]
    exp='.?AUIRTTITypeInfo@@' if tag in ('House','Aircraft') else '.?AUILocomotion@@'
    hasu=any(x=='.?AUIUnknown@@' for x in r4)
    ok9 = ok9 and (exp in r4) and hasu and len(r4)==2
    print('   %-8s %#x  4记录=%s'%(tag,a,r4))
ck('G9 8 类第二记录身份 + IUnknown 伴随',ok9,True)
print('\n=== G10 分组 ===')
grp=collections.Counter()
for a in CHD:
    r4=[r for r in ALLR[a] if r['mdisp']==4]
    if r4: grp[tuple(sorted(tdn(r['pTD']) for r in r4))]+=1
ck('G10 96 类四组 78/12/5/1',sum(grp.values())==96 and sorted(grp.values(),reverse=True)==[78,12,5,1],dict(('%s'%(' + '.join(k),),v) for k,v in grp.items()))
print('\n=== G11 4∈V / 4∈B ===')
ck('G11a 4∈V=91',sum(1 for a in CHD if 4 in Vall[a])==91,sum(1 for a in CHD if 4 in Vall[a]))
ck('G11b 4∈B=96',sum(1 for a in CHD if any(r['mdisp']==4 for r in ALLR[a]))==96,sum(1 for a in CHD if any(r['mdisp']==4 for r in ALLR[a])))
A4b={a for a in CHD if any(r['mdisp']==4 for r in ALLR[a])}; A4v={a for a in CHD if 4 in Vall[a]}
ATL={0x80e680,0x80e740,0x80e780,0x80e7c0,0x80e998}
ck('G11c B−V 恰 5 个 ATL EventSink 且 V 空',(A4b-A4v)==ATL and all(Vall[a]==set() for a in ATL),sorted(hex(x) for x in A4b-A4v))
print('\n=== G12 + #542 说明① 口径核实 ===')
ck('G12 House V=[4,8,12,36,40,44]',sorted(Vall[0x802a18])==[4,8,12,36,40,44],sorted(Vall[0x802a18]))
ck('备注 0x802a18 是 CHD 键而非 COL 地址',0x802a18 in CHD and 0x802a18 not in COL,
   'in CHD=%s in COL=%s'%(0x802a18 in CHD,0x802a18 in COL))
ck('备注 本类 own COL = 0x802a28',0x802a28 in COL and COL[0x802a28]['pCHD']==0x802a18,
   'sig/name=%s'%('ok' if 0x802a28 in COL else 'missing'))
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
json.dump({'asserts':NA,'fails':fails,'nz_bca':nz_bca,'nz_col':nz_col,'uni':sorted(uni),
 'exc':[hex(x) for x in sorted(exc)],'chd_key':0x802a18,'own_col':0x802a28},
 open('/home/t628/projects/ra2-campaign-forge/_r211/d1.json','w'),indent=1)
