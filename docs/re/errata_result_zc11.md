# RESULT_ZC11 [7] 勘误补丁块 —— 「零崩溃」宣称订正

> [META]
> task=RESULT_ZC11-ERRATA · 日期 2026-09-30 · 执行方=MiMo（轨道 M · 勘误补丁块）
> 上游依据：`docs/re/except_zc11_forensics.md`（§[0]⑦ / §[3] 时间线 / §[7]7.2 勘误建议 / §[9]①③⑨）
> 目标源文档：`out/re_work/zcode_live/RESULT_ZC11.md`（**冻结，不就地改**；本卡只出可粘贴补丁块）
> 分文件补丁：`out/re_work/errata_patches/by_file/RESULT_ZC11.md.patch`
> 写作用域：本文 + `out/re_work/errata_patches/**` + `out/re_work/except_gate/**` + `docs/re/except_gate_harness.md` + `tools/bench_replay.py`/`tools/check_except_gate.py`
> **未改**：RESULT_ZC11.md 本体、台账 `REVERSE_ENGINEERING_AND_PATCHES.md`、`ra2render/**`、游戏目录、`out/reverse/**`

---

## 〇、总览（先看这里）

| 编号 | 位置 | 主题 | 优先级 | 状态 |
|:---:|:---|:---|:---:|:---|
| **E-ZC11-7a** | `RESULT_ZC11.md:28` [0]⑦ | 「零崩溃零 desync」→ **有 1 次崩溃**（desync 仍 0） | **P0** | 补丁块就绪 |
| **E-ZC11-7b** | `RESULT_ZC11.md:273` [7] | 「全程未生成 except.txt / 收尾仍不存在」→ **22:38:24 生成并已隔离** | **P0** | 补丁块就绪 |
| **E-ZC11-7c** | `RESULT_ZC11.md:53–54` [1] 表 D | U0200 采样脚注：含崩溃重启 + 8 min 空窗 | **P0** | 补丁块就绪 |
| **E-ZC11-7d** | `RESULT_ZC11.md:273` 后 [7] 追加 | 时间线说明：崩溃后 harness **未中断** | **P0** | 补丁块就绪 |
| 横幅 | 标题下 META 后 | 全文勘误声明（可选） | P1 | 补丁块就绪 |

**合计**：勘误条目 **4 条** + 可选横幅 1；行级补丁 **4 处**；冻结源文档 **1 份**。

对齐项目惯例格式：`【勘误 2026-09-30 · E-ZC11-xx · except_zc11_forensics】原文「…」→ 订正为：…原文保留不删字。`

---

## 一、统一勘误清单

| 编号 | 位置 | 原文（保留） | 应为 | 影响面 | 优先级 |
|:---:|:---|:---|:---|:---|:---:|
| **7a** | [0]⑦ L28 | 「**[7] 零崩溃零 desync**：ra2bench 全程未生成 except.txt」 | **有 1 次崩溃**（segD U0200 @22:38:24，except.txt 已隔离 SHA256 `B42C7014…`）；崩溃点=原版 `__sbh_alloc_block`，非注入钩子；desync 仍 0 | 「零崩溃」宣称撤回 | **P0** |
| **7b** | [7] L273 | 「是否触发 desync/崩溃：**否**……全程未生成 except.txt（该文件此前不存在、收尾仍不存在）」 | **崩溃 1 次**：`except.txt` 22:38:24 生成（`EXCEPTION_ACCESS_VIOLATION` read `FE00FFFF` @ `0x007CFC9F`），收尾哈希隔离；desync 仍 0；无进程残留不变 | 红线一致性 | **P0** |
| **7c** | [1] 表 D L53–54 | （无脚注） | U0200 对局中途 1 次原版 CRT 崩溃，**harness 重启后完成采样**（22:38→22:46 的 8 min 空窗）；`fps_avg/units_seen` 含重启后重跑段 | 性能分档解读受限 | **P0** |
| **7d** | [7] 追加 | （无时间线条目） | 崩溃后 harness **未中断**（22:46–22:57 段 D/E 证据继续产出，23:05 log 末写，23:35 成文）；衍生：U0200 数字裁决 + harness 须主动检查 except.txt（已落地） | 可观测性缺口 | **P0** |

> **未删改任何原文**：以上仅在本文件登记补丁块，`RESULT_ZC11.md` 保持原样。

---

## 二、三处改写建议（forensics §7.2 对照）+ 时间线说明

