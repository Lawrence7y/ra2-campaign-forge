# W11 任务书 · D-22 执行步：`except_post` 新鲜性缺失的完整语义核查 + 离线修复候选

> **来源**：D-22 裁决（`dwfrun-daa0cd3f`，`magpie/codex/gpt-6.1-sol$medium`）定谳 **A（先修观测）**，
> `nextSteps` 第 2、3 条明确「**不需新增用户授权**」：
> - 第 2 条：「沿 harness 调用链核查归档与文件新鲜性语义，输出**源码明确设计 / 实现缺陷 / 证据不足**三类结果及修复条件」
> - 第 3 条：「若静态证据确认缺陷，在 `D22_RULING/` 编写**独立离线文件处理候选或补丁文本**，
>   以合成文件验证源件缺失、原样遗留、内容变化及复制失败分支，记录预期与实际输出」
>
> **本任务只做这两步。不修改任何正式 harness 文件。** 零真机。

## 0. 已验证的前置事实（不要重新推翻，但可以质疑）

我（Leader）已在台账 **§595** 亲验并附行号：

1. **生成点唯一**：`out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py:4561`
   `copy_post_except_evidence()`，核心 `:4576-4581`：
   ```python
   src = carrier_dir / "except.txt"
   if not src.exists():      # ★ 只判存不存在
       return None
   blob = src.read_bytes()   # ★ 原样复制，零新鲜性校验
   dst = out_dir / f"except_post_{datetime.now()...}.txt"
   dst.write_bytes(blob)
   ```
2. **U-5 裁定后无人写载体**：`:6394-6406` 明写 `baseline_source=passive_read`、`reset_verdict=SKIPPED_U5`
   （外部裁定 V5 §6.1.1 U-5 移除 `except_reset` 的覆盖写）。
3. **判定口径本身正确**：`except_set_diff` `:672-707` 用 `collections.Counter` 多重集差。
4. **数据闭合**：59 份 `except_set_diff.json` 的 `pre_line_count` **恒为 1046（59/59）**、`new_exception_count` **全 0（59/59）**。

★ **以上四条你可以质疑。若你实测发现我写错了，直接写进回件，不要迁就。**

## 1. 四项任务

### T1 · 全链路语义核查（对应 D-22 nextSteps 第 2 条）

**目标**：把 `except.txt` 与 `except_post_*` 的**完整生命周期**讲清，输出三类判定。

必须回答（每条附 `文件:行号`）：

1. **载体 `except.txt` 从哪来**：是游戏写的、是 harness 写的、还是交接载体自带？
   查 `carrier_dir` 的定义、载体重建/交接代码（`ERRATA_CARRIER_REBUILD.md` 相关、`CARRIER_FILES` `:213-217`）。
2. **跑前基线**：`:6394-6406` 读到的 `pre_except_txt` 是**哪一刻**的内容？它有没有可能与"本趟之前那次"混淆？
3. **`copy_post_except_evidence` 的调用时机**：`:5939` 在 `finalize_trip` 的 `_except_evidence_copy()` 里，
   排在 `restore_carrier` **之前**（`:5953`）。核这个顺序对不对、有没有别的调用点。
4. **有无**任何地方**检查过新鲜性**：全文件搜 `st_mtime` / `getmtime` / `mtime` / 时间比较。
   `:4420` 有一处 `"mtime": _st.st_mtime` —— **它属于哪个函数、用来干什么、是不是新鲜性检查？**
5. **`carrier_post_state.json`**（`:4591-4596`）写了五件的跑后 size/sha256。
   ★ **有没有任何代码去比它和跑前备份？** 若没有，明写「写了但没人比」。
6. **归档语义**：`except_post_*` 之后有没有被归档/清理？谁读它？搜全仓读 `except_post` 的代码。

**输出三分类**（每项都要落到一类）：
- **源码明确设计**（注释/函数名明确表达了意图，且实现与意图一致）
- **实现缺陷**（意图与实现不符，或缺少必要条件）
- **证据不足**（源码看不出意图，需要更多信息）

★ 特别要回答：**`copy_post_except_evidence` 属于哪一类？** 它的 docstring（`:4563-4573`）说要抓「本趟跑后的原件」，
实现只判 `exists()` —— 这是「实现缺陷」还是「设计如此」？

### T2 · 新鲜性语义的判定口径设计

**目标**：给出「怎样才能判定 `except.txt` 是本趟新产生的」的**可实施判据**。

必须考虑至少这几条路，逐条给可行性与代价：

| 方案 | 判据 | 可行性 | 代价 | 误判风险 |
|---|---|---|---|---|
| A · mtime 比较 | `src.stat().st_mtime >= t_run_start` | ? | ? | ? |
| B · 跑前基线哈希 | 跑前算 `sha256(except.txt)`，跑后不同才算新 | ? | ? | ? |
| C · 跑前改名/移走 | 跑前把 `except.txt` 移走，跑后若出现即为新 | ? | ? | ? |
| D · 游戏侧保证 | 依赖游戏只在崩溃时写 | ? | ? | ? |

