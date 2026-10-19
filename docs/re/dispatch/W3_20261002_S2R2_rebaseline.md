# W3-S2R2 派工单 · **级联修复：m36r/m31r 两验证器的上游指纹断言重钉基线**（ZCode 客户端 · 新会话）

> 工作目录 `D:\Project\ra2-campaign-forge` · 本卡只做这一包。
> **来源与 Lead 裁决**（台账 §469 EXT-1/2/3）：
> - **S3 的授权回填**（已验收：`zero_deletion=18/18`、九卡双零）**追加改大了 agy 上游原件** ⇒ minimax 审计卡验证器里的**时点性上游指纹断言**失效：
>   - `verify_m36r` **20/21**（仅 `§[9] M36 originals size parity` 挂）
>   - `verify_m31r` **FAILED**（仅 `G2.1 M31 只读域指纹` 挂；**verdict tally 照常输出 258/3/0**）
> - **裁决**：两包验收状态不变；**处置 = 重钉基线（不比对旧数值）**，把断言升级为**"前缀逐字节相等 + 追加块计数"**（比原尺寸断言**更强**）。

## 🔴 铁律（先读）
1. **只准动两处断言**：`out/re_work/minimax/W3_20261002/m36r_ch14_audit/verify_m36r.py` 的 §[9] 与 `.../m31r_ch8_audit/verify_m31r.py` 的 G2.1。**其余断言一字不许改**（内容断言必须原样保留并照常通过）。
2. **新断言必须更强，不许更弱**：
   - **前缀逐字节**：S3 回填前的原文件内容（`zcode_live/W3_20261002/s3_backfill/snapshots_before/<card>/` 里有改前快照）**必须是现文件的逐字节前缀**。
   - **追加块计数**：现文件中 `【W3-S3 回填】` 标记数 == S1/S3 ledger 记录的该卡回填条数。
   - **sha 登记**：现文件 sha256 记入断言常量区并注明 `baseline: post-S3-append @<时刻>`。
3. **改前留证**：两文件改前副本 + sha 存 `out/re_work/zcode_live/W3_20261002/s2r2_rebaseline/`。
4. **两验证器改前改后各跑**（改前应为 20/21 与 FAILED —— 原文落 `runs/`；改后**须全绿 EXIT=0**），**并同时跑 `verify_m28r.py` 与 `verify_s3.py` 证明无副作用**（各两跑）。
5. **`S2R1_REPORT.md` 的 EXT 报告不需要改**（它如实记录了当时状态）—— 但你的报告要引用它。
6. **写域仅此**：两个 verify 文件（限铁律 2 的范围）+ `out/re_work/zcode_live/W3_20261002/s2r2_rebaseline/`

## 交付
`S2R2_REPORT.md`（§A 十节骨架；`[0]` 直答：两断言改前/改后原文 diff、为何更强、四验证器八跑结果）· `snapshots/`（改前两文件）· `runs/`（八跑原文）· `verify_s2r2.py`（**EXIT=0 + `verdict tally` 行**；断言：只改了两处、内容断言数量不变、四验证器全绿）

## 回报 `[0]`
① 两断言 diff 与"更强"论证 ② 四验证器八跑 EXIT ③ 有无内容断言被触碰 ④ `verdict tally` 原文

## 底线
> **宁可交"改后 m36r 全绿但你发现某条内容断言也因此变了并停下来报告"，也不要交一个把 21 条砍成 15 条的'全绿'。**
