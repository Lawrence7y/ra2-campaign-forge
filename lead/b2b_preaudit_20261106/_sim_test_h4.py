# -*- coding: utf-8 -*-
import hashlib
import json
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Load definitions from B2B_DESIGN
design_path = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md")
# Let's import directly from _draft_semantics_check which has the identical implementations
sys_path = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106")
import sys
sys.path.insert(0, str(sys_path))

FRESHNESS_GROUP = "FRESHNESS"
FRESHNESS_KEY_PREFIX = "freshness_"
FRESHNESS_VERDICTS = ("unknown", "absent_both", "new_first_appearance",
                      "vanished", "leftover_unchanged", "new_write",
                      "rewritten_same_content", "error_pre_snapshot",
                      "post_read_error")
FRESHNESS_CONFIDENCES = ("high", "medium", "low", "none")
FRESHNESS_SNAPSHOT_STATES = ("unknown", "absent_confirmed", "present", "error")

def make_pre_freshness_snapshot(except_path: Path) -> dict:
    snap = {"state": "unknown", "exists": None, "size": None,
            "sha256": None, "mtime_pre": None,
            "captured_at_epoch": None, "captured_at_iso": None,
            "error": None, "traceback": None,
            "source": "script:make_pre_freshness_snapshot"}
    try:
        p = Path(except_path)
        snap["captured_at_epoch"] = time.time()
        snap["captured_at_iso"] = now_iso()
        if not p.exists():
            snap["state"] = "absent_confirmed"
            snap["exists"] = False
            return snap
        st = p.stat()
        snap["state"] = "present"
        snap["exists"] = True
        snap["size"] = int(st.st_size)
        snap["mtime_pre"] = float(st.st_mtime)
        snap["sha256"] = sha256_file(p)
    except Exception as exc:
        import traceback
        snap["state"] = "error"
        snap["error"] = f"{type(exc).__name__}: {exc}"
        snap["traceback"] = "".join(traceback.format_exception(exc))
    return snap


def classify_except_freshness(pre_freshness_snapshot, post_observed: dict) -> dict:
    out = {"verdict": None, "confidence": "none", "is_new": None,
           "note": "", "usable_as_crash_evidence": False,
           "pre_snapshot_state": "unknown"}

    def _finish(verdict: str, confidence: str, is_new, note: str) -> dict:
        out.update({"verdict": verdict, "confidence": confidence,
                    "is_new": is_new, "note": note,
                    "usable_as_crash_evidence": False})
        return out

    pre = (pre_freshness_snapshot
           if isinstance(pre_freshness_snapshot, dict) else {})
    st = pre.get("state")
    if st not in FRESHNESS_SNAPSHOT_STATES:
        st = "unknown"
    out["pre_snapshot_state"] = st

    post = post_observed if isinstance(post_observed, dict) else {}
    if post.get("read_error"):
        return _finish("post_read_error", "none", None,
                       f"★ 跑后件读/复制失败: {post['read_error']}；pre_snapshot_state={st}")
    if st == "unknown":
        return _finish("unknown", "none", None, "★ 跑前快照未采集")
    if st == "error":
        return _finish("error_pre_snapshot", "none", None, f"★ 跑前采集失败: {pre.get('error')!r}")

    post_exists = bool(post.get("exists"))
    if not post_exists:
        if st == "absent_confirmed":
            return _finish("absent_both", "low", False, "★ 跑前确认无件 + 跑后无件")
        return _finish("vanished", "none", None, "★ 跑前在、跑后失")

    if st == "absent_confirmed":
        return _finish("new_first_appearance", "high", True, "★ 跑前确认无件 + 跑后在地")

    pre_sha = pre.get("sha256")
    if not pre_sha:
        return _finish("error_pre_snapshot", "none", None, "★ 跑前在场但缺 sha256")
    post_sha = post.get("sha256")
    if not post_sha:
        return _finish("post_read_error", "none", None, "★ 跑后缺 sha256")
    if post_sha != pre_sha:
        return _finish("new_write", "high", True, "★ 字节内容不同")

    pre_mt, post_mt = pre.get("mtime_pre"), post.get("mtime_post")
    if pre_mt is None or post_mt is None:
        return _finish("leftover_unchanged", "medium", False, "★ sha 同但 mtime 侧缺失")
    if abs(float(post_mt) - float(pre_mt)) <= 0.0:
        return _finish("leftover_unchanged", "high", False, "★ 原样遗留")
    if float(post_mt) < float(pre_mt):
        return _finish("rewritten_same_content", "low", True, "★ sha 同、mtime 回拨")
    return _finish("rewritten_same_content", "medium", True, "★ sha 同而 mtime 变")

