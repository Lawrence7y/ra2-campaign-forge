# A3 · `ra2render.dll` Inline Hook 对历史数据的污染普查

> **来源**：W4 两卡（`sections/card_00A8EC34.md` §6.2、`sections/card_00B0CE88.md` §6）
> 新发现 `ra2render.dll` 在 `0x6F8DF0`（`Greatest_Threat`）起 **9 字节 Inline Hook**，
> 跳板内按 `interval`（默认 8）节流，**被节流时整次跳过 `0x6F8E04/0x6F8E09` 的自增**。
> 这直接威胁「`0x00A8EC34` = 索敌入口调用累计」这条语义在历史趟件上是否成立。
>
> **本文回答**：历史 87 个 25 s 窗所在趟，是否有该 Hook 在场的证据。
> 只读既有 JSON/文本。**零真机、零采样实现、零母本改动。**

## 0. 一句话结论

**87 个 25 s 窗中，84 窗有干净的 S-4 证据（0 命中），3 窗证据不完整，0 窗命中。**
`qc151_fields.json` 的 `LAUNCH / exe_basename` 记录 **71 趟全部是 `gamemd.exe` 直启**，
且同文件 `LAUNCH` 组明写「**直启载体 gamemd.exe；绝不经 ra2loader.exe**」。
⇒ **历史窗的 `0x6F8DF0` 序言字节未被运行期改写**，W4 卡的静态字节证据对这批窗成立。

★ **但这不等于「历史 measure 数据里已有该字段的读数」**——既有 harness **从未读**这四个 VA
（`card_00A8EC34.md` §4 已核）；本文只回答「若将来采，历史窗的镜像前提是否被污染」。

## 1. 实跑命令与输出

```bash
python -I -X utf8 ".../A3_S4_INJECTION_CENSUS/_a3_s4_census3.py"
```
`EXIT=0`，原文 `_out3.txt`（前两版 `_out.txt` / `_out2.txt` 保留，见 §4 的自我订正）。

## 2. 三处证据合并后的分类（93 个趟目录）

| 分类 | 趟数 | 含义 |
|---|---|---|
| **clean** | **65** | S-4 证据在场且 0 命中 |
| **hit** | **0** | 命中 `ra2render` / `ra2loader` |
| **incomplete** | 5 | 模块表缺 `gamemd.exe`（只有 wow64 链）⇒ 身份不可判 |
| **enum_failed** | 2 | 模块表原文写「枚举失败，不能判定」 |
| NO_S4_EVIDENCE | 21 | 非趟目录（`ct`、`evidence`、`_src_*`、`.mimosa` 等）+ `archive_T17` |

**证据来源分布**：`s4_module_table.txt` **55** 趟、`qc151_fields.json` 的 `group=S4` **17** 趟、无 **21**。
★ 关键：`archive_*` 系列的 S-4 结论**不在** `s4_module_table.txt` 里，
而是以 `group=S4 / key=ra2render_hits / value=[]` 的 rec 行写进 `qc151_fields.json`
（`note` 逐字为「★ 空列表 = 0 命中」）。**第一版普查正是漏了这一点**（见 §4）。

## 3. ★ 87 个 25 s 窗的归属

| 分类 | 窗数 | 占比 |
|---|---|---|
| **clean** | **84** | 96.6% |
| **incomplete** | 3 | 3.4% |
| enum_failed / hit | 0 | 0% |

**3 个不完整窗**（模块表只有 wow64 链、无 `gamemd.exe`）：
`l3_1101v4e`（1 窗）、`l3_1101v4h`（1 窗）、`l1_20261023k`（1 窗）
—— 这 3 趟**不能断言**进程身份，**其窗属「不可判」**，不得当作干净窗引用。

**LAUNCH 记录**：71 趟有 `exe_basename` 记录，**全部 = `gamemd.exe`**，无一为 `ra2loader.exe`。

## 4. ★ 我自己的两次普查错误（如实记账）

| 版本 | 错误 | 后果 | 发现方式 |
|---|---|---|---|
| 第一版 `_out.txt` | 把「无 `s4_module_table.txt`」直接当成「无命中」 | 报「55 表 / 0 命中」，**漏掉 17 趟 `qc151_fields.json` 里的 S4 证据**，也没识别 2 张「枚举失败」表 | 看到 `archive_T*` 的 MANIFEST 里有 `ra2loader.exe`/`ra2render.dll` 文件条目，起了疑 |
| 第二版 `_out2.txt` | 已区分 `enum_failed`/`incomplete`，但仍只读 `s4_module_table.txt` | 报「71/87 窗干净、42 窗无 S-4 表」——**把 17 趟有证据的趟误判成无证据** | 在 `archive_T32/qc151_fields.json` 里搜到 `group=S4` 行 |
| 第三版 `_out3.txt`（**现行**） | 三处证据合并 + 区分「非趟目录」 | 84/87 干净 | — |

