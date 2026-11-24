# B2B_DESIGN.md · D-25 第 1 步 · B2b 修正版主设计（唯一合并稿）

**角色**：B2b 主设计的唯一作者。**日期**：2026-11-06。
**唯一写域**：`lead/b2b_design_20261106/`。**产出**：本文件 + `STATE_MATRIX.json`（本次分工只这两个交付物）。
**边界**：母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` 一个字节未改；`ra2youli/**`、`out/re_work/**`、`lead/re_line_20261105/**`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md` 只读；零真机、零采样代码、不 commit、不 push；Python 一律 `python -I -X utf8` 绝对路径。
**本稿不是候选**：`patched` 文本只存在于检查脚本的内存里，`ast.parse` 后即丢弃，未写出任何候选 `.py`。

---

## 头部三件实算指纹（本会话重算，不抄派发材料）

**实算命令**（本机无 `sha256sum` / `wc`，用 `hashlib` 读二进制后取 `hexdigest()` 与 `len()`）：

```
python -I -X utf8 -c "import hashlib,sys
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    print(hashlib.sha256(d).hexdigest(), len(d), len(d.splitlines()), p)" <三个绝对路径>
```

**实算输出**（`sha256 / 字节数 / splitlines 行数 / 路径`）：

```
517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 399508 7291 D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f 11638 236 D:/Project/ra2-campaign-forge/lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md
e6685167f5d26030f9a2e28df06ee2fbda23c7e91687aa209f6769ac3450480b 13190 278 D:/Project/ra2-campaign-forge/lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py
```

| 对象 | 路径 | SHA256（64 hex） | 字节数 |
|:--|:--|:--|--:|
| 母本 `qc151_trip.py` | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | `399508 B` |
| 被否的旧 B2 | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | `11638 B` |
| W11 候选（语义参考，**不是基线**） | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py` | `e6685167f5d26030f9a2e28df06ee2fbda23c7e91687aa209f6769ac3450480b` | `13190 B` |

母本指纹与 `lead/b2b_design_20261106/TASK.md:21` 预期值一致 ⇒ **未触发 STOP**，未写 `STOP_MOTHER_DRIFT.md`。`TASK.md:23` 只给 W11 的 13,190 B（本次实算一致），**未给 W11 的 SHA256**；本稿补齐其 SHA256 供复核员对照。

**结构锚点依据**：`_b2b_probe_out.txt:1-182`（探针 `_b2b_probe.py` 用 `ast.parse` + 逐行文本比对实测，10 项全部命中）；`_draft_semantics_anchors_out.txt:1-61`（逐锚点打印母本原文）；本会话另实读 `qc151_trip.py:167-175`、`:416-455`、`:672-708`、`:4447-4462`、`:4498-4534`、`:4561-4615`、`:5930-5950`、`:5978-5992`、`:6020-6053`、`:6290-6315`、`:6334-6392`、`:6440-6450`、`:6472-6482`、`:6492-6500`、`:7017-7025`、`:7028-7136`。

---

## 0 说明（本设计只到「可交给候选实现者」，不等于可应用到母本）

1. **本设计的终点是「候选实现者可照抄」**：§4 的 9 个 `@@` hunk 可直接按序套用到上述指纹的母本副本上；§7 的 9 行清单与之一一对应；§5 给出每个新字段的完整契约；§2/§3 给出状态与路径覆盖。**它不等于「已获准应用到母本」**——D-25 裁决书 `RULING_D25.md:21` 明确「立即可安排范围止于新指定写域内的 B2b 设计和独立设计预审」，候选编写、隔离副本集成须由来源会话逐项另派写域（`RULING_D25.md:34-37`，`TASK.md:102`）。
2. **验收口径**：改动清单里的每一条，都能在同文件的 diff 里找到对应 hunk。本稿 §7 共 9 行数据、§4 共 9 个 `@@ ` 头；专项检查 A 在本会话重跑 `verify` 得 `§7 清单数据行 = 9 ；设计稿 hunk 数 = 9 → PASS`（见 §6 实跑账）。
3. **两路设计稿的实际合并来源**：派发材料称两路稿为 `_draft_scope.md` 与 `_draft_semantics.md`。本会话执行 `find lead/b2b_design_20261106 -maxdepth 2 -type f` 与 `find . -name "*_draft_scope*"`，**均无任何 `_draft_scope*` 文件**；目录内只有 `_draft_semantics.md`（52,841 B）及其检查脚本/输出。因此不存在「两稿互相矛盾」的可比对材料，本稿以 `_draft_semantics.md` 的 9 个已验证 hunk 为唯一设计骨架，以 **D-25 裁决约束**为准做取舍；逐项登记见 §8 第 3 条。
4. **零真机、零运行时复现**：本稿所有「不会崩 / 不会进退出码」结论均为母本实读 + 内存 `patched` 的 `ast.parse` / 静态禁词断言 / 离线合成字典单测所支持的结构性结论，**不是运行时复现**。未运行 `qc151_trip.py` 本体，未启动任何游戏进程。
5. **W11 只借出口结构**：`TASK.md:23` 明示「语义参考（不是基线）」；`RULING_D25.md:13` 指出 W11 自身在 `:154/:181/:187/:193` 也把 `None`/`{}` 折叠。本稿不照搬该折叠，`state` 四态由 H03 独立实现。
6. **本分工未产出**：`review/B2B_DESIGN_REVIEW.md`（`TASK.md:97`）与 `check_b2b.py`（`TASK.md:121`）属其他分工；本会话实查全仓无此二文件。`TASK.md:128` 的完整门禁若要求该复核件存在，按现状**不会 PASS**，如实记为「未验」，不伪造复核结论。

---

## 1 B2 被否的十条如何逐条根治

十条编号与要求来自 `TASK.md:34-45`（本会话实读）；根因另可参 `lead/b2_preaudit_20261106/B2_PREAUDIT.md:28`（本会话 grep 实见 `#### E1 作用域断裂`）。以下每条**只指认 §4 里已给出的 hunk**，没有「将修改」；括号内给「§4 第几个 hunk / 该 hunk 的 `-<起始>,<数> +<起始>,<数>` 头 / 母本 1-based 锚点」，即 diff 行号。全文 H 编号以 §7 表与 §4 实际 hunk 顺序为唯一口径（H01–H09，无 H10）。

#### E1 快照零赋值 / 早退未绑定

**根因**（`TASK.md:34`）：`_pre_freshness_snapshot` 在旧 B2 全文零次赋值，主调用点却传裸名；`main` 的 5 个早退 `return`（`:6340/:6349/:6361/:6374/:6377`）全部早于 `:6387`，`:7038 finally` 仍可能走到 `:7117` 调用。按 **D-25 §5 第 1 条**（`RULING_D25.md:52`）把风险口径限缩为「无赋值裸名存在 `NameError` 风险；补了局部赋值但早退绕过时才可能为 `UnboundLocalError`」，**不写「必抛 UnboundLocalError」、不写「finally 无条件进 :7117」**。

**根治（4 个 hunk 构成完整作用域链）**：
- **H07**（§4 #7，`-6294,6 +6523,9`；母本 `:6296` 后、`:6313 try:` 前）预初始化 `_pre_freshness_snapshot: dict | None = None`，注释写明 `None` 语义 = **未采集（unknown）**，绝不等于「跑前无件」。
- **H08**（§4 #8，`-6386,6 +6618,15`；母本 `:6388` 后，载体备份完成、launch 前）才真正调用 `make_pre_freshness_snapshot(...)` 赋值，并落 `FRESHNESS.captured_at_iso_pre`。
- **H05**（§4 #5，`-5906,7 +6133,8`；母本 `:5909`）`finalize_trip` 增加同名形参。
- **H09**（§4 #9，`-7122,7 +7363,8`；母本 `:7125` 后）把已绑定的名字传入 `:7117 finalize_trip`。

母本 `:6293-6296` 已有 `bak: dict = {}` / `t0: list = []` / `pre_except_txt = None` 的同类预初始化先例（本会话实读 `:6293-6296`）。五个早退逐行覆盖见 §3 P1–P5。

#### N5 唯一调用点 `:5939` 无 diff

**根因**（`TASK.md:35`）：`:5939` 是 `copy_post_except_evidence` 全文件唯一真实调用点。探针 `[3]`（`_b2b_probe_out.txt:48-58`）实测：文本出现 2 处（`:4561` def、`:5939` 调用），AST 调用点个数 **1**，实参 `['rec', 'carrier_dir', 'out_dir']`，关键字实参 `[]`；`:5938-5939` 原文见 `_draft_semantics_anchors_out.txt:31-32`。

**根治**：**H06**（§4 #6，`-5936,7 +6164,8`；母本 `:5939`）把该行改成两行关键字传参 `pre_freshness_snapshot=pre_freshness_snapshot`；**H03**（§4 #3，`-4558,8 +4577,131`；母本 `:4561-4562`）同步给 def 加同名形参。签名与唯一调用点闭合，不再「全趟恒走默认降级」。

#### N4 正常路径算完不落盘

**根因**（`TASK.md:36`；`B2_PREAUDIT.md:82-84` 转引自语义稿）：旧 B2 算完 `_fresh` 后一个字段都不落盘；母本 `:4583-4586` 的 `info` 仍 5 键（探针 `[9]`，`_b2b_probe_out.txt:143-161`）。

**根治**：**H04**（§4 #4，`-4572,20 +4714,105`；母本 `:4574-4599`）把函数体重写成**三条出口全部落盘**：
- 正常路径：`info` 从 5 键扩到 **12 键**（新增 `mtime_post` / `freshness_verdict` / `freshness_confidence` / `freshness_note` / `captured_at_iso` / `pre_snapshot_state` / `pre_freshness_snapshot` 七键），先 `rec.add("EXCEPT", "evidence_copy", info, ...)` 再 `_emit_f(fresh, "copied")`；
- `src_missing` 早退分支：`_emit_f(..., "src_missing")`；
- `copy_failed` 异常分支：`_emit_f(..., "copy_failed")` 后 `raise`。

`_emit_f` 每次固定写 7 个 `FRESHNESS` group 字段；本会话实算 `F 区 FRESHNESS_GROUP 写入次数: 7`。`info` 的完整新形态与写入点见 §5。

#### N6 字段全缺（名称 / 类型 / 取值域 / 写入点）

**根因**（`TASK.md:37`）：`freshness_confidence` / `freshness_note` / `captured_at_iso` 在旧 B2 全文各 0 次。

**根治**：**H01**（§4 #1，`-212,6 +212,21`；母本 `:214` 后）定义 5 个**单一真源常量** `FRESHNESS_GROUP` / `FRESHNESS_KEY_PREFIX` / `FRESHNESS_VERDICTS` / `FRESHNESS_CONFIDENCES` / `FRESHNESS_SNAPSHOT_STATES`；**H03/H04** 写入三字段；**H08**（§4 #8）单独落 `FRESHNESS.captured_at_iso_pre`。`captured_at_iso` 双份：跑前在快照 `make_pre_freshness_snapshot` 内（H03），跑后在 `post_observed` 与 `info`（H04）。完整契约表见 §5（每个字段的名称 / 类型 / 取值域 / 写入点 / 消费方齐全）。**纠偏**：语义稿 §1 N6/N10 把 `captured_at_iso_pre` 归给 H09，本稿按 §7 表与 §4 #8 实码纠正为 **H08**（§8 第 3 条取舍 C）。

#### N3 三态折叠 / 未知当不存在

**根因**（`TASK.md:38`）：`{}` / `None` / `{"exists": False}` 被折叠成同一状态并恒给 `high`。

**根治**：**H03**（§4 #3，`-4558,8 +4577,131`）的 `make_pre_freshness_snapshot` 用 `state` 作**唯一判别口**（`unknown / absent_confirmed / present / error` 四态，取值域由 H01 的 `FRESHNESS_SNAPSHOT_STATES` 单一真源给出），`exists` 不得反推状态；`classify_except_freshness` 首段把 `None` / `{}` / 缺 `state` / 脏值一律归一为 `unknown`，且在**第一个分支**就让 `unknown` 与 `absent_confirmed` 分道。**H07**（§4 #7）把预初始化值显式注释为「未采集（unknown），绝不等于跑前无件」。

本会话重跑 `python -I -X utf8 .../_draft_semantics_check.py matrix` 的输出（`_draft_semantics_matrix_out.txt:4-7`）：

```
  pre=None (未采集) + 跑后有历史件                -> verdict='unknown'                conf='none'   is_new=None  crash_ev=False
  pre={} (空) + 跑后有历史件                    -> verdict='unknown'                conf='none'   is_new=None  crash_ev=False
  pre={exists:False} 伪折叠 + 跑后有历史件        -> verdict='unknown'                conf='none'   is_new=None  crash_ev=False
  pre 脏 state=zzz + 跑后有历史件               -> verdict='unknown'                conf='none'   is_new=None  crash_ev=False
```

`{"exists": False}`（无 `state`）**不再是「确认无件」**——确认无件必须显式带 `state="absent_confirmed"`.

#### N1 异常路径静默降级

**根因**（`TASK.md:39`）：采集异常无独立出口，被降级成 `high`。

**根治**：**H03**（§4 #3）采集抛异常 ⇒ `state="error"` + `error` + `traceback` 留痕，判定器给独立 verdict `error_pre_snapshot` / `confidence="none"`；**H04**（§4 #4）复制 / 读取抛异常 ⇒ 三条 `rec.add("ERROR", ...)`（`freshness_copy_failed` / `freshness_copy_stage` / `freshness_copy_traceback`）后 `_emit_f(..., "copy_failed")` 走 `post_read_error` 独立出口，**再 `raise` 原异常**（与母本 `run_guarded_steps:4534` 的「不吞、原样重抛」口径一致，本会话实读 `:4507-4534`）。`matrix` 中 `pre.state=error` → `error_pre_snapshot/none`、跑后读失败 → `post_read_error/none`，均非 `high`（`_draft_semantics_matrix_out.txt:9`、`:18`）。

#### N2 遗留件恒 high

**根因**（`TASK.md:40`）：快照缺失时历史遗留 `except.txt` 恒判 `new_first_appearance/high`。

**根治**：**H03**（§4 #3）的 `unknown` 分支 `return _finish("unknown", "none", None, ...)`，`_finish` 每次硬编码 `usable_as_crash_evidence=False`；`new_first_appearance/high` **只在** `state == "absent_confirmed" and post_exists` 时可达（跑前确实采到「无件」）。`_draft_semantics_matrix_out.txt:4-7` 四行证明四种缺失形态都停在 `unknown/none`；硬断言 `ASSERT 通过：None/{}/缺state/脏值 ⇒ verdict=unknown 且 conf!=high 且 usable_as_crash_evidence=False`（`:19`）。

#### N7 清单与 hunk 不等

**根因**（`TASK.md:41`）：旧 B2 清单 8 条、hunk 4 个。

**根治**：本稿 **§7 恰 9 行数据**（H01–H09），**§4 恰 9 个 `@@ ` 头**，逐行一一对应；§4 开头注明「按出现顺序依次对应 H01…H09」。专项检查 A 在本会话重跑 `verify` 得 `§7 清单数据行 = 9 ；设计稿 hunk 数 = 9 → 专项检查 A (hunksMatchManifest) = PASS`。**一个 hunk 都不多、一个都不漏**。

#### N10 captured_at_iso 被删 / 复制失败无留痕

**根因**（`TASK.md:42`）：`captured_at_iso` 与「复制失败显式留痕」被静默删掉。

**根治**：**H03**（§4 #3）快照双时刻 `captured_at_epoch` + `captured_at_iso`；**H04**（§4 #4）`post_observed["captured_at_iso"]`、`info["captured_at_iso"]`、`_emit_f` 的 `FRESHNESS.captured_at_iso`；**H08**（§4 #8）`FRESHNESS.captured_at_iso_pre`；**H02**（§4 #2，`-4458,6 +4473,10`；母本 `:4460` 后）`RESTORE.backup_mtime_pre:{name}` 跑前 mtime 显式留痕（不改 `bak[name]` 三键契约，探针 `[7]`）；**H04** 三条 `ERROR` 留痕 + `raise` 满足「先留痕再上抛，不许静默」。

#### N9 F/E 分离无实现约束

**根因**（`TASK.md:43`）：旧稿 `:205` 只有「F 只答新鲜性」的断言，无命名 / group / 退出码约束。

**根治**：**H01**（§4 #1）强制 F 命名空间 `FRESHNESS_GROUP = "FRESHNESS"`；**H04**（§4 #4）`_emit_f` 全部写进该 group（4 键带 `freshness_` 前缀、3 键为同 group 独立名），E 恒 `EXCEPT`（探针 `[9]` 已证 `EXCEPT.evidence_copy` 的 group/key/source/note 未被改名，仅扩键）；**H03/H04** 的 F 区不含任何退出码符号；**H05/H06/H07/H09** 只传数据、不碰 `:5985-5990`。实现级约束与测试见 **§6**。

---

## 2 状态矩阵

`state` = 本矩阵行类别；`preState` = 跑前快照**采集态**（`unknown / absent_confirmed / present / error` 四态可分，由 H01 的 `FRESHNESS_SNAPSHOT_STATES` 约束）；`verdict` ∈ `FRESHNESS_VERDICTS`（9 值）；`confidence` ∈ `FRESHNESS_CONFIDENCES`（`high / medium / low / none`，`none` = **不可判**，不是 `low`）；`is_new` 为 `True / False / None`（`None` = 未测写 null，母本 `:439-440` 口径）；`usableAsCrashEvidence` 恒 `false`（`:677` 口径：sha 变化不判 crash）。

机器可读版为同目录 `STATE_MATRIX.json`（严格 JSON 数组，14 项，每项含 `state` / `condition` / `verdict` / `confidence` / `usableAsCrashEvidence`，另附 `preState`）；下表与之逐行一致。

| state | preState | condition（输入条件） | verdict | confidence | is_new | usableAsCrashEvidence |
|:--|:--|:--|:--|:--|:--|:--|
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |
| `unknown` | `unknown` | `pre.state` 显式 `unknown` + 跑后无件；未知不得默认等于不存在 | `unknown` | `none` | `None` | `false` |
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |
| `post_read_error` | `present` | 跑后 `read_bytes/stat/write_bytes` 抛异常（`post.read_error` 非空）⇒ 独立 error 出口 | `post_read_error` | `none` | `None` | `false` |
| `absent_confirmed` | `absent_confirmed` | 跑前确认无件 + 跑后在场（存在性硬证） | `new_first_appearance` | `high` | `True` | `false` |
| `absent_both` | `absent_confirmed` | 跑前确认无件 + 跑后无件 ⇒ 未见新出现，但不能证无崩溃 | `absent_both` | `low` | `False` | `false` |
| `leftover_unchanged` | `present` | 跑前在 + 跑后在 + sha 一致 + mtime 未变（双侧齐全） | `leftover_unchanged` | `high` | `False` | `false` |
| `leftover_unchanged` | `present` | 跑前在 + 跑后在 + sha 一致 + mtime 侧缺失 ⇒ 如实标注，不虚报 high | `leftover_unchanged` | `medium` | `False` | `false` |
| `new_write` | `present` | 跑前在 + 跑后在 + sha 不同 ⇒ 本趟被写 | `new_write` | `high` | `True` | `false` |
| `rewritten_same_content` | `present` | 跑前在 + 跑后在 + sha 同 + mtime 变大 ⇒ 同内容重写 | `rewritten_same_content` | `medium` | `True` | `false` |
| `rewritten_same_content` | `present` | 跑前在 + 跑后在 + sha 同 + mtime 回拨 ⇒ 时钟回拨/utime 拉回，须人工复核 | `rewritten_same_content` | `low` | `True` | `false` |
| `missing_sha` | `present` | 跑前在 + 跑后在 + 缺 `pre.sha256`（B 主判据不可用）⇒ 独立出口，不降级不静默 | `error_pre_snapshot` | `none` | `None` | `false` |
| `missing_sha` | `present` | 跑前在 + 跑后在 + 缺 `post.sha256`（无法比对） | `post_read_error` | `none` | `None` | `false` |
| `vanished` | `present` | 跑前在 + 跑后无件（被删/改名/复制链中断）⇒ 异常态旗标，须人工复核 | `vanished` | `none` | `None` | `false` |

**派发材料 `TASK.md:49-64` 的 8 类逐条对账**：① unknown（表中第 1–2 行，`none`）② absent_confirmed（第 5–6 行）③ `leftover_unchanged`（第 7–8 行）④ `new_write`（第 9 行）⑤ `rewritten_same_content`（第 10–11 行）⑥ present + 缺 sha → 独立 `error_pre_snapshot` 出口（第 12 行，另第 13 行为跑后缺 sha 的 `post_read_error`）⑦ `vanished` → `none` + 须人工复核（第 14 行）⑧ `absent_both` → `low` + 「不能证无崩溃」（第 6 行）。**`unknown` 恒 `none`，不存在 `unknown → high` 映射**（专项检查 B）。

**置信口径三条硬规**：
1. `high` 只给「跑前确实采到 + 判据完整」的 `new_first_appearance` / `new_write` / `leftover_unchanged`（mtime 双侧齐全）；
2. `low` 给 `absent_both`（不能证无崩溃）与 `rewritten_same_content` 时钟回拨；`medium` 给旁证不全 / 同内容重写；
3. `none` 给**所有不可判出口**（unknown / error / vanished / missing_sha / post_read_error），且 `is_new = None`（母本 `:439-440`「不可测写 `null`」，`:440` 明确不提供「写 `False` 表示未知」的口子）。

---

## 3 早退与异常路径覆盖表

`snapshotValue` = `finally` 进入时 `_pre_freshness_snapshot` 的值；`finalizeReceives` = `:7117` 调用实参；`outputVerdict` = `FRESHNESS.freshness_verdict`；`crashes` = 是否抛未绑定 / 未留痕异常。
**全表性质**：结构性结论（母本逐行实读 + 内存 `patched` 的 `ast.parse` / 静态断言 / 离线合成单测），**未做运行时复现**（零真机，见 §8 第 1 条）。

| pathId | 触发点（母本:行） | snapshotValue | finalizeReceives | outputVerdict | crashes |
|:--|:--|:--|:--|:--|:--|
| P1 | `main:6340` `return EXIT_CARRIER_NOT_OWNED`（所有权不成立，早于 `:6387`） | `None`（H07 预初始化，未采集态） | `pre_freshness_snapshot=None` | `unknown` / `none`（跑后若有遗留件，绝不给 `high`） | 否（结构性）：名字已绑定；若 `:7038 finally` 的先行语句与 `:7093..7116` 均成功，则 `:7117` → `finalize_trip` → `_except_evidence_copy` → `:5939` 收 `None`，分类器归一为 `unknown` |
| P2 | `main:6349` `return EXIT_TARGET_MISSING` | `None` | `None` | `unknown` / `none` | 否（结构性；同 P1） |
| P3 | `main:6361` `return EXIT_TARGET_MISMATCH`（目标哈希不符） | `None` | `None` | `unknown` / `none` | 否（结构性；同 P1） |
| P4 | `main:6374` `return EXIT_PRECHECK_SHA_MISMATCH` | `None` | `None` | `unknown` / `none` | 否（结构性；同 P1） |
| P5 | `main:6377` `return EXIT_PRECHECK_SIG_MISMATCH` | `None` | `None` | `unknown` / `none` | 否（结构性；同 P1） |
| P6 | `try` 内 `:6313..7029` 任一点抛 `BaseException`（`:7030 except` → `:7036 write_finalize_error` → `:7037 raise`；`:7038 finally` 进入） | 视抛出点：早于 `:6389` 为 `None`；晚于则为 `make_pre_freshness_snapshot` 的 dict | 该值经 **H09** 传入（若 `:7117` 可达） | `None` → `unknown`；dict → 按 §2 判定 | 否（结构性）：原异常由 `:7037 raise` 保留；H04 复制失败分支先 `rec.add("ERROR")` 再 `raise`，`:4507-4534 run_guarded_steps` 跑完全部收尾项后原样重抛 |
| P7a | `finally` 内 **`:7048..7092`** 失败（`finally_entered` 记账 / 进程令牌读取 / `terminate_owned_process` 失败记账 / `fin_carrier` 与 `fin_ownership` 构造）；该区间在母本 `:7093` 内层 `try:` **之外** | 已绑定值（H07 预初始化，可能已被 H08 覆写） | **未调用** `finalize_trip`；`:7126` 的 `except` 不覆盖此区间 | **无 F 字段落盘**（如实：收尾未跑到证据项） | 否（结构性）：不产生新未绑定名；异常直接由 `finally` 向外传播（D-25 §5 第 1 条「finally 中先行语句也可能失败」） |
| P7b | `finally` 内 **`:7099..7116`** 失败（冻结基线回读 / 枚举错误分支 / `rec.add("MOTHER", ...)`），在母本 `:7093` 内层 `try` 内、未到 `:7117` | 已绑定值 | **未调用** `finalize_trip` | **无 F 字段落盘** | 否（结构性）：由 `:7126-7134` 收尾异常分支接 `note_cleanup_failure` + `merge_cleanup_code` + `write_finalize_error` + `raise`（`qc151_trip.py:7126-7134`，本会话实读） |
| P8 | 正常路径 `:7029 return EXIT_OK`（经 `:6389` 快照构造） | dict，`state ∈ {absent_confirmed, present, error}` | 该 dict | 按 §2 判定；正常路径 `_emit_f(..., "copied")` 必落盘 | 否（结构性） |
| P9 | `:6445` / `:6478` / `:6496` / `:7021` 四个不早于 `:6387` 的 `return`（探针 `[5]`，`_b2b_probe_out.txt:73-77`） | dict（`:6389` 已赋值） | 该 dict | 按 §2 判定 | 否（结构性） |
| P10 | `copy_post_except_evidence` 内 `dst.write_bytes` 抛异常（H04 异常分支） | 上层传入值不变 | 上层传入值不变 | `post_read_error` / `none` + 3 条 `ERROR` 留痕 | 否（结构性）：`raise` 原异常，`:4507 run_guarded_steps` 记账后 `:4534` 原样重抛，不静默 |

**五个早退逐条覆盖率 = 5/5**（P1–P5；专项检查 C 在本会话重跑 `verify` 得 `earlyReturnsCovered = 5/5 [':6340', ':6349', ':6361', ':6374', ':6377'] → PASS`）。P6 覆盖「`try` 内抛异常」，P7a/P7b 覆盖「`finally` 内 `:7048` 到 `:7117` 之间失败」（派发材料 `TASK.md:70` 的「外加」两条）；P8–P10 补正常路径、其余 `return`、复制失败。

**为什么不会崩（结构性）**：H07（§4 #7）在 `try` 之前（`:6296` 后）就绑定名字，五个早退 `return` 在 `:6313 try` 内但都晚于 H07；`:7038 finally` 读的是同一函数作用域里已绑定的局部（母本 `:6293-6296` 有同类先例）；H05 把值接成形参、H09 传给收尾、H06 传给唯一调用点、`None` 在分类器里是**合法输入**（归一为 `unknown`），不是错误。
**P7a/P7b 的拆分依据**：本会话实读母本 `:7093` 才是内层 `try:`，`:7126` 的 `except` 只覆盖 `:7099..7125`；语义稿 §3 P7 把整个 `:7048..7116` 都归给 `:7126-7134` 与母本原文不符，按 D-25「finally 调用前失败必须明确处理」拆开（§8 第 3 条取舍 B）。

---

## 4 完整 diff

全部 9 个 hunk 由 `_draft_semantics_check.py build` 在内存里构造 `patched` 后实算 `difflib.unified_diff(n=3)` 产生（输出 `_draft_semantics_build_out.txt`），逐字取自 `_hunks_frag.md`，**未手工改写任何一行**。本会话重跑 `build` 得 `HUNK_COUNT = 9`、`ast.parse(patched) = PASS (exitcode 0)`；重跑 `verify` 得 `套用结果与 build patched 逐行一致 = True`、`ast.parse(套用后文本) = PASS`。每个 hunk 的 `-` 行与上下文行均与母本原文逐字相等。
应用目标为上述指纹的母本副本 `qc151_trip.py`；`-` 侧行号为**母本 1-based 锚点**，`+` 侧为按序套用后的行号（供参考）。
**按出现顺序依次对应 §7 的 H01…H09**；共 9 个 `@@ ` 头。

```diff
@@ -212,6 +212,21 @@
 # ★ 载体内五个文件（`QC141:152-160`）
 CARRIER_FILES = ("gamemd.exe", "ra2loader.exe", "ra2render.dll",
                  "ra2opt_play.bat", "except.txt")
+
+
+# ★★ B2b/N9：F（freshness）命名空间**单一真源**。
+#   ★ E 恒用 "EXCEPT" group；整趟退出码唯一判据恒在 :5985-5990 的集合差，
+#     F 字段与 F 代码**一律不得**进入该判据（静态门禁逐 token 核）。
+#   ★ F 结论恒 usable_as_crash_evidence=False（:677 口径：sha 变化不判 crash）。
+FRESHNESS_GROUP = "FRESHNESS"
+FRESHNESS_KEY_PREFIX = "freshness_"
+FRESHNESS_VERDICTS = ("unknown", "absent_both", "new_first_appearance",
+                      "vanished", "leftover_unchanged", "new_write",
+                      "rewritten_same_content", "error_pre_snapshot",
+                      "post_read_error")
+FRESHNESS_CONFIDENCES = ("high", "medium", "low", "none")
+FRESHNESS_SNAPSHOT_STATES = ("unknown", "absent_confirmed", "present", "error")
+
 
 # ===========================================================================
 # §1 · 两控常量（★ 逐字承自 `QC141:149`/`:150`/`:160`；★ 真值不写死为参数）
```

```diff
@@ -4458,6 +4473,10 @@
         dst.write_bytes(src.read_bytes())
         h = sha256_file(dst)
         bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}
+        rec.add("RESTORE", f"backup_mtime_pre:{name}",
+                float(src.stat().st_mtime), f"{src}:file",
+                note="★ B2b/N10：跑前 mtime 显式留痕（★ 不进 bak[name] 三键契约）")
+
         rec.add("RESTORE", f"backup_sha256:{name}", h, f"{dst}:file")
     return bak
 
```

```diff
@@ -4558,8 +4577,131 @@
         encoding="utf-8")
 
 
+def make_pre_freshness_snapshot(except_path: Path) -> dict:
+    """★ B2b/F：跑前 `except.txt` **带状态标签**的基线快照（纯只读，不写载体）。
+
+    ★★ N3 硬约束：`state` 是**唯一**判别口，`exists` 不得被用于反推状态。
+      `None` / `{}` / 缺 `state` / 脏值 ⇒ 一律 unknown（未采集），
+      **绝不等于**「跑前确认无件」。
+    ★ N10：`captured_at_epoch` 与 `captured_at_iso` 双时刻必留，缺一即契约失败。
+    ★ N1：采集抛异常 ⇒ state="error" 独立出口，不降级、不静默、不给 high。
+    """
+    snap = {"state": "unknown", "exists": None, "size": None,
+            "sha256": None, "mtime_pre": None,
+            "captured_at_epoch": None, "captured_at_iso": None,
+            "error": None, "traceback": None,
+            "source": "script:make_pre_freshness_snapshot"}
+    try:
+        p = Path(except_path)
+        snap["captured_at_epoch"] = time.time()
+        snap["captured_at_iso"] = now_iso()
+        if not p.exists():
+            snap["state"] = "absent_confirmed"
+            snap["exists"] = False
+            return snap
+        st = p.stat()
+        snap["state"] = "present"
+        snap["exists"] = True
+        snap["size"] = int(st.st_size)
+        snap["mtime_pre"] = float(st.st_mtime)
+        snap["sha256"] = sha256_file(p)
+    except Exception as exc:
+        import traceback
+        snap["state"] = "error"
+        snap["error"] = f"{type(exc).__name__}: {exc}"
+        snap["traceback"] = "".join(traceback.format_exception(exc))
+    return snap
+
+
+def classify_except_freshness(pre_freshness_snapshot, post_observed: dict) -> dict:
+    """★ B2b/F：只回答 **F（本趟窗口内是否被写/新出现）**。
+
+    ★★ N9：本函数不得引用退出码判据（:5985-5990）、不得登记收尾失败、
+      不得引用任何退出码常量；E（新异常）唯一口径恒为母本 :672-708。
+      `usable_as_crash_evidence` 恒 False，任何 F verdict 都不得作为崩溃证据。
+    ★★ N3：`state` 判别优先于一切；unknown ⇒ 不可判，**恒不给 high**。
+    """
+    out = {"verdict": None, "confidence": "none", "is_new": None,
+           "note": "", "usable_as_crash_evidence": False,
+           "pre_snapshot_state": "unknown"}
+
+    def _finish(verdict: str, confidence: str, is_new, note: str) -> dict:
+        out.update({"verdict": verdict, "confidence": confidence,
+                    "is_new": is_new, "note": note,
+                    "usable_as_crash_evidence": False})
+        return out
+
+    pre = (pre_freshness_snapshot
+           if isinstance(pre_freshness_snapshot, dict) else {})
+    st = pre.get("state")
+    if st not in FRESHNESS_SNAPSHOT_STATES:
+        st = "unknown"          # ★ None / {} / 缺 state / 脏值 ⇒ 一律「未采集」
+    out["pre_snapshot_state"] = st
+
+    post = post_observed if isinstance(post_observed, dict) else {}
+    # ★ N1：错误独立出口，优先于一切状态折叠
+    if post.get("read_error"):
+        return _finish("post_read_error", "none", None,
+                       "★ 跑后件读/复制失败（独立 error 出口，禁止静默）："
+                       f"{post['read_error']}；pre_snapshot_state={st}")
+    # ★★ N3/N2：unknown 与 absent_confirmed 在第一个分支就分道，禁止折叠
+    if st == "unknown":
+        return _finish("unknown", "none", None,
+                       "★ 跑前快照未采集/传参丢失/采集未完成 ⇒ F 不可判；"
+                       "未知 ≠ 不存在；不得据此输出「本趟新出现」或 high")
+    if st == "error":
+        return _finish("error_pre_snapshot", "none", None,
+                       f"★ 跑前采集失败（独立 error 出口）：{pre.get('error')!r}")
+
+    post_exists = bool(post.get("exists"))
+    if not post_exists:
+        if st == "absent_confirmed":
+            return _finish("absent_both", "low", False,
+                           "★ 跑前确认无件 + 跑后无件 ⇒ F=未见新出现；"
+                           "但「文件未出现」不能证无崩溃（E 口径另算）")
+        return _finish("vanished", "none", None,
+                       "★ 跑前在、跑后失 ⇒ 异常态旗标（被删/改名/复制链中断），"
+                       "须人工复核；不给 high、不判本趟新出现")
+
+    if st == "absent_confirmed":
+        return _finish("new_first_appearance", "high", True,
+                       "★ 跑前确认无件 + 跑后在地 ⇒ F=本趟新出现（存在性）；"
+                       "是否新崩溃仍只由 :672-708 集合差裁定")
+
+    # ---- st == "present" ----
+    pre_sha = pre.get("sha256")
+    if not pre_sha:
+        return _finish("error_pre_snapshot", "none", None,
+                       "★ 跑前在场但缺 sha256 ⇒ B 主判据不可用"
+                       "（独立 error 出口，不降级为 high、不静默）")
+    post_sha = post.get("sha256")
+    if not post_sha:
+        return _finish("post_read_error", "none", None,
+                       "★ 跑后缺 sha256 ⇒ 无法比对（error 出口）")
+    if post_sha != pre_sha:
+        return _finish("new_write", "high", True,
+                       "★ 字节内容不同 ⇒ F=本趟被写；是否新异常归集合差（:677）")
+
+    pre_mt, post_mt = pre.get("mtime_pre"), post.get("mtime_post")
+    if pre_mt is None or post_mt is None:
+        return _finish("leftover_unchanged", "medium", False,
+                       "★ sha 同但 mtime 侧缺失 ⇒ A 旁证不可用，"
+                       "同内容重写盲区此趟未覆盖（如实标注，不虚报 high）")
+    if abs(float(post_mt) - float(pre_mt)) <= 0.0:
+        return _finish("leftover_unchanged", "high", False,
+                       "★ 跑前在 + sha 同 + mtime 未变 ⇒ 原样遗留（非本趟写入）")
+    if float(post_mt) < float(pre_mt):
+        return _finish("rewritten_same_content", "low", True,
+                       "★ sha 同、mtime 变且回拨 ⇒ 疑似时钟回拨/utime 拉回，"
+                       "置信降级为 low，须人工复核")
+    return _finish("rewritten_same_content", "medium", True,
+                   "★ sha 同而 mtime 变 ⇒ 同内容重写（F 旁证补 B 盲区）")
+
+
 def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,
-                              out_dir: Path) -> dict | None:
+                              out_dir: Path,
+                              pre_freshness_snapshot: dict | None = None
+                              ) -> dict | None:
     """★★★ `QC162:W7`：★ 在**还原之前**把本趟跑后的 `except.txt` 原件
     （★ 与五个载体件的跑后状态）**另存一份证据副本**进 `--out-dir`。
 
```

```diff
@@ -4572,20 +4714,105 @@
     ★ 返回证据元信息（`None` = 载体 `except.txt` 不存在）。
     """
     src = carrier_dir / "except.txt"
-    if not src.exists():
-        rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
-                note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
-        return None
-    blob = src.read_bytes()
-    h = hashlib.sha256(blob).hexdigest()
-    dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
-    dst.write_bytes(blob)
+    blob = None
+    h = None
+    dst = None
+    post_observed = {"exists": None, "size": None, "sha256": None,
+                     "mtime_post": None, "captured_at_iso": None,
+                     "read_error": None}
+
+    def _emit_f(fresh: dict, stage: str) -> None:
+        """★ N4：正常与错误**每一条**出口都落盘 F 字段（不空转）。
+
+        ★★ N9：全部写进 FRESHNESS_GROUP，键名一律带 FRESHNESS_KEY_PREFIX；
+          本函数不读退出码判据、不登记收尾失败、不引用退出码常量。
+        """
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "verdict",
+                fresh["verdict"], "script:classify_except_freshness",
+                note=f"stage={stage}；F 只答新鲜性，E 归 :672-708 集合差")
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "confidence",
+                fresh["confidence"], "script:classify_except_freshness",
+                note="★ none = 不可判；unknown 恒 none，禁止映射到 high")
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "is_new",
+                fresh["is_new"], "script:classify_except_freshness",
+                note="★ None = 未测写 null（Recorder :439-440 口径），"
+                     "不得写 False 表示未知")
+        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "note",
+                fresh["note"], "script:classify_except_freshness",
+                note=fresh["note"])
+        rec.add(FRESHNESS_GROUP, "pre_snapshot_state",
+                fresh["pre_snapshot_state"],
+                "script:make_pre_freshness_snapshot",
+                note="★ unknown / absent_confirmed / present / error 三态可分")
+        rec.add(FRESHNESS_GROUP, "usable_as_crash_evidence",
+                fresh["usable_as_crash_evidence"],
+                "script:classify_except_freshness",
+                note="★★ 恒 False：F 结论不得作为本趟崩溃证据（:677）")
+        rec.add(FRESHNESS_GROUP, "captured_at_iso",
+                post_observed.get("captured_at_iso"), "script:now_iso",
+                note="★ N10：跑后观测时刻（ISO-8601）；跑前同名键在快照内")
+
+    try:
+        if not src.exists():
+            post_observed["exists"] = False
+            post_observed["captured_at_iso"] = now_iso()
+            rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
+                    note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
+            # ★ N4：早退分支同样落盘 F 字段（不可只算不写）
+            _emit_f(classify_except_freshness(pre_freshness_snapshot,
+                                              post_observed), "src_missing")
+            return None
+        post_observed["captured_at_iso"] = now_iso()
+        blob = src.read_bytes()
+        st = src.stat()
+        h = hashlib.sha256(blob).hexdigest()
+        post_observed.update({"exists": True, "size": len(blob),
+                              "sha256": h, "mtime_post": float(st.st_mtime)})
+        dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
+        dst.write_bytes(blob)
+    except Exception as exc:
+        # ★★ N10：复制/读取失败 ⇒ 先 rec.add("ERROR", ...) 显式留痕，再**上抛**
+        import traceback
+        where = f"{src}:file"
+        rec.add("ERROR", "freshness_copy_failed",
+                f"{type(exc).__name__}: {exc}", where,
+                note="★★ B2b/N10：复制失败显式留痕，不许静默降级")
+        rec.add("ERROR", "freshness_copy_stage",
+                "read_bytes/stat/write_bytes", where,
+                note="captured_at_iso="
+                     f"{post_observed.get('captured_at_iso')!r}")
+        rec.add("ERROR", "freshness_copy_traceback",
+                "".join(traceback.format_exception(exc)), "script:traceback")
+        post_observed["read_error"] = f"{type(exc).__name__}: {exc}"
+        # ★ N4/N1：错误分支同样落盘 F 字段，且走独立 error 出口
+        _emit_f(classify_except_freshness(pre_freshness_snapshot,
+                                          post_observed), "copy_failed")
+        raise
+
     info = {"source": str(src), "evidence_path": str(dst),
             "size": len(blob), "sha256": h,
             "note": "★ QC162:W7：还原**之前**取的跑后原件副本"
-                    "（☆ 还原之后仍存在、可复核）"}
+                    "（☆ 还原之后仍存在、可复核）",
+            # ★★ N4/N6/N10：正常路径**必须**落盘的 F 字段（B2 在此空转）
+            "mtime_post": post_observed["mtime_post"],
+            "freshness_verdict": None,
+            "freshness_confidence": None,
+            "freshness_note": None,
+            "captured_at_iso": None,
+            "pre_snapshot_state": None,
+            "pre_freshness_snapshot": None}
+    fresh = classify_except_freshness(pre_freshness_snapshot, post_observed)
+    info["freshness_verdict"] = fresh["verdict"]
+    info["freshness_confidence"] = fresh["confidence"]
+    info["freshness_note"] = fresh["note"]
+    info["captured_at_iso"] = post_observed["captured_at_iso"]
+    info["pre_snapshot_state"] = fresh["pre_snapshot_state"]
+    info["pre_freshness_snapshot"] = (
+        pre_freshness_snapshot
+        if isinstance(pre_freshness_snapshot, dict) else None)
     rec.add("EXCEPT", "evidence_copy", info, f"{src}:file",
             note="★★ 跑后 except.txt 原件副本（先于 restore_carrier）")
+    _emit_f(fresh, "copied")   # ★ N4：正常路径同样落盘（非仅早退分支）
     # ★ 跑后载体件快照（★ 供"证据先于还原"复核：证明取的是跑后状态）
     files: dict = {}
     for name in CARRIER_FILES:
```

```diff
@@ -5906,7 +6133,8 @@
                   mother_baseline: dict | None = None,
                   carrier_identity: dict | None = None,
                   handover: Path | None = None,
-                  created_receipt: dict | None = None) -> int:
+                  created_receipt: dict | None = None,
+                  pre_freshness_snapshot: dict | None = None) -> int:
     """★★★ `QC157:3`：★ 覆盖**全程**的收尾（★ `finally` 调用本函数）。
 
     ★★ `QC162:W7` —— ★★ **证据必须先于还原**（★ 本卡最重）：
```

```diff
@@ -5936,7 +6164,8 @@
     state: dict = {"evidence": None, "pre_manifest": None, "delete": None}
 
     def _except_evidence_copy() -> None:
-        copy_post_except_evidence(rec, carrier_dir, out_dir)
+        copy_post_except_evidence(rec, carrier_dir, out_dir,
+                                 pre_freshness_snapshot=pre_freshness_snapshot)
         # ★★ 第 1 项：★ 证据**先搬出**并**逐件验 SHA**
         ev = move_out_evidence_and_verify(rec, carrier_dir, out_dir)
         state["evidence"] = ev
```

```diff
@@ -6294,6 +6523,9 @@
     bak: dict = {}
     t0: list = []
     pre_except_txt = None
+    # ★★ B2b/E1/N3：★ **try 之前**预初始化 ⇒ 五个早退 + 异常路径均不会
+    #    未绑定；`None` 语义 = **未采集（unknown）**，绝不等于「跑前无件」。
+    _pre_freshness_snapshot: dict | None = None
     budget = TripBudget(rec)
     ACTIVE_REC[0] = rec       # ★ 第 3 项：★ 最外层最终落盘要用同一 rec
     # ★★ 进程身份跟踪（外部裁定：Popen 后须建立可清理所有权）
```

```diff
@@ -6386,6 +6618,15 @@
         budget.begin_stage("backup")
         bak = backup_carrier(rec, carrier_dir)
         budget.end_stage("backup")
+        # ★★ B2b/E1/N5/N10：载体定稿后、launch 前拍跑前 F 快照（纯只读，
+        #    不写载体）；captured_at_iso 显式落盘，未知态不折叠成「无件」。
+        _pre_freshness_snapshot = make_pre_freshness_snapshot(
+            carrier_dir / "except.txt")
+        rec.add(FRESHNESS_GROUP, "captured_at_iso_pre",
+                _pre_freshness_snapshot["captured_at_iso"],
+                "script:make_pre_freshness_snapshot",
+                note="★ N10：跑前捕获时刻；state="
+                     f"{_pre_freshness_snapshot['state']}")
 
         # ---- ④ `except.txt` 被动基线（★ U-5：★ 不再写载体 except.txt） ----
         #   ★ 外部裁定 V5 §6.1.1 U-5：★ 在既有禁写范围内移除 except_reset 对
```

```diff
@@ -7122,7 +7363,8 @@
                 carrier_identity=(TRIP_CARRIER.get("identity")),
                 handover=(Path(args.carrier_handover) if args.carrier_handover
                           else None),
-                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt))
+                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt),
+                pre_freshness_snapshot=_pre_freshness_snapshot)
         except Exception as exc:
             # ★★ 收尾项自身抛异常（★ `run_guarded_steps` 已把每个失败的
             #   文件:行·类型·repr 落盘 `finalize_errors.txt` 后**原样重抛**，
```

---

## 5 字段契约

母本 `Recorder.add`（`:446`，探针 `[10]`）签名 `(self, group: str, key: str, value, source: str, note: str = "") -> None`，`value` 无注解；`rec.dump`（`:452-454`）把全部行写进 `qc151_fields.json`。以下每个新字段都给**名称 / 类型 / 取值域 / 写入点 / 消费方**。写入点用「H 编号（§4 序号 / 母本锚点）」定位。

| 字段（`group.key` 或对象键） | 类型 | 取值域 | 写入点 | 消费方 |
|:--|:--|:--|:--|:--|
| `FRESHNESS_GROUP` | `str` 常量 | 固定 `"FRESHNESS"` | H01（§4 #1，母本 `:214` 后） | H04 `_emit_f` 7 次 + H08 1 次；下游按 group 过滤 |
| `FRESHNESS_KEY_PREFIX` | `str` 常量 | 固定 `"freshness_"` | H01（§4 #1） | H04 `_emit_f` **仅 4 个键**拼接（见下方说明） |
| `FRESHNESS_VERDICTS` | `tuple[str]` | `unknown / absent_both / new_first_appearance / vanished / leftover_unchanged / new_write / rewritten_same_content / error_pre_snapshot / post_read_error`（9 值） | H01（§4 #1） | 门禁校验 `verdict` 取值域；§2 矩阵 |
| `FRESHNESS_CONFIDENCES` | `tuple[str]` | `high / medium / low / none` | H01（§4 #1） | 门禁校验 `unknown` 不落 `high`（专项检查 B） |
| `FRESHNESS_SNAPSHOT_STATES` | `tuple[str]` | `unknown / absent_confirmed / present / error`（4 态） | H01（§4 #1） | H03 分类器唯一判别口 |
| `snapshot.state` | `str` | 上述 4 态 | H03（§4 #3，`make_pre_freshness_snapshot`） | H03 分类器 / §2 `preState` |
| `snapshot.exists` | `bool \| None` | `True / False / None` | H03（§4 #3） | 仅回显，**不得**用于反推 `state` |
| `snapshot.size` | `int \| None` | ≥0 / `None` | H03（§4 #3） | 复核 |
| `snapshot.sha256` | `str \| None` | 64 hex / `None` | H03（§4 #3，复用母本 `:416 sha256_file`） | B 主判据（字节内容比对） |
| `snapshot.mtime_pre` | `float \| None` | epoch 秒 / `None` | H03（§4 #3，`p.stat()`） | A 旁证（`abs` 差分） |
| `snapshot.captured_at_epoch` | `float \| None` | epoch 秒 / `None` | H03（§4 #3，`time.time()`） | 时间线复核（**N10 必留**） |
| `snapshot.captured_at_iso` | `str \| None` | ISO-8601 / `None` | H03（§4 #3，`now_iso()`，母本 `:432-433`） | H08 转写为 `FRESHNESS.captured_at_iso_pre`（**N10 必留**） |
| `snapshot.error` | `str \| None` | 异常摘要 / `None` | H03（§4 #3，仅采集失败） | 独立 `error_pre_snapshot` 出口 |
| `snapshot.traceback` | `str \| None` | 栈文本 / `None` | H03（§4 #3，仅采集失败） | 复核 |
| `snapshot.source` | `str` | `"script:make_pre_freshness_snapshot"` | H03（§4 #3） | 溯源 |
| `post_observed.exists` | `bool \| None` | `True / False / None` | H04（§4 #4） | H03 分类器（存在性） |
| `post_observed.size` | `int \| None` | ≥0 / `None` | H04（§4 #4） | 复核 |
| `post_observed.sha256` | `str \| None` | 64 hex / `None` | H04（§4 #4，`hashlib.sha256`） | B 主判据 |
| `post_observed.mtime_post` | `float \| None` | epoch 秒 / `None` | H04（§4 #4，`src.stat()`） | A 旁证 / `info.mtime_post` |
| `post_observed.captured_at_iso` | `str \| None` | ISO-8601 / `None` | H04（§4 #4） | `info.captured_at_iso` + `FRESHNESS.captured_at_iso` |
| `post_observed.read_error` | `str \| None` | 异常摘要 / `None` | H04（§4 #4，仅复制/读失败） | `post_read_error` 独立出口 |
| `FRESHNESS.freshness_verdict` | `str` | `FRESHNESS_VERDICTS` 9 值 | H04 `_emit_f` 三条出口（§4 #4，母本 `:4574` 起） | 复核员 / 状态矩阵门禁 |
| `FRESHNESS.freshness_confidence` | `str` | `FRESHNESS_CONFIDENCES` 4 值 | H04 `_emit_f` 三条出口 | 专项检查 B |
| `FRESHNESS.freshness_is_new` | `bool \| None` | `True / False / None` | H04 `_emit_f` 三条出口 | `None` = 未测写 null（母本 `:439-440`） |
| `FRESHNESS.freshness_note` | `str` | 人类可读说明 | H04 `_emit_f` 三条出口 | 复核员 |
| `FRESHNESS.pre_snapshot_state` | `str` | 4 态 | H04 `_emit_f` 三条出口 | 状态可分性取证（无 `freshness_` 前缀） |
| `FRESHNESS.usable_as_crash_evidence` | `bool` | **恒 `False`** | H04 `_emit_f` 三条出口 | `:677` 口径护栏（无前缀） |
| `FRESHNESS.captured_at_iso` | `str \| None` | ISO-8601 / `None` | H04 `_emit_f` 三条出口 | 跑后观测时刻（**N10**，无前缀） |
| `FRESHNESS.captured_at_iso_pre` | `str \| None` | ISO-8601 / `None` | **H08**（§4 #8，母本 `:6388` 后） | 跑前捕获时刻（**N10**） |
| `EXCEPT.evidence_copy`（`info` 由 5 键扩到 12 键） | `dict \| None` | 原 5 键 + 7 新键，见下 | H04（§4 #4，正常路径与 `src_missing` 分支） | 母本既有消费方；**新增键只读不破契约** |
| `info.mtime_post` | `float` | epoch 秒 | H04（§4 #4） | 复核 |
| `info.freshness_verdict` | `str` | `FRESHNESS_VERDICTS` | H04（§4 #4） | 正常路径 F 结论（**N4**） |
| `info.freshness_confidence` | `str` | `FRESHNESS_CONFIDENCES` | H04（§4 #4） | **N6** |
| `info.freshness_note` | `str` | 说明文本 | H04（§4 #4） | **N6** |
| `info.captured_at_iso` | `str` | ISO-8601 | H04（§4 #4） | **N10** |
| `info.pre_snapshot_state` | `str` | 4 态 | H04（§4 #4） | 可追溯 |
| `info.pre_freshness_snapshot` | `dict \| None` | 快照原样；未采集为 `None` | H04（§4 #4） | 可追溯；未知态留 `None` 不折叠 |
| `RESTORE.backup_mtime_pre:{name}` | `float` | epoch 秒 | H02（§4 #2，母本 `:4460` 后；`name ∈ CARRIER_FILES` 5 件，探针 `[7]`） | **N10** 留痕；不改 `bak[name]` 三键 |
| `ERROR.freshness_copy_failed` | `str` | `{type}: {msg}` | H04 异常分支（§4 #4） | 复制失败留痕（**N10/N1**） |
| `ERROR.freshness_copy_stage` | `str` | `"read_bytes/stat/write_bytes"` | H04 异常分支 | 定位失败阶段 |
| `ERROR.freshness_copy_traceback` | `str` | 栈文本 | H04 异常分支 | 复核 |
| `main._pre_freshness_snapshot` | `dict \| None` | 快照 dict / `None`（未采集） | H07 预初始化（§4 #7）/ H08 赋值（§4 #8）/ H09 传出（§4 #9） | E1 作用域链 |
| `finalize_trip.pre_freshness_snapshot` | `dict \| None` | 同上 | H05 形参（§4 #5）→ H06 传给 `:5939`（§4 #6） | N5 接线 |
| `copy_post_except_evidence.pre_freshness_snapshot` | `dict \| None = None` | 同上 | H03 def 签名（§4 #3）→ H06 唯一调用点关键字传参（§4 #6） | N5 闭合 |

**命名不冲突的精确口径**：H04 `_emit_f` 的 7 个 `rec.add` **全部**以 `FRESHNESS_GROUP` 为 group（本会话实算 `FRESHNESS_GROUP rec.add in + lines = 8`，其中 7 处在 H04、1 处在 H08）；其中 **4 键**由 `FRESHNESS_KEY_PREFIX + ...` 拼出（`freshness_verdict` / `freshness_confidence` / `freshness_is_new` / `freshness_note`），**3 键**为同 group 独立名（`pre_snapshot_state` / `usable_as_crash_evidence` / `captured_at_iso`）。语义稿 §1 N9 的「键名一律带前缀」是过度表述，本稿按 §4 实码收窄（§8 第 3 条取舍 D）。
E 侧 `EXCEPT.evidence_copy` 只**扩键**：原 5 键 `source / evidence_path / size / sha256 / note` 与 `rec.add` 的 group / key / source / note 一个字节不改（探针 `[9]`，`_b2b_probe_out.txt:143-161`）；母本 `EXCEPT` group 既有键（`set_diff_method :702`、`pre_line_count :703`、`post_line_count :704`、`new_exception_count :705`）保持原样。

---

## 6 F/E 分离的实现级约束

**F（freshness）**：`except.txt` 在**本趟窗口内**是否被写 / 新出现。唯一实现 = H03 两个纯函数 + H04 的 `_emit_f`。
**E（新异常）**：唯一口径恒为母本 `except_set_diff`（`:672-708`）。其判据是 `collections.Counter` 多重集差（`:683-688`）里含 `Exception occurred at` 的行（`:689`），结果键 `no_new_exception`（`:700`）；`:677` 原文「★ **不得**用 `sha` 变化判 crash（★ 游戏自身会重写该文件）」（本会话实读 `qc151_trip.py:672-708`）。E 影响退出码的落点在 `:5984-5990`（本会话实读 `:5978-5992`）。

| 约束 | 实现方式（对应代码行） | 可验证证据（本会话实跑） |
|:--|:--|:--|
| ① 字段命名隔离 | H01 定义 `FRESHNESS_GROUP="FRESHNESS"`；H04 `_emit_f` 7 次全写该 group（4 键带 `freshness_` 前缀、3 键独立名）；E 恒 `EXCEPT` | `build` 输出 `F 区 FRESHNESS_GROUP 写入次数: 7`；本会话实算 `FRESHNESS_GROUP rec.add in + lines = 8` |
| ② group 隔离 | H04 全部 `rec.add(FRESHNESS_GROUP, ...)`；`info` 保留在 `EXCEPT.evidence_copy` 仅为「证据副本元信息」扩键，不新增 E 判据键 | 探针 `[9]` 的 `EXCEPT.evidence_copy` 写入点未被删除 / 改名；`:4587-4588` 原文实读 |
| ③ **不得进入退出码判据** | **每个 hunk 的 `-` 侧覆盖区间**（按 hunk 头 `-起始,行数` 实算，本会话命令见 §6 下方）为 `212-217` / `4458-4463` / `4558-4565` / `4572-4591` / `5906-5912` / `5936-5942` / `6294-6299` / `6386-6391` / `7122-7128`，**均不含 5984-5990**；`build` 用整段原文 `assert ... in p` 比对该块不变；F 区（`make_pre_freshness_snapshot` → `def _dump_json(`）逐 token 零 `note_cleanup_failure(` / `no_new_exception` / `EXIT_` / `except_set_diff(` / `CLEANUP_FAILURES` | `build` 输出 `E 口径 unchanged: except_set_diff(:672-708) + :5985-5990 判据块 = PASS`、`F/E 静态门禁: ... = PASS`；本会话实算 `no hunk overlaps E judgment block 5984-5990 = True`、`forbidden tokens in ANY + line = 0`（255 条 `+` 行） |
| ④ F 结论恒不可作崩溃证据 | H03 `_finish` 每次把 `usable_as_crash_evidence` 置 `False`；H04 把它写进 `FRESHNESS` | `matrix` 15 行输出 `crash_ev=False` 全列，`MATRIX_ALL = PASS` |
| ⑤ 无新 import / 无采样 | H03/H04 只用母本已有 `hashlib` / `time` / `datetime, timezone` / `Path` / `json`（本会话实读 `qc151_trip.py:167-175`）；`traceback` 在函数内 `import`，为 Python 标准库、非采样 | `build` 输出 `依赖 import 已在母本存在 = PASS（无需新增 import）` |

**③ 的口径限缩（不美化）**：H01 内联注释写「整趟退出码唯一判据恒在 :5985-5990 的集合差」。本会话实读母本发现**另有** `note_cleanup_failure(...)` 调用点：`:5944`（证据搬出验 SHA 失败）、`:7075`（终止失败）、`:7130`（收尾抛异常）。因此本稿的**绑定结论**收窄为：「**E 的集合差判据块 `:5984-5990` 逐字未改**；F 区 `+` 行零退出码符号且不含任何 `note_cleanup_failure` / `EXIT_` 调用；其余收尾失败点也未被这 9 个 hunk 改动」。该注释是 diff 内的描述性文字、非可执行语义；为保持 9 个 hunk 与实算 `patched` 逐字一致，未改动它，按已知文字不精确登记（§8 第 3 条取舍 E）。`TASK.md:74` 的「唯一影响退出码处」亦按同一限缩理解。

**用什么测试证明（本会话实跑命令与输出，均为 `python -I -X utf8` + 绝对路径）**：

| 命令 | exitCode | 关键输出 |
|:--|--:|:--|
| `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics_check.py build` | `0` | `母本行数: 7292  patched 行数: 7534`；`ast.parse(patched) = PASS (exitcode 0)`；`E 口径 unchanged ... = PASS`；`F/E 静态门禁 ... = PASS`；`F 区 FRESHNESS_GROUP 写入次数: 7`；`HUNK_COUNT = 9` |
| `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics_check.py verify` | `0` | `套用结果与 build patched 逐行一致 = True`；`ast.parse(套用后文本) = PASS`；`§7 清单数据行 = 9 ；设计稿 hunk 数 = 9` → `专项检查 A = PASS`；`STATE_MATRIX.json 行数 = 12 ；unknown->high 行数 = 0` → `专项检查 B = PASS`；`earlyReturnsCovered = 5/5` → `专项检查 C = PASS`；`VERIFY_ALL = PASS` |
| `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics_check.py matrix` | `0` | 15 行合成矩阵；`ASSERT 通过：None/{}/缺state/脏值 ⇒ verdict=unknown 且 conf!=high ...`；`MATRIX_ALL = PASS` |
| `python -I -X utf8 -c "<读 `_hunks_frag.md` 逐 hunk 扫 255 条 `+` 行禁词 / 覆盖区间>"` | `0` | `diff blocks = 9`；`total + lines = 255`；`forbidden tokens in ANY + line = 0`；`FRESHNESS_GROUP rec.add in + lines = 8`；`no hunk overlaps E judgment block 5984-5990 = True` |

`build` 里的 `f_region()`（`_draft_semantics_check.py:352-358`）从 `def make_pre_freshness_snapshot(` 截到 `def _dump_json(`，对 5 个禁词逐个 `assert forbidden not in fr`；`:5985-5990` 块用**整段原文** `assert ... in p` 比对（`:376-382`，不是 grep 子串）。`verify` 的 `apply_hunks()`（`:431-467`）按标准 unified diff 语义把设计稿 hunk 套回母本，逐行断言 `-` 行与上下文行原文相等。这是「哪一行代码保证它不进退出码判据」的机器可执行回答。

**未验**：`ast.parse` 静态相等 ≠ 运行时退出码实测——铁律 1 零真机，本稿不运行 `qc151_trip.py`，故「整趟退出码在 F 字段存在时仍只由集合差触发」只由静态断言保证，**未做运行时复现**（§8 第 1 条）。

---

## 7 改动清单 ↔ hunk 对照表

**9 行数据 = §4 里 9 个 `@@ ` hunk**，按出现顺序一一对应（专项检查 A 逐行数）。全文 H 编号以本表为唯一口径，无第 10 个 hunk、无 H10。

| 编号 | 物理改动（母本锚点） | 对应 hunk（§4 序号 / 头） | 治哪条 |
|:--|:--|:--|:--|
| H01 | `:214` 后插入 F 命名空间 5 常量 | §4 #1 / `-212,6 +212,21` | N6 / N9 |
| H02 | `:4460` 后追加 `RESTORE.backup_mtime_pre:{name}` 留痕（不改 `bak[name]` 三键） | §4 #2 / `-4458,6 +4473,10` | N10 |
| H03 | `:4561` 前插入 `make_pre_freshness_snapshot` + `classify_except_freshness`；并改 `:4561-4562` def 签名加 `pre_freshness_snapshot` 形参 | §4 #3 / `-4558,8 +4577,131` | N3 / N1 / N2 / N6 / N5 / N9 |
| H04 | `:4574-4599` 函数体重写：三态判别 + 正常/错误双落盘 + 3 条 `ERROR` 留痕 + `raise` + `info` 扩到 12 键 | §4 #4 / `-4572,20 +4714,105` | N4 / N6 / N10 / N1 / N3 |
| H05 | `:5909` `finalize_trip` 签名加 `pre_freshness_snapshot` 形参 | §4 #5 / `-5906,7 +6133,8` | E1 / N5 |
| H06 | `:5939` **唯一调用点**改为关键字传参 | §4 #6 / `-5936,7 +6164,8` | N5 |
| H07 | `:6296` 后、`:6313 try` 前预初始化 `_pre_freshness_snapshot = None` | §4 #7 / `-6294,6 +6523,9` | E1 / N3 |
| H08 | `:6388` 后构造跑前快照 + 落 `FRESHNESS.captured_at_iso_pre` | §4 #8 / `-6386,6 +6618,15` | E1 / N10 |
| H09 | `:7125` 后把快照传给 `:7117 finalize_trip` | §4 #9 / `-7122,7 +7363,8` | E1 / N5 |

---

## 8 未验与已知限制

1. **未运行真机 / `qc151_trip.py` 本体**：铁律 1 零真机。本会话执行的只是 `python -I -X utf8` 的指纹实算、`_draft_semantics_check.py` 的 `build` / `verify` / `matrix`、逐行读母本、以及扫描 `_hunks_frag.md` 的 `+` 行。所有运行时行为（§3 全表、§6 的退出码结论）均为**结构性结论**，不是真机复现。
2. **未写出候选 `.py`**：铁律 4「本任务只写设计，不写候选」。`patched` 只在检查脚本内存里存在；`build` 输出 `母本行数: 7292  patched 行数: 7534`（`split("\n")` 含末行空串，比探针 `splitlines` 的 7291 多 1，为同一文本）。本次分工只写 `B2B_DESIGN.md` 与 `STATE_MATRIX.json`，未改门禁脚本、未 commit / 未 push。
3. **两路设计稿的取舍登记（D-25 要求）**：本会话 `find lead/b2b_design_20261106 -maxdepth 2 -type f` 与 `find . -name "*_draft_scope*"` 均**无 `_draft_scope*` 文件**，派发材料亦标注「读取失败，可能作者改了文件名」。故**不存在两稿互相矛盾的可比对材料**，无法对第二稿逐条对账，按「未验」记，不把它默认当成「不存在矛盾」。本稿以 `_draft_semantics.md`（磁盘 52,841 B，本会话实读）为唯一设计骨架，凡与 **D-25 裁决约束**或母本实读冲突处，一律以 D-25 / 母本为准，逐项登记：
   - **取舍 A（风险口径）**：语义稿 §1 E1 写「五个早退 + 异常路径必抛 `UnboundLocalError`」、§3 P6 写「`:7038 finally` 必达」，与 `RULING_D25.md:52` 的更正（不得写「必抛 UnboundLocalError」、不得写「finally 无条件进 :7117」，裸名是 `NameError` 风险）冲突 → 本稿 §1 E1 与 §3 改为「风险」措辞并声明未做运行时复现。
   - **取舍 B（finally 调用前失败）**：语义稿 §3 P7 把 `:7048..7116` 全部失败归给 `:7126-7134` 收尾异常分支。本会话实读母本 `:7093` 才是内层 `try:`，`:7126` 的 `except` 只覆盖 `:7099..7125` → 按 D-25「finally 调用前失败必须明确处理」拆为 **P7a（`:7048..7092`，外层直接传播）/ P7b（`:7099..7116`，由 `:7126-7134` 接）**，两行都如实写「未调用 `finalize_trip`、无 F 字段落盘」。
   - **取舍 C（H 编号漂移）**：语义稿散文里 §1 N6/N10 把 `captured_at_iso_pre` 归 H09、§3 P1 把预初始化归 H08、§3 P6/「为什么不会崩」出现不存在的 **H10**。以 §7 表与 §4 实际 hunk 顺序为唯一编号（H01–H09），本稿全文统一：H05 = 形参、H06 = 唯一调用点、H07 = 预初始化、H08 = 快照赋值 + `captured_at_iso_pre`、H09 = 传给 `finalize_trip`。
   - **取舍 D（前缀表述）**：语义稿 §1 N9 / §5 称 F 字段「键名一律带 `freshness_` 前缀」，与 H04 `_emit_f` 实码（4 键带前缀、3 键同 group 独立名）冲突 → 按 diff 收窄为「全部落 `FRESHNESS` group，其中 4 键带前缀」（§5 / §6 ①）。
   - **取舍 E（内联注释不精确）**：H01 注释「整趟退出码唯一判据恒在 :5985-5990」与母本实读的 `:5944` / `:7075` / `:7130` 等 `note_cleanup_failure` 调用点不符。该行属 diff 内注释，为保持 9 个 hunk 与实算 `patched` 逐字一致**未改动**；本稿 §6 的绑定结论收窄为「E 集合差块 `:5984-5990` 逐字未改 + F 区 `+` 行零退出码符号」，并在此登记为已知文字不精确（非可执行语义）。同理 H04 内 `note="★ unknown / absent_confirmed / present / error 三态可分"` 列了 4 值却写「三态」，亦为注释文字，未改动。
   - **取舍 F（状态矩阵口径）**：语义稿 §2 机器可读块把 `post_read_error` 塞进 `state` 字段、且未含独立的 `missing_sha` 行。本稿 `STATE_MATRIX.json` 把 `state` 定为矩阵行类别（含 `unknown` / `absent_confirmed` / `absent_both` / `leftover_unchanged` / `new_write` / `rewritten_same_content` / `vanished` / `missing_sha` 等），`preState` 定为 4 态采集态，并显式补 `missing_sha` 两行（跑前缺 sha / 跑后缺 sha），以满足派发材料 `TASK.md:49-64` 与本任务硬性格式。§2 表格与之逐行一致。
4. **未产出 `review/B2B_DESIGN_REVIEW.md` 与 `check_b2b.py`**：`TASK.md:97` / `:121` 把二者列为其他分工的交付物；本会话 `find . -name "check_b2b.py" -o -name "B2B_DESIGN_REVIEW.md" -o -name "STATE_MATRIX.json" -o -name "B2B_DESIGN.md"`（写本稿前）实查**均不存在**。因此 `TASK.md:128` 的完整门禁（要求复核件存在且 `checkedEveryRow: true` / `hunksMatchManifest: true` / `earlyReturnsCovered: 5/5`）**未运行**，按现状**不会 PASS**；本稿只交付两个文件，不伪造复核结论。本会话实际运行的是 `_draft_semantics_check.py` 的 `verify`（其专项检查 A/B/C 均 PASS，但检查对象是 `_draft_semantics.md`，不是本稿）。
5. **本稿自身未按 `check_b2b.py` 门禁跑过**：该脚本不存在（第 4 条）。本会话对本稿**另实跑**了一段 `python -I -X utf8` 内嵌校验脚本（非 `check_b2b.py`，未落盘为交付物），得 `FINAL_ALL_CHECKS = PASS`、`FINAL_EXIT=0`，逐项核：章节 0–8 齐全、三件指纹格式、`## 1` 恰 10 个 `####`、`## 2` 14 行 / `## 3` 11 行 / `## 7` 9 行、`## 8` 非空、全文 `^@@ ` 恰 9 行且 9 个 diff 块与 `_hunks_frag.md` **逐字相等**、9 个 hunk 无损回套母本（`-`/上下文行逐行断言）+ `ast.parse` PASS（7534 行）、E 判据块 `:5984-5990` 在套用后文本中逐字仅 1 处、`except_set_diff :672-708` 逐字未变、F 区零禁词且 `FRESHNESS_GROUP` 写入 7 次、`STATE_MATRIX.json` 14 项 / 五键齐全 / unknown 不落 high / 八类全覆盖 / 全表 `usableAsCrashEvidence=false`、母本收尾指纹未变。**这不是 `TASK.md:121-130` 所要求的 `check_b2b.py` exitCode 0**，也不是 §6 之外新增的独立复核；本会话实际运行的 `verify`（专项检查 A/B/C 全 PASS）检查对象是 `_draft_semantics.md`，不是本稿。
6. **`mtime` 的 TOCTOU / 文件系统语义未验**：H03 用 `p.stat()`、H04 用 `src.stat()` 与 `read_bytes()` 两次调用；NTFS 时间戳精度 / 时钟回拨只在 `classify` 里降级为 `low`，未做介质实测。
7. **`Recorder` 是扁平列表**（母本 `:436-455`，本会话实读）：`group` 仅是字符串，不带类型系统。§5 的类型 / 取值域是**契约**而非运行时强制；下游须按 `FRESHNESS_VERDICTS` / `FRESHNESS_CONFIDENCES` / `FRESHNESS_SNAPSHOT_STATES` 校验。若需运行时强类型，须另立裁定，本稿不改母本 `:436-454`。
8. **`RESTORE.backup_mtime_pre` 的取值范围**：H02 追加在 `:4460` 之后、`:4456 continue` 之后 ⇒ 只对**实际备份成功**的件留痕；源件不存在时无此字段，按「未测」记，不写 `False` 表示未知。
9. **hunk `+` 侧行号为构造结果**：由 `difflib.unified_diff` 在内存 `patched` 上实算；仅保证「按 §4 顺序套用到本稿头部指纹的母本副本」时自洽（`verify` 逐行回套已证），不保证与任何**未套用其它改动**的第三方副本行号一致。
10. **只读域的既有工作树状态未归属**：对话开头 gitStatus 快照列 `MM lead/GOAL_THREE_TARGETS_20261018.md` / `MM lead/PENDING_DECISIONS.md` 等，语义稿 §8 第 12 条另记 `?? lead/re_line_20261105/`。这些是**本任务开工前即存在**的工作树状态，本次会话未对其写入一字；其来源 / 归属**未验**，按「未知」记，不默认当作不存在，也不冒充本稿改过。
11. **旧治理文件未作废**：`lead/re_line_20261105/**` 属铁律 3 只读域；`B2_PREAUDIT.md` 中关于旧 TASK「只改三处」「git diff」的矛盾**不在本稿授权范围内解决**，需有权者另给替换版任务书。本稿只对 `TASK.md:34-45` 的十条负责。
12. **母本指纹收尾复核**：写完全部交付物后重算母本，命令与输出见本条下方；若与头部 `517889c6… / 399508 B` 不一致应以实算为准。本会话在写交付文件前后的实算均为 `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 399508`（命令 `python -I -X utf8 -c "import hashlib;d=open(<母本绝对路径>,'rb').read();print(hashlib.sha256(d).hexdigest(),len(d))"`），逐字相同 ⇒ 母本一个字节未改。只读域未触碰；未启真机；未写采样代码；未 commit / 未 push。
