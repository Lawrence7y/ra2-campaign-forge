#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R192 落盘：台账 V576 -> V577。只在 F55 一行追加第 ⑪ 段 + limitations 追加同批边界段。

本轮实测（_r192/r192e_deliver.py 32 断言 0 FAIL / r192c_layers.py 13 断言 0 FAIL /
r192b_why.py 11 断言 0 FAIL；执行员 #466 独立脚本 5 类计数与 525/0/0 逐值复现）：
  ① 1013 直接槽五类：NOSIB 478 / DIRECT_OTHER 525 / THUNK_OTHER 10 / SAME 0。
  ② 535 个可比对对全部跨层，且两边「层基类身份」（pCHD 基类数组里 PMD.mdisp==COL.mdisp、
     ncb 最大的那条 BCD 的 pTD 名）也全不同 —— 不是「同组」而是「跨接口层的同槽号」。
  ③ 跳板归并 1 跳与 8 跳口径 COLLAPSE 均 0 ⇒ 不存在「不同 thunk 壳包同一 impl」。
  ④ 535 对里 ret 立即数不同 295 / 相同 137 / 96B 内无 ret 103；前 16 字节全同 0 对。
  ⑤ (层基类名, mdisp, 槽号) 键：接口子表 110 键（单宿主 43 / 多宿主 67，覆盖 1275 槽实例，
     其中调整器 288、直接槽 987）；键内完全一致 6、众数覆盖 1037/1275 = 81.33%。
     含主表的全镜像键 12836。
  ⑥ 四个实现的结构身份：0x410450 = 77 槽全在主表槽 4；0x410580 = 75 槽全在
     .?AVINoticeSink@@ 层槽 0（ret 8）；0x410590 = 78 槽全在 .?AVINoticeSource@@ 层槽 0
     （ret 4）；0x4C9150 = 205 槽跨 33 个槽号、38 个宿主类。
