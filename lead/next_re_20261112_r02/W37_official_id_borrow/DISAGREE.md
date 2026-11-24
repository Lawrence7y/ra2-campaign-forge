# DISAGREE · W37 与任务前提不符 / 需澄清之处

> 全部为**纯离线只读复核**结果。每条给「前提原文 / 本次事实 / 证据 / 对结论的影响 / 等级」。
> 本卡不推翻任何已定谳的 Lead 裁定；D1–D3 是**前提的边界条件与措辞精确化**，D4 是**仓库内部文档口径分歧**（非任务前提）。

---

## D1 · 「散装 `BATTLEMD98.INI` 同 id 后装载者覆写」——成立，但有两个未闭环前置条件

**任务前提（Q2 引言）**：
> 「散装 `BATTLEMD98.INI` 是「追加合并」语义（同 id 后装载者覆写），所以覆写官方 id 走的是**同 id 后胜**这条路。」

**本次事实**：合并语义本身成立（`0x46CE10` = 对象复用 + `vtbl+0x64` 字段覆写，per-key last-write-wins，`[转引 docs/re/fs_mix_load_chain.md:280-285 / ARCHITECTURE_ATLAS.md:3638]`）；但「**后装载者 = BATTLEMD98.INI**」不是无条件事实：

1. **枚举顺序未定谳** `[转引 ARCHITECTURE_ATLAS.md:3646]`：同名 ID 的最终胜者取决于 `FindFirstFileA/FindNextFileA` 目录枚举顺序，**引擎不保证字母序**，文档原话「工程上禁止跨文件重复 ID」。`fs_mix_load_chain.md:284` 的「`BATTLEMD98.INI` 通常胜出」自带 `[推演]+[待实测]`；`W29 OVERRIDE_ORDER.md:22` 把「枚举顺序决定的最终胜者」标为 **[静态推断-弱] / [待运行验证]**。
   `[本次实测 e3 L6-13]`：`ra2youli` 现状同时有 `BATTLEMD.INI` 与 `BATTLEMD98.INI` 两个散装文件 ⇒ 借用官方 id **必然**构成跨文件重复 ID，正落在这条风险上。
2. **回退分支可能把官方 INI 变成后装载者** `[静态推断]`，依据 `[转引 ARCHITECTURE_ATLAS.md:3611-3631]`：`LoadBattleMdIni 0x52CB90` 在通配枚举（`0x52CC67 call 0x46CE10`）**之后**还有一个回退分支 `0x52CCCD → 0x52CD2C call 0x46CE10`，用 `CCFileClass("BATTLEMD.INI")` 读 MIX 内官方件。若目标机**没有散装官方 `BATTLEMD.INI`**，官方 `SOV1` 段反而后归并 ⇒ 我方覆写被翻盘、借用 id 静默失效。
   （`[转引 ra2forge_fix_forge2.md:97]` W3 勘误已实证嵌套 `LOCALMD.MIX` 内确有官方 `BATTLEMD.INI` 2,733 B / `7e40691a…`。）

**对结论的影响**：Q2 的「同 id 后胜」应改写为「**同 id 后胜，但胜者由目录枚举顺序决定且未定谳；且必须保留散装官方 `BATTLEMD.INI` 以跳过回退分支**」。这不是推翻前提，而是补上它省略的边界。**工程上不得把「98 一定赢」写进安装器契约**，见 `BORROW_FEASIBILITY.md` §2.3 / Q5 表 #3。

**等级**：合并语义 `[转引]`；两个前置条件 `[静态推断]` + `[待运行验证]`。最小实验见 `[转引 W29 UNKNOWNS.md:30]`（投 `BATTLEMD01/02.INI` 同 ID 不同 `Description`，在 `0x46CF60` 下断）。

---

## D2 · `BATTLEMD.INI` 里不存在 `[TUT*]` 段，也不存在 `tut1` 条目

**任务前提（Q1）**：
> 「列出官方 `BATTLEMD.INI` 的 `[Battles]` 全部条目与 `[ALL*]/[SOV*]/[TUT*]` 段的关键字段」。

**本次事实** `[本次实测 e1 L18-38, L57]`：
- `[Battles]` 恰好 **14** 条：`1=ALL1, 2=SOV1, 3..8=ALL02..ALL07, 9..14=SOV02..SOV07`；
- 战役段恰好 **14** 个：`ALL1 / SOV1 / ALL02..ALL07 / SOV02..SOV07`；
- **`tut1` 不在 `[Battles]` 中，文件里没有任何 `[TUT*]` 段**（e1 两条专门断言 PASS）。

**为什么会觉得有**：`WndProc 0x52EC00` 确有三个硬编码立即数 `0x6EA/0x6EC/0x6EB`，三个分派槽绑 `.data` 的 `"all1"/"sov1"/"tut1"`（任务前提本身也这么写）`[转引 LEAD_VERDICT_campaign_menu_q1.md:25, 33-39]`。但 `[转引 W32 MENU_ENTRIES.md:205,214]`：对话框模板 `RT_DIALOG id=148` 的 13 控件里徽章 Static **只有 1770 (`0x6EA`) / 1772 (`0x6EC`) 两个**，`0x6EB` 分支是**残留（模板无控件）**。

