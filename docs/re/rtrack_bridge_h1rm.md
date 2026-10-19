# rtrack_bridge_h1rm —— R 轨 SBH/ABI 结论 × ZC-H1RM 真机复测对接（T23）

> [META]
> 任务=T23 对接 + 结果吸收 · 起草方=MiMo（M 轨）· 日期=2026-09-30
> 性质：**只对接不改源**（R 轨 deep_dive / RESULT_H1_REMEASURE / 既有 errata 冻结件均不改）
> 只读上游：
> - R 轨：`docs/re/sbh_freelist_deep_dive.md`（R-02）、`lightconvert_0x420140_deep_dive.md`（R-01）、`warhead_abi_verses_deform_deep_dive.md`（R-03）、`warhead_abi_residuals_deep_dive.md`（R-06）、`sbh_uaf_writer_deep_dive.md`（R-05）
> - 真机：`out/re_work/zcode_live/h1_remeasure/RESULT_H1_REMEASURE.md`（ZC-H1RM，**禁止改**）+ `evidence/**`
> - 既有勘误包：`out/re_work/errata_patches/**`、`docs/re/errata_from_rtrack.md`
> 写作用域：本文 + `out/re_work/rtrack_bridge/**` + `out/re_work/errata_patches/**`（追加）+ `out/re_work/dispatch_v30/prompt_zcode_except_ab*.txt` + `docs/re/iface_mimo_re.md`（文末追加）

---

## [0] 一句话

> R-02 的 `__sbh_alloc_block` freelist 损坏模型与 H1RM 新崩溃码**同族兼容**（三种异常码落在同一指令序列的三个 EIP）；**唯一残留不一致**是 pilot#1 原始 `except.txt` 写 `EXCEPTION_BREAKPOINT` 而 RESULT 叙述写 `EXCEPTION_SINGLE_STEP`（已出勘误块，不改冻结源）。Verses/Deform（E-2/E-8）H1RM **零触碰、无冲突**。LightConvert 待办维持 R-01 后的「段 G 降权 + C1 否定」挂接。**except_ab 原卡的 F2 期望与高负载假设已过时**，增量卡 `prompt_zcode_except_ab_r1.txt` 已起草（三码家族 + U0050 必采 + except 消失留证 + 槽位协议兼容）。

---

## [1] SBH 结论 vs ZC-H1RM 新崩溃码 · 一致性表

### 1.1 R-02 指令序列（同函数 `__sbh_alloc_block @ 0x7CFB13`，摘链段）

| VA | 指令 | 语义（R-02） | H1RM 命中形态 |
|---|---|---|---|
| `0x7CFC9B` | `mov edx,[ecx+edi*8+4]` | `edx = head[class]->next`（freelist 节点指针装载） | **BREAKPOINT/SINGLE_STEP @ 0x7CFC9B**（U0050 pilot#1） |
| `0x7CFC9F` | `mov ecx,[edx]` | 读节点 size —— 毒值解引用 → **AV** | **ACCESS_VIOLATION @ 0x7CFC9F**（ZC-11 首例，`EDX=FE00FFFF`） |
| `0x7CFCA1` | `sub ecx,[ebp-0x10]`（`2B 4D F0`） | remainder = node_size − block | — |
| `0x7CFCA3` | （上条指令**末字节**） | 非指令边界 | **ILLEGAL_INSTRUCTION @ 0x7CFCA3**（U0050 #2，EIP 落入 `2B 4D F0` 中部） |

### 1.2 三种崩溃码家族对照

| # | 异常码 | EIP | 负载 | 来源 | 与 R-02 关系 | 等级 |
|:---:|---|---|---|---|---|---|
| C1 | `EXCEPTION_ACCESS_VIOLATION` | `0x7CFC9F` | U0200 / 713 单位（旧代误选态） | ZC-11 `except.txt.final_isolated`（SHA256 `B42C7014…`） | **教科书命中**：`mov ecx,[edx]` 解引用毒指针 `FE00FFFF`，`EDI=4`→class 4 | [实证] |
| C2 | `EXCEPTION_BREAKPOINT`（原始件）/ RESULT 叙述 `EXCEPTION_SINGLE_STEP` | `0x7CFC9B` | **U0050 / 67 单位（低负载）** | `h1_remeasure/evidence/except_U0050_pilot1_isolated.txt` | 落在 **C1 前一条**（freelist 指针装载）；字节首为 `CC`（INT3） | [实证·原始件] / 叙述冲突见 §1.3 |
| C3 | `EXCEPTION_ILLEGAL_INSTRUCTION` | `0x7CFCA3` | **U0050 / 67 单位（低负载）** | RESULT [7]（完整字节仅 gate 指纹 + head 存档，见消失事件） | EIP 落入 `0x7CFCA1` 的 `2B 4D F0` **中部** ⇒ 控制流已被污染 | [实证·RESULT] |

