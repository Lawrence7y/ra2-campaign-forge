#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 落盘：台账 V577 -> V578。只在 F55 一行追加第 ⑫ 段 + limitations 追加同批边界段。

本轮实测（_r193 下六个脚本全部 0 FAIL）：
  r193c_slot4_lin.py 18 断言：|L|=78；0x410450 双向唯一在槽 4（77 张）；唯一覆写者 HouseTypeClass；
       0x410450 体 6 条 = 读 [this+0x20] + sete；同形态在槽 5 命中 0；槽4读/槽13触及 +0x20 的表 3 张。
  r193d_recon.py 12 断言：COL d0 恒 0（signature）、d1 才是 mdisp；主表 954 / 子表 260；
       954 主表槽 4 Top1 = 0x410450 77 次；1214 全表槽 4 Top1 = 0x410220 78 次（全在子表）。
  r193e_recheck.py 15 断言：535/1013/478/525/10 复现；卡面字面 thunk 口径不可复现（实测 432/783/351/425/7）。
  r193f_pad.py 11 断言：103 对里 STRICT|STRICT 78 / STRICT|PAD 10 / STRICT|WINDOW_OUT 11 /
       WINDOW_OUT|STRICT 4 / 两侧都不可判 0；10 个 PAD 侧全是调整器 thunk 且 E9 落点有 ret。
  r193g_closure.py 18 断言：0x410220 / 0x410590 宿主类名集合 == L；0x410580 ⊂ L 缺 3 类均为覆写；
       直接引用 0x410220 = 14 处（订正 R192「四地址均为 0」）。
  r193h_fields.py 14 断言：0x410410 先 +0x10 后 +0x20；0x4A1D50 是 4 字节块写薄壳；
       0x4A1CA0 是 1 字节写 + CRC32 折叠（表 0x81F7B4，not/not 包裹，7 样本与 zlib 一致）。
