# W37 · 借用官方战役 id 的 DLC 路线：可行性 / 冲突面 / 回滚设计

> run_id `NEXT_RE_20261112_R02` ｜ 交付 `lead/next_re_20261112_r02/W37_official_id_borrow/`
> 日期 2026-11-13 ｜ **纯离线只读分析卡**，不启动游戏、不 attach、不写游戏目录。
> 目标：评估「借用官方战役 id」这条 DLC 路线的**可行性、冲突面与回滚设计**。
> **本卡不做产品决策**：是否覆盖官方战役、借哪一个 id、是否投产，均由用户拍板。本文只给代价与风险清单。

---

## 0 · 分级口径与本卡边界

| 标签 | 本卡含义 |
|---|---|
| `[本次实测]` | 本卡 `EVIDENCE/e1|e2|e3` 脚本对 INI / MIX / 文件系统字节直接读出并断言（exit 0） |
| `[本次读码]` | 本卡**未**对 `gamemd.exe` 做独立 Capstone 反汇编 ⇒ **本卡不签发此级别**；所有代码级依据一律降为 `[转引]` 并附 `file:line` |
| `[静态推断]` | 由实测 + 转引事实组合推出的判断，未做运行期观察 |
| `[转引]` | 来自 W21/W26/W27/W29/W31/W32/W33/W34 及 `docs/re/` 的既有结论；关键处本卡已读原文核对 |
| `[待运行验证]` | 静态无法确定，必须真机验证；**本卡不做** |

> 因此下文中凡出现 `0x46CE10` / `0x52CB90` / `0x5CEEF0` 等地址语义，**均为 `[转引]`**，出处逐条给出。
> 本卡 `[本次实测]` 只覆盖：INI 字节、MIX 内 `MAPSELMD.INI` 的提取与哈希、两游戏目录的文件清单、W21/W26 原文。

---

## 0.1 结论速览（先看这个，不是决策）

| # | 问题 | 结论 | 等级 |
|---|---|---|---|
| 1 | 借用哪个 id | **可见可点的入口只有 `ALL1` / `SOV1` 两个**（`tut1` 无控件、无 INI 段）；12 个 `DebugOnly` 段不产生徽章。两者代价对称；`SOV1` 是唯一有真机进图证据的通道（W27 D2/D3）| `[本次实测]`+`[转引]` |
| 2 | 同 id 合并语义 | **对象复用 + `vtbl+0x64` 字段覆写（per-key last-write-wins），不是整段替换**；但「后装载者是谁」有两个未闭环条件（枚举顺序、回退分支） | `[转引]`+`[待运行验证]` |
| 3 | MAPSELMD 配套 | 必须**克隆官方 5,573 B 全文 + 只改 `[Sov0x]` 段的 `Scenario=` 行**，作为散装投放；仅给最小文件会让官方 14 关全挂 | `[转引 W34]`+`[本次实测]` |
| 4 | 冲突面 | 6 项既定 + 4 项本卡补列；其中「官方战役存档」与「`RA2MD.INI` 战役进度」的实际载体与任务措辞有出入 | 见 §4 / `DISAGREE.md` |
| 5 | 回滚 | 全局 Battle 表是**启动时重建的内存结构**，不持久化 ⇒ 卸载还原是**文件级**的，与「整段替换 / 字段级合并」无关；难度全部落在 `original_absent`、直接改写官方文件、多包同名、存档残留 | `[转引]`+`[静态推断]` |

**路线现状判定**：`[转引 W27 D2/D3]` 「借用官方 id → 点徽章进我方图」这一层**已真机成立**；`[转引 W31/W33/W34]` 「通关后打一关→进下一关」这一层**仍未经真机闭环**（`MAPSELMD.INI` 阶段登记是硬前提）。本卡不把前者外推成后者。

---

# Q1 · 借用哪个 id 最合适

## 1.1 官方 `BATTLEMD.INI` 全量清单 `[本次实测]`

`ra2bench/BATTLEMD.INI` 与 `ra2youli/BATTLEMD.INI` **逐字节相同**：2,733 B、145 行全 CRLF、SHA-256 `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791`（`EVIDENCE/e1_read_ini.stdout.txt` L8-14）。
（与 `ra2forge_fix_forge2.md:97` 的 W3 勘误 `2,733 B / sha256 7e40691a…` 一致 `[转引]`。）

**`[Battles]` 全部 14 条目**（逐字）：

```ini
[Battles]
1=ALL1
2=SOV1
3=ALL02
4=ALL03
5=ALL04
6=ALL05
7=ALL06
8=ALL07
9=SOV02
10=SOV03
11=SOV04
12=SOV05
13=SOV06
14=SOV07
```

**14 个战役段的关键字段**（`CD` / `Scenario` / `FinalMovie` / `Description` / `DebugOnly`；空 = 该键不存在或值为空）：

| 段 | CD | Scenario | FinalMovie | Description | DebugOnly |
|---|---|---|---|---|---|
| `[ALL1]` | 2 | `ALL01umd.MAP` | *(空)* | `DESC:ALL1` | — |
| `[SOV1]` | 2 | `SOV01umd.MAP` | *(空)* | `DESC:SOV1` | — |
| `[ALL02]` | 2 | `all02umd.MAP` | *(空)* | `(all02umd.map)` | `yes` |
| `[ALL03]` | 2 | `all03umd.MAP` | *(空)* | `(all03umd.map)` | `yes` |
| `[ALL04]` | 2 | `all04dmd.MAP` | *(空)* | `(all04dmd.map)` | `yes` |
| `[ALL05]` | 2 | `all05umd.MAP` | *(空)* | `(all05umd.map)` | `yes` |
| `[ALL06]` | 2 | `all06umd.MAP` | *(空)* | `(all06umd.map)` | `yes` |
| `[ALL07]` | 2 | `all07smd.MAP` | *(空)* | `(all07smd.map)` | `yes` |
| `[SOV02]` | 2 | `sov02smd.MAP` | *(空)* | `(sov02smd.map)` | `yes` |
| `[SOV03]` | 2 | `sov03umd.MAP` | *(空)* | `(sov03umd.map)` | `yes` |
| `[SOV04]` | 2 | `sov04dmd.MAP` | *(空)* | `(sov04dmd.map)` | `yes` |
| `[SOV05]` | 2 | `sov05umd.MAP` | *(空)* | `(sov05umd.map)` | `yes` |
| `[SOV06]` | 2 | `sov06lmd.MAP` | *(空)* | `(sov06lmd.map)` | `yes` |
| `[SOV07]` | 2 | `sov07tmd.MAP` | *(空)* | `(sov07tmd.map)` | `yes` |

**三条硬事实**：
1. **全部 14 段 `FinalMovie=` 为空** `[本次实测]`（e1, 22/22 PASS）。⇒ 借用任一 id **不引入任何 FinalMovie 引用**，不存在「缺失时处理」的问题。详见 §1.4。
2. **只有 `ALL1` / `SOV1` 是正式战役**：`Description` 是 CSF 标签 `DESC:ALL1` / `DESC:SOV1`，且**没有** `DebugOnly`；其余 12 段是 `DebugOnly=yes` 的调试占位（文件 L21-22 / L60 注释自述 "temporary campaigns to assist us in debugging … REMOVE before shipping"）`[本次实测]`。
3. **`[Battles]` 里没有 `tut1`，文件里没有任何 `[TUT*]` 段** `[本次实测]`（e1 L37-38）。任务要求列 `[ALL*]/[SOV*]/[TUT*]` 段 ⇒ `TUT*` 一栏**为空**，见 `DISAGREE.md` D2。

**当前散装 `BATTLEMD98.INI`（`ra2youli`，453 B，GBK，12 行 LF）** `[本次实测]`：
```ini
[Battles]
15=RA2F1
[RA2F1]
CD=2
Scenario=ECH01.MAP
FinalMovie=
Description=苏联战役：同盟国在乌拉尔东麓秘密集结，…（纯中文文本）
```
⇒ 这是**追加新 id** 路线（`15=RA2F1`），不是官方 id 覆写；其注释自述 "Delete this file to unregister"。W32 已定谳「追加 id 不生成可见徽章」`[转引 W32 MENU_ENTRIES.md:196-214 / LEAD_VERDICT_campaign_menu_q1.md:78]`，这正是本卡改评「借用 id」的原因。

## 1.2 三个硬编码槽位的实际可达性 `[转引]`

