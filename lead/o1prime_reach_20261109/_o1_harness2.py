# -*- coding: utf-8 -*-
"""O1' 子格实证 harness v2（零真机/零采样；静态 import 被核模块 + 写域内真实写失败）。

· 用 importlib 标准 import 机制加载被核件（顶层惰性已由 _o1_astcheck.py 静态证明），
  直接调用其真函数：make_pre_freshness_snapshot / copy_post_except_evidence /
  classify_except_freshness / Recorder；
· 在写域 _o1_tmp 内造四种**真实** dst.write_bytes 失败形态（out_dir 缺失 / out_dir 是
  普通文件 / 超长路径 / ACL 拒写），spy 抓 classify 实收 post_observed 与真实返回；
· 另做方法 C 对照：直接构造 post_observed 喂真 classify。
被核件只读；所有写都落本任务写域。
"""
import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CAND = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\o1prime_reach_20261109")
TMP = OUT / "_o1_tmp"

raw = CAND.read_bytes()
print("被核对象 SHA256 =", hashlib.sha256(raw).hexdigest())
print("字节数 =", len(raw))
print("python =", sys.version.split()[0], "| platform =", platform.platform())

# ---- 静态 import 被核模块（ask 明示允许；顶层惰性已静态核过）----
spec = importlib.util.spec_from_file_location("qc151_cand_o1", CAND)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("IMPORT_OK  FRESHNESS_SNAPSHOT_STATES =", mod.FRESHNESS_SNAPSHOT_STATES)

real_classify = mod.classify_except_freshness
spy_log = []

def classify_spy(pre, post):
    ret = real_classify(pre, post)
    spy_log.append({"pre_state": pre.get("state") if isinstance(pre, dict) else repr(pre),
                    "post_in": dict(post) if isinstance(post, dict) else repr(post),
                    "ret": dict(ret)})
    return ret

mod.classify_except_freshness = classify_spy   # 同一全局名，copy_post 调用时查到 spy，spy 内调真件

def fresh_carrier(tag):
    c = TMP / ("carrier_" + tag)
    if c.exists():
        shutil.rmtree(c)
    c.mkdir(parents=True)
    return c

def run_case(tag, make_out_dir):
    print("=" * 76)
    print("CASE", tag)
    rec = mod.Recorder()
    spy_log.clear()
    carrier = fresh_carrier(tag)
    pre = mod.make_pre_freshness_snapshot(carrier / "except.txt")   # 跑前快照（此刻无件）
    print("pre_snapshot.state =", pre.get("state"), "（真 make_pre_freshness_snapshot 产出）")
    blob = ("O1' 实证趟 " + tag + " " + datetime.now().isoformat(timespec="milliseconds") + "\n").encode("utf-8")
    (carrier / "except.txt").write_bytes(blob)   # 模拟游戏进程本趟写出的崩溃件
    out_dir = make_out_dir(tag)
    if out_dir is None:
        print("   [SKIP] 该失败形态在本机造不出来（原因见上一行）")
        return None
    print("out_dir   =", str(out_dir)[:130])
    raised = None
    info = None
    try:
        info = mod.copy_post_except_evidence(rec, carrier, out_dir, pre_freshness_snapshot=pre)
    except Exception as exc:
        raised = type(exc).__name__ + ": " + str(exc)
    print("raised   =", raised)
    print("returned =", json.dumps(info, ensure_ascii=False, default=str)[:300] if info else None)
    if spy_log:
        post = spy_log[-1]["post_in"]
        print("classify 实收 post_observed（实流产物，非手工构造）:")
        for k in ("exists", "size", "sha256", "mtime_post", "captured_at_iso", "read_error"):
            print("   %-15s = %s" % (k, post.get(k) if isinstance(post, dict) else None))
        print("classify 实际返回:", json.dumps(spy_log[-1]["ret"], ensure_ascii=False))
    print("rec 留痕:")
    for e in rec.rows:
        print("   [%s] %s = %s" % (e["group"], e["key"], str(e["value"])[:120]))
    return {"tag": tag, "raised": raised,
            "post": spy_log[-1]["post_in"] if spy_log else None,
            "ret": spy_log[-1]["ret"] if spy_log else None}

def mk_ok(tag):
    d = TMP / ("out_ok_" + tag)
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d

def mk_missing(tag):
    d = TMP / ("vanished_out_" + tag)
    if d.exists():
        shutil.rmtree(d)
    return d                                    # 故意不创建 ⇒ dst 父目录缺失

