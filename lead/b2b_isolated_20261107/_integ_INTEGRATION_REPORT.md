# D-25 第 6 步 · 隔离副本离线集成演练报告（lead/b2b_isolated_20261107/）

**日期**：2026-11-07　**执行者**：离线集成执行员（独立上下文，执行者≠核验者）
**任务**：D-25 第 6 步「隔离副本离线集成」——把候选 LF 重物化版复制为隔离副本并做离线集成演练
**被核对象（隔离副本）SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759**
**母本 SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508**（集成前后两次实算一致，零漂移）
**方法**：全部数字取自本会话亲自实跑（`python -I -B -X utf8` + 绝对路径，指纹 `hashlib`）或本次实读「文件:行」。零真机、零采样代码、不 commit / push。**唯一写域** = `lead/b2b_isolated_20261107/` 下本任务指定新件；母本、候选原件、设计、判定书、绑定件本轮**零改动**（指纹三次实算一致 + `git status --porcelain` 全部仅 `??` 无 `M`）。

---

## 0 结论（先读这里）

1. **隔离副本与候选逐字节同一**：`qc151_trip.isolated.py` 复制自 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`，双侧 SHA256 均 = `ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2`、412,759 B（`_integ_make_isolated_out.txt`，`COPY_IDENTICAL = True`）。
2. **离线集成演练全 PASS**：集成探针 **43/43**（`_integ_probe_isolated_out.txt`，`PASS=43 FAIL=0` + `INTEG_PROBE_DONE`）；候选自带测试套件路径副本复跑 **PASS=29 FAIL=0**、`EXIT=0`（`_integ_test_isolated_out.txt`）；机械门禁路径副本复跑 **9/9**、`ALL 9 GATES PASSED! EXIT=0`（`_integ_check_isolated_out.txt`）。
3. **九 hunk 决定性重建（集成口径）**：`母本 + 设计 §4 九 hunk == 隔离副本`（逐字符串 == 逐字节）与 `母本 + CANDIDATE_LF.diff == 隔离副本`（逐字节）双路成立，重建 sha256 均为 `ca23c116064b25a6…`；设计九 hunk 母本区间 `(212,6)/(4458,6)/(4558,8)/(4572,20)/(5906,7)/(5936,7)/(6294,6)/(6386,6)/(7122,7)` 与 `B2B_DESIGN.md:635` 逐项一致；± 计数 +255/−13 与 R3 判定书 `:85` 口径一致。
4. **母本零漂移**：集成前（`_integ_fingerprint_pre.txt`）与集成后（`_integ_fingerprint_post.txt`）两次实算 + 门禁 [4] 项独立实算，三次均 = `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636 / 399508 B`。
5. **★ 本轮是「隔离副本集成演练」，不构成「可应用到母本」的放行**（依据见 §3）。

## 1 实跑命令与退出码（cwd = `D:/Project/ra2-campaign-forge`，均本会话亲自执行）

| # | 命令 | 输出件 | 关键结论 | 退出码 |
|--:|:--|:--|:--|--:|
| 1 | `python -I -X utf8 -c "<六件上游指纹核对，hashlib>"` | （会话输出） | 6/6 与编排方指纹一致 MATCH | 0 |
| 2 | `python -I -X utf8 lead/b2b_isolated_20261107/_integ_fingerprint.py pre > …_integ_fingerprint_pre.txt` | `_integ_fingerprint_pre.txt` | 母本第 1 次实算 = 绑定记录；隔离副本 MISSING（预期） | 0 |
| 3 | `python -I -X utf8 lead/b2b_isolated_20261107/_integ_make_isolated.py > …_integ_make_isolated_out.txt` | `_integ_make_isolated_out.txt` | `COPY_IDENTICAL = True`（双侧 ca23c116…/412759） | 0 |
| 4 | `python -I -B -X utf8 lead/b2b_isolated_20261107/_integ_probe_isolated.py > …_integ_probe_isolated_out.txt` | `_integ_probe_isolated_out.txt` | `PASS=43 FAIL=0` + `INTEG_PROBE_DONE` | 0 |
| 5 | `python -I -B -X utf8 lead/b2b_isolated_20261107/_integ_make_copies.py > …_integ_make_copies_out.txt` | `_integ_make_copies_out.txt` + 两份 diff 证明 | 测试副本仅改 :37；门禁副本仅改 :56/:61/:63/:64 | 0 |
| 6 | `python -I -B -X utf8 lead/b2b_isolated_20261107/_integ_test_isolated.py > …_integ_test_isolated_out.txt` | `_integ_test_isolated_out.txt` | `Ran 29 tests` / `OK` / `PASS=29 FAIL=0` / `EXIT=0` | 0 |
| 7 | `python -I -B -X utf8 lead/b2b_isolated_20261107/_integ_check_isolated.py > …_integ_check_isolated_out.txt` | `_integ_check_isolated_out.txt` | 9/9 PASS（门禁 [4] 自算母本指纹一致） | 0 |
| 8 | `python -I -B -X utf8 lead/b2b_isolated_20261107/_integ_fingerprint.py post > …_integ_fingerprint_post.txt` | `_integ_fingerprint_post.txt` | 母本第 2 次实算 = 第 1 次 = 绑定记录（零漂移）；隔离副本 == 候选 | 0 |
| 9 | `python -I -B -X utf8 lead/b2b_isolated_20261107/_integ_make_rollback.py > …_integ_make_rollback_out.txt` | `_integ_make_rollback_out.txt` + `_integ_isolated_vs_mother.diff` | 回退差异件 18,446 B / 9 个 `@@`；与 `CANDIDATE_LF.diff` 仅 `+++ b/` 头行不同（8 字节路径长度差），hunk 体逐字节同构 | 0 |
| 10 | `git status --porcelain -- <五个只读域>` / `git ls-files --error-unmatch -- <母本>` | （会话输出） | 只读域全为 `??`、无 `M`；母本不被 git 跟踪（故零改动证据以指纹三次实算为准） | 0 |

## 2 集成探针 43 项要点（`_integ_probe_isolated_out.txt`，逐项亲跑）

- **[1] 指纹与同一性（6 项）**：母本/候选/隔离/候选diff/设计五件 SHA256+字节数全部等于绑定记录；★隔离副本 == 候选逐字节；隔离副本 CR=0（N-1 不复发）。
- **[2] ast.parse（7 项）**：隔离副本 0 语法错误，顶层节点 333、顶层函数 135、顶层类 4；`make_pre_freshness_snapshot` / `classify_except_freshness` / `copy_post_except_evidence` / `finalize_trip` / `main` / `Recorder` 六符号 AST 顶层齐备。
- **[3] 隔离加载（10 项）**：与 R3 同法（`CANDIDATE_SEMANTIC_REVIEW_R3.md:6`、`_review_probe_r3.py:411-416`、`_test_candidate_lf.py:40-57`）——`importlib.util.spec_from_file_location` + `unittest.mock.patch("ctypes.windll.user32.SetProcessDPIAware", return_value=1)`（拦截目标字符串，防真调用，**非采样代码**），模块名 `qc151_trip_isolated_integ`，未触发 `__main__` 入口（候选 ：7532-7533 守卫，顶层 ：182 的 DPI 调用被拦截）。7 符号齐备；`FRESHNESS_GROUP='FRESHNESS'`；`FRESHNESS_SNAPSHOT_STATES` 4 态 / `FRESHNESS_VERDICTS` 9 值 / `FRESHNESS_CONFIDENCES` 4 值。
- **[4] 函数级冒烟（7 项）**：F01/F02/F03 fixture（与 `_test_candidate_lf.py:501-534` 逐字同源）→ `new_first_appearance/high/True/False`、`absent_both/low/False`、`leftover_unchanged/high/False`；未采集 4 形态置信恒非 high（C2 同形态）；三态可分 `unknown / new_first_appearance / new_write` 两两不等；快照采集不存在路径 → `absent_confirmed`，以隔离副本自身为只读输入 → `present` 且 sha256 与实算一致、双时刻齐。
- **[5] diff 统计（2 项）**：隔离副本 vs 母本变更 opcode 块 = 12、+255/−13（difflib 行文本口径，与 R3 `:85-86` 候选口径一致）。
- **[6] 决定性重建（8 项）**：设计 §4 恰 9 个 ```diff 块、九 hunk 母本区间与 `B2B_DESIGN.md:635` 逐项一致；上下文/`-` 行逐行断言母本原文、消费/产出行数逐 hunk 与 `@@` 头声明一致；`母本+九hunk` 与 `母本+CANDIDATE_LF.diff` 两路重建均逐字节 == 隔离副本；两路 ± 计数均 +255/−13。
- **[7] 九锚点（1 项）**：门禁 `ANCHORS`（`_check_candidate_r3.py:84-94`）9/9 在隔离副本可定位。

