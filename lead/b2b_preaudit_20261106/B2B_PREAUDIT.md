# B2b 独立设计预审判定书

### 三件基准实算指纹

| 对象 | 相对路径 | SHA256 (64 hex) | 字节数 (Bytes) | 状态 |
|:--|:--|:--|--:|:--|
| **正式母本** | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 | PASS (零漂移，一个字节未动) |
| **被审设计 B2b** | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66735 | 独立预审目标版本 |
| **被否旧设计 B2** | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11638 | 历史被否参照件 |

### 独立预审结论

verdict: YES

> **★ 效力边界说明**：
> `verdict: YES` 的准确含义 = 可以拿去编写候选；不等于可以应用到母本。
> 本预审仅证明设计稿在静态语法、hunk 覆盖、行号偏移、变量作用域、早退路径、状态矩阵与 F/E 隔离层面符合工程规范，具备起草候选补丁的前提条件；**绝对禁止将本设计直接应用到母本**，后续仍须严格执行候选编写、独立代码复审、隔离副本集成验证与真机验收流程。

---

## 九个 Hunk 逐项核验

#### H1
- **判定**：OK
- **证据**：母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:212-217` 对齐设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:205-227`（`@@ -212,6 +212,21 @@`）
- **一句话后果**：母本上下文逐行完全匹配；在模块顶层安全注入 5 个 F 命名空间单一真源常量，语法正确且全局作用域无阻碍，下游 H04 与 H08 可正常引用。

#### H2
- **判定**：OK
- **证据**：设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:230-241`（`@@ -4458,6 +4473,10 @@`）对齐母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:4458-4463`
- **一句话后果**：`-` 侧 6 行上下文与母本逐字符完全匹配；`+` 侧在 `backup_carrier` 内正确记录 `RESTORE.backup_mtime_pre` 留痕且保持 `bak[name]` 三键契约，语法与作用域均成立。

#### H3
- **判定**：OK
- **证据**：设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:244-377`（`@@ -4558,8 +4577,131 @@`）与母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:4558-4565` 逐行比对 8 行完全一致；依赖符号在母本作用域内均成立（`hashlib/time/Path` 见 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:167-175`，`sha256_file` 见 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:416`，`now_iso` 见 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:432`）
- **一句话后果**：成功前置定义跑前快照采集函数 `make_pre_freshness_snapshot` 与新鲜性判定纯函数 `classify_except_freshness`，并安全扩展 `copy_post_except_evidence` 签名支持 `pre_freshness_snapshot` 入参，默认值 `None` 保持向下兼容。

#### H4
- **判定**：OK
- **证据**：母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:4572-4591` 对齐设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:380-495`（`@@ -4572,20 +4714,105 @@`）
- **一句话后果**：重写 `copy_post_except_evidence` 函数体实现早退、正常、异常三出口全量落盘 7 个 FRESHNESS 字段与 12 键 info，三态严格可分且 `unknown` 置信度恒为 `none`，语法与作用域均成立。

#### H5
- **判定**：OK
- **证据**：设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:498-508`（`@@ -5906,7 +6133,8 @@`）对齐母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:5906-5912`
- **一句话后果**：`-` 侧 7 行上下文与母本完全匹配；`+` 侧在 `finalize_trip` 末尾追加 `pre_freshness_snapshot: dict | None = None` 形参，语法正确且向后兼容既有调用点。

#### H6
- **判定**：OK
- **证据**：设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:511-521`（`@@ -5936,7 +6164,8 @@`）覆盖母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:5936-5942`（`-` 侧上下文逐行逐字匹配，精确覆盖 `:5939` 唯一调用点）
- **一句话后果**：彻底修复旧 B2 的 N5 死因：母本 `:5939` 唯一调用点显式传入 `pre_freshness_snapshot=pre_freshness_snapshot`，作用域链与形参完整闭合，杜绝调用点丢失传参恒走默认降级。

#### H7
- **判定**：OK
- **证据**：设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:524-534`（`@@ -6294,6 +6523,9 @@`）与母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6294-6299` 逐行一致；外层 `try:` 位于母本 `:6313`，预初始化 `_pre_freshness_snapshot = None` 在 `:6296` 后插入（确在 `try:` 之前）；5 个早退点 `:6340`、`:6349`、`:6361`、`:6374`、`:6377` 均在快照构造 `:6388` 之前
- **一句话后果**：预初始化位于 `main` 的 `try:`（`:6313`）之前，使 5 个早退（`:6340`、`:6349`、`:6361`、`:6374`、`:6377`）与前置异常路径均能安全绑定 `_pre_freshness_snapshot=None` 传给 `finally`（`:7122`）中的 `finalize_trip`，根治 E1 作用域断裂与未绑定异常风险。

#### H8
- **判定**：OK
- **证据**：母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6386-6391` 逐行匹配设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:537-553`（`@@ -6386,6 +6618,15 @@`）；快照构造位于 `:6388` 后（`:6387` 备份之后、`:6456` launch 之前）
- **一句话后果**：在载体备份完成与游戏进程启动之间准确捕获跑前 `except.txt` 快照并记录 `captured_at_iso_pre`，与 H7 `try` 前预初始化完整闭合，彻底消除作用域未绑定风险。

#### H9
- **判定**：OK
- **证据**：母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:7122-7128` 与设计稿 `lead/b2b_design_20261106/B2B_DESIGN.md:556-566`（`@@ -7122,7 +7363,8 @@`）逐行比对完全匹配
- **一句话后果**：在 `main` 的 `finally` 中将已绑定的跑前快照 `_pre_freshness_snapshot` 传入 `finalize_trip`，打通主流程至收尾函数的实参传递链，闭合 E1 作用域。

