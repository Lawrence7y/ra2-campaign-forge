#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: the live session results and the navigation blocker (ledger §884)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

ANCH = "**必须记住的陷阱**"
ADD = """**真机会话（§884，2026-11-15，用户已授权）：确认 3 条静态结论，但未能进局**

已确认：
- **`-ATTRACT` ⇒ `[0xA8D5F8] = 0x4`**（真机实测）；不带开关为 `0x0` ⇒ §882 的门控推断成立。
- **帧计数器 `[0xA8ED84]` 在菜单期恒为 0**（轮询 70 s + EIP 采样双证）⇒ 主循环 `0x48CCC0` 进局前不跑。
- **菜单期 EIP 采样**（34 线程 / 1,261 样本）：**96.9% 落在 ntdll/kernel32 等待态**，
  gamemd 自身 `.text` 仅 **1** 个样本，§881/§883 的 9 个监控点**全 0** ⇒ 菜单不跑游戏逻辑。

三个真机专属事实（以后必须知道）：
1. **读 32 位线程上下文必须用 `Wow64GetThreadContext`**。从 64 位 Python 调原生
   `GetThreadContext` **返回成功但 CONTEXT 全 0**（420/420 样本 `EIP=0`）。
   ⇒ **"调用成功"≠"读到值"**；采样工具必须有值域合理性检查。
2. **分辨率三方不一致**：INI 写 `1366×768`；窗口客户区 `1706×960`（1.25 倍）；
   **实际渲染内容只有 `798×598`**（左上角，其余全黑）。
3. **gamemd 不导入 DirectInput**（16 个 DLL 无 DINPUT）⇒ 鼠标应走 USER32 消息，
   所以"sendinput 无效是因为 DInput"这个猜想**是错的**。

**阻塞点（未解决）**：`mouse_event` / `SendInput` / `PostMessage` × 3 种坐标映射 =
**9 次尝试全部无效**；判定依据是按钮区域（x660..800, y210..270）点击前后**像素差异 0**。
前提均已验证正常（前台窗口、`WindowFromPoint` 命中、`SendInput` 返回 1）。
⇒ **本项目 harness 必然做了我没做的事**：它有 `_focus_foreground`（多步焦点序列）与
`_fs_ensure_foreground`，我只做了单次 `SetForegroundWindow`。**下一步应复用它的焦点序列。**
其他未试路径：`-WIN`（窗口化）、直接加载存档（`SAVE0029.SAV`）。

⚠️ 因此 §881/§883 的所有**每帧量**（事件条数、`0x64C380` 遍历次数、`0x67D300` 是否每帧跑）
**仍未测到**，仍是 `[未证]`。

"""

if h.count(ANCH) != 1:
    raise SystemExit("REFUSE: trap anchor not unique")
if "真机会话（§884" in h:
    raise SystemExit("REFUSE: already present")
h = h.replace(ANCH, ADD + ANCH)

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