| 槽 | `.data` 串 | WndProc 立即数 | 对话框控件 | 能否作为 DLC 入口 |
|---|---|---|---|---|
| 盟军 | `"all1"` | `0x6EA` | Static **1770** ✓ | ✅ 可 |
| 苏军 | `"sov1"` | `0x6EC` | Static **1772** ✓ | ✅ 可 |
| 新兵训练 | `"tut1"` | `0x6EB` | **无**（`0x6EB` 分支是残留，模板无控件） | ❌ 不可 |

依据：`LEAD_VERDICT_campaign_menu_q1.md:25-27`（三串 `0x825C90/98/A0` 紧邻、各出现一次；13 控件仅 2 个徽章 Static）；`W32_campaign_menu_entries/MENU_ENTRIES.md:205,214`（`cDlgItems=13`、徽章 Static 仅 1770/1772、`0x6EB` 分支残留）。`[转引]`

⇒ **`0x46CC90("tut1")` 在 `[Battles]` 无对应段、且无控件可点**，若强行在散装 INI 新建 `[tut1]` 段，就退回「追加新 id」路线（已判不可达）。**可借用集合 = {ALL1, SOV1}**。`[静态推断]`

## 1.3 借用代价比较表（不做产品决策，只列代价）

| 候选 id | 覆盖了哪个官方战役 | 连带影响的同段字段 | 连带影响的其它文件 | FinalMovie 缺失处理 | 已有真机证据 | 总体代价 |
|---|---|---|---|---|---|---|
| **`SOV1`** | 顶替**玩家可玩的苏军战役链**（7 关）；BATTLEMD 侧被覆写的只有 `[SOV1]` 这 **1 个**正式段，另有 6 个 `SOV0x` 调试段与 `[Nod]` 阶段树 | `CD=2`（CD 检查）、`Description=DESC:SOV1`（CSF 标签，显示官方苏军文案）、`Scenario=SOV01umd.MAP` | `MAPSELMD.INI` 的 `[Nod] 1=Sov01..7=Sov07` 与 `[Sov01..07]` 全段；苏军战役 `.SAV`；`DESC:SOV1` CSF 标签 | **不需要**：官方该段 `FinalMovie=` 空 `[本次实测]` | ✅ W27 D2/D3：`[SOV1] Scenario=` 指向我方图能进图 `[转引]` | 改动面 = 1 个 BATTLEMD 段 + `[Nod]` 侧 7 个阶段段；**唯一有真机进图证据的通道** |
| **`ALL1`** | 顶替**玩家可玩的盟军战役链**（7 关）；BATTLEMD 侧被覆写的只有 `[ALL1]` 这 1 个正式段 | `CD=2`、`Description=DESC:ALL1`、`Scenario=ALL01umd.MAP` | `MAPSELMD.INI` 的 `[GDI] 1=ALL01..7=ALL07` 与 `[ALL00..07]`（**多一个 `Scenario=` 为空的 `[ALL00]` 起始段**）；盟军 `.SAV`；`DESC:ALL1` | **不需要**：同上 | ❌ 无（W27 只改了 `[SOV1]`）| 与 SOV1 对称，但**无真机证据**；`[ALL00]` 使阶段树多一层 `[静态推断]` |
| **`tut1` / `[TUT*]`** | 无（该段/条目不存在）| 无 | 需新建段 ⇒ 退化为追加 id | 不适用 | ❌ | **不可用**：无控件、无段 `[本次实测]`+`[转引]` |
| **`ALL02..ALL07` / `SOV02..SOV07`（12 段）** | 12 个调试占位战役 | 各带 `DebugOnly=yes`，`Description` 是字面 `(xxx.map)` | 隐藏调试 ListBox（实测不可达）| 不需要 | ❌ | **不可用**：可见徽章只查 `all1/sov1/tut1`；`DebugOnly=yes` 只给 Description 追加调试后缀 `[转引 LEAD_VERDICT_campaign_menu_q1.md:48-50]` |
| **直接改写官方散装 `BATTLEMD.INI`** | 同上，但**污染官方文件本身** | 同段全部字段 | 官方文件字节完整性 | 不需要 | ⚠️ W27 D2/D3 是在**沙箱内**改写 `[SOV1] Scenario` 做诊断，不是产品形态 `[转引 W27 CAMPAIGN_LIVE.md:15]` | **回滚代价最高**：必须逐字节备份 + 还原；`docs/re/mix_hygiene_product.md:122` 明确禁止「删散装指望 MIX 回退」`[转引]` |

> **比较结论（非决策）**：从「已有真机证据 + 改动面 + 回滚面」衡量，`SOV1` 是**已验证成本最低**的通道；`ALL1` 等价但缺证据。是否接受「覆盖一整条官方 7 关战役」这个代价，属产品决策，本卡不裁。

## 1.4 `FinalMovie` 问题的直接答案

`[本次实测]` **官方 `BATTLEMD.INI` 的 14 个段 `FinalMovie=` 全部为空**（e1 L59 PASS）。因此：
- 借用 `ALL1` / `SOV1` / 任意 debug 段，**都不会引入**指向影片文件的引用；
- 覆写段里**省略** `FinalMovie=` 或写 `FinalMovie=` 空，与官方原值一致，无「缺失需处理」；
- `[转引 W32 MENU_ENTRIES.md:36,230]`：`FinalMovie` 由 `Battle::Read_INI 0x46CCD0` 的 `0x46CD1E` 读进 `[battle+0x29C]`，**菜单层（WndProc 全文）从不读 `+0x29C`**；`FinalMovie` 非空/为空对 UI 无影响。
- `[待运行验证]` 战役**终章**是否另有 `FinalMovie` 消费点，本卡未找到逐指令证据 ⇒ 不作承诺。

⚠️ **不要与 `MAPSELMD.INI` 混淆**：官方阶段段另有 `MapVQ=NODMAP01.VQA` / `VoiceOver=NOD-01.AUD` / `ClickMap=NODCLK01.PCX` / `Overlays=TN02A.SHP,TG02A.SHP` / `Targets=1,190,100` / `Description=787`（CSF 索引号）共 6 类 UI 字段 `[本次实测 e3 L23-28]`。这些是 **MapSelect 界面资源**，不是 BATTLEMD 的 `FinalMovie`。它们指向 `movies01.mix` / `movies02.mix` / `movmd03.mix`（`ra2youli` 实存，357/304/394 MB）`[本次实测 e3 L15-20]`。若沿用官方 `[Sov0x]` 段，这些资源名全部有效、无需处理；若新造阶段段并留空，MapSelect UI 行为 `[待运行验证]`。

## 1.5 「该段还有哪些字段会连带影响」逐项

以 `[SOV1]` 为例（官方只有 4 个键）`[本次实测]`：

| 字段 | 覆写时的连带影响 | 等级 |
|---|---|---|
| `Scenario=` | **核心**：决定点徽章后进哪张图。W27 D2/D3 实测「直接指向我方图能进图」`[转引 W27 CAMPAIGN_LIVE.md:77-79, LEAD_CORRECTION_campaign_blockers.md:47-57]` | 实测（他卡）|
| `CD=2` | 若散装覆写段省略该键：字段级合并时保留官方 2；若 `Read_INI` 对缺失键写默认值则可能是 0。菜单层不读 CD（`W32 MENU_ENTRIES.md:229`），但「开始战役时是否校验 CD」是另一条路径，`W32 UNKNOWNS.md` 自列未定谳 ⇒ `[待运行验证]` | 转引 + 待验证 |
| `Description=DESC:SOV1` | 是 **CSF 标签位**（官方文件 L44 注释自述 "string file label"）`[转引 LEAD_FINDING_campaign_text_is_csf.md:21-26]`。沿用 ⇒ 菜单/列表显示官方苏军战役文案；改成纯文本 ⇒ 必然 `MISSING:'…'`（W27 实测）`[转引]`；要自定义文案需 CSF 读/写/落地三件能力（W30 在案）| 转引 |
| `DebugOnly` | `ALL1`/`SOV1` **没有**此键；若在覆写段误写 `DebugOnly=yes`，隐藏调试列表会附加调试后缀（该列表实测不可达，影响可忽略）`[转引]` | 转引 |
| `MAPSELMD.INI [Sov01]` 全段 | 虽不是 BATTLEMD 同段，但**借用 SOV1 必然连带**：7 类 UI 字段 + 数字子项 `2=Sov02`（ClickMap 颜色索引）。见 Q3 | 转引 W34 |

---

# Q2 · 怎样覆写才安全（`Register_Battles 0x46CE10` 合并语义）

## 2.1 判据（逐条给 `file:line`，全部 `[转引]`）

`Register_Battles 0x46CE10` 的反汇编与语义在仓库多处独立成文：

