# TASK · N-2 · B2 设计独立预审

**派发**：2026-11-06 11:4x，总控会话。**模型**：`magpie/work/cn:hy4free$high`。**max_concurrency=2**。
**上游依据**：`lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` 的 N-2；D-24 定谳 B 步。
**唯一写域**：`lead/b2_preaudit_20261106/`（新建目录，只写此目录内的新文件）。

---

## 0 背景（写给第一次看到这件事的人）

本项目的主体是一份 Python 真机趟驱动器 `qc151_trip.py`（7,291 行 / 399,508 B），
它在每趟跑完后会把 `except.txt` 等崩溃证据复制到输出目录。W11 的核查结论是：
**这个复制逻辑 `copy_post_except_evidence` 全链零新鲜性检查** —— 旧异常件会被反复当作本趟的证据复制进来，
导致「这趟崩了」的误判。这是**实现缺陷**，已在 W11 定为 CONFIRMED。

上一轮 B1（`lead/re_line_20261105/B1_HARNESS_PATCH/`）拿 W11 的候选补丁去集成，
被预审硬门判 **`shouldApply = NO`**，列出六条领队错误。随后领队手写了修复版设计
`B2_FIX_DESIGN.md`，但**该设计至今没有任何独立预审**，且它自己第 196-207 行明写
「本文件只是设计，应用前必须重新走一遍 B1 的预审硬门」。

**你的任务就是当这道硬门。**

## 1 要被审的东西

| 角色 | 文件 |
|:--|:--|
| 被审设计 | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md`（237 行） |
| 上一轮否决记录 | `lead/re_line_20261105/B1_HARNESS_PATCH/PRE_AUDIT.md`（195 行，六条 error 在 `:117/:131/:144/:154/:162/:168`） |
| 上一轮的旧任务书 | `lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md`（135 行，含已被 B2 判定要作废的三处限制） |
| 正式母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` |
| 新鲜性语义来源 | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/W11_EXCEPT_FRESHNESS.md` |

**母本基准指纹**（自己实跑核对，不许抄这句）：
`sha256sum` 应为 `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`，
`wc -c` 应为 `399508`。**若不符 → 立刻 STOP，写 `STOP_MOTHER_DRIFT.md` 并结束，不要继续审。**

## 2 必须逐条判定的六条旧错误

B2 自称已修六条，你要**逐条独立验证它是否真修好了**，不许采信它的自述：

| # | 旧错误 | 你要验什么 |
|:--|:--|:--|
| 1 | 作用域断裂（`main` 局部变量在 `finalize_trip` 里引用） | B2 的传参方案是否真能把快照送到 `_except_evidence_copy`；签名改动后所有调用点是否都改了 |
| 2 | `exists` 键缺失 ⇒ 100% 误判 | `bak[name]` 写入侧是否真写了 `"exists": True`；判定侧读的键名是否与写入侧一致 |
| 3 | `mtime_pre` vs `mtime` 键名不匹配 | 逐键核对，不许目测 |
| 4 | 规约死锁（不许改 `finalize_trip` 签名，但合法接线必须改） | B2 是否已放开签名并同步改旧 TASK 的三处限制 |
| 5 | 早退截断（判定内联在 `return None` 之后） | 判定是否真的提到早退之前；早退路径能否输出新鲜性结论 |
| 6 | `git diff` 要求与 `.gitignore:33` 矛盾 | B2 是否删净 `git diff` 要求，换成文件级 diff |

## 3 还要找 B2 自己引入的新问题

不要只验它声称修的六条。**专门找**：
- 新签名传参在**异常路径**（早退、捕获异常、初始化前收尾）上是否会拿到 `None` 而静默降级；
- 判定分支是否出现「空快照 `{}`」与「显式 `exists=False`」语义不等价；
- 改动面从三处扩到四处（B2 `:118`）后，**是否有第五处该改而没改**；
- `freshness_verdict` 是否越界侵占 `except_set_diff` 的 E 口径（B2 `:205` 自己点了这条）。

## 4 硬性纪律

1. **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存。
2. **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
3. **只读母本**：`out/re_work/` 下的 `qc151_trip.py` **只读，一个字节都不许改**。你只在 `lead/b2_preaudit_20261106/` 里写新文件。
4. **只读既有件**：`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、`ra2youli/**` 一律不得修改。
5. 不 commit、不 push。
6. Python 一律 `python -I -X utf8`，绝对路径。
7. **引用必须追到「文件:行」或「实跑命令+输出」**；拿不到就写「未验」，不许补造。
8. **否定性/存在性事实先用 `find`/`ls`/`grep`/`sha256sum` 核**，不要上全仓 Python 遍历或反汇编引擎。
9. 执行者 ≠ 核验者：你的每条判定都要有一道独立复核（见 §6）。

## 5 交付物（全部写进 `lead/b2_preaudit_20261106/`）

1. **`B2_PREAUDIT.md`** —— 主判定书，必须含：
   - 头部：被审设计 `B2_FIX_DESIGN.md` 的**实算 SHA256 + 字节数**，母本的**实算 SHA256 + 字节数**；
   - `verdict: YES | NO`（YES 只放行「制作完整候选」，**不放行正式应用**）；
   - 六条旧错误逐条判定表：`已修 / 未修 / 部分修`，每条给出**文件:行**证据；
   - 新增问题清单：每条给 `severity`（high/medium/low）+ 文件:行 + 一句话后果；
   - 若 NO：列出**责任角色**（设计者/任务书作者/候选实现者）、阻断项、以及「再提交一次需要什么证据」；
   - 「未验」清单：你没能核的项目，逐条说明为什么。
2. **`_b2_probe.py` + `_b2_probe_out.txt`** —— 你用来核键名/签名/调用点的**实际脚本与真实输出**（不许手写结论不跑）。
3. **`review/` 子目录** —— 独立复核员的回件。

## 6 独立复核（必做）

写完后，让一个**没有参与上面审查的新上下文**做复核员，任务是：
- 亲自打开 `B2_PREAUDIT.md` 里每条「文件:行」断言，核它是否真的说了那句话；
- 亲自重跑 `_b2_probe.py`，核输出是否一致；
- **专项检查**：被审设计有没有被「超额放行」（把设计 YES 写成应用 YES）。

复核回件写 `review/B2_PREAUDIT_REVIEW.md`，必须含**被核对象 SHA256 + 字节数**（铁律 9），
并给 `checkedEveryRow: true/false`。**复核判 NO 或 checkedEveryRow=false ⇒ 主判定书不得为 YES。**

## 7 确定性门槛

写一个 `check_b2_preaudit.py`，用 `python -I -X utf8` 跑，检查：
- `B2_PREAUDIT.md` 存在且含六条错误逐条判定（6 个条目标题齐全）；
- 头部含两个 SHA256（64 位十六进制 × 2）与两个字节数；
- 含 `verdict:` 行且值为 YES 或 NO；
- 含「未验」小节且非空；
- `review/B2_PREAUDIT_REVIEW.md` 存在且含 `checkedEveryRow:`；
- 若 verdict=YES，则 review 的 checkedEveryRow 必须为 true。

退出码 0 = PASS。**把 exitCode 与完整输出写进交付说明。**
