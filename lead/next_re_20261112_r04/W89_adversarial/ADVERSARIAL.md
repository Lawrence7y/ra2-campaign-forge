# W89 · 对抗性复核主报告（R03 W85 `PRESSURE.md`）

> **卡号**：`NEXT_RE_20261112_R04 · W89_adversarial`
> **靶标**：`lead/next_re_20261112_r03/W85_pressure/PRESSURE.md`（及同卡 `UNKNOWNS.md`、`DISAGREE.md`、`out/`）
> **硬纪律**：仅写 `lead/next_re_20261112_r04/W89_adversarial/`；其余路径严格只读；不改/不启动游戏、不注入、不附加调试器；待核样本已先复制至 `work/`。
> **结论分级**：`[本次实测]`（本卡脚本实际解析/反汇编输出）/ `[静态读码]`（已核源码或已有静态规格文档）/ `[静态推断]` / `[未证]`。
> **原件声明**：W85 当次崩溃生成的 `except.txt`（转述 26,236 B @12:31:32）已在沙箱还原时丢失，现存 `sandbox_game/except.txt` 为真目录还原出的 26,272 B 历史文件（`EIP=0x00724737`，`Access=0x250`）。**下文所有涉及 `EAX=0`、`Access=0x1D4`、栈回溯 `0x42A595 / 0x429F5A / 0x4DBE6B / 0x42CC07 / 0x0087E8B8` 的表述，均严格标为"（转述，原件已丢失）"。**

---

## §1 · 结论摘要

- **对 R03 原结论支持度打分**：**部分支持（停机现象与静态对照差异成立，但"纯交战/开火导致引擎崩溃"与"非交战结构因子已通过静态对照排除"的核心因果论断不成立）**。
- **一句话总判决**：`[本次实测]` 在全部 10 个压测包与控制包中，**既无坐标越界，也无单位同格堆叠**（否定这两项初筛怀疑）；但 R03 遗漏了两项决定性结构混杂因素——① 所有压测/对照图均有 **10~14 格 `NAPOWR`/`NACNST` 建筑底座物理重叠**，② 所有崩溃构型均含 **`Crewed=yes` 建筑**（而 `0x0051C2D3` 实测属于 **`InfantryClass::IsCellOccupied`**，仅在有步兵进入寻路时执行）；且静态 Guard 对照全程 **`0x0087E8E0` 冻结 (`dx=0`)**，完全未触发移动、寻路、建筑摧毁拆链与乘员步兵生成，因此不能证伪"混杂因子致崩"。

---

## §2 · 逐条技术检查（检查 1–7）

### 检查 1 · 坐标越界

- **我查了什么**：编写并运行 `EVIDENCE/check_1_2_3_4_geom.py`，全量解析本卡 `work/` 下的 `w85_design_pressure.json`、`w85_design_control.json`、`w84_design_df.json` 及 W85 各失败构型 `.MAP` 归档副本（`dose1500`、`control_dose1500`、`notesla400`、`P2`、`P3`、`pkg_pressure`、`w84_df`），按 `ra2forge/maplib.py` 的等距投影 `CellGrid.to_cell(row, col) = (W + col - row, row + 1)` 同时核对逻辑 `(row, col)` 边界与引擎地图菱形平行四边形 `{1 <= y <= W, W+1 <= x+y <= W+H+1}` 边界。
- **证据**（`[本次实测]`，见 `EVIDENCE/check_1_2_3_4_geom.stdout.txt:1-184`）：
  - **关键发现（文档与磁盘漂移）**：W85 `work/w85_design_pressure.json`（17,371 B）与 `w85_design_control.json`（17,450 B）在磁盘上实际上是**终版 P4**（`structures=19, units=90, infantry=0`），并非正文主表 `dose1500`（`structures=22, units=1500`）。因此本节对设计 JSON 与每个 `.MAP` 均做了独立实解析。
  - `dose1500` `.MAP`（`Size=0,0,100,100`, `LocalSize=1,1,98,98`, `Structures=22`, `Units=1500`）：
    - `Arabs`（n=400）：`rc_row=[12,36], rc_col=[82,97]` → 等距 `iso_x=[146,185], iso_y=[13,37]`（例如极点 `(row=12, col=97) → iso=(185,13)` 满足 `x+y=198 <= 201`，`(row=36, col=97) → iso=(161,37)` 满足 `x+y=198 <= 201`）。
    - `British`（n=400）：`rc_row=[12,36], rc_col=[2,17]` → `iso_x=[66,105], iso_y=[13,37]`。
    - `Confederation`（n=400）：`rc_row=[12,36], rc_col=[42,57]` → `iso_x=[106,145], iso_y=[13,37]`。
    - `Russians`（n=300）：`rc_row=[66,81], rc_col=[32,50]` → `iso_x=[51,84], iso_y=[67,82]`。
  - 全部 3 份 JSON 与全部 7 份 `.MAP`：`oob_rc = 0`、`oob_iso = 0`、`oob_struct_cells = 0`、`oob_unit_cells = 0`（含结构底座占用外延格亦全在 `LocalSize=1,1,98,98` 内）。
