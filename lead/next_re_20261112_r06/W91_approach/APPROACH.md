# W91 APPROACH — 长途接敌：分离「行军/寻路」与「交战」

卡片：`lead\next_re_20261112_r06\W91_approach\`（真机执行卡 W91）
日期：2026-11-14，全部结论为单机沙箱真机实测（gamemd.exe + cnc-ddraw，只读观测）。

## FINAL 一句话

**[本次实测] 在 200×200、对象数与 C6 完全一致（1522）的布局上，同一趟内：A 相位（纯行军/寻路，44.4 s）CPU 消耗率 56.86 % > B 相位（行军+交战+毁伤，215.6 s）37.49 %，A/B = 1.517 ≥ 0.8 ⇒ 按预注册判读 v2：「CPU 消耗率主要由行军/寻路贡献，交战增量有限」；但分段语境显示交战**初期**（前 60 s 64.2 %）与行军同量级，B 的低均值来自交战后期长尾（105–260 s 降到 27.1 %）。单趟、单布局。**

---

## 一、设计与方法

### 方法：地理分离 + 趟内两阶段（不造"纯移动 mission"）
敌军必须横穿大半张地图才接触玩家资产；同一趟内按两个机械锚切相位：

| 相位 | 判据（机械锚） | 语义 |
|---|---|---|
| **A** | `A8ED50==0` **且** `X87E8E0` 已变化 | 有移动/寻路，无弹药事件 |
| **B** | `A8ED50` 首次非零之后 | 移动+交战+毁伤 |

- 主统计量：窗口线程 CPU 消耗率 = Σ`win_cpu_ms_delta`（GetThreadTimes kernel+user FILETIME）/ Σ墙钟，6 ms 采样，增量归属后一个采样点所在相位；cycle 通道并列交叉核对。
- 相位切分在采样流内逐样本打 `phase` 标签，离线只做窗口聚合。

### 三个 trip（唯一目录，永不复用）

| trip | 设计 | 结果 |
|---|---|---|
| trip_P1 | v1（作废）：100×100，玩家只放建筑，敌 200 Hunt | 32 s 引擎 AV（Eip=0），outcome=ABORTED_ENGINE_ERROR；A 相位仅 26.0 s |
| trip_P2 | v1 对角极限 + `[NAPOWR] Crewed=no`（**W88 C7 证明 Crewed=no 并未阻止崩溃**，措辞已按 lead 更正） | 31 s 引擎 AV（Eip=0x006F36FE），ABORTED_ENGINE_ERROR；A 相位 23.8 s |
| **trip_P3** | **v2（lead 修正版）：200×200，对象数=C6（1522）**：玩家 NACNST×1+NAPOWR×6(step3)+TESLA×12+**300 MTNK Guard**（右下角），敌 3 house×400 MTNK 全 Hunt（左上对角）+3×GAPOWR | **VALID_WINDOW_target_reached，260.0 s 全程无崩** |

P1/P2 被作废的原因（lead 承认设计错误）：对象数 ~220 ≠ 1522，跨趟 CPU 率与 C6/CTRL_C6 不可比。P1/P2 数据保留作崩溃取证（`EVIDENCE\`、`UNKNOWNS.md` U-1/U-2），**不进入任何判读**。

### trip_P3 布局（`out\inputs\P3\w91_design_P3.json`，sha256 `eb1f64d6…`；RA2F_M1.MAP `e5c67172…`，89,047 B）
- 地图 200×200 TEMPERATE（ra2forge 支持 40..200 偶数方形，实测 build+load 通过）。
- 玩家 Russians（右下角紧凑，全部 2×2 基础不重叠）：NACNST(176,160)；NAPOWR row178 cols 154..169 step3；TESLA rows 180/182 cols 154..169 step3；**300 MTNK Guard** rows 185–196 cols 148–172。
- 敌 British/Confederation/Arabs 各 400 MTNK 全 `Hunt` rows 4–15 cols 2–103 + 各 house GAPOWR row2（C6 同构）。
- 直线接敌距离 ≈ 230 格。

## 二、核心数字（trip_P3，`out\analysis.json`）

### 相位锚
| 项 | 值 |
|---|---|
| `X87E8E0` 首变 | t=0.024 s（idx 3）⇒ 开局即开跑，**无静止段**，「静止 vs 行军」旁证不可用（如实记录） |
| A 相位范围 | 0.006 → 44.412 s（44.405 s，7,153 样本） |
| `A8ED50` 首非零 | **t=44.418 s**（idx 7153，frame 1424） |
| B 相位范围 | 44.418 → 260.003 s（215.585 s，35,746 样本；无弹窗，窗口干净） |
| `X87E8E0` 变化次数 | 全程 12,723；A 相位内 2,754 |

### CPU 消耗率（FILETIME 主通道；cycle 通道同向）
| 窗口 | rate（单核 %） | 墙钟 | 样本 | ΣCPU ms |
|---|---|---|---|---|
| **A（行军）** | **56.86** | 44.405 s | 7,153 | 25,250 |
| **B（行军+交战）** | **37.49** | 215.585 s | 35,746 | 80,828 |
| 全程 | 40.80 | 259.997 s | 42,899 | 106,078 |
| A 内前 10 s | 62.87 | 10 s | — | — |
| A 内 10–44 s | 55.07 | 34.4 s | — | — |
| B 内前 60 s（交战初期） | 64.15 | 60 s | — | — |
| B 内 105–260 s（交战后期） | 27.08 | 155 s | — | — |

### 预注册判读 v2 落点（跑前已写死 PROGRESS.md）
- **A/B = 56.8624 / 37.4924 = 1.517 ≥ 0.8** ⇒ 判读条目 1：「CPU 消耗率主要由行军/寻路贡献，交战增量有限」。
- **必须附带的地诚语境（单趟、单布局）**：B 的低均值是被交战后期长尾拉低的——交战**初期**（敌 1200 辆齐射的头 60 s）64.15 %，**高于** A 相位全程；105 s 后敌军被 300 Guard+TESLA 大量消耗，速率降到 27.08 %。所以更准确的表述是：**「寻路/行军」与「交战初期」都是主力成本，交战成本随单位死亡快速衰减**。判读表第 1 条成立，但「交战增量有限」仅对 260 s 全程平均成立，对交战初期不成立。`[本次实测]`
- cycle 通道核对：A 0.1965 / B 0.1429（同序，A > B），与 FILETIME 一致。

### 参照点（引用，未重跑；仅语境，不进判读）
| 臂 | 敌单位 | CPU 率 | 来源 |
|---|---|---|---|
| C6 交战臂 | 1200 Hunt | 31.0–33.6 % | W88 signed 33.6062 / W90 pair_c 31.0087 / pair_d 31.9672 |
| CTRL_C6 | 1200 Guard | 17.75–18.10 % | W88 signed 18.0950 / W90 pair_c 17.7624 / pair_d 17.7524 |
| 比值 | — | 1.746 / 1.801 / 1.857 | N=3 配对 |
- W88/W90 的布局是 100×100、两军贴脸（交战全程占满窗口）；P3 是 200×200 + 长途接敌。**P3 的 A 相位 56.86 % 高于 C6 的 31–33.6 %** —— 与「1200 单位密集寻路 + 200×200 大图寻路开销」相容，但这是跨布局对比，只作语境。`[静态推断]`

## 三、P1/P2 崩溃（D1 取证完整；详见 UNKNOWNS U-1/U-2、DISAGREE D-1）

| trip | A8ED50 首非零 | 弹窗 | except 签名 | 语境 |
|---|---|---|---|---|
| P1 | 26.02 s | ≈32 s | **Eip=0x00000000 / Access=0x00000000**（空指针调用，栈顶返回 0x47C500） | 无 Crewed 覆盖；玩家无单位，敌首个交战目标=建筑 |
| P2 | 23.81 s | ≈31 s | **Eip=0x006F36FE / Access=0x11378560** | 已带 Crewed=no ⇒ **生兵链非必要环节** |

- 两崩都在「接触 +6~7 s」，跨布局一致（N=2）；且是**两种不同**签名，均不同于 W88 的 `0x47C538/[eax+0x2C]` 与 R03 的 `0x51C2D3/[eax+0x1D4]`。`[本次实测]`
- 注意：lead 消息引 `EIP=0x006F36FE/Access=0x11378560` 只匹配 **P2**；P1 是 Eip=0 —— 已按「不合并」纪律分列（DISAGREE D-1 有原文与哈希）。
- P3（加了 300 玩家 MTNK Guard、对象数=C6）**不崩**：敌军在中途先撞上玩家坦克群，首个交战目标=单位而非建筑。与 U-2 的候选链相容，未证。`[未证]`

## 四、lead 零成本子步骤：ddraw `0x5EE48` 定案（trip_P3 上执行）

- 基址 `0x54400000`（ASLR 开启）；`0x5EE48` 运行时 = **210 (0xD2)**；maxfps(0x594E8)=60；interval(0x5F128)=16；last_t(0x5F120) 逐帧变化（1.2 s 两次读不同）；vsync(0x594EC)=0（lead 预期 1，实测 0，一并记录）。
- **判决**：运行时确实是 210 ⇒ W90 的 clamp=210 **不是读取口径问题**，存在静态扫描未覆盖的写入路径或配置覆盖（原始 16-dword dump 在 `trip_P3\ddraw_globals_probe.json/.txt`）。`[本次实测]`
- 过程：P1/P2 探测失败（64 位观察者 Toolhelp 枚举 WOW64 模块列表为空）→ 改 psapi `EnumProcessModulesEx(LIST_MODULES_ALL)` 兜底后 P3 成功。

## 五、分级与未覆盖项

**分级**
- A/B 相位数字、相位锚、ddraw dump、三趟 outcome/D1：`[本次实测]`
- 「P3 不崩是因为敌军先撞玩家单位」、U-1/U-2 崩溃链候选：`[未证]`
- 跨布局参照（C6/CTRL_C6 与 P3 并排）：`[静态推断]`（引用他人实测值）

**未覆盖项（下一步建议）**
1. **N=1**：P3 是单趟单布局。若要稳 A/B 结论，最小改法 = 同布局重跑 1 趟（trip 目录 trip_P3_r2）。
2. B 相位内分段（0–60 / 60–105 / 105–260 s）是**语境**，未预注册；若要把「交战成本随敌军消耗衰减」变成判读条目，需先预注册再跑。
3. U-1/U-2 崩溃链分离：最小诊断趟 = P1 布局 + 去掉 12×TESLA（看是否仍崩 ⇒ 二分「TESLA 击杀路径 vs 建筑毁伤路径」）。
4. 「静止 vs 行军」旁证：P3 开局即开跑（x87 首变 0.024 s），如需此旁证，需设计开局静止的布局（如敌单位 `mission=Guard` 起步 + 延迟触发，当前工具链无 unit-level 触发字段，需另行验证可行性）。
5. ddraw `0x5EE48`=210 的写入路径未找到（静态 4 处引用全查过）；若要定案需动态单步（本项目禁调试器），或对 cnc-ddraw 源码做配置面排查（如 ddraw.ini 其余键）。

## 六、产物清单

- `APPROACH.md`（本文）、`PROGRESS.md`（FINAL + 预注册 v1/v2 全文）、`HEARTBEAT.txt`、`UNKNOWNS.md`、`DISAGREE.md`
- `out\analysis.json`（相位率+锚+判读 v2+分段语境）、`out\analysis_context_P3.json`
- `out\trip_P1\` `trip_P2\`（各：run.ndjson、TRIP_RESULT.json、archived_except*.txt、wer_events.txt、archived_ndjson_tail.ndjson、installed_inputs\、截图）——均为 ABORTED_ENGINE_ERROR
- `out\trip_P3\`（VALID_WINDOW_target_reached：run.ndjson 42,900 样本、TRIP_RESULT.json、installed_inputs\、ddraw_globals_probe.json/.txt、截图 16 张含 **aph_t002/aph_t016/aph_t032 三张 A 相位中段**「敌军在路上」证据）
- `EVIDENCE\`（四份 except 副本，两两同哈希：P1 `F8F6BC24…` / P2 `3429FF45…`）
- `out\FINALIZE.json`（ok=true：沙箱 identical_tree（except.txt 按真目录哈希还原，还原前崩溃件已归档）、真目录 identical_tree、4 锚点一致、残留 gamemd=0）
- 输入存档 `out\inputs\P1|P2|P3\`（design JSON + .MAP + BATTLEMD.INI + MAPSELMD.INI + sha256）
- 真目录 `ra2youli` 全程只读：pre/post manifest identical_tree=true，4 锚点（gamemd.exe/ddraw.dll/RA2MD.INI/BATTLEMD.INI）哈希一致；沙箱内既存 v0.3 按先例仅在沙箱副本卸载，真目录未动。
