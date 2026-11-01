#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RC-4 守卫首验发射器（真机，2026-10-24）—— 三趟决定性试验。

★ 纪律
  - 只读他人件（_rc4_ab_probe.py 一字不改），经 import + monkeypatch 复用其方法学；
  - 载体/产物全落本线写域 `lead/qc161_u0400_trip/ab24/`；
  - 母本零污染：gamemd/ra2youli 不动，守卫 DLL/loader 只 cp 进载体；
  - 趟前后卫生：进程数、载体删除、母本哈希。

★ 三趟（每臂 1 趟即可判定——§369 关窗确定性 3/3）：
  t1 arm-A          基线复现：期望 rc4_hit=(0x724737, 0x250)，与 10-22 一致
  t2 arm-B 守卫关   注入对照：loader+DLL 但不装钩子——**关键归因控制**：
                    若此趟不崩，则「不崩」归因于注入本身而非守卫，v5 修复主张作废
  t3 arm-B 守卫开   修复臂：期望 0 AV、guard hits>=1、关窗后 <=20s 正常退出
  开关=载体 ini 的 `[Logic] EnableRC4Guard=0|1`（守卫从 cwd 的 ra2render.ini 读，
  本驱动负责写入该键；他人件无此 CLI ⇒ 驱动代劳，逐趟记录开关值）。

★ 用法：python _drive_rc4_ab24.py --live  （无 --live 只做预检）
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
MYCARD = ROOT / "lead" / "qc161_u0400_trip" / "ab24"
THEIR_SRC = ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py"
GAME_SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
GUARD_DIR = ROOT / "lead/goal2_rc4_fixv5_20261022/src"
GAMEMD_SHA16 = "73201cc021497c95"
GUARD_DLL_SHA16 = "0e2a9995ad71184c"   # ra2rc4guard.dll 本轮实测
LOADER_SHA16 = "ebddf6a61273c874"      # rc4_loader.exe 本轮实测