- **判决**：**越界假说不成立（`[本次实测]`）**。提示词第 1 条所怀疑的 `Arabs col=97` 等坐标越界在 `100×100` 菱形投影下实测为 **0 越界**。

---

### 检查 2 · 同格堆叠

- **我查了什么**：统计各设计 JSON 与 `.MAP` 内全部单位的 `(row, col)` 及 `(iso_x, iso_y)` 唯一格数、外接矩形格数 `bbox_slots`、占用密度 `n / bbox_slots`、最大单格对象数 `max_stack` 与重复格数 `dup_cells`。
- **证据**（`[本次实测]`，见 `EVIDENCE/check_1_2_3_4_geom.stdout.txt:8-48, 110-184`）：
  - `dose1500`：`1500` 辆坦克全部占满 `1500` 个互异网格单元，`dup_cells = 0`、`max_stack = 1`；若按 `w85_build.py` 的 16×30 / 19×30 预设槽区计，每 house 400 辆占用 480 槽（最大密度 0.833），玩家 300 辆占用 570 槽（0.526）。
  - `P4`（`w85_design_pressure.json`）：`British` n=90 占 `row=[12,17], col=[2,17]`（`bbox_slots=96`，密度 `90/96 = 0.938`），`unique_cells = 90`、`dup_cells = 0`、`max_stack = 1`。
  - `W84 df`（对照）：`British` n=30 占 `row=[38,42], col=[20,38]`（`bbox_slots=95`，密度 `0.316`，步长 2），`dup_cells = 0`、`max_stack = 1`。
  - 所有 10 份样本全局 `Unit-Unit` 重复格均为 **0**。
- **判决**：**单位同格堆叠假说不成立（`[本次实测]`）**。初始部署阶段不存在任何多单位共格问题。

---

### 检查 3 · 建筑与单位重叠（重要发现）

- **我查了什么**：从 `ra2youli/ra2md.mix -> localmd.mix -> artmd.ini` 及 `ra2youli/expandmd01.mix -> rulesmd.ini` 只读提取各建筑 `Foundation` 尺寸，按引擎 `eFoundation` 偏移规律将每个建筑左上锚点 `(iso_x, iso_y)` 展开为完整占位集合，同时检查"建筑-单位重叠"与"建筑-建筑重叠"。
- **证据**（`[本次实测]`，见 `EVIDENCE/check_1_2_3_4_geom.stdout.txt:9-39, 112-180`；`Foundation` 来自 `artmd.ini`）：
  - `Struct-Unit Overlap = 0`（全部 10 份样本均实测为 `0`；如 P4 玩家建筑在 rows 56–63、`British GAPOWR` 在 `rc=(8,9)` `iso=[101..102, 9..10]`，而敌军在 rows 12–36、友军在 rows 66+，零交集）。
  - **但是检出严重 `Struct-Struct Overlap`（建筑-建筑底座物理重叠）**：
    - `NAPOWR` 规则底座为 **`3x2`**（占 `iso_x .. iso_x+2`, `iso_y .. iso_y+1` 共 6 格）；`NACNST` 为 **`4x4`**；`GAPOWR` 为 **`2x2`**；`TESLA` 为 **`1x1`**。
    - 在 W85 全部含电厂地图中，6 座 `NAPOWR` 固定放在 `rc=(56,46), (56,48), (56,50), (56,52), (56,54), (56,56)`，对应 **`iso=(90,57), (92,57), (94,57), (96,57), (98,57), (100,57)`**——步长仅为 **2**，而宽度为 **3**，导致相邻每对 `NAPOWR` 在 **`iso(92,57..58), (94,57..58), (96,57..58), (98,57..58), (100,57..58)` 两两重叠共 10 个格子**！
    - 在保留 `NACNST` 的构型（`dose1500`、`control_dose1500`、`notesla400`、`P2`、`P3`）中，`NACNST`（`4x4`）与 `NAPOWR` 进一步叠加，使总重叠单元升至 **`14` 格**；即便 `P4` 移除了 `NACNST`，**6 座 `NAPOWR` 之间仍有 `10` 格重叠**！
- **判决**：**建筑-单位不重叠，但"建筑底座互相重叠"在 W85 全组 100% 实锤存在（`[本次实测]`）**。尽管静态 Control 同样含此 14 格重叠却绿跑 300 s、且 P4 去掉 `NACNST`（14→10）仍崩溃，但一旦进入**拆链/战斗摧毁阶段**（见 §4），底座重叠会对共享 `CellClass+0xE4` 链表与 `[BuildingClass+0x30]` 造成结构破坏。

---

### 检查 4 · 与稳定先例 W84 df 的逐字段结构对照

- **我查了什么**：将 `w84_design_df.json` / `w84_df_RA2F_M1.MAP` 与 W85 `w85_design_pressure.json` / `w85_dose1500_RA2F_M1.MAP` 及 `rulesmd.ini` 属性做逐段结构对比。
- **证据**（`[本次实测]`，见 `EVIDENCE/check_1_2_3_4_geom.stdout.txt:81-227`；`EVIDENCE/check_5_7_ndjson_and_crewed.stdout.txt:28-95`）：

