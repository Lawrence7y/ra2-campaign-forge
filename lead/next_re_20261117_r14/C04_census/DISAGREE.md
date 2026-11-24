# C04 · DISAGREE（与台账 / C01 / C02 / R14_COMMON 的冲突或措辞差异）

## D-1（中）atlas 空洞入口数口径：本卡 26（严格 rel32）vs C02 111（宽松含 EB）

- **C02 PROGRESS**：atlas 空洞入口 = **111**，采用 `audit_lib.sweep_calls` 的 call/jmp 目标，该 API 把 E8(call rel32)、E9(jmp rel32)、**EB(jmp rel8 短跳)** 一律记成 `jmp 0xADDR`，故 111 含大量 EB 命中。
- **C01 PROGRESS**：atlas 空洞入口 = **2**（仅 E8 call 目标 + 序言判据，更严）。
- **本卡 C04**：采用卡正文「全 .text 扫 **call/jmp rel32** 目标」的**严格字面**定义 —— rel32 = E8 + E9，排除 EB(rel8)，得 **26**（7 call + 19 jmp32）；另有 **69** 个仅 EB 命中的洞目标单列 UNKNOWNS，不硬算成 rel32 命中（卡正文明确要求）。
- 判读：**三卡差异是口径差异（2 / 111 / 26），非数据矛盾**。同一 `sweep_calls` 原始数据在 C04 片有 95 个 owner=None 目标（= 26 rel32 + 69 EB-only），C02 宽松口径会得 95。本卡不推翻 C01/C02 在其各自片上的结论；仅声明 C04 用严格 rel32 口径并已独立复算（`work/verify_core.py` CORE3）。合并员如需全镜像统一口径，建议 Lead 明文裁决后再统一（本卡不擅自改）。

## D-2（低）`0x4824D4` 不在本片，无冲突

- C01 提到 `0x4824D4` 为 EB 0A 短跳场景；C02 的 `atlas_gaps.tsv` 含它（在 0x482xxx）。本片范围 0x4F1840–0x54A28E，**不含**该地址；`atlas_gaps.tsv` 不含它是范围使然，不冲突。

## D-3（低）19 个 jmp32 洞目标多数是函数内部分支点

- 台账 §6-7 / §6-8 纪律禁「最近 E8/E9 目标」当入口启发式。本卡 19 个 jmp32 目标中，`0x504D2F`/`0x527466`/`0x5274BD`/`0x529394`/`0x52A153`/`0x52A345` 等首指令是 `cmp/jle`、`test/je`、循环体 —— 明显是函数内分支标签而非新入口。本卡按机械定义（rel32 目标 ∧ owner=None）收录并标 `high(jmp32-rel32)`，但**不声称**它们是真函数入口；只把 7 个 call 目标视为较强候选。若审计认为应剔除 jmp32 内部支点，核心数字 3 会变为 7 —— 本卡在 PROGRESS/UNKNOWNS 已明示此分歧空间。

## D-4（低）无已证名与作废索引冲突

- 本卡 [已证] 96 个名来自 YRpp `JMP_THIS`/`INI_READ` 与 re_atlas/kb 具名地址；抽查 `HouseClass::IsAlliedWith`（4 处）、`CCINIClass::*` 系列、`MapClass::RedrawSidebar`、`InfantryClass::AI@0x51BAB0`（台账 §24026 已有）、`InfantryClass::IsCellOccupied@0x51BF90`（台账 §10329 已有，RTTI 定名）、`MixFileClass::Bootstrap` —— 均与现有台账一致。
- R14_COMMON §1 作废索引各节落在 0x43xxxx/0x4Bxxxx/0x55xxxx–0x70xxxx；本片 0x4Fxxxx–0x54xxxx 仅 `0x51BF90`（IsCellOccupied）一条，且本卡未据它推翻任何结论。无实质性技术冲突。

## D-5（低）S09 / S22 占比高非与 §917/§918 冲突

- 本片 S09=300（23.2%）、S22=332（25.7%），源于地址区间覆盖大量 `*CommandClass` vtable 槽 + `Init.CPP` 命令串 + 通用容器模板；与真机 EIP 权重（Blitter 61.9% 等）是两个量纲（R14 §6-10）。本卡未引用 §917/§918 数字，无冲突。

> 结论：无实质性技术冲突；D-1 口径差异与 D-3 jmp32 真伪需 Lead / 审计留意。本卡未改 `COVERAGE\coverage.tsv`、未写台账、未改游戏文件、未 git commit/push。