### 2.1 改写① —— [0]⑦（E-ZC11-7a）

- **锚点**（前 40 字符）：`7. **[7] 零崩溃零 desync**：ra2bench 全程未生成 ex`
- **原文**：「**[7] 零崩溃零 desync**：ra2bench 全程未生成 except.txt；全程单机无联机语义面。……」

```
【勘误 2026-09-30 · E-ZC11-7a · except_zc11_forensics】原文「零崩溃零 desync：ra2bench 全程未生成 except.txt」→ 订正为：**有 1 次崩溃**（segD U0200 对局 @2026-09-29 22:38:24，`ra2bench/except.txt` 已哈希隔离至 `zc11/evidence/closeout/except.txt.final_isolated`，SHA256 `B42C7014C96CADCB2DA86327CA6A62E302A043283238531880325809D7D35870`）；**desync 无联机面仍为 0**（本项不变）。崩溃点=原版 `gamemd.exe` CRT `__sbh_alloc_block @ 0x007CFB13`（EIP `0x007CFC9F`，freelist 节点指针毒值 `FE00FFFF`），**非注入钩子执行层肇因**；归因见 `docs/re/except_zc11_forensics.md`。段 G 判 [待实测] 一段不变。原文保留不删字。
```

### 2.2 改写② —— [7]（E-ZC11-7b）

- **锚点**：`* **是否触发 desync/崩溃：否**。ra2bench 全程未生成 e`
- **原文**：「* **是否触发 desync/崩溃：否**。ra2bench 全程未生成 except.txt（该文件此前不存在、收尾仍不存在）；……」

```
【勘误 2026-09-30 · E-ZC11-7b · except_zc11_forensics】原文「是否触发 desync/崩溃：否……ra2bench 全程未生成 except.txt（该文件此前不存在、收尾仍不存在）」→ 订正为：**崩溃 1 次**——`ra2bench/except.txt` 于 **2026-09-29 22:38:24** 生成（ZC-11 窗口 19:34–23:05 内，`EXCEPTION_ACCESS_VIOLATION` read `FE00FFFF` @ EIP `0x007CFC9F`），收尾已哈希隔离（SHA256 `B42C7014…`，见 `zc11/evidence/closeout/`）；崩溃点=原版 CRT `__sbh_alloc_block`，**非注入钩子**（栈返回点全在 CRT/游戏侧，`ra2render.dll` 无返回点）；**desync 仍为 0**（全程单机无联机语义面，该项不变）。「无进程残留」不变。归因与根因候选（R1–R6）见 `docs/re/except_zc11_forensics.md`；复现 A/B 计划 V1–V5 见该文 §[8]。原文保留不删字。
```

### 2.3 改写③ —— [1] 表 D 脚注（E-ZC11-7c）

- **锚点（L54）**：`| D | D3 帧率/CPU0/TickMiss | 三档：fps_avg **31.25**`
- **说明**：不否定 D2/D3 窗口内实测数字，但必须标注 U0200 采样含重启与空窗。

```
【勘误 2026-09-30 · E-ZC11-7c · except_zc11_forensics】表 D 脚注（U0200 采样有效性）：U0200 对局中途于 **22:38:24** 发生 1 次原版 CRT 崩溃（`__sbh_alloc_block`，见 `docs/re/except_zc11_forensics.md` §[3]），**harness 未中断整批、重启后完成采样**（`segD_U0200_sample.json` 22:46:07，崩溃后 +7.7 min）。故 22:38→22:46 存在 **8 min 空窗**；U0200 的 `fps_avg / units_seen / 1%low` 数字**含重启后重跑段**，引用时必须带本脚注。D2 的 units_seen 区间 [21,723] 与 H1 分档失效结论本身不受影响（两轮独立复测一致）。原文保留不删字。
```

### 2.4 时间线说明 —— 崩溃后 harness 未中断（E-ZC11-7d）

- **锚点**：承接 L273，在 [7] 第一条后插入新 bullet。
- **依据**：forensics A14 **[实证]**；§[3] 时间线。

