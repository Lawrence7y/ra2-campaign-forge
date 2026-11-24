# C06 · UNKNOWNS（未证 / 待 P1 细化）

本文件记录本片普查中**未能证明**的部分。所有一行语义均为 `[未证]` 猜测，未写新 `[已证]` 发现。

## 1. 452 个零证据函数（source=none → S22 兜底）
- `EVIDENCE/classification_trace.tsv` 中 `source==none` 共 **452** 行：无 self_known 名、无 vtable 槽、无源文件模块、无强字符串、无亲戚名投票、无导入 API。
- 全部归 S22（随机数/数学/字符串/第三方库/通用容器）仅为兜底，**不是已证归属**。
- 建议 P1 用 YRpp 头文件地址名二次扫描 / re_atlas kb 具名方法再细化；这批地址较多集中在 0x63xxxx–0x640xxx 尾段（MPGameMode 系未具名方法、UI wrapper、动画/特效小函数）与散落的小 wrapper。

## 2. 三通道 atlas 空洞（call32 24 / jmp32 78 / jmp8 301 = 403 行 / 388 独立地址）
口径见 `PROGRESS.md` 核心数字 3。未证部分：
- **301 个 jmp8 洞目标**（`atlas_gaps.tsv` 中 chan=jmp8）：绝大多数引用站点在洞内（sites_in_fn=0），首指令分布 mov / cmp / test / add / push / call 等，形态多为**函数内短跳分支标签**或**跨函数的 switch/循环跳转**，非确证新入口。未逐点证明"从真入口线性可达"，按 Lead 口径 jmp8 **不计入疑似真入口**。
- **2 个 jmp8 假阳性**（`0x5DF100`、`0x5DF104`）：首次字节落在 `add al, byte ptr [edx]`（2 字节，`0x5DF0FF`/`0x5DF103` 起）内部。经 `audit_lib.boundary_check` 与自建 skipdata 线性反汇编**双通道自证非指令边界**；`EVIDENCE/gap_channels.tsv` boundary 列标 False。按纪律 #3 不把 boundary_check 结果当唯一判据，此处两法一致，故确认假阳性。
- **6 个 jmp32 已标「疑函数内分支标签」**：`0x5E1F9E`(jle)、`0x5FBCC7`(cmp)、`0x611A62`(cmp)、`0x61218E`(cmp)、`0x615226`(test)、`0x61C937`(cmp)，首指令是明确的条件分支/比较，按 Lead 口径不计入疑似真入口。
- **72 个非分支标签 jmp32** 仍须 P1 逐点用序言+调用链证真：**96 个疑似真入口是上界**（call32 24 + 非分支 jmp32 72），`verify_core.py` 确认 union 亦为 96（两类不重叠）。
- **15 个地址同时被 2 通道命中**（403 行 − 388 独立地址）：每通道在 `atlas_gaps.tsv` 各占一行，通道计数按行/按通道内独立目标一致。
- boundary_check 分布：401 True / 2 False / 0 unknown（本片无 span≥max_bytes 的 bail 案例，故未出现 unknown；如出现按纪律 #3 保留 None 不当 False）。

## 3. S10 计数偏低（2）、S14 high=24 与多类 vtable 的 most_common 规则
- 本片 vtable 原始命中中 `MissionClass` 70、`RadioClass` 66、`FootClass` 29 等，但多数函数同时含 `ParticleClass`/`ObjectClass`/`OverlayClass` 等其他类；分类按 C05 同规格「多类取 Counter.most_common 首个（并列取先出现）」→ 大量归 S20/S06/S05/S18，S10 仅剩 2。
- 这些函数**仍是 high**（mapped core 类），只是子系统归属分散；high 总数不受影响。MissionClass/RadioClass 单独归属 `[未证]`，建议 P1 按 vtable 主表（col_off=0 主槽）重新定主类。

## 4. 模板容器类的子系统归属（潜在误归）
- 类型如 `T_DynamicVectorClass_PAVMapStage__`、`T_VectorClass_PAVSpotLightClass__`、`T_VectorClass_UAcceleratorTracker__` 等，按"C05 同规格"的字符串包含匹配被归到元素类型对应的 S21/S07/S14（core=True，计入 high）。
- 它们本质是**通用容器**（应归 S22），元素类型只是模板参数。这是 C01–C05 共用规则的固有偏差，本卡为口径一致未单独改判；建议 P1 统一修正 `class_to_sub` 对 `T_VectorClass_*`/`T_DynamicVectorClass_*` 前缀优先归 S22。

## 5. 具名函数语义仍为猜测 / 本片已证地址照引不推翻
- 41 个 `[已证]` 仅证明"名字来自 YRpp/kb 地址名"，不证明其一行语义（如 `MPGameModeClass::SpawnBaseUnits`、`ObjectClass::DistanceFrom` 的具体行为）。语义列均按名推测，标 `[未证]`。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`；本片地址段内的已证事实（DrawIfVisible `0x5F4B10`、Limbo `0x5F4D30`/`0x5F4EC0`、Slot-114 `0x5F5F40`、MAPSEL 阶段 `0x5CEEF0`/`0x5CF830`、INI 键上限 `0x5CF04F`/`0x5CF367`）均按台账原结论引用，本卡不推翻、不新增 [已证]。台账中 `0x5C4BE3`（MPGameMode 无守卫调用点）与 `0x55AFB0`（11 路 AI 派发阶梯）落在本片地址范围**之外**（均属 C05 片 0x54A290–0x5CBD1F），本卡未触碰。
