# 独立复核 · W7 回件（ERRATA_W7.md）

被核对象 = W9_SINGLESTEP.md / W8_STATIC_LOCATE.md / W7_W4_REVIEW.md / V6_V3_REVIEW.md
W9_SINGLESTEP.md  SHA256 = 13fa9fe35339ea40d123cf340b09c9ac692e848305ebc48d9d35f5421d895e36，字节数 = 40,592
W8_STATIC_LOCATE.md SHA256 = 20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262，字节数 = 26,485
W7_W4_REVIEW.md  SHA256 = 22753a0ef603c6999c95b25e28a2b5a2d5820ded39c9b59559d088bf20da6ca6，字节数 = 19,225
V6_V3_REVIEW.md  SHA256 = 75cad20763952e7a6d92274f8d29e7db30c307194e45437d8d459242baceffdb，字节数 = 17,892
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（目标镜像，本任务不反汇编它）
回件时刻 = 2026-11-06 09:48:43 +0800

> 以上四份 SHA256 / 字节数与 gamemd.exe 的 SHA256 均为**本复核员本次会话自跑 `sha256sum` + `wc -c` 实得**（命令与输出见 §1），
> 非照抄 Leader 参照值、非照抄被核回件头部。本件唯一写域 = `A1_ERRATA_MAP/reviews/W7_review.md`。

## 0 总判

**CONFIRMED**（限定：见 §7 的三处非实质异议，均不构成 TASK.md §5 的 PARTIAL / REFUTED 条件）。

- `shaBindingPresent = true`：头部四 SHA256 + 四字节数齐全，且与我自算值逐位一致；§4-1/§4-2 有可复现的命令转录。
- `checkedEveryRow = true`：W7 应有 **7 项 + A1 = 8 条**，回件 §1 一览表 8 行（:35-42）、§1 分条 8 个 `### W7-*` 小节，逐条含「原位置 / 原断言逐字引用 / 限定句 / 汇总件已落实 / 判定档 / 证据」六要素，**无缺条**。
- **未发现** W7 以任何形式恢复/重建 phase 2（若发现则按 D-24 令总判直接 REFUTED，本次未触发）。
- **未发现**可归因于 W7 回件的既有件修改。

## 1 强制头部与「自己实算」核验（重点 1）

自跑命令（Git Bash，工作目录 `D:/Project/ra2-campaign-forge`）：

```
$ sha256sum lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md lead/re_line_20261105/W7_W4_REVIEW/W7_W4_REVIEW.md lead/re_line_20261105/V6_V3_REVIEW/V6_V3_REVIEW.md ra2youli/gamemd.exe
13fa9fe35339ea40d123cf340b09c9ac692e848305ebc48d9d35f5421d895e36 *lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md
20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262 *lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md
22753a0ef603c6999c95b25e28a2b5a2d5820ded39c9b59559d088bf20da6ca6 *lead/re_line_20261105/W7_W4_REVIEW/W7_W4_REVIEW.md
75cad20763952e7a6d92274f8d29e7db30c307194e45437d8d459242baceffdb *lead/re_line_20261105/V6_V3_REVIEW/V6_V3_REVIEW.md
73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 *ra2youli/gamemd.exe

$ wc -c <同上四份 .md>
 40592 ...  26485 ...  19225 ...  17892 ...  104194 total
```

结论：

- 回件 `ERRATA_W7.md:3-9` 头部**含完整强制头部**（TASK.md §4 要求的被核对象行、四 SHA256、四字节数、gamemd.exe、回件时刻）。`shaBindingPresent = true` ✓
- 四份参照值与**我自算**逐位一致 ⇒ 对象未变（若有差异必须标出，本次无）。`W7_W4_REVIEW.md` 在我会话开始与结束时两次 `sha256sum` 均为 `22753a0e…` ✓
- **「自己实算」可复核性**：`:11-12` 自述自算；`:192-199`（§4-1）逐行给出 `sha256sum` 输出（含第 5 个 gamemd.exe）；`:200`（§4-2）给出 `wc -c` 四值 + 合计 104,194。我复跑 §4-3/§4-4/§4-5/§4-6 全部命令，输出与转录一致（见 §2/§3/§6）。按静态文档可验证的上限，判定「自己实算」成立；**无法从文件本身证明其执行主体**，此点按「未验」诚实登记（不影响 CONFIRMED，因数值与转录均可复现）。
- 小疵（非实质）：`:11` 写「以上**五个** SHA256 / 字节数均为…自算实得」，实际头部仅四份给了字节数，gamemd.exe 未给字节数。

