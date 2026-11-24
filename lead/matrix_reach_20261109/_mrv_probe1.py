# -*- coding: utf-8 -*-
"""_mrv_probe1.py — 可达性复核员独立实证探针（不采信撰写人输出，全部自建）。

纪律：零 exec（零代码注入）；零真机（不启动/不杀/不读活进程）；零采样；
零真实文件写（copy_post 用假对象逼异常，写全部落内存 sink；Recorder 已实读
候选:451-469 为纯内存 rows，唯一 I/O 方法 dump() 本探针不调用）。
装载副作用声明：候选:182 ctypes.windll.user32.SetProcessDPIAware()（探针进程
自身 DPI 声明，无文件系统、无外部进程操作）；其余顶层 Call 已由
_mrv_toplevel_scan.py 实跑枚举为纯构造（Path/os.environ.get/c_void_p/tuple/
range/frozenset/len/_qc213p2_ladder_effective），顶层 If :7532 恰为 __main__ 门。
"""
import ast
import hashlib
import importlib.util
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

CAND = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py")
EXPECT_SHA = "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
WD = Path(r"D:\Project\ra2-campaign-forge\lead\matrix_reach_20261109")


def banner(s):
    print("\n" + "=" * 76)
    print(s)
    print("=" * 76)


# ============ R0 绑定（fail-closed） ============
banner("R0 绑定")
raw = CAND.read_bytes()
sha_all = hashlib.sha256(raw).hexdigest()
print(f"[bind] candidate sha256 = {sha_all}")
print(f"[bind] candidate bytes  = {len(raw)}")
print(f"[bind] MATCH = {sha_all == EXPECT_SHA}")
assert sha_all == EXPECT_SHA, "candidate fingerprint drift — abort"
src = raw.decode("utf-8")
tree = ast.parse(src, filename=str(CAND))

# ============ R1 静态装载（护栏后） ============
banner("R1 静态装载 importlib（副作用仅候选:182 SetProcessDPIAware，已声明）")
spec = importlib.util.spec_from_file_location("mrv_candidate_probe", str(CAND))
mod = importlib.util.module_from_spec(spec)
sys.modules["mrv_candidate_probe"] = mod
spec.loader.exec_module(mod)
print("[load] ok:", mod.__name__)
print("[load] FRESHNESS_SNAPSHOT_STATES =", mod.FRESHNESS_SNAPSHOT_STATES)
print("[load] CARRIER_FILES =", mod.CARRIER_FILES)
make_pre = mod.make_pre_freshness_snapshot
classify = mod.classify_except_freshness
copy_post = mod.copy_post_except_evidence

# ============ R2 AST-A：make_pre 路径枚举（自建控制流证明） ============
banner("R2 AST-A：make_pre 全路径枚举——无返回路径保持初值 unknown；"
       "present 返回路径必经 sha256")


def event_of(stmt):
    """state/sha256 事件抽取：仅认 snap['state']=常量 / snap['sha256']=...。"""
    if isinstance(stmt, ast.Assign):
        for t in stmt.targets:
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "snap"
                    and isinstance(t.slice, ast.Constant)):
                key = t.slice.value
                if key == "state" and isinstance(stmt.value, ast.Constant):
                    return ("state", stmt.value.value, stmt.lineno)
                if key == "sha256":
                    return ("sha256", stmt.lineno)
    return None


def walk_stmts(stmts):
    """自建路径枚举器（对可行路径过近似 ⇒ 对「不存在路径」结论健全）。
    返回 [(events, closed)]；closed=该路径已命中 Return。"""
    paths = [([], False)]
    for st in stmts:
        out = []
        if isinstance(st, ast.Return):
            for ev, closed in paths:
                out.append((ev if closed else ev + [("return", st.lineno)], True))
        elif isinstance(st, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Import,
                             ast.ImportFrom, ast.AugAssign, ast.Pass)):
            e = event_of(st)
            for ev, closed in paths:
                out.append((ev + ([e] if (e and not closed) else []), closed))
        elif isinstance(st, ast.If):
            tp = walk_stmts(st.body)
            ep = walk_stmts(st.orelse) if st.orelse else [([], False)]
            for ev, closed in paths:
                if closed:
                    out.append((ev, closed))
                    continue
                for bev, bc in tp:
                    out.append((ev + bev, bc))
                for sev, sc in ep:
                    out.append((ev + sev, sc))
        elif isinstance(st, ast.Try):
            assert len(st.handlers) == 1 and not st.orelse and not st.finalbody
            hp = walk_stmts(st.handlers[0].body)
            bp = walk_stmts(st.body)
            for ev, closed in paths:
                if closed:
                    out.append((ev, closed))
                    continue
                for bev, bc in bp:
                    if bc:
                        out.append((ev + bev, True))      # try 体内 return
                    else:
                        out.append((ev + bev, False))     # try 体正常走完
                        for hev, hc in hp:                # 或任一点抛异常 → handler
                            assert not hc, "handler 内 return 未预期"
                            out.append((ev + hev, False))
        else:
            raise AssertionError("未覆盖语句类型 " + type(st).__name__)
        paths = out
    return paths


