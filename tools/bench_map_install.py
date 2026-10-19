#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bench_map_install.py — 基准图一键装卸（MIMO-BENCHPRIS）

子命令：
  --install-a   装法 A（推荐）：备份并移走旧图 → H1 按旧名安装
  --install-b   装法 B：H1 以 _H1 名与旧图并存
  --restore     按 MANIFEST.sha256 还原旧图（卸下 H1 / 恢复原始状态）
  --verify      比对游戏目录现状与 MANIFEST，输出 PASS/FAIL（不启动游戏）

纪律：
  - 所有含 [2] 的路径一律走 Python os/shutil 直路径（等价 -LiteralPath），绝不用 shell 通配。
  - 脚本内置 LiteralPath 对照自检（调 PowerShell Test-Path 有/无 -LiteralPath）。
  - 每次安装/还原记录 before/after sha256 到 out/re_work/mimo_benchpris/script/install_log_*.json
  - --verify 可独立运行，供 Lead/ZCode 复核。

用法：
  python tools/bench_map_install.py --verify
  python tools/bench_map_install.py --install-a
  python tools/bench_map_install.py --install-b
  python tools/bench_map_install.py --restore
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ra2_paths import resolve_root  # noqa: E402

ROOT = str(resolve_root(__file__))
GAME = os.path.join(ROOT, "ra2youli")
LOAD = os.path.join(ROOT, "out", "loadbench")
PRISTINE = os.path.join(LOAD, "pristine")
MANIFEST = os.path.join(PRISTINE, "MANIFEST.sha256")
LOG_DIR = os.path.join(ROOT, "out", "re_work", "mimo_benchpris", "script")

# 5 张旧基准图（游戏目录原始名）
OLD_MAPS = [
    "[2]0LoadBench_U0050.yrm",
    "[2]0LoadBench_U0100.yrm",
    "[2]0LoadBench_U0200.yrm",
    "[2]0LoadBench_U0400.yrm",
    "[2]0LoadBench_U0800.yrm",
]
# 3 张 H1 图
H1_MAPS = [
    "[2]0LoadBench_U0050_H1.yrm",
    "[2]0LoadBench_U0200_H1.yrm",
    "[2]0LoadBench_U0800_H1.yrm",
]
# H1 目标旧名映射（装法 A 用）
H1_TO_OLD = {
    "[2]0LoadBench_U0050_H1.yrm": "[2]0LoadBench_U0050.yrm",
    "[2]0LoadBench_U0200_H1.yrm": "[2]0LoadBench_U0200.yrm",
    "[2]0LoadBench_U0800_H1.yrm": "[2]0LoadBench_U0800.yrm",
}
BACKUP_SUFFIX = ".benchbak"


# ── helpers ──────────────────────────────────────────────────────────────

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path: str) -> list[dict]:
    """Return list of {sha256, size, category, src, mirror}."""
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            sha, size, cat = parts[0], int(parts[1]), parts[2]
            src = parts[3]
            mirror = " ".join(parts[4:])  # path may contain spaces? unlikely but safe
            entries.append({
                "sha256": sha, "size": size, "category": cat,
                "src": src, "mirror": mirror,
            })
    return entries


def manifest_by_basename(entries: list[dict]) -> dict[str, dict]:
    """Map basename of src -> entry. For old maps, src is ra2youli\\name."""
    d = {}
    for e in entries:
        base = os.path.basename(e["src"].replace("\\", "/"))
        d[base] = e
    return d


def literal_path_selftest() -> list[str]:
    """对照自检：同一路径不带/带 -LiteralPath 的 Test-Path 结果（应为 False/True）。"""
    sample = os.path.join(GAME, "[2]0LoadBench_U0200.yrm")
    sample_ps = sample.replace("\\", "\\\\")
    lines = []
    lines.append("[LiteralPath 对照自检]")
    lines.append(f"  样本路径: {sample}")
    for label, cmd in [
        ("不带 -LiteralPath",
         f'Test-Path "{sample_ps}"'),
        ("带 -LiteralPath",
         f'Test-Path -LiteralPath "{sample_ps}"'),
    ]:
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True, text=True, timeout=15,
            )
            out = (r.stdout or "").strip()
            lines.append(f"  {label}: Test-Path → {out}")
        except Exception as ex:
            lines.append(f"  {label}: 调用失败 {ex}")
    lines.append("  预期: 不带 = False（[2] 被当字符类通配符）；带 = True。")
    lines.append("  ⇒ 本脚本一律用 Python os/shutil 直路径（等价 -LiteralPath），绝不经 shell 通配。")
    return lines


