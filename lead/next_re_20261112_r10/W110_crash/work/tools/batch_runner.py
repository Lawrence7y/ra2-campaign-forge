#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W94 BATCH MATRIX RUNNER - unattended matrix of real-machine trips.

    python batch_runner.py MATRIX.json [--dry-run] [--resume] [--pyexe PATH]
                                      [--plan-out PATH] [--trip-timeout-s N]

One cell = one effective arm (W85 green geometry + knobs).  One trip = one
unique directory under out/ (trip_<cell>_r<k>, NEVER reused).  Everything the
single-trip toolchain (W88/W90) earned the hard way is enforced per trip and
NOT bypassable by the matrix layer:

  * lock .game_instance.lock written at EVERY trip start AND end (owner
    w94-batchrun + measured time; end write happens even on crash),
  * zero-gamemd gate + sandbox-copy check before any launch,
  * D1 crash forensics captured immediately inside the trip runner
    (w94_trip.py) BEFORE any cleanup,
  * D2 outcome semantics (ok/outcome) verbatim from W90,
  * D4 input archive per trip (design + map + INIs + sha256),
  * per-trip RA2MD.INI / ddraw.ini byte restore + hash self-proof,
  * cleanup judged ONLY by sandbox_pre manifest diff (no save*.sav globs),
  * real dir ra2youli is READ-ONLY at all times.

The orchestrator itself launches no game: it builds (w94_build.py), installs
(w94_offline.py) and runs one trip per subprocess (w94_trip.py), records the
actual execution order in out/matrix_log.ndjson, and enforces per-cell
cumulative stop conditions.

STOP CONDITION GRAMMAR (per cell, accumulated over its completed trips):
    "any_crash"                 crash_count >= 1
    "any_<metric>"              metric >= 1
    "<metric>>=<N>"             metric >= N
    metrics: engine_error_count, crash_count, defeat_count, blocked_count,
             fatal_count, nonvalid_count, ok_count
    crash_count = engine-error dialog (any outcome containing ENGINE_ERROR)
                  OR abnormal process exit (ABORTED_CRASH_*).  Note
                  crash_count therefore >= engine_error_count.
A triggered condition skips the cell's REMAINING trips only (other cells
continue).  Unknown metric / unparsable condition => hard error at plan time.

--resume: completed trips (TRIP_RESULT.json present with an "outcome") are
skipped and their outcomes re-counted into the stop conditions; trip
directories present but INCOMPLETE are moved to out/aborted/<name>_<ts> and
re-run fresh (never overwritten in place).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

# [W98] this copy lives in work/tools (unlike W94 where the runner sat in the
# card root): CARD is the W110_crash card dir, TOOLS this very directory.
CARD = Path(__file__).resolve().parent.parent.parent
TOOLS = Path(__file__).resolve().parent
OUT = CARD / "out"
LOCK = CARD.parent / ".game_instance.lock"
ABORTED = OUT / "aborted"
SPECS = OUT / "specs"
LOGS = OUT / "logs"

DEFAULT_PYEXE = (r"C:\Users\Administrator\.dsh\dsh-runtimes"
                 r"\dsh-primary-runtime\dependencies\python\python.exe")

