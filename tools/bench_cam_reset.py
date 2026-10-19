#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bench_cam_reset.py — 箭头键等时闭环机位复位（ZC-11 segE3 移植）+ MAD/NCC 离线校验

协议（ZC-11 segE3 已验证，RESULT_ZC11 §段 E / §[9]②）：
  挪走：RIGHT 1.0s；复位：LEFT 1.0s（等时反向闭环）
  校验：MAD ≤ 2.0 且 NCC ≥ 0.99（静态 ROI / ROADS 逐字节 0 差）
  ★禁止小地图点击复位（ZC-10A FAIL：点击无效时 MAD=0 属空洞成功）
  每档切换后镜头可能被战斗拽走，须可重做对齐（本模块函数可重复调用）

离线自检（不启动游戏）：
  python tools/bench_cam_reset.py --selftest
  python tools/bench_replay.py --cam-selftest
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# ROADS 静态地形 ROI（1366x768 窗口坐标；ZC-9B/zc11common 同源）
ROADS_RECT = (1010, 600, 1230, 730)
# 等时闭环时长（秒）—— segE3 实测口径
LOOP_HOLD_S = 1.0
# 复位验收阈值 —— segE3 实测 MAD 0.13 / NCC 0.996，留安全裕度
MAD_TOL = 2.0
NCC_TOL = 0.99

VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28

DEFAULT_SEGE_DIR = (
    Path(__file__).resolve().parent.parent
    / "out" / "re_work" / "zcode_live" / "zc11" / "evidence" / "segE"
)


# ---------------- 图像度量（纯离线，无 Win32 依赖） ---------------------------

def _load_gray(path) -> "object":
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(path).convert("L")).astype(np.float64)


def mad_ncc(pa, pb, crop_rect=None) -> dict:
    """灰度 MAD + 零均值归一化互相关 NCC（segE_run.mad_ncc 同口径）。

    crop_rect=(x0,y0,x1,y1) 时只在矩形内比较（像素坐标，PIL 顺序）。
    两图均 std=0 时 NCC 记 1.0（常数图完全一致）。
    """
    a = _load_gray(pa)
    b = _load_gray(pb)
    if crop_rect:
        x0, y0, x1, y1 = crop_rect
        a, b = a[y0:y1, x0:x1], b[y0:y1, x0:x1]
    if a.shape != b.shape:
        return {"mad": float("inf"), "ncc": 0.0, "error": f"shape {a.shape} vs {b.shape}"}
    d = abs(a - b)
    va, vb = a.std(), b.std()
    ncc = float(((a - a.mean()) * (b - b.mean())).mean() / (va * vb)) if va > 0 and vb > 0 else 1.0
    return {"mad": round(float(d.mean()), 4), "ncc": round(ncc, 5)}


def mad_ncc_rgb(pa, pb, crop_rect=None) -> dict:
    """RGB 全通道 MAD（ROADS「逐字节 0 差」口径用这个 + 像素 max-delta）。"""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(pa).convert("RGB")).astype(np.int16)
    b = np.asarray(Image.open(pb).convert("RGB")).astype(np.int16)
    if crop_rect:
        x0, y0, x1, y1 = crop_rect
        a, b = a[y0:y1, x0:x1], b[y0:y1, x0:x1]
    if a.shape != b.shape:
        return {"mad": float("inf"), "max_delta": -1, "diff_pixels": -1,
                "error": f"shape {a.shape} vs {b.shape}"}
    delta = abs(a - b)
    per_px = delta.max(axis=2)
    return {
        "mad": round(float(delta.mean()), 4),
        "max_delta": int(per_px.max()),
        "diff_pixels": int((per_px > 0).sum()),
    }


def check_reset_quality(ref, back, *, mad_tol: float = MAD_TOL,
                        ncc_tol: float = NCC_TOL, roads_rect=ROADS_RECT) -> dict:
    """复位验收：全帧 MAD/NCC + ROADS 静态 ROI 逐字节 0 差。"""
    full = mad_ncc(ref, back)
    roads_g = mad_ncc(ref, back, crop_rect=roads_rect)
    roads_rgb = mad_ncc_rgb(ref, back, crop_rect=roads_rect)
    ok = (
        full["mad"] <= mad_tol
        and full["ncc"] >= ncc_tol
        and roads_rgb.get("max_delta") == 0
    )
    return {
        "ok": bool(ok),
        "full": full,
        "roads_gray": roads_g,
        "roads_rgb": roads_rgb,
        "thresholds": {"mad_tol": mad_tol, "ncc_tol": ncc_tol, "roads_max_delta": 0},
    }


