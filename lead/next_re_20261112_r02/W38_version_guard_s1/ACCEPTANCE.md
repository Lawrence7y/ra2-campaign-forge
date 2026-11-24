# ACCEPTANCE.md · W38 / S1 · 单元化验收断言设计

> 卡：`W38_version_guard_s1`｜**只做「能被机检」的检查设计，不做实现**。
> 下列 12 条断言是交给 **S2+ 回归脚本**执行的规格；本卡**未运行**任何一条（全部 `[待运行验证]`），未写生产代码、未接线、未新增回归脚本。
> 唯一在本卡真实运行过的自检是 `EVIDENCE\shape_check.py`（校验契约 JSON 结构本身，不是校验未来守卫），见 `EVIDENCE\shape_check.stdout.txt` / `exit_codes.txt`。

## 0 · 执行前置（所有断言共用） `[静态推断]`

| 项 | 规约 |
|---|---|
| 隔离载体 | 所有 fixture 复制到 **本卡/S2+ 自己的写域**（例如 `W38_version_guard_s1\sandbox\...` 或 S2 新卡目录）；**禁止**指向真实 `ra2youli`、禁止写仓库 `ra2forge/`、禁止动 `W21`–`W37`。 |
| 游戏进程 | 全程 `gamemd.exe` / `game.exe` 进程数 **0**；沙箱内 `gamemd.exe` 只能是 **inert 占位文件**（`W34\UNCOVERED.md` U9 `[转引]`），**不得启动游戏、不得 attach**。 |
| 镜像副本 | 如需改字节，**先复制到卡内副本再改**；原盘镜像只读。因本机存在多个物理副本且 `db264305…` 含原生 `.detour`，**不得**把任一副本当「干净零售金标准」 `[转引]`（W36 §3.1.1/§3.1.3）。 |
| `BASELINE.json` | 断言用的基线条目是**夹具**（`EVIDENCE\guard_contract_schema.json` 的 `baselineEntry` 形状，`provenance.is_clean_retail_gold=false`），由回归脚本注入；**不是** Lead 已定谳的真实基线。 |
| 零写判定 | 对夹具游戏目录做 `sha_tree()` 前后逐字节快照（含隐藏文件、stage 临时名、`.ra2forge.bak`、`.seal`）；**字节级相同**才算零写入。只比文件名/退出码不够。 |
| 分级 | 断言只证**文件层守卫行为**：拒绝/放行、零写入、原因码、报告字段。**不得**据此写「行为正确」「回归全绿 ⇒ 引擎行为正确」（RE-N09 L287 `文档门禁 PASS 不代替游戏行为对照`）。 |
| 结论口径 | 每条断言的「期望」必须可机检（退出码 / 报告字段 / 字节快照 / JSON schema 断言），不写「应该」「看起来」。 |

---

## A1 · `.text` 段哈希不同 ⇒ 拒绝 install 且零写入 `[待运行验证]`

- **输入**：`BASELINE.json` 含一条 `adjudicated=true` 夹具条目（`c02_text_sha256 = <夹具值>`）；沙箱游戏目录放一份 inert `gamemd.exe`，其 `.text` 段字节被改 1 字节（复制副本后改），其余 L1 字段（C01/C04/C08/C13）与夹具一致；执行 `install --package <pkg> --game <sandbox>`。
- **期望**：① `guardVerdict.state == "MISMATCH"`（或按 §3 步骤 4 声明 `baseline_id` 时必为 MISMATCH）；② `write_allowed == false`；③ `reason_codes` 含 `TEXT_SHA_MISMATCH`；④ exit code ∈ {21}（契约 R11）；⑤ 游戏目录**前后字节快照完全相同**（无 stage / 备份槽 / 清单 / seal）；⑥ `guard_report.json` 落在本卡写域且 `wrote_game_dir == false`。
- **失败信息**：`A1 FAIL: .text SHA differs from baseline but install proceeded; state=<state> writes=<n bytes changed> reason_codes=<...> exit=<code> — expected MISMATCH + zero writes + TEXT_SHA_MISMATCH`

## A2 · 判据不可读 ⇒ UNKNOWN，不得沉默放行 `[待运行验证]`

