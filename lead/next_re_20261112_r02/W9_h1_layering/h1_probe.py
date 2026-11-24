# -*- coding: utf-8 -*-
"""W9 H1 载体装入后分层复测（真机，单实例，一趟到底）。

run_id = NEXT_RE_20261112_R02
前置：Lead 已把 ra2youli\\[2]0LoadBench_U0800_H1.yrm（309,822 B,
SHA-256 e3acc1305f98698da293e5969cf6769c2ca7a84c758a18ff6b7ba020a28d9e39）
装入 ra2youli。本卡回答：装入后它落在五类里的哪一类。

五类：
  1 文件未发现        —— 装入后文件在，预期已排除（以列表证据复核）
  2 已进列表但名称为空（No Name 等）
  3 选中了错误条目（名称命中多个，选中的不是目标）
  4 加载失败（选中并 UseMap/StartGame 后没进图）
  5 进图但 owner 未实例化（看不到自己的单位/阵营）

复用：W7_load_baseline\\load_baseline_probe.py 的全部已验证底层实现
（Win32 绑定、启动、导航、选图、内存字段采样、收尾、配置还原）。
W6_transition 只复用控件快照思路；本卡禁 SuspendThread/StackWalk64/
MiniDump/断点/注入/写目标内存，绝不导入其抓栈组件。

用法：
  python -X utf8 h1_probe.py --run       # 真机一趟（启动→列表→选图→开局→采样→收尾）
  python -X utf8 h1_probe.py --analyze   # 离线汇总 + 五类判定骨架
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import importlib.util
import json
import sys
import threading
import time
import traceback
from pathlib import Path

RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
W9 = ROOT / "lead" / "next_re_20261112_r02" / "W9_h1_layering"
OUT = W9 / "out"
W7_PROBE = (ROOT / "lead" / "next_re_20261112_r02" / "W7_load_baseline"
            / "load_baseline_probe.py")
SELF_OWNER = "w9_h1_layering_subagent"      # 与 .game_instance.lock 写入一致

H1_FILE = ROOT / "ra2youli" / "[2]0LoadBench_U0800_H1.yrm"
H1_SHA256 = "e3acc1305f98698da293e5969cf6769c2ca7a84c758a18ff6b7ba020a28d9e39"
H1_SIZE = 309822

# 第 2 步离线读到的 [Basic] 字段原值（2026-11-13 由 h1_probe.py 前置核对复核）
BASIC_NAME = "[2] 0LoadBench U0800 H1 fp:1189b6b550ff"
MAP_PATTERN_FULL = BASIC_NAME                # 先按完整显示名精确匹配
MAP_PATTERN_SUB = "0loadbench u0800 h1"      # 回退子串（大小写不敏感）

EXPECTED_LIST_BASE = 268                     # W7 实测装入前列表条目数
EXPECTED_LIST_NOW = 269                      # 装入 +1 预期

SAMPLE_MS = 30                               # 开局后采样间隔
SAMPLE_SECONDS = 70.0                        # StartGame 起采样时长（≥60 s 要求 + 10 s 余量）
UI_EVERY_S = 5.0                             # 采样期内 UI 控件快照间隔
USEMAP_SETTLE_S = 4.0                        # UseMap 后高负载图解析缓冲
MENU_TIMEOUT_S = 90

LOG_LINES = []


def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def log(msg):
    line = "%s %s" % (utc_iso(), msg)
    LOG_LINES.append(line)
    try:
        print(line, flush=True)
    except Exception:
        pass
    return line


# ------------------------------------------------------------------ 加载 W7 模块
def load_w7():
    spec = importlib.util.spec_from_file_location("w7_probe", str(W7_PROBE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["w7_probe"] = mod
    spec.loader.exec_module(mod)
    mod.SELF_OWNER = SELF_OWNER              # 锁守卫允许接管/持有本代理
    return mod


W7 = load_w7()


def ui_summary(pid, limit=25):
    """轻量控件快照（W6 ui_snapshot 思路、W7 controls 实现）：可见按钮+静态文本。"""
    btns, stats = [], []
    for h, c, t, v in W7.controls(pid):
        if not (t and v):
            continue
        if c == "Button" and len(btns) < limit:
            btns.append(t)
        elif c == "Static" and len(stats) < limit:
            stats.append(t)
    return {"t_utc_iso": utc_iso(), "buttons": btns, "statics": stats}


def read_map_names_diag(hproc, lb, n):
    """逐条读 ListBox 条目名称（UTF-16LE），带诊断分类与原始字节记录。

    diag: ok / itemdata_zero / rpm_failed / empty_utf16 / decode_failed:<exc>
    """
    entries = []
    n_fail_decode = 0
    for i in range(n):
        d = int(W7.smt(lb, W7.LB_GETITEMDATA, i)) & 0xFFFFFFFF
        if not d:
            entries.append({"index": i, "name": None,
                            "diag": "itemdata_zero", "raw_hex": None})
            continue
        b = None
        for sz in (240 * 2, 128, 64, 32):
            b = W7.rpm_partial(hproc, d, sz)
            if b is not None:
                break
        if b is None:
            entries.append({"index": i, "name": None,
                            "diag": "rpm_failed", "raw_hex": None})
            continue
        out = bytearray()
        for j in range(0, len(b) - 1, 2):
            if b[j] == 0 and b[j + 1] == 0:
                break
            out += b[j:j + 2]
        if not out:
            entries.append({"index": i, "name": None, "diag": "empty_utf16",
                            "raw_hex": bytes(b[:16]).hex()})
            continue
        try:
            s = bytes(out).decode("utf-16-le")
        except Exception as e:
            n_fail_decode += 1
            entries.append({"index": i, "name": None,
                            "diag": "decode_failed:%r" % e,
                            "raw_hex": bytes(out[:16]).hex()})
            continue
        entries.append({"index": i, "name": s, "diag": "ok", "raw_hex": None})
    return entries


def match_target(entries):
    """目标匹配：完整显示名精确匹配优先；回退子串匹配。返回 (hits, matched_by)。"""
    hits = [e for e in entries if e["name"] == MAP_PATTERN_FULL]
    by = "exact_full_name"
    if not hits:
        hits = [e for e in entries
                if e["name"] and MAP_PATTERN_SUB in e["name"].lower()]
        by = "substring:%s" % MAP_PATTERN_SUB
    return hits, by


# ------------------------------------------------------------------ 主流程
def lb_itemdata(lb, i):
    return int(W7.smt(lb, W7.LB_GETITEMDATA, i)) & 0xFFFFFFFF


def map_panel(pid):
    """选中条目后的地图信息面板 statics + buttons。"""
    return ui_summary(pid)


def run_run2():
    """第二趟：钉死 No Name 条目身份（缓冲 hex + 信息面板）→ 选中 [97] 开局采样。"""
    OUT.mkdir(parents=True, exist_ok=True)
    ndjson_path = OUT / "run2.ndjson"
    meta_path = OUT / "meta_run2.json"
    maplist_path = OUT / "maplist_run2.json"
    sink = W7.NDJSONSink(ndjson_path)
    started_utc = utc_iso()
    exit_code = 0
    pid, launcher_pid, own = 0, 0, ""
    hproc = None
    game_hwnd = 0
    prelaunch_hashes = {}
    inventory_before, inventory_after = {}, {}
    residual_before, residual_after = [], []
    close_steps = []
    NN_CAND = (91, 97)          # No Name 条目候选索引（第一趟实测）
    CTRL_IDX = 96               # 对照条目：[2] 0LoadBench U800
    meta = {
        "run_id": RUN_ID, "card": "W9 run2：No Name 条目身份钉死 + 开局采样",
        "started_utc": started_utc,
        "nn_candidates": list(NN_CAND), "ctrl_index": CTRL_IDX,
        "addresses": {k: [hex(ad), sz] for k, (ad, sz) in W7.ADDR.items()},
        "pid": None, "is32": None, "game_hwnd": None,
        "maplist_run2": None, "nn_audit": {}, "panels": {},
        "selected": None, "code_signature_ok": None,
        "prelaunch_hashes": {}, "residual_before": [], "residual_after": [],
        "close_steps": [], "restore_rows": [], "written_back": None,
        "inventory_counts": None, "error": None, "n_samples": 0,
        "phase_stop": None, "sample_seconds": SAMPLE_SECONDS,
        "sample_ms": SAMPLE_MS,
    }

    def ev(name, detail=None):
        try:
            sink.write({"kind": "event", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "event": name,
                        "detail": detail or {}})
        except Exception:
            pass

    try:
        # ---------- S0 守卫 ----------
        log("[S0] run2 实例锁 + 残留进程 + 哈希守卫")
        lock_state = W7.check_lock()
        log("    实例锁 owner 状态 = %s" % lock_state)
        W7.write_lock("W9 run2：No Name 条目钉死 + 开局采样")
        ev("lock_claimed", {"owner": SELF_OWNER, "state": lock_state})
        residual_before = W7.list_gamemd()
        meta["residual_before"] = residual_before
        if residual_before:
            raise W7.GuardStop("启动前已存在 gamemd 残留，停手不杀：%r" % residual_before)
        for name in W7.VERIFY_FILES:
            p = W7.GAME_DIR / name
            if not p.exists():
                raise W7.GuardStop("缺少文件 %s" % p)
            h = W7.sha256_file(p)
            prelaunch_hashes[name] = {"bytes": p.stat().st_size, "sha256": h,
                                      "expected": W7.BASELINE_HASHES[name],
                                      "match": h == W7.BASELINE_HASHES[name]}
            log("    %-20s match=%s" % (name, prelaunch_hashes[name]["match"]))
        meta["prelaunch_hashes"] = prelaunch_hashes
        if not all(v["match"] for v in prelaunch_hashes.values()):
            bad = [n for n, v in prelaunch_hashes.items() if not v["match"]]
            raise W7.GuardStop("启动前哈希与基线不一致，停手：%s" % bad)
        if not H1_FILE.exists() or W7.sha256_file(H1_FILE) != H1_SHA256:
            raise W7.GuardStop("H1 载体缺失或哈希不符")
        inventory_before = W7.inventory(W7.GAME_DIR)
        log("    启动前 ra2youli 文件清单 %d 项；守卫全过" % len(inventory_before))
        sink.write({"kind": "meta", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "run_id": RUN_ID, "run": 2,
                    "prelaunch_hashes": prelaunch_hashes,
                    "residual_before": residual_before})

        # ---------- S1 启动 ----------
        log("[S1] WMI 分离启动 gamemd.exe")
        launcher_pid = W7.launch_game()
        pid, own = W7.wait_for_pid(launcher_pid, MENU_TIMEOUT_S)
        meta["pid"], meta["launcher_pid"], meta["ownership"] = pid, launcher_pid, own
        log("    pid=%d 归属=%s" % (pid, own))
        ev("pid_found", {"pid": pid, "ownership": own})
        hproc = W7.k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not hproc:
            raise RuntimeError("OpenProcess 失败")
        flag = wt.BOOL(0)
        W7.k32.IsWow64Process(hproc, ctypes.byref(flag))
        meta["is32"] = bool(flag.value)
        sig = W7.rpm(hproc, W7.CODE_SIG_ADDR, len(W7.CODE_SIG_EXPECT))
        meta["code_signature_ok"] = (sig == W7.CODE_SIG_EXPECT)
        log("    is32=%s 代码签名 ok=%s" % (meta["is32"], meta["code_signature_ok"]))
        if not meta["code_signature_ok"]:
            raise W7.GuardStop("代码签名不匹配，停手")
        W7.wait_main_menu(pid, MENU_TIMEOUT_S)
        ev("main_menu_ready", {})
        hwnds = W7.game_top_windows(pid)
        game_hwnd = hwnds[0] if hwnds else 0
        _, game_tid = W7.game_window_tid(pid)
        meta["game_hwnd"] = int(game_hwnd or 0)
        meta["game_tid"] = game_tid
        log("    游戏窗口 hwnd=%s tid=%s" % (meta["game_hwnd"], game_tid))

        # ---------- S2' 导航 + 列表复核 + No Name 审计 + 面板证据 ----------
        log("[S2'] 导航 + 列表复核 + No Name 条目审计")
        if not W7.click(pid, "GUI:SinglePlayer", 3.0):
            raise RuntimeError("GUI:SinglePlayer 点击失败")
        if not W7.click(pid, "GUI:Skirmish", 3.5):
            raise RuntimeError("GUI:Skirmish 点击失败")
        if not W7.click(pid, "GUI:ChooseMap", 3.0):
            raise RuntimeError("GUI:ChooseMap 点击失败")
        lb, n = W7.find_maplist(pid)
        log("    地图 ListBox=%s 条目=%d（第一趟 269）" % (lb, n))
        ev("maplist_open", {"listbox": int(lb), "n_items": n})
        entries = read_map_names_diag(hproc, lb, n)
        noname_lit = [e for e in entries if e["name"] == "No Name"]
        log("    字面 No Name 条目：%s" % [(e["index"]) for e in noname_lit])
        maplist = {"run_id": RUN_ID, "t_utc_iso": utc_iso(), "listbox": int(lb),
                   "n_items": n, "noname_literal_indices":
                       [e["index"] for e in noname_lit], "entries": entries}
        maplist_path.write_text(json.dumps(maplist, ensure_ascii=False, indent=1),
                                encoding="utf-8")

        # --- No Name 条目 + 对照条目审计：itemdata 指针 + 缓冲大块 hex ---
        nn_audit = {}
        for idx in NN_CAND + (CTRL_IDX,):
            d = lb_itemdata(lb, idx)
            e = entries[idx]
            buf_hex = None
            buf_txt16 = None
            if d:
                b = W7.rpm_partial(hproc, d, 768)
                if b is not None:
                    buf_hex = bytes(b).hex()
                    # 尝试把前 240 字节按 UTF-16LE 解出可读段（诊断用）
                    out = bytearray()
                    for j in range(0, min(len(b), 480) - 1, 2):
                        if b[j] == 0 and b[j + 1] == 0:
                            break
                        out += b[j:j + 2]
                    try:
                        buf_txt16 = bytes(out).decode("utf-16-le", "replace")
                    except Exception:
                        buf_txt16 = None
            nn_audit[idx] = {"name_via_itemdata": e["name"], "diag": e["diag"],
                             "itemdata": d, "buf768_sha_prefix":
                                 (buf_hex[:64] if buf_hex else None),
                             "buf768_utf16_head": buf_txt16,
                             "raw_hex_file": ("nn_audit_%d.hex" % idx)}
            if buf_hex:
                (OUT / ("nn_audit_%d.hex" % idx)).write_text(buf_hex,
                                                             encoding="ascii")
            log("    [%d] itemdata=%s buf_utf16_head=%r"
                % (idx, hex(d) if d else "0", (buf_txt16 or "")[:60]))
        meta["nn_audit"] = {str(k): v for k, v in nn_audit.items()}
        ev("nn_audit_done", {"indices": list(NN_CAND), "ctrl": CTRL_IDX})

        # --- 面板证据：分别选中 91 / 97 / 96，读信息面板 ---
        panels = {}
        for idx, tag in ((NN_CAND[0], "panel_91"), (NN_CAND[1], "panel_97"),
                         (CTRL_IDX, "panel_96_ctrl")):
            W7.smt(lb, W7.LB_SETCURSEL, idx)
            time.sleep(1.8)
            panels[tag] = {"index": idx, "ui": map_panel(pid)}
            log("    %s(idx=%d) statics=%s" % (tag, idx,
                (panels[tag]["ui"]["statics"][:10],)))
            sink.write({"kind": "event", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "event": "panel_snapshot",
                        "detail": {"tag": tag, "index": idx,
                                   "ui": panels[tag]["ui"]}})
        meta["panels"] = {k: v["ui"] for k, v in panels.items()}

        # --- 选中 [97]（候选 H1 条目）→ UseMap → StartGame ---
        sel_idx = NN_CAND[1]
        sel_name = entries[sel_idx]["name"]
        W7.smt(lb, W7.LB_SETCURSEL, sel_idx)
        time.sleep(0.6)
        meta["selected"] = {"index": sel_idx, "display_name": sel_name}
        log("    选中 [%d] %r → UseMap" % (sel_idx, sel_name))
        ev("map_selected", {"index": sel_idx, "display_name": sel_name,
                            "selection_basis":
                                "No Name 条目 = H1 载体候选（文件名序插入点 + "
                                "面板证据见 panels），开局复现历史路径"})
        if not W7.click(pid, "GUI:UseMap", 3.0):
            raise RuntimeError("GUI:UseMap 未点击成功")
        time.sleep(USEMAP_SETTLE_S)
        meta["usemap_ui"] = ui_summary(pid)
        ev("usemap_clicked", {"ui": meta["usemap_ui"]})

        # ---------- S3/S4 StartGame + ≥60s 采样 ----------
        log("[S3] StartGame；逐拍采样 %.1fs @ %dms" % (SAMPLE_SECONDS, SAMPLE_MS))
        ev("startgame_clicked", {})
        t0 = time.perf_counter_ns()
        W7.click(pid, "GUI:StartGame", 1.0)
        ok = W7.force_foreground(meta["game_hwnd"])
        log("    置前游戏窗口 -> %s" % ok)
        seq = 0
        n_fail = 0
        last_frame = None
        last_frame_change_ns = t0
        stall_reported = False
        mode_hist = []
        next_ui = t0 + int(UI_EVERY_S * 1e9)
        while True:
            vals, failed = W7.read_all(hproc)
            seq += 1
            t_ns = time.perf_counter_ns()
            elapsed = (t_ns - t0) / 1e9
            rec = {"seq": seq, "kind": "sample", "phase": "after_start",
                   "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                   "elapsed_s": round(elapsed, 6),
                   "read_status": "ok" if vals is not None else "fail",
                   "read_fail_detail": failed,
                   "win_foreground": W7.fg_is(pid)}
            if vals is not None:
                for k in W7.ADDR:
                    rec[k] = vals.get(k)
                mode_hist.append(vals["mode_A8B238"])
                f = vals["frame"]
                if f != last_frame:
                    last_frame = f
                    last_frame_change_ns = t_ns
            else:
                n_fail += 1
            stall_s = (t_ns - last_frame_change_ns) / 1e9
            rec["frame_stall_s"] = round(stall_s, 3)
            if stall_s >= 1.0 and not stall_reported:
                log("    !! frame 停推 ≥1.0s（elapsed=%.1fs, mode=%s, fg=%s）——"
                    "停推可能属闲置态，本卡不判，只记录"
                    % (elapsed, rec.get("mode_A8B238"), rec["win_foreground"]))
                ev("frame_stall_1s", {"elapsed_s": round(elapsed, 3),
                                      "mode": rec.get("mode_A8B238"),
                                      "win_foreground": rec["win_foreground"]})
                stall_reported = True
            if stall_s < 1.0:
                stall_reported = False
            if t_ns >= next_ui:
                rec["ui"] = ui_summary(pid)
                u = rec["ui"]
                log("    UI@%.1fs buttons=%s statics0=%s"
                    % (elapsed, u["buttons"][:6],
                       (u["statics"][0] if u["statics"] else "")))
                next_ui += int(UI_EVERY_S * 1e9)
            sink.write(rec)
            ec = wt.DWORD(0)
            alive = bool(W7.k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == W7.STILL_ACTIVE)
            if not alive:
                meta["phase_stop"] = "process_exited_during_sampling"
                ev("process_exited", {"phase": "after_start",
                                      "exit_code": ec.value,
                                      "elapsed_s": round(elapsed, 3)})
                log("    !! 采样 %.1fs 时进程退出（exit=%d）" % (elapsed, ec.value))
                break
            if elapsed >= SAMPLE_SECONDS:
                meta["phase_stop"] = "sample_duration_reached"
                break
            time.sleep(SAMPLE_MS / 1000.0)
        meta["n_samples"] = seq
        meta["n_read_fail"] = n_fail
        meta["mode_hist_head"] = mode_hist[:20]
        meta["mode_hist_tail"] = mode_hist[-20:]
        log("[S4] 采样结束 seq=%d read_fail=%d" % (seq, n_fail))

    except W7.GuardStop as e:
        meta["error"] = "GuardStop: %s" % e
        exit_code = 2
        log("!! GuardStop: %s" % e)
        ev("guard_stop", {"detail": str(e)})
    except Exception as e:
        meta["error"] = "%s: %s" % (type(e).__name__, e)
        exit_code = 1
        log("!! 异常 %s: %s" % (type(e).__name__, e))
        log(traceback.format_exc())
        ev("exception", {"detail": meta["error"]})

    # ---------- P1 收尾 ----------
    finally:
        ended_utc = utc_iso()
        if hproc:
            try:
                W7.k32.CloseHandle(hproc)
            except Exception:
                pass
        try:
            log("[P1] 收尾：关闭自启动实例")
            close_steps = W7.close_game(pid, meta.get("game_hwnd") or 0)
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:
            close_steps.append("close_game 异常: %r" % e)
            log("    close_game 异常 %r" % e)
        residual_after = W7.list_gamemd()
        log("    收尾后 gamemd 残留 = %d %s" % (len(residual_after), residual_after))
        try:
            inventory_after = W7.inventory(W7.GAME_DIR)
            log("    收尾后 ra2youli 文件清单 %d 项" % len(inventory_after))
        except Exception as e:
            log("    inventory_after 异常 %r" % e)
        diff = W7.diff_inventory(inventory_before, inventory_after)
        try:
            rows = W7.restore_configs()
            for r in rows:
                log("    还原 %s -> %s" % (r.get("file"),
                                           r.get("post_restore_sha256")
                                           or r.get("post_sha256")))
        except Exception as e:
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
            log("    restore_configs 异常 %r" % e)
        h1_still = H1_FILE.exists()
        h1_hash_after = W7.sha256_file(H1_FILE) if h1_still else None
        log("    H1 载体仍在=%s hash_after=%s" % (h1_still, h1_hash_after))
        try:
            (OUT / "run2_stdout.txt").write_text("\n".join(LOG_LINES) + "\n",
                                                 encoding="utf-8")
        except Exception:
            pass
        meta["ended_utc"] = ended_utc
        meta["residual_after"] = residual_after
        meta["close_steps"] = close_steps
        meta["restore_rows"] = rows
        meta["written_back"] = diff
        meta["inventory_counts"] = [len(inventory_before), len(inventory_after)]
        meta["h1_file_after"] = {"exists": h1_still, "sha256": h1_hash_after,
                                 "untouched": bool(h1_still and
                                                   h1_hash_after == H1_SHA256)}
        try:
            sink.write({"kind": "meta_end", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "run_id": RUN_ID, "run": 2,
                        "exit_code": exit_code, "error": meta["error"],
                        "residual_after": residual_after})
        except Exception:
            pass
        sink.close()
        meta["n_ndjson_lines"] = sink.n_lines
        try:
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1,
                                            sort_keys=True, default=str),
                                 encoding="utf-8")
        except Exception as e:
            log("    写 meta_run2.json 异常 %r" % e)
        log("[P1] run2 收尾完成（NDJSON=%d 行）" % sink.n_lines)
    return exit_code, meta


# ------------------------------------------------------------------ 离线分析
def run_run():
    OUT.mkdir(parents=True, exist_ok=True)
    ndjson_path = OUT / "run.ndjson"
    meta_path = OUT / "meta.json"
    maplist_path = OUT / "maplist.json"
    sink = W7.NDJSONSink(ndjson_path)
    started_utc = utc_iso()
    exit_code = 0
    pid, launcher_pid, own = 0, 0, ""
    hproc = None
    game_hwnd = 0
    maplist = None
    prelaunch_hashes = {}
    inventory_before, inventory_after = {}, {}
    residual_before, residual_after = [], []
    close_steps = []
    meta = {
        "run_id": RUN_ID, "card": "RE-N03 W9 H1 载体装入后分层复测",
        "started_utc": started_utc,
        "h1_file": {"path": str(H1_FILE), "expected_sha256": H1_SHA256,
                    "expected_size": H1_SIZE},
        "basic_name_offline": BASIC_NAME,
        "addresses": {k: [hex(ad), sz] for k, (ad, sz) in W7.ADDR.items()},
        "pid": None, "is32": None, "game_hwnd": None, "game_tid": None,
        "maplist": None, "code_signature_ok": None, "prelaunch_hashes": {},
        "residual_before": [], "residual_after": [], "close_steps": [],
        "restore_rows": [], "written_back": None, "inventory_counts": None,
        "error": None, "n_samples": 0, "phase_stop": None,
        "sample_seconds": SAMPLE_SECONDS, "sample_ms": SAMPLE_MS,
    }

    def ev(name, detail=None):
        try:
            sink.write({"kind": "event", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "event": name,
                        "detail": detail or {}})
        except Exception:
            pass

    try:
        # ---------- S0 守卫 ----------
        log("[S0] 实例锁 + 残留进程 + 哈希守卫（W9）")
        lock_state = W7.check_lock()
        log("    实例锁 owner 状态 = %s" % lock_state)
        W7.write_lock("W9 H1 载体装入后分层复测（真机单实例）")
        ev("lock_claimed", {"owner": SELF_OWNER, "state": lock_state})

        residual_before = W7.list_gamemd()
        meta["residual_before"] = residual_before
        log("    gamemd 残留 = %d %s" % (len(residual_before), residual_before))
        if residual_before:
            raise W7.GuardStop("启动前已存在 gamemd 残留，停手不杀：%r"
                               % residual_before)

        for name in W7.VERIFY_FILES:
            p = W7.GAME_DIR / name
            if not p.exists():
                raise W7.GuardStop("缺少文件 %s" % p)
            h = W7.sha256_file(p)
            prelaunch_hashes[name] = {"bytes": p.stat().st_size, "sha256": h,
                                      "expected": W7.BASELINE_HASHES[name],
                                      "match": h == W7.BASELINE_HASHES[name]}
            log("    %-20s %8d %s match=%s" % (name, prelaunch_hashes[name]["bytes"], h, prelaunch_hashes[name]["match"]))
        meta["prelaunch_hashes"] = prelaunch_hashes
        if not all(v["match"] for v in prelaunch_hashes.values()):
            bad = [n for n, v in prelaunch_hashes.items() if not v["match"]]
            raise W7.GuardStop("配置/主程序哈希与基线不一致，停手：%s" % bad)

        if not H1_FILE.exists():
            raise W7.GuardStop("H1 载体不在 ra2youli（装入被回退？）：%s" % H1_FILE)
        h1_hash = W7.sha256_file(H1_FILE)
        h1_size = H1_FILE.stat().st_size
        h1_ok = (h1_hash == H1_SHA256 and h1_size == H1_SIZE)
        meta["h1_file"].update({"sha256": h1_hash, "size": h1_size, "match": h1_ok})
        log("    H1 载体 %d B sha=%s match=%s" % (h1_size, h1_hash, h1_ok))
        if not h1_ok:
            raise W7.GuardStop("H1 载体哈希/大小与 Lead 装入记录不一致，停手")
        ev("h1_file_verified", {"size": h1_size, "sha256": h1_hash})

        inventory_before = W7.inventory(W7.GAME_DIR)
        log("    启动前 ra2youli 文件清单 %d 项" % len(inventory_before))
        sink.write({"kind": "meta", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                    "prelaunch_hashes": prelaunch_hashes,
                    "h1_file": meta["h1_file"],
                    "residual_before": residual_before,
                    "note": "meta：此后每行独立 NDJSON；异常退出此前各行仍可解析"})

        # ---------- S1 启动 ----------
        log("[S1] WMI 分离启动 gamemd.exe")
        ev("launching", {})
        launcher_pid = W7.launch_game()
        pid, own = W7.wait_for_pid(launcher_pid, MENU_TIMEOUT_S)
        meta["pid"], meta["launcher_pid"], meta["ownership"] = pid, launcher_pid, own
        log("    pid=%d 归属=%s (launcher_pid=%d)" % (pid, own, launcher_pid))
        ev("pid_found", {"pid": pid, "ownership": own})
        hproc = W7.k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not hproc:
            raise RuntimeError("OpenProcess(VM_READ|QUERY_INFORMATION) 失败")
        flag = wt.BOOL(0)
        W7.k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        meta["is32"] = is32
        sig = W7.rpm(hproc, W7.CODE_SIG_ADDR, len(W7.CODE_SIG_EXPECT))
        meta["code_signature_ok"] = (sig == W7.CODE_SIG_EXPECT)
        log("    is32=%s 代码签名@0x55DE4F ok=%s" % (is32, meta["code_signature_ok"]))
        if not meta["code_signature_ok"]:
            raise W7.GuardStop("代码签名不匹配，地址基线失效，停手")
        W7.wait_main_menu(pid, MENU_TIMEOUT_S)
        ev("main_menu_ready", {})
        hwnds = W7.game_top_windows(pid)
        game_hwnd = hwnds[0] if hwnds else 0
        game_hwnd2, game_tid = W7.game_window_tid(pid)
        meta["game_hwnd"] = int(game_hwnd or game_hwnd2 or 0)
        meta["game_tid"] = game_tid
        log("    游戏窗口 hwnd=%s tid=%s" % (meta["game_hwnd"], game_tid))

        # ---------- S2 导航 + 完整列表读取 ----------
        log("[S2] 导航 SinglePlayer -> Skirmish -> ChooseMap；读完整列表")
        if not W7.click(pid, "GUI:SinglePlayer", 3.0):
            raise RuntimeError("GUI:SinglePlayer 点击失败")
        if not W7.click(pid, "GUI:Skirmish", 3.5):
            raise RuntimeError("GUI:Skirmish 点击失败")
        if not W7.click(pid, "GUI:ChooseMap", 3.0):
            raise RuntimeError("GUI:ChooseMap 点击失败")
        lb, n = W7.find_maplist(pid)
        log("    地图 ListBox=%s 条目=%d（装入前基线 %d，预期 %d）"
            % (lb, n, EXPECTED_LIST_BASE, EXPECTED_LIST_NOW))
        if not lb:
            raise RuntimeError("未拿到地图列表")
        ev("maplist_open", {"listbox": int(lb), "n_items": n})

        entries = read_map_names_diag(hproc, lb, n)
        noname = [e for e in entries if e["name"] is None]
        hits, matched_by = match_target(entries)
        for e in hits[:20]:
            log("    目标命中 [%3d] %r" % (e["index"], e["name"]))
        log("    匹配方式=%s；命中 %d 条；空名/乱码条目 %d 个（索引 %s）"
            % (matched_by, len(hits), len(noname),
               [e["index"] for e in noname][:30]))

        maplist = {
            "run_id": RUN_ID, "t_utc_iso": utc_iso(), "listbox": int(lb),
            "n_items": n, "expected_base": EXPECTED_LIST_BASE,
            "expected_now": EXPECTED_LIST_NOW,
            "delta_vs_base": n - EXPECTED_LIST_BASE,
            "basic_name_offline": BASIC_NAME,
            "pattern_full": MAP_PATTERN_FULL, "pattern_sub": MAP_PATTERN_SUB,
            "matched_by": matched_by,
            "n_target_hits": len(hits),
            "target_hits": [{"index": e["index"], "name": e["name"]}
                            for e in hits],
            "n_noname": len(noname),
            "noname": noname,
            "entries": entries,
        }
        maplist_path.write_text(json.dumps(maplist, ensure_ascii=False, indent=1),
                                encoding="utf-8")
        log("    maplist.json 已写（%d 条）" % n)
        ev("maplist_read", {"n_items": n, "n_hits": len(hits),
                            "n_noname": len(noname), "matched_by": matched_by})

        if not hits:
            meta["maplist"] = {"n_items": n, "n_target_hits": 0,
                               "n_noname": len(noname), "matched_by": matched_by}
            raise W7.GuardStop(
                "列表 %d 条中无目标名称（完整名与子串均未命中）；空名条目 %d 个。"
                "装入后落在类 1/类 2 边界（列表证据已存 maplist.json），按失败收尾"
                % (n, len(noname)))
        if len(hits) > 1:
            # 类 3 风险：记录全部候选；选择策略 = 精确匹配优先已隐含（先精确），
            # 同名并列时取索引最小者并显式声明。
            log("    !! 名称命中 %d 条（类 3 风险）；取索引最小者并声明" % len(hits))
        sel = min(hits, key=lambda e: e["index"])
        sel_idx = sel["index"]
        log("    选择索引 %d 显示名=%r" % (sel_idx, sel["name"]))
        r = W7.smt(lb, W7.LB_SETCURSEL, sel_idx)
        log("    LB_SETCURSEL(%d) -> %s" % (sel_idx, r))
        time.sleep(0.6)
        if not W7.click(pid, "GUI:UseMap", 3.0):
            raise RuntimeError("GUI:UseMap 未点击成功")
        time.sleep(USEMAP_SETTLE_S)
        usemap_ui = ui_summary(pid)
        log("    UseMap 后 UI：buttons=%s" % (usemap_ui["buttons"][:12],))
        meta["maplist"] = {
            "n_items": n, "delta_vs_base": n - EXPECTED_LIST_BASE,
            "matched_by": matched_by, "n_target_hits": len(hits),
            "target_hits": maplist["target_hits"], "n_noname": len(noname),
            "noname_indices": [e["index"] for e in noname],
            "selected_index": sel_idx, "selected_name": sel["name"],
            "n_candidates": len(hits),
        }
        ev("map_selected", {"index": sel_idx, "name": sel["name"],
                            "n_hits": len(hits), "n_items": n,
                            "usemap_ui": usemap_ui})

        # ---------- S3/S4 StartGame + ≥60s 逐拍采样 ----------
        log("[S3] StartGame；逐拍采样 %.1fs @ %dms（phase=after_start）"
            % (SAMPLE_SECONDS, SAMPLE_MS))
        ev("startgame_clicked", {})
        t0 = time.perf_counter_ns()
        W7.click(pid, "GUI:StartGame", 1.0)
        ok = W7.force_foreground(meta["game_hwnd"])
        log("    置前游戏窗口 -> %s" % ok)

        seq = 0
        n_fail = 0
        last_frame = None
        last_frame_change_ns = t0
        stall_reported = False
        mode_hist = []
        next_ui = t0 + int(UI_EVERY_S * 1e9)
        while True:
            vals, failed = W7.read_all(hproc)
            seq += 1
            t_ns = time.perf_counter_ns()
            elapsed = (t_ns - t0) / 1e9
            rec = {"seq": seq, "kind": "sample", "phase": "after_start",
                   "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                   "elapsed_s": round(elapsed, 6),
                   "read_status": "ok" if vals is not None else "fail",
                   "read_fail_detail": failed,
                   "win_foreground": W7.fg_is(pid)}
            if vals is not None:
                for k in W7.ADDR:
                    rec[k] = vals.get(k)
                mode_hist.append(vals["mode_A8B238"])
                f = vals["frame"]
                if f != last_frame:
                    last_frame = f
                    last_frame_change_ns = t_ns
            else:
                n_fail += 1
            stall_s = (t_ns - last_frame_change_ns) / 1e9
            rec["frame_stall_s"] = round(stall_s, 3)
            if stall_s >= 1.0 and not stall_reported:
                log("    !! frame 停推 ≥1.0s（elapsed=%.1fs, mode=%s, fg=%s）——"
                    "停推可能属闲置态，本卡不判，只记录"
                    % (elapsed, rec.get("mode_A8B238"), rec["win_foreground"]))
                ev("frame_stall_1s", {"elapsed_s": round(elapsed, 3),
                                      "mode": rec.get("mode_A8B238"),
                                      "win_foreground": rec["win_foreground"]})
                stall_reported = True
            if stall_s < 1.0:
                stall_reported = False
            if t_ns >= next_ui:
                rec["ui"] = ui_summary(pid)
                next_ui += int(UI_EVERY_S * 1e9)
            sink.write(rec)
            ec = wt.DWORD(0)
            alive = bool(W7.k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == W7.STILL_ACTIVE)
            if not alive:
                meta["phase_stop"] = "process_exited_during_sampling"
                ev("process_exited", {"phase": "after_start",
                                      "exit_code": ec.value,
                                      "elapsed_s": round(elapsed, 3)})
                log("    !! 采样 %.1fs 时进程退出（exit=%d），如实记录"
                    % (elapsed, ec.value))
                break
            if elapsed >= SAMPLE_SECONDS:
                meta["phase_stop"] = "sample_duration_reached"
                break
            time.sleep(SAMPLE_MS / 1000.0)
        meta["n_samples"] = seq
        meta["n_read_fail"] = n_fail
        meta["mode_hist_head"] = mode_hist[:20]
        meta["mode_hist_tail"] = mode_hist[-20:]
        log("[S4] 采样结束 seq=%d read_fail=%d mode_head=%s mode_tail=%s"
            % (seq, n_fail, mode_hist[:6], mode_hist[-6:]))

    except W7.GuardStop as e:
        meta["error"] = "GuardStop: %s" % e
        exit_code = 2
        log("!! GuardStop: %s" % e)
        ev("guard_stop", {"detail": str(e)})
    except Exception as e:
        meta["error"] = "%s: %s" % (type(e).__name__, e)
        exit_code = 1
        log("!! 异常 %s: %s" % (type(e).__name__, e))
        log(traceback.format_exc())
        ev("exception", {"detail": meta["error"]})

    # ---------- P1 收尾（无论如何执行） ----------
    finally:
        ended_utc = utc_iso()
        if hproc:
            try:
                W7.k32.CloseHandle(hproc)
            except Exception:
                pass
        try:
            log("[P1] 收尾：关闭自启动实例")
            close_steps = W7.close_game(pid, meta.get("game_hwnd") or 0)
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:
            close_steps.append("close_game 异常: %r" % e)
            log("    close_game 异常 %r" % e)
        residual_after = W7.list_gamemd()
        log("    收尾后 gamemd 残留 = %d %s" % (len(residual_after), residual_after))
        try:
            inventory_after = W7.inventory(W7.GAME_DIR)
            log("    收尾后 ra2youli 文件清单 %d 项" % len(inventory_after))
        except Exception as e:
            log("    inventory_after 异常 %r" % e)
        diff = W7.diff_inventory(inventory_before, inventory_after)
        try:
            rows = W7.restore_configs()
            for r in rows:
                log("    还原 %s -> %s" % (r.get("file"),
                                           r.get("post_restore_sha256")
                                           or r.get("post_sha256")))
        except Exception as e:
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
            log("    restore_configs 异常 %r" % e)
        # H1 装入文件必须仍在（本卡禁删禁改名；还原由 Lead 负责）
        h1_still = H1_FILE.exists()
        h1_hash_after = W7.sha256_file(H1_FILE) if h1_still else None
        log("    H1 载体仍在=%s hash_after=%s" % (h1_still, h1_hash_after))

        try:
            (OUT / "run_stdout.txt").write_text("\n".join(LOG_LINES) + "\n",
                                                encoding="utf-8")
        except Exception:
            pass
        meta["ended_utc"] = ended_utc
        meta["residual_after"] = residual_after
        meta["close_steps"] = close_steps
        meta["restore_rows"] = rows
        meta["written_back"] = diff
        meta["inventory_counts"] = [len(inventory_before), len(inventory_after)]
        meta["h1_file_after"] = {"exists": h1_still, "sha256": h1_hash_after,
                                 "untouched": bool(h1_still and h1_hash_after == H1_SHA256)}
        try:
            sink.write({"kind": "meta_end", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                        "exit_code": exit_code, "error": meta["error"],
                        "residual_after": residual_after})
        except Exception:
            pass
        sink.close()
        meta["n_ndjson_lines"] = sink.n_lines
        try:
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1,
                                            sort_keys=True, default=str),
                                 encoding="utf-8")
        except Exception as e:
            log("    写 meta.json 异常 %r" % e)
        log("[P1] 收尾完成（配置已还原，NDJSON=%d 行）" % sink.n_lines)
    return exit_code, meta


# ------------------------------------------------------------------ 离线分析
def load_samples(path):
    samples, events, uis = [], [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("kind") == "sample":
                samples.append(rec)
                if "ui" in rec:
                    uis.append({"elapsed_s": rec["elapsed_s"], "ui": rec["ui"]})
            elif rec.get("kind") == "event":
                events.append(rec)
    return samples, events, uis


def rate_curve(samples, bucket_s=5.0):
    """区间口径速率（非逐帧 FPS）：按 bucket 桶取首末 frame 差分。"""
    ok = [s for s in samples if s.get("read_status") == "ok"
          and isinstance(s.get("frame"), int)]
    if len(ok) < 2:
        return []
    out = []
    b0 = ok[0]
    cur_first = b0
    cur_t0 = b0["elapsed_s"]
    for s in ok[1:]:
        if s["elapsed_s"] - cur_t0 >= bucket_s:
            dt = s["elapsed_s"] - cur_t0
            df = s["frame"] - cur_first["frame"]
            out.append({"t0": round(cur_t0, 2), "t1": round(s["elapsed_s"], 2),
                        "dt": round(dt, 3), "d_frame": df,
                        "rate": round(df / dt, 2) if dt > 0 else None})
            cur_first, cur_t0 = s, s["elapsed_s"]
    dt = ok[-1]["elapsed_s"] - cur_t0
    if dt > 0.5:
        out.append({"t0": round(cur_t0, 2), "t1": round(ok[-1]["elapsed_s"], 2),
                    "dt": round(dt, 3),
                    "d_frame": ok[-1]["frame"] - cur_first["frame"],
                    "rate": round((ok[-1]["frame"] - cur_first["frame"]) / dt, 2)})
    return out


def slide_rates(samples, win_s=2.0):
    """2s 滑动窗区间速率序列的 min/max（区间口径）。"""
    ok = [s for s in samples if s.get("read_status") == "ok"
          and isinstance(s.get("frame"), int)]
    rates = []
    lo = 0
    for hi in range(len(ok)):
        while ok[hi]["t_mono_ns"] - ok[lo]["t_mono_ns"] > win_s * 1e9:
            lo += 1
        if hi > lo:
            dt = (ok[hi]["t_mono_ns"] - ok[lo]["t_mono_ns"]) / 1e9
            df = ok[hi]["frame"] - ok[lo]["frame"]
            if dt > 0:
                rates.append((df / dt, ok[lo]["elapsed_s"]))
    if not rates:
        return None, None
    mn = min(rates, key=lambda x: x[0])
    mx = max(rates, key=lambda x: x[0])
    return ({"rate": round(mn[0], 2), "at_s": round(mn[1], 2)},
            {"rate": round(mx[0], 2), "at_s": round(mx[1], 2)})


def stall_segments(samples, min_s=1.0):
    ok = [s for s in samples if s.get("read_status") == "ok"]
    segs = []
    cur = None
    for s in ok:
        st = s.get("frame_stall_s") or 0
        in_stall = st >= min_s
        if in_stall and cur is None:
            cur = {"t0": s["elapsed_s"], "mode": s.get("mode_A8B238"),
                   "fg": s.get("win_foreground")}
        elif in_stall and cur is not None:
            cur["t_end"] = s["elapsed_s"]
        elif not in_stall and cur is not None:
            cur["t_end"] = s["elapsed_s"]
            segs.append(cur)
            cur = None
    if cur is not None:
        cur["t_end"] = ok[-1]["elapsed_s"]
        segs.append(cur)
    return segs


def dist(samples, key):
    c = {}
    for s in samples:
        v = s.get(key)
        c[v] = c.get(v, 0) + 1
    return c


def run_analyze(in_name="run.ndjson"):
    meta_path = OUT / ("meta_run2.json" if in_name == "run2.ndjson"
                       else "meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    maplist = json.loads((OUT / ("maplist_run2.json" if in_name == "run2.ndjson"
                                 else "maplist.json")).read_text(encoding="utf-8"))
    samples, events, uis = load_samples(OUT / in_name)
    asmp = [s for s in samples if s.get("phase") == "after_start"]
    buckets = rate_curve(asmp, 5.0)
    mn, mx = slide_rates(asmp, 2.0)
    segs = stall_segments(asmp)
    ok_asmp = [s for s in asmp if s.get("read_status") == "ok"]

    ingame_like = []
    for b in buckets:
        if b["rate"] is not None and 29.0 <= b["rate"] <= 32.0:
            ingame_like.append(b)
    hi_span = 0.0
    if ingame_like:
        hi_span = sum(b["dt"] for b in ingame_like)

    verdict = {
        "n_items": maplist["n_items"],
        "delta_vs_base": maplist.get("delta_vs_base"),
        "n_target_hits": maplist.get("n_target_hits"),
        "n_noname_literal": len(maplist.get("noname_literal_indices", [])),
        "noname_literal_indices": maplist.get("noname_literal_indices"),
        "cat1_file_missing": (maplist.get("n_target_hits") == 0
                              and maplist.get("delta_vs_base") == 0),
        "cat2_empty_name": (maplist.get("noname_literal_indices") is not None
                            and len(maplist.get("noname_literal_indices", [])) > 0
                            and maplist.get("delta_vs_base", 0) != 0),
        "cat3_risk": (maplist.get("n_target_hits") or 0) > 1,
        "battle_rate_buckets": len(ingame_like),
        "battle_rate_span_s": round(hi_span, 2),
        "battle_like_60s": hi_span >= 60.0,
        "frame_moved": bool(ok_asmp) and ok_asmp[-1]["frame"] != ok_asmp[0]["frame"],
    }
    result = {
        "run_id": RUN_ID, "generated_utc": utc_iso(),
        "meta_error": meta.get("error"), "phase_stop": meta.get("phase_stop"),
        "n_samples": meta.get("n_samples"),
        "maplist": {k: maplist[k] for k in maplist
                    if k in ("n_items", "delta_vs_base", "matched_by",
                             "n_target_hits", "target_hits", "n_noname",
                             "noname_literal_indices")},
        "buckets": buckets, "slide_min": mn, "slide_max": mx,
        "stall_segments": segs,
        "mode_dist_after_start": dist(asmp, "mode_A8B238"),
        "g_dist": {k: dist(asmp, k) for k in ("g1", "g2", "g3", "g4")},
        "A8E9A0_dist": dist(asmp, "A8E9A0"),
        "ABCD58_dist": dist(asmp, "ABCD58"),
        "A8ED50_range": [min([s.get("A8ED50") for s in ok_asmp
                              if isinstance(s.get("A8ED50"), int)] or [None]),
                         max([s.get("A8ED50") for s in ok_asmp
                              if isinstance(s.get("A8ED50"), int)] or [None])],
        "B0CE88_range": [min([s.get("B0CE88") for s in ok_asmp
                              if isinstance(s.get("B0CE88"), int)] or [None]),
                         max([s.get("B0CE88") for s in ok_asmp
                              if isinstance(s.get("B0CE88"), int)] or [None])],
        "ui_timeline": uis,
        "verdict": verdict,
    }
    (OUT / ("analyze_run2.json" if in_name == "run2.ndjson"
            else "analyze.json")).write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({
        "n_items": verdict["n_items"], "delta": verdict["delta_vs_base"],
        "hits": verdict["n_target_hits"], "noname": verdict["n_noname_literal"],
        "battle_buckets": verdict["battle_rate_buckets"],
        "battle_span_s": verdict["battle_rate_span_s"],
        "battle_like_60s": verdict["battle_like_60s"],
        "frame_moved": verdict["frame_moved"],
        "slide_min": mn, "slide_max": mx,
        "stalls": len(segs), "phase_stop": result["phase_stop"],
        "error": result["meta_error"],
    }, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--run2", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--in", dest="in_name", default="run.ndjson")
    a = ap.parse_args()
    if a.run:
        ec, _meta = run_run()
        return ec
    if a.run2:
        ec, _meta = run_run2()
        return ec
    if a.analyze:
        return run_analyze(a.in_name)
    print("用法：--run 真机第一趟；--run2 真机第二趟（No Name 钉死+开局）；"
          "--analyze [--in run2.ndjson]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
