# CHAIN_EQUIVALENCE · W51 独立复核：W31 与 W33 判定链等价性与「互证范围」审计

> **复核卡**：W51（纯离线只读复核）｜ **日期**：2026-11-13 ｜ **run_id**：`NEXT_RE_20261112_R02`
> **核查对象**：
> - W31：[WHY_MAP_FAILS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md)（及其 [DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/DISAGREE.md)、[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/UNKNOWNS.md)、[CORRECTION_s09.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/EVIDENCE/CORRECTION_s09.md)）
> - W33：[NEXTSCENARIO_FLOW.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md)（及其 [DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/DISAGREE.md)、[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/UNKNOWNS.md)）
> - 参照：[LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md)、[MAPSELMD_SPEC.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md)（含 [W34/DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/DISAGREE.md)）、[agy_w43_handoff.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/agy_w43_handoff.md)、[LEAD_W33_VERIFY.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md)、[LEAD_VERIFY_W34.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W34.md)
> **抽查目标镜像**：`D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe`（`4,825,360` B，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，`ImageBase = 0x00400000`；`.text`/`.rdata`/`.data` 均为 `RVA = FOFF = VA - 0x400000`）`[本次实测]`

---

## 0 · 执行摘要

1. **中间判定链并不等价**：W31 与 W33 仅在 `SkipMapSelect=no` 主干路径的核心地址上一致，在**入口衔接**（`GUI:Continue` → `0x00685A10`）、**下游开图流转**（`0x00685A74` → `0x00685C54`）、**`MapSelect` 前置/后置失败出口枚举**、**`SkipMapSelect=yes` 循环与失败退出机制**、`0x005CF6B0` 语义、vtable 槽位命名及部分报错文本/容器 ID 上均存在具体差异或缺失。`[本次读码]`
2. **Lead 合图确实强行合并了两条不同的失败出口**：[LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L20-L31) 把 `SkipMapSelect=no`（`0x005AE320` → `0x005ADDB5`/`0x005ADDCF`，`MapSel.CPP:0x86`）与 `SkipMapSelect=yes`（`0x005ADF20` 内部：索引越界 `0x005ADFF3` 或候选不匹配静默清空返回 `AL=0` 出口 `0x005AE0CD..0x005AE0F1` → `0x005ADEE0`/`0x005ADEFA`，`MapSel.CPP:0x98`）合并为同一条 `→ 0x005AE320 → 0x005ADD95..0x005ADDCF` 尾端，**属于明确的合图错误**。`[本次读码]`
3. **两卡的已纠正中间错误在合图中清理不彻底**：两卡均独立将 `0x007B5B30` 错判为「转大写」（实为 `0x007CAFF4` `tolower` 转小写），合图 §5 只点名 W33 却**漏掉 W31 的同一错误**；合图 §1 主图（L26）仍残留 W33 已被 W34 推翻的 `遍历候选子项(0x005CF6B0)` 表述；合图 §2 #6 SHA-256 缩写多打一个 `9`（`…6919d52`）。`0xFBE0D09D` 与 W31 `s09` 在合图现行文本中已清理/标注。`[本次读码]`
4. **「互证」成立与不成立的界线**：两卡在「**问题不在 `NextScenario` 写法与 MIX 寻址，而在于 `MAPSELMD.INI` 未登记我方地图，且 `SkipMapSelect=no` 时由 `0x005CF760` 用 `[Scen+0x125C]` 反查阶段失败**」这一顶层归因上互证成立；但在「**中间判定链完整等价**」「**底层辅助函数无共同盲区**」「**静态已证明真机触发哪条具体失败分支**」三个维度上不成立。`[静态推断]`

---

## 1 · 逐问作答

### 问题 1：两卡对同一条判定链给出的地址与分支是否一致？

**答：主干重合，但不完全一致——存在 8 处地址覆盖、分支语义或辅助结论上的不一致/遗漏。** `[本次读码]`

#### 1.1 一致的主干部分（两卡逐字节吻合）