# 三趟计划（目录名压短：载体目录长度门禁 ≤130）
PLAN = [
    {"tag": "t1A",  "arm": "A", "dll": None,          "enable": None},
    {"tag": "t2Boff", "arm": "B", "dll": "ra2rc4guard.dll", "enable": 0},
    {"tag": "t3Bon",  "arm": "B", "dll": "ra2rc4guard.dll", "enable": 1},
]


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_their_module():
    spec = importlib.util.spec_from_file_location("rc4_ab_probe", THEIR_SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def set_enable(ini: Path, val) -> None:
    """写/替换 `[Logic]` 节下的 EnableRC4Guard=<val>，其余字节原样。

    ★★ 首轮教训：载体 ini 的**头注释里就有字面 '[Logic]'**，
      txt.replace("[Logic]", …) 落在注释行 ⇒ 键插进注释区、不属于任何节，
      GetPrivateProfileIntA 读回缺省 0 ⇒ 「守卫开臂」实际关着跑（假开臂）。
      ⇒ 现在只认**独占一行的节头**，写完**回读验证**，不符即抛。
    """
    txt = ini.read_text(encoding="utf-8", errors="replace")
    lines = txt.splitlines()
    idx = next((i for i, ln in enumerate(lines)
                if ln.strip() == "[Logic]"), None)
    if idx is None:
        lines += ["", "[Logic]", "EnableRC4Guard=%d" % val]
    else:
        # 节内已有的键就地替换，没有就插在节头后第一行
        end = next((j for j in range(idx + 1, len(lines))
                    if lines[j].strip().startswith("[")), len(lines))
        for k in range(idx + 1, end):
            if lines[k].strip().startswith("EnableRC4Guard="):
                lines[k] = "EnableRC4Guard=%d" % val
                break
        else:
            lines.insert(idx + 1, "EnableRC4Guard=%d" % val)
    txt = "\r\n".join(lines) + "\r\n"
    ini.write_text(txt, encoding="utf-8", newline="")
    # ★ 回读验证：键必须紧跟在独占一行的 [Logic] 之后（同节内）
    chk = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = next((i for i, ln in enumerate(chk) if ln.strip() == "[Logic]"), None)
    if hi is None or not any(ln.strip() == "EnableRC4Guard=%d" % val
                             for ln in chk[hi + 1:hi + 6]):
        raise RuntimeError("set_enable 回读验证失败：键未落在 [Logic] 节内")


def make_patched_create(enable):
    def create_carrier(dst: Path, extra_files):
        dst.mkdir(parents=True, exist_ok=False)
        copied = {}
        for f in sorted(GAME_SRC.iterdir()):
            if f.is_file():
                shutil.copy2(f, dst / f.name)
                copied[f.name] = 1
        for f in extra_files or []:
            shutil.copy2(f, dst / f.name)
            copied[f.name] = 1
        if enable is not None:                       # B 臂才动 ini
            ini = dst / "ra2render.ini"
            set_enable(ini, enable)
            copied["EnableRC4Guard"] = enable
        return copied
    return create_carrier


def game_procs(mod):
    return [n for n in mod.list_procs().values()
            if n.lower() in ("gamemd.exe", "ra2loader.exe", "rc4_loader.exe")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--trips", default="1,2,3", help="逗号分隔的 PLAN 下标(1-based)")
    ap.add_argument("--debug-timeout", type=float, default=120.0,
                    help="每趟调试窗上限；判「关窗后是否自退」要短窗才看得见 EXIT_PROCESS")
    a = ap.parse_args()
    which = [int(x) for x in a.trips.split(",")]

    print("=" * 78)
    print("RC-4 守卫首验 ab24   live=%s   trips=%s" % (a.live, which))
    print("=" * 78)

    # —— 预检（离线部分先跑，任何一项红 ⇒ 不发射）——
    fails = []

    def pre(name, ok, detail=""):
        print("  [%s] %-46s %s" % ("OK" if ok else "RED", name, detail))
        if not ok:
            fails.append(name)

    mod = load_their_module()
    pre("他人探针件在盘", THEIR_SRC.is_file(), str(THEIR_SRC))
    pre("游戏源 88 件", len([f for f in GAME_SRC.iterdir() if f.is_file()]) == 88, "")
    pre("gamemd 母本 sha", sha16(GAME_SRC / "gamemd.exe") == GAMEMD_SHA16, sha16(GAME_SRC / "gamemd.exe"))
    pre("守卫 dll sha", sha16(GUARD_DIR / "ra2rc4guard.dll") == GUARD_DLL_SHA16, sha16(GUARD_DIR / "ra2rc4guard.dll"))
    pre("loader sha", sha16(GUARD_DIR / "rc4_loader.exe") == LOADER_SHA16, sha16(GUARD_DIR / "rc4_loader.exe"))
    pre("残留游戏进程=0", not game_procs(mod), str(game_procs(mod)))
    pre("one_trip 签名=(idx,arm,dll,hold,to,keep)",
        mod.one_trip.__code__.co_argcount == 6, str(mod.one_trip.__code__.co_varnames[:6]))
    for p in PLAN:
        cdir = MYCARD / p["tag"] / "ct" / ("c" + "0" * 10)
        pre("载体目录长度<=130 (%s)" % p["tag"], len(str(cdir)) <= 130, str(len(str(cdir))))
        # 信息行（非门禁）：趟目录由探针按 stamp 新建，天然不混叠旧证据
        print("  [--] %s 出目录现状: %s" % (p["tag"], "已存在(旧趟)" if (MYCARD).exists() else "无"))
    pre("ra2dumps 在盘", Path(r"D:\ra2dumps").is_dir(), "")
    if fails:
        print("!! 预检 %d 项红，不发射" % len(fails))
        return 2
    if not a.live:
        print("\n★ 预检全过；加 --live 才真跑。")
        return 0

    # —— 真机：逐趟串行 ——
    mod.CARD = MYCARD            # ★ 产物目录与 rm_carrier 根都改指本线写域
    # ★ 探针 B 臂按 CARD/"src" 取注入件 ⇒ 在本线写域建同样的布局（cp 非移动，原件不动）
    (MYCARD / "src").mkdir(parents=True, exist_ok=True)
    for f in ("rc4_loader.exe", "ra2rc4guard.dll"):
        shutil.copy2(GUARD_DIR / f, MYCARD / "src" / f)
        if sha16(MYCARD / "src" / f) != sha16(GUARD_DIR / f):
            print("!! src 复制件哈希漂移", f)
            return 2
    results = []
    for n in which:
        p = PLAN[n - 1]
        tag = p["tag"]
        out_dir = MYCARD / tag
        mod.create_carrier = make_patched_create(p["enable"])
        print("\n" + "-" * 78)
        print("[趟 %s] arm=%s dll=%s enable=%s" % (tag, p["arm"], p["dll"], p["enable"]))
        t0 = time.time()
        # hold_s=6.0 与 10-22 基线趟一致（§369 复现条件对齐）；
        # debug_timeout 可调：短窗（如 30 s）才能在窗内看到 EXIT_PROCESS ⇒ 区分自退 vs 挂死
        rec = mod.one_trip(n, p["arm"], p["dll"], 6.0, a.debug_timeout, False)
        rec["tag"] = tag
        rec["enable_written"] = p["enable"]
        rec["wall_s"] = round(time.time() - t0, 1)
        g = rec.get("guard")
        if isinstance(g, dict):
            rec["guard_present"] = g.get("present")
        # A 臂没注入任何 DLL ⇒ 没有守卫日志；B 臂必须 present
        if p["arm"] == "B":
            rec["guard_log_ok"] = bool(isinstance(g, dict) and g.get("present"))
        results.append(rec)
        h = rec.get("rc4_hit")
        print("  hit=%s clean_exit=%s a8=%s guard{enabled=%s install=%s hits=%s present=%s}" % (
            "YES" if h else "no", rec.get("clean_exit"), rec.get("a8_verdict"),
            (g or {}).get("enabled") if isinstance(g, dict) else g,
            (g or {}).get("install_ok") if isinstance(g, dict) else None,
            (g or {}).get("hits_total") if isinstance(g, dict) else None,
            (g or {}).get("present") if isinstance(g, dict) else None))
        # 趟间卫生
        leftovers = game_procs(mod)
        if leftovers:
            rec["leftover_between"] = leftovers
            print("  !! 趟间残留 %s —— 停跑后续" % leftovers)
            break
        # ★ 落盘用探针实际建的 out_dir（模块内按 stamp+arm+idx 命名，不是我的 tag 目录）
        real_out = Path(rec.get("out_dir") or (MYCARD / tag))
        real_out.mkdir(parents=True, exist_ok=True)
        (real_out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                            encoding="utf-8")

    (MYCARD / "ab24_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n" + "=" * 78)
    print("ab24 汇总")
    for r in results:
        g = r.get("guard") or {}
        print("  %-7s hit=%-4s clean=%-5s hits=%-4s install=%-5s a8=%s"
              % (r.get("tag"), "Y" if r.get("rc4_hit") else "n",
                 r.get("clean_exit"), g.get("hits_total"), g.get("install_ok"),
                 r.get("a8_verdict")))
    print("残留进程:", game_procs(mod) or "0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