**对结论的影响**：Q1 的 `[TUT*]` 一栏应为「**空**」；`tut1` **不是可借用入口**。可用集合 = `{ALL1, SOV1}`（见 `BORROW_FEASIBILITY.md` §1.2 / §1.3）。若强行在散装 INI 新建 `[tut1]` 段，就退回「追加新 id」路线，而该路线已被 W32 判定不生成可见徽章。

**等级**：`[本次实测]`（INI 字节）+ `[转引]`（模板/立即数）。

---

## D3 · `RA2MD.INI` 里没有「战役进度」键

**任务前提（Q4 冲突面清单）**：把「`RA2MD.INI` 里的战役进度」列为一项冲突对象。

**本次事实** `[本次实测 e1 L84-87 / e3 L44]`：
- `ra2youli/RA2MD.INI` 全文 **118 行 / 1,754 B**，SHA-256 `c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d`；
- 10 个段：`Intro, MultiPlayer, Skirmish, LAN, WonlinePref, Options, Video, Audio, Network, SerialDefaults`；
- 匹配 `camp/mission/scenario/progress/stage` 的键**只有** `[Options] CampDifficulty=0` —— 这是**战役难度**，不是进度；
- 另有 `[Video] StretchMovies=no`（视频缩放，e1 已明确把它排除在进度普查之外）；
- 没有 `[Campaign]` 段、没有 `Scenario` / `Mission` / `Progress` / `Stage` 键。

**实际载体** `[转引]`：战役推进状态是 `ScenarioClass` 内的 `[Scen+0x125C]`（当前地图名）/ `[Scen+0x35A0]`（当前阶段序号），由 `Write_Scenario_INI` 写回**存档/INI**（`W33 DISAGREE.md:8`），真机产物是 `.SAV`（`W27 CAMPAIGN_LIVE.md:117`：`SAVE4823.SAV` 559,553 B，内含 `ECH02.MAP` 串）。是否另有注册表项，本卡未查 ⇒ `[待运行验证]`。`W33 DISAGREE.md:15` 亦明确「`BATTLEMD.INI [Battles]` 不参与通关后的下一关选图」。

**对结论的影响**：Q4 该项应改写为「**`RA2MD.INI` 无进度键（只有难度 `CampDifficulty`），安装器 MUST NOT MODIFY；进度冲突的实际对象是 `.SAV` 存档**」。所以 Q4 第 1 项与第 4 项在事实层面**合并为同一类**：存档/进程态，而不是两个独立文件。`BORROW_FEASIBILITY.md` §4 表 #1/#4 已按此处理。

**等级**：`[本次实测]`（本文件）/ `[转引]`（存档载体）。

---

## D4 ·（附录，非任务前提）仓库内部对「回退分支触发条件」有三种口径

| 出处 | 措辞 |
|---|---|
| `W29_override_order/OVERRIDE_ORDER.md:22` | 「回退分支**仅在目录里一个 `BATTLEMD*.INI` 都没有时**才执行」 |
| `docs/re/fs_mix_load_chain.md:20` | 「若枚举结果里**没有 `BATTLEMD.INI` 本身**，再显式装载 `BATTLEMD.INI`」 |
| `docs/re/mix_hygiene_product.md:122` | 「官方 `BATTLEMD.INI` 可来自 MIX，但**仅当目录无任何散装 `BATTLEMD*.INI`**」 |
| `docs/re/ARCHITECTURE_ATLAS.md:3613-3631` 反汇编 | `0x52CC54 _stricmp(枚举名, "BATTLEMD.INI")` → `0x52CCC7 jne 0x52CD5F`（**已见过官方名** → 跳过回退）；`0x52CBB1 je 0x52CCCD`（FindFirstFile 失败 → 回退）|

四者措辞不一致。本卡**采信反汇编**（判据是「枚举里是否出现官方名 `BATTLEMD.INI`」，而不是「是否有任意 `BATTLEMD*.INI`」），并把它登记为 `UNCOVERED.md` U2 的 `[待运行验证]` 项。**不影响主结论**：`ra2youli` 现状有散装官方 `BATTLEMD.INI`（`[本次实测 e3]`），四种口径下都会跳过回退；分歧只在「目标机没有散装官方件」的边缘情形才暴露。

---

## 未构成分歧、已复核通过的前提

| 前提 | 复核 |
|---|---|
| `MAPSELMD.INI` 在 `ra2md.mix` 偏移 `0x71D050` / 5,573 B / CRLF / SHA-256 `074ccccd…6919d52` | `EVIDENCE/e2_extract_mapselmd.stdout.txt` 双路独立自证，34/34 PASS，exit 0；递归解码的绝对起点恰为 `0x71D050` ✅ |
| 官方 14 图逐一登记在 `[GDI] 1..7` / `[Nod] 1..7` 的 `Scenario=` | e2 §C 20 段 / 14 个非空 `Scenario=` ✅ |
| 两处游戏目录都无散装 `MAPSELMD.INI` | e3 L1-4 ✅ |
| `ra2bench/BATTLEMD.INI` 与 `ra2youli/BATTLEMD.INI` 一致 | e1 L13：逐字节相同，2,733 B ✅ |
| W21「错还原」、W26「吞异常/谎称回滚」原文 | 本卡逐字读 `W21 DISAGREE.md:17-24` / `W26 UNSEAL_FIX.md:13-34,48-64` ✅ |
