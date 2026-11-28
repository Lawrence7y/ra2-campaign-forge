#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 落盘：台账 V579 -> V580（只改 F55）+ 四件套追加。
台账：F55 statement 追加 ⑭、limitations 追加同批边界、第 4 列追加 _r195 证据路径。
四件套：R14_COMMON 追加 §2.200；GOAL_THREE_TARGETS 追加 §1250；LEAD_LOCK 追加 PX 段；STATUS_BOARD 追加第 195 轮。
全部断言 + 回读校验；CR 守恒：R14 1081 / GOAL 337 / LOCK 137 / BOARD 0 / LEDGER 0。
"""
import os,sys,hashlib,copy
ROOT='/home/t628/projects/ra2-campaign-forge'
T=os.path.join(ROOT,'lead/next_re_20261117_r14')
LROOT=os.path.join(ROOT,'lead')
OLDDIR=os.path.join(T,'R17_R131_FACTINDEX_V579'); NEWDIR=os.path.join(T,'R17_R131_FACTINDEX_V580')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def rd(p): return open(p,'rb').read()
def sha(b): return hashlib.sha256(b).hexdigest()

# ---------- 台账 ----------
old=rd(os.path.join(OLDDIR,'FACT_INDEX.tsv'))
ck('L1 旧 V579 = 193,424 B / CR 0 / sha 144cf72b',
   len(old)==193424 and old.count(b'\r')==0 and sha(old).startswith('144cf72b'),
   (len(old),old.count(b'\r'),sha(old)[:16]))
TXT=old.decode('utf-8'); L=TXT.split('\n')
ck('L2 58 段（57 行 + 空尾）',len(L)==58,len(L))
rows=[l.split('\t') for l in L[:57]]
ck('L3 57 行每行 5 列',all(len(r)==5 for r in rows),{len(r) for r in rows})
f55=[r for r in rows if r[0]=='F55'][0]
S0,L0,E0=len(f55[1].encode()),len(f55[4].encode()),len(f55[3].encode())
ck('L4 F55 现态 stmt 22159 / lim 17231 / evid 733',(S0,L0,E0)==(22159,17231,733),(S0,L0,E0))
ck('L5 F55 grade [已证]',f55[2]=='[已证]',f55[2])

S14=('⑭ **（V580 新增 · R195：L 的 78 张表的安装面全图、AbstractClass 构造族与字段初值、槽 18..23 默认实现、以及两处口径订正）** '
'上一段 ⑬ 给了 L 的槽 0..17 默认实现。本轮把「这 78 张表是怎么装上去的」做成可复算事实。'
'**（i）安装面（推翻两处旧读数）**：全 .text 用「分块 + 解码失败逐字节前移重同步」的线性反汇编'
'（1,394,132 条指令 / 覆盖 4,063,139 B / 段 4,063,232 B = 100.00% / 重同步 93 次）检索「imm32 == 某张 L 表头」的指令，'
'得 **341 条**，覆盖 **78/78 张表头，零命中 0 张**，形态 **100% 为 mov dword ptr [reg], imm32**（无 push/mov reg/lea）。'
'每张表头命中 3..8 次（恰 3 次 14 张、8 次 1 张）。⇒ 推翻了两种旧读数：用「字节扫描 C7 形态」得 4 条 / 只 2 张表（漏 ModRM 内的 C7 与其它形态），'
'用「64KB 分块但块内不重同步」得 285 条 / 10 张零命中（块内失步）。'
'反控：同样的 341 个地址在全文件（.data/.rdata/.rsrc/.detour）里**一次都不出现**，因此「字节口径会比指令口径虚高」在这组目标上**不成立**（byte=inst=341）。'
'**（ii）AbstractClass 构造族 = 5 个入口**：0x410170 / 0x4101C0 / 0x4101E0 / 0x4105A0 / 0x6E8000，全部以 `mov dword ptr [reg], 0x7E1F50` 装主表。'
'0x410170（15 条）同时给出字段初值：+0x10 = **0xFFFFFFFF**（`c7 40 10 ff ff ff ff`）、+0x14 低 3 位清零、+0x18 = 0、+0x1C = 0、+0x20 = **0**（`mov byte ptr [eax+0x20], cl`，cl 来自 `xor ecx,ecx`）。'
'**这是 +0x10 / +0x20 两个字段首次拿到二进制内部自证**（R193/R194 的字段语义此前只有 kb/22 外部源）。'
'0x4105A0（标量删除析构，15 条）一次性装 4 张表：+0 = 0x7E1F50（主表，24 槽）、+4 = 0x7E1F34（mdisp 4 子表，6 槽）、'
'+8 = 0x7E1F2C（mdisp 8，1 槽）、+0xC = 0x7E1F24（mdisp 12，1 槽）；四者的「表头前 4 字节」**4/4 都是 COL 地址**，'
'且后三条 pCHD 同为 0x7FB108 ⇒ 同一个类的 1 主表 + 3 接口子表。'
'**（iii）二次构造的字节实证**：0x6E8000（64 条）先装 0x7E1F50 四次（+0/+4/+8/+0xC），随后在 0x6E807E **把 +0 覆写成 0x7F4680**、'
'+4/+8/+0xC 覆写成 0x7F4664/0x7F465C/0x7F4654 ⇒ 同一个构造函数里主表被替换，是「先基类后半途改档」的直接证据。'
'**（iv）槽 18..23 默认实现（⑬ 只做到 17）**：槽 18 = 0x4104C0、槽 19 = 0x4104F0、槽 20 = 0x410520、槽 21 = 0x410530、'
'槽 22 = 0x410540、槽 23 = 0x410570。槽 19 与槽 22 **体内都 `call dword ptr [eax+0x48]`（= 槽 18）**，即它们复用槽 18 的接口方法；'
'该偏移在全 .text 有 **929 处**间接调用点。槽 18 从三个 .data **BSS** 全局取初值：0x887680 / 0x887684 / 0x887688（三者落在 .data 的 vsize 内、rawsize 外，'
'文件内无初值 = 0），唯一写入者是 0x410110（`xor eax,eax` 后连写三处，5 条），唯一读取者是 0x4104C0 ⇒ 一条闭合的「三元组清零 / 读取」对。'
'**（v）CRC 状态对象的归属（⑬ 遗留）**：0x4A1CA0 的调用面两口径**相等 = 331**（resync 线性 331 / 字节 E8+rel32 331），'
'══ R194 的「上界 U=331」其实就是真实值，之前的「下界 94 / 假命中 237」应作废（差额来自不做重同步）。'
'体 55 条 / 134 字节，状态槽位 **{+0, +4, +8, +0xC}** 四个全中：+0 是 CRC、+4 是 0..4 计数、+8..+0xB 是 4 字节折叠缓冲、+0xC 是 count 影子；'
'`not eax` 恰 2 次（读入前后各一次）。**+0 只有 1 处写：0x4A1D1B `89 01 mov dword ptr [ecx], eax`，是「读入→not→折叠→not→写回」的 read-modify-write，'
'没有独立的初值写入** ⇒ 「初值来源」**仍未取得**。')
S14_TAIL=('**（vi）未取得（不粉饰）**：① 18+6 个实现的游戏语义名仍未取得；② CRC 状态对象 +0 的初值来源未取得（只到「先读旧值」，'
'读到的是调用方栈/内存里未清零的字节）；③ 0x6E8000 覆写主表的语义动机（基类→具体类）未取得；④ 三个 BSS 全局的游戏含义未取得。')
f55n=copy.deepcopy(f55)
f55n[1]=f55[1]+' '+S14
f55n[4]=f55[4]+' '+S14_TAIL
f55n[3]=f55[3]+';_r195/m12_final.py;_r195/m12_final.json;_r195/m15_state.py;_r195/m16_ctor.py;_r195/m17_seal.py;_r195/m18_cross.py;_r195/m19_final.py;_r195/audit_r195_core.txt'
rows[rows.index(f55)]=f55n
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
newb=newtxt.encode('utf-8')
ck('L6 新台账 CR 0',newb.count(b'\r')==0,newb.count(b'\r'))
ck('L7 新台账 57 行 5 列',newb.count(b'\n')==57 and all(len(r)==5 for r in rows),(newb.count(b'\n'),))
ck('L8 只有 F55 变（其余 56 行字节不变）',
   all(rows[i]==[x for x in L[i].split('\t')] for i in range(57) if rows[i][0]!='F55'),True)
if fails:
    print('ABORT before ledger write: %d FAIL'%len(fails)); sys.exit(1)
os.makedirs(NEWDIR,exist_ok=True)
open(os.path.join(NEWDIR,'FACT_INDEX.tsv'),'wb').write(newb)
rb=rd(os.path.join(NEWDIR,'FACT_INDEX.tsv'))
ck('L9 回读新台账一致',rb==newb,(len(rb),sha(rb)[:16]))
print('LEDGER V579 -> V580 : %d -> %d B  sha %s'%(len(old),len(newb),sha(newb)[:16]))
print('F55 new stmt=%d lim=%d evid=%d'%(len(f55n[1].encode()),len(f55n[4].encode()),len(f55n[3].encode())))
print('FAILS=%d'%len(fails))
