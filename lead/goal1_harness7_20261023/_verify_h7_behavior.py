#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H7 行为验证（离线、零真机、零动态执行）。

★ 纪律：**不 import / 不 exec / 不 compile 动态源码**。
  只 `ast.parse` 读 harness7 的真实结构，把**取值**（常量、赋值右值、
  比较运算符）从真实文件里取出来，再用普通 Python 算术求值。
  ⇒ 变异发生在**真实产物**上，判据也读**真实产物**，两者不是同一份手抄。

四项实验
--------
E1  全屏 + 短路 on  ⇒ 采帧前等待轮数 = 0
E2  全屏 + 短路 off（--h7-keep-rect-wait）⇒ 跑满 deadline（母本语义）
E3  窗口模式（矩形已 800×600）⇒ 轮数 0（与短路无关）
E4  late-start 闸：nav→measure 超限 ⇒ late_start=True；正常值 ⇒ False

变异测试（★ 每条取值证明必须能被"改坏被测物"杀掉）
M1  `deadline = 0.0` → `deadline = deadline`（短路失效）⇒ E1 必红
M2  闸值 90.0 → 1e9（闸失效）⇒ E4-late 必红
M3  `>` → `>=` 并喂等值 ⇒ 边界判据可杀
"""
import ast
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H7 = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"

FRAME_W, FRAME_H = 800, 600
DEADLINE_ORIG = 125.0      # 实测 stage_seconds:frame 量级（母本 deadline 余量）
POLL_S = 0.5

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# AST 取值层
# ---------------------------------------------------------------------------
def parse(src):
    return ast.parse(src)


def const_assign(tree, name):
    """取模块级 `name = <literal>` 的右值；取不到 ⇒ None。"""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return None
    return None


def _is_state_subscript(node, key):
    """`_H7_STATE["<key>"]` 形态。"""
    return (isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "_H7_STATE"
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == key)


def find_if_by_state(tree, key):
    """找 `if _H7_STATE["<key>"]:` 的 If 节点。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_state_subscript(node.test, key):
            return node
    return None


def deadline_assigned_value(tree):
    """在 `if _H7_STATE["fs_rect_wait_skipped"]:` 体内找 `deadline = <expr>`。

    ★ 返回：
      - `("const", 0.0)` —— 右值是字面量（正常产物）
      - `("alias", None)` —— 右值是 `deadline` 自身（M1 变异形态）
      - `("missing", None)` —— 没有该赋值（短路块被删）
    """
    ifn = find_if_by_state(tree, "fs_rect_wait_skipped")
    if ifn is None:
        return ("missing", None)
    for node in ast.walk(ifn):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "deadline":
                    v = node.value
                    if isinstance(v, ast.Name) and v.id == "deadline":
                        return ("alias", None)
                    try:
                        return ("const", ast.literal_eval(v))
                    except Exception:
                        return ("expr", None)
    return ("missing", None)


def find_while_rect_wait(tree):
    """找采帧前那个 while：`(...) != (FRAME_W, FRAME_H) and time.monotonic() < deadline`。"""
    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        t = node.test
        if not isinstance(t, ast.BoolOp) or not isinstance(t.op, ast.And):
            continue
        if len(t.values) != 2:
            continue
        left, right = t.values
        # 左：Tuple != Tuple
        if not (isinstance(left, ast.Compare) and len(left.ops) == 1
                and isinstance(left.ops[0], ast.NotEq)):
            continue
        if not (isinstance(left.left, ast.Tuple)
                and isinstance(left.comparators[0], ast.Tuple)):
            continue
        # 右：time.monotonic() < deadline
        if not (isinstance(right, ast.Compare) and len(right.ops) == 1
                and isinstance(right.ops[0], ast.Lt)):
            continue
        if not (isinstance(right.comparators[0], ast.Name)
                and right.comparators[0].id == "deadline"):
            continue
        return node
    return None