在 `SkipMapSelect=no` 的核心静态链路与基础读取点上，两卡给出的关键地址一致，且经本次离线抽查确认与 `ra2bench\gamemd.exe` 字节完全匹配 `[本次实测]` `[本次读码]`：
- **读取点**：`0x00689FCA` (`push 0x83e19c ; "NextScenario"`) 写入 `[Scen+0x04]`；`0x0068A200` (`push 0x83e0e0 ; "SkipMapSelect"`) → `0x0068A211` 写入 `[Scen+0x34B0]`。
- **顶层分派**：`0x00685A38` (`mov al, byte ptr [ecx+0x34b0]`) → `0x00685A40` (`je 0x685a63`) → `0x00685A74` (`call 0x5add10` [Wrapper1])；`SkipMapSelect!=0` 时走 `0x00685A4C`/`0x00685A59` → `0x00685A52`/`0x00685A5C` (`call 0x5ade20` [Wrapper2])。
- **`SkipMapSelect=no` 查表与失败**：`0x005ADD63` (`call 0x5ae100`) → `0x005AE220` (`MapSelect::Init`) → `0x005AE2BE` (`call 0x5ceef0` 载入 `MAPSELMD.INI`，`0x005CEF62 push 0x830370`) → `0x005AE2F5` (`add ebp, 0x125c`) → `0x005AE30C` (`call 0x5cf760`) → `0x005AE31C` (`test edi, edi`) → `0x005AE320` (`push 0x82c134 ; "MapSelect: Invalid stage!\n"`) → Wrapper1 `0x005ADDB5` (`mov ecx, 0x82c108 ; "MSG:UnableMapSelect"`) → `0x005ADDCF` (`call 0x5d3490`)。
- **直接开图对比**：`Start_Scenario (0x00683AB0)` 经 `CCFileClass`（vtable `0x007E16B0`，`+0x1C = 0x00473D10` 先查磁盘 `0x00473D2D call 0x431f10`）打开地图，不经 `MapSelect`。

#### 1.2 不一致与遗漏清单（共 8 项）