mp = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "make_pre_freshness_snapshot")
# 结构前置断言：body = [docstring, snap=..., Try(1 handler), return]
assert isinstance(mp.body[0], ast.Expr) and len(mp.body) == 4
try_stmt = mp.body[2]
ret_stmt = mp.body[3]
assert isinstance(try_stmt, ast.Try) and isinstance(ret_stmt, ast.Return)
init_assign = mp.body[1]
assert isinstance(init_assign, ast.Assign)
init_state = {k.value: v.value for k, v in
              zip(init_assign.value.keys, init_assign.value.values)
              if isinstance(k, ast.Constant)}["state"]
print(f"[struct] 初值赋值 @:{init_assign.lineno}  初始 state = {init_state!r}")

paths = walk_stmts([init_assign, try_stmt, ret_stmt])
# 规整：closed 路径取其 return 行号
closed_paths = []
for ev, c in paths:
    if not c:
        continue
    ret_ln = next(x[1] for x in reversed(ev) if x[0] == "return")
    closed_paths.append((ret_ln, ev))
print(f"[enum] 封闭路径总数 = {len(closed_paths)}")

by_ret = {}
bad_unknown = 0
present_no_sha = 0
for ret_ln, ev in closed_paths:
    states = [x for x in ev if x[0] == "state"]
    last = states[-1] if states else None
    by_ret.setdefault(ret_ln, set()).add(last[1] if last else "<无state事件>")
    if last is None or last[1] == init_state:
        bad_unknown += 1
    if last is not None and last[1] == "present":
        if not any(x[0] == "sha256" for x in ev):
            present_no_sha += 1
print(f"[proof] 各 return 行的终态取值域: {by_ret}")
print(f"[proof] 保持初值 {init_state!r} 返回的路径数 = {bad_unknown}（须为 0）")
print(f"[proof] 终态 present 但缺 sha256 事件的路径数 = {present_no_sha}（须为 0）")
assert bad_unknown == 0 and present_no_sha == 0
# handler 无条件置 error 的结构断言
hbody = try_stmt.handlers[0].body
assert not any(isinstance(s, ast.If) for s in hbody)
h_state = [event_of(s) for s in hbody if event_of(s)]
print(f"[proof] except handler 顶层 state 事件 = {h_state}（无条件 error）")

# ============ R3 AST-B：classify 顶层分支序 / copy_post 写点 / 全模块 pre 写点 ============
banner("R3 AST-B：classify 分支序 · read_error 写点 · pre 快照全模块写点")
cl = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "classify_except_freshness")
if_lines = [(s.lineno, ast.get_source_segment(src, s.test)) for s in cl.body
            if isinstance(s, ast.If)]
for ln, t in if_lines:
    print(f"  if @:{ln}  {t}")
ln_read_err = next(ln for ln, t in if_lines if 'read_error' in t)
ln_unknown = next(ln for ln, t in if_lines if t == 'st == "unknown"')
ln_error = next(ln for ln, t in if_lines if t == 'st == "error"')
ln_absent = next(ln for ln, t in if_lines if t == 'st == "absent_confirmed"')
ln_presha = next(ln for ln, t in if_lines if t == "not pre_sha")
print(f"[order] read_error@:{ln_read_err} < unknown@:{ln_unknown} "
      f"< error@:{ln_error} < not post_exists < absent_confirmed@:{ln_absent} "
      f"< 缺pre_sha@:{ln_presha}")
assert ln_read_err < ln_unknown < ln_error < ln_absent < ln_presha

cp = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
          and n.name == "copy_post_except_evidence")
