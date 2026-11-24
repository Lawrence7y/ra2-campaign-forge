#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §885: the second navigation attempt — what it established, and why it failed."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()
if "## §885 ·" in s:
    raise SystemExit("REFUSE: §885 already present")

SEC = """
## §885 · **第二次导航尝试：找到了正确的点击手法（`AttachThreadInput` + harness 坐标），但**我自己的 PNG 解码有 bug**，坐标测量整体偏移，导航仍失败**（2026-11-15 22:30）

> 用户指示"我暂时点不了，请你自行处理"，因此本轮由我自行驱动 GUI。
> 结论：**仍未进局**。但排除了三个错误假设，并定位到真正的失败点（我的测量工具）。

- **§885-1 [已证·★ 找到点击无效的真正原因：缺 `AttachThreadInput`]**
  §884-7 用 `mouse_event` / `SendInput` / `PostMessage` 共 9 次点击全部无效。读了 harness
  `_focus_foreground`（`qc151_trip.harness8_v4.py:2376`）后补上该序列：
  ```python
  ShowWindow(hwnd, 9)                 # SW_RESTORE
  BringWindowToTop(hwnd)
  cur = GetCurrentThreadId(); tgt = GetWindowThreadProcessId(hwnd, None)
  AttachThreadInput(cur, tgt, True)
  SetForegroundWindow(hwnd)
  AttachThreadInput(cur, tgt, False)
  # 兜底：keybd_event(ALT) 绕前台锁
  ```
  - 补上之后**点击立刻生效**：主菜单点 `(700,218)` 后画面变成 **"載入中.."（Loading）**，
    截图 `n2_post1_mainmenu.png`（3.1 MB、71.7% 非黑）。
  - ⇒ **§884-7 的"合成输入完全无效"是错的**，真因是**缺输入队列附加**。
    **这是本轮最重要的方法学修正。**

- **§885-2 [已证·主菜单按钮的真实语义（逐一点过）]**
  | y（我测得的带中心） | 按钮 | 点了之后 |
  |---:|---|---|
  | 220 | 單人遊戲 | **"載入中.." → 又退回主菜单**（走战役路径，本机无战役存档/加载失败） |
  | 262 | 網際網路遊戲 | 未单独验证 |
  | 304 | 網絡 | 点击后**画面无变化**（见 §885-4 的测量误差） |
  | 345 | 動畫及製作人員 | 未验证 |
  | 388 | 選項 | 未验证 |
  | 555 | 退出遊戲 | 未验证 |
  - 我实测的带中心集合 `57 / 220 / 262 / 304 / 345 / 388 / 555` 与 harness 的签名表
    `mainmenu: [220, 262, 304, 346, 388, 556]` **数值上吻合**（57 是"主選單"标题栏，不在签名内）。
  - ⇒ **坐标表本身是对的**；问题在下一步（§885-4）。

- **§885-3 [已证·`NAV_CHAIN` 不能当"绝对步骤"用]**
  harness 的 `NAV_CHAIN = (("mainmenu",700,218),("skirmish",700,304),("start",700,262))`
  —— 三个坐标分属**三个不同画面**。我在 §884-7 把它们当主菜单上的三个按钮连点，
  **语义完全错了**（主菜单根本没有"遭遇战"按钮）。
  - ⇒ 正确用法：**每次点击后重新判断当前画面**，再决定下一个坐标。
    harness 正是用 `wait_screen` + 红色带签名做这件事的，而我只照抄了坐标、没照抄判据。

- **§885-4 [已证·★ 真正的失败点：我的 PNG 解码有 bug，坐标测量整体偏移]**
  同一张截图（`screen_menu.png`）上：
  | 来源 | 按钮 y |
  |---|---|
  | **我的 Python PNG 解码器量出** | 220 / 262 / 304 / 345 / 388 / 555（间距 42,42,41,43,167） |
  | **人眼在图上所见** | ≈237 / 290 / 342 / 394 / 446 / 636（间距 53,52,52,52,190） |
  - 两组数**系统性偏移且间距不同**（42 vs 52）⇒ **不是坐标表错，是我的测量错**。
  - 偏移比例 ≈ 52/42 ≈ **1.24**，与"窗口 1706 是配置 1366 的 1.25 倍"**吻合**。
  - ⇒ 强烈提示我那段手写 PNG 解码器（inflate + 逐行反滤波）在**行跨距或通道序**上算错了，
    导致量出的 y 被压缩了 ~1.25 倍。
  - ⇒ **这解释了为什么我点的 304 落在"網際網路遊戲"和"網絡"之间**——那一击本来就不该命中。
  - ⇒ **教训**：我自己写的解码器没做自检就当作测量依据。**任何自写解析器必须有已知输入的回归测试**
    （本例：拿一个已知尺寸/已知像素的 PNG 验证行列对应），否则测量结果会整体偏移而不报错。
    这与 §878-6（"没找到必须报扫描规模"）、§884-4（"调用成功≠读到值"）属同一族：
    **工具必须能证明自己是对的**。

- **§885-5 [未证·如实登记]**
  1. **仍未进局**，帧计数器始终为 0。§881/§883 的每帧量**依旧未测**。
  2. 主菜单 6 个按钮里**只实际点过 2 个**（單人遊戲、網絡），其余 4 个未验证。
  3. **没有**用 harness 的 `wait_screen` / 红色带签名做画面判据（只用了"两次截图相同"这种弱判据，
     而主菜单背景有动画，永远不"相同"，导致我的稳定性等待在 step2/3 全部超时 45 s）。
  4. 未验证"網絡"子菜单里是否真有 Skirmish。
  5. 未试 `-WIN`（窗口化）——窗口尺寸与配置不符可能就是 `ddraw.ini windowed` 造成的，
     窗口化后坐标映射可能变干净。

- **§885-6 [已证·产品与卫生]** 新增 `w138_nav.py`（harness 焦点/点击移植）、
  `w139_nav2.py`（加稳定性等待 + 帧计数器判据）、`w140_click.py`、
  `net_after.png` / `n2_*.png` / `screen_*.png` 等截图。
  - 沙盒事后：`gamemd.exe` 哈希未变、`expandmd01.mix` = 4,813,968 B、
    `except.txt` = 26,794 B（lastwrite **未变**，真机全程零新崩溃）、无残留进程、游戏未写任何新文件。

- **§885-7 [已判·下一步该怎么做（不是再猜坐标）]**
  按代价从低到高：
  1. **修我的 PNG 解码器**并做已知输入回归——否则任何像素测量都不可信。
  2. **直接复用 harness 的 `capture_frame` + `_red_button_centers` + `wait_screen`**
     （它有 `load_rgb`，是经过真机校准的实现），而不是自己写。
  3. 用 `-WIN` 窗口化启动，消除窗口/配置分辨率不一致。
  4. 若仍不通，**请用户手动点进一局遭遇战**（约 15 秒），我用已就绪的 `w136_poll.py` /
     `w136b_eipsample.py` 直接测——**这是最快且最可靠的路径**。
"""

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §885; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
