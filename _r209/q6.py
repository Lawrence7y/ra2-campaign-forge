# -*- coding: utf-8 -*-
"""R209 q6: 13 个 QI 目标的形态分类 + 0x410260 的 IID 比较表 + HouseClass idx3/4 thunk 定性。
QI 形态判据（互斥优先级）：
  P1 E_POINTER 早退：函数体前 64B 出现 0x80004003 立即数
  P2 返回常量 1：前 32B 出现 mov eax,1 ; ret 4 且无 IID 比较
  P3 IID 比较：前 256B 出现 4 次以上 repe cmpsd (f3 a7) 或 cmp [..], imm32 连续串
  P4 其它
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
TE=P.B['.text']; TB=P.RAW[TE['rawptr']:TE['rawptr']+TE['rawsize']]; BASE=TE['lo']
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
HIT={int(k,16):[(i,int(x,16)) for i,x in v] for k,v in d3['hit'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VO={int(k,16):int(v,16) for k,v in d3['vt_of'].items()}

def body(a,cap=512):
    o=P.r2o(a); return P.RAW[o:o+cap], list(md.disasm(P.RAW[o:o+cap],a))
def retimm(a,cap=512):
    b,ins=body(a,cap)
    for i in ins:
        if i.mnemonic=='ret': return int(i.op_str,16) if i.op_str else 0, i.address
    return None,None
QI=sorted({TH[VT[c][0]]['jmp'] for c in HIT})
print('# QI 目标 = %d 个'%len(QI))
rows=[]
for a in QI:
    b,ins=body(a,400)
    nep=1 if b'\x03\x40\x00\x80' in b else 0
    ncmps=sum(1 for i in ins if i.mnemonic=='repe' ) + b.count(b'\xf3\xa7')
    ncmpimm=sum(1 for i in ins if i.mnemonic=='cmp' and bool(__import__('re').match(r'^dword ptr \[.*\], 0x',i.op_str)))
    ri,ra=retimm(a)
    rows.append(dict(qi=a,ep=nep,cmpsd=b.count(b'\xf3\xa7'),cmpimm=ncmpimm,ret=ri,
                     nins=len(ins),first=' '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins[:4])))
    print('   %08x ep=%d cmpsd=%-3d cmpimm=%-3d ret=%-3s first: %s'%(
        a,nep,b.count(b'\xf3\xa7'),ncmpimm,ri,' '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins[:5])))
ck('Q1 QI 目标 12 个（实测）', len(QI)==12, len(QI))
ck('Q2 全部 QI 目标 ret 0xc', all(r['ret']==12 for r in rows), [r['ret'] for r in rows])
ck('Q3 其中 E_POINTER 早退形态 5 个', sum(r['ep'] for r in rows)==5, sum(r['ep'] for r in rows))
ck('Q4 其余 7 个无 E_POINTER ⇒ 另一套实现', sum(1 for r in rows if not r['ep'])==7)
# 0x410260 IID 比较目标地址
a=0x410260; b,ins=body(a,600)
cmps=[ (i.address,i.op_str) for i in ins if i.mnemonic=='mov' and 'edi,' in i.op_str and '0x7f' in i.op_str]
print('\n## 0x410260 内 IID 常量地址（mov edi, imm）: %d 处'%len(cmps))
for ad,s in cmps[:20]: print('   %08x %s'%(ad,s))
# 读这些地址的内容
iidaddrs=[]
for ad,s in cmps:
    v=int(s.split(',')[1],16); iidaddrs.append(v)
print('## 这些地址的值（16B GUID hex）:')
for v in iidaddrs:
    o=P.r2o(v)
    if o: print('   %08x %s'%(v,P.RAW[o:o+16].hex(' ')))
# 与 COL 的 pTD 名对照：IID 数据在 .rdata，查它们是否在 vftable 表里被引用
ck('Q5 0x410260 比较常量 ≥4 处', len(cmps)>=4, len(cmps))
# 0x7f7c90.. 区间
print('\n# 0x7f7c60..0x7f7d20 内容:')
print(P.RAW[P.r2o(0x7f7c60):P.r2o(0x7f7c60)+0xc0].hex(' '))
# HouseClass idx3/4
HC=0x8028b8
print('\n## HouseClass mdisp=40 视图表 vt=%08x len=%d slots=%s'%(VO[HC],len(VT[HC]),[hex(x) for x in VT[HC]]))
for idx in (3,4):
    tv=VT[HC][idx]; print('   idx%d thunk %08x imm=%d jmp=%08x'%(idx,tv,TH[tv]['imm'],TH[tv]['jmp']))
    bb,ii=body(TH[tv]['jmp'],200)
    print('      jmp 目标首 8 条: '+' | '.join('%s %s'%(i.mnemonic,i.op_str) for i in ii[:8]))
    print('      ret=%s'%(retimm(TH[tv]['jmp'],400),))
    print('      thunk 是否在其它表被用: %s'%([ (hex(c),i) for c in HIT for (i,v) in HIT[c] if v==tv]))
# 40 mdisp 表所属类
print('   HouseClass mdisp=40 视图 COL=%08x name=%s'%(HC,NM[HC]))
# 该表 idx3/4 对应接口方法语义线索：jmp 目标是否 add/sub 其它偏移
json.dump(dict(qi=rows,house=dict(vt=hex(VO[HC]),slots=[hex(x) for x in VT[HC]])),
          open('/home/t628/projects/ra2-campaign-forge/_r209/q6.json','w'),indent=1)
print('\n== FAILS: %s (%d) =='%(fails,NA))
