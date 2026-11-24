# UNSEAL_FIX · W26（UNSEAL-FIX02：回滚隔离/显式报错 + uninstall actions 完整性 + 39 用例闭环，TOOL_VERSION 0.9）

> 状态：**已完成并验证通过（39/39 用例全 PASS，387/387 断言通过，脚本 exit 0）**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02` ｜ 仓库基线 `main@3872ef6`
> 基于：`W25_dlc_unseal/ra2forge_patched_v8/`（`TOOL_VERSION = 0.8`）→ 本卡演进副本 `W26_dlc_unseal_fix/ra2forge_patched_v9/`（`TOOL_VERSION = 0.9`）。

---

## 1. W25 起点复核与真实根因定位（`文件:行`）

对 W25 现场（`W25_dlc_unseal/ra2forge_patched_v8/` 与 `W25_dlc_unseal/regress_dlc_v8.py`、`W25_dlc_unseal/out/`）复核后，W25 实盘存在 3 个失败项（`SUMMARY.txt`: 36 通过 / 3 失败：`V5` 8/12、`F7` 22/23、`R2` 12/13，共 376/6 断言），其生产代码与回归脚本根因定位如下：

### 1.1 缺陷 1（`R1` / `R2` 与 `install.py` 回滚隔离及异常传播）

1. **生产代码根因**（`W25_dlc_unseal/ra2forge_patched_v8/ra2forge/install.py`）：
   - `L1970-1985`：`write_install_seal(game, manifest)` 失败后，记录恢复（`manifest_path.unlink()` 或 `_stage_text_and_replace(prev_record_text, manifest_path, "install record restore")`）虽尝试执行，但 **`L1979-1980` 用 `except OSError: pass` 静默吞掉了记录恢复异常**。
   - 紧接着 **`L1981-1985` 无条件抛出误导性错误**：`"the install record was rolled back to its previous bytes, the package files are UNCHANGED; nothing was left in the unsealed state"`——即便记录恢复因 `[WinError 5]` 失败、新清单仍站在盘上（`R1`/`R2` 即因此留下 `verify exit 8` 状态），异常仍谎称记录已还原、文件未变。
   - 同时，错误构造（`L1981`）先于外层 `L1988` 的 `_rollback(game, undo)` 发生，记录回滚与包文件回滚未能作为两个独立 `try/except` 块各自隔离并汇总在同一错误报告中。
   - 此外在 `_rollback()`（`L1702-1708, L1739-1740`）中：其一，当 `_stage_and_replace(bak, dest, ...)` 成功还原目标文件但后续 `bak.unlink()` 抛出异常时，异常被 `L1739` 笼统记为 `rollback of <name> failed`，丢失“目标文件已还原”的事实；其二，循环仅捕获 `OSError`，其他 `Exception` 会中断其余包文件的回滚。
2. **测试脚本耦合问题**（`W25_dlc_unseal/regress_dlc_v8.py`）：
   - `L2202`（`R2`）：`R2.log` L11-15、L24-28 实证 v8 中 `_rollback` 已移除 4 个包文件（仅剩 golden 4 文件 + 只读 `ra2forge_install.json`），失败的直接原因是 `sha_tree()`（`L262`）按 `Path` 顺序输出，而 `tree_lines_without()`（`L294`）调用了 `sorted(kept)`（按 SHA-256 十六进制首字符排序），导致字符串顺序不一致（同文件 `R1` `L2126-2127` 对左右两侧同时调用 `tree_lines_without` 才未暴露此问题）。
   - `L2107-2110`（`R1`）与 `L2192-2194`（`R2`）：W25 原测试断言反向锁定了旧谎言 `"the install record was rolled back to its previous bytes"`。修复吞异常后必须同步升级为对诚实失败报错的校验。

### 1.2 缺陷 2（`F7` 与 `uninstall` 的 `actions` 完整性）

1. **测试脚本错位**（`W25_dlc_unseal/regress_dlc_v8.py:1741-1746`）：
   - `case_F7` 先在 `golden`（不含 `Y.MAP`）安装 `pkgA_v1`（4 个文件均 `action="created", backup=null`），再设 seal 只读，安装 `pkgA_v2` 失败并回滚回 `pkgA_v1` 状态；随后 `c.uninstall()` 卸载的是 `pkgA_v1`，`F7.log` L78-85 输出是 `removed    Y.MAP`（`L1769` `got_lines == want_lines` 已通过）。`L1744` 期望 `"restored   Y.MAP.ra2forge.bak -> Y.MAP"` 属于 W25 夹具错配。
2. **生产代码收尾容错加固点**（`W25_dlc_unseal/ra2forge_patched_v8/ra2forge/install.py`）：
   - `uninstall()` 的 `L2256-2272` 已对 `SEAL_NAME.unlink()` 做了隔离，但主循环中的 `dest.unlink()`（`L2184`）、`bak.unlink()`（`L2198` 与 `L2220`）、`_stage_and_replace(bak, dest, ...)`（`L2219`）与 `manifest_path.unlink()`（`L2237`），以及 `_uninstall_legacy()` 里的恢复/删除步骤（`L2437-2438`、`L2546-2547`、`L2568`）仍为裸调用：一旦任一文件/备份/清单删除遇到 `WinError 5` 等 `OSError`，立即中断函数并在 `cli.py:314` 退回 exit 1 stderr 报错，**此前已完成还原/移除的 `actions` 报告全部丢失**，且后续条目也被跳过。
   - 同时当 `_stage_and_replace(bak, dest, None, "restore")`（`L2219`）成功而紧接的 `bak.unlink()`（`L2220`）失败时，在旧代码中甚至连 `restored   <bak> -> <dest>` 都未加入 `actions` 就崩溃。

### 1.3 附带发现的 W25 回归脚本缺陷（`V5`）

- `W25_dlc_unseal/regress_dlc_v8.py:458` 将 `DRIVER` 覆盖为 `W25_ROOT / "tools" / "v8_rollback_fault_driver.py"`（注释误称 `unused in W25`），使 `case_V5`（`L700/708/720`）以 usage exit 3 失败（8/12 checks）。恢复为只读引用 `W24_ROOT / "tools" / "v7_fail_driver.py"` 即可恢复原 3 次真实写失败注入。

---

## 2. 修复设计（v8 → v9，附具体 `文件:行`）

### 2.1 [install.py](ra2forge_patched_v9/ra2forge/install.py)（434 行处为常量区，终态 2764 行）

1. **`TOOL_VERSION = "0.9"`**（[install.py:383](ra2forge_patched_v9/ra2forge/install.py#L383)）。
2. **`_rollback(game, undo, errors=None)` 逐项与分步隔离**（[install.py:1681-1768](ra2forge_patched_v9/ra2forge/install.py#L1681-L1768)）：
   - 保持 `_rollback(game, undo)` 签名前向兼容，新增可选 `errors: list[str] | None = None`。
   - 循环体改用 `try/except Exception as exc`（不再只捕 `OSError`），安全解析 `item_name`（优先 `u.get("name")` 或 `u.get("step").get("name")`）。
   - 对 `backup == "create"`：先执行 `_stage_and_replace(bak, dest, None, "rollback-restore")` 并记录 `rolled back <name> (restored from <slot>)`，再以独立 `try/except Exception` 执行 `bak.unlink()`，若删除临时备份失败则追加 `rollback cleanup of <slot> failed: ...` 并同时写入 `lines` 与 `errors`，确保“目标已还原”与“删 `.bak` 失败”互不掩盖。
   - 所有缺失备份/无法还原分支与异常分支均同步写入 `lines` 与 `errors`。
3. **`install_package` 记录回滚与包文件回滚完全解耦并诚实聚合**（[install.py:1906, 1998-2093](ra2forge_patched_v9/ra2forge/install.py#L1998-L2093)）：
   - 外层 `try` 入口新增 `rolled_back = False`（`L1906`），防止先做隔离回滚后在外层 `except BaseException` 重复调用 `_rollback`。
   - 当 `write_install_seal(game, manifest)` 抛出 `seal_exc`：
     1. **块 1（记录回滚）**：独立 `try/except Exception as r_exc` 执行 `manifest_path.unlink()`（fresh）或 `_stage_text_and_replace(prev_record_text, manifest_path, "install record restore")`（update），移除 `except OSError: pass`。
     2. **块 2（包文件回滚）**：无论 `rec_err` 是否发生，独立 `try/except Exception as f_exc` 调用 `_rollback(game, undo, rollback_errors)`，设 `rolled_back = True`。
     3. 若 `seal_exc` 为非 `Exception` 的 `BaseException`（如 `KeyboardInterrupt`），在完成两步尽责清理后原样 `raise`。
     4. **仅当 `rec_err is None and not rollback_errors`**（纯粹单点 seal 写失败、全部回滚干净）时，保留原单故障文本 `"the install seal ... could not be written (...) - the install record was rolled back to its previous bytes, the package files are UNCHANGED; nothing was left in the unsealed state"` 及明细，确保 `F1`–`F7` 单故障与正常路径零回归。
     5. **否则（任意回滚失败）**：禁止宣称记录已回滚或包文件未变；在同一个 `OSError` 中逐项聚合：`seal` 写失败原因 + `install record rollback FAILED (could not ...: <rec_err>; ...)`（或记录已干净回滚说明）+ `package file rollback had failures (N): ...`（或包文件已干净回滚说明）+ `best-effort rollback` 逐文件报告。
4. **`uninstall()` 与 `_uninstall_legacy()` 动作完整性与收尾故障隔离**（[install.py:2134-2446, 2448-2755](ra2forge_patched_v9/ra2forge/install.py#L2280-L2446)）：
   - 主循环：
     - `dest.unlink()`（`L2283-2290`）：`OSError` 写入 `warnings`、`refused = True`、继续处理其余条目。
     - `original_absent` 下的 `bak.unlink()`（`L2304-2314`）：`OSError` 写入 `warnings`、`refused = True`。
     - 常规恢复（`L2332-2348`）：`_stage_and_replace(bak, dest, None, "restore")` 独立保护（失败记 `warnings`、`refused = True`、`continue`）；**一旦还原成功即先写 `actions.append(f"restored   {backup} -> {name}")`**，再以独立 `try/except OSError` 执行 `bak.unlink()`，确保 `.bak` 只读不丢失已完成的还原动作。
   - 清单与 seal 清理（`L2364-2413`）：
     - `manifest_path.unlink()` 以独立 `try/except OSError` 隔离：若删除清单失败，置 `record_unlink_failed = True`，`manifest_removed = False`，写入明示 `warnings`（保留所有已完成 `actions`），且**禁止**继续删除 `SEAL_NAME`（因清单仍在盘上，不得制造无 seal 记录状态）。
   - 三态与失败归因（`L2418-2446`）：新增 `failed_step`（仅在 `manifest_unlink` / `legacy_manifest_unlink` 时写入内部报告 dict；`cli.py _uninstall_json` 仍输出完全相同的 9 个 JSON 键），保持既有正常/只读 seal（exit 10）/seal gate（exit 7/8）/record_refused（exit 0）语义零变化。
   - `_uninstall_legacy()`（`L2448-2755`）：同步隔离两处 `_stage_and_replace` + `bak.unlink()` 与末尾 `listing.unlink()`，返回是否清单 unlink 失败，绝不丢弃已完成 `actions`。

### 2.2 [cli.py](ra2forge_patched_v9/ra2forge/cli.py)（终态 468 行）

- [cli.py:62-95](ra2forge_patched_v9/ra2forge/cli.py#L62-L95)：同步修订 `UNINSTALL_EXIT_CODES_TEXT` 与 `UNINSTALL_EXIT_MEANINGS[1]` 中对 exit 1 与 `"failed"` 状态的说明，覆盖“条目处理完毕但清单移除失败（exit 1 且完整保留 `actions`）”。
- [cli.py:101-110](ra2forge_patched_v9/ra2forge/cli.py#L101-L110)：`_uninstall_exit_code(report)` 在 `seal_missing/seal_mismatch`（7/8）之后、`completed_with_warnings`（10）之外新增 `if report.get("failed_step"): return 1`。

### 2.3 [regress_dlc_v9.py](regress_dlc_v9.py) & [tools/v9_compound_rollback_driver.py](tools/v9_compound_rollback_driver.py)

- 完整保留 **39 个用例**，一条不减、判据零放宽；新增 3 个复合场景子验证以验证最严苛隔离要求：
  - `V5`：修正 `DRIVER = W24_ROOT / "tools" / "v7_fail_driver.py"`（12/12 PASS）。
  - `P1`：工具版本断言升至 `"0.9"`（与 `TOOL_VERSION` 一致）。
  - `F7`：纠正 A1 清单实态的 `removed` 断言，并新增 `F7-bak-ro-seal`（含 `.bak` 还原 + 只读 seal -> exit 10，actions 含 `restored` + `removed`）与 `F7-manifest-ro`（只读 `ra2forge_install.json` -> exit 1，`status="failed"`，全部 4 条文件动作仍完整保留在 `--json actions` 且未误删 seal）。
  - `R1` / `R2`：修正 `tree_lines_without()` 保持 `sha_tree` 路径序；升级 `R1`/`R2` 错误输出断言为严格校验（禁绝 `"the install record was rolled back"` 谎言、必须显式报 `"install record rollback FAILED"` + `[WinError 5]`）；并在 `R2` 末尾通过 [tools/v9_compound_rollback_driver.py](tools/v9_compound_rollback_driver.py) 新增 `R2-compound`（封条目录占槽 + 清单只读 + `X.MAP` 只读同时发生，实证 `BATTLEMD98.INI` / `Y.MAP` / `expandmd98.mix` 仍全部干净回滚，且两条失败汇总在同一异常输出中）。

---

## 3. 退出码表（与 `--help` 及 [W23 VERIFY.md](../W23_dlc_verify/VERIFY.md) 同族口径严格一致）

### 3.1 `verify` 退出码（与 `python -m ra2forge verify --help` 及 `W23/VERIFY.md` 一字不差）

```text
exit codes:
  0  everything ok (orphans, if any, are listed but do not change the
     code; a directory with no install record also verifies as 0 -
     nothing to check)
  1  the check itself failed to run (unexpected error)
  2  command-line usage error (argparse)
  5  manifest structure unusable (not JSON / required fields missing)
  6  package_digest mismatch - the manifest's own records are not
     self-consistent
  7  install seal MISSING for a seal-era manifest (tool >= 0.7)
  8  install seal MISMATCH / corrupt / aliased
  9  drift: recorded files changed or missing on disk