---

## 行号偏移与拼接

依据项目铁律（零真机、零采样、母本只读、唯一写域 `lead/b2b_preaudit_20261106/`、Python 隔离模式运行），已完成独立验证脚本 `lead/b2b_preaudit_20261106/_b2b_pa_probe.py` 编写并实跑，完整标准输出记录于 `lead/b2b_preaudit_20261106/_b2b_pa_probe_out.txt`。

实跑命令：
`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b2b_preaudit_20261106/_b2b_pa_probe.py`

### 1. 母本上下文匹配核验
全部 9 个 hunk 的 `-` 侧原文在母本中均为 **100% 逐行逐字匹配**，且在母本全局均 **唯一出现 1 次**（零多重匹配、零匹配缺失）：
- Hunk #01 (`@@ -212,6 +212,21 @@`，母本 `L212..L217`，共 6 行)：PASS
- Hunk #02 (`@@ -4458,6 +4473,10 @@`，母本 `L4458..L4463`，共 6 行)：PASS
- Hunk #03 (`@@ -4558,8 +4577,131 @@`，母本 `L4558..L4565`，共 8 行)：PASS
- Hunk #04 (`@@ -4572,20 +4714,105 @@`，母本 `L4572..L4591`，共 20 行)：PASS
- Hunk #05 (`@@ -5906,7 +6133,8 @@`，母本 `L5906..L5912`，共 7 行)：PASS
- Hunk #06 (`@@ -5936,7 +6164,8 @@`，母本 `L5936..L5942`，共 7 行)：PASS
- Hunk #07 (`@@ -6294,6 +6523,9 @@`，母本 `L6294..L6299`，共 6 行)：PASS
- Hunk #08 (`@@ -6386,6 +6618,15 @@`，母本 `L6386..L6391`，共 6 行)：PASS
- Hunk #09 (`@@ -7122,7 +7363,8 @@`，母本 `L7122..L7128`，共 7 行)：PASS

### 2. 内存拼接与 AST 语法解析
探针在内存中以只读副本依次应用 9 个 hunk 的 `+` 侧改动（母本物理文件一个字节未动）：
- 母本原始行数：7,291 行
- 内存拼接后总行数：7,533 行
- 净增行数：242 行（各 hunk Delta 累加和 `15 + 4 + 123 + 85 + 1 + 1 + 3 + 9 + 1 = 242` 精确一致）
- `ast.parse` 结果：**SUCCESS (0 syntax errors, 拼接文本完全符合 Python 语法，语法正确)**。AST 语法树中 171 个函数定义完好，`make_pre_freshness_snapshot`、`classify_except_freshness`、`copy_post_except_evidence`、`finalize_trip` 及 `main` 签名与形参全部闭合。