- `docs/re/fs_mix_load_chain.md:256-285`（§4.2 合并实现，反汇编逐行）
- `docs/re/ARCHITECTURE_ATLAS.md:3634-3646`（§17.4 归并契约 + 三条架构级定论）
- `docs/re/fs_mix_load_chain_deep.md:210-219`（§2.3 多文件合并语义）
- `W29_override_order/OVERRIDE_ORDER.md:204`、`W32_campaign_menu_entries/MENU_ENTRIES.md:196,35`（并表链闭环）
- `W34_mapselmd` 未涉及此函数；`W32_campaign_menu_entries/DISAGREE.md:13` 明确它属**配置装载层**、`ret 4`

关键指令（`fs_mix_load_chain.md:260-277`）`[转引]`：

```asm
0x46CE17  push 0x81B1D8              ; 段名 "Battles"
0x46CE1C  call 0x526960              ; 取 [Battles] 条目数 n
0x46CE34..55  0x526CC0(ini,"Battles",i,buf,0x20,..)  ; 逐条取条目名（如 "SOV1"）
0x46CE5A  mov eax,[0xA83D08]         ; g_Battles.Count
0x46CE65..77  _stricmp(g_Battles[j]+0x24, buf)       ; 按对象 +0x24 名字匹配
0x46CE81/8F    命中→idx=j ; 未命中→esi=-1
0x46CE97  push 0x3A0                 ; 未命中：new(0x3A0) = 928 B 新对象
0x46CEB5  call 0x410800              ; 用名字初始化
0x46CF1F..34   push_back 到 0xA83CFC ; Count++
0x46CF58  mov eax,[0xA83CFC]; mov esi,[eax+esi*4]    ; 命中→复用同一对象（只读指针）
0x46CF60  mov edx,[esi]; call [edx+0x64]             ; ★ Battle::Read_INI(本 INI) 覆写字段
0x46CF68..6D  循环下一个条目名
```

**`vtbl+0x64` = `Battle::Read_INI 0x46CCD0`**，读 `CD` / `Scenario` / `FinalMovie` / `DebugOnly` / `Description` 写进该对象 `[转引 W32 MENU_ENTRIES.md:35,196,322 / W32 UNKNOWNS.md:60 / re_atlas_reassess_20261112/step2_r036_rerun.stdout.md:2882-2889]`。

## 2.2 结论：**对象复用 + 字段覆写，不是整段替换** `[转引]`+`[静态推断]`

| 判据 | 说明 |
|---|---|
| **命中分支不 new 对象** | `0x46CF58` 只是 `mov esi,[eax+esi*4]`（从 `Items[]` **读**已有对象指针）；`new(0x3A0)` 只在 `0x46CE97` 的**未命中**分支 | 
| **无「替换/销毁」指令** | 全过程未见对 `Items[idx]` 的写回、旧对象析构、或覆盖整个 `0x3A0` 结构的 `memcpy`；只有 `call [edx+0x64]` 的**字段级写入** |
| **归并键是 `[Battles]` 条目名** | `_stricmp` 不区分大小写（`0x46CE77 call 0x7C8D20`）；`1=ALL1, 2=SOV1` 的**编号只是枚举顺序**，不是身份（`fs_mix_load_chain.md:283`）|
| **每个 INI 对象是临时的** | 装载后立即析构，数据只经 `0x46CE10` 落到全局表 `0xA83CF8`（`fs_mix_load_chain.md:285`）|

⇒ **同 id 覆写 = 「找到同名对象 → 复用 → 把本 INI 该段出现的键写进对象」**，即 per-key last-write-wins 的**字段级合并**；不是「用一个新段整体替换旧段」，也不是「把段文本替换掉」。`[静态推断]`（由上述四条读码事实组合得出，非单条外推）

### 仍未定谳的一层 `[待运行验证]`

`Battle::Read_INI 0x46CCD0` 对**本 INI 段里缺失的键**如何处理，本卡未取得逐指令证据：`W32 UNKNOWNS.md:60` 只说「`0x46CCD0` 会把这些键读进 Battle 对象」，未给出 `INIClass::Get_String` 的"缺失即跳过" vs "写默认值分支"。两种可能：

- (a) **只在键存在时写** ⇒ 真正的字段级合并：散装 `[SOV1]` 只写 `Scenario=`，官方的 `CD/FinalMovie/Description` 原值保留；
- (b) **无条件按默认值写** ⇒ 语义上接近「整段字段重置」：省略的键被写成 0 / 空串。

**取证方法**（需真机/调试器，本卡不做）：在 `0x46CF60` 下断，投一份只含 `[Battles] 2=SOV1` + `[SOV1] Scenario=ECH01.MAP` 的散装文件，dump 归并后对象 `+0x98`(CD) / `+0x29C`(FinalMovie) / `+0x2A0`(Description)。`[转引 W29 UNKNOWNS.md:30 / fs_mix_load_chain_deep.md:434]`

> 工程上的规避办法不依赖这一层：覆写段**显式写全 5 个键**（`CD=2` / `Scenario=` / `FinalMovie=` / `Description=DESC:SOV1` / 不写 `DebugOnly`），则两种分支结果一致。`[静态推断]`

## 2.3 「同 id 后装载者覆写」——两个未闭环条件（比合并语义更关键）

任务前提写「散装 `BATTLEMD98.INI` 是追加合并语义（同 id 后装载者覆写），所以覆写官方 id 走的是**同 id 后胜**这条路」。这个表述**有前置条件**，本卡必须标出：

### 条件 A：目录枚举顺序不保证 `[待运行验证]`

- `[转引 ARCHITECTURE_ATLAS.md:3646]`：同名战斗 ID 的最终胜者取决于 `FindFirstFileA/FindNextFileA` 枚举顺序，**引擎不保证字母序** ⇒ 「工程上禁止跨文件重复 ID」。
- `[转引 fs_mix_load_chain.md:284]`：`BATTLEMD.INI < BATTLEMD98.INI`（`.`=0x2E < `9`=0x39）在字母序下 98 靠后 ⇒ **通常**胜出，但标注为 `[推演]+[待实测]`。
- `[转引 W29 OVERRIDE_ORDER.md:22]`：枚举顺序决定的最终胜者 = **[静态推断-弱] / [待运行验证]**。
- `[转引 W29 UNKNOWNS.md:30]` 给出的最小实验：投两个散装 `BATTLEMD01/02.INI` 同 ID 不同 `Description`，在 `0x46CF60` 下断记录覆写次序。

`[本次实测 e3 L6-13]`：`ra2youli` 现状确有 `BATTLEMD.INI` + `BATTLEMD98.INI` 两个散装文件 ⇒ 借用 id 时**必然**构成跨文件重复 ID，落在这条未定谳风险上。`[静态推断]` 可用「所有覆写字段都放进同一个文件、且该文件名字典序最大」来降低（但仍是 `[待运行验证]`，不是定谳）。

### 条件 B：回退分支可能让官方 INI **后装载**而翻盘 `[静态推断]`+`[待运行验证]`

`[转引 ARCHITECTURE_ATLAS.md:3611-3631]` `LoadBattleMdIni 0x52CB90` 的控制流：

```asm
0x52CBA0  push "BATTLEMD*.INI"   ; FindFirstFileA，纯 FS
0x52CBB1  cmp esi,-1 → je 0x52CCCD          ; 0 个散装匹配 → 直接回退
; 循环内对每个枚举文件：
0x52CC4E  push "BATTLEMD.INI" ; _stricmp(枚举名, 官方名) → 设「已见过官方名」标志
0x52CC67  call 0x46CE10                       ; ★ 归并（通配路径）
0x52CCAB  FindNextFileA
0x52CCC7  jne 0x52CD5F                        ; 已见过散装 BATTLEMD.INI → 跳过回退
; 回退分支（唯一 mix 感知的 BATTLEMD 通道）：
0x52CCCD  push "BATTLEMD.INI" ; CCFileClass（磁盘优先 + MIX 回落）
0x52CD25  INIClass::Load
0x52CD2C  call 0x46CE10                       ; ★ 同一归并函数，但发生在通配之后
```

⇒ 若目标机**有**散装官方 `BATTLEMD.INI`（`ra2youli` 现状如此 `[本次实测]`）：跳过回退，两个散装文件按枚举顺序归并。
⇒ 若目标机**没有**散装官方 `BATTLEMD.INI`（只有 `BATTLEMD98.INI`）：按该反汇编，回退分支会读 MIX 内官方 `BATTLEMD.INI`（`[转引 ra2forge_fix_forge2.md:97` W3 勘误：嵌套 `LOCALMD.MIX` 内确有官方 `BATTLEMD.INI`，2,733 B，`7e40691a…`）并在 `0x52CD2C` **后归并** ⇒ 官方 `SOV1` 段反而覆写我方 ⇒ **借用 id 静默失效**。`[静态推断]`

