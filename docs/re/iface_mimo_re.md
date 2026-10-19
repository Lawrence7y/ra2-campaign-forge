# 双轨接口说明：MiMo（M 轨）↔ 逆向代理（R 轨）

> [META]
> 任务=EXCEPT-AB / M-R 接口 · 起草方=MiMo（M 轨）· 日期 2026-09-30
> 上位边界：`docs/re/TRACK_BOUNDARY_MIMO_RE.md`（写作用域以该文件为准；本文只补**消费/产出接口**，不改边界）
> 读者：R 轨逆向代理及其子代理 · 长度刻意短；细节链到源文档

---

## 1. R 轨可直接消费的 M 轨产物

| 产物 | 路径 | R 轨怎么用 | 等级 |
|---|---|---|---|
| **except 取证定谳** | `docs/re/except_zc11_forensics.md` | 崩溃点 = 原版 `__sbh_alloc_block @ 0x007CFB13`（EIP `0x007CFC9F`，FileOffset `0x3CFC9F`，字节 `8B 0A …`）；毒值 `EDX=FE00FFFF`；调用链 `CRT::_new 0x7C8E17 → _nh_malloc 0x7C9442 → heap_alloc 0x7C946E → __sbh_alloc_block 0x7CFB13`。**执行层与 ra2render 无关已定谳**；根因（UAF/double-free/越界写）是 R 轨选题 | [实证] |
| **可复算脚本** | `out/re_work/except_forensics/recompute_except_zc11.py` | 一键重放 except 解析 + 反汇编 + 毒值扫描 + 时间线；改 R 侧结论前先跑它对齐字段 | [实证] |
| **H1 fanout 机制** | `docs/re/h1_fanout_mechanism.md` | 三源模型：预置行 / `RespawnStartingForces 0x50D440` / `GenerateStartingUnits 0x5D70F0`；`mobile_count` 口径 = Unit+Infantry+Aircraft Array Count@+16；7× 同格堆叠；国家对耦合。解读引擎出兵/Array 语义时**以此为负载事实底座** | [实证]+[推演] |
| **进图指纹口径** | 同上 §4 M5 + `segD_run.py` 误选签名 | 误选签名 U0050/U0200/U0800 ≈ **178 / 713 / 2852**（7×per_house+StartingUnits）；units_seen≈713 优先判「进错图」而非负载异常。R 轨做动态 dump 时**必须**先对指纹，避免把误选当机制 | [实证] |
| **参考崩溃件** | `out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated`（SHA256 `B42C7014…`） | 同型对照；禁止改写 | [实证] |
| **符号/锚点** | `out/reverse/symbols.json`、`m1_blit_targets.txt`、`tools/verify_anchors.py` 323/323 基线 | 静态结论落锚点用 | 共享只读 |

**R 轨不必重做**：except 执行层归属、EIP 字节核对、调用链 CRT 帧、H1 图内无触发器出兵源、7× 堆叠几何缺陷——均已定谳，重做只会覆盖。

---

## 2. R 轨交付如何被 M 轨消费

| R 轨交付 | 落点（R 写域） | M 轨下游用途 | 契约 |
|---|---|---|---|
| **LightConvert `0x420140` dump 结论**（表生成公式 / 是否含 ×0.71875 / 向灰实现） | `out/re_work/re_sprint/**` 或 `out/reverse/feat_*` | **迷雾桩**：决定非线性混色/向灰桩的常量与阶段划分（当前 M1 最优、常数 k 已否决、g≈67–72；缺第一段站点） | 只要「结论 + 可复算 dump」；**不要** R 轨改桩代码 |
| **堆/SBH 深入**（freelist 布局、size-class、被污染槽位类型、UAF 指认） | 同上 | **harness 门禁**：`except_watch` 判据细化（EIP 集合、毒值族、size-class 签名）；A/B 协议 J4/J5 升级 | 机制产出 → M 写门禁；R **不改** `tools/bench_*.py` |
| **触发器/AI、新结构体偏移、源码锚点** | `docs/re/<主题>_deep_dive.md`、`ARCHITECTURE_ATLAS*`（须 Lead 授权） | 勘误补丁块素材、harness 字段读点、后续卡选题 | 新主题用**新文件名**；不改 M 已有主题文档 |
| **真机 dump 卡执行结果**（ZCode） | `out/re_work/zcode_live/**` 或 `out/re_work/re_sprint/**`（**约定后不换**） | 证据共享；M 侧收尾/门禁可引用 | dump 证据树两边可读不可改 |

