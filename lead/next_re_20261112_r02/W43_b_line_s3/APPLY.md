# APPLY.md · W43 / S3 应用、校验与回滚

> 全部路径相对仓库根 `D:\Project\ra2-campaign-forge`。**本卡未就地修改任何 W21–W42 / 仓库 `ra2forge/` / `ra2youli/` 文件**；本文件给出的是「从 v12 派生 v13」与「把 D1 修订合入 W38」的**相对路径补丁 + 校验 + 回滚**说明。
> 分级同 `S3_IMPLEMENTATION.md §0`。纯离线，不涉及游戏启动。

---

## 0 · 交付物清单（写域：`lead/next_re_20261112_r02/W43_b_line_s3/`）

```
W43_b_line_s3/
├── ra2forge_patched_v13/                     # 新包（v12 + 4 改 + 5 增）
│   └── ra2forge/
│       ├── builder.py          [改] csf-out 错误理由串
│       ├── cli.py              [改] 4 个 opt-in 开关 + resolve/guard-check 子命令 + E2b→E1 预检
│       ├── csf.py              [改] 完整性门禁理由 + 封死 create_if_missing 真实缺口
│       ├── install.py          [改] E1/E3 守卫接线 + 注释理由
│       ├── s3_contract.py      [增] 裁决常量 / E1 允许清单 / K1–K12 / 写入口覆盖表
│       ├── version_guard.py    [增] W38-S1 classify() + 决策表门禁 + guard_report
│       ├── feature_subset.py   [增] W42-S2 resolve()
│       └── data/
│           ├── E1_KNOWN_GOOD.json            [增] D1 修订允许清单（运行时可读）
│           └── guard_decision_table.json     [增] D1 同步 21 格决策表（运行时可读）
├── s1_revision/                             # D1 修订副本（待 Lead 决定是否合入 W38）
│   ├── E1_KNOWN_GOOD.json
│   └── guard_decision_table.json
├── regress_dlc_v13.py                       # 57 继承 + 25 S3 = 82 例
├── s3_cases.py                              # S3_1..S3_25 实现（被 regress 绑定）
├── out/                                     # 逐例日志 / SUMMARY / 两张 SHA-256 表 / 源 delta
├── EVIDENCE/                                # 脚本 + stdout + exit code
├── PATCH_RELATIVE.diff                      # v12→v13 的 4 个源文件统一 diff（18 hunks）
├── S3_IMPLEMENTATION.md
├── TRACK_B_gates.json                       # D4 独立工件
├── APPLY.md / UNCOVERED.md / DISAGREE.md
```

---

## 1 · 补丁（相对路径）

### 1.1 v12 → v13 的完整源补丁

`PATCH_RELATIVE.diff` 是 `git diff --no-index --unified=3` 的结果，路径已重写为仓库相对形式：

```
--- a/W41_csf_install/ra2forge_patched_v12/ra2forge/<file>
+++ b/W43_b_line_s3/ra2forge_patched_v13/ra2forge/<file>
```

覆盖 4 个文件、18 个 hunk（[本次实测]，`EVIDENCE/verify_s3.py` 校验 `>= 17` 以容忍后续文案微调）。应用方式（**从仓库根、在副本上**）：

```powershell
# 1) 先复制 v12 包到目标目录（不要在 W41 上原地改）
Copy-Item -Recurse -Force `
  "lead\next_re_20261112_r02\W41_csf_install\ra2forge_patched_v12" `
  "<目标>\ra2forge_patched_v13"

# 2) 逐文件应用 PATCH_RELATIVE.diff（路径需先映射到目标目录）
#    git apply 不跨仓库根；推荐直接以本卡已生成的 v13 目录为准，
#    用 3) 的哈希校验确认它是「v12 + 该 diff」的精确结果。
```