⚠️ **仓库内部口径不一致**：`W29 OVERRIDE_ORDER.md:22` 写「回退分支仅在目录里**一个 `BATTLEMD*.INI` 都没有**时才执行」；`fs_mix_load_chain.md:20` 写「若枚举结果里**没有 `BATTLEMD.INI` 本身**，再显式装载」；`mix_hygiene_product.md:122` 写「仅当目录**无任何散装 `BATTLEMD*.INI`**」。三者与上面反汇编的 `0x52CCC7` 判据（是否见过**官方名**）措辞不同。本卡**采信反汇编**并把这条列入 `UNCOVERED.md` U2，`[待运行验证]`。

> **对安装器的可操作含义** `[静态推断]`：借用 id 时**不要**删除/移走目标机的散装官方 `BATTLEMD.INI`（它既是 14 条官方战役的来源，也是「跳过回退」的开关）；应「保留官方文件 + 追加同 id 覆写文件」，并确保覆写文件在枚举序上靠后。此条不得写成定谳。

## 2.4 合并语义对「卸载还原难度」的实际影响

**核心洞察** `[静态推断]`（由 `[转引 W29 OVERRIDE_ORDER.md:22 / ARCHITECTURE_ATLAS.md:3644-3645 / W32 MENU_ENTRIES.md:196]` 组合）：

> 全局 Battle 表（`0xA83CF8` / Items `0xA83CFC` / Count `0xA83D08`，元素 `0x3A0` B）是**进程启动时由 `0x52DF25 → 0x52CB90 → 0x46CE10` 从 INI 重建的内存结构**，不持久化到磁盘。

因此：

| 若合并是… | 卸载需要做什么 | 难度 |
|---|---|---|
| 整段替换 | 删除/还原散装覆写文件；下次启动从官方 INI 重新 `new` 对象 | **文件级** |
| 字段级合并 | 删除/还原散装覆写文件；下次启动官方段重新写回对象 | **文件级** |

⇒ **在「文件级卸载 + 重启生效」这一语义下，两者对卸载还原的难度完全相同**。任务问句中「这决定卸载还原的难度」的关切，只在另外两种语义下才成立：`(a)` 要求**运行期热还原**（引擎不支持，全局表只能启动时重建）；`(b)` 安装器**直接改写官方 `BATTLEMD.INI`**（此时必须逐字段写回，难度陡增）。本卡采用的文件级语义下，真正决定难度的是**磁盘事实**（见 Q5）：

1. 覆写文件是**新建**（原本不存在）还是**替换**（原本存在）⇒ W21 的 `original_absent` 陷阱；
2. 是否**直接改写**了官方 `BATTLEMD.INI`（若是，必须逐字节备份/还原，且 `ra2forge_fix_forge2.md:93-97` 的勘误史表明「备份后删除指望 MIX 回退」曾被推翻）；
3. 是否还有**其它包**的 `BATTLEMD98.INI` 同名（跨包同 id 静默覆盖，枚举序未定）；
4. 是否残留**运行期产物**（`.SAV` 存档、崩溃后的 `.bak`）。

**但合并语义确实决定一件事** `[静态推断]`：字段级合并下，卸载**只需删掉覆写文件**，官方段的其它字段（`CD` / `FinalMovie` / `Description`）本来就在官方文件里完好无损，不存在「需要把被覆盖的字段逐个写回」的问题；若误判为整段替换而去重写官方 `BATTLEMD.INI`，反而引入 W21 的「错还原」风险（见 Q5）。

---

# Q3 · `MAPSELMD.INI` 该如何配套（若借用 `SOV1`）

## 3.1 官方文件事实 `[本次实测]`

`EVIDENCE/e2_extract_mapselmd.stdout.txt`（34/34 PASS，exit 0）双路独立自证：

| 项 | 值 | 验证 |
|---|---|---|
| 容器 | `ra2bench/ra2md.mix`，204,527,696 B | e2 L5 |
| 直接偏移 | **`0x71D050`**，读 5,573 B | e2 L8-19 |
| SHA-256 | `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52` | e2 L12-15，**与任务前提一致** |
| 行尾 | 261 行全 CRLF，`lone_LF=0 / lone_CR=0` | e2 L18-19 |
| 递归解码 | 顶层 25 条目（flags=0x3 加密）→ 嵌套 `LOCALMD.MIX` id `0xFBE0D09D` → 二级 187 条目 → `id=0x922B8CE7` (`crc32("MAPSELMD.INI")`) `size=5573`，**绝对起点恰为 `0x71D050`** | e2 L24-54，两路 payload 逐字节相同，且与 W34 产物相同 |
| 散装存在性 | `ra2bench` / `ra2youli` **都没有**散装 `MAPSELMD.INI` | e3 L1-4 `[本次实测]` |

官方 20 个段：`GDI, GDISFX, Nod, NODSFX, Anims, ALL00, ALL01..ALL07, Sov01..Sov07`。
`[GDI] 1=ALL01..7=ALL07`；`[Nod] 1=Sov01..7=Sov07`。**每个阶段段有 7 类字段 + 1 个数字子项键**；`ALL07` / `Sov07` 无数字子项（战役终点）。`[本次实测 e2 §C / MAPSELMD.OFFICIAL.INI L194-261]`

## 3.2 引擎解析语义（有代码依据，全部 `[转引 W34_mapselmd/MAPSELMD_SPEC.md]`）

| 事实 | 出处 |
|---|---|
| 散装优先于 MIX 内同名（`CCFileClass::Get_File 0x473D10` 磁盘命中即跳过 `MixFileClass::Find 0x5B4430`）| 任务前提 + `W29 OVERRIDE_ORDER.md:19,35-55` + `LEAD_VERDICT_map_start_root_cause.md:66` |
| **必须克隆官方全文再追加/改写**：最小文件会丢官方 14 关 + `[Anims]/[GDISFX]/[NODSFX]` UI 配置；加载器 `0x5CEEF0` 确实读 `'Anims'/'Sounds'/'TextRect'/'Palette'` | `W34 MAPSELMD_SPEC.md:66,152,158` + `W34 DISAGREE.md:60-71` + `LEAD_VERDICT_map_start_root_cause.md:67` |
| 阵营段键 = **阶段序号**：从 `1` 起 `%d` 造键、**首个缺口即停**、上限 `100`（`0x5CEF98` / `cmp edi,0x64`）；值是**阶段段名** | `W34 MAPSELMD_SPEC.md:59-68,118` |
| 阶段段数字子项键 = **`0..255`**（`0x5CFF81` 从 0、`cmp eax,0x100`），值是**阶段段名**、数字是 **ClickMap 颜色索引**（存成 1 字节 `[esi+4]`）；非数字键不参与 | `W34 MAPSELMD_SPEC.md:77-81,119-120` + `W34 DISAGREE.md:45-56` |
| `0x5CF6B0` 按 `[stage+0]` **阶段名**反查；`0x5CF760` 按 `[stage+4]` **`Scenario=`** 反查；`0x5CF810` 按序号取 | `W34 MAPSELMD_SPEC.md:85-91` |
| `SkipMapSelect=no` 路径 `0x5AE220`：`0x5AE30C call 0x5CF760` 用当前地图名 `[Scen+0x125C]` 按 `Scenario=` 反查当前阶段；未命中 → `"MapSelect: Invalid stage!"` → 弹 `MSG:UnableMapSelect` | `W34 MAPSELMD_SPEC.md:95-98` + `W33 DISAGREE.md:19-23` + `LEAD_VERDICT_map_start_root_cause.md:20-27` |
| `SkipMapSelect=yes` 路径 `0x5ADF20`：取当前阶段 → 遍历子项 → 按阶段名反查 → 取该子项的 `Scenario=` 与 `NextScenario` 归一化比对 → 命中则写 `[Scen+0x125C]` 并更新 `[Scen+0x35A0]` | `W34 MAPSELMD_SPEC.md:100-104` + `W33 NEXTSCENARIO_FLOW.md:34-36` |
| 值比对**大小写不敏感**，机制是两边先**转小写**（`0x7B5B30` → `0x7CAFF4` +0x20），再用大小写敏感 `0x7B4780` 比较 | `W34 MAPSELMD_SPEC.md:106-109,121` + `W34 DISAGREE.md:29-41` |
| **INI 段名/键名不做归一化**（裸 CRC32）⇒ 必须照抄官方拼写 `[Nod]` / `[Sov01]` | `W34 MAPSELMD_SPEC.md:121,166` |
| 行读取器 `0x65D5C0`：LF 终止、CR 跳过 ⇒ CRLF / 单 LF 可行，**单 CR 不可行** | `W34 MAPSELMD_SPEC.md:110,122` |

