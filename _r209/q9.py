# -*- coding: utf-8 -*-
"""R209 q9: 0x11c7/0x11c8 与 0x6d1770 的语义旁证；S 表 0x6d1770 的 3 张承载表身份；
主视图 vs 额外视图 ret 分布对比表（供落盘）；HouseClass idx3/4 的 T 槽位扩展。
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
VO={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
# S 表 0x6d1770 的 3 张表
tabs=[c for c in VT if 0x6d1770 in VT[c]]
print('# 0x6d1770 作 slot0 的表 %d 张:'%len(tabs))
for c in tabs:
    print('   COL %08x %-34s mdisp=%-6d vt=%08x slots=%s'%(c,NM[c],MD[c],VO[c],[hex(x) for x in VT[c]]))
    print('      COL 四要素: %s'%([hex(P.dw(c+4*j)) for j in range(5)]))
ck('S1 0x6d1770 的承载表恰 3 张且 mdisp 全 21784',
   len(tabs)==3 and all(MD[c]==21784 for c in tabs), [MD[c] for c in tabs])
ck('S2 三张表全为单槽', all(len(VT[c])==1 for c in tabs), [len(VT[c]) for c in tabs])
# 0xb0c1c0 表：26 * 96
base=0xb0c1c0
print('\n# 0xb0c1c0 段归属: %s（.data 虚拟尾部 = 运行期 BSS，静态无初值）'%(P.where(base),))
ck('S3 0xb0c1c0 与 0xb0cc1c 均落 .data 虚拟尾部（>hi_file，静态无字节）',
   P.where(base)=='virt-only' and P.where(0xb0cc1c)=='virt-only')
ck('S4 0xb0c1c0 落在 .data 段虚拟范围内', P.B['.data']['lo']<=base<P.B['.data']['hi_virt'], hex(P.B['.data']['hi_virt']))
# 0x6d1770 之后的下一个函数（把整段反汇编到 ret）
o=P.r2o(0x6d1770); ins=list(md.disasm(P.RAW[o:o+260],0x6d1770))
print('\n# 0x6d1770 完整反汇编:')
for i in ins:
    print('   %08x %-16s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
    if i.mnemonic=='ret': break
# 0x11c7 是否在别处作为数据（.rdata 无）
print('\n# dword 0x11c7 全域出现（重测，任意对齐）:')
for sn in ('.text','.rdata','.data','.rsrc'):
    s=P.B.get(sn); 
    if not s: continue
    buf=P.RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    print('   %s: %s'%(sn,[hex(s['lo']+i) for i in range(len(buf)) if buf[i:i+4]==b'\xc7\x11\x00\x00'][:6]))
# 主视图 vs 额外视图 ret 分布（cached）
prev=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q8.json'))
print('\n# 主视图 954 表 slot0/1/2 ret 分布: %s'%prev['prim_ret'])
print('# 额外视图 101 表 slot0/1/2 ret 分布: %s'%prev['extra_ret'])
ck('R1 额外视图三槽 ret 恒 12/4/4 而主视图异构',
   prev['extra_ret']==[{'12':101},{'4':101},{'4':101}] and len(prev['prim_ret'][1])>1,
   'prim slot1 不同 ret 种数=%d'%len(prev['prim_ret'][1]))
# HouseClass 表
HC=0x8028b8
ck('H1 HouseClass mdisp=40 表 9 槽，idx3/4 为 thunk，其余 5 槽非 thunk',
   len(VT[HC])==9 and [i for i,v in HIT.get(HC,[])]==[0,1,2,3,4], HIT.get(HC))
print('# HouseClass mdisp=40 表: %s'%[hex(x) for x in VT[HC]])
print('# 同组所有 COL（HouseClass 全部视图）:')
grp=collections.defaultdict(list)
for c in MD: grp[P.dw(c+16)].append(c)
for c in grp[P.dw(HC+16)]:
    print('   %08x mdisp=%-6d vt=%08x len=%d'%(c,MD[c],VO[c],len(VT[c])))
json.dump(dict(tabs_6d1770=[hex(c) for c in tabs]),open('/home/t628/projects/ra2-campaign-forge/_r209/q9.json','w'))
print('\n== FAILS: %s (%d) =='%(fails,NA))
