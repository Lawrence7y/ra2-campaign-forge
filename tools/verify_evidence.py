#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/verify_evidence.py — 逆向工程实测证据标准 v3 自动化校验器

依据规范：
  - docs/RE_COORDINATION.md (§🔴 P0 缺陷通报与派工 v6 + 证据标准 v2/v3)
  - docs/re/EVIDENCE_STANDARD.md

核心功能：
  1. PNG 图像深度校验：物理分辨率、文件字节数、80×80 网格均匀采样唯一色数、MD5 全哈希；
  2. 步骤去重与按键推断升级：同验收批次内任何两步哈希碰撞即标该步 FAIL，并输出“疑似按键未生效 / 画面未实质刷新”推断；
  3. 阈值判定（标准 v2 本机实测校准）：
     - 菜单类：体量约 300–400 KB，80×80 采样唯一色数 ≈ 249；
     - 战场类：体量 ≥ 400 KB，80×80 采样唯一色数建议 ≥ 2,000；
     - 色彩退化：采样唯一色数 = 1 时直接判定为伪造单色占位图（FAIL）；
  4. 崩溃零容忍与 EIP 归属判断 (P0 新增)：
     - 检测验收窗口内 ra2youli/except.txt 是否新增/更新；
     - 命中崩溃整批直接判 FAIL；
     - 解析 Error code / Eip / Access address / Esi，自动判断 Eip 归属（ra2render 注入区 vs gamemd 主程序）；
     - 自动保存 except.txt 快照到证据目录 (evidence_except_snapshot.txt)；
  5. 遥测末行生效性断言 (P0 新增)：
     - 解析 ra2youli/ra2render.log 末行遥测（Blit调用 / 像素 / 寻敌扫描 / 迷雾剔除 / 灰雾格子 / 渲染单位 / 建筑剔除 / 弹道剔除 / 小地图灰化像素）；
     - 对断言已开启的特性，若对应遥测计数为 0，标注为 未生效 (UNVERIFIED)，不得判 PASS；
  6. 存档文件 (.SAV) 结构一致性校验：
     - OLE2 Compound File Binary 规范魔数 (D0 CF 11 E0 A1 B1 1A E1) 与小端序 (3E 00)；
  7. 综合判定裁决：输出 JSON 与人类可读 Markdown 报告，给出 PASS / FAIL / UNVERIFIED 状态码。

