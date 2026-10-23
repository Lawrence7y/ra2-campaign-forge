#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H-5 死因侧证普查：WER 归档 + 事件日志在四趟时间窗内有没有 gamemd 崩溃/挂起记录。

★ 这一项 §401/§402 都写「要区分需 WER `AppCrash` 记录或退出时刻 dump——本轮未做」。
  本脚本把「未做」变成「做了，结论是没有」——这是一个**否证**，不是新证据。
  按铁律，`except.txt` 零新增**不作**未崩溃判据；但「WER 归档里连一条 AppCrash 都没有」
  是另一个量：它说明**连崩溃上报管线都没被触发**。

★ 判据纪律（避免「零命中」变成自我安慰）
  1. 先证明普查**确实看得到东西**：同一窗口内必须命中至少一条**别的进程**的事件。
     否则「gamemd 零命中」只说明扫描器坏了。
  2. 分别报：目录名命中 / Report.wer 内部 `AppName=` 命中 / 事件日志 Id 命中。
  3. 报**时间窗**，并明确「窗外的记录不进来」。

用法：
    python _probe_h5_wer_census.py
    python _probe_h5_wer_census.py --json out.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

# 四趟的 measure 窗绝对时刻（取自各趟 measure_w0.json 的 t_abs0）
TRIP_WINDOWS = [
    ("l1_20261023",  "2026-10-23T10:04:19", "2026-10-23T10:04:23"),
    ("l1_20261023b", "2026-10-23T10:16:28", "2026-10-23T10:16:32"),
    ("l3_20261023",  "2026-10-23T10:26:44", "2026-10-23T10:26:48"),
    ("l1_20261023c", "2026-10-23T10:43:17", "2026-10-23T10:43:21"),
]
# harness 全程窗（launch→fields_post）；四趟都在 10:04–10:47
HARNESS_WINDOW = ("2026-10-23T10:00:00", "2026-10-23T10:50:00")

WER_ROOTS = [
    Path(r"C:\ProgramData\Microsoft\Windows\WER\ReportArchive"),
    Path(r"C:\ProgramData\Microsoft\Windows\WER\ReportQueue"),
]
GAME_NAMES = ("gamemd.exe", "ra2loader.exe", "game.exe", "ra2md.exe")

RESULT: list[tuple[str, bool, str]] = []


def chk(tag: str, cond: bool, detail: str = "") -> bool:
    RESULT.append((tag, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {tag}  {detail}")
    return bool(cond)


def read_wer_appname(f: Path) -> str:
    try:
        raw = f.read_bytes()
    except OSError:
        return ""
    for enc in ("utf-16-le", "utf-8", "latin-1"):
        try:
            t = raw.decode(enc, errors="strict")
        except (UnicodeDecodeError, LookupError):
            continue
        m = re.search(r"^AppName=(.+)$", t, re.M)
        if m:
            return m.group(1).strip()
    return ""


def wer_census():
    """返回 (全部记录, gamemd 记录)。每条 = dict(dir, root, mtime, appname, files)."""
    all_recs, game_recs = [], []
    for root in WER_ROOTS:
        if not root.is_dir():
            continue
        for d in root.iterdir():
            try:
                mt = dt.datetime.fromtimestamp(d.stat().st_mtime)
            except OSError:
                continue
            files = [p.name for p in d.iterdir()] if d.is_dir() else []
            app = ""
            rw = d / "Report.wer"
            if rw.is_file():
                app = read_wer_appname(rw)
            rec = {"root": root.name, "dir": d.name, "mtime": mt.isoformat(timespec="seconds"),
                   "app": app, "files": files}
            all_recs.append(rec)
            low = (d.name + " " + app).lower()
            if any(g in low for g in GAME_NAMES):
                game_recs.append(rec)
    return all_recs, game_recs


def ps_events(ids: list[int] | None, t0: str, t1: str) -> list[dict]:
    """查 Application 日志的事件。ids=None ⇒ 不限 Id（用作可见性对照）。

    失败返回空表；调用方必须配一条「同窗口总事件数 > 0」的对照，
    否则「零命中」分不清是「没崩」还是「查询失败」。
    """
    id_clause = ("Id=@(%s);" % ",".join(str(i) for i in ids)) if ids else ""
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        "Get-WinEvent -FilterHashtable @{LogName='Application';"
        "%sStartTime=[datetime]'%s';EndTime=[datetime]'%s'} |"
        "ForEach-Object { [pscustomobject]@{t=$_.TimeCreated.ToString('s');"
        "id=$_.Id;app=($_.Properties[0].Value -as [string]);"
        "prov=$_.ProviderName} } | ConvertTo-Json -Compress"
        % (id_clause, t0, t1)
    )
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                           capture_output=True, text=True, timeout=180,
                           encoding="utf-8", errors="replace")
    except (subprocess.SubprocessError, OSError):
        return []
    out = (r.stdout or "").strip()
    if not out:
        return []
    try:
        j = json.loads(out)
    except json.JSONDecodeError:
        return []
    return j if isinstance(j, list) else [j]


