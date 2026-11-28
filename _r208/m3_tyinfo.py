# -*- coding: utf-8 -*-
"""R208 m3：0x7f9594 语义定性与 TD 头部模型（正反控同命令）。
主张 H1：0x7f9594 是 MSVC type_info 的**共享 vftable**，TD+0 == 该 vftable 指针（非「类 ID」），
        TD 布局 = {+0 vfptr, +4 _M_data(spare，恒 0), +8 内联名字符串}。
证据点：
 E1 988/988 TD 的 +0 == 0x7f9594；+4 恒 0
 E2 0x7f9594 起的连续 .text 槽数（应 1 个）
 E3 该槽目标反汇编前 24 B 应是函数序言（用 capstone，只 1 处 detail）
 E4 0x7f9594 后紧跟的字节是 C 字符串，内容含 'RTTI'
 E5 全文搜索 '.?AV__non_rtti_object@@' 与 'Access violation' 字符串地址，说明谁 own 这条 vftable
 E6 反控：.data 中指向 .rdata 的 dword 引用计数 top2..5（V 应为 988，第二名数量级差）
 E7 反控：TD+8 是内联名 ⇒ 同一 TD 的 +8 之后 4 B 不应解析成 .data 指针
"""
import sys, struct, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA; NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

# COL / TD 集合
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G); NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own_td={a:COL[a+16]['pTD'] for a in CHD}
phys=sorted({x for a in CHD for x in BCA[a]})
TD=sorted(set(own_td.values())|{P.dw(b) for b in phys})
V=0x7f9594
ck('E1.1 TD 数 988', len(TD)==988, len(TD))
ck('E1.2 TD+0 全 == 0x7f9594', all(P.dw(t)==V for t in TD), len({P.dw(t) for t in TD}))
ck('E1.3 TD+4 全 == 0', all(P.dw(t+4)==0 for t in TD), len({P.dw(t+4) for t in TD}))
nms={P.cstr(t+8,300) for t in TD}
ck('E1.4 TD+8 全是 .?A..@@ 名（内联，非指针）',
   all(x is not None and x.startswith(b'.?A') and x.endswith(b'@@') for x in nms), len(nms))
# E2 槽数
sl=[];a=V
while P.where(P.dw(a))=='.text':
    sl.append(P.dw(a)); a+=4
    if len(sl)>16: break
ck('E2.1 0x7f9594 起连续 .text 槽数 == 1', len(sl)==1, [hex(x) for x in sl])
# E3 反汇编
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
o=P.r2o(sl[0]); code=P.RAW[o:o+32]
dis=list(md.disasm(code,sl[0]))
print('  E3 槽目标 0x%x 前 %d 条：%s' % (sl[0],len(dis),'; '.join('%s %s'%(i.mnemonic,i.op_str) for i in dis[:8])))
ck('E3.1 槽目标可线性反汇编且首条是常见序言（push/mov/sub/ret/jmp 族）',
   len(dis)>=3 and dis[0].mnemonic in ('push','mov','sub','ret','jmp','lea'), dis[0].mnemonic if dis else None)
# E4 后继字节
nxt=P.RAW[P.r2o(V+4):P.r2o(V+4)+64]
print('  E4 V+4 起 64 B =', nxt[:48])
ck('E4.1 V+4 起是可读 C 串且含 RTTI 语义词',
   nxt[:1].isalpha() and (b'RTTI' in nxt or b'type' in nxt.lower()), nxt[:40])
# E5 相关字符串
hits={}
for pat in (b'.?AV__non_rtti_object@@', b'Access violation'):
    ps=[];st=0
    while True:
        i=P.RAW.find(pat,st)
        if i<0: break
        for s in P.SECS:
            if s['rawptr']<=i<s['rawptr']+s['rawsize']: ps.append(s['lo']+(i-s['rawptr']))
        st=i+1
    hits[pat]=ps
print('  E5 字符串地址', {k.decode():[hex(x) for x in v] for k,v in hits.items()})
# E6 反控 refs top
sd=P.B['.data']; w=struct.unpack_from('<%dI'%(sd['rawsize']//4),P.RAW,sd['rawptr'])
hit=collections.Counter(x for x in w if 0x7e1000<=x<0x812000)
top=hit.most_common(6)
print('  E6 .data→.rdata 引用计数 top6', [(hex(k),v) for k,v in top])
ck('E6.1 V 引用数 988 排名第 1 且与第 2 名差 >=10 倍', top[0]==(V,988) and top[0][1]>=10*top[1][1], top[:2])
# E7 TD+8 后 4B 是否像 .data 指针
bad=0
for t in TD:
    n=P.cstr(t+8,300); ln=len(n)
    nxt4=P.dw(t+8+ln+1) if (t+8+ln+1)%4==0 else P.dw(t+8+ln+((4-((ln+1)%4))%4))
    if P.where(nxt4)=='.data': bad+=1
ck('E7.1 名后 4 B 落到 .data 的 TD 极少（<5%）', bad < 0.05*len(TD), (bad,len(TD)))
print('== 断言 %d / FAIL %d ==' % (NA,len(fails)))
print('FAILS',fails)
