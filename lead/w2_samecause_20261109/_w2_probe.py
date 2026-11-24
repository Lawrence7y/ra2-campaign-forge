# -*- coding: utf-8 -*-
"""_w2_probe.py — W2 双时点同源检验探针（唯一写域内受控实验）。

纪律：零真机（不启动 gamemd.exe/ra2loader/YURI.exe，不 taskkill，不读活进程内存）；
零采样（无 hook/MiniDump/SuspendThread/StackWalk/注入/动态内存解析）；
所有受控文件操作仅落 D:\\Project\\ra2-campaign-forge\\lead\\w2_samecause_20261109\\ 内；
候选模块经 importlib 静态装载、原样调用、代码零改动。
"""
import ctypes
import hashlib
import importlib.util
import os
import subprocess
import sys
import traceback
from pathlib import Path

W2DIR = Path(r"D:\Project\ra2-campaign-forge\lead\w2_samecause_20261109")
CASE = W2DIR / "_w2_case"
OUTD = W2DIR / "_w2_out"

USER = os.environ.get("USERNAME", "Administrator")


def sep(title):
    print("")
    print("=" * 76)
    print(title)
    print("=" * 76)


# ---------------------------------------------------------------- A. 环境
sep("A. 环境")
print("python:", sys.version)
print("exe:", sys.executable)
print("user:", USER)

