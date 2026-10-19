#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_p21_a3.py — ZC-GAP-P21 A3 行为验收：敌方裂缝 + RevealArea2 开图后裂缝是否仍生效

场景图：ra2bench/[2]0GAPP21.yrm（由 tools/gap_p21_map_gen.py 生成安装）
  FogOfWar=yes；玩家基地位于多家环置裂缝候选（GAGAP/CAFARM02）内；
  一条 ElapsedTime=30s 触发器一次性释放 25×RevealAroundWaypoint（TA17 ⇒ RevealArea2）。

判据（逻辑计数为主，像素为辅）：
  before：读全部 CellClass+0x134（GapsCoveringThisCell）⇒ 期望 gapCells>0（裂缝在）
  after ：未打补丁 ⇒ 被开图格 +0x134 归 0（gapCells 显著下降/归零 = 废缝 bug 复现）
          已打补丁 ⇒ +0x134 保持（gapCells 与 before 同量级 = 修复生效）
  另存 before/after 截图 + 差异统计（透亮 vs 黑幕）。

用法：
  python tools/gap_p21_a3.py --calib                          # 开到设置屏截图（定位地图面板/默认图）
  python tools/gap_p21_a3.py --run                            # 完整 A3 跑局（默认做槽位置换）
  python tools/gap_p21_a3.py --run --no-swap                  # 游戏内已选中 GAPP21 时不换图
  python tools/gap_p21_a3.py --analyze before.json after.json # 离线对比两次读数
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "tools"))
import bench_replay as B  # noqa: E402

B.GAME_DIR = PROJECT / "ra2bench"     # 基准环境必须是 ra2bench（B 默认 ra2youli 是 mod/战役目录）

GAME_DIR = PROJECT / "ra2bench"
OUT_DIR = PROJECT / "out" / "re_work" / "zcode_live" / "gap_p21"
MAP_CELLS_PTR = 0x0087F924      # MapClass cell 指针数组（CellClass**）
IMAGE_BASE = 0x00400000
MAP_W, MAP_H = 100, 100
MAX_CELLS = 0x40000      # MapClass::MaxCells（平行四边形索引数组上限，YRpp MapClass.h:147）
ADDR_HOUSE_PLAYER = 0x00A83D4C   # HouseClass::Player 指针（TA17/TA16 的 [eax+0x240] 门所在）
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008

# ---- A3 状态注入：在「必然被 TA17 开图覆盖」的格上写 GapsCoveringThisCell ----
#   bench 遭遇战不实例化预置建筑（实测 bld_cells=0，AI 也不造裂缝产生器）⇒ 造不出真
#   敌方 GapGenerator。改为直接对目标格写 +0x134=5（模拟「被敌方裂缝覆盖」），
#   再验证 RevealArea2 的清零 store 是否被 NOP 掉：
#     未打补丁：开图后目标格 +0x134 归 0（bug 复现：开图即废缝）
#     已打补丁：开图后目标格 +0x134 保持 5（修复生效）
#   cells 数组索引 = (y-1)*512 + (x-1)（MaxCells=0x40000=512×512 平行四边形索引），
#   目标取 25 个开图 waypoint 所在格（TA17 必覆盖）。
CELL_IDX_STRIDE = 512
INJECT_TARGET_CELLS = [(90 + dc, 51 + dr) for dr in (-8, -4, 0, 4, 8) for dc in (-8, -4, 0, 4, 8)]


