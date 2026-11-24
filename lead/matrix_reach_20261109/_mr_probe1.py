# -*- coding: utf-8 -*-
"""_mr_probe1.py — 矩阵四处缺陷（W1/W2/O1/O2/W3）实际流可达性实证探针。

方法（零 exec）：importlib 静态装载候选模块（任务规则允许「静态 import 候选
模块」）；候选函数原样调用，不改其代码。classify 仅在模块属性层挂日志包装
（实码原样执行，用于记录 classify 实收输入）；copy_post 用假 Path 对象逼异常
分支（零真实文件写）；make_pre 只做真实只读检查（exists/stat/open 读）。
零真机、零采样、零载体写；本脚本自身除 stdout 外无任何文件写。
候选模块顶层仅 import/常量/一处 SetProcessDPIAware()（:182，探针进程本地）+
__main__ 门（:7532），装载无文件系统/进程副作用。
"""
import ast
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace

CAND = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py")
EXPECT_SHA = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
MATRIX_DOC = Path(r"D:\Project\ra2-campaign-forge\lead\matrix_row5_20261109\MATRIX_ROW5_COUPLING.md")
WD = Path(r"D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109")


def banner(s):
    print("\n" + "=" * 76)
    print(s)
    print("=" * 76)


# ============ P0 绑定 + 静态装载 ============
banner("P0 绑定与静态装载（importlib.util.spec_from_file_location，零 exec）")
raw = CAND.read_bytes()
sha_all = hashlib.sha256(raw).hexdigest()
print(f"[bind] candidate sha256 = {sha_all}")
print(f"[bind] candidate bytes  = {len(raw)}")
print(f"[bind] expected         = {EXPECT_SHA}")
print(f"[bind] MATCH = {sha_all == EXPECT_SHA}")

spec = importlib.util.spec_from_file_location("qc151_candidate_lf_probe", str(CAND))
mod = importlib.util.module_from_spec(spec)
sys.modules["qc151_candidate_lf_probe"] = mod
spec.loader.exec_module(mod)
print("[load] 候选模块静态装载成功：",
      mod.__name__, "FRESHNESS_SNAPSHOT_STATES =", mod.FRESHNESS_SNAPSHOT_STATES,
      "CARRIER_FILES =", mod.CARRIER_FILES)

make_pre = mod.make_pre_freshness_snapshot
real_classify = mod.classify_except_freshness
copy_post = mod.copy_post_except_evidence
Recorder = mod.Recorder

# ============ P0a AST 控制流图（对同一被绑定的原文做静态分析） ============
src = raw.decode("utf-8")
tree = ast.parse(src, filename=str(CAND))
src_lines = src.splitlines()


def seg_of(node):
    return ast.get_source_segment(src, node)


def show_lines(a, b):
    for i in range(a, b + 1):
        print(f"  :{i} {src_lines[i-1]}")


banner("P0a AST 控制流图：make_pre 全部 snap['state'] 赋值点与 return 点")
mp = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "make_pre_freshness_snapshot")
state_assigns, returns, ifs, excepts = [], [], [], []
for node in ast.walk(mp):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "snap" and isinstance(t.slice, ast.Constant)
                    and t.slice.value == "state"):
                state_assigns.append((node.lineno, seg_of(node)))
    elif isinstance(node, ast.Return):
        returns.append(node.lineno)
    elif isinstance(node, ast.If):
        ifs.append((node.lineno, seg_of(node.test)))
    elif isinstance(node, ast.ExceptHandler):
        excepts.append(node.lineno)
for ln, s in sorted(state_assigns):
    print(f"  state 赋值 @:{ln}  {s}")
for ln in sorted(returns):
    print(f"  return    @:{ln}")
for ln, s in sorted(ifs):
    print(f"  if        @:{ln}  test: {s}")
for ln in sorted(excepts):
    print(f"  except    @:{ln}")

banner("P0a2 AST：classify 顶层 if 分支码序")
cl = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "classify_except_freshness")
for st in cl.body:
    if isinstance(st, ast.If):
        print(f"  if @:{st.lineno}  test: {seg_of(st.test)}")

banner("P0a3 AST：copy_post 内 post_observed['read_error'] 全部赋值点")
cp = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "copy_post_except_evidence")
for node in ast.walk(cp):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "post_observed"
                    and isinstance(t.slice, ast.Constant)
                    and t.slice.value == "read_error"):
                print(f"  read_error 写点 @:{node.lineno}: {seg_of(node)}")

banner("P0a4 AST：全模块 _pre_freshness_snapshot / pre_freshness_snapshot 写点")
for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in tgts:
            if isinstance(t, ast.Name) and t.id in (
                    "_pre_freshness_snapshot", "pre_freshness_snapshot"):
                print(f"  {type(node).__name__} @:{node.lineno}: {seg_of(node)[:96]}")