| 维度 | `W84 df`（分钟级稳定） | `W85 崩溃臂`（8 构型共性 / 范围） | 差异性质 |
|---|---|---|---|
| 地图尺寸 `[Map]` | `Size=0,0,60,60`, `LocalSize=1,1,58,58` | `Size=0,0,100,100`, `LocalSize=1,1,98,98` | 图尺寸不同 |
| `[SpecialFlags]` / `[Lighting]` / `[Houses]` / `[Triggers]` / `[Events]` | 均完全同构 | 与 W84 **0 diff**（连 3 敌对 house 间均未结盟） | **已排除** |
| 敌方单位部署 | `30` British Hunt MTNK，步长 2，密度 `0.316`，距离目标约 8–12 格 | `30..1200` Hunt MTNK，步长 1，密度最高 `0.938`，行军距离约 40–55 格 | 移动距离与密排差异 |
| 玩家防御塔 | `1 × TESLA`（注：JSON/MAP 实为 **`TESLA`**，R03 误写成 `ATESLA`；二者均 `1x1, Crewed=no, Powered=yes, Power=-75`） | `0` 或 `12 × TESLA`（`Crewed=no, Powered=yes, Power=-75`） | `TESLA` 本身无乘员且 `notesla=0` 仍崩 |
| **基础设施（电厂/基地）** | **0 座 `NAPOWR` / 0 座 `NACNST` / 0 座 `GAPOWR`**（总电力 `0-75 < 0`） | **全组必有 `6 × NAPOWR`（`Crewed=yes`, `3x2`, 重叠 10 格）** + `0/1 × NACNST`（`Crewed=yes`, `4x4`）+ `0/1/3 × GAPOWR`（`Crewed=yes`, `2x2`） | **核心结构最小差集** |
| **底座重叠格数** | **`0` 格** | **`10` 格（P4）或 `14` 格（其余 9 组）** | **W85 独有结构缺陷** |
| **是否存在 `Crewed=yes` 对象** | **无**（`rulesmd.ini` 中 `TESLA Crewed=no`，`[MTNK]` 未设 `Crewed` 且构造默认 `0`） | **有**（`6` 座 `NAPOWR` + `NACNST` + `GAPOWR` 全为 `Crewed=yes`） | **W85 独有步兵生成源** |

- **判决**：**R03 把最小差集归纳为 `{GAPOWR, NAPOWR, 100×100, Hunt 规模}` 过于粗疏，漏掉了两项对 `0x0051C2D3` 最敏感的结构差集：`NAPOWR` `3x2` 底座重叠（10~14 格）与 `Crewed=yes` 乘员生成源（`W84 df = 0`，`W85 全组 >= 6`）（`[本次实测]`）**。

---

### 检查 5 · `0xA8ED50` 的语义核查与替代时序锚

- **我查了什么**：对照 `lead/re_line_20261105/W4_FIELD_SPEC/sections/card_00A8ED50.md` 静态字节规范，并用 `EVIDENCE/check_5_7_ndjson_and_crewed.py` 逐拍分析 R03 `out/trip_*/run.ndjson` 全 11 组真实采样序列（约 25 万+ 采样行）。
- **证据**：
  1. **静态语义**（`[静态读码]`，`card_00A8ED50.md` §1–§8）：
     - `0x00A8ED50` 是全局 `DynamicVectorClass<BulletClass*>`（基址 `0x00A8ED40`）的 `+0x10` `Count` 槽（向量当前登记条目数），不每帧清零，受 `Add`（`0x4664AB`）/ `Remove`（`0x466630`）双向维护。
     - 主更新遍历（`0x55B93F..0x55B960`）受对象 `[obj+0x98]` 一字节门控，`BulletClass::Update (0x4666E0)` 体内还受 `+0x90` 与 `+0x154/+0x158` 门控 ⇒ `实际活跃更新数 ≤ Count`，`Count` 只是遍历上界，不是"开火瞬间"或"交战强度"。
  2. **动态实测反证**（`[本次实测]`，`EVIDENCE/check_5_7_ndjson_and_crewed.stdout.txt:150-437`）：
     - **A8ED50 首非零前，寻路计数器早已剧烈狂飙**：在 `A8ED50` 仍严格为 `0` 的开火前窗口，`0x0087E8E0`（`PathFinder::GenerationStamp`）在 `notesla400` 已从 `2608 → 11965`（`+9357`）、`singlehouse` 从 `2694 → 11903`（`+9209`）、`P3` 从 `551 → 5427`（`+4876`）、`dose600` 从 `906 → 4521`（`+3615`）、`dose1500` 从 `2372 → 3590`（`+1218`）；甚至在进入采样首帧（`frame=37..60`）时压测组就已经累积到 `98..2694`，而静态 Control 全程 300 s 冻结在 `4294967295` (`0xFFFFFFFF`, `dx=0`)。
     - **`A8ED50` 在"交战窗"极微弱且反复跌回 0，不能代表持续火拼**：`P3_notanks` 全程 `A8ED50` 范围仅 `(0, 3)`、`dose400` 仅 `(0, 3)`、`P4` 仅 `(0, 4)`，且多个配置在停帧前多次回落至 `0` 或 `1`（如 `P3` 停帧前仅 `A=1`）。
     - **死亡/毁伤比"开火"更像真正的时间锚**：`PRESSURE.md` §0 称"A8ED50 首非零后 2.5–9 s"，但自身表 §3 与 §5.2 实测交战窗长为 `3.37–12.32 s`（`dose1500` 为 `10.44 s` / `14.8 s`，`dose800` 为 `12.32 s`，`P2` 为 `10.25 s`，均超出 9 s）；更重要的是，**`P3` / `P4` / `P4rerun`（同为 90 敌对 12 TESLA）全在 `A8ED50 != 0` 后仅 `105–111` 帧（`3.37–3.56 s`）同步停帧**——这正好是 `TESLA`/炮火首次击毁第一批单位或建筑（并释放乘员步兵/拆链）的时间尺度，而非炮弹出膛的时刻。
     - 此外在 `dose400`、`P3`、`P4`、`P4rerun` 中，`0x00B0CE88`（全局脏矩形向量 Count）在正常期大多为 `0`，却都在停帧前 **0–3 帧（0–66 ms）** 突然跃升至 `4..6`（提示崩溃发生于某一帧逻辑处理完毁伤/重绘注册之后、渲染排空 `0x00B0CE88` 之前）。