# Mock Recorder
class Recorder:
    def __init__(self):
        self.rows = []
    def add(self, group: str, key: str, value, source: str, note: str = ""):
        self.rows.append({"group": group, "key": key, "value": value, "source": source, "note": note})

def now_iso():
    return datetime.now().isoformat()

CARRIER_FILES = ("ra2.ini", "rulesmd.ini")
def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

# Define copy_post_except_evidence exactly as in H4
def copy_post_except_evidence(rec: Recorder, carrier_dir: Path,
                              out_dir: Path,
                              pre_freshness_snapshot: dict | None = None
                              ) -> dict | None:
    src = carrier_dir / "except.txt"
    blob = None
    h = None
    dst = None
    post_observed = {"exists": None, "size": None, "sha256": None,
                     "mtime_post": None, "captured_at_iso": None,
                     "read_error": None}

    def _emit_f(fresh: dict, stage: str) -> None:
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "verdict",
                fresh["verdict"], "script:classify_except_freshness",
                note=f"stage={stage}；F 只答新鲜性，E 归 :672-708 集合差")
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "confidence",
                fresh["confidence"], "script:classify_except_freshness",
                note="★ none = 不可判；unknown 恒 none，禁止映射到 high")
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "is_new",
                fresh["is_new"], "script:classify_except_freshness",
                note="★ None = 未测写 null（Recorder :439-440 口径），"
                     "不得写 False 表示未知")
        rec.add(FRESHNESS_GROUP, FRESHNESS_KEY_PREFIX + "note",
                fresh["note"], "script:classify_except_freshness",
                note=fresh["note"])
        rec.add(FRESHNESS_GROUP, "pre_snapshot_state",
                fresh["pre_snapshot_state"],
                "script:make_pre_freshness_snapshot",
                note="★ unknown / absent_confirmed / present / error 三态可分")
        rec.add(FRESHNESS_GROUP, "usable_as_crash_evidence",
                fresh["usable_as_crash_evidence"],
                "script:classify_except_freshness",
                note="★★ 恒 False：F 结论不得作为本趟崩溃证据（:677）")
        rec.add(FRESHNESS_GROUP, "captured_at_iso",
                post_observed.get("captured_at_iso"), "script:now_iso",
                note="★ N10：跑后观测时刻（ISO-8601）；跑前同名键在快照内")

    try:
        if not src.exists():
            post_observed["exists"] = False
            post_observed["captured_at_iso"] = now_iso()
            rec.add("EXCEPT", "evidence_copy", None, f"{src}:path",
                    note="★ 载体 except.txt 不存在 ⇒ 无原件可副本（如实记账）")
            _emit_f(classify_except_freshness(pre_freshness_snapshot,
                                              post_observed), "src_missing")
            return None
        post_observed["captured_at_iso"] = now_iso()
        blob = src.read_bytes()
        st = src.stat()
        h = hashlib.sha256(blob).hexdigest()
        post_observed.update({"exists": True, "size": len(blob),
                              "sha256": h, "mtime_post": float(st.st_mtime)})
        dst = out_dir / f"except_post_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}.txt"
        dst.write_bytes(blob)
    except Exception as exc:
        import traceback
        where = f"{src}:file"
        rec.add("ERROR", "freshness_copy_failed",
                f"{type(exc).__name__}: {exc}", where,
                note="★★ B2b/N10：复制失败显式留痕，不许静默降级")
        rec.add("ERROR", "freshness_copy_stage",
                "read_bytes/stat/write_bytes", where,
                note="captured_at_iso="
                     f"{post_observed.get('captured_at_iso')!r}")
        rec.add("ERROR", "freshness_copy_traceback",
                "".join(traceback.format_exception(exc)), "script:traceback")
        post_observed["read_error"] = f"{type(exc).__name__}: {exc}"
        _emit_f(classify_except_freshness(pre_freshness_snapshot,
                                          post_observed), "copy_failed")
        raise

    info = {"source": str(src), "evidence_path": str(dst),
            "size": len(blob), "sha256": h,
            "note": "★ QC162:W7：还原**之前**取的跑后原件副本"
                    "（☆ 还原之后仍存在、可复核）",
            "mtime_post": post_observed["mtime_post"],
            "freshness_verdict": None,
            "freshness_confidence": None,
            "freshness_note": None,
            "captured_at_iso": None,
            "pre_snapshot_state": None,
            "pre_freshness_snapshot": None}
    fresh = classify_except_freshness(pre_freshness_snapshot, post_observed)
    info["freshness_verdict"] = fresh["verdict"]
    info["freshness_confidence"] = fresh["confidence"]
    info["freshness_note"] = fresh["note"]
    info["captured_at_iso"] = post_observed["captured_at_iso"]
    info["pre_snapshot_state"] = fresh["pre_snapshot_state"]
    info["pre_freshness_snapshot"] = (
        pre_freshness_snapshot
        if isinstance(pre_freshness_snapshot, dict) else None)
    rec.add("EXCEPT", "evidence_copy", info, f"{src}:file",
            note="★★ 跑后 except.txt 原件副本（先于 restore_carrier）")
    _emit_f(fresh, "copied")
    files = {}
    for name in CARRIER_FILES:
        p = carrier_dir / name
        files[name] = ({"path": str(p), "size": p.stat().st_size,
                        "sha256": sha256_file(p)} if p.exists() else None)
    (out_dir / "carrier_post_state.json").write_text(
        json.dumps(files, ensure_ascii=False, indent=1), encoding="utf-8")
    rec.add("EXCEPT", "carrier_post_state_path",
            str(out_dir / "carrier_post_state.json"), "script:copy_post_except_evidence")
    return info