**一致性判定**：

1. **同族成立** `[实证+推演]`：三码 EIP 全在 `__sbh_alloc_block` 摘链 8 字节窗内（`0x7CFC9B..0x7CFCA3`），与 R-02「崩溃不在分配算术，而在 class 4 freelist head→next 已是业务毒值」**完全相容**。AV=毒指针解引用；ILLEGAL=EIP 被污染后落入指令中部；BREAKPOINT/SINGLE_STEP=同序列前一条指令上的异常形态。
2. **多形态表现** `[推演]`：同一元数据损坏可产生不同异常码（取决于毒值形态、EIP 对齐、是否有调试探针），RESULT [7]「同一函数三种异常码」表述与 R-02 相容，**不构成机制冲突**。
3. **低负载亦触发** `[实证]`：C2/C3 均在 **U0050（67 单位）**；R-02/R-05 的 UAF 候选（Waypoint 扩容、class 4 小结构 churn）**不要求高密度**——「高负载才崩」假设**否定**。A/B 协议 H0/H1 仍待跑，但**采样面必须含 U0050**。
4. **毒值形态在 C2 现场不同** `[实证]`：pilot#1 现场 `EDX=0x0B`、`EDI=1`（class 1），**不是** `FE00FFFF`/class 4。与 C1 的「毒值解引用」形态**不同**；更像「指针装载指令上的异常」或调试 INT3 命中，而非毒值 AV。见 §1.3。

### 1.3 残留不一致（必须登记，不改冻结源）

| 项 | RESULT_H1_REMEASURE 叙述 | 原始证据 | 处置 |
|---|---|---|---|
| pilot#1 异常码 | `EXCEPTION_SINGLE_STEP @ 0x007CFC9B`（[0]④ / [7]①） | `except_U0050_pilot1_isolated.txt:1` = **`EXCEPTION_BREAKPOINT`**；`Bytes at CS:EIP` 首字节 **`CC`**（INT3），其后才是 `54 F9 04 8B 0A…` | **勘误块 E-H1RM-1**（`errata_patches/by_file/RESULT_H1_REMEASURE.md.patch`）；RESULT 本体禁止改 |
| C2 是否「毒值 AV 同型」 | 归入「SBH 堆损坏家族 +2 例」 | 寄存器非毒值形态（`EDX=0x0B`/`EDI=1`）；`CC` 字节提示 **INT3 探针命中**（R-02 §8 V4 曾建议在 `0x7CFC9B` 下硬件断点；若为软件 INT3 则同址） | **[待实测]** 标注：C2 有两种读法——(a) 控制流污染后落入 `CC`；(b) 调试器/探针 INT3 命中被 except 捕获。**不得**在门禁里把 C2 无条件并入「毒值 AV 率」；A/B 卡按 EIP 分列 |
| C3 完整字节 | 全文隔离声明 | 实际仅 pilot#1 有完整隔离件；#2 因 **except.txt 不明消失** 仅存 head + gate 指纹 | **勘误块 E-H1RM-2**；留证规则进 except_ab_r1 |

> 红线：以上均为登记与标注，**不修改** `RESULT_H1_REMEASURE.md` / deep_dive / 参考崩溃件。

---

## [2] Verses / Deform 与既有 E-2 / E-8

| 项 | R 轨定谳 | H1RM 是否触碰 | 与 errata_patches 关系 | 结论 |
|---|---|---|---|---|
| E-2 Verses[0]=+0xA0 | R-03 复核通过（`0x75DE06` 等） | **否**（H1RM 为负载/崩溃测量，无 warhead ABI 操作） | `weapons_damage_production.md.patch` E-2×8 + E-7×2 + E-2 复核注 | **无冲突，维持** |
| E-8 Deform=+0x98 | R-03 定谳（`0x75D792 fstp [esi+0x98]`）；E-8-D 已入补丁包 | **否** | 同上 E-8 + E-8-D | **已收口，H1RM 无新增** |
| E-2-S 施加点 8 处 FPU | R-03/R-06；V1 属主 `MapClass::GetTotalDamage` | **否** | E-2-S / E-ABI-AC 已入包 | **维持**；动态确认仍待 ZC-RE1 段 A |
| E-ABI-AC / HouseClass Array | R-06 | **否** | 已入包 | **维持** |
| E-1 Blitter | R 轨未触碰 | **否** | 原补丁不动 | **维持** |