## 2 逐条覆盖核验（重点 2）

自跑命令：

```
$ grep -nE "^\| (A[1-4]|B[1-3]|C) \|" A1_ERRATA_MAP/ERRATA_W7.md   → 8 行：:35 A1, :36 A2, :37 A3, :38 A4, :39 B1, :40 B2, :41 B3, :42 C
$ grep -cE "^### W7-(A[1-4]|B[1-3]|C) " A1_ERRATA_MAP/ERRATA_W7.md  → 8
$ grep -nE "^\| (A[1-4]|B[1-3]|C) \|" W7_W4_REVIEW/W7_W4_REVIEW.md   → 8 行：:20-27
```

逐条落点（原位置均指向 `W7_W4_REVIEW.md` 实存表行，我 Read 全文核对）：

| 项 | 回件一览 | 回件分条 | 源表行 | 六要素 | 判定 |
|---|---|---|---|---|---|
| A1 | `:35` | `:49-64` | `:20` | 齐（含 A1 专用「自身即 PARTIAL、非降级」） | CONFIRMED |
| A2 | `:36` | `:66-78` | `:21` | 齐 | CONFIRMED |
| A3 | `:37` | `:80-92` | `:22` | 齐 | CONFIRMED |
| A4 | `:38` | `:94-106` | `:23` | 齐 | CONFIRMED |
| B1 | `:39` | `:108-120` | `:24` | 齐 | CONFIRMED |
| B2 | `:40` | `:122-134` | `:25` | 齐 | CONFIRMED |
| B3 | `:41` | `:136-148` | `:26` | 齐 | CONFIRMED |
| C  | `:42` | `:150-162` | `:27` | 齐 | CONFIRMED |

- **8/8 条齐全，无缺条** ⇒ `checkedEveryRow = true`；mustFix 无需点名任何缺条。
- 七项统一限定句「phase 1 初判，phase 2 未完成，仅按 PARTIAL 采信」见 `:183`（§3-2 逐字给出）；A1 专用限定句见 `:58`、`:185`，明写「不是由 CONFIRMED 降级而来」，符合 TASK.md §1.3 与 D-24 `RULING_D24.md:50,75`。
- 顺带（非本组职责，仅旁证口径）：`grep -c "^### W9-" ERRATA_W9.md = 20`、`grep -c "^### W8-" ERRATA_W8.md = 12`，与 TASK.md:14-16 的条数一致。

## 3 alreadyLanded 是否真看了落实处行号（重点 3）

**结论：真去看了，且不是「凭感觉标已落实」**——回件 8 条一律标 **部分落实**（不是「已落实」），并给出落实处行号 + 一条可复现的否定性 grep。

我逐项复核其援引的汇总件行（我 Read 了 `W7_W4_REVIEW.md` 全文）：

| 回件援引 | 汇总件实际内容 | 核对 |
|---|---|---|
| `:20` A1 两列 PARTIAL | `W7_W4_REVIEW.md:20` 「**PARTIAL** … PARTIAL」 | ✓ |
| `:21-27` 逐项「降级为『phase 1 初判』」 | `:21-27` 末列逐行一致（7 行） | ✓ |
| `:29` A1 判 PARTIAL 的独占性 | `:29`「七份里只有 A1 判 PARTIAL，其余七项（含 C 组）phase 1 判 CONFIRMED」 | ✓ |
| `:30` 总规则 | `:30`「未经 phase 2 的 CONFIRMED 只按 PARTIAL 级信任采信」 | ✓ |
| `:212` 总规则 | `:212`「七项 CONFIRMED 一律按『phase 1 初判』引用」 | ✓ |
| `:36-41` / `:192-194` A1 三条必改、`substantiveDefect=false` | `:36-41`（三条 + `substantiveDefect = false`，A1 记 PARTIAL）、`:192-194`（`:54` linker-map 假陈述 / `:47` `0x67C8E0`→`0x6C8E0` / `:306` `0x56721B`→`0x56721A`） | ✓ |
| `:75` A1 §2 标题 | `:75`「A1 · card_0087E8E0.md … **PARTIAL**（substantiveDefect = false）」 | ✓ |

