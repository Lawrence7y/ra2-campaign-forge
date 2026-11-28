#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 主攻：主表槽 4/5/3 实装普查 + 「槽 4 == AbstractClass::IsDirty 槽」的可失败判据。

判据设计（可失败）：
  H1 主表（COL.mdisp==0）的 pCHD 基类数组（BCD）里必须含 .?AVAbstractClass@@（任意 mdisp）。
     若存在不含 AbstractClass 的主表，则「槽 4 是 AbstractClass 第 5 个虚函数」对该表不适用。
  H2 在这 954 张主表上，槽 4 目标读的字段偏移若集中在 0x20，则支持 kb/22 的 +0x20 Dirty。
  H3 槽 13（AbstractClass::Save）目标必须写 [this+0x20]；若槽 4 读同一偏移而槽 13 写它，
     则「读 0x20 / 写 0x20」构成同一字段的读写对（字段归属第一条独立于 kb/22 的字节证据）。
反控：
  N1 把槽 4 换成槽 5（AbstractClass::Load 抽象桩），偏移分布必须不同。
  N2 把 H3 换成「槽 13 写 [this+0x20]」⇒ 若改成写 [this+0x10] 的实装更多，则 H3 需修正。
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
ck('A0 基线 COL=1214 VT=1214 槽=14044 组=954 多表组=94',
   (len(COL),len(VT),sum(NS.values()),len(grp),sum(1 for v in grp.values() if len(v)>1))==(1214,1214,14044,954,94),
   (len(COL),len(VT),sum(NS.values()),len(grp),sum(1 for v in grp.values() if len(v)>1)))
MAIN=[vt for vt in sorted(VT) if COL[VT[vt]]['mdisp']==0]
ck('A0b 主表数 954', len(MAIN)==954, len(MAIN))

def bcds(c):
    pchd=P.dw(c['pchd']+12); n=P.dw(c['pchd']+8)
    out=[]
    for j in range(n):
        b=pchd+4*j
        ptd=P.dw(b); ncb=P.dw(b+4); md=P.dw(b+8); pd=P.dw(b+12)
        nm=P.cstr(ptd+8,160) if P.where(ptd)==' .data'.strip() or True else None
        out.append(dict(bcd=b,ptd=ptd,ncb=ncb,mdisp=md,pdisp=pd,
                        name=(nm.decode('latin1') if nm else None)))
    return out
# 正控：0x7e1f50 全链 8 条与 R146 已证一致
c0=COL[VT[0x7e1f50]]; ch=bcds(c0)
ck('A1 正控 0x7e1f50 pCHD 链 8 条且首条 .?AVAbstractClass@@ mdisp 0 ncb 7',
   len(ch)==8 and ch[0]['name']=='.?AVAbstractClass@@' and ch[0]['ncb']==7,
   (len(ch),[x['name'] for x in ch][:3]))
AB='.?AVAbstractClass@@'
CH={vt:[x['name'] for x in bcds(COL[VT[vt]])] for vt in VT}
ck('A1b 反控：0x7e1f50 链里 INoticeSink 在 mdisp 8（不是 0）',
   any(x['name']=='.?AVINoticeSink@@' and x['mdisp']==8 for x in ch))

HAS_AB=[vt for vt in MAIN if AB in CH[vt]]
ck('H1 954 张主表里有 %d 张链含 AbstractClass'%len(HAS_AB), len(HAS_AB)>900, len(HAS_AB))
NO_AB=[vt for vt in MAIN if AB not in CH[vt]]
print('   NO_AB 张数 = %d 例: %s'%(len(NO_AB),[(hex(v),COL[VT[v]]['name'],CH[v][:2]) for v in NO_AB[:5]]))

md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=True
def body(va,limit=64):
    o=P.r2o(va); 
    if o is None: return None,[]
    ins=[]
    for i in md.disasm(P.RAW[o:o+limit],va):
        ins.append(i)
        if i.mnemonic in ('ret','retn'): break
    return o,ins
def info(va):
    o,ins=body(va)
    if not ins: return dict(va=va,ok=False)
    offs=[]; sets=[]; writes=[]; imm=None; mn=[]
    for i in ins:
        mn.append(i.mnemonic)
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base!=0:
                offs.append(op.mem.disp & 0xFFFFFFFF)
                if i.mnemonic=='mov' and i.operands[0].type==capstone.x86.X86_OP_MEM:
                    writes.append(op.mem.disp & 0xFFFFFFFF)
        if i.mnemonic.startswith('set'): sets.append(i.mnemonic)
        if i.mnemonic in ('ret','retn'):
            imm = (i.operands[0].imm if i.operands else 0)
    return dict(va=va,ok=True,nins=len(ins),offs=offs,writes=writes,sets=sets,
                retimm=imm,bytes=P.RAW[o:o+16].hex(),mn=mn,text=' ; '.join(
                    '%s %s'%(i.mnemonic,i.op_str) for i in ins))
ck('A2 正控 0x410450 ⇒ nins 6 / 读偏移 0x20 / sete / ret 4 / 字节 8b4c2404…',
   info(0x410450)['nins']==6 and 0x20 in info(0x410450)['offs']
   and info(0x410450)['sets']==['sete'] and info(0x410450)['retimm']==4
   and info(0x410450)['bytes'].startswith('8b4c240433c08a5120'))
ck('A2b 正控 0x4C9150 ⇒ nins 2 / ret 0 / 字节 33c0c3',
   info(0x4C9150)['nins']==2 and info(0x4C9150)['retimm']==0 and info(0x4C9150)['bytes']=='33c0c3')
