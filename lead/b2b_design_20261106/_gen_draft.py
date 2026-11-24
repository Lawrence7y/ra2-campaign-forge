# -*- coding: utf-8 -*-
"""拼装 _draft_semantics.md：散文段 + 逐字 diff 片段（片段由 builder 实算产生）。"""
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAG = io.open(HERE / "_hunks_frag.md", encoding="utf-8").read()

HEAD = r'''# B2b 语义设计稿 · 状态矩阵 / 置信口径 / 字段契约（N3 / N4 / N6 / N10 / N9）

**角色**：B2b 设计员·semantics（本稿只负责状态可分性、正常/错误双落盘、字段契约、复制失败留痕、F/E 实现级分离）。
**唯一写域**：`lead/b2b_design_20261106/`。**母本一个字节未改**、只读域未改、不 commit、不 push、零真机、零采样代码。
**本稿不是候选**：`patched` 文本只存在于 `_draft_semantics_check.py` 的内存里，`ast.parse` 后即丢弃，**没有写出任何候选 .py**。

---

## 0 开工实测（本次会话实算 / 实读，不抄派发材料）

**指纹命令**（`python -I -X utf8 -c ...`，绝对路径，本机无 `sha256sum`/`wc`）：

```
python -I -X utf8 -c "import hashlib,sys
for p in sys.argv[1:]:
    d=open(p,'rb').read()
    print(hashlib.sha256(d).hexdigest(), len(d), len(d.splitlines()), p)" <三个绝对路径>
```

**输出**（`sha256 / 字节数 / splitlines 行数 / 路径`）：

| 对象 | sha256 | 字节数 | 行数 |
|:--|:--|--:|--:|
| 母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 | 7291 |
| 旧 B2 `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11638 | 236 |
| W11 参考 `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py` | `e6685167f5d26030f9a2e28df06ee2fbda23c7e91687aa209f6769ac3450480b` | 13190 | 278 |

母本 SHA256 与 `lead/b2b_design_20261106/TASK.md:21` 预期值一致 ⇒ **未触发 STOP**，未写 `STOP_MOTHER_DRIFT.md`。
`TASK.md:23` 只给了 W11 的 13,190 B（本次实算一致），**未给 W11 的 SHA256**；本稿补齐其 SHA256 供复核员对照。

**结构锚点**（派发材料已给 `_b2b_probe_out.txt:1-182`，本稿另用 `_draft_semantics_check.py anchors` 逐行重读母本原文交叉核对，输出 `_draft_semantics_anchors_out.txt`）：

| 锚点 | 母本原文（截断 110 字符） | 依据 |
|:--|:--|:--|
| `:214` | `                 "ra2opt_play.bat", "except.txt")` | `_draft_semantics_anchors_out.txt` / 探针 §7 |
| `:4460` | `        bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}` | 探针 `[7]` |
| `:4561-4562` | `def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,` / `                              out_dir: Path) -> dict \| None:` | 探针 `[2]` |
| `:4574` | `    src = carrier_dir / "except.txt"` | 本稿实读 |
| `:4583-4586` | `info = {...}` 五键 `source/evidence_path/size/sha256/note` | 探针 `[9]` |
| `:4587` | `    rec.add("EXCEPT", "evidence_copy", info, f"{src}:file",` | 探针 `[9]` |
| `:5909` | `                  created_receipt: dict \| None = None) -> int:` | 探针 `[1]` |
| `:5938-5939` | `def _except_evidence_copy()` / `        copy_post_except_evidence(rec, carrier_dir, out_dir)` | 探针 `[3]`（唯一调用点） |
| `:6294-6296` | `bak: dict = {}` / `t0: list = []` / `pre_except_txt = None` | 本稿实读 `qc151_trip.py:6293-6296` |
| `:6387-6388` | `bak = backup_carrier(rec, carrier_dir)` / `budget.end_stage("backup")` | 探针 `[4]` |
| `:7125` | `                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt))` | 探针 `[6]` |
| `:677` | `- ★ **不得**用 \`sha\` 变化判 crash（★ 游戏自身会重写该文件）。` | 探针 `[8]` |
| `:5985-5990` | 唯一影响退出码的集合差块 | 探针 `[8]` |
| `:439-440` | `未读到写「未测」/ 不可测写 null / 不提供「写 False 表示未知」的口子` | `qc151_trip.py:436-450`（本稿实读） |
| `:167/:173/:174/:175` | `import hashlib` / `import time` / `from datetime import datetime, timezone` / `from pathlib import Path` | 本稿实读 ⇒ **无需新增 import** |

**五个早退 return**（探针 `[5]` 实测，全部早于 `:6387`，且 `:7038 finally` → `:7117 finalize_trip` 必达）：
`:6340 EXIT_CARRIER_NOT_OWNED` / `:6349 EXIT_TARGET_MISSING` / `:6361 EXIT_TARGET_MISMATCH` / `:6374 EXIT_PRECHECK_SHA_MISMATCH` / `:6377 EXIT_PRECHECK_SIG_MISMATCH`。

---

## 1 B2 被否的十条如何逐条根治（每条都有 diff 行号）

十条与 hunk 的对应关系见 `## 7`。以下每条**只指认已给出的 hunk**，没有「将修改」。

#### E1 快照零赋值 / 早退未绑定

**根因**（`B2_PREAUDIT.md:70-72`）：B2 全文零次赋值 `_pre_freshness_snapshot`，却在主调用点传裸名；五个早退 + 异常路径必抛 `UnboundLocalError`。

**根治**：**H07** 在 `:6296` 之后、`:6313 try:` 之前预初始化 `_pre_freshness_snapshot: dict | None = None`（`@@ -6294,6 +6523,9 @@`，上下文 `bak/t0/pre_except_txt` 三行逐字对齐探针 `[5]`/本稿 anchors）；**H08** 才在 `:6388` 之后（载体定稿、launch 前）真正赋值 `make_pre_freshness_snapshot(...)`（`@@ -6386,6 +6618,15 @@`）；**H05** 让 `finalize_trip` 收到形参（`@@ -5906,7 +6133,8 @@`）；**H09** 在 `:7125` 后把该已绑定的名字传进收尾（`@@ -7122,7 +7363,8 @@`）。四点构成完整作用域链，`None` 明确标注为 **未采集（unknown）**，不是「跑前无件」。

#### N5 唯一调用点 `:5939` 无 diff

**根因**（`B2_PREAUDIT.md:86-88`）：`:5939` 是 `copy_post_except_evidence` 全文件唯一真实调用点（探针 `[3]`：AST 调用点个数 1，实参 `['rec','carrier_dir','out_dir']`，关键字实参 `[]`），B2 加了形参却没人传。

**根治**：**H06** `@@ -5936,7 +6164,8 @@` 逐字核过母本 `:5936/:5937/:5938/:5939`（anchors 输出在册），把 `:5939` 改成两行关键字传参 `pre_freshness_snapshot=pre_freshness_snapshot`。**H03** 同步给 `:4561-4562` 的 def 加同名形参（`@@ -4558,8 +4577,131 @@` 尾部）。调用点与签名一一闭合，不再「全趟恒走降级」。

#### N4 正常路径算完不落盘

**根因**（`B2_PREAUDIT.md:82-84`）：B2 在 `:163` 之后到 hunk 结束没有任何 `rec.add`；母本 `:4583-4586` 的 `info` 仍 5 键。

**根治**：**H04** `@@ -4572,20 +4714,105 @@` 把函数体重写成 **三条出口全部落盘**：
- 正常路径：`info` 从 5 键扩到 12 键（`mtime_post / freshness_verdict / freshness_confidence / freshness_note / captured_at_iso / pre_snapshot_state / pre_freshness_snapshot` 七键），先 `rec.add("EXCEPT","evidence_copy",info,...)` 再 `_emit_f(fresh,"copied")`；
- `src_missing` 早退分支：`_emit_f(...,"src_missing")`；
- `copy_failed` 异常分支：`_emit_f(...,"copy_failed")` 后 `raise`。
`_emit_f` 每次固定写 7 个 `FRESHNESS` group 字段（builder 输出 `F 区 FRESHNESS_GROUP 写入次数: 7`）。**正常与错误两条分支都不空转**。

#### N6 字段全缺（名称/类型/取值域/写入点）

**根因**（`B2_PREAUDIT.md:55/:82/:111`）：`freshness_confidence` / `freshness_note` / `captured_at_iso` 在 B2 全文各 0 次。

**根治**：**H01** 定义 `FRESHNESS_GROUP` / `FRESHNESS_KEY_PREFIX` / `FRESHNESS_VERDICTS` / `FRESHNESS_CONFIDENCES` / `FRESHNESS_SNAPSHOT_STATES` 五个**单一真源常量**（`@@ -212,6 +212,21 @@`）；**H03/H04** 写入三字段；完整契约表见 `## 5`。`captured_at_iso` 双份：跑前在快照 `make_pre_freshness_snapshot` 内（H03），跑后在 `post_observed` 与 `info`（H04），并由 H09 单独落 `FRESHNESS.captured_at_iso_pre`。

#### N3 三态折叠 / 未知当不存在

**根因**（`B2_PREAUDIT.md:78-80`）：`{}` 与 `{"exists":False}` 被压成同一状态并恒给 `high`。

**根治**：**H03** 的 `make_pre_freshness_snapshot` 用 `state` 作**唯一判别口**（`unknown / absent_confirmed / present / error` 四态），`exists` 不得反推状态；`classify_except_freshness` 首段把 `None / {} / 缺 state / 脏值` 一律归一为 `unknown`，且在**第一个分支**就让 `unknown` 与 `absent_confirmed` 分道。**H07** 把预初始化值显式注释为「未采集（unknown），绝不等于跑前无件」。

实跑证据（`python -I -X utf8 _draft_semantics_check.py matrix`，输出 `_draft_semantics_matrix_out.txt`）：

```
  pre=None (未采集) + 跑后有历史件                -> verdict='unknown'  conf='none'  is_new=None  crash_ev=False
  pre={} (空) + 跑后有历史件                    -> verdict='unknown'  conf='none'  is_new=None  crash_ev=False
  pre={exists:False} 伪折叠 + 跑后有历史件        -> verdict='unknown'  conf='none'  is_new=None  crash_ev=False
  pre 脏 state=zzz + 跑后有历史件               -> verdict='unknown'  conf='none'  is_new=None  crash_ev=False
ASSERT 通过：None/{}/缺state/脏值 ⇒ verdict=unknown 且 conf!=high 且 usable_as_crash_evidence=False
```

`{exists:False}`（无 `state`）**不再是「确认无件」**——确认无件必须显式带 `state="absent_confirmed"`。这正是「不许把未采集当不存在」的实现级写法。

#### N1 异常路径静默降级

**根因**（`B2_PREAUDIT.md:70-76`）：采集异常无独立出口，被降级成 `high`。

**根治**：**H03** 采集抛异常 ⇒ `state="error"` + `error` + `traceback` 留痕，判定器给独立 verdict `error_pre_snapshot` / `confidence="none"`；**H04** 复制/读取抛异常 ⇒ 三条 `rec.add("ERROR",...)`（`freshness_copy_failed` / `freshness_copy_stage` / `freshness_copy_traceback`）后 `_emit_f(...,"copy_failed")` 走 `post_read_error` 独立出口，**再 `raise` 原异常**（与母本 `run_guarded_steps:4534` 不吞口径一致）。`matrix` 里 `pre.state=error` → `verdict='error_pre_snapshot' conf='none'`、跑后读失败 → `verdict='post_read_error' conf='none'`，均非 `high`。

#### N2 遗留件恒 high

**根因**（`B2_PREAUDIT.md:74-76`）：快照缺失时历史遗留 `except.txt` 恒判 `new_first_appearance/high`。

**根治**：**H03** 的 `unknown` 分支 `return _finish("unknown","none",None,...)`，硬编码 `usable_as_crash_evidence=False`；`new_first_appearance/high` **只在** `state=="absent_confirmed" and post_exists` 时可达（即跑前确实采到「无件」）。`matrix` 第 1–4 行证明四种缺失形态都停在 `unknown/none`，历史遗留件不再被误标。

#### N7 清单与 hunk 不等

**根因**（`B2_PREAUDIT.md:94-96`）：B2 清单 8 条、hunk 4 个。

**根治**：本稿 `## 7` 清单 **9 行**（H01–H09… 实为 H01–H09 共 9 条），`## 4` 恰 **9 个 `@@` hunk**，逐行一一对应。`_draft_semantics_check.py verify` 的专项检查 A 会数 `## 7` 的数据行与 `## 4` 的 hunk 数并断言相等。**一个 hunk 都不多、一个都不漏**。

#### N10 captured_at_iso 被删 / 复制失败无留痕

**根因**（`B2_PREAUDIT.md:106-108`）：`captured_at_iso` 全文 0 次，`write_bytes` 失败无 `rec.add("ERROR",...)` 守卫。

**根治**：**H03** 快照双时刻 `captured_at_epoch` + `captured_at_iso`；**H04** `post_observed["captured_at_iso"]`、`info["captured_at_iso"]`、`_emit_f` 的 `FRESHNESS.captured_at_iso`；**H09** `FRESHNESS.captured_at_iso_pre`；**H02** `RESTORE.backup_mtime_pre:{name}`（`@@ -4458,6 +4473,10 @@`，不改 `bak[name]` 三键契约，只在 `:4460` 后追加一行留痕）；**H04** 的三条 `ERROR` 留痕 + `raise` 满足「先留痕再上抛，不许静默」。

#### N9 F/E 分离无实现约束

**根因**（`B2_PREAUDIT.md:110-112`）：`:205` 只有「F 只答新鲜性」的断言，无命名/group/退出码约束。

**根治**：**H01** 强制 F 命名空间 `FRESHNESS` group + `freshness_` 键前缀（E 恒 `EXCEPT`，探针 `[9]` 已证）；**H03/H04** 的 F 区不含任何退出码符号；**H05/H06/H07/H09** 只传数据、不碰 `:5985-5990`。实现级约束与测试见 §6。

---

## 2 状态矩阵

`state` = 跑前快照的**采集态**（四态可分）；`condition` = 输入条件；`verdict` ∈ `FRESHNESS_VERDICTS`；`confidence` ∈ `FRESHNESS_CONFIDENCES`（`none` = 不可判，非 low）；`usableAsCrashEvidence` 恒 `false`（`:677` 口径）。

机器可读版（供门禁消费；`## 4` 的 `check` 会解析它）：

```json
[
 {"state":"unknown","condition":"pre=None / {} / 缺 state / 脏值（未采集或采集未完成），跑后任意","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
 {"state":"error","condition":"跑前采集抛异常（snap.error 非空）","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
 {"state":"post_read_error","condition":"跑后 read_bytes/stat/write_bytes 抛异常（post.read_error 非空）","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false},
 {"state":"absent_confirmed","condition":"跑前确认无件 + 跑后无件","verdict":"absent_both","confidence":"low","usableAsCrashEvidence":false},
 {"state":"absent_confirmed","condition":"跑前确认无件 + 跑后在场（存在性硬证）","verdict":"new_first_appearance","confidence":"high","usableAsCrashEvidence":false},
 {"state":"present","condition":"跑前在 + 跑后在 + sha 一致 + mtime 未变（含 mtime 侧缺失）","verdict":"leftover_unchanged","confidence":"high|medium","usableAsCrashEvidence":false},
 {"state":"present","condition":"跑前在 + 跑后在 + sha 不同","verdict":"new_write","confidence":"high","usableAsCrashEvidence":false},
 {"state":"present","condition":"跑前在 + 跑后在 + sha 同 + mtime 变大","verdict":"rewritten_same_content","confidence":"medium","usableAsCrashEvidence":false},
 {"state":"present","condition":"跑前在 + 跑后在 + sha 同 + mtime 回拨","verdict":"rewritten_same_content","confidence":"low","usableAsCrashEvidence":false},
 {"state":"present","condition":"跑前在 + 跑后在 + 缺 sha（B 主判据不可用）","verdict":"error_pre_snapshot","confidence":"none","usableAsCrashEvidence":false},
 {"state":"present","condition":"跑前在 + 跑后无件（被删/改名/复制链中断）","verdict":"vanished","confidence":"none","usableAsCrashEvidence":false},
 {"state":"present","condition":"跑前在 + 跑后缺 sha256","verdict":"post_read_error","confidence":"none","usableAsCrashEvidence":false}
]
```

**派发材料 §3.1 的 8 种状态逐条对账**：① unknown（第 1 行）② absent_confirmed（第 4/5 行）③ leftover_unchanged（第 6 行）④ new_write（第 7 行）⑤ rewritten_same_content（第 8/9 行）⑥ present + 缺 sha → 独立出口 `error_pre_snapshot`（第 10 行）⑦ vanished → `none` + 须人工复核（第 11 行）⑧ absent_both → `low` + 不能证无崩溃（第 4 行）。**`unknown` 恒 `none`，不存在 `unknown → high` 映射**（专项检查 B）。

**置信口径三条硬规**：
1. `high` 只给「跑前确实采到 + 判据完整」的 `new_first_appearance` / `new_write` / `leftover_unchanged(mtime 齐全)`；
2. `low` 给 `absent_both`（不能证无崩溃）与 `rewritten_same_content` 时钟回拨；`medium` 给旁证不全/同内容重写；
3. `none` 给**所有不可判出口**（unknown / error / vanished / post_read_error），且 `is_new=None`（母本 `:439-440` 的「不可测写 null」）。

---

## 3 早退与异常路径覆盖表

`snapshotValue` = `finally` 进入时 `_pre_freshness_snapshot` 的值；`finalizeReceives` = `:7117` 调用实参；`outputVerdict` = `FRESHNESS.freshness_verdict`；`crashes` = 是否抛未绑定/未留痕异常。

| pathId | 触发点 | snapshotValue | finalizeReceives | outputVerdict | crashes |
|:--|:--|:--|:--|:--|:--|
| P1 | `main:6340` `return EXIT_CARRIER_NOT_OWNED`（所有权不成立，早于 `:6387`） | `None`（H08 预初始化，未采集态） | `pre_freshness_snapshot=None` | `unknown` / `none`（若跑后有遗留件，绝不给 `high`） | 否：名字已绑定；`finally`→`finalize_trip`→`_except_evidence_copy`→`:5939` 收 `None`，分类器归一为 `unknown` |
| P2 | `main:6349` `return EXIT_TARGET_MISSING` | `None` | `None` | `unknown` / `none` | 否（同上） |
| P3 | `main:6361` `return EXIT_TARGET_MISMATCH`（哈希不符） | `None` | `None` | `unknown` / `none` | 否（同上） |
| P4 | `main:6374` `return EXIT_PRECHECK_SHA_MISMATCH` | `None` | `None` | `unknown` / `none` | 否（同上） |
| P5 | `main:6377` `return EXIT_PRECHECK_SIG_MISMATCH` | `None` | `None` | `unknown` / `none` | 否（同上） |
| P6 | `try` 内 `:6313..7029` 任一点抛 `BaseException`（`:7030 except` 写 `write_finalize_error` 后 `:7037 raise`，`:7038 finally` 必达） | 视抛出点：早于 `:6389` 为 `None`；晚于则为 `make_pre_freshness_snapshot` 的 dict | 该值经 H10 传入 | `None` → `unknown`；dict → 按 §2 判定 | 否：原异常由 `:7037 raise` 保留；H04 的复制失败分支先 `rec.add("ERROR")` 再 `raise`，`:4534 run_guarded_steps` 跑完全部收尾项后原样重抛 |
| P7 | `finally` 内 `:7048..7116` 失败（终止失败 / `fin_ownership` 构造 / 冻结基线回读），未到 `:7117` | 已绑定值（H08） | **未调用** `finalize_trip`（`:7126-7134` 收尾异常分支接 `note_cleanup_failure` + `write_finalize_error` + `raise`） | 无 F 字段落盘（如实：收尾未跑到证据项） | 否：不产生新未绑定名；原异常/收尾异常按 `QC157:4` 向外传播 |
| P8 | 正常路径 `:7029 return EXIT_OK`（经 `:6389` 快照构造） | `dict` with `state ∈ {absent_confirmed, present, error}` | 该 dict | 按 §2 六/八分支（正常路径 `_emit_f(...,"copied")` 必落盘） | 否 |
| P9 | `:6445/:6478/:6496/:7021` 四个不早于 `:6387` 的 return（探针 `[5]`） | `dict`（`:6389` 已赋值） | 该 dict | 按 §2 | 否 |
| P10 | `copy_post_except_evidence` 内 `dst.write_bytes` 抛异常（H04 异常分支） | 上层传入值不变 | 上层传入值不变 | `post_read_error` / `none`，另 3 条 `ERROR` 留痕 | 否：`raise` 原异常，`:4507 run_guarded_steps` 记账后重抛，不静默 |

**五个早退逐条覆盖率 = 5/5**（P1–P5，专项检查 C）。P6/P7 覆盖派发材料「外加」的两条路径；P8–P10 补正常/其余 return/复制失败。

**为什么不会崩**：H08 在 `try` 之前（`:6296` 后）就绑定名字，五个早退 `return` 在 `:6313 try` 内但**都晚于 H08**；`:7038 finally` 读的是同一函数作用域里已绑定的局部（母本 `:6293-6296` 已有 `bak/t0/pre_except_txt` 同样的预初始化先例）；H07 把值接成形参、H10 传给收尾、H06 传给唯一调用点，`None` 在分类器里是**合法输入**（归一为 `unknown`），不是错误。

---

## 4 完整 diff（9 个 `@@` hunk，逐字取自 `difflib.unified_diff(n=3)`）

全部 hunk 由 `_draft_semantics_check.py build` 在内存里构造 `patched` 后实算产生（输出 `_draft_semantics_build_out.txt`），**未手工改写任何一行**。每个 hunk 的 `-` 行与上下文行均与母本原文逐字相等（`verify` 阶段会重新逐行断言）。应用目标为母本 `qc151_trip.py`；行号为**母本 1-based 锚点**，`+` 侧行号为应用后行号（供参考）。

'''

