# -*- coding: utf-8 -*-
# _w2v_probe1.py — 复核轮独立探针：R5 路径吞没 / 真函数 ACL 双时点桥接 / 写侧单点 / 正常对照
# 全部实验材料落在唯一写域 lead/w2_samecause_20261109/_w2v_case* 与 _w2v_out*；只读被核域。
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / r"lead\w2_samecause_20261109"
CASE = WD / "_w2v_case"
OUT = WD / "_w2v_out"
CAND = ROOT / r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"

print("python", sys.version.replace("\n", " "))

spec = importlib.util.spec_from_file_location("qc151_candidate_w2v", str(CAND))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("module_loaded OK")
make_pre = mod.make_pre_freshness_snapshot
copy_post = mod.copy_post_except_evidence
FG = mod.FRESHNESS_GROUP
FKP = mod.FRESHNESS_KEY_PREFIX

for d in (CASE, OUT):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)

results = []


def check(tag, cond, detail=""):
    results.append((tag, bool(cond)))
    print(("PASS" if cond else "FAIL"), tag, detail)


def fresh(rec):
    v = [r["value"] for r in rec.rows
         if r["group"] == FG and r["key"] == FKP + "verdict"]
    p = [r["value"] for r in rec.rows
         if r["group"] == FG and r["key"] == "pre_snapshot_state"]
    return (v[-1] if v else None), (p[-1] if p else None)


# ---------- R5: py3.12 exists() 吞非法路径；真 make_pre 全落 absent_confirmed ----------
(CASE / "notadir.txt").write_bytes(b"x")
cases5 = [("illegal", CASE / "bad<>|.txt"),
          ("enotdir", CASE / "notadir.txt" / "sub.txt"),
          ("toolong", CASE / ("x" * 300))]
for tag, p in cases5:
    try:
        e = p.exists()
        print("R5 exists(%s) -> %s" % (tag, e))
    except Exception as exc:
        e = "RAISED"
        print("R5 exists(%s) RAISED %s w%s" % (tag, type(exc).__name__,
                                               getattr(exc, "winerror", None)))
    snap = make_pre(p)
    print("R5 make_pre(%s) -> %s %s" % (tag, snap["state"],
                                        (snap["error"] or "")[:60]))
    check("R5_" + tag + "_absent_confirmed",
          e is False and snap["state"] == "absent_confirmed", snap["state"])

# ---------- R2 旁支：目录路径作 except_path → open 目录失败 → error ----------
snapd = make_pre(CASE)
print("R2dir make_pre(dir) ->", snapd["state"], (snapd["error"] or "")[:60])
check("R2dir_dir_open_error", snapd["state"] == "error", snapd["state"])

# ---------- S0 对照：在场→复制成功→leftover_unchanged ----------
d0 = CASE / "ctl0"
d0.mkdir()
f0 = d0 / "except.txt"
f0.write_bytes(b"hello\n")
snap = make_pre(f0)
check("S0_pre_present", snap["state"] == "present" and len(snap["sha256"]) == 64,
      snap["state"])
rec = mod.Recorder()
info = copy_post(rec, d0, OUT, pre_freshness_snapshot=snap)
v, ps = fresh(rec)
check("S0_copy_leftover", info is not None and v == "leftover_unchanged",
      "%s/%s" % (v, ps))

# ---------- S1 对照：跑前无件→跑后在场→new_first_appearance ----------
d1 = CASE / "ctl1"
d1.mkdir()
snap = make_pre(d1 / "except.txt")
check("S1_pre_absent", snap["state"] == "absent_confirmed", snap["state"])
(d1 / "except.txt").write_bytes(b"crash\n")
rec = mod.Recorder()
info = copy_post(rec, d1, OUT, pre_freshness_snapshot=snap)
v, ps = fresh(rec)
check("S1_new_first", v == "new_first_appearance" and ps == "absent_confirmed",
      "%s/%s" % (v, ps))

# ---------- H：写侧失败（out_dir=普通文件）也落 read_error=post_read_error ----------
d2 = CASE / "ctl2"
d2.mkdir()
(d2 / "except.txt").write_bytes(b"data\n")
outfile = CASE / "outfile_as_outdir"
outfile.write_bytes(b"")
snap = make_pre(d2 / "except.txt")
rec = mod.Recorder()
raised = None
try:
    copy_post(rec, d2, outfile, pre_freshness_snapshot=snap)
except Exception as exc:
    raised = exc
errs = [r for r in rec.rows if r["group"] == "ERROR"
        and r["key"] == "freshness_copy_failed"]
