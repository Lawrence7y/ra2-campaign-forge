# MUTATION_LOG.md — 证明测试能失败（防「全绿空壳」）

run_id = `NEXT_RE_20261112_R01`。
驱动器：`mutation_run.py`；原始输出：`out/mutation_results.txt`。
**所有变异都只改副本**（`out/_mutation/<id>/` 里的完整拷贝），原件候选件从未被改；
每次变异后用干净件重新覆盖副本、再跑一遍确认回绿。

精确命令（每次在副本根目录执行的都是同一条）：

```
python -X utf8 test_re_n01_offline.py
```

干净基线：**13 项检查 / 0 项失败 / exit 0**（`TEST_OUTPUT.txt`）。

引用约定：下面带 `...` 的结果行是**节选**（去掉了失败的完整中文断言名以省版面），
逐字原文见 `out/mutation_results.txt`；所有 `[RED]` 行均按原样抄录。

---

## 汇总

| 变异 | 目标断言 | 改坏了什么 | 变红？ | 变红行数 | 复原后 |
|---|---|---|---|---|---|
| M-A1 | T-A1 | `build_event` 的 `if only_tid:` 改成 `if False:`，`--only-tid` 退化成先调全线程 `sample(pid)` | ✅ | 5（含 T-A1） | 13/0 exit 0 |
| M-C2 | T-C2 | `_RunScanner.push` 的缺测/间隔处理整段换成朴素合并（过滤读失败、忽略 `gap_ns` 与段边界） | ✅ | 5（含 T-C2） | 13/0 exit 0 |
| M-C4 | T-C4 | `OnlineAccumulator.summary` 的 `n_frame_reads` 故意 `+1` | ✅ | 5（含 T-C4） | 13/0 exit 0 |
| M-B2 | T-B2 | `SAMPLE_STATES` 把 `resume_verified_ok` 改成 `ok`，五态塌成四态 | ✅ | 1（恰为 T-B2） | 13/0 exit 0 |
| M-A3（加做） | T-A3 | `event_total_ns` 只取 `resume→end`（退回「只记最后一次函数调用耗时」） | ✅ | 2（含 T-A3） | 13/0 exit 0 |

**结论：5/5 变异都让目标断言变红；没有出现「变异未能变红」的条目。**
任务卡至少要求 4 条（T-A1 / T-C2 / T-C4 / T-B2），四条全部成功，另加做 T-A3 一条。

---

## M-A1 — T-A1：`--only-tid` 模式下 `sample()` 调用数 == 0

- **改坏副本里的什么**：`candidate/re_n01_monitor.py` 的 `build_event()`：
  `if only_tid:` → `if False:`。于是 `--only-tid` 也走全线程 `sampler.sample(pid)`。
- **哪条断言变红**：`T-A1`（另连带 T-B1/B2/B3/B4，因为单线程入口被完全绕过）。
- **原始输出片段**（`out/mutation_results.txt`，`M-A1 MUTATED` 段，exit=1）：

```
[RED] T-A1 --only-tid ⇒ sample(pid) 调用数 == 0                     counts={'sample': 1, 'sample_single': 0, 'sample_one_thread': 0}
[RED] T-B1 恢复失败进事件：resume_failed / failed / errors 非空            state=error resume=unknown errors=['resume_fail:tid=30668']
...
结果：13 项检查，5 项失败：['T-A1 --only-tid ⇒ sample(pid) 调用数 == 0', ...]
```

- **为什么有区分力**：spy 是三个入口各自计数的独立假对象，断言 `sample==0 且 sample_single==1`；
  一旦驱动退化成「先 `sample(pid)` 再丢弃结果」（问题 A），计数立刻从 0 变 1。
- **复原**：`clean_copy()` 重新覆盖副本 → `结果：13 项检查，0 项失败`，exit 0。

## M-C2 — T-C2：帧100 → 长读失败 → 帧100 不产生已证实连续冻结

- **改坏副本里的什么**：`_RunScanner.push` 的 20 行缺测处理替换为：
  `if not ok: self.prev = r; return` + `gap = 0`，即过滤读失败、忽略 `gap_ns > gap_max_ns`、
  忽略跨段、忽略 `pending_gap`，把两端同值拼成一个长 run。
- **哪条断言变红**：`T-C2`（另连带 T-C1/C2b/C3/C4，因为在线摘要与 replay 不再一致）。
- **原始输出片段**（`M-C2 MUTATED`，exit=1）：