### 3. 行号冲突与累积偏移核验
- **母本 `-` 侧区间互不重叠**：9 个区间严格升序，区间之间保持正向安全间距（6..4240 行），无交叉。
- **设计稿 `+` 侧区间互不重叠**：声明区间与内存实际拼接区间完全一致，区间之间保持正向安全间距。
- **累积偏移校验（Cumulative Offset Drift Check）**：
  H03 引入净增 123 行（总长 131 行）、H04 引入净增 85 行，后续所有 hunk 声明的 `+<start>,<count>` 均已将前置所有 hunk 引入的 Delta 累加计算在内：
  - H01: 前置 Delta=0 $\rightarrow$ 计算起始 L212 vs 声明 L212（MATCH）
  - H02: 前置 Delta=+15 $\rightarrow$ 计算起始 L4473 vs 声明 L4473（MATCH）
  - H03: 前置 Delta=+19 $\rightarrow$ 计算起始 L4577 vs 声明 L4577（MATCH）
  - H04: 前置 Delta=+142 $\rightarrow$ 计算起始 L4714 vs 声明 L4714（MATCH）
  - H05: 前置 Delta=+227 $\rightarrow$ 计算起始 L6133 vs 声明 L6133（MATCH）
  - H06: 前置 Delta=+228 $\rightarrow$ 计算起始 L6164 vs 声明 L6164（MATCH）
  - H07: 前置 Delta=+229 $\rightarrow$ 计算起始 L6523 vs 声明 L6523（MATCH）
  - H08: 前置 Delta=+232 $\rightarrow$ 计算起始 L6618 vs 声明 L6618（MATCH）
  - H09: 前置 Delta=+241 $\rightarrow$ 计算起始 L7363 vs 声明 L7363（MATCH）
  全量 0 漂移，无任何行号冲突。

---

## 五个早退路径

在母本 `main` 函数内、`:6387`（`bak = backup_carrier(...)`）之前共有 5 个 `return` 早退点（`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6340 / :6349 / :6361 / :6374 / :6377`）。

