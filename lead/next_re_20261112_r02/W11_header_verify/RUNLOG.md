# W11 RUNLOG —— `[Header]` 节单变量验证执行记录

- run_id：`NEXT_RE_20261112_R02`；卡片：W11；日期：2026-11-13（本地 UTC+8）
- 执行：`python -X utf8 header_verify.py --run`（job pwsh-578156af3eb74602），
  随后 `--analyze`。逐拍/事件流：`out\run.ndjson`；控制台全量：`out\run_stdout.txt`。

## 时间线（UTC）

| 时刻 | 事件 |
|---|---|
| 18:29:55 | S0 锁 `owner=lead→w11_header_verify_subagent`；gamemd 残留 0；五件基线哈希 match=True；H1 载体 315,912 B / `3ce133ff…` match=True；清单 648 项 |
| 18:29:56 | S1 WMI 启动 gamemd.exe（launcher 13204 → pid 37692）；is32=True；代码签名@0x55DE4F ok=True |
| 18:30:17 | 主菜单就绪（20.0s）；窗口 hwnd=15405924 tid=39148 |
| 18:30:17–23 | 导航 SinglePlayer → Skirmish → ChooseMap 三击全 True |
| 18:30:26 | 列表 ListBox=27201732，条目 **269**（基线 268，Δ+1）；三口径命中 0（matched_by=none）；字面 `No Name` **2 个 [91, 97]**；读失败 0；空串 0 |
| 18:30:26 | S3 itemdata 768B 审计：[91] prm.yrm（`No Name` + base64 digest，历史项）；[96] `[2] 0LoadBench U800` 正常；**[97] 名称槽=`No Name`，文件名=`[2]0LoadBench_U0800_H1.yrm`，digest=`No Digest`** |
| 18:30:28 | panel_96_ctrl 快照正常；panel_target 因无命中跳过；**Q1 判定：未命中 ⇒ GuardStop Q1_NO_NAME，不开局、不试第四变量** |
| 18:30:41 | 收尾：WM_CLOSE→taskkill(无/F)→taskkill /F；存活=False；残留 0；清单 648→648 无增删改；三件配置逐字节还原 sha_match=True；H1 载体 untouched=True；锁恢复 `owner=lead` |
| 18:30:54 | `--analyze`：verdict=`header_not_the_cause`；W10↔W11 逐索引名称 diff=0；目标 hex 由 itemdata_audit_97.hex 复出（身份：内嵌文件名钉死） |

## 与前置两步的链

| 组 | 变量 | 条目数 | [H1] 显示名 | [H1] 名称槽 | [H1] digest |
|---|---|---|---|---|---|
| W9 | 原件（裸 LF、无 `[Header]`） | 269 | `No Name` | `No Name` | `No Digest` |
| W10 | 仅行尾（CRLF） | 269 | `No Name` | `No Name` | `No Digest` |
| **W11** | **CRLF + 最前补 `[Header]`** | **269** | **`No Name`** | **`No Name`** | **`No Digest`** |

## 交付物

- `header_verify.py`（--run / --analyze，可重跑）
- `out\maplist.json`（269 条全量 + 三口径命中 + 诊断分类）
- `out\itemdata_audit.hex`（目标 [97] 768B）与 `out\itemdata_audit_{91,96,97}.hex`
- `out\compare_with_W10.md`（三方逐字段 + 逐字节对照）、`out\verdict.json`
- `out\run.ndjson`（事件流；本卡未开局，无采样拍）、`out\meta.json`、`out\run_stdout.txt`
- `VERDICT.md`、`SAFETY.md`、`CONFIG_RESTORE.md`、`RUNLOG.md`、`UNCOVERED.md`

## 结果一句话

**`[Header]` 缺失不是主因 [否证]**：条目 269（+1，文件被扫描）但目标仍字面
`No Name`+`No Digest`，与 W10/W9 的 [97] 记录逐字段、逐字节全同（W11↔W10
768B 差异 0 字节）。行尾与 `[Header]` 两个结构变量均被单独否证；按任务书
停止，交回 Lead（「H1 修复失败时改用已验证对局作替代基线」收口）。
