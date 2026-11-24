import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))

mother_path = os.path.join(repo_root, "lead", "goal1_harness8_20261031", "qc151_trip.harness8_v4.py")
dest_path = os.path.join(base_dir, "qc151_trip.harness8_v4_ext.py")

with open(mother_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Verify anchors
assert lines[174] == "from pathlib import Path\n"
assert lines[961] == '            "hits": pairs, "hit_count": len(pairs)}\n'
assert lines[1200] == "    return True\n"
assert lines[4044] == "    return t0, samples, counters, err\n"
assert lines[4824] == "    return p\n"
assert lines[5388] == '                    note="★ §3.2：finally 关句柄")\n'
assert lines[7494] == "    # <<< H6-CLOSE-END argparse\n"
assert lines[7500] == "    args = parse_args(argv)\n"

block1 = '''# >>> W5EXT-BEGIN imports
_W5_DIR = Path(__file__).resolve().parent
_A1_DIR = _W5_DIR.parent / "A1_SAMPLER_CANDIDATE"
if str(_A1_DIR) not in sys.path:
    sys.path.insert(0, str(_A1_DIR))
import frame_edge_sampler

_W5_STATE = {
    "on": False,
    "ra2render_hits": None,
    "ra2loader_hits": None,
    "last_window_events": [],
    "last_window_stats": None,
    "last_window_tracker": None,
}

_W5_CUSTOM_READER = None


def w5_set_reader(reader_fn):
    """注入假 reader（供离线单测使用）"""
    global _W5_CUSTOM_READER
    _W5_CUSTOM_READER = reader_fn


def w5_reset_state():
    """重置 W5EXT 模块状态"""
    global _W5_CUSTOM_READER
    _W5_STATE["on"] = False
    _W5_STATE["ra2render_hits"] = None
    _W5_STATE["ra2loader_hits"] = None
    _W5_STATE["last_window_events"] = []
    _W5_STATE["last_window_stats"] = None
    _W5_STATE["last_window_tracker"] = None
    _W5_CUSTOM_READER = None
# <<< W5EXT-END imports
'''

block2 = '''# >>> W5EXT-BEGIN s4-scan-hook
_s4_scan_names_mother = s4_scan_names


def s4_scan_names(names) -> dict:
    scan = _s4_scan_names_mother(names)
    if _W5_STATE["on"]:
        _W5_STATE["ra2render_hits"] = list(scan.get("ra2render_hits") or [])
        _W5_STATE["ra2loader_hits"] = list(scan.get("ra2loader_hits") or [])
    return scan
# <<< W5EXT-END s4-scan-hook
'''

block3 = '''# >>> W5EXT-BEGIN s4-gate-hook
_s4_injection_gate_mother = s4_injection_gate


def s4_injection_gate(pid: int, rec: Recorder, authorized: bool = False) -> bool:
    res = _s4_injection_gate_mother(pid, rec, authorized=authorized)
    if not _W5_STATE["on"]:
        return res
    if authorized:
        rec.add("S4", "s4_gate", "w5_refused_allow_loader", "script:s4_injection_gate",
                note="★ W5EXT 硬断言阻断：严禁在 --allow-loader / authorized 下启用扩项")
        rec.add("S4", "s4_exit_code", EXIT_INJECTION_SUSPECTED, "script:s4_injection_gate")
        rec.add("W5EXT", "s4_hard_assertion", "FAILED_ALLOW_LOADER",
                "script:s4_injection_gate",
                note="★ W5EXT 硬断言阻断：严禁在 --allow-loader / authorized 下启用扩项")
        S4_VERDICT["gate"] = "w5_refused_allow_loader"
        S4_VERDICT["exit_code"] = EXIT_INJECTION_SUSPECTED
        return False
    r_hits = _W5_STATE.get("ra2render_hits") or []
    l_hits = _W5_STATE.get("ra2loader_hits") or []
    if r_hits != [] or l_hits != [] or not res:
        rec.add("S4", "s4_gate", "w5_hit_rejected", "script:s4_injection_gate",
                note=f"★ W5EXT 硬断言阻断：命中非零，立即停手 (ra2render={r_hits}, ra2loader={l_hits})")
        rec.add("S4", "s4_exit_code", EXIT_INJECTION_SUSPECTED, "script:s4_injection_gate")
        rec.add("W5EXT", "s4_hard_assertion", "FAILED_INJECTION_SUSPECTED",
                "script:s4_injection_gate",
                note=f"★ W5EXT 硬断言阻断：发现非零注入命中 (ra2render={r_hits}, ra2loader={l_hits})，立即停手")
        S4_VERDICT["gate"] = "w5_hit_rejected"
        S4_VERDICT["exit_code"] = EXIT_INJECTION_SUSPECTED
        return False
    rec.add("W5EXT", "s4_hard_assertion", "PASSED",
            "script:s4_injection_gate",
            note="★ W5EXT 硬断言通过：ra2render_hits==[] 且 ra2loader_hits==[]")
    return True
# <<< W5EXT-END s4-gate-hook
'''

block4 = '''# >>> W5EXT-BEGIN poll-span-hook
_measure_poll_span_mother = _measure_poll_span


def _w5_measure_poll_span(handle, span_s: float, hz: int):
    """★ W5 扩项定拍轮询：在既有 500 Hz 轮询中，仅在检测到 CurrentFrame 变化时追加读取四 VA"""
    if _W5_CUSTOM_READER is not None:
        reader = _W5_CUSTOM_READER
    else:
        reader = lambda va: _rpm_u32(handle, va)

    tracker = frame_edge_sampler.FrameEdgeTracker()
    events = []
    samples = []
    counters = []
    errs = 0
    t0 = time.perf_counter()
    t_end = t0 + span_s
    next_ctr = t0 - 1.0
    i = 0
    prev_f = None

    while True:
        t_now = time.perf_counter()
        if t_now >= t_end:
            break
        f = reader(MEASURE_CURRENT_FRAME_VA)
        if f is None:
            errs += 1
            tracker.feed(t_now, None, sample=None)
            prev_f = None
            _doze(0.001)
        else:
            samples.append((t_now, f))
            if prev_f is not None and f != prev_f:
                # 沿触发：恰好追加 4 次读 + 2 次帧号读
                sample = frame_edge_sampler.read_sample(reader, time.perf_counter)
                ev = tracker.feed(t_now, f, sample=sample)
                if ev is not None:
                    events.append(ev)
            else:
                tracker.feed(t_now, f, sample=None)
            prev_f = f

        if t_now >= next_ctr:
            row = _rpm_counters(handle)
            row["t_rel"] = round(t_now - t0, 6)
            counters.append(row)
            next_ctr = t_now + 1.0

        i += 1
        t_next = t0 + i / hz
        ahead = t_next - time.perf_counter()
        while ahead > 0.0025:
            _doze(0.002)
            ahead = t_next - time.perf_counter()

    err = (f"RPM 失败 {errs} 次（有效样本 {len(samples)}）"
           if errs else None)
    _W5_STATE["last_window_events"] = events
    _W5_STATE["last_window_stats"] = tracker.stats()
    _W5_STATE["last_window_tracker"] = tracker
    return t0, samples, counters, err


def _measure_poll_span(handle, span_s: float, hz: int):
    if not _W5_STATE["on"]:
        return _measure_poll_span_mother(handle, span_s, hz)
    return _w5_measure_poll_span(handle, span_s, hz)
# <<< W5EXT-END poll-span-hook
'''

block5 = '''# >>> W5EXT-BEGIN json-hook
_measure_write_json_mother = _measure_write_json


def _measure_write_json(out_dir: Path, k: int, payload: dict) -> Path:
    if not _W5_STATE["on"]:
        return _measure_write_json_mother(out_dir, k, payload)

    events = _W5_STATE.get("last_window_events") or []
    stats = _W5_STATE.get("last_window_stats") or {}

    jsonl_path = out_dir / f"measure_w{k}_w5_events.jsonl"
    try:
        with open(jsonl_path, "w", encoding="utf-8") as jf:
            for ev in events:
                jf.write(frame_edge_sampler.to_jsonl(ev) + "\\n")
    except Exception:
        pass

    payload["w5_ext"] = {
        "schema": frame_edge_sampler.SCHEMA,
        "markers": list(frame_edge_sampler.FIELD_MARKERS),
        "stats": stats,
        "events_count": len(events),
        "events_jsonl": jsonl_path.name,
    }

    if ACTIVE_REC and ACTIVE_REC[0]:
        ACTIVE_REC[0].add("W5EXT", f"window_{k}_stats", stats,
                          "frame_edge_sampler:FrameEdgeTracker",
                          note=f"★ W5 帧沿触发扩项四 VA 统计 (window={k})")
        ACTIVE_REC[0].add("W5EXT", f"window_{k}_events_file", str(jsonl_path),
                          "script:_measure_write_json",
                          note=f"★ W5 逐沿事件落盘 (count={len(events)})")

    return _measure_write_json_mother(out_dir, k, payload)
# <<< W5EXT-END json-hook
'''

block6 = '''# >>> W5EXT-BEGIN measure-run-hook
_measure_run_mother = _measure_run


def _measure_run(rec: Recorder, budget: TripBudget, pid: int, out_dir: Path,
                 map_sha256: str, hwnd=None) -> None:
    if _W5_STATE["on"]:
        # ★ 硬断言 S4：ra2render_hits == [] and ra2loader_hits == []，否则立即停手
        r_hits = _W5_STATE.get("ra2render_hits")
        l_hits = _W5_STATE.get("ra2loader_hits")
        if r_hits is None or l_hits is None or r_hits != [] or l_hits != []:
            rec.add("W5EXT", "measure_gate_aborted", {
                "ra2render_hits": r_hits,
                "ra2loader_hits": l_hits,
            }, "script:_measure_run",
                note="★ W5EXT 硬断言阻断：S4 非干净状态（命中非空或未检测），立即停手，禁止进入采样")
            return
        if getattr(A8_ALLOW_LOADER, "value", False) or (A8_ALLOW_LOADER and A8_ALLOW_LOADER[0]):
            rec.add("W5EXT", "measure_gate_aborted", "allow_loader_active",
                    "script:_measure_run",
                    note="★ W5EXT 硬断言阻断：拒绝在 --allow-loader 下执行扩项采样")
            return
        rec.add("W5EXT", "measure_gate_passed", True, "script:_measure_run",
                note="★ W5EXT 硬断言通过：S4 零命中且非 allow-loader，准许进入扩项采样")
    return _measure_run_mother(rec, budget, pid, out_dir, map_sha256, hwnd)
# <<< W5EXT-END measure-run-hook
'''

block7 = '''    # >>> W5EXT-BEGIN argparse
    ap.add_argument("--w5-ext", type=int, default=0,
                    help="★ W5：四 VA + 帧沿触发只读扩项采样开关（缺省 0=关闭；1=开启）")
    ap.add_argument("--measure-ext", type=int, default=0,
                    help="★ W5：--w5-ext 同义别名（缺省 0）")
    # <<< W5EXT-END argparse
'''

block8 = '''    # >>> W5EXT-BEGIN main-gate
    _w5_on = bool(getattr(args, "w5_ext", 0) or getattr(args, "measure_ext", 0))
    if _w5_on and getattr(args, "allow_loader", False):
        print("[FATAL] W5EXT 冲突：拒绝在 --allow-loader 下启用扩项采样！", file=sys.stderr)
        return EXIT_INJECTION_SUSPECTED
    _W5_STATE["on"] = _w5_on
    if _w5_on and getattr(args, "measure", 0) == 0:
        args.measure = 1
    # <<< W5EXT-END main-gate
'''

out_lines = []
out_lines.extend(lines[0:175])
out_lines.append(block1)
out_lines.extend(lines[175:962])
out_lines.append(block2)
out_lines.extend(lines[962:1201])
out_lines.append(block3)
out_lines.extend(lines[1201:4045])
out_lines.append(block4)
out_lines.extend(lines[4045:4825])
out_lines.append(block5)
out_lines.extend(lines[4825:5389])
out_lines.append(block6)
out_lines.extend(lines[5389:7495])
out_lines.append(block7)
out_lines.extend(lines[7495:7501])
out_lines.append(block8)
out_lines.extend(lines[7501:])

with open(dest_path, "w", encoding="utf-8", newline="\n") as f:
    f.writelines(out_lines)

print(f"Successfully generated {dest_path}")