| # | 判定链阶段 | W31（[WHY_MAP_FAILS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md) 等） | W33（[NEXTSCENARIO_FLOW.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md) 等） | 实测字节核对与差异定性 |
|---|---|---|---|---|
| **I1** | `GUI:Continue` → `0x00685A10` 入口衔接 | 只定位控件创建 `0x0046E8BD`（ID `0x6D1`）与状态机 `0x00685A10` 的 3 个调用点；在 [W31/UNKNOWNS.md:25](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/UNKNOWNS.md#L25) 明确声明**中间按钮消息处理到 `0x00685A10` 未追踪** `[待运行验证]` | [L26](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L26) 给出 `CampScor 处理 GUI:Continue 后由 0x0055D14A 调用 0x00685670` 进入 `0x00685A38` | `[本次读码]` 核实 `0x0055D14A` 确为 `call 0x685670`，`0x00685670` 在 `0x006859C7` (`je 0x685a10`) 进状态机；但 W33 **未给出 `0x0046E8BD` (`0x6D1`) 到 `0x0055D14A` 的中间跳链**。两卡在入口衔接上深度不同。 |
| **I2** | 弹窗之后 / `0x00685A74` 下游至开图 | 未追踪 `0x00685A74` 之后如何流向 `Start_Scenario`，弹窗后行为归入 [W31/UNKNOWNS.md:26](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/UNKNOWNS.md#L26) `[待运行验证]` | [L39, 92-94](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L39)、[W33/UNKNOWNS.md:3-5](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/UNKNOWNS.md#L3-L5) 给出下游 `0x00685C4E lea ecx,[eax+0x125c]` → `0x00685C54 call 0x683ab0`，并指出 `0x00685A74` **不检 `EAX` 返回值** | `[本次读码]` 核实 `0x00685C4E..0x00685C54` 确在下游调用 `0x00683AB0`。W31 无此下游片段，W33 有之。 |
| **I3** | `0x005AE100` / `0x005AE220` (`SkipMapSelect=no`) 失败分支 | [L119-126](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L119-L126) 列出 **5 道判定 / 4 条带 debug 串失败分支**（`Invalid Scenario pointer!` `0x005AE245`、`Invalid side!` `0x005AE280`、`Unable to initialize choices!` `0x005AE2DC`、`Invalid stage!` `0x005AE320`、`Unable to create font!` `0x005AE34C`），且在表 §5 未单独列出 `0x005AE10A` | [L48-49, 102-108](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L48-L49) 列出 `0x005AE10A call 0x5ae220`，但只写了 `0x005AE2BE` → `0x005AE30C` → `0x005AE320` (`Invalid stage!`) 一条线，**省略了其余 4 个前置/后置失败点** | `[本次读码]` 确认 `0x005AE220` 确有全部 5 处失败返回；W31 保留了多分支不确定性（不能静态断言真机必走 `Invalid stage!`），W33 则直接按单线叙述。 |
| **I4** | `0x005ADF20` (`SkipMapSelect=yes`) 中间步骤与失败退出 | [L134-141](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L134-L141) 列出前置检查 `0x005ADF2D`、`0x005ADF37` (`0x7B4710`)、`0x005ADF62`、`0x005ADFA0`/`0x005ADFBE`、`0x005ADFD7`/`0x005ADFE1`/`0x005ADFF3`，但**漏掉 `0x005AE013 call 0x686700` 先清空 `[Scen+0x125C]`**，也未写 `0x005CF6B0` | [L34-36, 109-115](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L34-L36) 写出了 `0x005AE013` 先清空 `[Scen+0x125C]` 与 `0x005AE032 call 0x5cf6b0`，但**省略了 `0x005ADF2D..0x005ADFF3` 的前置失败地址**，且**错把 `0x005CF6B0` 当作候选子项枚举器** | `[本次读码]` **两卡共同遗漏**：在 `0x005ADF20` 中若 `0x005CF810` 通过但**候选均未命中 `NextScenario`**，控制流跳往 `0x005AE0CD..0x005AE0F1`，靠先前已清空的 `[Scen+0x125C]` 返回 `AL=0`，**不经过 `0x005ADFF3`，不打印 `Invalid stage!`**！ |
| **I5** | 弹窗处源码行号与 Wrapper2 详细地址 | [L105-111](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L105-L111) 给出了 Wrapper2 的 `0x005ADEE0` / `0x005ADEFA`，但未标 `MapSel.CPP` 行号 `0x86` vs `0x98` | [L36, 49, 101, 115](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L36) 明确标出 Wrapper1 对应 `MapSel.CPP:0x86`、Wrapper2 对应 `MapSel.CPP:0x98` | `[本次读码]` 核实 `0x005ADD95`/`0x005ADDBB` 为 `push 0x86`，`0x005ADEC0`/`0x005ADEE6` 为 `push 0x98`。 |
| **I6** | 阶段表字符串比较与查找函数 (`0x7B5B30` / `0x5CF6B0`) | [L129, 141](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L129) 误称 `0x7B5B30`「统一大写」/「大写比对」；未分析 `0x005CF6B0` | [L35](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L35) 同样误称「统一转大写」；[L35, 113](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L35) 误称 `0x005CF6B0` 是循环候选子项 | `[本次读码]` `0x007B5B30` 调 `0x007CAFF4` (`add eax, 0x20`) 实为 **`tolower` 转小写**；`0x005CF6B0` 是按 `[stage+0]` 阶段名查全表，候选数组在 `[stage+0x58]`/`+0x64`（W34 已更正）。 |
| **I7** | `CCFileClass` vtable `0x007E16B0` 槽位命名 | [W31/DISAGREE.md:56-63](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/DISAGREE.md#L56-L63) 指出 `+0x1C=0x473D10` 在 W29 口径下称 `Get_File`、`+0x14=0x473C50` 称 `Open`，刻意不采信 W33 命名 | [L41](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L41) 称 `+0x1C=0x00473D10` 为 `CCFileClass::Open`、`+0x14=0x00473C50` 为 `Is_Available` | `[本次读码]` 槽位地址与行为字节一致（`+0x14` 先查 MIX 后查磁盘，`+0x1C` 先查磁盘后查 MIX），属**命名口径冲突**。 |
| **I8** | 弹窗 CSF 字符串与 `MAPSELMD.INI` ID 表述 | 全篇坚守实测真值 `「無法啟始選取地圖！\n」`；`s09` 误判缺失后自纠（[CORRECTION_s09.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/EVIDENCE/CORRECTION_s09.md)） | [L18, 49](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L18) 写 `「無法啟始選取地圖！\n」`，但 [L43, 45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L43) 退回误传串 `「無法啟動選取地圖!」`；[W33/DISAGREE.md:14](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/DISAGREE.md#L14) 混写 `id=0x922B8CE7 / 0xFBE0D09D` | `[本次实测]` 确认 `ts_crc_hash("LOCALMD.MIX") = 0xFBE0D09D`（容器 ID），`crc32("MAPSELMD.INI") = 0x922B8CE7`（嵌套文件 ID）。 |

---

### 问题 2：Lead 的合图是否把两条不同的失败出口（`SkipMapSelect=no` 与 `=yes`）合并成了一条？若是，正确应怎么分开写？

**答：是的，Lead 合图错误地合并了两条不同的失败出口（并附带另外两处细节偏差）。** `[本次读码]`

#### 2.1 Lead 合图错在哪里

在 [LEAD_VERDICT_map_start_root_cause.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L20-L31) 中，Lead 将 `SkipMapSelect=no` 与 `SkipMapSelect=yes` 两条分叉在末端强行并回同一条报错链：
```text
  两条路径都要求 MAPSELMD.INI 认识我方地图
  → 未命中 → 0x005AE320 打印 "MapSelect: Invalid stage!" → MapSelect::Init 返回 AL=0
  → 0x005ADD95..0x005ADDCF 弹 CSF 标签 MSG:UnableMapSelect
```
这至少混淆了 **4 个不可合并的事实** `[本次读码]`：
1. **`0x005AE320` 不在 `SkipMapSelect=yes` 路径上**：`0x005AE320` 位于 `MapSelect::Init (0x005AE220)` 内，只有 `SkipMapSelect=no` (`0x005ADD10 → 0x005AE100 → 0x005AE220`) 才会执行。
2. **`SkipMapSelect=yes` 的 `0x005ADF20` 有两个完全不同的"未命中"出口**：
   - 若 `[Scen+0x35A0]` 越界（`0x005ADFE1 call 0x5cf810` 返回 `0`），日志在 **`0x005ADFF3`**（`push 0x82c134 ; "MapSelect: Invalid stage!\n"`）打印后返回 `AL=0`；
   - 若当前 stage 有效，但遍历 `[ebx+0x58]`/`[ebx+0x64]` 候选子项的 `Scenario=` 与 `NextScenario` 均不匹配（**正是合图 L27 所说的比较未命中！**），控制流从 `0x005AE01F` / `0x005AE096` 跳到 **`0x005AE0CD..0x005AE0F1`**，检测 `0x005AE013` 预先清空后的 `[Scen+0x125C]` 长度为 0，**静默返回 `AL=0`，既不进 `0x005AE320`，也不进 `0x005ADFF3`**！
3. **弹窗调用点与 `MapSel.CPP` 行号完全不同**：
   - `SkipMapSelect=no`：由 Wrapper1（`0x005ADD10`）在 **`0x005ADD95` / `0x005ADDBB` (`push 0x86`)**、**`0x005ADDB5` (`mov ecx, 0x82c108`)**、**`0x005ADDCF` (`call 0x5d3490`)** 弹窗；
   - `SkipMapSelect=yes`：由 Wrapper2（`0x005ADE20`）在 **`0x005ADEC0` / `0x005ADEE6` (`push 0x98`)**、**`0x005ADEE0` (`mov ecx, 0x82c108`)**、**`0x005ADEFA` (`call 0x5d3490`)** 弹窗。
4. **分派层省略了 Wrapper2**：`0x00685A52`/`0x00685A5C` 先调用 Wrapper2 **`0x005ADE20`**，再由 `0x005ADE85` 调用 `0x005ADF20`（合图跳过了 `0x005ADE20`）；且 `遍历候选子项(0x005CF6B0)` 仍沿用了 W33 的错误描述。

#### 2.2 正确的分叉写法（经本次二进制抽查核实）

```text
结算继续点 (0x0055D14A call 0x685670 → 0x006859C7 je 0x685a10 [注：GUI:Continue 控件 0x6D1@0x46E8BD 至 0x55D14A 的UI消息桥未静态展开])
  → 0x00685A38 读 [Scen+0x34B0] (SkipMapSelect)
      │
      ├─ [SkipMapSelect == 0 (no)] 0x00685A40 je 0x685a63 → 0x00685A74 call 0x5add10 (Wrapper1)
      │     → 0x005ADD63 call 0x5ae100 → 0x005AE10A call 0x5ae220 (MapSelect::Init)
      │         ├─ 前置检查失败：0x005AE245 (Invalid Scenario pointer!) / 0x005AE280 (Invalid side!)
      │         ├─ 0x005AE2BE call 0x5ceef0 载入 MAPSELMD.INI 失败 → 0x005AE2DC (Unable to initialize choices!)
      │         ├─ 0x005AE30C call 0x5cf760 用当前图名 [Scen+0x125C] 按阶段 Scenario=([stage+4]) 反查未命中
      │         │     → 0x005AE320 push 0x82c134 ("MapSelect: Invalid stage!\n") → 0x005AE363 xor al,al
      │         └─ 0x005AE34C (Unable to create font!) → 0x005AE363 xor al,al
      │     → Wrapper1 检得 AL==0 (0x005ADD71 sete bl)
      │     → 0x005ADD95/0x005ADDBB push 0x86 (MapSel.CPP:0x86)
      │     → 0x005ADDB5 mov ecx, 0x82c108 ("MSG:UnableMapSelect") → 0x005ADDCF call 0x5d3490 弹窗
      │
      └─ [SkipMapSelect != 0 (yes)] 0x00685A4C/0x00685A59 选 AltNextScenario([Scen+0x108]) 或 NextScenario([Scen+0x04])
            → 0x00685A52 / 0x00685A5C call 0x5ade20 (Wrapper2) → 0x005ADE85 call 0x5adf20
                ├─ 前置检查失败：0x005ADF2F / 0x005ADF3E (空串 0x7B4710) / 0x005ADF62 (Invalid side!)
                ├─ 0x005ADFA0 call 0x5ceef0 载入 MAPSELMD.INI 失败 → 0x005ADFBE (Unable to initialize choices!)
                ├─ 0x005ADFE1 call 0x5cf810 查当前 stage 索引 [Scen+0x35A0] 越界
                │     → 0x005ADFF3 push 0x82c134 ("MapSelect: Invalid stage!\n") → 0x005AE000 xor al,al
                └─ 0x005AE013 call 0x686700 先清空 [Scen+0x125C]
                      → 遍历 [ebx+0x58]/[ebx+0x64] 候选子项名 → 0x005AE032 call 0x5cf6b0 按阶段名([stage+0])查阶段
                      → 0x005AE04A/0x005AE061 call 0x7b5b30 (tolower 转小写) → 0x005AE073 call 0x7b4780 比对 [esi+4] 与 NextScenario
                      → 全部候选均未命中 → 0x005AE0CD..0x005AE0F1 检得 strlen([Scen+0x125C])==0 → 静默返回 AL=0（不打印 Invalid stage!）
            → Wrapper2 检得 AL==0 (0x005ADE93 sete bl)
            → 0x005ADEC0/0x005ADEE6 push 0x98 (MapSel.CPP:0x98)
            → 0x005ADEE0 mov ecx, 0x82c108 ("MSG:UnableMapSelect") → 0x005ADEFA call 0x5d3490 弹窗
```

---

### 问题 3：两卡各自有哪些已被后续纠正的中间结论？这些在合图里是否被清理？

**答：两卡各自均有被 W34/自纠推翻的中间结论；Lead 合图对明显自纠项做了部分清理，但仍保留了 4 处未清理或清理不完全的残留。** `[本次读码]`

| 序号 | 原始卡片与被纠正的中间结论 | 后续纠正依据 | 在合图（`LEAD_VERDICT_map_start_root_cause.md`）及连带 `REVIEW/` 中的清理现状 |
|---|---|---|---|
| **C1** | **W31 与 W33 共同错误**：把 `0x007B5B30` 归一化方向写反为「**转大写**」（[W31 L129, 141](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L129)；[W33 L35](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L35)） | W34 [MAPSELMD_SPEC.md:108-109](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md#L108-L109) & [W34/DISAGREE.md:29-41](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/DISAGREE.md#L29-L41)：`0x007B5B30` 调 `0x007CAFF4` 对 `'A'..'Z'` 执行 `add eax, 0x20`（**`tolower` 转小写**），再用大小写敏感的 `0x007B4780` 比较 | **清理不完全**：① 合图 [§5 L78-80](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L78-L80) 只把 W33 列为错误方并采信 W34「小写」，**完全漏掉 W31 也犯了完全相同的错**；② 合图 [L84](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L84) 仍残留过时的 `在 W34 交付前标 [转引·待核]` 注记。（注：[LEAD_W33_VERIFY.md:93](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L93) 现行版本已补改为「转小写后比较」。） |
| **C2** | **W33 卡面/日志误读**：将 `0xFBE0D09D` 当成 `MAPSELMD.INI` 的「存储 id / 被异或处理的 id」（[W33/DISAGREE.md:14](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/DISAGREE.md#L14)、[LEAD_W33_VERIFY.md:116](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_W33_VERIFY.md#L116)）；随后 Lead 曾用零填充错算误“证伪”W34 | W34 [MAPSELMD_SPEC.md:39-42](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/MAPSELMD_SPEC.md#L39-L42) & [W34/DISAGREE.md:7-25](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/DISAGREE.md#L7-L25)：`0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")`（嵌套容器 ID）；`MAPSELMD.INI` 在第二级加密头 MIX 内，ID 为普通 `crc32 = 0x922B8CE7` | **主体已清理，局部有残瑕**：合图 [§4 L72](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L72) 已撤回假证伪并改口 `[已定谳·本次实测] 0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")`；但 §8 [L108](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L108) 未回填 `LOCALMD.MIX` 名称，且 §2 [L46](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L46) 的 `MAPSELMD.INI` SHA-256 缩写仍带笔误 `…6919d52`（实为 `…691d52`）。 |
| **C3** | **W31 `s09` 早期误判**：扫描顶层 33 个 MIX 未命中 `0x922B8CE7`，曾误判 `MAPSELMD.INI` 缺失 | W31 `s10`/`s11` 自我推翻并出具 [CORRECTION_s09.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/EVIDENCE/CORRECTION_s09.md)，在 [WHY_MAP_FAILS.md:154-155](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/WHY_MAP_FAILS.md#L154-L155) 标废 | **已清理**：合图 [§8 L117-118](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L117-L118) 明确记录了该自我推翻及「顶层扫不到 ≠ 容器内没有」。 |
| **C4** | **W33 误读 `0x005CF6B0`**：称 `0x005AE032 call 0x5cf6b0` 为「遍历候选子项」（[W33 L35, 113](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L35)） | W34 [W34/DISAGREE.md:45-56](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/DISAGREE.md#L45-L56)：`0x005CF6B0` 是按 `[stage+0]` 阶段名查找全表，候选数组在 `[stage+0x58]`/`+0x64` | **未清理（文内打架）**：合图 [§5 L81](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L81) 虽已采信 W34 纠偏，但**同文件 §1 主图 [L26](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L26) 依然保留 `遍历候选子项(0x005CF6B0)`**。 |
| **C5** | **W33 结构简写与旧错误串**：① [L64-66](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L64) 仅列 `[GDI]`/`[Nod]` + `ALL01..07`/`Sov01..07` 简写；② [L43, 45](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W33_nextscenario_dataflow/NEXTSCENARIO_FLOW.md#L43) 残留 `「無法啟動選取地圖!」` | ① W34 [W34/DISAGREE.md:60-71](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W34_mapselmd/DISAGREE.md#L60-L71) 实测 20 段完整结构（含 `[ALL00]`、`[Anims]`、`[GDISFX]`、`[NODSFX]` 与 7 类 UI 字段）；② W31/Lead 锁定 `「無法啟始選取地圖！\n」` | **部分未清理**：合图 [§2 #7 L47](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L47) 已锁定「啟始」真值；但 [§2 #3 L43](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/REVIEW/LEAD_VERDICT_map_start_root_cause.md#L43) 仍沿用 W33 简写结构，未补出加载器实际读取的 `[Anims]`/`[GDISFX]`/`[NODSFX]` 段。 |

---

### 问题 4：结论——「两卡互证」这个说法在什么范围内成立、在什么范围内不成立？

**答：两卡对「顶层故障归因与排错方向」构成有效的双路互证；但对「完整判定链等价」「底层细节独立无误」「运行时根因已最终定谳」均不成立。** `[静态推断]`

#### 4.1 成立的范围（可称为互证的部分）
1. **研究起点正交下的顶层归因收敛**：
   - W31 从 `MSG:UnableMapSelect`（`0x0082C108`）的唯二指令 xref（`0x005ADDB5`、`0x005ADEE0`）**反向回溯**；
   - W33 从 `NextScenario`（`0x0083E19C`）的数据读写与 `Start_Scenario`（`0x00683AB0`）**正向追踪**。
   - 两路独立收敛到同一静态核心结论：`ECH01.MAP` 与官方 14 图同样设为 `SkipMapSelect=no`，`0x00685A38`/`0x00685A40` 将其分派至 `0x005ADD10 → 0x005AE100 → 0x005AE220` (`MapSelect::Init`)，使用**当前地图名 `[Scen+0x125C]`** 通过 `0x005CF760` 在 `MAPSELMD.INI`（`0x005CEEF0` 载入）中反查 stage 失败；而直接开图 `Start_Scenario (0x00683AB0)` 走 `CCFileClass`（`0x007E16B0`，`+0x1C=0x00473D10` 磁盘优先），不进 `MapSelect`。
2. **关键主干指令与字节互证**：两卡在 `0x00685A38..0x00685A74`、`0x005ADD63`、`0x005ADDB5`/`0x005ADDCF`、`0x005AE2BE`/`0x005AE2F5`/`0x005AE30C`/`0x005AE31C`/`0x005AE320`、`0x005CEF62`、`0x00473D2D`、`0x00689FCA`、`0x00683AF8` 等主干点的 VA 与指令语义一致。
3. **排错假说证伪互证**：两卡独立证伪了 `H-A`（`NextScenario` 并非死字段，也不走 `BATTLEMD.INI [Battles]` 推进）与 `H-B`（`Continue` 不存在直调 `MixFileClass::Find` 绕过磁盘的分支，打进 MIX 无效）。

#### 4.2 不成立的范围（不能用「两卡互证」背书的部分）
1. **不能宣称「两卡给出等价的中间判定链」**：
   - 两卡在 `GUI:Continue → 0x00685A10` 入口衔接、`0x00685A74 → Start_Scenario` 下游、`MapSelect::Init` 的 4 条 debug 失败出口枚举、以及 `0x005ADF20` 前置失败点上覆盖面不对称；
   - Lead 合图把 `SkipMapSelect=no`（`0x005AE320` → `0x005ADDB5`/`0x005ADDCF`，`MapSel.CPP:0x86`）与 `SkipMapSelect=yes`（`0x005ADFF3` 或静默出口 `0x005AE0CD..0x005AE0F1` → `0x005ADEE0`/`0x005ADEFA`，`MapSel.CPP:0x98`）拼成同一出口，**并非两卡原始链路的真实交集**。
2. **不能把「两卡一致」等同于「底层实现细节无误」**：
   - 两卡在**同一处公共底层辅助函数 `0x007B5B30`** 上各自独立犯了完全相同的方向错误（把 `tolower` 说成「转大写」），直到 W34 深入读 `0x007CAFF4` 才翻案。这说明“两卡互相印证”并不覆盖未实际拆穿的底层细节。
3. **不能把两卡静态互证上升为「真机失败瞬间的运行时分支已定谳」**：
   - 两卡均为**纯静态分析**，均未观测 `W27` 帧 `frame=210` 时 `[Scen+0x125C]` 的内存态与控制台/日志输出；静态链只能收窄到 `MapSelect::Init` 阶段登记表分支（`Invalid stage!` 最可能），仍需运行时断点/日志证据才能严格区分 `MapSelect::Init` 4 条失败分支（正如 W31 [UNKNOWNS.md:14-19](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W31_map_start_failure/UNKNOWNS.md#L14-L19) 与 Lead 合图 §3 原本设定的边界；后续 W39 真机实测仅从结果端证实“补全 `MAPSELMD.INI` 后可推进到 `A2`”，并未直接抓到负对照报错帧的内部调试串）。

---

## 2 · 关键地址静态字节抽查核对表（`ra2bench\gamemd.exe`）

> `[本次实测]` `[本次读码]` 全部地址均由本次离线脚本对 `ra2bench\gamemd.exe`（`4,825,360` B，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`）使用 Capstone 实测读出；`.text` / `.data` 均满足 `RVA = FOFF = VA - 0x400000`。

| 归属环节 | VA | RVA | FOFF | 原始字节 | 反汇编 | 复核结论 |
|---|---|---|---|---|---|---|
| `CampScor` → 状态机 | `0x0055D14A` | `0x15D14A` | `0x15D14A` | `e8 21 85 12 00` | `call 0x685670` | W33 入口调用确认；经 `0x006859C7` (`74 47 je 0x685a10`) 进状态机 |
| `SkipMapSelect` 分派 | `0x00685A38` | `0x285A38` | `0x285A38` | `8a 81 b0 34 00 00` | `mov al, byte ptr [ecx + 0x34b0]` | 两卡一致 |
| `SkipMapSelect==0` 分支 | `0x00685A40` | `0x285A40` | `0x285A40` | `74 21` | `je 0x685a63` | 两卡一致（→ `0x00685A74 call 0x5add10`） |
| `SkipMapSelect!=0` 传 `NextScenario` | `0x00685A59` | `0x285A59` | `0x285A59` | `8d 51 04` | `lea edx, [ecx + 4]` | 紧随 `0x00685A5C e8 bf 83 f2 ff call 0x5ade20` |
| Wrapper1 调 Validator1 | `0x005ADD63` | `0x1ADD63` | `0x1ADD63` | `e8 98 03 00 00` | `call 0x5ae100` | `0x005AE10A e8 11 01 00 00 call 0x5ae220` |
| Wrapper1 弹窗行号 (`no`) | `0x005ADD95` | `0x1ADD95` | `0x1ADD95` | `68 86 00 00 00` | `push 0x86` | `MapSel.CPP:0x86`；`0x005ADDB5` `mov ecx, 0x82c108`；`0x005ADDCF` `call 0x5d3490` |
| Wrapper2 调 Validator2 | `0x005ADE85` | `0x1ADE85` | `0x1ADE85` | `e8 96 00 00 00` | `call 0x5adf20` | 合图未显式画出 Wrapper2 `0x005ADE20` |
| Wrapper2 弹窗行号 (`yes`) | `0x005ADEC0` | `0x1ADEC0` | `0x1ADEC0` | `68 98 00 00 00` | `push 0x98` | `MapSel.CPP:0x98`；`0x005ADEE0` `mov ecx, 0x82c108`；`0x005ADEFA` `call 0x5d3490` |
| `MapSelect::Init` 查阶段 | `0x005AE30C` | `0x1AE30C` | `0x1AE30C` | `e8 4f 14 02 00` | `call 0x5cf760` | 仅 `SkipMapSelect=no`；以 `[Scen+0x125C]` 按 `[stage+4]` 查 |
| `SkipMapSelect=no` 报错日志 | `0x005AE320` | `0x1AE320` | `0x1AE320` | `68 34 c1 82 00` | `push 0x82c134` | `"MapSelect: Invalid stage!\n"`（仅 `no` 路径） |
| `SkipMapSelect=yes` 越界报错 | `0x005ADFF3` | `0x1ADFF3` | `0x1ADFF3` | `68 34 c1 82 00` | `push 0x82c134` | 仅 `[Scen+0x35A0]` 越界 (`0x005CF810` 返回 0) 时打印 |
| `SkipMapSelect=yes` 清空缓冲 | `0x005AE013` | `0x1AE013` | `0x1AE013` | `e8 e8 86 0d 00` | `call 0x686700` | 先清空 `[Scen+0x125C]`（W31 漏列） |
| `SkipMapSelect=yes` 查阶段名 | `0x005AE032` | `0x1AE032` | `0x1AE032` | `e8 79 16 02 00` | `call 0x5cf6b0` | 按 `[stage+0]` 阶段名查全表（非候选枚举器） |
| `SkipMapSelect=yes` 无匹配出口 | `0x005AE0CD` | `0x1AE0CD` | `0x1AE0CD` | `8b cf e8 1c 15 02 00` | `mov ecx,edi; call 0x5cf5f0` | 后接 `0x005AE0DD..0x005AE0F1` 查空串返回 `AL=0`，**不打印 `Invalid stage!`** |
| 字符串归一化 | `0x007B5B30` | `0x3B5B30` | `0x3B5B30` | `80 fa 41 7c 16 80 fa 5a 7f 11 ... e8 91 54 01 00` | `cmp dl,0x41..0x5a; call 0x7caff4` | `0x007CAFF4` 在 `0x007CB00D` 执行 `83 c0 20` (`add eax, 0x20`) = **转小写** |
| 敏感逐字节比较 | `0x007B4780` | `0x3B4780` | `0x3B4780` | `8b 01 8b 4c 24 04` | `mov eax,[ecx]; mov ecx,[esp+4]` | 函数体内无 `call`，纯区分大小写比较 |
| `Start_Scenario` 调点 | `0x00685C54` | `0x285C54` | `0x285C54` | `e8 57 de ff ff` | `call 0x683ab0` | W33 给出、W31 未展开 |
| `CCFileClass` 磁盘优先 | `0x00473D2D` | `0x073D2D` | `0x073D2D` | `e8 de e1 fb ff` | `call 0x431f10` | 虚表 `0x007E16B0+0x1C` (`0x00473D10`) |

CRC 算法抽查 `[本次实测]`：`zlib.crc32(b"MAPSELMD.INI") == 0x922B8CE7`、`ts_crc_hash("LOCALMD.MIX") == 0xFBE0D09D`、`ts_crc_hash("RA2MD.CSF") == 0xBD835079`（按 `mixlib.ts_crc_hash` 尾部填充规则复算一致）。