- **输入**：把 `gamemd.exe` 副本换成非 PE 文件（或截断使 `pe.read()` 抛 `PEError`），使 C02/C04 不可读；其余 L1 字段仍可读；执行 install。
- **期望**：`state == "UNKNOWN"`；`write_allowed == false`；`missing_criteria` 含 `C02` 且 `reason_codes` 含 `CRITERION_MISSING` 或 `CRITERION_UNREADABLE`；exit ∈ {20,23}；零写入；报告列出**实际读到的全部判据值** + 缺失清单；**不得**因「C01/C06 都对」而判 `KNOWN_GOOD`。
- **失败信息**：`A2 FAIL: unreadable PE criteria were silently ignored; state=<state> missing=<...> — expected UNKNOWN + CRITERION_MISSING + zero writes`

## A3 · `UNKNOWN` + `--force-unknown` 不得放行任何游戏目录写 `[待运行验证]`

- **输入**：同 A2 的 UNKNOWN 夹具；分别执行 `install --force-unknown`、`uninstall --force-unknown`、`build --install --force-unknown`、`build --csf-out <sandbox_game>/ra2md.csf --force-unknown`。
- **期望**：四次调用全部 `write_allowed == false`、零写入、exit ∈ {20}；`guard_report.json` 记录 `force_unknown_used=true` + 判据快照；`MISMATCH` 夹具下同一 flag 必须 exit 21 且报告无 `FORCE_UNKNOWN_READONLY_ONLY` 放行语义。
- **失败信息**：`A3 FAIL: --force-unknown escalated to a game-dir write; entry=<E1/E2b/E3> state=<state> bytes_changed=<n> — flag is read-only degradation only`

## A4 · 原始字节窗口不符 ⇒ MISMATCH + 零写入 `[待运行验证]`

- **输入**：`KNOWN_GOOD` 夹具；在某个待 patch 的 PE 头字段（COFF Characteristics / SizeOfStackReserve）**写前**把该 N 字节窗口篡改为别的值；执行 `ra2opt apply` 等价的接线后入口（或 S2 的 E6/XCHAIN 入口）。
- **期望**：`byte_windows_ok == false`；`state == "MISMATCH"`；`reason_codes` 含 `ORIGINAL_BYTE_WINDOW_MISMATCH`；exit 21；零写入（含备份区）；`guard_report.json` 含 `{target_file, foff, rva, va, n, before_sha256, after_sha256}`。
- **失败信息**：`A4 FAIL: original-byte window mismatch not detected; window_ok=<b> state=<state> — expected MISMATCH + ORIGINAL_BYTE_WINDOW_MISMATCH + zero writes`

## A5 · `verify` 在 UNKNOWN 下只读且必须标 UNKNOWN `[待运行验证]`

- **输入**：A2 夹具；执行 `verify --game <sandbox> --json`。
- **期望**：零写入（目录快照相同）；报告含 `guard_state == "UNKNOWN"`、`missing_criteria[]`、`verdict_evidence[]`；报告**不含** `OK` / `installed` / `no drift` 之类可被读作放行的措辞；exit code 按 v11 既有 `0/1/2/5/6/7/8/9` 语义，但 `guard_state` 字段必须存在。
- **失败信息**：`A5 FAIL: verify under UNKNOWN wrote bytes or omitted the UNKNOWN label; bytes_changed=<n> guard_state=<v> report_keys=<...>`

## A6 · 契约机器结构自检（本卡已可跑的静态断言） `[本次实测]`（结构自检） / `[待运行验证]`（S2 引用）

- **输入**：`EVIDENCE\guard_contract_schema.json`、`EVIDENCE\guard_decision_table.json`、`EVIDENCE\guard_contract_example.json`。
- **期望**：① schema `$defs` 10 个定义齐全；② `baselineEntry.adjudicated.const == true`；③ `provenance.is_clean_retail_gold.const == false`；④ `decisionTable.cells.minItems == 21`；⑤ 决策表恰 21 格、`(state, entry_id)` 无重复、覆盖 3 态 × 7 入口；⑥ 所有 `UNKNOWN`/`MISMATCH` 且 `entry_id ∈ {E1,E2b,E3,E4,E6}` 的行 `deny` 含 `ALL_GAME_DIR_WRITES` 且 `exit_code ∈ {20,21}`；⑦ `KNOWN_GOOD` 的 E1/E3 行 `require` 含 `L1_RECOMPUTED_AT_CALL` + `BYTE_WINDOW_OK`，`UNKNOWN` 的 E2b/E5 行分别含 `ALLOW_SANDBOX_ONLY` / `REPORT_UNKNOWN_MANDATORY`；⑧ 示例 `guardReport.wrote_game_dir == false` 且 `UNKNOWN ⇒ write_allowed == false`。
- **本卡实测**：`EVIDENCE\shape_check.py` 输出 `TOTAL FAILURES: 0`，exit 0（`shape_check.stdout.txt`、`exit_codes.txt`）。S2 应把同一组断言并入回归。
- **失败信息**：`A6 FAIL: contract schema/decision table invariant violated; check=<name> expected=<v> got=<v>`

