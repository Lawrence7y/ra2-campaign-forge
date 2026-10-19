# 「向灰混合 vs 纯压暗」离线验证 + 单位可见性交叉核验（FOG-GRAYMIX-OFFLINE）

> [META]
> task=FOG-GRAYMIX-OFFLINE · 执行方=MiMo 子代理 · 日期 2026-09-29 · mode=read-only（新建本文 + `out/re_work/fog_offline_verify/**`）
> 基线（只读，前后一致）：`ra2youli/gamemd.exe` 4,825,360 B / MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`；`scratch_fog.shp` 88,712 B / MD5 `27F87294F68A923012F4F6B9575583D3`（sha256 `B8E36404…55E73F`）
> 数据来源：ZC-9B 3 档 ROI 均值（`out/re_work/zcode_live/zc9b/evidence/b3_valid_rungs.json`）；FOG.SHP 帧数据；`gamemd.exe` 静态反汇编
> 交付物：本文 + `out/re_work/fog_offline_verify/**`（3 个可复算脚本 + results/）
> 证据等级：**[实证]** / **[推演]** / **[待实测]**；离线拟合**不当定谳**

---

## [0] 结论摘要（≤5 行，可独立读懂）

1. **常数 k 纯压暗被量化否决**[实证]：4 个 ROI 对同一 s 的响应比 `out(s=256)/out(s=0)` 分别为 0.837 / 0.290 / 0.298 / **1.275**（跨 ROI 差 4 倍以上，且 BRIDGE **>1 反向**）；常数 k 模型对所有材质预测同一比值 0.5，与实测矛盾。
2. **「暗像素变亮」只能由向灰混合（M1/M3）解释**[实证+推演]：DIR 从 13.10→45.21、TOP 从 12.98→43.57（s:256→0），M1/M3/M4 方向全对，M0（常数 k）**不能**使暗像素向固定灰增亮；BRIDGE 反向（g<c_bridge）三模型均能解释。
3. **残差表**[实证·可复算]：M1 在 FOG(SS=0.20)/DIR(51.60)/TOP(46.82) 最优，M4 在 BRIDGE(3.91) 最优；M1 与 M3 数学等价（最大预测差 = 0）。DIR/TOP 的 SS~50 说明 α 线性假设不完美（或 ROI 混入渐变格 / 机位残差），需 ZC-11 补档。
4. **反汇编与假设一致性**[实证]：`CellClass::Draw_Shroud_And_Fog 0x004801F0` / `Draw_Fog 0x0047F250` 锚点 14/14 命中；原版 B1/B2 为 FOG.SHP 索引**加性 tint**（`lea ecx,[ecx+edx-0x7f]`，fog=66 ⇒ dest−61），**不是**向灰、**不是** 50% 减法；该窗口现网已被我方强度桩覆盖 ⇒ 实测向灰行为**不来自**原版 opcode，来源仍在「第一段 ×0.71875 / 调色板路径」未定位段（与 FOG-FIRSTSTAGE-R3 未闭环项一致）。
5. **DEF-FOGPARTIAL**：静态首选候选仍是 H1（中心格 shroud ⇒ 整栋零光照画黑）+ 感知「半截」；但「灰雾区敌方建筑只画一半」现象另有 3 条可检验候选（附属 Anim 不受 EnableBuildingFog 约束 / 三粒度判定不一致 / FadeFogTransition 逐格过渡），见 §F5。

---

## [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|---|------|------|----------|----------|
| Q1 | M1/M3/M4 残差交叉验证（可复算） | 已完成；汇总表见 §3 | [实证]（脚本输出） | `out/re_work/fog_offline_verify/results/residual_table.csv` |
| Q2 | 哪个模型能解释「暗像素变亮」 | **M1 / M3（=M4 方向也可）**；M0 常数 k **不能** | [实证]+[推演] | `results/model_compare.json` direction_tests |
| Q3 | `net=k(1-s/512)` 常数 k 是否成立 | **不成立**（比值跨 ROI 4 倍差 + BRIDGE 反向） | [实证] | `results/ratio_table.csv` |
| Q4 | `0x4801F0` / `0x47F250` 与假设是否一致 | 锚点一致；原版混色语义 = **加性 tint**（非向灰、非 50% 减法）；现网已被桩替换 | [实证] | `results/asm_verify.json` 14/14 |
| Q5 | 单位可见性机制交叉核验 | 与 `unit_visibility_mechanism.md` 一致：灰雾档引擎无生效隐藏门（0x5865E0 stub）；可见性剔除只在 EnableUnitFog 三钩子；引擎灰雾层现网不可达（Scenario bit12 被清） | [实证] | 该文档 §F1/F2；本轮 asm 复核 0x480251 门 |
| Q6 | ZC-11 可执行最小判别实验 | 已给出 4 档 × 4 ROI × 判据阈值 + 机位不可复位替代方案（§F5） | [待实测] | 本文 §F5 |
| Q7 | DEF-FOGPARTIAL 静态根因候选 | 4 条候选 + 验证步骤（§F6）；H1 仍首选 | [推演]+[待实测] | `fog_partial_building_rootcause.md`；本文 §F6 |

---

## [2] 背景与继承口径

### 2.1 必须继承、不得无据推翻

| 继承结论 | 出处 | 本卡态度 |
|----------|------|----------|
| M1 向固定灰插值 / M3 乘性 k 非常数 2 参等价 | `fog_model_hypothesis.md` §3.3 | **复算确认**（最大预测差 0.000000） |
| 残差：M1 优 FOG/DIR/TOP，M4 优 BRIDGE | 同上 | **复算确认** |
| DIR/TOP 暗像素加雾后变亮 ⇒ 向灰混合强证据 | 同上 §3.4 | **复算确认**（方向 + 幅度） |
| 「50% 减法」是错误口径，已勘误 | `fog_switch_report.md` E1 | **接受**；本卡 asm 复核原版 = 加性 tint |
| VisibilityMode 双态 / 半透明黑总闸 / DEF-FOGPARTIAL 仍有问题 | `fog_visibility_mode_report.md` 等 | **接受**，不扩展定谳 |

### 2.2 α 约定（沿用 MIMO-FOGMODEL）

```
α(s) = 0.71875 × (1 − s/512)        # 0.71875 = 23/32 = s_fogFirstStageGainUpstream
s=256 (auto)     → α=0.359375
s=0   (T=71.875) → α=0.718750
s=85  (T=60)     → α=0.599426
```

注意语义：**s 越小 = α 越大 = 「向灰/雾效」越强**（T 越大越亮是「净保留比例」口径，见 `fog_strength_calibration.md`；两套口径并存，判别时以 s 为准）。

---

## [3] 模型对比与残差表（离线可复算）

### 3.1 输入数据 [实证]（ZC-9B `b3_valid_rungs.json`）

| s | T_label | α | FOG | DIR | TOP | BRIDGE |
|---|---------|---|-----|-----|-----|--------|
| 256 | auto | 0.359375 | 47.25 | 13.10 | 12.98 | 48.71 |
| 0 | 71.875 | 0.718750 | 56.44 | 45.21 | 43.57 | 38.21 |
| 85 | 60 | 0.599426 | 52.83 | 43.51 | 41.95 | 38.23 |

ROI（屏幕矩形，来自 RESULT_ZC9B）：FOG=雾中水面(80,200,280,330) · DIR=右暗水(680,150,880,300) · TOP=左上暗区(10,10,200,120) · BRIDGE=桥面(120,480,400,570)。

### 3.2 候选模型

| 模型 | 公式 | 参数 | 物理含义 |
|------|------|------|---------|
| **M0 常数 k 纯压暗** | `out = c·(1−s/512)`（k 隐含于 c） | 1 | 被否决的 `net=k(1-s/512)` |
| **M1 向固定灰** | `out = c + (g−c)·α` | c, g | 像素向灰色 g 线性插值 |
| **M3 乘性非常数** | `out = c·(1−β·α)` | c, β | 与 M1 **同一 2 参线性张成** |
| **M4 两段/二次** | `out = base·(1−α) + gray·α²` | base, gray | 非线性叠加 |

### 3.3 残差表（SS_res，越小越好）[实证·脚本输出]

| ROI | M0 | M1 | M3 | M4 | 最优 |
|-----|----|----|----|----|------|
| FOG | 289.94 | **0.20** | 0.20 | 1.85 | M1/M3 |
| DIR | 124.05 | **51.60** | 51.60 | 87.16 | M1/M3 |
| TOP | 109.00 | **46.82** | 46.82 | 79.35 | M1/M3 |
| BRIDGE | 709.09 | 7.72 | 7.72 | **3.91** | M4 |

逐点残差见 `results/residual_table.csv`（M1/M3 恒等，故只列一份差异说明）。

### 3.4 响应比表 —— 常数 k 的量化否决 [实证]

| ROI | out(256)/out(0) | out(85)/out(0) | 幅度% | 备注 |
|-----|-----------------|----------------|-------|------|
| FOG | 0.8372 | 0.9360 | 17.6 | |
| DIR | 0.2898 | 0.9624 | 94.6 | 暗像素，响应极大 |
| TOP | 0.2979 | 0.9628 | 93.2 | 同上 |
| BRIDGE | **1.2748** | 1.0005 | 25.2 | **反向**（s 更大反而更亮） |

常数 k 预测：所有 ROI 在 s=256 的比值应同为 0.5、s=85 同为 0.834。实测 0.29 ~ 1.275，**且 BRIDGE>1 使纯压暗在任何正 k 下不可能**。

### 3.5 「暗像素变亮」归因 [实证+推演]

| 检验 | 实测 | M0 | M1 | M3 | M4 |
|------|------|----|----|----|-----|
| DIR(s=0)−DIR(s=256) = +32.11 > 5 | 变亮 | **否**（只会同步变暗/变亮） | **是** | **是** | **是** |
| TOP(s=0)−TOP(s=256) = +30.59 > 5 | 变亮 | **否** | **是** | **是** | **是** |
| BRIDGE(s=256)−BRIDGE(s=0) = +10.50 > 0 | 反向 | **否**（比值恒定） | 是（g<c） | 是（β>0） | 是 |

> **判词**：「暗像素变亮」= 像素被拉向一个高于自身的中间灰；纯压暗只能把像素拉向 0，**不能**在暗端变亮、又在亮端（桥面）变暗。故继承结论「向灰混合强证据、常数 k 不成立」在本轮离线复算中**再次成立**。

### 3.6 拟合灰目标 g（M1）[推演]

| ROI | c | g | 备注 |
|-----|---|---|------|
| FOG | 38.06 | **63.30** | |
| DIR | −19.03 | **75.70** | c 为负 ⇒ 线性模型对暗端不完美 |
| TOP | −17.63 | **72.62** | 同上 |
| BRIDGE | 59.22 | 27.92 | 离群：g 显著低于其它 ROI |

- FOG/DIR/TOP 的 g 落在 **63–76**（中暗灰），与 FOG.SHP 不透明调色板索引 **66**（frame15 全 0x42）在数值上同量级 ⇒ **[推演]**「向雾色（索引 66≈luma 66）混合」是自然解释。
- BRIDGE 的 g=27.92 是离群点，恰是 M4 在 BRIDGE 更优的原因；若 ZC-11 补档后 g 仍双峰，则「全局统一灰」假设应降级为「随材质/纹理变化的雾色」。
- 跨 ROI `max(g)−min(g)=47.8`，**不满足** <10 的「单一全局灰」判据 ⇒ 当前数据下灰目标可能空间变化，或 DIR/TOP 线性模型欠拟合（c 为负是症状）。

### 3.7 FOG.SHP 侧约束 [实证]

脚本 `parse_fog_shp.py` 复算（与 MIMO-FOGMODEL 完全自洽）：

| 项 | 值 |
|----|----|
| 文件大小 / 布局 | 88712 B = 8 + 96×24 + 48×1800 ✓ |
| 数据帧 / 空帧 | 48 / 48 |
| 全局 0xFE 计数 / 最长游程 | 44,100 / 1,828 |
| 全局 0x42 最长游程 | 60 |
| Frame15 | **恰 900×0x42 + 900×0xFE** |
| 不透明雾值 | 调色板索引 **66 (0x42)**；透明 = 254 (0xFE) |

> 注：帧分类（gradient/mixed）阈值与 MIMO-FOGMODEL 略有差别（本脚本 5% 双阈值 ⇒ gradient 14 / mixed 33；原文 45/2）。**量化断言（frame15、计数、游程）逐项一致**，仅分类标签粒度不同，不影响结论。

### 3.8 代码侧张力（重要未闭环）

原版 B1（`0x47F42F`）：`lea ecx,[ecx+edx-0x7f]` ⇒ fog=66 时 **dest−61**（加性压暗）。
我方强度桩：`out = c − ⌊c/2⌋·s/256`（s=256 ⇒ 50%）。
两者都是**单调压暗**，都不产生「暗像素变亮」。

⇒ [推演] 实测向灰行为的来源不在 B1/B2 窗口，而在：
1. 未定位的「第一段 ×0.71875」（FOG-FIRSTSTAGE-R3 明示未定位；疑在地表 8→16 bit LightConvert / 光照表路径）；
2. 或调色板/光照表把「压暗」实现为「向表内某灰靠拢」；
3. 或 ROI 均值受渐变格 / FadeFogTransition 过渡态 / 机位残差污染（ZC-9B 已有镜头跳变前科）。

**ZC-11 必须同时做「同 s 不同 T」等价对 + 机位校验**，才能把 2/3 排除。

---

## [4] 反汇编核对（只读 gamemd.exe）

### 4.1 `CellClass::Draw_Shroud_And_Fog` 0x004801F0

| 锚点 | VA | 字节 | 含义 | 与假设 |
|------|-----|------|------|--------|
| 入口 | 0x4801F0 | `53 55 56 8B F1 8B 0D 24 73 88 00` | prologue | ✓ |
| 黑幕/雾瓦片层 | 0x480230 | `E8 AB ED FF FF` call 0x47EFE0 | 恒执行 | ✓ |
| FogOfWar 位门 | 0x480251 | `F6 C6 10 74 3F` test dh,0x10 / je | 位清则**不走** 0x47F250 | ✓ 与「现网引擎灰雾层不可达」一致 |
| Draw_Fog #1 | 0x480278 | `E8 D3 EF FF FF` | 仅位=1 可达 | ✓ |
| Draw_Fog #2 | 0x480290 | `E8 BB EF FF FF` | 同上 | ✓ |

> 交叉核验 `unit_visibility_mechanism.md` F2-7：DLL 每逻辑帧清 Scenario bit12 ⇒ 0x480251 恒不走 ⇒ 引擎自身半透明灰雾层现网不可达；玩家看到的灰雾全部是我方 FOG.SHP 图层。本卡 asm 复核与该结论**一致**。

### 4.2 `Draw_Fog` 0x0047F250 与混色桩 B1/B2

| 锚点 | VA | 字节 | 语义 |
|------|-----|------|------|
| 读雾字节 | 0x47F403 | `8A 1F 47 80 FB 7F` | `mov bl,[edi]; inc edi; cmp bl,0x7f` |
| 透明跳过 | 0x47F40D | `77` ja | 索引 >0x7F（含 0xFE）不混色 |
| B1 混色 | 0x47F42F | `8D 4C 11 81` | `lea ecx,[ecx+edx-0x7f]` ⇒ dest+fog−127 |
| B1 钳位 | 0x47F437 | `0F 9E C2 4A 23 CA` | 负值钳 0（全 exe 仅 2 处此签名） |
| B1 落点 | 0x47F43D | `66 89 08` | `mov [eax],cx` |
| B2 入口 | 0x47F4AE | `66 8B 08` | 第二循环（51 B 窗） |
| B2 签名 | 0x47F4D8 | `0F 9E C2 4A 23 CA` | 第 2 处 |
| 反证 | 窗 0x47F250–0x47F500 | **无** `and *,0x7BEF` | 0x7BEF 是我方 c50 掩码，不在原版 |

**语义判定**[实证]：原版 = FOG.SHP **调色板索引加性 tint**（fog=66 ⇒ −61）；透明索引跳过。**不是**向灰插值、**不是** 50% 减法（勘误 E1 的方向正确）。现网该窗口被强度桩替换，故「向灰」行为不得归因到本 opcode。

### 4.3 与 `unit_visibility_mechanism.md` 交叉核验

| 机制文档断言 | 本卡核对 | 结果 |
|--------------|----------|------|
| 灰雾档引擎无生效隐藏门（0x5865E0 = stub 恒假） | 本轮不重复验证 stub 本体（已有 [实证]）；但 0x480251 门复核通过 | 一致 |
| 黑幕档建筑/步兵 `xor edi,edi` 零光照（非跳过） | 与 DEF-FOGPARTIAL H1 同源 | 一致 |
| VisibilityMode / EnableUnitFog 三钩子独立 | 不在本轮 asm 范围；引用该文档 F1 | 继承 |
| 引擎灰雾层现网不可达 | 0x480251 + DLL 清位链复核 | 一致 |

---

## [5] ZC-11 可执行最小判别实验

### 5.1 目标

用 ≥4 个 s 档 + 固定 ROI，把 M1（向灰）与 M0（常数 k）与 M4（非线性）分开，并检验「单一全局灰」假设。

### 5.2 档位（4 档最小集）

| 档 | FogStrengthPct | 目标 s | α | 作用 |
|----|----------------|--------|---|------|
| **A** | auto | 256 | 0.359 | 基线 |
| **B** | 71.875 | 0 | 0.719 | 最大向灰 / 最小桩压暗 |
| **C** | 35.9375 | 256 | 0.359 | 与 A **同 s 不同 T** ⇒ 等价对（换算正确性） |
| **D** | 50 | 156 | 0.500 | 中间点，区分线性 vs 二次 |

> 现网注意：`FogStrengthPct` **只在 DLL init 读取**（`blitter_hooks.cpp` init 路径；ZC-9B 勘误）。改 ini 后必须**重开局**才生效；若存在运行期写 `g_fogStrengthScale256` 的通道，可同局多档，但必须用 2 秒遥测行 `[ra2render-telemetry-fogcal]` 双确认 s 回读值。

### 5.3 ROI 与采样点

| ROI | 位置（ZC-9B 已用） | 选点要求 |
|-----|-------------------|----------|
| FOG | 雾中水面 (80,200,280,330) | ≥40×40，避开建筑/单位 |
| DIR | 右暗水 (680,150,880,300) | 与 FOG **同材质**（水）以公平对比 |
| TOP | 左上暗区 (10,10,200,120) | 同材质，距 FOG ≥200px |
| BRIDGE | 桥面 (120,480,400,570) | 固定桥面中段 ≥30×30 |

每档采样：整 ROI meanLuma（0–255）+ 4 个**点探针**（ROI 四角内 3×3 均值），点探针用于对齐校验。

### 5.4 判据（可执行阈值）

| ID | 判据 | 阈值 | 指向 |
|----|------|------|------|
| D1 | M1 线性残差 | 每 ROI `SS_res < 5` | M1 向灰成立 |
| D2 | M1 线性残差 | 每 ROI `SS_res > 20` | 非线性，倾向 M4 / 需更复杂 |
| D3 | 桥面反常 | `pred(s=256) > pred(s=0)` 或实测同向 | 向灰**必要条件** |
| D4 | DIR 增亮 | `DIR(s=0) − DIR(s=256) > 15` | 暗端被拉亮 ⇒ 向灰**强证据** |
| D5 | 响应比一致性 | 4 ROI 的 `out(256)/out(0)` 极差 < 0.08 | 若成立则**推翻**向灰（回到常数 k）；预期**不成立** |
| D6 | 跨 ROI 灰一致 | `max(g)−min(g) < 10` | 全局统一灰；否则空间变化雾色 |
| D7 | 等价对 | A vs C 同 s：ROI 均值差 < 1.0 | 换算路径无偏；否则 T→s 公式有问题 |

**汇总判决**：
- D1 成立 + D3/D4 成立 + D5 不成立 ⇒ **M1 向灰混合定谳候选**（仍需 4 档独立复现）
- D2 成立 + D3/D4 成立 ⇒ 非线性，M4 或两段复合；记录 SS 比
- D4 不成立且 D5 成立 ⇒ 回退常数 k（与继承结论冲突，需**书面举证**才可改口）
- D7 不成立 ⇒ 先修换算，本组数据作废

### 5.5 机位确定性

**首选（同局多档）**：同一局、不移动镜头，只切 s（运行期全局或热改+重载），每档间隔 ≥3s（等 FadeFogTransition 收敛）后截图。

**A4 机位不可复位时的替代（ZC-9B 教训：点小地图复位不可靠）**：

1. **重开局 + 固定走位脚本**：每档新开局，同一张图、同一开局脚本（固定建造/移动序列），用键盘/脚本把镜头定到同一世界坐标（禁止点小地图）；每档延迟固定 N 秒截图。
2. **机位校验（硬门槛）**：对每档的 `b*_camera_ref.png`（无雾直视区 200×200 裁剪）做两两互相关 / MAD；**MAD ≤ 2.0**（16-bit 索引域）或互相关 ≥ 0.99 才收；否则该档作废重采。
3. **点探针锁**：4 个点探针在直视区的取值跨档必须相同（±1）；不同即机位漂移。
4. 排除 UI：`tools/bench_diff.py --exclude-sidebar --exclude-radar` 或自设掩码。
5. 遥测粘贴：每档 2 秒遥测行原文（`[ra2render-telemetry-fogcal]` 的 s 回读值 + 半透明层绘制次数）。

### 5.6 计算脚本（已就绪）

```powershell
# 采集后把 4 档 ROI 均值填入 measurements.json
python out\re_work\mimo_fogmodel\design\discriminate.py --input measurements.json
python out\re_work\fog_offline_verify\fit_and_compare.py   # 或扩展为读入 json
```

---

## [6] DEF-FOGPARTIAL 静态根因候选与验证步骤

### 6.1 现象定义（问题仍在）

「灰雾区（已探索非直视）敌方建筑只画出一半」——用户截图报告 + ZC-9B A4 对**该张截图**判定为「感知特征（深色 sprite）虚警」（对象中心格雾面命中 0.00%），但**现象类别本身未关闭**：多格建筑在雾界附近的视觉「半截」仍有 4 条可检验候选。

### 6.2 候选排序

| ID | 候选 | 机制一句话 | 静态支持 | 级别 |
|----|------|-----------|----------|------|
| **H1** | 引擎中心格 shroud ⇒ 整栋零光照画黑 | `BuildingClass::Draw` 只采**中心格** `IsShrouded`，shrouded 则 `xor edi,edi`（打包 RGB 光照色清零）+ 核心内 `0x7063E0 xor eax,eax` 二次清零；**不跳过绘制** ⇒ 整栋近黑 + 透明孔洞透地形 = 「像没画完/半截」 | [实证] 字节（`fog_partial_building_rootcause.md` E-1） | **首选** |
| **H2** | 建筑附属 Anim 不受 EnableBuildingFog 约束 | 主体走 v[69] 钩子（可整栋剔除）；雷达/烟雾/叶片等 `AnimClass::Draw` **未挂钩** ⇒ 主体被剔除时附属仍画，或主体画一半感（附属悬浮） | [实证] 钩子范围；`building_fog_residual_deep_dive.md` | **P1** |
| **H3** | 三粒度判定不一致 | `ShouldDrawBuilding` 取**锚格**、`everSeen` 盖章按**整个地基**、引擎取**中心格** ⇒ 雾界切过多格建筑时不同步，可出现「一部分该剔除/一部分该画」的感知 | [推演] 粒度已实证，表现待测 | **P1** |
| **H4** | FadeFogTransition 逐格 4 帧过渡 | 按格去重的明暗过渡，边界量化 60×30 px；多格建筑过渡中呈「半亮半暗」 | [实证] 机制；瞬态 | **P2** |
| **H5** | L4 脏矩形部分重绘 | 本构建 `0x006D3D99` 已打成**无条件全量重绘**，`L4DirtyMode` 不存在 | [实证] 否决 | **排除** |
> 【W3 勘误 · W3-A6/ISSUE-STALE-L4-EXIST】改前：L4DirtyMode` 不存在；改后：L4DirtyMode 已在 blitter_hooks.cpp:757 读取并支持 force-full / vision-dirty 模式；三处 ini 均已配置出厂值。；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251; ra2youli/ra2render.ini:186; ra2bench/ra2render.ini:186；分级：P1

### 6.3 验证步骤（可执行）

| 步 | 动作 | 判据 | 指向 |
|----|------|------|------|
| V1 | 复现镜头：灰雾区放**同型号**建筑 A（跨雾界）+ 直视区同型号 B；截图 | A 整栋黑/缺 vs B 彩色 | H1：A 全黑含孔洞马赛克 |
| V2 | `EnableBuildingFog` 1→0（A1/A2 对） | 剔除计数归零；若「附属雷达/烟雾仍可见而主体无」⇒ H2 | H2 |
| V3 | 把 A 推入直视圈再推回，连续截图 8 帧 | 若「半截」只在过渡 4 帧内出现 ⇒ H4 | H4 |
| V4 | 存档回放同机位，逐格打印 `IsShrouded` / 锚格 / 地基 everSeen | 三者不一致的格子集合与「缺半边」空间重合 ⇒ H3 | H3 |
| V5 | 只读断点 `0x43D539`（IsShrouded）与 `0x7063E0`，记录返回值与 edi | 若 shrouded=1 且 edi=0 且仍进派发表 ⇒ H1 字节级闭环 | H1 |

> 纪律：V1–V5 只观察、只读内存；不改 IsShrouded / 0x5865E0 判定（红线：禁开图）。

---

## [7] 与单位可见性机制的交叉核验结论

| 项 | 结论 | 影响 |
|----|------|------|
| 灰雾区敌方**单位**「靠近才显现」 | **我方 EnableUnitFog 剔除**，与引擎无关（0x5865E0 stub 恒假） | ZC-11 不必测引擎隐藏；测单位可见性只改 EnableUnitFog |
| 引擎灰雾层（半透明） | 现网**不可达**（Scenario bit12 每帧清） | 观测到的灰雾 = 我方 FOG.SHP 层；混色性质以我方桩+未定位第一段为准 |
| 黑幕（未探索） | 引擎原生绘制；建筑/步兵零光照；Unit/Aircraft 无黑幕分支（负向） | DEF-FOGPARTIAL H1 只在黑幕/光照路径，不在灰雾混色路径 |
| 半透明黑总闸 EnableStarCraftFog | 关闸 ⇒ 不画我方雾层、不混色、不落回 50% | 判别实验必须**开闸**，否则无雾可测 |
| VisibilityMode 双态 | 与混色模型正交 | ZC-11 固定一种模式，不混测 |

---

## [8] 未闭环清单

| ID | 缺口 | 为何离线不能闭环 | 下一步 | 级别 |
|----|------|------------------|--------|------|
| FM-1 | DIR/TOP SS~50：α 线性欠拟合 | 仅 3 档 + 可能机位/渐变污染 | ZC-11 四档 + 机位校验 | **P0** |
| FM-2 | 灰目标 g 跨 ROI 散布 47.8（BRIDGE 离群） | 需更多材质 ROI | ZC-11 D6；或按 FOG.SHP 帧色分层 | P1 |
| FM-3 | 「向灰」代码站点未定位 | 第一段 ×0.71875 / LightConvert 未静态定位 | 断点 `0x47F40F` 读 [eax] 前后 + `0x547CF0` Tile blitter（FOG-FIRSTSTAGE-R3 建议） | **P0** |
| FM-4 | 原版加性 tint（dest−61）与「向灰」的关系 | 现网已替换，无法 A/B | 总闸关/开 + 短路桩回退实验（需真机、需门控） | P2 |
| FM-5 | DEF-FOGPARTIAL 现象类别 | 单张截图只否证了个案 | V1–V5 | **P0** |
| FM-6 | 48 空帧（offset=0）运行期用途 | 静态无引用语义 | 可选 | P2 |

---

## [9] §九台账草稿（供 Lead 裁决，本卡不改台账）

```
[v1.8.x]  FOG-GRAYMIX-OFFLINE 离线验证纪要（草稿，待并入台账）

状态：离线完成，非定谳；等 ZC-11 真机四档。

1. 否决（量化）：`net = k×(1−s/512)` 常数 k 纯压暗。
   依据：4 ROI 响应比 0.290/0.298/0.837/1.275（BRIDGE>1 反向），常数 k 预测恒 0.5。
   产物：out/re_work/fog_offline_verify/results/ratio_table.csv

2. 支持（维持继承）：向灰混合（M1）解释「暗像素变亮 + 桥面反向」；
   M1 与 M3 数学等价；M1 优 FOG/DIR/TOP，M4 优 BRIDGE。
   产物：results/residual_table.csv , model_compare.json

3. 澄清（勘误强化）：原版 B1/B2 = FOG.SHP 索引加性 tint（fog=66 ⇒ dest−61），
   不是 50% 减法、不是向灰插值。现网已被强度桩替换；
   实测向灰行为来源不在 B1/B2 窗口（第一段 ×0.71875 仍未定位，P0）。
   产物：results/asm_verify.json 14/14

4. FOG.SHP 量化断言再次自洽（frame15=900×0x42+900×0xFE 等 8 条）。
   可对 [v1.8.36]「保留（P2）」条目做二次订正 —— 由 Lead 决定。

5. DEF-FOGPARTIAL 不关闭：H1 首选 + H2/H3/H4 候选；验证步骤 V1–V5 见
   docs/re/fog_gray_mix_offline_verify.md §F6。

6. ZC-11 判别协议已给（4 档 / 4 ROI / D1–D7 阈值 / 机位替代）：
   重开局+固定走位，MAD≤2.0 或点探针锁；A/C 同 s 等价对。
```

---

## [10] 写作用域与红线

* **新增（唯一写入）**：`docs/re/fog_gray_mix_offline_verify.md`（本文）、`out/re_work/fog_offline_verify/**`（README.md、parse_fog_shp.py、fit_and_compare.py、verify_asm_fog_paths.py、data/b3_valid_rungs.json、results/*）。
* **未触碰**：`ra2render/**`、`ra2youli/**`（gamemd.exe 仅只读打开）、`REVERSE_ENGINEERING_AND_PATCHES.md`、既有 `docs/re/fog_*.md` / `unit_visibility_mechanism.md` / `layer_order_fog_vs_objects.md`（只读引用）、台账、任何二进制。
* **未启动游戏 / 未注入 / 未改任何字节**。
* 离线拟合**不当定谳**；真机判据见 §F5。

---

## [11] 交付物与复算入口

| 路径 | 内容 |
|------|------|
| `out/re_work/fog_offline_verify/parse_fog_shp.py` | FOG.SHP 帧表 + 统计 |
| `out/re_work/fog_offline_verify/fit_and_compare.py` | M0/M1/M3/M4 残差 + 方向判别 |
| `out/re_work/fog_offline_verify/verify_asm_fog_paths.py` | 0x4801F0 / 0x47F250 字节锚点 |
| `out/re_work/fog_offline_verify/results/shp_report.json` | 帧表报告 |
| `out/re_work/fog_offline_verify/results/residual_table.csv` | 逐点残差 |
| `out/re_work/fog_offline_verify/results/ratio_table.csv` | 响应比（常数 k 否决） |
| `out/re_work/fog_offline_verify/results/model_compare.json` | 汇总裁决 |
| `out/re_work/fog_offline_verify/results/asm_verify.json` | 14/14 锚点 |
| `out/re_work/fog_offline_verify/data/b3_valid_rungs.json` | 继承实测输入副本 |

**复算**：`python out\re_work\fog_offline_verify\parse_fog_shp.py && python out\re_work\fog_offline_verify\verify_asm_fog_paths.py && python out\re_work\fog_offline_verify\fit_and_compare.py`