re_writes, ex_writes = [], []
for node in ast.walk(cp):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "post_observed"
                    and isinstance(t.slice, ast.Constant)):
                (re_writes if t.slice.value == "read_error"
                 else ex_writes if t.slice.value == "exists"
                 else []).append((node.lineno,
                                  ast.get_source_segment(src, node)[:70]))
    if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "update"
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "post_observed"):
        ex_writes.append((node.lineno, "post_observed.update({...})"))
print(f"  read_error 写点: {re_writes}")
print(f"  exists 写点: {ex_writes}")
assert len(re_writes) == 1 and re_writes[0][0] == 4786

pre_writes, pre_field_writes = [], []
for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in tgts:
            if isinstance(t, ast.Name) and t.id in (
                    "_pre_freshness_snapshot", "pre_freshness_snapshot"):
                pre_writes.append((node.lineno, type(node).__name__))
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) \
                    and t.value.id in ("_pre_freshness_snapshot",
                                       "pre_freshness_snapshot"):
                pre_field_writes.append(node.lineno)
pre_writes = sorted(pre_writes)
print(f"  pre 快照变量写点: {pre_writes}")
print(f"  pre 快照字段级改写点: {pre_field_writes}")
assert pre_writes == [(6528, "AnnAssign"), (6623, "Assign")]
assert pre_field_writes == []

# ============ R4 运行期：make_pre 8 类输入 sweep（全只读） ============
banner("R4 make_pre sweep（8 类输入；含「在场但 sha 必炸」目录）")
targets = [
    ("present·候选本体(在场)", CAND),
    ("absent·写域不存在件", WD / "_mrv_no_such_target.bin"),
    ("absent·非法字符路径", str(WD / "_mrv_ill<*>egal.txt")),
    ("absent·ENOTDIR子路径", str(CAND / "_mrv_under.txt")),
    ("error·写域目录(sha必炸)", WD),
    ("error·None", None),
    ("error·整数3", 3),
    ("error·空串", ""),
]
states_seen = {}
snaps = {}
for label, t in targets:
    s = make_pre(t)
    snaps[label] = s
    states_seen.setdefault(s["state"], []).append(label)
    print(f"  [{label}] -> state={s['state']!r} exists={s['exists']} "
          f"error={(s['error'] or '')[:58]!r}")
print(f"  states_seen = { {k: len(v) for k, v in states_seen.items()} }")
print(f"  ★ 'unknown' in states_seen = {'unknown' in states_seen}（须 False）")
assert "unknown" not in states_seen
ps = snaps["present·候选本体(在场)"]
direct = hashlib.sha256(raw).hexdigest()
print(f"  交叉验证: make_pre(候选本体).sha256 == hashlib 直算 → {ps['sha256'] == direct}")
print(f"  present 件 sha 长度 = {len(ps['sha256'])}（64 位非空）")
assert ps["sha256"] == direct and len(ps["sha256"]) == 64
d = snaps["error·写域目录(sha必炸)"]
print(f"  目录(在场但不可哈希) → state={d['state']!r} error={d['error'][:52]!r}")
assert d["state"] == "error"

# ============ R5 运行期：classify 9×5 全格网格 ============
banner("R5 classify 9 pre × 5 post 全格（45 格实跑）")
PRE_ISO = "2026-11-09T00:00:00+08:00"
P_NONE = None
P_EMPTY = {}
P_NOSTATE = {"sha256": "x"}
P_DIRTY = {"state": "garbage"}
P_UNK = {"state": "unknown", "exists": None, "size": None, "sha256": None,
         "mtime_pre": None, "captured_at_epoch": None, "captured_at_iso": None,
         "error": None, "traceback": None, "source": "mrv-fixture"}
P_ABSENT = snaps["absent·写域不存在件"]
P_PRESENT = ps
P_PRES_NOSHA = dict(P_PRESENT, sha256=None)
P_ERROR = snaps["error·None"]


def T_re(exists):
    return {"exists": exists, "size": 18 if exists else None,
            "sha256": ("ab" * 32) if exists else None,
            "mtime_post": 1760000000.5 if exists else None,
            "captured_at_iso": PRE_ISO, "read_error": "PermissionError: 假锁(复核探针)"}


def T_full():
    return {"exists": True, "size": 18, "sha256": "cd" * 32,
            "mtime_post": 1760000000.5, "captured_at_iso": PRE_ISO,
            "read_error": None}


def T_gone():
    return {"exists": False, "size": None, "sha256": None, "mtime_post": None,
            "captured_at_iso": PRE_ISO, "read_error": None}