when several classes apply, the exit code is the MOST SEVERE one
(5 > 6 > 7/8 > 9); every finding is still listed. Old manifests (tool
< 0.7, no seal) verify in degraded mode: warned, still fully run.
The seal detects accidents, not attacks - it is not anti-tamper.
```

### 3.2 `uninstall` 退出码（与 `python -m ra2forge uninstall --help` 一字不差）

```text
exit codes (uninstall):
  0  completed - the recorded lifecycle was processed (or there was
     nothing to remove). Two documented sub-cases also exit 0: entry
     refusals keep the record for a later retry (each one listed as a
     warning; behavior unchanged since tool 0.7), and a non-qualifying
     install-record slot is not acted on (report status "failed", see
     the warning)
  1  the uninstall itself failed unexpectedly (error on stderr, or
     post-entry record removal failed - actions remain in the report)
  2  command-line usage error (argparse)
  7  uninstall REFUSED: install seal MISSING for a seal-era manifest
     (tool >= 0.7) - nothing removed, nothing restored, record kept
  8  uninstall REFUSED: install seal MISMATCH / corrupt / aliased
  10 partial completion (report status "completed_with_warnings"):
     the main uninstall COMPLETED - the record was deleted and every
     recorded file was processed - but the FINAL cleanup failed (the
     install seal could not be removed). The warning names the stray
     seal file and the recovery (clear the obstacle and delete it by
     hand, or re-run the install of the SAME package and uninstall
     again). New in tool 0.8 (UNSEAL-FIX01): tool 0.7 exited 1 here
     and lost the actions report