## 3 口径声明（任务项 4 · 对照 D-25 第 6 步原文）

**D-25 第 6 步原文**（`lead/d25_ruling_20261106/RULING_D25.md:37`，本次实读）：
> 「来源会话派具有明确隔离副本写域的人员离线集成；独立复审最终差异并复跑离线回归，保存输入/输出指纹、差异和回退材料。只签“隔离副本离线集成通过”，不签正式母本已应用或真机验收。本次不授权正式母本写入。」

逐项对照与本轮落点：

| D-25 第 6 步要求 | 本轮落点 | 状态 |
|:--|:--|:--|
| 具有明确隔离副本写域的人员 | 写域 = `lead/b2b_isolated_20261107/`（本任务书指定，本轮唯一写域） | 已满足 |
| 离线集成 | 隔离副本逐字节复制 + 探针 43/43 + 测试 29/29 + 门禁 9/9 | 已满足 |
| 复跑离线回归 | 测试套件路径副本 + 门禁路径副本复跑（判定逻辑零改动，仅路径改绑，diff 证明在案） | 已满足 |
| 保存输入/输出指纹、差异和回退材料 | `_integ_fingerprint_pre/post.txt`、`_integ_make_isolated_out.txt`、两份路径副本 diff 证明、`_integ_isolated_vs_mother.diff`、全部 `*_out.txt` | 已满足 |
| **独立复审最终差异** | **不在本轮签发范围**：执行者≠核验者（R3 判定书 `:138` 惯例），须由来源会话另派独立复审复跑；本轮只产出全部材料 | **移交下游** |
| 只签「隔离副本离线集成通过」，不签母本已应用/真机验收 | 本轮结论严格限定为：**隔离副本离线集成演练完成、离线回归复跑全 PASS** | 遵守 |
| 本次不授权正式母本写入 | 母本全程零接触；`RULING_D25.md:21`「隔离副本集成须依次通过前置门禁，并由来源会话逐项指定写域」、`:26`「不得把隔离副本离线集成扩大为正式母本应用；后续正式应用必须另有明确允许目标文件写入的任务」 | 遵守 |

