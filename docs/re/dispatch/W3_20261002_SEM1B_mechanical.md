# W3-SEM1B 派工单 · **SEM1 第二批：141 个 MECHANICAL 文件的动作判定与修正版副本**（Qoder CN · 新会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源**：SEM1（已验收 `verify_sem1.py` GATE OK）清册 151 文件，其中 **`PRIMARY=9`（已处置）· `ATLAS=1`（登记）· `MECHANICAL=141`（`errata_quote_only=19` + `pending_later_batch=122`）** —— 本卡处理那 **141 个 MECHANICAL**。
> **MECHANICAL 的定义（SEM1 清册）**：manifest/claims/claims_agg/调度卡等**机械登记文件**里的 `FrameTimer_SelectAutoTarget`（或幻影 `CurrentFrame`）出现点 —— **它们被各卡验证器逐字节/逐条断言，原地改会红灯**（SEM1 因此只登记不动）。

## 🔴 铁律（先读）
1. **原地零写入**：本卡**不修改任何 MECHANICAL 原文件**（141 个全部只读）—— 产出全部落在你的写域。
2. **产出 = 修正版副本 + 判定表**：
   - 每个含错名的 MECHANICAL 文件生成 `corrected/<相对路径>`（**只改命名字符串、其余逐字节不变**，改完自证：`原文件 == 把副本中该改名还原后的字节`）；
   - `action_verdict` 逐文件三值：`ADOPT_LATER（值得原地换，列条件）/ KEEP_AS_IS（机械登记，错名无害或断言依赖，永不换）/ UNCLEAR（列理由交 Lead）`。
   - **判定标准**：该文件是否被任一 `verify_*.py` 逐字断言（grep 全部验证器引用它的地方）—— **被断言 ⇒ 默认 KEEP_AS_IS，除非给出"断言值也同步更新"的方案**。
3. **抽验**：≥10 个副本跑**对应解析器**（如 `tools/audit_bytes.py` 对 claims 类、`parse_claims()` 对 `#` 行）证明**功能等价**（断言条数/读数不变）。
4. **反向验证**：构造一个"假修正"（副本里多改一处非命名字节）⇒ 你的"其余逐字节不变"检查必须 FAIL。
5. **只读红线**：原版侧 ATLAS、`coverage_ledger/**`（CS2 在写）、`docs/**`、`ra2youli/**`、`tools/**`、141 个原文件。
6. **写域仅此**：`out/re_work/qc/W3_20261002/sem1b_mechanical/`

## 交付
`SEM1B_REPORT.md`（§A 十节骨架；`[0]` 直答：141 三类计数、抽验结果、被验证器引用的文件数）· `action_verdict.json`（141 逐文件）· `corrected/`（副本树）· `verify_sem1b.py`（**EXIT=0 + `verdict tally` 行**；断言：141 齐、原文件 141/141 sha 未变、每副本还原等价、抽验功能等价、负控咬）

## 回报 `[0]`
① 三类计数 ② 被验证器引用的文件数（未来原地换的风险面）③ 抽验结果 ④ 反向验证 ⑤ `verdict tally` 原文

## 底线
> **宁可交"141 全清册、0 个副本（因为判定全部 KEEP_AS_IS 并给出断言依赖证据）"，也不要交 122 个副本却有 3 个把断言弄坏了。**