- **替代时序锚建议**：
  1. **移动与寻路起始锚**：`0x0087E8E0`（`PathFinder` 代际戳）首次偏离 `-1`（`0xFFFFFFFF`）并持续递增的时刻；
  2. **物体销毁与步兵生成锚**：`InfantryClass::Array.Count`（步兵全局向量 Count）从 `0` 跳变为 `>0` 的精确帧，以及 `BuildingClass::Array.Count` / `UnitClass::Array.Count` 首次发生递减的时刻（可严格分辨"开火 → 击毁 → 乘员产生 → 崩溃"）。
- **判决**：**R03 把 `0xA8ED50 != 0` 当作唯一事件锚不成立（`[本次实测]`）**；把开火前长窗的寻路积压与击毁后置延时混为一谈。

---

### 检查 6 · `0x0051C2D3` 崩溃点语义与反汇编定位

- **我查了什么**：静态反汇编 `work/gamemd.exe`（`SHA256 73201CC0...`）中的 `0x0051BF90..0x0051C800`、全镜像指针/相对调用交叉引用、所有类虚表槽 `+0x1AC` 与 `+0x1D4`、+0x270 读写点、`CellClass::AddObject/RemoveObject (0x0047E8A0 / 0x0047EA90)`、`TechnoTypeClass`/`UnitTypeClass`/`BuildingTypeClass` 对 `+0xCCD` (`Crewed`) 的构造默认及销毁生兵链 `0x00707D20` / `0x007381D5`，并核对转述调用栈 `0x42A595 / 0x429F5A / 0x4DBE6B / 0x42CC07`。
- **证据**（`[本次实测]`，见 `EVIDENCE/disasm_51C2D3.stdout.txt`、`EVIDENCE/check_6_deep_disasm.stdout.txt`、`EVIDENCE/check_6_part2_ctors_and_celllist.stdout.txt`、`EVIDENCE/check_6_part3_unittype_crewed_and_270.stdout.txt`、`EVIDENCE/check_6_part4_cell_unlink_and_270.stdout.txt`）：
  1. **函数归属唯一锁定为 `InfantryClass::IsCellOccupied`**：
     - `0x0051C2D3`（`FF 90 D4 01 00 00`）位于函数 **`0x0051BF90`**（`ret 0x14`）内部。
     - 全 `.text` 无任何直接 `call/jmp` 到 `0x51BF90..0x51C800`；全 `.rdata`/`.data` 仅有一处函数入口指针引用 **`0x007EB204`**，它是 **`.?AVInfantryClass@@` 主虚表 `0x007EB058` 的 `+0x1AC` 槽（第 107 槽）**！
     - **坦克 (`UnitClass`, `0x007f5c70`) 在 `+0x1AC` 槽指向 `0x0073F0A0`，不走 `0x0051BF90`**；`BuildingClass` 走 `0x00449440`，`FootClass` 走 `0x004D9C10`。
  2. **为什么 0 步兵图能进 `InfantryClass` 方法**：
     - `rulesmd.ini` 实测：`NAPOWR`、`GAPOWR`、`NACNST` 均显式配置 **`Crewed=yes`**；`TESLA` / `ATESLA` 为 `Crewed=no`；`[MTNK]` 未配置 `Crewed` 且 `TechnoTypeClass` 构造 `0x0071145A` 默认置 `+0xCCD` 为 `0`、`UnitTypeClass` 未覆写。
     - 摧毁 `Crewed=yes` 建筑或单位（`0x00707D20` / `0x007381DB` 查 `+0xCCD`）会分配 `0x6F0` 字节 **`InfantryClass`**（`AlliedCrew=E1` / `SovietCrew=E2`），幸存步兵随即执行寻路（`0x0042CC02 -> 0x00429A90 -> 0x00429F54 call [edx+0x1AC]` → **`0x0051BF90`**）！
  3. **崩溃指令与空指针来源**：
     - 在 `0x0051C23F..0x0051C2D3` 中，`ebp = this (InfantryClass*)`，`[esp+0x38] = pCell (CellClass*)`；先读取 **`esi = [pCell + 0xE4]`（`CellClass::FirstObject`）** 或 `0x51C237` 读取 **`esi = [pCell + 0xE8]`（`AltObject`）**，并在循环尾 `0x51C70F` 沿 `esi = [esi + 0x30]`（`ObjectClass::NextObject`）遍历。
     - 至 `0x0051C2CF: mov eax, [esi]; mov ecx, esi; call [eax+0x1D4]`（`0x0051C2D3`）。
     - RTTI 全类虚槽 `+0x1D4` 核查证实：`TechnoClass`/`UnitClass`/`BuildingClass`/`InfantryClass`/`FootClass` 均指向 **`0x0070C5B0`（`mov al, byte ptr [ecx+0x270]; ret`）**；`ObjectClass`/`TerrainClass`/`OverlayClass`/`SmudgeClass`/`AnimClass`/`BulletClass` 均指向 **`0x004264E0`（`xor al, al; ret`）**——**没有任何合法派生类的 `+0x1D4` 槽为空**。若如转述（`eax=0`，**原件已丢失**）于 `0x0051C2D3` 崩在访问 `0x1D4`，唯一的可能是 **`CellClass` 对象链表节点 `esi` 本身的虚表指针 `[esi]` 为 `0`**（悬空释放块清零，或重叠底座破坏了 `[obj+0x30]` 链表）。
  4. **对转述调用栈的静态核验**：
     - `0x429F5A`：其前指令 `0x00429F54` 确为 `call dword ptr [edx+0x1ac]`（调用 `IsCellOccupied`）；
     - `0x42CC07`：其前指令 `0x0042CC02` 确为 `call 0x429a90`（`FindPath` 子段）；
     - `0x4DBE6B`：其前指令 `0x004DBE68` 确为 `call dword ptr [ecx+0x18]`（`Locomotor` 查询）；
     - **`0x42A595` 存疑**：`0x0042A590` 实为 `call 0x4cac40`（浮点开方辅助段），其后 `0x0042A595` 为 `fadd dword ptr [esi+4]`，并非 `0x429F5A` 的直接调用帧，应为无帧指针下 SEH 栈扫描捡到的残余返回地址或转述误差（再次印证原始 `except.txt` 缺失造成的核验盲区）。
