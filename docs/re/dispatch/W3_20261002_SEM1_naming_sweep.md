# W3-SEM1 派工单 · **`FrameTimer_SelectAutoTarget` 错名全库清扫**（Qoder CN · 新会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：S2 裁决 SEM-1（`BOTH_PARTIAL`，Lead 已验收）对 VA `0x00A40D2C` 的命名裁定：
> > **`0x00A40D2C` = 引擎级 BSS 全局 dword = 每逻辑帧自增的帧时钟**（全 `.text` 唯一自增写点 `0x00540681 inc edx` + `0x00540684 mov [0x00A40D2C],edx`，主循环驱动函数内）。
> > **命名裁定：帧时钟语义名可留 `[推演]+字节锚`；`FrameTimer_SelectAutoTarget` 删除；单例唯一写入点声称不予恢复。**
> **影响面（S2 grep 实测）**：**99 个文件含命名断言，其中 57 个含 `FrameTimer_SelectAutoTarget`**（主改点=原始卡面 9 个文件；另 ATLAS 幻影 `CurrentFrame` 1 处）。
> **权威裁决**：`zcode_live/W3_20261002/s2_conflict_adjudication/{S2_REPORT.md §SEM-1, conflict_adjudication.json, raw/step10_impact.txt}`

## 🔴 铁律（先读）
1. **两段式执行（先清册，后动刀）**：
   - **第 1 段（必做）**：产出**全量清册** `sem1_sweep.json` —— 99 文件逐条：`file:line` + 含该名的上下文片段 + 分类（`PRIMARY=主改点 9 文件` / `MECHANICAL=manifest/claims 机械登记` / `ATLAS=幻影 CurrentFrame`）+ 建议动作。
   - **第 2 段（只动 PRIMARY）**：**仅对主改点 9 文件**执行追加式勘误；**MECHANICAL（约 90 文件）只登记不动**（它们被各卡验证器逐字断言，动了会红灯 —— 清册里标注"待后续批次"）。
2. **追加式勘误形态**（原句零删除）：
   `> 【W3-SEM1 勘误】此处 `FrameTimer_SelectAutoTarget` 命名撤销（S2#SEM-1 判据：该名无字节锚）。正确表述：引擎级 BSS 帧时钟（每逻辑帧自增；唯一自增写点 0x00540681/0x00540684，主循环驱动函数内；915 引用 = 903 读 + 10 写 + 2 立即数）｜语义名分级 [推演]+字节锚｜单例唯一写入点声称不予恢复｜依据：S2_REPORT §SEM-1`
3. **改前快照** + PRIMARY 9 文件的**相关验证器改前改后两次 EXIT=0**（原文落 `runs/`）；**改后红灯 ⇒ 回滚该文件并报告**（不许改验证器）。
4. **ATLAS 幻影 `CurrentFrame` 1 处**：S2 记录在案 —— 若它在 `ARCHITECTURE_ATLAS_GAME.md`（Qoder 写域）**可直接追加勘误**；若在 `docs/re/ARCHITECTURE_ATLAS.md` ⇒ **只登记不动**（docs 写权另排）。
5. **只读红线**：`ra2youli/**`、`tools/**`、coverage_ledger 不碰。
6. **写域**：PRIMARY 文件（追加式）+ `out/re_work/qc/W3_20261002/sem1_sweep/`

## 做什么（四件）
1. **全量清册 99 文件**（第 1 段，先落盘 —— 即使第 2 段没做完，清册本身就是交付）。
2. **PRIMARY 9 文件追加勘误**（按铁律 2 形态；`sem1_sweep.json` 里逐文件记 before/after sha）。
3. **验证器两次跑**（受影响的那几张原卡/审计件的 verify）。
4. **反向验证**：抽 2 条勘误核"原句还在 + 块在"；再**抽 1 个 MECHANICAL 文件证明它没被改**（sha 未变）。

## 交付
`SEM1_REPORT.md`（§A 十节骨架；`[0]` 直答：99 文件分类计数 / PRIMARY 落了几处 / 验证器结果）· `sem1_sweep.json`（全量清册）· `snapshots_before/` · `runs/` · `sem1_changes.json` · `verify_sem1.py`（**EXIT=0 + `verdict tally` 行**）· `raw/progress.log`

## 回报 `[0]`
① 99 文件三类计数 ② PRIMARY 9 处各自动作 ③ 验证器两次 EXIT ④ 幻影 CurrentFrame 落在哪/是否只登记 ⑤ 反向验证 ⑥ `verdict tally` 原文

## 底线
> **宁可交"清册 99 全、PRIMARY 落 6 处、3 处因验证器拦截列出待裁"，也不要交"99 个文件全改了但十个验证器红灯"。**
> **清册是本卡的第一价值 —— 后续批次拿它就能机械执行。**
