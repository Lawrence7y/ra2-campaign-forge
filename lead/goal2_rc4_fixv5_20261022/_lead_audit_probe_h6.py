#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 独立核验：A/B 探针安全属性 + harness6 派生完整性。

★ 为什么由 Lead 亲自做
  原计划派异族子代理，子代理被取消。本件是**只读静态核验**，不涉及
  「执行者核验自己实现」的利益冲突问题（探针与 harness6 的实现者分别是
  本会话与子代理，本件只核**可机械判定**的静态属性，不核设计判断）。
  ⇒ 仍建议下轮补一次真异族核验；本件的结论定位是「Lead 自查」，不是「异族 CONFIRMED」。

★ 核验项（逐条机械可判）
  A 组 —— _rc4_ab_probe.py（8 项）
  B 组 —— qc151_trip.harness6.py（7 项）
"""
from __future__ import annotations

import ast
import hashlib
import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
PROBE = ROOT / "lead" / "goal2_rc4_fixv5_20261022" / "_rc4_ab_probe.py"
H6 = ROOT / "lead" / "goal1_harness6_20261022" / "qc151_trip.harness6.py"
H5 = ROOT / "lead" / "goal1_a8_fix_20261022" / "qc151_trip.harness5.py"

H5_SHA16 = "f1e5bc7b0ff30c9c"
H5_SIZE = 427456

RESULTS: list[tuple[str, bool, str]] = []


def chk(tag: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((tag, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {tag}  {detail}")
    return bool(cond)


def src_of(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def func_src(text: str, name: str) -> str | None:
    """取某个顶层/嵌套函数的源码文本（按 ast 的 lineno/end_lineno 切）。"""
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = text.splitlines()
            return "\n".join(lines[node.lineno - 1:node.end_lineno])
    return None


def main() -> int:
    print("=" * 88)
    print("== 0  identity")
    print("=" * 88)
    for p in (PROBE, H6, H5):
        b = p.read_bytes()
        print(f"  {p.name:32s} {len(b):>8d} B  sha16={hashlib.sha256(b).hexdigest()[:16]}")

    # ===================================================================
    print()
    print("=" * 88)
    print("== A 组  _rc4_ab_probe.py")
    print("=" * 88)
    ptxt = src_of(PROBE)
    ptree = ast.parse(ptxt)

    # ---- A1 默认不发射 -------------------------------------------------
    # 真机动作：Popen / DebugActiveProcess / TerminateProcess / rmtree
    live_gates = []
    for node in ast.walk(ptree):
        if isinstance(node, ast.If):
            seg = ast.get_source_segment(ptxt, node.test) or ""
            if "args.live" in seg or "not args.live" in seg:
                live_gates.append(seg.strip())
    chk("A1 存在 args.live 门禁", len(live_gates) >= 1, f"gates={live_gates}")

    # 真机动作必须全部出现在 `if not args.live: ... return` 之后
    lines = ptxt.splitlines()
    live_guard_line = None
    for i, ln in enumerate(lines, 1):
        if "if not args.live" in ln:
            live_guard_line = i
            break
    chk("A1 存在 `if not args.live` 早退", live_guard_line is not None,
        f"line={live_guard_line}")

    # 统计真机动作首次出现行号
    live_actions = {}
    for i, ln in enumerate(lines, 1):
        for kw in ("subprocess.Popen", "DebugActiveProcess(", "TerminateProcess(",
                   "shutil.rmtree("):
            if kw in ln and kw not in live_actions:
                live_actions[kw] = i
    print(f"    真机动作首次出现行号: {live_actions}")
    if live_guard_line:
        # one_trip / _cleanup 是函数定义，真正的调用在 live 分支之后
        call_sites = [i for i, ln in enumerate(lines, 1)
                      if "one_trip(" in ln and "def " not in ln]
        print(f"    one_trip 调用行号: {call_sites}")
        ok = bool(call_sites) and all(c > live_guard_line for c in call_sites)
        chk("A1 one_trip 只在 live 门禁之后被调用", ok,
            f"guard@{live_guard_line}, calls={call_sites}")

    # ---- A2 pid 归属 ---------------------------------------------------
    # ★ 真正的 pid 解析在 one_trip() 里，且是 `if arm == "A": ... else: ...` 的
    #   **else 分支**（不是 `if arm == "B":`）。首版两处误抓：
    #   (a) main 里的预检分支；(b) 内层 `if not dll_name:` 子分支 ⇒ 两次假红。
    #   改为：在 one_trip 里找 `if arm == "A"` 的 orelse 体。
    ot_node = None
    for node in ast.walk(ptree):
        if isinstance(node, ast.FunctionDef) and node.name == "one_trip":
            ot_node = node
            break
    b_body = ""
    if ot_node is not None:
        for node in ast.walk(ot_node):
            if isinstance(node, ast.If) and node.orelse:
                seg_t = ast.get_source_segment(ptxt, node.test) or ""
                if seg_t.strip() in ('arm == "A"', "arm == 'A'"):
                    for st in node.orelse:
                        b_body += (ast.get_source_segment(ptxt, st) or "") + "\n"
                    break
    chk("A2 取到 B 臂（arm==A 的 else）分支体", bool(b_body), f"{len(b_body)} chars")
    has_carrier_match = ("under_carrier" in b_body and "gamemd.exe" in b_body)
    has_procpid = "pid = proc.pid" in b_body
    chk("A2 B 臂按载体目录匹配 gamemd 取 pid", has_carrier_match,
        "under_carrier + gamemd.exe 同现" if has_carrier_match else "missing")
    chk("A2 B 臂不存在 `pid = proc.pid` 兜底", not has_procpid,
        "已确认无兜底" if not has_procpid else "★ 发现兜底")
    chk("A2 B 臂找不到 gamemd 时 abort（不兜底）",
        "gamemd_not_found_under_carrier" in b_body, "")

    # ---- A3 路径归属判定 -----------------------------------------------
    starts = [i for i, ln in enumerate(lines, 1)
              if "startswith" in ln and "under_carrier" not in ln]
    print(f"    startswith 出现行号（排除注释）: {starts[:10]}")
    # 只关心是否用于路径归属
    path_starts = [i for i in starts if "img" in lines[i - 1] or "image" in lines[i - 1]
                   or "path" in lines[i - 1].lower()]
    chk("A3 无 startswith 用于路径归属", not path_starts, f"suspects={path_starts}")

    uc = func_src(ptxt, "under_carrier") or ""
    chk("A3 under_carrier 用 relative_to", "relative_to" in uc, "ok" if "relative_to" in uc else "missing")
    chk("A3 under_carrier 捕获 ValueError", "ValueError" in uc, "ok" if "ValueError" in uc else "missing")

    # ---- A4 枚举器正控驱动控制流 ---------------------------------------
    sweep = func_src(ptxt, "a8_sweep") or ""
    chk("A4 a8_sweep 有清扫前正控", "enum_probe(\"before_sweep\")" in sweep, "")
    chk("A4 a8_sweep 有收尾前正控", "enum_probe(\"before_remaining\")" in sweep, "")
    chk("A4 正控失败返回 ENUM_FAILED 哨兵（非空 list）",
        "ENUM_FAILED_BEFORE" in sweep and "ENUM_FAILED_AFTER" in sweep, "")
    # 关键：哨兵必须是非空 remaining
    chk("A4 正控失败时 remaining 非空",
        "remaining\": [{\"pid\": None" in sweep or '"remaining": [{"pid": None' in sweep,
        "哨兵形态")

    # ---- A5 clean_exit 不依赖 except.txt --------------------------------
    # ★ 首版直接搜 "except" 子串 ⇒ 两次假红：
    #   (a) 命中注释「不看 except.txt」；
    #   (b) 剔除注释后仍命中**紧邻其后的字段名** `rec["except_sha16_after"]`
    #       （那是记录 except 变化，不是 clean_exit 的判据输入）。
    #   改为：只取 clean_exit 赋值语句本身 + 其前 12 行（不含之后的行）。
    ot = func_src(ptxt, "one_trip") or ""
    ot_lines = ot.splitlines()
    ce_idx = None
    for i, ln in enumerate(ot_lines):
        if 'rec["clean_exit"]' in ln:
            ce_idx = i
            break
    window = ot_lines[max(0, ce_idx - 12):ce_idx + 3] if ce_idx is not None else []
    code_only = [ln for ln in window if not ln.lstrip().startswith("#")]
    seg_code = "\n".join(code_only)
    chk("A5 定位到 clean_exit 赋值", ce_idx is not None, f"line_in_func={ce_idx}")
    chk("A5 clean_exit 判据窗口（剔注释、不含其后字段）不含 except 变量",
        "except" not in seg_code,
        "clean" if "except" not in seg_code else "★ 引用 except")
    chk("A5 clean_exit 用 CLOSE_WAIT_S 时限",
        "CLOSE_WAIT_S" in seg_code, "")

    # ---- A5b B 臂 clean_exit 不得采信 proc.poll() -----------------------
    # ★ 本轮自查发现的假绿通道：B 臂的 proc 是 **loader**，不是 gamemd。
    #   loader 因自身异常先退而 gamemd 仍在跑时，`proc.poll() is not None`
    #   会让 exited=True ⇒ 误判 clean_exit。故 B 臂必须只认 gamemd 的 pid。
    has_arm_split = 'if arm == "A":' in seg_code
    chk("A5b clean_exit 按臂分流", has_arm_split,
        "ok" if has_arm_split else "★ 两臂共用 proc.poll()")
    # ★ 只取 `else:` 之后到第一条 `rec[` 之前的**判据语句**。
    #   首版把 `rec["loader_alive_at_judge"] = ... proc.poll() ...` 这条**诊断记录**
    #   也算了进去 ⇒ 假红。诊断字段记录 loader 状态是**允许且有用**的，
    #   只要它不参与 clean_exit 的计算。
    b_judge = ""
    if ce_idx is not None:
        judge_block = ot_lines[max(0, ce_idx - 14):ce_idx + 1]
        if "else:" in "\n".join(judge_block):
            tail = "\n".join(judge_block).split("else:", 1)[1]
            # 截到第一条 rec[ 为止
            cut = tail.find("rec[")
            b_judge = tail[:cut] if cut >= 0 else tail
    b_code = "\n".join(ln for ln in b_judge.splitlines()
                       if not ln.lstrip().startswith("#"))
    chk("A5b B 臂判据语句不含 proc.poll()",
        "proc.poll()" not in b_code,
        "ok" if "proc.poll()" not in b_code else "★ 仍在采信 loader 状态")
    chk("A5b B 臂只按 gamemd pid 判退出",
        "list_procs()" in b_code and "pid" in b_code,
        f"judge={b_code.strip()[:80]}")

    # ---- A6 --dll 单层校验 ---------------------------------------------
    sn = func_src(ptxt, "safe_name") or ""
    chk("A6 safe_name 拒绝 ..", '".."' in sn or "'..'" in sn, "")
    chk("A6 safe_name 拒绝 / 与 \\\\", '"/"' in sn and '"\\\\"' in sn, "")
    chk("A6 B 臂强制要求 --dll",
        'if not args.dll' in ptxt or "arm_B_requires_dll" in ptxt, "")

    # ---- A7 载体目录长度门禁 -------------------------------------------
    chk("A7 预检检查载体目录长度",
        "载体目录长度" in ptxt and "probe_dir" in ptxt, "")
    chk("A7 one_trip 内检查 carrier_len",
        "carrier_len" in ot and "CARRIER_PATH_MAX" in ot, "")
    chk("A7 门禁对象是目录字符串",
        'str(carrier)' in ptxt, "")

    # ---- A8 _cleanup 顺序 ----------------------------------------------
    cl = func_src(ptxt, "_cleanup") or ""
    i_stop = cl.find("DebugActiveProcessStop")
    i_sweep = cl.find("a8_sweep")
    i_rm = cl.find("rm_carrier")
    chk("A8 Stop 先于 sweep", 0 <= i_stop < i_sweep, f"stop@{i_stop} sweep@{i_sweep}")
    chk("A8 sweep 先于删载体", 0 <= i_sweep < i_rm, f"sweep@{i_sweep} rm@{i_rm}")
    chk("A8 own_pid 用 os.getpid()", "os.getpid()" in cl, "")

    # ===================================================================
    print()
    print("=" * 88)
    print("== B 组  qc151_trip.harness6.py")
    print("=" * 88)
    h5b = H5.read_bytes()
    h6b = H6.read_bytes()
    h5sha = hashlib.sha256(h5b).hexdigest()

    # ---- B1 母本未改 ---------------------------------------------------
    chk("B1 母本 sha16 == f1e5bc7b0ff30c9c", h5sha.startswith(H5_SHA16), h5sha[:16])
    chk("B1 母本字节数 == 427456", len(h5b) == H5_SIZE, str(len(h5b)))

    # ---- B2 零删除行（多重集） -----------------------------------------
    a = h5b.decode("utf-8").splitlines()
    b = h6b.decode("utf-8").splitlines()
    ca, cb = Counter(a), Counter(b)
    removed = ca - cb
    chk("B2 零删除行（多重集）", sum(removed.values()) == 0,
        f"removed={sum(removed.values())}, mother={len(a)}, copy={len(b)}")
    if removed:
        for ln, n in list(removed.items())[:5]:
            print(f"      removed x{n}: {ln[:100]}")

    # ---- B3 WER Sig 按名读 ---------------------------------------------
    h6txt = h6b.decode("utf-8")
    h6lines = h6txt.splitlines()
    sig_by_name = [i for i, ln in enumerate(h6lines, 1)
                   if "Sig[" in ln and ".Name" in ln]
    sig_by_index = [i for i, ln in enumerate(h6lines, 1)
                    if "Sig[0]" in ln or "Sig[1]" in ln]
    chk("B3 存在按 .Name 读 Sig 的代码", len(sig_by_name) > 0,
        f"lines={sig_by_name[:6]}")
    chk("B3 不存在按固定索引读 Sig", len(sig_by_index) == 0,
        f"lines={sig_by_index}" if sig_by_index else "none")

    # ---- B4 隔离计数不把失败当零 ---------------------------------------
    iso = func_src(h6txt, "carrier_isolation_count") or ""
    chk("B4 carrier_isolation_count 存在", bool(iso), f"{len(iso)} chars")
    has_none = "None" in iso
    chk("B4 枚举失败时计数为 None 而非 0", has_none,
        "ok" if has_none else "★ 只见到数值")

    # ---- B5 near-limit 不改退出码 --------------------------------------
    chk("B5 存在 near limit 130 WARN", "near limit 130" in h6txt, "")
    chk("B5 >=131 硬停逻辑仍在",
        "CARRIER_PATH_MAX_CHARS" in h6txt or "RuntimeError" in h6txt,
        "")

    # ---- B6 --close-mode 默认 terminate ---------------------------------
    chk("B6 close-mode 默认 terminate",
        'default="terminate"' in h6txt or "default='terminate'" in h6txt, "")
    chk("B6 记录 close_fallback_terminate", "close_fallback_terminate" in h6txt, "")

    # ---- B7 terminate_owned_process 函数体逐字节相同 ---------------------
    f5 = func_src(h5txt := h5b.decode("utf-8"), "terminate_owned_process")
    f6 = func_src(h6txt, "terminate_owned_process")
    same = (f5 is not None and f6 is not None and f5 == f6)
    chk("B7 terminate_owned_process 函数体逐字节相同", same,
        f"h5={len(f5) if f5 else 0} chars, h6={len(f6) if f6 else 0} chars")

    # ===================================================================
    print()
    print("=" * 88)
    print("== RESULT")
    print("=" * 88)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    a_pass = sum(1 for t, ok, _ in RESULTS if t.startswith("A") and ok)
    a_tot = sum(1 for t, _, _ in RESULTS if t.startswith("A"))
    b_pass = sum(1 for t, ok, _ in RESULTS if t.startswith("B") and ok)
    b_tot = sum(1 for t, _, _ in RESULTS if t.startswith("B"))
    print(f"  A 组（探针）  : {a_pass}/{a_tot}")
    print(f"  B 组（harness6）: {b_pass}/{b_tot}")
    print(f"  checks passed : {passed}/{total}")
    verdict = passed == total
    print(f"  RESULT: {'ALL PASS' if verdict else 'HAS FAILURES'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