- **判决**：**R03 把 `0x0051C2D3` 简化为"战斗摧毁某通用弹药/目标链导致空虚调用"的静态推断严重失准（`[本次实测]`）**；实测指向 **`InfantryClass` 步兵寻路占用检查遍历已损坏/悬空的 `CellClass+0xE4` 链表节点**。

---

### 检查 7 · 静态对照等价性批判与最小判别实验

- **我查了什么**：对比 `trip_control_dose1500_static` 与 10 组压测 `run.ndjson` 的 `0x0087E8E0`（`PathFinder` 代际戳）及行为路径差异。
- **证据**（`[本次实测]`，`EVIDENCE/check_5_7_ndjson_and_crewed.stdout.txt:150-437`）：
  - `trip_control_dose1500_static`（1522 对象全 Guard，49,751 拍，300.003 s，9376 帧）：
    - **`X87E8E0` 全程恒为 `4294967295` (`0xFFFFFFFF`)，`dx = 0`，`steps_with_dx = 0`**；`A8ED50` 恒为 `0`；`B0CE88` 恒为 `0`。
  - 所有 10 组 Hunt 压测：`X87E8E0` 从开局第 1 样本前就已脱离 `-1`（达 `98..2694`），并在开火前与交战期持续高速攀升至 `560..16919`。
- **关键批判**：全 Guard 对照与 Hunt 加压臂之间**同时变化了四条完全不同的代码路径**，绝非单变量"是否开火"：
  1. **地面移动与 A* 寻路路径**（`0x4D3920 -> 0x42C900 -> 0x429A90 -> IsCellOccupied`，Guard 完全没进过）；
  2. **单位/建筑受损摧毁与 `CellClass::RemoveObject` 拆链**（涉及重叠 `NAPOWR` 的 `NextObject` 链）；
  3. **`Crewed=yes` 生成 `InfantryClass` 并运行步兵寻路 `0x0051BF90`**（Guard 完全没有步兵产生）；
  4. **弹药 `BulletClass` 开火与伤害结算**（R03 唯一归因的路径）。
- **判决**：**静态 Guard 对照不能隔离"交战/开火"，更不能证明非交战混杂因子已被排除（`[本次实测]`）**。

