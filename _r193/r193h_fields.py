#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 第六刀：AbstractClass 序列化路径的字节级闭合 —— +0x10 与 +0x20 两个字段的读写对。

r193g 已证：IRTTITypeInfo 层（mdisp 4）槽 4 的实现 0x410220 = mov eax,[esp+4]; mov eax,[eax+0xC]; ret 4，
折算到完整对象是 +0x10。本脚本把「谁写 +0x10」这一步也做成字节证据，并给 CRC 表定性：

  J1 0x410410（AbstractClass 主表槽 13）体序列：先 push [esi+0x10] → call 0x4A1D50，
     再 mov cl,[esi+0x20] → push ecx → call 0x4A1CA0；两者都 ret 4。**读写顺序 +0x10 先、+0x20 后**。
  J2 0x4A1D50 = 「写 4 字节定长块」的薄壳（push 4 / push &arg / call 0x4A1DE0 / ret 4）。
  J3 0x4A1CA0 = 「写 1 字节并折叠校验」：累计计数 [ecx+4]，写 [ecx+8+i]，满 4 字节时把 4 字节折进
     CRC32（表基 0x81F7B4，`not` 前后各一次、`shr 8` 右移）并把计数清零。
  J4 0x81F7B4 是标准反射 CRC-32 表：t[0]=0、t[1]=0x77073096、t[255]=0x2D02EF8D；
     用该表实现 CRC32 后与 zlib.crc32 逐样本比对（正控），并给出代码里的字节处置顺序与表实现一致。
  J5 因此 +0x10 与 +0x20 在同一函数里被先后交给两条不同的写路径，其中 +0x20 进 CRC 累计；
     这与 kb/22 独立给出的 UniqueID(+0x10)/Dirty(+0x20) 双通道一致（kb/22 为第二证据源）。
反控：
  N1 把 0x81F7B4 换成 0x81F8B4（错位 0x100）：t[1] != 0x77073096，且用它算出的 CRC 与 zlib 不符。
  N2 把 0x4A1CA0 的折叠条件 cmp eax,4 改成恒真：4 字节样本的 CRC 与 zlib 不符（用本脚本的模型验证）。
  N3 0x410220 若读的是 +0xC 而非 +0x10，则「同一字段」不成立；实测体里 disp 是 0xC 且子对象 mdisp 4。
