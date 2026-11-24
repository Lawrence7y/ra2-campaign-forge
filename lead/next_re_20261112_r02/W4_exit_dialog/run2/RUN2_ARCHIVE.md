# RUN2_ARCHIVE.md —— 第 2 趟真机原始记录说明

- run_id: `NEXT_RE_20261112_R02` / W4；第 2 趟时间(UTC) `2026-11-12T15:57:31`–`15:59:05`
- pid=`32448`，launcher_pid=`41260`，is32=True，map=`[8] Proving Grounds`（index=265），窗口 tid=`36700`
- 退出码 `0`（脚本正常结束；进程未自然退出，是收尾阶段 `close_game` 关闭的），残留进程 0，配置逐字节还原

## 做了什么

跳过第 1 趟已实测致命的 ① `Alt+F4`（`--skip-altf4`），继续优先级序列 ② → ③：
- ② 正常局内无按钮 → **仅作导航**按一次 Esc 暴露局内菜单按钮；
  按控件文字（不猜索引）找到并点击 `GUI:AbortMission`（hwnd=2495812，`BM_CLICK`）。
- ③ 尝试局内菜单 Restart / Exit-to-main-menu 类按钮（无匹配，未点击）。
- 触发后加了 0.4 s 间隔、共 9 拍（0.0–3.2 s）的轮询观察。

## ★ 关键发现（本趟最大价值）

**确认对话框确实被触发了**，只是当时探针的 UI 判据漏检：

点 `GUI:AbortMission` 前（Esc 菜单，父容器 `28120762`）：
`GUI:ResumeMission / GUI:GameControls / GUI:LoadGame / GUI:AbortMission / GUI:SaveGame /
GUI:DeleteGame`，另有 `Static GUI:GameOptions`、`Static GUI:Blank`。

点之后（**全新子容器 `28186298`**，菜单按钮全部消失）：
```
hwnd 1447262  Button  'GUI:ResumeMission'   visible=True
hwnd 3020146  Static  'GUI:AskAbortMission' visible=True   ← 放弃任务询问标题
hwnd 1381730  Button  'GUI:Blank'           visible=True  ← 位图按钮
hwnd 4397208  Button  'GUI:Blank'           visible=False
hwnd 2561348  Static  'GUI:Blank'           visible=True
```
9 次轮询 0.001–3.217 s 该控件集**完全稳定**（`out/run2/triggers.json` 逐拍留证）。
RA2/YR 的自定义对话框按钮是位图绘制，窗口文字是 `GUI:Blank`，没有 `Yes/No` 文本，
所以第 2 版按 Yes/No 文字匹配的判据判成 `dialog_present=False`，误报「未能触发」。

## 本趟读数

- D0（正常局内，usable=True）：4 帧 `ntdll+0x7858c → KERNELBASE×2 → gamemd+0x15e332`；
  `frame=967`，`g1..g4` 全 0，`mode=5`，`A8E9A0=1`，`ABCD58=1`，`exitstate=0`；
  `prev_count=0 / resume_ret=1 / held=5.444ms`。
- 本趟**没有 D1/D2 抓栈**（判据漏检导致），故不产生 P1–P4 读数，**未伪造**。
- 进程在 ② ③ 后仍存活（`ec=259 / STILL_ACTIVE`），不存在「游戏直接退出」情形。

## 处置

本趟是**仪器判据 bug 的证据来源**，不是判档数据。修复判据（识别
`GUI:AskAbortMission` 标题 + 新子容器 `parent_hwnd`；补录控件 rect/ctrl_id）后做第 3 趟重测。
第 3 趟为主判据，见根目录 `VERDICT.md` / `out/*.json`。
判据修复的自测结果：用本趟 `out/run2/triggers.json` 的真实快照回放，
修复后 `dialog_present=True`（captions=1 / new_containers=1），且 Esc 菜单自身**不**误判。

## 归档清单

- 本目录 `RUN2_ARCHIVE.md` + 从根目录复制的 5 份 MD（运行时原样）
- `out/run2/`：14 个文件（含 `triggers.json` 三趟尝试完整 UI 快照与轮询日志），逐字节未改动
