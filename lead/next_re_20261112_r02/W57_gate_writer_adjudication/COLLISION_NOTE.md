# W57 — COLLISION_NOTE.md（并发执行者共写同一目录，验收前必读）

`[本次实测]` 2026-11-13T15:08Z（本地 23:08）由本实例（接到本卡的 `Hy4`，`STARTED.txt` = `2026-11-13T14:31:50Z`）在最终校验时发现。

## 事实

目录 `W57_gate_writer_adjudication\` 内存在**另一个执行者**的产物，其自述为：

```
STARTED_W57B.txt:  W57b retry / model: Hy4 / started_iso: 2026-11-13T22:50:42.8757580+08:00
                   note: W57 re-dispatch; prior instance froze silent after 22:32 with zero output.
```

即：Lead 在 22:50（本地）把**同一张 W57 卡**重新派发给第二个 `Hy4` 实例，而本实例仍在运行；两个实例写入了**同一个目录**。共享文件 `HEARTBEAT.txt` 中可看到两套时间戳交错（本实例为纯 ISO UTC 行；W57b 为 `+08:00 | stage: ...` 行）。

## 文件归属（Lead 验收时按此区分）

**本实例（W57 / `STARTED.txt` 14:31:50Z）产物：**
- `STARTED.txt`、`HEARTBEAT.txt`（共享，含两套行）
- `GATE_WRITER_SCAN.md`、`UNKNOWNS.md`、`DISAGREE.md`、`COLLISION_NOTE.md`
- `EVIDENCE\w57_scan.py`（`env|classify|regbase`）、`EVIDENCE\w57_targeted.py`
- `EVIDENCE\w57_env_stdout.txt` / `w57_classify_stdout.txt` / `w57_regbase_stdout.txt` / `w57_targeted_stdout.txt`（各带 `_stderr.txt`、`_exitcode.txt`）
- `EVIDENCE\w57_candidates_raw.tsv`（773 个原始候选）
- `EVIDENCE\regbase_abs_page_writes.tsv`、`regbase_forward_tracking.tsv`、`regbase_page_disp_filter.tsv`、`regbase_string_sites.tsv`、`regbase_base_loads.tsv`
- `EVIDENCE\w57_targeted_regions.tsv`、`w57_targeted_required_base.tsv`
- **本实例的 740 行逐条分类表**：`EVIDENCE\w57_hy4_candidates_classified_740.tsv`
  （= W57b 备份出来的 `EVIDENCE\w57_prior_classified.tsv`，741 行含表头；W57b 的 `w57b_layer1_stdout.txt` 明确记录 `backed up prior table -> ...w57_prior_classified.tsv`）

**另一实例（W57b / `STARTED_W57B.txt` 22:50:42+08:00）产物（本实例未修改、未删除）：**
- `STARTED_W57B.txt`、`baserel_writes.tsv`（根目录）
- `EVIDENCE\w57b_*.py` / `w57b_*.stdout.txt` / `*.stderr.txt` / `*.exitcode.txt` / `w57b_*.tsv`
- `EVIDENCE\w57_prior_*`（W57b 对本实例 env/classify/regbase stdout 的备份副本）
- **根目录 `candidates_classified.tsv`**：现为 W57b 的 **773 行**表（含 `.text 740 + .rdata 14 + .data 19`）。它覆盖了本实例原先写入的同名 740 行表。

## 对结论的影响：无（且构成独立复核）

`[本次实测]` W57b 的 `EVIDENCE\w57b_layer1_stdout.txt` 记录：

```
[L1] wrote ... candidates_classified.tsv : 773 rows
[L1] category counts : {'false-positive': 99, 'immediate': 5, 'write': 215, 'read': 380, 'address-taken': 74}
[L1] WRITE rows covering GATE_VA 0xA8F7AD : 0
```

本实例（`w57_classify_stdout.txt`）对 740 个 `.text` 候选：`read 379 / write 211 / address-taken 74 / false-positive 72 / immediate 4`，`gate_write != no` 仅 2 行（`unknown`）；层 2 锚定超集 `0` 个可确定命中。

两者**方法独立**却给出相同决定性事实：**没有任何静态写入者的有效地址覆盖 `0xA8F7AD`**，最终结论同为 ②不存在（静态写入者）。分类计数差异来自「740 行 vs 773 行（多 33 个非 `.text` 行）」与边界判据细微差别，不是结论分歧。

## 给 Lead 的验收建议

1. 若按**本卡任务书**逐字验收「740 个 `.text` 候选的逐条表」，请读 `EVIDENCE\w57_hy4_candidates_classified_740.tsv`（16 列、含 `gate_write` / `evidence`），其计数与 `GATE_WRITER_SCAN.md §3` 一致。
2. 根目录 `candidates_classified.tsv` 现为 W57b 的 773 行版本（12 列，中文列名），可作**独立复核**，其 `[L1] WRITE rows covering GATE_VA 0xA8F7AD : 0` 与本实例结论一致。
3. 两套脚本、stdout、TSV 均保留，未互相删除；`HEARTBEAT.txt` 的两种行格式即并发证据。
4. 本实例**未**修改 W21–W56，未写 `ra2youli`/`ra2forge`/`ra2opt`/`ra2bench`，`git` 只读未 commit，launched 0 / attached 0。

> 注：W57b 的 `STARTED_W57B.txt` 称「prior instance froze silent after 22:32 with zero output」——这与本实例实际情况不符（本实例 22:31 起持续产出，见 `STARTED.txt` / `HEARTBEAT.txt` / 全部 stdout）。此为调度层对上一实例的观察，本实例不据此否定自身产物；所有产物均以落盘时间戳与 stdout 为准。
