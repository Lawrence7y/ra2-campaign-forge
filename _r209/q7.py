# -*- coding: utf-8 -*-
"""R209 q7: (a) thunk 的 E9 落点 == 本类主视图 slot0 复算；(b) 0x410260 完整 QI 语义；
(c) 主视图表 slot0 的 ret 分布；(d) 0x11c7 (0x6379fb) 语境；(e) S 形态三表归属；(f) T/S/I 三形态互斥性。
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
VO={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
COL={k:{'mdisp':MD[k],'name':NM[k]} for k in MD}
chd={}
for c in COL: chd.setdefault(P.dw(c+8),[]).append(c)
def retimm(a,cap=512):
    o=P.r2o(a)
    for i in md.disasm(P.RAW[o:o+cap],a):
        if i.mnemonic=='ret': return int(i.op_str,16) if i.op_str else 0
    return None
# (a) jmp == 本类主视图 slot0
ok=0; bad=[]
for c in HIT:
    prim=[x for x in chd[P.dw(c+8)] if MD[x]==0]
    if len(prim)!=1: bad.append((hex(c),'no primary')); continue
    p=prim[0]
    if TH[VT[c][0]]['jmp']==VT[p][0]: ok+=1
    else: bad.append((hex(c),hex(TH[VT[c][0]]['jmp']),hex(VT[p][0])))
ck('A1 101 表中 slot0 thunk 的 E9 落点 == 本类主视图 slot0', ok==101, 'ok=%d bad=%d %s'%(ok,len(bad),bad[:3]))
ok2=0
for c in HIT:
    prim=[x for x in chd[P.dw(c+8)] if MD[x]==0][0]
    if TH[VT[c][1]]['jmp']==VT[prim][1]: ok2+=1
ck('A2 slot1 thunk 落点 == 主视图 slot1', ok2==101, ok2)
ok3=sum(1 for c in HIT if TH[VT[c][2]]['jmp']==VT[[x for x in chd[P.dw(c+8)] if MD[x]==0][0]][2])
ck('A3 slot2 thunk 落点 == 主视图 slot2', ok3==101, ok3)

# (b) 0x410260 完整
print('\n## 0x410260 完整反汇编（到第一个 ret 与其后 60 条）:')
o=P.r2o(0x410260); ins=list(md.disasm(P.RAW[o:o+700],0x410260))
for i in ins[:56]: print('   %08x %-22s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))

# (c) 主视图 954 表 slot0 ret 分布
prim_tabs=[c for c in VT if MD[c]==0]
ck('C1 主视图表数 954', len(prim_tabs)==954, len(prim_tabs))
rd=collections.Counter()
for c in prim_tabs:
    r=retimm(VT[c][0],700); rd[r]+=1
print('# 954 主视图 slot0 的 ret 立即数分布 = %s'%rd.most_common())
ck('C2 主视图 slot0 ret 0xc 占多数', rd[12]>500, rd[12])

# (d) 0x11c7 第二处语境
o=P.r2o(0x6379fb)
print('\n## 0x6379fb 前后 48B: %s'%P.RAW[o-16:o+32].hex(' '))
ins2=list(md.disasm(P.RAW[P.r2o(0x6379e0):P.r2o(0x6379e0)+96],0x6379e0))
for i in ins2[:16]: print('   %08x %-20s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))

# (e) S 形态三表
for tv in (0x410590,0x410580,0x6d1770):
    owners=[(c,i) for c in VT for i,v in enumerate(VT[c]) if v==tv]
    if not owners:  # 用 dict keys
        owners=[(c,i) for c in VT for i,v in enumerate(VT[c]) if v==tv]
    print('# 表 %08x 被引用 %d 次，idx 分布=%s'%(tv,len(owners),collections.Counter(i for c,i in owners).most_common(6)))

# (f) 三形态互斥：T 表内是否有 S 表地址；S 表所在表是否也含 thunk
S={0x410590,0x410580,0x6d1770}
sowners=collections.defaultdict(list)
for c in VT:
    for i,v in enumerate(VT[c]):
        if v in S: sowners[v].append(c)
for v in S:
    tabs=sowners[v]
    print('# S 表 %08x 承载表数=%d，这些表中含 thunk 的=%d，mdisp 分布=%s'%(
        v,len(tabs),sum(1 for c in tabs if c in HIT),collections.Counter(MD[c] for c in tabs).most_common()))
ck('F1 三张 S 表承载表集合互不重叠',
   sum(len(set(sowners[v])) for v in S)==len(set().union(*[set(sowners[v]) for v in S])), '')
json.dump(dict(prim_ret={str(k):v for k,v in rd.items()}),open('/home/t628/projects/ra2-campaign-forge/_r209/q7.json','w'))
print('\n== FAILS: %s (%d) =='%(fails,NA))