**区分"移动寻路 vs 交战摧毁 vs 建筑重叠/乘员步兵"的最小三臂判别实验**：
1. **判别臂 M1（纯移动寻路臂）**：同 `100×100` 图、保留同布局或全 400–1200 辆敌 `Hunt` MTNK，但**玩家仅放 1 个非交战/隐形/停火目标或友军全结盟（零 `A8ED50`、零伤害）**，并用地图路径或巡逻点让敌军连续移动 ≥120 s —— 若不崩，直接否证"纯移动寻路过载致崩"；
2. **判别臂 M2（纯交战·去重叠·去 `Crewed` 臂）**：取崩溃极稳定的 `P4`（90 敌 `Hunt` vs `TESLA` + `NAPOWR`），**仅删去 6 座 `NAPOWR`（消除 `3x2` 底座重叠 + 消除 `Crewed=yes`）或改 `NAPOWR` 间隔 col ≥ 3 且设地图内 `[NAPOWR] Crewed=no`（与 `TESLA` 由触发/电厂不重叠供电对比，或纯 90 敌 `Hunt` vs 100 友 `Guard` MTNK 无任何建筑）** —— 若 120 s 不崩，即证崩溃不是"坦克/TESLA 交战"本身，而是建筑重叠或乘员步兵；
3. **判别臂 M3（重叠 vs `Crewed` 二选一消融）**：保留 6 座 `NAPOWR` 但拉大间距 col 步长 ≥3（使重叠格 `10 → 0`，仍保留 `Crewed=yes`），对比"保留重叠但地图覆盖 `[NAPOWR] Crewed=no` `NACNST Crewed=no`（0 步兵生成）"。

---

## §3 · 混杂因素排序表（按"同时解释 8+2 个崩溃、静态 Control 绿及 W84 df 稳定"能力排序）

| 排名 | 混杂因素 | 解释力覆盖分析（为何 10 次崩溃 / Control 绿 / W84 df 绿） | 分级 | 最小否证实验 |
|---|---|---|---|---|
| **1** | **`Crewed=yes` 建筑摧毁生成 `InfantryClass` 幸存兵，触发 `InfantryClass::IsCellOccupied (0x0051BF90)` 遍历异常单元格节点（或二者叠加）** | **完美解释全集**：① 解释了为什么 0 步兵地图会死在**仅属 `InfantryClass` 的 `0x0051BF90`**；② 所有崩溃组（含 `notesla400`、`P2`、`P3`、`P4`、`singlehouse`）都有至少 6 座 `Crewed=yes` 的 `NAPOWR`；③ 解释 `P3`/`P4`/`P4rerun` 精准在首弹后 ~3.5 s（建筑被打爆时刻）停帧；④ 静态 Control 与 `W84 df`（仅 1 座 `Crewed=no` 的 `TESLA`）零乘员步兵故全绿 | `[本次实测]` + `[静态推断]` | 在 `P4` 地图写入 INI 覆写 `[NAPOWR] Crewed=no`（如同时消重叠对比更佳）：若不再出现崩溃/步兵向量 Count 始终为 0，即锁定 `Crewed` 生兵为必要链条 |
| **2** | **`NAPOWR` (`3x2` 步长 2) 与 `NACNST` (`4x4`) 物理底座重叠（10~14 格）破坏 `CellClass+0xE4` / `[obj+0x30]` 单链表，摧毁拆链后遗留悬空/清零 `[esi]==0` 节点** | **强烈解释绝大部分谜团**：① `CellClass::AddObject (0x47E8A0)` 把同格多个 `BuildingClass` 串入单一 `[obj+0x30]` 链，`RemoveObject (0x47EA90)` 按足迹逐格拆链时对共用 `+0x30` 清零极易致多格链表错位或悬空；② `P4` 虽删 `NACNST` 仍有 **10 格 `NAPOWR` 重叠**故仍死；③ 解释转述中 **`eax=[esi]=0`（没有任何合法类虚表或 `+0x1D4` 为空）** 的最自然物理解释；④ Control 中建筑未死未拆链、W84 df 重叠为 0 故均全绿 | `[本次实测]` + `[静态推断]` | 保持 `P4` 全部单位/建筑数量与 `Crewed=yes` 不变，**仅把 6 座 `NAPOWR` 列距由 2 改为 ≥3（重叠格 `10 → 0`）**：若绿跑 ≥120 s，即可证明"底座重叠"为主真因 |
| **3** | **无 `Crewed` / 无重叠下的 `TESLA` 与大量建筑供电/炮火摧毁行为（W84 df 实为 `1 TESLA` 无电厂）** | 解释 `W84 df` 与 W85 的电力状态差异；但 **无法单独解释 `notesla400`（`TESLA=0`）仍然崩溃**，仅能作为辅助放大器 | `[本次实测]` | 见 §2.7 M2（无 `NAPOWR` 仅坦克交战，`0` 电厂 `0` TESLA） |
| **4** | **`Hunt` 单位长距离密集移动与连续 `FindPath` 寻路（`X87E8E0` 狂飙）** | 解释 `Guard` 对照与开火前窗口差异（`20.38%` vs `32.4%`）及部分崩溃组在交战前已寻路上万次；但 **无法解释为什么不走 `0x0051BF90`（`UnitClass` 用 `0x73F0A0`）且为什么总在首次交战击毁后约 3.5–12 s 才爆** | `[本次实测]` + `[静态推断]` | §2.7 判别臂 M1（纯 `Hunt` 移动无攻击目标跑 120 s） |
| **5** | **坐标越界 / Unit-Unit 初始同格堆叠** | **解释力 = 0** | `[本次实测]` **已否决** | 已在检查 1–2 用全量解析否决（均 `0`） |

---

## §4 · 对 `0x0051C2D3` 所属函数的反汇编解读与最小取证整改规范

### 4.1 `0x0051BF90`（`InfantryClass::IsCellOccupied`）关键字节链（`[本次实测]`）

