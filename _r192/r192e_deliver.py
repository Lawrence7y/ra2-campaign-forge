#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 交付定稿：R191 待办(a)「1,013 个非 thunk 直接槽为何同组同序号无匹配」的机械闭合
+ 四个高频实现的接口身份（用结构判据，不猜名）+ 一处口径订正（接口子表键数与单宿主键数
在第一版里按直觉预填 704/637，实测 110/43，本脚本按实测写）。

E1 1013 直接槽五类：NOSIB 478 / DIRECT_OTHER 525 / THUNK_OTHER 10（实测）。
E2 535 个可比对对全部跨层（两边 COL.mdisp 不同 535/535），且两边「层基类身份」也全不同。
E3 跳板归并 1 跳与 8 跳口径 COLLAPSE 均 0 —— 不存在「不同 thunk 壳包同一 impl」。
E4 535 对里 ret 立即数不同 295 / 相同 137 / 96B 窗口内无 ret 103；前 16 字节全同的对 0 对。
    ⇒ 至少 295 对在调用约定层面就不可能共用同一入口。
E5 227 个「同类不同层槽号相同」的对里，最典型一对是 INoticeSink@8 槽0（ret 8）与
   INoticeSource@12 槽0（ret 4）—— 同槽号、不同接口、不同参数个数。
E6 (层基类名, mdisp, 槽号) 键：全镜像 12836 个；>=2 宿主 67 个覆盖 1275 槽实例；
   完全一致键 6 个、众数覆盖 1037/1275 = 81.33%。
E7 接口子表（mdisp != 0）键 110 个，其中单宿主键 43 个、多宿主键 67 个；多宿主键覆盖的
   1275 槽实例里调整器 288 个、直接槽 987 个。
E8 四个实现的接口身份（实测，结构判据）：
   0x410450 77 槽全部落在主表槽 4；0x410580 75 槽全部落在 .?AVINoticeSink@@ 层槽 0；
   0x410590 78 槽全部落在 .?AVINoticeSource@@ 层槽 0；0x4C9150 205 槽跨 33 个槽号、
   38 个宿主类，除 1 个在 mdisp==4 外都在主表。
E9 主表槽 4 的 954 个实现里 Top1 = 0x410450（77 次）；主表槽 0 的 954 个实现里
   Top1 = 0x410260（75 次）。