**冲突核对结论**：D-25 第 6 步原文与本任务书**未发现冲突**（任务书第 4 条与 `RULING_D25.md:37` 同义；任务书比裁决书多要求的仅是「九 hunk 按批准设计 §4 集成演练」与「逐字节核对」，属更细的验收材料，不放宽也不改写裁决口径）。另核 `N1_BINDING.md §7`（:100-110 区段，实读）：「不签第 5 步语义复审通过」「不进入第 6 步隔离副本集成」「不代表可应用到母本」——与本轮口径一致；本轮是第 6 步本身的执行，不改写 N1 绑定的任何声明。

**准确含义**：本轮可支撑的签发 = 「隔离副本离线集成演练通过（离线回归复跑 29/29 + 门禁 9/9 + 探针 43/43，母本零漂移）」。它**不等于**：候选可应用到母本（须另有明确允许母本写入的任务）、独立复审已通过（移交下游）、运行时已验证（零真机）。

## 4 探针诚实记录

- 首趟探针在「[6] 决定性重建」hunk2 处 FAIL：探针自身缺陷——`apply_hunks` 把上下文/`-` 行断言用在了**输出坐标**（累计 offset 后）而非**母本坐标**，hunk1 因 offset=0 未暴露。修正后记档趟 43/43 PASS。迭代中母本、候选、设计、R3 件**零改动**（指纹三次实算 + git status 为证）；探针修正仅写域内文件。
- 首趟探针（未加 `-B`）曾在本写域产生 `__pycache__`（`spec_from_file_location` 字节码缓存所致）；已删除并以 `python -I -B -X utf8` 重跑作为记档趟，写域现无缓存残留。
- 三个 diff 生成器首趟用 `write_text` 落盘（Windows 默认把 `\n` 翻译成 `\r\n`），致 3 份 diff 输出件盘上带 CRLF、回退件盘上字节与脚本打印值不符（18,446+339=18,785 B）；已改为 `write_text(..., newline="\n")` 重跑，盘上现为纯 LF 且与记档哈希一致（§6）。重跑 `_integ_make_copies.py` 重写的两份路径副本指纹**未变**（`_integ_test_isolated.py`=8e73dccc…、`_integ_check_isolated.py`=9632cbe0…，独立实算复核），故已完成的测试 29/29 与门禁 9/9 趟次对盘上件仍然有效。
- 测试套件沙盒使用系统临时目录（`tempfile.mkdtemp`，`_test_candidate_lf.py:66`，tearDown 清理），不在仓库内、不触任何只读域——与 R3 复跑同法。