---

## 3. 禁止事项（双侧对称）

1. **不越界写**：R 不写 `tools/bench_*.py`、`out/loadbench/**`、`out/re_work/zcode_live/**`（执行结果除外且仅 ZCode）、`out/re_work/h1_map_fix/**`、harness/勘误块；M 不写 `out/reverse/fn_*`、`out/re_work/*_disasm*`、`ARCHITECTURE_ATLAS*.md`、纯 exe 反汇编专章。
2. **不伪造实测**：证据等级只用 `[实证]/[推演]/[待实测]`；未跑过的一律 `[待实测]`。
3. **不改对方已有主题文档**、不就地改冻结源文档（勘误只出补丁块，Lead/用户解冻后写）。
4. **不改游戏二进制 / ra2render**：`ra2youli/**`、`ra2bench/**` 游戏文件、`gamemd.exe` 只读；`ra2render/**` 归 ZCode（A 轨），两轨都无授权不得代写。
5. **不把「建议」写成「定谳」**；不把「没崩/没数据」写成「已排除」。

---

## 4. 升级路径（撞车/矛盾时）

1. **撞写同一文件**：后到者停手，改投本轨写域或请用户裁决（边界 §4）。
2. **跨轨问题**：写进**自己**报告的「跨轨提示」节，不代改对方文件。
3. **证据冲突**（如 R 新 dump 与 M 取证不一致）：各自保留原文 + 等级，升级用户/Lead；禁止静默改对方结论。
4. **需要对方写域才能闭环**：提工单（谁的域谁落笔），不在对方域「顺手修」。
5. **台账**：仅 Lead 合并 `REVERSE_ENGINEERING_AND_PATCHES.md`；两轨只交 §九草稿。

---

## 5. 建议 R 轨首批选题（**只建议、不派工、不排期**）

> 以下为 M 轨从当前缺口倒推的**候选**，优先级供参考；**不构成任务分配**，实际认领以用户/Lead 派工为准。与边界 §5「明确让给 R 轨」一致。

| 候选 | 为什么现在做 | 关键缺口 | 预估产出形态 |
|---|---|---|---|
| **① LightConvert `0x420140` dump 分析** | 迷雾「第一段 ×0.71875」站点未定位；表运行期生成，静态读不到；卡住非线性混色桩与灰目标 g | 表公式、是否嵌入 0.71875、与 M1 拟合 g≈67–72 对齐 | 真机 dump + 公式推导 + 可复算脚本；M 侧接迷雾桩 |
| **② SBH / 堆深入** | except 已定谳在 `__sbh_alloc_block`，但「谁污染 freelist」未指认；直接喂 harness 门禁与 A/B 判读 | size-class 签名、被毒槽位归属对象类型、UAF/double-free 判别 | 机制专章 + 判别签名表；M 侧写 `except_watch` 门禁 |
| **③ Verses / Deform ABI 补全** | `Verses[0]=+0xA0` 已实证，但**施加点未定位**（全 `.text` 无 `*8+0xA0/0xB0` 索引访存）；`Deform +0xA8` 与 `Verses[1]` 重叠存疑（E-8） | Verses 乘算指令、Deform 真实偏移、与 `ReceiveDamage 0x701900` 形参链衔接 | 偏移/施加点实证 → 勘误 E-8 收口；**闭环前禁止**基于 Verses 的优化放行 |