report status values (report dict / uninstall --json "status"):
  completed - the command ran to its defined end (see exit 0 notes)
  completed_with_warnings - main flow done, final cleanup failed
  failed - refused: seal gate (exit 7/8) or a non-qualifying record
           slot (exit 0, unchanged since tool 0.7), or post-entry
           record removal failed (exit 1, actions preserved in report)
```

---

## 4. 修复前后实测对照（均取自磁盘原始日志）

### 4.1 缺陷 1：`R2`（`W25/out/R2.log` → `W26/out/R2.log`）与 `R1` + 复合三故障

**修复前（W25 `out/R2.log` L9-28，exit 1，`12/13` FAIL）**：
```text
--- exception message ---
the install seal (ra2forge_install.json.seal) could not be written (the install seal slot was refused right before the write: install seal ra2forge_install.json.seal exists but is not a regular file - refusing to use it) - the install record was rolled back to its previous bytes, the package files are UNCHANGED; nothing was left in the unsealed state
  install aborted mid-write; best-effort rollback of what this run wrote:
    rolled back expandmd98.mix (created file removed)
    rolled back Y.MAP (created file removed)
    rolled back X.MAP (created file removed)
    rolled back BATTLEMD98.INI (created file removed)
--- end exception message ---
...
[assert] R2: the error CLAIMS the record was rolled back (over-claim) ... PASS
[assert] R2: package files rolled back (created files removed) - the tree is exactly golden + the standing record ... FAIL
```
（注：W25 既在 `install.py:1979` 用 `except OSError: pass` 吞掉 `[WinError 5]` 并撒谎称“record was rolled back”，又因 `tree_lines_without()` 排序错位导致 `R2` 第 6 条断言 FAIL。）

**修复后（W26 `out/R2.log` L9-23, L102-112，exit 1，`14/14` PASS）**：
```text
--- exception message ---
the install seal (ra2forge_install.json.seal) could not be written (the install seal slot was refused right before the write: install seal ra2forge_install.json.seal exists but is not a regular file - refusing to use it) - install record rollback FAILED (could not remove ra2forge_install.json: [WinError 5] 拒绝访问。: 'D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261112_r02\\W26_dlc_unseal_fix\\sandbox\\R2\\game\\ra2forge_install.json'; ra2forge_install.json may be left standing without a matching ra2forge_install.json.seal); package files rolled back cleanly (all other writes of this run undone)
  install aborted mid-write; best-effort rollback of what this run wrote:
    rolled back expandmd98.mix (created file removed)
    rolled back Y.MAP (created file removed)
    rolled back X.MAP (created file removed)
    rolled back BATTLEMD98.INI (created file removed)
