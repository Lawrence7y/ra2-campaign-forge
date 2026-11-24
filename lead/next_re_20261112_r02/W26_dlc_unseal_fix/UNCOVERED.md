# UNCOVERED · W26（UNSEAL-FIX02）未覆盖与不确定项

> 状态：**已完成并按实测口径锁定**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02`

继承 W23 [VERIFY.md](../W23_dlc_verify/VERIFY.md) / `UNCOVERED.md`（§1–§4、§6–§8）与 W24 [UNCOVERED.md](../W24_dlc_seal_fault/UNCOVERED.md)（§3–§5）的既有前提，此处列本卡范围外或受限于环境/方法学的未覆盖项：

1. **非 Windows 平台实测（沿 W23/W24）**：
   - 本卡所有只读/写入阻塞（`os.chmod(S_IREAD)` 触发 `PermissionError [WinError 5]`、目录占槽导致生产 landing-slot 门禁拒绝、NTFS 大小写判定）均在 Windows + NTFS + Python 3.12.10 下实测。Linux/POSIX 下（对文件仅设 `0444` 仍允许同属主对所在可写目录 `unlink`，需改目录 `0555` 或 `chattr +i`）未实测。
2. **`R1` 复合故障（update 时旧 seal 只读 + 新清单回滚写失败）的自愈边界**：
   - 在 `R1` 中，旧 seal 保持未动、新清单因自身回滚写失败而留盘上，形成“新清单 + 旧 seal”不匹配对（`verify` exit 8、`uninstall` exit 8、`install` 因盘上是旧字节而与新清单不符触发 strict risks 拒绝）。本卡已保证**诚实报错并完整回滚所有包文件**，但不越权删除用户/只读清单文件，仍需清除只读并人工清理损坏记录对后重装——若未来需要专用诊断/恢复子命令需另立设计。
3. **非 `OSError` / 异步信号中断路径**：
   - [install.py:2002-2093](ra2forge_patched_v9/ra2forge/install.py#L2002-L2093) 与 `_rollback()`（[install.py:1681-1768](ra2forge_patched_v9/ra2forge/install.py#L1681-L1768)）已将回滚逻辑隔离范围扩大到 `Exception` 并在非 `Exception` 的 `BaseException` 时先尽力清理再重抛；本卡实测注入（`v8_rollback_fault_driver.py` 与 `v9_compound_rollback_driver.py`）触发的是真实 `PermissionError [WinError 5]` 与生产 landing-slot `OSError`、`v7_fail_driver.py` 模拟 `OSError`，未在进程级注入 `SIGINT`/`KeyboardInterrupt` 或任意自定义 `RuntimeError`。
4. **另一进程持句柄锁死（`WinError 32`）vs 只读属性（`WinError 5`）**：
   - 本卡通过 `S_IREAD` 触发真实 OS `PermissionError [WinError 5]`；另一进程打开锁文件触发的共享冲突（`WinError 32`）在 `uninstall()` / `_rollback()` 中走同一 `except OSError` 分支，但未另起锁进程做独立触发。
5. **部分卸载条目/旧版卸载子分支**：
   - 本卡已对 `uninstall()` 中 `dest.unlink()`、`bak.unlink()`、`_stage_and_replace(bak, dest, ...)` 与 `manifest_path.unlink()`（含 `F7-bak-ro-seal` 与 `F7-manifest-ro` 实测）以及 `_uninstall_legacy()` 对应路径补齐隔离；其中 `_uninstall_legacy()` 中 `bak.unlink()` 单独失败及“主循环条目 `dest.unlink()` 半途失败但后续条目继续移除”两分支为代码审核路径，未在 `regress_dlc_v9.py` 中单拆独立用例。
6. **`uninstall` `actions` 既有契约边界**：
   - `C1` / `U6b` 锁定了 `actions` 仅列出实际完成动作（不向 `actions` 写入假 `removed`/`restored`，失败写入 `warnings`，`--json` 保持既有 9 键）。若未来需要结构化 `failed_actions[]` 列表，需作为 schema 升级另立卡片。