## A7 · `--csf-out` 落在游戏目录内 ⇒ 必须按 E1 全流程拒绝 `[待运行验证]`

- **输入**：`UNKNOWN` 夹具；执行 `build --design <d> --out <sandbox_pkg> --csf-out <sandbox_game>\ra2md.csf`（路径经 `realpath` 解析落在游戏目录内）。
- **期望**：`csf_out` 路径**零写入**（`p.parent.mkdir()`、`.tmp-*` stage、`os.replace` 全部不得发生）；exit 20；`reason_codes` 含 `NO_BASELINE_MATCH`/`CRITERION_MISSING`；即使 `KNOWN_GOOD` 夹具，也必须先按 E1 完成 L1 重算 + C12 才允许写，且目标全文 SHA 与登记值一致。
- **失败信息**：`A7 FAIL: build --csf-out wrote into an UNKNOWN game dir; path=<p> bytes_changed=<n> — E2b must inherit E1 guard`

## A8 · 既有 flag 不得改变 `guard_state` `[待运行验证]`

- **输入**：`UNKNOWN` 与 `MISMATCH` 两套夹具；分别叠加 `--force`、`--allow-content-conflict`、`--adopt-legacy`、`--legacy`、`--drop-legacy-battlemd` 执行 install / uninstall。
- **期望**：每种组合 `guard_state` 不变（仍 `UNKNOWN`/`MISMATCH`）、`write_allowed == false`、零写入、exit 保持 20/21；这些 flag 只可在 `KNOWN_GOOD` 下作用于既有业务门禁。
- **失败信息**：`A8 FAIL: legacy flag overrode guard verdict; flag=<f> state_before=<s1> state_after=<s2> bytes_changed=<n>`

## A9 · 每次写入口调用前重新实算 L1（禁止哈希缓存复用） `[待运行验证]`

- **输入**：`KNOWN_GOOD` 夹具；第 1 次 install 成功；随后**原地替换**沙箱内 `gamemd.exe` 为另一份字节（改 C01/C02），第 2 次执行 install（不重启进程、不新建对象）。
- **期望**：第 2 次 `state != "KNOWN_GOOD"`（`UNKNOWN` 或 `MISMATCH`）、`write_allowed == false`、零写入、`observed_at` 晚于第 1 次；`guard_report.json` 的 `evidence[].observed_at` 为本次新值。
- **失败信息**：`A9 FAIL: L1 evidence was cached across write-entry calls; second call state=<s> observed_at=<t> (unchanged) — expected re-computation`

## A10 · 写入口穷举自证 + 隔离自证 `[本次实测]`（本卡已做） / `[待运行验证]`（S2 回归引用）