def late_gate_compare(tree):
    """找 late-start 闸的比较 `_h7_n2m <op> H7_MEASURE_MAX_NAV_TO_W0_S`。

    ★ 返回 (op_name, limit_from_const_ref)；op_name ∈ {"Gt","GtE","Lt","LtE"}。
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        left = node.left
        right = node.comparators[0]
        if not (isinstance(left, ast.Name) and left.id == "_h7_n2m"):
            continue
        if not (isinstance(right, ast.Name)
                and right.id == "H7_MEASURE_MAX_NAV_TO_W0_S"):
            continue
        return (type(node.ops[0]).__name__, True)
    return (None, False)


def late_gate_guard(tree):
    """取 late-start 闸的**启用条件**：两个合取项。

    ★ 返回 (has_nav_end_check, has_skip_check)：
      - has_nav_end_check：条件里出现 `_h7_nav_end` 非空判定
      - has_skip_check ：条件里出现 `_H7_STATE["fs_rect_wait_skipped"]`
    ★ 两者缺一即为设计缺陷（后者缺失正是 2026-10-23 自查抓到的那条：
      无条件施加会把 10-21 四趟成功趟一律误判）。
    """
    # 找 `if _h7_nav_end is not None and _H7_STATE["fs_rect_wait_skipped"]:` 形态
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        src = ast.dump(node.test)
        if "_h7_nav_end" in src:
            return ("_h7_nav_end" in src, "fs_rect_wait_skipped" in src)
    return (False, False)


def _is_not_none_check(node, name):
    """`<name> is not None` 形态。"""
    return (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.ops[0], ast.IsNot)
            and isinstance(node.left, ast.Name) and node.left.id == name
            and isinstance(node.comparators[0], ast.Constant)
            and node.comparators[0].value is None)


def gate_polarity(tree):
    """判定 late-start 闸两个合取项的**极性**（不只判存在）。

    ★ 返回 dict：
      - `nav_end_ok`  ：含 `_h7_nav_end is not None`（正向；反相成 `is None` ⇒ False）
      - `skip_ok`     ：含 `_H7_STATE["fs_rect_wait_skipped"]` 且**不是** `not ...`
      - `conjunction` ：两个合取项用 `and` 连接（不是 `or`）
    ★ 这是对「只判子串存在」那版判据的补强：反相（`not`）或换成 `or`
      都必须在 E0g/E0h 上红。
      ★ 残留边界（如实登记）：本判据读**首个**含 `_h7_nav_end` 的 If；
        若有人再插入一个诱饵 If 且其 ast.walk 序更靠前，仍可能遮蔽真闸。
        补这道口子的办法是「按 lineno 取最靠后/最靠前的真实闸」，
        但那要求已知闸的相对位置——见 E0i 的**顺序断言**（更硬的补丁）。
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        src = ast.dump(node.test)
        if "_h7_nav_end" not in src:
            continue
        vals = node.test.values if isinstance(node.test, ast.BoolOp) else []
        nav_ok = any(_is_not_none_check(v, "_h7_nav_end") for v in vals)
        skip_ok = False
        for v in vals:
            # 必须是「裸」的 _H7_STATE["fs_rect_wait_skipped"]，不能包在 not 里
            if _is_state_subscript(v, "fs_rect_wait_skipped"):
                skip_ok = True
        conj = isinstance(node.test, ast.BoolOp) and isinstance(node.test.op, ast.And)
        return {"nav_end_ok": nav_ok, "skip_ok": skip_ok, "conjunction": conj}
    return {"nav_end_ok": False, "skip_ok": False, "conjunction": False}


