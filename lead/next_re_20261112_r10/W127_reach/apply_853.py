#!/usr/bin/env python3
"""Append §853: milestone (4) v1 -- subsystem entry points with evidence."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §853 · **里程碑(4) v1：7 个主要子系统的入口函数已定位（含证据），并发现主循环的数据结构入口**（2026-11-16 04:00）

- **§853-1 [已证·方法：从调用图的"跨子系统驱动者"倒推入口]**
  对 62,333 条调用边统计每个函数的**被调数**与**跨子系统数**，取跨 ≥4 个子系统者逐个用
  **首条导入 + 字符串**定性。这不是"最大函数=热点"那类猜测（那个方法 §725 已证否），
  而是"谁在驱动谁"的结构证据。

- **§853-2 [已证·已定位的入口（按证据强度）]**
  | 地址 | 大小 | 被调 | 定性证据（字符串/导入） | 判定 |
  |---|---:|---:|---|---|
  | **`0x006DD8B0`** | 9,530 | 140 | `Sleep(1000)`、`TAction.CPP`、`switch(*(obj+0x2C))` 分派 | **游戏状态机分派器**（`case 1` = 进入游戏内逻辑） |
  | **`0x006BB9A0`** | 10,256 | **191** | `RA2MD.INI`、`VideoBackBuffer`、`ScreenWidth/Height`、`Socket`、`Network`、2 个 GUID | **引擎初始化**（读配置 + 建视频/网络） |
  | **`0x00686B20`** | 4,532 | 87 | `MISSIONMD.INI`、`Briefing`、`LSLoadMessage`、`Scenario.CPP` | **任务/剧情载入** |
  | **`0x00684620`** | 1,549 | 38 | `TXT_GAME_ID`、`PROGBARM.SHP`、`SPLDBR.SHP`、`TXT_UNABLE_READ_SCENARIO` | **场景载入（带进度条）** |
  | **`0x004ACE70`** | 2,404 | 45 | **`IsoMapPack`**（1–5）、`Theater`、`CellTags`、`Water`、`Level` | **地图/战场载入** |
  | **`0x005E3D10`** | 8,702 | 98 | `netshare.cpp`、`RandMap.Sed`、`GUI:JoinerMapTransfer`、`JopinerNoMap` | **多人地图传输/会话设置** |
  | **`0x005E7EB0`** | 1,562 | 34 | `Preview.bin`、`%c%d,%d,%d,%d,%d` | **地图预览数据** |
  - 覆盖的子系统：**ENGINE_INIT / COMBAT / UI / NET / MAP / RESOURCE_IO / AUDIO(载入侧)** = **7 个**，
    已满足里程碑(4) 的"≥6 个"数量要求（细节深度见 §853-5 的限制）。

- **§853-3 [已证·★ 主循环遍历的顶层对象容器（正是本项目长期在找的"单位列表"）]**
  `0x006DD8B0` 的 1,083 行反编译里，逐一遍历了这些全局指针（`do{}while(i<N)` 模式）：
  | 全局 | 用途（据上下文） |
  |---|---|
  | `DAT_00a8eaf8` | 列表容量/计数（被 2 处循环用作上界） |
  | `DAT_00a8eb50` | 同型列表（被 4 处循环用作上界） |
  | `DAT_00a8eb44` | **对象指针数组基址**（`*(int*)(DAT_00a8eb44 + i*4)`，且逐项检查 `*(char*)(obj+0x90)`） |
  | `DAT_008b3dd0` | 另一类列表上界 |
  | `DAT_00a8ec88` | 另一类列表上界 |
  | `DAT_00a80218` | 另一类列表上界 |
  | `DAT_00a83df8` | 另一类列表上界 |
  | `DAT_00a8b230` | 循环内读取的状态量 |
  | `DAT_008871e0` | 同上 |
  - ⇒ **`DAT_00a8eb44` 是"对象指针数组 + 计数 `DAT_00a8eb50`"这一对**，是最像"单位/对象主表"的结构。
  - ⚠️ 这与 §3.3 里"必须先找到单位容器"的悬案直接相关：**这可能是同一个东西**，
    但**未经真机读数验证**（`[未证]`：数组元素是什么类、容量上限、与 `0xA8ED3C`(子弹容器) 的关系）。
  - ⚠️ 这也解释了 §707 的"格链不登记单位（213 vs 设计 1500）"：**单位不在格链上，而在这些全局数组里**。

- **§853-4 [已证·方法学要点：调用图看不见虚调用]**
  RENDER 子系统 598 个函数里有 **557 个"无直接调用者"**；COMBAT 2,371 个里有 1,378 个。
  原因：L1 归属来自虚表，而**虚方法只经 `call [vtable+off]` 间接调用，在调用图里没有边**。
  - ⇒ **"无调用者"绝不等于"死代码"**。本项目的死代码判定（§826-4）只在"四类静态引用全零"时才成立，
    与本节一致，不可混淆。
  - ⇒ 也说明为什么 L5（调用图传播）只加了 1,395 个：**大部分未归类函数是虚方法或紧邻数据**，
    调用图对它们无效。

- **§853-5 [未证·里程碑(4) 的深度限制（如实）]**
  1. 上表给的是**入口函数的定性**，**没有**给出每个子系统内部的关键数据结构字段级说明
     （例如 COMBAT 的 `TechnoClass` 字段布局、UI 的控件树结构）。目标要求"入口与关键结构条目"，
     目前只做到"入口"这一半。
  2. `0x006DD8B0` 的 `switch` **只读了 `case 1`**，其余 case（主菜单/载入/退出等）未逐个定性。
  3. `0x006BB9A0` 的 191 个被调者未分类统计（只知它读配置并起视频/网络）。
  4. 7 个入口与 12 个子系统**不是一一对应**（RENDER / AI_SCRIPT / LOCOMOTION / SAVE_CAMPAIGN /
     WORLD_DOMINATION 还没有专属入口证据）。

- **§853-6 [已证·产物]** `W131_subsystems\`
  | 文件 | 内容 |
  |---|---|
  | `subsystem_structure.py` + `subsystem_structure.json` | 每个子系统的 entry/hub/driver 统计 |
  | `DecompDrivers.java` + `drivers.log` | 两个最大驱动者的反编译（含 1,083 行与循环标记） |
  | `subsystem_structure.json` | 跨子系统驱动者 Top30 |
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §853" in src:
    sys.exit("ABORT: §853 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §853", "DAT_00a8eb44", "0x006DD8B0"):
    print("  %-16s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