def T_nosha():
    d = T_full()
    d["sha256"] = None
    return d


PRE_LIST = [("None", P_NONE), ("{}", P_EMPTY), ("缺state", P_NOSTATE),
            ("脏值", P_DIRTY), ("显式unknown", P_UNK), ("absent_confirmed", P_ABSENT),
            ("present带sha", P_PRESENT), ("present缺pre.sha", P_PRES_NOSHA),
            ("error", P_ERROR)]
POST_LIST = [("re·ex=None", lambda: T_re(None)), ("re·ex=True", lambda: T_re(True)),
             ("跑后无件", T_gone), ("跑后在·全", T_full), ("跑后在·缺post.sha", T_nosha)]
grid = {}
for pname, p in PRE_LIST:
    for tname, tf in POST_LIST:
        r = classify(p, tf())
        grid[(pname, tname)] = (r["verdict"], r["confidence"], r["is_new"])
        print(f"  {pname:<14} × {tname:<14} -> {r['verdict']!r}/{r['confidence']!r}"
              f"/is_new={r['is_new']} pre_state={r['pre_snapshot_state']!r}")

re_cells = [k for k in grid if k[1].startswith("re·")]
assert all(grid[k][0] == "post_read_error" for k in re_cells), "read_error 格有非 PRE"
print(f"  ★ W1/W1'/O1/O1'/W2/W3-fixture：read_error 两型 × 9 pre = "
      f"{len(re_cells)} 格全部 post_read_error")
assert grid[("error", "跑后无件")] == ("error_pre_snapshot", "none", None)
assert grid[("absent_confirmed", "跑后无件")] == ("absent_both", "low", False)
assert grid[("absent_confirmed", "跑后在·全")] == ("new_first_appearance", "high", True)
assert grid[("显式unknown", "跑后在·全")][0] == "unknown"
assert grid[("None", "跑后在·全")][0] == "unknown"
assert grid[("present缺pre.sha", "跑后在·全")] == ("error_pre_snapshot", "none", None)
assert grid[("present缺pre.sha", "跑后在·缺post.sha")] == ("error_pre_snapshot", "none", None)
assert grid[("present带sha", "跑后在·缺post.sha")] == ("post_read_error", "none", None)
print("  ★ 断言全过：:4✓ :7✓ :6✓；显式unknown×跑后在=unknown（O2 仅 fixture）；"
        "None×跑后在=unknown（撰写人未测格，复核补测）；缺pre.sha 域内 :13✓")

# ============ R5b 运行期：LU/RW 出口 + usable 恒 False（writer 输出域补全） ============
banner("R5b classify 出口域补全：leftover/rewritten 四支 + usable 恒 False")
same_sha = P_PRESENT["sha256"]
cases = [
    ("mt 同", {"exists": True, "size": 18, "sha256": same_sha,
               "mtime_post": P_PRESENT["mtime_pre"], "captured_at_iso": PRE_ISO,
               "read_error": None}, ("leftover_unchanged", "high", False)),
    ("mt 侧缺", {"exists": True, "size": 18, "sha256": same_sha,
                 "mtime_post": None, "captured_at_iso": PRE_ISO,
                 "read_error": None}, ("leftover_unchanged", "medium", False)),
    ("mt 升", {"exists": True, "size": 18, "sha256": same_sha,
               "mtime_post": P_PRESENT["mtime_pre"] + 5.0,
               "captured_at_iso": PRE_ISO, "read_error": None},
     ("rewritten_same_content", "medium", True)),
    ("mt 降", {"exists": True, "size": 18, "sha256": same_sha,
               "mtime_post": P_PRESENT["mtime_pre"] - 5.0,
               "captured_at_iso": PRE_ISO, "read_error": None},
     ("rewritten_same_content", "low", True)),
]
for tag, post, want in cases:
    r = classify(P_PRESENT, post)
    got = (r["verdict"], r["confidence"], r["is_new"])
    print(f"  present带sha × {tag} -> {got}  (期望 {want}) usable={r['usable_as_crash_evidence']}")
    assert got == want, f"出口域不符: {tag}"
assert grid[("present带sha", "跑后在·全")] == ("new_write", "high", True)
# 45 格 + 4 格 usable 逐格核（重放 classify 取 usable 字段）
n_usable_false = 0
for pname, p in PRE_LIST:
    for tname, tf in POST_LIST:
        r = classify(p, tf())
        if r["usable_as_crash_evidence"] is False:
            n_usable_false += 1