def source_order_ok(tree):
    """断言「短路块」在源文件里位于「母本 while」**之前**（行号级）。

    ★★ 这条是补 H7 盲验抓出的 medium 缺陷（裁决 #10）：
      旧版只用 ast.walk 判两个节点**存在**，不判先后。把 rect-wait-skip 块
      整体搬到 while 之后，短路在运行时永不生效（deadline 重绑晚于循环跑满），
      但所有基于"存在性"的判据照常绿（实测 22/22 PASS 骗过整套件）。
      ⇒ 必须用 lineno 硬断言顺序。
    ★ 返回 (ok, detail)：
      - skip_lineno：`if _H7_STATE["fs_rect_wait_skipped"]:` 的行号
      - while_lineno：母本 while 的行号
      - deadline_lineno：`deadline = 0.0` 的行号（必须夹在上面两者之间）
    """
    ifn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_state_subscript(
                node.test, "fs_rect_wait_skipped"):
            if ifn is None or node.lineno < ifn.lineno:
                ifn = node
    wh = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        t = node.test
        if not (isinstance(t, ast.BoolOp) and isinstance(t.op, ast.And)
                and len(t.values) == 2):
            continue
        right = t.values[1]
        if (isinstance(right, ast.Compare)
                and isinstance(right.comparators[0], ast.Name)
                and right.comparators[0].id == "deadline"):
            wh = node
            break
    dl = None
    if ifn is not None:
        for node in ast.walk(ifn):
            if isinstance(node, ast.Assign):
                for tg in node.targets:
                    if isinstance(tg, ast.Name) and tg.id == "deadline":
                        try:
                            if ast.literal_eval(node.value) == 0.0:
                                dl = node
                        except Exception:
                            pass
    if ifn is None or wh is None:
        return (False, {"skip": None, "while": None, "deadline": None})
    detail = {"skip": ifn.lineno, "while": wh.lineno,
              "deadline": dl.lineno if dl is not None else None}
    ok = (ifn.lineno < wh.lineno
          and dl is not None
          and ifn.lineno <= dl.lineno < wh.lineno)
    return (ok, detail)


