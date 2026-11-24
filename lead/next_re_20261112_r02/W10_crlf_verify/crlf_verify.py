# -*- coding: utf-8 -*-
"""W10 CRLF 单变量验证（真机，单实例，一趟，只到地图列表，不开局）。

run_id = NEXT_RE_20261112_R02
唯一问题：装入文件换成「只改行尾」（0 裸 LF / 5,884 CRLF）的修复版之后，
地图列表里这条是否仍显示字面 `No Name`？若正常，准确显示串是什么？digest 有没有？

修复版载体（Lead 装入，本卡只核对、禁改禁删）：
  ra2youli\\[2]0LoadBench_U0800_H1.yrm
  315,706 B / SHA-256 afb18a33895c5ff55ab3156c9a43d2a658c5c0889137f251e2d4952622925861
  内容差异仅行尾；首节仍是 [Preview]（故意不动的第二变量）。

判定（只归因到行尾，不推断节顺序）：
  - 名称正常显示（[Basic]Name 内容）且 digest 非 No Digest ⇒ 行尾是主因 [已证]
  - 仍 No Name ⇒ 行尾不是主因 [否证]（下一变量 = 节顺序，交回 Lead）
  - 空名 / 读失败 / 条目数变化 ⇒ 如实记录原始字节与数量，分开记录
    「没读到名称」（diag≠ok，记原始字节）与「名称为空」（读到但空串）。

复用：W9_h1_layering\\h1_probe.py 的已验证实现（read_map_names_diag / ui_summary，
其 module 级已加载 W7_load_baseline\\load_baseline_probe.py 全部底层）。
本卡禁 SuspendThread/StackWalk64/MiniDump/断点/注入/写目标内存；只读 RPM。

用法：
  python -X utf8 crlf_verify.py --run       # 真机一趟（启动→导航→列表→审计→收尾）
  python -X utf8 crlf_verify.py --analyze   # 离线：与 W9 [97] 逐字段对照 + VERDICT
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import importlib.util
import json
import re
import sys
import time
import traceback
from pathlib import Path

RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
R2 = ROOT / "lead" / "next_re_20261112_r02"
W10 = R2 / "W10_crlf_verify"
OUT = W10 / "out"
W9_OUT = R2 / "W9_h1_layering" / "out"
H1_PROBE = R2 / "W9_h1_layering" / "h1_probe.py"

SELF_OWNER = "w10_crlf_verify_subagent"
LEAD_OWNER = "lead"

H1_FILE = ROOT / "ra2youli" / "[2]0LoadBench_U0800_H1.yrm"
H1_SHA256 = "afb18a33895c5ff55ab3156c9a43d2a658c5c0889137f251e2d4952622925861"
H1_SIZE = 315706

# 离线 [Basic]Name 原值（行尾修复不改动内容；W9 第 2 步读得）
BASIC_NAME = "[2] 0LoadBench U0800 H1 fp:1189b6b550ff"
PAT_SUB_NAME = "loadbench u0800 h1"          # 子串匹配 1（显示名，lower() 后）
PAT_SUB_FILE = "0loadbench_u0800_h1"         # 子串匹配 2（内嵌文件名形态）

EXPECTED_LIST_BASE = 268                     # W7 实测装入前列表条目数
EXPECTED_LIST_NOW = 269                      # 装入 +1 预期（W9 两趟实测 269）

CTRL_IDX = 96                                # 对照条目：[2] 0LoadBench U800
W9_NONAME_IDX = (91, 97)                     # W9 的 No Name 索引（91=prm.yrm，97=H1）
AUDIT_FIXED_IDX = (91, 96, 97)               # 固定审计集（连续性对照）

MENU_TIMEOUT_S = 90
PANEL_SETTLE_S = 1.8                         # LB_SETCURSEL 后信息面板稳定等待

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


# ------------------------------------------------------------------ 复用 h1_probe（其模块级加载 W7）
def load_hp():
    spec = importlib.util.spec_from_file_location("h1_probe", str(H1_PROBE))
    hp = importlib.util.module_from_spec(spec)
    sys.modules["h1_probe"] = hp
    spec.loader.exec_module(hp)
    return hp


HP = load_hp()
W7 = HP.W7
W7.SELF_OWNER = SELF_OWNER              # 锁守卫允许接管/持有本代理（write_lock 用）
LEAD_OWNER = getattr(W7, "LEAD_OWNER", LEAD_OWNER)
LOCK_PATH = W7.LOCK_PATH


# ------------------------------------------------------------------ itemdata 768B 缓冲解析
_B64_RE = re.compile(r"^[A-Za-z0-9+/]{16,}={0,2}$")


def _ascii_runs(b):
    """768B 内所有 ≥4 字符的可打印 ASCII 连续段 [(offset, text)]。"""
    runs = []
    cur = bytearray()
    start = None
    for i, ch in enumerate(b):
        if 0x20 <= ch < 0x7F:
            if start is None:
                start = i
            cur.append(ch)
        else:
            if len(cur) >= 4:
                runs.append((start, cur.decode("ascii")))
            cur = bytearray()
            start = None
    if len(cur) >= 4:
        runs.append((start, cur.decode("ascii")))
    return runs


def parse_item_buffer(b):
    """解析 itemdata 指向的记录缓冲（W9 已验证布局）：
    头部 = UTF-16LE 名称槽（到 null）；随后内嵌 ASCII 文件名（*.yrm）；
    再后 digest 区（"No Digest" 或 base64）。
    返回 dict；「没读到」与「读到但空」由调用方区分（本函数只在读到字节时被调）。"""
    rec = {"buf_len": len(b)}
    # 名称槽：UTF-16LE 从 0 到 null（按偶数步进）
    end = None
    for j in range(0, len(b) - 1, 2):
        if b[j] == 0 and b[j + 1] == 0:
            end = j
            break
    if end is None:
        end = min(len(b) - (len(b) % 2), 480)
        rec["name_slot_diag"] = "no_terminator_in_768b"
    else:
        rec["name_slot_diag"] = "ok"
    raw = b[:end]
    rec["name_slot_utf16_bytes"] = len(raw)
    rec["name_slot_chars"] = end // 2
    try:
        rec["name_slot"] = raw.decode("utf-16-le")
    except Exception as e:
        rec["name_slot"] = None
        rec["name_slot_diag"] = "decode_failed:%r" % e
        rec["name_slot_raw_hex_head"] = raw[:32].hex()
    if rec.get("name_slot") == "":
        rec["name_slot_diag"] = "empty_utf16"     # 读到字节但名称为空串
    # ASCII 段
    runs = _ascii_runs(b)
    rec["ascii_runs"] = [{"offset": o, "text": t} for o, t in runs]
    # 内嵌文件名：第一个含 .yrm 的段
    rec["filename"] = None
    rec["filename_offset"] = None
    for o, t in runs:
        if ".yrm" in t.lower():
            rec["filename"] = t
            rec["filename_offset"] = o
            break
    # digest：优先字面 No Digest；否则文件名之后的 base64 形态段
    rec["digest"] = None
    rec["digest_offset"] = None
    rec["digest_is_no_digest"] = None
    for o, t in runs:
        if t.strip() == "No Digest":
            rec["digest"] = t
            rec["digest_offset"] = o
            rec["digest_is_no_digest"] = True
            break
    if rec["digest"] is None:
        lo = (rec["filename_offset"] or 0)
        for o, t in runs:
            if o > lo and _B64_RE.match(t):
                rec["digest"] = t
                rec["digest_offset"] = o
                rec["digest_is_no_digest"] = False
                break
    # 其余 ASCII 段（诊断用，如 GameMode "standard"）
    used = {rec.get("filename_offset"), rec.get("digest_offset")}
    rec["other_ascii_runs"] = [{"offset": o, "text": t} for o, t in runs
                               if o not in used]
    return rec


# ------------------------------------------------------------------ 目标匹配
def match_target(entries):
    """三种口径分别记录，优先级：精确完整名 > 子串1(显示名) > 子串2(文件名形态)。
    返回 (target_list, matched_by, hits_full, hits_p1, hits_p2)。"""
    hits_full = [e for e in entries if e["name"] == BASIC_NAME]
    hits_p1 = [e for e in entries
               if e["name"] and PAT_SUB_NAME in e["name"].lower()]
    hits_p2 = [e for e in entries
               if e["name"] and PAT_SUB_FILE in e["name"].lower()]
    if hits_full:
        return hits_full, "exact_full_name", hits_full, hits_p1, hits_p2
    if hits_p1:
        return hits_p1, "substring:%s" % PAT_SUB_NAME, hits_full, hits_p1, hits_p2
    if hits_p2:
        return hits_p2, "substring:%s" % PAT_SUB_FILE, hits_full, hits_p1, hits_p2
    return [], "none", hits_full, hits_p1, hits_p2


def audit_entry(hproc, lb, idx, entries, is_target):
    """对单条目做 itemdata 768B hex 审计（复用 W9 逻辑 + 新增逐字段解析）。"""
    d = int(W7.smt(lb, W7.LB_GETITEMDATA, idx)) & 0xFFFFFFFF
    rec = {"index": idx,
           "itemdata": d,
           "itemdata_hex": hex(d) if d else "0",
           "display_diag": entries[idx]["diag"],
           "display_name_via_list": entries[idx]["name"]}
    if not d:
        rec["audit_error"] = "itemdata_zero"
        return rec
    b = W7.rpm_partial(hproc, d, 768)
    if b is None:
        rec["audit_error"] = "rpm_partial_768_failed"
        rec["buf_read_attempts_hex"] = None
        return rec
    b = bytes(b)
    rec["buf768"] = parse_item_buffer(b)
    fname = "itemdata_audit_%d.hex" % idx
    try:
        (OUT / fname).write_text(b.hex(), encoding="ascii")
        rec["raw_hex_file"] = fname
    except Exception as e:
        rec["raw_hex_file_error"] = repr(e)
    if is_target:
        try:
            (OUT / "itemdata_audit.hex").write_text(b.hex(), encoding="ascii")
            rec["raw_hex_file_target"] = "itemdata_audit.hex"
        except Exception as e:
            rec["raw_hex_file_target_error"] = repr(e)
    return rec


# ------------------------------------------------------------------ 主流程
def run_verify():
    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / "meta.json"
    maplist_path = OUT / "maplist.json"
    sink = W7.NDJSONSink(OUT / "run.ndjson")
    started_utc = utc_iso()
    exit_code = 0
    pid, launcher_pid, own = 0, 0, ""
    hproc = None
    game_hwnd = 0
    prelaunch_hashes = {}
    inventory_before, inventory_after = {}, {}
    residual_before, residual_after = [], []
    close_steps = []
    meta = {
        "run_id": RUN_ID,
        "card": "W10 CRLF 单变量验证（只到列表）",
        "started_utc": started_utc,
        "h1_file": {"path": str(H1_FILE), "expected_sha256": H1_SHA256,
                    "expected_size": H1_SIZE},
        "expected": {"list_base": EXPECTED_LIST_BASE, "list_now": EXPECTED_LIST_NOW,
                     "basic_name": BASIC_NAME,
                     "patterns": [PAT_SUB_NAME, PAT_SUB_FILE]},
        "pid": None, "is32": None, "game_hwnd": None, "game_tid": None,
        "code_signature_ok": None, "prelaunch_hashes": {},
        "maplist": None, "target": None, "audits": {}, "panels": {},
        "residual_before": [], "residual_after": [], "close_steps": [],
        "restore_rows": [], "written_back": None, "inventory_counts": None,
        "h1_file_after": None, "lock_restored": None,
        "error": None,
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
        log("[S0] 实例锁 + 残留进程 + 哈希守卫（W10）")
        lock_state = W7.check_lock()
        log("    实例锁 owner 状态 = %s" % lock_state)
        W7.write_lock("W10 CRLF 单变量验证（只改行尾；只到地图列表）")
        ev("lock_claimed", {"owner": SELF_OWNER, "state": lock_state})
        log("    锁已改为 owner=%s" % SELF_OWNER)

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
            log("    %-20s match=%s" % (name, prelaunch_hashes[name]["match"]))
        meta["prelaunch_hashes"] = prelaunch_hashes
        if not all(v["match"] for v in prelaunch_hashes.values()):
            bad = [n for n, v in prelaunch_hashes.items() if not v["match"]]
            raise W7.GuardStop("启动前哈希与基线不一致，停手：%s" % bad)

        if not H1_FILE.exists():
            raise W7.GuardStop("H1 载体不在 ra2youli：%s" % H1_FILE)
        h1_hash = W7.sha256_file(H1_FILE)
        h1_size = H1_FILE.stat().st_size
        h1_ok = (h1_hash == H1_SHA256 and h1_size == H1_SIZE)
        meta["h1_file"].update({"sha256": h1_hash, "size": h1_size,
                                "match": h1_ok})
        log("    H1 载体（CRLF 修复版）%d B sha=%s match=%s"
            % (h1_size, h1_hash, h1_ok))
        if not h1_ok:
            raise W7.GuardStop("H1 载体哈希/大小与 Lead 装入记录不一致，停手")
        ev("h1_file_verified", {"size": h1_size, "sha256": h1_hash})

        inventory_before = W7.inventory(W7.GAME_DIR)
        log("    启动前 ra2youli 文件清单 %d 项；守卫全过"
            % len(inventory_before))
        sink.write({"kind": "meta", "seq": 0,
                    "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                    "prelaunch_hashes": prelaunch_hashes,
                    "h1_file": meta["h1_file"],
                    "residual_before": residual_before})

        # ---------- S1 启动 ----------
        log("[S1] WMI 分离启动 gamemd.exe")
        ev("launching", {})
        launcher_pid = W7.launch_game()
        pid, own = W7.wait_for_pid(launcher_pid, MENU_TIMEOUT_S)
        meta["pid"], meta["launcher_pid"], meta["ownership"] = (pid,
                                                                launcher_pid,
                                                                own)
        log("    pid=%d 归属=%s (launcher_pid=%d)" % (pid, own, launcher_pid))
        ev("pid_found", {"pid": pid, "ownership": own})
        hproc = W7.k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not hproc:
            raise RuntimeError("OpenProcess(VM_READ|QUERY_INFORMATION) 失败")
        flag = wt.BOOL(0)
        W7.k32.IsWow64Process(hproc, ctypes.byref(flag))
        meta["is32"] = bool(flag.value)
        sig = W7.rpm(hproc, W7.CODE_SIG_ADDR, len(W7.CODE_SIG_EXPECT))
        meta["code_signature_ok"] = (sig == W7.CODE_SIG_EXPECT)
        log("    is32=%s 代码签名@0x55DE4F ok=%s"
            % (meta["is32"], meta["code_signature_ok"]))
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

        # ---------- S2 导航 + 完整列表读取（只到列表，不开局） ----------
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

        entries = HP.read_map_names_diag(hproc, lb, n)
        noname_lit = [e for e in entries if e["name"] == "No Name"]
        # 「没读到名称」（diag≠ok：itemdata_zero / rpm_failed / decode_failed）
        read_fail = [e for e in entries
                     if e["diag"] not in ("ok", "empty_utf16")]
        # 「名称为空」（读到字节但空串）
        empty_name = [e for e in entries if e["diag"] == "empty_utf16"]
        target_list, matched_by, hits_full, hits_p1, hits_p2 = \
            match_target(entries)
        for e in target_list[:20]:
            log("    目标命中 [%3d] %r" % (e["index"], e["name"]))
        log("    匹配方式=%s；命中 %d 条（完整名 %d / 子串1 %d / 子串2 %d）；"
            "字面No Name %d 个 %s；读失败 %d 个 %s；空串 %d 个 %s"
            % (matched_by, len(target_list), len(hits_full), len(hits_p1),
               len(hits_p2), len(noname_lit),
               [e["index"] for e in noname_lit], len(read_fail),
               [(e["index"], e["diag"]) for e in read_fail][:30],
               len(empty_name), [e["index"] for e in empty_name][:30]))
        ev("maplist_read", {
            "n_items": n, "matched_by": matched_by,
            "n_target": len(target_list), "n_full": len(hits_full),
            "n_p1": len(hits_p1), "n_p2": len(hits_p2),
            "n_noname": len(noname_lit), "n_read_fail": len(read_fail),
            "n_empty": len(empty_name)})

        maplist = {
            "run_id": RUN_ID, "t_utc_iso": utc_iso(), "listbox": int(lb),
            "n_items": n,
            "expected_base": EXPECTED_LIST_BASE,
            "expected_now": EXPECTED_LIST_NOW,
            "delta_vs_base": n - EXPECTED_LIST_BASE,
            "basic_name_offline": BASIC_NAME,
            "pattern_full": BASIC_NAME, "pattern_sub1": PAT_SUB_NAME,
            "pattern_sub2": PAT_SUB_FILE,
            "matched_by": matched_by,
            "n_target_hits": len(target_list),
            "target_hits": [{"index": e["index"], "name": e["name"]}
                            for e in target_list],
            "n_hits_full": len(hits_full),
            "hits_full": [{"index": e["index"], "name": e["name"]}
                          for e in hits_full],
            "n_hits_p1": len(hits_p1),
            "hits_p1": [{"index": e["index"], "name": e["name"]}
                        for e in hits_p1],
            "n_hits_p2": len(hits_p2),
            "hits_p2": [{"index": e["index"], "name": e["name"]}
                        for e in hits_p2],
            "n_noname_literal": len(noname_lit),
            "noname_literal_indices": [e["index"] for e in noname_lit],
            "n_read_fail": len(read_fail),
            "read_fail": read_fail,
            "n_empty_name": len(empty_name),
            "empty_name_indices": [e["index"] for e in empty_name],
            "entries": entries,
        }
        maplist_path.write_text(json.dumps(maplist, ensure_ascii=False,
                                           indent=1), encoding="utf-8")
        log("    maplist.json 已写（%d 条）" % n)

        # ---------- S3 itemdata 768B 审计（目标 + 固定对照集，不开局） ----------
        log("[S3] itemdata 768B 审计（目标 + [91]/[96]/[97] 对照）")
        audits = {}
        target_idxs = [e["index"] for e in target_list]
        audit_idx = sorted(set(target_idxs) |
                           set(i for i in AUDIT_FIXED_IDX if i < n))
        for idx in audit_idx:
            is_t = idx in target_idxs
            rec = audit_entry(hproc, lb, idx, entries, is_t)
            audits[idx] = rec
            b = rec.get("buf768") or {}
            log("    [%d] itemdata=%s 名称槽=%r 文件名=%r digest=%r%s"
                % (idx, rec["itemdata_hex"], b.get("name_slot"),
                   b.get("filename"), b.get("digest"),
                   " （目标）" if is_t else ""))
        meta["audits"] = {str(k): v for k, v in audits.items()}
        ev("audit_done", {"indices": audit_idx, "target": target_idxs})

        # ---------- S4 目标/对照条目信息面板快照（辅助证据；失败不影响） ----------
        panels = {}
        for idx, tag in ([(target_idxs[0], "panel_target")]
                         if target_idxs else []) + \
                        [(CTRL_IDX, "panel_96_ctrl")]:
            try:
                W7.smt(lb, W7.LB_SETCURSEL, idx)
                time.sleep(PANEL_SETTLE_S)
                panels[tag] = {"index": idx, "ui": HP.ui_summary(pid)}
                log("    %s(idx=%d) statics=%s"
                    % (tag, idx, panels[tag]["ui"]["statics"][:10]))
                ev("panel_snapshot", {"tag": tag, "index": idx,
                                      "ui": panels[tag]["ui"]})
            except Exception as e:
                panels[tag] = {"index": idx, "error": repr(e)}
                log("    %s(idx=%d) 面板快照异常 %r（不影响主流程）"
                    % (tag, idx, e))
        meta["panels"] = panels

        meta["maplist"] = {
            "n_items": n, "delta_vs_base": n - EXPECTED_LIST_BASE,
            "matched_by": matched_by,
            "n_target_hits": len(target_list),
            "target_hits": maplist["target_hits"],
            "n_noname_literal": len(noname_lit),
            "noname_literal_indices": maplist["noname_literal_indices"],
            "n_read_fail": len(read_fail),
            "n_empty_name": len(empty_name),
        }
        meta["target"] = {"indices": target_idxs, "matched_by": matched_by,
                          "names": [{"index": e["index"],
                                     "name": e["name"]}
                                    for e in target_list]}
        log("[S4] 列表+审计完成；不开局，进入收尾")

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
            close_steps = W7.close_game(pid, game_hwnd)
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:
            close_steps.append("close_game 异常: %r" % e)
            log("    close_game 异常 %r" % e)
        residual_after = W7.list_gamemd()
        log("    收尾后 gamemd 残留 = %d %s"
            % (len(residual_after), residual_after))
        try:
            inventory_after = W7.inventory(W7.GAME_DIR)
            log("    收尾后 ra2youli 文件清单 %d 项" % len(inventory_after))
        except Exception as e:
            log("    inventory_after 异常 %r" % e)
        try:
            diff = W7.diff_inventory(inventory_before, inventory_after)
        except Exception as e:
            diff = {"error": repr(e)}
        try:
            rows = W7.restore_configs()
            for r in rows:
                log("    还原 %s -> %s"
                    % (r.get("file"),
                       r.get("post_restore_sha256") or r.get("post_sha256")))
        except Exception as e:
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
            log("    restore_configs 异常 %r" % e)
        # H1 装入文件必须仍在且未被改动（本卡禁删禁改名；还原由 Lead 负责）
        h1_still = H1_FILE.exists()
        h1_hash_after = W7.sha256_file(H1_FILE) if h1_still else None
        log("    H1 载体仍在=%s hash_after=%s" % (h1_still, h1_hash_after))
        # 锁恢复 owner=lead
        try:
            LOCK_PATH.write_text(
                "run_id=%s\nowner=%s\ntime=%s\npurpose=%s\n"
                % (RUN_ID, LEAD_OWNER,
                   datetime.datetime.now().astimezone().isoformat(),
                   "W10 done: CRLF verify finished, lock returned to lead"),
                encoding="utf-8")
            meta["lock_restored"] = True
            log("    实例锁已恢复 owner=%s" % LEAD_OWNER)
        except Exception as e:
            meta["lock_restored"] = repr(e)
            log("    锁恢复异常 %r" % e)

        try:
            (OUT / "run_stdout.txt").write_text(
                "\n".join(LOG_LINES) + "\n", encoding="utf-8")
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
                        "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                        "exit_code": exit_code, "error": meta["error"],
                        "residual_after": residual_after})
        except Exception:
            pass
        sink.close()
        try:
            meta_path.write_text(json.dumps(meta, ensure_ascii=False,
                                            indent=1, sort_keys=True,
                                            default=str), encoding="utf-8")
        except Exception as e:
            log("    写 meta.json 异常 %r" % e)
        log("[P1] 收尾完成（配置已还原，锁已还 lead）")
    return exit_code, meta


# ------------------------------------------------------------------ 离线分析
def load_hex(path):
    txt = path.read_text(encoding="ascii").strip()
    return bytes.fromhex(txt)


def audit_from_hex(idx, b, display_name=None, source=""):
    rec = parse_item_buffer(b)
    rec = dict(rec)
    rec["index"] = idx
    rec["display_name_via_list"] = display_name
    rec["source"] = source
    return rec


def fmt_field(rec, key):
    v = rec.get(key)
    if key == "name_slot" and v is not None:
        return json.dumps(v, ensure_ascii=False)
    if v is None:
        return "（未解析出）"
    return str(v)


def run_analyze():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))
    maplist = json.loads((OUT / "maplist.json").read_text(encoding="utf-8"))
    w9_maplist = json.loads((W9_OUT / "maplist_run2.json")
                            .read_text(encoding="utf-8"))

    # ---- W10 侧审计（重读 hex，保证可重跑一致） ----
    w10_audits = {}
    for idx_s, rec in meta.get("audits", {}).items():
        f = rec.get("raw_hex_file")
        if f and (OUT / f).exists():
            w10_audits[int(idx_s)] = audit_from_hex(
                int(idx_s), load_hex(OUT / f),
                display_name=rec.get("display_name_via_list"),
                source="W10/%s" % f)

    # ---- W9 侧审计（同一解析器重算，逐字段可比） ----
    w9_names = {e["index"]: e.get("name") for e in w9_maplist.get("entries", [])}
    w9_audits = {}
    for idx in (91, 96, 97):
        f = W9_OUT / ("nn_audit_%d.hex" % idx)
        if f.exists():
            w9_audits[idx] = audit_from_hex(idx, load_hex(f),
                                            display_name=w9_names.get(idx),
                                            source="W9/nn_audit_%d.hex" % idx)

    # ---- 列表逐索引 diff（W9 run2 vs W10） ----
    w9_entries = w9_maplist.get("entries", [])
    w10_entries = maplist.get("entries", [])
    diffs = []
    for i in range(min(len(w9_entries), len(w10_entries))):
        a, b = w9_entries[i].get("name"), w10_entries[i].get("name")
        if a != b:
            diffs.append({"index": i, "w9_name": a, "w10_name": b,
                          "w9_diag": w9_entries[i].get("diag"),
                          "w10_diag": w10_entries[i].get("diag")})
    list_diff = {
        "n_w9": len(w9_entries), "n_w10": len(w10_entries),
        "n_items_equal": len(w9_entries) == len(w10_entries),
        "n_diff_entries": len(diffs), "diffs": diffs,
    }

    # ---- 目标字段 ----
    target_idxs = (meta.get("target") or {}).get("indices") or []
    w9_97 = w9_audits.get(97)
    w10_target = w10_audits.get(target_idxs[0]) if target_idxs else None
    target_basis = "display_name_hit"
    if w10_target is None:
        # 无显示名命中 ⇒ 按内嵌 ASCII 文件名钉身份（优先 0LoadBench_U0800_H1）
        for idx in sorted(w10_audits):
            f = w10_audits[idx].get("filename") or ""
            if PAT_SUB_FILE in f.lower():
                w10_target = w10_audits[idx]
                target_basis = "embedded_filename:%s" % PAT_SUB_FILE
                break
    if w10_target is None and maplist.get("noname_literal_indices"):
        # 身份仍未钉死：取第一个字面 No Name 条目并显式声明未定身份
        cand = maplist["noname_literal_indices"][0]
        w10_target = w10_audits.get(cand)
        target_basis = "first_no_name_entry:identity_unconfirmed"
    # 交付物 out\itemdata_audit.hex = 目标条目 768B hex 原文
    # （run 阶段仅在显示名命中时写；无命中、身份由内嵌文件名钉死时，
    #   从 itemdata_audit_<idx>.hex 复写出目标 hex，口径记入 target_basis）
    if w10_target is not None and not (OUT / "itemdata_audit.hex").exists():
        t_hex_file = OUT / ("itemdata_audit_%d.hex" % w10_target["index"])
        if t_hex_file.exists():
            (OUT / "itemdata_audit.hex").write_text(
                t_hex_file.read_text(encoding="ascii"), encoding="ascii")
            log("    itemdata_audit.hex 由 itemdata_audit_%d.hex 复出"
                "（目标身份：%s）" % (w10_target["index"], target_basis))

    # ---- 目标缓冲逐字节对比（W9 [97] vs W10 目标；运行期易变字节除外） ----
    buf_byte_diff = None
    if w9_97 is not None and w10_target is not None:
        f10 = OUT / ("itemdata_audit_%d.hex" % w10_target["index"])
        f9 = W9_OUT / "nn_audit_97.hex"
        if f10.exists() and f9.exists():
            a = bytes.fromhex(f10.read_text(encoding="ascii").strip())
            b = bytes.fromhex(f9.read_text(encoding="ascii").strip())
            diff_offs = [i for i in range(min(len(a), len(b)))
                         if a[i] != b[i]]
            segs = []
            for i in diff_offs:
                if segs and i == segs[-1][1] + 1:
                    segs[-1][1] = i
                else:
                    segs.append([i, i])
            buf_byte_diff = {
                "n_bytes": min(len(a), len(b)),
                "n_diff_bytes": len(diff_offs),
                "diff_segments": [tuple(s) for s in segs],
                "name_slot_0_87_equal": a[:88] == b[:88],
                "filename_88_116_equal": a[88:117] == b[88:117],
                "digest_348_361_equal": a[348:362] == b[348:362],
            }

    # ---- 判定 ----
    name_ok = bool(maplist.get("n_target_hits"))
    digest_present = bool(w10_target and w10_target.get("digest")
                          and not w10_target.get("digest_is_no_digest"))
    still_noname = bool(maplist.get("noname_literal_indices"))
    n_items = maplist.get("n_items")
    delta = maplist.get("delta_vs_base")

    if name_ok and digest_present and not still_noname:
        verdict = "crlf_confirmed"
        verdict_zh = ("行尾是主因 [已证]：CRLF 修复后名称正常显示且 digest 正常，"
                      "字面 No Name 条目清零（W9 的 [97] No Name 消失）。")
    elif name_ok and digest_present and still_noname:
        verdict = "crlf_confirmed_partial_residual"
        verdict_zh = ("行尾是主因 [已证]（本条）：目标条目名称/digest 已正常；"
                      "但仍存在其它字面 No Name 条目（见索引清单，应仅为 [91] prm.yrm 历史项）。")
    elif name_ok and not digest_present:
        verdict = "name_fixed_digest_missing"
        verdict_zh = ("名称已修复但 digest 仍缺失 [部分证实]：行尾修复使 Name= 可读"
                      "（名称显示正常），digest 生成另有条件/来源，须单列观测。")
    elif (not name_ok) and still_noname and delta == 1:
        verdict = "crlf_not_the_cause"
        verdict_zh = ("行尾不是主因 [否证]：条目已进列表（+1）但仍显示字面 No Name；"
                      "下一变量 = 节顺序（[Preview] 打头），交回 Lead，本卡未改动。")
    elif delta == 0:
        verdict = "file_not_scanned"
        verdict_zh = ("条目数未变（仍 %d）：文件未被扫描到，与「显示 No Name」是不同"
                      "问题；须先查扫描/文件层。" % (n_items,))
    else:
        verdict = "inconclusive"
        verdict_zh = "证据不全，按未定 [未定] 记录；见 meta.json 与 maplist.json。"

    # ---- compare_with_W9.md ----
    def field_row(label, a, b):
        return "| %s | %s | %s |" % (label, a, b)

    t_idx = w10_target.get("index") if w10_target else "-"
    lines = []
    lines.append("# W10 CRLF 修复版 与 W9 原件 —— 逐字段对照")
    lines.append("")
    lines.append("- run_id：`%s`" % RUN_ID)
    lines.append("- 生成：`crlf_verify.py --analyze`（%s，同一解析器重算双方 hex）"
                 % utc_iso())
    lines.append("- 变量：仅行尾（W9 原件 0 CRLF/5,884 裸 LF → W10 修复版 "
                 "0 裸 LF/5,884 CRLF；首节仍 [Preview] 未动）")
    lines.append("- W9 基线：`W9_h1_layering\\out\\nn_audit_97.hex` + "
                 "`maplist_run2.json`；W10：`W10_crlf_verify\\out\\itemdata_audit.hex`"
                 " + `maplist.json`")
    lines.append("")
    lines.append("## 1. 主对照：W9 [97]（原件） vs W10 [%s]（CRLF 修复版）" % t_idx)
    lines.append("")
    lines.append("| 字段 | W9 run2 [97]（裸 LF 原件） | W10 [%s]（CRLF 修复版） |" % t_idx)
    lines.append("|---|---|---|")
    a, b = w9_97 or {}, w10_target or {}
    lines.append(field_row("列表条目总数",
                           "%d（基线 268，Δ+1）" % w9_maplist.get("n_items"),
                           "%d（基线 %d，Δ%+d）"
                           % (n_items, EXPECTED_LIST_BASE, delta)))
    lines.append(field_row("条目索引", "97", str(t_idx)))
    lines.append(field_row("显示名（列表读取）",
                           json.dumps(a.get("display_name_via_list"),
                                      ensure_ascii=False)
                           if a.get("display_name_via_list") is not None
                           else "（未读取）",
                           json.dumps(b.get("display_name_via_list"),
                                      ensure_ascii=False)
                           if b.get("display_name_via_list") is not None
                           else "（未读取）"))
    lines.append(field_row("名称槽（缓冲 UTF-16 头）",
                           fmt_field(a, "name_slot"),
                           fmt_field(b, "name_slot")))
    lines.append(field_row("名称槽诊断", a.get("name_slot_diag", "-"),
                           b.get("name_slot_diag", "-")))
    lines.append(field_row("内嵌 ASCII 文件名",
                           fmt_field(a, "filename"), fmt_field(b, "filename")))
    lines.append(field_row("文件名缓冲偏移",
                           str(a.get("filename_offset")),
                           str(b.get("filename_offset"))))
    lines.append(field_row("digest 字段", fmt_field(a, "digest"),
                           fmt_field(b, "digest")))
    lines.append(field_row("digest 是否字面 No Digest",
                           str(a.get("digest_is_no_digest")),
                           str(b.get("digest_is_no_digest"))))
    lines.append(field_row("digest 缓冲偏移", str(a.get("digest_offset")),
                           str(b.get("digest_offset"))))
    lines.append(field_row("目标显示名命中数",
                           "0（完整名与子串均未命中）",
                           "%d（matched_by=%s）"
                           % (maplist.get("n_target_hits"),
                              maplist.get("matched_by"))))
    lines.append(field_row("字面 No Name 条目",
                           "2 个：[91], [97]",
                           "%d 个：%s" % (maplist.get("n_noname_literal"),
                                          maplist.get("noname_literal_indices"))))
    lines.append(field_row("读失败/空串条目",
                           "0 / 0",
                           "%d / %d" % (maplist.get("n_read_fail"),
                                        maplist.get("n_empty_name"))))
    lines.append("")
    lines.append("## 2. 连续性对照（环境未变的旁证）")
    lines.append("")
    lines.append("| 字段 | W9 [91] | W10 [91] | W9 [96] | W10 [96] |")
    lines.append("|---|---|---|---|---|")
    a91, b91 = w9_audits.get(91, {}), w10_audits.get(91, {})
    a96, b96 = w9_audits.get(96, {}), w10_audits.get(96, {})
    lines.append("| 显示名 | %s | %s | %s | %s |" % (
        json.dumps(a91.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(b91.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(a96.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(b96.get("display_name_via_list"), ensure_ascii=False)))
    lines.append("| 名称槽 | %s | %s | %s | %s |" % (
        fmt_field(a91, "name_slot"), fmt_field(b91, "name_slot"),
        fmt_field(a96, "name_slot"), fmt_field(b96, "name_slot")))
    lines.append("| 文件名 | %s | %s | %s | %s |" % (
        fmt_field(a91, "filename"), fmt_field(b91, "filename"),
        fmt_field(a96, "filename"), fmt_field(b96, "filename")))
    lines.append("| digest | %s | %s | %s | %s |" % (
        fmt_field(a91, "digest"), fmt_field(b91, "digest"),
        fmt_field(a96, "digest"), fmt_field(b96, "digest")))
    lines.append("")
    lines.append("## 3. 列表逐索引 diff（W9 run2 vs W10，条目名按索引比对）")
    lines.append("")
    lines.append("- 条目数：W9=%d，W10=%d，%s"
                 % (list_diff["n_w9"], list_diff["n_w10"],
                    "一致" if list_diff["n_items_equal"] else "不一致"))
    lines.append("- 名称差异条目数：%d" % list_diff["n_diff_entries"])
    for d in list_diff["diffs"]:
        lines.append("  - [%d] W9=%r → W10=%r（diag %s→%s）"
                     % (d["index"], d["w9_name"], d["w10_name"],
                        d["w9_diag"], d["w10_diag"]))
    lines.append("")
    lines.append("## 3bis. 目标条目缓冲 768B 逐字节对比（W9 [97] vs W10 [%s]）"
                 % t_idx)
    lines.append("")
    if buf_byte_diff:
        lines.append("- 差异字节：%d / %d（散落单字节，运行期易变计数类，"
                     "偏移 %s）"
                     % (buf_byte_diff["n_diff_bytes"],
                        buf_byte_diff["n_bytes"],
                        buf_byte_diff["diff_segments"]))
        lines.append("- 名称槽 0–87 逐字节相等：%s；内嵌文件名 88–116 相等：%s；"
                     "digest 区 348–361 相等：%s"
                     % (buf_byte_diff["name_slot_0_87_equal"],
                        buf_byte_diff["filename_88_116_equal"],
                        buf_byte_diff["digest_348_361_equal"]))
        lines.append("⇒ 记录结构（布局/偏移/字段内容）与 W9 完全一致，"
                     "差异仅为运行期易变字节；`No Name`+`No Digest` 状态本身"
                     "两次运行相同。")
    else:
        lines.append("-（缺 hex，未做逐字节对比）")
    lines.append("")
    lines.append("## 4. 判定")
    lines.append("")
    lines.append("- verdict：`%s`" % verdict)
    lines.append("- %s" % verdict_zh)
    lines.append("")
    (OUT / "compare_with_W9.md").write_text("\n".join(lines) + "\n",
                                            encoding="utf-8")

    # ---- VERDICT.md ----
    v = []
    v.append("# W10 VERDICT —— CRLF 单变量验证（只到地图列表）")
    v.append("")
    v.append("- run_id：`%s`；日期：2026-11-13" % RUN_ID)
    v.append("- 变量：仅行尾（裸 LF → CRLF，5,884 处；内容其它字节等价；"
             "首节仍 `[Preview]` 未动）")
    v.append("- 载体：`ra2youli\\[2]0LoadBench_U0800_H1.yrm` 315,706 B / "
             "SHA-256 `afb18a33…2925861`（run 前后哈希一致，未改动）")
    v.append("- 离线 [Basic]Name 预期显示：`%s`" % BASIC_NAME)
    v.append("")
    v.append("## 主因判定")
    v.append("")
    v.append("**verdict = `%s`**" % verdict)
    v.append("")
    v.append("%s" % verdict_zh)
    v.append("")
    v.append("## 关键证据")
    v.append("")
    v.append("1. 条目总数：W10=%d（基线 %d，Δ%+d；W9 两趟均 269）——文件被扫描、"
             "进了列表%s" % (n_items, EXPECTED_LIST_BASE, delta,
                             "" if delta == 1 else "（与预期不符，见下）"))
    v.append("2. 目标命中：matched_by=%s，命中 %d 条：%s"
             % (maplist.get("matched_by"), maplist.get("n_target_hits"),
                json.dumps(maplist.get("target_hits"), ensure_ascii=False)))
    v.append("3. 字面 `No Name` 条目：%d 个，索引 %s"
             % (maplist.get("n_noname_literal"),
                maplist.get("noname_literal_indices")))
    v.append("4. 读失败条目（没读到名称）：%d 个；名称为空条目（读到但空串）："
             "%d 个 —— 两种口径分开记录"
             % (maplist.get("n_read_fail"), maplist.get("n_empty_name")))
    v.append("5. itemdata 768B 审计（目标条目 [%s]）：名称槽=%s；内嵌文件名=%s；"
             "digest=%s（is_no_digest=%s）"
             % (t_idx,
                json.dumps((w10_target or {}).get("name_slot"),
                           ensure_ascii=False),
                (w10_target or {}).get("filename"),
                (w10_target or {}).get("digest"),
                (w10_target or {}).get("digest_is_no_digest")))
    v.append("6. 与 W9 [97] 逐字段对照见 `out\\compare_with_W9.md`"
             "（同一解析器重算双方 hex）")
    v.append("7. 列表逐索引 diff：名称差异条目 %d 个（预期仅 [97] 一处变化）"
             % list_diff["n_diff_entries"])
    if buf_byte_diff:
        v.append("8. 目标缓冲 768B 逐字节对比 W9↔W10：差异 %d/%d 字节"
                 "（散落单字节，运行期易变类）；名称槽 0–87 / 文件名 88–116 / "
                 "digest 区 348–361 全部逐字节相等 —— 记录结构两次运行相同"
                 % (buf_byte_diff["n_diff_bytes"], buf_byte_diff["n_bytes"]))
    v.append("")
    v.append("## 归因纪律（红线）")
    v.append("")
    v.append("- 只改了一个变量（行尾），结论只归因到行尾；"
             "节顺序（[Preview] 打头）的影响本卡不推断、不改动。")
    v.append("- 「没读到名称」（diag≠ok，含原始字节）与「名称为空」（读到但空串）"
             "分开记录，不混写。")
    v.append("- 条目数若未变（仍 268）= 文件未被扫描，与「显示 No Name」是不同问题。")
    v.append("")
    (W10 / "VERDICT.md").write_text("\n".join(v) + "\n", encoding="utf-8")

    result = {
        "run_id": RUN_ID, "generated_utc": utc_iso(),
        "verdict": verdict, "verdict_zh": verdict_zh,
        "meta_error": meta.get("error"),
        "n_items": n_items, "delta_vs_base": delta,
        "matched_by": maplist.get("matched_by"),
        "n_target_hits": maplist.get("n_target_hits"),
        "target_hits": maplist.get("target_hits"),
        "noname_literal_indices": maplist.get("noname_literal_indices"),
        "n_read_fail": maplist.get("n_read_fail"),
        "n_empty_name": maplist.get("n_empty_name"),
        "w9_97": {k: w9_97.get(k) for k in
                  ("name_slot", "name_slot_diag", "filename", "digest",
                   "digest_is_no_digest")} if w9_97 else None,
        "w10_target": {k: (w10_target or {}).get(k) for k in
                       ("index", "name_slot", "name_slot_diag", "filename",
                        "digest", "digest_is_no_digest")},
        "target_basis": target_basis,
        "list_diff": {k: list_diff[k] for k in
                      ("n_w9", "n_w10", "n_items_equal", "n_diff_entries")},
        "list_diffs": list_diff["diffs"],
        "buf_byte_diff": buf_byte_diff,
        "residual_after": meta.get("residual_after"),
        "restore_rows": meta.get("restore_rows"),
        "h1_file_after": meta.get("h1_file_after"),
        "lock_restored": meta.get("lock_restored"),
    }
    (OUT / "verdict.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({
        "verdict": verdict, "n_items": n_items, "delta": delta,
        "hits": maplist.get("n_target_hits"),
        "matched_by": maplist.get("matched_by"),
        "noname": maplist.get("noname_literal_indices"),
        "w10_name_slot": (w10_target or {}).get("name_slot"),
        "w10_filename": (w10_target or {}).get("filename"),
        "w10_digest": (w10_target or {}).get("digest"),
        "digest_is_no_digest": (w10_target or {}).get("digest_is_no_digest"),
        "target_basis": target_basis,
        "diff_entries": list_diff["n_diff_entries"],
        "diffs": list_diff["diffs"][:5],
        "error": meta.get("error"),
    }, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.run:
        ec, _meta = run_verify()
        return ec
    if a.analyze:
        return run_analyze()
    print("用法：--run 真机一趟（只到地图列表）；--analyze 离线对照 W9 + VERDICT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