## 5 未验（单列，不补造）

1. **真机 / 运行时整趟**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 taskkill、未读活进程内存、未写采样代码（铁律 1/2）。全部结论为静态 + 隔离函数级 + 测试套件级结构性结论（继承 R3 `:114` 同款限缩）。
2. **运行时退出码实测**：F/E 分离的整趟运行时行为未验（R3 `:115` 同款）。
3. **`rec.dump` 真实磁盘落盘链**：测试套件为内存/临时沙盒合成，`qc151_fields.json` 真盘写链未做整趟复现（R3 `:116` 同款）。
4. **STATE_MATRIX 14 行全矩阵 exec**：本轮探针只冒烟了 7 类 fixture（F01/F02/F03 + 4 未采集形态 + 三态可分）；14 行全矩阵沿用 R3 `_review_probe_r3_out.txt:135-149` 的既有全验，本轮未重复（本轮是集成演练，不是第二轮语义复审）。
5. **P7a/P7b（finally 内先于收尾失败时 F 是否落盘）**：未单独构造场景，沿用设计 §3 登记（R3 `:117` 同款）。
6. **「独立复审最终差异」**：未做也不由本轮自签（执行者≠核验者）；材料已备齐待独立复审复跑。

## 6 写域文件清单（lead/b2b_isolated_20261107/，共 20 件，全部本轮新建）

| 文件 | 说明 |
|:--|:--|
| `qc151_trip.isolated.py` | 隔离副本（= 候选逐字节，412,759 B） |
| `_integ_fingerprint.py` / `_integ_fingerprint_pre.txt` / `_integ_fingerprint_post.txt` | 指纹脚本 + 集成前/后两次实算输出 |
| `_integ_make_isolated.py` / `_integ_make_isolated_out.txt` | 复制脚本 + 输出 |
| `_integ_probe_isolated.py` / `_integ_probe_isolated_out.txt` | 集成探针 + 记档趟输出（43/43） |
| `_integ_make_copies.py` / `_integ_make_copies_out.txt` | 路径副本生成器 + 输出 |
| `_integ_test_isolated.py` / `_integ_test_isolated_diff.txt` / `_integ_test_isolated_out.txt` | 测试路径副本（仅改 ：37，8e73dccc…/34,103 B）+ diff 证明（ba3415a5…/424 B）+ 复跑输出（29/29） |
| `_integ_check_isolated.py` / `_integ_check_isolated_diff.txt` / `_integ_check_isolated_out.txt` | 门禁路径副本（仅改 ：56/:61/:63/:64，9632cbe0…/12,070 B）+ diff 证明（5054bedb…/1,003 B）+ 复跑输出（9/9） |
| `_integ_make_rollback.py` / `_integ_make_rollback_out.txt` / `_integ_isolated_vs_mother.diff` | 回退材料生成器 + 输出 + 母本→隔离副本差异件（32ac4730…/18,446 B/CR=0/9 个 `@@`） |
| `_integ_INTEGRATION_REPORT.md` | 本报告 |

三份 diff 落盘件均为纯 LF（CR=0），盘上 SHA256 由独立核对命令实算（2026-11-07 21:02 趟）：`_integ_isolated_vs_mother.diff` = `32ac4730027d61aa70f0b3f69afbc49fb65f243df6c56339e95def9df76120e6`；`_integ_test_isolated_diff.txt` = `ba3415a5355558a5b747726aa15885615b091405158f63f1aed312b4972af48a`；`_integ_check_isolated_diff.txt` = `5054bedbb480d188e1314ec1ee6da888c04a5388ce0c0f32c5cbe09d50d45ba4`。

## 7 复现命令

```
python -I -B -X utf8 D:/Project/ra2-campaign-forge/lead/b2b_isolated_20261107/_integ_fingerprint.py post
python -I -B -X utf8 D:/Project/ra2-campaign-forge/lead/b2b_isolated_20261107/_integ_probe_isolated.py
python -I -B -X utf8 D:/Project/ra2-campaign-forge/lead/b2b_isolated_20261107/_integ_test_isolated.py
python -I -B -X utf8 D:/Project/ra2-campaign-forge/lead/b2b_isolated_20261107/_integ_check_isolated.py
```
退出码 0 = 全 PASS。注：`_integ_probe_isolated.py` 与 `_integ_test_isolated.py` 会加载隔离副本执行其模块顶层（DPI 调用已被 mock 拦截、`__main__` 入口不触发）；`_integ_test_isolated.py` 自建临时沙盒并在结束时清理。