banner("P0a5 源码锚点（候选原文逐行）")
print("-- sha256_file 全文 --")
show_lines(431, 437)
print("-- make_pre try 体 --")
show_lines(4594, 4613)
print("-- classify 头三支 --")
show_lines(4641, 4654)
print("-- classify present 支 --")
show_lines(4671, 4683)
print("-- copy_post src_missing / 异常路径 --")
show_lines(4755, 4764)
show_lines(4773, 4790)

# ============ classify 日志包装（挂模块属性，实码原样执行） ============
CLASSIFY_LOG = []


def classify_logged(pre, post):
    r = real_classify(pre, post)
    CLASSIFY_LOG.append({
        "pre_state_field": (pre.get("state") if isinstance(pre, dict) else None),
        "pre_is_None": pre is None,
        "post_exists": post.get("exists"),
        "post_read_error": post.get("read_error"),
        "verdict": r["verdict"], "confidence": r["confidence"],
        "is_new": r["is_new"],
        "pre_snapshot_state": r["pre_snapshot_state"]})
    return r


mod.classify_except_freshness = classify_logged  # 观察点；copy_post 经模块全局名解析

# ============ P4 make_pre 输出域实跑 sweep（全部真实只读） ============
banner("P4 make_pre 输出域实跑 sweep（8 类输入，纯只读：exists/stat/open 读）")
targets = [
    ("absent·真实不存在的文件", str(WD / "_mr_no_such_file_target.txt")),
    ("present·真实在场的文件(矩阵母件)", str(MATRIX_DOC)),
    ("error?·目录路径(sha256_file 必炸)", str(WD)),
    ("error·Path(None)", None),
    ("error·Path(3)", 3),
    ("error?·非法字符路径", r"D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109\_mr_ill<*>egal.txt"),
    ("edge?·文件底下的子路径(ENOTDIR)", str(MATRIX_DOC / "_mr_under.txt")),
    ("edge·空字符串 ''", ""),
]
states_seen = {}
pre_snaps = {}
for label, t in targets:
    try:
        s = make_pre(t)
    except Exception as exc:  # make_pre 契约是自查不外抛；防御性记录
        print(f"  [{label}] !! make_pre 外抛 {type(exc).__name__}: {exc}")
        continue
    states_seen.setdefault(s["state"], []).append(label)
    pre_snaps[label] = s
    print(f"  [{label}] -> state={s['state']!r} exists={s['exists']} "
          f"size={s['size']} sha256={(s['sha256'] or '')[:16]}"
          f"{'…' if s['sha256'] else ''} error={(s['error'] or '')[:64]!r}")
print(f"  states_seen = { {k: len(v) for k, v in states_seen.items()} }")
print(f"  ★ 显式 'unknown' 是否出现在 make_pre 输出域：{'unknown' in states_seen}")
direct = hashlib.sha256(MATRIX_DOC.read_bytes()).hexdigest()
print(f"  交叉验证：present 件 make_pre 内 sha256 == hashlib 直算："
      f"{pre_snaps['present·真实在场的文件(矩阵母件)']['sha256'] == direct}")

# ============ post 形态构造（与 copy_post 实产形态同构，:4720-4722 七键） ============
PRE_ISO = "2026-11-09T00:00:00+08:00"


def post_read_fail(exists):
    return {"exists": exists,
            "size": 18 if exists else None,
            "sha256": ("ab" * 32) if exists else None,
            "mtime_post": 1760000000.5 if exists else None,
            "captured_at_iso": PRE_ISO,
            "read_error": "PermissionError: [Errno 13] fake-lock (探针构造)"}


def post_ok(sha_hex="ab" * 32, mtime=1760000000.5):
    return {"exists": True, "size": 18, "sha256": sha_hex,
            "mtime_post": mtime, "captured_at_iso": PRE_ISO, "read_error": None}


def post_missing_file():
    return {"exists": False, "size": None, "sha256": None, "mtime_post": None,
            "captured_at_iso": PRE_ISO, "read_error": None}


PRE_ABSENT = pre_snaps["absent·真实不存在的文件"]
PRE_PRESENT = pre_snaps["present·真实在场的文件(矩阵母件)"]
PRE_ERROR = pre_snaps["error·Path(None)"]
PRE_EXPLICIT_UNKNOWN = {"state": "unknown", "exists": None, "size": None,
                        "sha256": None, "mtime_pre": None,
                        "captured_at_epoch": None, "captured_at_iso": None,
                        "error": None, "traceback": None,
                        "source": "probe-fixture:hand-made"}
PRE_PRESENT_NO_SHA = dict(PRE_PRESENT, sha256=None)
PRE_DIRTY = {"state": "garbage"}

