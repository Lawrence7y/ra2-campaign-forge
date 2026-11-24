# -*- coding: utf-8 -*-
# O1′ 复核员独立实证 harness（写域内受控实验；零真机、零采样）。
# 方法与撰写人（方法 A+B：父目录缺失 / 父为文件 / icacls ACL 拒写）不同：
#   · 方法 C：构造字典直喂真 classify_except_freshness（不经 copy_post）；
#   · 方法 A'：两种撰写人未用过的真实 write_bytes 失败根因——
#       A'-1 out_dir 含 Windows 非法字符 '?' → OSError WinError 123；
#       A'-2 out_dir 本身是已存在的普通文件 → NotADirectoryError；
#   · 探针包装 classify_except_freshness（只捕获入参后转调原函数，不改判定），
#     用 copy_post 真函数 + 候选件自产 make_pre_freshness_snapshot 走真实
#     pre(absent_confirmed)→本趟写出 except.txt→copy 读源成功→dst 写失败 全序列，
#     直接观察 except 块之后 post_observed 里 exists 是否仍为 True（关键分歧点④）。
import importlib.util
import json
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CAND = ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
TMP = ROOT / "lead/o1prime_reach_20261109/_o1v_tmp"

print(f"[0] python={sys.version.split()[0]} isolated={sys.flags.isolated}")
if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir(parents=True)
print("[0] import candidate via importlib (module-level code will run)")

spec = importlib.util.spec_from_file_location("qc151_cand_o1v", CAND)
cand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cand)
print(f"[0] import OK: {CAND.name} bytes={CAND.stat().st_size}")

# ---------------- 方法 C：构造字典 → 真 classify ----------------
_orig = cand.classify_except_freshness


def c(label, pre, post):
    r = _orig(pre, post)
    print(f"[C {label}]\n    verdict={r['verdict']!r} confidence={r['confidence']!r} "
          f"is_new={r['is_new']!r} usable={r['usable_as_crash_evidence']!r} "
          f"pre_state={r['pre_snapshot_state']!r}")
    return r


pre_absent = {"state": "absent_confirmed", "exists": False, "size": None,
              "sha256": None, "mtime_pre": None, "captured_at_epoch": 1.0,
              "captured_at_iso": "pre", "error": None, "traceback": None,
              "source": "o1v-constructed"}
post_err = {"exists": True, "size": 26515, "sha256": "ab" * 32,
            "mtime_post": 1234.5, "captured_at_iso": "post",
            "read_error": "OSError: [WinError 123] injected-o1v"}
post_ok = dict(post_err, read_error=None)
pre_unkn = dict(pre_absent, state="unknown")
pre_pres = dict(pre_absent, state="present", exists=True,
                sha256="cd" * 32, mtime_pre=1.0)

c("C1 O1prime cell absent_confirmed x exists=True x read_error", pre_absent, post_err)
c("C2 control legit NFA absent_confirmed x exists=True x no error", pre_absent, post_ok)
c("C3 pre=unknown x read_error (branch-order proof)", pre_unkn, post_err)
c("C4 pre=present x read_error", pre_pres, post_err)
c("C5 empty-string read_error (truthiness edge)", pre_absent, dict(post_err, read_error=""))

# ---------------- spy：捕获 copy_post 实传 classify 的 post_observed ----------------
captured = []


def _spy(pre, post):
    captured.append({
        "pre_state": pre.get("state") if isinstance(pre, dict) else None,
        "post": dict(post) if isinstance(post, dict) else None})
    return _orig(pre, post)


cand.classify_except_freshness = _spy


def real_failure(label, out_dir):
    """真实流序列：pre 快照(src 不存在)→本趟写出 except.txt→copy_post 读源成功→
    dst.write_bytes 真实失败→except 块→classify（被 spy 捕获）→raise。"""
    carrier = TMP / ("carrier_" + label)
    carrier.mkdir(parents=True, exist_ok=True)
    src = carrier / "except.txt"
    pre = cand.make_pre_freshness_snapshot(src)  # 真函数；此时 src 尚不存在
    print(f"[A' {label}] pre_snapshot.state={pre['state']!r} "
          f"(via candidate's own make_pre_freshness_snapshot :4580)")
    src.write_bytes(b"O1V-REVIEW-PROBE carrier payload written by this-run simulation "
                    + label.encode() * 30)
    captured.clear()
    rec = cand.Recorder()
    err = None
    try:
        cand.copy_post_except_evidence(rec, carrier, out_dir,
                                       pre_freshness_snapshot=pre)
    except Exception as e:  # noqa: BLE001 —— 本实验就是要接住这个 raise
        err = e
    print(f"[A' {label}] raised = {type(err).__name__}: {err}")
    if err is not None:
        frs = [(Path(fr.filename).name, fr.lineno, fr.name)
               for fr in traceback.extract_tb(err.__traceback__)]
        cand_frames = [f for f in frs if "candidate_lf" in f[0]]
        print(f"[A' {label}] traceback frames bound to candidate = {cand_frames}")
    last = captured[-1] if captured else None
    print(f"[A' {label}] spy.post_observed_at_classify = "
          f"{json.dumps(last, ensure_ascii=False)}")
    if last and isinstance(last.get("post"), dict):
        p = last["post"]
        print(f"[A' {label}] >>> KEY POINT4: post_observed['exists'] after write_bytes "
              f"failure = {p.get('exists')!r} (None reset would show None)")
    rows = rec.rows
    ekeys = [(r["key"], str(r["value"])[:80]) for r in rows if r["group"] == "ERROR"]
    print(f"[A' {label}] ERROR rows = {ekeys}")
    frows = {r["key"]: r["value"] for r in rows if r["group"] == "FRESHNESS"}
    print(f"[A' {label}] F = (verdict={frows.get('freshness_verdict')!r}, "
          f"confidence={frows.get('freshness_confidence')!r}, "
          f"is_new={frows.get('freshness_is_new')!r}, "
          f"usable={frows.get('usable_as_crash_evidence')!r})")


# A'-1：out_dir 含非法字符 '?'（Windows 保留字符）→ 真实 open() 失败
real_failure("badchar", TMP / "_o1v_bad?dir")
# A'-2：out_dir 本身是普通文件 → NotADirectoryError（撰写人未用的根因）
fileout = TMP / "_o1v_out_is_file"
fileout.write_bytes(b"this is a regular file, not a directory")
real_failure("outdirfile", fileout)

print("[end] harness done (no game process, no sampling, write domain only)")
