# _m_MATRIX_DIFF_20261108.md · 甲↔乙逐项差异核证（矩阵核证员 GLM）

**性质**：事实核证，不代签发人决断甲/乙，不签 APPROVE_SCOPE，不放行 N-5（NEXT_STEPS_20261106.md:47「不由测试者临时决定」）。
**日期**：2026-11-08　**方法**：全部条目出自本会话实读「文件:行」或本会话实跑命令（`python -I -X utf8` + 绝对路径 + `hashlib`）。零真机、零采样代码、不 commit / 不 push、不改既有件；唯一写域 = `lead/matrix_binding_20261108/`。

## 0 被核对象指纹（本会话实算，`_m_rebuild_out.txt:3-13`）

| 对象 | 路径 | SHA256 | 字节数 |
|:--|:--|:--|--:|
| **甲** B2 设计 | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11,638 |
| **乙** B2b 设计 | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66,735 |
| 乙状态矩阵 | `lead/b2b_design_20261106/STATE_MATRIX.json` | `1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016` | 3,558 |
| 乙预审 | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` | `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` | 20,615 |
| 甲预审（NO） | `lead/b2_preaudit_20261106/B2_PREAUDIT.md` | `a108a6e45f42c449db5d228abc469e5c17d40db0b04f15aa32105adff8905449` | 28,410 |
| R3 判定书 | `lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md` | `96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea` | 24,661 |
| N-4 规格 | `lead/bexec_n4_20261108/B_EXECUTION_SPEC.md` | `be73333541ddef9a9782aff2ae2f98e657d50d254c50dad5acdf8052ebc25358` | 32,183 |
| N-4 原文 | `lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md` | `c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c` | 27,225 |
| 母本 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399,508 |
| 候选（LF） | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2` | 412,759 |
| 候选 diff | `lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff` | `72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9` | 18,454 |

## 1 分支取值差异（4 处 —— 承接 B_EXECUTION_SPEC.md §3.4 :119-128 已登记项，本会话对原始出处逐项实读复核）

| # | 分支 | 甲值 | 乙值 | 甲出处 | 乙出处 |
|:--|:--|:--|:--|:--|:--|
| 1 | `absent_both` 的 confidence | `n/a` | **`low`**（且 is_new=False，「文件未出现」不能证无崩溃） | `B2_FIX_DESIGN.md:137-138`：`"high" if _pre_exists else "n/a"`（absent_both 分支取 n/a） | `STATE_MATRIX.json:7`（verdict=absent_both, confidence=low）+ `B2B_DESIGN.md:153` + 硬规 `:167`（low 给 absent_both） |
| 2 | `vanished` 的 confidence | `high` | **`none`**（不给 high、is_new=null、须人工复核） | `B2_FIX_DESIGN.md:137-138`：vanished 分支取 `high` | `STATE_MATRIX.json:15`（vanished, none）+ `B2B_DESIGN.md:161` + 硬规 `:168`（vanished 列入所有不可判出口） |
| 3 | 空快照 `{}`（≡exists=False） | 折叠为「跑前无件」：跑后有件 → `new_first_appearance/high`；跑后无件 → `absent_both/n/a` | **`unknown/none`**、is_new=None、「未知 ≠ 不存在」，不作本趟新出现归因 | `B2_FIX_DESIGN.md:133-134`：`_pre = dict(pre_snapshot or {})`、`_pre_exists = bool(_pre.get("exists"))` ⇒ `{}` → pre_exists=False；`N-4 原文 NEXT_STEPS_20261106.md:47`：「空快照 {} 与显式 exists=False 等价」 | `STATE_MATRIX.json:2`（pre=None/{}/缺state/脏值 → unknown/none）+ `B2B_DESIGN.md:148`；归一实现候选 `:4634-4651`（B_EXECUTION_SPEC.md:132 转引，R3:44 穷举 36 组 unknown→high 泄漏=0） |
| 4 | `mtime_pre` 缺失 | **无独立分支**：`:150` elif 守卫 `_pre_mtime is not None` 直接跳过 mtime 比较，sha 同即落 `leftover_unchanged/high` | **`leftover_unchanged/medium`**（A 旁证不可用、盲区如实标注、不虚报 high） | `B2_FIX_DESIGN.md:150-154`（elif 守卫 + else 落 leftover_unchanged/high） | `STATE_MATRIX.json:9`（mtime 侧缺失 → leftover_unchanged/medium）+ `B2B_DESIGN.md:155` |