"""
import sys, os, struct, collections, json, capstone
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
ck('E0 基线 COL=1214 VT=1214 槽=14044 组=954 多表组=94',
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
ck('E0b TypeDescriptor 988 条', len(TD)==988, len(TD))
def bcds(c):
    return [P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))]
def layer_bcd(colva):
    c=COL[colva]
    m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    if not m: return None
    best=max(m,key=lambda b:P.dw(b+4))
    return best if sum(1 for b in m if P.dw(b+4)==P.dw(best+4))==1 else None
LAY={va:layer_bcd(va) for va in COL}
ck('E0c 1214 条 COL 全部解出唯一层 BCD', all(v is not None for v in LAY.values()),
   sum(1 for v in LAY.values() if v is None))
def lname(colva):
    b=LAY[colva]; return TD.get(P.dw(b),'?') if b else '?'
ck('E0d 层名解析 0 个 ?', all(lname(va)!='?' for va in COL),
   sum(1 for va in COL if lname(va)=='?'))

def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04
def kind(va):
    o=P.r2o(va)
    if o is None or in_text(va) is False: return 'NONTEXT'
    if is_adj(va): return 'ADJ'
    if P.RAW[o] in (0xE9,0xEB) or P.RAW[o:o+2]==b'\xff\x25': return 'JMP:plain'
    return 'DIRECT'
direct=[]; adj=[]
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp']==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        (adj if is_adj(v) else direct).append((vt,k,v))
ck('E1a 非主表调整器 305 / 直接槽 1013', (len(adj),len(direct))==(305,1013),(len(adj),len(direct)))

# ---- E1 五类 ----
stat=collections.Counter(); pairs=[]
for vt,k,v in direct:
    nm=COL[VT[vt]]['name']
    sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: stat['NOSIB']+=1; continue
    t=sorted(sibs)[0]; w=P.dw(t+4*k)
    if w==v: stat['SAME']+=1; continue
    if is_adj(w): stat['THUNK_OTHER']+=1
    else: stat['DIRECT_OTHER']+=1
    pairs.append((vt,k,v,t,w))
ck('E1b 五类 = {NOSIB 478, DIRECT_OTHER 525, THUNK_OTHER 10}',
   dict(stat)=={'NOSIB':478,'DIRECT_OTHER':525,'THUNK_OTHER':10}, dict(stat))
ck('E1c 合计数 1013', sum(stat.values())==1013, sum(stat.values()))
ck('E1d 可比对对 535', len(pairs)==535, len(pairs))

# ---- E2 跨层 ----
cross=sum(1 for vt,k,v,t,w in pairs if COL[VT[vt]]['mdisp']!=COL[VT[t]]['mdisp'])
ck('E2a 535 对全部跨层（COL.mdisp 不同）', cross==535, cross)
xlay=sum(1 for vt,k,v,t,w in pairs if lname(VT[vt])!=lname(VT[t]))
ck('E2b 535 对全部跨接口层（层基类名不同）', xlay==535, xlay)

# ---- E3 跳板归并 ----
def jump_tgt(va):
    o=P.r2o(va)
    if o is None: return None
    r=P.RAW[o:o+6]
    if r[0]==0xE9: return va+5+struct.unpack_from('<i',r,1)[0]
    if r[0]==0xEB: return va+2+struct.unpack_from('<b',r,1)[0]
    if r[0]==0xFF and r[1]==0x25: return P.dw(struct.unpack_from('<I',r,2)[0])
    return None
def canon(va,h=8):
    cur=va; seen=set()
    for _ in range(h):
        t=jump_tgt(cur)
        if t is None or not in_text(t) or t in seen: break
        seen.add(cur); cur=t
    return cur
for h,lab in ((1,'1 跳'),(8,'8 跳')):
    col=sum(1 for vt,k,v,t,w in pairs if canon(v,h)==canon(w,h))
    ck('E3 %s 口径 COLLAPSE 0 / DISTINCT 535'%lab, col==0 and 535-col==535, (col,535-col))
ck('E3c 恒等 canon 反控 COLLAPSE 也 0', sum(1 for vt,k,v,t,w in pairs if v==w)==0)

# ---- E4 ret 立即数 ----
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def retn(va,b=96):
    o=P.r2o(va)
    if o is None: return None
    for ins in md.disasm(P.RAW[o:o+b],va):
        if ins.mnemonic=='ret': return int(ins.op_str,16) if ins.op_str else 0
        if ins.mnemonic in ('jmp','int3','hlt') and ins.address>va: return 'no-ret'
    return 'no-ret'
d=0; s=0; u=0; body=0
for vt,k,v,t,w in pairs:
    a=retn(v); b2=retn(w)
    if isinstance(a,int) and isinstance(b2,int):
        if a!=b2: d+=1
        else: s+=1
    else: u+=1
    h1=P.RAW[P.r2o(v):P.r2o(v)+16]; h2=P.RAW[P.r2o(w):P.r2o(w)+16]
    if h1==h2: body+=1
ck('E4a ret 不同 295 / 相同 137 / 不可解 103', (d,s,u)==(295,137,103), (d,s,u))
ck('E4b 前 16 字节完全相同的对 0', body==0, body)

# ---- E5 典型对：同宿主类、不同接口、槽 0 ----
sub=[vt for vt in VT if COL[VT[vt]]['mdisp']!=0]
host0=collections.defaultdict(dict)
for vt in sub:
    if NS[vt]<=0: continue
    host0[COL[VT[vt]]['name']][lname(VT[vt])]=(COL[VT[vt]]['mdisp'],P.dw(vt),retn(P.dw(vt)))
ck('E5a AbstractClass 两接口槽 0 = INoticeSink(8) ret8 / INoticeSource(12) ret4',
   host0['.?AVAbstractClass@@'].get('.?AVINoticeSink@@',(None,None,None))[2]==8
   and host0['.?AVAbstractClass@@'].get('.?AVINoticeSource@@',(None,None,None))[2]==4,
   {k2:(v2[0],hex(v2[1]),v2[2]) for k2,v2 in host0['.?AVAbstractClass@@'].items()})

# ---- E6/E7 接口键 ----
sub=[vt for vt in VT if COL[VT[vt]]['mdisp']!=0]
key=collections.defaultdict(list)
for vt in sub:
    for k in range(NS[vt]): key[(lname(VT[vt]),COL[VT[vt]]['mdisp'],k)].append(vt)
ck('E7a 接口子表键 110', len(key)==110, len(key))
multi={k:v for k,v in key.items() if len(v)>1}
ck('E7b 多宿主键 67 / 覆盖槽实例 1275',
   (len(multi),sum(len(v) for v in multi.values()))==(67,1275),
   (len(multi),sum(len(v) for v in multi.values())))
ck('E7c 单宿主键 43', len(key)-len(multi)==43, len(key)-len(multi))
inst=[P.dw(t+4*k[2]) for k,v in multi.items() for t in v]
nadj=sum(1 for x in inst if is_adj(x))
ck('E7d 1275 实例里调整器 288 / 直接槽 987', (nadj,len(inst)-nadj)==(288,987),(nadj,len(inst)-nadj))
cons=sum(1 for k,v in multi.items() if len({P.dw(t+4*k[2]) for t in v})==1)
mod=sum(collections.Counter(P.dw(t+4*k[2]) for t in v).most_common(1)[0][1] for k,v in multi.items())
ck('E6a 完全一致键 6 / 不一致 61', (cons,len(multi)-cons)==(6,61),(cons,len(multi)-cons))
ck('E6b 众数覆盖 1037/1275 = 81.33%', (mod,len(inst))==(1037,1275),(mod,len(inst)))
allkey=collections.defaultdict(list)
for vt in VT:
    for k in range(NS[vt]): allkey[(lname(VT[vt]),COL[VT[vt]]['mdisp'],k)].append(vt)
ck('E6c 含主表的全镜像键 12836', len(allkey)==12836, len(allkey))

# ---- E8 四个实现 ----
TGT=[0x410450,0x410580,0x410590,0x4C9150]
ident={}
for tgt in TGT:
    slots=collections.Counter(); lays=collections.Counter(); mds=collections.Counter(); names=set()
    for vt,colva in VT.items():
        for k in range(NS[vt]):
            if P.dw(vt+4*k)!=tgt: continue
            slots[k]+=1; lays[lname(colva)]+=1; mds[COL[colva]['mdisp']]+=1; names.add(COL[colva]['name'])
    tot=sum(slots.values())
    ident[hex(tgt)]=dict(total=tot,slots=dict(sorted(slots.items())),
                         layer=lays.most_common(3),mdisp=dict(sorted(mds.items())),hosts=len(names))
    print('E8 %08x 槽 %d 个：槽号 %s | 层 %s | mdisp %s | 宿主类 %d'%(
        tgt,tot,list(sorted(slots.items()))[:6] if tot>40 else dict(sorted(slots.items())),lays.most_common(2),dict(sorted(mds.items())),len(names)))
ck('E8a 0x410450 = 77 槽全在槽 4 主表层',
   ident['0x410450']['slots']=={4:77} and ident['0x410450']['mdisp']=={0:77}, ident['0x410450']['slots'])
ck('E8b 0x410580 = 75 槽全在 INoticeSink 层槽 0',
   ident['0x410580']['slots']=={0:75} and ident['0x410580']['layer'][0][0]=='.?AVINoticeSink@@',
   (ident['0x410580']['slots'],ident['0x410580']['layer'][0]))
ck('E8c 0x410590 = 78 槽全在 INoticeSource 层槽 0',
   ident['0x410590']['slots']=={0:78} and ident['0x410590']['layer'][0][0]=='.?AVINoticeSource@@',
   (ident['0x410590']['slots'],ident['0x410590']['layer'][0]))
ck('E8d 0x4C9150 跨 33 个槽号 / 205 槽 / 38 宿主类',
   (len(ident['0x4c9150']['slots']),ident['0x4c9150']['total'],ident['0x4c9150']['hosts'])==(33,205,38),
   (len(ident['0x4c9150']['slots']),ident['0x4c9150']['total'],ident['0x4c9150']['hosts']))

# ---- E9 主表高频 ----
main=[vt for vt in VT if COL[VT[vt]]['mdisp']==0]
ck('E9a 主表 954 / 槽 12726', (len(main),sum(NS[t] for t in main))==(954,12726),
   (len(main),sum(NS[t] for t in main)))
c4=collections.Counter(P.dw(vt+16) for vt in main if NS[vt]>4)
ck('E9b 主表槽 4 Top1 = 0x410450（77）', c4.most_common(1)[0]==(0x410450,77), [(hex(a),c) for a,c in c4.most_common(3)])
c0=collections.Counter(P.dw(vt) for vt in main)
ck('E9c 主表槽 0 Top1 = 0x410260（75）', c0.most_common(1)[0]==(0x410260,75), [(hex(a),c) for a,c in c0.most_common(3)])
ck('E9d 主表槽 0 有 863 个不同实现', len(c0)==863, len(c0))

# ---- 字节证据表 ----
def hx(va,n=24):
    o=P.r2o(va); return P.RAW[o:o+n].hex() if o is not None else None
ev={hex(t):hx(t) for t in TGT}
ev['0x410220']=hx(0x410220); ev['0x410210']=hx(0x410210)
ck('E10 五个实现字节取证齐备', all(ev[k] for k in ('0x410450','0x410580','0x410590','0x4c9150','0x410220','0x410210')), ev)

out=dict(stat=dict(stat),pairs=len(pairs),cross=cross,xlay=xlay,
         retn=dict(diff=d,same=s,unres=u,samebody=body),
         keys=len(key),multi=len(multi),multi_inst=len(inst),single=len(key)-len(multi),
         adj_in_multi=nadj,cons=cons,modal=mod,allkeys=len(allkey),
         ident=ident,mainslot4=[[hex(a),c] for a,c in c4.most_common(5)],
         mainslot0=[[hex(a),c] for a,c in c0.most_common(5)],bytes=ev,
         abstract_slot0={k:[v[0],hex(v[1]),v[2]] for k,v in host0['.?AVAbstractClass@@'].items()})
json.dump(out,open('/home/t628/projects/ra2-campaign-forge/_r192/r192e.json','w'),indent=1)
print('断言 %d 条，FAIL %d 条'%(N,len(fails)))
sys.exit(1 if fails else 0)
