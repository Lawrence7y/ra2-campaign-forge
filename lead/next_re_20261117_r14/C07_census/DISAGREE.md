# C07 · DISAGREE（口径差异 / 无事实冲突）

## 1. 与 C05/C06 口径的差异：仅追加本片类族规则 + 两处数据修正（无结论冲突）
- 本卡 `classify.py` **完整保留 C05/C06 的 CLASS_RULES / NAME_CLASS_RULES / MOD_RULES / STR_SPECIFIC / IMP_RULES 框架**，仅以 `# C07+` 追加本片出现而 C05/C06 未覆盖的类族（RAMFile/RawFile/BufferIOFile/FileClass→S03、RulesClass→S04、ScriptClass/ScriptTypeClass/SideClass→S14、SlaveManager/SpawnManager→S10、RadSiteClass→S13、SuperClass/SuperWeaponTypeClass→S16、ScoreFont/ColorScheme→S09、Networking/PhoneEntry/GlobalPacketType/MultiMission→S18、Scenario/Skirmish 字符串）与对应命名/模块/导入规则。
- **数据修正 1（虚表槽）**：C05/C06 的 `collect.py` 直接读 `vtables_v2.json['slots']`；本卡改为从 `.rdata` RTTI COL 直读真实槽数（实测 790/1205 差 +1），这是执行卡任务书明确要求的 off-by-one 坑修正，非结论冲突。影响：vt 槽命中从"按 JSON"会漏掉虚表末槽对应的函数，本卡补全。
- **数据修正 2（具名前向声明）**：具名提取加 `FWD_DECL` 正则过滤 `class X;`，防止方法名错挂前向声明类名（C01 曾错 23 处）。C05/C06 未显式加此过滤，本卡按任务书要求补上。
- 分级定义、high 判据（self_known + vtable-core）、grade 三级、来源优先级、站点归属（函数区间包含）、三通道 gap 定义：**全部照 C05/C06 / Lead R14-R1 口径执行，无异议**。high=559（self_known 109 + vtable-core 450）与 C05 563、C06 382 的差异纯由三片类族结构不同所致。

## 2. 与 C05/C06 的「疑似真入口」判据差异：采用 R14-R1 严格版（按任务书）
- C05/C06 的 `gap_full.py` 用宽松判据 `suspect = call32 ∪ 非分支标签 jmp32`（仅凭 E8/E9 指向 + 首指令非分支）。本卡按 **R14-R1 严格判据**（前三片审计实证）：**16 字节对齐 + 前驱为 nop 填充/ret/jmp + 首指令不像循环体分支标签**，仅靠有 E8/E9 指向不足以称真入口。
- 本片数字 call32=14 / jmp32=18 / jmp8=93（行=独立地址=125）。若按 C05/C06 宽松口径会得到 29（=14 call32 + 15 非分支 jmp32）；**按 R14-R1 严格口径为 17**（14 call32 + 3 jmp32）。这不是数据矛盾，是判据按任务书统一升级；本卡以 R14-R1 为准。
- 两套独立实现交叉确认 17：`gap_full.py`（全 .text 指令起点表 + 线性跳过 nop/int3 判前驱）与 `verify_core.py`（前驱用原始字节 C3/C2/E9/EB/90/CC，不同数据通路）逐地址一致。

## 3. 与既有事实底座无冲突
- 本片地址 0x640A40–0x6BF750 覆盖类族（S09 UI、S04 RulesClass、S11 Ship/Rocket Locomotion、S14 Radio/Script、S18 网络会话、S06 地表、S03 文件、S17 序列化、S20 粒子）与 `R14_COMMON.md` §1–§7、台账 §911–§928 无口径冲突。
- 写卡前已 grep 台账：`RadSiteClass`（vtable slot 69）、`SlaveManagerClass` 有既有条目，按原结论引用未推翻；未写任何新 `[已证]`；未改 `R14_COMMON.md` / 台账 / `COVERAGE\coverage.tsv`。

## 4. 未与 Lead 裁决口径 disagreement 的项目
- 站点归属用「函数区间包含」`owner()`（§6-17），抽检 `owner(0x482854)=None`。
- capstone `skipdata=True`（全 .text 1,394,120 条）；`boundary_check` 超 max_bytes 返回 unknown（保留 None 不当 False）。本片 125 洞目标 boundary 全 True，仅作辅助；不把"全 True"当独立佐证（无鉴别力），真伪完全由 R14-R1 三条件判定。
- 双通道：通道 B 不依赖 function_atlas.tsv 的 entry+size（全 .text skipdata 逐条反汇编），与通道 A 不同源。
- 未用 Ghidra（并发 ≤4 留给别卡）；未改 gamemd.exe / ddraw.dll / ra2youli\；未 git commit/push。