def write_install_log(action: str, before: dict, after: dict, extra: dict | None = None) -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(LOG_DIR, f"install_log_{ts}_{action}.json")
    payload = {
        "action": action,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": after,
        "extra": extra or {},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def snapshot_game_dir() -> dict:
    """Return {basename: {exists, size, sha256, mtime}} for all bench-related files."""
    snap = {}
    names = set(OLD_MAPS) | set(H1_MAPS) | {n + BACKUP_SUFFIX for n in OLD_MAPS}
    for n in sorted(names):
        p = os.path.join(GAME, n)
        if os.path.isfile(p):
            snap[n] = {
                "exists": True,
                "size": os.path.getsize(p),
                "sha256": sha256_file(p),
                "mtime": datetime.fromtimestamp(
                    os.path.getmtime(p), tz=timezone.utc
                ).isoformat(),
            }
        else:
            snap[n] = {"exists": False}
    return snap


# ── commands ─────────────────────────────────────────────────────────────

def cmd_verify(entries: list[dict], strict_game: bool = True) -> int:
    """比对游戏目录现状与 MANIFEST。返回退出码 0=PASS。"""
    by_name = manifest_by_basename(entries)
    print("=== bench_map_install.py --verify ===")
    for line in literal_path_selftest():
        print(line)
    print()
    print(f"MANIFEST: {MANIFEST}  entries={len(entries)}")
    print()

    results = []
    # 1) 镜像完整性（pristine 镜像 vs MANIFEST）
    print("[A] pristine 镜像 vs MANIFEST")
    for e in entries:
        mir = os.path.join(ROOT, e["mirror"].replace("\\", os.sep))
        if not os.path.isfile(mir):
            results.append(("MIRROR", e["src"], "FAIL", f"镜像缺失 {e['mirror']}"))
            print(f"  FAIL  镜像缺失 {e['mirror']}")
            continue
        s = sha256_file(mir)
        sz = os.path.getsize(mir)
        ok = (s == e["sha256"] and sz == e["size"])
        results.append(("MIRROR", e["src"], "PASS" if ok else "FAIL",
                        f"sha={s[:16]}... size={sz}" + ("" if ok else f" 期望 sha={e['sha256'][:16]}... size={e['size']}")))
        print(f"  {'PASS' if ok else 'FAIL'}  {e['mirror']}  {sz}  {s[:16]}...")

    # 2) 游戏目录 vs MANIFEST（旧图类别）
    print()
    print("[B] 游戏目录 vs MANIFEST（old 类别；H1 不强制在游戏目录）")
    for e in entries:
        if e["category"] != "old":
            continue
        base = os.path.basename(e["src"].replace("\\", "/"))
        gp = os.path.join(GAME, base)
        if not os.path.isfile(gp):
            # 允许被装法 A 移走（.benchbak 存在也算合理）
            bak = gp + BACKUP_SUFFIX
            if os.path.isfile(bak):
                bs = sha256_file(bak)
                ok = bs == e["sha256"]
                results.append(("GAME", base, "PASS" if ok else "FAIL",
                                f"主文件缺失但 .benchbak 存在 sha={bs[:16]}..."))
                print(f"  {'PASS' if ok else 'FAIL'}  {base}  (主文件缺失，.benchbak sha={bs[:16]}...)")
            else:
                results.append(("GAME", base, "FAIL", "游戏目录无此文件且无 .benchbak"))
                print(f"  FAIL  {base}  游戏目录无此文件且无 .benchbak")
            continue
        s = sha256_file(gp)
        sz = os.path.getsize(gp)
        ok = (s == e["sha256"] and sz == e["size"])
        note = ""
        if not ok:
            # 若是 H1 装法 A（旧名装的是 H1 内容），标记 AMBIGUOUS
            h1_hash = None
            for he in entries:
                if he["category"] == "H1" and H1_TO_OLD.get(os.path.basename(he["src"].replace("\\", "/"))) == base:
                    h1_hash = he["sha256"]
                    break
            if h1_hash and s == h1_hash:
                note = "  ⚠ 当前为 H1 内容（装法 A 已安装）"
                results.append(("GAME", base, "PASS-H1", f"sha={s[:16]}... (H1 installed)"))
                print(f"  PASS-H1  {base}  {sz}  {s[:16]}...{note}")
                continue
        results.append(("GAME", base, "PASS" if ok else "FAIL",
                        f"sha={s[:16]}... size={sz}" + ("" if ok else f" 期望 sha={e['sha256'][:16]}... size={e['size']}")))
        print(f"  {'PASS' if ok else 'FAIL'}  {base}  {sz}  {s[:16]}...{note}")

    # summary
    n_fail = sum(1 for r in results if r[2] == "FAIL")
    n_pass = sum(1 for r in results if r[2].startswith("PASS"))
    print()
    print(f"=== verify 汇总: PASS={n_pass}  FAIL={n_fail}  (镜像 + 游戏目录) ===")
    print("判据: sha256 与 MANIFEST 一致 ⇒ PASS；不一致或缺失 ⇒ FAIL。")
    print("      装法 A 下游戏目录旧名可能是 H1 内容，标 PASS-H1（sha 匹配 H1 镜像）。")

    log = write_install_log("verify", {}, {}, {
        "results": results, "n_pass": n_pass, "n_fail": n_fail,
    })
    print(f"日志: {log}")
    return 0 if n_fail == 0 else 1


def cmd_install_a(entries: list[dict]) -> int:
    """装法 A：备份并移走旧图 → H1 按旧名安装。"""
    print("=== bench_map_install.py --install-a （装法 A：H1 按旧名）===")
    for line in literal_path_selftest():
        print(line)
    before = snapshot_game_dir()
    by_name = manifest_by_basename(entries)

    for h1_name, old_name in H1_TO_OLD.items():
        h1_src = os.path.join(LOAD, h1_name)          # 源：out/loadbench 的 H1
        h1_mir = os.path.join(PRISTINE, "H1", h1_name)
        game_old = os.path.join(GAME, old_name)
        game_bak = os.path.join(GAME, old_name + BACKUP_SUFFIX)

        if not os.path.isfile(h1_mir):
            print(f"  FAIL  镜像缺失 {h1_mir}")
            continue
        # 1) 若旧图存在，备份并移走
        if os.path.isfile(game_old):
            # 若旧图已是 H1 内容则跳过备份（幂等）
            cur = sha256_file(game_old)
            h1_sha = by_name.get(h1_name, {}).get("sha256")
            old_sha = by_name.get(old_name, {}).get("sha256")
            if cur == h1_sha:
                print(f"  SKIP  {old_name} 已是 H1 内容（幂等）")
                continue
            if os.path.isfile(game_bak):
                print(f"  KEEP  {old_name}{BACKUP_SUFFIX} 已存在，不覆盖")
            else:
                shutil.copy2(game_old, game_bak)
                print(f"  BAK   {old_name} → {old_name}{BACKUP_SUFFIX}")
            os.remove(game_old)
            print(f"  RMV   移走 {old_name}")
        # 2) 从镜像安装 H1 到旧名
        shutil.copy2(h1_mir, game_old)
        s = sha256_file(game_old)
        print(f"  INST  {h1_name} → {old_name}  sha={s[:16]}...")

    after = snapshot_game_dir()
    log = write_install_log("install-a", before, after)
    print(f"\n日志: {log}")
    print("判据: 还原请用 --restore（按 MANIFEST sha256）。")
    return 0


def cmd_install_b(entries: list[dict]) -> int:
    """装法 B：H1 以 _H1 名与旧图并存。"""
    print("=== bench_map_install.py --install-b （装法 B：H1 并存）===")
    for line in literal_path_selftest():
        print(line)
    before = snapshot_game_dir()

    for h1_name in H1_MAPS:
        h1_mir = os.path.join(PRISTINE, "H1", h1_name)
        game_h1 = os.path.join(GAME, h1_name)
        if not os.path.isfile(h1_mir):
            print(f"  FAIL  镜像缺失 {h1_mir}")
            continue
        if os.path.isfile(game_h1):
            cur = sha256_file(game_h1)
            mir_sha = sha256_file(h1_mir)
            if cur == mir_sha:
                print(f"  SKIP  {h1_name} 已存在且与镜像一致（幂等）")
                continue
            bak = game_h1 + ".bak"
            shutil.copy2(game_h1, bak)
            print(f"  BAK   {h1_name} → {h1_name}.bak")
        shutil.copy2(h1_mir, game_h1)
        s = sha256_file(game_h1)
        print(f"  INST  {h1_name}  sha={s[:16]}...")

    after = snapshot_game_dir()
    log = write_install_log("install-b", before, after)
    print(f"\n日志: {log}")
    print("用法提示: bench_replay.py --tiers <n> --map-suffix _H1")
    return 0


def cmd_restore(entries: list[dict]) -> int:
    """按 MANIFEST sha256 还原旧图到游戏目录（卸下 H1 / 恢复原始）。"""
    print("=== bench_map_install.py --restore （按 MANIFEST 还原）===")
    for line in literal_path_selftest():
        print(line)
    before = snapshot_game_dir()
    by_name = manifest_by_basename(entries)

    # 1) 删除游戏目录中的 H1 文件（装法 B 产物）
    for h1_name in H1_MAPS:
        game_h1 = os.path.join(GAME, h1_name)
        if os.path.isfile(game_h1):
            os.remove(game_h1)
            print(f"  RMV   游戏目录 H1 {h1_name}")

    # 2) 还原 5 张旧图（从 pristine/old 镜像）
    for old_name in OLD_MAPS:
        entry = by_name.get(old_name)
        if not entry:
            print(f"  FAIL  MANIFEST 无 {old_name}")
            continue
        mir = os.path.join(PRISTINE, "old", old_name)
        game_old = os.path.join(GAME, old_name)
        game_bak = os.path.join(GAME, old_name + BACKUP_SUFFIX)

        if not os.path.isfile(mir):
            print(f"  FAIL  镜像缺失 {mir}")
            continue

        mir_sha = entry["sha256"]
        # 若当前已是正确内容则跳过
        if os.path.isfile(game_old) and sha256_file(game_old) == mir_sha:
            print(f"  SKIP  {old_name} 已是 MANIFEST 内容（幂等）")
            continue

        # 优先从 .benchbak 还原（若其 sha 匹配）
        if os.path.isfile(game_bak) and sha256_file(game_bak) == mir_sha:
            shutil.copy2(game_bak, game_old)
            print(f"  REST  {old_name} ← .benchbak")
        else:
            shutil.copy2(mir, game_old)
            print(f"  REST  {old_name} ← pristine/old")

        s = sha256_file(game_old)
        ok = s == mir_sha
        print(f"        sha={s[:16]}...  {'OK' if ok else 'MISMATCH'}")

    after = snapshot_game_dir()
    log = write_install_log("restore", before, after)
    print(f"\n日志: {log}")
    return cmd_verify(entries)


# ── main ─────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="基准图一键装卸（MIMO-BENCHPRIS）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--install-a", action="store_true", help="装法 A：H1 按旧名安装（推荐）")
    g.add_argument("--install-b", action="store_true", help="装法 B：H1 与旧图并存")
    g.add_argument("--restore", action="store_true", help="按 MANIFEST 还原旧图")
    g.add_argument("--verify", action="store_true", help="比对游戏目录与 MANIFEST")
    ap.add_argument("--game-dir", default="", help="游戏目录（默认 ra2youli；基准环境分离后指向 ra2bench）")
    args = ap.parse_args()
    global GAME
    if args.game_dir:
        GAME = args.game_dir

    if not os.path.isfile(MANIFEST):
        print(f"FAIL: MANIFEST 不存在 {MANIFEST}")
        return 2

    entries = parse_manifest(MANIFEST)
    if not entries:
        print("FAIL: MANIFEST 解析为空")
        return 2

    if args.verify:
        return cmd_verify(entries)
    if args.install_a:
        return cmd_install_a(entries)
    if args.install_b:
        return cmd_install_b(entries)
    if args.restore:
        return cmd_restore(entries)
    return 2


if __name__ == "__main__":
    sys.exit(main())