def mk_isfile(tag):
    f = TMP / ("plainfile_" + tag + ".txt")
    f.write_bytes(b"not a directory\n")
    return f

def mk_long(tag):
    base = TMP / ("long_" + tag)
    if base.exists():
        shutil.rmtree(base)
    p = base
    for _ in range(5):
        p = p / ("d" * 48)
    try:
        p.mkdir(parents=True)
    except Exception as exc:
        print("   [B3 前置] 深目录建不出来（本机长路径未放行）:", type(exc).__name__, str(exc)[:110])
        return None
    return p

DENY_DIR = [None]

def mk_denied(tag):
    d = TMP / ("denied_" + tag)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    r = subprocess.run(["icacls", str(d), "/deny", "*S-1-1-0:(WD)"],
                       capture_output=True, text=True)
    print("   [B4 前置] icacls deny rc =", r.returncode, (r.stdout or r.stderr).strip()[:100])
    if r.returncode != 0:
        return None
    DENY_DIR[0] = d
    return d

summary = []
summary.append(run_case("success_control", mk_ok))
summary.append(run_case("B1_outdir_missing", mk_missing))
summary.append(run_case("B2_outdir_is_file", mk_isfile))
summary.append(run_case("B3_longpath", mk_long))
summary.append(run_case("B4_acl_denied", mk_denied))

# ---------- 方法 C：直接构造 post_observed 喂真 classify ----------
print("=" * 76)
print("CASE C · 直接构造 post_observed 喂真 classify（对照）")
pre_absent = mod.make_pre_freshness_snapshot(TMP / "no_such_dir_xyz" / "except.txt")
probe = TMP / "probe_present.txt"
probe.write_bytes(b"hello")
pre_present = mod.make_pre_freshness_snapshot(probe)
print("pre_absent.state =", pre_absent["state"], "| pre_present.state =", pre_present["state"],
      "| pre_present.sha256 =", pre_present["sha256"])
now = mod.now_iso()
cases_c = [
    ("O1' 子格: exists=True × read_error × pre=absent_confirmed", pre_absent,
     {"exists": True, "size": 5, "sha256": "a" * 64, "mtime_post": 1700000000.0,
      "captured_at_iso": now, "read_error": "PermissionError: 模拟"}),
    ("O1' 子格: exists=True × read_error × pre=present", pre_present,
     {"exists": True, "size": 5, "sha256": "a" * 64, "mtime_post": 1700000000.0,
      "captured_at_iso": now, "read_error": "OSError: 模拟"}),
    ("主子格: exists=None × read_error × pre=absent_confirmed", pre_absent,
     {"exists": None, "size": None, "sha256": None, "mtime_post": None,
      "captured_at_iso": now, "read_error": "FileNotFoundError: 模拟"}),
    (":6 行合法形态: exists=True 无 read_error × pre=absent_confirmed", pre_absent,
     {"exists": True, "size": 5, "sha256": "b" * 64, "mtime_post": 1700000000.0,
      "captured_at_iso": now, "read_error": None}),
]
for label, pre, post in cases_c:
    ret = mod.classify_except_freshness(pre, post)
    print(" - %s\n     => verdict=%r confidence=%r is_new=%r usable=%r" %
          (label, ret["verdict"], ret["confidence"], ret["is_new"],
           ret["usable_as_crash_evidence"]))

# ---------- 清理 ACL ----------
if DENY_DIR[0] is not None:
    r = subprocess.run(["icacls", str(DENY_DIR[0]), "/remove:d", "*S-1-1-0"],
                       capture_output=True, text=True)
    print("CLEANUP icacls remove-deny rc =", r.returncode)
print("SUMMARY_JSON =", json.dumps(
    [{"tag": s["tag"], "raised": s["raised"],
      "post_exists": (s["post"] or {}).get("exists") if s else None,
      "post_read_error": (s["post"] or {}).get("read_error") if s else None,
      "verdict": (s["ret"] or {}).get("verdict") if s else None,
      "confidence": (s["ret"] or {}).get("confidence") if s else None,
      "is_new": (s["ret"] or {}).get("is_new") if s else None,
      "usable": (s["ret"] or {}).get("usable_as_crash_evidence") if s else None}
     for s in summary if s], ensure_ascii=False))
print("HARNESS_DONE")