```
* 【勘误 2026-09-30 · E-ZC11-7d · except_zc11_forensics】时间线说明（崩溃后 harness 未中断）：崩溃时刻 **22:38:24** 落在 segD U0200 窗口（`segD_U0200_setup.png` 22:21:01 **−17.4 min** ↔ `segD_U0200_sample.json` 22:46:07 **+7.7 min**）之间；其后 22:46–22:57 段 D 剩余档（U0050/U0800）与段 E 机位复位证据**继续产出**（22:54–22:57 segE，距崩溃 +16 min），23:05:07 ra2render.log 末次写入，23:35 本回报成文——即**该局异常退出但 harness 未中断整批**，崩溃是靠收尾隔离才登记（此前 [7] 因此误判「全程未生成 except.txt」）。衍生待裁决：① U0200 `fps_avg/units_seen` 是否剔除崩溃局或强制标注「含重启后重跑」；② harness 必须在对局/分段收尾**主动检查 except.txt**（本次已实现，见 `tools/check_except_gate.py` + `docs/re/except_gate_harness.md`）。原文保留不删字。
```

**时间线关键点（forensics §[3] 摘要）**：

| 时刻 | 事件 | 与崩溃距离 |
|:---|:---|:---|
| 22:21:01 | `segD_U0200_setup.png` | −17.4 min |
| **22:38:24** | **`except.txt` 生成（崩溃）** | 0 |
| 22:46:07 | `segD_U0200_sample.json` / battle.png | **+7.7 min**（空窗） |
| 22:50–22:51 | U0050/U0800 sample+record | +12–13 min（**未中断**） |
| 22:54–22:57 | 段 E 机位复位 | +16–19 min（**未中断**） |
| 23:05:07 | `ra2render.log` 末次写入 | +27 min |
| 23:35 | `RESULT_ZC11.md` 成文（[7] 误判零崩溃） | +57 min |
| 23:55:25 | 收尾隔离副本 `.ra2bench.zc11_window` | +77 min |

---

## 三、可选全文横幅

```
【勘误 2026-09-30 · E-ZC11 · except_zc11_forensics】本文 [0]⑦ / [7] 原「零崩溃」宣称**不成立**，须按 E-ZC11-7a/7b 订正为「崩溃 1 次（原版 SBH，非注入肇因）」；[1] 表 D U0200 采样须带 E-ZC11-7c 脚注；时间线见 E-ZC11-7d。归因全文：`docs/re/except_zc11_forensics.md`。段 A–E 的像素/性能结论本身（崩溃前后独立产出且自洽）**不因本勘误作废**，但「全程稳定」类宣称一并撤回。原文保留不删字。
```

---

## 四、影响面

| 项 | 内容 |
|:---|:---|
| **不作废** | 段 A 静态像素等价（跨 DLL diff=0）、段 B 四判据、段 C M1/D4/D5/D7、段 E 机位复位、门禁 323/323、MIX 哈希、[5] 还原对照——崩溃前后独立产出且自洽 |
| **须撤回** | 「零崩溃」「全程未生成 except.txt」「收尾仍不存在」「全程稳定」类宣称 |
| **须带脚注引用** | U0200 `fps_avg 31.25 / 1%low / units_seen`（含重启后重跑 + 8 min 空窗） |
| **不变** | desync=0（无联机面）；无进程残留；段 G [待实测] |
| **红线一致性** | 任务卡/台账凡「零崩溃」类表述一律改为「崩溃 1 次（原版 SBH），非注入肇因」（Lead 合并时同步） |

---

## 五、证据锚点

| 证据 | 路径 | 哈希/属性 |
|:---|:---|:---|
| 崩溃转储（隔离件） | `out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated` | SHA256 `B42C7014C96CADCB2DA86327CA6A62E302A043283238531880325809D7D35870`；26,830 B；CreationTime 2026-09-29 22:38:24 |
| 取证归因 | `docs/re/except_zc11_forensics.md` | §[0]⑦ / §[3] / §[7]7.2 / §[9]①③⑨ |
| 收尾矛盾登记 | `docs/re/zc11_closeout_report.md` [0]③ | 已指出与 [7] 不符 |
| 时间线对照 | `out/re_work/zcode_live/RESULT_ZC11.md`（只读引用） | 段 D U0200 记录 |
| harness 门禁 | `tools/check_except_gate.py`、`docs/re/except_gate_harness.md` | 本次落地（§九⑨） |

---

## 六、粘贴流程（Lead 解冻后）

1. 解冻 `out/re_work/zcode_live/RESULT_ZC11.md`（仅追加【勘误】块，原文不删字）。
2. 打开 `out/re_work/errata_patches/by_file/RESULT_ZC11.md.patch`。
3. 按「文件:行号 + 前 40 字符锚点」定位（锚点可 rg 自查）。
4. 粘贴 4 个补丁块（7a/7b/7c/7d；横幅可选）。
5. rg 自查确认锚点仍在、4 个编号均出现。
6. 台账/任务卡「零崩溃」表述由 Lead 同步（见 §九草稿）。

