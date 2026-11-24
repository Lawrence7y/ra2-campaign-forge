# C05 · DISAGREE（口径差异 / 无事实冲突）

## 1. 与 C04 口径的差异：atlas 空洞入口（按 Lead 统一裁定执行）
- C04 的 `atlas_gaps.tsv` 只收 **rel32（E8 call + E9 jmp）**、把 EB 短跳单列于 UNKNOWNS；本卡按 **Lead 2026-11-17 统一口径**改为三通道分列：call32(E8)、jmp32(E9)、jmp8(EB) 各为一列/一段，`note` 标注分支标签与引用站点位置。
- 因此本片数字为 **call32=32 / jmp32=23 / jmp8=97**（疑似真入口 53），而若按 C04 的"仅 rel32"宽松旧口径会得到 **55**（=32+23）。**不是数据矛盾，是口径统一**；本卡以 Lead 裁定为准，未为与 C04 对齐而增删任何实测结果。
- 三通道均满足纪律 #1（至少一条不依赖 function_atlas.tsv 的 entry+size）：通道 B 为全 .text skipdata=True 逐条反汇编，按 opcode 首字节分类目标，site 归属只用区间包含 `owner()`。

## 2. 与既有事实底座无冲突
- 本片地址 0x54A290–0x5CBD1F 覆盖的类族（LocomotionClass / MPGameMode 系 / MapClass / MissionClass / RadioClass / UI 控件 / 电影句柄 / 压缩管线）与 `R14_COMMON.md` §1–§7、台账 §911–§928 无口径冲突。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`：`0x5B40B0`（FileSystem::LoadFile）仅以 `FUN_005b40b0` 出现在 §13409 一处非相关上下文，无已证结论被本卡推翻；其余拟提及地址（0x556600/0x5CB3A0/0x5CA800/0x5B3700/0x54F5C0）台账未出现。
- 本卡未写任何新 `[已证]` 发现，未改 `R14_COMMON.md` / 台账 / `COVERAGE\coverage.tsv`。

## 3. 未与 Lead 裁决口径 disagreement 的项目
- 分级定义、high 判据（self_known + vtable-core）、grade 三级、来源优先级：全部照 C01/C02/C04 同规格执行，无异议。
- 站点归属用「函数区间包含」`owner()`（`R14_COMMON §6-17`），已抽检 `owner(0x482854)=None`（atlas 空洞不被错归）。
- capstone `skipdata=True`、`boundary_check` 超 max_bytes 返回 `unknown`（保留 None 不当 False）：均已落实。