> `[转引 LEAD_VERDICT_map_start_root_cause.md:50-57]` 特别提醒：整条判定链是**静态**的，`frame=210` 时 `[Scen+0x125C]` 的实际内容未观测；不得写「已定位根因」的绝对化措辞。本卡沿用该口径。

## 3.3 建议改法（具体到行，示例 INI 片段）

**设定**（均为示例，非产品决策）：我方 3 关 `ECH01.MAP` → `ECH02.MAP` → `ECH03.MAP`；地图 `[Basic]` 写 `SkipMapSelect=no`、`NextScenario=ECH02.MAP` / `ECH03.MAP` / 空、`EndOfGame=no/no/yes`（与官方 14 张图同形 `[转引 LEAD_VERDICT_map_start_root_cause.md:39]`）；`BATTLEMD98.INI` 覆写 `[SOV1] Scenario=ECH01.MAP`。

### 步骤 0（硬前提）`[转引 W34]`

**把官方 5,573 B 全文逐字节克隆为散装 `MAPSELMD.INI` 投放到游戏目录**，CRLF 不变、20 个段一个不删。`[本次实测 e3]` 两目录原本无此文件 ⇒ 这是 **CREATE**（卸载时 DELETE，见 Q5）。

### 步骤 1：`[Nod]` 阵营段 **完全不改**（官方 L41-51）

```ini
; Soviet Progression            ; L41
[Nod]                          ; L42
Anims=Anims                    ; L43
Sounds=NODSFX                  ; L44
1=Sov01                        ; L45  ← 保持指向 [Sov01]（借用 SOV1 的入口阶段）
2=Sov02                        ; L46
3=Sov03                        ; L47
4=Sov04                        ; L48
5=Sov05                        ; L49
6=Sov06                        ; L50
7=Sov07                        ; L51
```
**依据** `[转引 W34 §2.1]`：`1..7` 是连续阶段序号，改 `1=` 会让「阶段序号 1」指向别的段，而 `[Scen+0x35A0]` 语义未验证（见 §3.4）；保持不动是最小改动。`[静态推断]`

### 步骤 2：只改 3 个阶段段的 `Scenario=` 行（其余 7 类字段 + 子项键全部原样）

```ini
; ---------- 官方 L194-202，改 1 行 ----------
[Sov01]                        ; L194  段名照抄（大小写敏感）
Scenario=ECH01.MAP             ; L195  ★改：原 Sov01umd.MAP
Description=787                ; L196  沿用（CSF 索引，官方 Sov01 文案）
VoiceOver=NOD-01.AUD           ; L197  沿用（资源实存）
MapVQ=NODMAP01.VQA             ; L198  沿用
Overlays=TN02A.SHP,TG02A.SHP   ; L199  沿用
Targets=1,190,100              ; L200  沿用
ClickMap=NODCLK01.PCX          ; L201  沿用
2=Sov02                        ; L202  ★不改：颜色 2 → 阶段名 Sov02

; ---------- 官方 L204-212，改 1 行 ----------
[Sov02]                        ; L204
Scenario=ECH02.MAP             ; L205  ★改：原 sov02smd.MAP
Description=788                ; L206
VoiceOver=NOD-01.AUD           ; L207
MapVQ=NODMAP01.VQA             ; L208
Overlays=TN02A.SHP,TG02A.SHP   ; L209
Targets=1,190,100              ; L210
ClickMap=NODCLK01.PCX          ; L211
3=Sov03                        ; L212  ★不改

; ---------- 官方 L214-222，改 1 行 ----------
[Sov03]                        ; L214
Scenario=ECH03.MAP             ; L215  ★改：原 sov03umd.MAP
Description=789                ; L216
VoiceOver=NOD-01.AUD           ; L217
MapVQ=NODMAP01.VQA             ; L218
Overlays=TN02A.SHP,TG02A.SHP   ; L219
Targets=1,190,100              ; L220
ClickMap=NODCLK01.PCX          ; L221
4=Sov04                        ; L222  ⚠ 见 §3.4「末关子项」— 建议删除或保留待验证
```

### 步骤 3：`BATTLEMD98.INI`（或同名覆写文件）配套

```ini
[Battles]
2=SOV1                 ; 覆写官方同 id（不是 15=RA2F1）
[SOV1]
CD=2                   ; 显式写全，规避 §2.2 未定谳的缺失键语义 [静态推断]
Scenario=ECH01.MAP
FinalMovie=            ; 官方即空，见 Q1.4
Description=DESC:SOV1  ; 沿用官方 CSF 标签，避免 MISSING: [转引 W27 D1]
```

`[转引 W27 CAMPAIGN_LIVE.md:77-79 / LEAD_CORRECTION_campaign_blockers.md:47-57]`：点苏军徽章 → `0x46CC90("sov1")` → `[SOV1] Scenario` → `Start_Scenario` 进 `ECH01.MAP`，**完全不经过 MapSelect** ⇒ 这一跳已真机成立。

### 步骤 4：通关后的推进链（**代码依据 + 推断 + 待验证 三段**）

```
打完 ECH01 → GUI:Continue
  → 0x685A38 读 SkipMapSelect=no → 0x5ADD10 → 0x5AE100 → 0x5AE220 载入散装 MAPSELMD.INI
  → 0x5AE30C call 0x5CF760 以当前地图名 [Scen+0x125C]="ECH01.MAP" 按 Scenario= 反查
  → 命中 [Sov01]（因 L195 已改为 ECH01.MAP）  ← 这一步是本改法要修的失败点
  → MapSelect 界面按 [Sov01] 的 ClickMap/Targets/MapVQ 显示，玩家点颜色 2 区域
  → 子项 2=Sov02 → 0x5CF6B0 按阶段名反查 [Sov02] → 其 Scenario=ECH02.MAP
  → 与 ECH01.MAP 的 NextScenario=ECH02.MAP 归一化（转小写）比对 → 命中
  → 0x686700 把 ECH02.MAP 写入 [Scen+0x125C]，更新 [Scen+0x35A0]
```

| 段落 | 等级 | 依据 / 说明 |
|---|---|---|
| 「反查当前阶段必须命中」 | `[转引]`（代码依据）| `W34 MAPSELMD_SPEC.md:95-98`；W27 D2 的失败正是此处未命中（`W33 DISAGREE.md:19-23`）|
| 「`Scenario=` 与 `NextScenario` 比对」 | `[转引]`（代码依据）| `W34 MAPSELMD_SPEC.md:100-104` |
| 「改 `Scenario=` 而不改段名/子项键」 | `[静态推断]` | 保持 `[Nod] 1..7` 与 `2=Sov02` 等链接不变是最小改动；引擎按段名与颜色索引工作，不按 `.MAP` 文件名 |
| 「沿用官方 `Description/MapVQ/VoiceOver/ClickMap/Overlays/Targets`」 | `[静态推断]` | 资源名在 `ra2youli` 实存（e3 L15-28）；W34 v11 亦克隆官方最后一关 UI 值（`MAPSELMD_SPEC.md:155`）|
| 「点击颜色 2 区域能进下一关」 | `[待运行验证]` | `W34 MAPSELMD_SPEC.md:164` 明确「交互式 MapSelect 界面在追加/改写阶段上能否被玩家点选到下一关未经真机验证」 |
| 「`ECH03` 打完正常结束」 | `[待运行验证]` | 末关 `NextScenario=` 空 + `EndOfGame=yes` 是 `ra2forge` 惯例 `[转引 ra2forge_fix_forge2.md:77-79,99]`；但 `[Sov03] 4=Sov04` 子项仍在，未命中时是否弹窗未验证 |
| 「散装 `MAPSELMD.INI` 端到端覆盖 MIX 内同名」 | `[待运行验证]` | `W29` 只定谳分支顺序；`W34 DISAGREE.md:86` 明确端到端未验证 |

## 3.4 需要显式标注的三个不确定点