**排序建议**（非派工）：② 与 A/B 真机协议（ZC-EXCEPT-AB）同期最互补 → ① 解锁迷雾桩 → ③ 清 ABI 债。若只做一件，M 轨倾向 **② SBH**（直接消解「注入态才复现」残留不确定性）。

---

## 6. 一句话

> M 轨交「负载事实 + 崩溃定谳 + 指纹口径 + harness 门禁」；R 轨交「机制与偏移」；ZCode 交「真机证据」。桥 = dump 结论（迷雾桩）与堆结论（except 门禁）；红线 = 各守写域、不伪造、不代改对方文档。

---

## 7. 2026-09-30 再声明（R 轨边界复确认）

> [META] 追加方=MiMo（M 轨）· 时点 2026-09-30 · 性质=边界复确认，不改正文契约
> 本节为**追加**，与 §1–§6 并列有效；若与上位 `TRACK_BOUNDARY_MIMO_RE.md` 冲突以边界文件为准。

### 7.1 R 轨**禁止写入**（含新增项，合并 §3.1）

| 禁区路径 | 说明 |
|---|---|
| `out/loadbench/**` | 负载基准图、pristine 镜像、安装日志、截图证据树全部归 M 轨；R 轨只读 |
| `MANIFEST.sha256`（`out/loadbench/pristine/MANIFEST.sha256`） | 完整性基线；仅 M 轨经工具重采；R 轨不得重写/补行 |
| `tools/bench_*.py` | bench harness 全家（replay / cam_reset / map_install / metrics / filter …） |
| `tools/h1_*` | H1 指纹与地图生成（`h1_map_fingerprint.py`、`tools/bench_maps/**`） |
| `tools/check_except_gate.py` | except 门禁；R 轨机制结论只能进判据提案，不改脚本 |
| `out/re_work/{h1_*,except_gate,harness_closeout,errata_patches}**` | M 轨工作区；含 `h1_map_fix/`、`h1_fanout/`、`except_gate/`、`harness_closeout/`、`errata_patches/` 及此后同前缀新目录 |

> 另重申既有禁止（不因本节放宽）：`ra2render/**`、`ra2youli/**`、`ra2bench/**` 游戏文件、`gamemd.exe`、顶层台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、`out/re_work/zcode_live/**`（ZCode 执行结果除外）。

### 7.2 R 轨建议首批选题（**仍为**这三项，不派工、不排期）

与 §5 一致，2026-09-30 复确认不变：

| 序 | 选题 | 对接 M 轨缺口 | 预期落点 |
|---|---|---|---|
| ① | **SBH / 堆深入**（freelist、size-class、UAF 指认） | except 门禁判据细化（EIP 集合 / 毒值族 / size-class 签名） | `docs/re/sbh_freelist_deep_dive.md` 等 R 域新文件 |
| ② | **LightConvert `0x420140`**（表公式 / ×0.71875 / 向灰） | 迷雾非线性混色桩常量与阶段划分 | `docs/re/lightconvert_0x420140_deep_dive.md` 等 |
| ③ | **Verses-Deform ABI**（乘算指令、Deform 真实偏移） | 勘误 E-8 收口；闭环前禁止基于 Verses 的优化放行 | `docs/re/warhead_abi_verses_deform_deep_dive.md` 等 |

> 观察：截至 2026-09-30 10:12，R 轨已就上述三项分别落出 deep dive 初稿（`sbh_freelist_deep_dive.md` / `lightconvert_0x420140_deep_dive.md` / `warhead_abi_verses_deform_deep_dive.md`）——与本建议首批吻合；后续仍以可复算证据收口为准，M 轨不代改这些文件。

### 7.3 跨轨**只读**引用路径清单（双方可读、都不可写）