v, ps = fresh(rec)
print("H raised:", type(raised).__name__ if raised else None,
      "errno=", getattr(raised, "errno", None),
      "winerror=", getattr(raised, "winerror", None))
check("H_write_side_post_read_error",
      raised is not None and errs and v == "post_read_error" and ps == "present",
      "%s/%s/%s" % (v, ps, type(raised).__name__))

# ---------- E：文件级 deny-(RD)，真 make_pre(T0)=error + 真 copy_post(T1)=post_read_error ----------
user = os.environ.get("USERNAME", "Administrator")


def icacls(*args):
    r = subprocess.run(["icacls"] + [str(a) for a in args],
                       capture_output=True, text=True)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


d3 = CASE / "aclt"
d3.mkdir()
f3 = d3 / "except.txt"
f3.write_bytes(b"denied\n")
rc, so = icacls(f3, "/deny", "%s:(RD)" % user)
print("E icacls deny rc=%s %s" % (rc, so[:110]))
try:
    ex = f3.exists()
    try:
        f3.stat()
        statres = "ok"
    except Exception as exc:
        statres = "%s w%s" % (type(exc).__name__, getattr(exc, "winerror", None))
    try:
        with open(f3, "rb") as fh:
            fh.read()
        openres = "readable"
    except Exception as exc:
        openres = "%s errno=%s winerror=%s" % (type(exc).__name__,
                                               getattr(exc, "errno", None),
                                               getattr(exc, "winerror", None))
    print("E under deny: exists=%s stat=%s open=%s" % (ex, statres, openres))
    snapE = make_pre(f3)
    print("E make_pre(T0) ->", snapE["state"], (snapE["error"] or "")[:90])
    check("E_pre_error_exists_true",
          ex is True and snapE["state"] == "error", snapE["state"])
    rec = mod.Recorder()
    raisedE = None
    try:
        copy_post(rec, d3, OUT, pre_freshness_snapshot=snapE)
    except Exception as exc:
        raisedE = exc
    v, ps = fresh(rec)
    print("E copy_post(T1) raised:", type(raisedE).__name__ if raisedE else None,
          "errno=", getattr(raisedE, "errno", None),
          "winerror=", getattr(raisedE, "winerror", None))
    check("E_bridge_post_read_error_pre_error",
          raisedE is not None and v == "post_read_error" and ps == "error",
          "verdict=%s pre=%s raised=%s" % (v, ps, type(raisedE).__name__))
finally:
    rc2, so2 = icacls(f3, "/remove:d", user)
    print("E icacls remove:d rc=%s %s" % (rc2, so2[:80]))
    try:
        with open(f3, "rb") as fh:
            fh.read()
        check("E_cleanup_readable", True, "")
    except Exception as exc:
        check("E_cleanup_readable", False,
              "%s w%s" % (type(exc).__name__, getattr(exc, "winerror", None)))

# ---------- E2：目录级继承 deny-(OI)(CI)(RD) 跨「删除重建」持续 ----------
d4 = CASE / "aclt2"
d4.mkdir()
rc, so = icacls(d4, "/deny", "%s:(OI)(CI)(RD)" % user)
print("E2 icacls dir deny rc=%s %s" % (rc, so[:110]))
try:
    f4 = d4 / "except.txt"
    f4.write_bytes(b"v1\n")
    try:
        with open(f4, "rb") as fh:
            fh.read()
        r1 = "readable"
    except Exception as exc:
        r1 = "%s w%s" % (type(exc).__name__, getattr(exc, "winerror", None))
    f4.unlink()
    f4.write_bytes(b"v2\n")   # 模拟游戏删除重建 except.txt
    try:
        with open(f4, "rb") as fh:
            fh.read()
        r2 = "readable"
    except Exception as exc:
        r2 = "%s w%s" % (type(exc).__name__, getattr(exc, "winerror", None))
    snap4 = make_pre(f4)
    print("E2 v1 open=%s ; v2(recreated) open=%s ; make_pre=%s"
          % (r1, r2, snap4["state"]))
    check("E2_inherited_deny_persists_recreate",
          r1 != "readable" and r2 != "readable" and snap4["state"] == "error",
          "%s/%s/%s" % (r1, r2, snap4["state"]))
finally:
    icacls(d4, "/remove:d", user)
    try:
        with open(d4 / "except.txt", "rb") as fh:
            fh.read()
        check("E2_cleanup_readable", True, "")
    except Exception as exc:
        check("E2_cleanup_readable", False, type(exc).__name__)

ok = sum(1 for _, c in results if c)
print("W2V_PROBE1 %d/%d PASS" % (ok, len(results)))
for tag, c in results:
    if not c:
        print("W2V_PROBE1 FAILED:", tag)