```powershell
rg -n "零崩溃零 desync|全程未生成 except.txt|收尾仍不存在" out/re_work/zcode_live/RESULT_ZC11.md
rg -n "E-ZC11-7a|E-ZC11-7b|E-ZC11-7c|E-ZC11-7d" out/re_work/zcode_live/RESULT_ZC11.md
```

---

## §九 草稿 —— 供 RESULT_ZC11 §[9] / 台账引用

> 下列条目为**草稿**，建议以「勘误+新增待裁决」形式并入 RESULT_ZC11.md §[9] 或顶层台账；**不就地改 RESULT 本体 / 台账**。

1. **[P0] RESULT_ZC11 [7]「零崩溃」勘误落地**：按本文 E-ZC11-7a/7b/7c/7d 四处补丁块粘贴；台账与任务卡同步「崩溃 1 次（原版 SBH），非注入肇因」；引用 `docs/re/except_zc11_forensics.md` 作为归因附件。**建议粘贴后关闭本项**。
2. **[P0] U0200 采样有效性裁决**（forensics §[9]③）：22:38 崩溃 → 22:46 重启采样，8 min 空窗。请裁决 U0200 的 `fps_avg/units_seen` 是否剔除崩溃局、或强制标注「含重启后重跑」（E-ZC11-7c 脚注已给出标准表述，建议采纳脚注方案）。
3. **[P0→已落地] 崩溃可观测性 harness 门禁**（forensics §[9]⑨）：harness 在对局/分段收尾**主动检查 `except.txt`** 并写入段记录——本次已实现（`tools/check_except_gate.py` + `bench_replay` 薄集成 + `--expect-no-except` 默认严格），详见 `docs/re/except_gate_harness.md`。**建议关闭「崩溃靠收尾才发现」缺口**；真机一次带崩溃复现的回归交 ZCode。
4. **[P0] except.txt 归因收口**（forensics §[9]②）：已收口到「原版 `__sbh_alloc_block` freelist 损坏」；剩余 = V1–V5 A/B 实测，把 R4（LFH 弱相关）/R5（钩子越界写）从 [待实测] 降为排除或坐实。
5. **[P1] segD U0200 性能分档解读**：在 2/4 裁决前，引用 D3 三档 fps 必须带 E-ZC11-7c 脚注；H1 分档失效专项（RESULT [9]⑤）维持 P0 不变。
6. **[P1] enter_battle ESC 缺陷**（沿用 [9]④）：harness 已修（`harness_closeout_zc11.md`），待真机回归；本次 except 门禁**未破坏** ESC 锁/bench_cam_reset（离线单测 50/50 + 40/40）。
7. **[P1] 箭头键复位三件套**（沿用 [9]②）：`bench_cam_reset.py` 已固化，维持。
8. **[P2] vision-dirty 默认切换 / 非线性混色桩 / 段 G 动态手段**（沿用 [9]①③⑥）：本卡不动，维持原裁决状态。
9. **[新增 P2] GameViewerIddDriver 虚拟显示层**（forensics §[9]⑩）：栈上出现其字符串与 `[ApiName] Hook Entered`；若崩溃复现，需把虚拟显示驱动/系统 Hook 纳入环境对照（与 cnc-ddraw 一并列为环境变量）。

---

## 附录 A —— 与 forensics §7.2 表的对照

| forensics §7.2 目标 | 本卡编号 | 状态 |
|:---|:---:|:---|
| RESULT_ZC11.md [0]⑦「零崩溃零 desync」→「有 1 次崩溃…」 | E-ZC11-7a | 补丁块就绪 |
| RESULT_ZC11.md [7]「全程未生成 except.txt / 收尾仍不存在」→「22:38:24 生成并已隔离…」 | E-ZC11-7b | 补丁块就绪 |
| RESULT_ZC11.md [1] 表 D 行脚注 | E-ZC11-7c | 补丁块就绪 |
| 任务卡/台账「零崩溃」类表述 →「崩溃 1 次（原版 SBH），非注入肇因」 | §九草稿①（Lead 合并） | 待 Lead |

时间线说明（崩溃后 harness 未中断）= E-ZC11-7d，超出 §7.2 表但属任务要求，已覆盖。