★ **这两次都是我把「查不到」当成了「没有」**——正是纪律第四条的反面教材。
第三版把「枚举失败」「缺 gamemd」「无证据」三种都单列，**不并入 clean**。

## 5. Hook 的静态事实（采信 W4 卡，我未重反汇编）

| 项 | 内容 | 出处 |
|---|---|---|
| 改写点 | `0x6F8DF0` 起 9 字节，原 `83 EC 5C 8B 15 34 EC A8 00` → `E9 <rel32> 90 90 90 90` | `card_00A8EC34.md` §6.2 引 `blitter_hooks.cpp:1406-1416`、原字节见 `:1341-1344` |
| 跳板 | `s_greatestThreatTrampoline` 先重放 9 字节再 `jmp` 回 `0x6F8DF9` | 同上 `:1393-1399` |
| 抑制条件 | `interval > 1 && currentFrame > 0 && ((unitHash + currentFrame) % interval) != 0` ⇒ `throttledTargetScans++` 且 `return pTarget`（不调跳板） | 同上 `:1362-1366` |
| `interval` 默认 | **8** | `ra2render.ini:22-25`；`blitter_hooks.cpp:547` |
| 安装时机 | `DllMain(DLL_PROCESS_ATTACH)` → `InstallVTableHooks()` →（无条件）`InstallGreatestThreatHook()` | `dllmain.cpp:25-31`；`blitter_hooks.cpp:3781-3782` |

⇒ **若该 DLL 在场且 `GameSpeed` 条件满足，`0x00A8EC34` 最多只统计 1/8 的入口调用。**
这会**没有预警地**把一个「调用累计」变成「节流后调用累计」——W4 卡判其「需补证」是对的。

## 6. 边界与未验（**不要把本文当免检**）

1. **我未验**：这 84 个干净窗在**运行时刻**的模块表是否真等于落盘表（表是**某一瞬**的枚举，
   DLL 可在枚举之后才加载）。`card_00A8EC34.md` §6.2 也明确「本卡未检查任何具体趟件的 S4 记录」。
2. **我未验**：`enum_failed` 的 2 趟（`archive_T19`、`l3_1101v4a`）到底有没有 hook
   —— 它们**不可判**，本轮**不把它们计入任何一边**。
3. **我未验**：`incomplete` 的 5 趟（含 3 个有效窗）的具体进程身份。
4. **我未验**：既有 87 窗是否真的一次都没采过这四个 VA —— 本文采信 `card_00A8EC34.md` §4
   与 `Q1_C3C4_PHYS_TARGET.md:318-319`（`measure_w*.json` 从未采它），**未自己逐窗核 `counters` 键**。

   > **追记（同轮亲验，推翻上一条的「未验」）**：我跑了 `counters` 键全集普查 ——
   > 101 个 `measure_w*.json` 的 `counters` 键并集 = `['t_rel','units','infantry','aircraft','g','g_items','b','b_items','techno','ws_kb','pf_kb','shape']`，
   > **不含 `gen_stamp` / `threat_calls` / `dirty_rect_count` / `bullet_count` 任何一个**。
   > ⇒ **四 VA 确实从未被采过**，此项由「未验」改判 **已亲验**。
5. **本文不构成任何数据有效性验收**：只回答「历史窗的镜像前提有无被 hook 污染的**证据**」。
6. 本文**零真机、零采样实现、零母本改动、未 commit**。

## 7. 对后续步骤的两条要求

1. **真机通道验证（D-20 步骤 A 的后半）必须显式记录 `S4` 结果并断言 `ra2render_hits == []`**，
   且该断言须进**确定性门槛**（不是靠人看）。现有 `s4_injection_gate()`（`harness8_v4.py:1070-1084`）
   已有该判据，**但 `--allow-loader` 会把命中降级为 WARN 放行**（`:1080-1082`）⇒
   **测量趟必须禁用 `--allow-loader`**。
2. **`incomplete` / `enum_failed` 两类必须在卡片里单列**，不得并入 clean。