def arming_polarity(tree):
    """取 `--h7-keep-rect-wait` 的**武装极性**（H7 盲验裁决 #12 的 medium 缺陷）。

    ★ 真实产物：`if not getattr(args, "h7_keep_rect_wait", False):`
      ⇒ 没给 opt-out ⇒ 武装短路。这是缺省方向的核心语义。
    ★ 旧版验证器从不读这一行，把武装方向整体反转后所有判据照常绿。
    ★ 返回 "not_getattr"（正确）/ "getattr"（反转）/ None（找不到）。
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        # 体内须有 _H7_STATE["fs_rect_wait_skipped"] = True
        has_arm = False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign):
                for tg in sub.targets:
                    if _is_state_subscript(tg, "fs_rect_wait_skipped"):
                        try:
                            if ast.literal_eval(sub.value) is True:
                                has_arm = True
                        except Exception:
                            pass
        if not has_arm:
            continue
        src = ast.dump(node.test)
        if "h7_keep_rect_wait" not in src:
            continue
        if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            return "not_getattr"
        return "getattr"
    return None


# ---------------------------------------------------------------------------
# 模型求值层（普通算术；参数全部来自 AST）
# ---------------------------------------------------------------------------
def model_rect_wait(deadline_kind, deadline_val, skip_on, rect_wh,
                    deadline_orig=DEADLINE_ORIG):
    """复算采帧前等待的**轮数**。

    ★ 谓词 = `rect != (800,600) AND monotonic < deadline`
      （AST 已断言结构确为这两个合取项，见 E0）。
    ★ 母本 `deadline = time.monotonic() + STAGE_TIMEOUT_S`（`:7553`）⇒ 它是
      **绝对时刻**，不是余量；此处同构：`t0 = 1000.0`，`deadline_abs = t0 + 余量`。
    ★ 每轮 +0.5（与母本 `time.sleep(0.5)` 同）。
    """
    t0 = 1000.0
    t = t0
    if skip_on:
        if deadline_kind == "const":
            deadline = deadline_val           # 正常产物：字面量 0.0（绝对 0 ⇒ 立即短路）
        elif deadline_kind == "alias":
            deadline = t0 + deadline_orig     # M1：自己赋自己 ⇒ 原值不变
        elif deadline_kind == "missing":
            deadline = t0 + deadline_orig     # 短路块不存在 ⇒ 原值
        else:
            deadline = t0 + deadline_orig
    else:
        deadline = t0 + deadline_orig

    polls = 0
    # 与母本循环同序：先判谓词，再 sleep+读矩形+计数
    while (rect_wh != (FRAME_W, FRAME_H)) and (t < deadline):
        t += POLL_S
        polls += 1
        if polls > 100000:
            break
    return polls


def model_late(nav_to_measure_s, limit, op, guard_nav_end=True, guard_skip=True):
    """复算 late-start 闸的判定结果（含启用条件）。

    ★ 启用条件 = guard_nav_end ∧ guard_skip（AST 已断言结构，见 E0e）。
      ★ guard_skip=False（对照臂 --h7-keep-rect-wait）⇒ 闸**不判定**，一律 False。
    """
    if not (guard_nav_end and guard_skip):
        return False
    if op == "Gt":
        return nav_to_measure_s > limit
    if op == "GtE":
        return nav_to_measure_s >= limit
    if op == "Lt":
        return nav_to_measure_s < limit
    if op == "LtE":
        return nav_to_measure_s <= limit
    raise ValueError(f"unsupported op {op}")


# ---------------------------------------------------------------------------
def main():
    if not H7.exists():
        print("ABORT: harness7 not generated")
        return 1
    src = H7.read_text(encoding="utf-8")
    tree = parse(src)

    limit = const_assign(tree, "H7_MEASURE_MAX_NAV_TO_W0_S")
    dl_kind, dl_val = deadline_assigned_value(tree)
    while_node = find_while_rect_wait(tree)
    op, op_ok = late_gate_compare(tree)
    g_nav_end, g_skip = late_gate_guard(tree)
    polarity = gate_polarity(tree)
    order_ok, order_dt = source_order_ok(tree)
    arming = arming_polarity(tree)

    print("=" * 72)
    print("E0 结构取值（先证明模型不是虚构）")
    check("E0a 闸常量可取到", limit is not None, f"H7_MEASURE_MAX_NAV_TO_W0_S={limit}")
    check("E0b 短路赋值存在且为字面量", dl_kind == "const", f"kind={dl_kind} val={dl_val}")
    check("E0c 采帧前 while 结构匹配（Tuple!=Tuple AND monotonic<deadline）",
          while_node is not None, f"node={'found' if while_node else 'MISSING'}")
    check("E0d late 闸比较存在", op_ok, f"op={op}")
    check("E0e late 闸启用条件含 nav_end_t 判定", g_nav_end, f"guard={g_nav_end}")
    check("E0f late 闸启用条件含 fs_rect_wait_skipped 前置", g_skip, f"guard={g_skip}")
    # ★★ E0g/h/i/j：补 H7 盲验抓出的三条验证器缺陷
    check("E0g 闸极性正确（nav_end 是 `is not None`、skip 不在 not 里、用 and 连接）",
          polarity["nav_end_ok"] and polarity["skip_ok"] and polarity["conjunction"],
          json.dumps(polarity))
    check("E0h ★顺序：短路块在母本 while 之前，且 deadline=0.0 夹在两者之间",
          order_ok, json.dumps(order_dt))
    check("E0i ★武装极性：`--h7-keep-rect-wait` 是 opt-out（not getattr）",
          arming == "not_getattr", f"arming={arming}")
    if not (limit is not None and dl_kind == "const"
            and while_node is not None and op_ok and g_nav_end and g_skip
            and polarity["nav_end_ok"] and polarity["skip_ok"]
            and polarity["conjunction"] and order_ok
            and arming == "not_getattr"):
        print("ABORT: 结构取值失败，后续模型无意义")
        return 1

    print("=" * 72)
    print("E1 全屏 + 短路 on ⇒ 轮数 0")
    p1 = model_rect_wait(dl_kind, dl_val, True, (2560, 1440))
    check("E1 短路生效（轮数 0）", p1 == 0, f"polls={p1}")

    print("=" * 72)
    print("E2 全屏 + 短路 off ⇒ 跑满 deadline（母本语义）")
    # ★★ E2 的期望值必须来自**产物**，不能用手设常量（H7 盲验裁决 #14）：
    #   旧版期望 = int(DEADLINE_ORIG / POLL_S) = 250，两个数都手设 ⇒ 无法被改坏产物杀掉。
    #   新版：从产物读 `STAGE_TIMEOUT_S` 的**全屏覆写值**（真实 deadline 的余量来源），
    #   再与模型算出的轮数比。取不到就退化为「与真机实测 251 同量级」的区间判据，
    #   并如实标注是区间而非精确值。
    fs_timeout = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tg in node.targets:
                if isinstance(tg, ast.Name) and tg.id == "STAGE_TIMEOUT_S":
                    try:
                        v = ast.literal_eval(node.value)
                    except Exception:
                        continue
                    if v > 30.0:      # 全屏覆写值（窗口模式帽是 30.0）
                        fs_timeout = v
    p2 = model_rect_wait(dl_kind, dl_val, False, (2560, 1440))
    if fs_timeout is not None:
        # ★★ 关键：`deadline` 是 **window 阶段起点 + STAGE_TIMEOUT_S** 的绝对时刻
        #   （母本 `:7641`），不是"frame 阶段起点 + 150 s"。
        #   ⇒ frame 阶段实际可用的余量 = STAGE_TIMEOUT_S −（frame 起点 − window 起点）。
        #   用 2026-10-23 l1_20261023 实测两段耗时（window=13.282、并推得 frame 起点
        #   相对 window 起点 = 37.25 − 12.593 = 24.657 s）代入：
        #     余量 = 150 − 24.657 = 125.343 s ⇒ 250 轮；真机实测 251 轮 / 125.703 s。
        #   ⇒ 该式是**产物常量 + 真机两段耗时**共同决定的，不是手设数。
        #   （初版直接用 fs_timeout/POLL_S = 300，错在把 deadline 当成了阶段相对量；
        #     盲验裁决指出"期望值手设"是对的，但它给的原因也不完整——真正的因是
        #     deadline 的**钟源**是 window 阶段起点，不是 frame 阶段起点。）
        WINDOW_S, FRAME_LEAD = 13.282, 24.657     # l1_20261023 实测两段
        remain = fs_timeout - FRAME_LEAD
        expect2 = int(remain / POLL_S)
        check("E2 关闭短路跑满 deadline（余量=产物常量−真机实测偏移）",
              p2 == expect2,
              f"polls={p2} expect={expect2}（STAGE_TIMEOUT_S={fs_timeout} 取自产物；"
              f"frame 起点偏移={FRAME_LEAD} s 取自真机）")
        ratio = p2 / 251.0
        check("E2b 模型与真机实测 251 轮同量级（±5%）",
              0.95 <= ratio <= 1.05, f"polls={p2} 实测=251 ratio={ratio:.4f}")
    else:
        check("E2 关闭短路跑满 deadline（未取到覆写值 ⇒ 退化为区间判据）",
              200 <= p2 <= 300, f"polls={p2}（区间 200-300，非精确值）")

    print("=" * 72)
    print("E3 窗口模式（矩形已到 800×600）⇒ 轮数 0")
    p3 = model_rect_wait(dl_kind, dl_val, False, (800, 600))
    check("E3 窗口模式零等待", p3 == 0, f"polls={p3}")

    print("=" * 72)
    print("E4 late-start 闸")
    check("E4a 短路生效 + 正常值 0.3 s 不触发",
          model_late(0.3, limit, op, g_nav_end, g_skip) is False,
          f"0.3 {op} {limit} => {model_late(0.3, limit, op, g_nav_end, g_skip)}")
    check("E4b 短路生效 + 超限 130 s 触发",
          model_late(130.0, limit, op, g_nav_end, g_skip) is True,
          f"130 {op} {limit} => {model_late(130.0, limit, op, g_nav_end, g_skip)}")
    # ★★ E4c/E4d：对照臂（--h7-keep-rect-wait，短路未生效）—— 用 10-21 四趟的
    #    实测 nav→w0（126.187 / 127.704 / 130.688 / 130.704 s）逐一验：闸必须不判定。
    check("E4c 对照臂不判定（10-21 l1e 126.187 s）",
          model_late(126.187, limit, op, g_nav_end, guard_skip=False) is False,
          "短路未生效 ⇒ 闸不启用")
    check("E4d 对照臂不判定（10-21 l1a 130.688 s）",
          model_late(130.688, limit, op, g_nav_end, guard_skip=False) is False,
          "短路未生效 ⇒ 闸不启用")
    check("E4e 若闸被无条件施加，10-21 l1a 会被误判（反证 E4c/E4d 的必要性）",
          model_late(130.688, limit, op, g_nav_end, guard_skip=True) is True,
          "同一数值在短路生效时会触发 ⇒ 前置条件是必需的")

    print("=" * 72)
    print("M1 变异：`deadline = 0.0` → `deadline = deadline`（短路失效）")
    m1 = src.replace("            _h7_deadline_orig = deadline\n            deadline = 0.0",
                     "            _h7_deadline_orig = deadline\n            deadline = deadline")
    if m1 == src:
        check("M1 变异点可定位", False, "替换未命中")
    else:
        k1, v1 = deadline_assigned_value(parse(m1))
        pm1 = model_rect_wait(k1, v1, True, (2560, 1440))
        check("M1 变异后 E1 必红（轮数 > 0）", pm1 > 0,
              f"kind={k1} polls={pm1}")

    print("=" * 72)
    print("M2 变异：闸常量 90.0 → 1e9（闸失效）")
    m2 = src.replace("H7_MEASURE_MAX_NAV_TO_W0_S = 90.0",
                     "H7_MEASURE_MAX_NAV_TO_W0_S = 1e9")
    if m2 == src:
        check("M2 变异点可定位", False, "替换未命中")
    else:
        lim2 = const_assign(parse(m2), "H7_MEASURE_MAX_NAV_TO_W0_S")
        check("M2 变异后 E4b 必红（不触发）",
              model_late(130.0, lim2, op, g_nav_end, g_skip) is False,
              f"limit={lim2} => {model_late(130.0, lim2, op, g_nav_end, g_skip)}")

    print("=" * 72)
    print("M2b 变异：删掉启用条件里的 fs_rect_wait_skipped 前置")
    m2b = src.replace(
        'if _h7_nav_end is not None and _H7_STATE["fs_rect_wait_skipped"]:',
        "if _h7_nav_end is not None:")
    if m2b == src:
        check("M2b 变异点可定位", False, "替换未命中")
    else:
        gn2, gs2 = late_gate_guard(parse(m2b))
        check("M2b 变异后 E4c 必红（对照臂被误判）",
              model_late(126.187, limit, op, gn2, guard_skip=False) is True
              or not gs2,
              f"guard_skip={gs2}（原为 True）")

    print("=" * 72)
    print("M3 变异：`>` → `>=`，喂等值 ⇒ 边界判据可杀")
    m3 = src.replace("_h7_late = bool(_h7_n2m > H7_MEASURE_MAX_NAV_TO_W0_S)",
                     "_h7_late = bool(_h7_n2m >= H7_MEASURE_MAX_NAV_TO_W0_S)")
    if m3 == src:
        check("M3 变异点可定位", False, "替换未命中")
    else:
        op3, ok3 = late_gate_compare(parse(m3))
        check("M3 变异后边界必红（等值变触发）",
              ok3 and model_late(limit, limit, op3, g_nav_end, g_skip) is True,
              f"op={op3} {limit} {op3} {limit} => "
              f"{model_late(limit, limit, op3, g_nav_end, g_skip) if ok3 else 'n/a'}")
        # ★ 原产物在等值处必须**不**触发（与 M3 形成对照）
        check("M3 对照：原产物等值不触发",
              model_late(limit, limit, op, g_nav_end, g_skip) is False,
              f"{limit} {op} {limit} => {model_late(limit, limit, op, g_nav_end, g_skip)}")

    print("=" * 72)
    print("E5 late_start 落盘与记账一致")
    _verdict_line = '_h7_payload["verdict"] = "late_start"'
    _rec_line = ('rec.add("MEASURE", "verdict", "late_start", '
                 '"script:_measure_run"')
    check("E5a payload verdict 被改写为 late_start", _verdict_line in src,
          "读到即证明存在该赋值")
    check("E5b rec 行记 late_start", _rec_line in src,
          "rec 与 JSON 两处都是 late_start")

    # ★★ E5c 重新设计（H7 盲验裁决 #13）：旧版是**恒真断言** ——
    #   `m5 = src.replace(L, ""); check(L not in m5)`，判据即刚删掉的串，
    #   对任何源码都 True，且变异体从未被 parse() 重算。
    #   新版改为**真变异 + 真重算**：删掉改写行后，用 payload 的实际 verdict
    #   与 rec 的实际 verdict 比，必须变成「不一致」。
    def _late_verdicts(text):
        """从源码取 (payload 写出的 verdict, rec 记录的 verdict)。

        ★ 不是存在性检查：payload 侧取「late_start 分支内对
          `_h7_payload["verdict"]` 的赋值」，取不到就视为继承默认值 "error"
          （`_measure_error_payload` 的默认，见母本）。
        """
        br = re.search(r"            if _h7_late:\n(.*?)"
                       r"(?=\n        # <<< H7-END late-start-gate)",
                       text, re.S)
        if br is None:
            return (None, None)
        blk = br.group(1)
        m_p = re.search(r'_h7_payload\["verdict"\]\s*=\s*"([a-z_]+)"', blk)
        payload_v = m_p.group(1) if m_p else "error"   # ★ 继承默认值
        m_r = re.search(r'rec\.add\("MEASURE", "verdict", "([a-z_]+)"', blk)
        rec_v = m_r.group(1) if m_r else None
        return (payload_v, rec_v)

    pv, rv = _late_verdicts(src)
    check("E5c 原产物两处 verdict 一致", pv is not None and pv == rv,
          f"payload={pv} rec={rv}")

    m5 = src.replace(_verdict_line + "\n", "")
    if m5 == src:
        check("E5d 变异点可定位", False, "替换未命中")
    else:
        pv5, rv5 = _late_verdicts(m5)
        check("E5d 变异后两处 verdict 必不一致（真重算，非恒真）",
              pv5 != rv5, f"payload={pv5} rec={rv5}")

    print("=" * 72)
    print("M4 变异：把 rect-wait-skip 块整块搬到 while 之后（顺序搬移）")
    # ★ 补 H7 盲验裁决 #10：旧判据只判「存在」，搬移后运行时短路永不生效却全绿。
    #   ★ 变异必须保持语法合法：把 `# >>> H7-BEGIN rect-wait-skip` 到
    #     `# <<< H7-END rect-wait-skip` 之间的整块，挪到母本 while 循环之后。
    _b = src.find("        # >>> H7-BEGIN rect-wait-skip")
    _e_marker = "        # <<< H7-END rect-wait-skip\n"
    _e = src.find(_e_marker)
    _wh_i = src.find("while (_cap_rect[2] - _cap_rect[0],")
    if _b < 0 or _e < 0 or _wh_i < 0 or not (_b < _e < _wh_i):
        check("M4 变异点可定位", False,
              f"begin={_b} end={_e} while={_wh_i}（期望 begin<end<while）")
    else:
        _block = src[_b:_e + len(_e_marker)]
        _rest = src[:_b] + src[_e + len(_e_marker):]
        # while 循环体结束（4 行）之后插入该块
        _anchor = "            _cap_wait += 1\n"
        _ai = _rest.find(_anchor)
        if _ai < 0:
            check("M4 插入锚可定位", False)
        else:
            _end = _ai + len(_anchor)
            _m4 = _rest[:_end] + _block + _rest[_end:]
            try:
                _tree4 = parse(_m4)
            except SyntaxError as exc:
                check("M4 变异体语法", False, f"{exc}")
            else:
                ok4, dt4 = source_order_ok(_tree4)
                check("M4 变异后 E0h 必红（短路块已搬到 while 之后）",
                      ok4 is False, json.dumps(dt4))

    print("=" * 72)
    print("M5 变异：武装极性反转（if not getattr → if getattr）")
    # ★ 补 H7 盲验裁决 #12：旧验证器从不读武装行，反转后全绿。
    _m5a = src.replace(
        'if not getattr(args, "h7_keep_rect_wait", False):',
        'if getattr(args, "h7_keep_rect_wait", False):')
    if _m5a == src:
        check("M5 变异点可定位", False, "替换未命中")
    else:
        arm5 = arming_polarity(parse(_m5a))
        check("M5 变异后 E0i 必红（武装方向反转）",
              arm5 != "not_getattr", f"arming={arm5}")

    print("=" * 72)
    print("M6 变异：闸极性反转（skip 前置包进 not）")
    _m6 = src.replace(
        '_H7_STATE["fs_rect_wait_skipped"]:',
        'not _H7_STATE["fs_rect_wait_skipped"]:')
    if _m6 == src:
        check("M6 变异点可定位", False, "替换未命中")
    else:
        pol6 = gate_polarity(parse(_m6))
        check("M6 变异后 E0g 必红（skip 在 not 里）",
              pol6["skip_ok"] is False, json.dumps(pol6))

    print("=" * 72)
    npass = sum(1 for _, ok, _ in results if ok)
    print(f"TOTAL {npass}/{len(results)} PASS")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
