#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""empty_map_gen.py — H1RM 空图对照件生成与校验（ZC-H1RM 段 0.4）

标准空图对照件（EMPTY control）：
  - 与 H1 同尺寸（100×100 TEMPERATE）、同 waypoints / 边界 / 多人基本字段
  - 无 [Units]/[Infantry]/[Structures]/[Aircraft] 预置对象
  - 无 H1FP1 / H1Tier / Name fp: 标签（指纹期望 = 无 H1FP1，缺指纹是预期）
  - 禁止由 H1 图删段冒充：一律 MissionMap 从零生成

产物：
  out/loadbench/[2]0LoadBench_EMPTY.yrm              （工作副本）
  out/loadbench/pristine/EMPTY/[2]0LoadBench_EMPTY.yrm （镜像，MANIFEST 对照）
  out/re_work/empty_map/build_report.json
  MANIFEST.sha256 追加/更新 EMPTY 行（UTF-8 无 BOM）

用法：
  python tools/empty_map_gen.py              # 生成 + 自检 + 注册 MANIFEST
  python tools/empty_map_gen.py verify       # 只校验现有空图（不写盘）
  python tools/empty_map_gen.py --no-manifest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ra2_paths import resolve_root  # noqa: E402

ROOT = resolve_root(__file__)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from ra2forge.maplib import MissionMap, STANDARD_HOUSES, STANDARD_HOUSE_COLORS  # noqa: E402

OUT_DIR = ROOT / "out" / "loadbench"
PRISTINE_EMPTY = OUT_DIR / "pristine" / "EMPTY"
WORK_DIR = ROOT / "out" / "re_work" / "empty_map"
MANIFEST = OUT_DIR / "pristine" / "MANIFEST.sha256"

MAP_NAME = "[2]0LoadBench_EMPTY.yrm"
MAP_DISPLAY = "[2] 0LoadBench EMPTY"
MAP_SIZE = 100          # 与 H1 一致
THEATER = "TEMPERATE"

# 空图期望：无 H1FP1（缺指纹是预期，不是失败）
EMPTY_FP_EXPECT = ""    # empty string = no fingerprint
OBJECT_SECTIONS = ("Units", "Infantry", "Structures", "Aircraft")


# ── builders ─────────────────────────────────────────────────────────────

def build_empty_map() -> MissionMap:
    """从零构建空图对照件（禁止基于 H1 删段）。"""
    size = MAP_SIZE
    m = MissionMap(MAP_DISPLAY, width=size, height=size, theater=THEATER)

    # 与 H1 相同的多人基本字段（便于同 lobby 配置对照）
    m.basic.update({
        "GameMode": "standard",
        "MaxPlayer": 2,
        "MinPlayer": 2,
        "MultiplayerOnly": 1,
        "FreeRadar": "yes",
    })

    half = size // 2
    # 与 H1 完全相同的 waypoints / 边界
    m.add_waypoint(0, half, 4)
    m.add_waypoint(1, half, size - 5)

    # 房屋配置与 H1 对齐（唯一差异 = 无预置对象）
    m.house_configs = []
    for idx, h in enumerate(STANDARD_HOUSES):
        m.house_configs.append({
            "name": h,
            "player": False,
            "techlevel": 10,
            "credits": 10000,
            "iq": 5,
            "edge": "West" if idx % 2 == 0 else "East",
            "color": STANDARD_HOUSE_COLORS.get(h, "Grey"),
            "allies": h,
        })
    m.player_house = "Russians"
    # 不 add_unit / add_infantry / add_structure
    assert not m.units and not m.infantry and not m.structures
    return m


def patch_multiplayer_basic(map_text: str) -> str:
    """强制多人字段；不注入任何 H1 指纹字段。"""
    lines = map_text.splitlines()
    out: list[str] = []
    in_basic = False
    seen: set[str] = set()
    extras = {
        "GameMode": "standard",
        "MaxPlayer": "2",
        "MinPlayer": "2",
        "MultiplayerOnly": "1",
        "FreeRadar": "yes",
        "HomeCell": "0",
        "AltHomeCell": "0",
    }
    # 显式剔除指纹类键（若上游模板误带）
    banned = {"H1Tier", "H1Fingerprint"}
    for line in lines:
        if line.startswith("["):
            if in_basic:
                for k, v in extras.items():
                    if k not in seen:
                        out.append(f"{k}={v}")
                in_basic = False
            if line.strip() == "[Basic]":
                in_basic = True
                seen.clear()
        elif in_basic and "=" in line:
            k = line.split("=", 1)[0].strip()
            if k in banned:
                continue
            if k in extras:
                seen.add(k)
                out.append(f"{k}={extras[k]}")
                continue
        out.append(line)
    if in_basic:
        for k, v in extras.items():
            if k not in seen:
                out.append(f"{k}={v}")
    return "\n".join(out) + "\n"