1. **末关子项**：`[Sov03] 4=Sov04`（L222）指向官方第 4 阶段（其 `Scenario=` 仍是 `sov04dmd.MAP`，未被改）。两条选择：`(a)` 删除 L222，使 `[Sov03]` 无数字子项（与 `Sov07` 的终点形态一致 `[本次实测 e2 L79-80]`）；`(b)` 保留 L222 并把 `[Sov04..Sov07]` 的 `Scenario=` 也改成我方图或留空。**两者都是 `[静态推断]`，真机行为 `[待运行验证]`**。W34 v11 的惯例是「最后阶段不写数字子项」（`MAPSELMD_SPEC.md:156`）⇒ 倾向 (a)，但本卡不裁。
2. **`[Scen+0x35A0]` 初值**：`[转引 W34 UNCOVERED.md:15]` 从 `BATTLEMD98.INI` 菜单**新建**战役时该字段初值未经真机确认，若为 0 会取官方首关阶段而不是我方阶段。借用 `SOV1` 走的是官方徽章（不是新建战役），初值语义同样 `[待运行验证]`。
3. **不改 `SkipMapSelect`**：`[转引 W34 UNCOVERED.md:15]` 本卡生成的地图一律 `SkipMapSelect=no`；任何改成 `yes` 的用法都未验证。故本改法**不动** `[Basic] SkipMapSelect`。

## 3.5 备选方案（列出但不推荐，非产品决策）

| 方案 | 做法 | 问题 |
|---|---|---|
| **B. W34 式「追加新阶段」** | 保留官方 `[Sov01..07]` 原样，在 `[Nod]` 追加 `8=RA2F_…`、`9=…`，新增我方阶段段 `Scenario=ECH0x.MAP` | `[Nod] 1=Sov01` 仍指向官方首关；`0x5CF760` 反查 `ECH01.MAP` 能命中追加段，但 `[Scen+0x35A0]` 语义、`ClickMap` 颜色与阶段序号的对应、MapSelect 界面落位全部 `[待运行验证]`。且 W34 的 v11 是为「追加新 id 战役」设计的，与「借用 id」不是同一形态 `[转引 W34 MAPSELMD_SPEC.md:150-158]` |
| **C. 只给「只含我方条目」的最小 `MAPSELMD.INI`** | 丢弃官方 14 阶段与 UI 配置段 | **不可**：`[转引 W34 DISAGREE.md:60-71 / LEAD_VERDICT_map_start_root_cause.md:67]` 官方 14 关全挂，且加载器读不到 `[Anims]/Sounds/TextRect/Palette` |
| **D. 把 `MAPSELMD.INI` 打进 `expandmd98.mix`** | 依靠 MIX 覆盖 | **不可**：`MAPSELMD.INI` 由 `0x5CEEF0 → CCFileClass` 打开，散装优先；`[转引 W29 Q1]` 且 W34 明确产物必须散装投放（`MAPSELMD_SPEC.md:158`）|

---

# Q4 · 冲突面清单

> 每项：**冲突表现 / 可否检测 / 能否自动还原**。前 6 项为任务指定，后 4 项为本卡补列。

| # | 冲突对象 | 冲突表现 | 可否检测 | 能否自动还原 |
|---|---|---|---|---|
| 1 | **官方战役存档**（`.SAV`）| 借用 `SOV1` 后 `[Nod]` 阶段树的 `Scenario=` 被改。玩家在**安装前**存的官方苏军战役存档，其内嵌的当前地图名/阶段序号（`[Scen+0x125C]` / `[Scen+0x35A0]` `[转引 W31/W33/W34]`）指向 `Sov0xumd.MAP`；安装后读档，反查可能失败或落到我方图 ⇒ 弹 `MSG:UnableMapSelect` 或进错关 `[静态推断]`。**安装期间玩家在我方战役里新存的档**，卸载后变成「指向不存在地图」的孤儿存档 `[静态推断]` | 可：扫描存档里的 `.MAP` 名字串，与当前 `MAPSELMD.INI` 的 `Scenario=` 集合比对；`[转引 W27 CAMPAIGN_LIVE.md:67-70,117,125]` 表明存档内可命中 `ECH02.MAP` 等串且读档不改存档字节。**但**存档格式未在本卡解析 ⇒ 检测手段本身 `[待运行验证]` | **配置可自动**（卸载时还原 `MAPSELMD.INI` 即恢复官方阶段表，旧档自动重新兼容）；**存档本身不可也不应自动改/删**（`USER_AUTHORIZATION_20261112.md:24` 明令不修改用户存档）。只能提示用户：`[静态推断]` |
| 2 | **`FinalMovie`** | 官方 14 段 `FinalMovie=` 全空 `[本次实测]` ⇒ **无引用、无冲突**。唯一风险是覆写段误填一个不存在的影片名，引擎在战役终章尝试播放；`[待运行验证]` 是否报错 | 可：读所有 `BATTLEMD*.INI` 的 `FinalMovie=` 值，非空即告警 | 能：卸载删掉覆写文件即可（字段随文件消失）|
| 3 | **电影文件**（`movies01.mix` / `movies02.mix` / `movmd03.mix`，实存 357/304/394 MB `[本次实测 e3]`）| 不是 BATTLEMD 的 `FinalMovie`，而是 `MAPSELMD.INI` 阶段段的 `MapVQ=NODMAP01.VQA` / `VoiceOver=NOD-01.AUD`（`[本次实测 e3 L23-28]`）。沿用官方 `[Sov0x]` 段 ⇒ 资源名有效；若新造阶段段并把这些键留空/写错 ⇒ MapSelect 界面资源缺失 `[待运行验证]` | 可：把改后 `MAPSELMD.INI` 的 `MapVQ/VoiceOver/ClickMap/Overlays` 值与官方全集比对；资源是否在 MIX 内需解 MIX 索引（本卡未解这三个容器）⇒ `[待运行验证]` | 能：卸载删掉散装 `MAPSELMD.INI` 即回到 MIX 内官方文件；**电影容器本身绝不改** |
| 4 | **`RA2MD.INI` 里的战役进度** | ⚠️ **与任务前提有出入**：本次只读核对 `ra2youli/RA2MD.INI` 全文 118 行（1,754 B，SHA-256 `c91c6a47…3c27d`），**没有任何战役进度键**；只有 `[Options] CampDifficulty=0`（战役**难度**）与 `[Video] StretchMovies=no`（视频缩放）`[本次实测 e1 L84-87]`。真正的进度载体是 `.SAV` 存档内的 `[Scen+0x35A0]` / `[Scen+0x125C]` `[转引 W31 WHY_MAP_FAILS.md:140,182 / W34 UNCOVERED.md:15]`，或注册表 `[待运行验证]` | 可：`CampDifficulty` 与 `Side` 可静态读；进度不在本文件中，故「检测本文件进度冲突」这一动作无对象 | **不需要还原**：安装器**不应写** `RA2MD.INI`；`[本次实测 e3 L44]` 把它列为 MUST NOT MODIFY 并记基线哈希，用于卸载自证 |
| 5 | **`MAPSELMD.INI` 官方阶段** | 借用 `SOV1` 且按 Q3 改 3 个 `Scenario=` ⇒ 官方苏军 7 关里前 3 关的入口图被顶掉；`[GDI]` 侧 7 关不动 `[本次实测 e2 §C]`。若采用「追加新阶段」方案，则 `[Nod] 8..` 与阶段序号/颜色索引语义纠缠 `[待运行验证]` | 可：与官方 5,573 B 基线逐行 diff（e2 已产出 `MAPSELMD.OFFICIAL.INI` 供比对）| 能：**完全自动**——两目录原本无散装 `MAPSELMD.INI` `[本次实测 e3]` ⇒ 安装是 CREATE、卸载是 DELETE，官方文件在 MIX 内从未被写。前提是安装器记录 `original_absent`（见 Q5 / W21）|
| 6 | **其它包的 `BATTLEMD98.INI`** | `BATTLEMD*.INI` 是**通配枚举全合并**，同 id 后装载者覆写且枚举序不保证 `[转引 ARCHITECTURE_ATLAS.md:3646 / W29 Q4]`。若另一个包也覆写 `SOV1`（或也投 `BATTLEMD98.INI`），两包互相静默覆盖；`ra2youli` 现状已有一个 453 B 的 `BATTLEMD98.INI`（`15=RA2F1`）`[本次实测 e1]` ⇒ 借用 id 要么改写它、要么与它并存 | 可：安装前枚举 `BATTLEMD*.INI`，解析 `[Battles]` 全条目，若存在与待写 id 相同的条目即 definite content conflict（沿用 W22/W23/W26 的既有门）| 能但**需谨慎**：卸载应只删/还原**本包自己写的那个文件**，且必须记录该文件在本次安装前是否已存在、其原始字节。若两包写同一个路径，卸载会互相破坏 ⇒ 需「单活动包」语义 `[转引 W21 UNCOVERED.md:21-23]` |
| 7 | **官方散装 `BATTLEMD.INI` 本体**（补列）| 若安装器选择「直接改写官方文件」而非散装 98 ⇒ 官方 14 条战役定义被污染；`docs/re/mix_hygiene_product.md:122` 与 `ra2forge_fix_forge2.md:93-97` 的勘误史表明「备份后删除散装、指望引擎回退 MIX 内官方件」曾被推翻 | 可：安装前记 SHA-256（`7e40691a…`），安装后比对 | 能：逐字节备份/还原（W26 `_stage_and_replace` 链）；**但风险最高**，且会与回退分支（§2.3 条件 B）耦合 |
| 8 | **`Description` / CSF 标签**（补列）| `[SOV1] Description=DESC:SOV1` 是 CSF 标签位 `[转引 LEAD_FINDING_campaign_text_is_csf.md]`。沿用 ⇒ 显示官方苏军文案；写纯文本 ⇒ `MISSING:'…'`（W27 实测）；要自定义需新增 CSF 能力并投放散装 `ra2md.csf`（W29/W30 在案），而 CSF 必须是**完整合法**文件否则启动失败 `[转引 W29 OVERRIDE_ORDER.md:25]` | 可：静态检查 `Description=` 是否为 `DESC:` 前缀或已知标签 | 能：卸载删覆写文件；若额外投了 `ra2md.csf`，则它也是 CREATE→DELETE，需同样记 `original_absent` |
| 9 | **12 个 `DebugOnly` 占位段 / `tut1` 残留分支**（补列）| 误覆写 `ALL02..SOV07` 不产生可见徽章（白改）；误写 `tut1` 段退化为追加 id 路线（已判不可达）`[转引 W32]` | 可：检查覆写 id ∈ {ALL1, SOV1} | 能：删覆写文件 |
| 10 | **安装器自身清单 / seal / `.bak`**（补列）| W21 的「错还原」（把 A 自创文件字节当原版写进 `.bak`）、W26 的「吞异常 + 谎称已回滚」、中途失败留下孤儿 `.bak`／无 seal 清单 `[转引 W21 DISAGREE.md:17-24 / W26 UNSEAL_FIX.md:13-34]` | 可：`verify` 命令（`W23/W26` 退出码 5/6/7/8/9）| 能但**必须按 W26 v9 的双 `try/except` 隔离 + `original_absent` 旗标**，见 Q5 |