```
[RED] T-C2 帧100→长读失败→帧100 不产生已证实连续冻结                             online_conf=1 replay_conf=0 gap_runs=2 merged=False missing_segs=2 read_failed=3 max_gap_ns=2000000000
[RED] T-C4 在线摘要 vs replay 离线重算逐字段一致                              fields=98 diff=['$.n_zero_delta_runs: 1 != 3', '$.zero_delta_runs: len 1 != 3', '$.zero_delta_runs[0].duration_ns: 50000000 != 23000000'] n_records=12 n_events=2
结果：13 项检查，5 项失败：['T-C1 异常退出后 NDJSON 可解析且含此前记录', ...]
```

  `online_conf=1` 正是「把两端同值拼成连续冻结」被误证实；replay 侧仍是 0，
  因此 T-C4 的逐字段差异也把它抓出来。
- **为什么有区分力**：T-C2 **同时**断言在线与离线两方 `n_confirmed_continuous_freezes==0`、
  `n_gap_interrupted_runs>=2`、两个 run 不跨 gap 合并、存在 ≥2 个
  `verdict=missing_gap / undecidable=True` 的段、3 条 read_failed 原样保留、最大真实 `gap_ns≥2 s`；
  并且另设 **T-C2b 阳性对照**（无缺测长停必须 `confirmed>=1`），
  防止「重算器永远返回 0」也能让 T-C2 全绿。
- **复原**：干净件覆盖 → 13/0 exit 0。

## M-C4 — T-C4：在线摘要 vs `replay_re_n01.py` 逐字段一致

- **改坏副本里的什么**：`OnlineAccumulator.summary()` 的
  `"n_frame_reads": self.n_frame_reads,` → `… self.n_frame_reads + 1,`。
- **哪条断言变红**：`T-C4`（另连带所有也调用 `deep_diff(online, replayed)` 的 C 组断言）。
- **原始输出片段**（`M-C4 MUTATED`，exit=1）：

```
[RED] T-C4 在线摘要 vs replay 离线重算逐字段一致                              fields=114 diff=['$.n_frame_reads: 10 != 9'] n_records=12 n_events=2
结果：13 项检查，5 项失败：['T-C1 异常退出后 NDJSON 可解析且含此前记录', ...]
```

- **为什么有区分力**：`deep_diff()` 递归比对 114 个叶子字段（含 `segments` / `zero_delta_runs` /
  `events` / `cost_ns_sum` / `cost_ns_max` 的每一层），并额外校验
  `json.dumps(sort_keys=True)` 全等。在线侧是流式增量实现，离线侧是批式归约，
  **没有共用归约代码**，所以任何一侧单独漂移都会产生具体字段路径差异。
- **复原**：13/0 exit 0。

## M-B2 — T-B2：五态两两不同

- **改坏副本里的什么**：`SAMPLE_STATES` 常量里 `resume_verified_ok` → `ok`。
- **哪条断言变红**：**恰好 T-B2 一条**（最小、最干净的变异）。
- **原始输出片段**（`M-B2 MUTATED`，exit=1）：

```
[RED] T-B2 五态两两不同且均非 null/空                                      states=('not_attempted', 'ok', 'resume_verified_ok', 'resume_failed', 'error') SAMPLE_STATES_distinct=4
结果：13 项检查，1 项失败：['T-B2 五态两两不同且均非 null/空']
```

- **为什么有区分力**：测试分别用 5 个假采样器构造 未采集 / 无错误 / 恢复成功 /
  恢复失败 / 一般错误五种事件，从**实际写出的 NDJSON event 行**取 `sample_state`，
  断言 `len(set(...))==5`、每个都是非空字符串、都属于契约五态、且常量本身 5 个互异。
  用 `null` 或同值兼表状态会立刻塌缩。
- **复原**：13/0 exit 0。

## M-A3（加做） — T-A3：整事件时长 > 最后一次函数调用耗时

- **改坏副本里的什么**：`cost_from_marks()` 的 `"event_total_ns": d(t_cand, t_end)` →
  `d(t_res, t_end)`，即只记「恢复→收尾」这一段（最后一次函数调用）。
- **哪条断言变红**：`T-A3` 与 `T-D1`（后者要求 `event_total >= end_to_end`）。
- **原始输出片段**（`M-A3 MUTATED`，exit=1）：

```
[RED] T-A3 整事件时长 > 最后一次函数调用耗时                                    event_total=9000000 e2e=22000000 last_call=5000000 sampler=13000000 detect=2000000
[RED] T-D1 六计时字段 + e2e ≥ 分项之和（容差 0ns）                            events=1 e2e=16000000 parts=16000000 held=3000000
结果：13 项检查，2 项失败：['T-A3 整事件时长 > 最后一次函数调用耗时', ...]
```

- **复原**：13/0 exit 0。

---

## 关于「若有变异没变红就要加强」的复核

本轮 5 条变异全部变红，无需加强。特别地，为排除「T-C2 靠重算器恒返回 0 而空绿」，
**主动加了 T-C2b 阳性对照**；M-C2 下它也一并变红（`deep_diff` 不一致），
说明这条对照确实在监测两侧语义，而不是永真断言。