自跑复现其 §4-4 命令：

```
$ grep -n "phase 1 初判\|仅按 PARTIAL\|PARTIAL 采信\|探针输出" W7_W4_REVIEW/W7_W4_REVIEW.md
4: …只有 4 个探针输出落盘…
21..27: …降级为「phase 1 初判」…
210: …只落了 5 个探针输出…
212: …七项 CONFIRMED 一律按「phase 1 初判」引用…
$ grep -n "仅按 PARTIAL\|PARTIAL 采信" W7_W4_REVIEW/W7_W4_REVIEW.md   → 无命中（exit=1）
```

- 与 `:202-205` 转录**逐行一致**（含 `:30` 不是该 pattern 命中这一细节：我单独验证 `grep -n "…" | grep "^30:"` 无命中，`:30` 实际为「只按 PARTIAL 级信任采信」，不含四个 pattern 中任何一个）。
- ⇒ 「逐字统一限定句在汇总件中不存在」的否定性判断**有实跑 grep 支撑**，不是凭感觉。八条「部分落实」的缺口（`:44-47`）被逐条点名，符合 TASK.md §0 第 5 列要求。
- 口径对照：W9 `ERRATA_W9.md:22-24`、W8 `ERRATA_W8.md:22-25` 均把「汇总件」定义为**原组汇总正文**（W9/W8/W7 各自的 .md），W7 同样以 `W7_W4_REVIEW.md` 为「汇总件」——三组口径一致，未误指 `A1_ERRATA_MAP.md`。

## 4 是否偷偷重做 phase 2（重点 4）

**未发现。逐项实跑：**

```
$ grep -n "ra2tool\|Engine\|反汇编\|重跑\|重开\|phase 2\|复核意见\|_review.md\|探针" A1_ERRATA_MAP/ERRATA_W7.md
   → 全部命中均为「未重跑/禁止重开/本任务不反汇编它/存在性检查」等声明与限定句，无实质复核动作
$ find A1_ERRATA_MAP/ \( -iname "*w7*" -o -iname "*probe*" \) | sort
   → ERRATA_W7.md, _a1_g5_probe.py/out.txt, _a1_w9_probe.py/out.txt（无 W7 专用探针）
$ find W7_W4_REVIEW/ -name "*_review.md" | wc -l   → 0
$ ls -la W7_W4_REVIEW/reviews/
   → 恰好 5 个原始探针输出（19631 / 0 / 0 / 12697 / 589 B），零份 *_review.md
$ find W7_W4_REVIEW/ -type f -printf "%TY-%Tm-%Td %TH:%TM:%TS %p\n" | sort
   → 5 个探针输出 mtime 均为 2026-11-06 00:05–00:07（本任务开始前），W7_W4_REVIEW.md = 00:42
```

- `ERRATA_W7.md:17-20` 声明仅做「存在性/字节大小检查（`ls -la`/`find`）」且「5 个落盘件的内容一字未读」；`:188`「本勘误不授权任何形式的 W7 phase 2 重开」；`:218-221` 诚实账复述「未重跑、未复核、未顺便验证」+ 零真机/零采样/未用 `ra2tool.Engine`。
- `_a1_g5_probe.py:43,47` 只对 `W7_W4_REVIEW.md` 做 SHA256 绑定读取（只读字节），非 phase-2 复核；`_a1_w9_probe.py:2` 自述零 Engine。
- D-24 `RULING_D24.md:48,59,64,75,85-86` 明令禁止 Resume/Amend/换名重建 W7；回件未触碰。
- ⇒ **未触发「总判直接 REFUTED」条件**。

## 5 既有件是否被修改（重点 5）

```
$ git status --porcelain -- lead/GOAL_* lead/PENDING_DECISIONS.md lead/re_line_20261105/W7_W4_REVIEW/ … V6_V3_REVIEW/ D24_RULING/
MM lead/GOAL_THREE_TARGETS_20261018.md
MM lead/PENDING_DECISIONS.md
MM lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md
?? lead/re_line_20261105/V6_V3_REVIEW/   … ?? W7_W4_REVIEW/  … ?? W8_STATIC_LOCATE/  … ?? W9_SINGLESTEP_7CFC9F/
$ sha256sum <四份 .md>   → 会话开始与结束两次均为参照值（未变）
$ stat -c "%y %n" ra2youli/gamemd.exe   → 2026-09-25 16:10:48 +0800
$ stat -c "%y %n" A1_ERRATA_MAP/ERRATA_W7.md → 2026-11-06 08:27:14 +0800
$ git status --porcelain -- A1_ERRATA_MAP/  → ?? lead/re_line_20261105/A1_ERRATA_MAP/
```