---

# Q5 · 回滚设计：安装—运行—卸载后的逐字节还原清单

## 5.1 既有缺陷（本卡已读原文核对 `[转引]`）

| 缺陷 | 原文 | 对借用 id 回滚的直接含义 |
|---|---|---|
| **W21「错还原」/ over-restore** | `W21_dlc_orphan/DISAGREE.md:17-24`：A 自己创建的文件（INI/Y/MIX，原版状态是「**不存在**」）在 A′ 替换时被写进 `.ra2forge.bak`（"最旧原版优先"策略把 A 的字节当成原版），uninstall 于是把它们「还原」回 A 的内容，卸载后残留 4 个 A 时代文件。修法 = `original_absent` 旗标（V3：卸载后逐字节回到初始态）| 借 `SOV1` 时**散装 `MAPSELMD.INI` 原版状态就是「不存在」** `[本次实测 e3]` ⇒ 必须记 `original_absent=True`，卸载 = **DELETE**，绝不能「还原成某个 bak」。`BATTLEMD98.INI` 若原本不存在同理 |
| **W21 清单侧丢记录** | `W21 DISAGREE.md:10-15`：`install_package()` 用只含新包文件的 entries **整体重写** `ra2forge_install.json`，旧条目消失、文件留盘 ⇒ 卸载漏删 | 借用 id 若分多次安装/升级，清单必须保留本次 run 创建的每一个槽位 |
| **W26 吞异常 + 谎称回滚** | `W26_dlc_unseal_fix/UNSEAL_FIX.md:13-22, 48-56`：v8 在 `install.py:1979-1980` 用 `except OSError: pass` 吞掉记录回滚异常，并**无条件**抛 `"the install record was rolled back … nothing was left in the unsealed state"`。v9 修法：`rolled_back` 旗标、**记录回滚与包文件回滚两个独立 `try/except` 块**、任一失败即禁止宣称已还原、逐项聚合 | 借用 id 的卸载必须**诚实报告**：`MAPSELMD.INI` 删除失败、`BATTLEMD98.INI` 还原失败、`.bak` 清理失败要分别列出，不能吞 |
| **W26 actions 完整性** | `W26 UNSEAL_FIX.md:24-30, 56-64`：`uninstall()` 中 `dest.unlink()` / `bak.unlink()` / `_stage_and_replace()` / `manifest_path.unlink()` 原先是裸调用，一个 `[WinError 5]` 就中断并**丢失所有已完成 actions**；v9 逐项隔离、还原成功即先写 `actions`、删清单失败时 `status=failed / exit 1` 但保留全部 actions | 卸载报告必须逐文件列出 `created→removed` / `backup→restored`，即使中途失败 |
| **W26 清单/seal 门禁** | `W26 UNSEAL_FIX.md:81-134`：`verify` 退出码 5/6/7/8/9；`uninstall` 退出码 0/1/2/7/8/10；「清单仍在盘上不得制造无 seal 记录状态」 | 还原自证应包含 `verify` 的 seal/digest 判定，而不只是文件哈希 |

## 5.2 三阶段状态机 `[静态推断]`（基于 §5.1 + e3 文件清单）

```
[安装前 baseline]
  ra2youli/BATTLEMD.INI        EXISTS 2733 B  sha 7e40691a…   ← 只读，不动
  ra2youli/BATTLEMD98.INI      EXISTS 453  B  sha 4e341756…   ← 若复用此文件：REPLACE，须备份原字节
  ra2youli/MAPSELMD.INI        ABSENT                          ← CREATE，original_absent=True
  ra2youli/RA2MD.INI           EXISTS 1754 B  sha c91c6a47…   ← MUST NOT MODIFY
  ra2youli/ECH0x.MAP           (视包而定)                      ← CREATE 或 REPLACE
  ra2youli/expandmd98.mix      (视包而定)                      ← CREATE 或 REPLACE
  ra2youli/ra2forge_install.json(.seal)  ← 安装器清单，由工具维护
  ra2youli/*.SAV                                              ← 绝不触碰

[安装]  → 写覆写文件 + 散装 MAPSELMD.INI + 我方地图；清单记每个槽位的
           (name, sha_before, sha_after, original_absent, backup_path)
[运行]  → 引擎启动时从 INI 重建内存 Battle 表（不持久化）；游戏可能新增 .SAV
[卸载]  → 逐槽位：original_absent → DELETE；否则 → 从 .bak 逐字节 RESTORE + 删 .bak
        → 清清单/seal；verify；出报告
[还原后] → 与 baseline 逐文件 SHA-256 全等；新增 .SAV 允许留存但须明示
```

## 5.3 必须备份的文件 / 备份命名 / 逐字节基线 `[本次实测]`+`[静态推断]`

沿用项目既有 `.ra2forge.bak` 槽位约定（`[转引 W21 ORPHAN_FIX.md / W26 sandbox/P1` 里可见 `BATTLEMD98.INI.ra2forge.bak`、`X.MAP.ra2forge.bak`、`expandmd98.mix.ra2forge.bak`）。

| # | 文件（相对游戏目录）| 安装前状态 `[本次实测 e1/e3]` | 安装动作 | 备份命名 | 卸载动作 | 基线 SHA-256（本次实测）|
|---|---|---|---|---|---|---|
| 1 | `MAPSELMD.INI` | **ABSENT** | CREATE（完整克隆 5,573 B + Q3 改行）| **不建 bak**；清单记 `original_absent=True` | **DELETE**，且不得「还原」| 官方原文 `074ccccd…6919d52`（用于校验克隆源，非游戏目录基线）|
| 2 | `BATTLEMD98.INI` | EXISTS 453 B | 方案① REPLACE（写同 id 覆写）／方案② 另投 `BATTLEMD99.INI`（避开与既有 `15=RA2F1` 包冲突，`[静态推断]`）| `<name>.ra2forge.bak` | 方案① 从 bak **逐字节 RESTORE**；方案② DELETE | `4e3417568924891792520ad8c3ab44f42e11fdc9934fb453d4db7210bf3d2c74` |
| 3 | `BATTLEMD.INI` | EXISTS 2,733 B | **MUST NOT MODIFY**（保留官方 14 条；也是「跳过回退」的开关，§2.3 条件 B）| 不需要（但基线哈希入清单，用于自证未被误改）| 不动作；`verify` 比对哈希 | `7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791` |
| 4 | `RA2MD.INI` | EXISTS 1,754 B | **MUST NOT MODIFY** | 不需要（基线哈希入清单）| 不动作；`verify` 比对哈希 | `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d` |
| 5 | `ECH01.MAP` / `ECH02.MAP` / `ECH03.MAP`（或实际我方图名）| 视目标机而定（可能已有同名官方/用户图）| CREATE 或 REPLACE | `<name>.ra2forge.bak`（仅 REPLACE 时）| CREATE→DELETE；REPLACE→RESTORE | 安装前逐文件实测记入清单 |
| 6 | `expandmd98.mix`（若用）| 视目标机而定 | CREATE 或 REPLACE | `<name>.ra2forge.bak` | 同上 | 同上 |
| 7 | `ra2md.csf`（若走自定义 `Description`）| 本会话 `ra2youli` 下无散装 `[转引 LEAD_FINDING_campaign_text_is_csf.md:52]` | CREATE（**必须完整合法 CSF**，否则启动失败）| 不建 bak，`original_absent=True` | DELETE | — |
| 8 | `ra2forge_install.json` / `.seal` | 安装器维护 | 写 | 工具内部 `prev_record_text` | 工具内部 `unlink` / 还原 | — |
| 9 | `*.SAV` 存档 | 用户数据 | **绝不触碰** | — | 不动作；卸载报告明示「运行期新增的存档未由本工具清理」| — |