"""
import os, sys, copy, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
OLD=os.path.join(TIER,'R17_R131_FACTINDEX_V576','FACT_INDEX.tsv')
NEWD=os.path.join(TIER,'R17_R131_FACTINDEX_V577')
NEW=os.path.join(NEWD,'FACT_INDEX.tsv')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

raw=open(OLD,'rb').read()
ck('D1 旧 V576 = 171,758 B / sha 50efc728… / CR 0',
   len(raw)==171758 and hashlib.sha256(raw).hexdigest().startswith('50efc728') and raw.count(b'\r')==0,
   (len(raw),hashlib.sha256(raw).hexdigest()[:16]))
TXT=raw.decode('utf-8'); L=TXT.split('\n')
ck('D2 58 段（57 行 + 空尾）', len(L)==58, len(L))
rows=[l.split('\t') for l in L[:57]]
ORIG=copy.deepcopy(rows)
ck('D3 57 行每行 5 列', all(len(r)==5 for r in rows), {len(r) for r in rows})
f55=[r for r in rows if r[0]=='F55'][0]
S0,L0,E0=len(f55[1].encode()),len(f55[4].encode()),len(f55[3].encode())
ck('D4 F55 现态 stmt 10455 / lim 7691 / evid 311', (S0,L0,E0)==(10455,7691,311),(S0,L0,E0))
ck('D5 F55 grade 现态 [已证]', f55[2]=='[已证]', f55[2])

S11=('⑪ **（V577 新增 · R192 「同组同序号无匹配」的机械解释）** 上一段 ⑩ 留下「1,013 个直接槽没有同组同序号匹配（实测 0），'
'但这不等于证明它们语义上不同」；本轮把它做成可复算的结构判据，结论是**这些槽对根本不存在「同组」**：'
'把 1,013 个直接槽按「同 COL 修饰名、不同表、且该槽号在兄弟表里也存在」取第一张兄弟表分成三类 —— '
'**NOSIB 478 / DIRECT_OTHER 525 / THUNK_OTHER 10 / SAME 0**（478 个槽连一个兄弟表都没有该槽号，'
'535 个可比对里 525 个兄弟值是直接指针、10 个是调整器）。'
'**（i）535 对全部跨层**（两边 COL.offset-to-top 不同，535/535）。'
'**（ii）535 对全部跨接口层**：把每张表的「层基类身份」定义为 pCHD 基类数组里 PMD.mdisp 等于该表 COL.offset-to-top 的那条 BCD，'
'多条候选时取 numContainedBases 最大的一条（1,214 条 COL 全部解出唯一一条，0 个并列），其 pTD 名即层基类名；'
'则 535 对里两边层基类名相同的 **0** 对。前六个层基类对为 '
'INoticeSink→INoticeSource 75 / INoticeSource→INoticeSink 73 / UIPiggyback→UILocomotion 30 / '
'UILocomotion→UIPiggyback 30 / UILocomotion→{Fly,Hover,Locomotion,Mech,Rocket,Tunnel}LocomotionClass 各 7。'
'**（iii）不存在「不同 thunk 壳包同一 impl」**：把两目标的地址各自跟随无条件跳转'
'（E9 rel32 / EB rel8 / FF 25 绝对间址，带环与越界保护）后比对，**1 跳口径 COLLAPSE 0 / DISTINCT 535，'
'8 跳口径同样 0 / 535**；反控把 canon 换成恒等函数仍为 0（因为 525 对的两边值本来就不同），'
'把跟随范围收窄成「只跟 E9」也是 0，而把兄弟值人为替换成自身值则分类改判为 SAME（正控）。'
'**（iv）调用约定层面至少 295 对物理上不可能共用同一入口**：两侧目标的结尾 ret 立即数 **不同 295 对 / 相同 137 对 / '
'96 字节窗口内解不到 ret 103 对**；两侧前 16 字节完全相同的对 **0** 对。'
'最典型的一对是同宿主类 .?AVAbstractClass@@ 的主表槽 0 = 0x410260（75 个类共用）之外的另一组：'
'INoticeSink@mdisp8 槽 0 = 0x410580（32 C0 C2 08 00 = xor al,al; ret 8，75 个类共用）与 '
'INoticeSource@mdisp12 槽 0 = 0x410590（C2 04 00 = ret 4，78 个类共用）—— 同槽号、不同接口、不同参数个数。'
'**（v）接口子表层的槽一致性首次量化**：(层基类名, offset-to-top, 槽号) 键在 260 张接口子表上共 **110** 个，'
'其中单宿主键 43、多宿主键 67；多宿主键覆盖 **1,275** 个槽实例（调整器 288 + 直接槽 987），'
'键内取值完全一致的只有 **6** 个键，众数覆盖 **1,037/1,275 = 81.33%**；含主表的全镜像口径键数 **12,836**。')

L11=('**（V577 新增 · 与 ⑪ 同一批实测）** 边界：'
'（a）「层基类身份」是**结构判据不是语义判据** —— 它只说「这张接口子表按 RTTI 记录归属到哪个基类的哪一层」，'
'**不**说明该层各槽的语义名；本轮**没有**给任何槽装名字。'
'（b）1,214 条 COL 里有 **260 条** offset-to-top != 0，其中 **159 条**的层 BCD 候选唯一、**101 条**有 2 条候选（mdisp 相同、'
'pTD 不同，例如 mdisp 4 上同时有 UIRTTITypeInfo（ncb 1）与 IUnknown（ncb 0）、mdisp 1728 上同时有 UIFlyControl（ncb 1）与 IUnknown（ncb 0））；'
'取 ncb 最大的规则在 101 条上全部**消解为唯一**（0 个并列），但「ncb 最大 = 最外层」这条规则本身**未取得**编译器侧依据，'
'只证明它与「mdisp==0 的 954 条表首条 BCD 自证」口径一致。'
'（c）「103 对 96 字节内解不到 ret」的**口径**是：从目标地址线性反汇编，遇 jmp/int3/hlt 或窗口耗尽即判「无 ret」；'
'实测这 103 对**不含**无条件跳板（535 对的两侧目标全部不是 E9/EB/FF25 跳板），所以不是「跳板后面有 ret」造成的；'
'但**未**逐对做完整函数边界分析，因此「103 对里有多少真的没有 ret 指令」未取得。'
'（d）「众数覆盖 81.33%」的两端口径：分母是 67 个多宿主键覆盖的 1,275 个槽实例，分子是每个键里出现最多的那个实现的实例数；'
'单宿主键 43 个不进分母（它们恒为 100%，计入会把覆盖率抬到 98%+，属口径混淆）。'
'（e）反控清单：canon 换成恒等函数 ⇒ COLLAPSE 仍 0（正控是兄弟值替换成自身值 ⇒ 改判 SAME）；'
'只跟 E9 ⇒ 仍 0；把兄弟判据从「同 COL 修饰名」换成「同 pTD」⇒ 键空间从 954 组变 988 个 pTD（未改变 535 对全跨层的结论，'
'但该口径本轮**只做了键数核对**，未重跑五类分类）；把层名规则从 ncb 最大换成「取第一条」⇒ 101 条候选会落到 IUnknown，'
'接口键数从 110 变 43（说明规则敏感，故把它写进 (b) 的边界）。'
'（f）脚本 `_r192/r192e_deliver.py`（32 断言 0 FAIL）/ `_r192/r192c_layers.py`（13 断言 0 FAIL）/ '
'`_r192/r192b_why.py`（11 断言 0 FAIL）/ `_r192/r192f_archive.py`（21 断言 0 FAIL）；'
'执行员 #466（hy4，独立脚本）在 478/525/10/1013/535/0/0 七个计数上与本轮逐值一致。')

for nm,s in (('statement',S11),('limitations',L11)):
    ck('D7 %s 段无 tab / CR / LF'%nm, '\t' not in s and '\r' not in s and '\n' not in s)
    ck('D8 %s 段反引号成对（不改既有风格）'%nm, s.count('`')%2==0, s.count('`'))
ck('D9 ⑪ 段在 statement 里现态 0 次', f55[1].count(S11)==0)
f55[1]=f55[1]+S11
f55[4]=f55[4]+L11
NEWP='_r192/r192e_deliver.py;_r192/r192c_layers.py;_r192/r192b_why.py'
ck('D10 旧第 4 列不含 _r192', '_r192/' not in f55[3], f55[3])
f55[3]=f55[3]+';'+NEWP
ck('D11 新第 4 列含三条 _r192 路径',
   all(x in f55[3] for x in ('r192e_deliver.py','r192c_layers.py','r192b_why.py')))
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
nb=newtxt.encode()
R2=[l.split('\t') for l in newtxt.split('\n')[:57]]
ck('D12 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r')==0 and len(newtxt.split('\n'))==58 and all(len(x)==5 for x in R2))
ck('D13 只有 F55 一行变化', [a[0] for a,b in zip(ORIG,R2) if a!=b]==['F55'],
   [a[0] for a,b in zip(ORIG,R2) if a!=b])
ck('D14 F55 grade 未动', [r for r in ORIG if r[0]=='F55'][0][2]==f55[2])
exp=171758+len(S11.encode())+len(L11.encode())+len(NEWP.encode())+1
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
print('V577 = %d B / sha %s… / F55 stmt %d B / lim %d B / evid %d B'
      %(len(nb),hashlib.sha256(nb).hexdigest()[:16],len(f55[1].encode()),len(f55[4].encode()),len(f55[3].encode())))
sys.exit(0)