- 四份被核 .md 的 SHA256 **本次会话首尾两次一致**；`gamemd.exe` mtime 停留在 2026-09-25；W7 判定书 mtime = 00:42（早于本任务 TASK.md 07:44）。⇒ W7 组未改被核对象。✓
- W* 树最新 mtime：W1–W5、W8、W10、W11 均 ≤ 04:43；W7 树唯一 ≥ 08:00 的文件是 `W7_W4_REVIEW/.mimosa/hook-status/...actor_3_1-….json`（08:27:15），我读其内容为 `{"toolName":"Write","file":"…/A1_ERRATA_MAP/ERRATA_W7.md","event":"PostToolUse","outcome":"clear"}`——安全扫描器对**写域内那次 Write** 自动产生的旁路记录，且 `.gitignore:22` 忽略 `.mimosa/`。**不是既有 W7 交付件被改**。同理 W9 树 08:58:52 的 `.mimosa` 记录来自 `W9_review.md` 的写入。
- **不归因于 W7 的观察（标记「未验」，不算 W7 违规）**：`lead/PENDING_DECISIONS.md` mtime = `2026-11-06 08:57:44 +0800`（保护名单内、`TASK.md:129` 明令只读），处于本任务窗口内；但 W7 回件 08:27:14 已定稿，晚 30 分钟，且 `git status` 在会话开始快照中已显示 `MM lead/PENDING_DECISIONS.md`（历史既有改动）。我查 hook-status 中提及 PD 的两条记录为 2026-10-23 / 2026-11-01（历史），**无法归因**本次 08:57 的写入主体。按「拿不到就写未验」：此改动**不指向 W7 回件**，供 Leader 另查。
- 我本会话未执行任何写、未 commit、未 push（除本复核件外）；`git status` 前后两次快照一致。✓

## 6 两处 leaderErrors 复核

1. **行号「:20-30」→ 实为 :20-27**：数据行确为 `:20-27`（`:18` 表头、`:19` 分隔、`:28` 空行、`:29-30` 备注行），源表我 `grep` 得 8 行 `:20-27`。**结论正确** ✓。但**出处归属有 imprecision**：`grep -n "20-30" A1_ERRATA_MAP/TASK.md` → **零命中**；TASK.md:16 只写「那张八行表 / 7 项 + A1」，未给行号。该字符串真实出处是 `lead/PENDING_DECISIONS.md:79`（G3 条目）与 `:121`，以及 `_a1_w9_probe_out.txt:97` 引 PD:79；D-24 `RULING_D24.md:50,59,75,85` 用的是 `:18-30`。故回件 `:22`、`:227` 说「**任务书**称 :20-30」不可在 TASK.md 上复现（详见 §7  objection 1）。**不影响结论**。
2. **`:4`「4 个探针」 vs `:210`「5 个」**：
   - `W7_W4_REVIEW.md:4`「只有 **4 个**探针输出落盘、其中 2 个是 0 字节」；`:210`「只落了 **5 个**探针输出、**2 个是 0 字节**」；§0 表 `:20-27` 列出 5 个落盘件。
   - 我 `ls -la W7_W4_REVIEW/reviews/` = **恰好 5 个文件**（`B2_probe_rerun_out.txt` 19,631 / `_b1_rerun_out.txt` 0 / `_b3_reprobe.txt` 0 / `_cprobe_rerun.txt` 12,697 / `_rerun_a1_out.txt` 589 B），`find … -name "*_review.md" | wc -l = 0`。
   - `find lead/re_line_20261105 \( -name "_rerun_a1_out.txt" -o … \)` → 仅 `W7_W4_REVIEW/reviews/` 下这 5 个，无副本（复现 §4-6）。
   - ⇒ **`:4` 的「4 个」为错，以 5 为准**，回件 §6-2 / §3-4 判定正确，且限定句不引用该计数，不影响八条。**此属真实 Leader 错误，回件发现并登记，加分项** ✓。

