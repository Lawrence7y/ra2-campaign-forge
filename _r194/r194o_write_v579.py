#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 落盘：台账 V578 -> V579。只改 F55 一行（statement 追加 ⑬、limitations 追加同批边界段、
第 4 列追加 10 条 _r194 路径）。
"""
import os, sys, copy, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
OLD=os.path.join(TIER,'R17_R131_FACTINDEX_V578','FACT_INDEX.tsv')
NEWD=os.path.join(TIER,'R17_R131_FACTINDEX_V579')
NEW=os.path.join(NEWD,'FACT_INDEX.tsv')
fails=[]; n=0
def ck(nm,c,d=''):
    global n; n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

raw=open(OLD,'rb').read()
ck('D1 旧 V578 = 184,812 B / sha 5093b704… / CR 0',
   len(raw)==184812 and hashlib.sha256(raw).hexdigest().startswith('5093b704') and raw.count(b'\r')==0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
TXT=raw.decode('utf-8'); L=TXT.split('\n')
ck('D2 58 段（57 行 + 空尾）', len(L)==58, len(L))
rows=[l.split('\t') for l in L[:57]]
ORIG=copy.deepcopy(rows)
ck('D3 57 行每行 5 列', all(len(r)==5 for r in rows), {len(r) for r in rows})
f55=[r for r in rows if r[0]=='F55'][0]
S0,L0,E0=len(f55[1].encode()),len(f55[4].encode()),len(f55[3].encode())
ck('D4 F55 现态 stmt 17512 / lim 13491 / evid 508', (S0,L0,E0)==(17512,13491,508), (S0,L0,E0))
ck('D5 F55 grade 现态 [已证]', f55[2]=='[已证]', f55[2])

S13=('⑬ **（V579 新增 · R194：L 的槽位-默认实现全图、两键闭包、CRC 覆盖范围状态机，以及三处口径订正）** 上一段 ⑫ 只给了四个实现的身份，'
'本轮把 L 的 78 张表在槽 0..17 上逐槽统计成一张可复算的映射表。'
'**（i）槽位图（L 的 78 张，槽号 / Top1 地址 / 覆盖张数 / 不同实现数）**：'
'槽 0 0x410260 75/3；槽 1 0x410300 74/3；槽 2 0x410310 74/3；槽 3 0x4C9150 9/70；槽 4 **0x410450 77/2**；槽 5 0x5F5E80 3/75；'
'槽 6 0x4C9150 4/75；槽 7 0x4103E0 61/5；槽 8 0x4105A0 1/78；槽 9 0x410470 72/6；槽 10 0x410480 35/37；槽 11 0x4C9150 9/70；'
'槽 12 0x4C9150 9/70；槽 13 0x5F6250 8/68；槽 14 0x410490 72/2；槽 15 0x4104A0 72/2；槽 16 0x4104B0 59/20；槽 17 0x410440 57/3。'
'**（ii）两键闭包**：A = 主表里槽 4 == 0x410450 的集合（**77** 张）；B = 主表里槽 9 == 0x410470 的集合（**72** 张）；'
'**A ∪ B 与 L 双向差集为 0**（精确 78 张），且 **B 减 A 恰为一个元素**：.?AVHouseTypeClass@@（主表 0x7EAB58，槽 4 = 0x512280、槽 9 = 0x410470）。'
'注意 A 与 B **不互斥**（|A∩B| = 71），上一版草稿写成「78 = 77 + 1 的互斥拆分」是错的，正确的闭合式是「并集等于 L，且差集单点」。'
'两条键在补集 876 张主表与 260 张接口子表上命中**均为 0**。'
'**（iii）11 核判据**：核 D = {(0,0x410260),(1,0x410300),(2,0x410310),(4,0x410450),(7,0x4103E0),(9,0x410470),(10,0x410480),'
'(14,0x410490),(15,0x4104A0),(16,0x4104B0),(17,0x410440)}；对每张主表算 h = 命中数。'
'**h >= 1 的集合精确等于 L（FP 0 / FN 0）**，补集 876 张与子表 260 张的 h **全为 0**；L 的 h 分布为 3..11（h=3 仅 1 张、h>=9 共 66 张）。'
'阈值 3 口径下恰有 3 项是必要项（剔除任一项则 FN=1）：(4,0x410450) / (7,0x4103E0) / (16,0x4104B0)；最小可达子集为 2 项（槽 4 + 槽 9）。'
'**（iv）槽 13 口径订正（推翻 ⑫ 的一处读法）**：槽 13 在 L 的 78 张表上共有 **68 个不同实现**，Top1 = **0x5F6250**（8 张，体内直接 call 0x410410，是包装/委派）；'
'**0x410410 只在 3 张表**上，即 .?AVAbstractClass@@（0x7E1F50）/ .?AVCellClass@@（0x7E4EEC）/ .?AVTactical@@（0x7F4348），'
'且它在全部 1,214 张表里**只出现这 3 次、位置都在槽 13**。⇒ ⑫ 把 0x410410 称作「AbstractClass 主表槽 13 的实现」应读作「3 张覆写表的槽 13 实现」，'
'它不是这条血统的槽 13 默认实现；序列化路径的字节闭合结论本身不受影响（那 3 张之外另有 8 张走 0x5F6250 委派）。'
'**（v）CRC 覆盖范围（⑫ 遗留未取得项）**：0x4A1CA0 的状态对象只用四个槽 —— +0x0 = CRC、+0x4 = 已填计数 0..4、+0x8..+0xB = 4 字节折叠缓冲、'
'+0xC = 折叠时的计数影子；**跨调用累进**（同一状态对象、同一张表，计数不清零即继续），未满 4 字节**不折**（cmp eax,4 + jne 直落 ret 块）。'
'⇒ 「每次调用重置 CRC」的读法被否掉（4+4 分两次喂的结果 == 一次性喂 8 字节，且 != zlib(后 4 字节)）。'
'**（vi）0x4A1DE0 体长与形态订正**：⑫ 记「154 条」是 **400 字节窗口截断**的结果；实测到首个 ret 是 **174 条 / 445 字节**（0x4A1DE0..0x4A1F9D，ret 8），'
'体内分四段：部分填充 0x4A1E00 / 4 字节批量 0x4A1E75（以 N=4 调 0x4A1FB0）/ 单字节 0x4A1EC2 / 尾部 0x4A1F40。'
'尾部规则：count = n 落在 1..3 时，buf[n] 写入 n 本身，buf[n+1..3] 用 buf[0] 填充，再折一次 4 字节；n == 0 直接返回。'
'⇒ 0x4A1DE0 是**通用 N 字节写 + 尾部补齐**，真正的「4 字节定长薄壳」只有 0x4A1D50（7 条）。'
'**（vii）CRC 表引用面**：0x81F7B4 的 disp32 在 .text 里共 **7 处**（指令形式一律为 mov reg,[reg*4+0x81F7B4] 的 SIB + disp32），'
'分属 **5 个例程**：0x4A1C10（50 条，ret 4）/ 0x4A1CA0（55 条，ret 4）/ 0x4A1DE0（174 条，ret 8）/ 0x4A1FB0（24 条，ret 4，通用 N 字节 crc32，被 0x4A1DE0 以 N=4 调用）'
'/ 0x4A1FF0（28 条，ret 无立即数，循环以 test dl,dl 判 NUL 结尾 ⇒ **C 字符串版**）。'
'**（viii）三个序列化辅助例程的调用面要给区间不给点估计**：以「字节模式 E8+rel32 且落点相等」为**上界 U**、以「该位置被递归下降解码成 call 且目标相等」为**下界 L**，'
'得 0x4A1CA0 = 331 / 94 / 假命中 237；0x4A1D50 = 460 / 131 / 329；0x4A1DE0 = 87 / 69 / 18；三组都满足 U = L + F。'
'0x410410 同时是 0x4A1CA0 与 0x4A1D50 两条写路径的**共同宿主起点**（其体内两次 call 依次为 0x4A1D50 → 0x4A1CA0）。')

L13=('**（V579 新增 · 与 ⑬ 同一批实测）** 边界：'
'（a）⑬(i) 的 18 个 Top1 地址只是**结构身份**（槽号 + 覆盖张数 + 体形态），**一律没有**装游戏语义名；'
'「返回 !Dirty」「序列化」「读接口子对象」这类说法都是从字节形态推出的行为描述，不是符号名。'
'（b）⑬(v) 的「覆盖范围 = 整段累进」只说明**同一状态对象**内的多次写入是连续累积的，'
'**没有**证明这段累积覆盖的是存档里的哪一段（是对象整段、还是某个字段组），也没有证明初值来自何处（0x4A1D50 与 0x4A1CA0 都不设置 +0x0）。'
'（c）⑬(viii) 的三组数**不是同一个量**：上界 U 含落在数据里/指令中间的假命中，下界 L 依赖递归下降的可达性，'
'两者都不能单独当作「该函数被调用 N 次」发布；可复算的只有「U = L + F」这条记账恒等式与每个 L 元素附带的 5 字节 E8 指令原文。'
'执行员 #474 报的 190 / 177 / 32 三个点估计与本轮 L 不一致（其方法混用了「lite 线性扫描」与「播种合并」两套口径），已否；'
'其「lite 线性扫描在 0x4A1D0B 失步」的说法也被否：该地址在 lite 线性扫描下正常命中。'
'其「0x81F7B4 共 5 处引用」漏了 0x4A1FD3 与 0x4A200E 两处（后者所在例程 0x4A1FF0 未被任何种子覆盖，只能靠字节口径发现）——'
'这条「递归下降会漏掉不可达函数」正是本轮保留字节口径的理由。'
'（d）⑬(vi) 的尾部规则是从指令序列读出的，**未做**运行期插桩验证；「buf[n]=n 后 buf[n+1..3]=buf[0]」是字节级等价模型，'
'不是对存档产物的实测。'
'（e）跨家族审计员 #475（deepseek，13 回合成功）独立复算成立的部分：L = 78（类名与地址集合逐个一致）、'
'主表 954 / 槽总 14044、以及「按 COL 地址比 0x410220 与 L 交集为 0，按类名比才为 78」这一订正；'
'其指出的「卡面把 d0 说成主表判据」也成立（d0 是 signature 恒 0，分界字段是 d1）。'
'它给出的 Q2/Q3/Q4 三个回答本轮**未采用为结论**：Q2 的「含 ObjectClass 可区分」实测在补集上恒假（0/876），无鉴别力；'
'Q3 的「L 与补集槽数区间重叠 44 张」与本轮 ⑬(iii) 的核判据是不同问题，不构成矛盾；'
'Q4 的「1-based 第 13 槽 Top5」与「0-based idx13」两套口径它都列了，本轮统一按 **0-based 槽 13** 表述并已给出 3 张宿主。'
'（f）脚本 `_r194/r194a_crcpath.py`（23 断言 0 FAIL）/ `_r194/r194f_verify.py`（10）/ `_r194/r194e_slotmap.py`（12）/ '
'`_r194/r194g_recdesc.py`（3 通过 2 失败，仅作方法对照，不用于结论）/ `_r194/r194h_bracket.py`（6）/ '
'`_r194/r194i_mechanism.py`（6，含 1 条判据写反）/ `_r194/r194j_core.py`（4，含 1 条判据写反）/ '
'`_r194/r194k_controls.py`（16，含 4 条判据写反）/ `_r194/r194l_twokey.py`（13，含 1 条判据写反）/ '
'`_r194/r194m_strcrc.py`（4）/ `_r194/r194n_final.py`（**19 断言 0 FAIL**，把上述写反的六条判据按实测定稿）。'
'写反的六条一律按实测订正、未进入结论：⑬(iii) 的「h>=1 不够充分」实为 FN=0；'
'「每核剔除后应保持相等」实为 3 项剔除后 FN=1；「0x410260 错 4 字节即失去判别力」实为仍 78 张；'
'⑬(ii) 的「两键互斥」实为交集 71；(viii) 的「递归下降与字节口径同数」实为 6 对 7。'
'（g）F23 / F35 的 grade 本轮未动；coverage.tsv 与 function_atlas.tsv 仍不可读，相关五个数与分母仍禁止预估回填；'
'86.19% 原值仍不可重算；C7 三死分支仍各 0 行；C11 十二个永不 FAIL id 未动；④ 的 32 条部分失联事实项定性未在本轮投入。')

NEWP=('_r194/r194a_crcpath.py;_r194/r194e_slotmap.py;_r194/r194f_verify.py;_r194/r194h_bracket.py;'
      '_r194/r194i_mechanism.py;_r194/r194j_core.py;_r194/r194k_controls.py;_r194/r194l_twokey.py;'
      '_r194/r194m_strcrc.py;_r194/r194n_final.py')
for nm,s in (('statement',S13),('limitations',L13)):
    ck('D7 %s 段无 tab / CR / LF'%nm, '\t' not in s and '\r' not in s and '\n' not in s)
    ck('D8 %s 段反引号成对'%nm, s.count('`')%2==0, s.count('`'))
ck('D9 ⑬ 段在 statement 里现态 0 次', f55[1].count(S13)==0)
f55[1]=f55[1]+S13
f55[4]=f55[4]+L13
ck('D10 旧第 4 列不含 _r194', '_r194/' not in f55[3], f55[3])
f55[3]=f55[3]+';'+NEWP
ck('D11 新第 4 列含十条 _r194 路径',
   all(x in f55[3] for x in NEWP.split(';')))
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
nb=newtxt.encode()
R2=[l.split('\t') for l in newtxt.split('\n')[:57]]
ck('D12 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r')==0 and len(newtxt.split('\n'))==58 and all(len(x)==5 for x in R2))
ck('D13 只有 F55 一行变化', [a[0] for a,b in zip(ORIG,R2) if a!=b]==['F55'],
   [a[0] for a,b in zip(ORIG,R2) if a!=b])
ck('D14 F55 grade 未动', f55[2]=='[已证]', f55[2])
exp=184812+len(S13.encode())+len(L13.encode())+len(NEWP.encode())+1
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
print('V579 = %d B / sha %s… / F55 stmt %d B / lim %d B / evid %d B'
      %(len(nb),hashlib.sha256(nb).hexdigest()[:16],len(f55[1].encode()),len(f55[4].encode()),len(f55[3].encode())))
sys.exit(0)