| 路径 | 内容 | 用途 |
|---|---|---|
| `docs/re/except_zc11_forensics.md` | except 执行层定谳 | R 轨堆分析的事实底座 |
| `docs/re/h1_fanout_mechanism.md` | 三源模型 / mobile_count / 误选签名 | 引擎出兵与 Array 语义负载事实 |
| `docs/re/h1_map_fingerprint.md` | M1 互斥 + M5 指纹 + M2 规格 | 图字节与指纹口径；R 轨动态 dump 对指纹用 |
| `docs/re/except_ab_protocol.md` | A/B 真机协议细则 | R 轨解读 except 来源时对齐开关语义 |
| `docs/re/except_gate_harness.md` | 门禁判据 | R 轨产出机制后的判据接口 |
| `out/re_work/zcode_live/RESULT_ZC11.md` 与 `zc11/evidence/**` | 真机证据树 | 同型对照；**禁止改写** |
| `out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated` | 参考崩溃件（SHA256 `B42C7014…`） | 毒值/EIP 对照 |
| `out/loadbench/pristine/MANIFEST.sha256` | 完整性基线 | R 轨引用哈希即可，不改 |
| `out/loadbench/pristine/H1/[2]0LoadBench_U*_H1.yrm` | 修复后 H1 图（指纹 `H1FP1\|…`） | 动态 dump 前先对指纹 |
| `out/re_work/h1_map_fix/backup_pre_fix/**` | 旧图冻结字节 | 新旧对照 |
| `out/reverse/symbols.json`、`out/loadbench/m1_blit_targets.txt` | 符号/锚点 | 静态结论落锚 |
| `tools/verify_anchors.py`（323/323 基线） | 锚点门禁 | 共享只读；修复须提工单 |
| `docs/re/TRACK_BOUNDARY_MIMO_RE.md` | 上位边界 | 写作用域唯一裁决源 |

### 7.4 一句话

> R 轨禁区扩到 `out/loadbench/**` + `MANIFEST` + `tools/{bench_*,h1_*,check_except_gate}` + `out/re_work/{h1_*,except_gate,harness_closeout,errata_patches}**`；首批仍为 SBH / LightConvert / Verses-Deform；跨轨一律走 §7.3 只读清单。

---

## 8. 2026-09-30 第二批选题与真机卡（MiMo 追加）

> [META] 追加方=MiMo（M 轨）· 时点 2026-09-30 · 性质=第二批选题 + 边界续确认 + ZCode 真机卡
> 首批 R-01/R-02/R-03 已交付（三份 deep_dive 落盘）；本节登记**第二批**与**真机验证卡**。与 §7 并列有效。

### 8.1 首批成果速览（供双方对齐）

| 题 | 定谳摘要 | 对 M 轨的直接影响 |
|---|---|---|
| R-01 LightConvert | `0x420140 = AlphaLightingRemapClass::FindOrAllocate`；闭式 `q=floor(lo·hi·(L−1)/32258)` 全量零误差；**不含 0.71875**；与 M1 向灰结构性不吻合 | 迷雾第一段搜索面收窄：C1 降权；剩余 = DrawTile 光照链 / 环境光 |
| R-02 SBH | 毒 class=4（req 57..72B）在 heap_info freelist-head；主候选 UAF 写穿 `next`；size-class 64 类 + Region 0x14 步长 + H1-H6 钩子规格 | harness `except_watch` 判据可细化（class 0..8 优先、head 数组必查、位图 MSB-first） |
| R-03 Verses/Deform | **Deform=+0x98**（非 +0xA8）；Verses 施加点 8 处 FPU 实证（V1 `0x48923D` 主施加）；ABI 惯用式；`Size()=0x1D0` | E-8 可收口（补丁文本在 R-03 报告 §5.1）；Verses 优化放行前置已解 |
> 【W3 勘误 · W3-A6/ISSUE-VERSES-SITES-COUNT】改前：Verses/Deform | **Deform=+0x98**（非 +0xA8）；Verses 施加点 8 处；改后：Verses FPU 索引访存共 9 处 (V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)；依据：errata_sync_master_table.md:22 (R-E07); warhead_verses_residual_p2.md:18, 58；分级：P1