# ---------------- 按键（Win32；离线自检不触达） -------------------------------

def hold_key(vk: int, seconds: float, *, poll: float = 0.05):
    """按住 vk 至 seconds 秒后松开（keybd_event，与 bench_replay.press_key 同路径）。"""
    import ctypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.keybd_event(vk, 0, 0, 0)
    try:
        t_end = time.perf_counter() + seconds
        while time.perf_counter() < t_end:
            time.sleep(min(poll, max(0.0, t_end - time.perf_counter())))
    finally:
        user32.keybd_event(vk, 0, 2, 0)
    time.sleep(0.15)


def edge_hold_unused(*_a, **_k):
    """占位：边缘滚屏在 ZC-11 段 E 被判无效（0.16 ≈ 噪声），不提供实现。"""
    raise NotImplementedError("边缘滚屏无效（ZC-11 segE），请用箭头键等时闭环")


# ---------------- 等时闭环复位 -----------------------------------------------

def arrow_closed_loop(hwnd: int, *, shots: Path | None = None, tag: str = "cam",
                      ref: Path | None = None, hold_s: float = LOOP_HOLD_S,
                      move_vk: int = VK_RIGHT, reset_vk: int = VK_LEFT,
                      do_move: bool = True, tries: int = 1,
                      mad_tol: float = MAD_TOL, ncc_tol: float = NCC_TOL,
                      roads_rect=ROADS_RECT, grab_fn=None, settle_s: float = 0.8) -> dict:
    """箭头键等时闭环：挪走 move_vk hold_s 秒 → 等时反向 reset_vk hold_s 秒 → 与 ref 比对。

    - do_move=True（默认）：完整闭环，挪走样本可反证「复位成功」非空洞（moved MAD ≫ 噪声）。
    - do_move=False：只做反向 hold（镜头被战斗拽走后重做对齐的尝试路径）。
    - **不点击小地图**（ZC-10A FAIL 项禁用）。
    - 每档切换后镜头可能被拽走：本函数可重复调用；若 MAD/NCC 不过，调用方应重取 ref
      或重开局对齐（见 docs/re/harness_closeout_zc11.md）。
    """
    # 延迟导入，保持模块离线可 import
    if grab_fn is None:
        import bench_replay as br  # noqa: WPS433
        grab_fn = lambda path: br.grab(hwnd, path)  # noqa: E731

    if shots is not None:
        shots.mkdir(parents=True, exist_ok=True)

    out = {
        "protocol": f"arrow-key move_vk=0x{move_vk:02X} hold={hold_s}s / "
                    f"reset_vk=0x{reset_vk:02X} hold={hold_s}s; minimap excluded",
        "ok": False, "attempts": 0, "hold_s": hold_s,
        "ref": str(ref) if ref else None,
    }
    last = None
    for i in range(max(1, tries)):
        out["attempts"] = i + 1
        moved_path = None
        if do_move:
            hold_key(move_vk, hold_s)
            time.sleep(settle_s)
            if shots is not None:
                m = grab_fn(shots / f"{tag}_moved_{i}.png")
                moved_path = m.get("path") if isinstance(m, dict) else str(m)
        hold_key(reset_vk, hold_s)
        time.sleep(settle_s)
        back_path = None
        if shots is not None:
            m = grab_fn(shots / f"{tag}_back_{i}.png")
            back_path = m.get("path") if isinstance(m, dict) else str(m)

        if ref is None or back_path is None:
            # 无 ref/截图：仅完成动作，调用方自行比对
            last = {"ok": True, "note": "no ref compare (action only)",
                    "moved_path": moved_path, "back_path": back_path}
            out.update(last)
            out["ok"] = True
            return out

        q = check_reset_quality(ref, back_path, mad_tol=mad_tol,
                                ncc_tol=ncc_tol, roads_rect=roads_rect)
        moved_m = mad_ncc(ref, moved_path) if moved_path else None
        last = {"quality": q, "moved_mad": moved_m, "back_path": back_path}
        out.update(last)
        if q["ok"]:
            out["ok"] = True
            return out
    return out