"""
import os, sys, copy, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
OLD=os.path.join(TIER,'R17_R131_FACTINDEX_V577','FACT_INDEX.tsv')
NEWD=os.path.join(TIER,'R17_R131_FACTINDEX_V578')
NEW=os.path.join(NEWD,'FACT_INDEX.tsv')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

raw=open(OLD,'rb').read()
ck('D1 旧 V577 = 177,011 B / sha 81b3e116… / CR 0',
   len(raw)==177011 and hashlib.sha256(raw).hexdigest().startswith('81b3e116') and raw.count(b'\r')==0,
   (len(raw),hashlib.sha256(raw).hexdigest()[:16]))
TXT=raw.decode('utf-8'); L=TXT.split('\n')
ck('D2 58 段（57 行 + 空尾）', len(L)==58, len(L))
rows=[l.split('\t') for l in L[:57]]
ORIG=copy.deepcopy(rows)
ck('D3 57 行每行 5 列', all(len(r)==5 for r in rows), {len(r) for r in rows})
f55=[r for r in rows if r[0]=='F55'][0]
S0,L0,E0=len(f55[1].encode()),len(f55[4].encode()),len(f55[3].encode())
ck('D4 F55 现态 stmt 13249 / lim 10086 / evid 375', (S0,L0,E0)==(13249,10086,375),(S0,L0,E0))
ck('D5 F55 grade 现态 [已证]', f55[2]=='[已证]', f55[2])

S12=('⑫ **（V578 新增 · R193：四个高频实现落在同一个 78 类血统集合上 + AbstractClass 序列化路径的字节闭合）** 上一段 ⑪ 只给四个地址各自的'
'「槽号 + 层 + 宿主类数」，四组数（77 / 78 / 75 / 78）看起来互不相干；本轮证明它们落在**同一个集合**上，差异只由「覆写」与「缺层」解释。'
'**（i）血统集合 L 的定义与规模**：在 954 张主表（COL.offset-to-top == 0）里取「pCHD 基类数组的 pTD 名里含 .?AVAbstractClass@@」的那些表，'
'得 **78 张 / 78 个不同类名**（集合按类名去重后仍是 78，无重名）。'
'**（ii）0x410450 双向唯一且是默认实现**：在全部 1,214 张表的**所有**槽位上扫该地址，命中集合恰为 **{槽 4} × 77 张表**（其余 33 个槽号各 0 次），'
'77 张全部是主表；L 共 78 张，唯一不取 0x410450 的是 .?AVHouseTypeClass@@（表 0x7EAB58，槽 4 = 0x512280 = xor eax,eax; ret 4，'
'与 0x410450 同为 ret 4，槽位替换不改调用约定）⇒ **77 + 1 = 78 闭合**。'
'**（iii）0x410220 的宿主类名集合与 L 严格相等**（各 78 个，双向差集都为 0），且它**只**出现在 (.?AUIRTTITypeInfo@@, offset-to-top 4) '
'子表的**槽 4**（78/78）；体为 8B 44 24 04 / 8B 40 0C / C2 04 00（mov eax,[esp+4]; mov eax,[eax+0xC]; ret 4），'
'即**相对该接口子对象 +0xC**；由于该子对象在完整对象里的 offset-to-top 是 4，折算到完整对象是 **+0x10**。'
'这正是上一段 ⑪ 未能给出的「同一字段」的第二个观测面。'
'**（iv）0x410590 的宿主类名集合同样与 L 严格相等**，且只在 (.?AVINoticeSource@@, offset-to-top 12) 子表槽 0（78/78），体 C2 04 00（ret 4）。'
'**（v）0x410580 是 L 的真子集且缺 3 个类**（75/78），缺的是 .?AVAircraftClass@@ / .?AVInfantryClass@@ / .?AVUnitClass@@；'
'这 3 个类**都有** (.?AVINoticeSink@@, offset-to-top 8) 子表（不是缺表），只是槽 0 分别被覆写成 '
'0x41BC30（sub esp,0x20 起首）/ 0x522A60（sub esp,0x10）/ 0x746100（sub esp,0x18），三个实现互不相同 ⇒ **缺的 3 个是覆写，不是缺层**。'
'**（vi）直接引用面订正**：0x410450 / 0x410580 / 0x410590 被直接 call rel32 与 call [abs] 引用各 **0** 处，但 **0x410220 有 14 处**'
'（首个 0x413E89）—— 上一段 ⑪ 末句「四地址被直接引用均为 0」对 0x410220 **不成立**，就地作废，正确说法是「三个只经虚表调用，一个另有 14 处直接调用」。'
'**（vii）AbstractClass 序列化路径的字节闭合**：0x410410（.?AVAbstractClass@@ 主表 0x7E1F50 槽 13）体 15 条，顺序确定 —— '
'先 mov eax,[esi+0x10]; mov ecx,edi; push eax; call **0x4A1D50**，再 mov cl,[esi+0x20]; push ecx; mov ecx,edi; call **0x4A1CA0**，ret 4。'
'两条被调函数性质不同：**0x4A1D50**（7 条）= push 4 / lea edx,[esp+4] / push / call 0x4A1DE0 / ret 4，是**4 字节定长块写**的薄壳；'
'**0x4A1CA0**（39 条）= 累计计数 [ecx+4]、逐字节写 [eax+ecx+8]、满 4 字节时（cmp eax,4 + jne 跳过）把 4 字节折进 **CRC32** 并清零，'
'其表基为 **0x81F7B4**：t[0]=0 / t[1]=0x77073096 / t[255]=0x2D02EF8D，是**标准反射 CRC-32 表**；'
'代码里 not eax 出现 **2 次**（前置 + 收尾）、shr eax,8 一次，用「not 前后包裹的反射实现」在 7 个样本（含空串）上与 zlib.crc32 **逐样本一致**，'
'不带 not 包裹的纯反射实现则不一致（空串除外）⇒ 那两次 not 是语义必需的，不是冗余。4 字节路径 0x4A1DE0（154 条）同样引用 0x81F7B4。'
'**（viii）字段归属的独立字节证据（不依赖 kb/22）**：L 里「槽 4 读 [this+0x20] 且槽 13 也触及 [this+0x20]」的表有 **3 张** —— '
'.?AVAbstractClass@@（0x7E1F50）/ .?AVCellClass@@（0x7E4EEC）/ .?AVTactical@@（0x7F4348）；'
'配合 (iii) 的「槽 4 走 IRTTITypeInfo 层读到完整对象 +0x10」，可得 +0x10 与 +0x20 是**在同一函数里被先后写出的两个字段**，'
'且走两条不同的序列化路径（定长块 vs 带 CRC 的字节流）。这与 kb/22 独立给出的 UniqueID(+0x10) / Dirty(+0x20) 双通道一致，'
'但**语义名仍来自 kb/22 这一外部源**，本轮只补强字段归属的字节侧。')

L12=('**（V578 新增 · 与 ⑫ 同一批实测）** 边界：'
'（a）「血统集合 L」是**RTTI 结构判据**：只说明这张主表的 pCHD 基类数组里出现过 .?AVAbstractClass@@ 这一条，'
'**不**说明该表在运行期的对象布局、也不说明任何槽的语义名；78 这个数**只对 954 张 mdisp==0 的主表口径成立**，'
'把 260 张接口子表并进来算会得到不同的分母。'
'（b）集合比较必须**按 COL 修饰名**，不能按表地址：0x410580 / 0x410590 / 0x410220 只出现在接口子表上，而 L 是主表地址集合，'
'按地址比必然互不相交（本轮第一版正是这么写的，5 条断言当场 FAIL，已改正并保留作反控 N1）。'
'（c）(iii) 的「折算到完整对象 +0x10」依赖两个前提：接口子对象 offset-to-top == 4，以及实现体内的位移就是相对该子对象的字段偏移；'
'两条都只由字节与 RTTI 记录支撑，**未**用运行期内存采样验证（属动态项，按纪律留 win-main）。'
'（d）(vii) 的 CRC 结论只到「两个辅助函数各自做什么」：**没有**证明 +0x10 与 +0x20 在**同一**流里的先后顺序对应存档格式的字段序，'
'也**没有**确定校验覆盖范围（是整段还是分块）；「7 样本与 zlib 一致」只证明表是标准表 + not 包裹形态，'
'不等于证明调用点的入参与初值。'
'（e）(ii) 的 77 这个数在**两种分母下都出现**但含义不同：954 主表口径是 77（0x410450），'
'1,214 全表口径是 78 且 Top1 变成 0x410220（78 次，全部落在接口子表）。两口径不可混用；'
'审计员 #472 报的「槽 4 Top1 = 0x410220 78 次 / 0x410450 不是 Top1」是**用全表口径答主表问题**，'
'其基线「COL d0 in {0,1} 判主表 ⇒ 主表 1214 / 子表 0」也错在把 d0（signature，恒 0）当成 offset-to-top；'
'正确字段是 d1（实测 954 个 0 / 260 个非 0）。该审计结论本轮已逐条复算并**不采信基线**，只采信它与本轮重合的 0x410450=77。'
'（f）103 对「96 字节内无 ret」的完整边界分析已完成，但这**不是**「103 对都没有 ret」：'
'严格口径（遇 ret/retn 或指令边界上的 >=2 连续 90/CC 即停）下 STRICT|STRICT 78 / STRICT|PAD 10 / STRICT|WINDOW_OUT 11 / '
'WINDOW_OUT|STRICT 4 / 两侧都不可判 **0**；10 个 PAD 侧**全部**是调整器 thunk（83/81 6C 24 04 前缀 + E9），'
'其 E9 落点（0x414290 / 0x4F6E60 / 0x4F6950 / 0x4F6830 / 0x410260）在严格口径下都有 ret ⇒ '
'「两侧都真的没有 ret 的对数 = **0**」。'
'（g）卡面写法欠定：调度卡里「thunk 判据 = 首字节 E9/EB/FF25 或 引用<=1 且首指令 <=8 字节」实测得 432/783/351/425/7，'
'**不能**复现 478/525/10/1013/535；能复现的是「只剔除 83/81 6C 24 04 调整器」这一 R192 有效口径。'
'基线一律用后者，卡面写法已在下轮修改。'
'（h）脚本 `_r193/r193c_slot4_lin.py`（18 断言 0 FAIL）/ `_r193/r193d_recon.py`（12）/ '
'`_r193/r193e_recheck.py`（15）/ `_r193/r193f_pad.py`（11）/ `_r193/r193g_closure.py`（18）/ '
'`_r193/r193h_fields.py`（14）。执行员 #471（hy4）独立脚本在 535/1013/478/525/10 五数上与本轮一致，'
'其 103 对分类（78/0）与本轮 r193f 的 STRICT 口径口径一致（它未拆出 PAD 档）；'
'审计员 #472（deepseek）跑满 21 回合 error_max_turns 失败，只产出基线错误的审计文本，见 (e)。')

for nm,s in (('statement',S12),('limitations',L12)):
    ck('D7 %s 段无 tab / CR / LF'%nm, '\t' not in s and '\r' not in s and '\n' not in s)
    ck('D8 %s 段反引号成对（不改既有风格）'%nm, s.count('`')%2==0, s.count('`'))
ck('D9 ⑫ 段在 statement 里现态 0 次', f55[1].count(S12)==0)
f55[1]=f55[1]+S12
f55[4]=f55[4]+L12
NEWP=('_r193/r193c_slot4_lin.py;_r193/r193d_recon.py;_r193/r193e_recheck.py;'
      '_r193/r193f_pad.py;_r193/r193g_closure.py;_r193/r193h_fields.py')
ck('D10 旧第 4 列不含 _r193', '_r193/' not in f55[3], f55[3])
f55[3]=f55[3]+';'+NEWP
ck('D11 新第 4 列含六条 _r193 路径',
   all(x in f55[3] for x in ('r193c_slot4_lin.py','r193d_recon.py','r193e_recheck.py',
                             'r193f_pad.py','r193g_closure.py','r193h_fields.py')))
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
nb=newtxt.encode()
R2=[l.split('\t') for l in newtxt.split('\n')[:57]]
ck('D12 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r')==0 and len(newtxt.split('\n'))==58 and all(len(x)==5 for x in R2))
ck('D13 只有 F55 一行变化', [a[0] for a,b in zip(ORIG,R2) if a!=b]==['F55'],
   [a[0] for a,b in zip(ORIG,R2) if a!=b])
ck('D14 F55 grade 未动', [r for r in ORIG if r[0]=='F55'][0][2]==f55[2])
exp=177011+len(S12.encode())+len(L12.encode())+len(NEWP.encode())+1
ck('D15 体量按构造闭合', len(nb)==exp, (len(nb),exp,len(nb)-exp))
if fails:
    print('★ fail-closed：%d 条未过，不写盘'%len(fails)); sys.exit(1)
os.makedirs(NEWD,exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW,'xb') as f: f.write(nb)
ck('D16 回读 sha 一致',
   hashlib.sha256(open(NEW,'rb').read()).hexdigest()==hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条'%(n,len(fails)))
print('V578 = %d B / sha %s… / F55 stmt %d B / lim %d B / evid %d B'
      %(len(nb),hashlib.sha256(nb).hexdigest()[:16],len(f55[1].encode()),len(f55[4].encode()),len(f55[3].encode())))
sys.exit(0)