> 【勘误 2026-09-30 · R-E07 · errata_sync】上表「Verses 施加点 8 处 FPU」→ 订正为 **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）。权威：warhead_verses_residual_p2.md:18,58 / warhead_abi_verses_deform_deep_dive.md §3.2。原文保留不删字。

### 8.2 第二批选题（已派子代理，写域互斥）

| 题 | 目标 | 写域（R 侧） | 状态 |
|---|---|---|---|
| **R-04** | 迷雾第一段剩余候选定点取证（DrawTile `0x547D95` 光照参数链 / 环境光 `0x423621` / 向灰 lerp 形态） | `docs/re/fog_firststage_candidates_deep_dive.md` + `out/re_work/re_sprint/fog_stage1_candidates/**` | 已派 |
| **R-05** | SBH UAF 写穿路径收敛（class 4 分配点枚举 / 毒族业务常量反查 / 写者对象类型候选排序） | `docs/re/sbh_uaf_writer_deep_dive.md` + `out/re_work/re_sprint/sbh_uaf/**` | 已派 |
| **R-06** | Warhead ABI 残余（`+0xAC` 宿主类 / V1 `0x4891C6` 属主函数 / `TechnoTypeClass+0x9C` ArmorType 确认 / 选 2-3 类扩展偏移） | `docs/re/warhead_abi_residuals_deep_dive.md` + `out/re_work/re_sprint/warhead_abi2/**` | 已派 |

**边界续确认**：
- 三子代理**只写各自 deep_dive + re_sprint 子目录**，禁碰 M 域 / `ra2render` / 台账 / 已有 docs。
- M 轨（MiMo）**不写** R 域 deep_dive；本文件（`iface_mimo_re.md`）归 M 轨。
- ZCode 卡由 M 轨起草（下方 §8.3），ZCode 执行后证据落 `out/re_work/zcode_live/**`。
- 勘误补丁块（E-8 收口等）由 M 轨并入 `out/re_work/errata_patches/**`，待 Lead/用户解冻后粘贴。

### 8.3 ZCode 真机任务卡（M 轨起草 · 待用户转交）

```text
# ZC-RE1 · 首批 R 轨结论真机验证（2026-09-30 · M 轨起草）

> 证据真实性红线：截图唯一 MD5 / 进程留痕 / ini 前后 sha256 / 不得把没崩当功能成立。
> 环境：ra2bench（基准环境，与 ra2forge 安装件物理分离）；不改 ra2render 源码。
> 预算：单局 ≤30 min；只碰 ra2bench，ra2youli 不动。

## 段 A · Warhead ABI 真机确认（对应 R-03）
目的：确认 Deform=+0x98 与 Verses 施加点 V1=0x48923D 在真机执行。
步骤：
  A1. 加载遭遇战或战役局，选带护甲差异的目标（如坦克 vs 步兵）交火。
  A2. 对 gamemd.exe 下**只读断点**：
      - 0x48923D（fmul [edi+edx*8+0xA0]）命中计数 → 期望 >0
      - 0x75D792（fstp [esi+0x98]，Deform 装载）命中计数 → 期望 ≥1（INI 含 Deform 时）
  A3. 断点命中时记录：EDI/ESI 基址、edx（armor 0..10）、XMM/FPU 栈顶值。
判据：V1 命中 >0 且 edx ∈ [0,10]；Deform 写点命中则 ESI+0x98 内容为 double。
失败判据：V1 命中 =0（与静态矛盾，须回报寄存器现场）。

## 段 B · SBH freelist 只读采样（对应 R-02）
目的：采样 class 0..8 freelist head 与毒族哨兵，为 except_watch 门禁提供真机基线。
步骤：
  B1. U0200（H1 图，units_seen≈713）开局后每 60 s 读一次：
      - [0xB78B8C] / [0xB78B94] / [0xB78B98]（SBH 状态全局）
      - heap_info freelist head 数组（group 0..7 × class 0..8）前 8 项 next 指针
  B2. 扫描采样窗口内是否出现毒族签名：FE00FFFF / FFFF0000 / 00FFFF00。
  B3. 记录对局结束（或 except）时最终状态。
判据：正常局毒族命中 =0；若 >0 则记录指针地址 + size 字段 + 触发帧号。
产出：CSV（时间戳 / 地址 / 值 / 是否毒族）。

## 段 C · LightConvert 表抽样确认（对应 R-01，可选）
目的：真机抽 3 个 Level 值比对闭式公式（静态已零误差，本段为增强置信）。
步骤：
  C1. 断点 0x4201C7（写表瞬间），取 Level=L 时 idx=0x8080 / 0x40C0 / 0xFF01 三项。
  C2. 离线代入 q=floor(lo·hi·(L-1)/32258)，比对 word 值。
判据：3/3 一致。

## 判读约定
- A/B/C 每段独立判 PASS/FAIL；失败不掩盖，如实记录现场。
- 不改 ini 部署态；结束后逐字节还原。
- 证据落 out/re_work/zcode_live/zc_re1/**（截图 + CSV + 断点日志）。
- 回报按 AGENT_DELIVERY_FORMAT 十节骨架。
```