for tag, post, _ in cases:
    if classify(P_PRESENT, post)["usable_as_crash_evidence"] is False:
        n_usable_false += 1
print(f"  usable_as_crash_evidence=False 计数 = {n_usable_false}/49（49=45+4，须全 False）")
assert n_usable_false == 49

# ============ R6 运行期：copy_post 假对象实跑（零真实文件写） ============
banner("R6 copy_post 假对象实跑 C1-C5（全部写入落内存 sink）")
CALL_LOG = []


class FakeLeaf:
    def __init__(self, name, present=True, exists_err=None, read_err=None,
                 write_err=None, data=b"NEW-CRASH-BYTES", fspath=None):
        self.name = name
        self._present = present
        self._err = {"exists": exists_err, "read": read_err, "write": write_err}
        self.data = data
        self._fspath = fspath
        self.sink = []

    def _log(self, m):
        CALL_LOG.append((self.name, m))

    def __fspath__(self):
        return self._fspath if self._fspath else f"<FakeLeaf:{self.name}>"

    def exists(self):
        self._log("exists")
        if self._err["exists"] is not None:
            raise self._err["exists"]
        return self._present

    def read_bytes(self):
        self._log("read_bytes")
        if self._err["read"] is not None:
            raise self._err["read"]
        return self.data

    def stat(self):
        self._log("stat")
        return SimpleNamespace(st_size=len(self.data), st_mtime=1760000000.5)

    def write_bytes(self, b):
        self._log("write_bytes")
        if self._err["write"] is not None:
            raise self._err["write"]
        self.sink.append(("write_bytes", b))

    def write_text(self, t, encoding=None):
        self._log("write_text")
        self.sink.append(("write_text", t))

    def __str__(self):
        return f"FakeLeaf({self.name})"


class FakeDir:
    def __init__(self, except_leaf, fspath_leaf=None):
        self.except_leaf = except_leaf
        self.fspath_leaf = fspath_leaf

    def __truediv__(self, name):
        if name == "except.txt":
            return self.except_leaf
        if name.startswith("except_post_"):
            return FakeLeaf(name)
        if self.fspath_leaf is not None:
            return self.fspath_leaf
        return FakeLeaf(name, present=False)


def run_copy(pre, leaf, label, outdir=None):
    rec = mod.Recorder()
    out = outdir if outdir is not None else FakeDir(FakeLeaf("out"))
    info, err = None, None
    try:
        info = copy_post(rec, FakeDir(leaf), out, pre_freshness_snapshot=pre)
    except Exception as exc:
        err = exc
    print(f"\n  --- {label} ---")
    print(f"  返回: {'外抛 ' + type(err).__name__ + ': ' + str(err) if err else ('None(早退)' if info is None else 'info dict')}")
    if info is not None:
        print(f"  info.freshness_verdict={info['freshness_verdict']!r} "
              f"conf={info['freshness_confidence']!r} "
              f"pre_state={info['pre_snapshot_state']!r}")
    err_rows = [r["key"] for r in rec.rows if r["group"] == "ERROR"]
    fresh = {r["key"]: r["value"] for r in rec.rows if r["group"] == "FRESHNESS"}
    print(f"  ERROR 行数={len(err_rows)} keys={err_rows}")
    print(f"  FRESHNESS verdict={fresh.get('freshness_verdict')!r} "
          f"conf={fresh.get('freshness_confidence')!r} "
          f"is_new={fresh.get('freshness_is_new')}")
    return rec, info, err, fresh


# C5 特制：src 与 CARRIER_FILES 叶给真实只读 fspath → :4820-4821 走真实只读
fspath_leaf = FakeLeaf("carrier", present=False, fspath=str(CAND))
src_ok = FakeLeaf("except.txt", present=True, data=b"NEW-CRASH-BYTES",
                  fspath=str(CAND))
rec5, info5, err5, fresh5 = run_copy(
    P_ABSENT, src_ok, "C5 对照: 全成功整链（含 :4816-4825 尾段）",
    outdir=FakeDir(FakeLeaf("out"), fspath_leaf=fspath_leaf))
assert err5 is None and info5 is not None
assert info5["freshness_verdict"] == "new_first_appearance"
assert fresh5["freshness_verdict"] == "new_first_appearance"
print("  ★ C5 整链跑完（撰写人 C5 在 :4821 因脚手架 TypeError 截断；本探针以"
      " __fspath__ 指向只读真实文件走完全函数，无异常，结论一致：NFA/high/True）")