TAIL = r'''

---

## 5 字段契约

母本 `Recorder.add`（`:446`，探针 `[10]`）签名 `(self, group: str, key: str, value, source: str, note: str = "") -> None`，`value` 无注解；`rec.dump`（`:452-454`）把全部行写进 `qc151_fields.json`。以下每个字段都给名称/类型/取值域/写入点/消费方。

| 字段（`group.key`） | 类型 | 取值域 | 写入点（hunk / 应用后位置） | 消费方 |
|:--|:--|:--|:--|:--|
| `FRESHNESS_GROUP` = `"FRESHNESS"` | `str` 常量 | 固定值 | H01（`:214` 后） | H03/H04/H09 全部 F 写入；下游按 group 过滤 |
| `FRESHNESS_KEY_PREFIX` = `"freshness_"` | `str` 常量 | 固定值 | H01 | H04 `_emit_f` 键名拼接 |
| `FRESHNESS_VERDICTS` | `tuple[str]` | 9 个 verdict（§2） | H01 | 门禁校验 verdict 取值域 |
| `FRESHNESS_CONFIDENCES` | `tuple[str]` | `high / medium / low / none` | H01 | 门禁校验 `unknown` 不落 `high` |
| `FRESHNESS_SNAPSHOT_STATES` | `tuple[str]` | `unknown / absent_confirmed / present / error` | H01 | H03 判别口 |
| `snapshot.state` | `str` | 同上 4 值 | H03 `make_pre_freshness_snapshot` | H03 分类器 / §2 矩阵 |
| `snapshot.exists` | `bool \| None` | `True / False / None` | H03 | 仅回显，**不得**用于反推 state |
| `snapshot.size` | `int \| None` | ≥0 / `None` | H03 | 复核 |
| `snapshot.sha256` | `str \| None` | 64 hex / `None` | H03（复用母本 `:416 sha256_file`） | B 主判据 |
| `snapshot.mtime_pre` | `float \| None` | epoch 秒 / `None` | H03 | A 旁证（`abs` 差分） |
| `snapshot.captured_at_epoch` | `float \| None` | epoch 秒 / `None` | H03 | 时间线复核（**N10 必留**） |
| `snapshot.captured_at_iso` | `str \| None` | ISO-8601 / `None` | H03（`now_iso()`，母本 `:432-433`） | H09 转写为 `FRESHNESS.captured_at_iso_pre`（**N10 必留**） |
| `snapshot.error` / `snapshot.traceback` | `str \| None` | 异常摘要 / 栈文本 / `None` | H03（仅采集失败） | 独立 `error_pre_snapshot` 出口 |
| `post_observed.mtime_post` | `float \| None` | epoch 秒 / `None` | H04 `src.stat()` | A 旁证 / `info.mtime_post` |
| `post_observed.captured_at_iso` | `str \| None` | ISO-8601 / `None` | H04 | `info` + `FRESHNESS.captured_at_iso` |
| `post_observed.read_error` | `str \| None` | 异常摘要 / `None` | H04（仅复制/读失败） | `post_read_error` 独立出口 |
| `FRESHNESS.freshness_verdict` | `str` | `FRESHNESS_VERDICTS` | H04 `_emit_f` 三条出口 | 复核员 / 状态矩阵门禁 |
| `FRESHNESS.freshness_confidence` | `str` | `FRESHNESS_CONFIDENCES` | H04 `_emit_f` 三条出口 | 专项检查 B |
| `FRESHNESS.freshness_is_new` | `bool \| None` | `True / False / None` | H04 `_emit_f` 三条出口 | `None` = 未测写 null（`:439-440`） |
| `FRESHNESS.freshness_note` | `str` | 人类可读说明 | H04 `_emit_f` 三条出口 | 复核员 |
| `FRESHNESS.pre_snapshot_state` | `str` | 4 态 | H04 `_emit_f` 三条出口 | 三态可分性取证 |
| `FRESHNESS.usable_as_crash_evidence` | `bool` | **恒 `False`** | H04 `_emit_f` 三条出口 | `:677` 口径护栏 |
| `FRESHNESS.captured_at_iso` | `str \| None` | ISO-8601 / `None` | H04 `_emit_f` 三条出口 | 跑后观测时刻（**N10**） |
| `FRESHNESS.captured_at_iso_pre` | `str \| None` | ISO-8601 / `None` | H08（`:6388` 后） | 跑前捕获时刻（**N10**） |
| `EXCEPT.evidence_copy`（`info` 由 5 键扩到 12 键） | `dict \| None` | 原 5 键 + 7 新键，见下 | H04（正常路径与 `src_missing` 分支） | 母本既有消费方；新增键只读不破契约 |
| `info.mtime_post` | `float` | epoch 秒 | H04 | 复核 |
| `info.freshness_verdict` | `str` | `FRESHNESS_VERDICTS` | H04 | 正常路径 F 结论（**N4**） |
| `info.freshness_confidence` | `str` | `FRESHNESS_CONFIDENCES` | H04 | **N6** |
| `info.freshness_note` | `str` | 说明文本 | H04 | **N6** |
| `info.captured_at_iso` | `str` | ISO-8601 | H04 | **N10** |
| `info.pre_snapshot_state` / `info.pre_freshness_snapshot` | `str` / `dict \| None` | 4 态 / 快照原样（未采集为 `None`） | H04 | 可追溯；未知态留 `None` 不折叠 |
| `RESTORE.backup_mtime_pre:{name}` | `float` | epoch 秒 | H02（`:4460` 后，`name ∈ CARRIER_FILES` 5 件，探针 `[7]`） | **N10** 留痕；不改 `bak[name]` 三键 |
| `ERROR.freshness_copy_failed` | `str` | `{type}: {msg}` | H04 异常分支 | 复制失败留痕（**N10/N1**） |
| `ERROR.freshness_copy_stage` | `str` | `read_bytes/stat/write_bytes` | H04 异常分支 | 定位失败阶段 |
| `ERROR.freshness_copy_traceback` | `str` | 栈文本 | H04 异常分支 | 复核 |
| `main._pre_freshness_snapshot` | `dict \| None` | 快照 dict / `None`（未采集） | H07 预初始化 / H08 赋值 / H09 传出 | E1 作用域链 |
| `finalize_trip.pre_freshness_snapshot` | `dict \| None` | 同上 | H05 形参 → H06 传给 `:5939` | N5 接线 |

**命名不冲突**：F 全部字段落在 `FRESHNESS` group 且带 `freshness_` 前缀或独立名；E 的 `EXCEPT.evidence_copy` 只是**扩键**（追加 7 键，原 5 键与 `rec.add` 的 group/key/source/note 一个字节不改，探针 `[9]` 可核），不新增同名 E 键。母本 `EXCEPT` group 的既有键（`set_diff_method` `:702`、`evidence_copy` `:4587` 等）保持原样。

---

## 6 F/E 分离的实现级约束

**F（freshness）**：`except.txt` 在**本趟窗口内**是否被写/新出现。唯一实现 = H03 两个纯函数 + H04 的 `_emit_f`。
**E（新异常）**：唯一口径恒为母本 `except_set_diff`（`:672-708`，探针 `[8]`），其判据是 `collections.Counter` 多重集差里含 `Exception occurred at` 的行（`:689`），`:677` 明令**不得用 sha 变化判 crash**。

| 约束 | 实现方式 | 可验证证据 |
|:--|:--|:--|
| ① 字段命名隔离 | H01：`FRESHNESS_GROUP="FRESHNESS"` + `FRESHNESS_KEY_PREFIX="freshness_"`；E 恒 `EXCEPT` | `_draft_semantics_check.py build` 打印 `F 区 FRESHNESS_GROUP 写入次数: 7` |
| ② group 隔离 | H04 `_emit_f` **全部** `rec.add(FRESHNESS_GROUP, ...)`；`info` 保留在 `EXCEPT.evidence_copy` 仅为「证据副本元信息」扩键，不新增 E 判据键 | 探针 `[9]` 的 `EXCEPT.evidence_copy` 写入点未被删除/改名 |
| ③ **不得进入退出码判据** | 母本 `:5985-5990` 是唯一影响退出码处（`TASK.md:74` + 探针 `[8]`），**本稿 9 个 hunk 一个字节都没碰 `:5984-5990`**；F 区代码里不出现 `note_cleanup_failure` / `no_new_exception` / `EXIT_` / `except_set_diff(` / `CLEANUP_FAILURES` | `build` 阶段两条硬断言：`E 口径 unchanged = PASS`、`F/E 静态门禁 ... = PASS`；`verify` 阶段重跑 |
| ④ F 结论恒不可作崩溃证据 | H03 `_finish` 每次把 `usable_as_crash_evidence` 置 `False`；H04 把它写进 `FRESHNESS` | `matrix` 15 行输出 `crash_ev=False` 全列 |
| ⑤ 无新 import / 无采样 | H03/H04 只用母本已有的 `hashlib`/`time`/`datetime`/`Path`/`json`（`:167/:173/:174/:175`，本稿实读）；无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 | `build` 输出 `依赖 import 已在母本存在 = PASS（无需新增 import）` |

**用什么测试证明**（本次会话实跑命令与输出）：

```
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics_check.py build
  -> ast.parse(patched) = PASS (exitcode 0)
  -> E 口径 unchanged: except_set_diff(:672-708) + :5985-5990 判据块 = PASS
  -> F/E 静态门禁: F 区零 note_cleanup_failure/no_new_exception/EXIT_/except_set_diff(/CLEANUP_FAILURES = PASS
  -> F 区 FRESHNESS_GROUP 写入次数: 7
  -> HUNK_COUNT = 9
```

`build` 里的 `f_region()` 从 `def make_pre_freshness_snapshot(` 截到 `def _dump_json(`，对 5 个禁词逐个 `assert forbidden not in fr`；`:5985-5990` 块用**整段原文** `assert ... in p` 比对（不是 grep 子串）。这两条是「哪一行代码保证它不进退出码判据」的机器可执行回答：F 区物理上不含任何能触发 `note_cleanup_failure` 的符号，且 E 判据块与母本逐字相同。

**未验**：`AST` 静态相等不等于**运行时**退出码实测——铁律 1 零真机，本稿不运行 `qc151_trip.py`，故「整趟退出码在 F 字段存在时仍唯一由集合差触发」只由静态断言保证，未做运行时复现，按「未验」记（见 §8）。

---

## 7 改动清单 ↔ hunk 对照表

**清单 9 条 = `## 4` 里 9 个 `@@` hunk**（专项检查 A 逐行数）。

| 编号 | 物理改动（母本锚点） | 对应 hunk 头 | 治哪条 |
|:--|:--|:--|:--|
| H01 | `:214` 后插入 F 命名空间 5 常量 | `@@ -212,6 +212,21 @@` | N6 / N9 |
| H02 | `:4460` 后追加 `RESTORE.backup_mtime_pre:{name}` 留痕 | `@@ -4458,6 +4473,10 @@` | N10 |
| H03 | `:4561` 前插入 `make_pre_freshness_snapshot` + `classify_except_freshness`；并改 `:4561-4562` def 签名加 `pre_freshness_snapshot` 形参 | `@@ -4558,8 +4577,131 @@` | N3 / N1 / N2 / N6 / N5 / N9 |
| H04 | `:4574-4599` 函数体重写：三态判别 + 正常/错误双落盘 + `ERROR` 留痕 + `raise` + `info` 扩到 12 键 | `@@ -4572,20 +4714,105 @@` | N4 / N6 / N10 / N1 / N3 |
| H05 | `:5909` `finalize_trip` 签名加 `pre_freshness_snapshot` 形参 | `@@ -5906,7 +6133,8 @@` | E1 / N5 |
| H06 | `:5939` **唯一调用点**改为关键字传参 | `@@ -5936,7 +6164,8 @@` | N5 |
| H07 | `:6296` 后 `try` 前预初始化 `_pre_freshness_snapshot = None` | `@@ -6294,6 +6523,9 @@` | E1 / N3 |
| H08 | `:6388` 后构造跑前快照 + 落 `captured_at_iso_pre` | `@@ -6386,6 +6618,15 @@` | E1 / N10 |
| H09 | `:7125` 后把快照传给 `:7117 finalize_trip` | `@@ -7122,7 +7363,8 @@` | E1 / N5 |

（正文 §1 与 §5/§6 一律使用本表 H01–H09 同一编号，无第 10 个 hunk。）

---

## 8 未验与已知限制

1. **未运行真机 / `qc151_trip.py` 本体**：铁律 1 零真机。所有运行时断言来自 `ast.parse`（内存文本）、`difflib` hunk 回套、以及把 H03 纯函数 `exec` 后喂合成字典的离线单测（`matrix`），**不是真机复现**。
2. **未写出候选 .py**：铁律 4「本任务只写设计，不写候选」。`patched` 只在 `_draft_semantics_check.py` 内存里存在；`build` 输出 `母本行数: 7292  patched 行数: 7534`（`split("\n")` 含末行空串，故比探针 `splitlines` 的 7291 多 1），实为同一文本。母本指纹重算仍 `517889c6…/399508 B`，未改。
3. **未做运行时退出码复现**：F/E 隔离只由 `build` 的静态禁词断言 + E 判据块整段原文比对证明（§6）；「F 字段存在时整趟退出码不变」未跑运行时。
4. **未验 `:7048..7116` 之间每一条收尾失败子路径的逐格运行时行为**：P7 只按母本 `:7126-7134` 的 `except` 分支（`qc151_trip.py:7126-7134` 本稿实读）给出结构结论，未逐条合成复现。
5. **`mtime` 的 TOCTOU / 文件系统语义未验**：H03 用 `p.stat()`、H04 用 `src.stat()` 与 `read_bytes()` 两次调用，NTFS 时间戳精度/时钟回拨只在 `classify` 里降级为 `low`，未做介质实测。
6. **`Recorder` 是扁平列表**（`B2_PREAUDIT.md:111` 已指出 `group` 仅是字符串）：`FRESHNESS` group 不自带类型系统，`## 5` 的类型/取值域是**契约**而非运行时强制；下游须按 `FRESHNESS_VERDICTS` / `FRESHNESS_CONFIDENCES` 校验。若需运行时强类型，须另立裁定，本稿不改母本 `:436-454`。
7. **旧治理文件未作废**：`lead/re_line_20261105/**` 属铁律 3 只读域；`B2_PREAUDIT.md:102-104`（E4/E6/旧 TASK 的「只改三处」「git diff」）所述矛盾**不在本稿授权范围内解决**，需有权者另给替换版任务书。本稿只对派发的十条负责。
8. **W11 候选未作为基线**：`TASK.md:23` 明示「语义参考（不是基线）」；本稿只借其 `VERDICT_DOC:39-47` 出口结构，未照搬其 `:154/:181/:187/:193` 的 `None`/`{}` 折叠缺陷（派发材料 §3.1 已指出）。
9. **`RESTORE.backup_mtime_pre` 的取值范围**：H02 追加在 `:4460` 之后、`continue`（`:4456`）之后 ⇒ 只对**实际备份成功**的件留痕；源件不存在时无此字段，按「未测」记，不写 `False` 表示未知。
10. **本稿不是独立复核件**：`review/B2B_DESIGN_REVIEW.md` / `check_b2b.py` / `STATE_MATRIX.json` / `B2B_DESIGN.md` 属 `TASK.md §4` 的其他交付物，本分工**未产出**；`## 2` 的 JSON 是给主设计稿/门禁消费的等价机器可读块，未伪造复核结论。
11. **hunk `+` 侧行号为构造结果**：由 `difflib.unified_diff` 在内存 `patched` 上实算；若实施者按 hunk 顺序套用，行号自洽（`verify` 阶段逐行回套已证）。不保证与任何**未套用其它改动**的第三方副本行号一致。
12. **只读域的既有工作树状态未归属**：实跑 `git status --short -- lead/re_line_20261105 lead/GOAL_THREE_TARGETS_20261018.md lead/PENDING_DECISIONS.md` 得 `?? lead/re_line_20261105/`、`MM lead/GOAL_THREE_TARGETS_20261018.md`、`MM lead/PENDING_DECISIONS.md`（`out/re_work`、`ra2youli` 为 CLEAN）。这三条是**本任务开工前即存在**的工作树状态（对话开头 gitStatus 快照已列 `MM lead/GOAL_THREE_TARGETS_20261018.md` / `MM lead/PENDING_DECISIONS.md`），**本次会话未对其写入一字**；其来源/归属**未验**，按「未知」记，不默认当作不存在，也不冒充本稿改过。本稿与 `out/re_work/**` 母本一个字节未改（收尾重算指纹见 §9）。

---

## 9 本次实跑命令与结果汇总

| 命令（均 `python -I -X utf8`，绝对路径） | 输出件 | exitCode | 关键输出 |
|:--|:--|--:|:--|
| `python -I -X utf8 -c "<hashlib 三文件>"` | 终端（本稿 §0 表） | 0 | 母本 `517889c6…/399508/7291` 与 `TASK.md:21` 一致 |
| `python -I -X utf8 .../_draft_semantics_check.py build` | `_draft_semantics_build_out.txt`（355 行） | 0 | `ast.parse=PASS`；`E 口径 unchanged=PASS`；`F/E 静态门禁=PASS`；`HUNK_COUNT = 9` |
| `python -I -X utf8 .../_draft_semantics_check.py matrix` | `_draft_semantics_matrix_out.txt`（20 行） | 0 | 15 行合成矩阵；`ASSERT 通过：None/{}/缺state/脏值 ⇒ unknown 且 conf!=high`；`MATRIX_ALL = PASS` |
| `python -I -X utf8 .../_draft_semantics_check.py anchors` | `_draft_semantics_anchors_out.txt`（61 行） | 0 | 逐锚点打印母本原文；16 个探针结构锚点全部 `True` |
| `python -I -X utf8 .../_draft_semantics_check.py verify` | `_draft_semantics_verify_out.txt`（15 行） | **0** | `套用结果与 build patched 逐行一致 = True`；`ast.parse(套用后文本) = PASS`；`§7 清单数据行 = 9 / hunk = 9 → 专项检查 A PASS`；`STATE_MATRIX.json 行数 = 12 / unknown->high 行数 = 0 → B PASS`；`earlyReturnsCovered = 5/5 → C PASS`；`§1 十条覆盖 = True`；`VERIFY_ALL = PASS` |
| `python -I -X utf8 .../_gen_hunks_frag.py` | `_hunks_frag.md`（9 个 diff 块） | 0 | `HUNKS 9 / FENCE_COUNT 9` |

**收尾完整性实算**：写完全部产物后重算母本 → `MOTHER_SHA256_AFTER 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 BYTES 399508`（命令 `python -I -X utf8 -c "import hashlib;d=open(<母本>,'rb').read();print(hashlib.sha256(d).hexdigest(),len(d))"`），与 §0 开工值**逐字相同** ⇒ 母本一个字节未改。只读域未触碰；未 commit / 未 push；未启真机；未写采样代码。

'''

doc = HEAD + FRAG + TAIL
p = HERE / "_draft_semantics.md"
p.write_text(doc, encoding="utf-8", newline="\n")
print("WROTE", p)
print("BYTES", len(doc.encode("utf-8")), "LINES", len(doc.splitlines()))
print("DIFF_FENCES", doc.count("```diff"), "HUNK_HEADERS", doc.count("@@ -"))
