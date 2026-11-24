# S02-K2 · UNKNOWNS.md

| # | 未决项 | 现状 | 下一步 / 依据 |
|---|---|---|---|
| U1 | 290 个未具名 S02 靶中 289 个无法定名 | 保持 `sub_` | 0x77–0x7B 段 168 个为 MSVC CRT/C++ runtime 内部；YRpp 全量地址宏在此段仅 2 处（0x776D80 占位 / 0x777080 GetResource）。0x7C/0x7D 段 121 个中 25 个仅知"被具名 CRT 锚点调用"，无标准符号；**不造名**（纪律 8/16） |
| U2 | `vfprintf` `0x7CB302` | YRpp 具名 + 字节体吻合，但不在 atlas/coverage | 按"不在 atlas 区间内 ≠ 是函数"，须四项入口证据单独裁定后再作为新 entry；本卡不新增行 |
| U3 | `[0xB782C4]`（CRT malloc 堆句柄）写者 | 全 `.text` 0 写点 | 写点可能在 `_initterm` 表和 CRT 启动代码（3,944 项表，本卡只引用未重做）或 `.data` 初值；需专卡追 initterm 写点 |
| U4 | SBH `[0xB78B90]` 读者全集 | 仅见 init 清零写点 | 已给写点，读者未逐一列全 ⇒ 该字段降 `[静态推断]`，不虚标 |
| U5 | 靶内 S02 混入非 CRT 函数 | 如 `0x407780`（音频流线程）/`0x4095B0`（DirectSound 线程）/`0x53E6B0`（Game::ModalDialog）等被 coverage 归 S02 | 这些是 S02 "region guess" 桶的错归（真属 S19 音频/S09 UI），非本卡改写域；建议后续 M/审计卡按证据归位。本卡不改其 subsystem（避免连锁影响其它子系统计数） |
| U6 | qsort/bsearch/_ftol 跨子系统归位 | 本卡给出 `[已证]` 归位建议（CRT_NAMES.md B 表 + delta） | 改变 S19/S06 计数，须合并卡/审计协调；若审计否决则这 3 行 `(entry,subsystem)` 保留原状，仅采纳 `_nh_malloc` 靶内改名 |
| U7 | 两个额外 `SetUnhandledExceptionFilter`（`0x7D9FB1`/`0x7D9FC3`） | 判为 CRT 内部安装（非 except.txt 链） | 未逐字节追其 handler 参数；不影响 T4 主链（主安装点 `0x6BE084` 已逐字证实） |
| U7b | `0x6BB990` 尾跳桩用 `ecx` 取值（`mov eax,[ecx];mov edx,ecx;mov ecx,[eax];jmp 0x4C8FE0`），而 Windows 调 UnhandledExceptionFilter 时 `ecx` 非契约参数 | 字节链（push 0x6BB990 → SetUnhandledExceptionFilter → 尾跳 → 0x4C8FE0）逐字证实，但 `ecx` 来源未追 | 链的存在可证；`ecx` 语义（可能为 SEH 帧链 / 或该桩另有调用路径）未定 ⇒ "异常分发→0x6BB990"一步标 `[静态推断]`，写入点 `0x4C901C/0x4C9021` 本身为 `[已证]` |
| U8 | 递归计数 `[0x820E5C]` 精确语义 | 仅见 `0x4C8FFB inc` + `0x4C911C mov ...,0xFFFFFFFF` | 的行为侧（值 0 才写文件）已由 `0x4C9001 jne 0x4C9054` 证实；字段名"递归计数"为语义推断 `[静态推断]` |
| U9 | 升级硬规矩下的 `[已证]` 判定 | qsort/bsearch/_ftol 用 YRpp 外部符号表 + 字节体双证 | YRpp 符号表在本项目即 `[已证]` 命名依据（C01–C10 全 lineage）；字节体为独立第二通道，不复用他人结论 |
