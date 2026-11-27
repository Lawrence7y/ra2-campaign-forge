# -*- coding: utf-8 -*-
"""R186 HH：四件套追加（fail-closed：旧 sha + CR 硬闸，全部断言在写盘之前）。
看板当前 249 行 < 260 ⇒ 本轮不归档，直接追加。
  R14_COMMON.md  ## 2.191   (CR 1081)
  台账           ## §1241   (CR 337)
  LEAD_LOCK      ## PP · R17 第 186 轮 (CR 137)
  STATUS_BOARD   第 186 轮记录 (CR 0, 行数 <= 300)
"""
import hashlib, io, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
RC = os.path.join(TIER, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(TIER, 'STATUS_BOARD.md')
stamp = time.strftime('%Y%m%d_%H%M%S')
HARD = {RC: 1081, LED: 337, LOCK: 137, BRD: 0}
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
pre = {}
for p, cr in HARD.items():
    b = open(p, 'rb').read(); pre[p] = b
    ck('H0 %s 存在且 CR == %d' % (os.path.basename(p), cr), b.count(b'\r') == cr, b.count(b'\r'))
ck('H4 看板 %d 行 < 260 ⇒ 本轮不归档' % pre[BRD].count(b'\n'), pre[BRD].count(b'\n') < 260, pre[BRD].count(b'\n'))

SEC_COMMON = '''
## 2.191 R186：类对象模型的**层结构**在代码侧闭合（954 组 / 1,214 层 / 12 类取 mdisp==4 层），并撤回 r186b 四个覆盖不足的数

R186 的入口仍是用户裁定的第一优先级：gamemd.exe 静态二进制本体取证。R185 把四条 RTTI 链（vtable → COL → TD → CHD → BCD）全量复原了；本轮接着往下一层问一个 R185 没问的问题：**一个类有多张 vtable 时，构造器把它们各自装在对象的哪个偏移上？** 答案把 R185 那条「12 个 Locomotion 类的 vtable_va 指向次对象」从「RTTI 侧的推断」变成了「代码侧的实测」。

**一·层结构：954 组、1,214 层、算术闭合.** `_r186/r186b_ctor.py`（**28 断言 0 FAIL**）不依赖 symbols.json，全镜像枚举 **1,214** 个 COL、**1,214** 张 vtable，按 pTD 分组得 **954** 组；每组内 mdisp **两两不同**、且**恰含一个 mdisp==0**；层数直方图 **{1:860, 2:10, 3:6, 4:76, 5:1, 7:1}**，Σ 层数 **= 1,214**（与总 COL 数算术闭合）。一句人话：**一个类有几张 vtable，等价于它把自己在几个基类子对象位置上暴露给外界**，而 0 层永远是它在对象偏移 0 上的主接口。

**二·symbols.json 的取层规则（新事实）.** 954 条里 **942** 条取 mdisp==0 层、**12** 条取 mdisp==4 层。关键在后者：这 12 个类**同时也存在 mdisp==0 层**（12/12），所以 symbols 在这 12 类上**偏离**了「取 0 层」这条本可成立的规则。12 个全是 Locomotion 系（Locomotion + Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk）。

**三·代码侧证据：装点位移 == COL.mdisp（87.40%）.** `_r186/r186c_descent.py`（**23 断言 0 FAIL**）用两道互相独立的口径扫 `.text`：口径 A 是 `C7 /0` 字节模式（含 SIB，能自同步、不会因错位连锁丢失），命中 **5,731** 条；口径 B 是从「PE 入口 + 13,204 个 vtable 槽 + 数据节里指向 .text 的 dword」出发的**递归下降**，到达 **1,092,207** 个指令起点；两者交集 **4,886** 条（字节模式的假命中 **845** 条如实计数）。交集里基址非 esp/ebp 且无索引的 **3,666** 条中，位移**等于该 vtable 的 COL.mdisp** 的有 **3,204** 条 = **87.40%**。放宽到「位移 ∈ 该 TD 在全镜像 CHD 里出现过的 mdisp 集合」得 **3,255** = **88.79%**；残差 **411** 条里 **387** 条落在模板/容器类（`?$TypeList@H` 69、`?$DynamicVectorClass@PAVAbstractClass@@` 12、`GenericList` 11 等），**24** 条落在非模板类，真个例恒为 **3** 条（**004A8660** LayerClass / 位移 −8、**004F73CA** BaseClass / 22,272、**00632CE0** BlowPipe / 20）。

**四·12 个 Locomotion 类的 3 层装点（F29 的规则在代码侧被证实）.** 这 12 个类的 `mdisp==4` 表 **12/12** 被装到对象 **+4**（装点位移集合恒为 {4}），对应 `mdisp==0` 表 **12/12** 被装到 **+0**（且在 +4 上 **0 次**）⇒ F29 要求的「取 mdisp==0 主虚表」不是措辞：主表确实装在偏移 0。其中 6 个类（Drive / DropPod / Jumpjet / Ship / Teleport / Walk）另有 **mdisp==24** 的第三接口表，同样被装到 **+0x18（= 24）**，装点位移集合恒为 {24} ⇒ 装点位移 == COL.mdisp 这条关系在 3 层上同时成立。

**五·撤回：r186b 首版的四个数是覆盖不足下的下限.** `_r186/r186d_audit_recheck.py`（**17 断言 0 FAIL**）实测「从 .text 起点 64 KB 分块线性反汇编」**只消费 3,360,178/4,063,232 = 82.70% 字节**、**53 个块提前终止**（停在 .text 内嵌的指针表处，capstone 不重同步）。因此 r186b 首版报的 **4,720 / 4,564 / 3,216 / 3,009** 四个数**不得再引**；改用交叉口径后报 **5,731 / 4,886 / 3,666 / 3,204**。同一份复算也推翻 r186b 的一句「FlyLocomotionClass / TunnelLocomotionClass 无 imm32 装点」—— 这两张表各有 **4 条 / 2 条**标准装点（Fly: 004CCA12 / 004CCA76 / 004CFCDE / 004D03A9，Tunnel: 00728A42 / 0072A18C，位移全为 4）。**根因写清**：`0x4CCA0C` 处 `c706c08a7e00` 是 `mov dword ptr [esi], 0x7e8ac0`，线性扫描在该处输出的是 `46`（`inc esi`）/ `5c`（`pop esp`）—— 错位一格就整片丢失。

**六·布局事实：COL 与 vtable 不是相邻布局.** **COL+16 恰等于其配对 vtable 基址的个数 = 0/1214**；gap（vtable − COL）全为负、范围 −106,000..−84,760、**916** 个不同值 ⇒ 「每 COL 恰一张表」是**构造性事实**（vtable 的识别条件就是「首 dword ∈ .text 且前一 dword == 某 COL 地址」），不是独立发现的镜像性质。要判它真有结构意义需要布局佐证，而布局佐证**失败**。另：只算 `.?AV`（排除 `.?AU`）时 COL 与 vtable 都是 **1,212**、组数 **952**，故 1,214 / 954 这两个数依赖把 struct 侧 RTTI 也算进来。

**七·落盘与门禁.** 台账 **V567 → V568**：F01 limitations 9,651 → **12,239**、F29 limitations 15,256 → **16,840**，总 **144,718 B**（+4,172）、**55 行 5 列**、CR 0、sha **`335b403d…`**；其余 52 行逐单元格相同，两行只有第 5 列变。重钉 `_r186/r186f_repin.py`（**40 断言 0 FAIL**）：旧常量复算旧 MASTER **`60f5b21c…`** 命中旧 pin 作硬闸 → MASTER → **`7ee9f8ac…`**，`FLOORS['F01']` (458,9651)→(458,12239)、`FLOORS['F29']` (3435,15256)→(3435,16840)，gate_runner 1 行，指针四字段（含把自述「530..567 / 38 份」改准为「530..568 / 39 份」、声明轮次 R185→R186）。**三门终态**：`check_disc.py` exit 0（C19 ok(335b403d/144718/V568)、C20 ok(V568)）、`facts_floors.py` exit 0（D8 floor == 144,718、D9/D10 双一致）、`gate_runner.py` G1=G2=G3=ok。看板 249 行 < 260 ⇒ 本轮不归档。

**八·跨家族（执行一件 + 审计一件，审计 OVERTIME）.** 执行员 **#447**（hy4 / 10 回合 / 2.0 分 / 120 s）用 pefile 独立推导段边界、不复用主会话的公共模块，六个数字逐值复现（1214/1214/4720/4564/3216/3009），并**主动报出**「卡面要求 4 字节对齐滑窗，但只有按任意字节偏移才复现得出来」这条口径差（已采纳并写进本条五）。审计员 **#448**（deepseek / 20 回合 / 16.2 分 / **OVERTIME：16.2 分 vs 预算 2.0 分**）五条主张：主张 1/2/3 成立；**主张 4/5 的「82.70% 覆盖」与「4520→5894」被主会话 `r186d` 逐值复算成立并采纳**，四个旧数字就地撤回；主张 6 的「2 张无装点不成立」**经复算成立**（两条 false 都已推翻）；其「全覆盖 3735/4051 = 92.20%、残差 265、模板 262 / 个例 3」也被主会话独立复算**逐值相同**（本判据得 3,737/4,053 = 92.20%、残差 265、模板 262、个例恰是那 3 条）。

**九·自错 S-186a1..S-186h1（八处，全部当场抓出，无一条进入结论）.** **a1** 首版把「store 位移 == mdisp」当成 100% 可失败的铁律写断言，实测只有 **93.56%**（残差 168 条全是模板容器的成员装点）⇒ 断言红，改成三层口径；**b1** 首版对「每张表只有一个装点位移」下了全称断言，实测多位移（`?$DynamicVectorClass@PAVTechnoClass@@` 同时被装在 0 / 224 / 8910320…）⇒ 撤回该全称；**c1** 首版把「该 TD 的层集合」算成「全镜像 CHD 出现过的 mdisp」两回事混写，导致 3052 与 3048 两个数各自被当成对方；**d1** 首版拿 `d2`（COL 的 pdisp）当「层数」判据；**e1** `r186c` 首版用 `operands[0].type` 读 capstone 操作数，`detail=False` 下直接抛 `CS_ERR_DETAIL` —— **崩溃被当成判据失败**，改判据后才看出要逐条开 detail；**f1** `r186c` 第二版逐条 `detail=True` 解码 110 万条，跑满超时被后台化；**g1** `r186e` 在 `rows` 原地改完才快照，导致「只有两行变化」的断言恒得空集（假 PASS 方向）；**h1** `r186f` 首版把 F29 的 floor 只在注释里改、源码里漏改，被 `G3j` 用新常量复算 MASTER 抓出。**族谱**：「把崩溃当判据失败」**第五次**（e1）；「把应然数当实测」**第十七次**（c1/d1）。

**十·未取得（不粉饰）.** ① 「装点位移 == mdisp」的残差 411 条里那 **24** 条非模板类个例只逐条登记、未给出统一解释（其中 3 条真个例已逐字节核对）；② 全镜像 **10** 张表找不到任何 imm32 装点（`?$DynamicVectorClass@PAE` / `?$DynamicVectorClass@PAU_DDSURFACEDESC@@` / `CarryoverClass` / `Dial8Class` / `PKPipe` / `TextButtonClass` / `TriColorGaugeClass` 等）—— 可能被非 mov 形态装载，未穷举；③ 递归下降的可达性依赖种子集合，不可达但真实存在的构造函数仍会漏计，该下限未穷举；④ F01 statement 的 1201 / 1211 仍不可复现；⑤ F23 / F35 grade 未改；⑥ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ 「哪份是当前版」仍无人覆盖。
'''

SEC_LEDGER = '''
## §1241 R186：类对象模型的层结构在代码侧闭合；装点位移 == COL.mdisp 87.40%；撤回 r186b 四个覆盖不足的数

**一·层结构（954 组 / 1,214 层 / 算术闭合）.** `_r186/r186b_ctor.py` **28 断言 0 FAIL**：全镜像 1,214 COL、1,214 vtable，按 pTD 分 **954** 组，每组 mdisp **两两不同**且**恰含一个 0**；直方图 **{1:860, 2:10, 3:6, 4:76, 5:1, 7:1}**，Σ **= 1,214**。

**二·symbols 取层规则.** **942** 类取 mdisp==0 层、**12** 类取 mdisp==4 层；那 12 类**同时有 0 层**（12/12）⇒ symbols 在 12 类上偏离「取 0 层」规则，12 个全为 Locomotion 系。

**三·代码侧证据（交叉口径）.** `_r186/r186c_descent.py` **23 断言 0 FAIL**：口径 A（`C7 /0` 字节模式含 SIB）**5,731**；口径 B（递归下降，种子 = 入口 + 13,204 槽 + 数据节 .text 指针，到达 **1,092,207** 个指令起点）；交集 **4,886**（假命中 **845**）。交集中对象寄存器 store **3,666**，`disp == COL.mdisp` **3,204 = 87.40%**；放宽到 CHD 出现过的 mdisp **3,255 = 88.79%**；残差 **411**（模板/容器 **387**、非模板 **24**，真个例恒 3 条：004A8660/−8、004F73CA/22272、00632CE0/20）。

**四·12 个 Locomotion 的 3 层装点.** `mdisp==4` 表 **12/12** 装到 **+4**（位移集合恒 {4}）、`mdisp==0` 表 **12/12** 装到 **+0**（+4 上 0 次）⇒ F29 的「取 mdisp==0 主虚表」在代码侧被证实。其中 6 类另有 `mdisp==24` 第三接口表，装到 **+0x18**，位移集合恒 {24}。

**五·撤回（四个数 + 一句）.** `_r186/r186d_audit_recheck.py` **17 断言 0 FAIL**：64 KB 分块线性反汇编**只消费 82.70% 字节**（3,360,178/4,063,232）、**53 块提前终止** ⇒ r186b 首版 **4,720 / 4,564 / 3,216 / 3,009** 是下限、**不得再引**；「Fly / Tunnel 无装点」被推翻（各有 4 / 2 条装点，位移全为 4）。根因：`0x4CCA0C` 的 `c706c08a7e00` 被线性扫描读成 `inc esi` / `pop esp`。

**六·布局事实.** **COL+16 == 配对 vtable 基址 的个数 = 0/1214**；gap 全负、−106,000..−84,760、916 个不同值 ⇒ 「每 COL 恰一张表」是构造性事实。只算 `.?AV` 时 COL/vtable **1,212**、组数 **952**。

**七·落盘.** V567 → **V568**（F01 lim 9,651→**12,239**、F29 lim 15,256→**16,840**，**144,718 B / `335b403d…` / CR 0 / 55 行 5 列**），其余 52 行逐单元格相同；重钉 **40 断言 0 FAIL**（MASTER `60f5b21c…`→**`7ee9f8ac…`**、F01/F29 两处 floor、gate_runner 1 行、指针四字段含自述改准为「530..568 / 39 份」）；三门 exit 0 / G1=G2=G3=ok；看板 249 < 260 ⇒ 不归档。
'''

SEC_LOCK = '''
## PP · R17 第 186 轮（2026-11-28 2x–3x）· 类对象模型的层结构在代码侧闭合（954 组 / 1,214 层）；装点位移 == COL.mdisp 3,204/3,666 = 87.40%；撤回 r186b 四个覆盖不足的数；审计「82.70% 覆盖」被复算坐实

**PP1. 🔴 交付一：把「一个类有多张 vtable = 多个基类子对象位置」做成 954/954 可失败.** `_r186/r186b_ctor.py` **28 断言 0 FAIL**：全镜像 **1,214** COL、**1,214** vtable，按 pTD 分组得 **954** 组；每组 mdisp **两两不同**（0 例外）且**恰含一个 mdisp==0**（954/954）；层数直方图 **{1:860, 2:10, 3:6, 4:76, 5:1, 7:1}**，Σ 层数 **= 1,214 == 总 COL 数**（算术闭合）。反控五条：关掉 SIB 命中降 1,188 / 位移+1 判等 0 命中 / mdisp 换常数 0 命中骤减 / vtable+4 当 COL 命中 110/3216 / 层集合换成 {0} 退化。

**PP2. ✅ 交付二：symbols.json 的取层规则首次量化.** **942** 类取 mdisp==0 层、**12** 类取 mdisp==4 层；那 **12** 个类**同时也存在 mdisp==0 层**（12/12）⇒ symbols 在 12 类上**偏离**「取 0 层」这条本可成立的规则；12 个全为 Locomotion 系。⇒ 上一轮（R185）「vtable_va 语义不统一」这条现在有了**选择规则**的形式，不再只是「语义不同」。

**PP3. 🔴 交付三：装点位移 == COL.mdisp 的交叉口径实测.** `_r186/r186c_descent.py` **23 断言 0 FAIL**：口径 A（`C7 /0` 字节模式、含 SIB、自同步）**5,731** 条；口径 B（递归下降，种子 = PE 入口 + 13,204 个 vtable 槽 + 数据节里指向 .text 的 dword，去重 **18,961**，到达 **1,092,207** 个指令起点）；**交集 4,886**，字节模式假命中 **845** 如实计数。交集中基址非 esp/ebp 且无索引的 **3,666** 条里，位移 **== COL.mdisp** 的 **3,204 = 87.40%**；放宽到 CHD 出现过的 mdisp **3,255 = 88.79%**；残差 **411**（模板/容器 **387**、非模板 **24**），真个例恒 **3** 条：**004A8660** LayerClass/−8、**004F73CA** BaseClass/22272、**00632CE0** BlowPipe/20。

**PP4. 🔴 交付四：F29 那条「取 mdisp==0 主虚表」在代码侧被证实，并测出第 3 层.** 12 个 Locomotion 类的 `mdisp==4` 表 **12/12** 被装到 **+4**（装点位移集合恒 {4}，无一张装在其它位移），`mdisp==0` 表 **12/12** 被装到 **+0**（+4 上 **0 次**）。其中 6 类（Drive / DropPod / Jumpjet / Ship / Teleport / Walk）另有 **mdisp==24** 的第三接口表，装在 **+0x18（= 24）**，位移集合恒 {24} ⇒ 装点位移 == mdisp 在 3 层上同时成立。

**PP5. 📌 交付五：撤回 r186b 首版四个数（覆盖不足的下限）.** `_r186/r186d_audit_recheck.py` **17 断言 0 FAIL**：「64 KB 分块从 .text 起点线性反汇编」**只消费 3,360,178/4,063,232 = 82.70% 字节**、**53 块提前终止**（停在 .text 内嵌指针表，capstone 不重同步）⇒ **4,720 / 4,564 / 3,216 / 3,009** 四个数**不得再引**；「FlyLocomotionClass / TunnelLocomotionClass 无 imm32 装点」也被推翻（各 **4 条 / 2 条**，位移全为 4：Fly 0x4CCA12 / 0x4CCA76 / 0x4CFCDE / 0x4D03A9，Tunnel 0x728A42 / 0x72A18C）。根因逐字节写清：**0x4CCA0C 的 `c706c08a7e00` = `mov dword ptr [esi], 0x7e8ac0`**，线性扫描在此输出 `46`（inc esi）/ `5c`（pop esp），错一格整片丢失。

**PP6. 📌 交付六：布局事实 —— COL 与 vtable 不是相邻布局.** **COL+16 恰等于其配对 vtable 基址的个数 = 0/1214**；gap（vtable − COL）全为负、−106,000..−84,760、**916** 个不同值 ⇒ 「每 COL 恰一张表」是**构造性事实**（识别条件就是「首 dword ∈ .text 且前一 dword == 某 COL」），不是独立发现的镜像性质；要判其有结构意义需布局佐证，而布局佐证失败。另：只算 `.?AV`（排除 `.?AU`）时 COL/vtable 都是 **1,212**、组数 **952** ⇒ 1,214 / 954 依赖把 struct 侧 RTTI 也算进来。

**PP7. ✅ 交付七：落盘 + 重钉 + 三门.** 台账 **V567 → V568**：F01 limitations 9,651 → **12,239**、F29 limitations 15,256 → **16,840**，总 **144,718 B（+4,172）/ 55 行 5 列 / CR 0 / sha `335b403d…`**；其余 **52** 行逐单元格相同，两行**只有第 5 列变**。重钉 `_r186/r186f_repin.py` **40 断言 0 FAIL**：旧常量复算旧 MASTER **`60f5b21c…`** 命中旧 pin 作硬闸 → MASTER **`7ee9f8ac…`**，`FLOORS['F01']` (458,9651)→(458,12239)、`FLOORS['F29']` (3435,15256)→(3435,16840)，gate_runner 1 行，指针四字段（自述「530..567 / 38 份」改准为「530..568 / 39 份」、声明轮次 R185→R186）。**三门终态**：`check_disc` exit 0（C19 ok(335b403d/144718/V568) / C20 ok(V568)）、`facts_floors` exit 0（D8 floor == 144,718、D9+D10 双一致）、`gate_runner` G1=G2=G3=ok。看板 **249 < 260** ⇒ 本轮**不归档**。

**PP8. 📌 自错 S-186a1..S-186h1（八处，全部当场抓出，无一条进入结论）.** **a1** 首版把「store 位移 == mdisp」写成 100% 铁律，实测 **93.56%** ⇒ 断言红，改三层口径；**b1** 首版对「每张表只有一个装点位移」下全称断言，实测多位移（`?$DynamicVectorClass@PAVTechnoClass@@` 同时被装在 0/224/8910320…）⇒ 撤回；**c1** 把「该 TD 的层集合」与「全镜像 CHD 出现过的 mdisp」混写 ⇒ 3052 与 3048 各自被当成对方；**d1** 拿 COL 的 `pdisp` 当「层数」判据；**e1** `r186c` 首版用 `operands[0].type` 而 `detail=False` ⇒ 抛 `CS_ERR_DETAIL` —— **崩溃当判据失败**；**f1** 第二版逐条 `detail=True` 解 110 万条跑满超时被后台化；**g1** `r186e` 在 `rows` **原地改完才快照** ⇒「只有两行变化」恒得空集（假 PASS 方向）；**h1** `r186f` 首版 F29 floor 只在注释里改、源码漏改，被 `G3j` 用新常量复算 MASTER 抓出。**族谱**：「把崩溃当判据失败」**第五次**（e1）；「把应然数当实测」**第十七次**（c1/d1）。

**PP9. 📌 跨家族（执行一件 + 审计一件，审计 OVERTIME）.** 执行员 **#447**（hy4 / 10 回合 / 2.0 分 / 120 s）用 pefile 独立推导段边界、不复用公共模块，六数逐值复现（1214/1214/4720/4564/3216/3009），并**主动报出**口径差：「卡面要求 4 字节对齐滑窗，但只有按任意字节偏移才复现得出来」（已采纳并写进 PP3/§2.191 五）。审计员 **#448**（deepseek / 20 回合 / **16.2 分 vs 预算 2.0 分 ⇒ OVERTIME**）五条主张：**1/2/3 成立**；**4/5 的「82.70% 覆盖」与「应按全覆盖重标」被主会话 `r186d` 逐值复算坐实并采纳**（四个旧数就地撤回）；**6「2 张无装点不成立」经复算成立**。其「3735/4051 = 92.20%、残差 265、模板 262 / 个例恒 3」被主会话独立复算**逐值相同**（本判据 3,737/4,053 = 92.20%、残差 265、模板 262、个例恰那 3 条）。

**PP10. 📌 未取得（不粉饰）.** ① 残差 411 条里 **24** 条非模板类个例只逐条登记、未给统一解释（其中 3 条真个例已逐字节核对）；② 全镜像 **10** 张表找不到任何 imm32 装点（`?$DynamicVectorClass@PAE`、`?$DynamicVectorClass@PAU_DDSURFACEDESC@@`、`CarryoverClass`、`Dial8Class`、`PKPipe`、`TextButtonClass`、`TriColorGaugeClass` 等）—— 可能是非 mov 形态装载，未穷举；③ 递归下降的可达性依赖种子集合，不可达但真实存在的构造函数仍会漏计，该下限未穷举；④ F01 statement 的 1201 / 1211 仍不可复现；⑤ F23 / F35 grade 未改；⑥ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ 「哪份是当前版」仍无人覆盖。
'''

SEC_BOARD = '''
## 🟢 R17 第 186 轮（2026-11-28 2x–3x）· 类对象模型的**层结构**在代码侧闭合（954 组 / 1,214 层 / 12 类取 mdisp==4 层）；装点位移 == COL.mdisp **3,204/3,666 = 87.40%**；撤回 r186b 四个覆盖不足的数；审计「82.70% 覆盖」被复算坐实

**交付一（层结构）**：`_r186/r186b_ctor.py` **28 断言 0 FAIL** —— 全镜像 1,214 COL / 1,214 vtable，按 pTD 分 **954** 组，每组 mdisp **两两不同**且**恰含一个 0**，直方图 **{1:860, 2:10, 3:6, 4:76, 5:1, 7:1}**，Σ 层数 **= 1,214**（与 COL 总数算术闭合）。

**交付二（取层规则）**：symbols.json **942** 类取 mdisp==0 层、**12** 类取 mdisp==4 层；这 12 类**也都有 0 层**（12/12）⇒ 偏离「取 0 层」规则，且全为 Locomotion 系。

**交付三（代码侧证据）**：`_r186/r186c_descent.py` **23 断言 0 FAIL** —— 口径 A（`C7 /0` 字节模式含 SIB）5,731 / 口径 B（递归下降，到达 1,092,207 个指令起点）/ 交集 4,886（假命中 845）；对象寄存器 store **3,666** 里 `disp == COL.mdisp` **3,204 = 87.40%**，放宽 **3,255 = 88.79%**，残差 411（模板 387 / 非模板 24），真个例恒 3（004A8660 LayerClass/−8、004F73CA BaseClass/22272、00632CE0 BlowPipe/20）。

**交付四（F29 在代码侧被证实）**：12 个 Locomotion 类的 mdisp==4 表 **12/12** 装到 **+4**、mdisp==0 表 **12/12** 装到 **+0**（+4 上 0 次）；其中 6 类另有 mdisp==24 第三接口表装到 **+0x18**。

**交付五（撤回）**：`_r186/r186d_audit_recheck.py` **17 断言 0 FAIL** —— 64 KB 分块线性反汇编**只消费 82.70% 字节**（3,360,178/4,063,232）、**53 块提前终止** ⇒ **4,720 / 4,564 / 3,216 / 3,009** 是下限、**不得再引**；「Fly / Tunnel 无装点」被推翻（各 4 / 2 条，位移全 4）。根因：**0x4CCA0C 的 `c706c08a7e00`** 被读成 `inc esi` / `pop esp`。

**交付六（布局事实）**：**COL+16 == 配对 vtable 基址 的个数 = 0/1214**；gap 全负 −106,000..−84,760、916 个不同值 ⇒ 「每 COL 恰一张表」是构造性事实；只算 `.?AV` 时 COL/vtable 1,212、组数 952。

**交付七（落盘）**：V567 → **V568**：F01 lim 9,651→**12,239**、F29 lim 15,256→**16,840**，**144,718 B / `335b403d…` / CR 0 / 55 行 5 列**，其余 52 行逐单元格相同、两行只有第 5 列变；重钉 **40 断言 0 FAIL**（MASTER `60f5b21c…`→**`7ee9f8ac…`**、F01/F29 两处 floor、gate_runner 1 行、指针四字段含自述改准为「530..568 / 39 份」）。**三门** exit 0 / exit 0 / G1=G2=G3=ok；看板 249 < 260 ⇒ 不归档。

**跨家族**：执行员 **#447**（hy4 / 10 回合 / 2.0 分）六数逐值复现，**主动报出**「只有按任意字节偏移才复现得出来」的口径差（已采纳）；审计员 **#448**（deepseek / **20 回合 / 16.2 分 vs 预算 2.0 分 ⇒ OVERTIME**）五条主张：1/2/3 成立，4/5 的「82.70% 覆盖」与「应重标」**被主会话复算坐实并采纳**（四个旧数就地撤回），6「2 张无装点不成立」**经验证成立**；其「3735/4051 = 92.20%、残差 265、模板 262」被主会话独立复算**逐值相同**。

**自错 S-186a1..S-186h1（八处，全部当场抓出）**：把「位移==mdisp」写成 100% 铁律（实测 93.56%）；对「每表只有一个装点位移」下全称断言（多位移）；把「TD 层集合」与「CHD 出现过的 mdisp」混写（3052/3048 互换）；拿 COL.pdisp 当层数；`detail=False` 读 operands 抛 `CS_ERR_DETAIL`（**崩溃当判据**）；逐条 detail 解 110 万条跑满超时；`r186e` 原地改完才快照致「只两行变」恒空集；`r186f` F29 floor 只在注释里改。**族谱**：「把崩溃当判据失败」**第五次**；「把应然数当实测」**第十七次**。

**未取得**：① 残差里 24 条非模板个例只登记未解释；② 10 张表找不到 imm32 装点，可能非 mov 形态装载；③ 递归下降依赖种子集合，不可达的构造函数仍会漏计；④ F01 的 1201/1211 仍不可复现；⑤ F23/F35 grade 未改；⑥ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ 「哪份是当前版」仍无人覆盖。
'''

for nm, s in (('R14_COMMON 2.191', SEC_COMMON), ('台账 §1241', SEC_LEDGER), ('LEAD_LOCK PP', SEC_LOCK), ('看板 R186', SEC_BOARD)):
    ck('T1 %s 无 tab / CR' % nm, '\t' not in s and '\r' not in s)
    ck('T2 %s 以换行开头结尾' % nm, s.startswith('\n') and s.endswith('\n'))

rc = io.open(RC, encoding='utf-8', newline='').read()
led = io.open(LED, encoding='utf-8', newline='').read()
lock = io.open(LOCK, encoding='utf-8', newline='').read()
brd = io.open(BRD, encoding='utf-8', newline='').read()
ck('T3 R14_COMMON 末节 == 2.190', '## 2.190' in rc[-60000:], rc.rstrip().split('\n')[-1][:30])
ck('T4 台账末节 == §1240', '## §1240' in led[-60000:], led.rstrip().split('\n')[-1][:30])
ck('T5 LEAD_LOCK 末段码 == PO', '## PO · R17 第 185 轮' in lock[-40000:])
ck('T6 R14_COMMON 尚无 2.191', '## 2.191' not in rc)
ck('T7 台账尚无 §1241', '## §1241' not in led)
ck('T8 LEAD_LOCK 尚无 PP 段', '## PP · R17 第 186 轮' not in lock)
ck('T9 看板尚无 R186 段', 'R17 第 186 轮' not in brd)

nrc = rc.rstrip('\n') + '\n' + SEC_COMMON
nled = led.rstrip('\n') + '\n' + SEC_LEDGER
nlock = lock.rstrip('\n') + '\n' + SEC_LOCK
nbrd = brd.rstrip('\n') + '\n' + SEC_BOARD
ck('T10 R14_COMMON CR 保持 1081', nrc.count('\r') == 1081, nrc.count('\r'))
ck('T11 台账 CR 保持 337', nled.count('\r') == 337, nled.count('\r'))
ck('T12 LEAD_LOCK CR 保持 137', nlock.count('\r') == 137, nlock.count('\r'))
ck('T13 看板 CR 保持 0', nbrd.count('\r') == 0, nbrd.count('\r'))
ck('T14 看板新行数 <= 300', nbrd.count('\n') <= 300, nbrd.count('\n'))
ck('T15 四件套都变大', all(len(x.encode()) > len(y.encode()) for x, y in
   ((nrc, rc), (nled, led), (nlock, lock), (nbrd, brd))),
   (len(nrc.encode()) - len(rc.encode()), len(nled.encode()) - len(led.encode()),
    len(nlock.encode()) - len(lock.encode()), len(nbrd.encode()) - len(brd.encode())))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘 ==')
for path, newtxt in ((RC, nrc), (LED, nled), (LOCK, nlock), (BRD, nbrd)):
    oldraw = open(path, 'rb').read(); o = hashlib.sha256(oldraw).hexdigest()
    bak = os.path.join(BL, '%s.before_r186_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('W1 %s 备份独占且 sha 相同' % os.path.basename(path),
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
    assert open(path, 'rb').read() == oldraw, '母本被外部改动: %s' % path
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    back = open(path, 'rb').read()
    ck('W2 %s 回读一致' % os.path.basename(path),
       hashlib.sha256(back).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
    print('   %-22s %d -> %d B' % (os.path.basename(path), len(oldraw), len(back)))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