## 7 异议（objections）与 mustFix

**mustFix：[]** —— 八条应有的 7 项 + A1 全部逐条覆盖，无缺条；六列要素、头部 SHA 绑定、phase-2 禁令、只读铁律均无实质违反。TASK.md §5 的 PARTIAL/REFUTED 条件均未触发。

objections（均为非实质，登记备查，供 Leader 选用）：

1. **`:22` / `:227` 把「:20-30」归给「任务书」不可复现**：`A1_ERRATA_MAP/TASK.md` 无该字符串（我 `grep` 零命中）；真实出处 `PENDING_DECISIONS.md:79,121`，D-24 用 `:18-30`。建议改写为「PD:79/121（G3 条目）与 D-24 的 :18-30 行段把备注行计入」。行号订正结论 :20-27 本身正确。
2. **头部回件时刻与落盘时刻不一致**：`:9` 写 `2026-11-06 08:23:11 +0800`，而 `stat` 得文件 mtime `08:27:14`，hook-status `recordedAt = 00:27:15Z`（=08:27:15+0800）。TASK.md §4 要求「实际时刻」，差约 4 分钟；推测为草稿时刻，未验。不影响任何数值。
3. **「部分落实」判准比 W9/W8 更严（口径不一致但可辩护）**：W9 `:22`、W8 `:22-25` 用「修正后表述是否已在汇总件结论性正文写出（读汇总件即得修正口径）」的**语义**判准；W7 用**逐字串**判准（`:44-47` 以 `仅按 PARTIAL` 零命中判缺口），而汇总件 `:30` 已有语义等价的「只按 PARTIAL 级信任采信」、`:212` 已有「一律按 phase 1 初判 引用」。W7 补的正是「逐字可粘贴」句，标部分落实诚实且成立；若需三组口径统一，建议 W7 在 `:44` 补一句说明「语义已由 :30/:212 承接，本勘误只补逐字句」。
4. **跨组观察（非 W7 责任，标「未验」）**：① `A1_ERRATA_MAP.md`（TASK.md §3 要求的汇总件）在写域内 `find` 零命中，当前不存在；② `lead/PENDING_DECISIONS.md` mtime 08:57:44 落在任务窗口内（保护名单，只读），晚于 W7 定稿 30 分钟、写入主体查不到 ⇒ 不归因 W7，供 Leader 另查；③ W7 / W9 树内 `.mimosa/hook-status/*.json` 为 gitignored 扫描器旁路产物，非既有交付件改动。

## 8 诚实账（本复核员）

- **实跑**：`sha256sum`×2（首尾）、`wc -c`、`grep`×多组（表行 / 限定句 / §4-4 精确 pattern / 逐 pattern 隔离）、`ls -la`×3 目录、`find`×4（mtime / `*_review.md` / 五个探针名 / 汇总件存在性）、`stat -c`、`git status --porcelain`、`git diff --stat`、`git check-ignore -v`、`date`、`python -I -X utf8 -c`（仅只读打印 PENDING_DECISIONS.md 两行与一个 hook-status JSON）。
- **Read 全文**：`A1_ERRATA_MAP/TASK.md`、`A1_ERRATA_MAP/ERRATA_W7.md`、`W7_W4_REVIEW/W7_W4_REVIEW.md`；`grep` 抽查 `ERRATA_W9.md` / `ERRATA_W8.md` / `RULING_D24.md` / `PENDING_DECISIONS.md`。
- **未做（且被禁止）**：零真机、零采样注入、未读活进程内存、**未用 `ra2tool.Engine` 一次**、未对八项做任何实质复核 / 反汇编 / phase 2 补跑、未读 5 个探针输出内容；未 commit / push；未改任何既有件。
- **未验项（诚实登记）**：①「自己实算」的执行主体无法由静态文件证明（仅数值与转录可复现）；② `PENDING_DECISIONS.md` 08:57:44 写入主体无法归因；③ 回件时刻 08:23:11 与 mtime 08:27:14 的 4 分钟差原因。三者均不影响总判。
- **唯一写入** = 本文件 `A1_ERRATA_MAP/reviews/W7_review.md`。
