#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 G：四件套追加（R14_COMMON §2.195 / 台账 §1245 / LEAD_LOCK PT / 看板 R190）。

写入纪律：每份文件先用 wx 独占创建唯一备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
CR 不变量：R14_COMMON 1081 / GOAL_THREE_TARGETS 337 / LEAD_LOCK 137 / STATUS_BOARD 0。
"""
import hashlib, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
COMMON = os.path.join(TIER, 'R14_COMMON.md')
LEDGER = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BOARD = os.path.join(TIER, 'STATUS_BOARD.md')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def backup_write(path, add_txt, tag, exp_cr, tails):
    raw = open(path, 'rb').read()
    ck('%s 旧 CR == %d' % (tag, exp_cr), raw.count(b'\r') == exp_cr, raw.count(b'\r'))
    for t in tails:
        ck('%s 旧体含锚点 %s' % (tag, t[:18]), t.encode() in raw, t[:18])
    ck('%s 新段无 tab/CR' % tag, '\t' not in add_txt and '\r' not in add_txt)
    new = raw + add_txt.encode()
    ck('%s 新 CR == %d' % (tag, exp_cr), new.count(b'\r') == exp_cr, new.count(b'\r'))
    ck('%s 体量闭合' % tag, len(new) == len(raw) + len(add_txt.encode()), (len(new), len(raw)))
    bak = os.path.join(BL, '%s.before_r190_%s.bak' % (os.path.basename(path), stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(raw)
    ck('%s 备份 sha 一致' % tag,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest())
    assert open(path, 'rb').read() == raw
    open(path, 'wb').write(new)
    ck('%s 回读一致' % tag, hashlib.sha256(open(path, 'rb').read()).hexdigest() == hashlib.sha256(new).hexdigest())
    return len(raw), len(new)

C2195 = '''

### 2.195 R190：vtable 层结构 + RTTI 三层结构双双落成可复算事实（94 组排布规则、305 个调整器 thunk 的位移定律、5,302 条基础类描述符）

**一、同名多档组的排布规则（`_r190/r190a_groups.py` 17 断言 0 FAIL）.** 1,214 张表按 COL 修饰名分 **954 组**，其中 **94 组**含多于 1 张表（2 张 10 / 3 张 6 / 4 张 76 / 5 张 1 / 7 张 1）。组内相邻两表的**块间距 260/260 恒为 4**（组内完全紧排，中间只隔一个 COL 指针槽），94 组在全局地址序里**全部连续**（被别的名字隔开的 0 组）。组内按地址升序时 COL.mdisp **严格递减且末项恒为 0** 的 **91/94** —— 这条**不是全定律**：三个反例的序列实测为 OverlayClass `[12,4,8,0]` / SmudgeClass `[12,4,8,0]` / TerrainClass `[4,12,8,0]`。反控：组内 mdisp 随机打乱后严格递减掉到 **10** 组、改要求严格递增命中 **0** 组、块间距按「槽数+1」算命中 **0** 对。

**二、三个反例的成因，以及为什么不能当成第二条独立证据.** 把判据换成「地址升序 ⇒ 基类数组**首现索引**严格递减」时，同样是 **91 通过 / 3 失败**，且失败的还是这三组（TerrainClass 的首现索引序列 `[6,9,8,0]`）。⇒ 两条判据**同源**，不是两条独立证据；如实登记，不得写成「两个独立口径互相印证」。

**三、305 个调整器的位移定律（`_r190/r190b_thunks.py` 12 断言 0 FAIL）.** 非主表（mdisp != 0）共 **1,318** 槽，其中 **305** 个是 `sub dword ptr [esp+4], K ; jmp t` 形态的调整器 thunk，其余 **1,013** 个是普通函数指针。305 个 thunk 的 jmp 目标 **305/305** 能定位到**同组另一张表的同槽号**，位移规则是 **K == 本层 mdisp − 目标层 mdisp（305/305，反例 0）**，而**不是** `K == 本层 mdisp`（该口径只命中 **303**，漏掉 HouseClass 的两个 **40→36 层间转调**）。反控：改用「本层 mdisp − 组内最低地址层 mdisp」命中 **0**。

**四、三个固定层的表形.** **layer 12** 78 张全部 1 槽、槽 0 恒为 `0x410590`（`C2 04 00` = ret 4）；**layer 8** 78 张全部 1 槽，其中 **75** 张槽 0 为 `0x410580`（`32 C0 C2 08 00` = xor al,al; ret 8），**3** 张（AircraftClass / InfantryClass / UnitClass）换成真实现；**layer 4** 91 张槽数 `{5:1, 6:78, 50:12}`，6 槽的 78 张里 **72** 张共用同一组 6 个默认实现（共 7 种组合），50 槽的 12 张**全部**是 Locomotion 派生类。

**五、RTTI 三层结构闭合（`_r190/r190c_rtti.py` 19 断言 0 FAIL）.** **1,214** 条 COL 的 `TypeDescriptor.pVFTable` **全等于 0x7F9594**（type_info 表本身在册、其 TD.name 也是 `.?AVtype_info@@`），`ClassHierarchyDescriptor.signature` **全为 0**，基础类描述符合计 **5,302** 条（恰等于 1214 条 COL 的 numBaseClasses 之和）。每条的**数组第 0 项**（自项）TD 名 == 该 COL 名（**1214/1214**）、自项 PMD.mdisp == 0（**1214/1214**）、自项 numContainedBases == numBaseClasses−1（**1214/1214**），5,302 条描述符的 pTD 全部是可读 TypeDescriptor，且 pdisp **恒为 0xFFFFFFFF**、vdisp **恒为 0**（单继承、无虚基类）。`numContainedBases` 直方 `{0:2315, 1:1355, 2:498, 3:30, 4:24, 5:44, 6:18, 7:323, 8:319, 9:191, 10:101, 11:18, 13:25, 14:28, 15:8, 17:5}`。

**六、10 vs 14：层偏移与基类 mdisp 的差集.** PMD.mdisp 全镜像恰 **14** 个取值 `{0,4,8,12,24,36,40,44,172,176,240,248,1728,21784}`，而 vtable 层偏移恰 **10** 个 `{0,4,8,12,24,36,40,44,1728,21784}`。差集 **{172,176,240,248}** 是「有基类子对象、但没有独立副表」的四档：172 / 248 → StageClass（8 条 / 25 条），176 → BounceClass（4 条），240 → FlasherClass（25 条）。**边界**：5,302 条描述符里 **2,111** 条（34 个不同名）指向本镜像 1,214 个类名之外的基类（`IUnknown` 841 / `IPersistStream` 346 / `IPersist` 346 / `IRTTITypeInfo` 316 / `IClassFactory` 78 等 COM 接口），这些没有对应的 `.?AV...` 副表 —— 不得把 5,302 条读成「5,302 个在本镜像里有 vtable 的类」。

**七、自错的判据方向（`N3` 如实登记为无效反控）.** 「自项」的身份**只能**由名字判据确立：`numContainedBases == 0` 在数组**末项**同样恒成立（1214/1214），单靠计数区分不了首末项；只有 `numBaseClasses == 1` 的 **256** 条首末同项。这条如实写进脚本注释，不写成「两个判据互证」。

**八、这一轮没做的一件事（防止误读）.** 本轮**没有**给 `0x410450`（77 张表槽 4）/ `0x410580` / `0x410590` / `0x4C9150` 这四个实现装任何游戏语义名 —— 只到「槽号 + 宿主表集合 + 字节序列 + 位移规则」这一层。语义名仍需人读反汇编，不是枚举能得到的。
'''

L1245 = '''

## §1245 R190：vtable 层结构与 RTTI 三层结构落成可复算事实（94 组 / 305 调整器 / 5,302 基础类描述符）

**目标.** R189 把「vtable 在 .rdata 里怎么排」测清了（块紧排、前缀即真实槽数）；R190 接着测「**同一个类的多档表之间是什么关系**」与「**RTTI 的继承描述能不能逐条复算**」这两件事。全部在 t628 本机静态完成，未跑 gamemd.exe。

**一、94 个同名多表组的排布（17 断言 0 FAIL）.** 954 个名字组里有 94 组含多于 1 张表（2 张 10 / 3 张 6 / 4 张 76 / 5 张 1 / 7 张 1）；组内块间距 **260/260 恒为 4**、94 组在全局地址序里**全部连续**；按地址升序 COL.mdisp 严格递减且末项为 0 的 **91/94**。

**二、三个反例 + 一条「同源判据」的如实登记.** 反例序列 OverlayClass `[12,4,8,0]` / SmudgeClass `[12,4,8,0]` / TerrainClass `[4,12,8,0]`。换成「基类数组首现索引严格递减」判据后同样是 91/3、失败同三组 ⇒ 两条判据同源，**不得**当两条独立证据用。

**三、305 个调整器 thunk 的位移定律（12 断言 0 FAIL）.** 非主表 1,318 槽 = 305 个 `sub dword ptr [esp+4], K ; jmp t` + 1,013 个普通函数指针。**K == 本层 mdisp − 目标层 mdisp，305/305 反例 0**；不用这个规则（改用 K == 本层 mdisp）只命中 303，漏掉 HouseClass 的两个 **40→36 层间转调**。

**四、三层的表形.** layer 12 = 78×1 槽 `0x410590`（ret 4）；layer 8 = 78×1 槽，75 张 `0x410580`（xor al,al; ret 8）+ 3 张真实现；layer 4 = 91 张 `{5:1, 6:78, 50:12}`，72/78 共用同一组 6 个默认实现，50 槽 12 张全是 Locomotion 派生。

**五、RTTI 三层结构闭合（19 断言 0 FAIL）.** 1,214 COL → 5,302 条基础类描述符；TD.pVFTable 全等于 0x7F9594；CHD.signature 全 0；自项 TD 名 == COL 名 1214/1214、自项 PMD.mdisp == 0 1214/1214、自项 numContainedBases == numBaseClasses−1 1214/1214；pdisp 恒 0xFFFFFFFF、vdisp 恒 0。

**六、10 个层偏移 vs 14 个 PMD.mdisp.** 差集 `{172,176,240,248}` = 有基类子对象但无独立副表（StageClass 172/248、BounceClass 176、FlasherClass 240）。2,111 条描述符（34 个名）指向镜像外的 COM 接口基类，没有对应副表 —— 这是「5,302 ≠ 5,302 个有 vtable 的类」的原因。

**七、落盘.** 台账 **V574 → V575**：F55 追加第 ⑨ 段（statement 5,406 → **7,937 B**、limitations 3,735 → **5,791 B**、第 4 列 183 → **247 B**），**167,276 B / 57 行 5 列 / CR 0 / sha `ec21be7a…`**（16 断言 0 FAIL）；重钉 44 断言 0 FAIL（MASTER `b998b17a…` → **`f150e6a1…`**，FLOORS[F55] (5406,3735)→(7937,5791)、EVID[F55] 8→11、EVIDB 183→247、ITEMS 191→**194**、UNIQ 83→**86**、LOST 保持 43/16、指针「530..575 / 46 份」、声明轮次 R190）。**三门 exit 0**（check_disc C19/C20 均 ok(V575)、facts_floors D7/D8/D9/D10 全一致、gate_runner G1=G2=G3=ok）。看板 269 ≥ 260 ⇒ 归档 R179 + R180（21 断言 0 FAIL，CR 保持 2952，1,396,464 → **1,407,222 B**），归档后 217 行。
'''

PT = '''

**PT1. 📌 R190 交付一：同名多档组的排布规则测清，但有一条「全定律」被自己的反例挡下.** `_r190/r190a_groups.py`（**17 断言 0 FAIL**）：954 个名字组、94 个多表组；组内块间距 **260/260 恒为 4**、94 组全局连续；按地址升序 mdisp 严格递减且末项为 0 的 **91/94** —— 三个反例 OverlayClass `[12,4,8,0]` / SmudgeClass `[12,4,8,0]` / TerrainClass `[4,12,8,0]` **写进结论，不写成「全部成立」**。

**PT2. 📌 R190 交付二（如实登记的一条无效路径）：换判据不构成第二条独立证据.** 改用「基类数组首现索引严格递减」判据，同样是 **91 通过 / 3 失败**、失败同三组（TerrainClass 首现索引 `[6,9,8,0]`）⇒ 两条判据**同源**。这一条明确写进 F55 limitations 第 5 段，防止下一轮把它当「两个口径互相印证」。

**PT3. ✅ R190 交付三：305 个调整器 thunk 的位移定律.** `_r190/r190b_thunks.py`（**12 断言 0 FAIL**）：非主表 **1,318** 槽 = **305** 个 `sub dword ptr [esp+4], K ; jmp t` + **1,013** 个普通函数指针；305/305 的 jmp 目标落在**同组另一张表的同槽号**；**K == 本层 mdisp − 目标层 mdisp（305/305，反例 0）**，而 `K == 本层 mdisp` 只命中 **303**（漏掉 HouseClass 的两个 **40→36 层间转调**）。

**PT4. ✅ R190 交付四：三个固定层的表形（可直接复用的默认实现复用率）.** layer 12 = **78×1** 槽 `0x410590`（`C2 04 00` = ret 4）；layer 8 = **78×1** 槽，**75** 张 `0x410580`（`32 C0 C2 08 00` = xor al,al; ret 8）+ **3** 张真实现（AircraftClass / InfantryClass / UnitClass）；layer 4 = **91** 张 `{5:1, 6:78, 50:12}`，6 槽的 78 张里 **72** 张共用同一组 6 个默认实现（共 7 种组合），50 槽的 **12** 张全是 Locomotion 派生类。

**PT5. ✅ R190 交付五：RTTI 三层结构逐条闭合.** `_r190/r190c_rtti.py`（**19 断言 0 FAIL**）：**1,214** 条 COL 的 `TypeDescriptor.pVFTable` **全等于 0x7F9594**（type_info 表在册、其 TD.name 也是 `.?AVtype_info@@`）；`ClassHierarchyDescriptor.signature` **全 0**；基础类描述符合计 **5,302** 条 = 1214 条 COL 的 numBaseClasses 之和；**自项 TD 名 == COL 名 1214/1214**、自项 PMD.mdisp == 0 **1214/1214**、自项 numContainedBases == numBaseClasses−1 **1214/1214**、5,302 条 pTD 全部可读；pdisp 恒 **0xFFFFFFFF**、vdisp 恒 **0**。

**PT6. ✅ R190 交付六：10 个层偏移 ⊆ 14 个 PMD.mdisp，差集四档当场指名.** 层偏移恰 **10** 个 `{0,4,8,12,24,36,40,44,1728,21784}`；PMD.mdisp 恰 **14** 个，差集 **{172,176,240,248}** = StageClass（172 8 条 / 248 25 条）、BounceClass（176 4 条）、FlasherClass（240 25 条）—— 有基类子对象、但无独立副表。另有 **2,111** 条（34 个名）指向镜像外 COM 接口基类，**不得**把 5,302 条读成「5,302 个有 vtable 的类」。

**PT7. ✅ R190 落盘 + 重钉 + 三门 + 归档（台账 V574 → V575）.** F55 追加第 ⑨ 段：statement **5,406 → 7,937 B**、limitations **3,735 → 5,791 B**、第 4 列 **183 → 247 B**，**167,276 B（+4,651）/ 57 行 5 列 / CR 0 / sha `ec21be7a…`**（**16 断言 0 FAIL**）。重钉 `_r190/r190e_repin_v575.py` **44 断言 0 FAIL**：旧常量复算旧 MASTER **`b998b17a…`** 命中旧 pin 作硬闸 → 新 MASTER **`f150e6a1…`**；`FLOORS[F55]` (5406,3735)→**(7937,5791)**、`EVID[F55]` **8→11**、`EVIDB[F55]` 183→**247**、`ITEMS` 191→**194**、`UNIQ` 83→**86**、`LOST_ITEMS`/`LOST_UNIQ` 保持 **43/16**、gate_runner LEDGER 1 行、指针四字段（「530..574 / 45 份」→「**530..575 / 46 份**」、声明轮次 R189→**R190**）。**三门终态**：`check_disc` exit 0（**C19 ok(ec21be7a/167276/V575)** / **C20 ok(V575)**）、`facts_floors` exit 0（D7 items=194 uniq=86、D8 floor==167,276、D9+D10 双一致）、`gate_runner` **G1=G2=G3=ok**。看板 **269 ≥ 260** ⇒ 归档 R179 + R180（`_r190/r190f_archive.py` **21 断言 0 FAIL**，CR 保持 **2952**，1,396,464 → **1,407,222 B**），归档后 **217 行**。

**PT8. 📌 R190 自错（三处，全部当场抓出）.** **g1** `r190c_rtti.py` 的 C14 先把外部基类写成「1,392 条」再断言 2,111（**把应然数当实测**，第二十次），改语句按算式输出；**g2** `N2` 反控把阈值写成「< 300」而实测 455（**给反控设了想当然的上界**），改为断言实测值 455 并写明它的意义；**g3** `r190d_write_v575.py` 的 D11 对已 split 的列表再调 `.split` ⇒ AttributeError（**把上一行变量的类型当上上行**），当场修。另有 `r190e_repin_v575.py` 首版把 `EXPECT_CUR`（`os.path.join(...)` 调用）塞进 `ast.literal_eval` ⇒ ValueError，改为只取 12 个字面常量。

**PT9. 📌 R190 未取得（不粉饰）.** ① 审计员 **#460**（deepseek）跑满 **36 回合** `error_max_turns` 失败（**OVERTIME 18.03 分 vs 预算 8 分**），本轮**无第二家族结论**，全部主张只有主会话 + 执行员 **#459**（hy4，24 回合 2.85 分，`ok=15 fail=0`，独立脚本）两方复算；② `0x410450` / `0x410580` / `0x410590` / `0x4C9150` 四个实现的**游戏语义名**仍未取得（只到槽号 + 宿主表 + 字节 + 位移规则）；③ 1,013 个非 thunk 直接槽**没有**同组同序号匹配（实测 0），但这**不等于**证明它们语义上不同；④ {172,176,240,248} 四档为何不生成副表未取得；⑤ F23/F35 grade 未改；⑥ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ C11 十二个永不 FAIL id 未动；⑩ 「哪份是当前版」仍无人覆盖。
'''

BOARDTXT = '''

## 🟢 R17 第 190 轮（2026-11-28 6x–7x）· gamemd.exe 静态本体第二刀：**「同一个类的多档表之间是什么关系」+「RTTI 继承描述能否逐条复算」** 双双落成可复算事实（94 组 / 305 调整器 / 5,302 条基础类描述符）；一条「全定律」被自己的反例挡下

**入口**：R189 待办 (a)(b)(c)(d) —— 其中 (b)「76 张 mdisp==4 宿主表紧邻 mdisp==0 主表的排布规则」最像能一刀切开的结构问题，本轮把它扩成「94 个多表组全普查」，同时把 RTTI 的继承描述整条链路（COL → TD → CHD → 基础类描述符数组）按字段逐条复算。

**一、94 个同名多表组的排布（`_r190/r190a_groups.py` 17 断言 0 FAIL）.**

| 项 | 值（逐张实测，非抽样） |
|---|---|
| 名字组 / 多表组 | **954 / 94**（2 张 10、3 张 6、4 张 76、5 张 1、7 张 1） |
| 组内相邻块间距 | **260/260 恒为 4**（组内完全紧排，只隔一个 COL 指针槽） |
| 组在全局地址序里是否连续 | **94/94 连续**（被别的名字隔开的 0 组） |
| 地址升序 mdisp 严格递减且末项为 0 | **91/94** —— 三个反例：OverlayClass `[12,4,8,0]` / SmudgeClass `[12,4,8,0]` / TerrainClass `[4,12,8,0]` |

**二、换判据不构成第二条独立证据（如实登记）.** 把判据换成「基类数组首现索引严格递减」，同样是 **91 通过 / 3 失败**、失败还是这三组（TerrainClass `[6,9,8,0]`）⇒ 两条判据**同源**。这条写进 F55 limitations 第 5 段，防止下一轮当「两个口径互证」引用。

**三、305 个调整器 thunk 的位移定律（`_r190/r190b_thunks.py` 12 断言 0 FAIL）.** 非主表 **1,318** 槽 = **305** 个 `sub dword ptr [esp+4], K ; jmp t` + **1,013** 个普通函数指针；305/305 的 jmp 目标落在**同组另一张表的同槽号**；**K == 本层 mdisp − 目标层 mdisp（305/305，反例 0）**，而 `K == 本层 mdisp` 只命中 **303**（漏掉 HouseClass 的两个 **40→36 层间转调**）。反控：改用「本层 − 组内最低地址层」命中 **0**。

**四、三个固定层的表形.** layer 12 = **78×1** 槽 `0x410590`（`C2 04 00` = ret 4）；layer 8 = **78×1** 槽，**75** 张 `0x410580`（`32 C0 C2 08 00` = xor al,al; ret 8）+ **3** 张真实现；layer 4 = **91** 张 `{5:1, 6:78, 50:12}`，6 槽的 78 张里 **72** 张共用同一组 6 个默认实现（共 7 种组合），50 槽的 **12** 张全是 Locomotion 派生类。

**五、RTTI 三层结构逐条闭合（`_r190/r190c_rtti.py` 19 断言 0 FAIL）.** **1,214** 条 COL 的 `TypeDescriptor.pVFTable` **全等于 0x7F9594**（type_info 表在册、其 TD.name 也是 `.?AVtype_info@@`）；CHD.signature **全 0**；基础类描述符合计 **5,302** 条 = 1214 条 COL 的 numBaseClasses 之和；**自项 TD 名 == COL 名 1214/1214**、自项 PMD.mdisp == 0 **1214/1214**、自项 numContainedBases == numBaseClasses−1 **1214/1214**、5,302 条 pTD 全部可读；pdisp 恒 **0xFFFFFFFF**、vdisp 恒 **0**（单继承、无虚基类）。

**六、10 vs 14：层偏移 ⊆ PMD.mdisp，差集四档当场指名.** 层偏移恰 **10** 个 `{0,4,8,12,24,36,40,44,1728,21784}`；PMD.mdisp 恰 **14** 个，差集 **{172,176,240,248}** = StageClass（172：8 条 / 248：25 条）、BounceClass（176：4 条）、FlasherClass（240：25 条）—— 有基类子对象、但**无独立副表**。另有 **2,111** 条（34 个名）指向镜像外 COM 接口基类（`IUnknown` 841 / `IPersistStream` 346 / `IPersist` 346 / `IRTTITypeInfo` 316 / `IClassFactory` 78），**不得**把 5,302 条读成「5,302 个有 vtable 的类」。

**七、落盘 V574 → V575.** F55 追加第 ⑨ 段：statement **5,406 → 7,937 B**、limitations **3,735 → 5,791 B**、第 4 列 **183 → 247 B**，**167,276 B / 57 行 5 列 / CR 0 / sha `ec21be7a…`**（**16 断言 0 FAIL**）。重钉 **44 断言 0 FAIL**：MASTER `b998b17a…` → **`f150e6a1…`**，FLOORS[F55] (5406,3735)→**(7937,5791)**、EVID[F55] **8→11**、EVIDB 183→**247**、ITEMS 191→**194**、UNIQ 83→**86**、LOST 保持 43/16、指针「530..575 / 46 份」、声明轮次 R190。**三门 exit 0**：`check_disc`（**C19 ok(ec21be7a/167276/V575)** / C20 ok(V575)）、`facts_floors`（D7 items=194 uniq=86、D8 floor==167,276、D9+D10 双一致）、`gate_runner` **G1=G2=G3=ok**。看板 **269 ≥ 260** ⇒ 归档 R179 + R180（**21 断言 0 FAIL**，CR 保持 **2952**，1,396,464 → **1,407,222 B**），归档后 **217 行**。

**自错 S-190g1..g3 三处，全部当场抓出.** `g1` C14 先把外部基类写成「1,392 条」再断言 2,111（**把应然数当实测**，第二十次），改为按算式输出；`g2` `N2` 反控把上界写成「< 300」而实测 **455**（**给反控设了想当然的上界**），改为断言实测值并写明意义；`g3` `r190d_write_v575.py` D11 对已 split 的列表再调 `.split` ⇒ AttributeError（**把上一行变量的类型当上上行**）。另 `r190e_repin_v575.py` 首版把 `EXPECT_CUR`（`os.path.join(...)` 调用）塞进 `ast.literal_eval` ⇒ ValueError，改为只取 12 个字面常量。

**未取得**：① 审计员 **#460**（deepseek）跑满 **36 回合** `error_max_turns` 失败（**OVERTIME 18.03 分 vs 预算 8 分**），本轮**无第二家族结论**（只有主会话 + 执行员 **#459** hy4，24 回合 2.85 分、`ok=15 fail=0`、独立脚本）；② `0x410450` / `0x410580` / `0x410590` / `0x4C9150` 四个实现的**游戏语义名**仍未取得；③ 1,013 个非 thunk 直接槽**没有**同组同序号匹配（实测 0），但这不等于证明它们语义上不同；④ {172,176,240,248} 四档为何不生成副表未取得；⑤ F23/F35 grade 未改；⑥ `coverage.tsv` / `function_atlas.tsv` 仍不可读；⑦ 86.19% 原值仍不可重算；⑧ C7 三死分支仍各 0 行；⑨ C11 十二个永不 FAIL id 未动；⑩ 「哪份是当前版」仍无人覆盖。
'''

r14 = backup_write(COMMON, C2195, 'R14_COMMON', 1081, ['### 2.194 R189：'])
led = backup_write(LEDGER, L1245, 'LEDGER', 337, ['## §1244 R189 ·'])
lk = backup_write(LOCK, PT, 'LEAD_LOCK', 137, ['**PT'] if False else ['**PS9. 📌 未取得（不粉饰）.**'])
bd = backup_write(BOARD, BOARDTXT, 'STATUS_BOARD', 0, ['## 🟢 R17 第 189 轮'])
print('\nR14_COMMON %d -> %d / LEDGER %d -> %d / LOCK %d -> %d / BOARD %d -> %d'
      % (r14[0], r14[1], led[0], led[1], lk[0], lk[1], bd[0], bd[1]))
bb = open(BOARD, 'rb').read()
print('看板行数 %d / CR %d' % (bb.count(b'\n'), bb.count(b'\r')))
ck('Z1 看板总行数 %d <= 300' % bb.count(b'\n'), bb.count(b'\n') <= 300, bb.count(b'\n'))
ck('Z2 看板 CR 保持 0', bb.count(b'\r') == 0)
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