--- end exception message ---
[assert] R2: record-rollback failure is explicitly reported (never swallowed) with real WinError 5, and package rollback ran cleanly ... PASS
[assert] R2: package files rolled back (created files removed) - the tree is exactly golden + the standing record ... PASS
```
**追加 `R2-compound`（记录回滚失败 + `X.MAP` 回滚同时失败，`out/R2.log` L102-112）**：
```text
error: the install seal (ra2forge_install.json.seal) could not be written (...) - install record rollback FAILED (could not remove ra2forge_install.json: [WinError 5] 拒绝访问。: '...\\ra2forge_install.json'; ra2forge_install.json may be left standing without a matching ra2forge_install.json.seal); package file rollback had failures (1): rollback of X.MAP failed: [WinError 5] 拒绝访问。: '...\\X.MAP'
  install aborted mid-write; best-effort rollback of what this run wrote:
    rolled back expandmd98.mix (created file removed)
    rolled back Y.MAP (created file removed)
    rollback of X.MAP failed: [WinError 5] 拒绝访问。: '...\\X.MAP'
    rolled back BATTLEMD98.INI (created file removed)
```
（同样在 `R1` 更新双故障中，旧谎言 `"the install record was rolled back"` 已消失，改为 `install record rollback FAILED (could not restore ra2forge_install.json to its previous bytes: [WinError 5] ...); package files rolled back cleanly`，`17/17 PASS`。）

### 4.2 缺陷 2：`F7`（`W25/out/F7.log` → `W26/out/F7.log`）

**修复前（W25 `out/F7.log` L78-96，exit 10，`22/23` FAIL）**：
```text
uninstalled from D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W25_dlc_unseal\sandbox\F7\game:
  removed    expandmd98.mix
  removed    Y.MAP
  removed    X.MAP
  removed    BATTLEMD98.INI
  removed    ra2forge_install.json