def inject_gap_counts(pid: int, module_base: int, value: int = 5) -> dict:
    """对目标格写 GapsCoveringThisCell=value；返回每格写入前后回读。
    ★bench_replay.open_proc 只开 VM_READ ⇒ 本函数自开带 VM_WRITE 的句柄再写。"""
    import ctypes as c2
    k32 = c2.windll.kernel32
    k32.OpenProcess.restype = c2.wintypes.HANDLE
    k32.OpenProcess.argtypes = [c2.wintypes.DWORD, c2.wintypes.BOOL, c2.wintypes.DWORD]
    wproc = k32.OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION, False, pid)
    if not wproc:
        return {"error": f"OpenProcess(VM_WRITE) failed err={c2.get_last_error()}"}
    proc_r = B.open_proc(pid)          # 只读句柄（回读用）
    # ★TA17/TA16/RevealArea3 的处理函数都有 [PlayerHouse+0x240]!=0 的整体跳过门
    #   （"地图已全开"标志）。若该标志已置位，开图动作会直接返回成功而不揭示。
    #   故注入时顺带清掉它（否则 RevealArea2 根本不会被调用，补丁无可测）。
    house = B.rpm_u32(proc_r, module_base + (ADDR_HOUSE_PLAYER - IMAGE_BASE))
    reveal_flag = None
    if house:
        b4 = B.rpm(proc_r, house + 0x240, 1)
        reveal_flag = b4[0] if b4 else None
        if reveal_flag:
            z = c2.c_uint8(0)
            got0 = c2.c_size_t(0)
            k32.WriteProcessMemory(c2.wintypes.HANDLE(wproc), c2.wintypes.LPVOID(house + 0x240),
                                   c2.byref(z), 1, c2.byref(got0))
    cells_ptr = B.rpm_u32(proc_r, module_base + (MAP_CELLS_PTR - IMAGE_BASE))
    if not cells_ptr:
        return {"error": "cells ptr null"}
    idxs = [(y - 1) * CELL_IDX_STRIDE + (x - 1) for x, y in INJECT_TARGET_CELLS]
    arr = B.rpm(proc_r, cells_ptr, 4 * (max(idxs) + 1))
    if not arr:
        return {"error": "cells array read failed"}
    ptrs = struct.unpack(f"<{len(arr) // 4}I", arr)
    out = []
    for i in idxs:
        p = ptrs[i]
        if not p:
            out.append({"i": i, "cell": "null"})
            continue
        before = B.rpm(proc_r, p + 0x134, 4)
        buf = c2.c_uint32(value)
        got = c2.c_size_t(0)
        ok = k32.WriteProcessMemory(c2.wintypes.HANDLE(wproc), c2.wintypes.LPVOID(p + 0x134),
                                    c2.byref(buf), 4, c2.byref(got))
        after = B.rpm(proc_r, p + 0x134, 4)
        out.append({"i": i, "ok": bool(ok) and got.value == 4,
                    "before": struct.unpack("<I", before)[0] if before else None,
                    "after": struct.unpack("<I", after)[0] if after else None})
    k32.CloseHandle(wproc)
    return {"targets": len(idxs), "injected": sum(1 for o in out if o.get("ok")),
            "player_house": house, "reveal_flag_before": reveal_flag,
            "detail": out}


def rpm(proc, addr, n):
    return B.rpm(proc, addr, n)


def read_gap_state(proc: int, module_base: int) -> dict:
    """扫描全图 CellClass：+0x12C CopyFlags / +0x130 ShroudCounter / +0x134 GapsCovering。
    ★cells 数组是 0x40000 项的平行四边形索引（100×100 图的合法 cell 散布在前 20000 项），
      不能按 row-major 只读前 W*H 项（旧口径只读到 361 个非空指针，是扫描缺陷不是图小）。"""
    cells_ptr = B.rpm_u32(proc, module_base + (MAP_CELLS_PTR - IMAGE_BASE))
    if not cells_ptr:
        return {"error": "cell array pointer null"}
    # 分块读整个指针数组（单次 1MB ReadProcessMemory 会部分失败）
    ptrs = []
    CHUNK = 4 * 4096
    for off in range(0, 4 * MAX_CELLS, CHUNK):
        buf = B.rpm(proc, cells_ptr + off, CHUNK)
        if not buf:
            return {"error": f"cell array read failed at +0x{off:X}"}
        ptrs.extend(struct.unpack(f"<{CHUNK // 4}I", buf))
    gap_hist: dict[int, int] = {}
    cells = []
    gap_cells = shroud_cells = mapped_cells = bad = 0
    bld_cells = occ_cells = 0
    for i, p in enumerate(ptrs):
        if not p:
            continue
        data = rpm(proc, p + 0x124, 20)   # +0x124 Occ, +0x128 AltOcc, +0x12C CopyFlags, +0x130 Shroud, +0x134 Gaps
        if not data:
            bad += 1
            continue
        occ, altocc, flags, shroud, gaps = struct.unpack("<IIIII", data)
        if altocc & 0x80:
            bld_cells += 1
        if occ:
            occ_cells += 1
        if gaps:
            gap_cells += 1
            gap_hist[gaps] = gap_hist.get(gaps, 0) + 1
            cells.append({"i": i, "g": gaps, "s": shroud})
        if shroud:
            shroud_cells += 1
        if flags & 0x10:
            mapped_cells += 1
    return {
        "gap_cells": gap_cells, "gap_hist": {str(k): v for k, v in sorted(gap_hist.items())},
        "shroud_cells": shroud_cells, "mapped_cells": mapped_cells,
        "bad_ptrs": bad, "nonnull_ptrs": len(ptrs) - ptrs.count(0),
        "bld_cells": bld_cells, "occ_cells": occ_cells,
        "gap_details": cells,
    }


