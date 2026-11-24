# C10 · DISAGREE（口径差异 / 无事实冲突）

## 1. 疑似真入口口径：卡判据 (e) 严格=12，宽松 r14_strict=14（有意从严，非数据矛盾）
- C05/C06「call32 + 非分支 jmp32」口径在本片得 **104**（call32 36 ∪ 非分支 jmp32 69，减 1 重叠）；C08/C09 的 `r14_strict`（align16 + prev∈{nop,ret,jmp} + 首指令非分支）得 **14**。本卡按派卡纪律 (e) 追加「非 jcc 目的 + push ebp/sub esp 序言 + prev 含 int3」四项，得 **12**。
- 被剔除的 2 个：`0x7AEEC0`（call32，align16、prev=nop，但首 `push ecx`、22B 小函数，无 push ebp/sub esp 序言）、`0x7DD2E0`（call32，align16、prev=ret，但首 `mov eax,[0x87dd70]` 无序言）。二者形态是极短 getter/桩，不是标准序言函数，按 (e) 不计真入口，**未为凑数放宽**。
- 两条独立实现（struct 通道 `entry_criteria.py`、pefile 通道 `verify_core.py` CORE4）严格集合同为 12 且地址一致；宽松 14 亦两通道一致。PROGRESS 报 12 并同时列出宽松 14 供审计对照。jmp32 真入口本片为 **0/71**，是全镜像普查以来 jmp32 过宽最显著的一片，印证坑 (e)。
- 这不是数据矛盾：atlas_gaps.tsv 三通道原始数（36/71/169）与行数/独立地址（276/264）是客观事实，不随「真入口」判据变化。

## 2. 虚表槽数不用 vtables_v2.json 的 slots（按坑 (a) 独立定界）
- `vtables_v2.json` 全镜像槽数和 13,351；本卡自写 RTTI 通道 `rtti_independent.py`（COL→TypeDescriptor→vftable，槽数=从 slot0 起连续 .text 代码指针数，遇零/非代码停）实测 **14,044**，差 +693；delta 分布 `{1:794, 0:327, -1:85, -2:8}`：794 张表 v2 各少 1 末槽，85+8=93 张表 v2 多计 101 幻槽（85×1+8×2），与坑 (a) 及 C03/C08 审计完全一致。
- 后果：本片 239 个函数有 RTTI 虚表命中（真实槽），未直接引用 v2.json 的 `slots` 作判定。v2.json「漏收表」部分本卡亦不依赖（自己的 COL→TD 扫描独立收表）。

## 3. 与 C05/C06 口径的差异：通用模板包装器优先归 S22（承 C08 修正）
- `T_DynamicVectorClass_PAUWinsockBufferType_WinsockInterfaceClass__`、`T_VectorClass_PAUtConnInfoStruct__`、`T_BlitTrans_E/G` 等泛型模板，C05/C06 会按「字符串包含元素类型名」判 core（Winsock→S18、Blit→S07）。本卡 `GENERIC_WRAPPERS` 先于 core 规则识别，一律归 S22 core=False，避免分级虚高（同 C08 DISAGREE §1）。
- 后果：本片 `BSurface`/`XSurface`/`DSurface` 实体类仍归 S07 core（43 high），但 `T_BlitTrans_E/G` 模板包装归 S22；Winsock 接口类实体（UDP/IPX/WinsockInterface）归 S18 core（149 high），其元素容器归 S22。审计按本卡 `classification_trace.tsv` 的 conf 列复算即可自洽。

## 4. 类命名用 RTTI 实测校验，不用文件名启发式（坑 (d)）
- 本卡 vtable 类名全部来自 `.rdata` COL→TypeDescriptor 实测（`rtti_independent.py`），非头文件文件名推断；self_known 名来自 YRpp `JMP_THIS`/kb 具名地址。`work/check_naming.py` 交叉校验：16 个同时有 self_known 与 RTTI 类的地址，类名**全部一致、0 冲突**；其余 37 个 self_known 为 CRT 自由函数（无虚表），不涉及类名挂错。
- 前向声明泄漏（`class X;`）与按文件名推断类名（C05 错 24/31 处）两机制本卡均未采用，无同类错误。

## 5. 与既有事实底座无冲突
- 本片地址 0x773500–0x7E038D 覆盖的类族（S18 WOL/Winsock/Modem、S02 CRT、S09 WWMouse、S07 DirectDraw 曲面、S03 文件管道）与 `R14_COMMON.md` §1–§7、台账 §911–§928 无口径冲突；上述台账具名地址均落在 C05/C06 片，本卡未触碰、未推翻任何 `[已证]`。
- 本卡未写任何新 `[已证]` 发现，未改 `R14_COMMON.md` / 台账 / `COVERAGE\coverage.tsv`。

## 6. 未与 Lead 裁决口径 disagreement 的项目
- capstone `skipdata=True`（全 .text 解出 1,394,120 条，与 C05–C09 一致）；`boundary_check` 超 max_bytes 的「未判定」保留 None 不当 False（R14 §6-3），已落实（本片 0 例 bail）。
- 双通道不独立源：通道 A=atlas entry+size（切片/owner），通道 B1=自写 struct PE 的 RTTI（14044 槽）+ B2=自写 struct PE + capstone 字节扫（E8/E9/EB）；第三/第四通道 `verify_core.py` 用 pefile + `op_str` + CORE4 严格判据独立复核，核心数字全 match。
- 未用 Ghidra（并发 ≤4 留给别卡）；未改 gamemd.exe / ddraw.dll / ra2youli\；未 git commit/push。
