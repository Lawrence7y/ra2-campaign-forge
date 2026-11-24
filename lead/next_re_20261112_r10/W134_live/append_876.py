#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §876: the crash Access address is 0x250 => genuine NULL, entry guard is sufficient."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

SEC = """
## §876 · **【②-a 定谳】真机现场的 `Access address = 00000250` —— 是**真 NULL**，不是悬空指针；入口守卫方案有效**（2026-11-15 17:25）

> 来源：我在项目里**全量回查**真机 `except.txt`（纯读文件，零真机）。
> 这条回答了 §875-5 留下的那个唯一判别问题，并把 ②-a 与第三缺陷**双双钉成真 NULL**。

- **§876-1 [已证·②-a 的现场地址]**
  在所有含 `Eip:00724737` 的现场里，`Access address` **一致为 `00000250`**（我找到 15+ 份独立现场，全部相同）：
  | 现场 | Eip | Access address |
  |---|---|---|
  | `goal2_rc4_trigger_20261022\\probe_20261022T182303_t1\\except_after.txt` | `00724737` | **`00000250`** |
  | `next_re_20261112_r02\\W27_campaign_live\\sandbox_game\\except.txt` | `00724737` | **`00000250`** |
  | `next_re_20261112_r02\\W35_mapselmd_live\\sandbox_game\\except.txt` | `00724737` | **`00000250`** |
  | `next_re_20261112_r02\\W44_c_line_e2e\\sandbox_game\\except.txt` | `00724737` | **`00000250`** |
  | `next_re_20261112_r02\\W65_bline_live_collect\\…`（A1/A2/B1/B2 四份） | `00724737` | **`00000250`** |
  | `next_re_20261112_r02\\W69_bline_v2_collect\\…`（A1/A2/B1…） | `00724737` | **`00000250`** |
  - ⇒ `0x250 = this + 0x250`，而访问地址恰为 `0x250`，说明 **`this == 0`**。
  - ⇒ **真 NULL，不是悬空指针。** §875-5 的判别问题**已解**。
  - ⇒ **`ecx == 0` 的入口守卫足以拦住这一类崩溃。** ②-a 的修复方案**在语义上成立**。

- **§876-2 [已证·第三缺陷同样是真 NULL]**
  沙盒当前 `except.txt`（`Eip:006F40A2`）：
  ```
  Access address: 00000155 was read from.
  Eip:006F40A2   Bytes: 8A 82 55 01 00 00 ...
  ```
  - `0x006F40A2` 处的指令是 `mov al,[edx+0x155]`，其中 `edx = [ecx+0xAC]`（`0x6F409C`）。
  - 访问地址 `0x155` ⇒ **`edx == 0`** ⇒ **`[this+0xAC] == 0`**。
  - ⇒ **第三缺陷也是真 NULL**，与 §875-4 里"三处都解引用 `call [reg+0x3F8]` 的返回值"相容：
    该调用返回 0，随后 `[edx+0x155]` 崩在 `0x155`。
  - ⇒ **`0x155` / `0x159` / `0x15A` 三个偏移与 §875-4 的站点表逐一对应**（`+0x155`/`+0x159`/`+0x15A`）。
    **两套独立证据（静态站点 + 真机 fault address）互相印证。**

- **§876-3 [已证·②-a 剩余风险的最终状态]**
  | 风险 | 状态 |
  |---|---|
  | NULL 守卫是否足够 | **足够**（真机 fault address = 0x250，`this` 确为 0） |
  | 悬空指针窗口 | **本类崩溃不是它**（真机证据支持 NULL）——但**不能排除另有悬空型崩溃存在**，只是它不是这 25/26 份现场的成因 |
  | `ecx=0` 时静默返回的语义后果 | **仍 `[未证]`**，需交互测试，无法静态判定 |
  | **守卫列表漏了 `0x006CD8CD`** | **真实缺口**（§875-3），需补进 `entries.json` |
  | 静默续跑是否会导致后续逻辑错乱 | `[未证]` |

- **§876-4 [已证·对补丁清单的直接影响]**
  | 动作 | 依据 |
  |---|---|
  | 保留现有 6 个入口守卫 | 方案正确（§876-1） |
  | **新增评估 `0x006CD8CD`**（`this` 来自 `[0x8871E0]`，读 `[this+0x250]`，无守卫） | §875-3，真实缺口 |
  | 复核 `0x004FD7A0` / `0x0059A5B0` 的上游是否有守卫 | §875-3，形态成立但未追上游 |
  | **不要把 `0x005B32CA` 当同类** | 那是虚调用槽（`call [edx+0x250]`），`edi=0` 时崩在地址 **0**，不是 0x250 |
  | `0x7241A0` 的 14 个调用点**不需要**逐点补 | 入口守卫覆盖（§870），且 §875-1 已说明"守卫数"这个统计本身有误 |

- **§876-5 [未证·如实登记]**
  1. 我只回查了"含 `Eip:00724737` 或 Access 恰为 `00000250`"的文件；
     **未统计全部 25/26 份现场的 Access 字段分布**（可能有个别例外）。
  2. 项目内 `except.txt` 与 `baseline_except` 副本曾被混淆过一次（台账 §835 的教训）。
     本节只取**非 `baseline_except` 路径**下的文件，且逐一列出路径，可复核。
  3. `0x006CD8CD` 是否会真的被触发**未证**（需知道 `[0x8871E0]` 何时为 0）。
"""

if "## §876 ·" in s:
    raise SystemExit("REFUSE: §876 already present")

# resolve the open question flagged in §875-5/§875-6
OLD = ("  - ⇒ **判别证据非常具体**：**看崩溃记录里的 fault address**。\n"
       "    - ≈ `0x00000250` ⇒ 真 NULL，入口守卫足够。\n"
       "    - 其它地址 ⇒ 悬空指针，守卫**不够**。\n"
       "  - ⇒ 台账已有的真机现场签名是 `Eip:00724737`；**对应的 `Access address` 是否为 `0x250` 我需要回查**（见 §875-6）。")
NEW = ("  - ⇒ 判别问题**已由 §876 解决**：真机现场的 `Access address` **一致为 `00000250`** ⇒ **真 NULL**，\n"
       "    入口守卫足够。第三缺陷同样是真 NULL（Access = `00000155`）。")
if s.count(OLD) == 1:
    s = s.replace(OLD, NEW)
    print("§875-5 resolved with pointer to §876")
else:
    print("WARN: §875-5 anchor found %d times, skipped" % s.count(OLD))

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §876; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
