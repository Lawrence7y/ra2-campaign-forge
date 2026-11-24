#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: the navigation attempts' honest outcome (ledger §885/§886)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = """**阻塞点（未解决）**：`mouse_event` / `SendInput` / `PostMessage` × 3 种坐标映射 =
**9 次尝试全部无效**；判定依据是按钮区域（x660..800, y210..270）点击前后**像素差异 0**。
前提均已验证正常（前台窗口、`WindowFromPoint` 命中、`SendInput` 返回 1）。
⇒ **本项目 harness 必然做了我没做的事**：它有 `_focus_foreground`（多步焦点序列）与
`_fs_ensure_foreground`，我只做了单次 `SetForegroundWindow`。**下一步应复用它的焦点序列。**
其他未试路径：`-WIN`（窗口化）、直接加载存档（`SAVE0029.SAV`）。"""

NEW = """**阻塞点（两轮尝试后仍未解决，且我收回了一个错误结论）**

- **§885**：读了 harness 的 `_focus_foreground` 并补上 `AttachThreadInput` + ALT 兜底，
  点击**确实发出**（`SendInput` 返回 1），但**无法证明被游戏采纳**。
- **§886（关键自我更正）**：**主菜单背景是动画** —— 完全不发输入、每 5 秒截一帧，
  60 秒得到 **12 个全不同的帧**。⇒ **"画面变了"不能当作"点击生效"的证据**。
  因此 §885-1 的"点击立刻生效"**已收回**；「合成输入是否被采纳」回到 **`[未证]`**。
- **正确的判别指标**（今后必须用）：**`[0xA8ED84]` 逻辑帧计数器**（菜单期已证恒为 0），
  而不是截图。`w139_nav2.py` 已这样打印，但我在 `w138/w140/w141` 里仍以截图为准 —— 这是误判根源。
- **另一个自我更正**：§885-4 说"我的 PNG 解码有 bug"**是错的**。用 .NET `System.Drawing`
  独立解码同一张图，得到**完全相同**的按钮带中心 `220/262/304/346/388/556`。
  **目测缩放预览图不能用于像素测量。**

**已证的真机事实（不依赖截图）**：`-ATTRACT` ⇒ `[0xA8D5F8]=0x4`；菜单期帧计数器恒 0；
菜单期 EIP 96.9% 在等待态、gamemd `.text` 仅 1 样本；`Wow64GetThreadContext` 是唯一可用 API；
分辨率三方不一致（1366×768 / 1706×960 / 渲染 798×598）；gamemd 不导入 DirectInput；
主菜单按钮带中心 `220/262/304/346/388/556`、退出按钮 x 范围 `635..769`。

**未试过的路径**：`-WIN`（窗口化，可能消除分辨率不一致）；直接加载存档
（`SAVE0029.SAV` / `RA2F_M1.sav`）绕过菜单；复用 harness 的 `wait_screen`/`capture_frame`
（有真机校准过的 `load_rgb` 判据）。"""

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: anchor found %d times" % n)
h = h.replace(OLD, NEW)

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