# ============ P1 W1 网格：pre 全变体 × post.read_error 两型 ============
banner("P1 W1：pre 全变体 × read_error → classify 实跑 verdict（矩阵 :2 声称 unknown）")
pre_variants = [
    ("None(未采集)", None, ":2"),
    ("{}(未采集)", {}, ":2"),
    ("缺state(未采集)", {"sha256": "x"}, ":2"),
    ("脏值(未采集)", PRE_DIRTY, ":2"),
    ("显式unknown", PRE_EXPLICIT_UNKNOWN,
     "无行(严格键::2不含显式unknown、:3要跑后无件)=W1'"),
    ("absent_confirmed", PRE_ABSENT,
     "无行=O1 / exists=True 型被:6字面误claim=O1'"),
    ("present(带sha)", PRE_PRESENT, ":5"),
    ("error", PRE_ERROR, ":4=W2"),
]
for name, pre, row in pre_variants:
    for tag, post in (("read_error·exists=None", post_read_fail(None)),
                      ("read_error·exists=True", post_read_fail(True))):
        r = real_classify(pre, post)
        print(f"  pre={name:<14} × {tag:<22} -> verdict={r['verdict']!r} "
              f"conf={r['confidence']!r} is_new={r['is_new']} "
              f"pre_state={r['pre_snapshot_state']!r}  [矩阵归属: {row}]")

# ============ P2 W2：error × read_error 细查 ============
banner("P2 W2：pre=error(真实 make_pre 产) × read_error / 跑后无件 对照")
r1 = real_classify(PRE_ERROR, post_read_fail(None))
print(f"  error × read_error(exists=None) -> verdict={r1['verdict']!r} "
      f"conf={r1['confidence']!r} pre_state={r1['pre_snapshot_state']!r} "
      f"note={r1['note'][:72]!r}")
r2 = real_classify(PRE_ERROR, post_missing_file())
print(f"  error × 跑后无件              -> verdict={r2['verdict']!r} "
      f"conf={r2['confidence']!r}  (矩阵 :4 ✓ 对照组)")
print(f"  → 矩阵 :4 声称 error_pre_snapshot，read_error 格实码 "
      f"{r1['verdict']!r} ⇒ W2 实证")

# ============ P3 O1：copy_post 假对象实跑（真实流函数，异常由假对象逼出） ============
banner("P3 O1：copy_post 实跑——pre=absent_confirmed + 复制异常 → read_error")


class FakeLeaf:
    def __init__(self, name, present=True, exists_err=None, read_err=None,
                 write_err=None, data=b"NEW-CRASH-BYTES", mtime=1760000000.5):
        self.name, self._present, self.exists_err = name, present, exists_err
        self.read_err, self.write_err = read_err, write_err
        self.data, self.mtime = data, mtime
        self.written = None

    def exists(self):
        if self.exists_err is not None:
            raise self.exists_err
        return self._present

    def read_bytes(self):
        if self.read_err is not None:
            raise self.read_err
        return self.data

    def stat(self):
        return SimpleNamespace(st_mtime=self.mtime, st_size=len(self.data))

    def write_bytes(self, b):
        if self.write_err is not None:
            raise self.write_err
        self.written = b

    def write_text(self, t, encoding=None):
        self.written = t.encode("utf-8", "ignore")

    def __str__(self):
        return f"FakeLeaf({self.name})"


class FakeDir:
    def __init__(self, leaf, except_name="except.txt", dst_err=None):
        self.leaf, self.except_name, self.dst_err = leaf, except_name, dst_err

    def __truediv__(self, name):
        if name == self.except_name:
            return self.leaf
        if name.startswith("except_post_"):
            return FakeLeaf(name, present=True, write_err=self.dst_err)
        return FakeLeaf(name, present=False)


def run_copy(pre, src_leaf, label, dst_err=None):
    rec = Recorder()
    out = FakeDir(FakeLeaf("out", present=True), dst_err=dst_err)
    err, info = None, None
    try:
        info = copy_post(rec, FakeDir(src_leaf), out, pre_freshness_snapshot=pre)
    except Exception as exc:
        err = exc
    print(f"\n  --- {label} ---")
    res = "None(正常早退)" if (info is None and err is None) else (
        f"外抛 {type(err).__name__}: {err}" if err else "info dict(正常返回)")
    print(f"  copy_post 结果: {res}")
    if info is not None:
        print(f"  info.freshness_verdict={info['freshness_verdict']!r} "
              f"conf={info['freshness_confidence']!r} "
              f"pre_snapshot_state={info['pre_snapshot_state']!r}")
    err_rows = [(r["key"], str(r["value"])[:60]) for r in rec.rows
                if r["group"] == "ERROR"]
    fresh_rows = [(r["key"], r["value"]) for r in rec.rows
                  if r["group"] == "FRESHNESS"]
    print(f"  Recorder ERROR 行: {err_rows if err_rows else '无'}")
    print(f"  Recorder FRESHNESS verdict/conf/is_new: "
          f"{[(k, v) for k, v in fresh_rows if k in ('freshness_verdict', 'freshness_confidence', 'freshness_is_new')]}")
    lg = CLASSIFY_LOG[-1] if CLASSIFY_LOG else None
    if lg:
        print(f"  classify 实收: pre_is_None={lg['pre_is_None']} "
              f"pre_state={lg['pre_state_field']!r} "
              f"post_exists={lg['post_exists']} "
              f"post_read_error={str(lg['post_read_error'])[:44]!r} "
              f"→ verdict={lg['verdict']!r} conf={lg['confidence']!r}")
    return rec, info, err