**摘要**：H1RM 与 E-2/E-8 **零交集**；R-03/R-06 既有收口状态不变。伤害优化放行前置仍为「静态已齐 + ZC-RE1 段 A 真机命中」——H1RM **不解除**该动态前置（H1RM 未跑 ABI 断点）。

---

## [3] LightConvert 待办挂接点（R-01 × H1RM）

| 待办 | R-01 后状态 | H1RM 影响 | 挂接点 |
|---|---|---|---|
| 迷雾第一段 ×0.71875 | **C1（本表）否定**；剩余=DrawTile 光照链 / 环境光 / 向灰 lerp | H1RM 无迷雾测量，**无新证据** | 维持 `iface` §9.2；R-04b（`0x45452c imul 184`）继续 |
| 段 G 动态 dump | 降权为「增强置信」（公式已零误差闭环） | 无 | ZC-RE1 段 C 可选抽样（`0x4201C7`） |
| M1 向灰 / 非线性混色桩 | 本表不是 M1 实现；「用 LightConvert 解释残差」路径关闭 | H1RM 的 U0800 逻辑塌方**不改变**迷雾桩立项顺序 | 先 R-04b 站点 + 雾格分层，再议非线性桩 |
| N2 表消费端 | 开放 | 无 | 下批 R 选题候选 |

**对接结论**：LightConvert 线与 H1RM **正交**；不产生新 errata；待办挂接点维持 R-01 后版本，仅在 except_ab_r1 中避免把「表抽样」误当成崩溃门禁项。

---

## [4] H1RM 对 except 门禁 / A/B 协议的强制增量

| # | H1RM 事实 | 原协议/门禁假设 | 增量动作 | 落点 |
|:---:|---|---|---|---|
| 1 | 三码家族（AV / BREAKPOINT\|SINGLE_STEP / ILLEGAL） | J2 只认 `0x7CFC9F`；J3「其它崩溃」易把同族拆散 | **EIP 集合**扩为 `{0x7CFC9B, 0x7CFC9F, 0x7CFCA3}`，同族合并统计，但**按码分列** | except_ab_r1 §A；harness 判据提案（不改脚本） |
| 2 | U0050（67 单位）亦崩 | 「高负载加测层」= 双 0/5 才升；主场景只要 U0200 | **U0050 必采**（每臂 ≥2 局低负载）；高负载层降为可选加强 | except_ab_r1 §B |
| 3 | F2 期望 22–30 / 误选 713 **已过时** | A3/B3 预期 ≈22–30；≈713 ⇒ 误选作废 | 改为 **U0050=67 / U0200=177 / U0800=724**（UC10 美vs蘇）；误选=跨档签名互串 | except_ab_r1 §C |
| 4 | except.txt 无游戏时消失 ×1 | 「有则复制留证」不够 | **每局 hash 快照 + 时间戳**（begin/end 双采 + 消失事件登记） | except_ab_r1 §D |
| 5 | U0800 静默死亡 2/5（无 except） | gate PASS = 无事 | 静默死亡单独列（**不算** except 率分母的「未崩」） | except_ab_r1 §E |
| 6 | 槽位移置协议（H1RM） | 原卡 0.2「bench_map_install 装 U0200_H1」 | 两法并存：装法 A **或** 槽位移置；**必须** sha 闭环 + finally 还原 | except_ab_r1 §F |
| 7 | C2 现场非毒值形态 | J5 只盯 FE00FFFF 族 | J5 保留毒值族；**另列**「非毒值异常于 SBH 序列」（C2 型），不与 C1 合并率 | except_ab_r1 §A |

---

## [5] 与 H1RM 槽位置换协议的兼容说明

### 5.1 H1RM 实际协议（只读摘要，细节见 RESULT [1.3]/[2.3]）

1. **动机**：设置屏地图面板**不弹选图列表**；遭遇战按**文件名**持久化（`ScenIndex` 指向槽 `[2]0LoadBench_U0100.yrm`）。
2. **动作**：每局开始前把目标档 H1 字节拷入持久化槽 U0100（`slot_swap`，记录 `4c7f5f25afba → <tier_sha>`）；对局结束（含失败路径 **finally**）按 `pristine/old` 镜像还原（`slot_restore`，断言 `== MANIFEST 4c7f5f25afba…`）。
3. **证据链（每局三重）**：① slot sha 闭环；② 设置屏面板（`No Name`，**不能**按名区分档）；③ **units_seen 档位签名** 67/177/724 作最终误选反证。
4. **还原基准**：`out/loadbench/pristine/old/[2]0LoadBench_U0100.yrm` = 9644 B / `4c7f5f25afbab929…`（== MANIFEST）。

### 5.2 与 except_ab / 后续卡的兼容规则（强制）

