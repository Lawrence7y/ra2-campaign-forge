# DEFECT_PROOF.md — W68：v1 离散判据的语义缺陷证明（两反例，实跑）

> 卡：`W68_criterion_discrete_fix`｜纯离线（**I launched 0 / attached 0**）
> 判据变更的触发理由声明：见 `CRITERIA_SPEC_V2.md` §0 —— **语义正确性**（计数依赖采样时长），不是"改判据凑结论"。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]`。

---

## 1. 最小论证

**命题**：v1 的离散腿判决是**采样时长的函数**，不是**行为分布的函数**。

1. v1 把离散字段比较定义为**多重集（值→计数）**：`tool_b_stats.py:148-149` 的 `multiset()` 用 `Counter` 计数，`:203-207` 判 `ma != mb`，`:223-227` B-2 短路——任一字段多重集不等 ⇒ 直接 `SHIFT_DETECTED(reason=discrete_or_ui_mismatch)`，连续腿 B-3 从未被评估。`[本次读码]`
2. 计数 `c(v) = n × p(v)`，其中 n（行数）由采集时长 T 决定：W65 四趟按固定墙钟时长、6ms 节奏采集 ⇒ `n ≈ T/0.006s`。`T_A ≠ T_B ⇒ n_A ≠ n_B`；即使 `p_A(v)=p_B(v)` 对全部 v 成立（取值集合相同、占比相同），仍有 `c_A(v) ≠ c_B(v)` ⇒ `ma != mb` 必真。`[本次读码]` + `[转引 W65 out\b_compare.json]`
3. 因此存在"行为分布 X_A = X_B 且 T_A ≠ T_B"的输入世界（W65 四趟正是此世界：A=20,113 行 / B=20,229 行，五字段取值完全相同），在该世界里 f_v1 输出 `SHIFT_DETECTED`。**判决随 T 变化而 X 不变 ⇒ 判决不是行为的函数 ⇒ 语义缺陷**——与数据质量无关，与"想要什么结论"无关。

---

## 2. 反例 A —— 同分布但行数不同 ⇒ v1 必判 `SHIFT_DETECTED` `[本次实测]`

**构造**（对 W65 真采数据只读派生，**未改任何取值**；manifest 见 `EVIDENCE\counterexamples_manifest.json`，预期事先声明）：
- `--arm-a` = W65 `out\A_merged.ndjson`（20,113 行，原样）
- `--arm-b` = `B_merged.ndjson` 前 15,000 行 → `EVIDENCE\ca_unequal_n\ca_B_trunc15000.ndjson`
- 噪声臂：W65 `A1/A2/B1/B2` 原样

**命令**（对 FROZEN v1 原件**只读执行**，路径前缀 `<W65>`=`...\W65_bline_live_collect`、`<W68>`=`...\W68_criterion_discrete_fix`）：

```
python <W62>\tool_b_stats.py --compare
  --arm-a <W65>\out\A_merged.ndjson
  --arm-b <W68>\EVIDENCE\ca_unequal_n\ca_B_trunc15000.ndjson
  --noise-a1 <W65>\out\A1.ndjson --noise-a2 <W65>\out\A2.ndjson
  --noise-b1 <W65>\out\B1.ndjson --noise-b2 <W65>\out\B2.ndjson
  --out <W68>\EVIDENCE\ca_unequal_n\v1_result.json