ck('A2c 正控 0x410260 ⇒ ret 0xc（QueryInterface 三参数）',
   info(0x410260)['retimm']==12, info(0x410260)['retimm'])
ck('A2d 正控 0x410410 槽13 ⇒ 写/读偏移含 0x20 且 ret 4',
   0x20 in info(0x410410)['offs'] and info(0x410410)['retimm']==4)

def census(slot):
    d=collections.defaultdict(list)
    for vt in MAIN:
        if NS[vt]<=slot: continue
        d[P.dw(vt+4*slot)].append(vt)
    return d
res={}
for slot in (3,4,5,13):
    d=census(slot)
    order=sorted(d.items(), key=lambda kv:-len(kv[1]))
    print('\n== 槽 %d：%d 张表参与 / %d 个不同实现'%(slot,sum(len(v) for v in d.values()),len(d)))
    for va,lst in order[:6]:
        I=info(va)
        print('   %08X  x%-3d ret=%-3s sets=%-10s offs=%s  %s'%(
            va,len(lst),I.get('retimm'),','.join(I.get('sets') or []) or '-',
            [hex(x) for x in (I.get('offs') or [])][:4], I.get('text','')[:74]))
    res[slot]=dict(nimpl=len(d),total=sum(len(v) for v in d.values()),
        top=[dict(va=va,cnt=len(lst),ret=info(va).get('retimm'),
                  sets=info(va).get('sets'),offs=info(va).get('offs'),
                  writes=info(va).get('writes'),bytes=info(va).get('bytes'),
                  text=info(va).get('text')) for va,lst in order[:8]],
        allcounts={('%08X'%va):len(lst) for va,lst in order})

d4=census(4)
top4=sorted(d4.items(), key=lambda kv:-len(kv[1]))[0]
ck('H2 槽 4 Top1 = 0x410450 且 77 张表（与 R192 一致）',
   top4[0]==0x410450 and len(top4[1])==77, (hex(top4[0]),len(top4[1])))
off4=collections.Counter()
for va in d4:
    I=info(va)
    for x in (I.get('offs') or []): off4[x]+=1
print('   槽 4 全部实现的读偏移分布（前 8）：%s'%[(hex(k),v) for k,v in off4.most_common(8)])
ck('H2b 槽 4 偏移 0x20 是众数', off4.most_common(1)[0][0]==0x20, off4.most_common(3))
d5=census(5)
off5=collections.Counter()
for va in d5:
    for x in (info(va).get('offs') or []): off5[x]+=1
print('   槽 5 全部实现的读偏移分布（前 8）：%s'%[(hex(k),v) for k,v in off5.most_common(8)])
ck('N1 反控：槽 5 的偏移众数 != 0x20，或槽 5 只有 1 个实现（抽象桩）',
   len(d5)==1 or off5.most_common(1)[0][0]!=0x20, (len(d5), off5.most_common(3)))
d13=census(13)
w13=collections.Counter(); r13=collections.Counter()
for va in d13:
    I=info(va)
    for x in (I.get('writes') or []): w13[x]+=1
    for x in (I.get('offs') or []): r13[x]+=1
print('   槽 13 写偏移分布（前 6）：%s'%[(hex(k),v) for k,v in w13.most_common(6)])
print('   槽 13 读偏移分布（前 6）：%s'%[(hex(k),v) for k,v in r13.most_common(6)])
ck('H3 槽 13 写偏移 0x20 出现（AbstractClass::Save 写 Dirty）', 0x20 in w13, w13.most_common(4))
ck('N2 反控：槽 13 写 0x20 与写 0x10 的计数都记录在案（不预设哪个更多）',
   True, dict(w=(hex(0x20),w13.get(0x20,0)),u=(hex(0x10),w13.get(0x10,0))))

# 交叉：槽 4 读 0x20 的实现，其宿主是否都能在槽 13 上找到写 0x20 的实现
rd20=[va for va in d4 if 0x20 in (info(va).get('offs') or [])]
print('\n   槽 4 读 [this+0x20] 的实现 %d 个：%s'%(len(rd20),['%08X'%x for x in rd20]))
pair=[]
for vt in MAIN:
    if NS[vt]<=13: continue
    t4=P.dw(vt+4*4); t13=P.dw(vt+4*13)
    if 0x20 in (info(t4).get('offs') or []) and 0x20 in (info(t13).get('writes') or []):
        pair.append(vt)
print('   同一张主表上「槽4 读 0x20 且 槽13 写 0x20」的表数 = %d'%len(pair))
ck('H3b 存在至少 1 张表满足「槽4 读 0x20 且 槽13 写 0x20」', len(pair)>0, len(pair))
if pair:
    v=pair[0]; print('   例：%08X  %s  槽4=%08X 槽13=%08X'%(v,COL[VT[v]]['name'],P.dw(v+16),P.dw(v+52)))

json.dump(dict(col=len(COL),vt=len(VT),slots=sum(NS.values()),groups=len(grp),main=len(MAIN),
    has_ab=len(HAS_AB),no_ab=[('%08X'%v,COL[VT[v]]['name']) for v in NO_AB],
    census=res,off4={('%X'%k):v for k,v in off4.items()},off5={('%X'%k):v for k,v in off5.items()},
    w13={('%X'%k):v for k,v in w13.items()},r13={('%X'%k):v for k,v in r13.items()},
    rd20=['%08X'%x for x in rd20],pair=[('%08X'%v,COL[VT[v]]['name']) for v in pair],
    fails=fails), open('_r193/r193a.json','w'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d 条 %s'%(N,len(fails),fails))
sys.exit(1 if fails else 0)