| 规则 | 内容 | 违反处置 |
|---|---|---|
| **R-SLOT-1** | 槽位移置与「装法 A（bench_map_install）」**二选一**，同一局不得混用；RESULT 型卡用装法 A（三图并存），交互受限场景用槽位移置 | 混用 ⇒ 该局指纹作废 |
| **R-SLOT-2** | `slot_swap` / `slot_restore` **必须**记 sha256 前后值；restore 失败必须 finally 断言 | 无 sha 闭环 ⇒ 该局作废 |
| **R-SLOT-3** | 档位判定**不得**依赖地图名（面板显示 `No Name`）；以 **slot sha + units_seen 签名** 双确认 | 只凭截图名 ⇒ 不可采信 |
| **R-SLOT-4** | units_seen 新签名（UC10 美vs蘇）：**U0050=67 / U0200=177 / U0800=724**（同档极差 0）；UC0 对照：39/149/≈696 | 跨档互串（如 U0200 读到 67）⇒ 误选，作废重跑 |
| **R-SLOT-5** | 旧误选签名 **178/713/2852** 仅作历史参照；H1FP1 新图上**不应出现** 713–723 | 出现 713 ⇒ 先查是否旧图/误选，再谈负载异常 |
| **R-SLOT-6** | 还原后必须 `bench_map_install --verify`（或等价 sha 清点）至 PASS；H1 `_H1` 名文件零残留 | 有残留 ⇒ 未完成收尾 |
| **R-SLOT-7** | 槽位文件路径固定为游戏目录 `[2]0LoadBench_U0100.yrm`（当前 ScenIndex 持久化槽）；**不得**改 MANIFEST 基线来「适配」槽内容 | 改 MANIFEST ⇒ 红线 |

### 5.3 与 A/B 三臂的组合

- 臂 A（OFF）/ 臂 B（ON）/ 臂 C（LFH=0）**共用同一套槽位协议**；每臂独立 `slot_swap`→对局→`slot_restore`，禁止「换一次槽跑完整臂」（跨局残留风险）。
- 崩溃局与静默死亡局同样必须走 finally 还原（H1RM 12/12 闭环先例）。
- 国家对锁定 **P1=Americans / P2=Russians**（H1RM 已证国家耦合消失，但 A/B 仍须固定以便率比较）。

---

## [6] 跨轨提示（写在本轨，不代改对方文件）

1. **R-02/R-05**：H1RM C2 现场 `EDI=1`（class 1）而非 class 4——若 C2 非调试 INT3，则说明**被毒 class 可能不唯一**；建议 R 轨 UAF 收口时把 class 1（req 9..24B 量级）纳入观察面，但**不要**因单例改写 class 4 主结论。
2. **R-05 Waypoint 主候选**：H1RM 低负载（67 单位）仍崩，与「713 单位寻路高 churn」触发条件**弱化**——主候选仍成立（寻路/路径编辑在低负载亦存在），但「高密度必要性」论据降权。
3. **R-03/R-06**：H1RM 未提供 ABI 动态证据；ZC-RE1 段 A 仍是 Verses/Deform 真机确认的唯一路径。
4. **R-01**：H1RM 无迷雾数据；勿把 U0800 塌方误读为渲染/迷雾问题（实测 CPU 高位 = 逻辑/AI）。

---

## [7] 产物索引

| 产物 | 路径 |
|---|---|
| 本文（对接报告） | `docs/re/rtrack_bridge_h1rm.md` |
| except_ab 增量卡（不覆盖原卡） | `out/re_work/dispatch_v30/prompt_zcode_except_ab_r1.txt` |
| 勘误块 E-H1RM-1/2 | `out/re_work/errata_patches/by_file/RESULT_H1_REMEASURE.md.patch` |
| errata README 编号续登 | `out/re_work/errata_patches/README.md`（追加） |
| 接口增量「ZC-H1RM 后接口」 | `docs/re/iface_mimo_re.md` §10（文末追加） |
| 桥接工作副本/索引 | `out/re_work/rtrack_bridge/rtrack_bridge_h1rm_INDEX.md` |

---

## [8] 一句话（收口）

> R-02 机制模型 **吸收** H1RM 三码家族（同序列多形态 + 低负载触发）；E-2/E-8 **无冲突**；LightConvert **正交**；协议增量已落 `except_ab_r1`（三码 / U0050 必采 / 新签名 / except 消失留证 / 槽位七规）；唯一勘误是 RESULT 叙述 `SINGLE_STEP` vs 原始件 `BREAKPOINT`（E-H1RM-1）与 C3 证据残缺（E-H1RM-2）。ROI 维持冻结（继承 RESULT [9]，本文不改判）。
