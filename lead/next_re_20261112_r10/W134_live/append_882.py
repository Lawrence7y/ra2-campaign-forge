#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §882: the SYNC dumper is command-line gated -> NOT a per-frame cost."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()
if "## §882 ·" in s:
    raise SystemExit("REFUSE: §882 already present")

SEC = """
## §882 · **【排除最大嫌疑】SYNC 转储（`0x64DEA0` 11 KB / `0x6516F0`）由命令行开关门控，正常游戏完全不执行 —— 且顺手拿到完整命令行开关表**（2026-11-15 20:05）

> 承接 §881-5（我当时把 `0x64DEA0` 定性为"很可能是调试转储、门控未查"）。本节把门控查清。
> 结论是**否定**的：它不是每帧开销。同时**更正 §881-5 的一处定性错误**。

- **§882-1 [已证·外层门控在 `0x647260` 的入口]**
  `0x647260`（885 B）是每帧更新 `0x55D360` 的**深度 1 直接 callee**（BFS 已证）。它的头三条：
  ```asm
  00647260  mov  al,[0xA8D5F8]
  00647268  test al, 2
  0064726E  je   0x6474C7        ; <<< 该位为 0 ⇒ 直接跳走，后面全部跳过
  ```
  - `0x6474C7` 之后的整段（含 `0x64DEA0` / `0x6516F0` 两条路径）**只有 bit1 置位才进入**。
  - 进入后还有更多门：`test [0xA8D5F8], 4`（`bl=4`）、`[0xA8ED84] > 0`（帧号）、
    `[0xA8ED84] >= [0xA8E30C]`（帧号阈值）、以及内层 `[0xB04880]`。

- **§882-2 [已证·两个标志都由命令行开关决定]**
  `0x52F620` 是**命令行解析器**：模式为 `push <开关串>` → `call 0x7CA4B0`（匹配）→
  `test eax,eax` / `je` → 设标志。我逐条读出它认识的**全部开关**：
  | 开关 | 效果 |
  |---|---|
  | `-MPDEBUG` | **`[0xB04880] = 1`**（"Extra sync info ON"） |
  | `-ATTRACT` | **`[0xA8D5F8] |= 4`** |
  | `-DROP=` | 解析为数值 |
  | 其余 | `-jabber`, `-str`, `-nostr`, `-noaudio`, `-record`, `-play`, `-?`, `-h`, `-CD`, `-DESTNET`, `-SOCKET`, `-SPEEDCONTROL`, `-DLINK1`, `-NETGEAR`, `-NOROUTER`, `-STEALTH`, `-MESSAGES`, `-%dX%d`, `-WIN`, `-X` |
  - ⇒ 这修正了我在对话里"gamemd.exe 只有 `-MPDEBUG`/`-DESTNET`/`-CD` 三个开关"的说法 ——
    **实际有 23 个**（我的早期字符串扫描限定得太窄）。

- **§882-3 [已证·默认值 ⇒ 正常游戏不执行转储]**
  `[0xA8D5F8]` 与 `[0xB04880]` **都在 `.data` 的 BSS 尾部（> `0x87E000`）**，
  加载时按 PE 语义**清零** ⇒ **默认 `[0xA8D5F8] = 0`** ⇒ `test al,2` 失败 ⇒ **跳到 `0x6474C7`**。
  - ⇒ **不带 `-MPDEBUG` / `-ATTRACT` 时，`0x64DEA0` 与 `0x6516F0` 一次都不会被调用。**
  - ⇒ **§881-5 里"若未门控而每帧执行则开销巨大"这个担忧解除。**

- **§882-4 [已证·两条 SYNC 路径的真实分工（更正 §881-5 的定性）]**
  §881-5 我写"`0x64DEA0` 是 SYNC 状态转储（调试）"。**更准确的表述**：
  | 函数 | 大小 | 文件名格式 | 内容 |
  |---|---:|---|---|
  | `0x64DEA0` | 11,242 | **`SYNC%01d.TXT`** | 详细：`COORD:%d,%d Facing:%d ...`，并按类分组（Aircraft/Anim/Building/Bullet/Infantry/Overlay/Smudge/Terrain/Unit） |
  | `0x6516F0` | 2,417 | **`SYNC%01d_%03d.TXT`**（**带帧号**） | 更细：`COORD:%x Facing:%d Tgt:%s NavCom:%s TrkNum:%d` |
  - 文件以 `'wt'`（文本写）打开（`0x81D988 = 'wt'`，`call 0x7CA845` = `fopen`）。
  - 分支：`[0xB04880]==1`（`-MPDEBUG`，"Extra sync info ON"）⇒ **`0x6516F0`（每帧一个新文件，更细）**；
    `==0` ⇒ `0x64DEA0`（文件名不带帧号，会覆盖）。
  - ⇒ 两者都是**同步校验转储**，不是"模拟"也不是"常规开销"。**§881-5 的定性限于"是转储"这一点是对的，
    但"可能每帧执行"的判断已被本节否定。**

- **§882-5 [已证·★ 对 ① 的净结果]**
  | 项 | 结论 |
  |---|---|
  | `0x64DEA0`（11 KB）是否每帧 | **否**（默认被 `[0xA8D5F8] & 2` 挡在门外） |
  | `0x6516F0` 是否每帧 | **否**（同在门外；且需 `-MPDEBUG`） |
  | 每帧**已确认**的直接工作 | `0x55D360` 的 44 个 callee（其中 `0x647260` 每帧必进，但走 `0x6474C7` 的轻路径） |
  | 每帧**主要候选** | **`0x67D300`**（4,411 B、111 回边、7 种数组），路径 `0x55D360 → 0x67CEF0 → 0x67D300` |
  - ⇒ **① 的嫌疑清单从"两个 11 KB 级 + 若干"收窄为"`0x67D300` 为主"**。

- **§882-6 [未证·如实登记]**
  1. **`0x6474C7` 这条"轻路径"具体做什么，我未展开**（它每帧必走，可能本身也不轻）。
  2. `[0xA8D5F8]` 的其他写者（`0x48CF9A`、`0x52DC3B`、`0x52DD10`、`0x52DD2A`、`0x52E96A`）
     **我只确认了 `0x52F9F2`（`-ATTRACT`）**，其余 5 处**未逐条定性**。
     ⇒ **无法完全排除运行期某条路径把它置位**（例如进入多人游戏时）。
  3. `0x67CEF0`（`0x67D300` 的父）**未定性**，因此"`0x67D300` 每帧必跑"**仍未证**。
  4. 本节仍**无任何计时数据**。
  5. `[0x81D988]='wt'` 我按"fopen 的模式参数"解释，**未追 `0x7CA845` 的实现确认**。
"""

s = s.rstrip("\n") + "\n" + SEC

# correct §881-5's characterization with a pointer
OLD = "  - ⚠️ 若它**未被门控而每帧执行**，仅它一个就是巨大开销（11 KB、写文件、遍历 9 种数组）。\n    **这是 ① 最值得优先排除的一项**（静态可查：看两个调用者前是否有同步校验开关判断）。"
NEW = ("  - ✅ **§882 已排除**：`0x647260` 入口处 `test [0xA8D5F8], 2` / `je 0x6474C7`，\n"
       "    而 `[0xA8D5F8]` 默认 0（BSS），只有 `-ATTRACT` 置位 4、`-MPDEBUG` 置 `[0xB04880]`。\n"
       "    **正常游戏下两条 SYNC 路径都不会被调用 ⇒ 不是每帧开销。**")
if s.count(OLD) == 1:
    s = s.replace(OLD, NEW)
    print("§881-5 corrected with pointer to §882")
else:
    print("WARN: §881-5 anchor found %d times, skipped" % s.count(OLD))

io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §882; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
