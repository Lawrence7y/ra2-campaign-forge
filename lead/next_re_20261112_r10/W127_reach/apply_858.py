#!/usr/bin/env python3
"""Append §858: 22 subsystem entry points + one self-found misrule correction."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §858 · **里程碑(4) 补齐：22 个子系统全部有了"入口"证据；顺带查出并修正我自己的一条错误分类规则**（2026-11-16 09:00）

- **§858-1 [已证·为何要补这一轮]** 目标 (4) 的字面要求是"**至少 6 个主要子系统的入口与关键结构条目**"。
  §855/§856 交付了**结构**（11 类 + 23 子系统），§853 只交付了 **7 个入口**，
  且"入口+结构两者都齐"的只有 **4 个**（GameObj_Logic / UI / Net / Scenario_Map）。
  ⇒ 渲染/音频/存档/脚本这几个目标点名的子系统**只有结构、没有入口**。本节补齐。

- **§858-2 [已证·方法]** `W131_subsystems\find_entries.py`：
  对每个子系统，把成员按 **"外部调用者数（去重）"** 排序 —— 这是"入口"的合理判据
  （被子系统外的东西调用，说明它是该子系统的对接口）。
  **刻意不用**："最大函数"（那识别的是热点，不是入口，§725 已证否）与地址顺序。

- **§858-3 [已证·22 个子系统的入口（按字符串/导入确证）]**
  | 子系统 | 入口 | 外部调用者 | 大小 | 定性证据 |
  |---|---|---:|---:|---|
  | Render_DDraw_Display | `0x004A42F0` | 2 | 507 | **`DDRAW.DLL Error code = %08X` / `Direct X`** |
  | Video_Bink | `0x00683AB0` | 4 | 1,011 | **`Intro`/`Brief`/`LOADING`/`%s.VQA`**（29 个被调） |
  | Audio_Sound_Music | `0x007514D0` | 11 | 80 | **`Invalid Voc`** |
  | SaveLoad | `0x00558DD0` | 3 | 2,080 | **`LoadDlg.CPP`/`TXT_DISKFULL`/`TXT_DELETE_FILE_QUERY`**（36 个被调） |
  | AI_Team_Script | `0x00705D20` | 24 | 7 | 无字符串（极短桩，被 24 处调用） |
  | File_Mix_FS | `0x00473C50` | 39 | 115 | 无字符串（文件系统小入口） |
  | Movement_Locomotion | `0x00481A00` | 8 | 1,169 | — |
  | Ini_Rules_DB | `0x004A1DE0` | 28 | 457 | — |
  | Sidebar_Radar_HUD | `0x0048DCD0` | 7 | 64 | — |
  | Tactical_MapView | `0x00577F30` | 5 | 335 | **`We tried to clear the shroud without an owner`** |
  | Campaign_Meta | `0x00643AE0` | 7 | 367 | **`AlliedLoad`/`SovietLoad`** |
  | WDT_WorldDom | `0x005D2530` | 3 | 151 | 导入 `Sleep` |
  | Input_Commands_Mouse | `0x005BDA80` | 11 | 26 | — |
  | MP_Lobby_Session | `0x0049E3B0` | 10 | 68 | — |
  | WOL_Online | `0x007B5440` | 29 | 12 | — |
  | **Superweapon_Special** | `0x00539EB0` | 5 | 478 | **`TXT_LIGHTNING_STORM`/`Ion.cpp`**（闪电风暴/离子炮） |
  | Config_Registry | `0x005175F0` | 14 | 176 | **`SOFTWARE\Westwood\WOLAPI\`** + 导入 `RegOpenKeyExA` |
  | File_Stream_Crypto | `0x006C9890` | 10 | 67 | — |
  | Menus_Main_Intro | `0x00622B50` | 11 | 1,418 | **`ownrdraw.cpp`** + 导入 `SetFocus`（41 个被调） |
  | **Misc_Util_Mem** | **`0x006CF240`** | **75** | 118 | 见 §858-4 |
  | Main_Init_Flow | `0x004093B0` | 16 | 16 | — |
  | Graphics_Blit_Shape | `0x007BC2B0` | 13 | 717 | — |
  - ⇒ **22 个子系统全部有入口证据**，其中 **8 个由字符串/导入直接定性**，其余为结构性入口（待语义确认）。

- **§858-4 [已证·★ 自查出一条我自己的错误分类规则（Swizzle → RENDER 是错的）]**
  - 现象：`0x006CF240` 以 **75 个外部调用者**成为 `Graphics_Blit_Shape` 的入口候选。
    但它的形态（size=118、**callees=0**、被大量不同子系统调用）不像 blitter。
  - 追因：它是 **`SwizzleManagerClass`** 的方法，而我的类规则里把 `Swizzle` 归到了 **RENDER**
    （当初只是看到"Swizzle"像图形术语就写进去了）。
  - **实际语义**：`SwizzleManager` 是**指针重定位管理器**（对象表移动/存档时修指针），属内存/存档域。
    **佐证**：本项目台账 §3'1 早就记录"容器 `0xA8ED3C`（子弹列表）的 push = **`FUN_006cf240`**" ——
    即它同时是**子弹容器的 push**；这恰好自洽：**子弹列表就是一个被 swizzle 管理的指针数组**，
    所以"swizzle 表的 push" 被子弹容器复用。
  - **修正**：把 `Swizzle` 从 RENDER 规则移到 `ENGINE_CORE`（现 canonical 分类里落在 `Misc_Util_Mem`）。
    影响 **9 个函数**：`Graphics_Blit_Shape` 500 → **496**，`Misc_Util_Mem` 30 → **40**。
  - ⇒ **教训（方法层面）**：**关键词规则就是猜测**。凡"某个词看起来像某领域的术语"就写进规则，
    迟早会把功能归错。**类名 → 子系统必须有一条非命名的证据**（实际访问的 API / 字符串 / 调用关系），
    本轮这个反例正好由"入口分析"暴露出来 —— 因为**入口的形态（callees=0 + 75 个跨子系统调用者）
    与"渲染 blitter"的形态不符**，才让我去追因。

- **§858-5 [已证·里程碑(4) 的最终达成度]**
  | 项 | 数量 |
  |---|---:|
  | 有**入口**证据的子系统 | **22** |
  | 有**结构条目**的子系统 | **23** |
  | **两者都有** | **22**（几乎全覆盖） |
  - ⇒ 目标要求"≥6 个"，**实际 22 个**，超额达成。
  - 但要说清限制：22 个入口里只有 **8 个**由字符串/导入**语义定性**，
    其余 14 个是"按调用关系判定的结构性入口"，**其语义仍属 `[未证]`**（该函数具体做什么未反编译确认）。

- **§858-6 [已证·canonical 覆盖率微调]** Swizzle 修正后：
  **5,493 / 12,916 = 42.5% 函数；2,089,876 / 3,225,845 = 64.8% 字节**（原 5,497 / 42.6%，差异来自 T2 传播的连带变化）。

- **§858-7 [已证·产物]**
  | 文件 | 内容 |
  |---|---|
  | **`subsystem_entries.tsv` / `.json`** | 22 个子系统的入口 + 外部调用者数 + 大小 + 定性证据 |
  | `find_entries.py` | 入口识别器（可复跑） |
  | `subsystem_map.py` | **已修正 Swizzle 规则**（含注释说明为何不属 RENDER） |
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §858" in src:
    sys.exit("ABORT: §858 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §858", "Swizzle", "0x006CF240"):
    print("  %-12s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
