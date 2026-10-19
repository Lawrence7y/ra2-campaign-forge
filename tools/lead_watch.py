#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_watch.py - RA2 逆向项目 Lead 进度仪表盘（只读，无第三方依赖）

用法:
  python tools/lead_watch.py            # 最近 15 分钟活动
  python tools/lead_watch.py --minutes 60
  python tools/lead_watch.py --json     # 机器可读

输出: 各轨道最后活动时间/停滞时长、近期文件活动、活跃进程、台账登记缺口。
"""
import argparse, json, os, subprocess, sys, time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from datetime import datetime, timedelta

ROOT = r"D:\Project\ra2-campaign-forge"
LEDGER = os.path.join(ROOT, "REVERSE_ENGINEERING_AND_PATCHES.md")

SKIP_DIRS = {"node_modules", "__pycache__", ".git", "hook-state", "hook-status"}
SKIP_EXT = {".png", ".dll", ".exe", ".obj", ".mix", ".yrm", ".shp", ".bak", ".tgz", ".pyc"}

TRACKS = [
    ("A · L1/L2 Hook 落地", ("ra2render/blitter_hooks.cpp", "ra2render/ra2render.h",
                             "ra2render/ra2render.ini", "ra2render/dllmain",
                             "ra2youli/ra2render")),
    ("B · net_sync 联机确定性", ("out/re_work/net_sync/",)),
    ("C · 武器/伤害取证", ("out/reverse/", "tools/re_find_fns.py", "tools/check_syms.py")),
    ("D · 迷雾/可视性 gap", ("out/re_work/gap_spysat", "out/re_work/vis_gap",
                             "tools/re_gap_", "tools/scan_gap_calls.py")),
    ("E · VXL 体素渲染", ("out/re_work/vxl_re", "docs/re/vxl_render_sort.md")),
    ("F · 特效/时钟/AI/雷达波次", ("out/re_work/fx_draw", "out/re_work/clock_frame",
                                   "out/re_work/house_team_ai", "out/re_work/audio_input")),
    ("G · 文档/台账", ("docs/re/", "REVERSE_ENGINEERING_AND_PATCHES.md")),
]


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def track_of(r):
    for name, prefixes in TRACKS:
        for pre in prefixes:
            if r.startswith(pre):
                return name
    return "Z · 其他"


def scan(minutes):
    cutoff = time.time() - minutes * 60
    hits = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1].lower() in SKIP_EXT:
                continue
            p = os.path.join(base, f)
            try:
                m = os.path.getmtime(p)
            except OSError:
                continue
            if m >= cutoff:
                hits.append((m, os.path.getsize(p), rel(p)))
    hits.sort(reverse=True)
    return hits


def track_state(hits):
    st = {}
    for m, _sz, r in hits:
        t = track_of(r)
        st.setdefault(t, {"last": m, "files": 0, "latest": r})
        st[t]["files"] += 1
        if m > st[t]["last"]:
            st[t]["last"], st[t]["latest"] = m, r
    return st


def procs():
    out = []
    try:
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
               "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'ra2-campaign-forge' } | "
               "Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        raw = (r.stdout or "").strip()
        if raw:
            data = json.loads(raw)
            data = data if isinstance(data, list) else [data]
            for d in data:
                cl = " ".join((d.get("CommandLine") or "").split())
                out.append((d.get("ProcessId"), d.get("Name"), cl[:180]))
    except Exception as e:  # noqa
        out.append((None, "probe-failed", str(e)[:120]))
    return out


def ledger_gaps():
    """docs/re/*.md 是否已在台账中登记（按文件名出现与否粗判）。"""
    droot = os.path.join(ROOT, "docs", "re")
    try:
        ledger = open(LEDGER, encoding="utf-8", errors="replace").read()
    except OSError:
        ledger = ""
    try:
        docs = sorted(f for f in os.listdir(droot) if f.endswith(".md"))
    except OSError:
        docs = []
    reg, unreg = [], []
    for d in docs:
        (reg if d in ledger else unreg).append(d)
    return reg, unreg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    hits = scan(a.minutes)
    st = track_state(hits)
    reg, unreg = ledger_gaps()
    now = time.time()

    if a.json:
        print(json.dumps({
            "now": datetime.now().isoformat(timespec="seconds"),
            "window_minutes": a.minutes,
            "tracks": {k: {"last": datetime.fromtimestamp(v["last"]).isoformat(timespec="seconds"),
                           "idle_sec": int(now - v["last"]), "files": v["files"], "latest": v["latest"]}
                       for k, v in sorted(st.items(), key=lambda x: -x[1]["last"])},
            "files": [{"t": datetime.fromtimestamp(m).isoformat(timespec="seconds"), "size": s, "path": r}
                      for m, s, r in hits],
            "processes": procs(),
            "ledger_registered": reg, "ledger_unregistered": unreg,
        }, ensure_ascii=False, indent=2))
        return

    line = "=" * 84
    print(line)
    print(f"RA2 逆向 Lead 仪表盘 | {datetime.now():%Y-%m-%d %H:%M:%S} | 窗口 {a.minutes} 分钟")
    print(line)
    print("\n[轨道活跃度]")
    if not st:
        print("  窗口内无文件活动（全部疑似停滞）")
    for k, v in sorted(st.items(), key=lambda x: -x[1]["last"]):
        idle = int(now - v["last"])
        flag = "静止" if idle > 1200 else ("慢" if idle > 300 else "活跃")
        print(f"  {k:<26} 最后活动 {datetime.fromtimestamp(v['last']):%H:%M:%S}"
              f"  ({idle:>5}s, {flag})  文件 {v['files']:>3}  最新: {v['latest']}")

    print(f"\n[近期文件活动] 共 {len(hits)} 个")
    for m, s, r in hits[:30]:
        print(f"  {datetime.fromtimestamp(m):%H:%M:%S}  {s:>8} B  {r}")

    print("\n[活跃进程]")
    ps = procs()
    if not ps:
        print("  无匹配进程")
    for pid, name, cl in ps:
        print(f"  pid={pid} {name}\n      {cl}")

    print("\n[台账登记缺口] docs/re 共 {0} 份".format(len(reg) + len(unreg)))
    if unreg:
        for d in unreg:
            print(f"  ☐ 未登记: {d}")
    else:
        print("  ✓ 全部已登记")
    print(line)


if __name__ == "__main__":
    main()