根据 D-25 裁决书更正：Python 中未赋值裸名访问会抛 `NameError`；只有在作用域内存在局部赋值语句但执行路径绕过了赋值时才抛 `UnboundLocalError`。
B2b 设计在 H07 中将 `_pre_freshness_snapshot = None` 显式放置于 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6296`（在 `try:` `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6313` 之前）。因此在进入 `try` 块发生任何早退或前置异常时，变量已被安全绑定。

| 路径标识 | 触发位置与原因 | 快照变量值 | 异常抛出情况 | 判定结论 |
|:--|:--|:--|:--|:--:|
| `early_return@6340` | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6340`（所有权不成立早退 `EXIT_CARRIER_NOT_OWNED`） | `None` | **无异常**（H07 在 `:6296` 预初始化为 `None`，进入 `finally:7122` 安全传参；`finalize_trip` 归一为 `unknown`/`none` 留痕） | **SAFE** |
| `early_return@6349` | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6349`（目标地图缺失早退 `EXIT_TARGET_MISSING`） | `None` | **无异常**（已在 `try` 前完成绑定，进入 `finally` 无 `NameError`/`UnboundLocalError`） | **SAFE** |
| `early_return@6361` | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6361`（目标地图哈希不符 `EXIT_TARGET_MISMATCH`） | `None` | **无异常**（已在 `try` 前完成绑定，进入 `finally` 无 `NameError`/`UnboundLocalError`） | **SAFE** |
| `early_return@6374` | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6374`（两控跑前 SHA 不符 `EXIT_PRECHECK_SHA_MISMATCH`） | `None` | **无异常**（已在 `try` 前完成绑定，进入 `finally` 无 `NameError`/`UnboundLocalError`） | **SAFE** |
| `early_return@6377` | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6377`（两控签名校验失败 `EXIT_PRECHECK_SIG_MISMATCH`） | `None` | **无异常**（已在 `try` 前完成绑定，进入 `finally` 无 `NameError`/`UnboundLocalError`） | **SAFE** |
| `normal_path@7029` | 游戏正常运行并退场（通过 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:6388` 并在 `:7029` 正常结束） | `dict`（含 `captured_at_iso`、`state`、`sha256` 等规范字段） | **无异常**（H08 采集快照并落盘 `captured_at_iso_pre`，经 H09 传入 `finalize_trip`，完整记录 12 键 info） | **SAFE** |

---

## 状态矩阵

对机器可读矩阵 `lead/b2b_design_20261106/STATE_MATRIX.json`（共 14 条记录）及 `lead/b2b_design_20261106/B2B_DESIGN.md:148-161` §2 表格进行逐条对账核验：

| 序号 | 状态标识 (`state`) | 前置状态 (`preState`) | 条件判定逻辑 | 判定结果 (`verdict`) | 置信度 (`confidence`) | 崩溃证据 (`usableAsCrashEvidence`) | 判定 |
|:--:|:--|:--|:--|:--|:--:|:--:|:--:|
| 1 | `unknown` | `unknown` | `pre=None / {} / 缺 state / 脏值`（未采集或采集未完成），跑后任意 | `unknown` | `none` | `false` | **PASS** |
| 2 | `unknown` | `unknown` | `pre.state` 显式 `unknown` + 跑后无件；未知不得默认等于不存在 | `unknown` | `none` | `false` | **PASS** |
| 3 | `error` | `error` | 跑前采集抛异常（`snap.error` 非空）$\Rightarrow$ 独立 error 出口，不降级、不静默 | `error_pre_snapshot` | `none` | `false` | **PASS** |
| 4 | `post_read_error` | `present` | 跑后 `read_bytes/stat` 抛异常（`post.read_error` 非空）$\Rightarrow$ 独立 error 出口 | `post_read_error` | `none` | `false` | **PASS** |
| 5 | `absent_confirmed` | `absent_confirmed` | 跑前确认无件 + 跑后在场（存在性硬证）$\Rightarrow$ 本趟新出现 | `new_first_appearance` | `high` | `false` | **PASS** |
| 6 | `absent_both` | `absent_confirmed` | 跑前确认无件 + 跑后无件 $\Rightarrow$ 未见新出现，但不能证无崩溃 | `absent_both` | `low` | `false` | **PASS** |
| 7 | `leftover_unchanged` | `present` | 跑前在 + 跑后在 + SHA 未变 + mtime 未变（双侧齐全） | `leftover_unchanged` | `high` | `false` | **PASS** |
| 8 | `leftover_unchanged` | `present` | 跑前在 + 跑后在 + SHA 未变 + mtime 单侧或双侧缺失 $\Rightarrow$ 旁证缺失如实降级 | `leftover_unchanged` | `medium` | `false` | **PASS** |
| 9 | `new_write` | `present` | 跑前在 + 跑后在 + SHA 改变 $\Rightarrow$ 本趟发生写入 | `new_write` | `high` | `false` | **PASS** |
| 10 | `rewritten_same_content` | `present` | 跑前在 + 跑后在 + SHA 相同 + mtime 变大 $\Rightarrow$ 同内容重写（F 旁证补 B 盲区） | `rewritten_same_content` | `medium` | `false` | **PASS** |
| 11 | `rewritten_same_content` | `present` | 跑前在 + 跑后在 + SHA 相同 + mtime 回拨 $\Rightarrow$ 时钟回拨/utime，须人工复核 | `rewritten_same_content` | `low` | `false` | **PASS** |
| 12 | `missing_sha` | `present` | 跑前在 + 跑后在 + 缺 `pre.sha256`（B 主判据不可用）$\Rightarrow$ 独立 error 出口 | `error_pre_snapshot` | `none` | `false` | **PASS** |
| 13 | `missing_sha` | `present` | 跑前在 + 跑后在 + 缺 `post.sha256`（无法比对）$\Rightarrow$ 独立 error 出口 | `post_read_error` | `none` | `false` | **PASS** |
| 14 | `vanished` | `present` | 跑前在 + 跑后无件（被删/改名/复制链中断）$\Rightarrow$ 异常态旗标，须人工复核 | `vanished` | `none` | `false` | **PASS** |

### 核心核验项总结：
1. **`unknown` 的置信度**：第 1 条与第 2 条中，`confidence` 严格标注为 `none`，绝无映射为 `high`。在代码实现（`lead/b2b_design_20261106/B2B_DESIGN.md:316-320`）中，`st == "unknown"` 直接直出 `_finish("unknown", "none", None, ...)`。
2. **指定状态全覆盖**：要求的全部 7 种指定状态（`absent_confirmed` / `absent_both` / `leftover_unchanged` / `new_write` / `rewritten_same_content` / `missing_sha` / `vanished`）全部齐备且场景细分完备。
3. **`usableAsCrashEvidence` 属性**：14 条记录中**全部 100% 严格为布尔值 `false`**。代码实现（`lead/b2b_design_20261106/B2B_DESIGN.md:299`）中硬编码 `"usable_as_crash_evidence": False`，符合母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:677` 原文「不得用 sha 变化判 crash」。
4. **杜绝「未知被当作不存在」路径**：
   - 入参若为 `None`、`{}`、缺乏 `state` 键或脏值，强制归一为 `st = "unknown"`（`lead/b2b_design_20261106/B2B_DESIGN.md:304-307`）；
   - `if st == "unknown":` 位于 `if not post_exists:` 之前优先返回，即使跑后文件不存在也绝不跌入 `absent_both`；
   - 彻底根治了旧 B2 中因 `{}` 或无 `state` 键伪折叠为不存在的缺陷。