# W88 C-ladder presets, generalized (geometry lives in w94_build.py).
# [W98] three-point geometry split presets (napowr_step=3 = C6 geometry):
#   W98IDLE = enemy far + all Guard  (no march, no combat) = g_idle baseline
#   W98NEAR = enemy NEAR the player base + all Hunt  (no march, all combat)
#   W98FAR  = enemy far + all Hunt   (march + combat) = historical C6
ARM_PRESETS = {
    "C0":   {"hunt_all": False, "hunt_british": 0,  "napowr_step": 2, "crewed": False},
    "CTRL": {"hunt_all": False, "hunt_british": 0,  "napowr_step": 2, "crewed": False},
    "C1":   {"hunt_all": False, "hunt_british": 30, "napowr_step": 2, "crewed": False},
    "C2":   {"hunt_all": True,  "hunt_british": 0,  "napowr_step": 2, "crewed": False},
    "C7":   {"hunt_all": True,  "hunt_british": 0,  "napowr_step": 2, "crewed": True},
    "C6":   {"hunt_all": True,  "hunt_british": 0,  "napowr_step": 3, "crewed": False},
    "W98IDLE": {"hunt_all": False, "hunt_british": 0, "napowr_step": 3,
                "crewed": False, "enemy_zone": "far"},
    "W98NEAR": {"hunt_all": True,  "hunt_british": 0, "napowr_step": 3,
                "crewed": False, "enemy_zone": "near"},
    "W98FAR":  {"hunt_all": True,  "hunt_british": 0, "napowr_step": 3,
                "crewed": False, "enemy_zone": "far"},
}
ARM_KEYS = ("hunt_all", "hunt_british", "napowr_step", "crewed", "enemy_zone", "unit_scale")
TIMING_KEYS = ("observe_sec", "min_valid_sec", "hard_cap_sec", "sample_ms",
               "render_channel")
CELL_OVERRIDE_KEYS = ARM_KEYS + ("enemy_mission",) + TIMING_KEYS

METRICS = ("engine_error_count", "crash_count", "defeat_count",
           "blocked_count", "fatal_count", "nonvalid_count", "ok_count")


