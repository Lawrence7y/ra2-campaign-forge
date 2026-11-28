#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 C：把「同组」从「同 COL 修饰名」改成「同接口层身份」后，直接槽的不匹配现象有什么性质。
C1 每个 COL 的层基类身份：pCHD 基类数组里 PMD.mdisp == COL.mdisp 的 BCD，多条时取 ncb 最大（最外层）。
C2 这张表所在层的基类名 = 该 BCD 的 pTD 名字。954 条 mdisp==0 表由首条 BCD 自证。
C3 535 个可比对对：两边层基类名相同 vs 不同。
C4 全镜像 (层基类名, mdisp, 槽号) 键：多少个键有 >=2 宿主、键内一致率、众数覆盖率。
C5 四档 172/176/240/248 与 260 条非零 mdisp 表的判别量（层 BCD 条数分布）。
"""
import sys, os, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
grp=collections.defaultdict(list)
for vt in sorted(VT): grp[COL[VT[vt]]['name']].append(vt)
ck('C0 COL=1214 VT=1214 槽=14044 组=954 多表组=94',
   (len(COL),len(VT),sum(NS.values()),len(grp),sum(1 for v in grp.values() if len(v)>1))==(1214,1214,14044,954,94),
   (len(COL),len(VT),sum(NS.values()),len(grp)))
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
ck('C1 TypeDescriptor 988 条', len(TD)==988, len(TD))

def bcds(c):
    return [P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))]
def layer_bcd(colva):
    c=COL[colva]
    m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    if not m: return None
    best=max(m,key=lambda b:P.dw(b+4))
    top=[b for b in m if P.dw(b+4)==P.dw(best+4)]
    return best if len(top)==1 else None
LAY={}
for va in COL:
    LAY[va]=layer_bcd(va)
ck('C2 1214 条 COL 全部解出层 BCD（ncb 最大、无并列）', all(v is not None for v in LAY.values()),
   sum(1 for v in LAY.values() if v is None))
def lname(colva):
    b=LAY[colva]
    return TD.get(P.dw(b),'?') if b else '?'
# mdisp==0 自证：首条 BCD 的 pTD == COL.pTD
selfok=sum(1 for va,c in COL.items() if c['mdisp']==0 and bcds(c)[0] is not None
           and P.dw(bcds(c)[0])==c['ptd'] and P.dw(bcds(c)[0]+8)==0)
ck('C3 mdisp==0 的 954 表首条 BCD 自证（pTD 相同且 mdisp 0）', selfok==954, selfok)
# 非零 mdisp 的层 BCD 候选数分布
dist=collections.Counter(len([b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']])
                         for c in COL.values() if c['mdisp']!=0)
ck('C4 260 条非零 mdisp 表的层 BCD 候选数分布 = {1:159,2:101}', dict(dist)=={1:159,2:101}, dict(dist))

# ---- C3 535 对两层身份 ----
def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04
direct=[]
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp']==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if not is_adj(v): direct.append((vt,k,v))
ck('C5 直接槽 1013', len(direct)==1013, len(direct))
same=0; diff=0; pairs=0; det=collections.Counter()
for vt,k,v in direct:
    nm=COL[VT[vt]]['name']
    sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: continue
    t=sorted(sibs)[0]; pairs+=1
    a=lname(VT[vt]); b=lname(VT[t])
    if a==b: same+=1
    else: diff+=1; det[(a,b)]+=1
ck('C6 可比对对 535', pairs==535, pairs)
ck('C7 535 对里两边层基类名相同 0 / 不同 535', (same,diff)==(0,535), (same,diff))
print('C8 层基类名对 Top8:', det.most_common(8))

# ---- C4 全镜像接口槽键一致性 ----
key=collections.defaultdict(list)
for vt,colva in VT.items():
    ln=lname(colva); m=COL[colva]['mdisp']
    for k in range(NS[vt]):
        key[(ln,m,k)].append((vt,P.dw(vt+4*k)))
ck('C9 键数 12836（层基类名,mdisp,槽号）', len(key)==12836, len(key))
multi={k:v for k,v in key.items() if len(v)>1}
ck('C10 有 >=2 宿主的键 67 个 / 覆盖槽实例 1275', (len(multi),sum(len(v) for v in multi.values()))==(67,1275),
   (len(multi),sum(len(v) for v in multi.values())))
cons=sum(1 for k,v in multi.items() if len({x for _,x in v})==1)
ck('C11 键内完全一致的键 6 个 / 不一致 61 个', (cons,len(multi)-cons)==(6,61), (cons,len(multi)-cons))
mod=sum(collections.Counter([x for _,x in v]).most_common(1)[0][1] for v in multi.values())
tot=sum(len(v) for v in multi.values())
ck('C12 众数覆盖率 1037/1275 = 81.33%', mod==1037 and tot==1275, (mod,tot))
uniq_inst=sum(NS.values())-tot
ck('C13 独占槽实例 12769（14044-1275）', uniq_inst==12769, uniq_inst)

json.dump(dict(pairs=pairs,same=same,diff=diff,keys=len(key),multi=len(multi),
               multi_inst=tot,cons=cons,modal=mod,uniq=uniq_inst,
               laypairs=[[list(k),c] for k,c in det.most_common(20)]),
          open('/home/t628/projects/ra2-campaign-forge/_r192/r192c.json','w'), indent=1)
print('断言 %d 条，FAIL %d 条'%(N,len(fails)))
sys.exit(1 if fails else 0)
