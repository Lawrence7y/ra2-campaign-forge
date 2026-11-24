# RUNS.md —— W4 四趟真机历史归档与合并判读（跨会话执行汇总）

- run_id: `NEXT_RE_20261112_R02`；本文件生成(UTC): `2026-11-12T16:14` 左右（由 W4 执行代理在 run3 判档后补记）。
- 背景：本卡执行期间存在**并行代理共享同一写域**（exit_dialog_probe.py 在 00:00–00:10 间被并行会话多次改写并执行）。
  为避免误判，本文件按**时间戳 + pid + 落盘产物**（而非目录命名）登记全部四趟；每趟产物独立归档、可离线复核。

## 1. 四趟登记（按开始时间）

| # | 开始(UTC) | 执行方 | pid / tid | 脚本要点 | 过程与结果 | 产物 |
|---|---|---|---|---|---|---|
| run1 | 23:54:11Z | 并行会话 | 16052 / (见 meta) | 首版检测（顶层 yes/no 文字） | D0 阴性对照完成；**Alt+F4 → 游戏直接退出 exit=0，无任何对话框**；GuardStop 收尾、配置还原 | `out/run1/` |
| run2 | 23:57:31Z | 并行会话 | 32448 / 36700 | 跳过 Alt+F4；② Esc→点 `GUI:AbortMission`；③ restart 类 | **确认框实际出现**（按钮集合变为 `[GUI:ResumeMission, GUI:AskAbortMission, GUI:Blank×3]`，轮询多拍），但首版判据只查顶层窗口 + yes/no 文字 → `dialog_present=False` → 按红线未做 D1；WM_CLOSE+taskkill 收尾、还原 | `out/run2/`（triggers.json 38KB 全量 UI 证据） |
| stale（本卡执行代理） | 00:01:23Z | 本卡代理 | 13260 / 26052 | Alt+F4 复核 | **再次证实 Alt+F4 直接退出 exit=0、无框**；D0 阴性对照（帧推进、四门控全 0、栈=主循环 Sleep 前缀 `gamemd+0x15e332`）；红线不重启 | `out/_pre_run3_stale/` |
| run3（判档主判据） | 00:04:56Z | 并行会话 | 4856 / 9832 | 检测修正版（`--skip-altf4`；captions/new_containers 签名识别 `GUI:AskAbortMission`） | ② Esc→点 `GUI:AbortMission` → **确认框识别成功**（captions=1 new_containers=1），稳定 >3s；P3 成对读数 850→850；**D1a/D1b/D1c 三抓逐帧一致**；D2 点 `GUI:ResumeMission`（取消路径）Δframe=31 恢复；D2 抓栈回主循环前缀；判档 **[否证]**；收尾还原 | 顶层 `out/*.json` + 五份 MD |

## 2. 确认对话框的 Win32 形态（run2 + run3 双趟一致）

- 触发：局内 Esc 菜单 → 按文字点击 **`GUI:AbortMission`**（放弃任务）。
- 对话框本体：主窗口（cls `Yuri's Revenge`）的**子对话框容器**（`parent_hwnd=5178498`，非顶层 → 首版 `is_dialog_top` 漏检的根因）。
- 子控件（run3 实测，run2 同构）：
  - `Static "GUI:AskAbortMission"`（ctrl_id 65535，visible，确认提示文本）
  - `Button "GUI:ResumeMission"`（ctrl_id 1670，visible —— 「返回任务/取消放弃」= **否** 路径）
  - `Button "GUI:Blank"` ×2（ctrl_id 1737 visible / 1810 **hidden** —— 「是/否」文字由游戏绘制，Win32 text 为空）
  - `Static "GUI:Blank"`（ctrl_id 1685）
- 稳定性：run3 连续 6 拍 ≥3s 存在 = True；run2 轮询多拍同构状态。

## 3. 合并判读（判档主判据 = run3）

- **总档 [否证]**：退出/放弃任务确认对话框打开时，游戏窗口线程栈为
  `win32u+0x11ac → USER32+0xc7f51 → DDRAW+0x22b06 → gamemd+0x13eb1c`（三抓逐帧一致），
  与基准 S_sleep 七帧（`ntdll+0x7858c → KERNELBASE×2 → gamemd+0x207f17 → USER32+0x74775 → USER32+0x3505d → gamemd+0x20833f`）
  **逐帧无一处相同**（7 帧一致数 0/7；P1 两关键点 0/2；4 关键点 0/4）。
  该栈形与 W3 已测的「Esc 局内菜单」栈**完全同形**（同一模态 UI 消息等待路径）。
- P1=不成立（0x207f17/0x20833f 未出现在帧序列）；P2=不成立（G4 全程 0）；P3=成立（帧 850 冻结，成对读 Δ=0）；P4=成立（取消后 Δframe=31，门控全 0，ABCD58 回 1）。
- 走查深度说明：D1 走查 4 帧 < 基准 7 帧（`normal_end_of_walk` 正常终止）；已用挂起窗口内 64 KiB 只读原始栈交叉核验兜底——
  **两个 gamemd 关键点在 D0/D1a/D1b/D1c/D2 的原始栈上均为 false（未出现）**；原始栈上唯一的 1/4 关键点（USER32 类）在
  **D0 阴性对照同样出现** → 非判别性残留，不影响 [否证]。
- **Alt+F4 语义**：两趟独立实测（run1、stale）直接退出 exit=0、无确认框 —— 「确认退出」对话框假设对 Alt+F4 路径不成立。
- **G4 线索修正**：`0x4C7917` 置位（紧跟 `Processing EXIT event` 打印）在本确认对话框路径上**未发生**（G4 全 0）。
  该门控对应的 EXIT 事件应属**另一条退出路径**（如直接退出进程/其它事件源），S_sleep 的真实来源仍未知。

## 4. 对下一卡的移交建议（供 Lead 判断）

1. S_sleep（`EnumChildWindows(hWnd,0x606800,1)` 内 `Sleep(30)` 的模态轮询）尚未归因；已排除：Esc 局内菜单（W3）、放弃任务确认框（本卡）。
2. 候选下一批探测对象（同协议：触发→稳定→读门控→D1×3 抓栈→取消→D2）：
   - 局内菜单的 `GUI:GameControls / GUI:GameOptions` 子页（本卡 run2 见过这些按钮文字）；
   - 主菜单/加载界面的模态框（如 选图确认、退出到 Windows 确认）；
   - 联网/断线提示框、CD/音量类系统对话框。
3. 检测器教训（已在本仓库修入）：确认框是**子容器 + Static 标题（GUI:AskAbortMission）+ 空文字按钮**形态；
   判据必须含「新容器分组 / 标题 Static 文字 / askabort 签名」，不能只依赖顶层窗口与 yes/no 按钮文字。