### 8.4 一句话

> 第二批 R-04/05/06 已并行放飞（写域互斥）；ZCode 真机卡 ZC-RE1 已起草（段 A ABI / 段 B SBH 采样 / 段 C 表抽样），待用户转交执行。

---

## 9. 2026-09-30 第三批选题与边界续确认（MiMo 追加）

> [META] 追加方=MiMo（M 轨）· 时点 2026-09-30 · 性质=第三批选题 + 边界续确认
> 第二批 R-05/R-06 已交付；R-04 被取消（有中间证据、无报告）→ 拆 R-04b 补完。

### 9.1 第二批成果速览

| 题 | 定谳摘要 | M 轨影响 |
|---|---|---|
| R-05 SBH UAF | class 4 共 31 处分配点；毒值 `FE00FFFF` = `CellStruct{-1,-512}`（非代码常量，是计算/拷贝产物）；**主候选** = `DynamicVectorClass<WaypointClass>` 扩容释放后悬垂写 | harness 门禁：盯 Waypoint 编辑/寻路路径 + class 4 buffer 释放点 |
| R-06 Warhead ABI | `+0xAC = WeaponTypeClass.Warhead`（非 BulletClass）；V1 属主 = **`MapClass::GetTotalDamage @ 0x489180`**；Armor `+0x9C` 继承自 ObjectTypeClass；Bullet WH 真偏移 **+0x128** | Verses hook 直接挂 `GetTotalDamage`；勘误：BulletClass+0xAC 误用须排查 |

### 9.2 第三批选题（已派，写域互斥）

| 题 | 目标 | 写域（R 侧） | 来源 |
|---|---|---|---|
| **R-04b** | 迷雾第一段补完：`0x45452c` **imul 184** 深挖 + 复用 R-04 中间产物落报告 | `docs/re/fog_firststage_candidates_deep_dive.md` + `out/re_work/re_sprint/fog_stage1_candidates/`（追加） | R-04 遗留关键命中 |
| **R-07** | Waypoint DynamicVector UAF 确认/排除（三选一：确认/排除/无法静态判定） | `docs/re/waypoint_uaf_confirm_deep_dive.md` + `out/re_work/re_sprint/waypoint_uaf/` | R-05 主候选 |
| **R-08** | 触发器/Tag 生命周期 ABI 补全（TriggerClass/TagClass 布局 + ctor/dtor 锚点 + YRpp 对照） | `docs/re/trigger_tag_abi_deep_dive.md` + `out/re_work/re_sprint/trigger_tag_abi/` | 边界 §5 让渡项 |