def nav_to_setup(hwnd):
    B.focus_game(hwnd)
    time.sleep(18)
    B.press_key(0x1B); time.sleep(1.2)
    B.press_key(0x1B); time.sleep(2.5)
    B.send_click(hwnd, 700, 218); time.sleep(3.0)
    assert B.verify_screen(hwnd, "sp_submenu")["ok"], "未到單人遊戲子菜单"
    B.send_click(hwnd, 700, 304); time.sleep(9.0)
    assert B.verify_screen(hwnd, "skirmish_setup")["ok"], "未到遭遇战设置屏"


def launch_and_attach(tag: str):
    B.kill_game(); time.sleep(1.5)
    log_mark = (GAME_DIR / "ra2render.log").stat().st_size if (GAME_DIR / "ra2render.log").is_file() else 0
    pid = B.launch()
    proc = B.open_proc(pid)
    hwnd = None
    t_end = time.time() + 20
    while time.time() < t_end and not hwnd:
        hwnd = B.find_game_hwnd(pid)
        time.sleep(0.5)
    assert hwnd, "未找到游戏窗口"
    return pid, proc, hwnd, log_mark


# ---- 槽位移置：把 GAPP21 场景图写进当前选中的地图文件（= [2]0LoadBench_U0800.yrm）----
#   选择态已由 gap_p21_select.py --auto-u800 固定为 U0800（RA2MD.INI ScenIndex 持久化）。
SLOT_MAP = "[2]0LoadBench_U0800.yrm"
SLOT_BAK = OUT_DIR / "map" / "U0800.slotbak.yrm"
LOOSE_MAP = OUT_DIR / "map" / "[2]0GAPP21.yrm"


def map_swap() -> dict:
    """备份当前选中地图文件 → 写入 GAPP21 内容。返回 before/after sha256。"""
    import hashlib
    import shutil
    slot = GAME_DIR / SLOT_MAP
    OUT_DIR.joinpath("map").mkdir(parents=True, exist_ok=True)
    if not SLOT_BAK.is_file():
        shutil.copy2(slot, SLOT_BAK)
    before = hashlib.sha256(slot.read_bytes()).hexdigest()
    shutil.copy2(LOOSE_MAP, slot)
    after = hashlib.sha256(slot.read_bytes()).hexdigest()
    return {"slot": str(slot), "bak": str(SLOT_BAK),
            "before": before, "after": after,
            "gapp21_sha": hashlib.sha256(LOOSE_MAP.read_bytes()).hexdigest()}


def map_restore() -> dict:
    import hashlib
    import shutil
    slot = GAME_DIR / SLOT_MAP
    if not SLOT_BAK.is_file():
        return {"restored": False, "why": "no bak"}
    shutil.copy2(SLOT_BAK, slot)
    return {"restored": True, "sha": hashlib.sha256(slot.read_bytes()).hexdigest()}