```

**实跑结果**：
- 退出码 **0**（`--compare` 恒 0，判决看 `verdict` 字段 `[本次读码]`；stdout 全文 `v1_stdout.txt`）
- `verdict = SHIFT_DETECTED`，`reason = discrete_or_ui_mismatch`
- `n_a=20112 / n_b=14999`（dframe 数，行数 20113 vs 15000）
- `discrete_mismatch_fields = ['map_name','stage_idx','end_of_game','skip_map_select','battle_idx']` —— 全部五字段
- 逐字段多重集：A = `{SOV01UMD.MAP×20113, 0×20113, 0×20113, 0×20113, 1×20113}` vs B = `{SOV01UMD.MAP×15000, 0×15000, 0×15000, 0×15000, 1×15000}` —— **取值集合与占比完全相同，唯一差别是计数**；`J_ui=1.000000`。

**结论**：行为相同 ⇒ 判决 SHIFT，仅因采样时长（行数）不同。这正是 W65 四趟被判 `SHIFT_DETECTED` 的机制（`[转引]` `b_compare.json`：A=20113/B=20229 行，五字段全常量同值，仅计数不同即触发；`D_ks=0.001286、p=0.766、J_ui=1.0、ΔQ=0` 等连续证据从未参与判定）。

**v2 回归（同一输入，`tool_b_stats_v2.py`）**：
- 退出码 0；`verdict = SAME_DISTRIBUTION`（`within_noise_band`）
- 离散腿：`D_disc=0.0`、`N_disc=0.0`、`p_disc=1.0`（五字段占比逐值相同 ⇒ TVD=0；`v1_style_count_mismatch=True` 仅作对照报告）
- 连续腿：`D_ks=0.000364 ≤ max(N_ks=0.001572, D_floor=0.05)` 且 `p=0.940530 ≥ alpha` ⇒ B-3
- 说明：诊断性读数，正式判定须新采集（`CRITERIA_SPEC_V2.md` §6）。

---

## 3. 反例 B —— 行数相同但离散取值不同 ⇒ v1 也判 `SHIFT_DETECTED` `[本次实测]`

**构造**：`--arm-a` = `A_merged` 前 10,000 行；`--arm-b` = `B_merged` 前 10,000 行，其中前 5,000 行 `battle_idx` 1→0（flipped=5000）；**行数相等**（10,000 vs 10,000）。

**实跑（v1 原件）**：
- 退出码 0；`verdict = SHIFT_DETECTED`，`reason = discrete_or_ui_mismatch`，mismatch=[`battle_idx`]，`n_a=9999/n_b=9999`（相等）
- ⇒ **该判的对**：v1 在计数维度具备检出力。注意（收紧表述）：这只证明计数维度的检出力，不证明 v1 整体正确（B-2 短路使其 KS/UI 腿在本反例中未被检验）。

**实跑（v2，同一输入）**：
- 退出码 0；`verdict = SHIFT_DETECTED`，`reason = discrete_or_ui_mismatch`
- `battle_idx`：`props_A={1:1.0}` vs `props_B={1:0.5, 0:0.5}`，`tvd_f=0.5`
- `D_disc=0.5 > max(N_disc=0.0, D_floor=0.05)` **且** `p_disc=0.0005`（=1/2001，置换 2000 次，seed=20261113，+1 校正）⇒ B-2v2 触发
- ⇒ **v2 修正后检出力保留**：缺陷只在"计数"这个比较量，不在"检出离散差异"这个目标。

---

## 4. 合成对照补充（v2 selftest + v1 同用例）`[本次实测]`

v2 selftest（`EVIDENCE\v2_selftest\b_selftest_v2.json`，`TOOL_SELFTEST_PASS=True`，退出码 0；预期事先声明于 `CRITERIA_SPEC_V2.md` §5）：

| 用例 | 预期（事先声明） | 实际 | 通过 |
|---|---|---|---|
| B-POS | SAME_DISTRIBUTION | SAME_DISTRIBUTION（within_noise_band，D_disc=0） | ✓ |
| B-NEG | SHIFT_DETECTED | SHIFT_DETECTED（ks_beyond_noise：D_ks=0.998752，p=0.000500） | ✓ |
| B-NEG2 | SHIFT_DETECTED | SHIFT_DETECTED（discrete_or_ui_mismatch：D_disc=1.0，p_disc=0.0005） | ✓ |
| W68-CA-unequal-n | SAME_DISTRIBUTION | SAME_DISTRIBUTION（within_noise_band：N_ks=0.005750，D_ks=0.019424，D_disc=0） | ✓ |

**v1 在 W68-CA 同一用例上的实跑**（`--arm-a` = `ca_A1∪ca_A2` 合并文件 `synth\ca_A_merged.ndjson`（8,002 行），`--arm-b` = `synth\ca_B1.ndjson`（4,001 行）——同分布、同离散取值、仅行数不同）：退出码 0；`verdict = SHIFT_DETECTED`(discrete_or_ui_mismatch)，`n_a=8001/n_b=4000`，五字段全部"mismatch"（纯计数）。⇒ 缺陷在合成数据上同样复现，非 W65 数据特有。

---

## 5. 证据索引（全部在本卡目录内）

| 件 | 路径（相对本卡根） |
|---|---|
| 反例构造脚本 | `EVIDENCE\gen_counterexamples.py`（+ `gen_counterexamples.stdout.txt`、`gen_counterexamples.exit.txt`） |
| 反例 manifest | `EVIDENCE\counterexamples_manifest.json` |
| 反例 A v1 | `EVIDENCE\ca_unequal_n\{v1_result.json, v1_stdout.txt, v1.exit.txt, ca_B_trunc15000.ndjson}` |
| 反例 A v2 | `EVIDENCE\ca_unequal_n\{v2_result.json, v2_stdout.txt, v2.exit.txt}` |
| 反例 B v1/v2 | `EVIDENCE\cb_equal_n_diffvals\{v1_result.json, v1_stdout.txt, v1.exit.txt, v2_result.json, v2_stdout.txt, v2.exit.txt, cb_A_10000.ndjson, cb_B_10000_flip.ndjson}` |
| v2 selftest | `EVIDENCE\v2_selftest\{b_selftest_v2.json, v2_selftest.stdout.txt, selftest.exit.txt, synth\}` |
| v1 on W68-CA | `EVIDENCE\v2_selftest\{v1_on_w68ca_result.json, v1_on_w68ca_stdout.txt}` |
| 诊断重算原始输出 | `EVIDENCE\recompute_v2_real_compare.json`（+ `recompute_v2_real.stdout.txt`、`recompute_v2_real.exit.txt`） |
| RECOMPUTE 组装脚本 | `EVIDENCE\build_recompute_doc.py`（+ `.exit.txt`） |
| 退出码语义 | `EVIDENCE\EXIT_CODE_SEMANTICS.txt` |

---

## 6. 纪律声明

- 全程 **I launched 0 / attached 0**；未启动 `gamemd.exe`、未 attach、未取 `.game_instance.lock`。
- 只写本卡目录；W62 / W65 / W21–W67 产物**零改动**（v1 工具只读执行，W65 数据只读引用）；`git` 只读。
- 本卡交付"判据修正 + 诊断性重算"；全文不含"B 线等价性成立"或"装包无影响"表述（禁语同时登记于 `RECOMPUTE_DIAGNOSTIC.json.forbidden_claims`）。
