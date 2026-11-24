# CHANNELS.md — P0-RESIDUAL-2 新通道定义与异源说明

> 目标：把"≈222 估计值"变成枚举清单。新通道须与已用五通道（a atlas 区间 / b call·jmp 直接目标 / c COL·vftable 槽值 / d 裸游程 / e 叶函数形态）**判据层面异源**。
> 全程只读 `gamemd.exe`（SHA-256 现场校验通过）；capstone 5.0.7 `skipdata=True`；`.text=[00401000,007E038D)`，全网格 253,753 个 16B 对齐点。

## 共同基础：合格池（qualified pool）
`pool` = 16B 对齐 ∧ 不在 atlas 区间（区间包含判定）∧ 前驱指令属 TERM={nop,ret,jmp,int3} ∧ 首指令非 JCC ∧ 可解码。
实测 **N_pool=7,228**（P0-RESIDUAL 审计 a13 记 7,229，差 1 为边界细节，见 UNKNOWNS）。
ENUM 全集 = `pool \ coverage(当前 14,495)` = **5,656** 地址（`EVIDENCE/stats.json`）。

---

## 通道 F — 全对齐网格（full aligned grid）
- **判据**：扫全 `.text` 每个 16B 对齐地址，套四项判据（align16 ∧ 首字节∉{E8,E9,EB} ∧ 前驱∈TERM ∧ 合法序言 `push ebp`/`push imm32`/`sub esp,imm` 或叶形态）。
- **规模**：全量输出 **253,753**；四项判据筛后 **9,497**（其中 in_atlas 8,114 / in_coverage 9,353 / 不在 coverage 144）。落合格池且不在 coverage 后剩 **~20**（严格判据）。
- **异源说明**：这是唯一**不依赖任何引用**（不看 call/jmp/槽值/指针）的通道类型——直接按"对齐网格 + 局部字节形态"枚举地址。旧通道 b/c 全靠引用，通道 D 靠前驱孤儿。故 F 能捞到 `0x7775C0` 这类"无人引用但真存在"的入口类型（但注意 F 的**形态过滤器**仍会漏掉 `push ecx`，见下）。
- **产物**：`EVIDENCE/channel_F_grid.tsv`（9,497 行全量）。
- **结论性发现**：F 的形态过滤器（c4a∨leaf）**召回不足**——已知 oracle `0x7775C0`（首字节 `0x51`=push ecx）在 coverage 中，却 `chF=False`（`EVIDENCE/oracle_and_crosscheck.tsv`）。F 单独对 1,572 正样本召回 **86.45%**。

## 通道 G — 数据段指针表（data-section pointer tables）
- **判据**：扫 `.data`/`.rdata`（及 `.detour`）全部 dword，凡值落入 `.text` 者视为函数指针候选；另扫连续 dword 数组（≥3 个连续值均落 `.text`）作为跳表/分派表。
- **规模**：数据段 dword→`.text` 目标 **18,954** 个 distinct（.rdata 7,233 / .data 11,787）；密集指针游程 **1,095** 个、覆盖 25,703 槽；落合格池且不在 coverage **3,935** 个。
- **异源说明**：旧通道 c 只取 **COL 校验的 vftable 槽**（`.rdata` 特定结构）；G 取**所有数据段 dword**（含 `.data`、非 vftable 结构、跳表），判据是"数据段是否存在指向该地址的指针"，与 c 的"是否 vftable 槽"判据层面不同。重叠部分（vftable 槽）已在旧通道计数，ENUM 中标注 channel 来源。
- **产物**：`EVIDENCE/channel_G_ptrs.tsv`（18,954 行全量，含来源位置）。
- **结论性发现**：G 对 gate476 召回 99.8%（gate 多为 vtable 槽，与旧 c 同源），但对 resid1096 仅 11.5%——G 与 F **互补**（F|G 对 1,572 正样本召回 99.62%），但 G 的 3,935 个新候选中 **0 个**有 call 引用、且密集游程命中 0，绝大多数是数据指针/跳表目标而非函数入口，不作 FUNC 判定。

## 通道 H — 结构化元数据（structured metadata）
- **判据**：查 PE 异常目录 `.pdata`/SEH、增量链接 ILT/thunk、导入跳板、内联 SEH 注册（`push fs:[0]` / `mov fs:[0],esp` 前的 `push <handler>`）、`FF 25 <abs>` 间接 jmp、`.detour` 段指针与 E9 目标、TLINK 填充边界后的下一个对齐地址。
- **规模/可用性**：本镜像 **无 EXCEPTION 目录、无 LOAD_CONFIG/SafeSEH、无 TLS、无 BASERELOC**（PE 数据目录实测，见 `work/recon.py`）——故 `.pdata`/ILT/SafeSEH 子源**在此 PE 上为空**，如实记录不臆造。可用子源命中：`jmp_abs` 404、`detour_ptr` 466、`seh_movfs` 15、`seh_pushfs` 0；落合格池且不在 coverage **0 个**（H 的 7 个候选多已在 coverage）。
- **异源说明**：完全基于 PE 结构目录与间接跳转/段边界，不涉及 atlas 区间、引用目标或字节形态——与旧五通道异源。
- **产物**：`EVIDENCE/channel_H_meta.tsv`。
- **结论性发现**：H 在本镜像**零新增**（结构化元数据已全部被 coverage 覆盖或不在合格池）。这不是通道失败，而是该 PE 缺乏相应目录的真实反映。

---

## 通道完备性判定
三组对照见 `COUNTERFACTUAL.md`。核心：正对照 F|G 召回 99.62%（看似达标），但**对照样本有偏**（gate/resid 本身由旧通道筛出），独立 oracle `0x7775C0`（首字节 0x51）被 F 和 G 双双漏检，且 2,026 个 FPU 叶函数（真实完整函数体、以 ret 终结、无引用）同样被形态过滤器漏掉。因此**通道不完备**，交 (c)。