...
[assert] F7 (W25): actions intact - every recorded file restored/removed and the record deleted ... FAIL
```
（主 loop 无异常，实际卸载的是 A1 的 4 个 `created` 文件；且生产代码中主循环与清单 unlink 仍缺隔离。）

**修复后（W26 `out/F7.log` L78-90, L170-222，exit 10 / exit 1，`27/27` PASS）**：
1. 原 `F7` 主场景 exit 10，全部 4 个 A1 记录文件 + `ra2forge_install.json` 删除完整输出，`27/27` PASS。
2. 追加 `F7-bak-ro-seal`（含原 `X.MAP` 备份 + 只读 seal）：exit 10，`actions` 完整包含 `restored   X.MAP.ra2forge.bak -> X.MAP` 与其余 `removed` 行、`removed    ra2forge_install.json`。
3. 追加 `F7-manifest-ro --json`（只读 `ra2forge_install.json` 导致删清单本身 `[WinError 5]`）：
   `exit_code: 1`, `status: "failed"`, `actions` **完整保留** `["removed    expandmd98.mix", "removed    Y.MAP", "removed    X.MAP", "restored   X.MAP.ra2forge.bak -> X.MAP", "removed    BATTLEMD98.INI"]`，未误删清单与 seal，`warnings` 显式列出 `[WinError 5]`。

### 4.3 附带修复：`V5`（`W25/out/V5.log` → `W26/out/V5.log`）

- **修复前**：W25 `out/V5.log` 因 `DRIVER` 错指向 `v8_rollback_fault_driver.py`，3 次驱动注入全部直接以 exit 3 用法拒绝（`8/12` FAIL）。
- **修复后**：W26 `out/V5.log` 恢复调用 `W24/tools/v7_fail_driver.py`，`V5a`（`X.MAP`）、`V5b`（`Z.MAP`）、`V5c`（`@record`，重装回被删孤儿 `X.MAP`）全部真执行并在回滚后目录与快照逐字节一致，`12/12` PASS。

### 4.4 正常路径零回归证据（`R0`、`U2`、`C1`、`C2`、`U1–U6`）

- **`R0`**：`out/R0.log` 确认坏模式拒绝 exit 3、不改目录；随后的普通 `install` exit 0，写盘 `ra2forge_install.json` + `.seal`。
- **`U2`**：`out/U2.log` 确认正常 `uninstall` exit 0、**无任何 warning**、`removed ra2forge_install.json.seal` 与清单双双移除、`status: completed (exit code 0)`、目录逐字节回归 `golden`。
- **`C1` / `C2`**：与 W21 `v0.5` 参考输出及终态（`C2` 除外 v0.5 不认识的 seal 文件）逐字节一致。
- **`U1–U6`**：`U1`（9/9）、`U2`（6/6）、`U3`（8/8）、`U4`（6/6）、`U5`（7/7）、`U6`（23/23）全部 PASS。

---

## 5. 39 用例回归结果总表（`out/SUMMARY.txt`，脚本退出码 `0`）

> 总计：**cases: 39 ｜ passed: 39 ｜ failed: 0 ｜ assertions: 387 passed / 0 failed**

| 用例 | 断言 | 结论 | 日志 | 用例 | 断言 | 结论 | 日志 |
|---|---|---|---|---|---|---|---|
| `P0` | 13/13 | PASS | [P0.log](out/P0.log) | `S6` | 10/10 | PASS | [S6.log](out/S6.log) |
| `V1` | 10/10 | PASS | [V1.log](out/V1.log) | `S7` | 10/10 | PASS | [S7.log](out/S7.log) |
| `V2` | 3/3 | PASS | [V2.log](out/V2.log) | `S8` | 7/7 | PASS | [S8.log](out/S8.log) |
| `V3` | 4/4 | PASS | [V3.log](out/V3.log) | `F0` | 9/9 | PASS | [F0.log](out/F0.log) |
| `V4` | 7/7 | PASS | [V4.log](out/V4.log) | `F1` | 11/11 | PASS | [F1.log](out/F1.log) |
| `V5` | 12/12 | PASS | [V5.log](out/V5.log) | `F2` | 9/9 | PASS | [F2.log](out/F2.log) |
| `V6` | 14/14 | PASS | [V6.log](out/V6.log) | `F3` | 10/10 | PASS | [F3.log](out/F3.log) |
| `P1` | 13/13 | PASS | [P1.log](out/P1.log) | `F4` | 10/10 | PASS | [F4.log](out/F4.log) |
| `P2` | 9/9 | PASS | [P2.log](out/P2.log) | `F5` | 12/12 | PASS | [F5.log](out/F5.log) |
| `P3` | 5/5 | PASS | [P3.log](out/P3.log) | `F6` | 9/9 | PASS | [F6.log](out/F6.log) |
| `P4` | 11/11 | PASS | [P4.log](out/P4.log) | `F7` | 27/27 | PASS | [F7.log](out/F7.log) |
| `C1` | 6/6 | PASS | [C1.log](out/C1.log) | `U1` | 9/9 | PASS | [U1.log](out/U1.log) |
| `C2` | 9/9 | PASS | [C2.log](out/C2.log) | `U2` | 6/6 | PASS | [U2.log](out/U2.log) |
| `T4` | 3/3 | PASS | [T4.log](out/T4.log) | `U3` | 8/8 | PASS | [U3.log](out/U3.log) |
| `S1` | 14/14 | PASS | [S1.log](out/S1.log) | `U4` | 6/6 | PASS | [U4.log](out/U4.log) |
| `S2` | 9/9 | PASS | [S2.log](out/S2.log) | `U5` | 7/7 | PASS | [U5.log](out/U5.log) |
| `S3` | 4/4 | PASS | [S3.log](out/S3.log) | `U6` | 23/23 | PASS | [U6.log](out/U6.log) |
| `S4` | 8/8 | PASS | [S4.log](out/S4.log) | `R0` | 4/4 | PASS | [R0.log](out/R0.log) |
| `S5` | 15/15 | PASS | [S5.log](out/S5.log) | `R1` | 17/17 | PASS | [R1.log](out/R1.log) |
|  |  |  |  | `R2` | 14/14 | PASS | [R2.log](out/R2.log) |

---

## 6. 隔离与红线核验

- `git status --porcelain -- ra2forge/ ra2youli/ lead/next_re_20261112_r02/W21_dlc_orphan/ lead/next_re_20261112_r02/W22_dlc_pkgid/ lead/next_re_20261112_r02/W23_dlc_verify/ lead/next_re_20261112_r02/W24_dlc_seal_fault/ lead/next_re_20261112_r02/W25_dlc_unseal/` 确认：
  - 仓库 `ra2forge/` 与真实目录 `D:\Project\ra2-campaign-forge\ra2youli\` **零修改**；
  - `W21–W25` 既有目录 **零修改**（仅作为未跟踪历史卡片目录列出，`W22_dlc_pkgid/` 不在 git 状态中变化且未做任何写入）；
  - 全部测试写入隔离在 `lead/next_re_20261112_r02/W26_dlc_unseal_fix/sandbox/`，唯一涉及 `ra2youli/` 的接触仅为原有 `C1/P3/S7` 测试对 `ra2youli/ra2forge_install.json` 的只读复制。
- 补丁 `PATCH_RELATIVE.diff`（119,339 字节，纯相对路径 `a/ra2forge/*` → `b/ra2forge/*`）经 `tools/make_patch.py` 在临时沙箱回放后 12/12 文件 SHA-256 100% 匹配，且在仓库根 `git apply --check` 通过。
