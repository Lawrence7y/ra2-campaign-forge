#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qc151_trip.py — QC151 · `U0400` 首趟**载体趟脚本**（★ 本卡**不运行**它）。

=============================================================================
★★★ 授权与边界（★ 逐字承自 `lead\\cards\\QC141.md`）
=============================================================================
本脚本是 `QC141`（**授权提请单**）§9 签署后的**执行载体**。★ `QC141` 本件
**不构成运行授权**（`QC141:3`）；★ 只有用户在 `QC141:§9` 签署后，
本脚本才可被执行者运行。★ **本卡的交付物是"脚本 + 报告"**，
★ **本卡未运行本脚本、未启动任何游戏进程、未做任何真机读数**。

★★ **首趟只答两件**（`QC141:17`）：**启动观测** · **能否进图**
   （`L-A` 进对局 ∧ `L-B` 取到实际加载标识 ∧ `L-C` 等于预先固定的目标）。
★★ **本单不含**（`QC141:18`）：内存读 · 任何断点（`A4`/`A5`）· 注入 ·
   写地图数据面 · 改任何游戏文件内容 · 性能/卡顿判据。

=============================================================================
★★★ 禁止面（★ 连**伪装形态**一起写进注释；`QC141:171`）
=============================================================================
★★ **经 `ra2loader.exe` / 任何 loader / stub / 注入器启动游戏 —— 一律禁止**。
   ★ `ra2loader.exe` 是**注入型**启动器：`LoadLibraryA` + `GetProcAddress`
     加载 `ra2render.dll`，而该 DLL 在 `DLL_PROCESS_ATTACH` 上**无条件改写
     游戏代码 6 字节**（`QC141:88` 逐字）⇒ ★ **一经它启动即落入"改码/注入"
     禁令，本趟证据作废**。
   ★★ **明令禁止的伪装形态**（★ 本脚本**零处**使用，此注释即为禁令本身）：
     (a) **批处理间接调** —— 例如 `subprocess.Popen(["ra2opt_play.bat"])`
         或 `cmd /c ra2opt_play.bat`（该 bat 内含 `start "" /high "gamemd.exe"`）；
     (b) **`start` 转接** —— `cmd /c start "" gamemd.exe`；
     (c) **`lpApplicationName` 指向 shell** —— 即 `Popen(["cmd.exe",...])`
         再把 exe 名当参数塞进去（★ 本脚本**显式传 exe 全路径给
         `lpApplicationName`**，见 `Popen` 调用处的 `[EXE]` 标记）；
     (d) **"先起 loader 再按名找 `gamemd.exe`"** —— 即先 `Popen(ra2loader.exe)`
         再 `find_pids('gamemd.exe')` 把被注入的进程当成本趟对象。
   ★★ 本脚本**只允许**直启 `carrier\\gamemd.exe`（`QC141:171` 末句）。

★★ **禁止**（`QC141:171` / 任务书 ⑨）：
   - 任何**断点**（`DR0`–`DR7`；★ 含硬件断点伪装成 `SetThreadContext` 写
     `Dr0`/`Dr7`，以及 `DebugActiveProcess` 间接设断）；
   - **注入**（含 `CreateRemoteThread` / `QueueUserAPC` / `SetWindowsHookEx` /
     `VirtualAllocEx` + `WriteProcessMemory` 的经典组合）；
   - **写**目标内存（`WriteProcessMemory` / `VirtualProtectEx`）；
   - **读**目标内存（`ReadProcessMemory`）—— ★ **本单不含内存读**（`QC141:18`）；
   - 改任何**游戏文件字节**（★ 含桩槽 / patch / stub / hook / 替字节）；
   - 改 `RA2MD.INI`；
   - 经 loader 启动；
   - `taskkill` **非本卡自己 `Popen` 的 pid**（★ 只杀 `self.launch_pid`）。
★★ 上述 API **本脚本零调用**；★ 静态自检 #2 用 AST 遍历全部 `ast.Call` 证明。

★★ **允许改的**（`QC141:172`）：仅本卡写域内的报告/日志 · 载体内副本 ·
   `ra2opt_play.bat` 的**文本命令行**（跑后**逐字节**还原）。★ 本脚本对
   `ra2opt_play.bat` 的做法是**不改**（★ 本趟直启 exe，不需要它）。

=============================================================================
★★★ 两控（跑前跑后各一次；`QC141:§7`）
=============================================================================
控一：`ra2bench\\gamemd.exe` `sha256 = 73201cc0…f67476` / size `4825360`（`QC141:149`）。
控二：同件 `VA 0x00829284 / file_off 0x429284` 8 字节 = `4E 6F 20 4E 61 6D 65 00`
      （`QC141:150`）。★ `file_off` 与 `VA` **成对写出**（`D-79`）。
★★ **两控都真读文件**（★ 不缓存跑前结果冒充跑后）。

=============================================================================
★★★ 零写自证 `T0`/`T1`（`QC141:132`/`:140`）
=============================================================================
★ **634 件** = `ra2bench` 顶层 **410** + `ra2youli` `*.yrm` **224**
  （★ 两数**由本脚本自己复算**，★ 不照抄常量）。
★ `T0` 跑前落、`T1` 跑后落，★ **逐件 sha 比对**并发 `diff`。
★★ 载体件**逐字节还原并给还原后 `sha256`**。

=============================================================================
★★★ `except.txt` 复位 + 集合差（`QC141:134`/`:141`）
=============================================================================
★ 跑前**从只读母本**（`ra2bench\\except.txt`，`ca175a71…f39d` / `26515 B`）
  **复制回载体**：★ **先校验母本哈希、后复制**（★ 顺序不可颠倒）。
★ 复制后**复读载体并复核**（★ 不是"写完就信"）。
★★ **母本只读、绝不写母本**（★ 本脚本对母本**只** `open(...,'rb')`）。
★★ 判定**只用集合差**：
   - ★ **不得**用 `post[len(pre):]` 切片（★ 那假定"appending-only"，未证）；
   - ★ **不得**用 `sha` 变化判 crash（★ 游戏自身会重写该文件）。
★ 本脚本用**行集合差**：`new_lines = [ln for ln in post_lines if ln not in pre_counter]`，
  以 `collections.Counter` 做**多重集**差（★ 重复行也正确计入）。

=============================================================================
★★★ 导航与采帧（`QC141:§2`/`§3`）
=============================================================================
★ 导航链 `mainmenu(700,218)` → `skirmish(700,304)` → `start(700,262)`
  （`QC141:93`；★ 逻辑坐标，`800×600`）。
★ 点击（**屏**坐标）`(1580,724)` / `(1580,682)`（`QC141:94`）。
★★ **采帧固定 `800×600`**（`QC141:79`）。
★★ 若实测主窗**不是** `800×600` ⇒ ★ 记 **`frame_resolution_mismatch`**，
   且该帧 `L-A` 记 **`null`**（★ **不得记 `False`**，`D-53`）。
★ `L-A` 调用**既有** `qc95_classify.py`（`QC141:74`/`:75`）：
  `lead\\qc95_tactical_criterion\\_probe\\qc95_classify.py`，
  函数 `load_rgb(p)` @ **:15** / `features(w,h,img)` @ **:46** / `classify(f)` @ **:83**。
  ★ **不得改它**（★ 本脚本只 `import`，零写入）。

=============================================================================
★★★ 字段 `F-1`…`F-9`（★ 全部**根限定**；`QC141:§5`）
=============================================================================
★★ `F-2`/`F-4`/`F-5` **必须写全路径（含根名）** —— ★ 因为同名文件在
   `ra2bench\\` 与 `ra2youli\\` 下 **3/5 不同件**（★ `QC141:39`；本卡已复算：
   `U0050`/`U0200`/`U0800` 不同，`U0100`/`U0400` 同）。
★ `F-1` = `scen_index_pre`：读 `RA2MD.INI`，★ **只在 `[Skirmish]` 段内**取
  `ScenIndex`（★ 按 INI 段头解析；`QC157:2`）。★ 记录**段名 + 行号 + 原文**，
  ★ **同段内若有多条 `ScenIndex` 全部列出**并声明取哪条（★ 取**同段第一条**，
  ★ 不再有"全文第一条"策略）。
  ★★ **找不到 `[Skirmish]` 或段内无 `ScenIndex` ⇒ 记 `null`**，
  ★★ **绝不回落到"全文第一条"**（`QC157:2`，★ 那种写法证明不了实际地图身份）。
★ `F-3` = `scen_index_post`：`RA2MD.INI` **由游戏进程在对局开始时改写
  `[Skirmish]`**（`QC141:120`）⇒ ★ **`post` 才是该趟实际用的槽**。
★ `F-6` = `in_tactical`（`L-A`），分辨率不符时记 `null`。
★ `F-7` = 帧上地图面板：★ **人工读图、非自动判据** ⇒ ★ 本脚本**记 `null`
  并置 `needs_human`**，★ 绝不自动编造。
★ `F-8` = `except.txt` 完整前后件 + 各自 `sha256`。
★ `F-9` = 窗口形态（主窗矩形 / 分辨率）：`GetWindowRect`。
  ★ 判 `0x0` 退化**必须用主窗 `GetWindowRect`**（`D-59`）。

=============================================================================
★★★ ⑦ 采帧（★ 只采**目标图帧**一张；`QC157:1` 裁决）
=============================================================================
★★ **伪反控已删除**（`QC157:1`，★ 用户点名的头号缺陷）：
  ★ 旧版 `dual_capture()` 只是**对同一个窗口连续截两张图**，却把第二张标
    `label="other"`，并在 `reverse_control_5_other` 里写 `in_match = False`
    —— ★ 那是"**未换图却产出 `in_match=False`**"的**伪证据**，已**全部删除**。
  ★★ `--other-map` **一并移除**（`QC157:1` 选项 A）：★ 用户已裁决"其他地图
    反控改**后续独立一趟**" ⇒ 本脚本**不再提供**该开关，★ 结构上**不可能**
    产出任何 `other` 判定。
  ★★ 本趟**只采目标图帧** `frame_target_01.png`（`label="target"`）；
    ★ `L-A`（`qc95_classify`）的结论**唯一挂在该帧上**。
  ★ 反控⑤（已进对局为真而目标地图匹配为假的样本）⇒
    ★ **本趟不造**，★ 交由**后续独立一趟**（真换图后）产出。


★ ★ `T4`（`222799 / 93c2974b…`）与母本（`92332 / cb5785a1…`）★ **均不写死**
   为唯一目标（★ 任务书 ⑧）—— ★ 一切由 `--target-map` + `--target-sha256` 决定。

=============================================================================
★★★ ⑧ 目标地图**参数化**（★ 用户尚未选；`QC141:§9-A`）
=============================================================================
★ 必填：`--target-map <全路径>` + `--target-sha256 <值>`。
★ 启动前**校验该文件哈希 = 给定值**，★ **不等 ⇒ 硬停**（`EXIT_TARGET_MISMATCH`）。
★★ `--target-map` 支持 `[2]` 等特殊字符 ⇒ ★ 全程 `os.path` / `open()` 直读，
   **不经 shell**（★ 等价于 PowerShell 的 `-LiteralPath`，`D-44`）。

=============================================================================
★★★ ⑨ 上限与禁止（★ 写进**退出逻辑**，不只是注释）
=============================================================================
★ `MAX_LAUNCHES = 5` · 单趟 `TRIP_BUDGET_S = 180` · 单阶段 `STAGE_TIMEOUT_S = 30`。
★ 三者在**运行期**被检查，越限 ⇒ **非 0 退出**（★ 见 `_check_budget()` /
  `_bump_launch()`）；★ 不是纸面常量。

=============================================================================
★★ 口径（`QC141:5`）
=============================================================================
★ 中文；★ 每数追 `文件:行`；★ **未读到写「未测」**；★ **不可测写 `null`**，
★ **绝不写 `false`/`0`**；★ 凡 `file_off` 与 `VA` 成对写出（`D-79`）。

★ 本脚本**不得**被本卡运行（铁则 1）。★ 本卡只做**静态自检**（AST）。
"""
from __future__ import annotations

import argparse
import ast
import collections
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ★★ QC197/P1：探针进程 **DPI 感知**（先例 `qc63_trip.py:47`；
#   `MENU_NAV_DESIGN_v1.md:§1.1/§4.1-P1`）——T18 实测 533×400 =
#   800×600 物理 ÷ 150% 的**探针侧 DPI 虚拟化**，根因在此。
#   模块导入即生效 ⇒ 此后 find_main_window/rect_of/click_*/capture_frame
#   读到的坐标全部是**物理像素**（★ 自身进程声明，不触碰任何其它进程）。
ctypes.windll.user32.SetProcessDPIAware()

# ===========================================================================
# §0 · 路径与写域（★★ `QC162`：★ 运行期写域 = 本趟批准域，**绝不**是本卡目录）
# ===========================================================================
# ★★ 运行期写域（★ `QC162:W1`）解析优先级（★ `main()` 内定稿）：
#   ★ `--out-dir`(cli) > `QC151_OUT_DIR`(env) > 默认 `lead\qc161_u0400_trip`。
# ★★ 默认值 = **`lead\qc161_u0400_trip`**（★ 即本趟**批准**的趟写域，
#   ★ `QC162:W1`）——★ **不是**本卡目录 `qc151_u0400_trip`。
# ★★ 本卡目录（`qc151_u0400_trip`）**只放卡面产物**（脚本本件 + 三件
#   `QC162_FIXES.*` + 历史脚本副本）——★ **运行期零写入**（静态自检 #2 用
#   grep 证明：代码面无任何以本卡目录为落盘点的引用）。
ROOT = Path(r"D:\Project\ra2-campaign-forge")
BENCH = ROOT / "ra2bench"
YOULI = ROOT / "ra2youli"
LEAD = ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead"

OUT_DIR_ENV_VAR = "QC151_OUT_DIR"
DEFAULT_OUT_DIR = (LEAD / "qc161_u0400_trip")

# ★ 写域（`QC141:168` + `QC162:W1`）：★ 本脚本运行期产物**只**往这里写。
#   ★ **不得**是 `LEAD / "qc151_u0400_trip"`（★ 本卡目录只留卡面/报告/自检产物）。
#   ★ `WORKDIR` 在本模块导入时即解析（★ 优先级：环境变量 > 默认值 `qc161_u0400_trip`）；
#     ★ `--out-dir` 传入的 CLI 值在 `main()` 内**覆盖**本模块级变量
#       （★ 见 `main()` 首段 `global WORKDIR`；同时留痕 `out_dir_source`）。
WORKDIR = Path(os.environ.get(OUT_DIR_ENV_VAR) or DEFAULT_OUT_DIR)

# ★ 严格只读的外部助手（★ 只 import，绝不写；见模块 docstring §导航与采帧）
QC95_PATH = LEAD / "qc95_tactical_criterion" / "_probe" / "qc95_classify.py"

# ★ 载体内五个文件（`QC141:152-160`）
CARRIER_FILES = ("gamemd.exe", "ra2loader.exe", "ra2render.dll",
                 "ra2opt_play.bat", "except.txt")

# ★★ [PATHLEN 20261021] 载体**目录**长度门禁（★ 硬门禁，不是建议值）
#   ★ 门禁值 = 130 字符：★ 载体**目录**（★ 不含件名）字符数 **> 130**
#     ⇒ ★ 立即失败并给出该目录与长度。
#
#   ★★ 口径裁决（2026-10-21 主会话，27 趟历史实证）：★ 判据作用在**目录**上，
#     ★ 不是件的完整路径上。证据（`_gate_recheck2.py` 复跑）：
#       · `frame_target`/`frame_early` 任一为 800×600 或 533×400 的 **10 趟**，
#         载体目录长全部 ≤130（116/129/130）；
#       · 旧 `carrier_trip/carrier_<stamp>_<pid>` 命名族的 **12 个目录全部 =141**，
#         **零正常帧**（6 个 464×191、2 个空占位、4 个无帧）；
#       · 若改按**件路径** 120 卡，则历史 **27/27 趟全部被拦**，含两趟已成功趟
#         （`l1a_20261020` 件路径 140、`t55k_20261020` 件路径 141）⇒ 该口径被证伪。
#     ★ 130 是**已实证的安全上界**（`l1a_20261020`=129、`t55k_20261020`=130 均成功）。
#
#   ★★ 项目坑（★ 与门禁值**不是同一个数**，★ 不得互相替代）：
#     ★ **≥131 字符**是本项目**已实证的故障阈值**（QC193/D-117：141 目录族的
#       464×191「Unable to initialize 'ra2.csf'」框）——★ 131 是**故障线**；
#     ★ **130** 是取其下留 1 字符余量的门禁值（★ 判据落在故障发生之前，
#       ★ 不是对 131 的重述）。
CARRIER_PATH_MAX_CHARS = 130          # ★ 门禁值（硬失败线，★ 作用在载体**目录**）
CARRIER_PATH_KNOWN_BAD_CHARS = 131    # ★ 历史实证故障阈值（★ 仅对照记录，不作门禁）


def carrier_pathlen_violations(paths) -> list:
    """★ [PATHLEN] 返回超门禁的载体**目录**：`[(dir_str, char_len), ...]`。

    ★ 口径：★ 按 **Python `len(str)` 字符数**计（★ 不含件名，★ 见上方裁决）。
    ★ 传入的每个元素都被当**目录**判；调用方不得把件路径传进来。
    """
    out = []
    for p in paths:
        s = str(p)
        if len(s) > CARRIER_PATH_MAX_CHARS:
            out.append((s, len(s)))
    return out


def carrier_pathlen_gate(dirs, where: str, rec=None) -> None:
    """★ [PATHLEN] 硬门禁：★ 任一载体**目录** > 130 字符 ⇒ 立即失败。

    ★★ 失败语义沿用本文件**既有**的载体清单拒绝机制（`RuntimeError`，与
      「★ 拒绝不安全件名」「★ 拒绝越界目的路径」同族）⇒ ★ **不新增退出码**。
    """
    bad = carrier_pathlen_violations(dirs)
    if not bad:
        return
    if rec is not None:
        rec.add("CARRIER", "pathlen_gate", {
            "max_chars": CARRIER_PATH_MAX_CHARS,
            "known_bad_chars": CARRIER_PATH_KNOWN_BAD_CHARS,
            "scope": "carrier_dir_only",
            "violations": [{"dir": p, "chars": n} for p, n in bad],
        }, f"script:{where}",
                note="★★ [PATHLEN] 载体目录超门禁 ⇒ 硬停（★ 未 mkdir、未启动）")
    _detail = "; ".join(f"{p}（{n} 字符）" for p, n in bad)
    raise RuntimeError(
        f"★ [PATHLEN] 载体目录超门禁（>{CARRIER_PATH_MAX_CHARS} 字符）"
        f"@{where}：{_detail}；"
        f"★ 项目已实证故障阈值为 >={CARRIER_PATH_KNOWN_BAD_CHARS} 字符，"
        f"本门禁取其下留余量的 {CARRIER_PATH_MAX_CHARS}")

# ===========================================================================
# §1 · 两控常量（★ 逐字承自 `QC141:149`/`:150`/`:160`；★ 真值不写死为参数）
# ===========================================================================
CTRL1_SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
CTRL1_SIZE = 4825360

# ★ 控二：`VA 0x00829284` / `file_off 0x429284`（★ 成对写出，`D-79`）
CTRL2_VA = 0x00829284
CTRL2_FILE_OFF = 0x429284
CTRL2_BYTES = b"\x4E\x6F\x20\x4E\x61\x6D\x65\x00"   # "No Name\0"

# ★ 母本 `except.txt`（★ 只读；★ 绝不写母本）
EXCEPT_MASTER = BENCH / "except.txt"
EXCEPT_MASTER_SHA256 = "ca175a71c8a25228685d28bf5b3a9d883665aec429dc03c46478cf486672f39d"
EXCEPT_MASTER_SIZE = 26515

# ===========================================================================
# §2 · 上限（★ 写进退出逻辑）
# ===========================================================================
MAX_LAUNCHES = 5          # ★ 最多 5 趟（`QC141:169`）
TRIP_BUDGET_S = 180.0     # ★ 单趟 ≤180 s（`QC141:169`）
STAGE_TIMEOUT_S = 30.0    # ★ 单阶段超时 ≤30 s（任务书 ⑨）

# ===========================================================================
# §3 · 导航链（★ 逻辑坐标，`800×600`；`QC141:93`）
# ===========================================================================
NAV_CHAIN = (("mainmenu", 700, 218), ("skirmish", 700, 304), ("start", 700, 262))
# ★ 点击（**屏**坐标；`QC141:94`）
# ★★ QC197/P5：上二屏坐标 = 母链 2560×1440 全屏窗口时代的**遗产**，U 线
#   800×600 窗口下语义失效（T18：5 次点击全部落在窗口外）⇒ **退役、不再
#   执行**（常量保留仅作溯源；导航改走 NAV_SIG_PLAN 三段带闸子阶段）。
CLICK_SCREEN = ((1580, 724), (1580, 682))

FRAME_W, FRAME_H = 800, 600      # ★ 采帧固定 800×600（`QC141:79`）
MAIN_WINDOW_TITLE = "Yuri's Revenge"

# >>> QC151FS-BEGIN const（嵌套哨兵：删本块=还原锚 5b435487…；缺省 off=行为与改前逐字节一致）
# ★★ QC151FS 全屏模式适配状态容器（cnc-ddraw `windowed=false` ⇒ 独占/边框全屏）。
#   ★ 实证基线（20261019 boot-hang 破解实测）：全屏窗=整屏尺寸；
#     渲染面=屏幕左上 (0,0) 起 800×600 **不缩放**；PrintWindow（旗标 0/2）对
#     独占面返回黑/失败；桌面拷贝（GDI 屏 DC BitBlt）对全屏内容**有效**；
#     菜单 busy-loop 烧 ~1 核 ⇒ CPU 档位不得用作状态判别。
_QC151FS = {"on": False, "fg_attempts": 0, "fg_fail": 0,
            "arrival": None, "baseline": None,
            "arrival_polls": [], "poll_errs": [], "clicks": []}
# ★ 到达判据阈值（设计定值；T55 真机标定=待办，按 fs_arrival 遥测复准）：
#   ★ FS_LUMA_FLOOR=8：桌面拷贝纯黑帧均值实测 0-1；logo/菜单帧均值实测
#     ~55-60（diag_boot_longwatch.py:4 头注）⇒ 8 居黑/非黑判别带，仅拒纯黑帧。
#   ★ FS_LOGO_DIFF_MIN=15：整帧 800×600 平均绝对差；同态帧噪声=0（PrintWindow
#     时代同态帧逐字节同，锚 :1796 实证）；logo→菜单为整版面切换（量级 ≥40）
#     ⇒ 15 ≈ 动态范围 6%，远高于噪声、远低于真实换面。
#   ★ 菜单签名臂（**判定**）：复用 SCREEN_SIG["mainmenu"]（T20/T21 真机校准）
#     经 `_sig_match` 子集±3 + absent 否决——零新增魔法数。
#   ★ diff 臂（**仅遥测**）：非黑 ∧ 与 boot 基线帧差 ≥ FS_LOGO_DIFF_MIN。
#     ★ 不用于到达判定：片头影片帧同样满足该臂（逐帧异于静态基线），仅凭它
#     无法区分菜单/影片 ⇒ 只落 fs_arrival 遥测留档（回执 §判据依据同文）。
FS_LUMA_FLOOR = 8                # ★ 黑帧门（0-255 亮度均值）
FS_LOGO_DIFF_MIN = 15            # ★ 遥测臂：与基线帧平均绝对差阈值
FS_SCALE = 1.0                   # ★ 全屏不缩放 ⇒ 直通映射系数 1.0（替换窗口时代 533×400 DPI 虚拟化 ×0.667 换算语义）
FS_RENDER_ORIGIN = (0, 0)        # ★ 实证：渲染面自屏幕左上 (0,0) 起（叠加窗口原点偏移）
# <<< QC151FS-END const

# ★ `S-4` 注入面闸门钩子（★ 大小写不敏感**子串**；`QC141:89`）
S4_NEEDLES = ("ra2render", "ra2loader")

# ===========================================================================
# ★★ [U8 20261021] `--allow-loader` 授权通道（★ 默认关；★ 唯一授权路径）
# ===========================================================================
# ★ 依据：Notion U1–U9 裁决（`ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` §300）：
#   「U8 同意单独立项……立项四条件：① `--allow-loader` **默认关**、
#     **只对指定 trip-id 生效**、基线趟 `S-4` 照旧」。
#
# ★★ 本块是 §1 禁止面（`:21-35`）的**唯一**例外通道，且**不是**解禁：
#   - `ra2loader.exe` 仍是**注入型**启动器（`LoadLibraryA` + `GetProcAddress`），
#     `ra2render.dll` 在 `DLL_PROCESS_ATTACH` 上仍会改写游戏代码 6 字节；
#   - 禁止面的 4 种**伪装形态** (a) 批处理间接调 (b) `start` 转接
#     (c) `lpApplicationName` 指向 shell (d) 先起 loader 再按名找 `gamemd.exe`
#     —— ★ **全部仍然禁止**，本通道只新增 (e) **显式授权直启 loader**。
#   - ★ 授权趟的证据**仅可用于 B 臂（B0/B1）对比**，
#     **不得**用于 A 臂基线，**不得**用于 ② 的崩溃复现率统计。
#
# ★★ 授权判据 = **双键**，缺一不可：
#   1. `--allow-loader`（`store_true`，缺省 `False`）
#   2. `TRIP_ID` **逐字等于**命令行 `--trip-id` 的原始字符串
#      （`--trip-id` 未给 ⇒ `TRIP_ID` 是随机生成值 ⇒ 必然不等 ⇒ **天然 fail-closed**）
#   ★ 未给 `--trip-id` 时**即使**给了 `--allow-loader` 也**不授权**（判据 2 不成立）。
ALLOW_LOADER_EXE = "ra2loader.exe"     # ★ 授权时的启动目标（载体内的注入型 loader）


def allow_loader_authorized(args, trip_id: str) -> bool:
    """★★ [U8] 判定本趟是否获得 `--allow-loader` 授权（★ 双键，fail-closed）。

    ★ 返回值语义：
      - `True`  ⇒ 允许直启 `ra2loader.exe`，且 `S-4` 命中降级为 WARN；
      - `False` ⇒ 行为与授权前**逐字相同**（直启 `gamemd.exe`，`S-4` 命中即 62）。

    ★★ 为什么要求 `--trip-id` 必须显式给出：
      `TRIP_ID` 在 `--trip-id` 缺省时由 `new_trip_id()` **随机生成**
      （见 `main()` 内 `TRIP_ID = ... else new_trip_id()`），
      而随机值不可能等于命令行字符串 ⇒ 判据 2 自动失败 ⇒ 不会误授权。
      ★ 这是**结构性 fail-closed**，不是靠调用方自觉。
    """
    if not getattr(args, "allow_loader", False):
        return False
    raw = getattr(args, "trip_id", None)
    if not raw or not str(raw).strip():
        return False                       # ★ 未给 --trip-id ⇒ 不授权
    return str(raw).strip() == str(trip_id).strip()

# ★★ QC184：★ 64 位句柄/指针的**哨兵值**（★ 口径与 `ctypes` 的返回一致）。
#   `INVALID_HANDLE_VALUE` 语义值是 -1；★ 但句柄型（`HANDLE`/`HMODULE`/`HWND`…
#   = `c_void_p`）作为 `restype` 时，`ctypes` 按**无符号指针**取值
#   （64 位 → 2**64-1；32 位 → 2**32-1）⇒ ★ 直接写 `h == -1` **恒为假**
#   （★ QC183 只补了 `restype`、漏改这处比较）。
#   ★ 故统一用 `c_void_p(-1).value` 作哨兵，★ 两种字长下都成立。
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
# ★★ QC184：★ 模块条数硬上限。`cbNeeded` 是 **OS 回填**值，★ 若异常巨大，
#   直接按它分配数组会抛 `MemoryError`（★ 属 `Exception`，但本趟不得让它
#   以"未捕获回溯"形态冒泡）⇒ ★ 超限即判"不可判定"，★ 走枚举失败收口。
S4_MAX_MODULES = 65536
# ★★ QC184：★ `S-4` 闸门**判定容器**（★ 模块级，★ 跨 `main()` 边界可读）。
#   ★ 取代旧"反读 `s4_module_table.txt` 的文字内容去猜退出码"的做法——
#     文件读本身可能抛 `OSError`/`FileNotFoundError`（★ 仍未捕获回溯）。
S4_VERDICT = {"gate": None, "exit_code": None, "err": None}

# ===========================================================================
# §4 · ★★ 退出码常量全表（★ 值无重复；★ 静态自检 #6 核验）
# ===========================================================================
EXIT_OK = 0
EXIT_PRECHECK_SHA_MISMATCH = 10      # 控一失败
EXIT_PRECHECK_SIG_MISMATCH = 11      # 控二失败
EXIT_TARGET_MISSING = 12             # --target-map 文件不存在
EXIT_TARGET_SHA_UNREADABLE = 13      # --target-sha256 未给或非法
EXIT_TARGET_MISMATCH = 14            # ★ 目标哈希 ≠ 给定值 ⇒ 硬停（任务书 ⑧）
EXIT_EXCEPT_MASTER_SHA_MISMATCH = 15 # ★ 母本哈希不符 ⇒ 不复制
EXIT_EXCEPT_RESET_VERIFY_FAILED = 16 # ★ 复制后复读复核失败
EXIT_LAUNCH_LIMIT = 17               # ★ 超过 MAX_LAUNCHES
EXIT_TRIP_BUDGET = 18                # ★ 超过 TRIP_BUDGET_S
EXIT_STAGE_TIMEOUT = 19              # ★ 单阶段超过 STAGE_TIMEOUT_S
EXIT_LAUNCH_FAILED = 20              # Popen 失败（★ 保留：由文档化异常路径收口）
EXIT_PID_NOT_FOUND = 21              # ★ find_pids 查不到（★ 绝不用 launch_pid 兜底）
EXIT_WINDOW_NOT_FOUND = 22           # 主窗未出现
# ★★ `QC169` 新增（★ 值无重复；★ 承接第 1/3 项的收尾失败码）
EXIT_CARRIER_NOT_OWNED = 23          # ★ 载体所有权不成立 ⇒ **启动前**拒绝（第 1 项）
EXIT_TERMINATE_FAILED = 24           # ★ 本趟进程终止未确认（第 3 项）
EXIT_EVIDENCE_VERIFY_FAILED = 25     # ★ 证据搬出后逐件验 SHA 失败（第 1 项）
EXIT_MANIFEST_FAILED = 26            # ★ 删除前清单 / 最终 MANIFEST 落盘失败（第 1 项）
EXIT_CARRIER_DELETE_FAILED = 27      # ★ 拒删 / 删除失败 / 删除后仍有残留（第 1 项）
EXIT_PID_IDENTITY_UNVERIFIED = 28    # ★ 创建时间缺失 ⇒ PID 身份不可核验（fail-closed）
EXIT_INJECTION_SUSPECTED = 62        # ★★ S-4 命中 ⇒ 硬停、本趟作废、落盘模块表原文
EXIT_MODULE_ENUM_FAILED = 63         # ★★ 枚举失败 ⇒ 同样硬停（★ 不当"未加载"放行）
EXIT_T0_T1_DIFF = 64                 # ★★ 零写自证失败（634 件逐件 sha 有差）
EXIT_RESTORE_FAILED = 65             # ★ 载体件逐字节还原失败
EXIT_INTERNAL_ERROR = 70             # 兜底（★ 仅最外层一处，见 _main_wrapper）
# ★★ QC176 / v6 §6.1.1 U-6：★ 未处理 `KeyboardInterrupt` 的**实际**进程退出码
#   （★ 与解释器真实行为一致：128 + SIGINT(2) = 130）⇒ ★ 记录不得再声称 70/71。
EXIT_KEYBOARD_INTERRUPT = 130

# [FAILFAST] 进程死亡 fail-fast 退出码（Notion 裁决1 附加项）
#   与既有退出码表不冲突；语义=主进程在等待期内自行退出（非超时、非 harness 错误）。
EXIT_PID_DEAD = 29

# ★★ `QC162:W2`：★ **模块级收尾失败码容器**（单元素 list）。
#   ★ `main()` 的 `finally` 在**收尾跑完后**写入本容器（★ `main()` 的
#     `return` 已发生，★ finally 改不了那个 return —— 外部裁定指出的缺陷）。
#   ★ 最外层 `_main_wrapper()` 在 `main()` **返回后**读本容器，★ 收尾失败
#     （≠`EXIT_OK`）⇒ **以收尾失败码覆盖** `main()` 的返回码 ⇒ ★ 进程退出码
#     **真的非 0**（★ 见 `_main_wrapper` 的合并逻辑）。
#   ★ 初值 `EXIT_OK`：★ 若 `main()` 未进 try/finally（启动前即失败）⇒ 不改写。
FINALIZE_CODE = [EXIT_OK]

# ★★ `QC169` 第 1/3 项：★★ **模块级可外达**收尾失败容器。
#   ★ `finally` 里的**局部变量**（如旧 `term_ok`）既改不了已发生的 `return`，
#     ★ 也会被随后 `finalize_trip` 的成功码覆盖 ⇒
#     ★ 一切收尾失败（终止未确认 / 证据验 SHA 失败 / 清单失败 / 拒删 / 残留 /
#       PID 身份不可核验）★ **一律先进本容器**，★ 由 `merge_cleanup_code()`
#       统一合并进最终退出码。
CLEANUP_FAILURES: list = []

# ★ 最外层最终落盘用（★ 保证最终 JSON/日志与**实际最终码**一致；第 3 项）
ACTIVE_REC = [None]

# ★★ QC179 / v7 §2.1 U-2：★ **跑前冻结**的母本基线（★ 不可变实盘基线）。
#   ★ 在启动前计算并冻结，★ finally 只引用此基线、不再现采源树。
#   ★ 枚举失败/缺树/截断均显式失败（★ walk_errors 非空 ⇒ 基线不成立）。
FROZEN_MOTHER_BASELINE: list = [None]   # [0] = dict | None
FROZEN_MOTHER_ERRORS: list = []         # walk onerror 收集

# ★★ QC176 / v6 §6.1.1 U-6：★ 最近一次 `write_final_manifest()` 的**内存副本**。
#   ★ 入口最终合并**之后**据此用**实际最终码**重写 `MANIFEST.json`
#     （★ 补"晚发生失败"的终态引用，★ 避免 MANIFEST 停留在旧 PASS/旧失败集）。
LAST_FINAL_MANIFEST: list = [None]

# ★ 本趟**新建**的执行载体（★ `os.mkdir` 成功后**立即**登记 ⇒ finally 可回收）
#   ★ `identity` = 创建时登记的目录对象身份（`st_dev`/`st_ino`），QC176/U-4
TRIP_CARRIER: dict = {"dir": None, "receipt": None, "identity": None}

# ★★ QC176 / v6 §6.1.1 U-4：★ **唯一趟身份**（★ 交接须绑定本趟）。
#   ★ 由 `--trip-id` 显式给定；★ 未给定 ⇒ 本运行生成一次性随机标识
#     （★ 生成值**不可能**与任何外部交接件相符 ⇒ 交接分支 fail-closed）。
TRIP_ID: str = ""


def new_trip_id() -> str:
    """★ 生成本运行的一次性趟标识（★ 不可预测、不可复用）。"""
    return ("qc151-" + datetime.now().strftime("%Y%m%dT%H%M%S%f") + "-"
            + str(os.getpid()) + "-" + os.urandom(8).hex())

# ★ Popen 清理令牌（★ `main()` 内建、传给 `launch_direct`；★ 见 §9 `LaunchToken`）
LAUNCH_TOKEN = None

# ★★ [A8] 授权趟标志（★ 模块级容器，★ `finally` 必须能读到）。
#   ★ 理由：`_u8_authorized` 是 `main()` try 内的局部变量；若在它赋值**之前**
#     抛异常（如母本冻结失败、预算超限），`finally` 里引用它会 `NameError`
#     ⇒ 收尾本身崩掉。用单元素 list 与既有 `FINALIZE_CODE` / `TRIP_CARRIER`
#     同范式，★ 默认 False ⇒ 非授权趟行为**逐字不变**。
A8_ALLOW_LOADER = [False]

# ★ 收尾失败码合并优先级（★ 小者优先；★ 未列出者按出现顺序排最后）
CLEANUP_CODE_PRIORITY = (
    EXIT_TERMINATE_FAILED, EXIT_CARRIER_DELETE_FAILED,
    EXIT_EVIDENCE_VERIFY_FAILED, EXIT_MANIFEST_FAILED,
    EXIT_CARRIER_NOT_OWNED, EXIT_PID_IDENTITY_UNVERIFIED,
    EXIT_T0_T1_DIFF, EXIT_RESTORE_FAILED, EXIT_INTERNAL_ERROR,
)


def note_cleanup_failure(code: int, where: str, note: str, rec=None) -> None:
    """★★ 记一笔**可外达**的收尾失败（★ **禁止**用 finally 局部变量承载）。"""
    CLEANUP_FAILURES.append({"code": int(code), "where": where, "note": note})
    if rec is not None:
        rec.add("CLEANUP", f"failure_{len(CLEANUP_FAILURES)}",
                {"code": int(code), "where": where, "note": note}, where, note=note)


def merge_cleanup_code(base: int) -> int:
    """★★ 统一合并：★ `base` 与全部收尾失败取**优先级最高**者。

    ★★ **禁止后续成功清空既有失败**：★ 只要容器里有任一非 0 码，
      ★ 结果**必非 0**（★ 与 `base` 是否 `EXIT_OK` 无关）。
    """
    codes = [int(c) for c in [base] + [f["code"] for f in CLEANUP_FAILURES]]
    codes = [c for c in codes if c != EXIT_OK]
    if not codes:
        return EXIT_OK

    def _rank(c: int) -> int:
        return (CLEANUP_CODE_PRIORITY.index(c)
                if c in CLEANUP_CODE_PRIORITY else len(CLEANUP_CODE_PRIORITY))
    return min(codes, key=_rank)


# ===========================================================================
# §5 · 基础设施（★ 全部只读 / 无副作用）
# ===========================================================================
def sha256_file(p: Path) -> str:
    """★ 流式 sha256。★ 纯只读（`open(...,'rb')`）。"""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def read_bytes(p: Path, off: int, n: int) -> bytes:
    """★ 定点只读（★ 用于控二）。★ 只读**本卡自己**的文件，不碰任何进程内存。"""
    with open(p, "rb") as f:
        f.seek(off)
        return f.read(n)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Recorder:
    """★ 逐字段留痕器：`(group, key, value, source, note)`。

    ★★ 口径（`QC141:5`）：★ **未读到写「未测」**；★ **不可测写 `null`**。
    ★ 本类**不提供**"写 `False` 表示未知"的口子 —— ★ 调用方必须显式传值。
    """

    def __init__(self) -> None:
        self.rows: list = []

    def add(self, group: str, key: str, value, source: str, note: str = "") -> None:
        self.rows.append({
            "group": group, "key": key, "value": value,
            "source": source, "note": note, "ts": now_iso(),
        })

    def dump(self, path: Path) -> None:
        path.write_text(json.dumps(self.rows, ensure_ascii=False, indent=1),
                        encoding="utf-8")


class TripBudget:
    """★★ 上限记账（★ 真检查，不是注释）。"""

    def __init__(self, rec: Recorder) -> None:
        self.rec = rec
        self.launches = 0
        self.t0 = time.monotonic()
        self.stage_t0 = time.monotonic()

    def bump_launch(self) -> None:
        """★ `MAX_LAUNCHES = 5` ⇒ 越限**非 0 退出**。"""
        self.launches += 1
        self.rec.add("BUDGET", "launches", self.launches, "script:MAX_LAUNCHES")
        if self.launches > MAX_LAUNCHES:
            self.rec.add("BUDGET", "launch_limit_exceeded", True,
                         "script:MAX_LAUNCHES",
                         note=f"★ 超过 {MAX_LAUNCHES} 趟 ⇒ 硬停")
            sys.exit(EXIT_LAUNCH_LIMIT)

    def begin_stage(self, name: str) -> None:
        self.stage_t0 = time.monotonic()
        self.rec.add("BUDGET", f"stage_begin:{name}", round(self.elapsed(), 3),
                     "time.monotonic")

    def end_stage(self, name: str) -> None:
        """★ 单阶段 ≤30 s ⇒ 越限**非 0 退出**。"""
        dt = time.monotonic() - self.stage_t0
        self.rec.add("BUDGET", f"stage_seconds:{name}", round(dt, 3),
                     "time.monotonic")
        if dt > STAGE_TIMEOUT_S:
            self.rec.add("BUDGET", f"stage_timeout:{name}", True,
                         "script:STAGE_TIMEOUT_S",
                         note=f"★ 超过 {STAGE_TIMEOUT_S} s ⇒ 硬停")
            sys.exit(EXIT_STAGE_TIMEOUT)

    def elapsed(self) -> float:
        return time.monotonic() - self.t0

    def check_trip(self) -> None:
        """★ 单趟 ≤180 s ⇒ 越限**非 0 退出**。"""
        if self.elapsed() > TRIP_BUDGET_S:
            self.rec.add("BUDGET", "trip_budget_exceeded", True,
                         "script:TRIP_BUDGET_S",
                         note=f"★ 超过 {TRIP_BUDGET_S} s ⇒ 硬停")
            sys.exit(EXIT_TRIP_BUDGET)


# ===========================================================================
# §6 · ② 两控（★ 跑前 / 跑后各调一次；★ 真读文件，不缓存）
# ===========================================================================
def control_one(rec: Recorder, tag: str) -> bool:
    """★ 控一：`ra2bench\\gamemd.exe` sha256 = `73201cc0…f67476` / size `4825360`。

    ★ 出处 `QC141:149`。★ **真读文件**；`tag` ∈ {`"pre"`, `"post"`}。
    """
    exe = BENCH / "gamemd.exe"
    actual_size = exe.stat().st_size
    actual_sha = sha256_file(exe)
    ok = (actual_sha == CTRL1_SHA256) and (actual_size == CTRL1_SIZE)
    rec.add("CTRL1", f"sha256_{tag}", actual_sha,
            f"{exe}:file", note=f"★ 期望 {CTRL1_SHA256}（QC141:149）")
    rec.add("CTRL1", f"size_{tag}", actual_size,
            f"{exe}:file", note=f"★ 期望 {CTRL1_SIZE}（QC141:149）")
    rec.add("CTRL1", f"verdict_{tag}", "PASS" if ok else "FAIL",
            "script:control_one")
    return ok


def control_two(rec: Recorder, tag: str) -> bool:
    """★ 控二：`gamemd.exe` `VA 0x00829284` / `file_off 0x429284` 8 字节 =
    `4E 6F 20 4E 61 6D 65 00`。

    ★ 出处 `QC141:150`。★★ `file_off` 与 `VA` **成对写出**（`D-79`）。
    ★ 这是**文件**偏移（`open().seek`），★ **不是** `ReadProcessMemory`。
    """
    exe = BENCH / "gamemd.exe"
    got = read_bytes(exe, CTRL2_FILE_OFF, len(CTRL2_BYTES))
    ok = (got == CTRL2_BYTES)
    rec.add("CTRL2", f"va_{tag}", hex(CTRL2_VA), "QC141:150",
            note="★ VA（成对写出，D-79）")
    rec.add("CTRL2", f"file_off_{tag}", hex(CTRL2_FILE_OFF), "QC141:150",
            note="★ file_off（成对写出，D-79）")
    rec.add("CTRL2", f"bytes_{tag}", got.hex(" ").upper(),
            f"{exe}:file@{hex(CTRL2_FILE_OFF)}",
            note="★ 期望 4E 6F 20 4E 61 6D 65 00")
    rec.add("CTRL2", f"verdict_{tag}", "PASS" if ok else "FAIL",
            "script:control_two")
    return ok


# ===========================================================================
# §7 · ③ 零写自证 `T0`/`T1`（★ 634 件 = 410 + 224；两数自己复算）
# ===========================================================================
def enumerate_zero_write_set(rec: Recorder) -> list:
    """★ **634 件** = `ra2bench` 顶层 **410** + `ra2youli` `*.yrm` **224**。

    ★ 出处 `QC141:132`。★★ 两数**由本函数自己复算**（★ 不照抄常量）：
      ★ 复算值与 `QC141:132` **不一致即留痕**（★ 不静默）。
    ★ 返回逐件 `(全路径, size, sha256)`。
    """
    entries: list = []
    bench_top = [p for p in BENCH.iterdir() if p.is_file()]
    youli_yrm = [p for p in YOULI.glob("*.yrm") if p.is_file()]
    rec.add("T", "ra2bench_top_count", len(bench_top), f"{BENCH}:*",
            note="★ 期望 410（QC141:132）")
    rec.add("T", "ra2youli_yrm_count", len(youli_yrm), f"{YOULI}:*.yrm",
            note="★ 期望 224（QC141:132）")
    total = len(bench_top) + len(youli_yrm)
    rec.add("T", "zero_write_total", total, "script:复算",
            note="★ 期望 634（QC141:132）")
    for p in bench_top + youli_yrm:
        entries.append((str(p), p.stat().st_size, sha256_file(p)))
    return entries


def t_snapshot(rec: Recorder, tag: str, path: Path) -> list:
    """★ 落 `T0`（跑前）或 `T1`（跑后）。★ `tag` ∈ {`"T0"`, `"T1"`}。"""
    snap = enumerate_zero_write_set(rec)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    rec.add("T", f"{tag}_path", str(path), "script:t_snapshot")
    rec.add("T", f"{tag}_entries", len(snap), "script:t_snapshot")
    return snap


def t_diff(rec: Recorder, t0: list, t1: list, diff_path: Path) -> bool:
    """★★ `T0 ↔ T1` **逐件 sha 比对**并发 `diff`。

    ★ 口径 `QC141:140`。★ 比对集合 = **路径并集**（★ 新增/删除/改内容都算差）。
    ★★ 任何一件不同 ⇒ 返回 `False`（★ 调用方以 `EXIT_T0_T1_DIFF` 收口）。
    """
    m0 = {p: (s, h) for p, s, h in t0}
    m1 = {p: (s, h) for p, s, h in t1}
    diffs: list = []
    for p in sorted(set(m0) | set(m1)):
        a, b = m0.get(p), m1.get(p)
        if a == b:
            continue
        if a is None:
            kind = "added"
        elif b is None:
            kind = "removed"
        elif a[0] != b[0]:
            kind = "size_changed"
        else:
            kind = "sha_changed"
        diffs.append({"path": p, "kind": kind,
                      "t0": ({"size": a[0], "sha256": a[1]} if a else None),
                      "t1": ({"size": b[0], "sha256": b[1]} if b else None)})
    diff_path.write_text(json.dumps(diffs, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    rec.add("T", "diff_count", len(diffs), "script:t_diff",
            note=f"★ 落盘 {diff_path}")
    rec.add("T", "t0_t1_identical", (len(diffs) == 0),
            "script:t_diff", note="★ True = 零写成立")
    return len(diffs) == 0


# ===========================================================================
# §8 · ④ `except.txt` 复位 + 集合差
# ===========================================================================
def read_lines(p: Path) -> list:
    """★ 只读按行读取（`errors="replace"`，★ 不因编码挂掉）。"""
    return p.read_text(encoding="utf-8", errors="replace").splitlines()


def except_reset(rec: Recorder, carrier_dir: Path) -> bool:
    """★ 跑前把 `except.txt` **从只读母本复制回载体**，建立已知基线。

    ★ 口径 `QC141:134` / `QC141:15`。★★ **顺序不可颠倒**：
      **先校验母本哈希、后复制**。★ 复制后**复读载体并复核**。
    ★★ **母本只读、绝不写母本**（★ 本函数对母本只有 `sha256_file`/`open('rb')`）。
    """
    # --- 步 1：★ 先校验母本哈希 ---
    if not EXCEPT_MASTER.exists():
        rec.add("EXCEPT", "master_missing", True, f"{EXCEPT_MASTER}:path",
                note="★ 母本不存在 ⇒ 无法建立基线")
        return False
    m_size = EXCEPT_MASTER.stat().st_size
    m_sha = sha256_file(EXCEPT_MASTER)
    rec.add("EXCEPT", "master_path", str(EXCEPT_MASTER), "QC141:160")
    rec.add("EXCEPT", "master_size", m_size, f"{EXCEPT_MASTER}:file",
            note=f"★ 期望 {EXCEPT_MASTER_SIZE}（QC141:160）")
    rec.add("EXCEPT", "master_sha256", m_sha, f"{EXCEPT_MASTER}:file",
            note=f"★ 期望 {EXCEPT_MASTER_SHA256}（QC141:160）")
    if m_sha != EXCEPT_MASTER_SHA256 or m_size != EXCEPT_MASTER_SIZE:
        rec.add("EXCEPT", "master_verify", "FAIL", "script:except_reset",
                note="★★ 母本哈希不符 ⇒ **不复制**（★ 绝不用可疑基线）")
        return False
    rec.add("EXCEPT", "master_verify", "PASS", "script:except_reset")

    # --- 步 2：★ 后复制（★ 母本只读打开） ---
    dst = carrier_dir / "except.txt"
    with open(EXCEPT_MASTER, "rb") as fsrc:      # ★ 只读
        blob = fsrc.read()
    with open(dst, "wb") as fdst:                 # ★ 只写**载体副本**
        fdst.write(blob)

    # --- 步 3：★ 复制后复读载体并复核 ---
    c_sha = sha256_file(dst)
    c_size = dst.stat().st_size
    rec.add("EXCEPT", "carrier_copied_size", c_size, f"{dst}:file")
    rec.add("EXCEPT", "carrier_copied_sha256", c_sha, f"{dst}:file",
            note="★ 复制后**复读**所得")
    ok = (c_sha == EXCEPT_MASTER_SHA256) and (c_size == EXCEPT_MASTER_SIZE)
    rec.add("EXCEPT", "carrier_reverify", "PASS" if ok else "FAIL",
            "script:except_reset",
            note="★ 复读复核；★ FAIL ⇒ 不继续")
    # ★ 母本复核：证明我们**没写母本**
    rec.add("EXCEPT", "master_sha256_after_copy", sha256_file(EXCEPT_MASTER),
            f"{EXCEPT_MASTER}:file",
            note="★ 证明母本**未被写**（值须与 master_sha256 相同）")
    return ok


def except_set_diff(rec: Recorder, pre_txt: str, post_txt: str) -> dict:
    """★★ `except.txt` **集合差**（★ 唯一判定口径）。

    ★ 口径 `QC141:141`。★★ **明令禁止**：
      - ★ **不得**用 `post[len(pre):]` 切片（★ 假定 appending-only，未证）；
      - ★ **不得**用 `sha` 变化判 crash（★ 游戏自身会重写该文件）。
    ★ 本函数用 `collections.Counter` 做**多重集差**（★ 重复行正确计入）。
    ★ 新增异常的判据 = 集合差里含 `Exception occurred at` 的行。
    """
    pre_lines = pre_txt.splitlines()
    post_lines = post_txt.splitlines()
    c_pre = collections.Counter(pre_lines)
    c_post = collections.Counter(post_lines)
    new_counter = c_post - c_pre          # ★ 多重集差
    gone_counter = c_pre - c_post
    new_lines = list(new_counter.elements())
    gone_lines = list(gone_counter.elements())
    new_exc = [ln for ln in new_lines if "Exception occurred at" in ln]
    res = {
        "method": "collections.Counter 多重集差（★ 非 post[len(pre):] 切片）",
        "pre_line_count": len(pre_lines),
        "post_line_count": len(post_lines),
        "new_line_count": len(new_lines),
        "gone_line_count": len(gone_lines),
        "new_lines": new_lines,
        "gone_lines": gone_lines,
        "new_exception_lines": new_exc,
        "new_exception_count": len(new_exc),
        "no_new_exception": (len(new_exc) == 0),
    }
    rec.add("EXCEPT", "set_diff_method", res["method"], "script:except_set_diff")
    rec.add("EXCEPT", "pre_line_count", res["pre_line_count"], "script:except_set_diff")
    rec.add("EXCEPT", "post_line_count", res["post_line_count"], "script:except_set_diff")
    rec.add("EXCEPT", "new_exception_count", res["new_exception_count"],
            "script:except_set_diff",
            note="★ 0 = 未见新异常；判据**仅**集合差")
    return res


# ===========================================================================
# §9 · ① 直启 + `S-4` 注入面闸门
# ===========================================================================
def find_pids(name: str) -> list:
    """★ 按名查 pid（`CreateToolhelp32Snapshot`，**只读枚举**）。

    ★ 自建理由：`qc63_trip.py:57` 的 `find_pids` **签名相符**
      （`(name: str) -> list[int]`，亲读 `:57-80`），★ 但其同模块
      `qc63_trip.py:101` 的 `find_hwnd` **注解与实现不符**（注解 `-> int | None`，
      实现 `:124` 返回 `tuple`）。★ 为避免把该模块的**副作用与错注解**一并引入，
      本卡**自建**这两个函数（★ 任务书 ① 允许"照其口径自建"）。
    ★ 出处：`QC141:90`「按名查 `find_pids('gamemd.exe')`」。
    """
    pids: list = []

    class PE32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                    ("th32ProcessID", wt.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                    ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                    ("th32ParentProcessID", wt.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                    ("szExeFile", ctypes.c_char * 260)]

    k32 = ctypes.windll.kernel32
    # ★ QC183：HANDLE 是 64 位指针值，必须声明 restype 防截断。
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)   # TH32CS_SNAPPROCESS
    # ★★ QC184：`snap` 的 `restype` 已声明为 `HANDLE`(= `c_void_p`) ⇒
    #   ★ 失败时 OS 返回的 `INVALID_HANDLE_VALUE`(-1) 被 `ctypes` 取成
    #     **无符号**指针值（64 位 → 2**64-1）⇒ ★ 旧写法 `snap == -1`
    #     **恒为假**（★ 会把失败快照当有效句柄继续枚举）。
    #   ★ `not snap` 同时吃掉 NULL（`None` / 0）。
    if not snap or snap == INVALID_HANDLE_VALUE:
        return pids
    ent = PE32()
    ent.dwSize = ctypes.sizeof(PE32)
    # ★ QC183：Process32First/Next 第 1 参 HANDLE 同理。
    k32.Process32First.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    k32.Process32First.restype = wt.BOOL
    k32.Process32Next.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    k32.Process32Next.restype = wt.BOOL
    if k32.Process32First(snap, ctypes.byref(ent)):
        while True:
            if ent.szExeFile.decode("mbcs", "ignore").lower() == name.lower():
                pids.append(ent.th32ProcessID)
            if not k32.Process32Next(snap, ctypes.byref(ent)):
                break
    k32.CloseHandle(snap)
    return pids


def get_process_creation_time(pid: int) -> int | None:
    """★ 取进程创建时间（FILETIME 转 100-ns 计数），失败返回 None。

    ★ 用于绑定 Popen.pid 与按名解析的 pid，防止 pid 复用。
    """
    k32 = ctypes.windll.kernel32
    # ★ QC183：同 s4_enum_modules —— HANDLE 必须声明 restype 防 64 位截断。
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.GetProcessTimes.argtypes = [
        wt.HANDLE, ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME),
        ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME)]
    k32.GetProcessTimes.restype = wt.BOOL
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        ct = wt.FILETIME()
        et = wt.FILETIME()
        kt = wt.FILETIME()
        ut = wt.FILETIME()
        if k32.GetProcessTimes(h, ctypes.byref(ct), ctypes.byref(et),
                               ctypes.byref(kt), ctypes.byref(ut)):
            return (ct.dwHighDateTime << 32) | ct.dwLowDateTime
        return None
    finally:
        k32.CloseHandle(h)


def s4_scan_names(names) -> dict:
    """★ `S-4` 纯函数：对模块名做**大小写不敏感子串**匹配。

    ★ 判据逐字（`QC141:89`）：「枚举该 pid 模块表，命中 `ra2render` 或
      `ra2loader`（**大小写不敏感**子串）⇒ 硬停、本趟作废、落盘模块表原文；
      命中数必须 = 0」。
    ★★ 自建（★ 口径照 `qc135_objloc.py:186` 的 `s4_scan_names`，亲读 `:186-222`）。
    """
    r_hits: list = []
    l_hits: list = []
    pairs: list = []
    for nm in names:
        if not isinstance(nm, str):
            continue
        low = nm.lower()
        for needle in S4_NEEDLES:
            if needle in low:
                pairs.append((needle, nm))
                (r_hits if needle == "ra2render" else l_hits).append(nm)
    return {"ra2render_hits": r_hits, "ra2loader_hits": l_hits,
            "hits": pairs, "hit_count": len(pairs)}


def s4_enum_modules(pid: int) -> tuple:
    """★ 枚举目标 pid 的**模块表** ⇒ `(names, paths, err)`。

    ★ 机制：`psapi.EnumProcessModulesEx(LIST_MODULES_ALL)` +
      `psapi.GetModuleFileNameExW`（★ 与 `qc135_objloc.py:299-353` 同口径）。
    ★★ **无 `try`/`except`**（★ 不吞异常）。
    ★★ **失败即失败**：任一步拿不到表 ⇒ `err` 非 `None`
      ⇒ 调用方按 `EXIT_MODULE_ENUM_FAILED`(63) 收口，
      ★ **绝不当"未加载"放行**（`QC141:88`）。
    ★★ **完整性**：填充后核新 cbNeeded 是否超出分配容量；
      取名拒绝缓冲区截断（`n == 0` 或 `n >= 259` 均视为截断/失败）。
    ★★ QC184 **上界**：模块数 > `S4_MAX_MODULES` ⇒ **不**按它分配数组
      （★ 防 `MemoryError`），★ 直接按"不可判定"走枚举失败收口。
    """
    psapi = ctypes.windll.psapi
    k32 = ctypes.windll.kernel32
    # ★★ QC183：声明 argtypes/restype —— 64 位 Windows 上 HANDLE/HMODULE 是
    #   64 位指针值（c_void_p）。未声明时 ctypes 默认参数为 c_int（32 位有符号），
    #   HMODULE 值超过 2^31 即 OverflowError（★ 首趟真机 :791 崩溃根因）。
    #   ★ restype 同样必须声明：OpenProcess 返回 HANDLE，默认 c_int 会截断。
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    psapi.EnumProcessModulesEx.argtypes = [
        wt.HANDLE, ctypes.POINTER(wt.HMODULE), wt.DWORD,
        ctypes.POINTER(wt.DWORD), wt.DWORD]
    psapi.EnumProcessModulesEx.restype = wt.BOOL
    # ★★ GetModuleFileNameExW 第 2 参 HMODULE = c_void_p（指针宽度）。
    #   声明后 arr[i]（Python int，来自 c_void_p 数组）被正确转为 64 位 HMODULE，
    #   不再经 c_int ⇒ 不溢出。
    psapi.GetModuleFileNameExW.argtypes = [
        wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]
    psapi.GetModuleFileNameExW.restype = wt.DWORD
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    LIST_MODULES_ALL = 0x03

    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        return None, None, f"OpenProcess(pid={pid}) 失败: err={ctypes.GetLastError()}"
    try:
        need = wt.DWORD(0)
        if not psapi.EnumProcessModulesEx(h, None, 0, ctypes.byref(need),
                                          LIST_MODULES_ALL):
            return None, None, (
                f"EnumProcessModulesEx(probe) 失败: err={ctypes.GetLastError()}")
        cnt = need.value // ctypes.sizeof(ctypes.c_void_p)
        if cnt <= 0:
            # ★ 表为空 ⇒ **不可判"未加载"** ⇒ 按枚举失败收口。
            return None, None, f"EnumProcessModulesEx: cbNeeded={need.value} ⇒ 模块数为 0"
        # ★★ QC184：`cbNeeded` 由 OS 回填（★ 非本脚本可信输入）。
        #   ★ 直接按它分配 ⇒ 极端值抛 `MemoryError`（★ 属 `Exception`，
        #     但**不得**以未捕获回溯形态冒泡）⇒ ★ 超限即判不可判定 ⇒ 失败收口。
        if cnt > S4_MAX_MODULES:
            return None, None, (
                f"EnumProcessModulesEx: cbNeeded={need.value} ⇒ 模块数={cnt} "
                f"> S4_MAX_MODULES={S4_MAX_MODULES} ⇒ 不可判定")
        # ★★ QC199/D-124：probe 与 fill 之间模块数可增长（T19 实证 9→10，
        #   cbNeeded=80>allocated=72 ⇒ 截断硬停作废整趟）。标准做法=按新
        #   cbNeeded 重分配并重试（上限 3 次重试；仍截断或超 S4_MAX_MODULES
        #   ⇒ 硬停，语义不放宽）。
        _retries = 0
        while True:
            arr = (ctypes.c_void_p * cnt)()
            if not psapi.EnumProcessModulesEx(h, arr, ctypes.sizeof(arr),
                                              ctypes.byref(need), LIST_MODULES_ALL):
                return None, None, (
                    f"EnumProcessModulesEx(fill) 失败: err={ctypes.GetLastError()}")
            # ★★ 完整性：新 cbNeeded 若大于已分配容量 ⇒ 有模块被截断 ⇒ 重试
            if need.value <= ctypes.sizeof(arr):
                break
            _retries += 1
            cnt = need.value // ctypes.sizeof(ctypes.c_void_p)
            if cnt > S4_MAX_MODULES:
                return None, None, (
                    f"EnumProcessModulesEx: cbNeeded={need.value} ⇒ 模块数={cnt} "
                    f"> S4_MAX_MODULES={S4_MAX_MODULES} ⇒ 不可判定")
            if _retries >= 3:
                return None, None, (
                    f"EnumProcessModulesEx: cbNeeded={need.value} > "
                    f"allocated={ctypes.sizeof(arr)} ⇒ 重试 3 次仍被截断 ⇒ 不能判定")
        names: list = []
        paths: list = []
        failed = 0
        for i in range(cnt):
            buf = ctypes.create_unicode_buffer(260)
            n = psapi.GetModuleFileNameExW(h, arr[i], buf, 260)
            # ★★ 拒绝截断：n == 0（失败）或 n >= 259（可能截断）均视为不完整
            if n == 0 or n >= 259:
                failed += 1
                names.append(None)
                paths.append(None)
                continue
            paths.append(buf.value)
            names.append(os.path.basename(buf.value))
        if failed > 0:
            return None, None, (
                f"GetModuleFileNameExW 有 {failed}/{cnt} 个模块取名失败/截断 ⇒ "
                f"模块表**不完整** ⇒ 不能判定 ra2render/ra2loader 未加载")
        return names, paths, ""
    finally:
        k32.CloseHandle(h)


def s4_injection_gate(pid: int, rec: Recorder, authorized: bool = False) -> bool:
    """★★ `S-4` 注入面闸门（★ **拿到 pid 之后、任何 L* 步骤之前**跑）。

    ★ 判据 `QC141:88`/`:89`：
      「命中 `ra2render` 或 `ra2loader` ⇒ **立即停手**、本趟作废、
        落盘模块表原文；**命中数必须 = 0**」。
    ★ 命中 > 0 ⇒ `EXIT_INJECTION_SUSPECTED`(62)；★ 并落盘模块表原文。
    ★★ **枚举失败 ⇒ 同一个 62/63 收口**（★ `EXIT_MODULE_ENUM_FAILED`），
      ★ **不得**当"未加载"放行。

    ★★ [U8 20261021] `authorized=True`（`--allow-loader` 双键授权成立）时：
      命中**降级为 WARN 并放行**，`S4_VERDICT["gate"] = "hit_authorized"`。
      ★ 缺省 `False` ⇒ 行为与授权前**逐字相同**（flag-off 房规）。
      ★★ 授权**不**改变枚举失败的收口：拿不到模块表仍按 63 硬停
        （★ 授权只放宽"命中"，不放宽"不可判定"）。
    """
    rec.add("S4", "module_enum_method",
            "psapi.EnumProcessModulesEx(LIST_MODULES_ALL) + "
            "psapi.GetModuleFileNameExW（口径同 qc135_objloc.py:299-353）",
            "script:s4_enum_modules")
    # ★★ QC183：防御性 try/except —— s4_enum_modules 内部任何异常
    #   （ctypes.ArgumentError / OverflowError / OSError 等）均走干净 STOP，
    #   ★ **不得**冒泡成未捕获回溯（★ 首趟 error.txt 的根因路径）。
    try:
        names, paths, err = s4_enum_modules(pid)
    except Exception as _exc:
        names, paths, err = None, None, (
            f"s4_enum_modules 抛出未预期异常: {type(_exc).__name__}: {_exc}")

    if names is None:
        # ★★ 枚举失败 ⇒ **以失败收口**，★ 不放行。
        #   ★★ QC184：★ 顺序固定为「判定记录 → 落盘 → 返回」。
        #     ★ 先落判定：★ 即使随后落盘失败，"本趟为何作废"已在记录里。
        rec.add("S4", "module_enum_error", err, "psapi:ret",
                note="★★ 拿不到模块表 ⇒ 不能证明 ra2render/ra2loader 未加载 "
                     "⇒ 硬停（**不**当'未加载'放行）")
        rec.add("S4", "modules_total", None, "psapi:未执行",
                note="★ 不可得 ⇒ null（★ 不写 0）")
        rec.add("S4", "ra2render_hits", None, "s4_scan_names:未执行",
                note="★ 未测得 ⇒ null")
        rec.add("S4", "ra2loader_hits", None, "s4_scan_names:未执行",
                note="★ 未测得 ⇒ null")
        rec.add("S4", "s4_gate", "enum_failed", "script:s4_injection_gate")
        rec.add("S4", "s4_exit_code", EXIT_MODULE_ENUM_FAILED,
                "script:s4_injection_gate",
                note="★★ 枚举/截断/不完整/不可判定 ⇒ 一律 63（★ 不当'未加载'放行）")
        # ★★ QC184：★ 判定结论**直接**落入模块级容器 ⇒ `main()` 据此取退出码，
        #   ★ 不再反读 `s4_module_table.txt` 的文字内容去猜（★ 文件读会抛
        #     `OSError`/`FileNotFoundError` ⇒ 未捕获回溯）。
        S4_VERDICT["gate"] = "enum_failed"
        S4_VERDICT["exit_code"] = EXIT_MODULE_ENUM_FAILED
        S4_VERDICT["err"] = err
        # ★★ QC184：★ 落盘**自己**收口（★ 不让 `OSError`/`UnicodeError` 冒泡）。
        table_path = WORKDIR / "s4_module_table.txt"
        try:
            table_path.write_text(
                "★ 模块表**枚举失败**，无原文可落盘。\n"
                f"err = {err}\n★ 失败原因行号：script:s4_enum_modules"
                "（names is None 分支）\n",
                encoding="utf-8")
            rec.add("S4", "module_table_path", str(table_path),
                    "script:s4_injection_gate")
        except (OSError, UnicodeError) as _we:
            rec.add("S4", "module_table_write_error",
                    f"{type(_we).__name__}: {_we}", "script:s4_injection_gate",
                    note="★★ 落盘失败**不**改变判定 ⇒ 仍按 63 硬停")
        return False

    rec.add("S4", "modules_total", len(names), "psapi:EnumProcessModulesEx")

    # ★ 模块表原文落盘（★ 无论命中与否都落，供用户复核）
    table_path = WORKDIR / "s4_module_table.txt"
    # ★★ QC184：★ 同上——落盘失败**不**冒泡，★ 判定照常进行。
    try:
        table_path.write_text(
            "\n".join(f"[{i:03d}] {p}" for i, p in enumerate(paths)),
            encoding="utf-8")
        rec.add("S4", "module_table_path", str(table_path), "script:s4_injection_gate")
    except (OSError, UnicodeError) as _we:
        rec.add("S4", "module_table_write_error",
                f"{type(_we).__name__}: {_we}", "script:s4_injection_gate",
                note="★ 落盘失败 ⇒ 原文未落盘；★ 判定**仍**按实测命中数进行")

    scan = s4_scan_names(names)
    rec.add("S4", "ra2render_hits", scan["ra2render_hits"],
            "script:s4_scan_names", note="★ 空列表 = 0 命中")
    rec.add("S4", "ra2loader_hits", scan["ra2loader_hits"],
            "script:s4_scan_names", note="★ 空列表 = 0 命中")
    rec.add("S4", "hit_count", scan["hit_count"], "script:s4_scan_names",
            note="★★ 必须 = 0")
    rec.add("S4", "needles", list(S4_NEEDLES), "QC141:89",
            note="★ 大小写不敏感**子串**（非文件名相等）")

    if scan["hit_count"] > 0:
        # ★★ [U8 20261021] 授权旁路：仅在 `--allow-loader` 双键授权成立时放行。
        #   ★ 未授权 ⇒ 逐字维持原行为（HIT ⇒ 62）。
        #   ★ 授权 ⇒ **降级为 WARN 并放行**，但必须逐条留痕（hit 明细 + 授权依据）。
        if authorized:
            rec.add("S4", "u8_authorized_bypass", True, "argv:--allow-loader",
                    note="★★ [U8] 授权趟：S-4 命中降级为 WARN（★ 不是解禁，"
                         "禁止面 (a)(b)(c)(d) 仍全部有效）")
            rec.add("S4", "u8_bypass_hits", {
                "ra2render_hits": scan["ra2render_hits"],
                "ra2loader_hits": scan["ra2loader_hits"],
                "hit_count": scan["hit_count"],
            }, "script:s4_scan_names",
                    note="★★ [U8] 授权旁路下的实际命中明细（★ 事后可审计）")
            rec.add("S4", "s4_gate", "hit_authorized", "script:s4_injection_gate",
                    note="★★ [U8] 命中但已授权 ⇒ 放行（★ 证据仅可用于 B0/B1 臂对比）")
            rec.add("S4", "s4_exit_code", EXIT_OK, "script:s4_injection_gate",
                    note="★★ [U8] 授权趟不设 62")
            S4_VERDICT["gate"] = "hit_authorized"
            S4_VERDICT["exit_code"] = EXIT_OK
            S4_VERDICT["err"] = None
            return True
        rec.add("S4", "s4_gate", "HIT", "script:s4_injection_gate",
                note="★★ 命中 ⇒ 硬停、本趟作废（EXIT_INJECTION_SUSPECTED=62）")
        # ★★ QC184：★ 判定结论落入容器（`main()` 据此取 62，★ 不再猜文件内容）。
        rec.add("S4", "s4_exit_code", EXIT_INJECTION_SUSPECTED,
                "script:s4_injection_gate",
                note="★★ 命中 ra2render/ra2loader ⇒ 62")
        S4_VERDICT["gate"] = "HIT"
        S4_VERDICT["exit_code"] = EXIT_INJECTION_SUSPECTED
        S4_VERDICT["err"] = None
        return False
    rec.add("S4", "s4_gate", "pass", "script:s4_injection_gate",
            note="★ 命中数 = 0 ⇒ 放行")
    # ★★ QC184：★ 放行同样登记 ⇒ ★ 容器在三条路径下**都**有确定值。
    S4_VERDICT["gate"] = "pass"
    S4_VERDICT["exit_code"] = EXIT_OK
    S4_VERDICT["err"] = None
    return True


class LaunchToken:
    """★★ 第 2 项：★ **外层可见**的进程清理令牌（★ **先于** `Popen` 建立）。

    ★★ 缺陷原文（`EXTERNAL_RULING_PI_V4.md` §1 U 第 2 条）：
      ★ 旧 `launch_direct` 在 `Popen` 之后还要**记日志、查创建时间**才
        `return`；★ `main()` 到函数**返回后**才持有 `proc`
        ⇒ ★ 中间任一语句抛异常 ⇒ ★ 外层 `proc` 仍为 `None`
        ⇒ ★ `finally` 无从终止已启动的进程。
    ★★ 本类即修复：★ 令牌由 `main()` **预先**建立并传入；★ `Popen` 一返回，
      ★ **第一条**语句就是 `token.register_proc(proc)`（★ 早于任何可能抛出的
        日志 / API / 时间查询）；★ 时间基线取得后由 `register_ct()` **独立补登记**。
    ★★ 因此"登记后异常"、"时间查询失败"、"启动函数返回失败"三条失败路径
      ★ **都**能让外层 `finally` 看得到 `proc`（★ 不只是把某一句日志后移）。
    """

    def __init__(self) -> None:
        self.proc = None          # type: subprocess.Popen | None
        self.pid = None           # type: int | None
        self.ct = None            # type: int | None  ★ 启动时**冻结**的基线
        self.ct_query_error = None

    def reset(self) -> None:
        self.proc = None
        self.pid = None
        self.ct = None
        self.ct_query_error = None

    def register_proc(self, proc) -> None:
        """★★ 必须是 `Popen` 返回后的**第一条**语句（★ 早于任何可抛语句）。"""
        self.proc = proc
        self.pid = proc.pid

    def register_ct(self, ct) -> None:
        """★ 时间基线取得**之后**独立补登记（★ 失败则留 `None` ⇒ fail-closed）。"""
        self.ct = ct
        self.ct_query_error = (None if ct is not None
                               else "创建时间不可得（OpenProcess/GetProcessTimes 失败）")


def launch_direct(rec: Recorder, budget: TripBudget, carrier_dir: Path,
                  token: "LaunchToken", allow_loader: bool = False):
    """★★ 直启 `carrier\\gamemd.exe`（★ 缺省路径；★ **绝不经 `ra2loader.exe`**）。

    ★ 出处 `QC141:87`/`:88`。
    ★★ 本函数是**全脚本唯一** `subprocess.Popen`（★ 静态自检 #4 核验）：
      - ★ **无** `creationflags`（★ 无 `DEBUG_PROCESS` / `DEBUG_ONLY_THIS_PROCESS`）；
      - ★ `lpApplicationName` = **exe 全路径**（★ 不是 `cmd.exe` / shell）；
      - ★ 不经批处理、不经 `start`。
    ★ 口径 `QC141:14`「**普通 `subprocess.Popen`（无任何调试标志）**」。

    ★★ [U8 20261021] `allow_loader=True` 时（**唯一**例外，须双键授权）：
      启动目标改为 `carrier\\ra2loader.exe`——它 `LoadLibraryA` 注入
      `ra2render.dll`，从而让优化臂 B0/B1 与 ② 的守卫 A/B 可跑。
      ★ **其余一切不变**：仍是普通 `Popen`、仍无 `creationflags`、
      ★ 仍**不**经批处理 / `start` / shell（禁止面 (a)(b)(c) 仍然禁止）。
      ★ 与禁止面 (d) 的区别：本函数**直接**以 loader 全路径为
      `lpApplicationName`，**不**在启动后按名去猜 `gamemd.exe` 的 pid；
      pid 一律来自 `Popen.pid`（`token.register_proc`）。
    """
    if allow_loader:
        exe = carrier_dir / ALLOW_LOADER_EXE
        # ★★ [U8] 授权路径必须留痕：这是禁止面的唯一例外，事后可审计。
        rec.add("LAUNCH", "u8_allow_loader", True, "argv:--allow-loader",
                note="★★ [U8] 授权直启 loader（注入型）——证据仅可用于 B0/B1 臂对比")
    else:
        exe = carrier_dir / "gamemd.exe"  # ★★ 可执行体 = gamemd.exe（静态自检 #3）
    rec.add("LAUNCH", "exe_path", str(exe),
            "QC141:88" if not allow_loader else "argv:--allow-loader",
            note=("★★ 直启载体 gamemd.exe；**绝不经 ra2loader.exe**"
                  if not allow_loader else
                  "★★ [U8] 授权直启 ra2loader.exe（注入 ra2render.dll）"))
    rec.add("LAUNCH", "exe_basename", exe.name, "script:launch_direct")
    rec.add("LAUNCH", "via_loader", bool(allow_loader), "QC141:171",
            note=("★ 该维度**未测**（本函数结构上仅有一个 Popen 且指向 exe）"
                  if not allow_loader else
                  "★★ [U8] 授权趟：启动目标即 loader"))
    rec.add("LAUNCH", "debug_flags_used", False, "script:launch_direct",
            note="★ 结构事实：调用未传 creationflags")
    budget.bump_launch()
    # ★★ 无 `try`/`except`（★ 本函数**不需要** `except`，`QC157:4`：
    #   ★ 该由 `finally` 覆盖 ⇒ ★ 就不加）。
    #   ★ 启动失败时 `subprocess.Popen` 抛出的 `OSError` **不被吞**
    #   ⇒ 传给 `main()` 的 `except BaseException`（★ 落盘原始异常 +
    #     `raise` 原样重抛）⇒ ★ `finally` 先收尾 ⇒ 异常再向解释器传播
    #   ⇒ ★ **非 0 收口**（★ 绝不是"吞掉当成功"）。
    #   ★ 依据 `D-35`：严禁 `try/except ⇒ pass=True` 兜底。
    proc = subprocess.Popen([str(exe)], cwd=str(carrier_dir))
    # ★★ 第 2 项：★ **Popen 一返回，第一条语句就是向外层令牌登记 proc**。
    #   ★ 其后的日志 / 创建时间查询**都可能抛出**；★ 只要令牌已登记，
    #     ★ 外层 `finally` 就一定能拿到该进程并尝试终止（★ 消除所有权窗口）。
    token.register_proc(proc)
    rec.add("LAUNCH", "launch_pid", proc.pid, "subprocess.Popen:pid",
            note="★ **仅作对照**；★ 绝不用它兜底（QC141:90）")
    # ★★ 记录创建时间，用于后续身份绑定与防复用（★ 登记**之后**才做）
    ct = get_process_creation_time(proc.pid)
    token.register_ct(ct)     # ★★ 时间基线取得后**独立补登记**（第 2 项）
    rec.add("LAUNCH", "launch_pid_creation_time", ct,
            "script:get_process_creation_time",
            note="★ 用于绑定 Popen.pid 与按名解析结果，防止 pid 复用")
    return proc


def resolve_pid(rec: Recorder, proc, expected_ct: int | None,
                expect_name: str = "gamemd.exe") -> int:
    """★ 按名查 `find_pids(expect_name)` ⇒ **绑定** `proc.pid` 与创建时间。

    ★ 出处 `QC141:90`。★ 查不到 ⇒ `EXIT_PID_NOT_FOUND`(21)。
    ★★ 绑定：要求按名解析的候选 pid **等于** `proc.pid`，
      且创建时间与 `proc` 启动时记录的一致；不等 ⇒ 可能 pid 复用 ⇒ 硬停。
    ★★ `QC169` 收紧（`EXTERNAL_RULING_PI_FIX_AUTH_3.md` §4.2）：
      - ★ `expected_ct` = **启动时冻结的基线**（★ 不再在本函数里重取
        `get_process_creation_time(expected_pid)`，旧 :838 即此放宽）；
      - ★ **拒绝 `None == None`**：★ 基线或候选创建时间为 `None` ⇒ 不成立；
      - ★ **删除**"唯一 PID 即接受"的显式回退（旧 :855–862）。

    ★★ [U8 20261021] `expect_name` 参数（★ 缺省 `"gamemd.exe"` ⇒ 逐字原行为）：
      授权趟以 `ra2loader.exe` 启动时，`proc.pid` **就是 loader 自己的 pid**
      （`Popen` 返回的是被直接 CreateProcess 的那个进程），
      故按名解析也必须查 **`ra2loader.exe`**，否则
      「`find_pids("gamemd.exe")` 得到 gamemd 的 pid」与「`proc.pid` 是 loader 的 pid」
      **必然不等** ⇒ 直接 21 硬停，根本到不了 S-4。
      ★ 这是 U8 的**必要配套**，不是可选优化。
      ★★ 注意：loader 会另起/注入 `gamemd.exe` 子进程，本函数**不**去绑定那个子进程
        —— 身份锚点始终是 `Popen` 返回的 loader 进程本身（★ 与 `terminate_owned_process`
        的 `expected_pid` 一致）。
    """
    pids = find_pids(expect_name)
    rec.add("LAUNCH", "find_pids_result", pids, "script:find_pids",
            note=f"★ 按名查（**非** launch_pid 兜底）；★ 查询名 = {expect_name!r}")
    if not pids:
        rec.add("LAUNCH", "pid_resolved", None, "script:find_pids",
                note="★★ 查不到 ⇒ 硬停（**绝不**回落 launch_pid）")
        sys.exit(EXIT_PID_NOT_FOUND)
    # ★★ 身份绑定：★ 用**冻结基线**，不重取
    expected_pid = proc.pid
    rec.add("LAUNCH", "expected_pid", expected_pid, "subprocess.Popen:pid")
    rec.add("LAUNCH", "expected_creation_time_frozen", expected_ct,
            "script:LaunchToken.register_ct",
            note="★ 启动时冻结的基线（★ 不再重取）")
    if expected_ct is None:
        rec.add("LAUNCH", "pid_resolved", None, "script:resolve_pid",
                note="★★ 冻结基线为 None ⇒ PID 身份不可核验"
                     "（★ 拒绝 None==None；★ 不按 PID 猜）")
        sys.exit(EXIT_PID_IDENTITY_UNVERIFIED)
    pid = None
    for candidate in pids:
        ct = get_process_creation_time(candidate)
        rec.add("LAUNCH", f"candidate_pid_{candidate}", candidate,
                "script:find_pids")
        rec.add("LAUNCH", f"candidate_ct_{candidate}", ct,
                "script:get_process_creation_time")
        # ★★ 拒绝 None==None：★ 候选时间也必须是非 None 才可能相等
        if candidate == expected_pid and ct is not None and ct == expected_ct:
            pid = candidate
            break
    if pid is None:
        rec.add("LAUNCH", "pid_resolved", None, "script:resolve_pid",
                note="★★ 按名解析结果与 Popen.pid 不一致或创建时间不匹配 "
                     "⇒ 可能 pid 复用 ⇒ 硬停（★ 无'唯一 PID'回退）")
        sys.exit(EXIT_PID_NOT_FOUND)
    rec.add("LAUNCH", "pid_resolved", pid, "script:resolve_pid",
            note="★ pid 与创建时间均绑定通过")
    return pid


def terminate_owned_process(rec: Recorder, proc,
                            expected_pid: int, expected_ct: int | None) -> bool:
    """★★ 受控终止：以本趟 Popen 身份及创建时间核验为前置，再发终止。

    ★ 出处：外部裁定 §2.3 / §3.3 / §4.4。
    ★★ 步骤：
      1. 核验当前 pid 仍等于 expected_pid 且创建时间仍匹配；
      2. 调用 `proc.terminate()`（或 taskkill）并记录返回；
      3. 等待退出并复核（poll / wait）；
      4. 无法证明目标退出时 ⇒ 返回 False，不继续删载体。
    ★ 不等时 ⇒ 不杀身份不明/复用的 pid。
    ★★ `QC169` 收紧（`EXTERNAL_RULING_PI_FIX_AUTH_3.md` §4.2）：
      ★ 旧实现接受 `expected_ct is None 且 current_ct is None` 的
        `None == None`（旧 :894）⇒ ★ 现**显式拒绝双 None**。
      ★ 基线缺失时：★ **不按 PID 发终止**；★ 只经**本趟自己持有的
        `Popen` 句柄**终止并等待（★ 句柄身份 ≠ PID 猜测），
        ★ 同时以 `EXIT_PID_IDENTITY_UNVERIFIED`(28) 记账为**收尾失败**
        （★ fail-closed：★ 不因"句柄终止成功"就宣称 PID 身份已核验）。
    ★★ 返回值 = **进程退出是否已由本趟句柄确认**（★ 不是"是否已发送"）。
    """
    rec.add("TERM", "term_requested", True, "script:terminate_owned_process")
    rec.add("TERM", "expected_pid", expected_pid,
            "script:terminate_owned_process")
    rec.add("TERM", "expected_creation_time", expected_ct,
            "script:terminate_owned_process")

    # --- 步 1：身份复核（★ 拒绝双 None） ---
    pid_identity_ok = True
    if expected_ct is None:
        pid_identity_ok = False
        rec.add("TERM", "identity_pid_verified", False,
                "script:terminate_owned_process",
                note="★★ 基线缺失 ⇒ PID 身份不可核验（★ 拒绝 None==None）"
                     "⇒ ★ 只经本趟 Popen 句柄终止，★ 并记为收尾失败")
        note_cleanup_failure(
            EXIT_PID_IDENTITY_UNVERIFIED, "script:terminate_owned_process",
            "★ 启动基线创建时间缺失 ⇒ PID 身份不可核验（fail-closed）", rec)
        current_ct = None
    else:
        current_ct = get_process_creation_time(expected_pid)
    rec.add("TERM", "current_creation_time", current_ct,
            "script:get_process_creation_time")
    if pid_identity_ok and current_ct != expected_ct:
        pid_identity_ok = False
        rec.add("TERM", "identity_mismatch", True,
                "script:terminate_owned_process",
                note="★★ 创建时间不匹配 ⇒ pid 可能已复用 ⇒ 不终止")
        return False
    rec.add("TERM", "identity_pid_verified", pid_identity_ok,
            "script:terminate_owned_process")

    # --- 步 2：发终止（★ `proc` = 本趟 Popen 句柄；★ 从不按 PID 猜杀） ---
    try:
        proc.terminate()
        rec.add("TERM", "terminate_sent", True, "subprocess.Popen:terminate")
    except Exception as e:
        rec.add("TERM", "terminate_sent", False,
                "subprocess.Popen:terminate",
                note=f"★ 终止失败：{e!r}")
        return False

    # --- 步 3：等待退出并复核 ---
    try:
        returncode = proc.wait(timeout=10)
        rec.add("TERM", "wait_returncode", returncode,
                "subprocess.Popen:wait",
                note="★ 进程已退出")
        return True
    except subprocess.TimeoutExpired:
        rec.add("TERM", "wait_timeout", True, "subprocess.Popen:wait",
                note="★★ 10 秒内未退出 ⇒ 尝试 kill")
        try:
            proc.kill()
            returncode = proc.wait(timeout=5)
            rec.add("TERM", "kill_returncode", returncode,
                    "subprocess.Popen:kill",
                    note="★ kill 后已退出")
            return True
        except Exception as e:
            rec.add("TERM", "kill_failed", repr(e),
                    "subprocess.Popen:kill",
                    note="★★ 无法证明目标已退出")
            return False
    except Exception as e:
        rec.add("TERM", "wait_error", repr(e), "subprocess.Popen:wait")
        return False


# ===========================================================================
# [A8] 进程树清扫：终止本趟载体目录下的 gamemd / ra2loader 残留
# ===========================================================================
def _a8_query_image_path(pid: int):
    """★ 只读：取进程可执行文件全路径。失败返回 None。

    ★ 每个 ctypes 调用都声明 argtypes/restype（★ 不声明会让 HANDLE 在 64 位截断）。
    """
    k32 = ctypes.windll.kernel32
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.QueryFullProcessImageNameW.argtypes = [
        wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    k32.QueryFullProcessImageNameW.restype = wt.BOOL
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(2048)
        n = wt.DWORD(2048)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return buf.value
        return None
    finally:
        k32.CloseHandle(h)


def _a8_path_under_carrier(image_path: str, carrier_dir: Path) -> bool:
    """★ 路径归属判定：image_path 是否落在 carrier_dir 之下。

    ★ 必须按**目录边界**比较，不能只用 startswith：
      载体 `...\abc` 与 `...\abcd` 前者是后者前缀，startswith 会误判。
    """
    if not image_path:
        return False
    try:
        img = Path(image_path).resolve()
        base = Path(carrier_dir).resolve()
    except Exception:
        return False
    try:
        img.relative_to(base)
        return True
    except ValueError:
        return False


def a8_sweep_carrier_processes(rec: Recorder, carrier_dir: Path,
                               own_pid: int | None) -> dict:
    """★★ [A8] 按载体目录精确清扫 gamemd / ra2loader 残留（★ 不做按名全杀）。

    ★ 只在 `--allow-loader` 授权趟调用（loader 会派生 gamemd）。
    ★ 三轮重试：子进程退出可能滞后于父进程终止。
    ★ 返回 {"swept": [...], "remaining": [...], "rounds": n}。
    ★★ 调用方必须检查 `remaining` 非空 ⇒ 记收尾失败（V-fail）。
    """
    TARGETS = ("gamemd.exe", "ra2loader.exe")
    swept = []
    rounds = 0
    for _round in range(3):
        rounds = _round + 1
        killed = 0
        for pid in find_pids("gamemd.exe") + find_pids("ra2loader.exe"):
            if own_pid is not None and pid == own_pid:
                continue
            img = _a8_query_image_path(pid)
            if img is None or not _a8_path_under_carrier(img, carrier_dir):
                continue
            k32 = ctypes.windll.kernel32
            k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
            k32.OpenProcess.restype = wt.HANDLE
            k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
            k32.TerminateProcess.restype = wt.BOOL
            k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
            k32.WaitForSingleObject.restype = wt.DWORD
            k32.CloseHandle.argtypes = [wt.HANDLE]
            k32.CloseHandle.restype = wt.BOOL
            PROCESS_TERMINATE = 0x0001
            SYNCHRONIZE = 0x00100000
            h = k32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
            if not h:
                continue
            try:
                if k32.TerminateProcess(h, 1):
                    k32.WaitForSingleObject(h, 5000)
                    killed += 1
                    swept.append({"pid": pid, "image": img})
            finally:
                k32.CloseHandle(h)
        if killed == 0:
            break
        time.sleep(0.8)

    # ★ 收尾断言：再枚举一次，看还有没有落在我载体目录下的
    remaining = []
    for pid in find_pids("gamemd.exe") + find_pids("ra2loader.exe"):
        if own_pid is not None and pid == own_pid:
            continue
        img = _a8_query_image_path(pid)
        if img is not None and _a8_path_under_carrier(img, carrier_dir):
            remaining.append({"pid": pid, "image": img})

    rec.add("A8", "a8_sweep_enabled", True, "script:a8_sweep_carrier_processes",
            note="★★ [A8] 授权趟进程树清扫（按载体目录精确匹配，非按名全杀）")
    rec.add("A8", "a8_carrier_dir", str(carrier_dir),
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_swept_count", len(swept),
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_swept_detail", swept, "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_remaining_count", len(remaining),
            "script:a8_sweep_carrier_processes",
            note="★★ 必须为 0；非 0 ⇒ 该趟 V-fail")
    rec.add("A8", "a8_remaining_detail", remaining,
            "script:a8_sweep_carrier_processes")
    rec.add("A8", "a8_rounds", rounds, "script:a8_sweep_carrier_processes")
    return {"swept": swept, "remaining": remaining, "rounds": rounds}


# ===========================================================================
# §10 · ⑤ 导航链与采帧
# ===========================================================================
def find_main_window(pid: int) -> tuple:
    """★ 取**主窗** `hwnd` + 矩形 + 标题 + `visible`。

    ★ 自建（★ 理由见 `find_pids` docstring）。
    ★ `GetWindowRect`（★ 判 `0x0` 退化必须用主窗 `GetWindowRect`，`D-59`）。
    """
    user32 = ctypes.windll.user32
    # ★ QC183：HWND/HDC 等均为 64 位指针值，必须声明防截断。
    user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
    user32.GetWindowThreadProcessId.restype = wt.DWORD
    user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
    user32.GetWindowRect.restype = wt.BOOL
    user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.IsWindowVisible.argtypes = [wt.HWND]
    user32.IsWindowVisible.restype = wt.BOOL
    # ★★ QC184：★ 回调取**具名**类型（`WNDENUMPROC`），★ 并直接用作
    #   `EnumWindows` 第 1 参的 `argtypes` ⇒ ★ 函数指针**按指针宽度**传递。
    #   ★ QC183 用 `c_void_p` 承接回调：能调用，但**类型不精确**——
    #     ★ 回调实例经 `c_void_p` 中转时，ctypes 对"函数指针 vs 数据指针"
    #       的接纳依赖实现细节 ⇒ ★ 显式 `WINFUNCTYPE` 才是 64 位正确口径。
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                     ctypes.c_void_p)
    user32.EnumWindows.argtypes = [WNDENUMPROC, wt.LPARAM]
    user32.EnumWindows.restype = wt.BOOL
    res = {"hwnd": None, "fallback": None, "info": []}
    pid_buf = ctypes.c_ulong()

    @WNDENUMPROC
    def proc(hwnd, _):
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
        if pid_buf.value == pid:
            r = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            w, h = r.right - r.left, r.bottom - r.top
            t = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, t, 256)
            rec_i = {"hwnd": hwnd, "rect": [r.left, r.top, r.right, r.bottom],
                     "wh": [w, h], "title": t.value,
                     "visible": bool(user32.IsWindowVisible(hwnd))}
            res["info"].append(rec_i)
            if w > 200:
                if rec_i["visible"] and res["hwnd"] is None:
                    res["hwnd"] = hwnd
                elif res["fallback"] is None:
                    res["fallback"] = hwnd
        return True

    user32.EnumWindows(proc, 0)
    return (res["hwnd"] or res["fallback"]), res["info"]


def rect_of(hwnd: int) -> tuple:
    """★ 主窗 `GetWindowRect` ⇒ `(left, top, right, bottom)`（`D-59`）。"""
    # ★ QC183：自声明 argtypes（★ 不依赖 find_main_window 已设置）。
    _u32 = ctypes.windll.user32
    _u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
    _u32.GetWindowRect.restype = wt.BOOL
    r = wt.RECT()
    _u32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def click_logical(hwnd: int, lx: int, ly: int) -> None:
    """★ 点击：**逻辑** `800×600` 坐标 ⇒ **屏**坐标（★ 按主窗原点平移）。

    ★ 逻辑坐标 `NAV_CHAIN` 出处 `QC141:93`。
    ★ 用 `SendInput` 模拟用户输入（★ 与 `qc63_trip.py:25` 同口径）。
    ★ **不改**游戏内存、不注入、不发消息到窗口过程。
    """
    # >>> QC151FS-BEGIN click-map（缺省 off ⇒ 走锚路径，行为逐字节同改前）
    # ★★ QC151FS：全屏下游戏坐标 ⇒ 屏改**直通映射**（窗口原点 + ×1.0，见
    #   `click_logical_fullscreen`）；off（缺省）⇒ 本分支零执行。
    if _QC151FS["on"]:
        click_logical_fullscreen(hwnd, lx, ly)
        return
    # <<< QC151FS-END click-map
    user32 = ctypes.windll.user32
    # ★ QC183：SendInput/SetCursorPos argtypes。
    user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    user32.SetCursorPos.restype = wt.BOOL
    left, top, _, _ = rect_of(hwnd)
    sx, sy = left + lx, top + ly

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD),
                    ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wt.DWORD), ("mi", MOUSEINPUT)]

    # ★ QC183：SendInput argtypes 需引用 INPUT 类型。
    user32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wt.UINT

    def _send(flags: int) -> None:
        inp = INPUT(type=0, mi=MOUSEINPUT(dx=sx, dy=sy, mouseData=0,
                                          dwFlags=flags, time=0, dwExtraInfo=None))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    user32.SetCursorPos(sx, sy)
    _send(0x0002)          # MOUSEEVENTF_LEFTDOWN
    time.sleep(0.05)
    _send(0x0004)          # MOUSEEVENTF_LEFTUP
    time.sleep(0.35)


def click_screen(sx: int, sy: int) -> None:
    """★ 点击 **屏**坐标（★ `(1580,724)` / `(1580,682)`；`QC141:94`）。"""
    user32 = ctypes.windll.user32
    # ★ QC183：同 click_logical。
    user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    user32.SetCursorPos.restype = wt.BOOL

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD),
                    ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wt.DWORD), ("mi", MOUSEINPUT)]

    user32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wt.UINT

    def _send(flags: int) -> None:
        inp = INPUT(type=0, mi=MOUSEINPUT(dx=sx, dy=sy, mouseData=0,
                                          dwFlags=flags, time=0, dwExtraInfo=None))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    user32.SetCursorPos(sx, sy)
    _send(0x0002)
    time.sleep(0.05)
    _send(0x0004)
    time.sleep(0.35)


def _doze(seconds: float) -> None:
    """★ QC197：新增代码的**唯一**延时入口。

    ★★ 既有 7 处 `time.sleep` 一字不动（时长与数量均属禁止面）；本补丁的
      全部新增延时**只**经本函数，便于 grep 自查："time.sleep" 命中数
      改前 7 ⇒ 改后 8，新增仅本处。
    """
    time.sleep(seconds)


def _focus_foreground(hwnd: int) -> dict:
    """★ QC197/P2：导航**前置焦点**（`qc63_trip.py:187 focus_hard` 精简移植）。

    ★ 序列：SW_RESTORE → BringWindowToTop → AttachThreadInput +
      SetForegroundWindow → ALT(keybd_event 0x12) 绕前台锁（★ 仅前两步
      失败时的兜底；★ **不是 Esc(0x1B)**，动用与否逐次 trail 记账）。
    ★ 每次尝试后**校验** `GetForegroundWindow()==hwnd`（不隐藏失败）。
    ★ ★不移植 `minimize_others` 的窗口枚举部分（设计稿 §4.1-P2：遮挡由
      签名闸门失配兜底）。attempts=3。返回 `{"ok", "attempts", "trail"}`。
    """
    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32
    u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
    u32.ShowWindow.restype = wt.BOOL
    u32.BringWindowToTop.argtypes = [wt.HWND]
    u32.BringWindowToTop.restype = wt.BOOL
    u32.SetForegroundWindow.argtypes = [wt.HWND]
    u32.SetForegroundWindow.restype = wt.BOOL
    u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
    u32.AttachThreadInput.restype = wt.BOOL
    u32.GetForegroundWindow.argtypes = []
    u32.GetForegroundWindow.restype = wt.HWND
    u32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, wt.WPARAM]
    u32.keybd_event.restype = None
    u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
    u32.GetWindowThreadProcessId.restype = wt.DWORD
    k32.GetCurrentThreadId.argtypes = []
    k32.GetCurrentThreadId.restype = wt.DWORD
    trail: list = []
    for i in range(3):
        u32.ShowWindow(hwnd, 9)          # SW_RESTORE（cnc-ddraw 无边框窗常态）
        _doze(0.2)
        u32.BringWindowToTop(hwnd)
        fg = u32.GetForegroundWindow()
        trail.append({"attempt": i + 1, "step": "bring_to_top",
                      "fg_is_ours": fg == hwnd})
        if fg == hwnd:
            return {"ok": True, "attempts": i + 1, "trail": trail}
        cur = k32.GetCurrentThreadId()
        tgt = u32.GetWindowThreadProcessId(hwnd, None)
        u32.AttachThreadInput(cur, tgt, True)
        u32.SetForegroundWindow(hwnd)
        u32.AttachThreadInput(cur, tgt, False)
        _doze(0.3)
        if u32.GetForegroundWindow() == hwnd:
            return {"ok": True, "attempts": i + 1, "trail": trail}
        # ★ 兜底：ALT(0x12) 绕前台锁（qc63 focus_hard 同款；唯一 keybd_event）
        u32.keybd_event(0x12, 0, 0, 0)
        u32.keybd_event(0x12, 0, 2, 0)
        u32.SetForegroundWindow(hwnd)
        _doze(0.3)
        trail.append({"attempt": i + 1, "step": "alt_bypass",
                      "fg_is_ours": u32.GetForegroundWindow() == hwnd})
        if u32.GetForegroundWindow() == hwnd:
            return {"ok": True, "attempts": i + 1, "trail": trail}
    return {"ok": u32.GetForegroundWindow() == hwnd, "attempts": 3, "trail": trail}


def capture_frame(hwnd: int, out_png: Path) -> tuple:
    """★ 截主窗为客户区 `800×600` 并落 `PNG`（★ **不落盘 bytecode**，是图片）。

    ★★ **采帧固定 `800×600`**（`QC141:79`）。
    ★★ 若实测主窗**不是** `800×600` ⇒ ★ 返回 `resolution_ok=False`，
      该帧 `L-A` 记 **`null`**（★ **不得记 `False`**，`D-53`）。
    ★ `PrintWindow` 只**渲染**窗口到位图 ⇒ ★ **不读进程内存**、不改目标。
    """
    # >>> QC151FS-BEGIN capture（缺省 off ⇒ PrintWindow 路径，行为逐字节同改前）
    # ★★ QC151FS：全屏 ⇒ 抓帧切**桌面拷贝**（实证：PrintWindow 旗标 0/2 对
    #   独占面返回黑/失败；桌面拷贝有效）。本函数=唯一采帧缝 ⇒ wait_screen/
    #   guard/burst/early-frame/目标帧/measure 空闲取证等全部既有调用点零改动
    #   即被覆盖；QC214 guard-v3 抓帧位同样经此缝（与其五 hunk 区域零重叠）。
    if _QC151FS["on"]:
        return capture_frame_desktop(hwnd, out_png)
    # <<< QC151FS-END capture
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    # ★ QC183：HDC/HBITMAP 均为 64 位指针值。
    user32.GetDC.argtypes = [wt.HWND]
    user32.GetDC.restype = wt.HDC
    user32.PrintWindow.argtypes = [wt.HWND, wt.HDC, wt.UINT]
    user32.PrintWindow.restype = wt.BOOL
    user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
    gdi32.CreateCompatibleDC.restype = wt.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wt.HBITMAP
    gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
    gdi32.SelectObject.restype = wt.HGDIOBJ
    gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
    gdi32.DeleteObject.restype = wt.BOOL
    gdi32.DeleteDC.argtypes = [wt.HDC]
    gdi32.DeleteDC.restype = wt.BOOL
    left, top, right, bottom = rect_of(hwnd)
    w, h = right - left, bottom - top
    resolution_ok = (w == FRAME_W and h == FRAME_H)

    hdc = user32.GetDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 0)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long),
                    ("biHeight", ctypes.c_long), ("biPlanes", wt.WORD),
                    ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                    ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                    ("biClrImportant", wt.DWORD)]

    bi = BITMAPINFOHEADER()
    bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.biWidth, bi.biHeight = w, -h      # 负高 = 自上而下
    bi.biPlanes, bi.biBitCount = 1, 24
    stride = ((w * 3 + 3) // 4) * 4
    buf = ctypes.create_string_buffer(stride * h)
    # ★ QC183：GetDIBits argtypes。
    gdi32.GetDIBits.argtypes = [
        wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT,
        ctypes.c_void_p, ctypes.POINTER(BITMAPINFOHEADER), wt.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)

    write_png_no_filter(out_png, w, h, buf.raw, stride)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return resolution_ok, (w, h)


# >>> QC151FS-BEGIN funcs（嵌套哨兵：删本块=还原锚 5b435487…；缺省 off ⇒ 全部零调用）
def _fs_ensure_foreground(hwnd: int) -> bool:
    """★ QC151FS：每次抓帧前把游戏窗口置前台（轻量；**不**替代 `_focus_foreground`）。

    ★ 任务口径：抓帧前 `SetForegroundWindow(MainWindowHandle)`。已前台 ⇒ 零
      系统调用。置前失败（前台锁拒绝）不抛，仅 `fg_attempts/fg_fail` 记账 ⇒
      桌面拷贝仍执行，若被他窗遮挡则签名闸自然失配，不造假。
      ★ 重型三段序列（ALT 绕锁等）仍专属导航期 `_focus_foreground`，此处不动。
    """
    u32 = ctypes.windll.user32
    u32.GetForegroundWindow.argtypes = []
    u32.GetForegroundWindow.restype = wt.HWND
    u32.SetForegroundWindow.argtypes = [wt.HWND]
    u32.SetForegroundWindow.restype = wt.BOOL
    if u32.GetForegroundWindow() == hwnd:
        return True
    _QC151FS["fg_attempts"] += 1
    _ok = bool(u32.SetForegroundWindow(hwnd))
    if not _ok:
        _QC151FS["fg_fail"] += 1
    return _ok


def capture_frame_desktop(hwnd: int, out_png: Path) -> tuple:
    """★ QC151FS：全屏抓帧=桌面拷贝（GDI **屏 DC BitBlt**；实证对全屏内容有效）。

    ★ 抓取区=窗口原点+`FS_RENDER_ORIGIN` 起 `FRAME_W×FRAME_H`（800×600）——
      实证渲染面自屏幕左上 (0,0) 起**不缩放**；只抓渲染面 ⇒ 下游 qc95 分类/
      红钮签名/战术色数继续消费**已校准的 800×600 口径**，零改动。
    ★ 返回契约与 `capture_frame` 同构：`(resolution_ok, (w,h))`；全屏下
      `resolution_ok` 按构造为 True（抓取区即判据口径尺寸）；主窗矩形退化
      （0 尺寸）⇒ 回落屏幕 (0,0)（实证渲染面原点）。
    ★ `BitBlt` 只读屏 DC 到位图 ⇒ **不读进程内存**、不改目标（PrintWindow 同纪律）。
    """
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    _fs_ensure_foreground(hwnd)
    user32.GetDC.argtypes = [wt.HWND]
    user32.GetDC.restype = wt.HDC
    user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
    gdi32.CreateCompatibleDC.restype = wt.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wt.HBITMAP
    gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
    gdi32.SelectObject.restype = wt.HGDIOBJ
    gdi32.BitBlt.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             ctypes.c_int, wt.HDC, ctypes.c_int, ctypes.c_int,
                             wt.DWORD]
    gdi32.BitBlt.restype = wt.BOOL
    gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
    gdi32.DeleteObject.restype = wt.BOOL
    gdi32.DeleteDC.argtypes = [wt.HDC]
    gdi32.DeleteDC.restype = wt.BOOL
    w, h = FRAME_W, FRAME_H
    try:
        _l, _t, _r, _b = rect_of(hwnd)
    except Exception:
        _l, _t, _r, _b = 0, 0, 0, 0
    ox = (_l if (_r - _l) > 0 else 0) + FS_RENDER_ORIGIN[0]
    oy = (_t if (_b - _t) > 0 else 0) + FS_RENDER_ORIGIN[1]

    sdc = user32.GetDC(None)                 # ★ 屏 DC（桌面拷贝源）
    mem = gdi32.CreateCompatibleDC(sdc)
    bmp = gdi32.CreateCompatibleBitmap(sdc, w, h)
    gdi32.SelectObject(mem, bmp)
    gdi32.BitBlt(mem, 0, 0, w, h, sdc, ox, oy, 0x00CC0020)   # SRCCOPY

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long),
                    ("biHeight", ctypes.c_long), ("biPlanes", wt.WORD),
                    ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                    ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                    ("biClrImportant", wt.DWORD)]

    bi = BITMAPINFOHEADER()
    bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.biWidth, bi.biHeight = w, -h      # 负高 = 自上而下
    bi.biPlanes, bi.biBitCount = 1, 24
    stride = ((w * 3 + 3) // 4) * 4
    buf = ctypes.create_string_buffer(stride * h)
    gdi32.GetDIBits.argtypes = [
        wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT,
        ctypes.c_void_p, ctypes.POINTER(BITMAPINFOHEADER), wt.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)

    write_png_no_filter(out_png, w, h, buf.raw, stride)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(None, sdc)
    return True, (w, h)


def _fs_arrival_poll(hwnd: int, rec: Recorder, mod) -> bool:
    """★ QC151FS：全屏到达判据单轮轮询（window 稳定循环内每 ~0.5 s 一轮）。

    ★ **判定臂** = 主菜单色签名：非黑门后 `_red_button_centers` 红带中心集 vs
      `SCREEN_SIG["mainmenu"]` 子集±3 + absent 否决（T20/T21 真机校准，零新增
      判据）⇒ 命中由锚 `_stab_same×2` 机制连续 2 轮确认 = 到达。
    ★ **遥测臂（不判定）** = 非黑 ∧ 与 boot 基线帧平均绝对差 ≥
      `FS_LOGO_DIFF_MIN`：boot 推进指示；片头影片帧同样满足该臂 ⇒ 仅凭它无法
      区分菜单/影片，只落 `WIN.fs_arrival` 遥测供 T55 复准（不据此宣布到达）。
    ★ 首轮捕到即锁基线帧（`baseline`，仅 diff 参照，不落盘）。
    """
    _fs_ensure_foreground(hwnd)
    png = WORKDIR / "fs_boot_probe.png"
    try:
        _ok_cap, _wh = capture_frame_desktop(hwnd, png)
    except Exception as _e:
        _QC151FS["poll_errs"].append({"kind": "capture", "err": repr(_e)})
        return False
    if not _ok_cap:
        return False
    try:
        _w, _h, _img = mod.load_rgb(str(png))
        _luma = float(_img.mean())
        _sig_ok = False
        _centers = None
        if _luma >= FS_LUMA_FLOOR:
            _centers = _red_button_centers(png, mod)
            _sig_ok = bool(_sig_match(
                _centers, list(SCREEN_SIG["mainmenu"]["present"]),
                absent=list(SCREEN_SIG["mainmenu"].get("absent", []))))
        _diff = None
        _diff_ok = False
        _base = _QC151FS["baseline"]
        if _base is not None:
            _diff = float(abs(_img.astype(int) - _base.astype(int)).mean())
            _diff_ok = bool(_luma >= FS_LUMA_FLOOR
                            and _diff >= FS_LOGO_DIFF_MIN)
        if _QC151FS["baseline"] is None:
            _QC151FS["baseline"] = _img.copy()
        _arrived = _sig_ok
        if _arrived:
            _QC151FS["arrival"] = True
        if len(_QC151FS["arrival_polls"]) < 240:
            _QC151FS["arrival_polls"].append({
                "png": png.name, "cap_ok": True, "wh": [_w, _h],
                "luma": round(_luma, 2), "red_centers": _centers,
                "sig_ok": _sig_ok,
                "diff_vs_baseline": (None if _diff is None
                                     else round(_diff, 2)),
                "diff_ok": _diff_ok, "arrived": _arrived})
        return _arrived
    except Exception as _e:
        _QC151FS["poll_errs"].append({"kind": "metrics", "err": repr(_e)})
        return False


def click_logical_fullscreen(hwnd: int, lx: int, ly: int) -> None:
    """★ QC151FS：全屏坐标**直通映射**——屏 = 窗口原点 + 游戏坐标 × `FS_SCALE`(=1.0)。

    ★ 替换窗口时代 533×400 DPI 虚拟化换算（×0.667）语义：全屏**不缩放**、
      渲染面原点实证 (0,0) ⇒ 系数恒 1.0，仅平移（与 SetProcessDPIAware 物理
      像素口径一致）。
    ★ 复用既有 `click_screen`（SendInput 同口径，零重复结构）；越出 800×600
      渲染面仍执行但记 `in_surface=False` 遥测——不静默造假。
    """
    _l, _t, _r, _b = rect_of(hwnd)
    _sx = int(_l + lx * FS_SCALE)
    _sy = int(_t + ly * FS_SCALE)
    if len(_QC151FS["clicks"]) < 64:
        _QC151FS["clicks"].append({
            "lx": lx, "ly": ly, "origin": [_l, _t], "screen": [_sx, _sy],
            "scale": FS_SCALE,
            "in_surface": bool(0 <= lx < FRAME_W and 0 <= ly < FRAME_H)})
    click_screen(_sx, _sy)
# <<< QC151FS-END funcs


def write_png_no_filter(path: Path, w: int, h: int, raw: bytes, stride: int) -> None:
    """★ 写**规范 PNG**（★ 每行前置 1 字节 filter type = 0；★ 逐像素 B/R 交换）。

    ★★ D-114（帧文件非标准 PNG）：旧实现逐行**只取** `w*3` 字节、**不写**
      PNG 规范要求的 1 字节 filter type ⇒ IDAT 解压长度 = `w*h*3`
      （464×191 实测 265,872），标准解码器（Pillow）报
      `OSError: unrecognized data stream contents`。现每行前置 `0x00`
      （filter type 0 = None）⇒ 解压长度 = `h*(1+w*3)`（464×191 = 266,063），
      成为**规范 PNG**。★ 函数名里的 `no_filter` 仍准确：逐行 filter type 恒为 0。

    ★★ D-115（像素 R/B 互换）：`GetDIBits`（`:1394`）取到的是 24bpp
      **`BI_RGB`** DIB（`biCompression` 未赋值 ⇒ 0 = `BI_RGB`），内存序
      **B,G,R**；而本函数 IHDR `colortype=2` 期望 **R,G,B** ⇒ 旧实现把 R/B
      写反（屏幕上红色 X 图标 ⇒ 文件里成了蓝盘）。现写出时**逐像素交换 B 与 R**，
      使**文件里的颜色 = 屏幕上的颜色**。

    ★ 兼容性依据：`qc95_classify.load_rgb()`
      （`qc95_tactical_criterion/_probe/qc95_classify.py:24` 认 no-filter、
      `:26` 认标准）**同时兼容**两种格式 ⇒ 改标准**不会**破坏它。
    """
    import struct
    import zlib
    rows = bytearray()
    for y in range(h):
        line = raw[y * stride: y * stride + w * 3]      # ★ 丢 stride padding
        px = bytearray(line)
        # ★★ D-115：DIB 内存序 B,G,R ⇒ 交换 B/R 得 R,G,B（屏幕色 = 文件色）
        px[0::3], px[2::3] = line[2::3], line[0::3]
        rows.append(0)                                  # ★★ D-114：filter type 0 = None
        rows += px
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    def _chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    blob = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(rows), 6)) +
            _chunk(b"IEND", b""))
    path.write_bytes(blob)


def classify_frame_LA(png: Path, resolution_ok: bool, rec: Recorder, label: str):
    """★ `L-A`：调用**既有** `qc95_classify.py`（★ **不得改它**）。

    ★ 出处 `QC141:74`/`:75`/`:123`。
    ★★ `resolution_ok=False` ⇒ ★ **直接返回 `None`**（★ 记 `null`，
      ★ **绝不得记 `False`**，`D-53`；`QC141:79`）。
    """
    if not resolution_ok:
        rec.add("LA", f"in_tactical_{label}", None,
                "script:classify_frame_LA",
                note="★★ frame_resolution_mismatch ⇒ L-A 记 null"
                     "（★ **不得记 False**，D-53）")
        return None
    mod = load_qc95(rec)
    w, h, img = mod.load_rgb(str(png))
    feats = mod.features(w, h, img)
    verdict = mod.classify(feats)
    rec.add("LA", f"in_tactical_{label}", verdict,
            f"{QC95_PATH}:83 classify()",
            note="★ 'tactical?(UNVALIDATED)' 前缀 ⇒ 仅候选，非判据")
    rec.add("LA", f"features_{label}", feats, f"{QC95_PATH}:46 features()")
    rec.add("LA", f"frame_wh_{label}", [w, h], f"{QC95_PATH}:15 load_rgb()")
    return verdict


_QC95_MOD = None


def load_qc95(rec: Recorder):
    """★ 延迟 `import` 既有 `qc95_classify.py`（★ **只读**，★ 不改它）。

    ★ `qc95_classify.py` 模块级只有 `import` + `def`（亲读 `:12-13`），
      ★ 无模块级副作用 ⇒ ★ 可安全 `import`。
    """
    global _QC95_MOD
    if _QC95_MOD is not None:
        return _QC95_MOD
    import importlib.util
    spec = importlib.util.spec_from_file_location("qc95_classify", str(QC95_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _QC95_MOD = mod
    rec.add("LA", "qc95_module", str(QC95_PATH), "script:load_qc95",
            note="★ 既有判据模块；★ 只读引用，**未改一字**")
    return mod


# ===========================================================================
# §10.5 · QC197/P3 屏幕状态签名闸门（★ 导航专用；`MENU_NAV_DESIGN_v1.md:§4.1-P3`）
# ===========================================================================
# ★ 期望表出处 = bench_replay.py:885-896（2026-09-28 繁中 800×600 真机校准）。
# ★ 与 qc95_classify.classify() 的分工（设计稿 §3.2）：本表**只作导航闸门**
#   （能区分 mainmenu / sp_submenu / skirmish_setup）；F-6 终判仍唯一挂
#   qc95 的 classify()（两套签名在 scratch S3 用同批截图交叉标定）。
SCREEN_SIG = {
    "mainmenu":       {"present": [220, 262, 304, 346, 388, 556], "absent": []},
    "sp_submenu":     {"present": [220, 262, 304, 556],           "absent": [346, 388]},
    "skirmish_setup": {"present": [262, 304, 556],                "absent": [220]},
}
# ★ QC201b/D-126b：sp_submenu 按 T22 实测重校准——点击 單人遊戲 后 post 轮询
#   red_centers=[61,220,262,304,556]（61=EVA 警告条，状态性；旧 72=幻影带）。
#   取四真钮 [220,262,304,556]；子集判据容忍 61 等状态性多余带。
# ★ ★ 阶段预算注：sp_submenu 校准后 attempt1 的 post 应通过 ⇒ 不再触发
#   attempt2 的二次 25s 预等待（T22 实测该路径把 nav_menu 推到 45.6s>30s 帽）。
# ★ QC201/D-126：mainmenu 按 T20/T21 实测重校准——旧 72 是 bench_replay 时代
#   校准残留（现菜单无此带）；实测六真钮 [220,262,304,346,388,556]（T20 帧
#   实物 + T21 轮询 red_centers 双证）。
# ★ QC206/D-127：T31 实证子集判据的区分力弱化**真实发生**——nav_menu post 在
#   主菜单全 7 带上误判 sp_submenu（[220,262,304,556] ⊂ 主菜单带集）⇒ 假阳性
#   通过后 [700,304] 落在主菜单網口網路 ⇒ 网络大厅屏。修法=**absent 否决**：
#   sp_submenu 须无 346/388（主菜单专属带）；skirmish_setup 须无 220（子菜单
#   专属带；T24 实测其无 220）。battle 后态走 _burst_battle 不经本表。
TACTICAL_COLOR_FLOOR = 600    # ★ 战术区唯一色数下限（bench_replay.py:896）

# ★ QC197/P4：三段导航计划 = (子阶段名, 前态签名, 后态签名, NAV_CHAIN 坐标)；
#   每步点击后等待（bench_replay.py:1197-1215 校准值：2.5 / 9.0 / 6.0 s）。
NAV_SIG_PLAN = (
    ("nav_menu",   "mainmenu",       "sp_submenu",     NAV_CHAIN[0]),
    ("nav_setup",  "sp_submenu",     "skirmish_setup", NAV_CHAIN[1]),
    ("nav_start",  "skirmish_setup", "battle",         NAV_CHAIN[2]),
)
NAV_WAITS_S = {"nav_menu": 3.0, "nav_setup": 3.0, "nav_start": 3.0}
# ★ QC201c/D-125b：T23 实证——NAV_WAITS_S 只被用作点击后渲染 doze（:3935），
#   而 pre 等待由 wait_screen 的阶段余量参数自供给（T23 pre 在其中命中）。
#   25s doze + pre ~15s = 44.7s 顶穿 30s 帽（exit 19，尽管 post 首轮即命中）。
#   子菜单点击后 ~1-2s 渲染完成 ⇒ doze 回归 3.0 纯渲染等待。


def _red_button_centers(png: Path, mod) -> list:
    """★ 侧栏红钮 y 中心集（折算到逻辑 600 高）——导航闸门签名（QC197/P3）。

    ★ 右缘 x≥0.80w 条带；判红口径逐字同 qc95_classify.features：
      `R>140 ∧ R>G+50 ∧ R>B+50`；行红占比 >0.25 聚带、带高 ≥max(4, 0.01h)
      （qc95_classify.py:48/:54-62）。★ 解码复用**已延迟加载**的 `load_rgb`
      （★ 只读调用，qc95 一字不改）；中心折算同 bench_replay.py:923
      `round((y0+y-1)/2 / h * 600)`。
    """
    w, h, img = mod.load_rgb(str(png))
    r = img[:, :, 0].astype(int)
    g = img[:, :, 1].astype(int)
    b = img[:, :, 2].astype(int)
    isred = (r > 140) & (r > g + 50) & (r > b + 50)
    rf = isred[:, int(w * 0.80):].mean(axis=1)
    centers: list = []
    inb = False
    y0 = 0
    for y in range(h):
        v = bool(rf[y] > 0.25)
        if v and not inb:
            inb, y0 = True, y
        elif not v and inb:
            inb = False
            if y - y0 >= max(4, int(h * 0.010)):
                centers.append(int(round((y0 + y - 1) / 2 / h * 600)))
    return centers


def _tactical_color_count(png: Path, mod) -> int:
    """★ 战术区唯一色数：窗口左侧 86% 宽（bench_replay.py:931-941 同口径）。

    ★ 被过场/对话框盖住时塌到 ~365 ⇒ ≥TACTICAL_COLOR_FLOOR 才认战术视图。
    """
    w, h, img = mod.load_rgb(str(png))
    a = img[:, :int(w * 0.86)]
    return len(set(map(tuple, a.reshape(-1, 3).tolist()))) if a.size else -1


def _sig_match(got: list, want: list, tol: int = 3,
               absent: list | None = None) -> bool:
    """★ QC201/D-126：**子集 ±tol** 比对——want 每项须在 got 中有 ≤tol 邻居
      （got 允许状态性多余带，如侧栏 EVA 警告条 61/96 随机出没）；
      len(got) ≥ len(want)（屏幕带数不得少于期望钮数）。
      ★ 旧口径（长度相等+逐项差 ≤tol，bench_replay.py:1000-1002）被 T21
      实测否证：实际检测 8 带 vs 旧期望 7 带，精确相等永不成立。
      ★ QC206/D-127：**absent 否决**——absent 列表中任一带在 got 的 ±tol
      邻域内出现 ⇒ False。T31 实证：主菜单 7 带包含 sp_submenu 全部 4 带
      （子集恒真假阳性），区分带=346/388（主菜单专属）。"""
    if absent:
        if any(any(abs(g - w) <= tol for g in got) for w in absent):
            return False
    return (len(got) >= len(want)
            and all(any(abs(g - w) <= tol for g in got) for w in want))


def wait_screen(hwnd: int, expect: str, timeout: float, rec: Recorder,
                mod, tag: str) -> dict:
    """★ 屏幕状态闸门：轮询到画面签名 == 期望为止（QC197/P3）。

    ★ 每 ~1 s 用既有 `capture_frame`（PrintWindow，不改）采一帧，帧**全落盘**：
      `<tag>_g##.png` = 命中 / `<tag>_x##.png` = 未命中（同 qc63 口径），
      逐轮签名记账。expect ∈ SCREEN_SIG 键（`battle` 后态走 `_burst_battle`）。
    ★ 超时 ⇒ 返回 ok=False（★ **不** sys.exit：由 P4 落 INCOMPLETE，帧阶段照采）。
    ★ 循环留 1.5 s 余量（D-113 教训：不撞 `end_stage` 的 30 s 阶段硬停）。
    """
    _sig = SCREEN_SIG[expect]
    want = list(_sig["present"])
    absent = list(_sig.get("absent", []))   # QC206/D-127: 区分力弱化修复——负向约束
    wall = time.monotonic() + max(timeout, 2.0)   # QC200/D-125: 下限防御——预算<1.5s 余量时曾零轮询
    polls: list = []
    res = {"ok": False, "expect": expect, "want": want, "absent": absent,
           "polls": polls, "png": None}
    i = 0
    while time.monotonic() < wall - 1.5:
        png = WORKDIR / f"navsig_{tag}_{i:02d}_x.png"
        ok_cap, _wh = capture_frame(hwnd, png)
        centers = _red_button_centers(png, mod) if ok_cap else None
        hit = bool(ok_cap and centers is not None
                   and _sig_match(centers, want, absent=absent))
        if hit:
            hit_png = WORKDIR / f"navsig_{tag}_{i:02d}_g.png"
            hit_png.unlink(missing_ok=True)  # QC197b/D-122: WORKDIR 跨趟复用时残留 _g.png 会令 rename 抛 WinError 183 作废整趟
            png.rename(hit_png)
            png = hit_png
            res["ok"] = True
            res["png"] = png.name
        polls.append({"i": i, "png": png.name, "cap_ok": ok_cap,
                      "red_centers": centers, "hit": hit})
        if hit:
            break
        _doze(1.0)
        i += 1
    rec.add("NAV", f"wait_screen_{tag}", res, "script:wait_screen",
            note="★ QC197/P3：签名闸门逐轮（_g=命中/_x=未命中，帧全留档）")
    return res


def _burst_battle(hwnd: int, wall: float, rec: Recorder, mod) -> dict:
    """★ `nav_start` 后态 burst：红钮集==空 ∧ 战术色数 ≥FLOOR（QC197/P4）。

    ★ 记账同 qc124 口径（qc124_trip.py:497-503）：`post_start_burst` 逐轮
      留档、命中即停、附 `burst_owned`。≤6 轮 × ~5 s 间隔，且受 `wall`
      （阶段余量）硬约束（D-113：不撞 `end_stage` 硬停）。
    """
    polls: list = []
    burst_ok = False
    for k in range(6):
        if time.monotonic() >= wall - 1.5:
            break
        png = WORKDIR / f"navsig_burst_{k:02d}_x.png"
        ok_cap, _wh = capture_frame(hwnd, png)
        centers = _red_button_centers(png, mod) if ok_cap else None
        colors = _tactical_color_count(png, mod) if ok_cap else -1
        hit = bool(ok_cap and centers == [] and colors >= TACTICAL_COLOR_FLOOR)
        if hit:
            hit_png = WORKDIR / f"navsig_burst_{k:02d}_g.png"
            hit_png.unlink(missing_ok=True)  # QC197b/D-122: 同上（burst 位点）
            png.rename(hit_png)
            png = hit_png
            burst_ok = True
        polls.append({"k": k, "png": png.name, "cap_ok": ok_cap,
                      "red_centers": centers, "tactical_colors": colors,
                      "hit": hit})
        if hit or k == 5:
            break
        _doze(min(5.0, max(0.0, wall - 1.5 - time.monotonic())))
    res = {"ok": burst_ok, "expect": "battle", "polls": polls,
           "burst_owned": burst_ok}
    rec.add("NAV", "post_start_burst", res, "qc124_trip.py:497 同口径",
            note="★ QC197/P4：红钮集==空 ∧ 战术色数≥600；_g=命中/_x=未命中")
    return res


# >>> QC210-BEGIN section（§10.7b 整节为本次新增；删本节即还原改前锚 f587dfdd…）
# ===========================================================================
# §10.7b · QC210 显式遭遇战指位段 + 帧钟 burst 分类器（★ 纯新增节）
# ===========================================================================
# ★★ 授权与出处（goal1_earlyend_analysis_20261018\EARLY_END_ANALYSIS.md
#   §10/§11/§11.1，2026-10-18 定谳）：遭遇战自动指位把两家压到第一个已定义
#   出生点 wp0 ⇒ 指位碰撞随机胜负（T34 人类赢/T35 AI 赢），wp1 从未被用。
#   本节两件事：①设置屏显式指位（人类行位置=1、AI 行位置=2；S1..S4
#   点→抓帧→定位→点 + S5 验证）；②burst 开战判据改**帧钟推进**（T35 实测
#   战斗实际跑了 16s 但 tactical_colors=1 恒定 ⇒ 旧判据「红钮空 ∧ 色数≥600」
#   失效）。
# ★★ 纪律（同 §10.5/§10.8 房规）：
#   - 只读 + SendInput 合成输入（spot 点击与既有 nav 点击同类；零禁止面漂移）；
#   - RPM 只沿用 §10.8 既有 `_rpm_open/_rpm_u32/_rpm_close` 只读模式；
#   - 延时只经既有 `_doze`（`time.sleep` 命中数不增）；
#   - 定位不确定 ⇒ readings 如实记 + 按首项估计值兜底 + S5 验证兜底（不硬造）。
# ★ 坐标出处 = QC211 实测修正（T36 真机证据 archive_T36 亲读复核；原 §11.1 旧值
#   (487,97)/(487,125) 系分析员误读——T36 实证 S1 落 AI 框内、S3 点两行下空处
#   ⇒ spot_verify_ok=false）。客户区 800×600；主窗 rect [880,420,1680,1020]，
#   同既有 NAV 坐标系 ⇒ 复用 `click_logical`。
#   ★ 独立复核（navsig_nav_setup_post_00_g.png 亲读）：行分隔亮线 y56/y82/y108；
#   人类行「??？」文本带 y65-74、AI 行 y91-100（x488-504）；框竖边线 x467/x524
#   ⇒ 框中心 (490,70)/(490,95) 与下达值一致；红「1」徽标 x25-29,y77-80 旁证行序。
_QC210_SPOT = {"on": False, "pid": None}   # ★ 运行态开关（main 装载；模块级容器）

SPOT_HUMAN_BOX_XY = (490, 70)      # S1 人类行「位置」框点击点（QC211 实测修正）
SPOT_AI_BOX_XY = (490, 95)         # S3 AI 行「位置」框点击点（QC211 实测修正）
SPOT_HUMAN_BOX_REGION = (473, 60, 508, 79)   # 人类框像素区 (x0,y0,x1,y1)（QC211；36×20）
SPOT_AI_BOX_REGION = (473, 85, 508, 104)     # AI 框像素区（QC211；与人类框同形 36×20）
SPOT_ITEM_H_EST = 18               # ★ 下拉项高 ~17-19px 的中值估计（§11.1）
SPOT_LIST_GAP_EST = 12             # ★ 框底→首项中心估距（QC211 起按实测框区自适应：
                                   #   人类首项≈79+12=91、AI 首项≈104+12=116）
SPOT_PANEL_SCAN_DY = 84            # ★ 列表扫描深度（框底下方 ~4-5 项）
SPOT_PANEL_SCAN_DX = 45            # ★ 列表扫描右扩（列表可能比框略宽）
SPOT_CLICK_DOZE_S = 0.6            # ★ 每次点击后渲染等待（下拉/收起为即时 UI）
SPOT_VERIFY_MIN_CHG = 8            # ★ S5 判「框文本已变」的最小像素变化数
#   ★★ QC211 阈值复核：真框 36×20=720px（旧假定区 66×19=1254）；T36 设置屏
#   真帧（navsig_nav_setup_post_00_g）亲测「??？」亮墨迹=86px/框（>150 亮度
#   口径）⇒ ???→数字 实际变化约百 px 量级；阈值 8 ≈ 框区 1.1%，保守且约一个
#   数量级低于预期变化。PrintWindow+无损 PNG ⇒ 同态帧逐字节相同（T36 S5 帧与
#   基线 0px 差实证）⇒ 无噪声底，无需更高阈值。
SPOT_WINDOW_BUDGET_S = 16.0        # ★ 段内自限（< STAGE_TIMEOUT_S=30 帽；独立小阶段）
# >>> QC212-BEGIN const（嵌套哨兵：删本块=还原 QC211 锚 84598f9a…）
# ★★ QC212 正向判据与守卫耐心参数（T38 真机标定；archive_T38 亲测，判据依据
#   DARK_FRAME_ANALYSIS.md §3.2/§3.3-2 预注册升级路径 + T38 实证）：
#   - T38 [63,96] 态帧（spot_guard_S2_0/1/2）与 T36 暗帧**逐字节同哈希**
#     （d9fa3804…）＝地图预览/装载瞬态（分析件 §1.5/§7-H1）：框区亮像素 0/0、
#     面板行 0、框列区红像素 0 ⇒ 非「下拉打开态」（H3 被证伪；[63,96] 系 EVA
#     横幅被下凹切两带 + 侧栏菜单钮灰化，非列表项红带）；
#   - 下拉开态唯一实拍 spot_S1_open 与 setup 签名/框亮逐指标同构（下拉对
#     PrintWindow 不可见）⇒ 白名单无视觉特征可依，改以等效解：正向判据 +
#     耐心扩展（见 guard-v2 块注）。
SPOT_POSITIVE_LUM = 100           # ★ 正向判据亮度阈值（分析件 §3.3-2 同口径：
                                  #   设置屏 106/106、瞬态 0/0、burst 0/0、战术 0/0）
SPOT_GUARD_TRIES_PRE = 3          # ★ S1/S3（点击前）守卫轮数（T36/T38 首轮即绿）
SPOT_GUARD_TRIES_POST = 6         # ★ S2/S4（点击后）守卫轮数：6×1.0s≈7s 窗覆盖
                                  #   T38 实测瞬态寿命 ≈2.5-4s（原 3×0.7s≈2.3s 不足
                                  #   ⇒ T38 误判 screen_changed、S2-S5 被绝育）
SPOT_GUARD_RETRY_S = 1.0          # ★ 重试间隔（原 0.7s → 1.0s）
# <<< QC212-END const
# >>> QC214-BEGIN const（嵌套哨兵：删本块=还原锚 5b435487…）
# ★★ QC214 下拉态白名单守卫参数（QC214_BOXSIG_DESIGN.md §5-1，窗口取值理由 §3：
#   3.0s = trip :1813 自报标定「瞬态寿命 2.5-4s」区间中位、≈2× 正常
#   「点击→面板可见→列表项点击」节奏（实测 <2s，:2160/:2208 抓帧位互证）、
#   显著小于 S2/S4 守卫总耐心 6×1.0s≈7s（:1812）⇒ 超窗 [63,96] 如实落
#   screen_changed，不构成「永真白名单」。
SPOT_DROPDOWN_WINDOW_S = 3.0      # ★ 白名单窗口宽（classify_screen 形参口径）
# ★ 纯函数校验模块（★ 只读引用，本体零改动零就地写——禁区）：
QC214_BOXSIG_PATH = (LEAD / "qc214_boxsig_20261018" / "boxsig_verify.py")
# <<< QC214-END const


def _spot_region_sig(png: Path, mod, region: tuple) -> dict:
    """★ S5 验证用：框区像素签名（sha256 前 16 + 暗像计数）。

    ★ 只读解码（既有 `load_rgb`，qc95 一字不改）；区域越界按帧界裁剪。
    """
    w, h, img = mod.load_rgb(str(png))
    x0, y0, x1, y1 = region
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w - 1, x1), min(h - 1, y1)
    rows = img[y0:y1 + 1, x0:x1 + 1]
    dark = 0
    for px in rows.reshape(-1, 3).tolist():
        if px[0] < 100 and px[1] < 100 and px[2] < 100:
            dark += 1
    return {"sha256_16": hashlib.sha256(rows.tobytes()).hexdigest()[:16],
            "w": int(x1 - x0 + 1), "h": int(y1 - y0 + 1), "dark_px": int(dark)}


def _spot_region_diff(png_a: Path, png_b: Path, mod, region: tuple) -> dict:
    """★ S5 验证用：两帧同框区**像素变化数**（???→数字 ⇒ 大量变化）。

    ★ 解码失败/形状不齐 ⇒ `error` 如实记（不硬造 0）。
    """
    try:
        w, h, img_a = mod.load_rgb(str(png_a))
        _w2, _h2, img_b = mod.load_rgb(str(png_b))
        x0, y0, x1, y1 = region
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w - 1, x1), min(h - 1, y1)
        a = img_a[y0:y1 + 1, x0:x1 + 1]
        b = img_b[y0:y1 + 1, x0:x1 + 1]
        if a.shape != b.shape:
            return {"error": "shape_mismatch", "changed_px": None}
        return {"changed_px": int((a != b).any(axis=2).sum()),
                "n_px": int(a.shape[0] * a.shape[1])}
    except Exception as e:
        return {"error": repr(e), "changed_px": None}


def _spot_locate_item(png_open: Path, png_base: Path, mod, box_region: tuple,
                      want_index: int) -> tuple:
    """★ S2/S4：以**实拍帧**定位下拉列表第 want_index 项（0 基；禁盲点主路径）。

    ★ 三层定位（§11.1：必须实拍定位；不确定 ⇒ 兜底 + S5 验证兜底）：
      ① ink_band：S1/S3 后帧 vs 基线帧在框下扫描带做逐行变化数 ⇒ 下拉面板
        行集（面板遮蔽 ⇒ 与基线显著不同；行数 ≥项高半 且 面板顶紧贴框底
        ±窗口 才认）；面板内再做「与行中位亮度离群 ≥60」墨迹行聚带 ⇒
        项中心（带序=项序，中心须落在该项几何窗内）。
      ② panel_geometric：面板行集可信但墨迹带不足 ⇒ 项中心=面板顶+10+项高×k。
      ③ fallback_estimate：面板不可信 ⇒ 首项估计 (框中心x, 框底+12+项高×k)
        （QC211 起按实测框区自适应：人类首项≈79+12=91、AI 首项≈104+12=116；
        旧 §11.1 值 118 系按误读框区推得，作废）。
    ★ 返回 `(xy, meta)`；meta 全量落 readings（located/面板行/墨迹带表）。
    """
    w, h, img_open = mod.load_rgb(str(png_open))
    _w0, _h0, img_base = mod.load_rgb(str(png_base))
    bx0, by0, bx1, by1 = box_region
    cx = (bx0 + bx1) // 2
    sx0 = max(0, bx0 - 5)
    sx1 = min(w - 1, bx1 + SPOT_PANEL_SCAN_DX)
    sy0 = min(h - 1, by1 + 1)
    sy1 = min(h - 1, by1 + SPOT_PANEL_SCAN_DY)
    meta = {"located": "fallback_estimate", "panel_rows": None,
            "ink_bands": None, "scan": [sx0, sy0, sx1, sy1]}
    xy = (cx, by1 + SPOT_LIST_GAP_EST + SPOT_ITEM_H_EST * want_index)
    try:
        if img_open.shape != img_base.shape:
            meta["error"] = "shape_mismatch_vs_base"
            return xy, meta
        # ①-a 面板行：与基线帧相比显著变化的行（下拉面板遮蔽 ⇒ 变化大）
        panel_rows = []
        for y in range(sy0, sy1 + 1):
            n_chg = int((img_open[y, sx0:sx1 + 1] != img_base[y, sx0:sx1 + 1])
                        .any(axis=1).sum())
            if n_chg >= 8:
                panel_rows.append(y)
        meta["panel_rows"] = [panel_rows[0], panel_rows[-1]] if panel_rows else []
        if len(panel_rows) < SPOT_ITEM_H_EST // 2:
            return xy, meta                      # 面板未见 ⇒ 估计兜底
        p_top = panel_rows[0]
        if not (by1 - 6 <= p_top <= by1 + 14):   # 面板顶须紧贴框底
            meta["panel_reject"] = f"panel_top={p_top} not near box_bottom={by1}"
            return xy, meta
        # ①-b 面板列：面板行块内逐列变化数 ≥ 行数半 ⇒ 面板列范围
        #   （列表可窄于扫描窗 ⇒ 墨迹分析只看面板列，防框外背景带偏置中位数）
        n_p = len(panel_rows)
        _blk_o = img_open[panel_rows[0]:panel_rows[-1] + 1, sx0:sx1 + 1]
        _blk_b = img_base[panel_rows[0]:panel_rows[-1] + 1, sx0:sx1 + 1]
        col_chg = (_blk_o != _blk_b).any(axis=2).sum(axis=0)
        pcols = [sx0 + i for i, v in enumerate(col_chg.tolist())
                 if int(v) >= n_p // 2]
        meta["panel_cols"] = [pcols[0], pcols[-1]] if pcols else None
        if not pcols:
            return xy, meta
        pc0, pc1 = pcols[0], pcols[-1]
        # ①-c 面板内墨迹行（限面板列）：与行中位亮度离群 ≥60 的像素 ≥2
        band_rows = []
        for y in panel_rows:
            lum = sorted((int(p[0]) * 299 + int(p[1]) * 587 + int(p[2]) * 114)
                         // 1000 for p in img_open[y, pc0:pc1 + 1].tolist())
            med = lum[len(lum) // 2]
            if sum(1 for v in lum if abs(v - med) >= 60) >= 2:
                band_rows.append(y)
        bands: list = []
        for y in band_rows:
            if bands and y - bands[-1][-1] <= 2:
                bands[-1].append(y)
            else:
                bands.append([y])
        centers = [(b[0] + b[-1]) // 2 for b in bands if len(b) >= 2]
        meta["ink_bands"] = centers
        if len(centers) > want_index:
            c = centers[want_index]
            lo = p_top + SPOT_ITEM_H_EST * want_index - 8
            hi = p_top + SPOT_ITEM_H_EST * (want_index + 1) + 6
            if lo <= c <= hi:
                meta["located"] = "ink_band"
                return (cx, int(c)), meta
        # ② 面板几何兜底（面板顶实测；项几何仍估计）
        meta["located"] = "panel_geometric"
        return (cx, int(p_top + 10 + SPOT_ITEM_H_EST * want_index)), meta
    except Exception as e:
        meta["error"] = repr(e)
        return xy, meta


def _spot_centers_match(png: Path, mod) -> tuple:
    """★ QC211：对已落盘帧按**既有** skirmish_setup 签名判屏幕态（机制零新造）。

    ★ 复用 `SCREEN_SIG["skirmish_setup"]`（present [262,304,556]/absent [220]）、
      `_red_button_centers`、`_sig_match`（三者均既有，零改动）。
    ★ 下拉开出不会破坏本签名：红钮带取自 x≥0.80w（≥640px）侧栏，而下拉面板
      在框列区（x≈473-545）⇒ 物理不重叠（T36 证据帧组同口径复核）。
    ★ 返回 `(ok, centers)`。
    """
    sig = SCREEN_SIG["skirmish_setup"]
    centers = _red_button_centers(png, mod)
    ok = bool(_sig_match(centers, list(sig["present"]),
                         absent=list(sig.get("absent", []))))
    return ok, centers
# >>> QC212-BEGIN fns（嵌套哨兵：删本块=还原 QC211 锚 84598f9a…）
def _spot_box_bright(png: Path, mod) -> tuple:
    """★ QC212 正向判据：两处「位置」框区亮像素计数（lum > SPOT_POSITIVE_LUM）。

    ★ 标定（archive_T38/archive_T36 真帧亲测；DARK_FRAME_ANALYSIS §3.3-2 同源）：
      设置屏 106/106（>100 口径；>150 口径 86/86）、瞬态暗帧 0/0、burst 黑屏
      0/0、战术/终帧 0/0 ⇒ 「>0」＝「主区有设置屏内容」，四帧型区分力实证。
    """
    w, h, img = mod.load_rgb(str(png))
    lum = (img[:, :, 0].astype(int) * 299 + img[:, :, 1].astype(int) * 587
           + img[:, :, 2].astype(int) * 114) // 1000
    out = []
    for region in (SPOT_HUMAN_BOX_REGION, SPOT_AI_BOX_REGION):
        x0, y0, x1, y1 = region
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w - 1, x1), min(h - 1, y1)
        out.append(int((lum[y0:y1 + 1, x0:x1 + 1] > SPOT_POSITIVE_LUM).sum()))
    return tuple(out)


def _spot_positive_ok(bright: tuple) -> bool:
    """★ QC212：正向判据——至少一处框区亮像素 >0（暗帧类 0/0 必 False）。"""
    return bool(bright and (bright[0] > 0 or bright[1] > 0))
# <<< QC212-END fns
# >>> QC212-BEGIN centers-v2（嵌套哨兵：删本块=还原 QC211 锚 84598f9a…）
_spot_centers_match_qc211 = _spot_centers_match


def _spot_centers_match(png: Path, mod) -> tuple:
    """★ QC212 包装（同名可插拔缝；锚=紧上方 `_spot_centers_match_qc211`）。

    ★ 签名通过后再过正向判据（**EVA 横幅 ≥3 带假阳性否决**：若未知屏以
      EVA/状态带凑齐 [262,304,556] 邻居，暗帧类框区亮 0 必被拦——分析件
      §3.2 预注册缺陷的封闭）；签名不过 ⇒ 照旧 False。调用方 `_open_frame_checked`
      的重抓/跳过语义不变。
    """
    ok, centers = _spot_centers_match_qc211(png, mod)
    if ok:
        return (_spot_positive_ok(_spot_box_bright(png, mod)), centers)
    return False, centers
# <<< QC212-END centers-v2


def _spot_screen_guard(hwnd: int, mod, tag: str, tries: int = 3) -> dict:
    """★ QC211：spot 段**每步点击前**的屏幕态守卫（设置屏签名仍在才准点）。

    ★★ 防御对象（T36 真机实证）：一过性「暗屏」帧——spot_S1_open 与
      navsig_nav_start_pre_00_x 同内容（迷雾地图+槽位侧栏，centers [63,96]，
      mean_lum 19.4 vs 设置屏 59.2），~1s 自愈、无点击也复现（S5 后→pre_00 暗
      →pre_01 复原）。T36 中该瞬态曾令 S2 定位误判（panel_rows=[107,190] 全带
      ⇒ 盲点 (487,117)）。
    ★ 容忍自愈：连测 tries 轮（间隔 0.7s，帧全留档 `spot_guard_<tag>_*.png`），
      任一轮过 ⇒ 放行；全失败 ⇒ ok=False ⇒ 调用方如实记 readings
      （spot_screen_changed）并中止 spot 段（不盲点）。
    """
    polls: list = []
    ok = False
    for i in range(max(1, tries)):
        png = WORKDIR / f"spot_guard_{tag}_{i}.png"
        ok_cap, _wh = capture_frame(hwnd, png)
        if ok_cap:
            hit, centers = _spot_centers_match(png, mod)
        else:
            hit, centers = False, None
        polls.append({"i": i, "png": png.name, "cap_ok": ok_cap,
                      "red_centers": centers, "hit": hit})
        if hit:
            ok = True
            break
        if i + 1 < max(1, tries):
            _doze(0.7)
    return {"tag": tag, "ok": ok, "expect": "skirmish_setup",
            "tries": max(1, tries), "polls": polls}
# >>> QC212-BEGIN guard-v2（嵌套哨兵：删本块=还原 QC211 锚 84598f9a…）
_spot_screen_guard_qc211 = _spot_screen_guard


def _spot_screen_guard(hwnd: int, mod, tag: str, tries: int = 0) -> dict:
    """★ QC212 包装（同名可插拔缝；锚=紧上方 `_spot_screen_guard_qc211`）。

    ★ 判据 = **正向判据 ∧ 设置屏签名**（正向为必要条件：T38 [63,96] 瞬态与
      T36 暗帧逐字节同哈希、框区亮 0/0——即使未知屏以 EVA ≥3 带凑齐签名假
      阳性，也必被正向判据拦下；DARK_FRAME_ANALYSIS §3.2 预注册缺陷封闭）。
    ★ 耐心（绝育根因修复）：QC211 的 3×0.7s≈2.3s 窗 < T38 实测瞬态寿命
      ≈2.5-4s（14:05:54 现身 → 14:05:57 前自愈）⇒ S2/S4（点击后守卫）扩为
      SPOT_GUARD_TRIES_POST=6 轮 × SPOT_GUARD_RETRY_S=1.0s ≈7s 窗；
      S1/S3 维持 3 轮（T36/T38 首轮即绿）。轮数用尽仍不过 ⇒ 照旧 ok=False
      （上层如实中止 spot_screen_changed，不盲点）。
    ★ polls 增遥测 `box_bright`/`sig_ok`/`positive_ok`（分析件 §3.3-1 预注册
      升级路径的数据底座）；行结构与 QC211 同形（expect 值挂 qc212 出处）。
    ★ 白名单申报（T38 实证）：任务书设想的「下拉态签名（面板行带+签名缺席）」
      在其自引帧上实测为零（guard_S2 帧与 T36 暗帧同哈希、面板行 0、框区亮
      0/0）；下拉开态唯一实拍 spot_S1_open 与 setup 同构 ⇒ 下拉态经签名臂
      天然放行，无需独立白名单臂——详见 QC212_FIX.md。
    """
    _tries = tries if tries else (SPOT_GUARD_TRIES_POST if tag in ("S2", "S4")
                                  else SPOT_GUARD_TRIES_PRE)
    polls: list = []
    ok = False
    for i in range(max(1, _tries)):
        png = WORKDIR / f"spot_guard_{tag}_{i}.png"
        ok_cap, _wh = capture_frame(hwnd, png)
        if ok_cap:
            sig_ok, centers = _spot_centers_match_qc211(png, mod)
            bright = _spot_box_bright(png, mod)
            pos_ok = _spot_positive_ok(bright)
            hit = bool(pos_ok and sig_ok)
        else:
            sig_ok, centers, bright, pos_ok, hit = (False, None, (0, 0),
                                                    False, False)
        polls.append({"i": i, "png": png.name, "cap_ok": ok_cap,
                      "red_centers": centers, "box_bright": list(bright),
                      "sig_ok": sig_ok, "positive_ok": pos_ok, "hit": hit})
        if hit:
            ok = True
            break
        if i + 1 < max(1, _tries):
            _doze(SPOT_GUARD_RETRY_S)
    return {"tag": tag, "ok": ok, "expect": "skirmish_setup_qc212",
            "tries": max(1, _tries), "polls": polls}
# <<< QC212-END guard-v2
# >>> QC214-BEGIN guard-v3（嵌套哨兵：删本块=还原锚 5b435487…＝QC212 守卫）
_spot_screen_guard_qc212 = _spot_screen_guard

_QC214_BOXSIG = None    # ★ 延迟加载缓存：None=未尝试 False=加载失败 模块=对象


def _boxsig_load():
    """★ QC214：延迟 `import` 既有 `boxsig_verify.py`（★ 只读引用，★ 模块本体一字不改）。

    ★ 风格同 `load_qc95`（:1563-1579：`spec_from_file_location`+`exec_module`）；
      ★ 该模块模块级只有常量+def（亲读 boxsig_verify.py 全文，零 import 零副作用）
      ⇒ 可安全 import。加载失败 ⇒ 缓存 False ⇒ 白名单臂停用（守卫行为逐字回退
      QC212），★ 不抛（本段任何失败都不得把守卫变成崩溃）。
    """
    global _QC214_BOXSIG
    if _QC214_BOXSIG is None:
        try:
            import importlib.util
            _spec = importlib.util.spec_from_file_location(
                "boxsig_verify", str(QC214_BOXSIG_PATH))
            _m = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_m)
            _QC214_BOXSIG = _m
        except Exception:
            _QC214_BOXSIG = False
    return _QC214_BOXSIG or None


def _spot_screen_guard(hwnd: int, mod, tag: str, tries: int = 0,
                       since_click_s: "float | None" = None) -> dict:
    """★ QC214 包装（同名可插拔缝；锚=紧上方 `_spot_screen_guard_qc212`）。

    ★ 判据 = **正向判据 ∧（设置屏签名 ∨ 白名单臂）**（QC214_BOXSIG_DESIGN.md
      §5-3：`hit = pos_ok AND (sig_ok OR boxsig_arm_ok)`；
      `boxsig_arm_ok = classify_screen(centers, "skirmish_setup",
      since_click_s, SPOT_DROPDOWN_WINDOW_S) == "ok_dropdown_open"`）。
      **正向判据仍为必要条件** ⇒ §0 实证矛盾无害化：瞬态暗帧（框亮 0/0）照拦，
      白名单臂只在窗口内且面板臂匹配时扩一处判定面。
    ★ `since_click_s` = 自最近一次**开框点击**（S2←S1、S4←S3）的秒数，由
      `_spot_run` 以 `time.monotonic()` 差值传入（时钟纪律同 :1692；本守卫不
      自读时钟——设计文档 §4-3）；S1/S3 缺省 None ⇒ 白名单臂关 ⇒ 判定与
      QC212 **逐字一致**（面板带在窗口内才可能过，无窗=不可能过）。
    ★ polls 行增遥测 `boxsig_verdict`（三值字符串；模块不可用=
      "module_unavailable"），行结构向后兼容（§5-4，做法同 guard-v2 对 QC211）。
    ★ 出入如实登记（见 QC214_TRIP_PATCH_NOTE.md §3）：guard-v2 :2049-2052 已
      申报「下拉态经签名臂天然放行，无需独立白名单臂」——本补丁按任务书仍接
      白名单臂；在正向判据必真的构造下二者不冲突（臂独启用才会拦不住瞬态，
      此处臂不独用）。boxsig_verify.py 本体零改动（import 调用式集成）。
    """
    _tries = tries if tries else (SPOT_GUARD_TRIES_POST if tag in ("S2", "S4")
                                  else SPOT_GUARD_TRIES_PRE)
    _bs = _boxsig_load()
    polls: list = []
    ok = False
    for i in range(max(1, _tries)):
        png = WORKDIR / f"spot_guard_{tag}_{i}.png"
        ok_cap, _wh = capture_frame(hwnd, png)
        if ok_cap:
            sig_ok, centers = _spot_centers_match_qc211(png, mod)
            bright = _spot_box_bright(png, mod)
            pos_ok = _spot_positive_ok(bright)
        else:
            sig_ok, centers, bright, pos_ok = (False, None, (0, 0), False)
        if _bs is None:
            verdict, arm_ok = "module_unavailable", False
        else:
            verdict = _bs.classify_screen(centers, "skirmish_setup",
                                          since_click_s,
                                          SPOT_DROPDOWN_WINDOW_S)
            arm_ok = bool(verdict == _bs.OK_DROPDOWN)
        hit = bool(pos_ok and (sig_ok or arm_ok))
        polls.append({"i": i, "png": png.name, "cap_ok": ok_cap,
                      "red_centers": centers, "box_bright": list(bright),
                      "sig_ok": sig_ok, "positive_ok": pos_ok, "hit": hit,
                      "boxsig_verdict": verdict})
        if hit:
            ok = True
            break
        if i + 1 < max(1, _tries):
            _doze(SPOT_GUARD_RETRY_S)
    return {"tag": tag, "ok": ok, "expect": "skirmish_setup_qc214",
            "tries": max(1, _tries), "polls": polls}
# <<< QC214-END guard-v3


def _spot_run(hwnd: int, rec: Recorder, mod, budget: TripBudget) -> dict:
    """★ QC210 显式指位段主入口（S1..S5；QC211 坐标/守卫修正版）。

    ★ 前置：nav_setup 后态签名已过（skirmish_setup 屏）；在 nav_start 点击前
      执行（独立小阶段 `spot_select`，自限 SPOT_WINDOW_BUDGET_S 不撞 30s 帽）。
    ★ 每步落 readings 行 `spot_step_S1..S5`（含坐标/定位层/验证结果）；
      S5 = 两处「位置」框区域 基线帧 vs 终帧 像素变化 + 哈希 ⇒ `spot_verify_ok`
      （不过 ⇒ 如实 False，不硬造）。
    ★★ QC211 屏幕态守卫：每步点击前 `_spot_screen_guard`（自愈瞬态重试；
      全败 ⇒ rec 如实记 `spot_screen_changed` 并中止，不盲点）；S1/S3 抓帧
      自证（`_spot_centers_match`）——瞬态暗帧不得作 S2/S4 定位输入
      （T36 实证：瞬态曾致 panel_rows 全带误判 ⇒ 盲点）。
    ★ 焦点前置失败 ⇒ 零点击退出（零盲点纪律；nav_start 由既有焦点纪律自理）。
    """
    out = {"ok": False, "spot_verify_ok": False, "steps": []}
    t_wall = budget.stage_t0 + SPOT_WINDOW_BUDGET_S
    _focus = _focus_foreground(hwnd)
    rec.add("NAV", "spot_focus", _focus, "qc63_trip.py:187 focus_hard 精简移植",
            note="★ QC210：指位段前置焦点（失败 ⇒ 零点击退出）")
    if not _focus["ok"]:
        out["aborted"] = "focus_failed"
        rec.add("NAV", "spot_step_S0", out, "script:_spot_run",
                note="★ QC210：焦点未就位 ⇒ 零点击（零盲点纪律）")
        return out
    alive = True
    # ★ QC214：开框点击时刻表（S1→S2 守卫、S3→S4 守卫的 since_click_s 钟源；
    #   时钟纪律同 :1692 time.monotonic；未点击=None ⇒ 白名单臂关，见 guard-v3）
    _click_t = {"S1": None, "S3": None}

    def _guard(tag: str) -> bool:
        nonlocal alive
        if not alive:
            return False
        # ★ QC214：S2/S4 传「自最近一次开框点击」秒差；S1/S3 与无时刻记录 ⇒
        #   None（白名单关 ⇒ 判定与 QC212 逐字一致，仅多一列遥测）
        _since = None
        if tag == "S2" and _click_t["S1"] is not None:
            _since = time.monotonic() - _click_t["S1"]
        elif tag == "S4" and _click_t["S3"] is not None:
            _since = time.monotonic() - _click_t["S3"]
        g = _spot_screen_guard(hwnd, mod, tag, since_click_s=_since)
        rec.add("NAV", f"spot_guard_{tag}", g, "script:_spot_screen_guard",
                note="★ QC211：点击前设置屏签名守卫（自愈瞬态重试；帧全留档）")
        if not g["ok"]:
            alive = False
            out["aborted"] = "screen_changed"
            rec.add("NAV", "spot_screen_changed", g, "script:_spot_screen_guard",
                    note="★ QC211：设置屏签名消失（重试仍未恢复）⇒ 中止 spot 段、"
                         "不盲点（T36 暗帧防御）")
        return alive

    def _snap(name: str) -> Path:
        p = WORKDIR / name
        capture_frame(hwnd, p)
        return p

    def _left() -> bool:
        return time.monotonic() < t_wall - 1.0

    def _open_frame_checked(png: Path) -> tuple:
        """★ QC211：S1/S3 抓帧自证——瞬态暗帧重抓一次；成功 ⇒ 换用重抓帧
        （定位输入必须是过签名守卫的帧，否则 S2/S4 会在暗帧上定位——T36 事故
        模式 panel_rows 全带误判的根因）。返回 `(ok, frame_to_use)`。"""
        if _spot_centers_match(png, mod)[0]:
            return True, png
        _doze(0.7)
        retry = WORKDIR / (png.stem + "_retry.png")
        capture_frame(hwnd, retry)
        ok2 = _spot_centers_match(retry, mod)[0]
        return ok2, (retry if ok2 else png)

    png_base = WORKDIR / "spot_S0_base.png"
    ok_base, _wh = capture_frame(hwnd, png_base)
    out["base_cap_ok"] = ok_base
    out["base_sig_human"] = (_spot_region_sig(png_base, mod,
                                              SPOT_HUMAN_BOX_REGION)
                             if ok_base else None)
    out["base_sig_ai"] = (_spot_region_sig(png_base, mod, SPOT_AI_BOX_REGION)
                          if ok_base else None)

    # ---- S1：点人类行「位置」框 → 抓帧（下拉展开态） ----
    s1 = {"xy": list(SPOT_HUMAN_BOX_XY), "click": False}
    if not _left():
        s1["skipped"] = "budget"
    elif _guard("S1"):
        click_logical(hwnd, SPOT_HUMAN_BOX_XY[0], SPOT_HUMAN_BOX_XY[1])
        s1["click"] = True
        _click_t["S1"] = time.monotonic()   # ★ QC214：S2 守卫白名单钟源
        _doze(SPOT_CLICK_DOZE_S)
        s1["png"] = _snap("spot_S1_open.png").name
        _ok_v, _use = _open_frame_checked(WORKDIR / s1["png"])
        s1["open_frame_valid"] = _ok_v
        s1["png"] = _use.name   # ★ QC211：重抓成功 ⇒ readings 记重抓帧裸名（口径同 S2/S4）
    else:
        s1["skipped"] = "screen_changed"
    out["steps"].append({"step": "S1", **s1})
    rec.add("NAV", "spot_step_S1", s1, "EARLY_END_ANALYSIS.md:§11.1+QC211",
            note="★ QC211/S1：点人类行「位置」框 (490,70) → 抓帧定位下拉"
                 "（点击前屏幕态守卫）")

    # ---- S2：定位并点列表项「1」（人类行；基线/展开帧无效 ⇒ 不点击，零盲点） ----
    s2 = {}
    if not _left():
        s2["skipped"] = "budget"
    elif not alive:
        s2["skipped"] = "screen_changed"
    elif not (s1.get("png") and ok_base and s1.get("open_frame_valid")):
        s2["skipped"] = ("no_base_frame" if not ok_base
                         else "no_open_frame" if not s1.get("png")
                         else "open_frame_invalid")
    elif _guard("S2"):
        xy, meta = _spot_locate_item(WORKDIR / s1["png"], png_base, mod,
                                     SPOT_HUMAN_BOX_REGION, 0)
        s2["locate"] = meta
        s2["xy"] = list(xy)
        click_logical(hwnd, xy[0], xy[1])
        _doze(SPOT_CLICK_DOZE_S)
        s2["png"] = _snap("spot_S2_done.png").name
        s2["human_box_sig"] = _spot_region_sig(WORKDIR / s2["png"], mod,
                                               SPOT_HUMAN_BOX_REGION)
    else:
        s2["skipped"] = "screen_changed"
    out["steps"].append({"step": "S2", **s2})
    rec.add("NAV", "spot_step_S2", s2, "EARLY_END_ANALYSIS.md:§11.1+QC211",
            note="★ QC211/S2：列表项「1」实拍定位（ink_band/panel_geometric/"
                 "fallback_estimate 三层；展开帧须过屏幕态自证）→ 点击")

    # ---- S3：点 AI 行「位置」框 → 抓帧（下拉展开态） ----
    s3 = {"xy": list(SPOT_AI_BOX_XY), "click": False}
    if not _left():
        s3["skipped"] = "budget"
    elif not alive:
        s3["skipped"] = "screen_changed"
    elif _guard("S3"):
        click_logical(hwnd, SPOT_AI_BOX_XY[0], SPOT_AI_BOX_XY[1])
        s3["click"] = True
        _click_t["S3"] = time.monotonic()   # ★ QC214：S4 守卫白名单钟源
        _doze(SPOT_CLICK_DOZE_S)
        s3["png"] = _snap("spot_S3_open.png").name
        _ok_v, _use = _open_frame_checked(WORKDIR / s3["png"])
        s3["open_frame_valid"] = _ok_v
        s3["png"] = _use.name   # ★ QC211：重抓成功 ⇒ readings 记重抓帧裸名（口径同 S2/S4）
    else:
        s3["skipped"] = "screen_changed"
    out["steps"].append({"step": "S3", **s3})
    rec.add("NAV", "spot_step_S3", s3, "EARLY_END_ANALYSIS.md:§11.1+QC211",
            note="★ QC211/S3：点 AI 行「位置」框 (490,95) → 抓帧定位下拉"
                 "（点击前屏幕态守卫）")

    # ---- S4：定位并点列表项「2」（AI 行；基线/展开帧无效 ⇒ 不点击，零盲点） ----
    s4 = {}
    if not _left():
        s4["skipped"] = "budget"
    elif not alive:
        s4["skipped"] = "screen_changed"
    elif not (s3.get("png") and ok_base and s3.get("open_frame_valid")):
        s4["skipped"] = ("no_base_frame" if not ok_base
                         else "no_open_frame" if not s3.get("png")
                         else "open_frame_invalid")
    elif _guard("S4"):
        xy, meta = _spot_locate_item(WORKDIR / s3["png"], png_base, mod,
                                     SPOT_AI_BOX_REGION, 1)
        s4["locate"] = meta
        s4["xy"] = list(xy)
        click_logical(hwnd, xy[0], xy[1])
        _doze(SPOT_CLICK_DOZE_S)
        s4["png"] = _snap("spot_S4_done.png").name
        s4["ai_box_sig"] = _spot_region_sig(WORKDIR / s4["png"], mod,
                                            SPOT_AI_BOX_REGION)
    else:
        s4["skipped"] = "screen_changed"
    out["steps"].append({"step": "S4", **s4})
    rec.add("NAV", "spot_step_S4", s4, "EARLY_END_ANALYSIS.md:§11.1+QC211",
            note="★ QC211/S4：列表项「2」实拍定位（同 S2 三层+展开帧自证）→ 点击")

    # ---- S5：验证两处「位置」框 ???→数字（像素变化+哈希；不过 ⇒ 如实 False） ----
    s5 = {}
    if not _left():
        s5["skipped"] = "budget"
    elif not alive:
        s5["skipped"] = "screen_changed"
    elif not ok_base:
        s5["skipped"] = "no_base_frame"
    else:
        png_fin = _snap("spot_S5_final.png")
        s5["png"] = png_fin.name
        d_h = _spot_region_diff(png_base, png_fin, mod, SPOT_HUMAN_BOX_REGION)
        d_a = _spot_region_diff(png_base, png_fin, mod, SPOT_AI_BOX_REGION)
        s5["human_box_diff"] = d_h
        s5["ai_box_diff"] = d_a
        s5["final_sig_human"] = _spot_region_sig(png_fin, mod,
                                                 SPOT_HUMAN_BOX_REGION)
        s5["final_sig_ai"] = _spot_region_sig(png_fin, mod, SPOT_AI_BOX_REGION)
        s5["human_changed"] = bool(d_h.get("changed_px") is not None
                                   and d_h["changed_px"] >= SPOT_VERIFY_MIN_CHG)
        s5["ai_changed"] = bool(d_a.get("changed_px") is not None
                                and d_a["changed_px"] >= SPOT_VERIFY_MIN_CHG)
        out["spot_verify_ok"] = bool(s5["human_changed"] and s5["ai_changed"])
    out["steps"].append({"step": "S5", **s5})
    out["ok"] = bool(s1.get("click") and s2.get("png") and s3.get("click")
                     and s4.get("png") and s5.get("png"))
    rec.add("NAV", "spot_step_S5", s5, "EARLY_END_ANALYSIS.md:§11.1+QC211",
            note="★ QC211/S5：两处「位置」框(473,60,508,79)/(473,85,508,104) "
                 f"基线vs终帧 像素变化+哈希（≥{SPOT_VERIFY_MIN_CHG}px 记 changed）")
    rec.add("NAV", "spot_verify_ok", out["spot_verify_ok"], "script:_spot_run",
            note="★ QC210：S5 汇总判定；False=未证实（如实记，不硬造）")
    return out


# ★★ QC210 可插拔缝（burst）：**锚绑定 + 同名包装**——既有 `def _burst_battle`
#   与其唯一调用点（nav 循环内）**零改动**；off ⇒ 一字不差委托锚函数
#   （flag-off 等价）；on ⇒ 帧钟判据实现（见 `_burst_battle_qc210_impl`）。
_burst_battle_anchor = _burst_battle


def _burst_battle(hwnd: int, wall: float, rec: Recorder, mod) -> dict:
    """★ QC210 包装（同名可插拔缝；锚=紧上方 `_burst_battle_anchor`）。

    ★ `--spot-select` off（缺省）⇒ 直接委托锚函数：行为与改前**逐字节一致**
      （rec 行流同形同序同值）；on ⇒ `_burst_battle_qc210_impl`（帧钟判据）。
    """
    if not _QC210_SPOT.get("on"):
        return _burst_battle_anchor(hwnd, wall, rec, mod)
    return _burst_battle_qc210_impl(hwnd, wall, rec, mod, _QC210_SPOT.get("pid"))


def _burst_battle_qc210_impl(hwnd: int, wall: float, rec: Recorder, mod,
                             pid: int) -> dict:
    """★ QC210 burst：开战判据 = CurrentFrame(0x00A8ED84) **帧钟推进**（主）。

    ★ 依据（EARLY_END_ANALYSIS.md §11）：T35 战斗实际跑 16s 但
      tactical_colors=1 恒定 ⇒ 旧判据（红钮空 ∧ 色数≥600）失效。新判据：
      每轮 ~5 s 只读采样 CurrentFrame（~20 Hz；沿用 §10.8 `_rpm_*` 只读模式：
      S-4 之后开句柄、finally 关闭、零写入），**相邻读数相对首轮递增连续
      2 次** ⇒ in_battle（早停，不空烧窗口）。
    ★ `red_centers`/`tactical_colors` 保留为**辅助信号**逐轮照记（不参与判据）；
      RPM 不可用（句柄失败/零有效样本）⇒ 该轮回退旧判据并记 `fallback_used`
      （比死闸诚实）。超时与 INCOMPLETE 语义与锚版一致（≤6 轮、受 wall 硬
      约束、命中即停、`_g`/`_x` 留档、ok=False ⇒ 上层 INCOMPLETE 不 sys.exit）。
    """
    polls: list = []
    burst_ok = False
    handle = _rpm_open(pid)
    rpm_open_ok = bool(handle)
    try:
        for k in range(6):
            if time.monotonic() >= wall - 1.5:
                break
            png = WORKDIR / f"navsig_burst_{k:02d}_x.png"
            ok_cap, _wh = capture_frame(hwnd, png)
            centers = _red_button_centers(png, mod) if ok_cap else None
            colors = _tactical_color_count(png, mod) if ok_cap else -1
            fc = {"rpm_open_ok": rpm_open_ok, "n_samples": 0, "f_first": None,
                  "f_last": None, "read_err": 0, "advanced": False,
                  "fallback_used": False}
            if handle:
                t_end = time.monotonic() + min(
                    5.0, max(0.5, wall - 1.5 - time.monotonic()))
                f_first = None
                inc = 0
                while time.monotonic() < t_end:
                    f = _rpm_u32(handle, MEASURE_CURRENT_FRAME_VA)
                    if f is None:
                        fc["read_err"] += 1
                        _doze(0.05)
                        continue
                    if f_first is None:
                        f_first = f
                    fc["n_samples"] += 1
                    fc["f_last"] = f
                    if f > f_first:
                        inc += 1
                        if inc >= 2:
                            fc["advanced"] = True
                            break
                    else:
                        inc = 0
                fc["f_first"] = f_first
            if fc["n_samples"] == 0:
                # ★ RPM 不可用 ⇒ 旧判据兜底（如实记 fallback_used）
                fc["fallback_used"] = True
                hit = bool(ok_cap and centers == []
                           and colors >= TACTICAL_COLOR_FLOOR)
            else:
                hit = bool(ok_cap and fc["advanced"])
            if hit:
                hit_png = WORKDIR / f"navsig_burst_{k:02d}_g.png"
                hit_png.unlink(missing_ok=True)  # QC197b/D-122 同款防 WinError 183
                png.rename(hit_png)
                png = hit_png
                burst_ok = True
            polls.append({"k": k, "png": png.name, "cap_ok": ok_cap,
                          "red_centers": centers, "tactical_colors": colors,
                          "frame_clock": fc, "hit": hit})
            if hit or k == 5:
                break
            _doze(min(2.0, max(0.0, wall - 1.5 - time.monotonic())))
    finally:
        _rpm_close(handle)
    res = {"ok": burst_ok, "expect": "battle", "polls": polls,
           "burst_owned": burst_ok, "criterion": "qc210_frame_clock",
           "rpm_open_ok": rpm_open_ok}
    rec.add("NAV", "post_start_burst", res, "qc210:frame_clock",
            note="★ QC210：开战判据=CurrentFrame(0x00A8ED84) 推进（主）；"
                 "红钮/战术色=辅助；RPM 不可用回退旧判据（fallback_used）")
    return res
# <<< QC210-END section

# >>> QC151SG-BEGIN funcs（嵌套哨兵：删本块=还原锚 d6e52d3f…；三旗标缺省关 ⇒ 全部零调用零行）
# ===========================================================================
# §10.7c · QC151SG · 遭遇战设置屏「短游戏」开关取证+可控点击（★ 纯新增节）
# ===========================================================================
# ★★ 背景（T55d-h 定谳·写回件自证）：四趟全程 ShortGame=yes 规则下作战 ⇒
#   四屋零建筑被规则判负清洗、长战局无法成立（T50 窗口代=no 可对照）。
#   修复路线（Lead 已裁甲）=harness 在遭遇战设置屏把 ShortGame 点回 no。
#   ★ 设置屏从未被截图（既有 navsig 只覆盖菜单/影片/战局，坐标未知）⇒
#   两段式：T55i 纯取证（--sg-capture 单给）先行标定；T55j 凭标定坐标
#   （--sg-toggle-x/y）精确点击。
# ★★ 纪律（同 §10.5/§10.7b 房规；QC210 main-gate 缺省等价）：
#   - 截图复用既有 capture_frame（QC151FS 缝自适应 PrintWindow/桌面拷贝）；
#     帧名走既有 navsig_* 口径（设置屏位首次入档）。
#   - 点击复用既有 click_logical（800×600 游戏系；FS 下自动直通映射）。
#   - 延时只经既有 _doze（sleep 直调命中数不增，grep 可自查）。
#   - rec 一律 MEASURE 组各一行：pre / click / post（Recorder 逐行自带 ts）。
#   - 点击前置**双重断言**：①坐标范围 0<x<800 ∧ 0<y<600（800×600 游戏系）；
#     ②pre 帧过 _spot_centers_match（QC212 签名+正向判据；≤SG_GUARD_TRIES
#     轮自愈重试，防 T36/T38 一过性暗帧——spot S2/S4 点击后瞬态恰可能覆盖
#     本挂点时刻）。★ 断言任一不成立/半坐标/pre 截帧失败 ⇒ fail-closed 拒点
#     并如实记账（零盲点）；点击正确性另有双重终验：post 截图 + 写回 INI 的
#     ShortGame 值（后者既有 EVIDDIFF 差异件天然保回写、零新代码）。
_QC151SG = {"capture": False, "toggle": None}   # ★ 运行态开关（main 装载）

SG_PRE_PNG = "navsig_skirmish_set_pre.png"    # ★ 设置屏取证帧（点击前）
SG_POST_PNG = "navsig_skirmish_set_post.png"  # ★ 点击后设置屏帧
SG_CLICK_DOZE_S = 1.0                         # ★ 点击→post 抓帧渲染等待（_doze）
SG_GUARD_TRIES = 3                            # ★ pre 签名断言轮数（=SPOT_GUARD_TRIES_PRE）


def _sg_skirmish_run(hwnd: int, rec: Recorder, mod) -> dict:
    """★ QC151SG 主入口：设置屏取证（--sg-capture）+可控点击（--sg-toggle-x/y）。

    ★ 前置：nav_setup 后态签名已过（skirmish_setup 在屏）；nav_start 点击前
      执行（独立小阶段 `sg_skirmish`，自计时不侵 nav_start 的 30s 阶段帽）。
    ★ pre：抓 SG_PRE_PNG；签名断言不过 ⇒ ≤SG_GUARD_TRIES 轮重试（重试帧
      _r2/_r3 全留档，命中轮回改名 canonical——QC197b/D-122 防 WinError 183）。
    ★ click：范围断言（0<x<800 ∧ 0<y<600，800×600 游戏系）⇒ click_logical
      → _doze(SG_CLICK_DOZE_S) → post 抓帧。任一断言不成立 ⇒ 拒点（零盲点）。
    ★ 未给 toggle 坐标 = 纯取证模式（T55i）：抓 pre 后零点击返回。
    """
    out = {"armed": True, "capture": bool(_QC151SG["capture"]),
           "toggle_xy": (list(_QC151SG["toggle"])
                         if _QC151SG["toggle"] else None),
           "clicked": False, "pre_ok": False}
    # ---- ① pre 取证 + 签名断言（≤SG_GUARD_TRIES 轮自愈；帧全留档） ----
    pre_png = WORKDIR / SG_PRE_PNG
    attempts: list = []
    for _i in range(1, SG_GUARD_TRIES + 1):
        if _i > 1:
            _doze(1.0)
        cap_to = (pre_png if _i == 1
                  else WORKDIR / (SG_PRE_PNG[:-4] + f"_r{_i}.png"))
        ok_cap, wh = capture_frame(hwnd, cap_to)
        sig_ok, centers, sig_err = False, None, None
        if ok_cap:
            try:
                sig_ok, centers = _spot_centers_match(cap_to, mod)
            except Exception as _sg_e:
                sig_err = repr(_sg_e)[:160]
        attempts.append({"i": _i, "png": cap_to.name, "cap_ok": bool(ok_cap),
                         "wh": list(wh) if wh else None,
                         "sig_ok": bool(sig_ok), "red_centers": centers,
                         "sig_err": sig_err, "ts": now_iso()})
        if sig_ok:
            if _i > 1:
                pre_png.unlink(missing_ok=True)  # ★ QC197b/D-122 防 WinError 183
                cap_to.rename(pre_png)
                attempts[-1]["png"] = pre_png.name
            break
    out["pre_ok"] = bool(attempts and attempts[-1]["sig_ok"])
    out["pre_attempts"] = attempts
    pre_sha = None
    if out["pre_ok"]:
        try:
            pre_sha = sha256_file(pre_png)
        except Exception:
            pre_sha = None
    rec.add("MEASURE", "sg_skirmish_pre",
            {"ok": out["pre_ok"],
             "path": (str(pre_png) if out["pre_ok"] else None),
             "sha256": pre_sha, "attempts": attempts},
            "script:capture_frame",
            note="★ QC151SG：设置屏取证帧（命中轮=canonical 名；失败轮 _r2/_r3 "
                 "留档；签名断言=QC212 口径；行 ts=末轮抓帧时刻）")
    # ---- ② 点击（范围断言+pre 断言全过才点；任一失败 ⇒ fail-closed 拒点） ----
    xy = _QC151SG["toggle"]
    if xy is None:
        rec.add("MEASURE", "sg_skirmish_click",
                {"clicked": False, "reason": "toggle_not_given",
                 "ts": now_iso()},
                "argv:--sg-toggle-x/--sg-toggle-y",
                note="★ QC151SG：纯取证模式（T55i）——未给坐标 ⇒ 零点击零行为")
        out["mode"] = "capture_only"
        return out
    x, y = int(xy[0]), int(xy[1])
    range_ok = bool(0 < x < 800 and 0 < y < 600)   # ★ 范围断言（800×600 游戏系）
    out["toggle_range_ok"] = range_ok
    refuse = None
    if not out["pre_ok"]:
        refuse = "pre_signature_failed"
    elif not range_ok:
        refuse = "toggle_range_assert"
    if refuse is not None:
        rec.add("MEASURE", "sg_skirmish_click",
                {"clicked": False, "refused": refuse, "xy": [x, y],
                 "range_ok": range_ok, "ts": now_iso()},
                "script:_sg_skirmish_run",
                note="★ QC151SG：拒点（fail-closed 零盲点）——范围断言 "
                     "0<x<800 ∧ 0<y<600；pre 断言逐轮见 sg_skirmish_pre.attempts")
        out["mode"] = "refused"
        return out
    click_logical(hwnd, x, y)
    out["clicked"] = True
    _doze(SG_CLICK_DOZE_S)
    rec.add("MEASURE", "sg_skirmish_click",
            {"clicked": True, "xy": [x, y], "range_ok": True,
             "doze_s": SG_CLICK_DOZE_S, "ts": now_iso()},
            "script:click_logical",
            note="★ QC151SG：「短游戏」开关点击（800×600 游戏系；已过范围断言"
                 "+pre 签名断言；正确性终验=post 截图+写回 INI ShortGame 值）")
    # ---- ③ post 取证 ----
    post_png = WORKDIR / SG_POST_PNG
    ok_post, wh_post = capture_frame(hwnd, post_png)
    post_centers = None
    if ok_post:
        try:
            _ps, post_centers = _spot_centers_match(post_png, mod)
        except Exception:
            post_centers = None
    post_sha = None
    if ok_post:
        try:
            post_sha = sha256_file(post_png)
        except Exception:
            post_sha = None
    out["post_ok"] = bool(ok_post)
    rec.add("MEASURE", "sg_skirmish_post",
            {"ok": bool(ok_post), "path": str(post_png),
             "wh": list(wh_post) if wh_post else None, "sha256": post_sha,
             "red_centers": post_centers, "ts": now_iso()},
            "script:capture_frame",
            note="★ QC151SG：点击后设置屏帧（终验①；终验②=写回 INI 的 "
                 "ShortGame 值——既有 EVIDDIFF 差异件天然保回写，零新代码）")
    return out
# <<< QC151SG-END funcs


# ===========================================================================
# §10.8 · QC202/C1 进图态性能测量（★ 纯新增节；`MEASURE_DESIGN_v1.md`）
# ===========================================================================
# ★★ 授权状态（★ 如实声明，§5.3）：本模块 docstring 的 QC141 口径
#   「本单不含内存读」（`QC141:18`）**不覆盖**本节 —— 本节是
#   `MEASURE_DESIGN_v1.md:§3.1` 选定的 **RPM 只读轮询**扩项（§5.3
#   「授权扩项」）：**只读、非注入、S-4 之后开句柄、finally 关闭**，
#   须 QC20x 卡面显式扩项签署后方可真机运行 `--measure>0`。
#   ★ 缺省 `--measure=0` ⇒ 本节**零执行**（零 rec 行、零落盘），
#     门禁行为语义与 T24（锚 `e4f87b96`）完全一致（§2.1）。
# ★★ 观测扰动禁令（§3.1-②/§4.1）：测量窗内**零键鼠、零 PrintWindow**
#   （`capture_frame` 属观测扰动，测量窗内禁用）；本节**不向目标进程
#   注入任何模块/线程** ⇒ S-4 模块面零变化（§5.2）。
# ★★ 地址记法纪律（D-79）：VA 与 file_off **成对写出**
#   （file_off = VA − 0x400000）。
MEASURE_CURRENT_FRAME_VA = 0x00A8ED84         # ★ CurrentFrame（逻辑帧计数器 u32）
MEASURE_CURRENT_FRAME_FILE_OFF = 0x0068ED84   # ★ = VA − 0x400000（D-79）
# ★ 计数器副读（§3.2；bench `ARR_*+0x10` 口径，LIVE_M0 两源互证 [实证]）
MEASURE_UNITS_VA = 0x008B4118        # units    / file_off 0x004B4118
MEASURE_INFANTRY_VA = 0x00A83DF8     # infantry / file_off 0x00683DF8
MEASURE_AIRCRAFT_VA = 0x00A8E3A0     # aircraft / file_off 0x0068E3A0
MEASURE_G_VA = 0x008A03A0            # G（Items=0x008A0394；形状自检 D-3：Items!=0 ∧ Count≤100000）
MEASURE_G_ITEMS_VA = 0x008A0394
MEASURE_B_VA = 0x00A8EB50            # B（Items=0x00A8EB44）
MEASURE_B_ITEMS_VA = 0x00A8EB44
MEASURE_TECHNO_VA = 0x00A8EC88       # Techno   / file_off 0x0068EC88
# ★ 协议常量（§3.2/§3.3/§5.1，v1 固定；帽值一字不改）
MEASURE_HZ = 500                     # [设计假设] 追拍不稳 ⇒ scratch 回退 200 Hz（§3.2）
MEASURE_WINDOWS = 3                  # 3 窗 × 25 s 连续（§3.3）
MEASURE_WINDOW_S = 25.0              # 单窗 25 < 30−2（STAGE_TIMEOUT_S 帽值不改）
MEASURE_SETTLE_S = 4.0               # 窗 0 前置 settle（§3.3）
MEASURE_GATE_FPS15_MIN = 3.0         # 窗前在局闸：1.5 s 内推进 ≥3 fps（§3.2）
MEASURE_GATE_SPAN_S = 1.5
MEASURE_W1_UNITS0_MIN = 150          # W1 裁决门：首窗 units0 ≥150（§4.3）
MEASURE_TICK_MISS_FACTOR = 1.5       # tick_miss：间隔 >1.5×p50（bench 同口径）


def _rpm_open(pid: int):
    """★ RPM 只读句柄：`OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ)`。

    ★ 权限位段同 bench `open_proc`（§3.2）；argtypes/restype 规范与本文件
      既有风格一致（QC183/QC184：HANDLE 必须 `restype=wt.HANDLE` 防 64 位截断）。
    ★ **只读**：绝不 WriteProcessMemory/VirtualProtectEx/注入（模块 docstring 禁止面）。
    """
    k32 = ctypes.windll.kernel32
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    _PQLI = 0x1000        # PROCESS_QUERY_LIMITED_INFORMATION
    _VM_READ = 0x0010     # PROCESS_VM_READ
    return k32.OpenProcess(_PQLI | _VM_READ, False, pid)


def _rpm_close(handle) -> None:
    """★ 关只读句柄（§3.2：finally 关闭）。"""
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)


def _rpm_u32(handle, va: int):
    """★ `ReadProcessMemory` 读 u32；失败 ⇒ `None`（**不抛**，采样器内部收口）。

    ★ `lpNumberOfBytesRead` 必须核 4 字节全读（半读 ⇒ 视为失败，§5.4 读数畸形）。
    """
    k32 = ctypes.windll.kernel32
    k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                      ctypes.c_void_p, ctypes.c_size_t,
                                      ctypes.POINTER(ctypes.c_size_t)]
    k32.ReadProcessMemory.restype = wt.BOOL
    buf = ctypes.c_uint32(0)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(handle, ctypes.c_void_p(va), ctypes.byref(buf),
                               ctypes.sizeof(buf), ctypes.byref(got))
    if not ok or got.value != ctypes.sizeof(buf):
        return None
    return buf.value


class _PMC(ctypes.Structure):
    """★ `PROCESS_MEMORY_COUNTERS`（工作集/提交内存；服务 M-6 静默死亡归因）。"""
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


def _rpm_mem_kb(handle):
    """★ 工作集/提交内存（KB；`GetProcessMemoryInfo`）；失败 ⇒ `(None, None)`。

    ★ 不可测写 `null` 不写 0（Recorder 纪律）。
    """
    try:
        psapi = ctypes.windll.psapi
        psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE,
                                               ctypes.POINTER(_PMC), wt.DWORD]
        psapi.GetProcessMemoryInfo.restype = wt.BOOL
        pmc = _PMC()
        pmc.cb = ctypes.sizeof(_PMC)
        if psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize // 1024, pmc.PagefileUsage // 1024
    except Exception:
        return None, None
    return None, None


def _rpm_counters(handle) -> dict:
    """★ 1 Hz 计数器副读（§3.2）：units/infantry/aircraft + G/B/Techno
    （Items 形状自检 D-3：`Items != 0 ∧ Count ≤ 100000`——Items 是**指针**，
    ★ 禁用 `Count−Items==0xC`（把指针当计数，恒假；§3.6-D3））+ 工作集/提交内存。

    ★ 任一项读失败 ⇒ 该项 `null`（不写 0）；**零写入**目标进程。
    """
    units = _rpm_u32(handle, MEASURE_UNITS_VA)
    infantry = _rpm_u32(handle, MEASURE_INFANTRY_VA)
    aircraft = _rpm_u32(handle, MEASURE_AIRCRAFT_VA)
    g = _rpm_u32(handle, MEASURE_G_VA)
    g_items = _rpm_u32(handle, MEASURE_G_ITEMS_VA)
    b = _rpm_u32(handle, MEASURE_B_VA)
    b_items = _rpm_u32(handle, MEASURE_B_ITEMS_VA)
    techno = _rpm_u32(handle, MEASURE_TECHNO_VA)
    ws_kb, pf_kb = _rpm_mem_kb(handle)
    return {"units": units, "infantry": infantry, "aircraft": aircraft,
            "g": g, "b": b, "techno": techno, "g_items": g_items,
            "b_items": b_items, "ws_kb": ws_kb, "pf_kb": pf_kb,
            "shape": {"g_valid": (None if (g is None or g_items is None)
                                  else (g_items != 0 and g <= 100000)),
                      "b_valid": (None if (b is None or b_items is None)
                                  else (b_items != 0 and b <= 100000))}}


def _measure_poll_span(handle, span_s: float, hz: int):
    """★ 定拍只读轮询一段墙钟：`CurrentFrame` u32 采样 + 1 Hz 计数器副读。

    ★ 同构 bench `poll_frames`（§3.2）；主线程内联 `time.perf_counter` 定拍；
      ★ 节拍延时**只**经既有 `_doze`（QC197 纪律：`time.sleep` 既有调用一字不动）。
    ★ 实际到拍节奏照实留痕（samples 的 t = `time.perf_counter()` 浮点；
      stats 的 `hz_effective` 折算披露；§3.2 量化照实披露）。
    ★ RPM 读失败**不抛**：退避 `_doze(0.001)` 继续守窗，失败计数随 err 返回。
    ★ 返回 `(t0, samples, counters, err)`；samples=`[(perf_counter, f), ...]`。
    """
    samples: list = []
    counters: list = []
    errs = 0
    t0 = time.perf_counter()
    t_end = t0 + span_s
    next_ctr = t0 - 1.0        # ★ 首轮即做一次计数器副读（t_rel≈0，§3.2 schema）
    i = 0
    while True:
        t_now = time.perf_counter()
        if t_now >= t_end:
            break
        f = _rpm_u32(handle, MEASURE_CURRENT_FRAME_VA)
        if f is None:
            errs += 1
            _doze(0.001)       # ★ 失败退避：仍守窗长，不空转烧核
        else:
            samples.append((t_now, f))
        if t_now >= next_ctr:
            row = _rpm_counters(handle)
            row["t_rel"] = round(t_now - t0, 6)
            counters.append(row)
            next_ctr = t_now + 1.0
        # ★ 定拍：离下拍有余量才睡；睡过头则顺延（节奏照实留痕，不追读补样）
        i += 1
        t_next = t0 + i / hz
        ahead = t_next - time.perf_counter()
        while ahead > 0.0025:
            _doze(0.002)
            ahead = t_next - time.perf_counter()
    err = (f"ReadProcessMemory 失败 {errs} 次（有效样本 {len(samples)}）"
           if errs else None)
    return t0, samples, counters, err
# >>> QC213-BEGIN probe（嵌套哨兵：删本块=还原 QC212 锚 bf4f32fe…）
# ===========================================================================
# §10.8b · QC213 · per-house 运行期探针（★ 纯新增只读节；随 --measure 窗激活）
# ===========================================================================
# ★★ 授权与门控（照 QC210-212 flag-off 房规）：探针**不新增 CLI 开关**，随既有
#   `--measure`（缺省 0）且 nav 全绿时随窗激活（main-arm 块）；缺省 off ⇒ 零执行、
#   零 rec 行、零行为。RPM 只沿用 §10.8 既有只读模式（句柄=measure 句柄，S-4 后
#   开、finally 关；本节零写入、零注入）。
# ★ 枚举读法（分析员规格；VA/file_off 成对，D-79）：
#   Items=rd32(0xA8022C / file_off 0x68022C)；Count=rd32(0xA80238 / 0x680238)；
#   哨兵 items==0 或 n>64 ⇒ probe_error=bad_vector（预期 n=4=两槽+Neutral+Special；
#   n≥14 = FFA 块军模型对象级实锤，本身即关键读数）。
# ★ 人类 house 三重识别：主=Items[i]==rd32(0xA83D4C / 0x683D4C)（引擎 PlayerPtr）；
#   辅=+0x1EC!=0；对照=id30==0。AI=id30==8 且 ≠PlayerPtr。
# ★ 采样：锚点=CurrentFrame u32@0xA8ED84（既有读法）；三档闩锁 frame≥300/600/1800
#   各一次（去重）；帧钟冻结≥2s 补 final 快照后停；piggyback 既有 500Hz measure
#   循环（经 `_rpm_u32` 同名包装顺路驱动，见块尾；每 house ~20 dword 开销可忽略）。
# ★ readings 键：p{帧号 6 位零填}_h{i}_{字段}（h{i} 按 Items 序）+ meta_count/
#   meta_playeridx + 预注册布尔 q213_allies_us_fr/br/ru（随快照落，组=QC213）。
_QC213_PROBE = {
    "on": False, "done": False, "err": None, "errs": 0,
    "latched": {}, "latched_n": 0, "frozen_done": False,
    "last_f": None, "last_t": None, "snapshots": [],
    "latch_frames": None,              # ★ QC151P3：阶梯锁存帧集（None ⇒ 锚 QC213_LATCH_FRAMES）
}
QC213_HOUSE_ITEMS_VA = 0x00A8022C   # HouseClass::Array Items（file_off 0x0068022C）
QC213_HOUSE_COUNT_VA = 0x00A80238   # Count（file_off 0x00680238）
QC213_PLAYERPTR_VA = 0x00A83D4C     # PlayerPtr（file_off 0x00683D4C）
QC213_LATCH_FRAMES = (300, 600, 1800)
QC213_FREEZE_S = 2.0                # 帧钟冻结 ≥2s ⇒ 补 final 快照后停
QC213_ID30_FR = 2                   # 预注册同盟位号：FR
QC213_ID30_BR = 4                   # BR
QC213_ID30_RU = 8                   # RU（战争成立性：同盟位必须为 0）
QC213_ERR_CAP = 3                   # probe_error 行上限（防坏向量刷屏；达帽即收口）
QC213_SCORE_OFF = 0x15FF4           # 可选便宜项：计分簿区偏移
QC213_SCORE_LEN = 0x20B             # 原始 dump 长度（摘要入 rec，blob 不入）
_QC213_FIELDS = (                   # (键, 种类, 偏移)；u8=4字节对齐小端取字节
    ("id30", "u32", 0x30), ("htc34", "u32", 0x34),
    ("isHuman1EC", "u8", 0x1EC), ("loser1ED", "u8", 0x1ED),
    ("def1F5", "u8", 0x1F5),
    ("wf1F6", "u8", 0x1F6), ("wf1F7", "u8", 0x1F7), ("wf1F8", "u8", 0x1F8),
    ("x2F0", "u32", 0x2F0),
    ("c5560", "u32", 0x5560), ("c5574", "u32", 0x5574),
    ("c5588", "u32", 0x5588), ("c559C", "u32", 0x559C),
    ("m5788", "u32", 0x5788), ("m578C", "u32", 0x578C),
    ("m5798", "u32", 0x5798), ("m579C", "u32", 0x579C), ("m57A0", "u32", 0x57A0),
    ("spot6B", "u8", 0x6B), ("gate6D5", "u8", 0x6D5), ("team6CC", "u32", 0x6CC),
)


def _qc213_u8(handle, base_va: int, off: int):
    """★ QC213：4 字节对齐小端取单字节——对齐下取 dword，按 (off&3)*8 移位。"""
    v = _rpm_u32_qc213_base(handle, base_va + (off & ~3))
    return None if v is None else ((v >> ((off & 3) * 8)) & 0xFF)


def _qc213_digest(handle, base_va: int, off: int, n: int):
    """★ QC213 可选便宜项：+0x15FF4 起 n=0x20B 原始 dump（计分簿区）→ 摘要。

    ★ 4 字节对齐 dword 逐读拼包（小端）后截 n 字节；**sha16+首 8 字节 hex 入 rec**，
      原始 blob 不入 rec（Recorder 纪律：原始样列禁入）。读失败 ⇒ None。
    """
    aligned = off & ~3
    skip = off - aligned
    total = skip + n
    buf = bytearray()
    for k in range((total + 3) // 4):
        v = _rpm_u32_qc213_base(handle, base_va + aligned + 4 * k)
        if v is None:
            return None
        buf += v.to_bytes(4, "little")
    raw = bytes(buf[skip:skip + n])
    return {"sha16": hashlib.sha256(raw).hexdigest()[:16],
            "head8": raw[:8].hex()}


def _qc213_err(rec, frame, kind: str) -> None:
    """★ QC213：probe_error 只记不抛；同段错误达帽（QC213_ERR_CAP）即收口。"""
    if rec is not None and _QC213_PROBE["errs"] < QC213_ERR_CAP:
        _QC213_PROBE["errs"] += 1
        rec.add("QC213", "qc213_probe_error", {"kind": kind, "frame": frame},
                "script:_qc213_snapshot",
                note="★ QC213：哨兵 items==0/n>64=bad_vector、读失败=read_fail"
                     "（只记不抛；达帽收口）")
    if _QC213_PROBE["errs"] >= QC213_ERR_CAP:
        _QC213_PROBE["done"] = True


def _qc213_snapshot(handle, frame: int, kind: str) -> None:
    """★ QC213 单次快照：House 枚举 + 每 house 字段表（全只读；失败只记不抛）。"""
    rec = ACTIVE_REC[0]
    tag = f"p{frame:06d}"
    if rec is None:
        return
    items = _rpm_u32_qc213_base(handle, QC213_HOUSE_ITEMS_VA)
    count = _rpm_u32_qc213_base(handle, QC213_HOUSE_COUNT_VA)
    if items is None or count is None:
        _qc213_err(rec, frame, "read_fail")
        return
    if items == 0 or count > 64:
        _qc213_err(rec, frame, "bad_vector")
        return
    player = _rpm_u32_qc213_base(handle, QC213_PLAYERPTR_VA)
    pidx = None
    hus = None
    rec.add("QC213", f"{tag}_meta_count", count, "rpm:rd32(0xA80238)",
            note=f"★ QC213 快照 kind={kind}；预期 n=4（两槽+Neutral+Special）；"
                 f"n≥14=FFA 块军模型对象级实锤")
    for i in range(count):
        hp = _rpm_u32_qc213_base(handle, items + 4 * i)
        if hp is None:
            for k, _kd, _off in _QC213_FIELDS:
                rec.add("QC213", f"{tag}_h{i}_{k}", None,
                        "rpm:Items[i] 读失败",
                        note="★ QC213：Items[i] 指针读失败 ⇒ 该 house 全字段 null")
            if kind == "frozen_final":
                rec.add("QC213", f"{tag}_h{i}_c5550", None,
                        "rpm:Items[i] 读失败",
                        note="★ QC151P3：Items[i] 读失败 ⇒ c5550 null（frozen_final 集）")
            continue
        if player is not None and hp == player and pidx is None:
            pidx = i
        row = {}
        for k, kd, off in _QC213_FIELDS:
            v = (_qc213_u8(handle, hp, off) if kd == "u8"
                 else _rpm_u32_qc213_base(handle, hp + off))
            row[k] = v
            rec.add("QC213", f"{tag}_h{i}_{k}", v,
                    f"rpm:HouseClass+0x{off:X} {kd}",
                    note="★ QC213 per-house 探针（只读）")
        dg = _qc213_digest(handle, hp, QC213_SCORE_OFF, QC213_SCORE_LEN)
        rec.add("QC213", f"{tag}_h{i}_d15FF4", dg,
                "rpm:HouseClass+0x15FF4（0x20B 原始→sha16+head8）",
                note="★ QC213 可选便宜项：计分簿区摘要（blob 不入 rec）")
        if kind == "frozen_final":
            # ★★ QC151P3：frozen_final 探针集扩展——+0x5550 链表计数读
            #   （照 c5574 既有模式：list 对象 +0x10 的 Count 直读 u32，即
            #   house+0x5550+0x10；键 c5550 仅入 frozen_final 集）。
            #   ★ 用途：裁决「败北判定是否数步兵」勘误候选（正典=四链表和为零
            #   才败北；T55d 实测 h1 c5588=90>0 在场时 def1F5 已置位）。
            #   ★ c5550 与同快照 c5560 同址（0x5560）⇒ 两路实现互核自检；
            #   与 def1F5/c5588 同行同帧可比 ⇒ 冻结态败北表自洽、离线可裁决。
            v5550 = _rpm_u32_qc213_base(handle, hp + QC151P3_L5550_COUNT_OFF)
            rec.add("QC213", f"{tag}_h{i}_c5550", v5550,
                    f"rpm:HouseClass+0x{QC151P3_L5550_COUNT_OFF:X} u32"
                    "（list@0x5550 Count=list+0x10）",
                    note="★ QC151P3：frozen_final 集扩展（c5574 同模式；"
                         "与 c5560 同址互核）")
        if player is not None and hp == player:
            hus = row
    rec.add("QC213", f"{tag}_meta_playeridx", pidx,
            "rpm:Items[i]==PlayerPtr(0xA83D4C)",
            note="★ QC213：人类 house 三重识别之主判（辅=+0x1EC!=0，对照=id30==0；"
                 "AI=id30==8 且 ≠PlayerPtr）")
    m5788_hus = None if hus is None else hus.get("m5788")
    m579C_hus = None if hus is None else hus.get("m579C")
    for nm, bit in (("fr", QC213_ID30_FR), ("br", QC213_ID30_BR)):
        v = (None if (m579C_hus is None or m5788_hus is None)
             else bool(((m579C_hus >> bit) & 1) and ((m5788_hus >> bit) & 1)))
        rec.add("QC213", f"{tag}_q213_allies_us_{nm}", v,
                "qc213:((m579C_hus>>id30)&1)&&((m5788_hus>>id30)&1)",
                note=f"★ QC213 预注册布尔（id30_{nm}={bit}；两量分读区分"
                     f"「解析成功未应用」vs「解析失败」）")
    v_ru = (None if m5788_hus is None
            else bool(((m5788_hus >> QC213_ID30_RU) & 1) == 0))
    rec.add("QC213", f"{tag}_q213_allies_us_ru", v_ru,
            "qc213:((m5788_hus>>id30_ru)&1)==0",
            note=f"★ QC213 预注册布尔（id30_ru={QC213_ID30_RU}；战争成立性："
                 f"与 RU 的同盟位必须为 0）")
    _QC213_PROBE["snapshots"].append({"frame": frame, "kind": kind,
                                      "count": count, "playeridx": pidx})


def _qc213_tick(handle, frame: int) -> None:
    """★ QC213：measure 循环每帧读数驱动的闩锁/冻结看门（**绝不抛**）。"""
    st = _QC213_PROBE
    if not st["on"] or st["done"]:
        return
    try:
        now = time.monotonic()
        lf = st["last_f"]
        if lf is None or frame != lf:
            st["last_f"], st["last_t"] = frame, now
        elif ((now - st["last_t"]) >= QC213_FREEZE_S
              and not st["frozen_done"]):
            st["frozen_done"] = True
            st["done"] = True
            if _QC151P3_STATE["on"]:         # ★ QC151P3：缺省 off ⇒ 零调用零行
                _qc151p3_frozen_dump(frame)  # ★ dump 先于快照（最贴冻结点；失败不抛不挡快照）
            _qc213_snapshot(handle, frame, "frozen_final")
            return
        latches = st["latch_frames"] or QC213_LATCH_FRAMES   # ★ QC151P3：阶梯锁存（None ⇒ 锚 300/600/1800）
        for th in latches:
            if frame >= th and str(th) not in st["latched"]:
                st["latched"][str(th)] = True
                st["latched_n"] += 1
                _qc213_snapshot(handle, frame, f"latch{th}")
                break
        if (st["latched_n"] >= len(latches)
                and st["frozen_done"]):
            st["done"] = True
    except Exception as e:                     # ★ 探针内部异常收口（不抛）
        st["done"] = True
        st["err"] = repr(e)
        rec = ACTIVE_REC[0]
        if rec is not None and st["errs"] < QC213_ERR_CAP:
            st["errs"] += 1
            rec.add("QC213", "qc213_probe_error",
                    {"kind": "exception", "repr": repr(e)[:200]},
                    "script:_qc213_tick",
                    note="★ QC213：探针内部异常收口（只记不抛）")


_rpm_u32_qc213_base = _rpm_u32


def _rpm_u32(handle, va: int):
    """★ QC213 包装（同名可插拔缝；锚=`_rpm_u32_qc213_base`）：CurrentFrame 读数
    顺路驱动 per-house 探针闩锁/冻结看门（piggyback 既有 500Hz measure 循环）。

    ★ 探针 off（缺省）⇒ 逐字直通锚函数（同对象调用，异常语义同锚，零行为差异）；
      on ⇒ 每次帧钟读数做闩锁阈值比较（ns 级），命中才做一次性快照
      （~20 dword/house）；基础读若违反「不抛」契约 ⇒ 探针失败只记
      probe_error 不抛（返回 None，measure 循环按既有读失败语义处理）。
    """
    if not _QC213_PROBE["on"]:
        return _rpm_u32_qc213_base(handle, va)
    try:
        v = _rpm_u32_qc213_base(handle, va)
    except Exception as e:                     # ★ 探针失败不抛（契约外异常收口）
        st = _QC213_PROBE
        st["done"] = True
        st["err"] = repr(e)
        _qc213_err(ACTIVE_REC[0], None, "exception")
        return None
    if (not _QC213_PROBE["done"]
            and v is not None and va == MEASURE_CURRENT_FRAME_VA):
        _qc213_tick(handle, v)
    return v
# <<< QC213-END probe
# >>> QC213P2-BEGIN probe（嵌套哨兵：删本块=还原锚 37c1d435…；缺省 off=零执行零行）
# ===========================================================================
# §10.8d · QC213P2 · 败北触发链定谳探针（★ 纯新增只读节；随 --measure 窗激活）
# ===========================================================================
# ★★ 判读依据：spawnfix9_freeze_20261019\WIPE_TRIGGER_ANALYSIS.md §5.1 探针表
#   与「附：关键地址速查」；VA→file_off 一律 VA−0x400000（速查表核对项）：
#     RulesClass            0x008871E0 / file_off 0x004871E0
#     RulesClass+0x8E8      0x008872C8 / 0x004872C8（速查表显式行）
#     ShortGame 全局        0x00A8B262 / 0x0068B262
#     SessionClass          0x00A8B230 / 0x0068B230
#     SessionClass+0x14B6   0x00A8C6E6 / 0x0068C6E6
#     HouseClass Items      0x00A8022C / 0x0068022C；Count 0x00A80238 / 0x00680238
#     CurrentFrame          0x00A8ED84 / 0x0068ED84（既有 MEASURE_CURRENT_FRAME_VA）
# ★ 探针：
#   P1 RulesClass+0x8E8 → [eax+8]（Arr8E8[1]）→ [+0xDF8]（指数/ID）：逐级解引、
#      逐级落 rec；再按引擎 0x49FAE0 同款边界（idx < [list+0x8]）读该指数在每屋
#      list@H+0x5550（步兵链）上的计数。预测：Arr8E8[1]==NULL（或该计数=0）。
#   P2 每屋 [H+0x34]（HouseTypeClass*）→ +0x1A6 字节（观察者/非参战门）。
#      预测 h0/h1=0、h2/h3=1。
#   P3 0x00A8B262（ShortGame 全局）与 [SessionClass+0x14B6] 对读。预测恒等（=0）。
#   P5 SessionClass byte[1] & 0x08（0x4FC179 清洗循环前置）。预测 =0x08 置位。
#   P4 逐帧阶梯（QC213P2_LADDER_SRC 常量可配）：f10 早闩 + f250-f450 步长 1；
#      超 QC213P2_LADDER_CAP(64) 自动截断并落 note；每帧记每屋
#      x2F0/c5574/c5588/def1F5（另附 id30/isHuman1EC/htc34/ht1A6/P1 计数）。
# ★★ 与 QC213 的关系：本探针为**独立闩锁**（不覆写 _QC213_PROBE["latch_frames"]）；
#    QC213 原三点闩锁（300/600/1800）保留作交叉复核。包装器链：本包装 →
#    QC213 包装 → 锚 _rpm_u32；只读、零写入、零注入、零新增 sleep。
_QC213P2_PROBE = {
    "on": False, "done": False, "err": None, "errs": 0,
    "latched": {}, "latched_n": 0, "frozen_done": False,
    "last_f": None, "last_t": None, "snapshots": [],
    "first_frame": None, "last_frame": None, "early_done": False,
}
QC213P2_RULES_VA = 0x008871E0            # RulesClass 指针槽 / file_off 0x004871E0
QC213P2_RULES_ARR8E8_OFF = 0x8E8         # 0x008872C8（速查表）
QC213P2_RULES_ELEM1_OFF = 0x8            # [Arr8E8+8] = Arr8E8[1]
QC213P2_HT_IDX_OFF = 0xDF8               # Arr8E8[1]+0xDF8 = 指数/ID
QC213P2_SHORTGAME_VA = 0x00A8B262        # ShortGame 全局 / file_off 0x0068B262
QC213P2_SESSION_VA = 0x00A8B230          # SessionClass / file_off 0x0068B230
QC213P2_SESSION_SHORTGAME_OFF = 0x14B6   # 0x00A8C6E6
QC213P2_SESSION_CLEAN_MASK = 0x08        # byte[1]&0x08（0x4FC16C）
QC213P2_HOUSE_ITEMS_VA = 0x00A8022C     # Items / file_off 0x0068022C
QC213P2_HOUSE_COUNT_VA = 0x00A80238     # Count / file_off 0x00680238
QC213P2_L5550_OFF = 0x5550               # 步兵链 list 对象基址（+0x4 Array/+0x8 上限/+0x10 Count）
QC213P2_HT_IS_OBS_OFF = 0x1A6            # HouseTypeClass+0x1A6（0x4F8EAF）
QC213P2_ERR_CAP = 3                      # probe_error 行上限（达帽收口）
QC213P2_FREEZE_S = 2.0                   # 帧钟冻结 ≥2s ⇒ 补 frozen_final 后停
QC213P2_LADDER_CAP = 64                  # 阶梯帧上限（>64 截断并记 note）
QC213P2_LADDER_SRC = (10,) + tuple(range(250, 451))   # ★ 可配阶梯源：f10 + f250-f450 步 1


def _qc213p2_ladder_effective(src):
    """★ QC213P2：阶梯去重升序 + 上限截断；返回 (有效阶梯, 丢弃数)。"""
    vals = sorted({int(v) for v in src if int(v) > 0})
    if len(vals) > QC213P2_LADDER_CAP:
        return tuple(vals[:QC213P2_LADDER_CAP]), len(vals) - QC213P2_LADDER_CAP
    return tuple(vals), 0


QC213P2_LADDER, QC213P2_LADDER_DROPPED = _qc213p2_ladder_effective(QC213P2_LADDER_SRC)
QC213P2_LADDER_SET = frozenset(QC213P2_LADDER)
QC213P2_LADDER_NOTE = (
    f"ladder={len(QC213P2_LADDER)} 帧"
    f"（f{QC213P2_LADDER[0]}..f{QC213P2_LADDER[-1]}）"
    f"；cap={QC213P2_LADDER_CAP}；丢弃 {QC213P2_LADDER_DROPPED} 帧"
    if QC213P2_LADDER else "ladder=空（源被过滤）")
_QC213P2_HOUSE_FIELDS = (                # (键, 种类, 偏移)；u8=4 字节对齐小端取字节
    ("x2F0", "u32", 0x2F0), ("c5574", "u32", 0x5574),
    ("c5588", "u32", 0x5588), ("def1F5", "u8", 0x1F5),
    ("id30", "u32", 0x30), ("isHuman1EC", "u8", 0x1EC),
    ("htc34", "u32", 0x34),
)


def _qc213p2_u8(handle, base_va: int, off: int):
    """★ QC213P2：4 字节对齐小端取单字节（同 QC213 `_qc213_u8` 口径）。"""
    v = _rpm_u32_qc213p2_base(handle, base_va + (off & ~3))
    return None if v is None else ((v >> ((off & 3) * 8)) & 0xFF)


def _qc213p2_err(rec, frame, kind: str) -> None:
    """★ QC213P2：probe_error 只记不抛；达帽（QC213P2_ERR_CAP）即收口。"""
    if rec is not None and _QC213P2_PROBE["errs"] < QC213P2_ERR_CAP:
        _QC213P2_PROBE["errs"] += 1
        rec.add("QC213P2", "qc213p2_probe_error",
                {"kind": kind, "frame": frame}, "script:_qc213p2_snapshot",
                note="★ QC213P2：哨兵 items==0/n>64=bad_vector、读失败=read_fail"
                     "（只记不抛；达帽收口）")
    if _QC213P2_PROBE["errs"] >= QC213P2_ERR_CAP:
        _QC213P2_PROBE["done"] = True


def _qc213p2_snapshot(handle, frame: int, kind: str) -> None:
    """★ QC213P2 单次快照：P1/P3/P5 全局 + 每屋 P2/P4 字段（只读；失败只记不抛）。"""
    rec = ACTIVE_REC[0]
    if rec is None:
        return
    tag = f"p{frame:06d}_qc213p2"
    rec.add("QC213P2", f"{tag}_kind", kind, "script:_qc213p2_tick",
            note="★ QC213P2 快照种类：early=首拍（h1 开局零出生签名）/"
                 "latch<帧>/frozen_final")
    # ---- P1：RulesClass+0x8E8 → Arr8E8[1] → +0xDF8（逐级解引、逐级落 rec）----
    rules = _rpm_u32_qc213p2_base(handle, QC213P2_RULES_VA)
    arr = (None if (rules is None or rules == 0)
           else _rpm_u32_qc213p2_base(handle, rules + QC213P2_RULES_ARR8E8_OFF))
    elem1 = (None if (arr is None or arr == 0)
             else _rpm_u32_qc213p2_base(handle, arr + QC213P2_RULES_ELEM1_OFF))
    idx = (None if (elem1 is None or elem1 == 0)
           else _rpm_u32_qc213p2_base(handle, elem1 + QC213P2_HT_IDX_OFF))
    rec.add("QC213P2", f"{tag}_p1_rules", rules, "rpm:rd32(0x008871E0)",
            note="★ P1 解引链第 1 级：RulesClass 指针（0x4F8F4C）")
    rec.add("QC213P2", f"{tag}_p1_arr8e8", arr,
            "rpm:rd32(RulesClass+0x8E8 / 0x008872C8)",
            note="★ P1 解引链第 2 级：Arr8E8 数组基（0x4F8F54）")
    rec.add("QC213P2", f"{tag}_p1_elem1", elem1,
            "rpm:rd32(Arr8E8+0x8) = Arr8E8[1]",
            note="★ P1 解引链第 3 级：Arr8E8[1]（0x4F8F5A）")
    rec.add("QC213P2", f"{tag}_p1_elem1_null",
            None if elem1 is None else (elem1 == 0), "script:(Arr8E8[1]==0)",
            note="★ P1 预测：True（NULL）或下项计数=0；None=读失败（不可测）")
    rec.add("QC213P2", f"{tag}_p1_idx_df8", idx,
            "rpm:rd32(Arr8E8[1]+0xDF8)",
            note="★ P1 解引链第 4 级：指数/ID（0x4F8F61）")
    # ---- P3：ShortGame 全局 vs SessionClass+0x14B6 ----
    sg_glob = _qc213p2_u8(handle, QC213P2_SHORTGAME_VA & ~3,
                          QC213P2_SHORTGAME_VA & 3)
    sess = _rpm_u32_qc213p2_base(handle, QC213P2_SESSION_VA)
    sg_sess = (None if (sess is None or sess == 0)
               else _qc213p2_u8(handle, sess, QC213P2_SESSION_SHORTGAME_OFF))
    rec.add("QC213P2", f"{tag}_p3_shortgame_glob", sg_glob,
            "rpm:byte@0x00A8B262", note="★ P3 全局 ShortGame 位（0x4F8EBD）")
    rec.add("QC213P2", f"{tag}_p3_shortgame_sess", sg_sess,
            "rpm:byte@[SessionClass+0x14B6]",
            note="★ P3 会话侧 ShortGame（0x52D1F5 拷贝源）")
    rec.add("QC213P2", f"{tag}_p3_equal",
            (None if (sg_glob is None or sg_sess is None)
             else (sg_glob == sg_sess)),
            "script:(0x00A8B262 == SessionClass+0x14B6)",
            note="★ P3 预测：True（ShortGame=no ⇒ 双 0）")
    # ---- P5：SessionClass byte[1] & 0x08 ----
    sess_dw = (None if (sess is None or sess == 0)
               else _rpm_u32_qc213p2_base(handle, sess))
    b1 = None if sess_dw is None else ((sess_dw >> 8) & 0xFF)
    rec.add("QC213P2", f"{tag}_p5_sess_byte1", b1,
            "rpm:byte@[SessionClass+0x1]",
            note="★ P5：SessionClass[0] dword 的 byte[1]")
    rec.add("QC213P2", f"{tag}_p5_clean_bit",
            None if b1 is None else (b1 & QC213P2_SESSION_CLEAN_MASK),
            "script:(byte[1] & 0x08)",
            note="★ P5 预测：0x08（0x4FC16C 清洗循环前置置位）")
    rec.add("QC213P2", f"{tag}_p5_clean_set",
            None if b1 is None else bool(b1 & QC213P2_SESSION_CLEAN_MASK),
            "script:bool(byte[1] & 0x08)",
            note="★ P5 预测：True；False ⇒ 0x4FC179 清洗不执行，"
                 "f373 步兵清零需另寻路径")
    # ---- 每屋：P2/P4 + P1 该指数在 list@0x5550 上的计数 ----
    items = _rpm_u32_qc213p2_base(handle, QC213P2_HOUSE_ITEMS_VA)
    count = _rpm_u32_qc213p2_base(handle, QC213P2_HOUSE_COUNT_VA)
    if items is None or count is None:
        _qc213p2_err(rec, frame, "read_fail")
        return
    if items == 0 or count > 64:
        _qc213p2_err(rec, frame, "bad_vector")
        return
    rec.add("QC213P2", f"{tag}_meta_count", count, "rpm:rd32(0x00A80238)",
            note="★ QC213P2：HouseClass 枚举数（预期 4；≥14=FFA 块军模型）")
    for i in range(count):
        hp = _rpm_u32_qc213p2_base(handle, items + 4 * i)
        if hp is None:
            for k, _kd, _off in _QC213P2_HOUSE_FIELDS:
                rec.add("QC213P2", f"{tag}_h{i}_{k}", None,
                        "rpm:Items[i] 读失败",
                        note="★ QC213P2：Items[i] 指针读失败 ⇒ 该 house 全字段 null")
            for k in ("ht1A6", "p1_c5550_count", "p1_c5550_idx",
                      "p1_idx_ge_cap"):
                rec.add("QC213P2", f"{tag}_h{i}_{k}", None,
                        "rpm:Items[i] 读失败",
                        note="★ QC213P2：Items[i] 指针读失败 ⇒ 该 house 全字段 null")
            continue
        for k, kd, off in _QC213P2_HOUSE_FIELDS:
            v = (_qc213p2_u8(handle, hp, off) if kd == "u8"
                 else _rpm_u32_qc213p2_base(handle, hp + off))
            rec.add("QC213P2", f"{tag}_h{i}_{k}", v,
                    f"rpm:HouseClass+0x{off:X} {kd}",
                    note="★ QC213P2 per-house 探针（只读）")
        htc = _rpm_u32_qc213p2_base(handle, hp + 0x34)
        ht1a6 = (None if (htc is None or htc == 0)
                 else _qc213p2_u8(handle, htc, QC213P2_HT_IS_OBS_OFF))
        rec.add("QC213P2", f"{tag}_h{i}_ht1A6", ht1a6,
                "rpm:byte@[HouseClass+0x34]+0x1A6",
                note="★ P2 预测：h0/h1=0、h2/h3=1（=1 ⇒ 0x4F8EB7 跳过该屋）")
        lcap = _rpm_u32_qc213p2_base(handle, hp + QC213P2_L5550_OFF + 0x8)
        lcount = _rpm_u32_qc213p2_base(handle, hp + QC213P2_L5550_OFF + 0x10)
        litems = _rpm_u32_qc213p2_base(handle, hp + QC213P2_L5550_OFF + 0x4)
        rec.add("QC213P2", f"{tag}_h{i}_p1_c5550_count", lcount,
                "rpm:rd32(HouseClass+0x5560)（list@0x5550 Count=list+0x10）",
                note="★ P1 辅读：步兵链总计数（与 QC213 c5560 同址互核）")
        if idx is None or lcap is None:
            cidx, ge_cap = None, None
        elif idx >= lcap:
            cidx, ge_cap = 0, True       # 引擎 0x49FAE0：越界扩容并清零尾部 ⇒ 计数 0
        else:
            cidx = (None if (litems is None or litems == 0)
                    else _rpm_u32_qc213p2_base(handle, litems + 4 * idx))
            ge_cap = False
        rec.add("QC213P2", f"{tag}_h{i}_p1_c5550_idx", cidx,
                "rpm:rd32([list@0x5550+0x4] + 4*idx)（idx<[list+0x8]）",
                note="★ P1 预测：0（或 Arr8E8[1]==NULL ⇒ 不参与判据）")
        rec.add("QC213P2", f"{tag}_h{i}_p1_idx_ge_cap", ge_cap,
                "script:(idx >= [list@0x5550+0x8])",
                note="★ P1：True ⇒ 引擎 0x49FAE0 会扩容清零尾部 ⇒ 该指数计数=0")
    _QC213P2_PROBE["snapshots"].append({"frame": frame, "kind": kind,
                                        "count": count})


def _qc213p2_tick(handle, frame: int) -> None:
    """★ QC213P2：measure 循环帧钟读数驱动的闩锁/冻结看门（**绝不抛**）。"""
    st = _QC213P2_PROBE
    if not st["on"] or st["done"]:
        return
    try:
        now = time.monotonic()
        if st["first_frame"] is None:
            st["first_frame"] = frame
        st["last_frame"] = frame
        lf = st["last_f"]
        if lf is None or frame != lf:
            st["last_f"], st["last_t"] = frame, now
        if not st["early_done"]:
            # ★ 早闩：首拍必落（捕 h1 开局零出生签名；键=实际帧号）
            st["early_done"] = True
            _qc213p2_snapshot(handle, frame, "early")
            if frame in QC213P2_LADDER_SET:
                st["latched"][str(frame)] = True
                st["latched_n"] += 1
        elif ((now - st["last_t"]) >= QC213P2_FREEZE_S
              and not st["frozen_done"]):
            st["frozen_done"] = True
            st["done"] = True
            _qc213p2_snapshot(handle, frame, "frozen_final")
            return
        elif frame in QC213P2_LADDER_SET and str(frame) not in st["latched"]:
            st["latched"][str(frame)] = True
            st["latched_n"] += 1
            _qc213p2_snapshot(handle, frame, f"latch{frame}")
        if (st["latched_n"] >= len(QC213P2_LADDER)
                and st["frozen_done"]):
            st["done"] = True
    except Exception as e:                     # ★ 探针内部异常收口（不抛）
        st["done"] = True
        st["err"] = repr(e)
        rec = ACTIVE_REC[0]
        if rec is not None and st["errs"] < QC213P2_ERR_CAP:
            st["errs"] += 1
            rec.add("QC213P2", "qc213p2_probe_error",
                    {"kind": "exception", "repr": repr(e)[:200]},
                    "script:_qc213p2_tick",
                    note="★ QC213P2：探针内部异常收口（只记不抛）")


_rpm_u32_qc213p2_base = _rpm_u32


def _rpm_u32(handle, va: int):
    """★ QC213P2 包装（同名可插拔缝；锚=`_rpm_u32_qc213p2_base`=QC213 包装）：
    CurrentFrame 读数顺路驱动 QC213P2 逐帧阶梯（piggyback 500Hz measure 循环）。

    ★ 探针 off（缺省）⇒ 逐字直通锚函数（同对象调用，异常语义同锚，零行为差异）；
      on ⇒ 每拍做「帧号 ∈ 阶梯集合」的 O(1) 判定，命中才做一次性快照
      （每屋 ~11 dword）；基础读违反「不抛」契约 ⇒ 只记 probe_error 不抛。
    """
    if not _QC213P2_PROBE["on"]:
        return _rpm_u32_qc213p2_base(handle, va)
    try:
        v = _rpm_u32_qc213p2_base(handle, va)
    except Exception as e:                     # ★ 探针失败不抛（契约外异常收口）
        st = _QC213P2_PROBE
        st["done"] = True
        st["err"] = repr(e)
        _qc213p2_err(ACTIVE_REC[0], None, "exception")
        return None
    if (not _QC213P2_PROBE["done"]
            and v is not None and va == MEASURE_CURRENT_FRAME_VA):
        _qc213p2_tick(handle, v)
    return v
# <<< QC213P2-END probe


# >>> QC151P3-BEGIN p3dump（嵌套哨兵：删本块=还原锚 c25ad782…；缺省 off=零执行零行）
# ===========================================================================
# §10.8c · QC151P3 · 冻结态 minidump 采集 + 锁存阶梯解析（★ 随 --frozen-dump/
#   --probe-frames 显式开启；★ 补丁副本制：本块只存在于补丁文本，锚零改动）
# ===========================================================================
# ★ 触发点：QC213 冻结检测（_qc213_tick 的 frozen_done 判定处；见本补丁 hunk D）。
# ★ 手段：dbghelp!MiniDumpWriteDump（MiniDumpNormal=0）对 gamemd.exe 抓 dump，落
#   WORKDIR 根下 frozen_f<frame>.dmp；供离线解析主线程挂死 IP/调用栈（目标②：
#   终局路径 0x4FC9E0 指令级定谳）；并终审「记分板等待输入（良性）vs 真挂死」。
# ★★ 冻结窗内运行时动作最小化：仅 OpenProcess+CreateFileW+MiniDumpWriteDump
#   +CloseHandle×2；★ 栈解析零运行时（一律离线）；rec（MEASURE 组）只写
#   dump 路径/字节数/pid/frame（成功一行）或 pid/frame/err（失败一行）。
# ★ 权限：PROCESS_QUERY_INFORMATION(0x0400)|PROCESS_VM_READ(0x0010)|
#   PROCESS_DUP_HANDLE(0x0040)（任务书 §c 钉定；MiniDumpNormal 即可）。
# ★★ ctypes argtypes 纪律（★ 真机实证坑）：64 位 Python 调 Win32 必须逐 API
#   声明 argtypes/restype——否则句柄按默认 c_int(32 位) 截断 ⇒ "int too long
#   to convert"/静默截断（QC183/QC184 先例；find_pids/_rpm_open 同款写法）。
# ★ 失败只记不抛（QC213 探针同纪律：冻结窗内绝不冒泡异常）。
# ★★ WoW64 注意（离线解析口径）：本探针进程=64 位 Python、gamemd.exe=32 位
#   ⇒ dump 为 WoW64 形态：主视图线程上下文为 64 位，x86 EIP 须 wow64 感知
#   工具离线取（WinDbg `.load wow64exts` / `.effmach x86`）；兜底口径：
#   MiniDumpNormal 含全线程栈内存 ⇒ 可在 gamemd 映像区间（0x400000–0x8E0000）
#   直接扫返回地址链复核 0x4FC9E0 挂死段。两路均为离线动作。
_QC151P3_STATE = {"on": False, "pid": None}

QC151P3_L5550_COUNT_OFF = 0x5550 + 0x10   # ★ list@0x5550 的 Count（=list 对象 +0x10；c5574 同模式）
QC151P3_MINIDUMP_NORMAL = 0x00000000      # MINIDUMP_TYPE：MiniDumpNormal
QC151P3_OPEN_RIGHTS = 0x0400 | 0x0010 | 0x0040   # QUERY_INFORMATION|VM_READ|DUP_HANDLE
QC151P3_GENERIC_WRITE = 0x40000000        # GENERIC_WRITE
QC151P3_FILE_SHARE_READ = 0x00000001      # FILE_SHARE_READ
QC151P3_CREATE_ALWAYS = 2                 # CREATE_ALWAYS
QC151P3_FILE_ATTRIBUTE_NORMAL = 0x00000080  # FILE_ATTRIBUTE_NORMAL


def _qc151p3_probe_frames(spec):
    """★ QC151P3：--probe-frames argparse type：'300,600,1800' ⇒ (300,600,1800)。

    ★ 逗号分隔正整数；去重升序；空/0/负/非整数 ⇒ ArgumentTypeError
      （argparse 退出码 2 硬停——不静默回退）。
    ★★ 缺省串 = "300,600,1800"（== 锚 QC213_LATCH_FRAMES ⇒ 缺省=现行为逐字节
      一致）。★ 补遗①原文拟缺省 "300"，但锚现行为是三点锁存
      （QC213_LATCH_FRAMES=(300,600,1800)）⇒ 为守 flag-off 房规取三点全列
      （见 RECEIPT §缺省等价性论证）。
    """
    try:
        vals = [int(p.strip()) for p in str(spec).split(",") if p.strip() != ""]
        if not vals or any(v <= 0 for v in vals):
            raise ValueError(spec)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(
            f"--probe-frames 须为逗号分隔正整数（得 {spec!r}）") from None
    return tuple(sorted(set(vals)))


def _qc151p3_frozen_dump(frame: int) -> None:
    """★ QC151P3：冻结触发 ⇒ MiniDumpWriteDump 抓 gamemd.exe；★ 只记不抛。

    ★ 落 WORKDIR 根下 frozen_f<frame>.dmp；成功一行 rec（MEASURE 组）只含
      {ok,path,bytes,pid,frame}；失败一行 {ok:False,pid,frame,err}。
      ★ 栈解析一律离线（冻结窗内零解析动作）。
    """
    st = _QC151P3_STATE
    rec = ACTIVE_REC[0]
    pid = st["pid"]
    if rec is None or pid is None:
        return
    k32 = ctypes.windll.kernel32
    dbgh = ctypes.windll.dbghelp
    # ★★ argtypes/restype 全声明（缺声明 ⇒ 64 位句柄按 c_int 截断——真机实证坑）
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle.restype = wt.BOOL
    k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD,
                                ctypes.c_void_p, wt.DWORD, wt.DWORD, wt.HANDLE]
    k32.CreateFileW.restype = wt.HANDLE
    dbgh.MiniDumpWriteDump.argtypes = [
        wt.HANDLE,        # [in] HANDLE hProcess
        wt.DWORD,         # [in] DWORD ProcessId
        wt.HANDLE,        # [in] HANDLE hFile
        wt.DWORD,         # [in] MINIDUMP_TYPE DumpType（MiniDumpNormal=0）
        ctypes.c_void_p,  # [in] PMINIDUMP_EXCEPTION_INFORMATION（NULL）
        ctypes.c_void_p,  # [in] PMINIDUMP_USER_STREAM_INFORMATION（NULL）
        ctypes.c_void_p]  # [in] PMINIDUMP_CALLBACK_INFORMATION（NULL）
    dbgh.MiniDumpWriteDump.restype = wt.BOOL
    hproc = None
    hfile = None
    out = WORKDIR / f"frozen_f{frame}.dmp"
    try:
        hproc = k32.OpenProcess(QC151P3_OPEN_RIGHTS, False, pid)
        if not hproc:
            rec.add("MEASURE", "qc151p3_frozen_dump",
                    {"ok": False, "pid": pid, "frame": frame,
                     "err": f"OpenProcess err={ctypes.GetLastError()}"},
                    "kernel32:OpenProcess",
                    note="★ QC151P3：dump 失败只记不抛（冻结窗内零冒泡）")
            return
        hfile = k32.CreateFileW(
            str(out), QC151P3_GENERIC_WRITE, QC151P3_FILE_SHARE_READ,
            None, QC151P3_CREATE_ALWAYS, QC151P3_FILE_ATTRIBUTE_NORMAL, None)
        if (not hfile) or (hfile == INVALID_HANDLE_VALUE):
            rec.add("MEASURE", "qc151p3_frozen_dump",
                    {"ok": False, "pid": pid, "frame": frame,
                     "err": f"CreateFileW err={ctypes.GetLastError()}"},
                    "kernel32:CreateFileW",
                    note="★ QC151P3：dump 失败只记不抛（冻结窗内零冒泡）")
            return
        ok = dbgh.MiniDumpWriteDump(hproc, pid, hfile,
                                    QC151P3_MINIDUMP_NORMAL, None, None, None)
        if not ok:
            rec.add("MEASURE", "qc151p3_frozen_dump",
                    {"ok": False, "pid": pid, "frame": frame,
                     "err": (f"MiniDumpWriteDump ret=FALSE "
                             f"err={ctypes.GetLastError()}")},
                    "dbghelp:MiniDumpWriteDump",
                    note="★ QC151P3：dump 失败只记不抛（冻结窗内零冒泡）")
            return
        k32.CloseHandle(hfile)     # ★ 先关再计字节数（size 以文件系统为准）
        hfile = None
        rec.add("MEASURE", "qc151p3_frozen_dump",
                {"ok": True, "path": str(out), "bytes": out.stat().st_size,
                 "pid": pid, "frame": frame},
                "dbghelp:MiniDumpWriteDump(MiniDumpNormal)",
                note="★ QC151P3：冻结 dump 落盘；栈解析一律离线"
                     "（主线程终态 ⇒ 裁决「记分板等待输入（良性）vs 真挂死」；"
                     "喂目标② 0x4FC9E0 指令级定谳）")
    except Exception as e:                     # ★ 冻结窗内绝不抛（QC213 同纪律）
        try:
            rec.add("MEASURE", "qc151p3_frozen_dump",
                    {"ok": False, "pid": pid, "frame": frame,
                     "err": repr(e)[:200]},
                    "script:_qc151p3_frozen_dump",
                    note="★ QC151P3：dump 异常只记不抛")
        except Exception:
            pass
    finally:
        if hfile:
            k32.CloseHandle(hfile)
        if hproc:
            k32.CloseHandle(hproc)
# <<< QC151P3-END p3dump


def _measure_pctl(sorted_vals, q: float):
    """★ 线性插值分位（无 numpy 依赖；空 ⇒ None）。"""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    idx = (len(sorted_vals) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def _measure_stats(samples):
    """★ 窗统计（D-1 帧沿差分口径；`MEASURE_DESIGN_v1.md` §3.2/§3.3）。

    ★ fps_avg = (f_end − f_start)/实测跨度 —— 主对照指标（R8；总量式，稳健口径）；
      ★★ **零推进 ⇒ 写 `null` 不写 0**（§3.2 / Recorder 纪律）。
    ★★ D-1：frame_ms_p50/p90/p99/max 一律**帧沿差分**——
      `frame_edges[k] = (f, t_first_observed)`（只记 `f` 变化的那次读数），
      帧时 = 相邻沿时刻差；`df>1` 的沿**整条丢弃并计数** `n_multi_advance`
      （不折进 dt/df）。★ 禁用 bench「相邻轮询 `dt/df`」式——500 Hz 轮询下
      塌缩为轮询周期 2 ms（§3.3 合成流实证：现行式 2.0ms/500fps vs 沿差分
      34ms/29.41fps）。fps_p50 = 1000/p50；fps_1pct_low = 1000/p99
      （仅沿差分口径下合法，QI16 口径表）；tick_miss = 沿间隔 >1.5×p50 计数。
    ★ max_stall_s = 最长「连续 df=0」墙钟跨度（E-3/U0800 塌方边界描述量；
      观测口径 = 值变化时刻 − 该值段起点，量化边界照实披露）。
    ★ 返回 `(st, frame_edges)`：st 含 n_edges / n_multi_advance 量化披露；
      frame_edges = 原始沿表 `[(f, t_first_observed), ...]`（★ D-2：只落
      窗 JSON，**禁入 rec**——原始样序列不进 rec，§3.2）。
    """
    st = {"fps_avg": None, "fps_p50": None, "fps_1pct_low": None,
          "frame_ms_p50": None, "frame_ms_p90": None, "frame_ms_p99": None,
          "frame_ms_max": None, "tick_miss": None, "logic_frames": None,
          "max_stall_s": None, "hz_effective": None, "samples": len(samples),
          "n_edges": 0, "n_multi_advance": 0,
          "note": ""}
    if len(samples) < 2:
        st["note"] = "insufficient samples"
        return st, []
    (t_a, f_a), (t_b, f_b) = samples[0], samples[-1]
    span = t_b - t_a
    logic = int(f_b) - int(f_a)
    st["logic_frames"] = logic
    if span > 0:
        st["hz_effective"] = round(len(samples) / span, 1)
    # ★★ D-2：帧沿表 `frame_edges` = (f, t_first_observed)——只记 `f` 变化
    #   的那次读数（原始沿时刻表，随窗 JSON 落盘供离线换估计式重算，S-1）
    frame_edges: list = []
    _prev_f = None
    for _t, _f in samples:
        _fi = int(_f)
        if _prev_f is None or _fi != _prev_f:
            frame_edges.append((_fi, _t))
            _prev_f = _fi
    st["n_edges"] = len(frame_edges)
    # ★ max_stall_s（≥2 样即可测；整窗零推进 ⇒ = 整窗跨度）
    run_t0, run_f = samples[0]
    best = 0.0
    for t, f in samples[1:]:
        if f != run_f:
            if t - run_t0 > best:
                best = t - run_t0
            run_t0, run_f = t, f
    if samples[-1][0] - run_t0 > best:
        best = samples[-1][0] - run_t0
    st["max_stall_s"] = round(best, 6)
    if logic <= 0:
        # ★★ 零推进：主指标全 `null` + note（max_stall_s 已留存整窗跨度）
        st["note"] = "frame not advancing"
        return st, frame_edges
    if span <= 0:
        st["note"] = "span not measurable"
        return st, frame_edges
    st["fps_avg"] = logic / span
    # ★★ D-1：帧时 = 相邻帧沿时刻差（df==1 入样；df>1 整条丢弃并计数
    #   `n_multi_advance`，不折进 dt/df；df≤0（计数器回绕）同样不入样）
    frame_ms: list = []
    _n_multi = 0
    for (fa, ta), (fb, tb) in zip(frame_edges, frame_edges[1:]):
        df = fb - fa
        if df == 1:
            frame_ms.append((tb - ta) * 1000.0)
        elif df > 1:
            _n_multi += 1
    st["n_multi_advance"] = _n_multi
    if frame_ms:
        frame_ms.sort()
        p50 = _measure_pctl(frame_ms, 0.50)
        p90 = _measure_pctl(frame_ms, 0.90)
        p99 = _measure_pctl(frame_ms, 0.99)
        st["frame_ms_p50"] = p50
        st["frame_ms_p90"] = p90
        st["frame_ms_p99"] = p99
        st["frame_ms_max"] = frame_ms[-1]
        st["fps_p50"] = (1000.0 / p50) if p50 > 0 else None
        st["fps_1pct_low"] = (1000.0 / p99) if p99 > 0 else None
        thr = p50 * MEASURE_TICK_MISS_FACTOR
        st["tick_miss"] = sum(1 for v in frame_ms if v > thr)
    else:
        st["note"] = st["note"] or "net advance without adjacent advancing pair"
    return st, frame_edges


def _measure_write_json(out_dir: Path, k: int, payload: dict) -> Path:
    """★ 窗 JSON **即刻**落盘（§3.2：防硬退出丢样；★ 原始样序列禁入 rec）。"""
    p = out_dir / f"measure_w{k}.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


def _measure_error_payload(k: int, trip_id: str, map_sha256: str, err: str) -> dict:
    """★ 整窗不可测时的占位 JSON（全 `null` 不写 0；§5.4 verdict=error）。"""
    return {"schema": "MEASURE_V1", "trip_id": trip_id,
            "map_sha256": map_sha256, "gamemd_sha256": CTRL1_SHA256,
            "window": k, "hz": MEASURE_HZ, "t_clock": "time.perf_counter",
            "t_abs0": time.time(), "span_s": 0.0, "settle_s": 0.0,
            "gate": {"pre_fps15": None, "units0": None, "ok": False},
            "w1": None,
            "samples": {"t": [], "f": []}, "counters": [],
            "stats": _measure_stats([])[0],
            "verdict": "error", "error": err}


# ★★ QC208（2026-10-18，T32 真机实录 trip-id QC161-U0400-T32）三点修复：
#   ① 阶段 verdict 空窗降级（绿闸修复）；② 测窗末取证；③ 窗前焦点重取。
#   ★ D-1 帧沿差分统计内核（`_measure_stats`：df 采样 / fps_avg 总量式 /
#     frame_ms 分位 / frame_edges 落盘）**零改动**；NAV 三段/签名闸/S-4/
#     安全链/退出码表**零改动**。取证全走既有只读 API 模式（与 §10.8
#     RPM 轮询同风格）：**不 sleep/暂停进程、不写游戏内存**。

def _measure_focus_regrab(rec: Recorder, hwnd: int, k: int) -> None:
    """★★ QC208-③：窗前焦点重取（尽力而为，不硬抢）。

    ★ 仅当 `GetForegroundWindow() != hwnd`（游戏非前台）时行动：
      记 `focus_lost_w{k}` 行 + **恰一次** `SetForegroundWindow`
      （★ 不重试多次、不走 `_focus_foreground` 的 3 段序列、不发 ALT）；
      成功与否都如实记（API 返回值 + 复核前台归属 `focus_ok_after`）。
    ★ 调用点在 `begin_stage` **之前** ⇒ 不占用 30s 阶段帽预算（不阻塞窗口预算）。
    """
    u32 = ctypes.windll.user32
    u32.GetForegroundWindow.argtypes = []
    u32.GetForegroundWindow.restype = wt.HWND
    u32.SetForegroundWindow.argtypes = [wt.HWND]
    u32.SetForegroundWindow.restype = wt.BOOL
    fg = u32.GetForegroundWindow()
    if fg == hwnd:
        return
    rec.add("MEASURE", f"focus_lost_w{k}",
            {"game_hwnd": hwnd, "fg_hwnd": fg},
            "user32:GetForegroundWindow",
            note="★ QC208-3：窗前游戏非前台 ⇒ 记账并尝试一次重取（不硬抢）")
    _ok = bool(u32.SetForegroundWindow(hwnd))
    _fg2 = u32.GetForegroundWindow()
    rec.add("MEASURE", f"focus_regrab_w{k}",
            {"setforeground_ok": _ok, "focus_ok_after": _fg2 == hwnd},
            "user32:SetForegroundWindow",
            note="★ QC208-3：恰一次尝试；成功与否如实记（不重试多次）")


def _measure_window_forensics(rec: Recorder, handle, hwnd, k: int,
                              out_dir: Path, stats) -> None:
    """★★ QC208-②：测窗末取证（每窗结束必做，无论空否）。

    ★ 全走既有只读 API 模式（与 §10.8 RPM 轮询同风格；零写目标进程）：
      - 游戏窗口标题（user32 GetWindowTextW）；
      - 前台窗口 hwnd（user32 GetForegroundWindow）及其标题；
      - 游戏 hwnd 与前台一致性（focus_ok 布尔）；
      - CurrentFrame 现值（VA 0x00A8ED84 / file_off 0x0068ED84；`_rpm_u32`）。
    ★ 空窗（QC208-1 判据：logic_frames==0 ∨ n_edges≤1；或本窗异常无统计
      `stats=None`）⇒ 另存截图 `measure_w{k}_end_x.png`（复用既有
      `capture_frame`；★ `_x` 后缀 = 空窗取证，同 navsig `_g`/`_x` 口径；
      ★ 采点在轮询窗**结束后** ⇒ 不碰 §3.1-②「测量窗内零 PrintWindow」禁令）。
    ★ 本函数自身全收口：取证异常只记 `measure_forensics_w{k}_error` 行，
      绝不影响趟（§5.4 同款）。
    """
    try:
        u32 = ctypes.windll.user32
        u32.GetForegroundWindow.argtypes = []
        u32.GetForegroundWindow.restype = wt.HWND
        u32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
        u32.GetWindowTextW.restype = ctypes.c_int
        fg = u32.GetForegroundWindow()
        _tg = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd, _tg, 256)
        _tf = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(fg, _tf, 256)
        payload = {"window": k, "game_hwnd": hwnd, "game_title": _tg.value,
                   "fg_hwnd": fg, "fg_title": _tf.value,
                   "focus_ok": bool(fg == hwnd),
                   "current_frame": (_rpm_u32(handle,
                                              MEASURE_CURRENT_FRAME_VA)
                                     if handle else None)}
        # ★ QC208-1 空窗判据复用；本窗异常（stats=None）按空窗取证
        _empty = (stats is None or stats.get("logic_frames") == 0
                  or (stats.get("n_edges") or 0) <= 1)
        payload["empty_window"] = _empty
        if _empty and hwnd:
            _png = out_dir / f"measure_w{k}_end_x.png"
            _ok_cap, _wh = capture_frame(hwnd, _png)
            payload["forensics_png"] = _png.name
            payload["capture_ok"] = bool(_ok_cap)
            payload["capture_wh"] = list(_wh)
        rec.add("MEASURE", f"measure_forensics_w{k}", payload,
                "user32:GetForegroundWindow/GetWindowTextW"
                "+kernel32:ReadProcessMemory",
                note="★ QC208-2：测窗末取证（每窗必做；空窗另存 "
                     "measure_w{k}_end_x.png）")
    except Exception as exc:      # ★ §5.4：内部捕获，不冒泡
        rec.add("MEASURE", f"measure_forensics_w{k}_error", repr(exc),
                "script:_measure_window_forensics",
                note="★ QC208-2：取证失败只记账，绝不影响趟")


def _measure_run(rec: Recorder, budget: TripBudget, pid: int, out_dir: Path,
                 map_sha256: str, hwnd=None) -> None:
    """★★ QC202/C1 measure 阶段簇（MEASURE_DESIGN_v1.md §2.1/§3.2/§3.3/§5）。

    ★ 前置（调用方保证）：`--measure` 非 0 且 `NAV.verdict=="OK"`（burst 闸全绿）。
    ★ 结构：settle 4 s（窗 0 前置，§3.3）→ 窗前在局闸（§3.2）→
      W1 裁决门（首窗 units0≥150，§4.3；★ D-4：TIER_INVALID ⇒ 跳全部采样窗）→
      3 窗×25 s（每窗独立 `begin_stage`/`end_stage`，25<30−2 帽余量；
      窗间 `check_trip`，§5.1）。
    ★★ QC208（T32 实录绿闸修复）：`hwnd` = 游戏主窗（调用方传入；
      缺省 None ⇒ ③②自动让位）——③ 每窗 `begin_stage` 前焦点重取
      （`_measure_focus_regrab`，尽力而为恰一次）；② 每窗 `end_stage` 后
      测窗末取证（`_measure_window_forensics`；空窗另存
      `measure_w{k}_end_x.png`）；① 阶段 verdict 空窗降级（采样窗
      logic_frames==0 ∨ n_edges≤1 记 empty ⇒ 全空 "empty"/部分空
      "degraded"；三窗全有效保持 "ok" 零回归；异常窗维持既有 "error"）。
    ★ 退出语义（§5.4/§5.2）：采样器一切异常**内部捕获** ⇒ verdict 落账后
      照常继续 fields_post/T1；**不改**进图闸语义、**不加**退出码。
    ★ 落盘：仅 `WORKDIR\\measure_w{k}.json`（运行期写域，QC162:W1）；
      rec 只入统计行（原始样序列禁入 rec，§3.2）。
    ★ 句柄：本函数开头 OpenProcess（S-4 之后）、finally CloseHandle（§3.2）。
    """
    rec.add("MEASURE", "protocol", {
        "schema": "MEASURE_V1", "hz": MEASURE_HZ, "windows": MEASURE_WINDOWS,
        "window_s": MEASURE_WINDOW_S, "settle_s": MEASURE_SETTLE_S,
        "current_frame": (f"VA 0x{MEASURE_CURRENT_FRAME_VA:08X} / "
                          f"file_off 0x{MEASURE_CURRENT_FRAME_FILE_OFF:08X}"),
        "w1_units0_min": MEASURE_W1_UNITS0_MIN, "trip_id": TRIP_ID,
    }, "MEASURE_DESIGN_v1.md:§3.2/§3.3/§5.1")
    # ★ 场景固定化（§4.1/§5）：各项已由既有 trip 结构钉死，此处**只记录不依赖**
    #   （记录值为设计稿钉定值；运行期**不新增**任何读/写/动作）。
    rec.add("MEASURE", "scene_fixed", {
        "map_sha256": map_sha256, "gamemd_sha256": CTRL1_SHA256,
        "game_speed": 2, "credits": 10000, "unit_count": 0,
        "input_zero_disturbance": "measure 窗内零键鼠零捕获（§3.2/§4.1）",
        "note": "★ §4.1 母版冻结变体钉定值（记录不依赖）"},
        "MEASURE_DESIGN_v1.md:§4.1")
    handle = None
    try:
        handle = _rpm_open(pid)
    except Exception as exc:       # ★ §5.4：内部捕获，不冒泡
        rec.add("MEASURE", "open_exception", repr(exc), "kernel32:OpenProcess")
    rec.add("MEASURE", "handle_opened", bool(handle), "kernel32:OpenProcess",
            note="★ PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ **只读**"
                 "（§3.2）；★ S-4 之后开、本函数 finally 关")
    if not handle:
        payload = _measure_error_payload(0, TRIP_ID, map_sha256,
                                         "OpenProcess 失败 ⇒ 全窗不可测")
        _p = _measure_write_json(out_dir, 0, payload)
        rec.add("MEASURE", "window_0_stats", payload["stats"],
                "script:_measure_stats", note=f"★ verdict=error；JSON={_p.name}")
        rec.add("MEASURE", "verdict", "error", "script:_measure_run",
                note="★ 句柄不可得 ⇒ 进图闸语义不变、退出码不加新码（§5.2）")
        rec.add("MEASURE", "w1_u0400_tier",
                {"units0": None, "valid": None, "verdict": "UNMEASURABLE",
                 "note": "★ 句柄不可得 ⇒ 不可测（记 null，不写 0）"},
                "MEASURE_DESIGN_v1.md:§4.3")
        return
    try:
        # ---- settle 4 s（窗 0 前置，§3.3；同时供窗前在局闸取数）----
        _settle_wall0 = time.time()
        t0s, s_samples, s_counters, s_err = _measure_poll_span(
            handle, MEASURE_SETTLE_S, MEASURE_HZ)
        rec.add("MEASURE", "settle_seconds",
                (round(s_samples[-1][0] - s_samples[0][0], 3)
                 if len(s_samples) >= 2 else None),
                "time.perf_counter",
                note="★ §5.1 settle 4.0 s（窗 0 前置；不在任何 30s 阶段帽内，"
                     "受 TRIP_BUDGET_S 全程账约束）")
        # ---- 窗前在局闸（§3.2）：1.5 s 内推进 ≥3 fps 且 机动计数 >0 ----
        pre_fps15 = None
        if len(s_samples) >= 2:
            t_cut = t0s + MEASURE_SETTLE_S - MEASURE_GATE_SPAN_S
            gate_pts = [(t, f) for t, f in s_samples if t >= t_cut]
            if len(gate_pts) >= 2:
                _gspan = gate_pts[-1][0] - gate_pts[0][0]
                if _gspan > 0:
                    pre_fps15 = (gate_pts[-1][1] - gate_pts[0][1]) / _gspan
        units0 = None
        for _row in s_counters:
            if _row.get("units") is not None:
                units0 = _row["units"]
                break
        gate_ok = bool(pre_fps15 is not None
                       and pre_fps15 >= MEASURE_GATE_FPS15_MIN
                       and units0 is not None and units0 > 0)
        gate_block = {"pre_fps15": (round(pre_fps15, 3)
                                    if pre_fps15 is not None else None),
                      "units0": units0, "ok": gate_ok,
                      "gate_fps15_min": MEASURE_GATE_FPS15_MIN,
                      "gate_span_s": MEASURE_GATE_SPAN_S}
        rec.add("MEASURE", "gate", gate_block, "script:_measure_run",
                note="★ §3.2 窗前在局闸（fail-fast）：不过 ⇒ no_advance、跳余窗"
                     "（不硬停趟）")
        # ---- W1 裁决门（§4.3）：首窗 units0 ≥150 ⇒ U0400 档成立 ----
        if units0 is None:
            w1 = {"units0": None, "valid": None, "verdict": "UNMEASURABLE",
                  "note": "★ units 不可测 ⇒ 记 null（不写 0）；档位成立与否未证"}
        elif units0 >= MEASURE_W1_UNITS0_MIN:
            w1 = {"units0": units0, "valid": True, "verdict": "OK",
                  "note": "★ fanout 假设成立、U0400 档有效（§4.3）"}
        else:
            w1 = {"units0": units0, "valid": False, "verdict": "TIER_INVALID",
                  "note": "★ units0<150 ⇒ **U0400 档不成立**（§4.3：降级移交 Lead）"}
        rec.add("MEASURE", "w1_u0400_tier", w1, "MEASURE_DESIGN_v1.md:§4.3",
                note="★ W1 裁决门（D-4 接入判定流）：TIER_INVALID ⇒ 跳全部"
                     "采样窗（§4.3）；OK/UNMEASURABLE 不改趟语义")
        if not gate_ok:
            # ★ §5.4：no_advance —— 落 w0 JSON（含塌方描述量 max_stall_s）＋统计行
            stats, s_edges = _measure_stats(s_samples)
            payload = {"schema": "MEASURE_V1", "trip_id": TRIP_ID,
                       "map_sha256": map_sha256, "gamemd_sha256": CTRL1_SHA256,
                       "window": 0, "hz": MEASURE_HZ,
                       "t_clock": "time.perf_counter",
                       "t_abs0": _settle_wall0, "span_s": MEASURE_SETTLE_S,
                       "settle_s": MEASURE_SETTLE_S,
                       "gate": gate_block, "w1": w1,
                       "samples": {"t": [round(t, 6) for t, _f in s_samples],
                                   "f": [f for _t, f in s_samples]},
                       "frame_edges": [[f, round(t, 6)] for f, t in s_edges],
                       "counters": s_counters,
                       "stats": stats,
                       "verdict": "no_advance", "error": s_err}
            _p = _measure_write_json(out_dir, 0, payload)
            rec.add("MEASURE", "window_0_stats", stats, "script:_measure_stats",
                    note=f"★ verdict=no_advance；JSON={_p.name}")
            rec.add("MEASURE", "verdict", "no_advance", "script:_measure_run",
                    note="★ 窗前在局闸不过 ⇒ 跳过全部采样窗（§5.4；不硬停趟）")
            return
        if w1["valid"] is False:
            # ★★ D-4（§4.3）：W1=TIER_INVALID 接入判定流——units0<150 ⇒
            #   U0400 不构成有效负载档（旧图病复发/「空图测 FPS」）⇒
            #   跳过全部采样窗，落 w0 JSON（settle 样本＋max_stall_s）＋统计行；
            #   不硬停趟、不加退出码（§5.2/§5.4），降级移交 Lead（§4.3）。
            #   （units0 不可测 ⇒ UNMEASURABLE：units0=None 时上面 gate_ok
            #     必为 False，已由 no_advance 分支收口，不进此支。）
            stats, s_edges = _measure_stats(s_samples)
            payload = {"schema": "MEASURE_V1", "trip_id": TRIP_ID,
                       "map_sha256": map_sha256, "gamemd_sha256": CTRL1_SHA256,
                       "window": 0, "hz": MEASURE_HZ,
                       "t_clock": "time.perf_counter",
                       "t_abs0": _settle_wall0, "span_s": MEASURE_SETTLE_S,
                       "settle_s": MEASURE_SETTLE_S,
                       "gate": gate_block, "w1": w1,
                       "samples": {"t": [round(t, 6) for t, _f in s_samples],
                                   "f": [f for _t, f in s_samples]},
                       "frame_edges": [[f, round(t, 6)] for f, t in s_edges],
                       "counters": s_counters,
                       "stats": stats,
                       "verdict": "tier_invalid", "error": s_err}
            _p = _measure_write_json(out_dir, 0, payload)
            rec.add("MEASURE", "window_0_stats", stats, "script:_measure_stats",
                    note=f"★ verdict=tier_invalid；JSON={_p.name}")
            rec.add("MEASURE", "verdict", "tier_invalid",
                    "script:_measure_run",
                    note="★ W1 units0<150 ⇒ 跳过全部采样窗（D-4/§4.3：U0400 档"
                         "不成立，降级移交 Lead；不硬停趟、退出码不变）")
            return
        # ---- 3 窗 × 25 s（§5.1：每窗独立 begin/end_stage；窗间 check_trip）----
        n_err = 0
        win_status: list = []    # ★ QC208-1：逐窗状态 ok/empty/error（降级判据）
        for k in range(MEASURE_WINDOWS):
            budget.check_trip()      # §5.1：窗间调用（超 180 ⇒ 既有 exit(18) 语义）
            # ★★ QC208-3：窗前焦点重取（尽力而为；begin_stage 之前 ⇒ 不占阶段帽）
            if hwnd:
                _measure_focus_regrab(rec, hwnd, k)
            budget.begin_stage(f"measure_w{k}")
            _win_wall0 = time.time()
            w_samples: list = []
            w_counters: list = []
            w_err = None
            w_status = None          # ★ QC208-1：本窗状态（finally 恰好落一次）
            w_stats = None           # ★ QC208-2：末取证用（异常窗 ⇒ None 按空窗取证）
            try:
                _wt0, w_samples, w_counters, w_err = _measure_poll_span(
                    handle, MEASURE_WINDOW_S, MEASURE_HZ)
                stats, w_edges = _measure_stats(w_samples)
                verdict = "ok" if w_samples else "error"
                # ★★ QC208-1：窗级空窗判定（只读 stats 字段；D-1 内核零改动）
                w_status = ("empty" if (stats.get("logic_frames") == 0
                                        or (stats.get("n_edges") or 0) <= 1)
                            else "ok")
                w_stats = stats
                payload = {"schema": "MEASURE_V1", "trip_id": TRIP_ID,
                           "map_sha256": map_sha256,
                           "gamemd_sha256": CTRL1_SHA256,
                           "window": k, "hz": MEASURE_HZ,
                           "t_clock": "time.perf_counter",
                           "t_abs0": _win_wall0, "span_s": MEASURE_WINDOW_S,
                           "settle_s": (MEASURE_SETTLE_S if k == 0 else 0.0),
                           "gate": gate_block,
                           "w1": (w1 if k == 0 else None),
                           "samples": {"t": [round(t, 6)
                                             for t, _f in w_samples],
                                       "f": [f for _t, f in w_samples]},
                           "frame_edges": [[f, round(t, 6)]
                                           for f, t in w_edges],
                           "counters": w_counters,
                           "stats": stats,
                           "verdict": verdict, "error": w_err}
                _p = _measure_write_json(out_dir, k, payload)
                rec.add("MEASURE", f"window_{k}_stats", stats,
                        "script:_measure_stats",
                        note=f"★ verdict={verdict}；JSON={_p.name}"
                             + (f"；{w_err}" if w_err else ""))
            except Exception as exc:
                # ★ §5.4：窗内异常 ⇒ 只废本窗（截断落盘 verdict=error），继续下窗
                n_err += 1
                try:
                    payload = _measure_error_payload(
                        k, TRIP_ID, map_sha256, f"{type(exc).__name__}: {exc}")
                    payload["t_abs0"] = _win_wall0
                    payload["span_s"] = MEASURE_WINDOW_S
                    payload["gate"] = gate_block
                    payload["w1"] = (w1 if k == 0 else None)
                    _p = _measure_write_json(out_dir, k, payload)
                    rec.add("MEASURE", f"window_{k}_stats", payload["stats"],
                            "script:_measure_stats",
                            note=f"★ 窗内异常只废本窗（§5.4）；JSON={_p.name}")
                except Exception as exc2:
                    rec.add("MEASURE", f"window_{k}_error_payload_failed",
                            repr(exc2), "script:_measure_run",
                            note=f"★ 原窗异常 {type(exc).__name__}: {exc}")
            finally:
                # ★ QC208-1：每窗恰好落一次状态（异常/漏判 ⇒ "error"）
                win_status.append(w_status if w_status is not None
                                  else "error")
                budget.end_stage(f"measure_w{k}")
            # ★★ QC208-2：测窗末取证（end_stage 之后 ⇒ 不占阶段帽；每窗必做）
            _measure_window_forensics(rec, handle, hwnd, k, out_dir, w_stats)
        # ★★ QC208-1：阶段 verdict 空窗降级（绿闸修复）——任一采样窗
        #   logic_frames==0 ∨ n_edges≤1 ⇒ 不得为 "ok"：全空 ⇒ "empty"、
        #   部分空 ⇒ "degraded"；三窗全有效保持 "ok"（T25/T26 三窗可复现
        #   路径零回归：verdict 值与 note 逐字节不变）。异常窗维持既有
        #   "error" 语义（n_err 口径一字不动）。
        if n_err:
            _m_verdict = "error"
        elif win_status and all(s == "empty" for s in win_status):
            _m_verdict = "empty"
        elif "empty" in win_status:
            _m_verdict = "degraded"
        else:
            _m_verdict = "ok"
        _empty_tags = " ".join(f"w{i}:empty"
                               for i, s in enumerate(win_status)
                               if s == "empty")
        rec.add("MEASURE", "verdict", _m_verdict, "script:_measure_run",
                note=(f"★ {MEASURE_WINDOWS} 窗采样完（窗级 verdict 见 "
                      f"window_k_stats 与 measure_w{{k}}.json；异常窗 {n_err}）"
                      + (f"；★ QC208 空窗降级：{_empty_tags}" if _empty_tags
                         else "")))
    finally:
        if handle:
            _rpm_close(handle)
            rec.add("MEASURE", "handle_closed", True, "kernel32:CloseHandle",
                    note="★ §3.2：finally 关句柄")


# ===========================================================================
# §11 · ⑥ 字段 `F-1`…`F-9`（★ 全部**根限定**）
# ===========================================================================
def read_scen_index_lines(ini: Path) -> list:
    """★ 只读 `[Skirmish]` **段内**的 `ScenIndex` 行 ⇒ `[(行号, 原文), ...]`。

    ★★★ `QC157:2`：★ `ScenIndex` **只在 `[Skirmish]` 段内**取（★ 按 INI
      **段头**解析，段头形如 `[Skirmish]`）⇒ ★ 这才能**证明实际地图身份**。
    ★★ **找不到 `[Skirmish]` 或段内无 `ScenIndex` ⇒ 返回空列表**，★ 调用方
      **不得**回落到"全文第一条"（`QC157:2`）—— ★ 那证明不了实际用的槽。
    ★ 返回**同段内全部** `ScenIndex` 行（★ 不截断），由调用方声明取哪条。
    """
    out: list = []
    if not ini.exists():
        return out
    in_skirmish = False
    for i, line in enumerate(ini.read_text(encoding="utf-8", errors="replace")
                             .splitlines(), start=1):
        s = line.strip()
        # ★ INI 段头（★ 形如 `[Skirmish]`；★ 容 `[Skirmish] ; 注释`）
        if s.startswith("[") and "]" in s:
            sec = s[1:s.index("]")].strip().lower()
            in_skirmish = (sec == "skirmish")   # ★ 只有该段内才算
            continue
        if in_skirmish and s.lower().startswith("scenindex"):
            out.append((i, s))
    return out


def collect_F_fields(rec: Recorder, carrier_dir: Path, target_map: Path,
                     target_sha: str, tag: str) -> dict:
    """★ 采集 `F-1`…`F-9`。★ `tag` ∈ {`"pre"`, `"post"`}。

    ★★ `F-2`/`F-4`/`F-5` **必须写全路径（含根名）** —— ★ 因为同名文件在
      `ra2bench\\` 与 `ra2youli\\` 下 **3/5 不同件**（`QC141:39`；
      ★ 本卡复算：`U0050`/`U0200`/`U0800` 不同）。
    ★★ 不可测一律 `null`（`QC141:5`），★ **绝不写 `false`/`0`**。
    """
    res: dict = {}
    ini = carrier_dir / "RA2MD.INI"
    slot = carrier_dir / "[2]0LoadBench_U0400.yrm"

    # --- F-1 / F-3：scen_index（★ 只在 `[Skirmish]` 段内；`QC157:2`） ---
    lines = read_scen_index_lines(ini)
    rec.add("F", "scen_index_lines_skirmish_section", lines, f"{ini}:file",
            note="★ QC157:2：★ 只取 `[Skirmish]` **段内**的 ScenIndex 行；"
                 "★ 段内多条则**全部**列出")
    f_key = "F-1" if tag == "pre" else "F-3"
    # ★★ `QC157:2`：找不到 `[Skirmish]` 或段内无 `ScenIndex` ⇒ 记 `null`，
    #   ★★ **绝不回落到"全文第一条"**（★ 那证明不了实际地图身份）。
    val = lines[0][1].split("=", 1)[-1].strip() if lines else None
    res[f_key] = {
        "name": ("scen_index_pre" if tag == "pre" else "scen_index_post"),
        "value": (int(val) if (val is not None and val.isdigit()) else None),
        "section": ("[Skirmish]" if lines else None),
        "raw": (lines[0][1] if lines else None),
        "line_no": (lines[0][0] if lines else None),
        "line_policy": "只取 `[Skirmish]` 段内**第一条** ScenIndex 行"
                       "（QC157:2：★ 段外一律不算；★ 无 `[Skirmish]` "
                       "或段内无该项 ⇒ null，★ 不回落全文第一条）",
        "all_lines_in_section": lines}
    rec.add("F", f_key, res[f_key],
            f"{ini}:{lines[0][0] if lines else '未测'}",
            note="★ 不可测 ⇒ null（★ 不写 0）")

    # --- F-2 / F-4：槽文件 sha256（★ 全路径含根名） ---
    f_slot = "F-2" if tag == "pre" else "F-4"
    if slot.exists():
        res[f_slot] = {
            "name": ("slot_file_sha256" if tag == "pre" else "slot_file_sha256_post"),
            "full_path": str(slot),                    # ★★ 全路径（含根名）
            "root_name": slot.parent.name,             # ★★ 根名
            "size": slot.stat().st_size,
            "sha256": sha256_file(slot),
        }
    else:
        res[f_slot] = {"full_path": str(slot), "root_name": slot.parent.name,
                       "size": None, "sha256": None}
    rec.add("F", f_slot, res[f_slot], f"{slot}:file",
            note="★★ 全路径含根名（QC141:39：3/5 不同件）")

    # --- F-5：目标地图 sha256（★ 全路径含根名；★ 必填） ---
    res["F-5"] = {"name": "target_map_sha256_pinned",
                  "full_path": str(target_map),        # ★★ 全路径（含根名）
                  "root_name": target_map.parent.name,
                  "size": (target_map.stat().st_size if target_map.exists() else None),
                  "sha256_pinned": target_sha}
    rec.add("F", "F-5", res["F-5"], f"{target_map}:file",
            note="★★ 来自 --target-map/--target-sha256（★ 不写死 T4/母本）")

    # --- F-8：except.txt 完整前后件 + 各自 sha256 ---
    ex = carrier_dir / "except.txt"
    res["F-8"] = {"name": f"except_txt_{tag}",
                  "full_path": str(ex), "root_name": ex.parent.name,
                  "size": (ex.stat().st_size if ex.exists() else None),
                  "sha256": (sha256_file(ex) if ex.exists() else None)}
    rec.add("F", "F-8", res["F-8"], f"{ex}:file",
            note="★ 集合差**仅作辅助**（D-64）")

    # --- F-9：窗口形态 ---
    res["F-9"] = {"name": "window_geometry", "rect": None, "wh": None,
                  "note": "★ 由 collect_window_fields() 在主窗取得（D-59）"}
    return res


def collect_window_fields(rec: Recorder, hwnd) -> dict:
    """★ `F-9` 窗口形态（主窗矩形 / 分辨率）。

    ★ `QC141:126`：★ 判 `0x0` 退化**必须用主窗 `GetWindowRect`**（`D-59`）。
    ★ 未取到 ⇒ `null`（★ 不写 `0`）。
    """
    if hwnd is None:
        f9 = {"rect": None, "wh": None, "degenerate_0x0": None,
              "note": "★ 主窗未取到 ⇒ 全 null（★ 不写 0）"}
        rec.add("F", "F-9", f9, "script:collect_window_fields")
        return f9
    l, t, r, b = rect_of(hwnd)
    w, h = r - l, b - t
    f9 = {"rect": [l, t, r, b], "wh": [w, h],
          "degenerate_0x0": (w == 0 and h == 0),
          "resolution_matches_800x600": (w == FRAME_W and h == FRAME_H),
          "note": "★ GetWindowRect 主窗（D-59）"}
    # >>> QC151FS-BEGIN f9（缺省 off ⇒ f9 键集/取值与锚逐字节一致）
    # ★★ QC151FS：全屏下补输出**窗口实际几何**（全屏窗=整屏尺寸，按实测如实
    #   记录、绝不改写为 800×600）+ 渲染面与坐标映射口径。
    if _QC151FS["on"]:
        _u32_fs = ctypes.windll.user32
        _u32_fs.GetSystemMetrics.argtypes = [ctypes.c_int]
        _u32_fs.GetSystemMetrics.restype = ctypes.c_int
        f9["fullscreen_mode"] = True
        f9["screen_wh"] = [_u32_fs.GetSystemMetrics(0),
                           _u32_fs.GetSystemMetrics(1)]
        f9["render_surface"] = {"origin": list(FS_RENDER_ORIGIN),
                                "wh": [FRAME_W, FRAME_H], "scaled": False}
        f9["coordinate_mapping"] = "screen = window_origin + game_xy × 1.0"
        f9["fs_note"] = ("★ QC151FS：全屏不缩放；渲染面=屏幕左上 (0,0) 起 "
                         "800×600（20261019 实测）")
    # <<< QC151FS-END f9
    rec.add("F", "F-9", f9, f"hwnd={hwnd}:GetWindowRect")
    return f9


# ===========================================================================
# §12 · ⑦ 采帧（★ **只采目标图帧**；`QC157:1` 删除伪反控）
# ===========================================================================
def capture_target_frame(rec: Recorder, hwnd, out_dir: Path) -> dict:
    """★★ 采**唯一一帧**：目标图帧（`QC157:1`）。

    ★★ 旧版 `dual_capture()` 已**删除**（`QC157:1`，★ 用户点名的头号缺陷）：
      ★ 旧版只是**对同一个窗口连续截两张图**，却把第二张标 `label="other"`，
        并在 `reverse_control_5_other` 里写 `in_match = False` ⇒
        ★★ **"未换图却产出 `in_match=False`" = 伪反控证据**，已不复存在。
    ★★ `--other-map` **一并移除**：★ 用户已裁决"其他地图反控改后续独立一趟"。
    ★ 本函数**结构上**只有 `label="target"` 一路：★ 不产 `other` 帧、
      ★ 不产 `reverse_control_5_*`、★ 不产任何 `in_match` 判定。
    ★ `L-A`（`qc95_classify`）的结论**唯一挂在该帧上**。
    """
    label = "target"                       # ★★ 唯一取值（`QC157:1`）
    png = out_dir / "frame_target_01.png"  # ★ 唯一帧文件
    resolution_ok, wh = capture_frame(hwnd, png)
    rec.add("FRAME", f"frame_{label}_wh", wh, "script:capture_frame",
            note="★★ 固定 800×600（QC141:79）")
    rec.add("FRAME", f"frame_{label}_png", str(png), "script:capture_frame")
    if not resolution_ok:
        rec.add("FRAME", f"frame_{label}_frame_resolution_mismatch", True,
                "script:capture_frame",
                note="★★ 主窗≠800×600 ⇒ 该帧 L-A 记 null（★ 不得记 False）")
    la = classify_frame_LA(png, resolution_ok, rec, label)
    return {label: {"png": str(png), "wh": wh,
                    "resolution_ok": resolution_ok,
                    "L_A_in_tactical": la}}



# ===========================================================================
# QC192/T14: diagnostic helpers (read-only observation, no control flow change)
# ===========================================================================

def _pid_alive_check(pid):
    try:
        _k32 = ctypes.windll.kernel32
        _k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
        _k32.OpenProcess.restype = wt.HANDLE
        _k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
        _k32.GetExitCodeProcess.restype = wt.BOOL
        _k32.CloseHandle.argtypes = [wt.HANDLE]
        _k32.CloseHandle.restype = wt.BOOL
        _h = _k32.OpenProcess(0x1000, False, pid)
        if not _h:
            return None
        try:
            _ec = wt.DWORD()
            if _k32.GetExitCodeProcess(_h, ctypes.byref(_ec)):
                return True if _ec.value == 259 else False
            return None
        finally:
            _k32.CloseHandle(_h)
    except Exception:
        return None



def _pid_exit_code(pid):
    """[FAILFAST] 读取已退出进程的 exit code（只读；进程仍活则返回 None）。"""
    try:
        _k32 = ctypes.windll.kernel32
        _k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
        _k32.OpenProcess.restype = wt.HANDLE
        _k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
        _k32.GetExitCodeProcess.restype = wt.BOOL
        _k32.CloseHandle.argtypes = [wt.HANDLE]
        _k32.CloseHandle.restype = wt.BOOL
        _h = _k32.OpenProcess(0x1000, False, pid)
        if not _h:
            return None
        try:
            _ec = wt.DWORD()
            if _k32.GetExitCodeProcess(_h, ctypes.byref(_ec)):
                return None if _ec.value == 259 else int(_ec.value)
            return None
        finally:
            _k32.CloseHandle(_h)
    except Exception:
        return None

def _sys_window_scan():
    try:
        _u = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                         ctypes.c_void_p)
        _u.EnumWindows.argtypes = [WNDENUMPROC, wt.LPARAM]
        _u.EnumWindows.restype = wt.BOOL
        _u.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
        _u.GetWindowThreadProcessId.restype = wt.DWORD
        _u.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
        _u.GetWindowRect.restype = wt.BOOL
        _u.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
        _u.GetWindowTextW.restype = ctypes.c_int
        _u.IsWindowVisible.argtypes = [wt.HWND]
        _u.IsWindowVisible.restype = wt.BOOL
        _items = []
        _total = [0]

        @WNDENUMPROC
        def _proc(hwnd, _):
            _total[0] += 1
            _r = wt.RECT()
            _u.GetWindowRect(hwnd, ctypes.byref(_r))
            _w = _r.right - _r.left
            _h = _r.bottom - _r.top
            _vis = bool(_u.IsWindowVisible(hwnd))
            if _w > 200 and _vis:
                _pid_buf = ctypes.c_ulong()
                _u.GetWindowThreadProcessId(hwnd, ctypes.byref(_pid_buf))
                _t = ctypes.create_unicode_buffer(256)
                _u.GetWindowTextW(hwnd, _t, 256)
                if len(_items) < 40:
                    _items.append({
                        "hwnd": hwnd,
                        "pid": _pid_buf.value,
                        "title": _t.value,
                        "wh": [_w, _h],
                    })
            return True

        _u.EnumWindows(_proc, 0)
        return {"total": _total[0], "big_visible": _items}
    except Exception:
        return None


def _render_log_probe(carrier_dir):
    try:
        _matches = []
        for _pp in Path(carrier_dir).glob("ra2render*.log"):
            try:
                _st = _pp.stat()
                _matches.append({"name": _pp.name, "size": _st.st_size,
                                 "mtime": _st.st_mtime})
            except Exception:
                _matches.append({"name": _pp.name, "size": None, "mtime": None})
        return _matches if _matches else None
    except Exception:
        return None

# ===========================================================================
# §13 · ④ 载体件逐字节还原（★★ 收尾**最后**一步；`QC162:W7`）
# ===========================================================================
# ★★ `BACKUP_DIR` **不在**本卡目录（★ `qc151_u0400_trip` 运行期零写入，
#   静态自检 #2）—— 它位于运行期写域 `WORKDIR`（`QC162:W1`）。
BACKUP_DIR = WORKDIR / "_carrier_bak"


def sync_backup_dir() -> Path:
    """★★ `QC162:W1`：★ 使 `BACKUP_DIR` 跟随 `WORKDIR`（★ `--out-dir` 可改写）。

    ★ 调用点：`main()` 首段（★ 定稿写域之后、**备份载体件之前**）。
    ★ 原因：`BACKUP_DIR` 在**模块级**由 `WORKDIR` 派生；★ `--out-dir`
      覆盖 `WORKDIR` 后必须同步，★ 否则备份会落到旧路径（★ 造成运行期
      写域分裂）。
    """
    global BACKUP_DIR
    BACKUP_DIR = WORKDIR / "_carrier_bak"
    return BACKUP_DIR

def backup_carrier(rec: Recorder, carrier_dir: Path) -> dict:
    """★ 跑前把五个载体件**逐字节**备份（★ 供跑后还原）。"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bak: dict = {}
    for name in CARRIER_FILES:
        src = carrier_dir / name
        if not src.exists():
            rec.add("RESTORE", f"backup_missing:{name}", None, f"{src}:path",
                    note="★ 未测（源不存在）")
            continue
        dst = BACKUP_DIR / name
        dst.write_bytes(src.read_bytes())
        h = sha256_file(dst)
        bak[name] = {"path": str(dst), "size": dst.stat().st_size, "sha256": h}
        rec.add("RESTORE", f"backup_sha256:{name}", h, f"{dst}:file")
    return bak


def restore_carrier(rec: Recorder, carrier_dir: Path, bak: dict) -> bool:
    """★★ 载体件**状态核验**（★ 禁用无条件写回游戏字节，与硬边界一致）。

    ★ 原口径 `QC141:140` 的"逐字节还原"已**禁用**：
      ★ 硬边界禁止改任何游戏文件字节（含以"还原"名义覆盖）。
    ★ 现行为：核验当前载体件与备份的 sha256 是否一致；
      ★ 不一致 ⇒ 记 FAIL，但**不写回**（★ 由 T0/T1 差证明零写）。
    ★ 任何一件不符 ⇒ `False`（★ 调用方以 `EXIT_RESTORE_FAILED` 收口）。
    """
    all_ok = True
    for name in CARRIER_FILES:
        info = bak.get(name)
        if info is None:
            rec.add("RESTORE", f"restore_skipped:{name}", None,
                    "script:restore_carrier", note="★ 无备份 ⇒ 未测")
            continue
        dst = carrier_dir / name
        if not dst.exists():
            rec.add("RESTORE", f"restore_verdict:{name}", "FAIL",
                    "script:restore_carrier",
                    note="★ 载体件缺失 ⇒ 无法核验")
            all_ok = False
            continue
        h = sha256_file(dst)
        ok = (h == info["sha256"]) and (dst.stat().st_size == info["size"])
        if not ok:
            all_ok = False
        rec.add("RESTORE", f"current_sha256:{name}", h, f"{dst}:file",
                note="★ 跑后状态 sha256（★ 不写回，仅核验）")
        rec.add("RESTORE", f"backup_sha256:{name}", info["sha256"],
                f"{info['path']}:file", note="★ 备份 sha256")
        rec.add("RESTORE", f"restore_verdict:{name}", "PASS" if ok else "FAIL",
                "script:restore_carrier",
                note="★ FAIL ⇒ 载体件被改动，但**不写回**（硬边界）")
    return all_ok


# ===========================================================================
# §13-A · ★★★ 全程 `finally` 收尾（`QC157:3`：★ 失败路径不许绕过还原）
#   ★★ `QC162:W7`：★ **先取证、后还原**（证据先于还原；★ 还原放最后一步）
#   ★★ `QC162:W2`：★ 收尾失败 ⇒ 退出码**真的非 0**（见 `_main_wrapper`）
# ===========================================================================
def run_guarded_steps(fns, out_dir: Path | None = None) -> None:
    """★★ 逐个执行收尾项，★ **前一步失败也继续做后面的**（`QC157:3`）。

    ★ 每个收尾项**各自独立、互不跳过**：★ 某步失败只**记账**，
      ★ **绝不**让一个收尾项的异常带走后续收尾项。
    ★★ 全部项跑完后，★ **`raise errors[0][1]` 原样重抛第一个异常**
      （`QC157:4`：★ **不得吞**）—— ★ 重抛前已把每个失败的
      `文件:行`·`类型`·`repr` 落盘到 `finalize_errors.txt`。
    ★★ `QC162:W1`：`out_dir` 缺省 `WORKDIR`（★ 运行期写域），
      ★ **绝不**落进本卡目录 `qc151_u0400_trip`。
    """
    if out_dir is None:
        out_dir = WORKDIR
    errors: list = []
    for name, fn in fns:
        try:
            fn()
        except Exception as e:
            errors.append((name, e))
            print(f"[FINALLY] 收尾项 {name} 失败：{e!r}", file=sys.stderr)
    # ★★ 先把**每一个**失败的上下文落盘（★ 不吞的第一步）
    if errors:
        (out_dir / "finalize_errors.txt").write_text(
            "★ QC157:4 · 收尾项异常（★ 未吞，★ 跑完全部项后原样重抛）\n"
            + "\n".join(f"- 收尾项 {n}：{type(e).__name__}: {e!r}"
                        for n, e in errors),
            encoding="utf-8")
        raise errors[0][1]          # ★★ 原样重抛第一个（★ 不吞）


def write_finalize_error(rec: Recorder, exc: BaseException,
                         out_dir: Path | None = None) -> None:
    """★ 落盘**原始异常**（`QC157:4`）：类型 + 位置 + 留痕 + 原始消息。"""
    if out_dir is None:
        out_dir = WORKDIR
    import traceback
    tb = traceback.extract_tb(exc.__traceback__)
    where = tb[-1].filename + ":" + str(tb[-1].lineno) if tb else "未知"
    rec.add("ERROR", "exception_type", type(exc).__name__, where)
    rec.add("ERROR", "exception_repr", repr(exc), where,
            note="★★ QC157:4：★ 原始异常**如实落盘**（★ 不吞）")
    rec.add("ERROR", "exception_message", str(exc), where,
            note="★★ QC157:4：★ 原始异常消息原样保留（★ 不吞）")
    rec.add("ERROR", "traceback", "".join(traceback.format_exception(exc)),
            "script:traceback")
    (out_dir / "error.txt").write_text(
        "★ QC157:4 · 原始异常（★ 未被吞掉，★ 收尾后重新抛出）\n"
        f"type = {type(exc).__name__}\n"
        f"where = {where}\n"
        f"repr = {exc!r}\n"
        + "".join(traceback.format_exception(exc)),
        encoding="utf-8")


def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,
                              out_dir: Path) -> dict | None:
    """★★★ `QC162:W7`：★ 在**还原之前**把本趟跑后的 `except.txt` 原件
    （★ 与五个载体件的跑后状态）**另存一份证据副本**进 `--out-dir`。

    ★★ 理由（外部裁定指出）：旧执行序 `restore_carrier` 第一、
      `except_set_diff` 第三 ⇒ ★ `_restore` 先把跑前旧件写回载体，
      `_except_diff` 再读时读到的**已是旧内容** ⇒ ★★ 本趟新产生的
      `except.txt` 崩溃证据被覆盖、集合差失去意义。
    ★★ 故本函数**必须先于** `restore_carrier` 执行，且副本落
      **运行期写域**（★ 还原之后仍存在、可复核）。
    ★ 返回证据元信息（`None` = 载体 `except.txt` 不存在）。
    """
    src = carrier_dir / "except.txt"
    if not src.exists():
        rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
                note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
        return None
    blob = src.read_bytes()
    h = hashlib.sha256(blob).hexdigest()
    dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
    dst.write_bytes(blob)
    info = {"source": str(src), "evidence_path": str(dst),
            "size": len(blob), "sha256": h,
            "note": "★ QC162:W7：还原**之前**取的跑后原件副本"
                    "（☆ 还原之后仍存在、可复核）"}
    rec.add("EXCEPT", "evidence_copy", info, f"{src}:file",
            note="★★ 跑后 except.txt 原件副本（先于 restore_carrier）")
    # ★ 跑后载体件快照（★ 供"证据先于还原"复核：证明取的是跑后状态）
    files: dict = {}
    for name in CARRIER_FILES:
        p = carrier_dir / name
        files[name] = ({"path": str(p), "size": p.stat().st_size,
                        "sha256": sha256_file(p)} if p.exists() else None)
    (out_dir / "carrier_post_state.json").write_text(
        json.dumps(files, ensure_ascii=False, indent=1), encoding="utf-8")
    rec.add("EXCEPT", "carrier_post_state_path",
            str(out_dir / "carrier_post_state.json"), "script:copy_post_except_evidence")
    return info


# ===========================================================================
# §13-B · ★★★ 第 1 项：载体**真实所有权** · 证据搬出验 SHA ·
#          删除**前**不可变清单 · 趟后删除链 · 最终 `MANIFEST.json`
#   ★ 依据 `EXTERNAL_RULING_PI_FIX_AUTH_3.md` §1 第 1 项 / §2 / §3.5：
#     ★ 真实新建/交接证明；★ 完整删除前清单；★ 证据移出并验 SHA；
#     ★ 安全删除及结果复核；★ **不得**因补删除链取得删除共享历史件的权限；
#     ★ 所有权不成立应在**启动前**拒绝，不能先跑后发现无权删。
# ===========================================================================
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400


def _dump_json(obj) -> str:
    """★ 确定序列化（★ `sort_keys` + 固定缩进）⇒ ★ 外部可复算文件哈希。"""
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)


def _norm_path(p) -> str:
    """★ 比对用规范化路径（★ normcase + abspath + 去尾部分隔符）。"""
    s = os.path.normcase(os.path.abspath(str(p)))
    return s.rstrip("\\/") or s


def path_is_reparse(p: Path) -> bool:
    """★ 是否重解析点（联接/符号链接）⇒ ★ 不可当作本趟排他副本。

    ★★ 不可判定（`lstat` 失败）⇒ **保守返回 True**（fail-closed）。
    """
    try:
        at = os.lstat(str(p)).st_file_attributes
    except Exception:
        return True
    return bool(at & FILE_ATTRIBUTE_REPARSE_POINT)


def path_parts(name) -> list:
    """★★ 按**两种**分隔符切分路径段（★ 去掉空段与 `.`）。

    ★★ QC176 / v6 §6.1.1 U-3：★ **不能只按 `os.sep` 切**。
      ★ Windows 下 `os.sep == "\\"`，则 `"../outside.dat".split(os.sep)`
        得 `["..", "outside.dat"]` —— 看似能查出 `..`；
      ★ 但如果 `os.sep` 为 `/`（POSIX 或手工拼串），`"..\\outside.dat"` 就
        **不含**独立的 `..` 段 ⇒ ★ 可漏过越界件名。
      ★ 故此处**同时**按 `\\` 与 `/` 切分（★ 不依赖 `os.sep`）。
    """
    s = str(name).replace("/", "\\")
    return [seg for seg in s.split("\\") if seg not in ("", ".")]


def unsafe_path_name_reason(name) -> str | None:
    """★★ 判定不安全件名 ⇒ ★ 返回原因；★ `None` = 安全。

    ★★ QC176 / v6 §6.1.1 U-3：★ 统一两种分隔符，★ 拒绝两种分隔符下的越界名字。
    """
    s = str(name)
    if not s.strip():
        return "空件名"
    if s.strip() in (".", ".."):
        return "纯 . / .."
    if os.path.isabs(s) or (len(s) >= 2 and s[1] == ":"):
        return "绝对路径"
    if s.startswith("\\") or s.startswith("/"):
        return "根相对路径"
    if any(seg == ".." for seg in path_parts(s)):
        return "含 .. 上跳段"
    return None


def carrier_protected_exact_roots() -> list:
    """★★ **只保护根本身**的关键根（★ **不**连带其整棵子树）。

    ★★ QC176 / v6 §6.1.1 U-3：★ 原保护表把 **ROOT / LEAD 整体**纳入，
      ★ 后代排除又无区别施用于全部保护根 ⇒
      ★ `WORKDIR/carrier_trip/carrier_*`（★ 本趟**批准**域内新建的执行副本）
        以及其它批准 lead 趟域内载体，**一律**是 ROOT/LEAD 的后代
        ⇒ ★ `boundary.ok=False`（★ 批准趟域被自己的边界误杀）。
      ★ 故 ROOT / LEAD **只**作**精确命中**排除（★ 删根本身仍拒绝），
        ★ **不再**排除其后代。
    """
    return [_norm_path(x) for x in (ROOT, LEAD)]


def carrier_protected_subtrees() -> list:
    """★★ **真正受保护的子树**（★ 根与其**全部后代**均受保护）。

    ★ 母本（BENCH）/ 有理原树（YOULI）/ 历史树（qc63c_finish 及其 carrier）/
      本卡目录（qc151_u0400_trip）/ 证据树（WORKDIR/evidence）/ 备份（BACKUP_DIR）。
    ★★ 注意：★ **不含** ROOT 与 LEAD 本身（★ 见 `carrier_protected_exact_roots`）。
    """
    return [_norm_path(x) for x in (
        BENCH, YOULI,
        LEAD / "qc63c_finish", LEAD / "qc63c_finish" / "carrier",
        LEAD / "qc151_u0400_trip", WORKDIR / "evidence", BACKUP_DIR,
    )]


def carrier_approved_roots() -> list:
    """★★ 本趟**批准**的载体域（★ 每次现算）。

    ★★ QC176 / v6 §6.1.1 U-3：★ 原实现「反过来没有强制外部 carrier/out-dir
      位于本趟批准域」⇒ ★ 此处**正向**要求载体目录必须落在本趟写域内。
    """
    return [_norm_path(WORKDIR / "carrier_trip"), _norm_path(WORKDIR)]


def carrier_protected_roots() -> list:
    """★ 排除名单全表（★ 每次现算，不缓存）＝ 精确根 ∪ 受保护子树。

    ★★ 仅供**留痕/外部核对**；★ 判定请用上面两个分表（★ 语义不同）。
    """
    return list(carrier_protected_exact_roots()) + list(carrier_protected_subtrees())


def path_within(child, parent) -> bool:
    """★ `child` 是否**真的**在 `parent` 内（★ 同一规范化键域；★ 不含自身）。"""
    c = _norm_path(child)
    p = _norm_path(parent)
    return c.startswith(p + os.sep)


def check_per_layer_ancestors(path_str: str) -> dict:
    """★★ QC179 / v7 §2.1 U-3：★ 逐层原始祖先检查（★ 不只叶节点 reparse）。

    ★ 从 `path_str` 的**直接父级**向上遍历到根，★ 每层 `lstat` 检查重解析点。
    ★ 任何一层是联接/符号链接 ⇒ `reparse_layer` 非 None ⇒ 边界不过。
    ★ 不可判定（`lstat` 失败）⇒ fail-closed（`truncated=True`）。
    """
    layers: list = []
    reparse_layer = None
    truncated = False
    cur = os.path.dirname(path_str)
    while cur and cur != os.path.dirname(cur):
        layers.append(cur)
        try:
            st = os.lstat(cur)
            if hasattr(st, 'st_file_attributes'):
                if bool(st.st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT):
                    reparse_layer = cur
                    break
        except Exception:
            truncated = True
            break
        cur = os.path.dirname(cur)
    return {"layers_checked": len(layers), "reparse_layer": reparse_layer,
            "truncated": truncated}


def check_carrier_boundary(carrier_dir: Path) -> dict:
    """★★ 身份与路径边界复核（★ 进入运行**前**与删除**前**都重新核）。

    ★ 排除：关键根 / 母本 / 历史树 / 证据树 / 相互包含 / 路径别名 / 重解析点。
    ★★ QC176 / v6 §6.1.1 U-3（★ 三条）：
      1. ★ **区分**「关键根本身」（ROOT/LEAD，★ 只精确命中）与
         「真正受保护子树」（★ 根与后代都排除）⇒ ★ 不再误封批准趟域；
      2. ★ **正向**要求载体落在本趟**批准域**内（★ 外部 `--carrier` 亦然）；
      3. ★ 后代/包含比较统一使用 `_norm_path`（★ normcase + abspath）。
    """
    ap = os.path.abspath(str(carrier_dir))
    rp = os.path.realpath(str(carrier_dir))
    n = _norm_path(ap)
    res = {"given": str(carrier_dir), "abspath": ap, "realpath": rp,
           "alias_free": (_norm_path(ap) == _norm_path(rp)),
           "reparse_point": path_is_reparse(Path(carrier_dir)),
           "is_dir": os.path.isdir(str(carrier_dir)),
           "protected_hit": None, "contains_protected": None,
           # ★★ QC179 / v7 §2.1 U-3：★ approved_domain 用**独立固定参照**
           #   （★ DEFAULT_OUT_DIR = 批准常量），★ 不再 = 可被 --out-dir 改写的 WORKDIR。
           "approved_domain": _norm_path(DEFAULT_OUT_DIR),
           "in_approved_domain": None,
           "per_layer_ancestors": check_per_layer_ancestors(ap)}
    _is_descendant_of_protected = None
    # ★★ (1a) 关键根**本身**：★ 只精确命中，★ **不**连带后代
    for root in carrier_protected_exact_roots():
        if n == root:
            res["protected_hit"] = root
        if root.startswith(n + os.sep):
            res["contains_protected"] = root
    # ★★ (1b) 真正受保护**子树**：★ 根与后代都排除
    for root in carrier_protected_subtrees():
        if n == root:
            res["protected_hit"] = root
        if root.startswith(n + os.sep):
            res["contains_protected"] = root
        if n.startswith(root + os.sep):
            _is_descendant_of_protected = root
    res["is_descendant_of_protected"] = _is_descendant_of_protected
    # ★★ (2) 正向批准域：★ 载体必须落在 WORKDIR（本趟写域）内
    res["in_approved_domain"] = bool(
        n == res["approved_domain"]
        or path_within(n, res["approved_domain"]))
    _pla = res["per_layer_ancestors"]
    res["ok"] = bool(res["alias_free"] and not res["reparse_point"]
                     and res["is_dir"] and res["protected_hit"] is None
                     and res["contains_protected"] is None
                     and _is_descendant_of_protected is None
                     and res["in_approved_domain"]
                     and _pla.get("reparse_layer") is None
                     and not _pla.get("truncated", False))
    if res["ok"]:
        res["reason"] = ""
    else:
        reasons = []
        if not res["alias_free"]:
            reasons.append("★ realpath ≠ abspath（路径别名/链接）")
        if res["reparse_point"]:
            reasons.append("★ 是重解析点（联接/符号链接）")
        if not res["is_dir"]:
            reasons.append("★ 不是目录")
        if res["protected_hit"]:
            reasons.append(f"★ 命中排除根 {res['protected_hit']}")
        if res["contains_protected"]:
            reasons.append(f"★ 包含排除根 {res['contains_protected']}")
        if res.get("is_descendant_of_protected"):
            reasons.append(f"★ 是排除根 {res['is_descendant_of_protected']} 的后代")
        if not res["in_approved_domain"]:
            reasons.append(f"★ 不在本趟批准域 {res['approved_domain']} 内")
        if _pla.get("reparse_layer"):
            reasons.append(f"★ 祖先层含重解析点：{_pla['reparse_layer']}")
        if _pla.get("truncated"):
            reasons.append("★ 祖先枚举不可判定（lstat 失败）⇒ fail-closed")
        res["reason"] = "；".join(reasons)
    return res


def dir_identity_stamp(p) -> dict:
    """★★ 目录**对象身份**基线（★ `st_dev` + `st_ino` + realpath）。

    ★★ QC176 / v6 §6.1.1 U-4：★ 删除**前**必须复核**同一目录对象**，
      ★ 防止「同路径目录被替换」后误删他人对象。
      ★ 不可读 ⇒ **fail-closed**（`ok=False`）。
    """
    try:
        st = os.stat(str(p))
    except Exception as e:
        return {"ok": False, "error": repr(e), "st_dev": None, "st_ino": None,
                "realpath": None, "is_dir": False}
    try:
        rpp = os.path.realpath(str(p))
    except Exception as e:                                    # pragma: no cover
        return {"ok": False, "error": repr(e), "st_dev": int(st.st_dev),
                "st_ino": int(st.st_ino), "realpath": None, "is_dir": False}
    return {"ok": True, "error": None, "st_dev": int(st.st_dev),
            "st_ino": int(st.st_ino), "realpath": rpp,
            "is_dir": bool(os.path.isdir(str(p)))}


def same_dir_object(base: dict | None, now: dict) -> bool:
    """★★ 同一目录对象判定（★ `st_dev` + `st_ino` 全等且均 ok）。"""
    if not base or not isinstance(base, dict):
        return False
    if not base.get("ok") or not now.get("ok"):
        return False
    return (base.get("st_dev") is not None
            and base.get("st_ino") is not None
            and int(base["st_dev"]) == int(now["st_dev"])
            and int(base["st_ino"]) == int(now["st_ino"]))


def tree_relative_key(root: Path, p: Path) -> str:
    """★★ **相对**键（★ 统一用 `/` 作分隔符，★ 母本与载体**同一键域**）。

    ★★ QC176 / v6 §6.1.1 U-2：★ 原清单键为**绝对路径**，
      ★ 母本树与载体树**根不同** ⇒ ★ 键集合无交集
      ⇒ ★ 同一相对文件同时被计为 `added` 与 `removed`，
      ★ `modified` **永远不成立**。
    """
    try:
        rel = os.path.relpath(str(p), str(root))
    except Exception:
        rel = str(p)
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    return rel


def sha256_dir_tree(root: Path, walk_errors: list | None = None) -> dict:
    """★ **完整递归**逐件 sha256（★ 删除前清单用；★ 空树如实返回空）。

    ★★ QC176 / v6 §6.1.1 U-2：★ 键为**相对**路径（★ 与母本同一键域），
      ★ 绝对路径另存于值内 `path` 字段（★ 留痕不丢失）。
    ★★ QC179 / v7 §2.1 U-2：★ `os.walk` 传 `onerror` —— 遍历被拒子树
      ★ 不再被跳过而不生成逐件 error（★ 原 :1876 无 onerror 的缺口）。
    """
    out: dict = {}
    if not os.path.isdir(str(root)):
        return out
    _errs: list = walk_errors if walk_errors is not None else []
    def _onerror(err: Exception) -> None:
        _errs.append({"error": repr(err),
                      "path": getattr(err, "filename", None)})
    for dirpath, dirnames, filenames in os.walk(str(root), onerror=_onerror):
        dirnames.sort()
        filenames.sort()
        for fn in filenames:
            p = Path(dirpath) / fn
            k = tree_relative_key(root, p)
            try:
                out[k] = {"path": str(p), "size": p.stat().st_size,
                          "sha256": sha256_file(p)}
            except Exception as e:
                # ★★ 哈希不可读 ⇒ **如实记 error**（★ 不用 null==null 冒充成功）
                out[k] = {"path": str(p), "size": None, "sha256": None,
                          "error": repr(e)}
    return out


def create_isolated_carrier(rec: Recorder, src_dir: Path, trip_root: Path,
                            names) -> tuple:
    """★★ 在本趟写域内**排他新建**唯一执行目录（★ **真实创建证明**）。

    ★★ 逐件：读源字节 ⇒ `write_bytes` 写入新副本 ⇒ **复读副本验 SHA**
      （★ 与源逐件相等；★ 不等即抛 ⇒ 不回落共享目录启动，§2.2）。
    ★★ 只用**真实字节**复制：★ 不建符号链接 / 联接 / 硬链接伪隔离（§2.2）。
    ★ 目录用 `os.mkdir`（★ 已存在即抛 ⇒ 证明本趟**新建**、未复用旧件）。
    ★★ 本副本**不是** `carrier_bak`（§2.3）：★ 它是唯一的本趟执行载体，
      ★ 不另造整套备份、不复制无关历史证据。
    ★ 返回 `(carrier_dir, receipt)`；★ 失败抛异常（★ 由调用方收口）。
    """
    src_dir = Path(src_dir)
    if not src_dir.is_dir():
        raise RuntimeError(f"★ 源目录不存在/不是目录：{src_dir}")
    trip_root = Path(trip_root)
    trip_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H%M%S%f")          # QC193/D-117: 缩短载体名（gamemd 路径≥141 缺陷；微秒+pid 仍唯一）
    carrier_dir = trip_root / f"c_{stamp}_{os.getpid()}"
    # ★★ [PATHLEN] **载体清单构建处**的硬门禁（★ 在 `os.mkdir` **之前**判
    #   ⇒ ★ 超门禁时**不留下**半个载体目录）。
    #   ★ 判据 = 载体**目录**长度（★ 不含件名；★ 口径裁决见模块头 `[PATHLEN]` 段）。
    carrier_pathlen_gate([carrier_dir], "create_isolated_carrier", rec)
    os.mkdir(str(carrier_dir))          # ★ 排他：已存在即抛（★ 不复用旧件）
    # ★★ QC176 / U-4：★ **创建时**登记目录**对象身份**基线
    #   （★ `st_dev` + `st_ino`）⇒ ★ 删除前据此复核**同一对象**，
    #   ★ 排除「同路径目录被替换」的情形。
    # ★★ QC179 / v7 §2.1 U-4：★ **提前到 mkdir 成功后、复制循环前**
    #   （★ 原 :1943 在整段复制之后 ⇒ 部分创建异常时无完整基线）。
    _ident = dir_identity_stamp(carrier_dir)
    TRIP_CARRIER["identity"] = _ident
    # ★★ mkdir 成功**立即**登记 ⇒ ★ 后续复制失败也纳入 finally 回收（§2.4）
    TRIP_CARRIER["dir"] = str(carrier_dir)
    files: dict = {}
    _base_n = _norm_path(carrier_dir)
    for name in names:
        # ★★ QC176 / v6 §6.1.1 U-3：★ **两种分隔符都归一**再判
        #   （★ 原 `".." in name.split(os.sep)` 在 `os.sep` 为 `/` 时，
        #    `"..\\outside.dat"` **不含**独立 `..` 段 ⇒ 可漏过）。
        _why = unsafe_path_name_reason(name)
        if _why is not None:
            raise RuntimeError(f"★ 拒绝不安全件名：{name!r}（{_why}）")
        s = src_dir / name
        if not s.exists():
            # ★ [CARRIERFIX 20261020] F3：源件缺失**必须留痕**（原实现静默 continue）
            files[name] = None
            rec.add("CARRIER", "missing_source_file", {
                "name": name,
                "name_repr": repr(name),
                "source": str(s),
            }, "script:create_isolated_carrier",
                    note="★ CARRIERFIX：请求的件在源目录中不存在（可能是编码错乱或真缺件）")
            continue
        s_sha = sha256_file(s)
        d = carrier_dir / name
        # ★★ QC176 / v6 §6.1.1 U-3：★ 核**实际目的边界**
        #   （★ 不只看件名；★ 任何解析后落到 carrier 之外的目的路径一律拒绝）
        _d_n = _norm_path(d)
        if not (_d_n == _base_n or _d_n.startswith(_base_n + os.sep)):
            raise RuntimeError(f"★ 拒绝越界目的路径：{d}（不在 {carrier_dir} 内）")
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_bytes(s.read_bytes())        # ★ 真实字节（★ 非链接）
        d_sha = sha256_file(d)               # ★ 复读验 SHA
        if d_sha != s_sha:
            raise RuntimeError(f"★ 复制校验失败：{name} 源 {s_sha} ≠ 副本 {d_sha}")
        files[name] = {"src": str(s), "dst": str(d), "size": d.stat().st_size,
                       "sha256_src": s_sha, "sha256_dst": d_sha}
    # ★★ QC179 / v7 §2.1 U-4：★ 身份已在 mkdir 后登记（见上方）；
    #   ★ 此处 _ident 仍引用同一对象（★ 不重取，以免复制中途对象被替换）。
    receipt = {
        "created_by_this_trip": True,
        "carrier_dir": str(carrier_dir),
        "parent_root": str(trip_root),
        "source_dir": str(src_dir),
        "created_at": now_iso(), "trip_pid": os.getpid(),
        "exclusive_mkdir": True,
        "copy_method": "read_bytes→write_bytes（真实字节，★ 非链接/硬链接）",
        # ★★ U-4：★ **唯一趟身份**（★ 交接须绑定本趟；★ 不自造空值放行）
        "trip_id": TRIP_ID,
        # ★★ U-4：★ **目录对象身份**（★ 缺基线不得放行删除）
        "identity": _ident,
        "files": files,
        # ★ [CARRIERFIX 20261020] F1：未复制的件（None）必须算失败。
        #   原式 `all(... if v)` 跳过 None ⇒ 87/88 件却报 verified=True（E1 实证）。
        "files_verified": all(
            v is not None and v.get("sha256_src") == v.get("sha256_dst")
            for v in files.values()),
        # ★ [CARRIERFIX 20261020] F2：明列未复制的件名（人读；原实现静默吞掉）。
        "files_missing": sorted(n for n, v in files.items() if v is None),
        "files_requested": len(files),
        "files_copied": sum(1 for v in files.values() if v is not None),
    }
    rp = Path(WORKDIR) / "carrier_creation_receipt.json"
    rp.write_text(_dump_json(receipt), encoding="utf-8")
    TRIP_CARRIER["receipt"] = receipt
    rec.add("CARRIER", "created_by_this_trip", True,
            "script:create_isolated_carrier")
    rec.add("CARRIER", "creation_receipt_path", str(rp),
            "script:create_isolated_carrier")
    return carrier_dir, receipt


def assess_carrier_ownership(carrier_dir: Path, out_dir: Path, rec: Recorder,
                             handover: Path | None = None,
                             created_receipt: dict | None = None,
                             skip_file_hashes: bool = False) -> dict:
    """★★ 真实所有权判据（★ **只有**「本趟创建」或「受控交接」成立）。

    ★★ `A created_by_this_trip`：★ `created_receipt` 由**本次运行**的
      `create_isolated_carrier()` 产生 ⇒ ★ 逐件复核 receipt 里每个 sha 在
      盘上**仍相等**，★ 且路径 == receipt.carrier_dir，★ 且边界校验通过。
    ★★ `B handover`：★ 由 `--carrier-handover` 显式给出的**交接证明** JSON
      （★ 须含 `carrier_dir` / `exclusive_for_trip: true` /
      `files{name:{sha256}}`）⇒ ★ 逐件复核盘上 sha，★ 且边界校验通过。
    ★★ **一律不算**（§2.5 / §4.5）：目录时间戳、脚本自写 marker、
      路径"看起来像"、事先准备好的共享目录。
    ★ `owned=False` ⇒ 调用方**启动前拒绝**（★ 不能先跑后发现无权删）。

    ★★ QC176 / v6 §6.1.1 U-4（★ 补三条）：
      1. ★ **receipt 值为 `None` 不再跳过**：★ 必需件 ⇒ **判失败**；
         ★ 非必需件 ⇒ 如实记「源件缺失 ⇒ 未复制 ⇒ 未测」（★ 不以 null 冒充成功）。
      2. ★ **交接件自身**须落在本趟批准域内（★ 不接受任意位置的自写声明）。
      3. ★ **可信交接主体 + 唯一趟身份**：★ 交接须含非空
         `handover_from` / `handover_to` / `trip_id`，
         ★ 且 `trip_id` 必须与本运行 `TRIP_ID` **完全一致**（★ 绑定本趟）。
      ★ 交接件中每个**相对件名**也须通过 `unsafe_path_name_reason()`
        与「实际目的在 carrier 内」两项边界验证。
    """
    carrier_dir = Path(carrier_dir)
    b = check_carrier_boundary(carrier_dir)
    res = {"carrier_dir": str(carrier_dir), "owned": False, "basis": "none",
           "boundary": b, "boundary_ok": bool(b["ok"]), "checked_at": now_iso(),
           "files_checked": {}, "files_match": None,
           "receipt_path": None, "refuse_reason": None}

    def _fail(msg: str) -> dict:
        res["refuse_reason"] = msg
        return res

    if not b["ok"]:
        return _fail(f"★ 边界校验不通过：{b['reason']}")
    if created_receipt is not None:
        if _norm_path(created_receipt.get("carrier_dir", "")) != _norm_path(carrier_dir):
            return _fail("★ receipt.carrier_dir 与实际载体目录不一致")
        if created_receipt.get("created_by_this_trip") is not True:
            return _fail("★ receipt 未声明 created_by_this_trip=True")
        rc_files = created_receipt.get("files")
        if not rc_files or not isinstance(rc_files, dict):
            return _fail("★ receipt files 缺失/空/非字典 ⇒ 所有权不成立")
        essential = {"except.txt"} | set(CARRIER_FILES)
        missing_in_receipt = essential - set(rc_files.keys())
        if missing_in_receipt:
            return _fail(f"★ receipt 缺必需件：{sorted(missing_in_receipt)}")
        mism: list = []
        if skip_file_hashes:
            # ★★ QC179 / v7 §2.1 U-4：★ 删除前重验**跳过文件哈希比较**
            #   （★ 合法运行可改变 except.txt 等 ⇒ 内容 ≠ 创建时字节
            #    ⇒ 不以"仍等于创建时所有字节"替代对象所有权）。
            #   ★ 仅验证结构：receipt 字段 + 目录存在 + 必需件列出。
            res["file_hashes_skipped"] = True
            res["files_match"] = None
            res["note"] = ("★ QC179/U-4：★ 删除前重验跳过文件哈希"
                          "（★ 合法运行可改变内容；★ 以目录身份+边界+证明为准）")
        else:
            for name, v in rc_files.items():
                if v is None:
                    if name in essential:
                        mism.append(name)
                    else:
                        res["files_checked"][name] = {
                            "expect": None, "actual": None, "match": None,
                            "note": "★ receipt 值为 None（源件缺失）⇒ 未复制 ⇒ 未测"}
                    continue
                p = carrier_dir / name
                if not p.exists():
                    mism.append(name)
                    continue
                h = sha256_file(p)
                res["files_checked"][name] = {"expect": v["sha256_dst"], "actual": h,
                                              "match": (h == v["sha256_dst"])}
                if h != v["sha256_dst"]:
                    mism.append(name)
            res["files_match"] = (len(mism) == 0)
            if mism:
                return _fail(f"★ receipt 逐件 sha 复核不符：{mism}")
        res["owned"] = True
        res["basis"] = "created_by_this_trip"
        res["receipt_path"] = str(Path(out_dir) / "carrier_creation_receipt.json")
        return res
    if handover is not None:
        hp = Path(handover)
        if not hp.exists():
            return _fail(f"★ 交接证明不存在：{hp}")
        # ★★ QC176 / v6 §6.1.1 U-4：★ **交接件自身**也须落在本趟批准域内
        #   （★ 不能接受来自任意位置的自写声明 ⇒ 拒绝"只凭自写声明"）。
        if not (_norm_path(hp) == _norm_path(WORKDIR)
                or path_within(hp, WORKDIR)):
            return _fail(f"★ 交接证明不在本趟批准域 {_norm_path(WORKDIR)} 内：{hp}")
        try:
            hv = json.loads(hp.read_text(encoding="utf-8"))
        except Exception as e:
            return _fail(f"★ 交接证明不可解析：{e!r}")
        if not isinstance(hv, dict):
            return _fail("★ 交接证明不是 JSON 对象 ⇒ 所有权不成立")
        if _norm_path(hv.get("carrier_dir", "")) != _norm_path(carrier_dir):
            return _fail("★ 交接证明的 carrier_dir 与实际载体目录不一致")
        if hv.get("exclusive_for_trip") is not True:
            return _fail("★ 交接证明未声明 exclusive_for_trip=True")
        # ★★ QC176 / v6 §6.1.1 U-4：★ **唯一趟身份约束** —— 交接须绑定本趟
        #   （★ `TRIP_ID` 由 `--trip-id` 显式给定；★ 未给定 ⇒ 随机值必然不符）。
        hv_trip = hv.get("trip_id")
        if not isinstance(hv_trip, str) or not hv_trip.strip():
            return _fail("★ 交接证明缺 trip_id（★ 无法绑定本趟）⇒ 所有权不成立")
        if hv_trip.strip() != TRIP_ID:
            return _fail(f"★ 交接证明 trip_id={hv_trip!r} 与本趟 TRIP_ID={TRIP_ID!r} 不符")
        # ★★ U-4：★ **可信交接主体**（★ 须明列受让方/移交方，★ 不得留空）
        hv_from = hv.get("handover_from")
        hv_to = hv.get("handover_to")
        if not (isinstance(hv_from, str) and hv_from.strip()):
            return _fail("★ 交接证明缺 handover_from（★ 无可信移交主体）")
        if not (isinstance(hv_to, str) and hv_to.strip()):
            return _fail("★ 交接证明缺 handover_to（★ 无可信受让主体）")
        hv_files = hv.get("files")
        if not hv_files or not isinstance(hv_files, dict):
            return _fail("★ 交接证明 files 缺失/空/非字典 ⇒ 所有权不成立")
        essential = {"except.txt"} | set(CARRIER_FILES)
        missing_in_handover = essential - set(hv_files.keys())
        if missing_in_handover:
            return _fail(f"★ 交接证明缺必需件：{sorted(missing_in_handover)}")
        mism = []
        _hb = _norm_path(carrier_dir)
        for name, v in hv_files.items():
            # ★★ U-4：★ **交接件中的相对件名**也须完整边界验证
            _why = unsafe_path_name_reason(name)
            if _why is not None:
                mism.append(name)
                continue
            p = carrier_dir / name
            _pn = _norm_path(p)
            if not (_pn == _hb or _pn.startswith(_hb + os.sep)):
                mism.append(name)
                continue
            want = (v or {}).get("sha256")
            if (want is None) or (not p.exists()):
                mism.append(name)
                continue
            h = sha256_file(p)
            res["files_checked"][name] = {"expect": want, "actual": h,
                                          "match": (h == want)}
            if h != want:
                mism.append(name)
        res["files_match"] = (len(mism) == 0)
        if mism:
            return _fail(f"★ 交接证明逐件 sha 复核不符：{mism}")
        res["owned"] = True
        res["basis"] = "handover"
        res["receipt_path"] = str(hp)
        # ★★ QC179 / v7 §2.1 U-4：★ 交接成功**立即登记**目录对象身份基线
        #   （★ 原实现交接成功不登记 ⇒ finally 传 None ⇒ 必因缺身份基线拒删）。
        TRIP_CARRIER["identity"] = dir_identity_stamp(carrier_dir)
        return res
    return _fail("★ 无本趟创建证明、也无受控交接证明 ⇒ 所有权不成立"
                 "（★ 目录时间戳 / 自写 marker / 路径形似**均不算**）")


# >>> EVIDDIFF-BEGIN helpers（嵌套哨兵：删本块=还原锚 5b435487…；--evid-diff
#     缺省 off ⇒ 本块仅定义常量与函数，零 IO、零副作用，行为与锚逐字节一致）
# ★★ EVID-DIFF（2026-10-19）：证据搬出**差异件模式**（CLI 旗标 `--evid-diff`）。
#   ★ 背景：每趟把载体全树（≈1.8GB）**全量**拷入 `evidence/<stamp>/` ⇒ 趟趟
#     重复磁盘税。先例 = 两遍哈希去重（同趟域 `evidence/_DEDUP_20261018.json`：
#     87GB→1.8GB）——逐趟变化件仅 RA2MD.INI / XMP29U2.MAP / yrm 槽位 /
#     ddraw.ini 变体等，游戏本体（*.mix / mph*.exe 等）逐趟恒定。
#   ★ 语义（on）：对**参照证据趟**逐件 sha256+size 对比 ⇒ **差异件才拷出**；
#     同时写 `evidence/<stamp>/MANIFEST.json`（全集逐件：relative / sha256 /
#     size / copied_this_trip / reference_stamp）＋ `README_REBUILD.md`
#     （重建命令附内）。必需件 `except.txt` **永远照拷**（不参与跳过）。
#   ★ 参照管理：`evidence/_EVID_REFERENCE.json`（指针文件，**内联**逐件
#     sha+size 清单 ⇒ 自洽）。指针缺失/损坏 ⇒ 本趟**回退全量**并把本趟记为
#     新参照（首趟全量，之后差异）；已有参照 ⇒ **冻结不滚动**（防旧趟按旧
#     参照记账后重建失据）；重锚 = 手动删除该指针文件（README 同款说明）。
#   ★ 跳过判据（**全部**成立才跳过）：旗标 on ∧ 参照清单含同 rel 项 ∧ 其
#     sha256 与 size **全等** ∧ 参照趟盘上该件**现仍存在**（防参照被外部
#     清理后留空洞）。★ 源 sha 仍逐件全算（跳过只省**写盘**不省**读源**）。
#   ★ 安全面不变：末次全集复验 / 碰撞拒绝 / 必需件门控 / 退出码语义全部不变；
#     跳过件 `evidence_path=null`、`copied_this_trip=false` **如实**入清单与
#     趟记录（不以 null 冒充已存证）。
EVID_DIFF_POINTER_NAME = "_EVID_REFERENCE.json"
EVID_DIFF_MANIFEST_NAME = "MANIFEST.json"
EVID_DIFF_README_NAME = "README_REBUILD.md"
EVID_DIFF_SCHEMA = "qc151.evid-diff/1"
# ★ 运行期旗标容器（★ `main()` 由 `--evid-diff` 置位；★ 缺省 off；
#   ★ 同 `FINALIZE_CODE`/`CLEANUP_FAILURES` 的模块级容器房规 ⇒ finalize 侧可读）
EVID_DIFF_FLAG = {"on": False}


def _evid_ref_load(ev_dir: Path):
    """★ EVID-DIFF：读参照指针（内联清单）；缺失/损坏 ⇒ None（⇒ 回退全量）。"""
    try:
        obj = json.loads((Path(ev_dir) / EVID_DIFF_POINTER_NAME).read_text(
            encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    if not obj.get("reference_stamp") or not isinstance(obj.get("files"),
                                                        dict):
        return None
    return obj


def _evid_ref_entry_covers(ref: dict, rel: str, src_sha: str,
                           src_size: int) -> bool:
    """★ EVID-DIFF 跳过判据：参照同 rel 项 sha+size 全等 ∧ 参照盘上该件仍在。

    ★ 参照件在盘 = 存在性检查（不重算哈希——参照趟自证链在其自身指针/
      MANIFEST 内）；★ 参照件缺席 ⇒ 不覆盖 ⇒ 照常拷出（fail-safe：外部去重
      把参照趟清空时自动退回全量拷出，不报错、不留空洞）。
    """
    ent = (ref.get("files") or {}).get(rel)
    if not isinstance(ent, dict):
        return False
    if ent.get("sha256") != src_sha or ent.get("size") != src_size:
        return False
    ref_dir = ref.get("reference_evidence_dir")
    if not ref_dir:
        return False
    try:
        return (Path(str(ref_dir)) / str(rel).replace("/", os.sep)).is_file()
    except Exception:
        return False


def _evid_ref_record(ev_dir: Path, stamp: str, items: list) -> dict:
    """★ EVID-DIFF：把**本趟（全量趟）**记为参照——指针文件内联逐件清单。

    ★ 只收 `evidence_path` 非空且 `sha256_src` 非空且 `size` 非空的件
      （★ 存在性缺测件不入参照）。
    """
    files: dict = {}
    for it in items:
        if (it.get("evidence_path") and it.get("sha256_src")
                and it.get("size") is not None):
            files[str(it.get("relative"))] = {
                "sha256": it.get("sha256_src"), "size": it.get("size")}
    obj = {"schema": EVID_DIFF_SCHEMA, "reference_stamp": stamp,
           "reference_evidence_dir": str(Path(ev_dir) / stamp),
           "recorded": now_iso(), "entry_count": len(files),
           "files": files}
    pp = Path(ev_dir) / EVID_DIFF_POINTER_NAME
    pp.write_text(json.dumps(obj, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    return {"pointer": str(pp), "entry_count": len(files),
            "reference_stamp": stamp}


def _evid_write_manifest_and_readme(ev_dir: Path, stamp: str, mode: str,
                                    ref: "dict | None",
                                    items: list) -> dict:
    """★ EVID-DIFF：写 `MANIFEST.json`（全集逐件元数据）＋ `README_REBUILD.md`。

    ★ 仅旗标 on 时被调用 ⇒ 旗标 off ⇒ 证据树与锚**逐字节一致**（零新增文件）。
    ★ MANIFEST 逐件键：relative / sha256 / size / copied_this_trip /
      evidence_path / reference_stamp；★ mode = "full"（本趟即参照）| "diff"。
    ★ 写失败 ⇒ 返回值带 `manifest_error`/`readme_error`（★ 由调用方计入
      failed ⇒ 证据判失败，**不静默**）。
    """
    ref_stamp = None if ref is None else ref.get("reference_stamp")
    files: list = []
    for it in items:
        copied = bool(it.get("copied_this_trip"))
        files.append({"relative": it.get("relative"),
                      "sha256": it.get("sha256_src"),
                      "size": it.get("size"),
                      "copied_this_trip": copied,
                      "evidence_path": it.get("evidence_path"),
                      "reference_stamp": None if copied else ref_stamp})
    manifest = {"schema": EVID_DIFF_SCHEMA, "stamp": stamp, "mode": mode,
                "created": now_iso(), "trip_id": TRIP_ID,
                "reference": None if ref is None else
                {"stamp": ref_stamp,
                 "evidence_dir": ref.get("reference_evidence_dir"),
                 "entry_count": len(ref.get("files") or {})},
                "file_count": len(files),
                "copied_count": sum(1 for f in files
                                    if f["copied_this_trip"]),
                "files": files}
    stamp_dir = Path(ev_dir) / stamp
    outs: dict = {"mode": mode, "manifest_path": None, "readme_path": None,
                  "file_count": len(files),
                  "copied_count": manifest["copied_count"]}
    try:
        stamp_dir.mkdir(parents=True, exist_ok=True)
        mp = stamp_dir / EVID_DIFF_MANIFEST_NAME
        mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                      encoding="utf-8")
        outs["manifest_path"] = str(mp)
    except Exception as e:
        outs["manifest_error"] = repr(e)
    _sd = str(stamp_dir).replace("\\", "/")
    if ref is None:
        ref_line = "本趟即**参照全量基线**（无更早参照）"
        rebuild = ("robocopy \"" + _sd + "\" \"<目标目录>\" /E"
                   "   ★ 本目录已含全部证据件（全量）")
    else:
        _rd = str(ref.get("reference_evidence_dir")).replace("\\", "/")
        ref_line = ("参照趟（全量基底）= `" + _rd + "`（stamp="
                    + str(ref_stamp) + "）")
        rebuild = ("步骤1：robocopy \"" + _rd + "\" \"<目标目录>\" /E\n"
                   "步骤2（一条命令重建＝基底＋本趟差异件覆盖；尖括号占位按实际"
                   "改写；<本stamp目录> 即本 README 所在目录）：\n"
                   "python -c \"import json,shutil,pathlib; "
                   "s=pathlib.Path(r'<本stamp目录>'); "
                   "d=pathlib.Path(r'<目标目录>'); "
                   "m=json.loads((s/'MANIFEST.json').read_text("
                   "encoding='utf-8')); "
                   "shutil.copytree(m['reference']['evidence_dir'], d, "
                   "dirs_exist_ok=True); "
                   "[shutil.copy2(s/f['relative'], d/f['relative']) "
                   "for f in m['files'] if f['copied_this_trip']]\"")
    readme = (
        "# 证据重建说明（EVID-DIFF 差异件模式 · " + EVID_DIFF_SCHEMA + "）\n"
        "\n"
        "- 本目录 = 趟 `" + stamp + "` 的证据集（mode=**" + mode + "**）。\n"
        "- " + ref_line + "。\n"
        "- 跳过件（copied_this_trip=false）**未落本目录**，凭参照趟同名件重建；"
        "其 sha256/size 同时入本目录 MANIFEST 与参照指针（`evidence/"
        + EVID_DIFF_POINTER_NAME + "`），两处可交叉复核。\n"
        "- 必需件 `except.txt` 每趟**必拷**（不参与跳过）。\n"
        "- 重建命令：\n" + rebuild + "\n"
        "- 参照冻结纪律：参照不随差异趟滚动；**重锚 = 删除 `evidence/"
        + EVID_DIFF_POINTER_NAME + "`**（下一趟 `--evid-diff` 即回退全量并成"
        "新参照）。\n"
        "- 完整性门：重建后逐件 sha256 与 MANIFEST.json 比对，**任一不符 ⇒ "
        "不得宣称重建成功**。\n")
    try:
        rp = stamp_dir / EVID_DIFF_README_NAME
        rp.write_text(readme, encoding="utf-8")
        outs["readme_path"] = str(rp)
    except Exception as e:
        outs["readme_error"] = repr(e)
    return outs


# <<< EVIDDIFF-END helpers


def move_out_evidence_and_verify(rec: Recorder, carrier_dir: Path,
                                 out_dir: Path) -> dict:
    """★★ 证据**先搬出**并**逐件验 SHA**（★ 删除**之前**必须完成）。

    ★★ U-2：★ **递归收集载体全树**所有文件（★ 不只固定 CARRIER_FILES 五件）。
      ★ 必需件 `except.txt` 不存在 ⇒ **失败**（★ 不以 null 冒充成功）。
      ★ 每件：搬出**前**算源 sha ⇒ 写入 `out_dir/evidence/` ⇒ **复读副本**算
      sha ⇒ ★ 两者不等即**失败**。
    ★★ QC176 / v6 §6.1.1 U-2（★ 补两条）：
      ★ **证据目的路径保结构**（★ 不再把分隔符全压成 `_`）
        ⇒ ★ 同一 stamp 下 `a/b.log` 与 `a_b.log` **不会**映成同一目的文件；
      ★ 另加**显式碰撞拒绝**（★ 规范化后重复即判失败，★ 含大小写折叠）；
      ★ 末次做**全集复验**（★ 重读盘上每一件证据副本 ⇒ 逐件比对源 sha、
        ★ 并核路径唯一与件数一致）。
    """
    ev_dir = Path(out_dir) / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    # >>> EVIDDIFF-BEGIN mode-prep（旗标 off ⇒ 本块零副作用、零记录，与锚等价）
    _ed_on = bool(EVID_DIFF_FLAG.get("on"))
    _ed_ref = _evid_ref_load(ev_dir) if _ed_on else None
    _ed_mode = None
    if _ed_on:
        # ★ 无参照（缺失/损坏）⇒ 回退全量并把本趟记为参照（首趟全量，之后差异）
        _ed_mode = "diff" if _ed_ref is not None else "full"
        rec.add("EVID", "evid_diff_mode",
                {"mode": _ed_mode,
                 "reference_stamp": (None if _ed_ref is None
                                     else _ed_ref.get("reference_stamp")),
                 "pointer": str(ev_dir / EVID_DIFF_POINTER_NAME)},
                "script:move_out_evidence_and_verify",
                note="★ EVID-DIFF：full=本趟回退全量并记为新参照；"
                     "diff=对既有参照做差异件")
    # <<< EVIDDIFF-END mode-prep
    items: list = []
    failed: list = []
    required_missing: list = []
    collisions: list = []
    seen: set = set()
    dst_seen: dict = {}
    carrier_p = Path(carrier_dir)
    all_sources: list = []
    if os.path.isdir(str(carrier_p)):
        for dp, dns, fns in os.walk(str(carrier_p)):
            dns.sort()
            fns.sort()
            for fn in fns:
                all_sources.append(Path(dp) / fn)
    except_src = carrier_p / "except.txt"
    if except_src not in all_sources:
        all_sources.insert(0, except_src)
    for s in all_sources:
        key = _norm_path(s)
        if key in seen:
            continue
        seen.add(key)
        # ★★ QC176：★ 统一**相对键域**（★ 与母本清单同一口径）
        rel = tree_relative_key(carrier_p, s)
        if rel.startswith("../") or rel == ".." or unsafe_path_name_reason(rel):
            rel = s.name
        is_required = (rel == "except.txt")
        if not s.exists():
            item = {"source": str(s), "relative": rel, "evidence_path": None,
                    "size": None, "sha256_src": None, "sha256_evidence": None,
                    "ok": None,
                    "note": "★ 源不存在 ⇒ 未测（★ 不以 null==null 冒充成功）"}
            if is_required:
                item["ok"] = False
                item["note"] = "★ 必需件不存在 ⇒ 失败"
                required_missing.append(rel)
                failed.append(str(s))
            items.append(item)
            continue
        try:
            src_sha = sha256_file(s)
            # >>> EVIDDIFF-BEGIN skip-decision（差异件模式：与参照同 rel 项
            #   sha256+size 全等 ∧ 参照盘上该件仍在 ∧ 非必需件 ⇒ 不拷出；
            #   ★ 源 sha 已全算，跳过只省**写盘**不省**读源**）
            if _ed_on and _ed_ref is not None and not is_required:
                _ed_size = s.stat().st_size
                if _evid_ref_entry_covers(_ed_ref, rel, src_sha, _ed_size):
                    items.append({"source": str(s), "relative": rel,
                                  "evidence_path": None,
                                  "size": _ed_size,
                                  "sha256_src": src_sha,
                                  "sha256_evidence": None, "ok": True,
                                  "copied_this_trip": False,
                                  "reference_stamp":
                                      _ed_ref.get("reference_stamp"),
                                  "note": "★ EVID-DIFF：与参照同 sha256+size"
                                          "且参照件在盘 ⇒ 不拷出（凭参照＋"
                                          "清单可重建；except.txt 除外）"})
                    continue
            # <<< EVIDDIFF-END skip-decision
            blob = s.read_bytes()
            # ★★ QC176 / U-2：★ **保相对路径结构**（★ 不再压平成 `_`）
            #   ⇒ ★ `a/b.log` → `<stamp>/a/b.log`、`a_b.log` → `<stamp>/a_b.log`
            dst = ev_dir / stamp
            for _seg in rel.split("/"):
                dst = dst / _seg
            _dst_key = _norm_path(dst)
            if _dst_key in dst_seen:
                # ★★ **显式碰撞拒绝**（★ 后件覆盖前件的漏洞由此堵住）
                collisions.append({"destination": str(dst),
                                   "first_source": dst_seen[_dst_key],
                                   "second_source": str(s)})
                items.append({"source": str(s), "relative": rel,
                              "evidence_path": str(dst), "size": None,
                              "sha256_src": src_sha, "sha256_evidence": None,
                              "ok": False,
                              "error": "★ 证据目的路径碰撞（★ 会覆盖已存证据）"})
                failed.append(str(s))
                continue
            dst_seen[_dst_key] = str(s)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(blob)
            dst_sha = sha256_file(dst)
            ok = (dst_sha == src_sha) and (dst.stat().st_size == len(blob))
        except Exception as e:
            items.append({"source": str(s), "relative": rel,
                          "evidence_path": None, "size": None,
                          "sha256_src": None, "sha256_evidence": None,
                          "ok": False, "error": repr(e)})
            failed.append(str(s))
            continue
        _item = {"source": str(s), "relative": rel,
                 "evidence_path": str(dst),
                 "size": dst.stat().st_size, "sha256_src": src_sha,
                 "sha256_evidence": dst_sha, "ok": bool(ok)}
        # >>> EVIDDIFF-BEGIN（旗标 on 才加键 ⇒ off 时记录与锚逐字节一致）
        if _ed_on:
            _item["copied_this_trip"] = True
        # <<< EVIDDIFF-END
        items.append(_item)
        if not ok:
            failed.append(str(s))
    # ★★ QC176 / U-2：★ **末次全集复验**（★ 重读**盘上**每一件证据副本）
    reverify = reverify_evidence_items(items)
    if not reverify["ok"]:
        # ★ 复验失败项为 dict（★ 含路径与原因）⇒ ★ 归一成**字符串**入 failed
        #   （★ 与逐件 failed 的字符串口径一致；★ 不可 dict.fromkeys ⇒ 会 TypeError）
        for _f in reverify["failed"]:
            _label = f"{_f.get('path')}｜{_f.get('reason')}"
            if _label not in failed:
                failed.append(_label)
    # >>> EVIDDIFF-BEGIN manifest+pointer（仅旗标 on；off ⇒ 零新增文件）
    _ed_extra = None
    if _ed_on:
        _ed_extra = _evid_write_manifest_and_readme(
            ev_dir, stamp, _ed_mode, _ed_ref, items)
        for _k in ("manifest_error", "readme_error"):
            if _k in _ed_extra:
                failed.append(f"evid_diff:{_k}｜{_ed_extra[_k]}")
        # ★ 只有本趟证据**完整且验毕全过**才允许把本趟记为新参照
        #   （full 模式；diff 模式参照冻结不滚动）
        if (_ed_mode == "full" and not failed and not required_missing
                and not collisions and bool(reverify["ok"])):
            _ed_extra["reference_recorded"] = _evid_ref_record(
                ev_dir, stamp, items)
    # <<< EVIDDIFF-END manifest+pointer
    res = {"evidence_dir": str(ev_dir), "items": items, "failed": failed,
           "required_missing": required_missing, "collisions": collisions,
           "final_reverify": reverify,
           "ok": (len(failed) == 0 and len(required_missing) == 0
                  and len(collisions) == 0 and bool(reverify["ok"]))}
    # >>> EVIDDIFF-BEGIN res-ext（旗标 on ⇒ 附写入摘要；off ⇒ res 与锚逐键一致）
    if _ed_on:
        res["evid_diff"] = _ed_extra
    # <<< EVIDDIFF-END res-ext
    rec.add("EVID", "evidence_move_out", res,
            "script:move_out_evidence_and_verify",
            note="★★ U-2：★ 递归收集载体全树 + 必需件缺失判失败"
                 "；★ QC176：★ 无碰撞目的路径 + 末次全集复验")
    return res


def reverify_evidence_items(items: list) -> dict:
    """★★ QC176 / v6 §6.1.1 U-2：★ 删除**前**对**证据全集**做末次复验。

    ★ 逐件：★ 证据路径非空且**存在** ⇒ ★ 重读盘上字节算 sha
      ⇒ ★ 与记录的 `sha256_src` 比对；★ 路径须**两两不同**（★ 防覆盖）。
    ★★ 这与"复制瞬间逐件 ok"不同：★ 后者无法发现**后件覆盖前件**，
      ★ 全集复验可以（★ 覆盖会使前件的盘上内容变成后件内容 ⇒ 比对失败）。
    """
    paths: list = []
    failed: list = []
    checked = 0
    for it in items or []:
        ep = (it or {}).get("evidence_path")
        if not ep:
            continue
        checked += 1
        paths.append(_norm_path(ep))
        try:
            h = sha256_file(Path(ep))
        except Exception as e:
            failed.append({"path": ep, "reason": f"★ 复读失败：{e!r}"})
            continue
        want = (it or {}).get("sha256_src")
        if want is None or h != want:
            failed.append({"path": ep, "reason": "★ 末次复验 sha ≠ 源 sha（★ 可能被覆盖/改写）"})
    dup = sorted({p for p in paths if paths.count(p) > 1})
    for p in dup:
        failed.append({"path": p, "reason": "★ 证据目的路径重复（★ 覆盖风险）"})
    return {"checked": checked, "unique_paths": len(set(paths)),
            "duplicate_paths": dup, "failed": failed,
            "ok": (len(failed) == 0)}


def _compute_mother_diff(mother_baseline: dict, carrier_tree: dict) -> dict:
    """★★ U-2：★ 母本基线与载体实际差异（增/删/改）。

    ★★ QC176 / v6 §6.1.1 U-2：★ 两侧键**同为相对路径域**
      （★ 由 `sha256_dir_tree` 统一产出）⇒
      ★ 相同相对文件**不再**同时被计为 `added` 与 `removed`，
      ★ `modified` 由此**可以成立**。
    ★★ 任一侧 sha 为 `None`（不可读）⇒ ★ **不**判为 modified（★ 记为 unreadable，
      ★ 由 `..._error_count` ⇒ 清单失败门控拒删，★ 不用 null 冒充相等）。
    """
    mb_keys = set(mother_baseline.keys())
    ct_keys = set(carrier_tree.keys())
    added = sorted(ct_keys - mb_keys)
    removed = sorted(mb_keys - ct_keys)
    modified: list = []
    unreadable: list = []
    for k in sorted(mb_keys & ct_keys):
        m_sha = (mother_baseline[k] or {}).get("sha256")
        c_sha = (carrier_tree[k] or {}).get("sha256")
        if m_sha is None or c_sha is None:
            unreadable.append(k)
            continue
        if m_sha != c_sha:
            modified.append(k)
    return {"added": added, "removed": removed, "modified": modified,
            "unreadable": unreadable,
            "key_domain": "relative（★ 母本与载体同一相对路径域）"}


def write_pre_delete_manifest(rec: Recorder, carrier_dir: Path, out_dir: Path,
                              ownership: dict, evidence: dict,
                              mother_baseline: dict | None = None) -> dict:
    """★★ 落**不可变**的删除**前**完整清单（★ 绝不覆盖、不事后重算，§1 第10项）。

    ★★ U-2：★ 逐件 error/null ⇒ 清单失败；★ 含母本基线与差异。
    ★★ QC176 / v6 §6.1.1 U-2（★ 补两条）：
      ★ **完整母本逐件基线**落**独立不可变文件** `carrier_mother_baseline.json`
        （★ 不再只存一个计数），★ 并在本清单中引用其**实盘 SHA**；
      ★ **母本错误也门控**：★ 母本缺失 / 非字典 / 空 / 含 error 或 null sha
        ⇒ ★ `manifest_ok=False` ⇒ ★ 由 U-1 门控**拒删**（★ 缺基线不得放行）。
    """
    tree = sha256_dir_tree(carrier_dir)
    tree_errors = [p for p, v in tree.items()
                   if v.get("error") is not None or v.get("sha256") is None]
    diff: dict = {}
    mother_path = None
    mother_sha = None
    mother_errors: list = []
    mother_status = "missing"
    if isinstance(mother_baseline, dict) and mother_baseline:
        mother_status = "ok"
        mother_errors = [k for k, v in mother_baseline.items()
                         if (v or {}).get("error") is not None
                         or (v or {}).get("sha256") is None]
        try:
            _mp = Path(out_dir) / "carrier_mother_baseline.json"
            _mp.write_text(_dump_json(mother_baseline), encoding="utf-8")
            mother_path = str(_mp)
            mother_sha = sha256_file(_mp)
        except Exception as e:
            mother_status = "write_failed"
            mother_errors = list(mother_errors) + [f"★ 母本基线落盘失败：{e!r}"]
        diff = _compute_mother_diff(mother_baseline, tree)
    elif mother_baseline is not None:
        mother_status = "invalid"
        mother_errors = ["★ 母本基线不是非空字典"]
    mother_ok = bool(mother_status == "ok" and len(mother_errors) == 0)
    manifest_ok = bool(len(tree_errors) == 0 and mother_ok)
    body = {
        "manifest_kind": "carrier_pre_delete",
        "created_at": now_iso(),
        "carrier_dir": str(carrier_dir),
        "carrier_boundary": check_carrier_boundary(carrier_dir),
        "ownership": {k: ownership.get(k) for k in
                      ("owned", "basis", "receipt_path", "files_match")},
        "evidence": evidence,
        # ★★ QC176：★ 完整母本逐件基线（★ 独立不可变文件 + 其实盘 SHA）
        "mother_baseline_path": mother_path,
        "mother_baseline_sha256": mother_sha,
        "mother_baseline_status": mother_status,
        "mother_baseline_file_count": (len(mother_baseline)
                                       if isinstance(mother_baseline, dict)
                                       else None),
        "mother_baseline_errors": mother_errors,
        "diff_from_mother": diff,
        "files": tree,
        "file_count": len(tree),
        "tree_errors": tree_errors,
        "manifest_ok": manifest_ok,
        "note": "★ U-2：★ 删除**前**完整递归逐件 sha256；★ error/null ⇒ 清单失败；"
                "★ 不可变（★ 不覆盖、不重算）"
                "；★ QC176：★ 母本与载体同一相对键域 + 完整母本基线 + 母本错误门控",
    }
    p = Path(out_dir) / "carrier_manifest_pre_delete.json"
    p.write_text(_dump_json(body), encoding="utf-8")
    m_sha = sha256_file(p)
    (Path(out_dir) / "carrier_manifest_pre_delete.sha256").write_text(
        m_sha + "\n", encoding="utf-8")
    rec.add("MANIFEST", "pre_delete_path", str(p),
            "script:write_pre_delete_manifest")
    rec.add("MANIFEST", "pre_delete_sha256", m_sha, f"{p}:file",
            note="★ 外部文件哈希（★ 非自引用）")
    rec.add("MANIFEST", "pre_delete_file_count", len(tree),
            "script:write_pre_delete_manifest")
    rec.add("MANIFEST", "pre_delete_tree_errors", len(tree_errors),
            "script:write_pre_delete_manifest",
            note="★ U-2：★ error/null 件数 ⇒ 清单失败判据")
    rec.add("MANIFEST", "pre_delete_manifest_ok", manifest_ok,
            "script:write_pre_delete_manifest")
    return {"path": str(p), "sha256": m_sha, "file_count": len(tree),
            "tree_error_count": len(tree_errors), "manifest_ok": manifest_ok}


def delete_owned_carrier(rec: Recorder, carrier_dir: Path, ownership: dict,
                         terminated_ok: bool, out_dir: Path,
                         evidence_ok: bool = False,
                         pre_manifest_ok: bool = False,
                         carrier_identity: dict | None = None,
                         handover: Path | None = None,
                         created_receipt: dict | None = None,
                         skip_file_hashes: bool = False) -> dict:
    """★★ 趟后删除链（★ **只删本趟拥有**的载体；★ 拒删**传播失败**）。

    ★★ 前置（★ 缺一即**拒删并记为收尾失败**，★ 不为"必删"越权强删）：
      1. `ownership.owned` 成立（本趟创建 / 受控交接）；
      2. 删除**前**重新核实身份与路径边界（★ 排除关键根/母本/历史树/证据树）；
      3. 本趟进程退出**已确认**（★ 未停稳不得删）；
      4. ★★ U-1：★ `evidence_ok` = True（证据搬出验 SHA 成功）；
      5. ★★ U-1：★ `pre_manifest_ok` = True（删除前清单成功且无 error 件）；
      6. ★★ QC176 / U-4：★ 创建时登记的**目录对象身份**（`st_dev`/`st_ino`）
         与删除前实测**同一对象**（★ 排除同路径目录被替换）；
      7. ★★ QC176 / U-4：★ 删除前**重验交接/创建证明有效性**（★ 重新判一次）。
    ★ 删除后**复核残留**；★ `final` 只写**实际结果**。
    ★★ U-2：★ 落**实际删除时间**。
    """
    res = {"carrier_dir": str(carrier_dir), "deleted": False,
           "applicable": bool(ownership and ownership.get("owned")),
           "refused_reason": None, "residual_exists": None, "result_path": None,
           "deleted_at": None, "identity_check": None, "revalidation": None}
    if not res["applicable"]:
        res["refused_reason"] = ("★ 所有权不成立（无本趟创建/受控交接证明）"
                                 "⇒ 启动前已拒绝 ⇒ 无本趟可回收对象（不适用）")
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier",
                note="★ 不适用（★ 未创建本趟副本；★ **不是**吞掉回收责任）")
        return res
    b = check_carrier_boundary(carrier_dir)
    res["boundary_before_delete"] = b
    if not b["ok"]:
        res["refused_reason"] = f"★ 删除前边界复核不通过：{b['reason']}"
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier",
                             res["refused_reason"], rec)
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier")
        return res
    # ==== QC176 / U-4 (6)：★ 删除前**同一目录对象**复核 ====================
    _now_ident = dir_identity_stamp(carrier_dir)
    _ident_ok = same_dir_object(carrier_identity, _now_ident)
    res["identity_check"] = {"baseline": carrier_identity, "before_delete": _now_ident,
                             "same_object": bool(_ident_ok)}
    if not _ident_ok:
        res["refused_reason"] = (
            "★ QC176/U-4：★ 删除前目录对象身份复核不通过"
            "（★ 无创建时身份基线，或 st_dev/st_ino 与基线不符"
            "⇒ ★ 同路径目录可能已被替换 ⇒ 拒删）")
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier:identity",
                             res["refused_reason"], rec)
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier",
                note="★ QC176/U-4：★ 缺身份基线不得放行")
        return res
    # ==== QC176 / U-4 (7)：★ 删除前**重验**交接/创建证明 ==================
    # ★★ QC179 / v7 §2.1 U-4：★ 传 skip_file_hashes=True
    #   （★ 合法运行产生的内容变化不以"仍等于创建时所有字节"替代对象所有权）。
    _reval = assess_carrier_ownership(
        carrier_dir, out_dir, rec,
        handover=(Path(handover) if handover else None),
        created_receipt=created_receipt,
        skip_file_hashes=True)
    res["revalidation"] = {"owned": bool(_reval.get("owned")),
                           "basis": _reval.get("basis"),
                           "refuse_reason": _reval.get("refuse_reason")}
    if not _reval.get("owned"):
        res["refused_reason"] = (
            "★ QC176/U-4：★ 删除前交接/创建证明重验不通过："
            + str(_reval.get("refuse_reason")))
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier:revalidate",
                             res["refused_reason"], rec)
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier")
        return res
    if not terminated_ok:
        res["refused_reason"] = "★ 本趟进程退出未确认 ⇒ 不删载体（★ 不冒险删）"
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier",
                             res["refused_reason"], rec)
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier")
        return res
    if not evidence_ok:
        res["refused_reason"] = ("★ U-1：★ 证据搬出/验 SHA 未成功 ⇒ 拒删"
                                 "（★ 不能「记录失败但照样 rmtree」）")
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier",
                             res["refused_reason"], rec)
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier")
        return res
    if not pre_manifest_ok:
        res["refused_reason"] = ("★ U-1：★ 删除前清单未成功/含 error 件 ⇒ 拒删"
                                 "（★ 不能「记录失败但照样 rmtree」）")
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier",
                             res["refused_reason"], rec)
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier")
        return res
    try:
        shutil.rmtree(str(carrier_dir))
    except Exception as e:
        res["refused_reason"] = f"★ 删除失败：{e!r}"
        res["residual_exists"] = os.path.exists(str(carrier_dir))
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier",
                             res["refused_reason"], rec)
        rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier")
        return res
    res["deleted"] = True
    res["deleted_at"] = now_iso()
    res["residual_exists"] = os.path.exists(str(carrier_dir))
    if res["residual_exists"]:
        res["refused_reason"] = "★ 删除后仍有残留 ⇒ 复核失败"
        note_cleanup_failure(EXIT_CARRIER_DELETE_FAILED,
                             "script:delete_owned_carrier",
                             res["refused_reason"], rec)
    rp = Path(out_dir) / "carrier_delete_result.json"
    rp.write_text(_dump_json(res), encoding="utf-8")
    res["result_path"] = str(rp)
    rec.add("DELETE", "carrier_delete", res, "script:delete_owned_carrier",
            note="★ U-1：★ 证据+清单门控通过后才删；★ U-2：★ 含实际删除时间")
    return res


def write_final_manifest(rec: Recorder, carrier_dir: Path, out_dir: Path,
                         ownership: dict, evidence: dict, pre_manifest: dict,
                         delete_res: dict, finalize_code: int,
                         main_return_code: int = EXIT_OK) -> dict:
    """★★ 最终 `MANIFEST.json`（★ 在**全部判定之后**落；★ 引用删除前清单与其 SHA）。

    ★★ U-6：★ 区分 cleanup 成功与整趟 PASS。★ `verdict` 仅当
      `main_return_code == EXIT_OK` 且收尾全成功时才为 PASS。
    """
    ev_items = [{"source": it.get("source"), "path": it.get("evidence_path"),
                 "sha256": it.get("sha256_evidence"), "ok": it.get("ok")}
                for it in (evidence or {}).get("items", [])]
    cleanup_ok = bool(delete_res.get("deleted") and not delete_res.get("residual_exists")
                      and (evidence or {}).get("ok") and not CLEANUP_FAILURES)
    whole_trip_ok = bool(main_return_code == EXIT_OK and cleanup_ok)
    body = {
        "manifest_kind": "trip_final", "created_at": now_iso(), "card": "QC169",
        "carrier_dir": str(carrier_dir),
        "ownership": {k: ownership.get(k) for k in
                      ("owned", "basis", "receipt_path", "files_match")},
        "evidence": {"verified": (evidence or {}).get("ok"), "items": ev_items},
        "pre_delete_manifest": pre_manifest,
        "delete_result": delete_res,
        "cleanup_failures": list(CLEANUP_FAILURES),
        "main_return_code": main_return_code,
        "finalize_exit_code": finalize_code,
        "cleanup_ok": cleanup_ok,
        "verdict": "PASS" if whole_trip_ok else "FAIL",
        "note": "★ U-6：★ final 区分 cleanup 成功与整趟 PASS；"
                "★ 删除前清单见 pre_delete_manifest（不可变）",
    }
    p = Path(out_dir) / "MANIFEST.json"
    p.write_text(_dump_json(body), encoding="utf-8")
    rec.add("MANIFEST", "final_path", str(p), "script:write_final_manifest")
    rec.add("MANIFEST", "final_sha256", sha256_file(p), f"{p}:file")
    rec.add("MANIFEST", "final_verdict", body["verdict"],
            "script:write_final_manifest")
    # ★★ QC176 / U-6：★ 留存内存副本 ⇒ ★ 入口最终合并后按**实际最终码**重写
    LAST_FINAL_MANIFEST[0] = body
    return body


def rewrite_final_manifest_with_actual(final_code: int,
                                       rec: Recorder | None = None) -> bool:
    """★★ QC176 / v6 §6.1.1 U-6：★ 入口最终合并**之后**用**实际最终码**重写 MANIFEST。

    ★★ 原缺陷：★ final MANIFEST 早于 `dump` 与入口最终合并（v6 §6.1.1 U-6）
      ⇒ ★ 之后的落盘/收尾失败可令**实际**失败，
      ★ 而 MANIFEST 仍留此前的 PASS / 旧失败集 ⇒ ★ 记录与实际不一致。
    ★ 本函数：★ 重新计算 `cleanup_ok` / `verdict`（★ 用**当前** `CLEANUP_FAILURES`），
      ★ 写入 `final_exit_code` = `final_code`，★ 并把落盘**结果**如实返回。
    """
    body = LAST_FINAL_MANIFEST[0]
    if not isinstance(body, dict):
        return True                     # ★ 未落过 final MANIFEST ⇒ 不适用
    try:
        nb = dict(body)
        _dr = nb.get("delete_result") or {}
        _mrc = int(nb.get("main_return_code", EXIT_OK))
        cleanup_ok = bool(_dr.get("deleted") and not _dr.get("residual_exists")
                          and (nb.get("evidence") or {}).get("verified")
                          and not CLEANUP_FAILURES)
        nb["cleanup_failures"] = list(CLEANUP_FAILURES)
        nb["cleanup_ok"] = bool(cleanup_ok)
        nb["finalize_exit_code"] = int(final_code)
        nb["final_exit_code"] = int(final_code)
        nb["verdict"] = ("PASS" if (_mrc == EXIT_OK and cleanup_ok
                                    and int(final_code) == EXIT_OK) else "FAIL")
        nb["rewritten_at"] = now_iso()
        nb["rewrite_note"] = ("★ QC176/U-6：★ 入口最终合并之后按**实际最终退出码**重写"
                              "（★ 补晚发生失败的终态引用）")
        p = Path(WORKDIR) / "MANIFEST.json"
        p.write_text(_dump_json(nb), encoding="utf-8")
        _sha = sha256_file(p)
        (Path(WORKDIR) / "MANIFEST.sha256").write_text(_sha + "\n",
                                                       encoding="utf-8")
        LAST_FINAL_MANIFEST[0] = nb
        if rec is not None:
            rec.add("MANIFEST", "final_rewritten_exit_code", int(final_code),
                    "script:rewrite_final_manifest_with_actual",
                    note="★ QC176/U-6：★ 与**实际最终退出码**一致")
        return True
    except Exception as e:
        print(f"[WRAPPER] final MANIFEST 重写失败：{e!r}", file=sys.stderr)
        return False


def exception_process_exit_code(exc: BaseException) -> int:
    """★★ QC176 / v6 §6.1.1 U-6：★ **显式定义**「未处理异常 ⇒ 实际进程退出码」。

    ★★ 原缺陷（v6 §6.1.1 U-6 原文）：★ 入口记录"内部合并后的码（通常 70）"
      后 `bare raise` ⇒ ★ `:2771` 的 `sys.exit(数字)` 路径**不再执行**
      ⇒ ★ 普通未处理异常**实际**退出通常为 **1**、`SystemExit` 则保留自己的 code
      ⇒ ★ 盘上 `final_exit_code` **不是**实际最终码。
    ★★ 故此处**定义**映射（★ 与解释器真实行为**一致**），★ 入口按此返回：
      - `SystemExit`  ：`code is None` ⇒ 0；`code` 为 `int` ⇒ 该值；
                        其它（如 `str`）⇒ 打到 stderr 后为 1；
      - `KeyboardInterrupt` ⇒ 130；
      - 其它 `BaseException` ⇒ 1。
    ★★ 「保留原异常」由 `write_finalize_error()` 落盘
      （类型 / 位置 / repr / message / 完整 traceback）保证；
      ★ 入口只在**最外层边界**把"传播"换成"映射后的实际退出码"。
    """
    if isinstance(exc, SystemExit):
        c = exc.code
        if c is None:
            return EXIT_OK
        if isinstance(c, int):
            return int(c)
        print(str(c), file=sys.stderr)
        return 1
    if isinstance(exc, KeyboardInterrupt):
        return EXIT_KEYBOARD_INTERRUPT
    return 1


def finalize_trip(rec: Recorder, carrier_dir: Path, bak: dict,
                  t0: list, pre_except_txt: str,
                  out_dir: Path | None = None,
                  ownership: dict | None = None,
                  terminated_ok: bool = False,
                  main_return_code: int = EXIT_OK,
                  mother_baseline: dict | None = None,
                  carrier_identity: dict | None = None,
                  handover: Path | None = None,
                  created_receipt: dict | None = None) -> int:
    """★★★ `QC157:3`：★ 覆盖**全程**的收尾（★ `finally` 调用本函数）。

    ★★ `QC162:W7` —— ★★ **证据必须先于还原**（★ 本卡最重）：
      执行序（★ 逐项有行号）：
        1. `except_evidence_copy_and_verify` —— 跑后 `except.txt` 原件 + 五载体件
           跑后状态**另存证据副本**进 `out_dir`，★ 并**逐件验 SHA**（第 1 项）；
        2. `t0_t1_sha_diff` —— `T1` 落盘 + `T0↔T1` 逐件 sha 比对；
        3. `except_set_diff` —— `except.txt` 集合差（★ 读的是**未被还原
           污染**的跑后内容）；
        4. `controls_post` —— 跑后两控（★ 真读文件，不缓存）；
        5. `carrier_pre_delete_manifest` —— **不可变**的删除前完整清单（第 1 项）；
        6. `restore_carrier` —— 载体件状态核验（★ 放到删除**之前**）；
        7. `carrier_delete_chain` —— 删除**本趟拥有**的副本 + 残留复核（第 1 项）；
        8. `final_manifest` —— 最终 `MANIFEST.json`（★ 引用 5 的路径与 SHA）；
        9. `dump_records` —— 字段总落盘 + `run_log`（★★ 放到**最后**：
           ★ 修 `QC162` 旧序 `dump` 早于末项核验 ⇒ 最终记录早于最终失败码）。
    ★★ `QC169` 第 3 项：★ 收尾失败**不再**写 `verdict[0]` 局部变量
      （★ 它会被后续成功项覆盖）⇒ ★ 一律进**模块级容器** `CLEANUP_FAILURES`
      ⇒ ★ 本函数返回 `merge_cleanup_code(EXIT_OK)`（★ 成功**不清空**既有失败）。
    ★ 收尾项**逐个落盘**、★ **各自独立、互不跳过**（★ 见 `run_guarded_steps`）。
    ★ 本函数在 `finally` 内执行：★ **返回**合并退出码，不吞异常。
    """
    if out_dir is None:
        out_dir = WORKDIR
    if ownership is None:
        ownership = {"owned": False, "basis": "none", "receipt_path": None}
    state: dict = {"evidence": None, "pre_manifest": None, "delete": None}

    def _except_evidence_copy() -> None:
        copy_post_except_evidence(rec, carrier_dir, out_dir)
        # ★★ 第 1 项：★ 证据**先搬出**并**逐件验 SHA**
        ev = move_out_evidence_and_verify(rec, carrier_dir, out_dir)
        state["evidence"] = ev
        if not ev["ok"]:
            note_cleanup_failure(
                EXIT_EVIDENCE_VERIFY_FAILED, "script:move_out_evidence_and_verify",
                f"★ 证据搬出后逐件验 SHA 失败：{ev['failed']}", rec)

    def _restore() -> None:
        if not bak:
            rec.add("RESTORE", "finalize_verdict", None, "script:finalize_trip",
                    note="★ 未备份（启动前即失败）⇒ 无载体件可还原 ⇒ null")
            return
        ok = restore_carrier(rec, carrier_dir, bak)
        rec.add("RESTORE", "finalize_verdict", "PASS" if ok else "FAIL",
                "script:finalize_trip")
        if not ok:
            note_cleanup_failure(EXIT_RESTORE_FAILED, "script:restore_carrier",
                                 "★ 载体件跑后状态与备份不符（★ 不写回）", rec)

    def _t0t1() -> None:
        if not t0:
            rec.add("T", "finalize_t0_t1_verdict", None, "script:finalize_trip",
                    note="★ 无 T0（启动前即失败）⇒ 未测 ⇒ null")
            return
        t1 = t_snapshot(rec, "T1", out_dir / "T1_zero_write.json")
        same = t_diff(rec, t0, t1, out_dir / "T0_T1_diff.json")
        rec.add("T", "finalize_t0_t1_verdict", "PASS" if same else "FAIL",
                "script:finalize_trip")
        if not same:
            note_cleanup_failure(EXIT_T0_T1_DIFF, "script:t_diff",
                                 "★ T0↔T1 逐件 sha 有差 ⇒ 零写自证失败", rec)

    def _except_diff() -> None:
        if pre_except_txt is None:
            rec.add("EXCEPT", "finalize_set_diff", None, "script:finalize_trip",
                    note="★ 无跑前基线（启动前即失败）⇒ 未测 ⇒ null")
            return
        post_txt = (carrier_dir / "except.txt").read_text(
            encoding="utf-8", errors="replace")
        setdiff = except_set_diff(rec, pre_except_txt, post_txt)
        (out_dir / "except_set_diff.json").write_text(
            json.dumps(setdiff, ensure_ascii=False, indent=1),
            encoding="utf-8")
        # ★★ 集合差发现新异常 ⇒ 影响退出码（外部裁定：不能只记账）
        if not setdiff.get("no_new_exception", True):
            rec.add("EXCEPT", "finalize_new_exception_found", True,
                    "script:finalize_trip",
                    note="★★ 跑后出现新异常 ⇒ 非 0 退出码")
            note_cleanup_failure(EXIT_INTERNAL_ERROR, "script:except_set_diff",
                                 "★ 跑后 except.txt 出现新异常行", rec)

    def _ctrl_post() -> None:
        c1_ok = control_one(rec, "post")
        c2_ok = control_two(rec, "post")
        both_ok = c1_ok and c2_ok
        rec.add("CTRL", "both_post_ok", both_ok,
                "script:finalize_trip",
                note="★ 跑后两控（★ 真读文件，不缓存跑前结果）")
        # ★★ 跑后控失败 ⇒ 影响退出码（外部裁定：不能只记账）
        if not both_ok:
            rec.add("CTRL", "finalize_post_ctrl_failed", True,
                    "script:finalize_trip",
                    note="★★ 跑后两控任一失败 ⇒ 非 0 退出码")
            note_cleanup_failure(EXIT_PRECHECK_SHA_MISMATCH, "script:control_*",
                                 "★ 跑后两控任一失败", rec)

    def _pre_delete_manifest() -> None:
        pm = write_pre_delete_manifest(rec, carrier_dir, out_dir,
                                       ownership, state.get("evidence"),
                                       mother_baseline=mother_baseline)
        state["pre_manifest"] = pm

    def _delete_chain() -> None:
        ev_ok = bool((state.get("evidence") or {}).get("ok"))
        pm_ok = bool((state.get("pre_manifest") or {}).get("manifest_ok"))
        # ★★ QC176 / U-4：★ 传创建时身份基线与交接/创建证明 ⇒ 删除前重核同一对象
        state["delete"] = delete_owned_carrier(
            rec, carrier_dir, ownership, terminated_ok, out_dir,
            evidence_ok=ev_ok, pre_manifest_ok=pm_ok,
            carrier_identity=carrier_identity,
            handover=handover, created_receipt=created_receipt)

    def _final_manifest() -> None:
        write_final_manifest(rec, carrier_dir, out_dir, ownership,
                             state.get("evidence"), state.get("pre_manifest"),
                             state.get("delete"), merge_cleanup_code(EXIT_OK),
                             main_return_code=main_return_code)

    def _dump() -> None:
        code = merge_cleanup_code(EXIT_OK)
        rec.add("META", "finalized", now_iso(), "script:finalize_trip")
        rec.add("META", "finalize_exit_code", code,
                "script:finalize_trip",
                note="★ 收尾侧合并退出码（★ 最终码由 _main_wrapper 再合并 main 返回值）")
        rec.dump(out_dir / "qc151_fields.json")
        (out_dir / "qc151_run_log.json").write_text(
            json.dumps({"finalize_exit": code,
                        "cleanup_failures": list(CLEANUP_FAILURES)},
                       ensure_ascii=False, indent=1), encoding="utf-8")

    # ★★ 逐项执行（★ 前一步失败也继续后面的；★ 跑完才重抛第一个异常）
    run_guarded_steps([
        ("except_evidence_copy_and_verify", _except_evidence_copy),
        ("t0_t1_sha_diff", _t0t1),
        ("except_set_diff", _except_diff),
        ("controls_post", _ctrl_post),
        ("carrier_pre_delete_manifest", _pre_delete_manifest),
        ("restore_carrier", _restore),
        ("carrier_delete_chain", _delete_chain),
        ("final_manifest", _final_manifest),
        ("dump_records", _dump),
    ], out_dir=out_dir)
    return merge_cleanup_code(EXIT_OK)


# ===========================================================================
# §14 · 主流程
# ===========================================================================
def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        prog="qc151_trip.py",
        description="QC151 · U0400 首趟载体趟（★ 直启 gamemd.exe；★ 不注入）")
    ap.add_argument("--target-map", required=True,
                    help="★ 目标地图**全路径**（含根名），如 "
                         r"…\lead\<card>\carrier\[2]0LoadBench_U0400.yrm")
    ap.add_argument("--target-sha256", required=True,
                    help="★ 目标地图的预期 sha256（小写十六进制）")
    # ★★ `--other-map` **已移除**（`QC157:1`）：★ 用户已裁决"其他地图反控
    #   改**后续独立一趟**"。★ 本趟**只采目标图帧**，★ 结构上不产 `other` 判定。
    ap.add_argument("--carrier", required=True,
                    help="★ 载体目录（含 gamemd.exe 与 [2]0LoadBench_U0400.yrm）"
                         "★ 第 1 项：★ 该目录须**本趟创建**或持**受控交接证明**，"
                         "★ 否则启动前拒绝（EXIT_CARRIER_NOT_OWNED=23）")
    # ★★ 第 1 项：★ 本趟**排他新建**执行副本（★ 真实创建证明；§2.2）
    ap.add_argument("--carrier-create-from", default=None,
                    help="★ 源目录：在本趟写域内排他新建唯一执行副本，"
                         "★ 逐件复制并验 SHA（★ 给出时 --carrier 被覆盖）")
    ap.add_argument("--carrier-create-files", default=None,
                    help="★ 追加复制的载体件名（逗号分隔；默认只复制 "
                         "CARRIER_FILES 五件，★ 来源须**明列**，§2.3）")
    # ★★ 第 1 项：★ 受控**交接证明**（★ 逐件 sha + exclusive_for_trip）
    ap.add_argument("--carrier-handover", default=None,
                    help="★ 交接证明 JSON（carrier_dir / exclusive_for_trip / "
                         "trip_id / handover_from / handover_to / source_dir / "
                         "files{name:{sha256}}）⇒ ★ 逐件复核后所有权才成立")
    # ★★ QC176 / U-4：★ **唯一趟身份**（★ 交接须绑定本趟；★ 不自凭声明）
    ap.add_argument("--trip-id", default=None,
                    help="★ 本趟唯一标识（★ 与交接证明 trip_id **必须一致**；"
                         "★ 使用 --carrier-handover 时**必须**显式给出）")
    # ★★ [U8 20261021] 授权通道（★ 缺省关 ⇒ 行为与授权前逐字相同）
    #   ★★ 双键：本开关 + `--trip-id` 逐字匹配（未给 --trip-id ⇒ 不授权）。
    #   ★ 依据 Notion U1–U9 裁决四条件①。禁止面 (a)(b)(c)(d) 仍全部有效。
    ap.add_argument("--allow-loader", action="store_true", default=False,
                    help="★★ [U8] 授权直启载体 ra2loader.exe（注入 ra2render.dll）。"
                         "★ 默认关；★ 必须同时给 --trip-id 且逐字匹配才生效；"
                         "★ 授权趟证据仅可用于 B0/B1 臂对比，不得用于 A 臂基线")
    # ★★ `QC162:W1`：★ 运行期写域（★ 一切运行期落盘都进这里）
    #   ★ 默认值 = `out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip`
    #     （★ 本趟**批准**的趟写域）；
    #   ★ 也可用环境变量 `QC151_OUT_DIR` 预设（★ CLI 优先于环境变量）。
    ap.add_argument("--out-dir", default=None,
                    help="★ 运行期写域（默认：lead\\qc161_u0400_trip，"
                         "即本趟批准域；★ 也可用环境变量 QC151_OUT_DIR 预设）")
    # ★★ QC202/C1（MEASURE_DESIGN_v1.md §2.1/§3.2/§5）：进图态性能测量开关。
    #   ★ 缺省 0 ⇒ 不采样 ⇒ 本开关外的门禁行为语义与 T24（锚 e4f87b96）
    #     完全一致（§2.1 flag-off 等价）。
    #   ★ 非 0 ⇒ 导航全绿（NAV.verdict=="OK"）后，在 frame 与 fields_post
    #     之间执行 3 窗×25 s + settle 4 s 的 RPM 只读采样（协议常量按
    #     设计稿 v1 固定，不另设窗数/秒数开关）；RPM 扩项授权见 §10.8 头注。
    ap.add_argument("--measure", type=int, default=0,
                    help="★ QC202/C1：进图态测量开关（缺省 0=不开启；"
                         "非 0 ⇒ 按 MEASURE_DESIGN_v1 固定协议采样，"
                         "仅导航全绿后执行；退出码表不加新码）")
    # >>> QC210-BEGIN argparse（--spot-select 单开关；缺省 off=行为与改前逐字节一致）
    # ★★ QC210：显式遭遇战指位段 + 帧钟 burst 分类器 单开关（缺省 off）。
    #   ★ off（缺省）⇒ 指位段零执行、burst 包装器一字不差委托锚函数
    #     ⇒ 行为与改前逐字节一致（flag-off 等价，§2.1 房规；--measure/T24 先例）。
    #   ★ on（T36 显式给）⇒ nav_setup 过闸后、nav_start 点击前执行 S1..S5
    #     显式指位（EARLY_END_ANALYSIS.md §11.1），且 nav_start 后态 burst
    #     开战判据改**帧钟推进**（tactical_colors 降为辅助信号）。
    ap.add_argument("--spot-select", action="store_true", default=False,
                    help="★ QC210：设置屏显式指位（人类行=1/AI 行=2）+ "
                         "帧钟 burst 分类器（缺省 off=行为与改前逐字节一致；"
                         "T36 显式给 on）")
    # <<< QC210-END argparse
    # >>> QC151FS-BEGIN argparse（--fullscreen 单开关；缺省 off=行为与改前逐字节一致）
    # ★★ QC151FS：全屏模式适配（cnc-ddraw ddraw.ini windowed=false ⇒ 独占/
    #   边框全屏启动）。
    #   ★ off（缺省）⇒ 抓帧仍 PrintWindow、到达仍 800×600 矩形判据、坐标仍锚
    #     换算路径 ⇒ 行为与改前逐字节一致（§2.1 房规；--spot-select/--measure 先例）。
    #   ★ on（T55 显式给）⇒ 抓帧=桌面拷贝（GDI 屏 DC BitBlt，每次抓帧前
    #     SetForegroundWindow）；到达判据=菜单签名（替换 800×600 矩形判据）；
    #     坐标映射=窗口原点+游戏坐标×1.0（替换 ×0.667 虚拟化换算语义）；
    #     qc151_fields 增 META.fullscreen 与 F-9 全屏几何字段。
    ap.add_argument("--fullscreen", action="store_true", default=False,
                    help="★ QC151FS：全屏模式适配（缺省 off=行为与改前逐字节"
                         "一致；T55 显式给 on）")
    # <<< QC151FS-END argparse
    # >>> EVIDDIFF-BEGIN argparse（--evid-diff 单开关；缺省 off=现行全量拷贝
    #   行为逐字节不变；on=差异件模式，语义见 EVIDDIFF helpers 块头注）
    ap.add_argument("--evid-diff", action="store_true", default=False,
                    help="★ EVID-DIFF：证据搬出差异件模式（缺省 off=全量拷贝"
                         "与改前逐字节一致；on=差异件才拷出＋每趟写 "
                         "evidence/<stamp>/MANIFEST.json + README_REBUILD.md；"
                         "参照缺失 ⇒ 本趟回退全量并记为参照）")
    # <<< EVIDDIFF-END argparse
    # >>> QC151P3-BEGIN argparse（--frozen-dump / --probe-frames；缺省关=行为与改前逐字节一致）
    # ★★ QC151P3：冻结态 minidump 采集 单开关（缺省 False ⇒ 全文件行为与改前
    #   逐字节一致；QC210 main-gate 房规：off 时连 False 记录行都不写）。
    #   ★ on（P3 趟显式给）⇒ QC213 冻结检测触发点（frozen_done 判定处）用
    #     dbghelp!MiniDumpWriteDump（MiniDumpNormal）对 gamemd.exe 抓 dump，落
    #     WORKDIR 根下 frozen_f<frame>.dmp；qc151_fields（MEASURE 组）只记
    #     dump 路径/字节数/pid/frame；栈解析一律离线（冻结窗内动作最小化）。
    #   ★ 须配 --measure≠0（探针随 measure 窗激活；单给本旗标不生效、零行）。
    ap.add_argument("--frozen-dump", action="store_true", default=False,
                    help="★ QC151P3：冻结触发抓 gamemd.exe minidump"
                         "（缺省 off=行为与改前逐字节一致；P3 显式给 on；"
                         "须配 --measure≠0）")
    # ★★ QC151P3 补遗①：锁存帧阶梯。缺省 "300,600,1800" == 锚 QC213_LATCH_FRAMES
    #   ⇒ 缺省=现行为逐字节一致（★ 补遗原文拟缺省单值 "300"，但锚现行为是
    #   300/600/1800 三点锁存 ⇒ 单值缺省会砍掉 600/1800 两档，违反同一房规
    #   ⇒ 为守 flag-off 房规取三点全列，勘误论证见 RECEIPT §缺省等价性）。
    #   ★ P3 趟显式给 "15,30,45,60,90,120,150,180,210,240,270,300"（衰变曲线，
    #   分辨 h1/h0 车辆归零=一次性清洗 vs 渐进消耗）。frozen_final 逻辑不变。
    #   ★ 须配 --measure≠0（同上）。
    ap.add_argument("--probe-frames", type=_qc151p3_probe_frames,
                    default="300,600,1800",
                    help="★ QC151P3：探针锁存帧阶梯（逗号分隔正整数；"
                         "缺省 '300,600,1800'=现行为逐字节一致；"
                         "P3 趟显式给阶梯串；须配 --measure≠0）")
    # <<< QC151P3-END argparse
    # >>> QC151SG-BEGIN argparse（--sg-capture / --sg-toggle-x/y；缺省全关=行为与改前逐字节一致）
    # ★★ QC151SG：遭遇战设置屏「短游戏」开关 取证+可控点击（缺省零旗标 ⇒
    #   零行为零行；QC210 main-gate 房规：off 时连 False 记录行都不写）。
    #   ★ --sg-capture 单给 = 纯取证（T55i：抓 navsig_skirmish_set_pre.png
    #     标定「短游戏」开关坐标）；--sg-toggle-x/y 成对给 = 点击（T55j）。
    #   ★ 坐标空间 = 800×600 游戏系（同 NAV_CHAIN/spot 坐标口径）。
    ap.add_argument("--sg-capture", action="store_true", default=False,
                    help="★ QC151SG：设置屏取证（抓 navsig_skirmish_set_pre.png；"
                         "缺省 off=行为与改前逐字节一致；T55i 显式给 on）")
    ap.add_argument("--sg-toggle-x", type=int, default=None,
                    help="★ QC151SG：「短游戏」开关点击 x（800×600 游戏系；"
                         "缺省 None=零点击；须与 --sg-toggle-y 成对给，"
                         "单给 ⇒ 拒点并如实记账；T55j 凭 T55i 标定值给）")
    ap.add_argument("--sg-toggle-y", type=int, default=None,
                    help="★ QC151SG：「短游戏」开关点击 y（800×600 游戏系；"
                         "缺省 None=零点击；语义同 --sg-toggle-x）")
    # <<< QC151SG-END argparse
    return ap.parse_args(argv)


def main(argv=None) -> int:
    global WORKDIR
    args = parse_args(argv)
    # =====================================================================
    # ★★ `QC162:W1`：★ **先定稿运行期写域**，再建目录、再留痕。
    #   ★ 优先级：`--out-dir`(cli) > `QC151_OUT_DIR`(env) > 默认 `qc161_u0400_trip`。
    #   ★ 目录不存在 ⇒ **自建**（★ `mkdir(parents=True, exist_ok=True)`）。
    #   ★★ **绝不**是本卡目录 `qc151_u0400_trip`（★ 该目录只留卡面/报告/自检产物）。
    # =====================================================================
    if args.out_dir:
        WORKDIR = Path(args.out_dir)
        out_dir_source = "cli"
    elif os.environ.get(OUT_DIR_ENV_VAR):
        WORKDIR = Path(os.environ[OUT_DIR_ENV_VAR])
        out_dir_source = "env"
    else:
        WORKDIR = Path(DEFAULT_OUT_DIR)
        out_dir_source = "default"
    sync_backup_dir()
    # ★★ QC179 / v7 §2.1 U-3：★ WORKDIR 须落在批准域内（★ 不让 --out-dir
    #   自行重新定义"批准域"）。★ 先验证、再 mkdir、再写任何文件。
    _w_n = _norm_path(str(WORKDIR))
    _d_n = _norm_path(str(DEFAULT_OUT_DIR))
    _workdir_in_approved_domain = bool(
        _w_n == _d_n or _w_n.startswith(_d_n + os.sep))
    if not _workdir_in_approved_domain:
        # ★ 不在默认批准域内 ⇒ 检查是否为 ROOT/LEAD 的受保护子树后代
        _w_protected = False
        for _pr in carrier_protected_subtrees():
            if _w_n == _pr or _w_n.startswith(_pr + os.sep):
                _w_protected = True
                break
        if _w_protected:
            raise SystemExit(
                f"★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}")
        # ★ 非受保护但也不在默认域内 ⇒ 记录警告但允许（★ 外部可能合法授权）
    WORKDIR.mkdir(parents=True, exist_ok=True)
    rec = Recorder()
    rec.add("META", "card", "QC151", "cards/QC141.md")
    rec.add("META", "script_fix_card", "QC162", "cards/QC162.md")
    rec.add("META", "out_dir", str(WORKDIR), "argv:--out-dir / env / default",
            note="★★ QC162:W1：运行期写域（一切运行期落盘都进这里）")
    rec.add("META", "out_dir_source", out_dir_source,
            "script:main",
            note="★ cli / env / default（默认 = lead\\qc161_u0400_trip）")
    rec.add("META", "out_dir_is_card_dir", (WORKDIR == LEAD / "qc151_u0400_trip"),
            "script:main",
            note="★★ 必须为 False：本卡目录运行期零写入（QC162:W1）")
    rec.add("META", "out_dir_in_approved_domain", _workdir_in_approved_domain,
            "script:main",
            note="★★ QC179/U-3：★ WORKDIR 是否落在批准域（DEFAULT_OUT_DIR）内")
    rec.add("META", "started", now_iso(), "script:main")
    rec.add("META", "script_ran_by", "QC151 执行者（★ 签字后）",
            "QC141:3", note="★ 本卡**不运行**本脚本")
    # >>> EVIDDIFF-BEGIN flag（模块级容器置位；缺省 off；EVID 记录旗标状态）
    EVID_DIFF_FLAG["on"] = bool(getattr(args, "evid_diff", False))
    rec.add("EVID", "evid_diff_flag", EVID_DIFF_FLAG["on"],
            "argv:--evid-diff",
            note="★ EVID-DIFF：off=全量拷贝（与锚逐字节一致）；"
                 "on=差异件模式（差异件才拷出＋MANIFEST/README）")
    # <<< EVIDDIFF-END flag

    # >>> QC151FS-BEGIN main-arm（缺省 off ⇒ 本块零行为、零 rec 行；行为与改前逐字节一致）
    # ★★ QC151FS：--fullscreen ⇒ 武装全屏容器并在 META 如实留痕
    #   （off ⇒ 连 False 行都不写，同 QC210 main-gate 纪律）。
    if getattr(args, "fullscreen", False):
        _QC151FS["on"] = True
        rec.add("META", "fullscreen", True, "argv:--fullscreen",
                note="★ QC151FS：全屏模式（cnc-ddraw windowed=false）⇒ 抓帧="
                     "桌面拷贝（抓前 SetForegroundWindow）、到达=主菜单签名"
                     "（非 800×600 矩形）、坐标=窗口原点+游戏坐标×1.0；"
                     "窗口实际几何见 F-9.fullscreen_mode/screen_wh")
        # ★★ QC151FS 预算放宽：全屏启动时间线=模式切换稳定化 ~28s+片头播放
        #   +菜单 ~60-90s ⇒ 窗口模式 30s 阶段帽/180s 总帽必爆（T55b 实证
        #   EXIT_STAGE_TIMEOUT@NAV）。仅 --fullscreen 覆写本两全局；
        #   窗口模式路径的卡面帽（30s/180s）零改动。
        global STAGE_TIMEOUT_S, TRIP_BUDGET_S
        STAGE_TIMEOUT_S = 150.0
        TRIP_BUDGET_S = 540.0
    # <<< QC151FS-END main-arm

    # ★★ `QC162:W2` + `QC169` 第 3 项：★ 收尾失败码写入**模块级容器**
    #   （★ `finally` 内可写、`main()` 返回后仍可读）—— ★ 由最外层
    #   `_main_wrapper()` 在 `main()` 返回后**再合并**（★ 收尾失败 ⇒ 以
    #   收尾失败码**覆盖** `main()` 的返回值 ⇒ 进程退出码真的非 0）。
    global FINALIZE_CODE, LAUNCH_TOKEN, TRIP_ID
    # ★★ QC176 / U-4：★ 本趟**唯一趟身份**（★ 早于任何创建/交接判定）
    #   ★ CLI 显式给定 ⇒ 采信；★ 否则生成一次性随机值
    #     （★ 随机值必然 ≠ 任何外部交接件的 trip_id ⇒ 交接分支 fail-closed）。
    TRIP_ID = (str(args.trip_id).strip()
               if getattr(args, "trip_id", None)
               and str(args.trip_id).strip() else new_trip_id())
    FINALIZE_CODE[0] = EXIT_OK
    main.finalize_verdict = FINALIZE_CODE     # ★ 兼容留痕（★ 同名同体）
    # ★★ 第 3 项：★ 清空**可外达**收尾失败容器（★ 单趟一次性）
    CLEANUP_FAILURES.clear()
    # ★★ 第 2 项：★ **预先**建立外层可见清理令牌（★ 早于任何 Popen）
    LAUNCH_TOKEN = LaunchToken()
    TRIP_CARRIER["dir"] = None
    TRIP_CARRIER["receipt"] = None
    TRIP_CARRIER["identity"] = None

    rec.add("META", "trip_id", TRIP_ID, "argv:--trip-id / generated",
            note="★★ QC176/U-4：★ 唯一趟身份（★ 交接须与本值一致）")
    carrier_dir = Path(args.carrier)
    target_map = Path(args.target_map)
    target_sha = args.target_sha256.strip().lower()

    # ★ 收尾所需的跑前状态（★ `finally` 里读；★ **未取到即 None/空**）
    bak: dict = {}
    t0: list = []
    pre_except_txt = None
    budget = TripBudget(rec)
    ACTIVE_REC[0] = rec       # ★ 第 3 项：★ 最外层最终落盘要用同一 rec
    # ★★ 进程身份跟踪（外部裁定：Popen 后须建立可清理所有权）
    proc = None          # type: subprocess.Popen | None
    launch_pid = None    # type: int | None
    launch_ct = None     # type: int | None
    # ★★ 第 1 项：★ 载体所有权（★ `finally` 也要用 ⇒ 先置 None，防未绑定）
    ownership: dict | None = None
    created_receipt: dict | None = None
    _main_return_code = EXIT_INTERNAL_ERROR  # ★ U-6：★ 默认非 0（异常路径）；正常 return 前覆写

    # =====================================================================
    # ★★★ `QC157:3`：★ 覆盖**全程**的 `try/finally`
    #   （启动 → 闸门 → 导航 → 采帧 → `F` 字段）
    # ★★ 任何**提前返回 / 异常**都经 `finally` 收尾 ⇒ ★ 没有"绕过还原"的路径。
    # =====================================================================
    try:
        # ---- ★★ 第 1 项：载体所有权（★ **启动前**判定；★ 不成立即拒绝） ----
        #   ★ 依据 §1 第 1 项：★「所有权不成立应在**启动前**拒绝，
        #     ★ 不能先跑后发现无权删」。
        budget.begin_stage("carrier_ownership")
        # ★★ [PATHLEN] **启动前预检**（★ 早于任何 `os.mkdir` / `Popen`；
        #   ★ 与载体清单构建处**同一判据**、同一函数 ⇒ ★ 两处不会漂移）。
        #   ★ 载体目录：★ 给了 `--carrier-create-from` ⇒ 本趟新建目录
        #     `WORKDIR/ct/c_<12 位 stamp>_<pid>`（★ stamp 恒 12 字符：
        #     `%H%M%S%f`；★ pid 取**本进程真值** ⇒ 预检与实际目录同长）；
        #     ★ 否则 = `--carrier` 给定目录。
        #   ★ 只判**目录**长度（★ 不含件名；★ 超 130 字符 ⇒ ★ 立即失败）。
        #   ★ 失败语义：★ 与本文件既有的载体清单拒绝**同族**（`RuntimeError`，
        #     见「★ 拒绝不安全件名」「★ 拒绝越界目的路径」）⇒ ★ 不新增退出码。
        if args.carrier_create_from:
            _pl_base = (Path(WORKDIR) / "ct"
                        / f"c_{'0' * 12}_{os.getpid()}")
        else:
            _pl_base = Path(args.carrier)
        carrier_pathlen_gate([_pl_base], "main.preflight", rec)
        if args.carrier_create_from:
            names = list(CARRIER_FILES)
            if args.carrier_create_files:
                names += [x.strip() for x in args.carrier_create_files.split(",")
                          if x.strip()]
            carrier_dir, created_receipt = create_isolated_carrier(
                rec, Path(args.carrier_create_from), WORKDIR / "ct",
                names)
        ownership = assess_carrier_ownership(
            carrier_dir, WORKDIR, rec,
            handover=(Path(args.carrier_handover) if args.carrier_handover
                      else None),
            created_receipt=created_receipt)
        rec.add("CARRIER", "carrier_dir", str(carrier_dir), "argv/created")
        rec.add("CARRIER", "ownership", ownership,
                "script:assess_carrier_ownership",
                note="★ 只有 created_by_this_trip / handover 才算成立")
        if not ownership["owned"]:
            rec.add("CARRIER", "trip_verdict", "REFUSED_NOT_OWNED", "script:main",
                    note="★★ 所有权不成立 ⇒ **启动前拒绝**"
                         "（★ 不先跑后发现无权删；★ 不越权删共享/历史件）")
            _main_return_code = EXIT_CARRIER_NOT_OWNED
            return EXIT_CARRIER_NOT_OWNED
        budget.end_stage("carrier_ownership")

        # ---- ⑧ 目标地图参数化：★ 启动前校验哈希 = 给定值，不等 ⇒ 硬停 ----
        budget.begin_stage("target_pin")
        if not target_map.exists():
            rec.add("TARGET", "exists", False, f"{target_map}:path",
                    note="★ 目标文件不存在 ⇒ 硬停")
            _main_return_code = EXIT_TARGET_MISSING
            return EXIT_TARGET_MISSING
        actual_target_sha = sha256_file(target_map)
        rec.add("TARGET", "full_path", str(target_map), "script:main",
                note="★★ 全路径（含根名）")
        rec.add("TARGET", "root_name", target_map.parent.name, "script:main")
        rec.add("TARGET", "pinned_sha256", target_sha, "argv:--target-sha256")
        rec.add("TARGET", "actual_sha256", actual_target_sha,
                f"{target_map}:file")
        if actual_target_sha != target_sha:
            rec.add("TARGET", "verdict", "FAIL", "script:main",
                    note="★★ 哈希 ≠ 给定值 ⇒ **硬停**（不进启动阶段）")
            _main_return_code = EXIT_TARGET_MISMATCH
            return EXIT_TARGET_MISMATCH
        rec.add("TARGET", "verdict", "PASS", "script:main",
                note="★ 哈希 = 给定值 ⇒ 放行")
        rec.add("TARGET", "is_hardcoded_T4_or_master", False, "script:main",
                note="★★ 结构事实：目标**全部**来自 argv；"
                     "代码中无 T4(93c2974b…)/母本(cb5785a1…) 常量"
                     "（★ 静态自检 #5/#3 可核）")
        budget.end_stage("target_pin")

        # ---- ② 跑前两控 ----
        budget.begin_stage("ctrl_pre")
        if not control_one(rec, "pre"):
            _main_return_code = EXIT_PRECHECK_SHA_MISMATCH
            return EXIT_PRECHECK_SHA_MISMATCH
        if not control_two(rec, "pre"):
            _main_return_code = EXIT_PRECHECK_SIG_MISMATCH
            return EXIT_PRECHECK_SIG_MISMATCH
        budget.end_stage("ctrl_pre")

        # ---- ③ `T0` 零写基线 ----
        budget.begin_stage("T0")
        t0 = t_snapshot(rec, "T0", WORKDIR / "T0_zero_write.json")
        budget.end_stage("T0")

        # ---- 备份载体件（供跑后逐字节还原） ----
        budget.begin_stage("backup")
        bak = backup_carrier(rec, carrier_dir)
        budget.end_stage("backup")

        # ---- ④ `except.txt` 被动基线（★ U-5：★ 不再写载体 except.txt） ----
        #   ★ 外部裁定 V5 §6.1.1 U-5：★ 在既有禁写范围内移除 except_reset 对
        #     载体 except.txt 的覆盖写。★ 改为被动读取现有内容作基线。
        budget.begin_stage("except_baseline")
        _except_pre_path = carrier_dir / "except.txt"
        if _except_pre_path.exists():
            pre_except_txt = _except_pre_path.read_text(
                encoding="utf-8", errors="replace")
            rec.add("EXCEPT", "baseline_source", "passive_read",
                    "script:main",
                    note="★ U-5：★ 被动读取现有 except.txt 作基线（★ 不写载体）")
        else:
            pre_except_txt = None
            rec.add("EXCEPT", "baseline_source", "none",
                    "script:main",
                    note="★ U-5：★ 载体 except.txt 不存在 ⇒ 无基线（★ 不写载体）")
        rec.add("EXCEPT", "reset_verdict", "SKIPPED_U5",
                "script:main",
                note="★ U-5：★ except_reset 已禁用（★ 禁写范围内不覆盖写载体）")
        budget.end_stage("except_baseline")

        # ---- ★★ QC179 / v7 §2.1 U-2：★ **跑前冻结**母本基线 ----
        #   ★ 在启动前计算源目录完整逐件 SHA ⇒ 存入模块级容器。
        #   ★ finally 只引用此不可变基线、不再现采源树。
        #   ★ 枚举失败/缺树/截断均显式失败（★ walk_errors 非空 ⇒ 基线不成立）。
        budget.begin_stage("mother_freeze")
        _mother_src_dir = None
        _rc_for_mother = TRIP_CARRIER.get("receipt") or created_receipt
        if _rc_for_mother and _rc_for_mother.get("source_dir"):
            _mother_src_dir = _rc_for_mother["source_dir"]
        elif args.carrier_handover:
            try:
                _hv_m = json.loads(Path(args.carrier_handover).read_text(
                    encoding="utf-8"))
                if isinstance(_hv_m, dict) and _hv_m.get("source_dir"):
                    _mother_src_dir = _hv_m["source_dir"]
            except Exception:
                pass
        if _mother_src_dir and Path(_mother_src_dir).is_dir():
            _m_walk_errs: list = []
            FROZEN_MOTHER_BASELINE[0] = sha256_dir_tree(
                Path(_mother_src_dir), walk_errors=_m_walk_errs)
            FROZEN_MOTHER_ERRORS.extend(_m_walk_errs)
            rec.add("MOTHER", "frozen_at", now_iso(), "script:main",
                    note="★ QC179/U-2：★ 跑前冻结（★ finally 只引用此基线）")
            rec.add("MOTHER", "frozen_source", _mother_src_dir, "script:main")
            rec.add("MOTHER", "frozen_file_count",
                    len(FROZEN_MOTHER_BASELINE[0]), "script:main")
            rec.add("MOTHER", "frozen_walk_errors", len(_m_walk_errs),
                    "script:main",
                    note="★ 非空 ⇒ 枚举不完整 ⇒ 基线不成立 ⇒ 硬停")
            if _m_walk_errs:
                rec.add("MOTHER", "frozen_baseline_ok", False, "script:main",
                        note="★ 枚举失败 ⇒ 基线不成立")
                _main_return_code = EXIT_INTERNAL_ERROR
                return EXIT_INTERNAL_ERROR
        else:
            rec.add("MOTHER", "frozen_baseline_missing", True, "script:main",
                    note="★ 无母本源目录 ⇒ 无基线 ⇒ 清单失败 ⇒ 拒删")
        rec.add("MOTHER", "frozen_baseline_ok",
                bool(FROZEN_MOTHER_BASELINE[0] is not None
                     and len(FROZEN_MOTHER_ERRORS) == 0),
                "script:main")
        budget.end_stage("mother_freeze")

        # ---- ① 直启 + `S-4` 闸门 ----
        budget.begin_stage("launch")
        # ★★ 第 2 项：★ 令牌**预先**建好并传入；★ `Popen` 一成功即登记 proc。
        #   ★ 故"登记后异常/时间查询失败/启动函数返回失败"三条路径，
        #     ★ `finally` 都能从 `LAUNCH_TOKEN` 拿到进程。
        # ★★ [U8 20261021] 授权判定（★ 双键，fail-closed；缺省 False ⇒ 逐字原行为）。
        _u8_authorized = allow_loader_authorized(args, TRIP_ID)
        # ★★ [A8] 同步到模块级容器（★ 早于 launch，★ 保证 finally 一定读得到）。
        A8_ALLOW_LOADER[0] = bool(_u8_authorized)
        rec.add("LAUNCH", "u8_allow_loader_authorized", _u8_authorized,
                "script:allow_loader_authorized",
                note="★★ [U8] 双键授权判定结果（--allow-loader 且 --trip-id 逐字匹配）")
        proc = launch_direct(rec, budget, carrier_dir, LAUNCH_TOKEN,
                             allow_loader=_u8_authorized)
        launch_pid = LAUNCH_TOKEN.pid
        launch_ct = LAUNCH_TOKEN.ct        # ★ 启动时**冻结**的基线（★ 不重取）
        # ★★ [U8] 授权时按名解析也必须查 loader（proc.pid 是 loader 自己的 pid）。
        pid = resolve_pid(rec, proc, launch_ct,
                          expect_name=(ALLOW_LOADER_EXE if _u8_authorized
                                       else "gamemd.exe"))
        # ★★ [U8] 授权时闸门命中降级为 WARN；未授权时逐字原行为。
        if not s4_injection_gate(pid, rec, authorized=_u8_authorized):
            rec.add("S4", "trip_verdict", "VOID", "script:main",
                    note="★★ 闸门不过 ⇒ 本趟作废（★ 模块表原文已落盘）")
            # ★★ QC184：★ 退出码**直接**取闸门写入 `S4_VERDICT` 的判定值。
            #   ★ 旧做法反读 `s4_module_table.txt` 的文字去猜 62/63：
            #     (a) `read_text` 会抛 `OSError`/`FileNotFoundError`（★ 未捕获）；
            #     (b) 文字匹配不是判定依据。★ 现一律以判定容器为准。
            _s4_code = S4_VERDICT["exit_code"]
            if _s4_code not in (EXIT_INJECTION_SUSPECTED, EXIT_MODULE_ENUM_FAILED):
                # ★★ fail-closed：★ 容器无有效判定值 ⇒ 取**最严**的 63。
                _s4_code = EXIT_MODULE_ENUM_FAILED
            rec.add("S4", "s4_exit_code", _s4_code, "script:main",
                    note="★★ 63 = 枚举失败/截断/不完整/不可判定；62 = 命中")
            _main_return_code = _s4_code
            return _main_return_code
        budget.end_stage("launch")

        # ---- ⑤ 启动观测 ----
        budget.begin_stage("window")
        hwnd, win_info = None, []
        deadline = time.monotonic() + STAGE_TIMEOUT_S
        while time.monotonic() < deadline:
            hwnd, win_info = find_main_window(pid)
            if hwnd:
                break
            time.sleep(0.25)
        rec.add("WIN", "windows", win_info, "script:find_main_window")
        if not hwnd:
            rec.add("WIN", "main_window_found", False,
                    "script:find_main_window",
                    note="★ 主窗未出现 ⇒ 硬停")
            _main_return_code = EXIT_WINDOW_NOT_FOUND
            return EXIT_WINDOW_NOT_FOUND
        # ★★ QC187/T7 补丁：窗口尺寸稳定后再继续（T5 教训：采到“启动态”464×191）。
        #   连续 3 次读矩形（≈1.5s）不变才算稳定；上限 = window 阶段 deadline；
        #   到期仍未稳定 ⇒ 如实继续（帧按实测记录，绝不造假）。
        _stab_t0 = time.monotonic()
        _stab_rect = rect_of(hwnd)
        _stab_same = 0
        _poll = 0
        _esc_sent = 0
        _pid_dead_streak = 0      # [FAILFAST] 连续 pid_alive=False 计数
        # ★★ QC189/T11：T10 实测 main 作用域无 user32 别名（NameError @:3356）⇒ 改用局部 _u32。
        _u32 = ctypes.windll.user32
        _u32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, wt.WPARAM]
        _u32.keybd_event.restype = None
        # ★★ QC191/T13：诊断采集用 argtypes（★ 不改 rect_of / find_main_window）。
        _u32.IsWindow.argtypes = [wt.HWND]
        _u32.IsWindow.restype = wt.BOOL
        _u32.IsWindowVisible.argtypes = [wt.HWND]
        _u32.IsWindowVisible.restype = wt.BOOL
        _u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
        _u32.GetWindowRect.restype = wt.BOOL
        _stab_rect_series = []
        _stab_series_truncated = False
        _esc_send_times = []
        _early_frame_done = False
        _win_boundary_done = False
        _win_boundary_data = None
        _win_boundary_render = None
        _win_ok_prev = True
        # ★★ QC188/T10：T9 实测窗口在片头阶段稳定于 464×191（影片分辨率），
        #   “连续不变”会过早收敛 ⇒ 判据升级为“达到采帧口径 (FRAME_W, FRAME_H) 且连续 2 次不变”；
        #   未达标期间每 ~4s 补一次 Esc 跳片（★ QC197/P6：上限 6→2 次，全部记账；
        #   bench 口径，MENU_NAV_DESIGN_v1.md:§3.2 Esc 纪律——Esc 只允许出现在
        #   片头期，点击 3（開始遊戲）之后永久禁 Esc）；
        #   deadline 到期仍未达标 ⇒ 如实继续（帧按实测记录，绝不造假）。
        # ★★ D-113：「如实继续」结构不可达 —— `deadline`（`:3335`）同时被“等主窗出现”
        #   与“等窗口达 800×600”使用，而 `:3390 budget.end_stage("window")` 在
        #   `dt > STAGE_TIMEOUT_S` 时无条件 `sys.exit(EXIT_STAGE_TIMEOUT)` ⇒ 等到
        #   deadline 必然越阶段硬停，上面那句“如实继续”永远到不了。
        #   现把「等待达标」的上限与阶段硬停**解耦**：稳定等待只用到阶段截止前 2.0 s，
        #   留出余量让 `end_stage("window")` 仍可**正常**通过并继续（★ 不改
        #   STAGE_TIMEOUT_S / TRIP_BUDGET_S / MAX_LAUNCHES / end_stage / 退出码表）。
        _stab_deadline = min(deadline, budget.stage_t0 + STAGE_TIMEOUT_S - 2.0)
        while _stab_same < 2 and time.monotonic() < _stab_deadline:
            time.sleep(0.5)
            _poll += 1
            _sr = rect_of(hwnd)
            _pid_alive_now = _pid_alive_check(pid)   # [FAILFAST] 单次取样，供字典与判定共用
            # ★ QC191/T13：逐轮诊断采集（★ 不改控制流）。
            if len(_stab_rect_series) < 240:
                _gwr_r = wt.RECT()
                _gwr_ok = bool(_u32.GetWindowRect(hwnd, ctypes.byref(_gwr_r)))
                _stab_rect_series.append({
                    "t": round(time.monotonic() - _stab_t0, 3),
                    "rect": list(_sr),
                    "win_ok": bool(_u32.IsWindow(hwnd)),
                    "vis": bool(_u32.IsWindowVisible(hwnd)),
                    "gwr_ok": _gwr_ok,
                    "esc_before": _esc_sent,
                    "pid_alive": _pid_alive_now,
                })
            else:
                _stab_series_truncated = True
            # >>> FAILFAST-BEGIN（Notion 裁决1 附加项；补丁副本制）
            # ★ 背景：L1 五趟失败时 gamemd 在 t=5.188s 就自行退出，但 harness 继续对
            #   死 PID 空转 148 秒并产出 140 张错误截图（实为桌面区域）。此处补 fail-fast。
            # ★ 纪律：仅在**连续 2 次** pid_alive 明确为 False 时触发（不用 None，
            #   因为 None = OpenProcess 失败/权限问题，不等于进程已死）。
            #   退出前把退出码与时刻记进字段，便于事后归因。
            if _pid_alive_now is False:
                _pid_dead_streak += 1
            else:
                _pid_dead_streak = 0
            if _pid_dead_streak >= 2:
                _dead_ec = _pid_exit_code(pid)
                rec.add("WIN", "pid_dead_failfast", {
                    "t_dead": round(time.monotonic() - _stab_t0, 3),
                    "pid": pid,
                    "exit_code": _dead_ec,
                    "esc_sent_before_death": _esc_sent,
                    "polls_before_death": _poll,
                    "rect_before_death": list(_sr),
                }, "script:_pid_alive_check",
                        note="★ FAILFAST：连续 2 次 pid_alive=False ⇒ 主进程已自行退出，"
                             "不再对死 PID 空转；退出码 EXIT_PID_DEAD=29")
                raise SystemExit(EXIT_PID_DEAD)
            # <<< FAILFAST-END
            # >>> QC151FS-BEGIN stab-arrive（缺省 off ⇒ 锚矩形判据逐字保留）
            # ★★ QC151FS：全屏 ⇒ 到达**不依赖 800×600 窗口尺寸**（全屏窗=整屏），
            #   改桌面拷贝帧内容判据（`_fs_arrival_poll`：判定臂=主菜单签名，
            #   非黑门内；遥测臂=非黑∧差≥FS_LOGO_DIFF_MIN 不判定）；失败轮如实
            #   记账不硬停（D-113「如实继续」语义原样保留，Esc 纪律路径共用）。
            if _QC151FS["on"]:
                try:
                    _sz_ok = _fs_arrival_poll(hwnd, rec, load_qc95(rec))
                except Exception as _fs_e:
                    _QC151FS["poll_errs"].append(
                        {"kind": "poll", "err": repr(_fs_e)})
                    _sz_ok = False
            else:
                _sz_ok = ((_sr[2] - _sr[0], _sr[3] - _sr[1]) == (FRAME_W, FRAME_H))
            # <<< QC151FS-END stab-arrive
            if _sz_ok:
                _stab_same += 1
            else:
                _stab_same = 0
                if _poll % 8 == 0 and _esc_sent < 2:   # ★ QC197/P6：Esc 上限 6→2（bench 口径；MENU_NAV_DESIGN_v1.md:§3.2 Esc 纪律）
                    _u32.keybd_event(0x1B, 0, 0, 0)
                    _u32.keybd_event(0x1B, 0, 2, 0)
                    _esc_sent += 1
                    _esc_send_times.append(round(time.monotonic() - _stab_t0, 3))
            # QC192/T14-D-a: early frame capture on first w>200 && visible.
            try:
                if not _early_frame_done:
                    _ef_w = _sr[2] - _sr[0]
                    _ef_vis = bool(_u32.IsWindowVisible(hwnd))
                    if _ef_w > 200 and _ef_vis and (_sr[0] != 0 or _sr[1] != 0 or _sr[2] != 0 or _sr[3] != 0):
                        _early_frame_done = True
                        _ef_path = WORKDIR / "frame_early_01.png"
                        _ef_ok, _ef_wh = capture_frame(hwnd, _ef_path)
                        _ef_bytes = None
                        _ef_sha = None
                        _ef_err = None
                        try:
                            _ef_data = _ef_path.read_bytes()
                            _ef_bytes = len(_ef_data)
                            _ef_sha = hashlib.sha256(_ef_data).hexdigest()
                        except Exception as _ef_e:
                            _ef_err = str(_ef_e)
                        rec.add("WIN", "early_frame", {
                            "t": round(time.monotonic() - _stab_t0, 3),
                            "rect": list(_sr),
                            "path": str(_ef_path),
                            "bytes": _ef_bytes,
                            "sha256": _ef_sha,
                            "capture_ok": _ef_ok if _ef_err is None else None,
                            "error": _ef_err,
                            "wh": _ef_wh,
                        }, "script:capture_frame",
                                note="QC192/T14-D-a: first frame while window alive")
            except Exception:
                pass
            # QC192/T14-D-c: full system window scan on first win_ok true->false.
            try:
                _cur_win_ok = bool(_u32.IsWindow(hwnd))
                if _win_ok_prev and not _cur_win_ok and not _win_boundary_done:
                    _win_boundary_done = True
                    _win_boundary_data = _sys_window_scan()
                    _win_boundary_render = _render_log_probe(carrier_dir)
                _win_ok_prev = _cur_win_ok
            except Exception:
                pass
            _stab_rect = _sr
        # ★ QC191/T13：稳定性循环诊断序列 + 复枚举。
        rec.add("WIN", "stab_rect_series", {
            "items": _stab_rect_series,
            "truncated": _stab_series_truncated,
        }, "script:stab_diag",
                note="★ QC191/T13：稳定性循环逐轮诊断（上限 240 条）")
        _reenum_hwnd, _reenum_info = find_main_window(pid)
        _reenum_match = None
        for _wi in _reenum_info:
            if _wi["hwnd"] == hwnd:
                _reenum_match = _wi
                break
        rec.add("WIN", "stab_reenum", {
            "hwnd_still_enumerated": _reenum_match is not None,
            "match_wh": _reenum_match["wh"] if _reenum_match else None,
            "match_visible": _reenum_match["visible"] if _reenum_match else None,
            "enum_count": len(_reenum_info),
        }, "script:find_main_window",
                note="★ QC191/T13：循环后复枚举同 pid 窗口")
        rec.add("WIN", "window_stable_rect", list(_stab_rect), "script:rect_of",
                note="★ QC188/T10：末次窗口矩形（达标=800×600 连续 2 次；到期未达则按实测）")
        rec.add("WIN", "window_stabilize_seconds", round(time.monotonic() - _stab_t0, 3),
                "time.monotonic")
        rec.add("WIN", "esc_skip_sent", _esc_sent, "user32:keybd_event",
                note="★ QC188/T10：未达标期间的 Esc 跳片次数（★ QC197/P6：上限 2）")
        # ★ QC191/T13：取**被选窗**标题（原 `win_info[-1]` 取枚举末项，非被选窗）。
        title = None
        for _wi in win_info:
            if _wi["hwnd"] == hwnd:
                title = _wi["title"]
                break
        rec.add("WIN", "main_window_hwnd", hwnd, "script:find_main_window",
                note="★ QC191/T13：被选中的主窗 hwnd")
        rec.add("WIN", "main_window_found", True, "script:find_main_window")
        rec.add("WIN", "main_window_title", title, "user32:GetWindowTextW",
                note=f"★ 期望 {MAIN_WINDOW_TITLE!r}（QC141:91）")
        # ★ QC191/T13：记录选择依据。
        _pick_match = None
        for _wi in win_info:
            if _wi["hwnd"] == hwnd:
                _pick_match = _wi
                break
        _has_visible_wide = any(
            _wi["visible"] and _wi["wh"][0] > 200 for _wi in win_info
        )
        rec.add("WIN", "main_window_pick", {
            "hwnd": hwnd,
            "wh": _pick_match["wh"] if _pick_match else None,
            "visible": _pick_match["visible"] if _pick_match else None,
            "fallback_used": not _has_visible_wide,
            "enum_count": len(win_info),
        }, "script:find_main_window",
                note="★ QC191/T13：被选窗选择依据")
        f9 = collect_window_fields(rec, hwnd)
        rec.add("WIN", "seconds_to_window", round(budget.elapsed(), 3),
                "time.monotonic", note="★ 期望 ≈0.5 s（QC141:91）")
        # QC192/T14-D-c: window stage end full system window scan.
        _win_end_scan_data = None
        try:
            _win_end_scan_data = _sys_window_scan()
        except Exception:
            pass
        rec.add("WIN", "win_boundary_scan", _win_boundary_data,
                "script:_sys_window_scan",
                note="QC192/T14-D-c: full system scan at first win_ok true->false")
        rec.add("WIN", "win_end_scan", _win_end_scan_data,
                "script:_sys_window_scan",
                note="QC192/T14-D-c: full system scan at window stage end")
        # QC192/T14-D-d: render log growth probe.
        _render_probe_end = None
        try:
            _render_probe_end = _render_log_probe(carrier_dir)
        except Exception:
            pass
        rec.add("WIN", "render_log_probe", {
            "boundary": _win_boundary_render,
            "end": _render_probe_end,
        }, "script:_render_log_probe",
                note="QC192/T14-D-d: ra2render*.log probe (boundary=transition, end=stage end)")
        # QC192/T14-A: Esc send times.
        rec.add("WIN", "esc_send_times", _esc_send_times,
                "user32:keybd_event",
                note="QC192/T14-A: seconds relative to _stab_t0 for each Esc send (round 3)")
        # >>> QC151FS-BEGIN arrival-log（缺省 off ⇒ 零 rec 行）
        # ★★ QC151FS：全屏到达判据逐轮遥测收口（判定臂/遥测臂、阈值、置前
        #   成败、轮询异常全留档 ⇒ T55 复准依据）。
        if _QC151FS["on"]:
            rec.add("WIN", "fs_arrival", {
                "arrived": bool(_QC151FS["arrival"]),
                "thresholds": {"luma_floor": FS_LUMA_FLOOR,
                               "logo_diff_min": FS_LOGO_DIFF_MIN,
                               "consecutive_polls_required": 2},
                "polls": list(_QC151FS["arrival_polls"]),
                "poll_errs": list(_QC151FS["poll_errs"]),
                "fg_attempts": _QC151FS["fg_attempts"],
                "fg_fail": _QC151FS["fg_fail"],
            }, "script:_fs_arrival_poll",
                note="★ QC151FS：全屏到达判据逐轮遥测（判定=主菜单签名×2；"
                     "diff 臂仅遥测——片头影片同样触发，无法单独区分菜单/影片）")
        # <<< QC151FS-END arrival-log
        budget.end_stage("window")

        # ---- ★★ QC197/P4：导航链三段**带闸**子阶段（替换原「3 次逻辑盲点 +
        #      2 次屏坐标盲点」13 行块；`MENU_NAV_DESIGN_v1.md:§4.1-P4`）----
        # ★ Esc 纪律（设计稿 §3.2 / bench ZC-11）：nav 起永久禁 Esc——加载中
        #   ESC×2 会打断开局；本段零 keybd_event（`_focus_foreground` 兜底
        #   ALT=0x12 属 qc63 `focus_hard` 同款前台锁旁路、非 Esc，逐次 trail 记账）。
        rec.add("NAV", "esc_locked", True, "MENU_NAV_DESIGN_v1.md:§3.2",
                note="★ QC197/P6：nav/帧阶段不再发任何 Esc（0x1B）")
        rec.add("META", "DPIaware", True, "script:SetProcessDPIAware",
                note="★ QC197/P1：探针进程已声明 DPI 感知 ⇒ 坐标口径=物理像素")
        _qc95 = load_qc95(rec)
        _nav_verdict = "OK"
        _nav_failed_at = None
        _focus_trail: list = []
        # >>> QC210-BEGIN main-gate（缺省 off ⇒ 本块零行为、零 rec 行）
        # ★★ QC210：开关装载——on 时指位段/帧钟 burst 生效；pid 供 RPM 只读。
        if getattr(args, "spot_select", False):
            _QC210_SPOT["on"] = True
            _QC210_SPOT["pid"] = pid
            rec.add("NAV", "qc210_spot_select_enabled", {"on": True, "pid": pid},
                    "argv:--spot-select",
                    note="★ QC210：显式指位段+帧钟 burst 分类器已启用"
                         "（缺省 off ⇒ 行为与改前逐字节一致）")
        # <<< QC210-END main-gate
        # >>> QC151SG-BEGIN main-arm（缺省零旗标 ⇒ 零置位零行；行为与改前逐字节一致）
        # ★★ QC151SG：--sg-capture / --sg-toggle-x/y 装载——遭遇战设置屏
        #   「短游戏」开关取证+可控点击（T55i 纯取证 / T55j 点击）。
        #   ★ 三旗标全缺省 ⇒ 本块零执行、连 False 记录行都不写（QC210 房规）。
        #   ★ 只给 x 不给 y（或反之）⇒ toggle 不武装（None）、armed 行如实记
        #     incomplete ⇒ 后续零点击（fail-closed，绝不半坐标盲点）。
        _sg_x = getattr(args, "sg_toggle_x", None)
        _sg_y = getattr(args, "sg_toggle_y", None)
        if (getattr(args, "sg_capture", False) or _sg_x is not None
                or _sg_y is not None):
            _QC151SG["capture"] = bool(getattr(args, "sg_capture", False))
            if _sg_x is not None and _sg_y is not None:
                _QC151SG["toggle"] = (int(_sg_x), int(_sg_y))
            rec.add("MEASURE", "sg_skirmish_armed",
                    {"capture": _QC151SG["capture"],
                     "toggle_xy": (list(_QC151SG["toggle"])
                                   if _QC151SG["toggle"] else None),
                     "toggle_coords_incomplete":
                         bool((_sg_x is None) != (_sg_y is None))},
                    "argv:--sg-capture/--sg-toggle-x/--sg-toggle-y",
                    note="★ QC151SG：设置屏取证/点击武装（capture=纯取证 T55i；"
                         "toggle_xy 非 None ⇒ 点击后抓 post（T55j）；坐标=800×600 "
                         "游戏系；点击前另有范围断言+屏幕签名断言，全败即拒点")
        # <<< QC151SG-END main-arm
        for _step, _pre, _post, _chain in NAV_SIG_PLAN:
            _lx, _ly = _chain[1], _chain[2]   # QC197c/D-123: NAV_CHAIN[i] 是三元组(名,x,y)，原嵌套二元解包 (_lx,_ly) 首迭代即 ValueError（GLM 交叉复核查出）
            if _nav_verdict != "OK":
                rec.add("NAV", f"skipped_{_step}", True, "script:nav",
                        note="★ 前段未达预期屏 ⇒ 不盲点（设计稿 §3.4 防误入相邻项）")
                continue
            # >>> QC210-BEGIN nav-spot（nav_setup 成功后、nav_start 点击前；off ⇒ 零执行零行）
            # ★★ QC210：显式指位段——独立小阶段（自限 SPOT_WINDOW_BUDGET_S，
            #   不侵 nav_start 的 30s 阶段预算）；仅 nav_start 迭代且开关 on。
            if _step == "nav_start" and _QC210_SPOT.get("on"):
                budget.begin_stage("spot_select")
                _spot_res = _spot_run(hwnd, rec, _qc95, budget)
                budget.check_trip()
                budget.end_stage("spot_select")
                rec.add("NAV", "spot_run_result", _spot_res, "script:_spot_run",
                        note="★ QC210：指位段汇总（spot_verify_ok 如实，不硬造）")
            # <<< QC210-END nav-spot
            # >>> QC151SG-BEGIN nav-hook（nav_setup 过闸后、nav_start 点击前；
            #   三旗标全缺省 ⇒ 本块零执行零行，行为与改前逐字节一致）
            # ★★ QC151SG 挂点理由（详证见 QC151SG_RECEIPT.md §挂点）：
            #   本块位于 `for _step in NAV_SIG_PLAN` 的 `nav_start` 迭代内、
            #   QC210 nav-spot 块之后——此时 nav_setup 后态签名已过闸
            #   （skirmish_setup 在屏，QC206 absent 否决背书）、spot 段（若
            #   启用）已完成且 S5 验证，而 開始遊戲(nav_start) 点击**尚未发生**
            #   ⇒ 全流程唯一「确认在设置屏 ∧ 改动来得及生效」的缝。
            #   ★ 独立小阶段 sg_skirmish（D-113 同款：自计时不侵 nav_start 帽）。
            if _step == "nav_start" and (_QC151SG["capture"]
                                         or _QC151SG["toggle"] is not None):
                budget.begin_stage("sg_skirmish")
                _sg_res = _sg_skirmish_run(hwnd, rec, _qc95)
                budget.check_trip()
                budget.end_stage("sg_skirmish")
                rec.add("MEASURE", "sg_skirmish_result", _sg_res,
                        "script:_sg_skirmish_run",
                        note="★ QC151SG：设置屏取证/点击汇总（clicked/verify "
                             "如实，不硬造；正确性终验=post 截图+写回 INI 的 "
                             "ShortGame 值，收尾零新代码）")
            # <<< QC151SG-END nav-hook
            budget.begin_stage(_step)
            # ★ 阶段内等待硬上限 = 30 s 阶段帽 − 2.0 s 余量（D-113 教训，同
            #   window 阶段 `_stab_deadline` 口径；帽值本身**不改**）。
            _wall = budget.stage_t0 + STAGE_TIMEOUT_S - 2.0
            _attempts: list = []
            _did_click = False
            _sig_got = None
            _step_ok = False
            for _try in (1, 2):                 # ★ 每步点击 ≤2 次（设计稿 §3.2）
                if time.monotonic() >= _wall:
                    break
                _focus = _focus_foreground(hwnd)
                _focus_trail.append({"step": _step, "try": _try, **_focus})
                rec.add("NAV", f"focus_{_step}", _focus,
                        "qc63_trip.py:187 focus_hard 精简移植",
                        note="★ QC197/P2：每次尝试后校验 GetForegroundWindow()==hwnd")
                _pre_w = wait_screen(hwnd, _pre,
                                     max(0.0, _wall - time.monotonic()),
                                     rec, _qc95, f"{_step}_pre")
                _attempts.append({"try": _try, "focus_ok": _focus["ok"],
                                  "pre_ok": _pre_w["ok"]})
                if not _pre_w["ok"]:
                    continue                    # ★ 前态签名未就绪 ⇒ 不点击（零盲点）
                click_logical(hwnd, _lx, _ly)
                _did_click = True
                rec.add("NAV", f"clicked_{_step}", [_lx, _ly], "QC141:93",
                        note="★ 逻辑坐标（800×600）；★ QC197/P1 后 == 物理像素")
                _doze(NAV_WAITS_S[_step])
                if _post == "battle":
                    _post_w = _burst_battle(hwnd, _wall, rec, _qc95)
                else:
                    _post_w = wait_screen(hwnd, _post,
                                          max(0.0, _wall - time.monotonic()),
                                          rec, _qc95, f"{_step}_post")
                _attempts[-1]["post_ok"] = _post_w["ok"]
                if _post_w["polls"]:
                    _sig_got = _post_w["polls"][-1]["red_centers"]
                _attempts[-1]["signature_got"] = _sig_got
                if _post_w["ok"]:
                    _step_ok = True
                    break
            rec.add("NAV", f"step_clicked_{_step}", _did_click, "script:nav",
                    note="★ QC197/P7：False=前态签名未就绪、未点击（零盲点）")
            rec.add("NAV", f"signature_got_{_step}", _sig_got, "script:wait_screen",
                    note="★ QC197/P7：末轮观测到的红钮中心集（未点击=None）")
            rec.add("NAV", f"verify_ok_{_step}", _step_ok, "script:nav",
                    note="★ QC197/P7：后态签名达标与否")
            rec.add("NAV", f"attempts_{_step}", _attempts, "script:nav",
                    note="★ QC197/P7：逐次尝试（≤2；focus/pre/post+signature_got）")
            budget.check_trip()
            budget.end_stage(_step)
            if not _step_ok:
                # ★ 2 次未达 ⇒ 本趟 INCOMPLETE（帧/签名全留档）；★ 不继续盲点
                #   （设计稿 §3.2/§3.4）；★ 不 sys.exit——帧阶段照采、F-6 如实记。
                _nav_verdict = "INCOMPLETE"
                _nav_failed_at = _step
                break
        rec.add("NAV", "focus_trail", _focus_trail, "script:_focus_foreground",
                note="★ QC197/P2+P7：全部前置焦点尝试（ALT 兜底是否动用逐次可见）")
        rec.add("NAV", "verdict", _nav_verdict, "script:nav",
                note="★ QC197/P7：INCOMPLETE ⇒ 帧阶段照采、F-6 如实记（不 sys.exit）")
        if _nav_failed_at:
            rec.add("NAV", "failed_at", _nav_failed_at, "script:nav")

        # ---- ⑦ 采帧（★ 只采目标图帧；`QC157:1`） ----
        budget.begin_stage("frame")
        # ★★ QC187/T7 补丁：采帧前二次稳定确认（连续 2 次矩形不变 ≈1s；上限=window deadline 余量）。
        _cap_rect = rect_of(hwnd)
        _cap_wait = 0
        # ★★ QC188/T10：采帧前须达采帧口径矩形；到期未达 ⇒ 按实测采帧（帧检查如实记录）。
        # ★★ D-113：此处**刻意沿用**原 `deadline`（不换成 `_stab_deadline`）——
        #   本循环在 `begin_stage("frame")` 之后，阶段计时已重置，不受 window 阶段
        #   硬停约束；且“等不到 800×600 就不采帧”会更糟（无帧可记），故上限保持
        #   原样、到点按实测采帧（与 `:3416` 记账口径一致）。
        while (_cap_rect[2] - _cap_rect[0], _cap_rect[3] - _cap_rect[1]) != (FRAME_W, FRAME_H) and time.monotonic() < deadline:
            time.sleep(0.5)
            _cap_rect = rect_of(hwnd)
            _cap_wait += 1
        rec.add("FRAME", "pre_capture_rect", list(_cap_rect), "script:rect_of",
                note="★ QC188/T10：采帧前窗口矩形（须达 800×600；到期未达则按实测采帧）")
        rec.add("FRAME", "pre_capture_wait_polls", _cap_wait, "script:rect_of")
        frames = capture_target_frame(rec, hwnd, WORKDIR)
        budget.end_stage("frame")

        # ---- ★★ QC202/C1（MEASURE_DESIGN_v1.md §2.1/§5）：measure 阶段簇 ----
        #   ★ 插入点 = frame 段末与 fields_post 之间（设计稿 §2.1）。
        #   ★ 仅 `--measure` 非 0 且 `NAV.verdict=="OK"`（burst 闸全绿）才执行；
        #     ★ `--measure` 缺省 0 ⇒ 本块整体零执行（零 rec 行、零落盘），
        #       门禁行为语义与 T24（锚 e4f87b96）完全一致（§2.1 flag-off 等价）。
        #   ★ 采样器一切异常内部捕获（§5.4）⇒ 不改进图闸语义、
        #     退出码表不加新码（§5.2）；工具与协议见 §10.8。
        # >>> QC213-BEGIN arm（缺省 off：仅 --measure≠0 且 nav 全绿时随窗激活）
        if getattr(args, "measure", 0) and _nav_verdict == "OK":
            _QC213_PROBE["on"] = True
            rec.add("MEASURE", "qc213_probe_armed", {"on": True},
                    "argv:--measure",
                    note="★ QC213：per-house 运行期探针随 measure 窗激活"
                         "（帧钟闩锁 300/600/1800 各一次 + 冻结≥2s 补 final；"
                         "缺省 off 零执行零行）")
        # <<< QC213-END arm
        # >>> QC213P2-BEGIN arm（缺省 off：仅 --measure≠0 且 nav 全绿时随窗激活）
        if getattr(args, "measure", 0) and _nav_verdict == "OK":
            _QC213P2_PROBE["on"] = True
            rec.add("MEASURE", "qc213p2_probe_armed", {
                "on": True,
                "ladder": list(QC213P2_LADDER),
                "ladder_n": len(QC213P2_LADDER),
                "ladder_cap": QC213P2_LADDER_CAP,
                "ladder_dropped": QC213P2_LADDER_DROPPED,
                "ladder_src_n": len(QC213P2_LADDER_SRC),
                "freeze_s": QC213P2_FREEZE_S,
                "err_cap": QC213P2_ERR_CAP,
            }, "argv:--measure",
                note="★ QC213P2：败北触发链探针随 measure 窗激活（P1/P2/P3/P5 + "
                     "P4 逐帧阶梯 + 首拍 early）；" + QC213P2_LADDER_NOTE +
                     "；★ 阶梯源常量 QC213P2_LADDER_SRC 可配；>cap 自动截断"
                     "（丢弃帧数如实记）；缺省 off 零执行零行")
        # <<< QC213P2-END arm
        # >>> QC151P3-BEGIN arm（缺省 off：--frozen-dump 缺省 False ⇒ 零置位零行；
        #   --probe-frames 缺省 "300,600,1800" == 锚 QC213_LATCH_FRAMES ⇒ 零行为差）
        if getattr(args, "measure", 0) and _nav_verdict == "OK":
            if tuple(args.probe_frames) != QC213_LATCH_FRAMES:
                # ★ QC151P3：锁存帧阶梯（仅非锚缺省才置位留痕；缺省 ⇒ 零置位零行）
                _QC213_PROBE["latch_frames"] = tuple(args.probe_frames)
                rec.add("MEASURE", "qc151p3_probe_frames",
                        {"latch_frames": list(args.probe_frames),
                         "anchor_default": list(QC213_LATCH_FRAMES)},
                        "argv:--probe-frames",
                        note="★ QC151P3：锁存帧阶梯（P3 趟衰变曲线：每帧点全四屋"
                             "快照抓车辆归零衰变；frozen_final 逻辑不变）")
            if args.frozen_dump:
                # ★ QC151P3：dump 语义=主线程终态可终审「记分板等输入（良性）vs
                #   真挂死」；喂目标② 0x4FC9E0 指令级定谳（栈解析一律离线）。
                _QC151P3_STATE["on"] = True
                _QC151P3_STATE["pid"] = pid   # ★ dump 目标 pid（arm 时冻结；dump 时不再按名重查）
                rec.add("MEASURE", "qc151p3_frozen_dump_armed",
                        {"on": True, "pid": pid, "dir": str(WORKDIR)},
                        "argv:--frozen-dump",
                        note="★ QC151P3：冻结触发 ⇒ dbghelp!MiniDumpWriteDump 抓"
                             " frozen_f<frame>.dmp（MiniDumpNormal；rec 只记"
                             " 路径/字节数/pid/frame）")
        # <<< QC151P3-END arm
        if getattr(args, "measure", 0):
            if _nav_verdict == "OK":
                # ★ QC208：传入游戏主窗 hwnd（QC208-②③取证的焦点/标题来源）
                _measure_run(rec, budget, pid, WORKDIR, target_sha, hwnd)
            else:
                # ★ 设计稿 §5.4：nav 未全绿 ⇒ 跳过 measure（连窗都不开）
                rec.add("MEASURE", "skipped", {
                    "reason": "nav_verdict!=OK", "nav_verdict": _nav_verdict,
                    "windows_run": 0}, "script:main",
                    note="★ MEASURE_DESIGN_v1.md:§5.4（退出语义表第 1 行）")

        # >>> QC213-BEGIN finalize（探针随 measure 窗收口；缺省 off 零行）
        if _QC213_PROBE["on"]:
            _QC213_PROBE["on"] = False
            rec.add("MEASURE", "qc213_probe_final", {
                "latched": sorted(_QC213_PROBE["latched"].keys()),
                "latched_n": _QC213_PROBE["latched_n"],
                "frozen_done": _QC213_PROBE["frozen_done"],
                "snapshots": list(_QC213_PROBE["snapshots"]),
                "err": _QC213_PROBE["err"], "errs": _QC213_PROBE["errs"],
            }, "script:_qc213_tick",
                note="★ QC213：探针收口汇总（未闩档＝measure 窗内未达该帧号，"
                     "如实缺；probe_error 行见上，只记不抛）")
        # <<< QC213-END finalize
        # >>> QC213P2-BEGIN finalize（探针随 measure 窗收口；缺省 off 零行）
        if _QC213P2_PROBE["on"]:
            _QC213P2_PROBE["on"] = False
            rec.add("MEASURE", "qc213p2_probe_final", {
                "latched": sorted(_QC213P2_PROBE["latched"].keys(),
                                  key=lambda s: int(s)),
                "latched_n": _QC213P2_PROBE["latched_n"],
                "ladder_n": len(QC213P2_LADDER),
                "ladder_dropped": QC213P2_LADDER_DROPPED,
                "early_done": _QC213P2_PROBE["early_done"],
                "first_frame": _QC213P2_PROBE["first_frame"],
                "last_frame": _QC213P2_PROBE["last_frame"],
                "frozen_done": _QC213P2_PROBE["frozen_done"],
                "snapshots": list(_QC213P2_PROBE["snapshots"]),
                "err": _QC213P2_PROBE["err"], "errs": _QC213P2_PROBE["errs"],
            }, "script:_qc213p2_tick",
                note="★ QC213P2：探针收口汇总（未闩档＝measure 窗内未达该帧号，"
                     "如实缺；ladder_dropped>0 见 arm 行 note；"
                     "probe_error 行见上，只记不抛）")
        # <<< QC213P2-END finalize
        # ---- ⑥ `F-1`…`F-9`（跑后） ----
        budget.begin_stage("fields_post")
        fp = collect_F_fields(rec, carrier_dir, target_map, target_sha, "post")
        fp["F-6"] = {"name": "in_tactical",
                     "value": frames["target"]["L_A_in_tactical"],
                     "note": "★ 来自 L-A（qc95_classify）；★ 分辨率不符 ⇒ null"}
        fp["F-7"] = {"name": "frame_map_panel", "value": None,
                     "needs_human": True,
                     "note": "★★ **人工读图、非自动判据**（QC141:124）⇒ "
                             "记 null，★ 绝不自动编造"}
        fp["F-9"] = f9
        (WORKDIR / "qc151_fields_post.json").write_text(
            json.dumps(fp, ensure_ascii=False, indent=1), encoding="utf-8")
        rec.add("F", "F-6", fp["F-6"], "script:collect_F_fields")
        rec.add("F", "F-7", fp["F-7"], "QC141:124")
        rec.add("F", "F-9", fp["F-9"], "script:collect_window_fields")
        budget.end_stage("fields_post")

        # ---- ③ `T1` + 逐件比对（★ 收尾在 `finally`；★ 此处只判退出码） ----
        budget.begin_stage("T1")
        t1 = t_snapshot(rec, "T1", WORKDIR / "T1_zero_write.json")
        if not t_diff(rec, t0, t1, WORKDIR / "T0_T1_diff.json"):
            rec.add("T", "zero_write_verdict", "FAIL", "script:t_diff",
                    note="★★ 634 件有差 ⇒ 零写自证失败")
            _main_return_code = EXIT_T0_T1_DIFF
            return EXIT_T0_T1_DIFF
        rec.add("T", "zero_write_verdict", "PASS", "script:t_diff")
        budget.end_stage("T1")

        rec.add("META", "finished", now_iso(), "script:main")
        rec.add("META", "trip_seconds", round(budget.elapsed(), 3),
                "time.monotonic")
        _main_return_code = EXIT_OK
        return EXIT_OK
    except BaseException as exc:
        # ★★ `QC157:4`：★ 允许并鼓励用 `except` **保留原始异常**。
        #   ★ `except BaseException` 覆盖 `SystemExit`/`KeyboardInterrupt`
        #     等提前退出 ⇒ ★ **一条都不绕过收尾**。
        #   ★ body 只做**必要上下文的落盘**，★ **绝不吞**（★ 末尾 `raise`
        #     **原样重抛**）⇒ ★ 由 `finally` 先收尾，异常再向解释器传播。
        write_finalize_error(rec, exc, out_dir=WORKDIR)
        raise
    finally:
        # ★★ `QC162:W2`：★ 收尾失败 ⇒ **真的非 0**。
        #   ★ `finalize_trip` **返回**收尾失败码（`QC162:W2`），
        #     ★ 本行在 `finally` 内、`main()` 的 `return` **已经**发生后执行
        #       ⇒ ★ 只写**模块级容器** `FINALIZE_CODE`（★ 不改已发生的 return）。
        #   ★ 若 `run_guarded_steps` 抛出收尾项异常（★ 原样重抛，不吞）：
        #     ★ 该异常在 `finally` 内发生 ⇒ ★ **未被吞**（`QC157:4`），
        #       且此时**全部收尾项都已跑完**（★ 互不跳过已保证）⇒
        #       ★ 它取代正常返回值向解释器传播 ⇒ **`sys.exit` 非 0**（见
        #       `_main_wrapper`/`__main__`）。
        rec.add("META", "finally_entered", True, "script:main",
                note="★★ QC157:3：全程 finally 已进入（含所有提前返回）")

        # ==== 第 2 项：★ 从**外层可见令牌**取进程（★ 不靠 `proc` 局部变量） ====
        #   ★ `proc` 只在 `launch_direct` **正常返回**后才被赋值；
        #     ★ 若它在登记后抛异常 ⇒ `proc` 仍是 None，★ 但令牌里已有 ⇒
        #     ★ 本行保证**失败路径也外达 finally**（第 2 项要求的第二条）。
        term_proc = LAUNCH_TOKEN.proc if (LAUNCH_TOKEN is not None
                                          and LAUNCH_TOKEN.proc is not None) else proc
        term_pid = LAUNCH_TOKEN.pid if (LAUNCH_TOKEN is not None
                                        and LAUNCH_TOKEN.pid is not None) else launch_pid
        term_ct = LAUNCH_TOKEN.ct if (LAUNCH_TOKEN is not None
                                      and LAUNCH_TOKEN.ct is not None) else launch_ct

        # ==== 第 3 项：★ 终止失败 ⇒ 进**可外达容器**，★ 并计入最终码 ====
        term_ok = None            # ★ None = 不适用（未启动）；True/False = 已判定
        if term_proc is not None and term_pid is not None:
            try:
                term_ok = terminate_owned_process(rec, term_proc, term_pid, term_ct)
                rec.add("TERM", "termination_verdict",
                        "PASS" if term_ok else "FAIL", "script:main")
            except Exception as e:
                term_ok = False
                rec.add("TERM", "termination_verdict", "FAIL", "script:main",
                        note=f"★ 终止异常：{e!r}")
            if not term_ok:
                # ★★ **不**留在 finally 局部变量里（★ 那传不到退出码）
                note_cleanup_failure(
                    EXIT_TERMINATE_FAILED, "script:main:finally",
                    "★ 本趟进程退出未确认 ⇒ 收尾失败（第 3 项）", rec)
        else:
            rec.add("TERM", "termination_verdict", "N/A", "script:main",
                    note="★ 未启动（Popen 未成功/未登记）⇒ 不适用"
                         "（★ 仅此情形；★ 不用于吞掉已启动后的回收责任）")

        # ==== [A8] 授权趟：按载体目录清扫 loader 派生的 gamemd 残留 ====
        #   ★ 只在 A8_ALLOW_LOADER[0] 为真时执行（★ 读模块级容器，不读 try 局部）。
        #   ★★ 残留非 0 ⇒ note_cleanup_failure ⇒ 退出码非 0 ⇒ 该趟 V-fail。
        if A8_ALLOW_LOADER[0]:
            _a8_carrier = (Path(TRIP_CARRIER["dir"]) if TRIP_CARRIER["dir"]
                           else carrier_dir)
            try:
                _a8_res = a8_sweep_carrier_processes(
                    rec, _a8_carrier,
                    term_pid if term_pid is not None else None)
                if _a8_res["remaining"]:
                    note_cleanup_failure(
                        EXIT_TERMINATE_FAILED, "script:main:finally:a8",
                        "★ [A8] 载体目录下仍有 gamemd/ra2loader 残留 %d 个 ⇒ V-fail"
                        % len(_a8_res["remaining"]), rec)
                    rec.add("A8", "a8_verdict", "FAIL", "script:main:finally:a8",
                            note="★★ 残留未清零 ⇒ 本趟判 V-fail")
                else:
                    rec.add("A8", "a8_verdict", "PASS", "script:main:finally:a8",
                            note="★ 零残留（已断言）")
            except Exception as _a8e:
                note_cleanup_failure(
                    EXIT_TERMINATE_FAILED, "script:main:finally:a8",
                    "★ [A8] 清扫异常：%r ⇒ 视为收尾失败" % (_a8e,), rec)
                rec.add("A8", "a8_verdict", "ERROR", "script:main:finally:a8",
                        note="★★ 清扫抛异常 ⇒ V-fail：%r" % (_a8e,))
        else:
            rec.add("A8", "a8_verdict", "N/A", "script:main:finally:a8",
                    note="★ 非授权趟（直启 gamemd，无 loader 派生进程）")

        # ==== 第 1 项：★ 删除链用**本趟实际载体**（★ 创建即登记 ⇒ 可回收） ====
        fin_carrier = Path(TRIP_CARRIER["dir"]) if TRIP_CARRIER["dir"] else carrier_dir
        fin_ownership = ownership
        if fin_ownership is None and TRIP_CARRIER["dir"] is not None:
            fin_ownership = {
                "owned": True, "basis": "created_by_this_trip(partial)",
                "receipt_path": None, "files_match": None,
                "note": "★ 创建阶段中途失败，但目录已由本趟 mkdir 建立"
                        "⇒ 仍属本趟 ⇒ 纳入回收（§2.4）"}

        try:
            # ★ U-6：★ 传 _main_return_code 使 final manifest 区分整趟 PASS
            # ★★ QC179 / v7 §2.1 U-2：★ **引用跑前冻结的不可变母本基线**
            #   （★ 不再现采源树 ⇒ 不能声称"跑前基线"而实际是收尾快照）。
            #   ★ 若冻结时未成功（源不存在/枚举失败）⇒ _mother_bl = None
            #     ⇒ manifest_ok=False ⇒ U-1 门控拒删。
            _mother_bl = FROZEN_MOTHER_BASELINE[0]
            if _mother_bl is None:
                rec.add("MOTHER", "frozen_baseline_absent_in_finally", True,
                        "script:main:finally",
                        note="★ QC179/U-2：★ 跑前未冻结（启动前即失败/源不存在）"
                             "⇒ 无基线 ⇒ 清单失败 ⇒ 拒删")
            elif FROZEN_MOTHER_ERRORS:
                rec.add("MOTHER", "frozen_baseline_had_walk_errors",
                        len(FROZEN_MOTHER_ERRORS),
                        "script:main:finally",
                        note="★ QC179/U-2：★ 冻结时枚举有错 ⇒ 基线不完整")
                _mother_bl = None  # ★ 枚举不完整 ⇒ 不采信
            else:
                rec.add("MOTHER", "using_frozen_baseline", True,
                        "script:main:finally",
                        note="★ QC179/U-2：★ 引用跑前冻结的不可变基线"
                             "（★ 非收尾现采）")
            # ★ `term_ok is not False`：★ 未启动（None）⇒ 无进程需终止 ⇒ 视为已满足
            FINALIZE_CODE[0] = finalize_trip(
                rec, fin_carrier, bak, t0, pre_except_txt, out_dir=WORKDIR,
                ownership=fin_ownership, terminated_ok=(term_ok is not False),
                main_return_code=_main_return_code,
                mother_baseline=_mother_bl,
                carrier_identity=(TRIP_CARRIER.get("identity")),
                handover=(Path(args.carrier_handover) if args.carrier_handover
                          else None),
                created_receipt=(TRIP_CARRIER.get("receipt") or created_receipt))
        except Exception as exc:
            # ★★ 收尾项自身抛异常（★ `run_guarded_steps` 已把每个失败的
            #   文件:行·类型·repr 落盘 `finalize_errors.txt` 后**原样重抛**，
            #   `QC157:4`）⇒ ★ 如实记账为收尾失败（★ 不吞、不改写异常本体）。
            note_cleanup_failure(EXIT_INTERNAL_ERROR, "script:main:finally",
                                 f"★ 收尾抛异常：{exc!r}", rec)
            FINALIZE_CODE[0] = merge_cleanup_code(EXIT_OK)
            write_finalize_error(rec, exc, out_dir=WORKDIR)
            raise
        # ★★ 第 3 项：★ 收尾侧合并后的码（★ 成功**不得**清空既有失败）
        FINALIZE_CODE[0] = merge_cleanup_code(EXIT_OK)


def _main_wrapper() -> int:
    """★ 最外层入口。

    ★★ **口径更正（`QC157:4`，★ 用户裁决原话）**：
      ★ 「**`ExceptHandler=0` 不是验收目标；保留原始异常并可靠收尾才是。**」
      ⇒ ★ 本脚本**允许并鼓励**用 `except` 去**保留原始异常**：
        `except BaseException: <落盘必要上下文>; raise`（★ **必须
        **重新抛出**原异常，★ **不得吞**）。
    ★ 现结构（★ 逐处见 `QC157_FIXES.md` 逐子句表）：
      - `main()` 内**一处** `except BaseException` ⇒ 落盘原始异常后 **`raise`**；
      - `main()` 的 `finally` ⇒ 调 `finalize_trip()` 做全程收尾，
        ★ 并把它的返回码（`QC162:W2`）写进**外提容器** `finalize_verdict`；
      - `run_guarded_steps()` 内一处 `except Exception` ⇒ 记账 + 落盘
        `finalize_errors.txt`，★ 跑完全部收尾项后 **`raise` 第一个异常**
        （★ 不吞、不跳过后续项）。
    ★★ `QC162:W2` + `QC169` 第 3 项 —— ★★ **统一合并（★ 本函数）**：
      ★ `main()` **先返回**（`code`，可能是 0，也可能是各提前返回码）；
      ★ 收尾期间的一切失败（终止未确认 24 / 证据验 SHA 25 / 清单 26 /
        拒删·残留 27 / PID 身份不可核验 28 / T0-T1 64 / 还原 65 / 收尾异常 70）
        ★ 已由 `note_cleanup_failure()` 写进**模块级容器** `CLEANUP_FAILURES`
        （★ **不是** finally 局部变量 ⇒ ★ 真的传得出来）；
      ★ `merge_cleanup_code(code)` 按 `CLEANUP_CODE_PRIORITY` 取最高优先级者
        ⇒ ★★ **后续成功项**无论如何**都清不掉既有失败** ⇒ ★ 进程退出码
        **真的非 0**。
      ★ （★ 旧结构只在 `finally` 内改容器变量 / 只把终止失败"记账"，
        ★ 改不了已发生的 `return`，★ 且会被随后 finalize 的成功码覆盖
        —— 外部裁定指出的缺陷，本函数即修复。）
    ★★ 第 3 项末：★ 全部判定**之后**再落最终 JSON/日志
      （★ 修旧序 `dump` 早于末项核验 ⇒ 最终记录早于最终失败码的问题）
      ⇒ ★ 盘上 `qc151_fields.json` / `qc151_run_log.json` 与实际最终码一致。
    ★★ 本卡**不运行**本脚本（铁则 1）。
    ★★ U-6：★ `main()` 重抛时仍须产出明确最终失败记录。
    ★★ QC176 / v6 §6.1.1 U-6（★ 两条）：
      ★ **异常实际退出映射**：★ 盘上同时记录 `final_exit_code`
        （★ `exception_process_exit_code(exc)` = **实际**进程退出码）与
        `internal_verdict_code`（★ 内部合并判定码，通常 70）
        ⇒ ★ 不再把 70 声称为实际最终码；
      ★ **落盘失败传播**：★ `_write_final_records()` 返回**真正写入盘上的码**
        （★ 失败 ⇒ 记账 26 并用该码重写）⇒ ★ 记录与实际退出码**一致**。
    """
    try:
        code = main()
    except BaseException as exc:
        # ★★ QC176 / U-6：★ 两种码**分开记录**（★ 内部判定 vs 实际退出）
        internal_verdict = merge_cleanup_code(EXIT_INTERNAL_ERROR)
        actual_exit = exception_process_exit_code(exc)
        written = _write_final_records(
            actual_exit, internal_verdict_code=internal_verdict, exception=exc)
        FINALIZE_CODE[0] = written
        # ★★ QC179 / v7 §2.1 U-6：★ **不再 bare raise**（★ 原 bare raise
        #   ⇒ :3342-3347 按原异常映射返回，不使用 written/FINALIZE_CODE
        #   ⇒ 盘上记录与实际退出码不同）。
        #   ★ 改为 raise SystemExit(written) from exc ——
        #     ★ 实际退出码 = written（含落盘失败合并）；
        #     ★ 原异常链保留（__cause__ = exc）⇒ traceback 可追溯；
        #     ★ _entry() 捕获 SystemExit ⇒ 直接返回 .code = written。
        raise SystemExit(written) from exc
    # ★★ 统一合并：★ main 返回码 **+** 全部可外达收尾失败
    final = merge_cleanup_code(code)
    FINALIZE_CODE[0] = final
    # ★★ QC176：★ 用**实际写入盘上**的码收口（★ 落盘失败 ⇒ 记账后返回非 0）
    written = _write_final_records(final)
    FINALIZE_CODE[0] = written
    return written


def _emit_final_records(final_code: int, internal_verdict_code: int | None,
                        exception: BaseException | None,
                        rec: Recorder) -> bool:
    """★ 一次**完整**最终落盘（MANIFEST 重写 + 字段总落盘 + run_log）。

    ★★ 三者**同码**：★ 任一步失败 ⇒ ★ 返回 False（★ 由调用方记账并重写）。
    """
    try:
        if not rewrite_final_manifest_with_actual(final_code, rec):
            return False
        rec.add("META", "final_exit_code", int(final_code),
                "script:_write_final_records",
                note="★★ 全部判定**之后**落盘（★ 与**实际最终退出码**一致）")
        if internal_verdict_code is not None:
            rec.add("META", "internal_verdict_code", int(internal_verdict_code),
                    "script:_write_final_records",
                    note="★ QC176/U-6：★ 内部合并判定码（★ **不是**实际进程退出码）")
        if exception is not None:
            rec.add("META", "pending_exception_type", type(exception).__name__,
                    "script:_write_final_records",
                    note="★ QC176/U-6：★ 原异常类型保留（★ 本体见 error.txt）")
        rec.add("META", "cleanup_failures", list(CLEANUP_FAILURES),
                "script:_write_final_records")
        rec.dump(WORKDIR / "qc151_fields.json")
        (WORKDIR / "qc151_run_log.json").write_text(
            json.dumps({"final_exit": int(final_code),
                        "cleanup_failures": list(CLEANUP_FAILURES)},
                       ensure_ascii=False, indent=1), encoding="utf-8")
        return True
    except Exception as e:
        print(f"[WRAPPER] 最终记录落盘失败：{e!r}", file=sys.stderr)
        return False


def _write_final_records(final_code: int,
                         internal_verdict_code: int | None = None,
                         exception: BaseException | None = None) -> int:
    """★★ QC176 / U-6：★ 全部判定**之后**落最终 JSON/日志。

    ★★ **返回真正写入盘上的码**（★ 不再只是 `bool`）：
      ★ 落盘失败 ⇒ ★ `note_cleanup_failure(26)` 记账，★ 并用**该码**再写一次
      ⇒ ★ 盘上记录与进程实际退出码**一致**（★ 不再"先写 0、后改 26"）。
    """
    rec = ACTIVE_REC[0]
    written = int(final_code)
    if rec is None:
        return written
    if not _emit_final_records(written, internal_verdict_code, exception, rec):
        note_cleanup_failure(EXIT_MANIFEST_FAILED, "script:_write_final_records",
                             "★ 最终记录落盘失败 ⇒ 以 26 重写并如实传播", rec)
        written = merge_cleanup_code(EXIT_MANIFEST_FAILED)
        _emit_final_records(written, internal_verdict_code, exception, rec)
    return written


def _entry() -> int:
    """★ 进程入口：★ 返回**实际**退出码（★ 异常路径按 U-6 映射，★ 不再兜底为 1）。

    ★★ QC179 / v7 §2.1 U-6：★ `_main_wrapper` 异常路径改为
      `raise SystemExit(written) from exc` ⇒ ★ 此处捕获 SystemExit
      ⇒ 直接返回 `.code`（= written = 含落盘失败合并的实际最终码）。
      ★ 若 SystemExit 有 `__cause__`（链式原始异常）⇒ 打印原始异常 traceback
        （★ 保留原始异常类型/repr/traceback，★ 满足 v7 裁定要求）。
    """
    try:
        return _main_wrapper()
    except SystemExit as exc:
        # ★★ QC179 / U-6：★ 链式异常 ⇒ 打印原始异常 traceback
        if exc.__cause__ is not None:
            import traceback
            traceback.print_exception(type(exc.__cause__), exc.__cause__,
                                      exc.__cause__.__traceback__)
        c = exc.code
        if c is None:
            return EXIT_OK
        if isinstance(c, int):
            return int(c)
        print(str(c), file=sys.stderr)
        return 1
    except BaseException as exc:                       # ★ 最外层边界（★ 唯一）
        import traceback
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return exception_process_exit_code(exc)


if __name__ == "__main__":
    sys.exit(_entry())