★ **A 方案有已知陷阱**：D-22 事实核证员已指出「mtime 不自动等于异常发生时间」。
**你要说清：文件系统 mtime 在什么情况下不可靠**（如复制保留 mtime、时钟回拨、同一 tick 多次写）。

★ **B 方案要注意**：若游戏把同一内容重写一遍（内容相同但确实是新一次崩溃），B 会判「不是新的」——
**这个误判风险要说清**。

### T3 · 离线修复候选（对应 D-22 nextSteps 第 3 条）

**目标**：写一个**独立的、不依赖正式 harness 的**小模块 + 测试，验证四个分支。

要求：
1. 模块名 `except_freshness.py`，放在 `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/`。
2. 提供一个纯函数（**不启动游戏、不读活进程、只操作临时目录里的文件**），签名大意：
   `classify_except_post(pre_snapshot, post_path, run_start_ts, policy) -> dict`
   返回至少含 `is_new` / `reason` / `evidence` 三个键。
3. **必须覆盖四个分支**（用合成文件构造，不是真跑 harness）：
   - **源件缺失**（跑前没有 `except.txt`，跑后也没有）
   - **原样遗留**（跑前有、跑后有，内容与 mtime 都未变 ⇒ 应判 `not_new`）
   - **内容变化**（跑前有、跑后内容变了 ⇒ 应判 `new`）
   - **复制失败**（`write_bytes` 抛异常 ⇒ 应判 `error` 并留痕，不是静默）
4. 写 `test_except_freshness.py`，用 `unittest` 或纯 assert，**全绿输出 `PASS=n FAIL=0 EXIT=0`**。
5. ★ **在 `W11_EXCEPT_FRESHNESS/` 内建临时目录跑，不许碰 `out/re_work/` 下任何真实目录。**

★ **T3 只产出候选与测试，不产出对 `qc151_trip.py` 的修改。**
若你要给补丁文本，只能是**建议性的 diff 片段**（放在 `candidate/PATCH_SUGGESTION.md`），
**不得实际修改 `qc151_trip.py`**（那是 D-22 nextSteps 第 5 条，需用户新授权）。

### T4 · 影响面清单

**目标**：列出**所有依赖 `except_post` 或 `new_exception_count` 的历史判断**，标出哪些要重估。

- 搜全仓 `lead/*.md`、`docs/re/*.md` 里引用 `except_post` / `new_exception_count` / `no_new_exception` 的地方。
- 逐条给：`文件:行` + 该处用它论证了什么 + 是否应降级。
- ★ 特别核 §555 的「37 个 archive 零趟游戏崩溃」与 §545 起的相关表述。

## 2. 每份回件强制头部

```
被核对象 = qc151_trip.py + 相关 harness 文件
qc151_trip.py SHA256 = <自己实算的 64 位>，字节数 = <自己实算的>，行数 = <自己实算的>
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（目标镜像，本任务不反汇编它）
回件时刻 = <实际时刻>
```

## 3. 判定档

- **CONFIRMED**：每个结论都有 `文件:行号` 或「实跑命令 + 输出」支撑。
- **PARTIAL**：部分结论只能给「证据不足」。
- **REFUTED**：发现我 §595 的前置事实有实质错误（要点名是哪一条、你的依据是什么）。

## 4. 交付物

写到 `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/`：
- `T1_SEMANTICS.md` / `T2_CRITERIA.md` / `T3_CANDIDATE.md` / `T4_IMPACT.md`
- `candidate/except_freshness.py` + `candidate/test_except_freshness.py` + `candidate/PATCH_SUGGESTION.md`
- `reviews/T*_review.md` —— 每项一道独立复核
- `W11_EXCEPT_FRESHNESS.md` —— 汇总（`## 0 总判` / `## 1 SHA256 绑定` / `## 2 T1 语义核查` / `## 3 T2 判定口径` / `## 4 T3 离线候选` / `## 5 T4 影响面` / `## 6 必须改项` / `## 7 诚实账`）
- `_w11_*.py` + `_w11_*_out.txt` —— 只读探针

## 5. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**。
- **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。**E3 维持暂停（D-13）**。
- ★★ **不许修改 `qc151_trip.py` 或任何 `out/re_work/` 下的文件**。
  **唯一写域 = `W11_EXCEPT_FRESHNESS/`**（含其 `candidate/` 子目录里新建的文件）。
- **只读**：`ra2youli\`、`out\re_work\...`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `W1_*`…`W10_*` 既有件、`D*_RULING\` —— **一律不得修改**。
- Python 一律 `python -I -X utf8`，绝对路径。**不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- ★ **否定性/存在性事实先用文件系统命令核**（`find`/`ls`/`wc`/`sha256sum`），不要上全仓 Python 遍历。
- ★ **仓内有非 UTF-8 文件名**：`subprocess(text=True)` 会崩，用 `os.walk` + `open(...,'rb')`。
- ★ **并行度**：本任务最多同时 2 个子代理。
- ★ **测试必须在自己的临时目录里跑**，不许在真实趟目录产生任何文件。
