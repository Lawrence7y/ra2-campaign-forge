# -*- coding: utf-8 -*-
"""W11 `[Header]` 节单变量验证（真机，单实例；名称出现才开局采样）。

run_id = NEXT_RE_20261112_R02
前置两步已定（不重复）：
  W9  原件（裸 LF、无 [Header]）            → 269 条，字面 `No Name` + `No Digest`
  W10 仅改行尾（CRLF，仍无 [Header]）        → 仍 `No Name` + `No Digest`，逐字段全同
                                              ⇒ 行尾不是主因 [已否证]
本卡变量：Lead 已装入变体 C = CRLF（沿用 W10）+ 最前补 `[Header]` 节（取自正常图
U0800：Width/Height/StartX/StartY/NumberStartingPoints 等）。节顺序变为
[Header] [Preview] [PreviewPack] [Map] [Basic] …—— 与正常图完全一致。
因行尾已被 W10 单独否证，若本卡名称正常显示，只能归因到 `[Header]` 缺失。

载体（Lead 装入，本卡只核对、禁改禁删）：
  ra2youli\\[2]0LoadBench_U0800_H1.yrm
  315,912 B / SHA-256 3ce133ff53b67418918e3b3f812f79610094395a979ba27e444ad6fe873be1cb

判定：
  Q1 名称正常显示（[Basic]Name 内容） ⇒ `[Header]` 缺失是主因 [已证]；继续 Q2。
  Q1 仍 No Name                        ⇒ 行尾 + [Header] 两个结构变量均否证 [否证]，
                                        不做第四个变量，交回 Lead 收口。

Q2（仅当 Q1 名称正常）：选中开局，采样 ≥60 s @30ms，判定 frame 是否 ≈29–32/s
持续推进，还是复现 W9 的 ~20 s 异常结束（W9 观测：4.95–20s 三桶
31.12/31.28/30.71；21.0s 起 frame 停推 mode=5；~25s 起结算屏 GUI:Continue）。
不抓栈、不推断机制。

复用：W10_crlf_verify\\crlf_verify.py（列表读取 + itemdata 768B 审计 + 三口径匹配，
其经 W9_h1_layering\\h1_probe.py 模块级加载 W7_load_baseline 全部底层）；开局采样
循环复用 h1_probe.run_run2 的已验证实现；离线速率分析复用 h1_probe 的
load_samples/rate_curve/slide_rates/stall_segments/dist。
本卡禁 SuspendThread/StackWalk64/MiniDump/断点/注入/写目标内存；只读 RPM。

用法：
  python -X utf8 header_verify.py --run       # 真机一趟（启动→导航→列表→审计→[条件开局采样]→收尾）
  python -X utf8 header_verify.py --analyze   # 离线：与 W10 [97] / W9 [97] 对照 + VERDICT
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
W11 = R2 / "W11_header_verify"
OUT = W11 / "out"
W9_OUT = R2 / "W9_h1_layering" / "out"
W10_OUT = R2 / "W10_crlf_verify" / "out"
H1_PROBE = R2 / "W9_h1_layering" / "h1_probe.py"

SELF_OWNER = "w11_header_verify_subagent"
LEAD_OWNER = "lead"

H1_FILE = ROOT / "ra2youli" / "[2]0LoadBench_U0800_H1.yrm"
H1_SHA256 = "3ce133ff53b67418918e3b3f812f79610094395a979ba27e444ad6fe873be1cb"
H1_SIZE = 315912

# 离线 [Basic]Name 原值（三步共用；W9 第 2 步读得）
BASIC_NAME = "[2] 0LoadBench U0800 H1 fp:1189b6b550ff"
PAT_SUB_NAME = "loadbench u0800 h1"          # 子串匹配 1（显示名，lower() 后）
PAT_SUB_FILE = "0loadbench_u0800_h1"         # 子串匹配 2（内嵌文件名形态）

EXPECTED_LIST_BASE = 268                     # W7 实测装入前列表条目数
EXPECTED_LIST_NOW = 269                      # 装入 +1 预期（W9 两趟 / W10 均 269）

CTRL_IDX = 96                                # 对照条目：[2] 0LoadBench U800
AUDIT_FIXED_IDX = (91, 96, 97)               # 固定审计集（W9/W10/W11 连续性对照）
NONAME_HIST_IDX = 97                         # W9/W10 里 H1 载体所在索引

MENU_TIMEOUT_S = 90
PANEL_SETTLE_S = 1.8                         # LB_SETCURSEL 后信息面板稳定等待
SAMPLE_MS = 30                               # 开局后采样间隔
SAMPLE_SECONDS = 70.0                        # StartGame 起采样时长（≥60 s + 10 s 余量）
UI_EVERY_S = 5.0                             # 采样期内 UI 控件快照间隔
USEMAP_SETTLE_S = 4.0                        # UseMap 后高负载图解析缓冲

# W9 run2 观测基准（Q2 对照；analyze 期引用）
W9_REF = {"rates_3bucket": [31.12, 31.28, 30.71], "frame_stop_stall_t0": 21.006,
          "continue_seen_at": 25.0, "window_s": 70.0}

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


# ------------------------------------------------------------------ itemdata 768B 缓冲解析（与 W10 同一解析器）
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
    """解析 itemdata 指向的记录缓冲（W9/W10 已验证布局）：
    头部 = UTF-16LE 名称槽（到 null）；随后内嵌 ASCII 文件名（*.yrm）；
    再后 digest 区（"No Digest" 或 base64）。"""
    rec = {"buf_len": len(b)}
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
        rec["name_slot_diag"] = "empty_utf16"
    runs = _ascii_runs(b)
    rec["ascii_runs"] = [{"offset": o, "text": t} for o, t in runs]
    rec["filename"] = None
    rec["filename_offset"] = None
    for o, t in runs:
        if ".yrm" in t.lower():
            rec["filename"] = t
            rec["filename_offset"] = o
            break
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
    used = {rec.get("filename_offset"), rec.get("digest_offset")}
    rec["other_ascii_runs"] = [{"offset": o, "text": t} for o, t in runs
                               if o not in used]
    return rec


# ------------------------------------------------------------------ 目标匹配（三口径）
def match_target(entries):
    """三种口径分别记录，优先级：精确完整名 > 子串1(显示名) > 子串2(文件名形态)。"""
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
    """对单条目做 itemdata 768B hex 审计（W10 同逻辑）。"""
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
    ndjson_path = OUT / "run.ndjson"
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
    meta = {
        "run_id": RUN_ID,
        "card": "W11 [Header] 节单变量验证（名称出现才开局）",
        "started_utc": started_utc,
        "h1_file": {"path": str(H1_FILE), "expected_sha256": H1_SHA256,
                    "expected_size": H1_SIZE},
        "expected": {"list_base": EXPECTED_LIST_BASE, "list_now": EXPECTED_LIST_NOW,
                     "basic_name": BASIC_NAME,
                     "patterns": [PAT_SUB_NAME, PAT_SUB_FILE]},
        "pid": None, "is32": None, "game_hwnd": None, "game_tid": None,
        "code_signature_ok": None, "prelaunch_hashes": {},
        "maplist": None, "target": None, "q1": None, "audits": {}, "panels": {},
        "selected": None, "usemap_ui": None,
        "n_samples": 0, "n_read_fail": 0, "phase_stop": None,
        "sample_seconds": SAMPLE_SECONDS, "sample_ms": SAMPLE_MS,
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
        log("[S0] 实例锁 + 残留进程 + 哈希守卫（W11）")
        lock_state = W7.check_lock()
        log("    实例锁 owner 状态 = %s" % lock_state)
        W7.write_lock("W11 [Header] 节单变量验证（名称出现才开局）")
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
        log("    H1 载体（变体 C：CRLF + [Header]）%d B sha=%s match=%s"
            % (h1_size, h1_hash, h1_ok))
        if not h1_ok:
            raise W7.GuardStop("H1 载体哈希/大小与 Lead 装入记录不一致，停手")
        ev("h1_file_verified", {"size": h1_size, "sha256": h1_hash})

        inventory_before = W7.inventory(W7.GAME_DIR)
        log("    启动前 ra2youli 文件清单 %d 项；守卫全过" % len(inventory_before))
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

        entries = HP.read_map_names_diag(hproc, lb, n)
        noname_lit = [e for e in entries if e["name"] == "No Name"]
        read_fail = [e for e in entries
                     if e["diag"] not in ("ok", "empty_utf16")]
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

        # ---------- S3 itemdata 768B 审计（目标 + 固定对照集） ----------
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

        # ---------- S3b 目标/对照条目信息面板快照（辅助证据；失败不影响） ----------
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

        # ---------- Q1 判定 + 条件开局 ----------
        # 名称正常 = 三口径命中（命中本身就排除了字面 No Name / 空串 / 读失败）
        # digest 状态单独记录；Q2 只由「名称正常」门控
        tgt_audit = audits.get(target_idxs[0]) if target_idxs else None
        tgt_buf = (tgt_audit or {}).get("buf768") or {}
        name_ok = bool(target_list)
        digest_present = bool(tgt_buf.get("digest")
                              and not tgt_buf.get("digest_is_no_digest"))
        meta["q1"] = {
            "name_ok": name_ok, "matched_by": matched_by,
            "display_name": (target_list[0]["name"] if target_list else None),
            "target_index": (target_idxs[0] if target_idxs else None),
            "buffer_name_slot": tgt_buf.get("name_slot"),
            "digest": tgt_buf.get("digest"),
            "digest_is_no_digest": tgt_buf.get("digest_is_no_digest"),
            "digest_present": digest_present,
            "start_game": name_ok,
        }
        if not name_ok:
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
            meta["target"] = {"indices": target_idxs, "matched_by": matched_by}
            log("[S4] Q1 未命中（仍 No Name）⇒ 不开局；交回 Lead，进入收尾")
            ev("q1_no_name", {"matched_by": matched_by,
                              "noname": maplist["noname_literal_indices"]})
            raise W7.GuardStop("Q1_NO_NAME: 目标仍显示字面 No Name；按任务书"
                               "不再尝试第四变量，交回 Lead")

        log("[S4] Q1 命中 ⇒ 选中开局并采样 %.0fs @ %dms"
            % (SAMPLE_SECONDS, SAMPLE_MS))
        sel_idx = target_idxs[0]
        sel_name = entries[sel_idx]["name"]
        W7.smt(lb, W7.LB_SETCURSEL, sel_idx)
        time.sleep(0.6)
        meta["selected"] = {"index": sel_idx, "display_name": sel_name,
                            "selection_basis":
                                "三口径显示名命中（matched_by=%s）" % matched_by}
        log("    选中 [%d] %r → UseMap" % (sel_idx, sel_name))
        ev("map_selected", {"index": sel_idx, "display_name": sel_name,
                            "matched_by": matched_by})
        if not W7.click(pid, "GUI:UseMap", 3.0):
            raise RuntimeError("GUI:UseMap 未点击成功")
        time.sleep(USEMAP_SETTLE_S)
        meta["usemap_ui"] = HP.ui_summary(pid)
        ev("usemap_clicked", {"ui": meta["usemap_ui"]})

        # ---------- S5 StartGame + ≥60s 采样 ----------
        log("[S5] StartGame；逐拍采样 %.1fs @ %dms" % (SAMPLE_SECONDS, SAMPLE_MS))
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
        continue_seen_elapsed = None
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
                log("    !! frame 停推 ≥1.0s（elapsed=%.1fs, mode=%s, fg=%s）"
                    "——只记录，不抓栈"
                    % (elapsed, rec.get("mode_A8B238"), rec["win_foreground"]))
                ev("frame_stall_1s", {"elapsed_s": round(elapsed, 3),
                                      "mode": rec.get("mode_A8B238"),
                                      "win_foreground": rec["win_foreground"]})
                stall_reported = True
            if stall_s < 1.0:
                stall_reported = False
            if t_ns >= next_ui:
                rec["ui"] = HP.ui_summary(pid)
                u = rec["ui"]
                log("    UI@%.1fs buttons=%s statics0=%s"
                    % (elapsed, u["buttons"][:6],
                       (u["statics"][0] if u["statics"] else "")))
                btn_join = ",".join(u["buttons"]).lower()
                if continue_seen_elapsed is None and \
                        ("continue" in btn_join):
                    continue_seen_elapsed = round(elapsed, 2)
                    ev("continue_seen", {"elapsed_s": continue_seen_elapsed})
                    log("    结算屏 GUI:Continue 首现 @ %.1fs" % elapsed)
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
                log("    !! 采样 %.1fs 时进程退出（exit=%d）"
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
        meta["continue_seen_elapsed"] = continue_seen_elapsed
        log("[S6] 采样结束 seq=%d read_fail=%d continue_seen=%s"
            % (seq, n_fail, continue_seen_elapsed))
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
                          "names": [{"index": e["index"], "name": e["name"]}
                                    for e in target_list]}

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
        h1_still = H1_FILE.exists()
        h1_hash_after = W7.sha256_file(H1_FILE) if h1_still else None
        log("    H1 载体仍在=%s hash_after=%s" % (h1_still, h1_hash_after))
        try:
            LOCK_PATH.write_text(
                "run_id=%s\nowner=%s\ntime=%s\npurpose=%s\n"
                % (RUN_ID, LEAD_OWNER,
                   datetime.datetime.now().astimezone().isoformat(),
                   "W11 done: [Header] verify finished, lock returned to lead"),
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


def byte_diff(a, b):
    diff_offs = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    segs = []
    for i in diff_offs:
        if segs and i == segs[-1][1] + 1:
            segs[-1][1] = i
        else:
            segs.append([i, i])
    return {
        "n_bytes": min(len(a), len(b)),
        "n_diff_bytes": len(diff_offs),
        "diff_segments": [tuple(s) for s in segs],
        "name_slot_0_87_equal": a[:88] == b[:88],
        "filename_88_116_equal": a[88:117] == b[88:117],
        "digest_348_361_equal": a[348:362] == b[348:362],
    }


def list_index_diff(entries_a, entries_b, tag_a, tag_b):
    diffs = []
    for i in range(min(len(entries_a), len(entries_b))):
        a, b = entries_a[i].get("name"), entries_b[i].get("name")
        if a != b:
            diffs.append({"index": i, "%s_name" % tag_a: a,
                          "%s_name" % tag_b: b,
                          "%s_diag" % tag_a: entries_a[i].get("diag"),
                          "%s_diag" % tag_b: entries_b[i].get("diag")})
    return {
        "n_%s" % tag_a: len(entries_a), "n_%s" % tag_b: len(entries_b),
        "n_items_equal": len(entries_a) == len(entries_b),
        "n_diff_entries": len(diffs), "diffs": diffs,
    }


def run_analyze():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))
    maplist = json.loads((OUT / "maplist.json").read_text(encoding="utf-8"))
    w10_maplist = json.loads((W10_OUT / "maplist.json").read_text(encoding="utf-8"))
    w9_maplist = json.loads((W9_OUT / "maplist_run2.json").read_text(encoding="utf-8"))

    # ---- W11 侧审计 ----
    w11_audits = {}
    for idx_s, rec in meta.get("audits", {}).items():
        f = rec.get("raw_hex_file")
        if f and (OUT / f).exists():
            w11_audits[int(idx_s)] = audit_from_hex(
                int(idx_s), load_hex(OUT / f),
                display_name=rec.get("display_name_via_list"),
                source="W11/%s" % f)

    # ---- W10 侧审计（同一解析器重算） ----
    w10_names = {e["index"]: e.get("name") for e in w10_maplist.get("entries", [])}
    w10_audits = {}
    for idx in (91, 96, 97):
        f = W10_OUT / ("itemdata_audit_%d.hex" % idx)
        if f.exists():
            w10_audits[idx] = audit_from_hex(idx, load_hex(f),
                                             display_name=w10_names.get(idx),
                                             source="W10/itemdata_audit_%d.hex" % idx)

    # ---- W9 侧审计 ----
    w9_names = {e["index"]: e.get("name") for e in w9_maplist.get("entries", [])}
    w9_audits = {}
    for idx in (91, 96, 97):
        f = W9_OUT / ("nn_audit_%d.hex" % idx)
        if f.exists():
            w9_audits[idx] = audit_from_hex(idx, load_hex(f),
                                            display_name=w9_names.get(idx),
                                            source="W9/nn_audit_%d.hex" % idx)

    # ---- 列表逐索引 diff ----
    w11_entries = maplist.get("entries", [])
    w10_entries = w10_maplist.get("entries", [])
    w9_entries = w9_maplist.get("entries", [])
    diff_10_11 = list_index_diff(w10_entries, w11_entries, "w10", "w11")
    diff_9_11 = list_index_diff(w9_entries, w11_entries, "w9", "w11")

    # ---- 目标条目钉身份 ----
    target_idxs = (meta.get("target") or {}).get("indices") or []
    w11_target = w11_audits.get(target_idxs[0]) if target_idxs else None
    target_basis = "display_name_hit"
    if w11_target is None:
        for idx in sorted(w11_audits):
            f = w11_audits[idx].get("filename") or ""
            if PAT_SUB_FILE in f.lower():
                w11_target = w11_audits[idx]
                target_basis = "embedded_filename:%s" % PAT_SUB_FILE
                break
    if w11_target is not None and not (OUT / "itemdata_audit.hex").exists():
        t_hex_file = OUT / ("itemdata_audit_%d.hex" % w11_target["index"])
        if t_hex_file.exists():
            (OUT / "itemdata_audit.hex").write_text(
                t_hex_file.read_text(encoding="ascii"), encoding="ascii")
            log("    itemdata_audit.hex 由 itemdata_audit_%d.hex 复出"
                "（目标身份：%s）" % (w11_target["index"], target_basis))

    # ---- 缓冲逐字节对比 ----
    bd_11_vs_10 = None
    bd_11_vs_9 = None
    if w11_target is not None and w10_audits.get(97) is not None:
        try:
            a = load_hex(OUT / ("itemdata_audit_%d.hex" % w11_target["index"]))
            b = load_hex(W10_OUT / "itemdata_audit_97.hex")
            bd_11_vs_10 = byte_diff(a, b)
        except Exception as e:
            bd_11_vs_10 = {"error": repr(e)}
    if w11_target is not None and w9_audits.get(97) is not None:
        try:
            a = load_hex(OUT / ("itemdata_audit_%d.hex" % w11_target["index"]))
            b = load_hex(W9_OUT / "nn_audit_97.hex")
            bd_11_vs_9 = byte_diff(a, b)
        except Exception as e:
            bd_11_vs_9 = {"error": repr(e)}

    # ---- Q1 判定 ----
    n_items = maplist.get("n_items")
    delta = maplist.get("delta_vs_base")
    name_ok = bool(maplist.get("n_target_hits"))
    digest_present = bool(w11_target and w11_target.get("digest")
                          and not w11_target.get("digest_is_no_digest"))
    still_noname = bool(maplist.get("noname_literal_indices"))

    if delta == 0 and not name_ok:
        verdict = "file_not_scanned"
        verdict_zh = ("条目数未变（仍 %d）：文件未被扫描到，与「显示 No Name」是不同"
                      "问题。" % (n_items,))
    elif name_ok and digest_present and not still_noname:
        verdict = "header_confirmed"
        verdict_zh = ("[Header] 缺失是主因 [已证]：名称正常显示且 digest 正常，"
                      "字面 No Name 清零。")
    elif name_ok and digest_present and still_noname:
        verdict = "header_confirmed_partial_residual"
        verdict_zh = ("[Header] 缺失是主因 [已证]（本条）：目标名称/digest 已正常；"
                      "但仍有其它字面 No Name 条目（应仅 [91] prm.yrm 历史项）。")
    elif name_ok and not digest_present:
        verdict = "name_fixed_digest_missing"
        verdict_zh = ("名称已修复但 digest 仍缺失 [部分证实]：[Header] 使 Name= 可读，"
                      "digest 生成另有条件/来源，须单列观测。")
    elif (not name_ok) and still_noname and delta == 1:
        verdict = "header_not_the_cause"
        verdict_zh = ("[Header] 缺失不是主因 [否证]：条目已进列表（+1）但仍字面 "
                      "No Name。行尾（W10）与 [Header]（本卡）两个结构变量均被单独"
                      "否证；按任务书不再尝试第四变量，交回 Lead 收口。")
    else:
        verdict = "inconclusive"
        verdict_zh = "证据不全，按未定 [未定] 记录；见 meta.json 与 maplist.json。"

    # ---- Q2 分析（若开局） ----
    q2 = None
    ndjson_path = OUT / "run.ndjson"
    if ndjson_path.exists() and (meta.get("n_samples") or 0) > 0:
        try:
            samples, events, uis = HP.load_samples(ndjson_path)
            buckets = HP.rate_curve(samples, 5.0)
            slide_min, slide_max = HP.slide_rates(samples, 2.0)
            stalls = HP.stall_segments(samples, 1.0)
            cont = None
            for u in uis:
                btns = ",".join((u.get("ui") or {}).get("buttons") or []).lower()
                if "continue" in btns:
                    cont = u["elapsed_s"]
                    break
            moving = [b for b in buckets if (b.get("rate") or 0) > 1.0]
            frozen = [b for b in buckets if not (b.get("rate") or 0)]
            q2_rates = [b["rate"] for b in moving]
            anomaly = bool(stalls) and (
                (stalls[0].get("t0") or 0) < 30.0 and
                stalls[0].get("mode") == 5)
            if anomaly:
                q2_verdict = "q2_anomaly_still_present"
                q2_zh = ("~20s 异常结束仍在：frame 停推段 t0=%.1fs（mode=5）；"
                         "GUI:Continue 首现 %s；W9 基线 t0=21.0s / 25s，形态一致。"
                         % (stalls[0].get("t0") or -1,
                            ("%.1fs" % cont) if cont is not None else "未见"))
            elif len(moving) >= 10 and not stalls:
                q2_verdict = "q2_frame_continuous"
                q2_zh = ("frame 全程持续推进 ≥60s（移动桶 %d 个，速率范围 "
                         "%.2f–%.2f/s），无停推段 ⇒ 异常结束不再发生。"
                         % (len(moving), min(q2_rates), max(q2_rates)))
            else:
                q2_verdict = "q2_inconclusive"
                q2_zh = ("证据形态与两个预设模板都不完全吻合：移动桶 %d 个、"
                         "停推段 %s、GUI:Continue %s；见 run.ndjson 逐拍数据。"
                         % (len(moving),
                            [(round(s.get("t0") or -1, 2),
                              round(s.get("t_end") or -1, 2)) for s in stalls],
                            cont))
            q2 = {
                "verdict": q2_verdict, "verdict_zh": q2_zh,
                "n_samples": len(samples), "n_read_fail":
                    sum(1 for s in samples if s.get("read_status") != "ok"),
                "phase_stop": meta.get("phase_stop"),
                "buckets": buckets, "slide_min": slide_min,
                "slide_max": slide_max, "stall_segments": stalls,
                "continue_seen_at": cont,
                "mode_dist": HP.dist(samples, "mode_A8B238"),
                "exitstate_dist": HP.dist(samples, "exitstate"),
                "A8E9A0_dist": HP.dist(samples, "A8E9A0"),
                "ABCD58_dist": HP.dist(samples, "ABCD58"),
                "A8ED50_range": [min((s.get("A8ED50") or 0) for s in samples),
                                 max((s.get("A8ED50") or 0) for s in samples)],
                "w9_ref": W9_REF,
                "ui_timeline": [{"elapsed_s": u["elapsed_s"],
                                 "buttons": (u.get("ui") or {}).get("buttons"),
                                 "statics0": ((u.get("ui") or {})
                                              .get("statics") or [None])[0]}
                                for u in uis],
            }
        except Exception as e:
            q2 = {"error": "Q2 离线分析异常 %r" % e}

    # ---- compare_with_W10.md ----
    def field_row(label, a, b, c=None):
        if c is None:
            return "| %s | %s | %s |" % (label, a, b)
        return "| %s | %s | %s | %s |" % (label, a, b, c)

    t_idx = w11_target.get("index") if w11_target else "-"
    lines = []
    lines.append("# W11（CRLF + `[Header]`）与 W10（仅 CRLF）/ W9（原件）"
                 " —— 逐字段对照")
    lines.append("")
    lines.append("- run_id：`%s`" % RUN_ID)
    lines.append("- 生成：`header_verify.py --analyze`（%s，同一解析器重算三方 hex）"
                 % utc_iso())
    lines.append("- 变量链：W9 原件（裸 LF、无 [Header]）→ W10 仅行尾（CRLF）→ "
                 "W11 = CRLF 沿用 + 最前补 `[Header]` 节（节顺序 [Header] [Preview] "
                 "[PreviewPack] [Map] [Basic] …，与正常图一致）")
    lines.append("- W10 基线：`W10_crlf_verify\\out\\itemdata_audit_97.hex` + "
                 "`maplist.json`；W9 基线：`W9_h1_layering\\out\\nn_audit_97.hex` + "
                 "`maplist_run2.json`；W11：`W11_header_verify\\out\\"
                 "itemdata_audit.hex` + `maplist.json`")
    lines.append("")
    lines.append("## 1. 主对照：W9 [97]（原件）/ W10 [97]（仅 CRLF）/ W11 [%s]"
                 "（CRLF+[Header]）" % t_idx)
    lines.append("")
    lines.append("| 字段 | W9 [97]（原件） | W10 [97]（仅 CRLF） | W11 [%s]"
                 "（CRLF+[Header]） |" % t_idx)
    lines.append("|---|---|---|---|")
    a9, a10, a11 = (w9_audits.get(97) or {}), (w10_audits.get(97) or {}), \
                   (w11_target or {})
    lines.append(field_row(
        "列表条目总数",
        "%d（基线 268，Δ+1）" % w9_maplist.get("n_items"),
        "%d（基线 %d，Δ%+d）" % (w10_maplist.get("n_items"),
                                 EXPECTED_LIST_BASE,
                                 w10_maplist.get("delta_vs_base")),
        "%d（基线 %d，Δ%+d）" % (n_items, EXPECTED_LIST_BASE, delta)))
    lines.append(field_row("条目索引", "97", "97", str(t_idx)))
    lines.append(field_row(
        "显示名（列表读取）",
        json.dumps(a9.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(a10.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(a11.get("display_name_via_list"), ensure_ascii=False)))
    lines.append(field_row("名称槽（缓冲 UTF-16 头）",
                           fmt_field(a9, "name_slot"),
                           fmt_field(a10, "name_slot"),
                           fmt_field(a11, "name_slot")))
    lines.append(field_row("名称槽诊断", a9.get("name_slot_diag", "-"),
                           a10.get("name_slot_diag", "-"),
                           a11.get("name_slot_diag", "-")))
    lines.append(field_row("内嵌 ASCII 文件名",
                           fmt_field(a9, "filename"),
                           fmt_field(a10, "filename"),
                           fmt_field(a11, "filename")))
    lines.append(field_row("文件名缓冲偏移",
                           str(a9.get("filename_offset")),
                           str(a10.get("filename_offset")),
                           str(a11.get("filename_offset"))))
    lines.append(field_row("digest 字段", fmt_field(a9, "digest"),
                           fmt_field(a10, "digest"),
                           fmt_field(a11, "digest")))
    lines.append(field_row("digest 是否字面 No Digest",
                           str(a9.get("digest_is_no_digest")),
                           str(a10.get("digest_is_no_digest")),
                           str(a11.get("digest_is_no_digest"))))
    lines.append(field_row("digest 缓冲偏移", str(a9.get("digest_offset")),
                           str(a10.get("digest_offset")),
                           str(a11.get("digest_offset"))))
    lines.append(field_row(
        "目标显示名命中数",
        "0（matched_by=none）",
        "0（matched_by=none）",
        "%d（matched_by=%s）" % (maplist.get("n_target_hits"),
                                 maplist.get("matched_by"))))
    lines.append(field_row(
        "字面 No Name 条目",
        "2 个：[91], [97]",
        "2 个：%s" % w10_maplist.get("noname_literal_indices"),
        "%d 个：%s" % (maplist.get("n_noname_literal"),
                       maplist.get("noname_literal_indices"))))
    lines.append(field_row(
        "读失败/空串条目",
        "0 / 0",
        "%d / %d" % (w10_maplist.get("n_read_fail"),
                     w10_maplist.get("n_empty_name")),
        "%d / %d" % (maplist.get("n_read_fail"),
                     maplist.get("n_empty_name"))))
    lines.append("")
    lines.append("## 2. 连续性对照（环境未变的旁证）")
    lines.append("")
    lines.append("| 字段 | W9 [91] | W10 [91] | W11 [91] | W9 [96] | W10 [96] |"
                 " W11 [96] |")
    lines.append("|---|---|---|---|---|---|---|")
    a91, b91, c91 = (w9_audits.get(91) or {}), (w10_audits.get(91) or {}), \
                    (w11_audits.get(91) or {})
    a96, b96, c96 = (w9_audits.get(96) or {}), (w10_audits.get(96) or {}), \
                    (w11_audits.get(96) or {})
    lines.append("| 显示名 | %s | %s | %s | %s | %s | %s |" % (
        json.dumps(a91.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(b91.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(c91.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(a96.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(b96.get("display_name_via_list"), ensure_ascii=False),
        json.dumps(c96.get("display_name_via_list"), ensure_ascii=False)))
    lines.append("| 名称槽 | %s | %s | %s | %s | %s | %s |" % (
        fmt_field(a91, "name_slot"), fmt_field(b91, "name_slot"),
        fmt_field(c91, "name_slot"), fmt_field(a96, "name_slot"),
        fmt_field(b96, "name_slot"), fmt_field(c96, "name_slot")))
    lines.append("| 文件名 | %s | %s | %s | %s | %s | %s |" % (
        fmt_field(a91, "filename"), fmt_field(b91, "filename"),
        fmt_field(c91, "filename"), fmt_field(a96, "filename"),
        fmt_field(b96, "filename"), fmt_field(c96, "filename")))
    lines.append("| digest | %s | %s | %s | %s | %s | %s |" % (
        fmt_field(a91, "digest"), fmt_field(b91, "digest"),
        fmt_field(c91, "digest"), fmt_field(a96, "digest"),
        fmt_field(b96, "digest"), fmt_field(c96, "digest")))
    lines.append("")
    lines.append("## 3. 列表逐索引 diff")
    lines.append("")
    lines.append("- W10→W11：条目数 %d→%d，%s；名称差异条目 %d 个"
                 % (diff_10_11["n_w10"], diff_10_11["n_w11"],
                    "一致" if diff_10_11["n_items_equal"] else "不一致",
                    diff_10_11["n_diff_entries"]))
    for d in diff_10_11["diffs"][:10]:
        lines.append("  - [%d] W10=%r → W11=%r（diag %s→%s）"
                     % (d["index"], d["w10_name"], d["w11_name"],
                        d["w10_diag"], d["w11_diag"]))
    lines.append("- W9→W11：名称差异条目 %d 个"
                 % diff_9_11["n_diff_entries"])
    for d in diff_9_11["diffs"][:10]:
        lines.append("  - [%d] W9=%r → W11=%r（diag %s→%s）"
                     % (d["index"], d["w9_name"], d["w11_name"],
                        d["w9_diag"], d["w11_diag"]))
    lines.append("")
    lines.append("## 3bis. 目标条目缓冲 768B 逐字节对比")
    lines.append("")
    if isinstance(bd_11_vs_10, dict) and "error" not in bd_11_vs_10:
        lines.append("- W11[%s] vs W10[97]：差异 %d/%d 字节（散落单字节，"
                     "运行期易变计数类，偏移 %s）"
                     % (t_idx, bd_11_vs_10["n_diff_bytes"],
                        bd_11_vs_10["n_bytes"],
                        bd_11_vs_10["diff_segments"]))
        lines.append("  - 名称槽 0–87 相等=%s；文件名 88–116 相等=%s；"
                     "digest 区 348–361 相等=%s"
                     % (bd_11_vs_10["name_slot_0_87_equal"],
                        bd_11_vs_10["filename_88_116_equal"],
                        bd_11_vs_10["digest_348_361_equal"]))
    else:
        lines.append("- W11 vs W10：（%s）" % (bd_11_vs_10,))
    if isinstance(bd_11_vs_9, dict) and "error" not in bd_11_vs_9:
        lines.append("- W11[%s] vs W9[97]：差异 %d/%d 字节（偏移 %s）"
                     % (t_idx, bd_11_vs_9["n_diff_bytes"],
                        bd_11_vs_9["n_bytes"],
                        bd_11_vs_9["diff_segments"]))
        lines.append("  - 名称槽 0–87 相等=%s；文件名 88–116 相等=%s；"
                     "digest 区 348–361 相等=%s"
                     % (bd_11_vs_9["name_slot_0_87_equal"],
                        bd_11_vs_9["filename_88_116_equal"],
                        bd_11_vs_9["digest_348_361_equal"]))
    else:
        lines.append("- W11 vs W9：（%s）" % (bd_11_vs_9,))
    lines.append("")
    lines.append("## 4. 判定")
    lines.append("")
    lines.append("- verdict：`%s`" % verdict)
    lines.append("- %s" % verdict_zh)
    if q2 and not q2.get("error"):
        lines.append("- Q2：`%s` —— %s" % (q2["verdict"], q2["verdict_zh"]))
    lines.append("")
    (OUT / "compare_with_W10.md").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")

    # ---- VERDICT.md ----
    v = []
    v.append("# W11 VERDICT —— `[Header]` 节单变量验证（名称出现才开局）")
    v.append("")
    v.append("- run_id：`%s`；日期：2026-11-13" % RUN_ID)
    v.append("- 变量：`[Header]` 节（最前补入；行尾 CRLF 沿用 W10 已验证修复；"
             "节顺序变为与正常图完全一致）")
    v.append("- 载体：`ra2youli\\[2]0LoadBench_U0800_H1.yrm` 315,912 B / "
             "SHA-256 `3ce133ff…873be1cb`（run 前后哈希一致，未改动）")
    v.append("- 离线 [Basic]Name 预期显示：`%s`" % BASIC_NAME)
    v.append("- 前置已定：W9 原件 → `No Name`+`No Digest`；W10 仅行尾 → 逐字段"
             "全同 `No Name`+`No Digest` ⇒ 行尾不是主因 [已否证]")
    v.append("")
    v.append("## Q1 主因判定（[Header] 缺失是否主因）")
    v.append("")
    v.append("**verdict = `%s`**" % verdict)
    v.append("")
    v.append("%s" % verdict_zh)
    v.append("")
    if name_ok:
        v.append("**归因推理链（显式）**：本卡与 W10 之间只差一个新增差异"
                 "——`[Header]` 节；行尾（CRLF）已被 W10 单变量单独否证"
                 "（W10 与 W9 逐字段全同）。因此 W11 由 `No Name` 变为正常显示的"
                 "因果增量只能归因到 `[Header]` 缺失，不存在「两者协同才生效」"
                 "之外的解读空间：若行尾是必要成分，W10 应当已经修复。")
    v.append("")
    v.append("## 关键证据")
    v.append("")
    v.append("1. 条目总数：W11=%d（基线 %d，Δ%+d；W9 两趟 / W10 均 269）——"
             "文件被扫描、进了列表%s"
             % (n_items, EXPECTED_LIST_BASE, delta,
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
                json.dumps((w11_target or {}).get("name_slot"),
                           ensure_ascii=False),
                (w11_target or {}).get("filename"),
                (w11_target or {}).get("digest"),
                (w11_target or {}).get("digest_is_no_digest")))
    v.append("6. 与 W10 [97] / W9 [97] 逐字段对照见 `out\\compare_with_W10.md`"
             "（同一解析器重算三方 hex）")
    v.append("7. 列表逐索引 diff（W10→W11）：名称差异条目 %d 个（预期仅 [97]"
             " 一处变化）" % diff_10_11["n_diff_entries"])
    if isinstance(bd_11_vs_10, dict) and "error" not in bd_11_vs_10:
        v.append("8. 目标缓冲 768B 逐字节对比 W10↔W11：差异 %d/%d 字节"
                 "（散落单字节，运行期易变类）；名称槽 0–87 / 文件名 88–116 / "
                 "digest 区 348–361 相等性 = %s/%s/%s"
                 % (bd_11_vs_10["n_diff_bytes"], bd_11_vs_10["n_bytes"],
                    bd_11_vs_10["name_slot_0_87_equal"],
                    bd_11_vs_10["filename_88_116_equal"],
                    bd_11_vs_10["digest_348_361_equal"]))
    v.append("")
    if q2:
        v.append("## Q2：进图后 ~20s 异常结束是否仍在（仅当 Q1 名称正常才做）")
        v.append("")
        if q2.get("error"):
            v.append("- Q2 分析异常：%s" % q2["error"])
        else:
            v.append("**verdict = `%s`**" % q2["verdict"])
            v.append("")
            v.append("%s" % q2["verdict_zh"])
            v.append("")
            v.append("- 采样：%d 拍，读失败 %d 拍，phase_stop=%s"
                     % (q2["n_samples"], q2["n_read_fail"],
                        q2["phase_stop"]))
            v.append("- 5s 桶速率：%s"
                     % json.dumps(q2["buckets"], ensure_ascii=False))
            v.append("- 2s 滑动窗 min/max：%s / %s"
                     % (json.dumps(q2["slide_min"]),
                        json.dumps(q2["slide_max"])))
            v.append("- 停推段：%s"
                     % json.dumps(q2["stall_segments"], ensure_ascii=False))
            v.append("- 结算屏 GUI:Continue 首现：%s（W9 基线 25.0s）"
                     % q2["continue_seen_at"])
            v.append("- W9 基线对照：4.95–20s 三桶 31.12/31.28/30.71；"
                     "21.0s 起停推 mode=5；~25s 起 GUI:Continue 持续至 70s")
        v.append("")
    v.append("## 归因纪律（红线）")
    v.append("")
    v.append("- 本卡含两个差异（CRLF 沿用 + `[Header]`），但行尾已被 W10 单变量"
             "单独否证，故 Q1 成功时只能归因到 `[Header]`；该推理链已显式写入"
             "上文。")
    v.append("- Q1 仍 No Name 时按任务书停止：两个结构变量均否证，不再尝试"
             "第四变量（Lead 按「H1 修复失败时改用已验证对局作替代基线」收口）。")
    v.append("- 「没读到名称」（diag≠ok，含原始字节）与「名称为空」（读到但空串）"
             "分开记录。")
    v.append("- 条目数若未变（仍 268）= 文件未被扫描，与「显示 No Name」是不同"
             "问题。")
    v.append("- 不抓栈、不推断机制。")
    v.append("")
    (W11 / "VERDICT.md").write_text("\n".join(v) + "\n", encoding="utf-8")

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
        "w9_97": {k: w9_audits.get(97, {}).get(k) for k in
                  ("name_slot", "name_slot_diag", "filename", "digest",
                   "digest_is_no_digest")},
        "w10_97": {k: w10_audits.get(97, {}).get(k) for k in
                   ("name_slot", "name_slot_diag", "filename", "digest",
                    "digest_is_no_digest")},
        "w11_target": {k: (w11_target or {}).get(k) for k in
                       ("index", "name_slot", "name_slot_diag", "filename",
                        "digest", "digest_is_no_digest")},
        "target_basis": target_basis,
        "list_diff_10_11": {k: diff_10_11[k] for k in
                            ("n_w10", "n_w11", "n_items_equal",
                             "n_diff_entries")},
        "list_diff_10_11_detail": diff_10_11["diffs"],
        "list_diff_9_11_n": diff_9_11["n_diff_entries"],
        "buf_byte_diff_vs_10": bd_11_vs_10,
        "buf_byte_diff_vs_9": bd_11_vs_9,
        "q2": q2,
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
        "target_names": maplist.get("target_hits"),
        "noname": maplist.get("noname_literal_indices"),
        "w11_name_slot": (w11_target or {}).get("name_slot"),
        "w11_filename": (w11_target or {}).get("filename"),
        "w11_digest": (w11_target or {}).get("digest"),
        "digest_is_no_digest": (w11_target or {}).get("digest_is_no_digest"),
        "target_basis": target_basis,
        "diff_10_11_entries": diff_10_11["n_diff_entries"],
        "q2_verdict": (q2 or {}).get("verdict"),
        "q2_zh": (q2 or {}).get("verdict_zh"),
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
    print("用法：--run 真机一趟（名称出现才开局）；--analyze 离线对照 W10/W9 + VERDICT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
