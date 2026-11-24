# W35 · UNKNOWNS.md — 未验证与待运行项

> 本卡因 `WinSta0\exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX` vs `WinSta0\Default` 桌面隔离阻塞，所有依赖主菜单交互的真机运行验证均处于 `[待运行验证]` 状态，未做任何推断冒充。

1. **散装 `MAPSELMD.INI` 能否让 `SkipMapSelect=no` 的 `ECH01.MAP` 过 `MapSelect::Init`**：`[待运行验证]`。未观测到点击 `GUI:Continue` 后是否仍弹 `MSG:UnableMapSelect`（「無法啟始選取地圖！」）、或成功进入交互式 MapSelect 界面。
2. **交互式 MapSelect 界面（`SkipMapSelect=no`）能否把玩家点选推进到 `ECH02.MAP`**：`[待运行验证]`。`[RA2F_ECH01_2004FB14]` 沿用了 `[Sov07]` 的 `MapVQ=NODMAP01.VQA` / `ClickMap=NODCLK01.PCX` / `Targets=1,190,100` 与 `[Sov01]` 同款颜色键 `2=RA2F_ECH02_1E0DEBE8`；`NODCLK01.PCX` 上颜色 2 的精确命中像素坐标与点击后是否正常加载 `ECH02.MAP` 均未在真机上观测。
3. **`SkipMapSelect=yes` 区分实验**：`[待运行验证]`。由于主测试未进入主菜单，未执行 `SkipMapSelect=yes` 变体，故无法在运行期实测验证 `[Scen+0x35A0]`（当前 stage 序号）在借用 `[SOV1]` 入口时的初值是否为 `0`（`Sov01`）及是否触发另一条失败分支。
4. **`frame=210` 时 `[Scen+0x125C]` 的实际运行期内容**：`[待运行验证]`。W31 提出在 `MapSelect::Init` 前 `[Scen+0x125C]` 可能保留 `ECH01.MAP` 或被先清空；本次未达到局内胜利屏，未通过只读 RPM 采到该时刻值。
5. **在 `WinSta0\Default` 桌面会话下重跑验证**：`tools/run_mapsel_live.py --mode skip_no` 已完成结构修复（保证超时清理 `pid`），待在交互式 `Default` 桌面运行以补齐全部真机观测证据（定时器 `[0xA8ED84]`、`EnumChildWindows`、内存 `ECH02.MAP` 命中、截图）。