# Test Case 1: src missing
with tempfile.TemporaryDirectory() as td:
    cdir = Path(td) / "carrier"
    cdir.mkdir()
    odir = Path(td) / "out"
    odir.mkdir()
    rec = Recorder()
    res = copy_post_except_evidence(rec, cdir, odir, pre_freshness_snapshot=None)
    assert res is None
    fresh_rows = [r for r in rec.rows if r["group"] == FRESHNESS_GROUP]
    assert len(fresh_rows) == 7, f"Expected 7 FRESHNESS rows, got {len(fresh_rows)}"
    print("Test 1 (src missing): PASS")

# Test Case 2: normal copied
with tempfile.TemporaryDirectory() as td:
    cdir = Path(td) / "carrier"
    cdir.mkdir()
    (cdir / "except.txt").write_bytes(b"CRASH DATA")
    odir = Path(td) / "out"
    odir.mkdir()
    rec = Recorder()
    snap = make_pre_freshness_snapshot(cdir / "except.txt") # captured before
    time.sleep(0.01)
    (cdir / "except.txt").write_bytes(b"NEW CRASH DATA")
    res = copy_post_except_evidence(rec, cdir, odir, pre_freshness_snapshot=snap)
    assert res is not None
    assert len(res) == 12
    assert res["freshness_verdict"] == "new_write"
    fresh_rows = [r for r in rec.rows if r["group"] == FRESHNESS_GROUP]
    assert len(fresh_rows) == 7
    print("Test 2 (normal copied): PASS")

# Test Case 3: copy failure (read-only dst or simulate exception)
with tempfile.TemporaryDirectory() as td:
    cdir = Path(td) / "carrier"
    cdir.mkdir()
    (cdir / "except.txt").write_bytes(b"CRASH DATA")
    odir = Path(td) / "out_missing" # non-existent dir => write_bytes will fail
    rec = Recorder()
    try:
        copy_post_except_evidence(rec, cdir, odir, pre_freshness_snapshot=None)
        assert False, "Should have raised exception"
    except Exception as exc:
        err_rows = [r for r in rec.rows if r["group"] == "ERROR"]
        fresh_rows = [r for r in rec.rows if r["group"] == FRESHNESS_GROUP]
        assert len(err_rows) == 3, f"Expected 3 ERROR rows, got {len(err_rows)}"
        assert len(fresh_rows) == 7, f"Expected 7 FRESHNESS rows, got {len(fresh_rows)}"
        verdict_row = [r for r in fresh_rows if r["key"] == "freshness_verdict"][0]
        assert verdict_row["value"] == "post_read_error"
        print("Test 3 (copy failure): PASS")

print("ALL THREE PATH TESTS PASSED!")
