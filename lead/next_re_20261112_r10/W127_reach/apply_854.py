#!/usr/bin/env python3
"""Append §854: cross-audit of the two subsystem maps + merged canonical map."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §854 · **两份子系统地图的交叉审计：GLM 的 78.8% 覆盖率不可采信（含 2,615 个通用容器误标 + 2,578 个区间/簇填充）；合并出 canonical 42.6%**（2026-11-16 05:00）

- **§854-1 [已证·两份地图的差异（先说结论：都不能直接用）]**
  | | 我（§852） | GLM（独立切分） |
  |---|---|---|
  | 分类粒度 | 12 个粗桶 | **28 个细分类**（更好） |
  | 函数覆盖 | 5,426（42.0%） | **10,180（78.8%）** |
  | 字节覆盖 | 63.1% | **82.9%** |
  | 证据层 | L1 虚表/L2 模块/L3 导入/L4 字符串/**L5 调用图** | P0a 模块/P1 虚表/P2 导入/P3 字符串+**区间**/P4 调用图/**P5 簇填充** |
  - 表面看 GLM 强得多。**但拆开它的证据层后不成立**（§854-2/§854-3）。

- **§854-2 [已证·★ GLM 的 `P1+vtable` 有 2,615 个是"通用容器类"误标]**
  - 它的 P1 赋值共 **5,630** 个。我逐个回查函数所属虚表类：
    | 判定 | 数量 |
    |---|---:|
    | 有 ≥1 个**非通用**类（真实游戏类） | **2,998** |
    | **只属于通用容器类**（`VectorClass<T>`/`DynamicVectorClass<T>`/`rc_ptr`/`TypeList`…） | **2,615** |
    | 不在我的虚表映射里 | 17 |
  - ⇒ 这 2,615 个函数实现的是**容器方法**（push_back / 析构 / operator[]），
    **不能据此判定它属于哪个游戏子系统**。我在 §852-1 已把通用类列为"刻意不用的规则"，
    GLM 没有排除。
  - ⇒ 顺带：**我的非通用 P1 是 3,508，它的对应数是 2,998** —— 在"可辩护的虚表证据"上**我略多**。

- **§854-3 [已证·★ GLM 的 AUDIO 348 个函数是区间填充造成的 12 倍虚高]**
  | 检查 | 结果 |
  |---|---|
  | GLM 归入 `Audio_Sound_Music` 的函数 | **348** |
  | 其中**自身有音频证据**（字符串或导入） | **8** |
  | 其中**既无字符串也无导入**（纯被扫进来） | **308** |
  | 证据来源 | `P3+region` 228、`P5+cluster` 44、`P4+callgraph` 57、`P3+string` 7、`P1+vtable` 12 |
  - 它还报音频地址范围 `0x00401000..0x0077E1C8` —— **几乎覆盖整个 `.text`**，不可能是连贯音频区。
    典型误标：**`0x00401000`（`.text` 第一个函数）被标为音频**，实际是启动/CRT 侧代码。
  - **真实音频代码（我逐个查有自身证据的函数）**：
    | 地址区间 | 内容 | 函数数 |
    |---|---|---:|
    | **`0x00750440..0x00752DB0`** | Voc/Sounds/Volume/Priority/`taunts\tauam%02i.wav` | ~15 |
    | `0x00432700..0x004331F0` | Bink（`_BinkOpen/_BinkDoFrame/_BinkSetVolume`…） | 9 |
    | `0x007C89DA` | `DirectSoundCreate`（音频初始化） | 1 |
    | 其余零散 | 是别的模块里的 INI 键（`HighlightSound` 在 UI、`CrushSound` 在类型数据） | — |
  - ⇒ **真实音频约 25–30 个函数**（与 §852-4 的"薄代码+数据驱动"一致）。我的 15 接近，GLM 的 348 错。
  - ⇒ **方法教训**：**"某个地址范围内出现该子系统的字符串" ≠ "整个范围都是该子系统"**。
    区间种子只能作为**候选提示**，必须再有一条函数级证据才能定类。

- **§854-4 [已证·GLM 覆盖率的真实分解]**
  | 层次 | 函数 | 占比 | 字节 |
  |---|---:|---:|---:|
  | **直接证据**（P0a 模块/P1 虚表/P2 导入/P3 字符串） | 6,356 | **49.2%** | 1,462,220（45.3%） |
  | 推论（P3 区间/P4 调用图/P5 簇填充） | 3,824 | 29.6% | 1,210,938（37.5%） |
  | 合计（它报的头条数字） | 10,180 | 78.8% | 82.9% |
  - 而"直接证据"里的 2,615 个通用容器误标再扣掉 ⇒ **可辩护的直接证据约 3,741（29%）**，
    与**我的 T1 = 4,284（33.2%）**在同一量级。

- **§854-5 [已证·合并出 canonical 地图（采用 GLM 的细分类，只用可辩护证据）]**
  规则：**T1 = GLM 的 P1（仅当类非通用）+ P0a + P2 + P3-string，并叠加我的 L1–L4（投影到 GLM 的分类名）**；
  **T2 = 调用图传播（≥3 个已标注邻居且 ≥70% 一致，最多 2 轮）**；**不使用区间/簇填充**。
  | 结果 | 值 |
  |---|---|
  | **T1 直接证据** | **4,284（33.2%）** |
  | T2 调用图（r1 +668 / r2 +545） | 1,213 |
  | **canonical 覆盖** | **5,497 / 12,916 = 42.6% 函数；2,091,344 / 3,225,845 = 64.8% 字节** |
  | tier 分布 | T1:glm-vtable 2,998 / T1:P0a-module 396 / T1:my-vtable 345 / T1:P3-string 240 / T1:my-import 205 / T1:P2-import 90 / T1:my-string 10；T2 1,213；未归类 7,419 |

- **§854-6 [已证·canonical 子系统表（GLM 细分类 × 可辩护证据）]**
  | 子系统 | 函数 | 字节 |
  |---|---:|---:|
  | **GameObj_Logic** | **2,207** | **1,047,853** |
  | Graphics_Blit_Shape | 500 | 118,491 |
  | UI_Gadget_Dialog | 489 | 92,982 |
  | Movement_Locomotion | 361 | 47,713 |
  | **Ini_Rules_DB** | **358** | **142,037** |
  | Net_Transport | 310 | 88,904 |
  | WOL_Online | 223 | 138,335 |
  | Main_Init_Flow | 148 | 33,615 |
  | File_Mix_FS | 142 | 32,742 |
  | AI_Team_Script | 134 | 20,191 |
  | Scenario_Map | 119 | 62,826 |
  | MP_Lobby_Session | 113 | 88,164 |
  | Input_Commands_Mouse | 69 | 18,324 |
  | WDT_WorldDom | 54 | 16,346 |
  | Sidebar_Radar_HUD | 49 | 39,168 |
  | Video_Bink | 40 | 5,275 |
  | File_Stream_Crypto | 36 | 3,552 |
  | Misc_Util_Mem | 30 | 2,870 |
  | Campaign_Meta | 26 | 13,864 |
  | SaveLoad | 22 | 14,046 |
  | Tactical_MapView | 18 | 7,719 |
  | Config_Registry | 12 | 6,076 |
  | Menus_Main_Intro | 12 | 24,085 |
  | **Audio_Sound_Music** | **10** | 3,120 |
  | Render_DDraw_Display | 8 | 2,250 |
  | Superweapon_Special | 7 | 20,796 |
  - ⇒ **GLM 的细分类确实比我的 12 粗桶有信息量**：它把 `Ini_Rules_DB`（358 函数 / 142 KB）
    从我的 `RESOURCE_IO` 里分离出来 —— **INI/Rules 数据库是个独立的大子系统**，
    这解释了为什么本项目在 ① 里反复撞到 `rulesmd.ini`/`artmd.ini` 的加载路径。
  - ⇒ 它把 NET 拆成 `Net_Transport`(310)/`WOL_Online`(223)/`MP_Lobby_Session`(113) 三块，
    比我一个 `NET`(642) 更有结构。

- **§854-7 [已证·产物]** `W131_subsystems\`
  | 文件 | 内容 |
  |---|---|
  | **`fn_subsystem_canonical.tsv`** | **12,916 行：entry/size/subsystem/tier/n_callers**（`tier` 列区分 T1 直接证据与 T2 推论） |
  | **`subsystems_canonical.tsv` / `subsystem_map_canonical.json`** | canonical 子系统表 + tier 分布 + 覆盖率 |
  | `merge_canonical.py` | 合并器（可复跑） |

- **§854-8 [未证·canonical 仍是 57.4% 未归类]** 剩余 7,419 个函数没有任何直接证据，
  且调用图传播因"虚调用不可见"而失效（§853-4）。要提高必须换方法（反编译特征、社区检测、手工标注）。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §854" in src:
    sys.exit("ABORT: §854 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §854", "2,615", "42.6%"):
    print("  %-10s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
