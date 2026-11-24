# W19 / RE-N04h 安全与授权记录（LoadBench U800 CPU 负载对照）

run_id = NEXT_RE_20261112_R02 · 卡 = RE-N04h · 日期 = 2026-11-13
执行代理 = W19-load-U800-subagent（会话授权：用户已授予全部动作与自行裁决）

## 1. 实例互斥锁
- 开工状态：`lead\next_re_20261112_r02\.game_instance.lock` `owner=lead`（05:39:57+08:00 W18 收尾恢复）→ 可认领。
- 认领：探针 S0 写入 `owner=W19-load-U800-subagent`（05:55:04+08:00），purpose=「W19 RE-N04h U800 单位/步兵维度 CPU 负载对照 进行中 (attempt 1)」。
- 收尾：探针 `finally` 链恢复 `owner=lead`（结果见 RUNLOG.md 收尾核对）。
- 启动前残留核对：`Get-Process -Name gamemd` = 0 个（05:54 实测）→ 允许启动。

## 2. 授权动作（本卡实际使用）
| 动作 | 授权 | 本卡使用 |
|---|---|---|
| 启动 `ra2youli\gamemd.exe`（WMI 分离启动，父=WmiPrvSE） | 允许 | ✔ pid=41640 |
| `ReadProcessMemory` 只读 12 地址 | 允许 | ✔（frame/mode/g1..g4/A8E9A0/ABCD58/exitstate/A8ED50/B0CE88/87E8E0 + 代码签名 0x55DE4F） |
| `OpenThread`+`GetThreadTimes`/`QueryThreadCycleTime` | 允许 | ✔ 窗口线程 tid=2124 每拍；观察者 1Hz 全线程 |
| 枚举窗口/线程、发消息/点控件（导航/选图/开局） | 允许 | ✔ SinglePlayer→Skirmish→ChooseMap→UseMap→StartGame；LB_SETCURSEL(96) |
| 采样段输入 | **必须为零** | ✔（S3 置前后零输入；观察者只读枚举） |

## 3. 禁止动作（本卡全程未触犯）
- 未使用 SuspendThread / StackWalk64 / MiniDump / 断点 / 注入 / 写目标进程内存 / 改 exe / dll / hook。
- 未增删改 `ra2youli` 下任何文件（唯一例外：收尾配置还原，系卡面要求，见 CONFIG_RESTORE.md）。
- `taskkill` 仅作用于本探针自启动的 pid=41640；有非自启动残留时探针 S0 即停手（本趟无残留）。

## 4. 进程树纪律
- 探针本体：代理经 WMI `Win32_Process.Create` 启动（cmd pid=7244），父=WmiPrvSE，脱离代理进程树。
- 游戏：探针内再次经 WMI 启动（pid=41640，父=WmiPrvSE）。
- 观察者：第三次 WMI 启动（cmd pid=14180），独立进程 1Hz，与 6ms 采样器零 GIL 争用。
- 探针 `finally` 自愈链：停观察者 → 关游戏 → 残留核对 → 逐字节还原 RA2MD.INI/ddraw.ini/benchbak 并实算自证 → 写 `kind=meta_end` → 恢复锁 owner=lead。

## 5. 观测纪律（质量红线执行）
- 进图判定只用 `frame` 速率（≈29–32 计数/s 持续 ≥60 s）；`mode[0xA8B238]` 仅旁证记录。
- 主判读通道 = 窗口线程 cycle（`QueryThreadCycleTime`）逐拍 Δ；FILETIME 通道只作交叉核对（15.625 ms 记账量子，0 不读作「拍快」）。
- 无硬编码 cyc/ms 判读常数：探针逐拍只记 `win_cyc_delta` 原始值；`cyc_est_ms_Acorr_provisional`（÷3.104e6）仅为进度显示旁证；判读 ms 全部由 analyze_u800.py 用本趟全段自标定重算。
- `0xA8ED50` 只作旁证描述（候选 BulletCnt，语义未证），不当已证单位数。
- 采样段零输入、零切窗；读失败拍保留不填补、跨 fail 拍不计算递增。
- 「没观测到」≠「不存在」：所有未解码语义只描述不推断。