- **输入**：`WRITE_ENTRY_AUDIT.tsv` + `EVIDENCE\ast_scan.stdout.txt` + `callgraph_scan.stdout.txt` + `grep_scan.stdout.txt` + `gen_write_audit.stdout.txt` + `git_before.txt` / `git_after.txt` + `game_proc.txt`。
- **期望**：① TSV 恰 80 行（表头 + 79 行），每行 6 列、无 TAB 内嵌；② `43 direct + 25 [CALLER] + 9 XCHAIN + 2 ZERO-WRITE/INFO` 与生成器 stdout 一致；③ 43 = 54 AST 候选 − 3 OPEN_READ − 8 `str.replace` 假阳性；④ 有一行引用 `install.py:1140-1143`、有一行 `XCHAIN:GAP-ROW ra2opt optimize.apply()` 含 `FINAL_RULING.md §4-2: apply() 全函数体不调用 identity()`；⑤ 有 `verify_install() [ZERO-WRITE]` 行；⑥ `git status --porcelain -- ra2forge/ ra2youli/ 'lead/next_re_20261112_r02/W21*'` 开工前与收尾后**逐字节一致**（`EVIDENCE\git_before.txt` / `git_after.txt` 均为 `?? lead/next_re_20261112_r02/W21_dlc_orphan/`，exit 0）；⑦ `GAME_PROC_COUNT=0`；⑧ 最终版 `EVIDENCE` 脚本 exit code 全为 0 —— `gen_write_audit.py` 首次因 `[CALLER` 过滤式笔误 exit 1，修正后重跑 exit 0，**两次均留档**（`EVIDENCE\exit_codes.txt`、`RUN_LOG.md` §3 第 8 行）。
- **失败信息**：`A10 FAIL: write-entry audit or isolation self-proof inconsistent; row_count=<n> ast_candidates=<n> git_before=<x> git_after=<y> proc=<n>`

## A11 · `KNOWN_GOOD` 正例：允许 install，但不得写成「行为正确」 `[待运行验证]`

- **输入**：全部 L1 精确匹配夹具、C12 窗口匹配、`byte_windows_ok=true`；执行 install。
- **期望**：`state == "KNOWN_GOOD"`、`write_allowed == true`、exit 0；清单/seal/备份槽按 v11 既有事务落地；`guard_report.json` 记录 `baseline_id`；报告文本**不得**出现「行为正确」「功能正常」「回归全绿 ⇒ 行为正确」「已通过 RE-N09」等措辞（RE-N09 L287、任务书 L374 `[转引]`）。
- **失败信息**：`A11 FAIL: KNOWN_GOOD install did not proceed, or report overclaimed behavior correctness; state=<s> forbidden_phrase=<p>`

## A12 · 未定谳基线不参与判定；「干净零售金标准」被 schema 拒绝 `[待运行验证]`

- **输入**：`BASELINE.json` 含一条 `adjudicated=false` 的条目（或 `provenance.is_clean_retail_gold=true`）；其余字段与沙箱镜像完全一致。
- **期望**：① `adjudicated=false` 条目被 §3 步骤 2 过滤 ⇒ `state == "UNKNOWN"` + `NO_ADJUDICATED_BASELINE` + 零写入；② `provenance.is_clean_retail_gold=true` 的实例在 JSON Schema 校验阶段即被拒（`const:false`），回归脚本报 schema 错误而非放行；③ `db264305…` 若被登记，其 `provenance.contains_native_detour` 必须为 `true`。
- **失败信息**：`A12 FAIL: non-adjudicated / 'clean retail gold' baseline was accepted; adjudicated=<b> clean_gold=<b> state=<s> writes=<n>`

---

## 覆盖矩阵（断言 ↔ 契约 ↔ W36 S1 验收）

| 断言 | 契约章节 | W36 S1 验收项 |
|---|---|---|
| A1 / A2 / A3 | §3 判定算法、§4 E1、§5 R1–R5 | #3「判据不足 → 拒绝写入 + TARGET_ID=UNKNOWN + 缺失证据清单 + 仅只读降级」 |
| A4 | §2.2 C12、§5 R10 | RE-N09 L278「入口窗不符均拒绝」 |
| A5 | §4 E5 | #3 只读降级 |
| A6 | §6.1 / §6.2 | S1「机器可检形式」（W38 卡新增） |
| A7 | §1.2 路径归属规则、§4 E2b | W38 卡「build --csf-out / --mapselmd 相关」 |
| A8 / A9 | §4 跨态不变式、§5 R9 | #1「每行含判定与原因码」 |
| A10 | §7 现状结论、`WRITE_ENTRY_AUDIT.tsv` | #1/#2/#5（矩阵、`optimize.py:112-133`、`install.py:1140-1143` 引用行、隔离自证） |
| A11 / A12 | §0 红线、§6.1 不变式 5/6 | #4「失效风险 / 不得单独放行」、D4/D5 不迁就 |

> **再次声明**：A1–A12 是**断言设计**，本卡未执行 A1–A5/A7–A9/A11/A12；A6/A10 的自检只针对契约结构与本卡自身隔离，不证明任何游戏行为。安装态/执行态/行为态三态证据属 S4/S5。