### 9.3 边界续确认（与 R 轨代理 / 子代理）

**写域铁律（每批不变）**：
1. R 轨子代理**只写**各自 `docs/re/<新主题>_deep_dive.md` + `out/re_work/re_sprint/<topic>/**`。
2. M 轨（MiMo）写：`iface_mimo_re.md`、`errata_patches/**`、`harness_closeout/**`、`h1_*`、`tools/bench_*`、ZC 卡。
3. ZCode 写：`out/re_work/zcode_live/**`（执行结果）、`ra2render/**`（代码轨）。
4. Lead 写：`REVERSE_ENGINEERING_AND_PATCHES.md`（台账）。
5. **禁写**（全轨）：`ra2youli/**`、`ra2bench/**`、`gamemd.exe`（只读）。

**撞车升级**：撞写同一文件 → 后到者停手 → 投本轨写域或请用户裁决。跨轨问题写自己报告的「跨轨提示」节。

**R 轨禁写清单（累计）**：`out/loadbench/**`、`MANIFEST.sha256`、`tools/{bench_*,h1_*,check_except_gate}`、`out/re_work/{h1_*,except_gate,harness_closeout,errata_patches}**`、`ra2render/**`、顶层台账、已有他人 `docs/re/*.md`。

### 9.4 真机卡更新

`ZC-RE1`（§8.3）仍然有效。补充段 D（R-05 发现后新增）：

```text
## 段 D · Waypoint UAF 真机判别（对应 R-05/R-07）
目的：验证 DynamicVectorClass<WaypointClass> 扩容释放后悬垂写路径。
步骤：
  D1. 在 Waypoint 路径编辑/寻路触发时，对 CRT::_delete(0x7C8B3D) 下条件断点
      （size∈[0x3C,0x48] 且 caller 在 Waypoint/Path 相关函数内）。
  D2. 释放后对同一地址下写 watch，观察是否被写入 FE00FFFF / FFFF0000 毒族。
判据：写 watch 命中且写值为 CellStruct{-1,-512} 类 → 确认；全程无命中 → 排除。
失败判据：断点/探针未装上（非技术否定）。
```

### 9.5 一句话

> 第三批 R-04b（184 深挖）/ R-07（Waypoint UAF 确认）/ R-08（触发器 ABI）已并行放飞；边界续确认见 §9.3；ZC-RE1 补段 D。

---

## 10. ZC-H1RM 后接口（MiMo 追加 · 2026-09-30）

> [META] 追加方=MiMo（M 轨）· 只文末追加，不改 §1–§9 · 对接全文 `docs/re/rtrack_bridge_h1rm.md` · 增量卡 `out/re_work/dispatch_v30/prompt_zcode_except_ab_r1.txt`

| 接口点 | H1RM 后状态 | 消费方 |
|---|---|---|
| except EIP 集 | `{0x7CFC9B, 0x7CFC9F, 0x7CFCA3}` 同族合并、按码分列 | except_ab_r1 §A；harness 判据提案 |
| 负载采样面 | **U0050 必采**（低负载已实证可崩）；高负载层降可选 | except_ab_r1 §B |
| units_seen 签名 | U0050=67 / U0200=177 / U0800=724（UC10 美vs蘇）；713=旧误选 | R-SLOT-3/4/5 |
| except 留证 | 每局 begin/end mtime+size+sha256 快照；消失/静默单独登记 | except_ab_r1 §E |
| 装图协议 | 装法 A 与 U0100 槽位移置二选一；sha 闭环 + finally 还原 | rtrack_bridge §5 R-SLOT-1..7 |
| Verses/Deform | H1RM 零触碰，E-2/E-8 收口维持；动态确认仍待 ZC-RE1 段 A | bridge §[2] |

勘误增量 E-H1RM-1/2 → `out/re_work/errata_patches/by_file/RESULT_H1_REMEASURE.md.patch`（不改冻结源）。