run_copy(PRE_ABSENT,
         FakeLeaf("except.txt", present=True,
                  read_err=PermissionError("[Errno 13] 文件被占用(探针)")),
         "C1 O1主子格: pre=absent + src 在场但 read_bytes 被锁 PermissionError")
run_copy(PRE_ABSENT, FakeLeaf("except.txt", present=True),
         "C2 O1'子格: pre=absent + 读成功 + dst.write_bytes 失败(exists=True)",
         dst_err=OSError("[Errno 28] 磁盘满(探针)"))
run_copy(PRE_ABSENT,
         FakeLeaf("except.txt", present=True,
                  exists_err=OSError("[Errno 5] ACL 拒绝(探针)")),
         "C3 O1变体: src.exists() 自身抛异常")
run_copy(PRE_ABSENT, FakeLeaf("except.txt", present=False),
         "C4 对照组: pre=absent + 跑后无件 → src_missing 分支")
run_copy(PRE_ABSENT, FakeLeaf("except.txt", present=True),
         "C5 对照组: pre=absent + 跑后在 + 复制全成功 → new_first_appearance")

# ============ P5 W3：make_pre 在场必算 sha（实跑）+ fixture 域同抢格 ============
banner("P5 W3：make_pre 在场必算 sha 实跑 + fixture 同抢格")
p = PRE_PRESENT
print(f"  make_pre(真实在场文件) -> state={p['state']!r} sha256={p['sha256'][:16]}… "
      f"len(sha)={len(p['sha256'])} ⇒ 在场必带非空 64 位 sha")
d = PRE_ERROR
print(f"  make_pre(sha256 会炸的输入·Path(None)) -> state={d['state']!r} "
      f"error={d['error']!r} ⇒ sha 算炸 → 整体 error，绝不产出 present缺sha")
r_a = real_classify(PRE_PRESENT_NO_SHA, post_read_fail(None))
r_b = real_classify(PRE_PRESENT_NO_SHA, post_ok())
r_c = real_classify(PRE_PRESENT, post_read_fail(True))
print(f"  fixture present×缺pre.sha × read_error -> verdict={r_a['verdict']!r} "
      f"pre_state={r_a['pre_snapshot_state']!r} (:5 先截，:13 同抢落空)")
print(f"  fixture present×缺pre.sha × 跑后在·无read_error -> verdict={r_b['verdict']!r} "
      f"(:13 域内正确)")
print(f"  fixture present×带sha × read_error(exists=True) -> verdict={r_c['verdict']!r} "
      f"(:5 ✓)")

# ============ P6 O2：显式 unknown×跑后在 只能 fixture 直调 ============
banner("P6 O2：显式 unknown × 跑后在 —— classify 直调可构，实流不可产")
r_u = real_classify(PRE_EXPLICIT_UNKNOWN, post_ok())
print(f"  fixture 显式unknown × 跑后在 -> verdict={r_u['verdict']!r} "
      f"conf={r_u['confidence']!r} pre_state={r_u['pre_snapshot_state']!r}")
r_u2 = real_classify(PRE_EXPLICIT_UNKNOWN, post_missing_file())
print(f"  fixture 显式unknown × 跑后无件 -> verdict={r_u2['verdict']!r} (:3 ✓ 对照)")
r_n = real_classify(None, post_missing_file())
print(f"  fixture pre=None × 跑后无件  -> verdict={r_n['verdict']!r} (:2 ✓ 对照)")
print("  ⇒ make_pre 输出域(P4 实跑 states_seen)不含 'unknown'；"
      "实流 pre 只有两个写点 :6528(None) 与 :6623(make_pre 输出)（P0a4 实证）")

banner("P7 汇总")
print("  states_seen(make_pre 8 类输入实跑):", sorted(states_seen))
print("  classify 直调+经 copy_post 实跑总调用次数:", len(CLASSIFY_LOG))
print("PROBE_DONE")