def now_local() -> str:
    import datetime
    return datetime.datetime.now().astimezone().isoformat(
        timespec="milliseconds")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class MatrixLog:
    """Append-only ndjson of the WHOLE matrix run (order, lock writes,
    skips, stops).  Survives resumes; every line is one event."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: str, **kw):
        rec = {"event": event, "t_utc": time.strftime(
                   "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "t_local": now_local(), **kw}
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True,
                               default=str, separators=(",", ":")) + "\n")
        try:
            print("[matrix] %s %s" % (event, json.dumps(
                kw, ensure_ascii=True, default=str)[:300]), flush=True)
        except Exception:
            pass


# ------------------------------------------------------------------ matrix
def norm_enemy_mission(v):
    if not isinstance(v, str) or v.strip().lower() not in ("guard", "hunt"):
        raise ValueError("enemy_mission must be 'Guard' or 'Hunt', got %r" % (v,))
    return {"hunt_all": v.strip().lower() == "hunt", "hunt_british": 0}


def validate_matrix(m: dict) -> dict:
    if not isinstance(m.get("run_id"), str) or \
            not re.fullmatch(r"[A-Za-z0-9_\-]+", m["run_id"]):
        raise ValueError("run_id must match [A-Za-z0-9_-]+: %r" % m.get("run_id"))
    defaults = dict(m.get("defaults") or {})
    unknown_d = [k for k in defaults
                 if k not in ("arm_template",) + TIMING_KEYS + ARM_KEYS]
    if unknown_d:
        raise ValueError("unknown defaults keys: %r" % unknown_d)
    cells = m.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("cells must be a non-empty list")
    seen = set()
    for c in cells:
        cid = c.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9_\-]+", cid):
            raise ValueError("cell id invalid: %r" % (cid,))
        if cid in seen:
            raise ValueError("duplicate cell id: %r" % cid)
        seen.add(cid)
        ovr = c.get("overrides") or {}
        unknown_o = [k for k in ovr if k not in CELL_OVERRIDE_KEYS]
        if unknown_o:
            raise ValueError("cell %s: unknown override keys %r (valid: %r)"
                             % (cid, unknown_o, CELL_OVERRIDE_KEYS))
        if not isinstance(c.get("repeats", 1), int) or c.get("repeats", 1) < 1:
            raise ValueError("cell %s: repeats must be int >= 1" % cid)
    order = m.get("order") or {"mode": "fixed"}
    if isinstance(order, str):
        order = {"mode": order}
    if order.get("mode") not in ("fixed", "shuffle"):
        raise ValueError("order.mode must be fixed|shuffle: %r" % (order,))
    if order["mode"] == "shuffle":
        if not isinstance(order.get("seed"), int):
            raise ValueError("order.shuffle requires an integer seed")
    stop_on = m.get("stop_on") or []
    parsed = [parse_stop(s) for s in stop_on]
    return {"run_id": m["run_id"], "defaults": defaults, "cells": cells,
            "order": order, "stop_on": stop_on, "stop_parsed": parsed,
            "raw": m}


def parse_stop(cond: str):
    if not isinstance(cond, str):
        raise ValueError("stop condition must be a string: %r" % (cond,))
    c = cond.strip()
    if c == "any_crash":
        return {"metric": "crash_count", "n": 1, "raw": cond}
    mt = re.fullmatch(r"any_([a-z_]+)", c)
    if mt:
        if mt.group(1) not in METRICS:
            raise ValueError("unknown stop metric %r (valid: %r)"
                             % (mt.group(1), METRICS))
        return {"metric": mt.group(1), "n": 1, "raw": cond}
    mt = re.fullmatch(r"([a-z_]+)>=([0-9]+)", c)
    if mt:
        if mt.group(1) not in METRICS:
            raise ValueError("unknown stop metric %r (valid: %r)"
                             % (mt.group(1), METRICS))
        return {"metric": mt.group(1), "n": int(mt.group(2)), "raw": cond}
    raise ValueError("unparsable stop condition %r (forms: any_crash, "
                     "any_<metric>, <metric>>=<N>)" % cond)


def effective_arm(defaults: dict, cell: dict) -> dict:
    tpl = defaults.get("arm_template", "C6")
    if tpl not in ARM_PRESETS:
        raise ValueError("arm_template must be one of %r: %r"
                         % (sorted(ARM_PRESETS), tpl))
    arm = dict(ARM_PRESETS[tpl])
    for src in (defaults, cell.get("overrides") or {}):
        if "enemy_mission" in src:
            arm.update(norm_enemy_mission(src["enemy_mission"]))
        for k in ARM_KEYS:
            if k in src:
                arm[k] = src[k]
    if arm["hunt_all"] and arm["hunt_british"]:
        raise ValueError("hunt_all + hunt_british are mutually exclusive")
    if int(arm["napowr_step"]) not in (2, 3):
        raise ValueError("napowr_step must be 2 or 3")
    return {"hunt_all": bool(arm["hunt_all"]),
            "hunt_british": int(arm["hunt_british"]),
            "napowr_step": int(arm["napowr_step"]),
            "crewed": bool(arm["crewed"]),
            "enemy_zone": str(arm.get("enemy_zone", "far")),
            "unit_scale": float(arm.get("unit_scale", 1.0))}


def effective_timing(defaults: dict, cell: dict) -> dict:
    t = {"observe_sec": float(defaults.get("observe_sec", 155)),
         "min_valid_sec": float(defaults.get("min_valid_sec", 150)),
         "hard_cap_sec": float(defaults.get("hard_cap_sec", 200)),
         "sample_ms": float(defaults.get("sample_ms", 6)),
         "render_channel": bool(defaults.get("render_channel", False))}
    ovr = cell.get("overrides") or {}
    for k in TIMING_KEYS:
        if k in ovr:
            t[k] = ovr[k]
    t["observe_sec"] = float(t["observe_sec"])
    t["min_valid_sec"] = float(t["min_valid_sec"])
    t["hard_cap_sec"] = float(t["hard_cap_sec"])
    t["sample_ms"] = float(t["sample_ms"])
    t["render_channel"] = bool(t["render_channel"])
    if not (t["min_valid_sec"] <= t["observe_sec"] <= t["hard_cap_sec"]):
        raise ValueError("need min_valid_sec <= observe_sec <= hard_cap_sec: %r" % t)
    if not 1.0 <= t["sample_ms"] <= 1000.0:
        raise ValueError("sample_ms out of sane range: %r" % t["sample_ms"])
    return t


def build_plan(m: dict):
    """Expand cells x repeats -> ordered trip list (actual execution order)."""
    trips = []
    for cell in m["cells"]:
        reps = int(cell.get("repeats", 1))
        for r in range(1, reps + 1):
            trips.append({"cell": cell["id"], "r": r,
                          "trip": "trip_%s_r%d" % (cell["id"], r),
                          "arm": effective_arm(m["defaults"], cell),
                          "timing": effective_timing(m["defaults"], cell)})
    if m["order"]["mode"] == "shuffle":
        rng = random.Random(m["order"]["seed"])
        rng.shuffle(trips)
    names = [t["trip"] for t in trips]
    if len(set(names)) != len(names):
        raise RuntimeError("trip dir collision (cell ids not unique?)")
    # duplicate-arm visibility check: two cells with identical effective arm
    # + timing are EXACT replicates (legal as intended replicates, but often
    # a matrix authoring slip - e.g. the card demo where arm_template C6
    # already carries napowr_step 3, making c2 == c3).  Warn, never block.
    seen_arms = {}
    for t in trips:
        key = json.dumps({"arm": t["arm"], "timing": t["timing"],
                          "cell": t["cell"]}, sort_keys=True)
        cell_key = json.dumps({"arm": t["arm"], "timing": t["timing"]},
                              sort_keys=True)
        if cell_key in seen_arms and seen_arms[cell_key] != t["cell"]:
            print("[warn] cells %s and %s have IDENTICAL effective arm+timing"
                  % (seen_arms[cell_key], t["cell"]))
        seen_arms.setdefault(cell_key, t["cell"])
    return trips


# ------------------------------------------------------------------ helpers
def write_lock(owner: str, purpose: str):
    """W94 discipline: lock written at trip start AND trip end with the
    measured time; the end write happens even when the trip crashed
    (try/finally around every trip).  [W98] owner=w110-batchrun per card."""
    LOCK.write_text(
        "run_id=next_re_20261112_r10_W98\nowner=%s\ntime=%s\npurpose=%s\n"
        % (owner, now_local(), purpose), encoding="utf-8")


def read_lock() -> str:
    return LOCK.read_text(encoding="utf-8", errors="replace") \
        if LOCK.is_file() else "<absent>"


def list_gamemd():
    """Zero-gamemd gate helper (tasklist based; read-only)."""
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq gamemd.exe",
                            "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, timeout=30)
        rows = []
        for ln in (r.stdout or "").splitlines():
            parts = [p.strip().strip('"') for p in ln.split('","')]
            if len(parts) >= 2 and parts[0].lower() == "gamemd.exe":
                try:
                    rows.append({"pid": int(parts[1])})
                except ValueError:
                    pass
        return rows
    except Exception as e:
        return [{"error": repr(e)}]


def run_stage(log: MatrixLog, label: str, argv, env: dict, timeout_s,
              log_dir: Path = LOGS):
    """Run one stage script (build / offline install / trip) as a subprocess.
    stdout+stderr are archived to out/logs/<label>.log and the tail is put in
    the matrix log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    lp = log_dir / ("%s.log" % label)
    t0 = time.monotonic()
    killed = False
    try:
        r = subprocess.run(argv, cwd=str(TOOLS), env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout_s)
        rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired as e:
        killed = True
        rc, out, err = -999, (e.stdout or b"").decode("utf-8", "replace") \
            if isinstance(e.stdout, bytes) else (e.stdout or ""), \
            (e.stderr or b"").decode("utf-8", "replace") \
            if isinstance(e.stderr, bytes) else (e.stderr or "")
        err += "\n[batch_runner] TIMEOUT after %ss; process killed. NOTE: the " \
               "game itself was launched detached (WMI) and may still be " \
               "alive - see the residual-gamemd record.\n" % timeout_s
    lp.write_text("ARGV: %s\nCWD: %s\nEXIT: %s\n\n--- STDOUT ---\n%s\n\n"
                  "--- STDERR ---\n%s\n"
                  % (json.dumps([str(a) for a in argv]), str(TOOLS), rc,
                     out[-16000:], err[-8000:]),
                  encoding="utf-8", errors="replace")
    rec = {"label": label, "exit_code": rc, "killed_timeout": killed,
           "wall_s": round(time.monotonic() - t0, 2), "log": str(lp),
           "stdout_tail": out[-2000:], "stderr_tail": err[-1500:]}
    log.write("stage_" + ("timeout" if killed else ("done" if rc == 0
                                                    else "fail")),
              **rec)
    return rec


