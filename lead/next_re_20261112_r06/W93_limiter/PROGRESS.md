# W93 PROGRESS · 限帧通道定谳 + ABBA 可跑脚本

> 离线卡 W93｜工作目录：`D:\Project\ra2-campaign-forge`｜交付目录：`lead\next_re_20261112_r06\W93_limiter\`
> 纪律：仅写本卡目录；禁止启动游戏、禁止注入/调试器、禁止改二进制。

- [2026-11-14T16:22+08:00] 启动 W93；只读复制 `ra2youli\ddraw.dll` (SHA-256 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`, 411,648 B) 与 `ra2youli\ddraw.ini` (SHA-256 `c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52`) 至 `W93_limiter\bin\` 并校验哈希全等。
- [2026-11-14T16:25+08:00] 任务一核心突破（`clamp=210` 定谳）：
  1. 实读 W86/W90 两份 `exp_rpm_framebeat.py`（字节全等，188 行）及 W90 `framebeat_console.log`：脚本直接 `read_u32(h, base + 0x5EE48)`，无偏移错、无换算，故运行期 `[base+0x5EE48]` 确实为 `210`；脚本唯一错误是注释/打印期待 `(期望 60/60/16)` 误把失败兜底常数当恒定值。
  2. 全量 `.reloc` + 反汇编定谳：`0x1005EDD0..0x1005EE6B`（`0x9C = 156` 字节）为全局 `DEVMODEA` 结构体，`0x1005EE48` 即 `+0x78` 偏移的 `DEVMODEA.dmDisplayFrequency`（当前显示器刷新率）。`0x10015E34..0x10015E50` 调用 `USER32!EnumDisplaySettingsA(NULL, -1, 0x1005EDD0)`（通过动态槽位 `[0x10053A58]`），成功则由系统直接写入 `0x1005EDD0` 整块结构体并跳过 `0x10015E83`（`mov [0x1005EE48], 0x3C` 仅是 `EnumDisplaySettingsA` 返回 0 时的失败兜底）。本机只读查询 `EnumDisplaySettingsA` 实测返回 `2560x1440, 32bpp, dmDisplayFrequency=210`。
- [2026-11-14T16:29+08:00] 完整反汇编 `sub_10006880`、`sub_10006A40`、`sub_10006AE0`、`sub_10017AC0` 及三条渲染循环写入点（D3D9 `0x1001B01A` / OpenGL `0x1001CD51` / GDI `0x1001D2D2`），并交叉核对 W90 `framebeat_1794640742.csv`（`cur_t` 全为 0，证实走 `WaitableTimer` 主支路而非 `timeGetTime+Sleep` 兜底支路）。
- [2026-11-14T16:37+08:00] 完成交付文档 `LIMITER.md`、`DISAGREE.md`、`UNKNOWNS.md`、`ABBA.md` 与 3 个只读/外部启停可运行脚本（`verify_ddraw_globals.py`、`abba_driver.py`、`abba_analyze.py`），并完成全部离线自测（`EVIDENCE/verify_ddraw_globals_selftest.txt`、`EVIDENCE/abba_selftest.txt`）。
- [x] W93 离线卡全部交付与自测完成。
