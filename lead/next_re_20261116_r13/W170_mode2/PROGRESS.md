# W170 · PROGRESS（每完成一步追加一行）

| 时间 (Asia/Shanghai) | 做了什么 | 结论 / 下一步 |
|---|---|---|
| 2026-11-16 21:42 | 按顺序全读 `R13_COMMON.md`（先看作废索引 12 条）→ `R11_COMMON.md` → `R12_FACTS.md`（974 行全） | 记下两条硬纪律：寄存器语义须回溯全部写入点；"某分支什么都不做"须逐条打完。作废 §23/§24 的 mode3 强制放置、mode0 什么都不做。 |
| 21:44 | 检查环境：python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；`W170` 项目已存在且与 `W150` 逐文件同构（20 文件 / 147.5 MB，零差异）→ 直接复用；无 java 进程。建 `work\`、`EVIDENCE\`。 | 遵守"只用一个 Ghidra、不反复起停"。 |
| 21:46 | 读 `audit_lib.py`（只读写法，不 import）；读 `reverify_914.py`、`EVIDENCE_43F180_vtable/7014A0_identity/70D4A0/cfg_43F180/mode0_branch/grid_methods/slot73_classes`；读 W122 的 `DumpFunc/RangeDump/PcodeSlice2.java` 模板。 | 确定两通道策略。 |
| 21:47 | grep 主台账 §664/§665/§666/§890/§914/§915 与 `0x81`/`5F5850`/`7014A0`/mode2 相关节，避免重报旧结论；再 grep `705D70/5F6960/456F80/41BF40/70E360` → 仅 `43FB20` 命中，四个槽函数均为新发现。 | 符合"写新发现前先 grep 台账"。 |
| 21:48 | 写 `work/w170_channelA.py`（自实现 Bin/md32，capstone `skipdata=True`，不 import audit_lib、不依赖 atlas entry+size 做扫描）并运行，输出 6 份 EVIDENCE。 | `.text` 1,394,120 指令 / 跳 66 B；mode2 分支入口到 `ret 4` 逐条打完 114 条（无省略，紧随的 nop 不计）、无 grid 调用；四虚槽解析成功。 |
| 21:49 | 写 `work/w170_ctx81.py`，逐站点 ±48 B 上下文 dump 31 个对象字段写点。 | 发现 `0x44EB7C/0x44EBD8` 与 `0x44EBF0` 系列是"保存-置1-恢复"惯用法。 |
| 21:50 | 写 `work/w170_fn_ownership.py` + `w170_vtclass.py`，把写点函数映射到 rdata dword 命中与谓词直接调用者。 | 谓词 8 个直接调用点（含 `0x6F4A70`/`0x71BFB0` 两个槽73 与 3 个 18 B 小包装）。 |
| 21:50 | 写 `work/W170Dump.java`：一次 Ghidra `-noanalysis` 同时反编译 23 个目标函数 + 独立指令扫描 byte `[+0x81]`（通道 B）。输出重定向到 `EVIDENCE/ghidra_W170Dump.log`，exit=0。 | 一次起停完成全部 Ghidra 工作；imageBase=00400000，与实例一致。 |
| 21:51 | 读反编译：四槽函数、`0x70E360/0x70E380/0x70E4B0`、`0x43FB20`、`0x7014A0/0x70D4A0`、`0x5F5850`、`0x5F4D30/0x5F4EC0` 等。 | **关键突破**：`0x5F4D30` 摘链后置 `+0x81=1`、`0x5F4EC0` 挂链前清 `+0x81=0` ⇒ `+0x81` = 已 Limbo；`0x7014A0` = SetOwner（非设目的地）。 |
| 21:52 | 写 `work/w170_followup.py`（0x5F6960 全 27 条、`0x43FB20` mode2 调用点上下文、A/B 对账）；`work/w170_reclassify.py`（B 通道 W/R 重分类）；`work/w170_helpers.py`（`0x565730`/`0x70E380`/`0x70E4B0` 反汇编）。 | A/B 对账 `onlyB=0`、31 个 A-only（含 3 个孤儿写点）；B 重分类后 28 写/204 读，与 A 的对象字段 31/232 严格包含。 |
| 21:53 | 逐条核对 Q1/Q2/Q3 证据，写 `MODE2_AND_0x81.md`（5 行摘要 + 三问 + 判决 + LEAD_AUDIT）、`PROGRESS.md`、`UNKNOWNS.md`、`DISAGREE.md`。 | 全部结论带 [已证]/[静态推断]/[未证] 与复跑命令；完成交付。 |

## 纪律自检

- ✅ 未启动游戏、未 attach/读活进程、未改任何游戏文件、未改主台账；只写 `W170_mode2\`（`work\`、`EVIDENCE\`）。
- ✅ Ghidra 用 `W170` 副本（已存在且与 W150 同构）、项目 `gamemd_auto`、程序 `gamemd.exe`、**`-noanalysis`**、输出重定向到日志、未用管道截断；**只起一次**。
- ✅ 穷举结论双通道，通道 A 不依赖 `function_atlas.tsv` 的 entry+size（从节首逐字节扫）；通道 B 独立指令模型；对账 `onlyB=0`。
- ✅ capstone 全程 `skipdata=True`（channelA 统计 `skipped_bytes=66`）。
- ✅ 凡寄存器/字段语义判断均回溯写入点（`+0x81` 全写点、`ebp` 教训、`+0x21C` 的新 owner 写入）。
- ✅ "分支什么都不做"类结论逐条打完（mode2 分支 115 条全列、谓词 79 条全列、`0x7014A0` 321 条全列）。
- ✅ 写"新发现"前 grep 主台账。
- ✅ 每个数字附可复跑命令；结论只用 [已证]/[静态推断]/[未证]。
- ✅ 未 git commit/push。