def reset_camera_arrows(hwnd: int, *, shots: Path | None = None, tag: str = "cam",
                        ref: Path | None = None, tries: int = 3, **kw) -> dict:
    """机位复位（箭头键等时闭环版）—— 供 bench_replay 复位/重对齐调用。

    与 ZC-10A `reset_camera`（小地图点击）并列保留，但本实现是 ZC-11 验证过的
    唯一可用复位手段；小地图点击路径继续禁用。
    """
    return arrow_closed_loop(hwnd, shots=shots, tag=tag, ref=ref,
                             do_move=True, tries=tries, **kw)


def realign_camera(hwnd: int, *, shots: Path | None = None, tag: str = "cam_realign",
                   ref: Path | None = None, tries: int = 2, **kw) -> dict:
    """镜头被战斗拽走后的重对齐尝试：只做 LEFT 等时 hold（不做 RIGHT 挪走）。

    若 ref 仍不可达（MAD/NCC 不过），返回 ok=False 并带 quality 供上层决策
    （重取 ref / 重开局）。禁止小地图点击兜底。
    """
    return arrow_closed_loop(hwnd, shots=shots, tag=tag, ref=ref,
                             do_move=False, tries=tries, **kw)


# ---------------- 离线自检 ---------------------------------------------------

def selftest(sege_dir: Path | None = None, *, verbose: bool = True) -> int:
    """用 ZC-11 segE3 真机截图离线复现 MAD/NCC 量级（不启动游戏）。

    期望（segE3_record.json）：
      moved MAD ≈ 13.36（≫ 噪声，非空洞）
      back  MAD ≈ 0.13 ≤ 2.0，NCC ≈ 0.996 ≥ 0.99
      ROADS 静态 ROI max_delta = 0
    """
    sege = Path(sege_dir) if sege_dir else DEFAULT_SEGE_DIR
    ref = sege / "segE3_ref.png"
    if not ref.is_file():
        print(f"[FAIL] 缺 segE3 基准帧: {ref}")
        return 2
    print(f"=== cam reset 离线自检（sege={sege}）===")
    fails = 0
    rows = []
    for i in range(3):
        moved = sege / f"segE3_moved_{i}.png"
        back = sege / f"segE3_back_{i}.png"
        if not (moved.is_file() and back.is_file()):
            print(f"  [FAIL] 缺 segE3 样本 i={i}")
            fails += 1
            continue
        q = check_reset_quality(ref, back)
        mm = mad_ncc(ref, moved)
        rows.append({"i": i, "moved": mm, "quality": q})
        ok_i = q["ok"] and mm["mad"] > 5
        if not ok_i:
            fails += 1
        if verbose:
            print(f"  i={i} moved_MAD={mm['mad']:<8} back_MAD={q['full']['mad']:<8} "
                  f"back_NCC={q['full']['ncc']:<8} "
                  f"ROADS_max_delta={q['roads_rgb'].get('max_delta')} "
                  f"→ {'PASS' if ok_i else 'FAIL'}")
    # 对照：moved vs back 本身（挪走后与复位后应显著不同 → 证明动作有效）
    if rows:
        best = min(rows, key=lambda r: r["quality"]["full"]["mad"])
        print(f"  best back_MAD={best['quality']['full']['mad']} "
              f"NCC={best['quality']['full']['ncc']} "
              f"moved_MAD={best['moved']['mad']}")
        if not best["moved"]["mad"] > 5:
            print("  [FAIL] moved MAD 未远离基准（空洞复位反证失效）")
            fails += 1
    print(f"=== 离线自检 {'PASS' if fails == 0 else f'FAIL ({fails})'} ===")
    return 0 if fails == 0 else 1


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="bench_cam_reset")
    ap.add_argument("--selftest", action="store_true", help="segE3 截图离线自检（不启动游戏）")
    ap.add_argument("--sege-dir", default="", help="segE 证据目录（默认 zc11/evidence/segE）")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest(Path(args.sege_dir) if args.sege_dir else None)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