复核说明：以上 4 项与 `B_EXECUTION_SPEC.md:123-126`（§3.4 前 4 行）登记一致；差异本身由本会话对甲 `:133-154` 实码与乙 `STATE_MATRIX.json` 全文实读独立得出，非转抄。

## 2 值域差异

| 维度 | 甲值域 | 乙值域 | 出处 |
|:--|:--|:--|:--|
| confidence | `{n/a, high, low, medium}` | `{high, medium, low, none}`，`none`=不可判、显式区别于 low | 甲：`B2_FIX_DESIGN.md:137-154` 实码出现的全部字面量；乙：`B2B_DESIGN.md:142`「`none` = **不可判**，不是 `low`」+ `:579`（FRESHNESS_CONFIDENCES）+ 本会话实跑 `_m_rebuild_out.txt:31`（14 行 JSON confidence 实测值域 = ['high','low','medium','none']） |
| verdict | 6 值：absent_both / vanished / new_first_appearance / new_write / rewritten_same_content / leftover_unchanged | **9 值** = 甲 6 值 + `unknown` + `error_pre_snapshot` + `post_read_error` | 甲：`B2_FIX_DESIGN.md:137-154`；乙：`B2B_DESIGN.md:578`（FRESHNESS_VERDICTS 9 值）+ 本会话实跑 `_m_rebuild_out.txt:32` |
| 跑前快照判别 | 无 `state` 维度：`exists` 布尔唯一判别（`_pre.get("exists")`） | `preState` 4 态：`unknown / absent_confirmed / present / error`，`state` 为唯一判别口、`exists` 不得反推 | 甲：`B2_FIX_DESIGN.md:134`；乙：`B2B_DESIGN.md:142`、`:580`、`:95`（N3 根治） |

## 3 乙新增出口与字段（甲不存在）

**乙新增 verdict 出口 3 个**（甲矩阵无对应分支）：

| 出口 | 触发 | 出处 |
|:--|:--|:--|
| `unknown` | pre=None / `{}` / 缺 state / 脏值 / 显式 unknown（跑前快照未采集或未完成） | `STATE_MATRIX.json:2-3`；`B2B_DESIGN.md:148-149` |
| `error_pre_snapshot` | 跑前采集抛异常（snap.error 非空）；跑前在但缺 pre.sha256 | `STATE_MATRIX.json:4,13`（json 行 3、12）；`B2B_DESIGN.md:150,159` |
| `post_read_error` | 跑后 read_bytes/stat/write_bytes 抛异常；跑后缺 post.sha256 | `STATE_MATRIX.json:5,14`（json 行 4、13）；`B2B_DESIGN.md:151,160` |

**乙新增字段（输出超集）**：甲的 F 输出只有两值——`evidence_freshness` 记录（value=verdict、note 内含置信，`B2_FIX_DESIGN.md:160-161`）+ info 加 4 键（点位 `:4583-4586`，甲文只写「加 4 个键」未给键名，`:114`/`:186`；甲预审实证该 4 键无 diff：`B2_PREAUDIT.md:83`「§2 :186 声称的 info +4 键无 diff」）。乙的 F 输出 7 键全路径落盘：`freshness_verdict / freshness_confidence / freshness_is_new / freshness_note` + `pre_snapshot_state / usable_as_crash_evidence / captured_at_iso`（`R3:63`；契约表 `B2B_DESIGN.md:574-619`），另有 H08 单独落 `captured_at_iso_pre`（`B2B_DESIGN.md:669`）。相对甲新增：**is_new、note、usable_as_crash_evidence（恒 False，`:142`/`:677` 口径）、pre_snapshot_state、captured_at_iso、captured_at_iso_pre**。

