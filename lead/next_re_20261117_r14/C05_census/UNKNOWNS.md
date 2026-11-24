# C05 · UNKNOWNS（未证 / 待 P1 细化）

本文件记录本片普查中**未能证明**的部分。所有一行语义均为 `[未证]` 猜测，未写新 `[已证]` 发现。

## 1. 335 个零证据函数（source=none → S22 兜底）
- `EVIDENCE/classification_trace.tsv` 中 `source==none` 共 **335** 行：无 self_known 名、无 vtable 槽、无源文件模块、无强字符串、无亲戚名投票、无导入 API。
- 全部归 S22（随机数/数学/字符串/第三方库/通用容器）仅为兜底，**不是已证归属**。
- 建议 P1 用 YRpp 头文件地址名二次扫描 / re_atlas kb 具名方法再细化；这批地址集中在 0x5Cxxxx 尾段（MPGameMode 相关未具名方法）与若干 wrapper。

## 2. 三通道 atlas 空洞（call32 32 / jmp32 23 / jmp8 97，合计 152 行 / 150 独立地址）
口径见 `PROGRESS.md` 核心数字 3。未证部分：
- **97 个 jmp8 洞目标**（`atlas_gaps.tsv` 中 chan=jmp8）：全部引用站点都在洞内（sites_in_fn=0/全部），首指令分布 mov×52 / test×12 / cmp×11 / push×7 / lea×7 / call×5 / xor×2 / fcom×1。多数形态是**函数内短跳分支**（如 `0x5500D0` mov al,[esi+0x50];test al,al;je`、`0x552657` mov al,[edx];inc edx;test al,0x80），非确证新入口。未逐点证明"从真入口线性可达"，故**不计入疑似真入口**。
- **2 个 jmp32 已标「疑函数内分支标签」**：`0x5B1E20`（cmp [ecx],0;jne）、`0x5C8F1B`（cmp ebp,eax;jl），首指令是明确的条件分支比较，按 Lead 口径不计入疑似真入口。
- **21 个非分支标签 jmp32 中仍有可疑者**：例如 `0x552653`（mov ebp,[esp+0x28]）与 `0x552657`（mov al,[edx]）仅相距 4 字节，形态像 switch 跳转表内的函数内标签，但首指令是 mov（不属 test/cmp/jcc 类），按口径未标分支标签、计入疑似真入口。**53 个疑似真入口是上界**，需 P1 逐点用序言+调用链证真。
- **2 个地址同时被 jmp32+jmp8 命中**（如 `0x552657`）：在 `atlas_gaps.tsv` 里占 2 行（每通道一行），故 152 行 = 150 独立地址。通道计数按行/按通道内独立目标均一致（call32 32 / jmp32 23 / jmp8 97）。
- 全部 152 行 boundary_check=True（从最近 atlas 入口线性反汇编能对齐到目标），无 unknown 案例。

## 3. S14 计数偏低（11，high=0）与多类 vtable 的 most_common 规则
- 本片 37 个函数含 `RadioClass` 虚表，但多数同时含 `MissionClass`/`TechnoClass`/`BuildingClass` 等类；分类按 C04 同规格「多类取 Counter.most_common 首个（并列取先出现）」→ 28 归 S10、7 归 S12、2 归 S05，无一归 S14。
- 这些函数**仍是 high**（Mapped core 类），只是子系统归属分散；high 总数不受影响。RadioClass 单独的 S14 归属 `[未证]`，建议 P1 按 vtable 主表（col_off=0 主槽）重新定主类。

## 4. 模板容器类的子系统归属（潜在误归）
- 类型如 `T_DynamicVectorClass_PAVCellClass__`、`T_VectorClass_PAVPendingCellClass_LightSourceClass__`、`T_VectorClass_PAUTileInsertType_IsometricTileTypeClass__` 等，按"C04 同规格"的字符串包含匹配被归到元素类型对应的 S06/S07（core=True，计入 high）。
- 它们本质是**通用容器**（应归 S22），元素类型只是模板参数。这是 C01–C04 共用规则的固有偏差，本卡为口径一致未单独改判；建议 P1 统一修正 `class_to_sub` 对 `T_VectorClass_*`/`T_DynamicVectorClass_*` 前缀优先归 S22。

## 5. 具名函数语义仍为猜测
- 106 个 `[已证]` 仅证明"名字来自 YRpp/kb 地址名"，不证明其一行语义（如 `FileSystem::LoadFile`、`MapClass::Update_Pathfinding_1` 的具体行为）。语义列均按名推测，标 `[未证]`。