> **方案① vs ② 的选择是产品/工程决策，本卡不裁**；但两者都必须把「本包写了哪个文件」精确到**路径 + 安装前是否存在 + 安装前字节**写进清单，否则会出现 W21 的孤儿/错还原。

## 5.4 如何自证还原成功 `[静态推断]`（逐字节、可机读）

1. **安装前**：对上表 1–6、9 生成 `baseline` 清单（rel path / size / mtime_ns / **SHA-256** / `exists`），与 W27 `real_pre.json` 同形（`[转引 W27 CAMPAIGN_LIVE.md:31-32]`）。
2. **安装后**：`verify` 应为 exit 0，清单 `seal OK / package_digest OK / files: N ok, 0 changed, 0 missing`（W27 §2 有同形输出 `[转引]`）。
3. **卸载后**：重跑同一 `baseline` 生成器，逐文件比对：
   - 表 1、2（方案②）、5、6（CREATE 槽）⇒ **文件不存在**；
   - 表 2（方案①）、5、6（REPLACE 槽）⇒ **SHA-256 == 安装前基线**；
   - 表 3、4 ⇒ **SHA-256 未变**；
   - 表 9 ⇒ 允许新增，但**禁止**任何既有 `.SAV` 的字节变化；
   - `ra2forge_install.json` / `.seal` 均不存在；无残留 `*.ra2forge.bak`。
4. **诚实性判据**（照 W26 v9）：任一还原/删除失败，报告须逐项列出 `install record rollback FAILED` / `package file rollback had failures (N)` / `best-effort rollback` 明细，**禁止**出现 `"the install record was rolled back"` / `"nothing was left in the unsealed state"` 这类无条件的成功宣称（`[转引 W26 DISAGREE.md:17-22 / UNSEAL_FIX.md:54-55]`）；`uninstall` 的 `actions` 即使 `status=failed / exit 1` 也必须完整保留。
5. **本卡可复用的现成基线**：`EVIDENCE/e1_read_ini.json` / `e3_conflict_surface.json` 已给出 4 个配置文件的实测 SHA-256；`EVIDENCE/MAPSELMD.OFFICIAL.INI` 是官方 5,573 B 的逐字节克隆源（SHA-256 `074ccccd…`）。

## 5.5 明确「不能自动还原」的部分

| 项 | 原因 | 建议处置 |
|---|---|---|
| 运行期新建的 `.SAV` 存档 | 用户数据；`USER_AUTHORIZATION_20261112.md:24` 明令不修改用户存档；卸载后它指向已被删除的我方 `.MAP` ⇒ 孤儿存档 `[静态推断]` | 卸载报告**显式提示**「本工具未清理存档」；不自动删、不自动改 |
| 其它包写的 `BATTLEMD*.INI` | 跨包同 id 覆盖且枚举序未定（§2.3 条件 A）；卸载器无权判断哪个是"别人的"`[转引 W21 UNCOVERED.md:21-23]` | 安装前做 definite content conflict 门（默认拒绝）；单活动包语义 |
| 引擎内已被玩家推进的战役状态 | 会话内的 `[Scen+0x35A0]` / `[Scen+0x125C]` 是内存态，进程退出即消失；但存档把它固化了 | 归入上一行 |
| 目标机上**原本就没有**散装官方 `BATTLEMD.INI` 的情形 | 触碰 §2.3 条件 B（回退分支），这不是文件还原能修的，是装载顺序语义 `[待运行验证]` | 安装前检查该文件存在性；缺失时拒绝安装或明确告警 |

---

## 6 · 前提核对结果（`[本次实测]` 复核）

| 任务前提 | 复核 | 结果 |
|---|---|---|
| 可见菜单焊死、2 徽章 Static、`0x6EA/6EC/6EB` 三立即数、`all1/sov1/tut1` | 读 `LEAD_VERDICT_campaign_menu_q1.md` + `W32 MENU_ENTRIES.md:205` 原文 | ✅ 一致（`tut1` 分支无控件，见 Q1.2）|
| 官方 14 图登记在 `[GDI] 1..7` / `[Nod] 1..7` 的 `Scenario=` | e2 §C 20 段 + 14 个 `Scenario=` 全非空 | ✅ 一致 |
| `MAPSELMD.INI` 在 `ra2md.mix` 偏移 `0x71D050` / 5,573 B / CRLF / SHA-256 `074ccccd…` | e2 双路独立自证，全 PASS | ✅ 一致（递归解码的绝对起点恰为 `0x71D050`）|
| 散装优先于 MIX 内同名 | 转引 W29 + LEAD_VERDICT；本卡未做端到端 | ✅ `[转引]`，端到端 `[待运行验证]` |
| W27 D2/D3：`[SOV1] Scenario=` 指向我方图能进图 | 读 `W27 CAMPAIGN_LIVE.md:77-79` + `LEAD_CORRECTION_campaign_blockers.md:47-57` | ✅ `[转引]`（沙箱诊断变体，非产品形态）|
| 散装 `BATTLEMD98.INI` 同 id 后胜 | **有未闭环前置条件**：枚举顺序 + 回退分支（§2.3）| ⚠️ 见 `DISAGREE.md` D1 |
| `[TUT*]` 段 | 不存在 | ⚠️ 见 `DISAGREE.md` D2 |
| `RA2MD.INI` 里的战役进度 | 该文件无进度键 | ⚠️ 见 `DISAGREE.md` D3 |

---

## 7 · 交付物索引

| 文件 | 内容 |
|---|---|
| `BORROW_FEASIBILITY.md` | 本文件（五问 + 代价比较表 + MAPSELMD 改法 + 冲突面 + 逐字节还原清单）|
| `DISAGREE.md` | 与任务前提不符 / 需澄清之处（3 条 + 1 条仓库内部口径分歧）|
| `UNCOVERED.md` | 未覆盖与 `[待运行验证]` 项（按影响排序）|
| `EVIDENCE/README.md` | 脚本、运行方式、exit code 汇总、自证点 |
| `EVIDENCE/e1_read_ini.py` / `.stdout.txt` / `.stderr.txt` / `.exitcode.txt` | 读 INI（22/22 PASS，exit 0）|
| `EVIDENCE/e2_extract_mapselmd.py` / `.stdout.txt` / `.stderr.txt` / `.exitcode.txt` | 解 MIX（34/34 PASS，exit 0）|
| `EVIDENCE/e3_conflict_surface.py` / `.stdout.txt` / `.stderr.txt` / `.exitcode.txt` | 冲突面核对（15/15 PASS，exit 0）|
| `EVIDENCE/MAPSELMD.OFFICIAL.INI` | 官方 5,573 B 逐字节提取产物 |
| `EVIDENCE/e1_read_ini.json` / `e2_extract.json` / `e3_conflict_surface.json` | 机器可读事实 |

---

## 8 · 纪律核验

- ✅ 未启动游戏、未 attach、未注入、未读活进程；
- ✅ 未写 `ra2youli/`、`ra2forge/`、`ra2bench/`（只读）；W21–W36 各目录**只读**（仅核对 W21/W26/W27/W29/W31/W32/W33/W34 原文）；
- ✅ `git` 只读（未执行任何写操作）；
- ✅ 全部写入仅发生在 `lead/next_re_20261112_r02/W37_official_id_borrow/`；
- ✅ 未做产品决策；结论按 `[本次实测]` / `[静态推断]` / `[转引]` / `[待运行验证]` 分级；本卡未对二进制做独立反汇编，故**不签发 `[本次读码]`**。
