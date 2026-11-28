# -*- coding: utf-8 -*-
"""R209 q4: 律 T 订正 —— 101 张含 thunk 表的 slot0/1/2 三连 = IUnknown 三方法 this 调整；
triple 键（thunk 三元组）与 mdisp 一一对应；反汇编三个 jmp 目标；mdisp=40 表 idx3/4 例外定性。
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
ck('0 载入 1214 表 / 70 thunk / 101 命中表', len(VT)==1214 and len(TH)==70 and len(HIT)==101,
   '%d/%d/%d'%(len(VT),len(TH),len(HIT)))

# 1. 每张 T 表的 (idx0,idx1,idx2) 三元组
tri=collections.defaultdict(list)
for c in HIT:
    s=VT[c]
    tri[(s[0],s[1],s[2])].append(c)
print('# 不同 slot0/1/2 三元组 = %d'%len(tri))
for k,v in sorted(tri.items(), key=lambda x:-len(x[1])):
    mdv={MD[c] for c in v}
    print('  %s 表数=%d mdisp=%s jmp=%s'%(
        [hex(x) for x in k], len(v), sorted(mdv),
        [hex(TH[x]['jmp']) if x in TH else '-' for x in k]))
ck('1 三元组数 == 101 表的去重数', sum(len(v) for v in tri.values())==101)
ck('2 每个三元组内 mdisp 唯一（22 组）', all(len({MD[c] for c in v})==1 for v in tri.values()),
   'groups=%d'%len(tri))
ck('3 slot0/1/2 全是 thunk 的 101/101', all(x in TH for c in HIT for x in VT[c][:3]),
   sum(1 for c in HIT if all(x in TH for x in VT[c][:3])))
# 每张表 mdisp == 该表 slot0 thunk 的 imm
ck('4 mdisp == slot0 thunk imm 101/101', all(MD[c]==TH[VT[c][0]]['imm'] for c in HIT),
   sum(1 for c in HIT if MD[c]==TH[VT[c][0]]['imm']))
ck('5 slot1/slot2 thunk 的 imm 亦 == mdisp 101/101',
   all(TH[VT[c][1]]['imm']==MD[c] and TH[VT[c][2]]['imm']==MD[c] for c in HIT))

# 2. idx3/4 例外
extra=[]
for c in HIT:
    for (i,v) in HIT[c]:
        if i>=3: extra.append((c,i,v))
print('# idx>=3 的 thunk 命中 = %d'%len(extra))
for c,i,v in extra:
    print('   COL %08x %-28s mdisp=%d vt=%08x idx=%d thunk=%08x imm=%d jmp=%08x slots=%s'%(
        c,NM[c],MD[c],VO[c],i,v,TH[v]['imm'],TH[v]['jmp'],VT[c]))
# 3. jmp 目标三元组
print('\n## 各三元组的 jmp 目标三元组:')
jt=collections.defaultdict(set)
for k,v in tri.items():
    jt[tuple(TH[x]['jmp'] for x in k)].add(tuple(sorted({MD[c] for c in v})))
for k,v in jt.items():
    print('  %s -> mdisp %s'%([hex(x) for x in k], sorted(v)))
ck('6 jmp 目标三元组数 == 三元组数（一表一套）', len(jt)==len(tri), '%d vs %d'%(len(jt),len(tri)))

# 4. 反汇编三个通用目标 + Aircraft 三个目标
def dis(a,n=60,cap=400):
    o=P.r2o(a); return list(md.disasm(P.RAW[o:o+cap],a))[:n]
for a in (0x410260,0x410300,0x410310):
    ins=dis(a,14)
    print('\n== %08x len_scan = %s'%(a, ' '.join(i.mnemonic+' '+i.op_str for i in ins)))
    for i in ins: print('   %08x %-18s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
# ret 形态
def func_ret(a,cap=200):
    o=P.r2o(a); ins=list(md.disasm(P.RAW[o:o+cap],a))
    for i in ins:
        if i.mnemonic in ('ret','retn'): return hex(a), i.address, i.op_str, i.bytes.hex()
    return hex(a),None,None,None
print('\n## 21 个 A83 的 jmp 目标 + 终点 ret:')
tg=sorted({TH[v]['jmp'] for v in TH if TH[v]['kind']=='A83'})
for a in tg:
    print('   %08x -> %s'%(a, func_ret(a)))
ck('7 A83 目标去重数 == 21', len(tg)==21, len(tg))
# 5. 全 70 thunk 使用情况
usedva={x for c in HIT for x in VT[c][:max(3, max([i for i,_ in HIT[c]]+[0])+1)]}
allused=set()
for c in HIT:
    for (i,v) in HIT[c]: allused.add(v)
ck('8 70 个 thunk 全部被 101 表使用', allused==set(TH), 'used=%d of %d'%(len(allused),len(TH)))
# 6. IUnknown 三方法判据：QI 目标是「读 [esp+4/8] 做 IID 比较」形态
o=P.r2o(0x410300); b=P.RAW[o:o+48]
print('\n0x410300 bytes: %s'%b.hex(' '))
o=P.r2o(0x410310); b=P.RAW[o:o+48]
print('0x410310 bytes: %s'%b.hex(' '))
o=P.r2o(0x4142f0); b=P.RAW[o:o+48]
print('0x4142f0 bytes: %s'%b.hex(' '))
o=P.r2o(0x414300); b=P.RAW[o:o+48]
print('0x414300 bytes: %s'%b.hex(' '))
json.dump(dict(tri={str([hex(x) for x in k]):[hex(c) for c in v] for k,v in tri.items()},
               jmp={str([hex(x) for x in k]):[hex(x) for x in v] for k,v in jt.items()},
               extra=[[hex(c),i,hex(v)] for c,i,v in extra]),
          open('/home/t628/projects/ra2-campaign-forge/_r209/q4.json','w'),indent=1)
print('\n== FAILS: %s (%d) =='%(fails,NA))