def compose_text() -> str:
    m = build_empty_map()
    text = patch_multiplayer_basic(m.to_ini_text())
    return text


# ── verification ─────────────────────────────────────────────────────────

def split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    cur: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]") and len(line) > 2:
            if cur is not None:
                sections[cur] = buf
            cur = line[1:-1].strip()
            buf = []
        else:
            if cur is not None:
                buf.append(line)
    if cur is not None:
        sections[cur] = buf
    return sections


def object_row_count(text: str) -> int:
    secs = split_sections(text)
    n = 0
    for sec in OBJECT_SECTIONS:
        for line in secs.get(sec, []):
            if "=" in line and not line.strip().startswith(";"):
                n += 1
    return n


def parse_basic(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    in_basic = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("["):
            in_basic = s.lower() == "[basic]"
            continue
        if in_basic and "=" in s and not s.startswith(";"):
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def verify_empty_map(path: Path) -> dict:
    """空图期望：无 H1FP1、无预置对象、有 waypoints、尺寸=100×100。"""
    raw = path.read_bytes()
    text = raw.decode("gbk", errors="replace")
    basic = parse_basic(text)
    n_obj = object_row_count(text)

    fp = basic.get("H1Fingerprint", "")
    tier = basic.get("H1Tier", "")
    name = basic.get("Name", "")
    fp_tag = bool(re.search(r"fp:[0-9a-fA-F]{6,64}", name))

    map_sec = re.search(r"^\[Map\]\s*\n(.*?)(?=^\[|\Z)", text, re.M | re.S)
    map_m = re.search(r"^Size=0,0,(\d+),(\d+)", map_sec.group(1), re.M) if map_sec else None
    w = int(map_m.group(1)) if map_m else -1
    h = int(map_m.group(2)) if map_m else -1

    wp_m = re.search(r"\[Waypoints\]\n(.*?)(?=\n\[|\Z)", text, re.S)
    wp_lines = []
    if wp_m:
        wp_lines = [ln for ln in wp_m.group(1).splitlines() if "=" in ln]
    wp_ids = sorted(int(ln.split("=", 1)[0].strip()) for ln in wp_lines)

    checks = {
        "no_h1fingerprint": fp == EMPTY_FP_EXPECT,
        "no_h1tier": tier == "",
        "no_name_fp_tag": not fp_tag,
        "no_preplaced_objects": n_obj == 0,
        "size_100x100": (w, h) == (MAP_SIZE, MAP_SIZE),
        "waypoints_present": wp_ids == [0, 1],
        "multiplayer_fields": (
            basic.get("MultiplayerOnly") == "1"
            and basic.get("MaxPlayer") == "2"
            and basic.get("MinPlayer") == "2"
        ),
    }
    ok = all(checks.values())
    return {
        "path": str(path),
        "file_bytes": len(raw),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "name": name,
        "h1_fingerprint": fp,
        "h1_tier": tier,
        "object_rows": n_obj,
        "map_size": [w, h],
        "waypoint_ids": wp_ids,
        "checks": checks,
        "ok": ok,
        "fp_expect": "(none) — EMPTY 期望无 H1FP1",
    }


# ── MANIFEST (UTF-8 no BOM) ──────────────────────────────────────────────

def update_manifest(rel_src: str, rel_mirror: str, sha: str, size: int) -> str:
    """追加或更新 EMPTY 行。UTF-8 无 BOM（PowerShell Set-Content -Encoding UTF8 会带 BOM）。"""
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    raw = MANIFEST.read_bytes() if MANIFEST.exists() else b""
    text = raw.decode("utf-8")  # 若历史带 BOM，这里会留下 \ufeff，下面写回前剥掉
    text = text.lstrip("\ufeff")

    # 更新头部注释里的类别说明（幂等）
    text = text.replace("类别(old/H1)", "类别(old/H1/EMPTY)")

    entry = f"{sha}  {size}  EMPTY  {rel_src}  {rel_mirror}"
    lines = text.splitlines()
    out: list[str] = []
    replaced = False
    for ln in lines:
        if re.match(rf"^{re.escape(sha[:16])}\s+{size}\s+EMPTY\s+", ln) or (
            ln.strip().endswith(rel_mirror) and " EMPTY " in ln
        ):
            out.append(entry)
            replaced = True
        elif " EMPTY " in ln and ln.strip().endswith(MAP_NAME):
            out.append(entry)  # 同名 EMPTY 旧条目覆盖
            replaced = True
        else:
            out.append(ln)
    if not replaced:
        if out and out[-1].strip():
            out.append("")
        out.append("# 2026-09-30 空图对照件 EMPTY（ZC-H1RM 段 0.4；无 H1FP1）")
        out.append(entry)
    new_text = "\n".join(out) + "\n"

    # ★ UTF-8 无 BOM —— 禁止 PowerShell Set-Content -Encoding UTF8
    MANIFEST.write_bytes(new_text.encode("utf-8"))
    # 自证无 BOM
    assert not MANIFEST.read_bytes().startswith(b"\xef\xbb\xbf"), "MANIFEST 带 BOM 了！"
    return entry


# ── CLI ──────────────────────────────────────────────────────────────────

def cmd_build(write_manifest: bool) -> int:
    text = compose_text()
    raw = text.encode("gbk", errors="replace")
    sha = hashlib.sha256(raw).hexdigest()
    size = len(raw)

    targets = [OUT_DIR / MAP_NAME, PRISTINE_EMPTY / MAP_NAME]
    for dest in targets:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        assert dest.read_bytes() == raw

    # 自检（对镜像）
    report = verify_empty_map(PRISTINE_EMPTY / MAP_NAME)
    report["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report["map_display_name"] = MAP_DISPLAY
    report["note"] = "EMPTY 期望无 H1FP1；由 MissionMap 从零生成，非 H1 删段"
    report["copies"] = [str(p) for p in targets]

    entry = None
    if write_manifest:
        entry = update_manifest(
            rel_src=f"out\\loadbench\\{MAP_NAME}",
            rel_mirror=f"out\\loadbench\\pristine\\EMPTY\\{MAP_NAME}",
            sha=sha, size=size,
        )
        report["manifest_entry"] = entry

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    (WORK_DIR / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    status = "OK" if report["ok"] else "FAIL"
    print(f"[{status}] {MAP_NAME}")
    print(f"  bytes={size}  sha256={sha}")
    print(f"  objects={report['object_rows']}  size={report['map_size']}  "
          f"waypoints={report['waypoint_ids']}")
    print(f"  H1Fingerprint={report['h1_fingerprint'] or '(none)'}  "
          f"H1Tier={report['h1_tier'] or '(none)'}  fp_expect={report['fp_expect']}")
    for k, v in report["checks"].items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    if entry:
        print(f"  MANIFEST: {entry}")
    print(f"  report: {WORK_DIR / 'build_report.json'}")
    return 0 if report["ok"] else 1


def cmd_verify() -> int:
    path = PRISTINE_EMPTY / MAP_NAME
    if not path.is_file():
        print(f"FAIL  空图缺失 {path}")
        return 1
    r = verify_empty_map(path)
    status = "PASS" if r["ok"] else "FAIL"
    print(f"[{status}] {path.name}  objects={r['object_rows']}  "
          f"fp={r['h1_fingerprint'] or '(none)'}  sha256={r['file_sha256'][:16]}...")
    for k, v in r["checks"].items():
        if not v:
            print(f"       FAIL check: {k}")
    print(f"  fp_expect: {r['fp_expect']}")
    return 0 if r["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="H1RM 空图对照件生成/校验")
    ap.add_argument("cmd", choices=["build", "verify"], nargs="?", default="build")
    ap.add_argument("--no-manifest", action="store_true",
                    help="不写 MANIFEST.sha256")
    args = ap.parse_args(argv)
    if args.cmd == "verify":
        return cmd_verify()
    return cmd_build(write_manifest=not args.no_manifest)


if __name__ == "__main__":
    raise SystemExit(main())