def log_tail(log_mark: int) -> list[str]:
    p = GAME_DIR / "ra2render.log"
    if not p.is_file():
        return []
    with open(p, "rb") as f:
        f.seek(log_mark)
        return f.read().decode("utf-8", "replace").splitlines()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", nargs=2, metavar=("BEFORE", "AFTER"))
    ap.add_argument("--no-swap", action="store_true", help="不做槽位置换（游戏内已选中 GAPP21）")
    ap.add_argument("--no-select", action="store_true", help="不进浏览器选图（用当前持久化选择直接开局）")
    ap.add_argument("--settle", type=float, default=25.0, help="开图后等待秒数（reshroud 很慢）")
    ap.add_argument("--pre-delay", type=float, default=0.0, help="开局后等多少秒再读 before（等 AI 造裂缝）")
    ap.add_argument("--poll", type=int, default=0, help="开图前轮询秒数（每 20s 报一次 gap_cells）")
    ap.add_argument("--inject", type=int, default=0, help="开局后向 25 个开图目标格写 GapsCoveringThisCell=该值（0=不注入）")
    ap.add_argument("--post", type=float, default=15.0, help="二段截图再等秒数")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tag = args.tag or datetime.now().strftime("%H%M%S")

    if args.analyze:
        a = json.loads(Path(args.analyze[0]).read_text(encoding="utf-8"))
        b = json.loads(Path(args.analyze[1]).read_text(encoding="utf-8"))
        diff = {
            "before_gap_cells": a.get("gap_cells"), "after_gap_cells": b.get("gap_cells"),
            "before_shroud_cells": a.get("shroud_cells"), "after_shroud_cells": b.get("shroud_cells"),
            "before_hist": a.get("gap_hist"), "after_hist": b.get("gap_hist"),
            "delta_gap_cells": (b.get("gap_cells") or 0) - (a.get("gap_cells") or 0),
        }
        # 逐格对照（before 有缝的格，after 是否仍 >0）
        ga = {(c["x"], c["y"]): c["g"] for c in a.get("gap_details", [])}
        gb = {(c["x"], c["y"]): c["g"] for c in b.get("gap_details", [])}
        kept = sum(1 for k, v in ga.items() if gb.get(k, 0) > 0)
        wiped = sum(1 for k, v in ga.items() if gb.get(k, 0) == 0)
        diff["before_cells_kept_gap"] = kept
        diff["before_cells_wiped"] = wiped
        diff["after_new_gap_cells"] = sum(1 for k, v in gb.items() if k not in ga)
        out = OUT_DIR / f"a3_analyze_{tag}.json"
        out.write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(diff, ensure_ascii=False, indent=2))
        return 0

    rec = {"tag": tag, "ts": datetime.now().isoformat(timespec="seconds")}

    if args.calib:
        pid, proc, hwnd, log_mark = launch_and_attach(tag)
        rec["pid"] = pid
        nav_to_setup(hwnd)
        # 地图列表面板（右侧黑框「作戰 / 地图名」）——先确认开没开：分别抓窗口与全屏
        shot0 = OUT_DIR / f"a3_setup_{tag}.png"
        rec["setup_md5"] = B.grab(hwnd, shot0)["md5"]
        B.send_click(hwnd, 700, 90); time.sleep(4.0)     # 尝试打开地图列表
        shot = OUT_DIR / f"a3_maplist_{tag}.png"
        rec["maplist_md5"] = B.grab(hwnd, shot)["md5"]
        # 全屏抓取（列表可能是覆盖整个游戏窗口的模态层或独立窗）
        try:
            from bench_shot import capture  # type: ignore
            m = capture(0, 0, 1920, 1200, OUT_DIR / f"a3_full_{tag}.png")
            rec["full_md5"] = m.get("md5")
            rec["full_bytes"] = m.get("bytes")
        except Exception as e:  # noqa: BLE001
            rec["full_err"] = str(e)
        rec["gap_log"] = [l for l in log_tail(log_mark) if "GapProtection" in l]
        B.kill_game()
        (OUT_DIR / f"a3_calib_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 0

    if not args.run:
        print("[FAIL] --run 需要")
        return 2

    swap_info = None
    if not args.no_swap:
        swap_info = map_swap()
        rec["map_swap"] = swap_info
        print("[swap]", json.dumps(swap_info, ensure_ascii=False))

    try:
        pid, proc, hwnd, log_mark = launch_and_attach(tag)
        rec["pid"] = pid
        nav_to_setup(hwnd)
        # 槽位移置后地图面板应显示 GAPP21（截图存证；md5 供前后对拍）
        shot_setup = OUT_DIR / f"a3_setup_{tag}.png"
        rec["setup_md5"] = B.grab(hwnd, shot_setup)["md5"]
        rec["setup_shot"] = str(shot_setup)

        # ---- 选中 U0800 槽位（其内容已被换成 GAPP21）→ 使用地圖 ----
        #   选择态只在真正开局/退出设置屏时才写 RA2MD.INI ⇒ 必须与开局同一会话完成。
        #   定位法：滚动条长按翻到 Urban Rush×4 行块，其下一行即 U0800 槽位行。
        #   滚动有 ±2 行抖动 ⇒ 行块可能被窗口边切半分次，按 run 位置自适应补翻。
        UP, DN, USE = (355, 94), (352, 295), (720, 180)
        loc = {"ok": True, "y": 0}
        pb = None
        if not args.no_select:
            B.send_click(hwnd, 700, 304); time.sleep(3.0)          # 自訂戰役 → 浏览器
            B.send_click(hwnd, UP[0], UP[1], hold=12.0); time.sleep(1.0)   # 长按▲回顶
            for _ in range(18):
                B.send_click(hwnd, DN[0], DN[1], hold=0.6)
                time.sleep(0.45)
            time.sleep(0.8)
            from gap_p21_select import find_u0800_row        # type: ignore

            loc = {"ok": False}
            pb = None
            for attempt in range(7):
                pb = OUT_DIR / f"a3_browser_{tag}_{attempt}.png"
                rec[f"browser_md5_{attempt}"] = B.grab(hwnd, pb)["md5"]
                loc = find_u0800_row(pb)
                rec[f"u800_locate_{attempt}"] = loc
                print(f"[locate {attempt}]", json.dumps(loc, ensure_ascii=False))
                if loc.get("ok"):
                    break
                runs = loc.get("runs", [])
                longest = max(runs, key=lambda r: r[2]) if runs else None
                if longest and longest[1] >= 8:          # 行块被底边切开 ⇒ 下翻
                    B.send_click(hwnd, DN[0], DN[1], hold=0.6); time.sleep(0.5)
                elif longest and longest[0] <= 1:        # 行块被顶边切开 ⇒ 上翻
                    B.send_click(hwnd, UP[0], UP[1], hold=0.6); time.sleep(0.5)
                else:
                    B.send_click(hwnd, DN[0], DN[1], hold=0.6); time.sleep(0.5)
            assert loc.get("ok"), "多次补翻后仍未定位到 U800 行"
            rec["browser_shot"] = str(pb)
        if not args.no_select:
            B.send_click(hwnd, 250, int(loc["y"])); time.sleep(1.2)
            B.send_click(hwnd, USE[0], USE[1]); time.sleep(3.0)   # 使用地圖
        shot_setup2 = OUT_DIR / f"a3_setup2_{tag}.png"
        rec["setup2_md5"] = B.grab(hwnd, shot_setup2)["md5"]
        rec["setup2_shot"] = str(shot_setup2)

        B.send_click(hwnd, 700, 262); time.sleep(3.0)          # 開始遊戲

        mon = B.BattleMonitor(proc)
        t_end = time.time() + 120
        in_battle = False
        while time.time() < t_end:
            if mon.wait_in_battle(5) and B.verify_screen(hwnd, "battle")["ok"] and mon.frame() > 200:
                in_battle = True
                break
            time.sleep(2)
        shot_wait = OUT_DIR / f"a3_afterstart_{tag}.png"
        mw = B.grab(hwnd, shot_wait)
        rec["after_start_shot"] = {"md5": mw["md5"], "bytes": mw["bytes"], "path": str(shot_wait)}
        rec["frame_after_start"] = mon.frame()
        print("[after start] frame=", mon.frame(), " md5=", mw["md5"][:12])
        if not in_battle:
            # 诊断：抓屏 + 记录后就退出（不当作 A3 结果）
            B.kill_game()
            (OUT_DIR / f"a3_diag_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            print("[DIAG] 未进对局，存证后退出:", OUT_DIR / f"a3_diag_{tag}.json")
            return 5
        rec["frame_at_start"] = mon.frame()
        rec["gap_log"] = [l for l in log_tail(log_mark) if "GapProtection" in l]

        mods = B.list_modules(pid)
        mod = next(((n, b) for n, b, s in mods if n.lower() == "gamemd.exe"), None)
        assert mod, "gamemd module not found"
        rec["module_base"] = f"0x{mod[1]:08X}"

        # ---- A3 状态注入（bench 造不出真敌方 GapGenerator ⇒ 直接写目标格 +0x134）----
        if args.inject > 0:
            inj = inject_gap_counts(pid, mod[1], args.inject)
            rec["inject"] = {k: v for k, v in inj.items() if k != "detail"}
            rec["inject_detail"] = inj.get("detail")
            print("[inject]", json.dumps(rec["inject"], ensure_ascii=False))

        # ---- before（等 AI 起基地造出裂缝；再读；trigger 尚未到点）----
        if args.pre_delay > 0:
            time.sleep(args.pre_delay)
        before = read_gap_state(proc, mod[1])
        rec["before"] = {k: v for k, v in before.items() if k != "gap_details"}
        shot_b = OUT_DIR / f"a3_before_{tag}.png"
        mb = B.grab(hwnd, shot_b)
        rec["before_shot"] = {"md5": mb["md5"], "bytes": mb["bytes"]}
        print("[before]", json.dumps(rec["before"], ensure_ascii=False))

        # ---- 等触发器开图 + reshroud ----
        time.sleep(args.settle)
        after = read_gap_state(proc, mod[1])
        rec["after"] = {k: v for k, v in after.items() if k != "gap_details"}
        shot_a = OUT_DIR / f"a3_after_{tag}.png"
        ma = B.grab(hwnd, shot_a)
        rec["after_shot"] = {"md5": ma["md5"], "bytes": ma["bytes"]}
        print("[after ]", json.dumps(rec["after"], ensure_ascii=False))

        # ---- 二段（reshroud 很慢，再等一屏）----
        time.sleep(args.post)
        after2 = read_gap_state(proc, mod[1])
        rec["after2"] = {k: v for k, v in after2.items() if k != "gap_details"}
        shot_a2 = OUT_DIR / f"a3_after2_{tag}.png"
        ma2 = B.grab(hwnd, shot_a2)
        rec["after2_shot"] = {"md5": ma2["md5"], "bytes": ma2["bytes"]}
        print("[after2]", json.dumps(rec["after2"], ensure_ascii=False))

        # ---- 存原始逐格数据供离线对比 ----
        (OUT_DIR / f"a3_before_cells_{tag}.json").write_text(
            json.dumps(before.get("gap_details", []), ensure_ascii=False), encoding="utf-8")
        (OUT_DIR / f"a3_after_cells_{tag}.json").write_text(
            json.dumps(after.get("gap_details", []), ensure_ascii=False), encoding="utf-8")

        rec["except_state"] = "exists" if (GAME_DIR / "except.txt").is_file() else "none"
        rec["verdict_hint"] = (
            "PATCH-WORKS" if (before.get("gap_cells") or 0) > 0 and (after.get("gap_cells") or 0) >= before.get("gap_cells")
            else ("NO-GAP-DETECTED" if (before.get("gap_cells") or 0) == 0 else "GAP-WIPED")
        )
    finally:
        B.kill_game()
        if swap_info is not None:
            rec["map_restore"] = map_restore()
            print("[restore]", json.dumps(rec["map_restore"], ensure_ascii=False))

    (OUT_DIR / f"a3_run_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[json]", OUT_DIR / f"a3_run_{tag}.json")
    print("[verdict hint]", rec.get("verdict_hint"))
    return 0 if rec.get("verdict_hint") not in (None, "GAP-WIPED") else 3


if __name__ == "__main__":
    raise SystemExit(main())
