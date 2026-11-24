# C06 · DISAGREE（口径差异 / 无事实冲突）

## 1. 与 C05 口径的差异：仅追加本片类族规则（无口径冲突）
- 本卡 `classify.py` **完整保留 C05 的 CLASS_RULES / NAME_CLASS_RULES / MOD_RULES / STR_SPECIFIC / IMP_RULES**，仅在末尾以 `# C06+` 追加本片地址段出现而 C05 未覆盖的类族（`Particle`/`VoxelAnim`/`Wave`/`MS*Anim`、`Overlay`/`Terrain`/`Smudge`、`ParasiteClass`、`BuildingLightClass`/`SpotlightClass`、`NullModemClass`/`MessageListClass`、`GameOptionsClass`、`UI::`、`PlanningTokenClass`、`MapStage`/`MapSelection`）与对应命名/模块/导入规则。
- 分级定义、high 判据（self_known + vtable-core）、grade 三级、来源优先级、站点归属（函数区间包含）、三通道 gap 定义：**全部照 C05 / Lead R14-R1 口径执行，无异议**。
- 因此 high=382（self_known 41 + vtable-core 341），与 C05 的 563 差异纯由两片类族结构不同所致；**未为对齐 C05 而增删任何实测结果**。

## 2. 与 C04 旧口径的差异：atlas 空洞三通道（按 Lead 统一裁定执行）
- C04 的 `atlas_gaps.tsv` 只收 rel32（E8 call + E9 jmp）、把 EB 短跳单列于 UNKNOWNS；本卡按 **Lead 2026-11-17 统一口径**三通道分列：call32(E8) / jmp32(E9) / jmp8(EB) 各为一类，`note` 标注分支标签与引用站点位置。
- 本片数字为 **call32=24 / jmp32=78 / jmp8=301**（疑似真入口 96）；若按 C04 的"仅 rel32"宽松旧口径会得到 102（=24+78）。**不是数据矛盾，是口径统一**；本卡以 Lead 裁定为准。
- 三通道均满足纪律 #1（至少一条不依赖 function_atlas.tsv 的 entry+size）：通道 B 为全 .text skipdata=True 逐条反汇编，按 opcode 首字节分类目标，site 归属只用区间包含 `owner()`。

## 3. 与既有事实底座无冲突
- 本片地址 0x5CBD20–0x640A3C 覆盖的类族（S20 粒子/Anim 特效、S06 地表、S13 Bullet/Parasite、S18 MPGameMode/Modem、S09 UI、S14 Radio/House、S05 Object/Techno/Foot、S21 战役阶段）与 `R14_COMMON.md` §1–§7、台账 §911–§928 无口径冲突。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`：本片内 `0x5CEEF0`/`0x5CF830`/`0x5CF04F`/`0x5CF367`（MAPSEL 阶段与 INI 上限）、`0x5F4B10`/`0x5F4D30`/`0x5F4EC0`/`0x5F5F40`（绘制/Limbo/Bullet AI）均以既有结论引用，未推翻任何 [已证]；台账 `0x5C4BE3`/`0x55AFB0` 落在本片范围外（均属 C05 片），未触碰。
- 本卡未写任何新 `[已证]` 发现，未改 `R14_COMMON.md` / 台账 / `COVERAGE\coverage.tsv`。

## 4. 未与 Lead 裁决口径 disagreement 的项目
- 站点归属用「函数区间包含」`owner()`（`R14_COMMON §6-17`），已抽检 `owner(0x482854)=None`（atlas 空洞不被错归）。
- capstone `skipdata=True`（全 .text 解出 1,394,120 条）；`boundary_check` 超 max_bytes 返回 `unknown`（保留 None 不当 False）：已落实。
- 2 例 `boundary_check=False`（`0x5DF100`/`0x5DF104`）**不**当作"非入口"的权威判据：用自建 skipdata 线性反汇编二次确认落在 `add al,[edx]` 指令内部，两法一致方确认假阳性（纪律 #3）。
- 未用 Ghidra（并发 ≤4 留给别卡）；未改 gamemd.exe / ddraw.dll / ra2youli\；未 git commit/push。