1. **函数身份与唯一归属**（`EVIDENCE/disasm_51C2D3.stdout.txt:719-720`、`check_6_deep_disasm.stdout.txt:42-46, 173-178`）：
   - 入口 `0x0051BF90`（`sub esp, 0x24`, `ret 0x14`），在 `.rdata` 唯一登记于 **`0x007EB204`** = **`.?AVInfantryClass@@` (`0x007EB058`) `+0x1AC` 槽（第 107 槽 `IsCellOccupied`）**。
   - 调用链上文（对应转述调用栈 `0x42CC07` / `0x429F5A` **（转述，原件已丢失）**）：`0x0042CC02 call 0x429a90` → `0x00429F54 call dword ptr [edx+0x1AC]`。
2. **故障指令精确上下文**（`EVIDENCE/check_6_deep_disasm.stdout.txt:185-235, 289-292`）：
   - `ebp` = `this`（`InfantryClass*`）；`[esp+0x38]` = `pCell`（`CellClass*`）。
   - `0x0051C237`: 若读 alt 层则 `esi = [ecx + 0xE8]` (`AltObject`)；否则 `0x0051C243`: **`esi = [edx + 0xE4]` (`FirstObject`)**。
   - `0x0051C251`: `cmp esi, ebp; je 0x51c70f`（跳过自身）。
   - 若无特殊通行检查跳出，即进入：
     ```asm
     0x0051c2cf: mov  eax, dword ptr [esi]        ; 取 Cell 中当前对象 esi 的虚表指针 vptr
     0x0051c2d1: mov  ecx, esi                    ; ecx = this = esi
     0x0051c2d3: call dword ptr [eax + 0x1d4]     ; 调用虚槽 +0x1D4 <-- CRASH 点
     ```
   - 循环尾 `0x0051C70F`: `mov esi, dword ptr [esi + 0x30]`（沿 `ObjectClass::NextObject` 推进），`test esi, esi; jne 0x51c251`。
3. **虚槽 `+0x1D4` 含义与"什么对象会空"**（`check_6_deep_disasm.stdout.txt:27-86, 340-350`；`check_6_part2:208-210`）：
   - `TechnoClass` 系（含 `UnitClass`, `BuildingClass`, `InfantryClass`, `FootClass`）在 `+0x1D4` 均挂 **`0x0070C5B0`**：`mov al, byte ptr [ecx+0x270]; ret`。
   - `ObjectClass`、`TerrainClass`、`OverlayClass`、`SmudgeClass`、`AnimClass`、`BulletClass` 在 `+0x1D4` 均挂 **`0x004264E0`**：`xor al, al; ret`。
   - **关键推论**（`[静态推断]`）：合法 C++ 对象不可能出现 `slot[+0x1D4] == 0`，连 `ObjectClass::~ObjectClass` 析构也只会回写父虚表而不是清 `0` vptr。若转述中 **`eax == 0` 成立（原件已丢失）**，则必是 **`esi`（挂在 `pCell->FirstObject` 或 `AltObject` 单链表上的指针）所指向的堆内存首 4 字节 `[esi]` 已被清零/释放覆盖**——即 `CellClass` 链表残留了已释放对象的**悬空指针**。
   - **为何底座重叠结构极易制造此悬空节点**：`check_6_part4_cell_unlink_and_270.stdout.txt:126-158, 275-315` 实测显示，`CellClass::AddObject (0x47E8A0)` 对 `WhatAmI()==6` (`BuildingClass`) 顺链表挂到尾部后写 **`[ebp+0x30] = 0`**；而一座 `3x2` 的 `NAPOWR` 只拥有**唯一一个 `[ebp+0x30]`**，却需同时挂进 6 个 `CellClass` 的链表。当相邻 `NAPOWR` 重叠 2 个或更多格时，后添加的建筑会改写前一座建筑共享的 `[Building_A+0x30] = Building_B`；一旦其中一个建筑在战斗中被摧毁触发 `RemoveObject (0x47EA90)`，逐格拆链并写 `[esi+0x30] = 0` 会使部分单元格链或从后续细胞中摘除失败、或将已删除/内存复用的建筑指针滞留在其它重叠格的 `+0xE4` 链上，待 `Crewed=yes` 产生的 `InfantryClass` 寻路扫过该格 `pCell+0xE4` 时即撞上 `0x0051C2D3`。

### 4.2 针对原件丢失的最小崩溃取证卡（整改建议）

因 W85 `finalize` 还原覆盖了沙箱 `except.txt`，导致全组异常地址与调用栈均落为无法复核的"转述"。后续所有实机跑卡在**清理/还原沙箱之前**必须执行以下最小取证规程：
1. **逐 trip 落盘保存引擎原生日志**：若 `sandbox_game/except.txt` 的 `mtime` 或 `sha256` 与基线不同，必须将其完整复制归档为 `out/<trip>/except_<trip>.txt`，并在 `TRIP_RESULT.json` 记录 `except_sha256`、`except_size` 与 `EIP/Access/Stack` 摘要；
2. **采集用户态 Minidump**：触发 `WerFault` / `Internal Error` 弹窗前或进程退出瞬间由 Procdump / WER `LocalDumps` 捕获迷你转储（含线程寄存器、栈内存及堆指针周边 256 B，直接看清 `[esi]` 究竟是 `0` 还是其它坏指针）；
3. **补充状态向量只读探针**：除 `0xA8ED50` 与 `0x87E8E0` 外，在 `run.ndjson` 纳入 `InfantryClass::Array.Count`、`BuildingClass::Array.Count`、`UnitClass::Array.Count`，以精确锁定崩溃发生在"开火"、"首例毁伤"还是"首名乘员步兵生成"之后。