# ------------------------------------------------- B. 编排方指纹逐件复算
sep("B. 指纹复算（hashlib.sha256，9 件 vs 编排方基线）")
EXPECTED = [
    (r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    (r"D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109\MATRIX_DEFECT_REACHABILITY.md",
     "cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6", 27825),
    (r"D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109\_mr_REACH_EVIDENCE_20261109.md",
     "67d0fc90ceae277f23d43f80484da9445a6385994752a882d04a8517809f10e9", 20820),
    (r"D:\Project\ra2-campaign-forge\lead\matrix_ab_ruling_20261109\RULING_MATRIX_AB.md",
     "0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851),
    (r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\STATE_MATRIX.json",
     "1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    (r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md",
     "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    (r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    (r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
match_n = 0
for path, want_sha, want_n in EXPECTED:
    p = Path(path)
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
            n += len(blk)
    ok = (h.hexdigest() == want_sha) and (n == want_n)
    match_n += 1 if ok else 0
    print(f"[{'MATCH' if ok else 'MISMATCH'}] {p.name} sha={h.hexdigest()} bytes={n}")
print(f"指纹核对：{match_n}/{len(EXPECTED)} MATCH")

# ------------------------------------------------------- C. 装载候选模块
sep("C. importlib 静态装载候选模块（代码零改动）")
CAND = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py")
spec = importlib.util.spec_from_file_location("_qc151_cand_w2check", CAND)
mod = importlib.util.module_from_spec(spec)
sys.modules["_qc151_cand_w2check"] = mod
spec.loader.exec_module(mod)
print("module loaded:", mod.__name__)
make_pre = mod.make_pre_freshness_snapshot
copy_post = mod.copy_post_except_evidence
classify = mod.classify_except_freshness
Recorder = mod.Recorder
print("functions:", make_pre.__name__, copy_post.__name__, classify.__name__)

# --------------------------------------------------- 工具：icacls / 句柄
def icacls(*args):
    r = subprocess.run(["icacls", *args], capture_output=True,
                       encoding="mbcs", errors="replace")
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def winerr(exc):
    return getattr(exc, "winerror", None) or getattr(exc, "errno", None)


def describe(path):
    """对路径做三项只读探测：os.stat / Path.exists / open('rb')。"""
    p = Path(path)
    r = {}
    try:
        st = os.stat(p)
        r["stat"] = f"ok size={st.st_size}"
    except OSError as e:
        r["stat"] = f"OSError winerror={winerr(e)} {type(e).__name__}"
    try:
        v = p.exists()
        r["Path.exists"] = f"returned {v}"
    except OSError as e:
        r["Path.exists"] = f"RAISED {type(e).__name__} winerror={winerr(e)}"
    except ValueError as e:
        r["Path.exists"] = f"RAISED ValueError {e}"
    try:
        with open(p, "rb") as f:
            f.read(1)
        r["open_rb"] = "ok"
    except OSError as e:
        r["open_rb"] = f"OSError winerror={winerr(e)} {type(e).__name__}"
    return r


def run_make_pre(path, tag):
    """真 make_pre（T0 时点模拟）。"""
    try:
        snap = make_pre(Path(path))
        print(f"  [{tag}] make_pre -> state={snap['state']!r} exists={snap['exists']!r} "
              f"size={snap['size']!r} sha={(snap['sha256'] or '')[:12]!r} "
              f"error={ (snap['error'] or '')[:80]!r}")
        return snap
    except Exception as e:
        print(f"  [{tag}] make_pre 外抛 {type(e).__name__}: {e}")
        return None


def run_copy_post(snap, carrier_dir, out_dir, tag):
    """真 copy_post（T1 时点模拟）+ 真 Recorder；返回 (raised, verdict_rows)。"""
    rec = Recorder()
    raised = None
    try:
        info = copy_post(rec, Path(carrier_dir), Path(out_dir),
                         pre_freshness_snapshot=snap)
        print(f"  [{tag}] copy_post 返回 {info if info is None else 'dict(evidence_path=' + str(info.get('evidence_path')) + ')'}")
    except Exception as e:
        raised = f"{type(e).__name__}: {e}"
        print(f"  [{tag}] copy_post 外抛 {raised}  (winerror={winerr(e)})")
    vr = [ (r['key'], r['value']) for r in rec.rows
           if r['group'] == 'FRESHNESS' and r['key'].endswith(('verdict', 'confidence', 'is_new')) ]
    er = [ (r['key'], str(r['value'])[:70]) for r in rec.rows if r['group'] == 'ERROR' ]
    print(f"  [{tag}] FRESHNESS verdict/conf/is_new = {vr}")
    print(f"  [{tag}] ERROR 行 = {er if er else '无'}")
    return raised, vr, er, rec


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateFileW.restype = ctypes.c_void_p
k32.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                            ctypes.c_void_p]
INVALID_HANDLE = ctypes.c_void_p(-1).value or 0


def open_exclusive(p):
    """同进程内持一把 share-mode=0 的独占句柄（模拟他方进程握柄）。"""
    h = k32.CreateFileW(str(p), 0xC0000000, 0, None, 3, 0x80, None)
    if h in (None, INVALID_HANDLE):
        print("  CreateFileW 失败 lasterr=", ctypes.get_last_error())
        return None
    return h


# ------------------------------------------------- D. 路径串异常（R5 前哨）
sep("D. 路径串异常三态（R5：非法字符 / ENOTDIR / 超长 / 正常缺席）——只读探测不建件")
ILL = W2DIR / "_w2_ill|gal.txt"
ENOTDIR = W2DIR / "_w2_probe.py" / "child.txt"
LONG = W2DIR / ("_w2_long_" + "x" * 250 + ".txt")
ABSENT = W2DIR / "_w2_absent_definitely.txt"
for nm, pp in [("非法字符", ILL), ("ENOTDIR", ENOTDIR), ("超长>260", LONG),
               ("正常缺席", ABSENT)]:
    print(f"  -- {nm}: {describe(pp)}")
    run_make_pre(pp, f"R5·{nm}")

# ------------------------------------------ E. deny-RD（拒读数据）双时点
sep("E. 同一 deny-(RD) ACE 横跨两时点（同源子集实证：真 make_pre + 真 copy_post）")
CASE.mkdir(parents=True, exist_ok=True)
OUTD.mkdir(parents=True, exist_ok=True)
src = CASE / "except.txt"
src.write_bytes(b"W2 samecause probe baseline content\n")
print("  S0 基线（无 deny）:", describe(src))
snap0 = run_make_pre(src, "S0·T0")
run_copy_post(snap0, CASE, OUTD, "S0·T1")

rc, out = icacls(str(src), "/deny", f"{USER}:(RD)")
print(f"  icacls /deny {USER}:(RD) -> rc={rc} {out[:120]!r}")
print("  S1 deny-RD 状态:", describe(src))
snap1 = run_make_pre(src, "S1·T0(deny-RD)")
run_copy_post(snap1, CASE, OUTD, "S1·T1(deny-RD 同一 ACE 持续)")

rc, out = icacls(str(src), "/remove:d", USER)
print(f"  icacls /remove:d {USER} -> rc={rc}")
print("  S2 还原后:", describe(src))
snap2 = run_make_pre(src, "S2·T0(还原)")
run_copy_post(snap2, CASE, OUTD, "S2·T1(还原)")

# ------------------------------------------ F. deny-R（连属性一起拒）形态
sep("F. deny-R（拒全部读含属性）——exists() 在 py3.12.10 下吞还是抛")
rc, out = icacls(str(src), "/deny", f"{USER}:R")
print(f"  icacls /deny {USER}:R -> rc={rc} {out[:120]!r}")
print("  S3 deny-R 状态:", describe(src))
snap3 = run_make_pre(src, "S3·T0(deny-R)")
run_copy_post(snap3, CASE, OUTD, "S3·T1(deny-R 同一 ACE 持续)")
icacls(str(src), "/remove:d", USER)
print("  S4 还原后:", describe(src))

# ---------------------------------------------- G. 独占句柄（R1/R6 机理）
sep("G. share-mode=0 独占句柄横跨两时点（机理演示；T0 无游戏进程见结论）")
lock_src = CASE / "except.txt"
h = open_exclusive(lock_src)
if h:
    print("  独占句柄已持有（同进程内模拟他方握柄）")
    print("  S5 锁定期状态:", describe(lock_src))
    snap5 = run_make_pre(lock_src, "S5·T0(锁)")
    run_copy_post(snap5, CASE, OUTD, "S5·T1(锁)")
    k32.CloseHandle(h)
    print("  句柄已释放:", describe(lock_src))
else:
    print("  无法建立独占句柄（本环境不支持？）")

# -------------------------------------------- H. 写侧失败也产 read_error
sep("H. dst 写失败（out_dir 指向普通文件）——T1-only 根因同样落 read_error")
notdir = W2DIR / "_w2_not_a_dir.txt"
notdir.write_bytes(b"i am a file, not a dir\n")
snap6 = run_make_pre(src, "H·T0(正常)")
run_copy_post(snap6, CASE, notdir, "H·T1(dst=普通文件)")

# ------------------------------------------------------------- I. 收尾
sep("I. 收尾清理（写域内临时件删除）")
for junk in [notdir, src]:
    try:
        junk.unlink()
        print("  deleted", junk.name)
    except OSError as e:
        print("  delete failed", junk.name, e)
for d in (CASE, OUTD):
    for q in sorted(d.rglob("*"), reverse=True):
        try:
            q.rmdir() if q.is_dir() else q.unlink()
        except OSError as e:
            print("  cleanup skip:", q, e)
print("W2_PROBE_DONE")