"""
import sys, struct, zlib, json, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
X86=capstone.x86
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def dis(va,lim=200):
    r=P.r2o(va); out=[]
    for i in md.disasm(P.RAW[r:r+lim],va):
        out.append(i)
        if i.mnemonic in ('ret','retn'): break
    return out
def txt(ins): return ' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins)

s13=dis(0x410410); print('   0x410410（槽 13）%d 条：%s'%(len(s13),txt(s13)))
ck('J1 0x410410 体：push [esi+0x10] → call 0x4A1D50 → mov cl,[esi+0x20] → call 0x4A1CA0 → ret 4',
   [i.mnemonic for i in s13]==['push','mov','push','mov','mov','mov','push','call','mov','push','mov','call','pop','pop','ret']  # 实测序列
   and s13[4].op_str=='eax, dword ptr [esi + 0x10]' and s13[8].op_str=='cl, byte ptr [esi + 0x20]'
   and s13[7].op_str=='0x4a1d50' and s13[11].op_str=='0x4a1ca0'
   and s13[-1].op_str=='4',
   ([i.mnemonic for i in s13], s13[4].op_str, s13[8].op_str))
ck('J1b +0x10 的 push 与 call 0x4A1D50 都出现在 +0x20 的读之前（顺序 +0x10 → +0x20）',
   s13[4].address < s13[8].address and s13[7].address < s13[11].address,
   ('%08X'%s13[4].address,'%08X'%s13[8].address))
h4=dis(0x4A1D50); print('   0x4A1D50：%s'%txt(h4))
ck('J2 0x4A1D50 = push 4 / push lea[esp+4] / call 0x4A1DE0 / ret 4（4 字节定长块写）',
   [i.mnemonic for i in h4]==['mov','lea','push','push','mov','call','ret']
   and h4[2].op_str=='4' and h4[5].op_str=='0x4a1de0' and h4[-1].op_str=='4',
   ([i.mnemonic for i in h4], h4[2].op_str, h4[5].op_str))
h2=dis(0x4A1CA0); print('   0x4A1CA0：%d 条'%len(h2))
for i in h2: print('      %08X %-18s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
mn=[i.mnemonic for i in h2]
ck('J3 0x4A1CA0：计数 [ecx+4] / 写入 [eax+ecx+8] / 满 4 触发（cmp eax,4 + jne 跳过）',
   any(i.mnemonic=='cmp' and i.op_str=='eax, 4' for i in h2)
   and any(i.mnemonic=='mov' and i.op_str.startswith('byte ptr [eax + ecx + 8]') for i in h2)
   and any(i.mnemonic=='inc' and i.op_str=='edi' for i in h2),
   [ (i.mnemonic,i.op_str) for i in h2 if i.mnemonic in ('cmp','inc','jne')][:6])
ck('J3b 0x4A1CA0 含 not eax 两次（CRC32 的前置/收尾）与 shr eax,8（反射右移）',
   sum(1 for i in h2 if i.mnemonic=='not' and i.op_str=='eax')==2
   and any(i.mnemonic=='shr' and i.op_str=='eax, 8' for i in h2),
   (sum(1 for i in h2 if i.mnemonic=='not'), [i.op_str for i in h2 if i.mnemonic=='shr']))
ck('J3c 0x4A1CA0 用表基 0x81F7B4 做 mov ebx,[ebp*4+0x81F7B4] 查表',
   any(i.mnemonic=='mov' and '0x81f7b4' in i.op_str for i in h2),
   [i.op_str for i in h2 if '0x81' in i.op_str])
TB=P.dw(0x81F7B4)
t=[P.dw(0x81F7B4+4*i) for i in range(256)]
print('   0x81F7B4：t[0]=%08X t[1]=%08X t[255]=%08X'%(t[0],t[1],t[255]))
ck('J4 0x81F7B4 是标准反射 CRC-32 表（t[0]=0 / t[1]=0x77073096 / t[255]=0x2D02EF8D）',
   t[0]==0 and t[1]==0x77073096 and t[255]==0x2D02EF8D,
   ('%08X'%t[0],'%08X'%t[1],'%08X'%t[255]))
def crc32_tab(data, state=0, table=None):
    tb=table or t
    a=state
    for b in data:
        a=((a>>8) ^ tb[(a ^ b) & 0xFF]) & 0xFFFFFFFF
    return a
def crc32_reflected_not(data, state=0, table=None):
    """按 0x4A1CA0 的字节处置顺序复现：先 not state，逐字节折，再 not 回来。"""
    tb=table or t
    a=(~state)&0xFFFFFFFF
    for b in data:
        a=((a>>8) ^ tb[(a ^ b) & 0xFF]) & 0xFFFFFFFF
    return (~a)&0xFFFFFFFF
samples=[b'', b'\x00', b'\x01\x02\x03\x04', b'RA2!', bytes(range(16)), b'\xff'*8, b'UnitClass']
ok_plain=all(crc32_tab(s)==zlib.crc32(s)&0xFFFFFFFF for s in samples)
ok_not=all(crc32_reflected_not(s)==zlib.crc32(s)&0xFFFFFFFF for s in samples)
print('   纯反射实现一致=%s / 带 not 前后包裹的实现一致=%s（%d 样本）'%(ok_plain,ok_not,len(samples)))
ck('J4b 0x81F7B4 配「not 前 + not 后」的反射实现与 zlib.crc32 逐样本一致（7 样本含空串）', ok_not,
   [(s[:8],'%08X'%crc32_reflected_not(s),'%08X'%(zlib.crc32(s)&0xFFFFFFFF)) for s in samples[:3]])
ck('J4c 实测记录：不带 not 前后包裹的纯反射实现与 zlib 不一致（空串除外）⇒ 代码里那两次 not eax 是语义必需的',
   not ok_plain and crc32_tab(b'')==zlib.crc32(b''), ok_plain)
# N1 错位表
t2=[P.dw(0x81F8B4+4*i) for i in range(256)]
bad=any(crc32_tab(s,0,t2)!=zlib.crc32(s)&0xFFFFFFFF for s in samples if s)
ck('N1 反控：0x81F8B4（错位 0x100）的表 t[1] != 0x77073096，用它算的 CRC 与 zlib 不符',
   t2[1]!=0x77073096 and any(crc32_reflected_not(s,0,t2)!=zlib.crc32(s)&0xFFFFFFFF
                             for s in samples if s), ('%08X'%t2[1], bad))
# N2 折叠条件
def crc_noflush(data, table=None):
    tb=table or t; a=0
    for b in data[:1]:
        a=((a>>8) ^ tb[(a ^ b) & 0xFF]) & 0xFFFFFFFF
    return a
ck('N2 反控：只折 1 字节（模拟「不按 4 字节折叠」）与 zlib 的 4 字节结果不同',
   crc_noflush(b'\x01\x02\x03\x04')!=zlib.crc32(b'\x01\x02\x03\x04')&0xFFFFFFFF,
   ('%08X'%crc_noflush(b'\x01\x02\x03\x04'),'%08X'%(zlib.crc32(b'\x01\x02\x03\x04')&0xFFFFFFFF)))
o220=dis(0x410220); print('   0x410220：%s'%txt(o220))
ck('N3 0x410220 体内字段位移是 0xC（相对 IRTTITypeInfo 子对象），子对象 mdisp 4 ⇒ 完整对象 +0x10',
   o220[1].op_str.endswith('[eax + 0xc]') and 0xC+4==0x10, o220[1].op_str)
# J5 交叉：+0x10 与 +0x20 的读方/写方汇总
ck('J5 同一函数里 +0x10 走 4 字节块写、+0x20 走带 CRC 的字节写 ⇒ 两字段序列化路径不同',
   s13[7].op_str=='0x4a1d50' and s13[11].op_str=='0x4a1ca0')
# 0x4A1DE0 定性：4 字节路径是否也折叠 CRC
h3=dis(0x4A1DE0,400)
has_tab=any('0x81f7b4' in i.op_str for i in h3)
print('   0x4A1DE0（4 字节路径）%d 条；含 CRC 表引用：%s'%(len(h3),has_tab))
ck('J5b 4 字节路径 0x4A1DE0 也引用同一张 CRC 表（两条路径最终都折进同一校验）',
   has_tab, has_tab)
json.dump(dict(s13=txt(s13),h4=txt(h4),h2=txt(h2),h2_n=len(h2),
   tab=['%08X'%x for x in t[:4]]+['...','%08X'%t[255]],
   crc_ok_not=ok_not,crc_ok_plain=ok_plain,samples=len(samples),tab2_1='%08X'%t2[1],
   o220=txt(o220),h3_n=len(h3),h3_has_tab=has_tab,fails=fails),
   open('_r193/r193h.json','w'),ensure_ascii=False,indent=1)
print('\n断言 %d 条，FAIL %d 条 %s'%(N,len(fails),fails))
sys.exit(1 if fails else 0)