---

## §5 · 若本复核成立，原 `PRESSURE.md` 必须改写的语句清单

| 原报告位置 | 改前原文（`PRESSURE.md` 逐字摘录） | 改后建议（按本次实测修正口径） |
|---|---|---|
| §0 L12–16 | 「"更重战斗"（Hunt 大兵团强制交战）在 8 个配置……下**全部在 A8ED50 首非零后 2.5–9 s 触发引擎崩溃/内部错误**（AV @ `0x51C2D3`：`call [eax+0x1D4]` 且 `eax=0`，空 `this` 虚调用）；而**同图同布局同对象数的静态对照（1522 对象全 Guard）300 s 全绿、0xA8ED50 全程 0**。」 | 「在本轮含 **10~14 格 `NAPOWR`/`NACNST` 底座物理重叠** 且含 **`Crewed=yes` 建筑** 的地图构型下，8 个 enemy-Hunt 配置均在 `0xA8ED50` 首非零后 **3.37–12.32 s**（且此前 `0x0087E8E0` 已持续跃变）触发引擎崩溃或内部错误（转述 AV @ `0x0051C2D3` 实属 **`InfantryClass::IsCellOccupied`**，原 `except.txt` 已丢失待复核）；静态 Guard 对照因 **`0x0087E8E0` 全程冻结（0 移动/0 销毁/0 乘员步兵）**，未能排除上述结构混杂因素，不能归因为纯交战触发。」 |
| §3 L67 | 「先例：W84 df：30 Hunt vs 1 TESLA，无 NACNST/NAPOWR/GAPOWR，60×60」 | （正文 L67 写对了 `TESLA`，须同步核实无电厂且无底座重叠/无乘员：`「先例：W84 df：30 Hunt vs 1 TESLA（Crewed=no, 1x1, 无电厂, 重叠 0 格），60×60」`，并修正 `w84_design` 叙事勿混作 `ATESLA`） |
| §3 L71–74 | 「**失败臂剩余公共要素**（与稳定臂差集）＝交战 + {敌 GAPOWR / 玩家 NAPOWR / 100×100 图 / Hunt 规模} 中的某组合……W84 稳定臂与本卡失败臂的最小差集 = 敌 GAPOWR + 玩家 NAPOWR + 地图尺寸三者的某子集。」 | 「**失败臂与稳定臂的实际差集**还包含两项高怀疑度机械因子：① **玩家 `NAPOWR`/`NACNST` 之间 10~14 格建筑底座重叠**；② **`Crewed=yes` 建筑（`NAPOWR`/`NACNST`/`GAPOWR`）在受损毁时产生原图不存在的 `InfantryClass` 幸存兵**；此外 `w85_pressure/work/` 磁盘 JSON 为 P4（90 单位无 `NACNST`），主实验包请以各自 `out/trip_*/` `.MAP` 为准。」 |
| §4 L78–83 | 「**[本次实测]** `except.txt`（引擎在 dose800 内部错误时写入沙箱，26,236 B，12:31:32）……EAX=`0x00000000`……栈含返回地址 0x42A595 / 0x429F5A / 0x4DBE6B / 0x42CC07」 | 「**[未证（原件已丢失）]** 原文所述 26,236 B `except.txt` 未随沙箱归档保留；以下 `EIP=0x0051C2D3`、`EAX=0` 及栈地址系报告转述。静态反汇编实测证实 `0x0051C2D3` 属于 **`InfantryClass::IsCellOccupied (0x0051BF90)`** 遍历 `CellClass+0xE4/+0xE8` 对象链表；其中 `0x42A595` 在镜像中对应浮点 `sqrt` 后返回点而非 `IsCellOccupied` 调用帧。」 |
| §5.2 L127–130 | 「差值来自 Hunt 单位的移动/寻路……0xA8ED50 在全部交战窗转非零（对照臂全程 0）——E1 独立证据成立。」 | 「0xA8ED50 在开火前窗口虽为 0，但 `0x0087E8E0` 在开火前已累积增长 `226..9357` 次，且交战窗内 `0xA8ED50` 屡次跌回 0、在 `P3` 等组峰值仅 3；该字段只证明向量曾经入队 Bullet，不能充当开火事件精准起点或崩溃直接原因。」 |
| §8 L164–165 | 「否则任何 ≥30 Hunt + 基建/坦克的配置都会在 2.5–9 s 内崩，无法支撑 10 趟区组设计。」 | 「下轮应优先执行 §2.7 最小三臂消融（去 `NAPOWR` 重叠、关闭/验证 `Crewed=yes`、单测纯移动），在未分离重叠底座与 `Crewed` 步兵前，不得断言'任何 ≥30 Hunt + 基建/坦克必崩'。」 |