def trip_is_complete(trip_dir: Path):
    """Complete = TRIP_RESULT.json exists, parses, and carries an 'outcome'.
    (w94_trip.py always writes TRIP_RESULT.json in its finally block; a dir
    without it means the runner process itself was killed mid-trip.)"""
    p = trip_dir / "TRIP_RESULT.json"
    if not p.is_file():
        return None
    try:
        r = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(r.get("outcome"), str):
            return None
        return r
    except Exception:
        return None


def outcome_counters(outcome: str, ok, terminal_kind=None):
    o = outcome or ""
    term = terminal_kind or ""
    return {
        "engine_error_count": int("ENGINE_ERROR" in o
                                  or term == "engine_internal_error_dialog"),
        "crash_count": int("ENGINE_ERROR" in o or o.startswith("ABORTED_CRASH")
                           or term == "engine_internal_error_dialog"),
        "defeat_count": int("DEFEAT_DIALOG" in o),
        "blocked_count": int(o.startswith("BLOCKED")),
        "fatal_count": int(o.startswith("FATAL")),
        "nonvalid_count": int(not ok),
        "ok_count": int(bool(ok)),
    }


def merge_counters(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) + b.get(k, 0) for k in METRICS}


def stop_hit(parsed_conds, counters: dict):
    for c in parsed_conds:
        if counters.get(c["metric"], 0) >= c["n"]:
            return c
    return None


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="W94 batch matrix runner")
    ap.add_argument("matrix", help="matrix JSON path")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate + print plan only; NO build/install/game")
    ap.add_argument("--resume", action="store_true",
                    help="skip completed trips; move incomplete dirs aside")
    ap.add_argument("--pyexe", default=DEFAULT_PYEXE)
    ap.add_argument("--plan-out", default=None,
                    help="extra copy of the plan JSON (e.g. EVIDENCE\\...)")
    ap.add_argument("--trip-timeout-s", type=int, default=None,
                    help="hard timeout per trip subprocess (default: "
                         "900 + hard_cap_sec * 5)")
    args = ap.parse_args()

    mpath = Path(args.matrix)
    matrix_raw = json.loads(mpath.read_text(encoding="utf-8-sig"))
    try:
        m = validate_matrix(matrix_raw)
    except ValueError as e:
        print("MATRIX INVALID: %s" % e)
        return 2
    trips = build_plan(m)
    plan = {
        "run_id": m["run_id"], "matrix_path": str(mpath),
        "matrix_sha256": sha256_file(mpath),
        "order": m["order"], "stop_on": m["stop_on"],
        "stop_parsed": m["stop_parsed"],
        "n_cells": len(m["cells"]), "n_trips": len(trips),
        "trips": [{"i": i, "cell": t["cell"], "r": t["r"], "trip": t["trip"],
                   "arm": t["arm"], "timing": t["timing"]}
                  for i, t in enumerate(trips)],
        "generated_t_local": now_local(),
        "dry_run": bool(args.dry_run), "resume": bool(args.resume),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    plan_path = OUT / ("plan_%s.json" % m["run_id"])
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    if args.plan_out:
        po = Path(args.plan_out)
        po.parent.mkdir(parents=True, exist_ok=True)
        po.write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    print("=" * 72)
    print("W94 BATCH PLAN  run_id=%s  cells=%d  trips=%d  order=%s%s"
          % (m["run_id"], len(m["cells"]), len(trips), m["order"]["mode"],
             (" seed=%d" % m["order"]["seed"]) if m["order"]["mode"] == "shuffle" else ""))
    for t in plan["trips"]:
        print("  #%-2d %-14s arm=%s timing=%s"
              % (t["i"], t["trip"],
                 json.dumps(t["arm"], separators=(",", ":")),
                 json.dumps(t["timing"], separators=(",", ":"))))
    print("stop_on: %s" % (m["stop_on"] or "[] (none - run every trip)"))
    print("plan json: %s" % plan_path)
    print("=" * 72)

    if args.dry_run:
        print("DRY RUN: no build, no install, no game launch.  "
              "Plan validated OK (cells, overrides, order, stop conditions).")
        return 0

    pyexe = args.pyexe
    log = MatrixLog(OUT / "matrix_log.ndjson")
    log.write("plan", run_id=m["run_id"], plan=str(plan_path),
              matrix_sha256=plan["matrix_sha256"],
              order=m["order"], stop_on=m["stop_on"],
              trips=[t["trip"] for t in trips])

    # ---- pre-flight: sandbox must already be a local copy ---------------
    sandbox = OUT / "sandbox_game"
    sandbox_pre = OUT / "sandbox_pre.json"
    if not sandbox_pre.is_file() or not (sandbox / "gamemd.exe").is_file():
        log.write("matrix_abort", reason="sandbox missing (out/sandbox_game "
                  "or out/sandbox_pre.json); run one offline FRESH setup first")
        print("ABORT: sandbox copy missing - the matrix runner never robocopies"
              " on its own; do the W94_FRESH=1 setup once, then rerun.")
        return 2

    # ---- build all cell packages first (offline, no lock needed) --------
    spec_paths = {}
    for cell in m["cells"]:
        cid = cell["id"]
        arm = effective_arm(m["defaults"], cell)
        sp = SPECS / ("%s.json" % cid)
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps({"cell": cid, "arm": arm},
                                 ensure_ascii=False, indent=2),
                      encoding="utf-8")
        spec_paths[cid] = sp
        built_ok = False
        bj = OUT / ("BUILD_%s.json" % cid)
        pkg = TOOLS.parent / ("pkg_%s" % cid) / "W94Probe"
        if bj.is_file() and (bj.parent.name == "out") \
                and (pkg / "RA2F_M1.MAP").is_file():
            try:
                rep = json.loads(bj.read_text(encoding="utf-8"))
                built_ok = (rep.get("verify") or {}).get("verdict") == "PASS"
            except Exception:
                built_ok = False
        if built_ok:
            log.write("build_skip", cell=cid, note="BUILD_<cell>.json verdict "
                      "PASS and package present; not rebuilt")
            print("[build] %s: cached package reused (sha-proven at verify "
                  "time)" % cid)
        else:
            rec = run_stage(log, "build_%s" % cid,
                            [pyexe, "-B", "-I", str(TOOLS / "w94_build.py")],
                            {**os.environ, "W94_CELL_SPEC": str(sp),
                             "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
                            timeout_s=900)
            if rec["exit_code"] != 0:
                log.write("matrix_abort", reason="cell build failed: %s" % cid)
                print("ABORT: build failed for cell %s (log: %s)"
                      % (cid, rec["log"]))
                return 2

    # ---- resume: counters from completed trips --------------------------
    counters = {c["id"]: {k: 0 for k in METRICS} for c in m["cells"]}
    cell_trips = {}
    for t in plan["trips"]:
        cell_trips.setdefault(t["cell"], []).append(t)
    if args.resume:
        for cid, tlist in cell_trips.items():
            for t in tlist:
                res = trip_is_complete(OUT / t["trip"])
                if res:
                    counters[cid] = merge_counters(
                        counters[cid],
                        outcome_counters(res.get("outcome"), res.get("ok"),
                                         (res.get("terminal") or {}).get("kind")))
                    log.write("resume_skip_complete", trip=t["trip"],
                              outcome=res.get("outcome"), ok=res.get("ok"))
                    print("[resume] %s complete (outcome=%s) - skipped"
                          % (t["trip"], res.get("outcome")))

    # ---- execute trips in the planned (possibly shuffled) order ---------
    results = []
    stopped_cells = set()
    residual_stop = False
    for t in plan["trips"]:
        cid, trip = t["cell"], t["trip"]
        trip_dir = OUT / trip
        if cid in stopped_cells:
            log.write("trip_skip", trip=trip, cell=cid,
                      outcome="SKIPPED_STOP_CONDITION",
                      note="cell %s already triggered a stop condition" % cid)
            results.append({"trip": trip, "cell": cid,
                            "outcome": "SKIPPED_STOP_CONDITION"})
            continue
        if residual_stop:
            log.write("trip_skip", trip=trip, cell=cid,
                      outcome="SKIPPED_RESIDUAL_GAMEMD",
                      note="residual gamemd after an earlier trip; matrix "
                           "stopped for manual triage (D1 discipline)")
            results.append({"trip": trip, "cell": cid,
                            "outcome": "SKIPPED_RESIDUAL_GAMEMD"})
            continue
        if trip_dir.exists():
            res = trip_is_complete(trip_dir)
            if res is not None:
                log.write("trip_skip_complete", trip=trip,
                          outcome=res.get("outcome"), ok=res.get("ok"))
                results.append({"trip": trip, "cell": cid,
                                "outcome": res.get("outcome"),
                                "ok": res.get("ok")})
                counters[cid] = merge_counters(
                    counters[cid],
                    outcome_counters(res.get("outcome"), res.get("ok"),
                                     (res.get("terminal") or {}).get("kind")))
                print("[skip] %s already complete" % trip)
                continue
            if args.resume:
                ts = time.strftime("%Y%m%d_%H%M%S")
                dest = ABORTED / ("%s_%s" % (trip, ts))
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(trip_dir), str(dest))
                log.write("trip_incomplete_moved", trip=trip,
                          moved_to=str(dest),
                          note="incomplete trip dir (no TRIP_RESULT.json); "
                               "moved aside, rerunning fresh")
            else:
                log.write("matrix_abort", reason="trip dir exists (never "
                          "reuse): %s; use --resume" % trip)
                print("ABORT: trip dir exists (never reuse): %s "
                      "(use --resume)" % trip_dir)
                return 2

        timing = t["timing"]
        timeout = args.trip_timeout_s or int(900 + timing["hard_cap_sec"] * 5)
        log.write("trip_start", trip=trip, cell=cid, r=t["r"],
                  arm=t["arm"], timing=timing)
        write_lock("w110-batchrun",
                   "W98 clean split run_id=%s cell=%s trip=%s START (build+"
                   "install+trip; owner restored at trip end even on crash)"
                   % (m["run_id"], cid, trip))
        log.write("lock_write", when="trip_start", trip=trip,
                  owner="w94-batchrun", lock=read_lock())
        trip_env = {**os.environ,
                    "W94_CELL": cid, "W94_TRIP": trip,
                    "W94_TARGET_S": str(timing["observe_sec"]),
                    "W94_MIN_VALID_S": str(timing["min_valid_sec"]),
                    "W94_HARD_CAP_S": str(timing["hard_cap_sec"]),
                    "W94_SAMPLE_MS": str(timing["sample_ms"]),
                    "W94_RENDER": "1" if timing["render_channel"] else "0",
                    "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        outcome, ok, terminal_kind = "FATAL_NO_RESULT", False, None
        try:
            # install (offline; short-circuits when the same package is
            # already installed and sha-identical)
            rec_i = run_stage(log, "install_%s_%s" % (cid, trip),
                              [pyexe, "-B", "-I", str(TOOLS / "w94_offline.py")],
                              {**trip_env, "W94_CELL": cid},
                              timeout_s=900)
            if rec_i["exit_code"] != 0:
                outcome = "BLOCKED_INSTALL_FAILED cell=%s" % cid
            else:
                rec_t = run_stage(log, "trip_%s" % trip,
                                  [pyexe, "-B", "-I", str(TOOLS / "w94_trip.py")],
                                  trip_env, timeout_s=timeout)
                res = trip_is_complete(trip_dir)
                if res is not None:
                    outcome = res.get("outcome")
                    ok = bool(res.get("ok"))
                    terminal_kind = (res.get("terminal") or {}).get("kind")
                elif rec_t["exit_code"] == 0:
                    outcome = "FATAL_TRIP_EXIT0_NO_RESULT_JSON"
        finally:
            # END lock write ALWAYS happens (crash too)
            residual = list_gamemd()
            write_lock("lead",
                       "W98 clean split run_id=%s trip=%s FINISHED "
                       "(outcome=%s, exit stage complete); "
                       "residual_gamemd=%d; owner restored."
                       % (m["run_id"], trip, outcome, len(residual)))
            log.write("lock_write", when="trip_end", trip=trip, owner="lead",
                      residual_gamemd=residual, lock=read_lock())
        # [W98 card discipline 8] small-step progress/heartbeat on disk after
        # EVERY trip (even a crashed one) - written by the orchestrator.
        try:
            _ts = now_local()
            (CARD / "HEARTBEAT.txt").write_text(
                "W98 heartbeat %s | last trip=%s outcome=%s ok=%s | "
                "gamemd_residual=%d\n" % (_ts, trip, outcome, ok,
                                          len(list_gamemd())),
                encoding="utf-8")
            with (CARD / "PROGRESS.md").open("a", encoding="utf-8",
                                             newline="\n") as _pf:
                _pf.write("- %s trip=%s cell=%s outcome=%s ok=%s\n"
                          % (_ts, trip, cid, outcome, ok))
        except Exception as _he:
            try:
                log.write("heartbeat_write_error", error=repr(_he))
            except Exception:
                pass
        counters[cid] = merge_counters(counters[cid],
                                       outcome_counters(outcome, ok,
                                                        terminal_kind))
        log.write("trip_end", trip=trip, cell=cid, r=t["r"],
                  outcome=outcome, ok=ok, counters_cell=counters[cid])
        results.append({"trip": trip, "cell": cid, "outcome": outcome,
                        "ok": ok})
        print("[trip] %s -> outcome=%s ok=%s" % (trip, outcome, ok))

        # residual gamemd after a returned trip = the trip runner could not
        # close what it launched: stop the matrix for manual D1 triage.
        if list_gamemd():
            residual_stop = True
            log.write("residual_gamemd_stop", trip=trip,
                      residual=list_gamemd(),
                      note="matrix stopped; manual triage required; no "
                           "blanket taskkill is performed by the runner")
        # per-cell cumulative stop conditions
        hit = stop_hit(m["stop_parsed"], counters[cid])
        if hit:
            stopped_cells.add(cid)
            log.write("stop_condition_triggered", cell=cid,
                      condition=hit["raw"], counters=counters[cid],
                      note="remaining trips of this cell will be skipped")
            print("[stop] cell %s: %s (counters=%s) - remaining trips of "
                  "this cell skipped" % (cid, hit["raw"],
                                         json.dumps(counters[cid])))

    # ---- final ----------------------------------------------------------
    result = {"run_id": m["run_id"], "finished_t_local": now_local(),
              "results": results, "counters_final": counters,
              "stopped_cells": sorted(stopped_cells),
              "residual_stop": residual_stop}
    rp = OUT / ("matrix_result_%s.json" % m["run_id"])
    rp.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    log.write("matrix_end", run_id=m["run_id"],
              n_trips=len(results),
              n_nonvalid=sum(1 for r in results
                             if r.get("ok") is False),
              stopped_cells=sorted(stopped_cells),
              residual_stop=residual_stop, result=str(rp))
    print("=" * 72)
    print("MATRIX DONE: %s" % rp)
    print("next: python batch_analyze.py out --matrix %s" % mpath)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        traceback.print_exc()
        print("FATAL: %r" % e)
        raise SystemExit(3)
