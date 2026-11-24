# D-25 条目草案（待用户批准后并入 `lead/PENDING_DECISIONS.md`）

> **本文件是条目草案，不是正式条目。** `lead/PENDING_DECISIONS.md` 属只读件，
> 本会话（总控）未获用户明示前不写入。批准后由本会话把下面「条目正文」整段并入
> 该文件待裁段，编号 **D-25**（当前最大 D-24，+1 无冲突）。

---

## 编号冲突核对

实跑 `grep -o "D-[0-9][0-9]" lead/PENDING_DECISIONS.md | sort -t- -k2 -n | uniq | tail -6`
→ `D-19 D-20 D-21 D-22 D-23 D-24`。**最大 = D-24，本次取 D-25，未复用。**

---

## 条目正文

- **D-25（2026-11-06 立，来源=总控会话，N-2 预审结果）**：**B2 设计被判 `verdict: NO` 之后，B 链下一步走哪条**。

  **背景（全部有据可查）**：
  - D-24 定谳执行顺序 **A > B > D > C**。A 已于 2026-11-06 收官
    （`lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md`，总判 PARTIAL）；
    其残余引用已由 N-1 固定成账（`lead/a_residual_20261106/`，17 条，CONFIRMED 12 / PARTIAL 5）。
  - **B 链首件 N-2（B2 设计独立预审）判定 `verdict: NO`**
    （`lead/b2_preaudit_20261106/B2_PREAUDIT.md`，28,410 B；被审设计
    `B2_FIX_DESIGN.md` = `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` / 11,638 B）。
    判定书经独立复核 `checkedEveryRow=true`、`overreachFound=false`；
    确定性门禁 `python -I -X utf8 lead/b2_preaudit_20261106/check_b2_preaudit.py` → `EXIT=0`。
  - **判 NO 的两条独立理由**（任一条即足）：
    1. 六条旧错中 **E1 = NOT_FIXED**：`_pre_freshness_snapshot` 在设计全文**零次赋值**，
       而母本 `main` 有 5 个早退 `return`（`qc151_trip.py:6340/6349/6361/6374/6377`）
       全部早于 `:6387`，`finally`（`:7038`）无条件进 `:7117` ⇒ 早退/异常路径必抛
       `UnboundLocalError`，收尾链被打崩、原异常被替换；
    2. **5 条新增 `severity=high`**，其中两条致命：
       - **N5**：真正要改的调用点 `qc151_trip.py:5939` 在设计里**没有任何 diff hunk**
         （全文只有 4 个 hunk：`:43/:52/:75/:128`），签名加了 `pre_snapshot=None` 却没人传
         ⇒ 所有趟（含正常趟）走静默降级；
       - **N6**：`§2:186` 声称 info「加 4 个键」，实算 `freshness_confidence` / `freshness_note` /
         `captured_at_iso` 在设计全文**各出现 0 次**，`freshness_verdict` 仅 `:205` 一句断言
         ⇒ 正常路径算完 `_fresh` 后 `:163` 直接接 `blob = src.read_bytes()`，**一个字段都不落盘**，
         W11 要修的核心场景等于空转。
  - **语义倒退**：B2 删掉了 W11 候选已有的三个出口 —— `error_pre_snapshot`（显式留痕）、
    `is_new=None`（不可判）、`absent_both` 的 `low` 置信。
    对照 `W11_EXCEPT_FRESHNESS/candidate/except_freshness.py:47/157/191/202/207`，
    B2 把 `vanished` 标成 `high`（候选是 `is_new=None` 须人工复核）、
    把 `{}` 与 `{"exists": False}` 折叠成同一状态并恒给 `high`。
    ⇒ 不是「没修好」，是**把「不敢判」升级成「高置信地判错」**，且会踩母本 `:677` 禁令。
  - **判定书自身有 6 处引用错误**（复核员抓出，如 N5「全仓唯一调用点」实为 22 处、
    `:52-64` 并未省略实参），**但不改变 `verdict: NO`**。

  **请裁（四选一）**：
  **(A)** **重做 B2b（修正版设计）**：在 B2 基础上补三处真 diff
      （① `main` 内 `:6387` 后构造快照并做 try 前预初始化；② `:5939` 调用点传参；
      ③ `:4583-4586` info 增 4 键），并恢复 `error_pre_snapshot` / `is_new=None` 出口。
      **代价**：等于重写设计的一半；**收益**：沿用 B2 已通过的 E3/E4/E6 部分。
  **(B)** **放弃 B2，以 W11 候选为基线重做集成设计**：
      `candidate/except_freshness.py`（13,190 B，14 测全绿）语义更完整（有 error/None 出口），
      只是从未集成进母本。新设计直接规定「如何把该候选的函数体搬进 `copy_post_except_evidence`
      并接线」，不复用 B2 文本。**代价**：弃掉 B2 已有工作；**收益**：语义基线正确，改动面更小。
  **(C)** **暂停 B 链，先走 D 链**（N-7 五读负担复算 / N-8 慢窗统计核对，零授权纯离线）。
      **代价**：目标②的观测缺陷继续存在；**收益**：不动母本，零风险推进目标①。
  **(D)** 其它顺序（请显式写出先后与理由）。

  **另请一并裁**：
  1. 上述某条若选 (A)/(B)，**是否只批「编写候选设计 + 离线单测」**、真机发射另批一次？
  2. **D-24 是否归档**（已定谳 A>B>D>C，条目仍挂在待裁段，属状态未同步）；
  3. **D-13 / D-14 本轮是否一并给处置建议**（我无权代裁；D-24 裁决书只给了建议：
     D-13 维持暂停、D-14 建议选 C 双口径并列）。

  **本线倾向**：**(B) 或 (C)**。理由：B2 被否得彻底（E1 完全未修 + 5 条 high + 语义倒退），
  重写量可能超过重做；而 W11 候选本身语义更完整、已有 14 测背书。
  **但这只是建议，不是裁决。**

  **证据**：`lead/b2_preaudit_20261106/B2_PREAUDIT.md` + `_b2_probe_out.txt`（16,296 B）
  + `review/B2_PREAUDIT_REVIEW.md`；
  `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md`；
  `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py`；
  `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md`（N-2/N-3/N-5）；
  `lead/re_line_20261105/D24_RULING/RULING_D24.md:7,:52,:61,:77`。
