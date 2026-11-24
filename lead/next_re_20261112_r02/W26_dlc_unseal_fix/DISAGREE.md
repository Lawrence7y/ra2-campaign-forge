# DISAGREE · W26 与任务书 / W25 既有假定及测试断言的分歧记录

> 状态：**已完成并经全量实测印证（39/39 PASS，387/387 断言通过）**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02`

本卡未违背任何质量红线或任务目标（保留全部 39 用例、不放宽判据、不吞异常、绝不触碰真实目录）。以下 4 条为**对 W25 盘上证据与任务书前提的实测勘误**及**必要的严格升级修订**：

## 1. 勘误：W25 的 `R2` 失败不是“包文件没被回滚”，而是吞异常 + 排序错位混合问题

- **任务书前提**：引述 `R2` 失败断言认为“记录回滚失败中断了后面的包文件回滚，导致创建的包文件没有被移除”。
- **实测事实**（见 [W25 R2.log L10-28](../W25_dlc_unseal/out/R2.log#L10-L28) 及 W25 `install.py:1979-1995`）：
  1. W25 `install.py:1979-1980` 用 `except OSError: pass` **直接吞掉了**记录回滚异常，所以外层 `L1988` 的 `_rollback(game, undo)` **当时实际执行了**且已经移除了全部 4 个包文件（`R2.log` L24-28 盘面只剩 golden 4 文件 + 只读 `ra2forge_install.json`）。
  2. `regress_dlc_v8.py:2202` 失败的直接原因，是 `sha_tree()`（`L262`）按 `Path` 顺序排列，而 `tree_lines_without()`（`L294`）调用 `sorted(kept)` 按行首 SHA-256 hex 排序，导致同一批 4 个文件因行序不同判等失败（而 `R1` `L2126-2127` 对左右两边均调用 `tree_lines_without` 因此未暴露）。
  3. **但任务书指出的生产隐患真实存在**：`install.py:1979-1985` 吞掉 `[WinError 5]` 并撒谎称 `"the install record was rolled back ... nothing was left in the unsealed state"`，且记录恢复与 `_rollback` 缺乏独立的 `try/except` 隔离与复合失败汇总结构。
- **本卡处置**：同时修好生产代码（去除 `except OSError: pass`，双回滚分别 `try/except` 隔离并汇总所有失败，不再撒谎）与 `regress_dlc_v9.py` 的 `tree_lines_without()` 序一致性问题，并追加 `R2-compound` 复合三故障实测。

## 2. 对 `R1` / `R2` 中“旧谎言断言”的升级修订（同 W24→W25 改 `F7` 的先例）

- W25 `regress_dlc_v8.py` `L2107-2110`（`R1`）与 `L2192-2194`（`R2`）原本断言错误消息里必须出现 `"the install record was rolled back to its previous bytes"`（锁定 v8 吞异常并虚假宣称成功的行为）。
- W26 修复吞异常后，v9 诚实报告 `install record rollback FAILED (...)`，自然不再输出该虚假句子。
- 因此 `regress_dlc_v9.py` 将两条断言替换为**更强判据**：显式断言不存在 `"the install record was rolled back"` / `"nothing was left in the unsealed state"` / `"the package files are UNCHANGED"`，同时必须出现 `"install record rollback FAILED"`、`[WinError 5]` 与 `ra2forge_install.json`（完全同构于 W25 对 W24 `F7` 旧崩溃断言的升级做法）。

## 3. 勘误：W25 的 `F7` 失败出自夹具错配（同时仍加固了 `uninstall()` 全链路隔离）

- **实测事实**（[W25 F7.log L78-96](../W25_dlc_unseal/out/F7.log#L78-L96) 与 `regress_dlc_v8.py:1741-1771`）：
  - `F7` 在 `golden`（无 `Y.MAP`）上先装 `A1`（4 个 `created` 文件，无 `.bak`），再设 seal 只读，安装 `A2` 失败并回滚回 `A1`；随后 `uninstall()` 卸载的是 `A1`。因此正确动作本就是 `removed    Y.MAP`（同一用例 `L1768-1771` 断言盘面等于 `golden + stray seal` 已 PASS）。`L1744` 要求 `"restored   Y.MAP.ra2forge.bak -> Y.MAP"` 系夹具错配。
- **本卡处置**：
  1. 修正该断言检查真实的 A1 5 条 `removed` 动作，并**新增** `F7-bak-ro-seal`（含原文件 `.bak` 还原 + 只读 seal -> exit 10）与 `F7-manifest-ro`（只读 `ra2forge_install.json` 删清单失败 -> exit 1，`actions` 完整保留），`F7` 由 `22/23` 增补验证至 **`27/27` PASS**。
  2. 同时在 `uninstall()` 与 `_uninstall_legacy()` 为所有 `dest.unlink()` / `bak.unlink()` / `_stage_and_replace()` / `manifest_path.unlink()` / `listing.unlink()` 补齐隔离，并在 `_uninstall_exit_code()` 映射 `failed_step -> exit 1`。

## 4. 勘误：W25 回归套件中实为 3 项失败——补修漏列的 `V5`

- 任务书聚焦列出 `R2` 与 `F7` 两项，但引用 Lead 复跑数字为 **36 通过 / 3 失败**——第 3 项失败是 [W25 SUMMARY.txt L10](../W25_dlc_unseal/out/SUMMARY.txt#L10) 记录的 `FAIL V5 (8/12 checks)`。
- 根因是 `regress_dlc_v8.py:458` 将 `DRIVER` 覆盖成了 `v8_rollback_fault_driver.py`，导致 `case_V5` 全部被 usage exit 3 拒绝。
- 本卡将 `DRIVER` 恢复只读指向 `W24_dlc_seal_fault/tools/v7_fail_driver.py`，使 `V5` 从 `8/12 FAIL` 转回 `12/12 PASS`，整套达到 `39/39 PASS, 387/387 checks PASS, exit 0`。
