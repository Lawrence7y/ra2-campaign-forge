#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §884: the live session — what it confirmed, and the navigation blocker."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()
if "## §884 ·" in s:
    raise SystemExit("REFUSE: §884 already present")

SEC = """
## §884 · **首次真机实测（用户已授权）：确认 3 条静态结论 + 发现 3 个真机专属事实；但**未能进局** —— 合成输入对该游戏无效**（2026-11-15 21:40）

> 工具：`lead\\next_re_20261112_r10\\W136_live2\\`（`w136_poll.py` 内存轮询、
> `w136b_eipsample.py` EIP 采样、`probe_wow64_ctx.py` API 判定、`w137_nav.py` 导航尝试）。
> 全部只读，除合成鼠标输入外未向目标写任何数据。**沙盒事后完全干净**（哈希/`expandmd01.mix`/`except.txt` 均未变，无残留进程）。

- **§884-1 [已证·真机确认 `-ATTRACT` 的静态结论]**
  带 `-ATTRACT` 启动后，`[0xA8D5F8]` **实测为 `0x4`**；不带该开关时为 `0x0`。
  - ⇒ **§882-2 的静态推断（`-ATTRACT` ⇒ `[0xA8D5F8] |= 4`）得到真机确认。**
  - ⇒ 这同时**反证**"正常游戏（无开关）时 SYNC 转储被跳过"——`[0xA8D5F8]=0`，`test al,2` 必失败。

- **§884-2 [已证·帧计数器在菜单期恒为 0（两法互证）]**
  | 方法 | 观测 |
  |---|---|
  | 内存轮询（`[0xA8ED84]`） | 70 秒内恒为 **0**（`-ATTRACT` 与普通启动皆然） |
  | EIP 采样 | 见 §884-3 |
  - ⇒ **主菜单不推进逻辑帧。`0x48CCC0`（Conquer.CPP 主循环）在进局前不运行。**
  - ⇒ 因此 §881 的每帧链路（`0x55D360` 等）**在当前可观测状态下无法被驱动**。

- **§884-3 [已证·★ 菜单期 EIP 采样：gamemd 自身几乎不执行]**
  34 个线程、1,261 个样本、20 秒：
  | 落点 | 占比 |
  |---|---|
  | `0x76F487FC` / `0x76F4A0BC` / `0x76F4826C` / `0x76F4858C`（ntdll/kernel32 等待态） | **96.9%** |
  | `0x750011AC`（疑似 kernel32/ddraw） | 1.5% |
  | **gamemd `.text` 内** | **1 个样本**（`0x4A1DE0`） |
  | **§881/§883 的 9 个监控点（主循环/每帧/事件泵/协调器/TAction）** | **全部 0 样本** |
  - ⇒ **主菜单期 gamemd 基本阻塞在系统调用里，不跑游戏逻辑。** 与 §884-2 互证。

- **§884-4 [已证·★ 一个会误导人的 API 陷阱：必须用 `Wow64GetThreadContext`]**
  本机 Python 是 **64 位**，gamemd 是 **32 位**（WOW64）。
  | API | 结果 |
  |---|---|
  | 原生 `GetThreadContext` + `CONTEXT_i386` | **调用返回成功，但 CONTEXT 全 0**（420/420 样本 `EIP=0`） |
  | `Wow64GetThreadContext` | **返回真实值**（如 `0x76F487FC`），EIP 落在 `0x76Fxxxxx` 系统 DLL 区间，与"线程在等待"自洽 |
  - ⇒ **"调用成功"不等于"读到了值"。** 我第一版采样器因此给出"97% 的 EIP 是 0"这种看似结论、实为 API 误用的数据。
  - ⇒ **教训**：任何采样类工具**必须**有"值域合理性检查"（本例：EIP 是否落在目标 `.text`）。
    这条与 §878-6（"没找到必须报扫描规模"）同族。

- **§884-5 [已证·★ 分辨率口径三方不一致]**
  | 来源 | 值 |
  |---|---|
  | `RA2MD.INI` `[Video] ScreenWidth/Height` | **1366 × 768** |
  | 游戏窗口客户区（`GetClientRect`） | **1706 × 960**（= 1366×1.249, 768×1.25） |
  | **实际渲染内容**（PNG 非黑像素包围盒） | **798 × 598**（位于窗口左上 (0,0)，其余全黑） |
  - ⇒ 窗口是配置分辨率的 **1.25 倍**，而**实际画面只有 798×598**。
  - ⇒ 这是**点击落点无法确定**的直接原因之一：无法判断游戏内部把屏幕坐标换算到哪个空间。

- **§884-6 [已证·★ gamemd 不导入 DirectInput]**
  导入表仅 16 个 DLL：`xyr / KERNEL32 / USER32 / GDI32 / ADVAPI32 / SHELL32 / ole32 / OLEAUT32 /
  WINMM / WSOCK32 / DDRAW / DSOUND / VERSION / COMCTL32 / IMM32 / binkw32`。
  **没有 DINPUT.dll，也没有任何 `DirectInput*` / `GetDeviceState` / `GetDeviceData` 符号。**
  - ⇒ 我最初怀疑"游戏用 DInput 所以不响应 SendInput"**是错的，当场收回**。
  - ⇒ 鼠标输入**应当**走 `USER32` 窗口消息，因此合成输入理论上可行 —— 但实测无效（§884-7）。

- **§884-7 [已证·★ 没能进局：三种注入 × 三个坐标映射全部无效]**
  | 注入方式 | 坐标 | 结果 |
  |---|---|---|
  | `mouse_event`（LEFTDOWN/UP） | (730, 237) | 按钮区**像素零变化** |
  | `SendInput`（含 `SetCursorPos` + `SetForegroundWindow`） | (730, 237) | 同上 |
  | `PostMessage(WM_MOUSEMOVE/LBUTTONDOWN/LBUTTONUP)` | (730, 237) | 同上（三条消息均返回 1） |
  | `SendInput` | (584, 190)（按 1366 空间换算） | 同上 |
  | `SendInput` | (1557, 505)（按窗口/渲染比换算） | 同上 |
  - 前提均已逐项验证**正常**：`GetForegroundWindow` = 游戏窗口；`WindowFromPoint(730,237)` = 游戏窗口；
    窗口类名 `"Yuri's Revenge"`；`SendInput` 返回 1（发送成功）。
  - 判定方法：点击前后**按钮区域（x 660..800, y 210..270）像素差异 = 0**；
    整屏哈希变化仅来自背景动画。
  - ⇒ **合成输入未被游戏采纳**，原因**未定**（候选：焦点/输入队列归属、DDraw 独占鼠标、
    或需 `AttachThreadInput` 等多步焦点序列）。
  - ⇒ **本项目 harness 必然做了我没做的事** —— 它有 `_focus_foreground`（多步焦点序列）
    与 `_fs_ensure_foreground`，而我只做了单次 `SetForegroundWindow`。
    **这是下一步最该复用的东西。**

- **§884-8 [未证·如实登记]**
  1. **没有进局** ⇒ §881/§883 的任何每帧量（事件条数、`0x64C380` 遍历次数、`0x67D300` 是否每帧跑）
     **一个都没测到**。这些仍是 `[未证]`。
  2. 合成输入失效的**真正原因未定**（§884-7 的候选未逐一排除）。
  3. 未读 harness 的 `_focus_foreground` 实现细节（只知它存在且是多步的）。
  4. 未尝试 `-WIN`（窗口化）开关；它可能消除 DDraw 对输入的影响。
  5. 未尝试加载存档（`SAVE0029.SAV` 等）——若 GUI 能通，这是比走菜单更快的进局路径。

- **§884-9 [已证·产物与卫生]**
  | 文件 | 内容 |
  |---|---|
  | `w136_poll.py` / `w136_run1.tsv` / `w136_attract.tsv` | 内存轮询器 + 两趟数据 |
  | `w136b_eipsample.py` / `eip_menu2.tsv` / `eip_menu2.log` | EIP 采样器（已修正为 Wow64）+ 数据 |
  | `probe_wow64_ctx.py` / `probe_ctx.log` | API 判定实验（420×2 样本） |
  | `w137_nav.py` / `screen_*.png` | 导航尝试 + 各阶段截图 |
  - 沙盒事后：`gamemd.exe` 哈希未变、`expandmd01.mix` = 4,813,968 B、`except.txt` = 26,794 B **未变**
    （**真机全程零新崩溃**）、无残留进程、游戏未写出任何新文件。
"""

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §884; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
