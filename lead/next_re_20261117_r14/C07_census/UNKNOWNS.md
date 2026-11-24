# C07 · UNKNOWNS（未证 / 待 P1 细化）

本文件记录本片普查中**未能证明**的部分。所有一行语义均为 `[未证]`/`[静态推断]` 猜测，未写新 `[已证]` 发现。

## 1. 362 个零证据函数（source=none → S22 兜底）
- `EVIDENCE/classification_trace.tsv` 中 `source==none` 共 **362** 行：无 self_known 名、无 vtable 槽、无源文件模块、无强字符串、无亲戚名投票、无导入 API。
- 全部归 S22（随机数/数学/字符串/第三方库/通用容器）仅为兜底，**不是已证归属**。
- 建议 P1 用 YRpp 头文件地址名二次扫描 / re_atlas kb 具名方法再细化；本批多集中在 0x68xxxx–0x6Bxxxx 段（RulesClass 未具名小方法、Queue/Session/SendFile 网络 wrapper、Sidebar/Radar UI 小函数、SHP 加载辅助）。

## 2. 三通道 atlas 空洞（call32 14 / jmp32 18 / jmp8 93 = 125 行 / 125 独立地址，疑似真入口 17）
口径见 `PROGRESS.md` 核心数字 3。未证部分：
- **93 个 jmp8 洞目标**：引用站点绝大多数在洞内（sites_in_fn>0 仅 1 行），首指令多 mov/cmp/test/push/call，前驱多 plain 或 align16=N，**全部不满足 R14-R1 严格入口判据**（需 align16 + 前驱 ret/jmp/pad + 首指令非分支标签），形态为**函数内短跳分支标签**或跨函数 switch/循环跳转。未逐点证明"从真入口线性可达"。按 Lead 口径 jmp8 不计入疑似真入口。
- **3 个 jmp32 已标「疑函数内分支标签」**：`0x6582D3`(cmp)、`0x6B3523`(test)、`0x6B3D73`(cmp)，首指令是明确的条件分支/比较，不计入疑似真入口。
- **15 个非分支标签 jmp32 中仅 3 个达严格判据**（`0x661700`/`0x69B670`/`0x6B9530`）；其余 12 个 align16=N 或前驱 plain，**疑似真入口 17 是严格下界**，P1 可用序言+调用链为这批补证。
- 本片 125 洞目标 boundary_check 全 True，无 False/unknown 案例；按纪律 #3 不把 boundary_check 当权威判据（"全 True"无鉴别力），真伪判别完全依赖 R14-R1 三条件（align16 + 前驱 + 首指令），并由两套独立实现（gap_full 指令表法 / verify_core 原始字节法）交叉确认。

## 3. 虚表槽直读与 JSON 的差异（已实测，属数据修正非未证发现）
- `vtables_v2.json['slots']` 与 `.rdata` RTTI COL 直读槽数系统性差 1：1205 共有虚表中 790 真实=JSON+1、83=JSON−1、8=JSON−2、仅 324 一致。本卡**全程用直读槽数**（`EVIDENCE/vtables_direct.tsv`），未盲信 JSON。
- RTTI 直读找到 1205 张虚表（JSON 1214 张），差 9 张为本扫描器按 COL 签名+TypeDescriptor 严格匹配未收（多为无 RTTI 或异常布局），属方法论差异，非本片结论缺失。

## 4. 具名函数语义仍为猜测 / 模板容器与多类归属偏差
- 109 个 `[已证]` 仅证明"名字来自 YRpp/kb 地址名"，不证明其一行语义（如 `RulesClass::Read_CombatDamage`、`RadSiteClass::SetRadLevel`、`SpawnManagerClass::CountAliveSpawns` 的具体行为）。语义列均按名推测，标 `[未证]`。
- 模板容器类（如 `T_DynamicVectorClass_PAVRadSiteClass__`、`T_VectorClass_PAVRadarEventClass__`、`T_TClassFactory_VCStreamClass__`）按"C01–C06 同规格"字符串包含匹配被归到元素类型对应的 core Sxx（S13/S09/S17，计入 high）。它们本质是**通用容器**（应归 S22），元素类型只是模板参数。这是共用规则固有偏差，本卡为口径一致未单独改判；建议 P1 统一修正 `class_to_sub` 对 `T_VectorClass_*`/`T_DynamicVectorClass_*`/`T_TClassFactory_*` 前缀优先归 S22。
- 多类并列 vtable 按 `Counter.most_common` 取首类（同 C05/C06）：本片 Ship/RocketLocomotion、Script/SlaveManager 等常与其他类同现，S12/S16 计数偏低（S12 n=7 high=0、S16 n=1 high=0）。这些函数仍是 high（映射到 core），只是子系统归属分散。

## 5. 本片已证地址照引不推翻 / 台账核对
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`：`RadSiteClass`（vtable slot 69、INI 读取器）、`SlaveManagerClass` 等有既有条目，按原结论引用不推翻。本片 0x640A40–0x6BF750 内 `RulesClass`/`Scenario.CPP`/Network 相关地址未见与本卡冲突的 [已证] 论断。
- 本卡未写任何新 `[已证]` 发现；未改台账 / `R14_COMMON.md` / `COVERAGE\coverage.tsv`。