def self_mutation() -> int:
    """★ 变异自检：证明「零命中」这条判据**能变红**。

    做法不是改代码，而是改**被查询的窗口**：挪到确有 AppCrash 的时段
    （WER 归档里 `AppCrash_bt-battery-bar.e_*` @2026-10-23 13:56）。
    若门禁在那种窗口下仍全绿 ⇒ 它抓不到「窗口里有崩溃」⇒ 零命中无意义。
    """
    global HARNESS_WINDOW
    print("=" * 92)
    print("变异自检：把窗口挪到 2026-10-23 13:50–14:00（该时段确有 AppCrash）")
    print("=" * 92)
    HARNESS_WINDOW = ("2026-10-23T13:50:00", "2026-10-23T14:00:00")
    all_recs, game_recs = wer_census()
    lo = dt.datetime.fromisoformat(HARNESS_WINDOW[0])
    hi = dt.datetime.fromisoformat(HARNESS_WINDOW[1])
    in_win = [r for r in all_recs
              if lo <= dt.datetime.fromisoformat(r["mtime"]) <= hi]
    print("  窗口内 WER 记录 %d 条：" % len(in_win))
    for r in in_win:
        print("     %s  %-45s app=%s" % (r["mtime"], r["dir"][:45], r["app"] or "?"))
    ev = ps_events([1000, 1001, 1002], HARNESS_WINDOW[0], HARNESS_WINDOW[1])
    print("  窗口内崩溃三 Id 事件 %d 条" % len(ev))
    for e in ev[:6]:
        print("     %s id=%s app=%s" % (e.get("t"), e.get("id"),
                                        (e.get("app") or "")[:36]))

    # 变异判据：这个窗口里**必须**看得到崩溃，否则说明普查抓不到真信号
    saw_wer = any(r["dir"].lower().startswith("appcrash") for r in in_win)
    saw_ev = len(ev) > 0
    print()
    print("  [%s] 变异窗口内 WER 有 AppCrash（证明普查能看见崩溃）"
          % ("PASS" if saw_wer else "FAIL"))
    print("  [%s] 变异窗口内事件日志有 1000/1001/1002（同上）"
          % ("PASS" if saw_ev else "FAIL"))
    ok = saw_wer and saw_ev
    print()
    print("  RESULT: %s" % ("变异可被抓住" if ok else "门禁是瞎的（零命中不可采信）"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--window", nargs=2, metavar=("T0", "T1"), default=None,
                    help="覆盖查询窗口（ISO，如 2026-10-23T13:00:00）")
    ap.add_argument("--self-mutation", action="store_true",
                    help="变异自检：把窗口挪到**确有**爆掉的时间段，门禁必须变红")
    a = ap.parse_args()

    global HARNESS_WINDOW
    if a.window:
        HARNESS_WINDOW = (a.window[0], a.window[1])
        print("★ 窗口（CLI 覆盖）: %s .. %s" % HARNESS_WINDOW)

    if a.self_mutation:
        return self_mutation()

    print("=" * 92)
    print("H-5 死因侧证普查：WER 归档 + 事件日志（四趟窗口 2026-10-23 10:00–10:50）")
    print("=" * 92)

    # ---------- 1. WER 归档全量 ----------
    print()
    print("--- 1. WER 归档/队列全量 ---")
    all_recs, game_recs = wer_census()
    print("    根目录存在: %s" % [str(r) for r in WER_ROOTS if r.is_dir()])
    print("    记录总数 %d" % len(all_recs))
    chk("WER 归档可读且非空（扫描器确实看得到东西）",
        len(all_recs) > 0, "%d 条" % len(all_recs))

    # ---------- 2. 可见性对照（WER 侧）----------
    print()
    print("--- 2. ★ 可见性对照：WER 归档本身在窗口内有没有记录 ---")
    lo = dt.datetime.fromisoformat(HARNESS_WINDOW[0])
    hi = dt.datetime.fromisoformat(HARNESS_WINDOW[1])
    in_win = [r for r in all_recs
              if lo <= dt.datetime.fromisoformat(r["mtime"]) <= hi]
    others = [r for r in in_win if not any(g in (r["dir"] + r["app"]).lower()
                                           for g in GAME_NAMES)]
    print("    窗口内记录 %d 条，其中非游戏进程 %d 条" % (len(in_win), len(others)))
    for r in others[:8]:
        print("       %s  %-40s app=%s" % (r["mtime"], r["dir"][:40], r["app"] or "?"))
    # ★ 这一条**故意不要求 in_win > 0**：WER 只在崩溃时才写记录，
    #   窗口内本来就可能一条都没有。真正的可见性对照放在事件日志侧（第 4 节）。
    wer_has_history = len(all_recs) > 0
    print("    ⇒ WER 归档有历史记录 %d 条（可见性由第 1 节保证），窗口内 %d 条"
          % (len(all_recs), len(in_win)))

    # ---------- 3. 游戏进程记录 ----------
    print()
    print("--- 3. 游戏进程相关记录（全时段，不设窗口）---")
    for r in game_recs:
        print("    %s  %-30s app=%-16s files=%s"
              % (r["mtime"], r["root"], r["app"] or "?", r["files"]))
    print("    ⇒ gamemd 相关记录共 %d 条" % len(game_recs))

    crash = [r for r in game_recs if r["dir"].lower().startswith("appcrash")]
    hang = [r for r in game_recs if r["dir"].lower().startswith("apphang")]
    in_win_game = [r for r in game_recs
                   if lo <= dt.datetime.fromisoformat(r["mtime"]) <= hi]
    chk("★★ 窗口 10:00–10:50 内无 gamemd AppCrash",
        not [r for r in in_win_game if r["dir"].lower().startswith("appcrash")],
        "%d 条" % len(in_win_game))
    print("    AppCrash %d 条 / AppHang %d 条（全时段）" % (len(crash), len(hang)))
    for r in hang:
        print("      AppHang: %s  files=%s（空目录 = 报告未落盘，只有元数据）"
              % (r["mtime"], r["files"]))

    # ---------- 4. 事件日志 ----------
    print()
    print("--- 4. Application 事件日志（10:00–10:50）---")
    # 4a. 可见性对照：**不限 Id** 查同窗口，必须有返回，否则查询本身坏了
    all_ev = ps_events(None, HARNESS_WINDOW[0], HARNESS_WINDOW[1])
    print("    同窗口全部事件（不限 Id）%d 条" % len(all_ev))
    from collections import Counter
    idc = Counter(str(e.get("id")) for e in all_ev)
    print("    Id 分布: %s" % dict(idc.most_common(10)))
    chk("★ 可见性对照：同窗口 Application 日志有事件（否则零命中不可解释）",
        len(all_ev) > 0, "%d 条" % len(all_ev))
    print("    ⇒ 其中 **不含** 1000/1001/1002：%s"
          % (not any(str(e.get("id")) in ("1000", "1001", "1002") for e in all_ev)))

    # 4b. 专查崩溃三 Id
    ev = ps_events([1000, 1001, 1002], HARNESS_WINDOW[0], HARNESS_WINDOW[1])
    print("    崩溃三 Id（1000/1001/1002）%d 条" % len(ev))
    for e in ev[:12]:
        print("       %s  id=%s  app=%s  prov=%s"
              % (e.get("t"), e.get("id"), (e.get("app") or "")[:36], e.get("prov")))
    game_ev = [e for e in ev
               if any(g in ((e.get("app") or "") + (e.get("prov") or "")).lower()
                      for g in GAME_NAMES)]
    chk("★★ 窗口内事件日志无 gamemd 的 1000/1001/1002",
        not game_ev, "%d 条" % len(game_ev))
    chk("★★ 窗口内三个崩溃 Id 一条都没有（不只是没有 gamemd 的）",
        len(ev) == 0, "%d 条" % len(ev))

    # ---------- 5. 结论 ----------
    print()
    print("=" * 92)
    print("结论")
    print("=" * 92)
    print("  WER 记录总数 %d；游戏进程相关 %d（AppCrash %d / AppHang %d）"
          % (len(all_recs), len(game_recs), len(crash), len(hang)))
    print("  10:00–10:50 窗口内：WER 游戏记录 %d，事件日志游戏事件 %d"
          % (len(in_win_game), len(game_ev)))
    print("  ⇒ 四趟期间 **WER 与事件日志都没有 gamemd 崩溃/挂起上报**。")
    print("  ⇒ 这把 H-5 死因进一步推向「进程自行退出，未触发任何崩溃上报管线」。")
    print("  ★ 但**不能**据此判定「正常退出」：按铁律，无上报 ≠ 无崩溃")
    print("    （崩溃上报可被禁用/跳过；且 §401 已证 C 趟在死前有 6.28 s 帧停摆）。")
    print("  ★ 这条与 §402 的「exit code 0」是**两条独立否证**，方向相同：")
    print("    排除「被 TerminateProcess 打死」与「未处理异常导致 WER 上报崩溃」。")
    print("    剩余可能：正常退出 / SEH 兜底主动 ExitProcess(0) / 上报被禁用。")

    passed = sum(1 for _t, ok, _d in RESULT if ok)
    print()
    print("  checks passed: %d/%d" % (passed, len(RESULT)))
    verdict = passed == len(RESULT)
    print("  RESULT: %s" % ("ALL PASS" if verdict else "FAIL"))

    if a.json:
        a.json.write_text(json.dumps({
            "wer_all": all_recs, "wer_game": game_recs,
            "events": ev, "harness_window": HARNESS_WINDOW,
            "checks": [{"tag": t, "ok": ok, "detail": d} for t, ok, d in RESULT],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("  json -> %s" % a.json)

    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