用法：
  python tools/verify_evidence.py <evidence_dir> [--log <ra2render.log>] [--except-file <except.txt>] [--sav-dir <path>] [--json-out <path>] [--md-out <path>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:
    print("错误: 缺少 Pillow 库，请先执行 pip install pillow", file=sys.stderr)
    sys.exit(1)

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

OLE2_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
OLE2_LITTLE_ENDIAN = bytes.fromhex("3e00")


def compute_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def full_frame_unique_colors(img: Image.Image) -> int:
    """全画面唯一色彩数（口径见 EVIDENCE_STANDARD 附·口径订正 2026-09-28：战场类 ≥800）。

    用 PIL 的 C 实现 getcolors 计数，避免 Python 级 set(getdata()) 在大图上退化。
    """
    try:
        cols = img.convert("RGB").getcolors(maxcolors=1 << 24)
    except Exception:
        return -1
    return -1 if cols is None else len(cols)


def sample_80x80_unique_colors(img: Image.Image) -> int:
    """按 80x80 均匀空间网格采样 6400 个像素点，统计唯一色彩数。"""
    w, h = img.size
    if w <= 0 or h <= 0:
        return 0
    xs = [i * w // 80 for i in range(80)]
    ys = [j * h // 80 for j in range(80)]
    rgb_img = img.convert("RGB")
    pixels = [rgb_img.getpixel((x, y)) for y in ys for x in xs]
    return len(set(pixels))


def classify_scene_type(filename: str) -> str:
    """根据文件名启发式判定是菜单界面还是战场实景。"""
    name_lower = filename.lower()
    menu_keywords = ["menu", "boot", "esc", "lobby", "title", "load", "save_dlg", "dlg", "dialog"]
    battle_keywords = ["battle", "skirmish", "game", "play", "map", "cull", "fog", "vision", "u200", "u800", "combat"]

    for kw in battle_keywords:
        if kw in name_lower:
            return "battlefield"
    for kw in menu_keywords:
        if kw in name_lower:
            return "menu"
    return "unknown"


def verify_savegame_header(path: Path) -> Tuple[bool, str]:
    """校验 .SAV 文件头是否符合 Westwood OLE2 Compound File 规范。"""
    if not path.exists():
        return False, "文件不存在"
    size = path.stat().st_size
    if size < 512:
        return False, f"文件过小 ({size} 字节)，不符合 OLE2 扇区要求"

    with open(path, "rb") as f:
        header = f.read(32)

    magic = header[:8]
    byte_order = header[24:26]

    if magic != OLE2_MAGIC:
        return False, f"魔数不匹配: 期待 {OLE2_MAGIC.hex()}，实际为 {magic.hex()}"
    if byte_order != OLE2_LITTLE_ENDIAN:
        return False, f"字节序不匹配: 期待小端 3E00，实际为 {byte_order.hex()}"

    return True, f"有效 OLE2 存档结构 (大小 {size:,} 字节)"


def parse_except_log(except_path: Path) -> Dict[str, Any]:
    """解析 ra2youli/except.txt 崩溃日志中的核心寄存器与故障地址。"""
    if not except_path.exists():
        return {"exists": False}

    text = except_path.read_text(encoding="utf-8", errors="replace")
    stat = except_path.stat()
    mtime = stat.st_mtime
    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    err_code_m = re.search(r"Error code:\s*([^\r\n]+)", text)
    desc_m = re.search(r"Description:\s*([^\r\n]+)", text)
    access_m = re.search(r"Access address:\s*([0-9a-fA-F]+)", text)
    eip_m = re.search(r"Exception occurred at\s*([0-9a-fA-F]+)", text)
    details_m = re.search(
        r"Eip:([0-9a-fA-F]+)\s+Esp:([0-9a-fA-F]+)\s+Ebp:([0-9a-fA-F]+)\s+Eax:([0-9a-fA-F]+)\s+"
        r"Ebx:([0-9a-fA-F]+)\s+Ecx:([0-9a-fA-F]+)\s+Edx:([0-9a-fA-F]+)\s+Esi:([0-9a-fA-F]+)\s+Edi:([0-9a-fA-F]+)",
        text
    )
    bytes_m = re.search(r"Bytes at CS:EIP \([^)]+\)\s*:\s*([^\r\n]+)", text)

    eip_str = eip_m.group(1) if eip_m else (details_m.group(1) if details_m else "0")
    try:
        eip_val = int(eip_str, 16)
    except ValueError:
        eip_val = 0

    # 判断 EIP 归属
    # ra2render.dll 注入地址通常在 0x54500000 - 0x54600000 或 0x10000000 - 0x10030000
    if 0x54500000 <= eip_val <= 0x545F0000 or 0x10000000 <= eip_val <= 0x10050000:
        attribution = "崩溃归属=ra2render 注入代码"
        is_render_crash = True
    elif 0x00400000 <= eip_val <= 0x008A0000:
        attribution = "崩溃归属=gamemd.exe 主程序"
        is_render_crash = False
    else:
        attribution = f"崩溃归属=未知/系统模块 (Eip: 0x{eip_val:08X})"
        is_render_crash = False

    # 提取调用栈中可能包含的雷达/渲染关键地址
    callsites = []
    if "006574C8" in text:
        callsites.append("0x006574C8 (RadarClass::Refresh 遍历循环内 Plot_Cell 调用点返回)")
    if "0065719F" in text:
        callsites.append("0x0065719F (RadarClass::Refresh 全刷判断返回)")
    if "006D3E37" in text:
        callsites.append("0x006D3E37 (TacticalClass::Render 全量刷新跳转)")

    return {
        "exists": True,
        "path": str(except_path.resolve()),
        "mtime": mtime,
        "mtime_str": mtime_str,
        "bytes": stat.st_size,
        "error_code": err_code_m.group(1).strip() if err_code_m else "UNKNOWN",
        "description": desc_m.group(1).strip() if desc_m else "Unknown crash",
        "access_address": f"0x{access_m.group(1).strip()}" if access_m else "N/A",
        "eip": f"0x{eip_val:08X}",
        "eip_int": eip_val,
        "attribution": attribution,
        "is_render_crash": is_render_crash,
        "registers": {
            "Eip": f"0x{details_m.group(1)}" if details_m else "N/A",
            "Esp": f"0x{details_m.group(2)}" if details_m else "N/A",
            "Ebp": f"0x{details_m.group(3)}" if details_m else "N/A",
            "Eax": f"0x{details_m.group(4)}" if details_m else "N/A",
            "Ebx": f"0x{details_m.group(5)}" if details_m else "N/A",
            "Ecx": f"0x{details_m.group(6)}" if details_m else "N/A",
            "Edx": f"0x{details_m.group(7)}" if details_m else "N/A",
            "Esi": f"0x{details_m.group(8)}" if details_m else "N/A",
            "Edi": f"0x{details_m.group(9)}" if details_m else "N/A",
        } if details_m else {},
        "faulting_bytes": bytes_m.group(1).strip() if bytes_m else "N/A",
        "key_callsites": callsites,
        "raw_snippet": text[:1000]
    }


def parse_telemetry_and_assertions(log_path: Path) -> Dict[str, Any]:
    """解析 ra2youli/ra2render.log 末行遥测数据与生效性断言。"""
    if not log_path.exists():
        return {"checked": False, "reason": "日志文件不存在"}

    text = log_path.read_text(encoding="utf-8", errors="replace")
    stat = log_path.stat()

    # 1. 查找配置加载行
    config_m = re.findall(r"\[ra2render\] 配置加载完成:\s*([^\r\n]+)", text)
    latest_config_str = config_m[-1] if config_m else ""
    config_dict = {}
    if latest_config_str:
        pairs = re.findall(r"(\w+)=([^, \t\r\n\(\)]+)", latest_config_str)
        for k, v in pairs:
            config_dict[k] = v.lower() == "true" if v.lower() in ("true", "false") else v

    # 2. 查找遥测行（支持中英文键名）
    pattern = (
        r"(?:BlitCalls|Blit调用):\s*(\d+).*?"
        r"(?:BlitPixels|像素):\s*([^\s,]+).*?"
        r"(?:TargetScans|寻敌扫描):\s*(\d+).*?"
        r"(?:迷雾剔除机动单位|迷雾剔除):\s*(\d+).*?"
        r"(?:半透明迷雾格子|灰雾格子):\s*(\d+).*?"
        r"(?:渲染单位):\s*(\d+).*?"
        r"(?:建筑剔除):\s*(\d+).*?"
        r"(?:弹道剔除):\s*(\d+).*?"
        r"(?:小地图灰化像素):\s*(\d+)"
    )
    matches = list(re.finditer(pattern, text))
    if not matches:
        return {
            "checked": True,
            "has_telemetry": False,
            "config": config_dict,
            "reason": "日志中未找到遥测计数器输出"
        }

    last = matches[-1]
    g = last.groups()
    telemetry_data = {
        "blit_calls": int(g[0]),
        "blit_pixels": g[1],
        "target_scans": int(g[2]),
        "fog_culled_units": int(g[3]),
        "fog_cells": int(g[4]),
        "rendered_units": int(g[5]),
        "building_culls": int(g[6]),
        "bullet_culls": int(g[7]),
        "minimap_dark_pixels": int(g[8])
    }

    # 3. 生效性断言检查（配置开启但计数为 0 则为未生效）
    assertions: List[Dict[str, Any]] = []
    has_zero_activation = False

    if config_dict.get("EnableBuildingFog", False):
        culls = telemetry_data["building_culls"]
        is_ok = culls > 0
        if not is_ok:
            has_zero_activation = True
        assertions.append({
            "key": "EnableBuildingFog",
            "metric": "建筑剔除",
            "value": culls,
            "status": "PASS" if is_ok else "UNVERIFIED (零生效)",
            "message": f"建筑剔除计数为 {culls}" + ("" if is_ok else " (开启但零触发/未生效)")
        })

    if config_dict.get("EnableBulletFog", False):
        culls = telemetry_data["bullet_culls"]
        is_ok = culls > 0
        if not is_ok:
            has_zero_activation = True
        assertions.append({
            "key": "EnableBulletFog",
            "metric": "弹道剔除",
            "value": culls,
            "status": "PASS" if is_ok else "UNVERIFIED (零生效)",
            "message": f"弹道剔除计数为 {culls}" + ("" if is_ok else " (开启但零触发/未生效)")
        })

    if config_dict.get("EnableMinimapFog", False):
        px = telemetry_data["minimap_dark_pixels"]
        is_ok = px > 0
        if not is_ok:
            has_zero_activation = True
        assertions.append({
            "key": "EnableMinimapFog",
            "metric": "小地图灰化像素",
            "value": px,
            "status": "PASS" if is_ok else "UNVERIFIED (零生效)",
            "message": f"小地图灰化像素计数为 {px}" + ("" if is_ok else " (开启但零触发/未生效)")
        })

    return {
        "checked": True,
        "has_telemetry": True,
        "config": config_dict,
        "metrics": telemetry_data,
        "assertions": assertions,
        "has_zero_activation": has_zero_activation
    }


def analyze_image(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    md5_hash = compute_md5(raw)
    file_size = len(raw)
    mtime = path.stat().st_mtime
    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    try:
        with Image.open(path) as img:
            w, h = img.size
            colors_80x80 = sample_80x80_unique_colors(img)
            colors_full = full_frame_unique_colors(img)
    except Exception as e:
        return {
            "file": path.name,
            "path": str(path.resolve()),
            "valid_image": False,
            "error": str(e),
            "bytes": file_size,
            "md5": md5_hash,
            "mtime": mtime,
            "mtime_str": mtime_str,
            "verdict": "FAIL",
            "reason": f"无法解析图像: {e}"
        }

    scene_type = classify_scene_type(path.name)
    issues: List[str] = []
    verdict = "PASS"

    # 1. 单色全等检查
    if colors_80x80 <= 1:
        issues.append("80×80 采样唯一色数 = 1 (判定为伪造单色占位图)")
        verdict = "FAIL"

    # 2. 体量与色彩基线检查 (针对 800x600 标准基线)
    if w == 800 and h == 600:
        if scene_type == "menu":
            if file_size < 200_000:
                issues.append(f"菜单体量偏小: {file_size:,} 字节 (校准基准 ≈ 300–400 KB)")
            if colors_80x80 < 100:
                issues.append(f"菜单色数偏低: {colors_80x80} (校准基准 ≈ 249)")
        elif scene_type == "battlefield":
            if file_size < 400_000:
                issues.append(f"战场体量不足: {file_size:,} 字节 (标准 v2 要求 ≥ 400 KB)")
                if verdict != "FAIL":
                    verdict = "FAIL"
            # 阈值口径：标准 v2 原文的 >=2000 / >=20000 在 16-bit RGB565 + cnc-ddraw 渲染路径
            # 不可达；按 EVIDENCE_STANDARD.md 附·口径订正（Lead 2026-09-28，实测 841–1046 采样 /
            # 978–1756 全画面）改为 >=600（80x80 采样）/ >=800（全画面），唯一色数 = 1 仍直接判伪造。
            if colors_80x80 < 600:
                issues.append(f"战场画面色数不足: {colors_80x80} (标准 v3 订正口径: 80x80 采样 >= 600)")
                if verdict != "FAIL":
                    verdict = "FAIL"
            if colors_full < 800:
                issues.append(f"战场全画面色数不足: {colors_full} (标准 v3 订正口径: 全画面 >= 800)")
    elif w > 800 or h > 600:
        if file_size < 100_000:
            issues.append(f"高分辨率 {w}×{h} 体量严重偏低: {file_size:,} 字节 (低于 100 KB)")
            verdict = "FAIL"

    return {
        "file": path.name,
        "path": str(path.resolve()),
        "valid_image": True,
        "width": w,
        "height": h,
        "bytes": file_size,
        "md5": md5_hash,
        "colors_80x80": colors_80x80,
        "colors_full": colors_full,
        "scene_type": scene_type,
        "mtime": mtime,
        "mtime_str": mtime_str,
        "verdict": verdict,
        "issues": issues,
        "reason": "; ".join(issues) if issues else "符合标准 v3 订正口径特征（体量/色数/MD5 唯一性静态筛）"
    }


def verify_evidence_directory(
    evidence_dir: Path,
    log_path: Optional[Path] = None,
    except_path: Optional[Path] = None,
    sav_dir: Optional[Path] = None,
    force_crash_check: bool = False
) -> Dict[str, Any]:
    if not evidence_dir.exists() or not evidence_dir.is_dir():
        return {
            "evidence_dir": str(evidence_dir),
            "overall_verdict": "FAIL",
            "summary": f"证据目录不存在: {evidence_dir}",
            "images": []
        }

    png_files = sorted(list(evidence_dir.glob("*.png")))
    if not png_files:
        return {
            "evidence_dir": str(evidence_dir),
            "overall_verdict": "UNVERIFIED",
            "summary": "目录下未找到任何 PNG 证据截图",
            "images": []
        }

    # 1. 逐图分析与步骤去重推断升级
    image_reports: List[Dict[str, Any]] = []
    seen_md5s: Dict[str, str] = {}
    duplicate_md5_pairs: List[Tuple[str, str, str]] = []

    for p in png_files:
        rep = analyze_image(p)
        md5_val = rep["md5"]
        if md5_val in seen_md5s:
            orig_file = seen_md5s[md5_val]
            duplicate_md5_pairs.append((orig_file, p.name, md5_val))
            rep["verdict"] = "FAIL"
            dup_msg = (
                f"MD5 哈希 ({md5_val[:10]}...) 与 {orig_file} 重复 "
                f"(疑似按键未生效 / 画面未实质刷新，参考 c0/c1 案例)"
            )
            rep["issues"].append(dup_msg)
            rep["reason"] = dup_msg if not rep["reason"] or rep["reason"] == "符合标准 v2 特征" else f"{rep['reason']}; {dup_msg}"
        else:
            seen_md5s[md5_val] = p.name
        image_reports.append(rep)

    # 2. 时间线分析
    mtimes = [r["mtime"] for r in image_reports]
    min_mtime = min(mtimes)
    max_mtime = max(mtimes)
    duration_sec = max_mtime - min_mtime
    start_time_str = datetime.fromtimestamp(min_mtime).strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = datetime.fromtimestamp(max_mtime).strftime("%Y-%m-%d %H:%M:%S")

    timeline_issues: List[str] = []
    if len(png_files) > 1 and duration_sec < 1.0:
        timeline_issues.append(f"截图批次总耗时仅 {duration_sec:.2f} 秒，疑似单帧或无交互连拍")

    # 3. 崩溃检测与快照保存 (P0 核心增强)
    crash_report: Dict[str, Any] = {"crash_detected": False}
    if except_path and except_path.exists():
        parsed_except = parse_except_log(except_path)
        except_mtime = parsed_except.get("mtime", 0)

        # 判断崩溃是否发生在当前验收时间窗口内（依据标准 v3：以本批截图最早 mtime 为绝对窗口下界，至截图结束后 10 分钟）
        window_start = min_mtime
        window_end = max_mtime + 600
        in_window = (window_start <= except_mtime <= window_end)
        is_stale = (except_mtime < window_start)

        crash_report = {
            "crash_detected": in_window or force_crash_check,
            "in_window": in_window,
            "is_stale": is_stale,
            "forced": force_crash_check,
            "window_start": window_start,
            "window_start_str": start_time_str,
            "window_end": window_end,
            "window_end_str": datetime.fromtimestamp(window_end).strftime("%Y-%m-%d %H:%M:%S"),
            "details": parsed_except
        }

        if in_window or force_crash_check:
            # 保存快照到证据目录
            snapshot_path = evidence_dir / "evidence_except_snapshot.txt"
            try:
                shutil.copy2(except_path, snapshot_path)
                crash_report["snapshot_saved"] = str(snapshot_path.resolve())
            except Exception as e:
                crash_report["snapshot_error"] = str(e)

    # 4. 日志与遥测生效性断言核验 (P0 核心增强)
    log_report: Dict[str, Any] = {"checked": False}
    if log_path and log_path.exists():
        log_stat = log_path.stat()
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        log_mtime = log_stat.st_mtime
        log_mtime_str = datetime.fromtimestamp(log_mtime).strftime("%Y-%m-%d %H:%M:%S")

        import re
        pids = re.findall(r"PID:\s*(\d+)", log_text)
        recent_pid = pids[-1] if pids else None
        has_hooks = "全部核心虚表" in log_text or "成功劫持虚表" in log_text
        has_fog = "[ra2render-fog]" in log_text
        has_minimap = "[ra2render-minimap]" in log_text

        telemetry_info = parse_telemetry_and_assertions(log_path)

        log_report = {
            "checked": True,
            "path": str(log_path.resolve()),
            "bytes": log_stat.st_size,
            "mtime": log_mtime,
            "mtime_str": log_mtime_str,
            "latest_pid": recent_pid,
            "has_hooks_installed": has_hooks,
            "has_fog_subsystem": has_fog,
            "has_minimap_subsystem": has_minimap,
            "telemetry": telemetry_info
        }

    # 5. 存档核验
    savegame_report: Dict[str, Any] = {"checked": False, "verdict": "UNVERIFIED"}
    if sav_dir and sav_dir.exists():
        sav_files = list(sav_dir.glob("*.sav"))
        if sav_files:
            sav_details = []
            valid_count = 0
            for sf in sav_files:
                ok, msg = verify_savegame_header(sf)
                if ok:
                    valid_count += 1
                sav_details.append({
                    "file": sf.name,
                    "valid": ok,
                    "detail": msg,
                    "mtime_str": datetime.fromtimestamp(sf.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            savegame_report = {
                "checked": True,
                "total_found": len(sav_files),
                "valid_count": valid_count,
                "verdict": "PASS" if valid_count > 0 else "FAIL",
                "details": sav_details
            }
        else:
            savegame_report = {
                "checked": True,
                "total_found": 0,
                "verdict": "UNVERIFIED",
                "reason": "指定目录未找到任何 .SAV 存档文件"
            }

    # 6. 综合判定裁决
    has_image_fail = any(r["verdict"] == "FAIL" for r in image_reports)
    has_dup_fail = len(duplicate_md5_pairs) > 0
    has_crash = crash_report.get("crash_detected", False)
    has_zero_activation = log_report.get("telemetry", {}).get("has_zero_activation", False)

    if has_crash:
        overall_verdict = "FAIL"
        c_det = crash_report["details"]
        summary = (
            f"运行期发生致命崩溃 ({c_det['error_code']} @ {c_det['eip']}, {c_det['attribution']})；"
            f"已保存崩溃快照至 evidence_except_snapshot.txt"
        )
    elif has_image_fail or has_dup_fail:
        overall_verdict = "FAIL"
        fail_reasons = []
        if has_dup_fail:
            fail_reasons.append(f"发现 {len(duplicate_md5_pairs)} 组重复 MD5 截图 (步骤未实质刷新)")
        for r in image_reports:
            if r["verdict"] == "FAIL" and r["reason"] not in fail_reasons:
                fail_reasons.append(f"{r['file']}: {r['reason']}")
        summary = "；".join(fail_reasons)
    elif has_zero_activation:
        overall_verdict = "UNVERIFIED"
        summary = "截图初步合格，但在线遥测显示已开启特性关键计数全为 0 (零生效，不得判 PASS)"
    else:
        if savegame_report.get("verdict") == "FAIL":
            overall_verdict = "FAIL"
            summary = "图像通过，但存档文件校验失败"
        elif savegame_report.get("verdict") == "UNVERIFIED" and sav_dir is not None:
            overall_verdict = "UNVERIFIED"
            summary = "图像初步达标，但缺少有效游戏存档留痕"
        else:
            overall_verdict = "PASS"
            summary = f"全部 {len(image_reports)} 张截图均符合证据标准 v3 (零崩溃、MD5 互异、色彩与遥测有效)"

    return {
        "evidence_dir": str(evidence_dir.resolve()),
        "overall_verdict": overall_verdict,
        "summary": summary,
        "metrics": {
            "total_images": len(image_reports),
            "distinct_md5_count": len(seen_md5s),
            "duplicate_md5_count": len(duplicate_md5_pairs),
            "start_time": start_time_str,
            "end_time": end_time_str,
            "duration_seconds": round(duration_sec, 2),
            "timeline_issues": timeline_issues
        },
        "images": image_reports,
        "crash_check": crash_report,
        "log_check": log_report,
        "savegame_check": savegame_report
    }


def format_markdown_report(res: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# 实测证据自动化校验报告 (标准 v3)")
    lines.append(f"")
    lines.append(f"- **目标证据目录**：`{res['evidence_dir']}`")
    lines.append(f"- **综合判定结果**：**{res['overall_verdict']}**")
    lines.append(f"- **核心结论摘要**：{res['summary']}")
    lines.append(f"")

    # 崩溃块高亮
    crash_c = res.get("crash_check", {})
    if crash_c.get("crash_detected"):
        cd = crash_c.get("details", {})
        lines.append(f"> [!CAUTION]")
        lines.append(f"> **检测到运行期致命崩溃**！整批证据直接判定为 **FAIL**。")
        lines.append(f"> - 故障异常：`{cd.get('error_code')}` ({cd.get('description')})")
        lines.append(f"> - 故障指令地址 (EIP)：`{cd.get('eip')}` —— **{cd.get('attribution')}**")
        lines.append(f"> - 访问违规目标虚拟地址：`{cd.get('access_address')}`")
        if cd.get("registers"):
            r = cd["registers"]
            lines.append(f"> - 核心寄存器：`Eax={r.get('Eax')}, Ecx={r.get('Ecx')}, Edx={r.get('Edx')}, Esi={r.get('Esi')}, Esp={r.get('Esp')}`")
        if cd.get("key_callsites"):
            lines.append(f"> - 关键调用点回溯：{', '.join(cd['key_callsites'])}")
        if crash_c.get("snapshot_saved"):
            lines.append(f"> - 崩溃现场快照：`{crash_c['snapshot_saved']}`")
        lines.append(f"")
    elif crash_c.get("is_stale"):
        cd = crash_c.get("details", {})
        lines.append(f"> [!NOTE]")
        lines.append(f"> **检测到历史 except.txt** (生成时间: `{cd.get('mtime_str')}`)，早于本批验收窗口下界 (`{crash_c.get('window_start_str')}`)。")
        lines.append(f"> 依据《实测证据标准 v3》窗口下界准则，判定为陈旧历史记录，不计入本次验收判定 (未误杀)。")
        lines.append(f"")

    lines.append(f"## 一、截图元数据与合规判定表")
    lines.append(f"")
    lines.append(f"| 序号 | 图像文件名 | 分辨率 | 字节大小 | 80×80采样色数 | MD5 前缀 | 场景类型 | 判定 | 理由 / 告警 |")
    lines.append(f"|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|")

    for idx, img in enumerate(res.get("images", []), 1):
        w_h = f"{img.get('width', '-')}×{img.get('height', '-')}"
        bytes_str = f"{img.get('bytes', 0):,} B"
        colors = str(img.get("colors_80x80", "-"))
        md5_prefix = img.get("md5", "")[:10]
        stype = img.get("scene_type", "unknown")
        verd = img.get("verdict", "UNVERIFIED")
        reason = img.get("reason", "")
        lines.append(f"| {idx} | `{img['file']}` | {w_h} | {bytes_str} | {colors} | `{md5_prefix}` | {stype} | **{verd}** | {reason} |")

    lines.append(f"")
    lines.append(f"## 二、指标度量汇总")
    m = res.get("metrics", {})
    lines.append(f"- **总截图数量**：{m.get('total_images', 0)} 张")
    lines.append(f"- **唯一 MD5 数量**：{m.get('distinct_md5_count', 0)} 个 (重复项: {m.get('duplicate_md5_count', 0)})")
    lines.append(f"- **时间跨度**：{m.get('start_time', '-')} 至 {m.get('end_time', '-')} (总耗时 {m.get('duration_seconds', 0)} 秒)")
    if crash_c.get("window_start_str"):
        lines.append(f"- **崩溃检测有效窗口**：`{crash_c.get('window_start_str')}` 至 `{crash_c.get('window_end_str')}` (窗口下界对齐本批最早截图)")
    if m.get("timeline_issues"):
        for iss in m["timeline_issues"]:
            lines.append(f"  - ⚠️ 告警: {iss}")

    log_c = res.get("log_check", {})
    if log_c.get("checked"):
        lines.append(f"")
        lines.append(f"## 三、日志交叉与遥测生效性断言")
        lines.append(f"- **日志路径**：`{log_c['path']}`")
        lines.append(f"- **最新目标 PID**：`{log_c.get('latest_pid', '未检测到')}`")
        lines.append(f"- **核心虚表拦截**：{'✅ 存在' if log_c.get('has_hooks_installed') else '❌ 未检测到'}")

        tel = log_c.get("telemetry", {})
        if tel.get("has_telemetry"):
            tm = tel.get("metrics", {})
            lines.append(f"- **末行遥测计数**：")
            lines.append(f"  - `BlitCalls`: {tm.get('blit_calls'):,} | `BlitPixels`: {tm.get('blit_pixels')} | `TargetScans`: {tm.get('target_scans')}")
            lines.append(f"  - `迷雾剔除`: {tm.get('fog_culled_units')} | `灰雾格子`: {tm.get('fog_cells')} | `渲染单位`: {tm.get('rendered_units')}")
            lines.append(f"  - `建筑剔除`: {tm.get('building_culls')} | `弹道剔除`: {tm.get('bullet_culls')} | `小地图灰化像素`: {tm.get('minimap_dark_pixels')}")

            if tel.get("assertions"):
                lines.append(f"- **特性生效性断言**：")
                for ass in tel["assertions"]:
                    st = ass["status"]
                    icon = "✅" if "PASS" in st else "⚠️"
                    lines.append(f"  - {icon} **{ass['key']}** -> {ass['message']} (状态: **{st}**)")

    sav_c = res.get("savegame_check", {})
    if sav_c.get("checked"):
        lines.append(f"")
        lines.append(f"## 四、存档文件 (.SAV) 核验")
        lines.append(f"- **存档判定**：**{sav_c.get('verdict')}** (发现 {sav_c.get('total_found', 0)} 个，合法 {sav_c.get('valid_count', 0)} 个)")
        for det in sav_c.get("details", []):
            lines.append(f"  - `{det['file']}`: {'✅' if det['valid'] else '❌'} {det['detail']} (时间: {det['mtime_str']})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="逆向工程实测证据标准 v3 自动化校验器 (含崩溃检测与生效性断言)")
    parser.add_argument("evidence_dir", type=Path, help="待校验的证据目录")
    parser.add_argument("--log", type=Path, default=Path("ra2youli/ra2render.log"), help="ra2render.log 路径")
    parser.add_argument("--except-file", type=Path, default=Path("ra2youli/except.txt"), help="except.txt 路径")
    parser.add_argument("--sav-dir", type=Path, default=None, help="游戏存档目录")
    parser.add_argument("--force-crash-check", action="store_true", help="强制检测 except.txt (忽略时间窗口限制)")
    parser.add_argument("--json-out", type=Path, default=None, help="输出完整 JSON 报告文件路径")
    parser.add_argument("--md-out", type=Path, default=None, help="输出 Markdown 报告文件路径")
    parser.add_argument("--quiet", action="store_true", help="静默模式，只通过退出码返回结果 (0: PASS, 1: FAIL/UNVERIFIED)")

    args = parser.parse_args()

    report = verify_evidence_directory(
        args.evidence_dir,
        log_path=args.log,
        except_path=args.except_file,
        sav_dir=args.sav_dir,
        force_crash_check=args.force_crash_check
    )
    md_text = format_markdown_report(report)

    if not args.quiet:
        print(md_text)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[+] JSON 报告已保存至: {args.json_out}")

    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md_text, encoding="utf-8")
        print(f"[+] Markdown 报告已保存至: {args.md_out}")

    sys.exit(0 if report["overall_verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