**推荐做法**：直接使用本卡已生成的 `W43_b_line_s3\ra2forge_patched_v13\`（它就是 `v12 + PATCH_RELATIVE.diff + 5 个新增文件` 的结果），用 §2 校验；`PATCH_RELATIVE.diff` 仅作可读审计与回滚依据。

### 1.2 D1：S1 的 E1 允许清单修订补丁（**未就地应用**）

按 Lead D1「S3 在同一补丁内提交 S1 修订」，但本卡纪律禁止改 W38 目录，故以**补丁 + 修订副本**交付。若 Lead 决定合入，目标文件与改动如下：

**目标 A**：`lead/next_re_20261112_r02/W38_version_guard_s1/VERSION_GUARD_CONTRACT.md` §4 决策表 `E1` 行 / §1.2 允许清单段落。

```diff
- 允许：备份槽写入、`*.MAP`/`BATTLEMD98.INI`/`MAPSELMD.INI`/`expandmd98.mix` 原子替换、
-       `ra2forge_install.json`、`…seal`、孤儿清理；拒绝：任何未登记目标文件…
+ 允许：备份槽写入、
+       `*.MAP`/`BATTLEMD98.INI`/`MAPSELMD.INI`/`expandmd98.mix`/**`ra2md.csf`** 原子替换、
+       `ra2forge_install.json`、`…seal`、孤儿清理；拒绝：任何未登记目标文件…
+ [W43-S3-D1] 新增 `ra2md.csf`：W40 A/E 证散装 CSF 覆盖 langmd.mix 且值驱动 UI；
+ W40 A 证合法最小 CSF 仍启动（19.34 s）；W40 D 证只有坏魔数才不启动 ⇒
+ 守卫形态是「完整性门禁」而非禁止投放、也不是「防启动失败」。
+ W41 v12 回归 57/57 已把 ra2md.csf 纳入安装/备份/卸载。
```

**目标 B**：`lead/next_re_20261112_r02/W38_version_guard_s1/EVIDENCE/guard_decision_table.json`

```diff
  {"entry_id": "E1", "state": "KNOWN_GOOD",
   "allow": ["BACKUP_SLOT_WRITE", "PACKAGE_FILE_REPLACE", "MANIFEST_WRITE",
-            "SEAL_WRITE", "ORPHAN_CLEANUP"],
+            "SEAL_WRITE", "ORPHAN_CLEANUP",
+            "<E1_KNOWN_GOOD.json 的 guard_decision_table_sync_token>"],
   "deny": [...], "require": [...], "exit_code": 0}
```

- `schema_version` 保持 `"w38-s1-1"`、`cells` 仍恰 **21** 格、其余 **20** 格字节不变（保持 `writeEntryPolicy.additionalProperties:false` 的 schema 合法性）。
- 同步 token 的精确值读 `s1_revision/E1_KNOWN_GOOD.json` 的 `guard_decision_table_sync_token` 字段（避免手写误差）。
- 修订后的完整副本：`s1_revision/guard_decision_table.json`；运行时副本：`ra2forge_patched_v13/ra2forge/data/guard_decision_table.json`（`S3_19h` 断言二者字节相同）。

**生成脚本（可复跑）**：`EVIDENCE/gen_s3_artifacts.py`（只读 W38 决策表 → 写 4 份副本 + `TRACK_B_gates.json`，`stdout`/`exit` 已留档）。

### 1.3 新增文件（无 diff 基线，直接落盘）

| 文件 | 作用 |
|---|---|
| `ra2forge/s3_contract.py` | 裁决常量 / E1 允许清单 / K1–K12 / `WRITE_ENTRY_COVERAGE`（64 条 HIGH/CRITICAL 审计行） |
| `ra2forge/version_guard.py` | W38-S1 `classify()`、`guard_write_entry()`、`guard_report.json`、退出码 20/21/22/23 |
| `ra2forge/feature_subset.py` | W42-S2 `resolve()` / `shipped()` / `validate_g4()` |
| `ra2forge/data/E1_KNOWN_GOOD.json` | D1 修订允许清单（运行时） |
| `ra2forge/data/guard_decision_table.json` | D1 同步决策表（运行时） |

---

## 2 · 校验（全部 `[本次实测]`）

### 2.1 向后兼容：不启用新开关时构建产物与 v12 逐字节相同

```powershell
cd lead\next_re_20261112_r02\W43_b_line_s3
python -B -X utf8 regress_dlc_v13.py S3_25
Get-Content out\SHA256_COMPAT_V13_V12.txt
```
期望：`files: 8  identical: 8  different: 0` / `VERDICT: IDENTICAL`。8 个产物逐一 SHA-256 对照见该文件。另有 `out\SHA256_COMPAT.txt`（v13 vs v11 只读参考，继承的 CSF_INST5）同样 MATCH。

### 2.2 完整回归：57 继承 + 25 S3

```powershell
cd lead\next_re_20261112_r02\W43_b_line_s3
python -B -X utf8 regress_dlc_v13.py
echo "exit=$LASTEXITCODE"
Get-Content out\SUMMARY.txt -TotalCount 6
```

期望（本卡实测）：
```
cases: 82  passed: 82  failed: 0
assertions: 714 passed / 0 failed
exit: 0
inherited v12 cases: 57
S3 cases: 25
```

### 2.3 五件事的定点校验

| 交付 | 命令 | 期望 |
|---|---|---|
| D1 | `python -B -X utf8 regress_dlc_v13.py S3_19` | 9/9，`ra2md.csf` 在允许清单、决策表同步、理由正确 |
| D2 csf 门禁 | `python -B -X utf8 regress_dlc_v13.py S3_8 S3_9 S3_20` | `MINIMAL_CSF_REFUSED`、v12 造最小 CSF / v13 零写拒绝、理由不含启动失败 |
| D3 resolve | `python -B -X utf8 regress_dlc_v13.py S3_1 S3_2 S3_17 S3_18` | 确定性子集、G4、形状自检、CLI `resolve` |
| D4 G3 警告 | `python -B -X utf8 regress_dlc_v13.py S3_21` | `warnings[]` 有 `G3_MID_COUPLING_NOTICE`、`hard_reject:false`、安装摘要可见 |
| D5 TRACK_B | `python -B -X utf8 regress_dlc_v13.py S3_22` | `adjudicated:true` / `is_clean_retail_gold:false` / schema 未扩展 |
| 守卫接线 | `python -B -X utf8 regress_dlc_v13.py S3_23` | exit 20/21、零写、`guard_report.json`、HIGH/CRITICAL 覆盖 |
| csf-out 归属 | `python -B -X utf8 regress_dlc_v13.py S3_16 S3_24` | E2b→E1、`CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1`、零写 |

### 2.4 源文件 delta / 工件生成器

```powershell
python -B -X utf8 EVIDENCE\gen_s3_artifacts.py
# 期望 stdout: TOTAL FAILURES: 0 ; exit 0
Get-Content out\V13_SOURCE_DELTA.json
# 期望: changed = 4 (builder/cli/csf/install.py), added = 5, 无 removed
```

### 2.5 隔离自证

```powershell
cd D:\Project\ra2-campaign-forge
git status --porcelain -- ra2forge/ ra2youli/ "lead/next_re_20261112_r02/W21*" ... "lead/next_re_20261112_r02/W42*"
(Get-Process -Name gamemd,game -ErrorAction SilentlyContinue | Measure-Object).Count
```
期望：scoped 快照只有开工前既有的 `??` 行（无 ` M`），进程数 `0`。留档：`EVIDENCE/git_scoped_after.txt`、`EVIDENCE/game_proc.txt`。

---

## 3 · 回滚

### 3.1 回滚 v13 → v12（构建产物与行为）

v13 的全部新能力都是 **opt-in**：只要不传 `--version-guard` / `--guard-report` / `--declared-baseline-id` / `--force-unknown`，也不调用 `resolve` / `guard-check` 子命令，行为与 v12 完全一致（§2.1 已实测）。因此**逻辑回滚 = 不启用新开关**，无需删除文件。

若要**物理回滚**到 v12：

```powershell
# 用 v12 只读参考覆盖（先确认目标路径）
$target = "<目标>\ra2forge_patched_v13"
$src    = "D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W41_csf_install\ra2forge_patched_v12"
# 校验目标确实是预期目录后再执行：
Resolve-Path -LiteralPath $target
# 删除 v13 副本内容并从 v12 重新复制（不触碰 W41 原件）
Remove-Item -LiteralPath $target -Recurse -Force
Copy-Item -LiteralPath $src -Destination $target -Recurse -Force
```

对 4 个已改源文件，`PATCH_RELATIVE.diff` 反向应用亦可（`git apply -R`，需先把 diff 里的 `W43_b_line_s3/...` 前缀映射到实际目标目录）。5 个新增文件（`s3_contract.py` / `version_guard.py` / `feature_subset.py` + 2 个 data JSON）直接删除即可，v12 无任一模块 import 它们。

### 3.2 回滚 D1 的 S1 修订

本卡**从未就地修改 W38**，所以「回滚」= 不使用 `s1_revision/` 副本、不应用 §1.2 的补丁；`W38_version_guard_s1/` 保持原样。若 Lead 已合入后需撤销：

- `VERSION_GUARD_CONTRACT.md`：把 §4 E1 行与 §1.2 允许清单段落中的 `` `ra2md.csf` `` 及 `[W43-S3-D1]` 注释块删除；
- `EVIDENCE/guard_decision_table.json`：从 `E1/KNOWN_GOOD` 的 `allow[]` 移除同步 token（`E1_KNOWN_GOOD.json` 的 `guard_decision_table_sync_token` 值），其余 21 格结构不动；
- 校验：决策表仍 21 格、`schema_version="w38-s1-1"`、E1/KNOWN_GOOD `allow` 恢复为原来的 5 项。

### 3.3 回滚 `TRACK_B_gates.json`

独立工件，删除 `W43_b_line_s3/TRACK_B_gates.json` 即可；不影响 `BASELINE.json`（本卡从未写/扩它，`S3_22d` 机检）。

---

## 4 · 注意事项（红线）

1. `PATCH_RELATIVE.diff` 的 `a/` 前缀指向 **W41 v12 只读参考**，应用时**不得**对 `W41_csf_install/` 写入；副本优先。
2. 所有新开关都是 opt-in，**不得**把「回归 82/82」读成「守卫默认已启用」或「行为正确」。
3. `s1_revision/` 是**待合入**补丁，不是已修改的 W38 文件；见 `DISAGREE.md D-W43-2`、`UNCOVERED.md U-W43-13`。
4. 回滚脚本在删除前必须 `Resolve-Path` 人工确认绝对路径（安全敏感操作）。
5. 真机行为验证不在本卡范围（`UNCOVERED.md U-W43-10`）。