## 4 改动面差异

| 项 | 甲：A—D 四处 | 乙：H01—H09 九 hunk |
|:--|:--|:--|
| 清单出处 | `B2_FIX_DESIGN.md:113-116`（A—D 表）+ `:118`「四处改动是可论证的最小集」+ `:181-190` 明细 8 行 + `:192`「净增 ≈31 行，删除 0 行」 | `B2B_DESIGN.md:656-670`（§7 表恰 9 行）+ `:202`「共 9 个 @@ 头」；本会话实跑：设计 ```diff 块恰 9、CANDIDATE_LF.diff @@ 恰 9（`_m_rebuild_out.txt:19,23`） |
| 具体锚点 | A `backup_carrier` `:4457-4461` 补 exists/mtime_pre/captured_at_epoch（改 bak[name] 三键契约，`:81-84` diff）；B `copy_post_except_evidence` `:4561-4562` 签名 + `:4573` 前插判定 + `:4583-4586` info；C `finalize_trip` 签名 `:5900-5909`；D `_except_evidence_copy` `:5939` + `finalize_trip` 调用点 `:7117-7125` + main 基线 `:6387` 后 | H01 `:214`后插 5 常量；H02 `:4460`后加 RESTORE.backup_mtime_pre 留痕（**不改** bak[name] 三键，`:663`）；H03 `:4561`前插 make_pre_freshness_snapshot + classify_except_freshness 并改 def 签名；H04 `:4574-4599` 函数体重写（三出口落盘、info 扩 12 键）；H05 `:5909` 加形参；H06 `:5939` 唯一调用点关键字传参；H07 `:6296`后预初始化 None；H08 `:6388`后构造快照+落 captured_at_iso_pre；H09 `:7125`后传入 finalize_trip（`B2B_DESIGN.md:662-670`） |
| 规模 | 净增 ≈31 行删 0（甲自算 `:192`；甲预审指其与 5 行 '-' 删除行对不上，`B2_PREAUDIT.md:83`） | +255/-13 行（R3:85 实测；母本 7292→候选 7534 行，本会话实跑 `_m_rebuild_out.txt:17`） |
| 结构性区别 | 判定内联在 `copy_post_except_evidence` 内（修正 5，`:127-165`）；无预初始化（早退路径作用域风险，甲预审 E1=NOT_FIXED，`B2_PREAUDIT.md:20,28-30`）；无常量命名空间 | 判定抽为纯函数 `classify_except_freshness` + 采集函数 `make_pre_freshness_snapshot`；H07 预初始化先于 `:6313 try`；H01 注入 FRESHNESS 5 常量单一真源（`B2B_DESIGN.md:61,95,662`） |
| 对应关系（事实映射，非等价声明） | 甲A ≈ 乙H02（语义不同：甲改 bak 三键、乙不动 bak 只加留痕）；甲B ≈ 乙H03+H04；甲C ≈ 乙H05；甲D ≈ 乙H06+H08；乙H01/H07/H09 在甲中无对应物（乙 :124「一个 hunk 都不多、一个都不漏」为乙内部口径） | 同左 |

## 5 已登记差异的承接声明

本表第 1 节 4 项 = `B_EXECUTION_SPEC.md:119-128`（§3.4）已登记的 4 处分支取值差 + 值域差 + 字段差；第 2–4 节值域/出口/字段/改动面为按本任务要求在 §3.4 之外的扩充核证。所有甲侧行号引用（`:133-154` 判定矩阵、`:113-116` 改动面、`:198` 设计声明）均出自本会话对 `B2_FIX_DESIGN.md` 全文实读（237 行全文已读）。

—— 本件只陈述差异事实；绑定选择见 `_m_DECISION_POINTS_20261108.md`，本工作流不代决。
