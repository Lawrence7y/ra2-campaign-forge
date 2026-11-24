# W35 · DISAGREE.md — 与既有流程/环境预期的差异记录

1. **与 `W27_campaign_live/CAMPAIGN_LIVE.md` 运行环境假设的差异（环境条件变化）**：
   - W27（2026-11-13 13:34–14:39）在同机上使用 `WMI Win32_Process.Create` + `EnumWindows` + `ImageGrab.grab()` 成功驱动并截取 `gamemd.exe` 画面。
   - 本卡（2026-11-13 18:23–18:30）执行时，即便使用 `BypassSandbox: true`，代理命令执行线程仍处于 `WinSta0\exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX` 桌面，而 WMI 创建的 `gamemd.exe` 位于 `WinSta0\Default` 桌面；由此导致 `EnumWindows` 返回 0 个窗口、`ImageGrab.grab()` 抛出 `OSError: screen grab failed`。
   - 此差异属于运行时环境/桌面隔离变化，不推翻 W27 在 `WinSta0\Default` 会话下的历史实测记录，但证明当前代理终端无法跨桌面驱动 WMI 启动的 GUI 进程。

2. **与 `W27` `live_lib.py` / `phase_p3_D2_chains.py` 脚本细节差异（工程修复）**：
   - W27 `phase_p3_D2_chains.py` 的 `launch_one()` 在 `wait_main_menu()` 超时抛异常时，`pid` 尚未赋回 `main()` 局部变量，导致 `finally` 无法自动关闭已拉起的 `gamemd.exe`。本卡首跑即遇到该问题（后由 `taskkill /F /PID 35448` 清理），并在 `W35_mapselmd_live/tools/run_mapsel_live.py` 中改用 `state` 字典提前登记 `pid`/`hwnd`/`hproc` 修复。
   - W27 `CAMPAIGN_LIVE.md §2` 记述 `uninstall --json` 与 `verify` 命令由 `W26_dlc_unseal_fix/ra2forge_patched_v9/` 提供；实测在仓库根目录直接用 `PYTHONPATH` 跑 `python -m ra2forge` 会因 CWD 优先命中仓库根尚未打补丁的 `ra2forge/`（无 `verify` / `--json`），必须 `cd` 至 `ra2forge_patched_v9/` 执行（已照此执行并留日志）。

3. **与 `LEAD_VERDICT` / `MAPSELMD_SPEC.md` 核心技术结论**：
   - 本卡**未发现与两份规格冲突的实测证据**；`ra2bench\ra2md.mix` 偏移 `0x71D050` 长度 `5,573 B` 的 SHA-256 `074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52` 复核完全一致 `[本次实测]`。推进链本身因桌面隔离未能真机完测。