src_locked = FakeLeaf("except.txt", present=True,
                      read_err=PermissionError("[Errno 13] 句柄被占(复核探针)"))
run_copy(P_ABSENT, src_locked, "C1 O1主子格: absent + 读锁 PermissionError")
src_wfail = FakeLeaf("except.txt", present=True)
rec2, info2, err2, fresh2 = None, None, None, None
rec2 = mod.Recorder()
out2 = FakeDir(FakeLeaf("out"))
# C2 需 dst 写失败：临时换 out 的 except_post_ 叶
class FakeDirW(FakeDir):
    def __truediv__(self, name):
        if name.startswith("except_post_"):
            return FakeLeaf(name, write_err=OSError("[Errno 28] 磁盘满(复核探针)"))
        return FakeDir.__truediv__(self, name)


try:
    copy_post(rec2, FakeDir(src_wfail), FakeDirW(FakeLeaf("out")),
              pre_freshness_snapshot=P_ABSENT)
except Exception as exc:
    err2 = exc
f2 = {r["key"]: r["value"] for r in rec2.rows if r["group"] == "FRESHNESS"}
print(f"\n  --- C2 O1'子格: 读成功 + dst.write_bytes 磁盘满 ---")
print(f"  外抛 {type(err2).__name__}: {err2} | FRESHNESS={f2.get('freshness_verdict')!r}"
      f"/{f2.get('freshness_confidence')!r}")
assert type(err2) is OSError and f2["freshness_verdict"] == "post_read_error"

src_acl = FakeLeaf("except.txt", present=True,
                   exists_err=OSError("[Errno 5] ACL 拒绝(复核探针)"))
run_copy(P_ABSENT, src_acl, "C3 O1变体: src.exists() 自身炸")
run_copy(P_ABSENT, FakeLeaf("except.txt", present=False),
         "C4 对照: absent + 跑后无件 → src_missing")

# pre=None × 复制失败（W1 组合半场：copy_post 对 pre 无守卫）
rec_w1 = mod.Recorder()
err_w1 = None
try:
    copy_post(rec_w1, FakeDir(src_locked), FakeDir(FakeLeaf("out")),
              pre_freshness_snapshot=None)
except Exception as exc:
    err_w1 = exc
f_w1 = {r["key"]: r["value"] for r in rec_w1.rows if r["group"] == "FRESHNESS"}
print(f"\n  --- W1 组合: pre=None(实流 :6528 态) × C1 读锁 ---")
print(f"  外抛 {type(err_w1).__name__} | FRESHNESS={f_w1.get('freshness_verdict')!r}")
assert type(err_w1) is PermissionError
assert f_w1["freshness_verdict"] == "post_read_error"

# Recorder 纯内存证据 + 零真实写证据
rsrc = inspect.getsource(mod.Recorder.__init__) + inspect.getsource(mod.Recorder.add)
assert "open(" not in rsrc and "write" not in rsrc
print(f"\n  Recorder.__init__/add 无 open/write（inspect 源码核）→ 内存态")
writes = [c for c in CALL_LOG if c[1] in ("write_bytes", "write_text")]
print(f"  假对象写入调用 {len(writes)} 次全部落内存 sink（CALL_LOG 可查）；"
      f"本探针除 stdout 外零文件写")
print(f"  CALL_LOG 总数={len(CALL_LOG)}")

# ============ R7 汇总 ============
banner("R7 汇总")
print("  [O2 不可达三重] ①路径枚举 0 路径保持 unknown；②运行期 8 类输入无 unknown；"
      "③pre 写点仅 :6528/:6623 且无字段级改写 → 实流 pre ∈ {None, make_pre 三态}")
print("  [W3 不可达三重] ①present 终态路径 100% 含 :4607 sha 事件；②在场不可哈希"
      "（目录）→ 整体 error 而非 present缺sha；③写点封闭无人清 sha")
print("  [W1] read_error 18 格全 PRE；pre=None×read_error 经 copy_post 实跑落地；"
      "实流收窄 = (None × read_error)")
print("  [W2] error×read_error → PRE（真 make_pre error 件 + 假对象 read_error）；"
      "error×无件 → EPS 对照")
print("  [O1] C1/C2/C3 经 copy_post 实跑全产 read_error → PRE；C4/C5 对照 :7/:6 ✓")
print("PROBE_DONE")
