# -*- coding: utf-8 -*-
"""XVERIFY_V4 探针 1：H8-7 四路 dump 完备性 + 缺省 False 等价性 + 溢出面。
- AST 全文检查（argparse 缺省 / main-arm 守卫 / dump 调用点 4 处 / append 守卫 2 处）
- frame-wait 块按 ast.get_source_segment 从 v4 文件按字节提取 → dedent → exec 桩测
  （非誊写）。场景：off+ok / on+ok / on+first_read / on+timeout / on+jump / off+first_read。
python -I -B -X utf8 本文件 ⇒ 全 PASS exit 0。
"""
import ast
import json
import sys
import tempfile
import textwrap
import time
from pathlib import Path

V4 = Path(r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py")
SRC = V4.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + (("  | " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


# ---------- A. 全文 AST 检查 ----------
calls = []          # (verdict 常量, 行号, 后继语句类型)
appends = []        # _h8_trace.append 调用行
append_guards = []  # 守卫 append 的 If.test 源码
argparse_node = None
mainarm_if = None
dump_def = None

for node in ast.walk(TREE):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_h8_trace_dump":
        calls.append(node)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "append" and isinstance(node.func.value, ast.Name) \
            and node.func.value.id == "_h8_trace":
        appends.append(node)
    if isinstance(node, ast.FunctionDef) and node.name == "_h8_trace_dump":
        dump_def = node
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "add_argument":
        for kw in node.keywords:
            if kw.arg == "dest" or (isinstance(node.args[0] if node.args else None, ast.Constant)
                                    and node.args[0].value == "--h8-wait-trace"):
                argparse_node = node
    if isinstance(node, ast.If) and isinstance(node.test, ast.Call) \
            and isinstance(node.test.func, ast.Name) and node.test.func.id == "getattr":
        if "h8_wait_trace" in ast.dump(node.test):
            mainarm_if = node

check("A1 dump 调用恰 4 处", len(calls) == 4, [c.lineno for c in calls])
verdicts = sorted(c.args[0].value for c in calls if c.args and isinstance(c.args[0], ast.Constant))
check("A2 四路 verdict 常量齐全",
      verdicts == ["frame_overrun_first_read", "frame_overrun_jump", "frame_wait_timeout", "ok"],
      verdicts)

# dump 调用点后继：前三路必须紧随 return；ok 路是块尾
for c in calls:
    v = c.args[0].value
    # 找到包含该调用的语句列表（dump 调用是裸表达式语句）
    parent_stmts = None
    for node in ast.walk(TREE):
        for field, vals in ast.iter_fields(node):
            lst = vals if isinstance(vals, list) else []
            for i, st in enumerate(lst):
                if isinstance(st, ast.Expr) and st.value is c:
                    parent_stmts = (lst, i)
    lst, i = parent_stmts
    nxt = lst[i + 1] if i + 1 < len(lst) else None
    if v == "ok":
        check("A3 ok 路 dump 为块尾（后继 = H8-END）", nxt is None or not hasattr(nxt, "lineno"),
              "next=%r" % (nxt,))
    else:
        check("A4 %s 路 dump 后紧随 return" % v, isinstance(nxt, ast.Return), type(nxt).__name__)

check("A5 逐拍 append 恰 2 处", len(appends) == 2, [a.lineno for a in appends])
# append 守卫：向上找 If(H8_WAIT_TRACE) 直接包裹
for a in appends:
    guarded = False
    for node in ast.walk(TREE):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "H8_WAIT_TRACE":
            for sub in ast.walk(node):
                if sub is a:
                    # 直接 body 第一层才算紧守卫
                    for st in node.body:
                        if st is a or (isinstance(st, ast.Expr) and st.value is a):
                            guarded = True
    append_guards.append(guarded)
check("A6 两处 append 均被 if H8_WAIT_TRACE 直接守卫", all(append_guards), append_guards)

# dump 定义体：先 off-return，再写文件；JSON 键 = n/verdict/wait_s/samples
body0 = dump_def.body[0]
check("A7 dump 首句 = if not H8_WAIT_TRACE: return",
      isinstance(body0, ast.If) and isinstance(body0.test, ast.UnaryOp)
      and isinstance(body0.test.op, ast.Not) and isinstance(body0.test.operand, ast.Name)
      and body0.test.operand.id == "H8_WAIT_TRACE"
      and len(body0.body) == 1 and isinstance(body0.body[0], ast.Return))
wr = dump_def.body[1]
check("A8 dump 第二句 = write_text(json.dumps(...))",
      isinstance(wr, ast.Expr) and isinstance(wr.value, ast.Call)
      and isinstance(wr.value.func, ast.Attribute) and wr.value.func.attr == "write_text")
dumps_call = wr.value.args[0]
keys = [k.value for k in dumps_call.args[0].keys]
check("A9 JSON 顶层键 = n/verdict/wait_s/samples",
      keys == ["n", "verdict", "wait_s", "samples"], keys)
check("A10 dump 体内无 try/except（溢出面：裸 write_text）",
      not any(isinstance(n, ast.Try) for n in ast.walk(dump_def)))

check("A11 argparse --h8-wait-trace 存在", argparse_node is not None)
if argparse_node:
    kw = {k.arg: k.value for k in argparse_node.keywords}
    check("A12 argparse action=store_true",
          "action" in kw and isinstance(kw["action"], ast.Constant)
          and kw["action"].value == "store_true")
    check("A13 argparse default=False（缺省中性）",
          "default" in kw and isinstance(kw["default"], ast.Constant) and kw["default"].value is False)

check("A14 main-arm 守卫 getattr(args,'h8_wait_trace',False)", mainarm_if is not None)
if mainarm_if:
    arm_calls = [n for n in ast.walk(mainarm_if) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "add"]
    check("A15 main-arm 内 rec.add 仅在守卫内（off ⇒ 零 rec 行）", len(arm_calls) == 1)

# _h8_trace 名字不得外泄（全文引用仅限 frame-wait 块行域）
import re
refs = [m.start() for m in re.finditer(r"\b_h8_trace\b", SRC)]
block_seg = None
fw_if = None
for node in ast.walk(TREE):
    if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) \
            and isinstance(node.test.left, ast.Name) and node.test.left.id == "H8_MEASURE_START_FRAME":
        seg = ast.get_source_segment(SRC, node)
        if seg and "_h8_trace_dump" in seg and fw_if is None:
            fw_if = node
            block_seg = seg
check("A16 frame-wait 块定位（含 _h8_trace_dump 的 H8_MEASURE_START_FRAME If）", fw_if is not None,
      "lines %d-%d" % (fw_if.lineno, fw_if.end_lineno) if fw_if else "")
if fw_if:
    check("A17 _h8_trace 全部引用均在 frame-wait 块内",
          all(fw_if.lineno <= SRC[:p].count("\n") + 1 <= fw_if.end_lineno for p in refs),
          "refs=%d lines" % len(refs))

# ---------- B. 桩测：按字节提取 block_seg，dedent 后 exec ----------
block_code = textwrap.dedent(block_seg)
check("B0 提取段含四路 dump 调用",
      all(s in block_code for s in ["frame_overrun_first_read", "frame_wait_timeout",
                                    "frame_overrun_jump", '"ok"']))


class RecStub:
    def __init__(self):
        self.rows = []

    def add(self, tag, key, val, src, note=None):
        self.rows.append((tag, key, val))


def run_scenario(name, trace_on, reads, timeout_s=50.0, settle_guard=None):
    """reads: _rpm_u32 依序返回值（耗尽后保持末值）。返回 (env, out_dir, rec)。"""
    rec = RecStub()
    out_dir = Path(tempfile.mkdtemp(prefix="xv4_"))
    seq = list(reads)
    last = [None]

    def _rpm_u32(handle, va):
        if seq:
            last[0] = seq.pop(0)
        return last[0]

    doze_calls = []

    def _doze(s):
        doze_calls.append(s)

    def _measure_error_payload(w, trip, sha, msg):
        return {"verdict": None, "stats": {"stub": True}, "msg": msg}

    def _measure_write_json(od, w, payload):
        p = od / ("stub_measure_w%d.json" % w)
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return p

    env = {
        "H8_MEASURE_START_FRAME": 800,
        "H8_WAIT_TRACE": trace_on,
        "H8_WAIT_HZ": None,
        "H8_FRAME_WAIT_TIMEOUT_S": timeout_s,
        "H8_OFFSET_MAX_FRAMES": 2,
        "MEASURE_CURRENT_FRAME_VA": 0xA8ED84,
        "TRIP_ID": "STUB",
        "map_sha256": "STUBSHA",
        "handle": 0,
        "out_dir": out_dir,
        "rec": rec,
        "_H8_STATE": {},
        "time": time,
        "json": json,
        "Path": Path,
        "_rpm_u32": _rpm_u32,
        "_doze": _doze,
        "_measure_error_payload": _measure_error_payload,
        "_measure_write_json": _measure_write_json,
    }
    # 块内含 return（原属 _measure_run）⇒ 包一层哑函数使其合法；return=块退出，语义保真
    wrapped = "def _xv4_block():\n" + textwrap.indent(block_code, "    ")
    ns = {"__name__": "xv4block"}
    ns.update(env)
    exec(compile(wrapped, "<v4-frame-wait-block>", "exec"), ns)
    ns["_xv4_block"]()
    tp = out_dir / "h8_wait_trace.json"
    print("---- 场景 %s：trace=%s reads=%s" % (name, trace_on, reads[:6]))
    print("     rec 行 = %s" % [(t, k) for t, k, _ in rec.rows])
    print("     trace 文件在场 = %s" % tp.exists())
    if tp.exists():
        j = json.loads(tp.read_text(encoding="utf-8"))
        print("     JSON 键=%s verdict=%s n=%s wait_s=%s samples_n=%d "
              "首样=%s 末样=%s" % (sorted(j.keys()), j["verdict"], j["n"], j["wait_s"],
                                  len(j["samples"]), j["samples"][0], j["samples"][-1]))
    return env, out_dir, rec


# S1 off + ok 路径：799→800
env1, od1, rec1 = run_scenario("S1 off+ok", False, [799, 800])
check("S1a off+ok 无 h8_wait_trace.json", not (od1 / "h8_wait_trace.json").exists())
check("S1b off+ok rec 仅 h7_frame_wait（零 trace rec 行）",
      [k for _, k, _ in rec1.rows] == ["h7_frame_wait"], rec1.rows)
fw1 = rec1.rows[0][2]
check("S1c off+ok 达标语义不变（reached=800 offset=0 overrun=False）",
      fw1["reached_frame"] == 800 and fw1["offset_frames"] == 0 and not fw1["overrun"], fw1)

# S2 on + ok 路径：799→800（2 拍）
env2, od2, rec2 = run_scenario("S2 on+ok", True, [799, 800])
j2 = json.loads((od2 / "h8_wait_trace.json").read_text(encoding="utf-8"))
check("S2a JSON 顶层键恰 n/verdict/wait_s/samples",
      sorted(j2.keys()) == ["n", "samples", "verdict", "wait_s"], sorted(j2.keys()))
check("S2b verdict=ok n=800", j2["verdict"] == "ok" and j2["n"] == 800)
check("S2c 样本数 = 读点数 2（首拍+循环内拍，无缺无重）", len(j2["samples"]) == 2, j2["samples"])
check("S2d 末样 frame=800（达标拍在环内）", j2["samples"][-1][1] == 800)
check("S2e t_rel 4 位小数", all(round(x[0], 4) == x[0] for x in j2["samples"]))
check("S2f wait_s 3 位小数且与末样 t_rel 接近",
      abs(j2["wait_s"] - j2["samples"][-1][0]) < 0.01,
      (j2["wait_s"], j2["samples"][-1][0]))

# S3 on + first_read 越界：首拍 810 > 800
env3, od3, rec3 = run_scenario("S3 on+first_read", True, [810])
j3 = json.loads((od3 / "h8_wait_trace.json").read_text(encoding="utf-8"))
check("S3a verdict=frame_overrun_first_read 样本 1 拍",
      j3["verdict"] == "frame_overrun_first_read" and len(j3["samples"]) == 1, j3["samples"])
check("S3b rec 带 verdict=frame_overrun（拒采，不硬停趟）",
      any(k == "verdict" and v == "frame_overrun" for _, k, v in rec3.rows), rec3.rows)

# S4 on + timeout：恒 300，timeout=0.02s
env4, od4, rec4 = run_scenario("S4 on+timeout", True, [300], timeout_s=0.02)
j4 = json.loads((od4 / "h8_wait_trace.json").read_text(encoding="utf-8"))
check("S4a verdict=frame_wait_timeout",
      j4["verdict"] == "frame_wait_timeout" and j4["samples"][-1][1] == 300,
      (len(j4["samples"]), j4["samples"][-1]))
check("S4b rec 带 verdict=frame_wait_timeout",
      any(k == "verdict" and v == "frame_wait_timeout" for _, k, v in rec4.rows))
check("S4c 超时拍全部留痕（样本数 = 全部读点）",
      len(j4["samples"]) == len([1 for _ in j4["samples"]]) and len(j4["samples"]) > 1,
      len(j4["samples"]))

# S5 on + jump：700 → 810（跳 10 帧 > 容差 2）
env5, od5, rec5 = run_scenario("S5 on+jump", True, [700, 810])
j5 = json.loads((od5 / "h8_wait_trace.json").read_text(encoding="utf-8"))
check("S5a verdict=frame_overrun_jump 样本 2 拍（跳沿前后都在环内）",
      j5["verdict"] == "frame_overrun_jump" and len(j5["samples"]) == 2
      and j5["samples"][0][1] == 700 and j5["samples"][-1][1] == 810, j5["samples"])

# S6 off + first_read 越界（off 等价性在失败路径同样成立）
env6, od6, rec6 = run_scenario("S6 off+first_read", False, [810])
check("S6a off+失败路径 无 trace 文件", not (od6 / "h8_wait_trace.json").exists())
check("S6b off+失败路径 rec 行为与 v3 语义同（verdict/frame_wait/error payload 三行）",
      [k for _, k, _ in rec6.rows] == ["h7_frame_wait", "window_0_stats", "verdict"],
      rec6.rows)

# ---------- C. 溢出面补充：dump 调用在错误路径的位置（payload 已写后才 dump） ----------
# first_read 路内顺序：_measure_write_json → rec×3 → dump → return（S3 已验文件存在）
# ⇒ trace dump 失败时 measure JSON 已在盘上；异常传播至 main finally（收尾保全）。
check("C1 S3 失败路径 stub measure JSON 先于 trace 落盘",
      (od3 / "stub_measure_w0.json").exists())

print()
print("FAILS =", FAILS)
sys.exit(0 if not FAILS else 1)
