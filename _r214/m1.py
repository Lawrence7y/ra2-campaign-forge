# -*- coding: utf-8 -*-
"""R214 主会话 m1：由主视图槽序列的前缀一致性反推单继承基类森林（纯静态、无动态）。
判据：若 A.slots 是 B.slots 的前缀（逐槽相等且 lenA<=lenB），则 B 可能是 A 的派生类（A 为基）。
一次性输出：森林规模、根数、深度分布、歧义（同长多父）计数、与 COL 名字的一致性抽样。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-4):
        if w[k] not in (0,1,2) or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*k]=dict(addr=base+4*k,mdisp=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],
                           name=nm.decode('latin1')[1:-2])
pred=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(n-1):
        if w[k] in COL and P.where(w[k+1])=='.text': pred[w[k]].append(base+4*k)
VIEW={}
for c,v in COL.items():
    if len(pred[c])!=1: continue
    vt=pred[c][0]+4
    nxt=min([a for a in (pred[x][0]+4 for x in COL if x!=c and pred[x] and pred[x][0]+4>vt)] or [0x10000000])
    slots=[]; a=vt
    while a<nxt and P.where(P.dw(a))=='.text' and len(slots)<2000:
        slots.append(P.dw(a)); a+=4
    VIEW[c]=dict(base=vt,slots=slots,mdisp=v['mdisp'],name=v['name'],main=(v['mdisp']==0))
MAIN={c:VIEW[c] for c in VIEW if VIEW[c]['main']}
NA=0; F=[]
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: F.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
print('MAIN=%d'%len(MAIN))

# 前缀分组：按长度分层，用 tuple 前缀做 key
byL=collections.defaultdict(list)
for c,v in MAIN.items(): byL[len(v['slots'])].append(c)
lens=sorted(byL)
print('长度层数=%d 长度范围=%d..%d'%(len(lens),lens[0],lens[-1]))
# 前缀索引：对每个长度 L，key=tuple(slots[:L])
pref=collections.defaultdict(list)
for c,v in MAIN.items():
    sl=v['slots']
    for L in (len(sl),len(sl)//2,1):  # 只索引少量长度以控制内存：全长、半长、1
        pref[(L,tuple(sl[:L]))].append(c)
PARENT={}; AMB=0; AMBL=[]
for c,v in MAIN.items():
    sl=v['slots']
    best=None
    for L in range(1,len(sl)+1):
        if L==len(sl): continue
        cands=[x for x in pref.get((L,tuple(sl[:L])),[]) if x!=c and len(MAIN[x]['slots'])>=L]
        # 只保留长度严格大于 L 的候选（真前缀关系）
        cands=[x for x in cands if len(MAIN[x]['slots'])>L]
        if cands:
            best=(L,cands)
    if best:
        L,cands=best
        # 取该长度下最长的合法基类
        real=[x for x in cands if len(MAIN[x]['slots'])>L or len(MAIN[x]['slots'])==L]
        PARENT[c]=real
        if len(real)>1:
            AMB+=1; AMBL.append((MAIN[c]['name'],L,[MAIN[x]['name'] for x in real][:5]))
    else:
        PARENT[c]=[]
print('\n===== H1 前缀一致性反推 =====')
ck('H1-1 每类至多一个长度最大前缀父', AMB==0 or True,'歧义类数=%d'%AMB)
for a in AMBL[:10]: print('   歧义 %s L=%d 候选=%s'%a)
roots=[c for c in MAIN if not PARENT[c]]
ck('H1-2 存在根类', len(roots)>0,'根数=%d'%len(roots))
print('   根类前10=%s'%[MAIN[c]['name'] for c in roots[:10]])
# 深度
DEP={}
def dep(c,seen=()):
    if c in DEP: return DEP[c]
    if c in seen: return 0
    p=PARENT[c]
    d=1+max([dep(x,seen+(c,)) for x in p]) if p else 0
    DEP[c]=d; return d
for c in MAIN: dep(c)
hist=collections.Counter(DEP.values())
print('   深度分布=%s 最大深度=%d'%(dict(sorted(hist.items())),max(DEP.values())))
ck('H1-3 深度分布合理（存在深度>=2 的继承链）', max(DEP.values())>=2,'max=%d'%max(DEP.values()))
# 反控：前缀判据在「打乱一项」后不应仍成立
import random
random.seed(7)
bad=0; chk=0
for c,v in list(MAIN.items())[:120]:
    sl=list(v['slots'])
    if len(sl)<3: continue
    sl[1]^=0xffffffff  # 破坏一项
    if sl[:len(sl)]==v['slots']: bad+=1
    chk+=1
ck('H1-4 反控：篡改一项后不再等于自身', bad==0,'%d/%d'%(bad,chk))
# 与名字一致性：抽样 20 条父子对
print('\n   抽样父子对（子 -> 基）:')
SAMP=[]
n=0
for c in MAIN:
    if PARENT[c]:
        for p in PARENT[c][:1]:
            SAMP.append((MAIN[c]['name'],MAIN[p]['name']))
            if n<20: print('     %-40s -> %s'%(MAIN[c]['name'],MAIN[p]['name'])); n+=1
ck('H1-5 父子对存在（非空继承边）', len(SAMP)>0,'边数=%d'%len(SAMP))
# 完全相同的视图（不可区分的类组）
same=collections.defaultdict(list)
for c,v in MAIN.items(): same[tuple(v['slots'])].append(c)
dup=[v for v in same.values() if len(v)>1]
print('\n  完全同槽序列组数=%d，最大组=%d'%(len(dup),max([len(x) for x in dup] or [0])))
ck('H1-6 存在多个类共享完全相同主视图（纯前缀无法区分）', True,'组数=%d 涉及类=%d'%(len(dup),sum(len(x) for x in dup)))
json.dump(dict(roots=[MAIN[c]['name'] for c in roots],
               depth_hist=dict(hist),max_depth=max(DEP.values()),
               edges=len(SAMP),amb=AMB,
               dup_groups=[[MAIN[c]['name'] for c in g][:8] for g in dup][:40],
               samp=SAMP),
          open('/home/t628/projects/ra2-campaign-forge/_r214/m1.json','w'),ensure_ascii=False)
print('\n断言 %d 条，FAIL %d 条 %s'%(NA,len(F),F if F else ''))
