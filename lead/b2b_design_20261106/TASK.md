# TASK · D-25 第 1 步 · B2b 修正版设计

**派发**：2026-11-06 14:5x，总控会话。**模型**：`magpie/work/cn:hy4free$high`。**max_concurrency=2**。
**授权依据**：**D-25 裁决书**（`lead/d25_ruling_20261106/RULING_D25.md`）第 2 节「立即可安排范围**止于**新指定写域内的 B2b 设计和独立设计预审」、第 3 节 order 第 1–2 步。
**唯一写域**：`lead/b2b_design_20261106/`（新建目录，只写此目录内的新文件）。

---

## 0 一句话

上一版设计 `B2_FIX_DESIGN.md` 被独立预审判 **NO**（`lead/b2_preaudit_20261106/B2_PREAUDIT.md`）。
你的任务是写 **B2b**：**完整、可直接套用**的修正版设计，把预审指出的每一处缺口都补成真代码。

**这不是「再写一份设计文档」，是「写完就能交给候选实现者照抄」。**
B2 最致命的毛病就是「只在表格里说要改，没有真 diff」。

## 1 现状与基准（开工前必须重算，不许抄本文）

| 对象 | 路径 | 预期指纹 |
|:--|:--|:--|
| 正式母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` / `399508` B |
| 被否的旧设计 | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` / `11638` B |
| 语义参考（**不是基线**） | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py` | 13,190 B |

**★ 开工第一步**：用 `python -I -X utf8 -c "import hashlib,sys;d=open(sys.argv[1],'rb').read();print(hashlib.sha256(d).hexdigest(),len(d))" <路径>`
实算这三个文件。**母本指纹不符 ⇒ 立即停止**，写 `STOP_MOTHER_DRIFT.md` 并结束（旧行号全部作废）。

**★ 注意**：`sha256sum` / `wc` 在本机 `world.run` 里 **不存在**（Windows 直接 spawn，无 shell），一律用 python。

## 2 B2 被否的原因（必须逐条根治，不许换个说法糊过去）

预审 23 条判定。以下是**必须解决的**，每一条你都要在 B2b 里给出可验证的答复：

| 编号 | 问题 | B2b 必须做到 |
|:--|:--|:--|
| **E1** | `_pre_freshness_snapshot` 在 B2 全文**零次赋值**；`main` 有 **5 个早退 `return`**（`:6340/:6349/:6361/:6374/:6377`）全部早于 `:6387`，`finally`（`:7038`）仍会走到 `:7117` 调用 ⇒ 未绑定名字风险 | **快照变量必须在所有引用之前定义**（建议 `try` 之前预初始化为 `None`），且**五个早退路径**各自明确：走哪条分支、输出什么、不留未绑定名 |
| **N5** | 母本 `:5939` 是 `copy_post_except_evidence` 的**唯一真实调用点**（本文件内），B2 **没给它 diff** ⇒ 签名加了参数却没人传 | **必须给出 `:5939` 的完整 diff**，并且**必须逐行核对母本 `:5938-5939` 的实际文本**再写 |
| **N4** | 正常路径算完 `_fresh` 后 `:163` 直接接 `blob = src.read_bytes()`，**一个字段都不落盘** ⇒ 补丁空转 | **正常与错误两条分支都要有字段落盘**，给出 `info` 字典的完整新形态与写入位置的 diff |
| **N6** | `freshness_confidence`/`freshness_note`/`captured_at_iso` 在 B2 全文**各 0 次** | 明确每个字段的**名称、类型、取值域、写入点**；缺一不可 |
| **N3** | `{}` / `None` / `{"exists": False}` 被**折叠成同一状态**并恒给 `high` | **必须三态可分**：`unknown`（未采集）/ `absent_confirmed`（确认无件）/ `present`。**禁止未知默认等于不存在** |
| **N1** | 异常路径静默降级 | 采集异常必须有**独立出口**（不是 `high`） |
| **N2** | 遗留件恒判 `new_first_appearance/high` | 快照缺失时**不得**输出高置信「本趟新出现」 |
| **N7** | B2 说「四处是最小集」，但 §2 列 8 个物理改动而只有 4 个 hunk | **改动清单与 hunk 必须一一对应**，不许清单里有、diff 里没有 |
| **N10** | `captured_at_iso` 与「复制失败显式留痕」被静默删掉 | 恢复；复制失败须 `rec.add("ERROR", ...)` 后再上抛，不许静默 |
| **N9** | `:205` 声称「F 只回答新鲜性、E 仍是唯一口径」但无实现约束 | 给出 **F/E 分离的实现级约束**：字段命名、group、**不得进入退出码判据** |

## 3 硬性设计要求

### 3.1 五类状态必须可分

参照 W11 候选的**出口结构**（`candidate/except_freshness.py` 的 `VERDICT_DOC:39-47`、
`error_pre_snapshot:157/207`、`is_new=None:202`、`absent_both low:189`），
**但不要照搬它的缺陷** —— 裁决书已指出 W11 自己在 `:154/:181/:187/:193` 也把 `None`/`{}` 折叠了。

你的 B2b 必须**明确区分**：

1. **unknown**（跑前快照未采集/采集失败）—— 不可判，**不得**给 `high`
2. **absent_confirmed**（跑前确认无件）
3. **present + sha 一致 + mtime 未变** → `leftover_unchanged`
4. **present + sha 不同** → `new_write`
5. **present + sha 同 + mtime 变** → `rewritten_same_content`
6. **present + 缺 sha** → 独立出口
7. **跑后无件 + 跑前有** → `vanished`（须 **人工复核**，不给 `high`）
8. **跑后无件 + 跑前无** → `absent_both`（`low` + 「不能证无崩溃」）

### 3.2 五个早退路径逐条覆盖

母本 `main` 在 `:6387` 之前有 5 个 `return`：`:6340/:6349/:6361/:6374/:6377`。
你要给出**一张表**：每一行 = 一个早退路径 → 快照的值是什么 → `finalize_trip` 拿到什么 → 输出什么 verdict → 会不会崩。
**外加**：`try` 内抛异常的路径、`finally` 内 `:7048` 到 `:7117` 之间失败的路径。

### 3.3 F/E 分离

母本 `:672-708` 是 `except_set_diff`，`:677` 明令「**不得用 sha 变化判 crash**」，`:5985-5990` 是唯一影响退出码处。
你的 B2b 必须写清：新字段写进哪个 group、**哪一行代码保证它不进退出码判据**、用什么测试证明。

### 3.4 完整 diff

**每一个改动点都要有可套用的 `@@` hunk**，包含足够上下文（≥3 行）。
**hunk 数量必须等于改动清单条数。** B2 就死在这（清单 8 条、hunk 4 个）。

## 4 交付物（全部写进 `lead/b2b_design_20261106/`）

1. **`B2B_DESIGN.md`** —— 主设计文档，必须含：
   - 头部：母本 / 旧 B2 / W11 候选的**实算 SHA256 + 字节数**（三个都要）；
   - 「## 1 B2 被否的十条如何逐条根治」—— 十条各一小节，每条给 **diff 行号**；
   - 「## 2 状态矩阵」—— 3.1 那 8 种状态 × 输入条件 × 输出 verdict × 置信 × 是否可判；
   - 「## 3 早退与异常路径覆盖表」—— 3.2 那张表，7 行以上；
   - 「## 4 完整 diff」—— 全部 hunk，带行号锚点；
   - 「## 5 字段契约」—— 每个新字段的名称/类型/取值域/写入点/消费方；
   - 「## 6 F/E 分离的实现级约束」；
   - 「## 7 改动清单 ↔ hunk 对照表」—— 条数必须相等；
   - 「## 8 未验与已知限制」。
2. **`_b2b_probe.py` + `_b2b_probe_out.txt`** —— 你用来**核母本真实行号与文本**的脚本与输出。
   **★ 凡 diff 里出现的行号，都必须能被这个探针打印出来对上。**
3. **`STATE_MATRIX.json`** —— 状态矩阵的机器可读版，供门禁与后续候选实现者使用。
4. **`review/B2B_DESIGN_REVIEW.md`** —— 独立复核（见 §6）。

## 5 硬性纪律

1. **零真机**、**零采样代码**、不 commit、不 push。
2. **只读**：`ra2youli/**`、`out/re_work/**`、`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md` 一律不改。**母本一个字节都不许动**（你只写设计，不写候选）。
3. `python -I -X utf8`，绝对路径。
4. 引用追到「文件:行」或「实算输出」；拿不到写「未验」。
5. **★ 不许写没 diff 的「将修改」**。清单里每一条都要能在 diff 里找到。
6. **★ 不许把「未知」默认当「不存在」**。这是 B1/B2 两轮反复犯的病。

## 6 独立复核（必做）

写完后让一个**新上下文**做复核员，任务是：
- **逐条**打开 `B2B_DESIGN.md` 每个 hunk 的行号锚点，核母本原文是否真在那里；
- 亲自重跑 `_b2b_probe.py`，核输出一致；
- **专项检查 A**：改动清单条数 vs hunk 条数是否相等（不等就判 NO）；
- **专项检查 B**：状态矩阵里有没有把 `unknown` 映射到 `high` 置信（有就判 NO）；
- **专项检查 C**：五个早退路径是否都有覆盖行（缺一条就判 NO）。

复核件 `review/B2B_DESIGN_REVIEW.md`，含 `subjectSha256` / `subjectBytes` / `checkedEveryRow` / `hunksMatchManifest` / `earlyReturnsCovered`（5/5）。

## 7 确定性门禁

写 `check_b2b.py`，`python -I -X utf8` 跑，检查：
- 三个指纹（母本/旧 B2/W11）都在头部，格式为 64 位 hex + 字节数；
- 「## 1」下**十条**都有 `####` 标题（E1/N5/N4/N6/N3/N1/N2/N7/N10/N9 或等价编号）；
- 「## 3」表格 ≥ 7 行；
- `STATE_MATRIX.json` 可解析，含 ≥ 8 个状态，且**不存在** `unknown` → `high` 的映射；
- 「## 7 改动清单 ↔ hunk 对照表」的行数 == 设计里 `@@` hunk 的数量；
- 「## 8 未验与已知限制」非空；
- `review/B2B_DESIGN_REVIEW.md` 存在且 `checkedEveryRow: true`、`hunksMatchManifest: true`、`earlyReturnsCovered: 5/5`。

退出码 0 = PASS。**exitCode 与完整输出写进交付说明。**