5. **设计主稿与 JSON 一致性**：`lead/b2b_design_20261106/B2B_DESIGN.md:148-161` §2 表格与 `STATE_MATRIX.json` 14 条记录逐行一一对应，无任何语义或字段冲突。

---

## F/E 分离

母本 `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:672-708` 为 `except_set_diff` 函数，母本 `:677` 明确规定「`★ 不得用 sha 变化判 crash（★ 游戏自身会重写该文件）`」，整趟退出码在母本 `:5984-5990` 处依据 `no_new_exception` 进行裁定。

核验 B2b 设计稿「`## 6 F/E 分离的实现级约束`」（`lead/b2b_design_20261106/B2B_DESIGN.md:626-654`），确认具备以下硬性约束与可验证检查点：

1. **字段命名隔离**：
   H01 定义 `FRESHNESS_GROUP = "FRESHNESS"` 常量。H04 的 `_emit_f` 仅向该组写入字段（包括 `freshness_verdict`、`freshness_confidence`、`freshness_is_new`、`freshness_usable_as_crash_evidence` 等）。E 口径严格保留在 `EXCEPT` 组，互不重叠。
2. **group 级别物理隔离**：
   F 字段全量走 `rec.add(FRESHNESS_GROUP, ...)`。`copy_post_except_evidence` 返回的 `info` 字典写入 `EXCEPT.evidence_copy` 仅作为元信息扩展，绝不注入任何 E 口径判定键。
3. **退出码判据隔离（零侵入）**：
   - 9 个 hunk 的 `-` 侧区间（`212-217` / `4458-4463` / `4558-4565` / `4572-4591` / `5906-5912` / `5936-5942` / `6294-6299` / `6386-6391` / `7122-7128`）完全避开母本 `:5984-5990` 判据块；
   - F 区域代码（`make_pre_freshness_snapshot` 至 `copy_post_except_evidence`）中，严禁出现 `note_cleanup_failure`、`no_new_exception`、`EXIT_`、`except_set_diff` 等退出码影响符号；实测 255 条 `+` 行中禁词出现次数为 0。
4. **F 结论恒不可作崩溃证据**：
   `classify_except_freshness` 中的 `_finish` 恒定输出 `"usable_as_crash_evidence": False`，杜绝任何外部逻辑通过 F 结论倒推进程崩溃。
5. **无新非标准依赖与零采样**：
   仅使用 Python 标准库（`hashlib`、`time`、`datetime`、`Path`、`json`、`traceback`），完全遵守铁律 2 零采样代码要求。

上述约束已由 `_draft_semantics_check.py` 脚本机械验证通过（`build`、`verify`、`matrix` 均 exitCode 0）。

---

## 未验

严格遵守铁律 7「拿不到写未验，不许补造」，以下范围明确属于未验事项，如实登记入账：

1. **零真机未验运行期退出码**：依据铁律 1（零真机），预审阶段严禁启动 `gamemd.exe` / `ra2loader.exe` / `YURI.exe`，母本 `qc151_trip.py` 未在真机进程环境中实跑。因此「游戏进程崩溃时 F 字段真实落盘数据与 E 集合差退出码的解耦运行表现」属于未验。
2. **文件系统竞争与并发未验**：操作系统层面的 `Path.stat()`、`read_bytes()` 与游戏进程写 `except.txt` 的微秒级文件锁冲突、I/O 竞争或缓存延迟未验。
3. **候选补丁物理生成未验**：本预审仅针对设计文档 `lead/b2b_design_20261106/B2B_DESIGN.md` 进行静态与内存 AST 比对，尚未实际生成 candidate 补丁文件。
4. **母本施用及回归未验**：依据铁律 4，母本 `qc151_trip.py` 一个字节未动。候选补丁在隔离副本环境的打补丁实测、回退演练以及各历史趟件回放未验。
5. **非 Windows 环境跨平台行为未验**：仅在当前 Windows 10 x64 + Python 3.12 环境下完成 AST 解析与静态分析，其它解释器平台行为未验。
