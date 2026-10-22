# -*- coding: utf-8 -*-
"""独立核验 A8-b 补丁（给 A8 加枚举器正控探针）。

★ 本脚本只读 harness4 / harness5，只写自己的 stdout。
★ 不启动游戏、不杀任何进程、不使用 py_compile（避免落 .pyc 破坏 mtime 门禁）。
★ 所有数字**本脚本自己算**，不采信实现者自述。

用法：
    python VERIFY_A8B.py > VERIFY_A8B.txt 2>&1
退出码：0 = 全部 CONFIRMED；1 = 至少一项 REFUTED。
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
H4 = HERE / "qc151_trip.harness4.py"
H5 = HERE / "qc151_trip.harness5.py"
GEN = HERE / "_gen_harness5.py"
DIFF = HERE / "a8b.diff"

BASE_LF16 = "cd9bbc87e46054af"

RESULTS = []   # (item_id, title, verdict, detail)


def chk(item, title, cond, detail=""):
    verdict = "CONFIRMED" if cond else "REFUTED"
    RESULTS.append((item, title, verdict, detail))
    print(f"[{verdict:9s}] {item}  {title}")
    if detail:
        for ln in str(detail).split("\n"):
            print(f"             {ln}")
    return bool(cond)


def info(msg):
    print(f"             {msg}")


def lf16(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()[:16]


def crlf16(b: bytes) -> str:
    t = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(t.replace(b"\n", b"\r\n")).hexdigest()[:16]


def load_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeRec:
    """最小 Recorder 替身（只收集 add 调用，不落盘）。"""

    def __init__(self):
        self.events = []

    def add(self, *a, **kw):
        self.events.append({"args": a, "kwargs": kw})

    def keys(self):
        return [e["args"][1] for e in self.events if len(e["args"]) > 1]

    def values_of(self, key):
        return [e["args"][2] for e in self.events
                if len(e["args"]) > 2 and e["args"][1] == key]


# ---------------------------------------------------------------------------
# 独立重建：用生成器里的 ANCHOR/PATCH 常量重算（不执行生成器）
# ---------------------------------------------------------------------------
def gen_constants():
    tree = ast.parse(GEN.read_text(encoding="utf-8"))
    consts = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            consts[node.targets[0].id] = node.value.value
    return consts


def rebuild_from_generator(src_text: str):
    c = gen_constants()
    missing = [k for k in ("ANCHOR_1", "PATCH_1", "ANCHOR_2", "PATCH_2",
                           "ANCHOR_3", "PATCH_3", "ANCHOR_4", "PATCH_4")
               if k not in c]
    if missing:
        raise KeyError(f"generator constants missing: {missing}")
    out = src_text
    for i in (1, 2, 3, 4):
        a, p = c[f"ANCHOR_{i}"], c[f"PATCH_{i}"]
        if out.count(a) != 1:
            raise ValueError(f"ANCHOR_{i} occurrence = {out.count(a)} (must be 1)")
        out = out.replace(a, p, 1)
    return out


def apply_unified_diff(old_lines, diff_text):
    """最小 unified-diff 应用器：逐 hunk 严格校验旧行后再拼接。"""
    lines = diff_text.split("\n")
    out = []
    old_i = 0
    i = 0
    hunk_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("---") or ln.startswith("+++"):
            i += 1
            continue
        m = hunk_re.match(ln)
        if not m:
            i += 1
            continue
        old_start = int(m.group(1))
        old_len = int(m.group(2)) if m.group(2) is not None else 1
        # 把旧文件游标推进到 hunk 起点（1-based → 0-based）
        target = old_start - 1
        if old_len == 0:
            target = old_start
        out.extend(old_lines[old_i:target])
        old_i = target
        i += 1
        while i < len(lines) and not hunk_re.match(lines[i]):
            body = lines[i]
            if body == "" and i == len(lines) - 1:
                break
            tag, text = body[:1], body[1:]
            if tag == " ":
                if old_i >= len(old_lines) or old_lines[old_i] != text:
                    raise ValueError(f"diff context mismatch at old line {old_i + 1}")
                out.append(text)
                old_i += 1
            elif tag == "-":
                if old_i >= len(old_lines) or old_lines[old_i] != text:
                    raise ValueError(f"diff removal mismatch at old line {old_i + 1}")
                old_i += 1
            elif tag == "+":
                out.append(text)
            elif tag == "\\":
                pass
            elif body == "":
                pass
            else:
                raise ValueError(f"bad diff line: {body[:60]!r}")
            i += 1
    out.extend(old_lines[old_i:])
    return out


def func_ast_map(src: str):
    tree = ast.parse(src)
    d = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            d.setdefault("def:" + node.name, []).append(ast.dump(node))
        elif isinstance(node, ast.ClassDef):
            d.setdefault("class:" + node.name, []).append(ast.dump(node))
    return d


def top_level_segment(src: str, name: str):
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(src, node)
    return None


def main() -> int:
    print("=" * 78)
    print("A8-b 独立核验（枚举器正控探针）")
    print(f"目录: {HERE}")
    print(f"python: {sys.version.split()[0]}  exe={sys.executable}")
    print("=" * 78)

    raw4 = H4.read_bytes()
    raw5 = H5.read_bytes()
    txt4 = raw4.decode("utf-8")
    txt5 = raw5.decode("utf-8")

    # ---------------- 1. 基线零改动 ----------------
    print("\n--- 1. 基线零改动 ---")
    b4 = lf16(raw4)
    info(f"harness4 bytes={len(raw4)}  LF16={b4}  CRLF16={crlf16(raw4)}")
    chk("1", "harness4 的 LF sha256 前16 == cd9bbc87e46054af",
        b4 == BASE_LF16, f"actual={b4} expect={BASE_LF16}")

    # ---------------- 2. 副本哈希自证 ----------------
    print("\n--- 2. 副本哈希自证 ---")
    l5, c5 = lf16(raw5), crlf16(raw5)
    info(f"harness5 bytes={len(raw5)}  LF16={l5}  CRLF16={c5}  "
         f"实际CRLF字节对={'YES' if b'\r\n' in raw5 else 'NO'}  "
         f"实际裸CR字节={'YES' if b'\r' in raw5 else 'NO'}")
    chk("2a", "harness5 LF16 == f1e5bc7b0ff30c9c", l5 == "f1e5bc7b0ff30c9c", f"actual={l5}")
    chk("2b", "harness5 CRLF16 == 3b10dae011d08c4b", c5 == "3b10dae011d08c4b", f"actual={c5}")
    chk("2c", "harness5 字节数 == 427456", len(raw5) == 427456, f"actual={len(raw5)}")

    # ---------------- 3. 反向重建 ----------------
    print("\n--- 3. 反向重建（生成器常量 + diff 两条独立路径）---")
    ok_gen = False
    try:
        rebuilt_gen = rebuild_from_generator(txt4)
        ok_gen = rebuilt_gen.encode("utf-8") == raw5
        info(f"生成器常量重建: bytes={len(rebuilt_gen.encode('utf-8'))} "
             f"LF16={lf16(rebuilt_gen.encode('utf-8'))} 逐字节相等={ok_gen}")
    except Exception as e:
        info(f"生成器常量重建异常: {e!r}")
    chk("3a", "用 _gen_harness5.py 的 ANCHOR/PATCH 常量可逐字节重建 harness5",
        ok_gen)

    ok_diff = False
    try:
        diff_text = DIFF.read_text(encoding="utf-8")
        rebuilt_diff = apply_unified_diff(txt4.split("\n"), diff_text)
        rebuilt_bytes = "\n".join(rebuilt_diff).encode("utf-8")
        ok_diff = rebuilt_bytes == raw5
        info(f"a8b.diff 重建: bytes={len(rebuilt_bytes)} "
             f"LF16={lf16(rebuilt_bytes)} 逐字节相等={ok_diff}")
    except Exception as e:
        info(f"diff 重建异常: {e!r}")
    chk("3b", "用 a8b.diff 可逐字节重建 harness5", ok_diff)

    # ---------------- 4. AST 零改动面 ----------------
    print("\n--- 4. AST 零改动面（按函数名分组比对 ast.dump）---")
    a4 = func_ast_map(txt4)
    a5 = func_ast_map(txt5)
    added = sorted(set(a5) - set(a4))
    removed = sorted(set(a4) - set(a5))
    changed = sorted(k for k in set(a4) & set(a5) if a4[k] != a5[k])
    info(f"h4 函数/类={len(a4)}  h5 函数/类={len(a5)}")
    info(f"新增={added}")
    info(f"删除={removed}")
    info(f"变更={changed}")
    chk("4a", "新增符号只有 _a8_enum_probe", added == ["def:_a8_enum_probe"], str(added))
    chk("4b", "无任何函数/类被删除", removed == [], str(removed))
    chk("4c", "变更面仅 a8_sweep_carrier_processes",
        changed == ["def:a8_sweep_carrier_processes"], str(changed))

    seg4 = top_level_segment(txt4, "find_pids")
    seg5 = top_level_segment(txt5, "find_pids")
    same_fp = seg4 is not None and seg4 == seg5
    info(f"find_pids 源码段 sha16={hashlib.sha256((seg5 or '').encode()).hexdigest()[:16]} "
         f"len={len(seg5 or '')}")
    chk("4d", "find_pids 逐字节相同（实现者声称不改本体）", same_fp)

    # ---------------- 5. 不新增退出码 ----------------
    print("\n--- 5. 不新增退出码 ---")
    def exit_codes(src):
        codes = {}
        for node in ast.parse(src).body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id.startswith("EXIT_")):
                try:
                    codes[node.targets[0].id] = ast.literal_eval(node.value)
                except Exception:
                    codes[node.targets[0].id] = "?"
        return codes
    e4, e5 = exit_codes(txt4), exit_codes(txt5)
    info(f"h4 EXIT_*={len(e4)}  h5 EXIT_*={len(e5)}")
    info(f"新增={sorted(set(e5) - set(e4))}  删除={sorted(set(e4) - set(e5))}")
    chk("5", "EXIT_* 定义集合与取值完全一致",
        set(e4) == set(e5) and all(e4[k] == e5[k] for k in e4),
        f"added={sorted(set(e5) - set(e4))} removed={sorted(set(e4) - set(e5))}")

    # ---------------- 6. 禁止面 ----------------
    print("\n--- 6. 禁止面（只看新增行）---")
    added_lines = Counter(txt5.split("\n")) - Counter(txt4.split("\n"))
    added_text = "\n".join(ln for ln, n in added_lines.items() for _ in range(n))
    forbidden = ["taskkill", "SendMessage", "PostMessage", "SendInput",
                 "WriteProcessMemory", "CreateRemoteThread", "RegSetValue",
                 "RegCreateKey", "RegDeleteKey", "RegOpenKey", "winreg",
                 "QueueUserAPC", "SetWindowsHookEx", "DebugActiveProcess"]
    hits = {tok: added_text.count(tok) for tok in forbidden}
    info(f"新增行数={len(added_text.split(chr(10)))}")
    info(f"新增行内禁用词命中={ {k: v for k, v in hits.items() if v} or 'none'}")
    chk("6a", "新增行不含任何禁用 API / taskkill / 注册表写",
        all(v == 0 for v in hits.values()), str({k: v for k, v in hits.items() if v}))
    # 全量计数：新增不得让任何禁用词出现次数上升
    full4 = {tok: txt4.count(tok) for tok in forbidden}
    full5 = {tok: txt5.count(tok) for tok in forbidden}
    grown = {k: (full4[k], full5[k]) for k in forbidden if full5[k] > full4[k]}
    info(f"全量计数（h4→h5）={full5}")
    chk("6b", "任何禁用词的全量出现次数都未上升", not grown, str(grown) or "none")
    # taskkill 仅存在于注释/文档串：用 tokenize 判定每次出现落在哪种 token 内
    import tokenize
    def taskkill_token_kinds(src_text):
        kinds = []
        toks = list(tokenize.generate_tokens(io.StringIO(src_text).readline))
        for tok in toks:
            if "taskkill" in tok.string:
                kinds.append((tokenize.tok_name[tok.type], tok.start[0]))
        return kinds
    tk5 = taskkill_token_kinds(txt5)
    tk4 = taskkill_token_kinds(txt4)
    info(f"taskkill token 归类(h5)={tk5}")
    info(f"taskkill token 归类(h4)={tk4}")
    code_hits5 = [k for k in tk5 if k[0] not in ("STRING", "COMMENT")]
    chk("6c", "taskkill 只出现在 STRING/COMMENT token 内（无按名全杀调用）",
        not code_hits5 and len(tk5) == len(tk4), str(code_hits5) or "none")

    # ---------------- 9. 零删除行 ----------------
    print("\n--- 9. 零删除行（Counter 多重集）---")
    cnt4, cnt5 = Counter(txt4.split("\n")), Counter(txt5.split("\n"))
    gone = {ln: (cnt4[ln], cnt5[ln]) for ln in cnt4 if cnt5[ln] < cnt4[ln]}
    info(f"行数 h4={len(txt4.split(chr(10)))} h5={len(txt5.split(chr(10)))}")
    info(f"缺失行数={len(gone)}")
    chk("9", "harness4 的每一行在 harness5 中仍存在（零删除行）", not gone,
        str(list(gone.items())[:3]))

    # ---------------- 10. 合成冒烟 ----------------
    print("\n--- 10. 合成冒烟（ast.parse，不执行主流程）---")
    ok_parse = True
    try:
        ast.parse(txt5, filename=str(H5))
    except SyntaxError as e:
        ok_parse = False
        info(f"SyntaxError: {e}")
    chk("10", "harness5 通过 ast.parse", ok_parse)

    # ---------------- 7. 探针逻辑正确性（实际执行） ----------------
    print("\n--- 7. 探针逻辑正确性（实际 import 并调用）---")
    m5 = load_mod(H5, "_a8b_h5_verify")
    probe = getattr(m5, "_a8_enum_probe", None)
    chk("7a", "harness5 可安全 import 且含 _a8_enum_probe", probe is not None)

    rec = FakeRec()
    r_pos = probe(rec, "verify_positive")
    info(f"self_name={r_pos['self_name']!r} self_pid={r_pos['self_pid']} "
         f"found={r_pos['found'][:10]} ok={r_pos['ok']}")
    chk("7b", "正控：正常环境 ok=True 且 self_pid 在 found 中",
        r_pos["ok"] is True and r_pos["self_pid"] in r_pos["found"],
        f"ok={r_pos['ok']}")
    chk("7c", "探针留痕 a8_enum_probe_ok=True",
        True in rec.values_of("a8_enum_probe_ok"),
        str(rec.keys()[:8]))

    orig_fp = m5.find_pids
    try:
        m5.find_pids = lambda name: []          # ★ 模拟快照失败
        rec_neg = FakeRec()
        r_neg = probe(rec_neg, "verify_negative")
        info(f"负控 probe: found={r_neg['found']} ok={r_neg['ok']}")
        chk("7d", "负控：find_pids 恒空 ⇒ 探针 ok=False", r_neg["ok"] is False,
            f"ok={r_neg['ok']}")

        rec_sweep = FakeRec()
        carrier = HERE / "_a8b_never_created_dir"
        info(f"载体目录存在={carrier.exists()}  path={carrier}")
        res_neg = m5.a8_sweep_carrier_processes(rec_sweep, carrier, None)
        info(f"sweep 返回: swept={res_neg['swept']} remaining={res_neg['remaining']} "
             f"rounds={res_neg['rounds']} enum_probe_ok={res_neg.get('enum_probe_ok')}")
        nonempty = bool(res_neg["remaining"])
        has_sentinel = any("ENUM_FAILED" in str(r.get("image", ""))
                           for r in res_neg["remaining"])
        no_kill = res_neg["swept"] == []
        chk("7e", "负控：清扫返回 remaining 非空", nonempty, str(res_neg["remaining"]))
        chk("7f", "负控：remaining 含 ENUM_FAILED 哨兵", has_sentinel)
        chk("7g", "负控：swept 为空（没有误杀）", no_kill, str(res_neg["swept"]))
        chk("7h", "负控：a8_enum_verdict 记录 FAIL",
            "FAIL" in rec_sweep.values_of("a8_enum_verdict"),
            str(rec_sweep.values_of("a8_enum_verdict")))

        # 7i：收尾探针失效（中途坏掉）也必须拦下
        calls = {"n": 0}
        def flaky(name):
            calls["n"] += 1
            if calls["n"] <= 3:      # 1=before_sweep, 2/3=清扫循环
                return orig_fp(name)
            return []
        m5.find_pids = flaky
        rec_mid = FakeRec()
        res_mid = m5.a8_sweep_carrier_processes(rec_mid, carrier, None)
        info(f"中途坏掉: find_pids 调用 {calls['n']} 次；remaining={res_mid['remaining']} "
             f"swept={res_mid['swept']}")
        mid_ok = (any("ENUM_FAILED_BEFORE_REMAINING" in str(r.get("image", ""))
                      for r in res_mid["remaining"]) and res_mid["swept"] == [])
        chk("7i", "收尾探针失败 ⇒ 返回 <ENUM_FAILED_BEFORE_REMAINING> 且未误杀", mid_ok)

        # 7j：正常路径（真实枚举器 + 不存在的载体目录）
        m5.find_pids = orig_fp
        rec_ok = FakeRec()
        res_ok = m5.a8_sweep_carrier_processes(rec_ok, carrier, None)
        info(f"正控 sweep: remaining={res_ok['remaining']} swept={res_ok['swept']} "
             f"rounds={res_ok['rounds']}")
        chk("7j", "正控：真实枚举器 + 空载体目录 ⇒ remaining 为空且 swept 为空",
            res_ok["remaining"] == [] and res_ok["swept"] == [],
            f"remaining={res_ok['remaining']}")

        # 7k：枚举器抛异常（另一种失效形态）也必须判失败
        def boom(name):
            raise OSError("simulated CreateToolhelp32Snapshot failure")
        m5.find_pids = boom
        rec_exc = FakeRec()
        r_exc = probe(rec_exc, "verify_raise")
        info(f"抛异常时: ok={r_exc['ok']} error={r_exc['error']}")
        chk("7k", "负控：find_pids 抛异常 ⇒ 探针 ok=False（异常不逃逸）",
            r_exc["ok"] is False and r_exc["error"] is not None,
            f"ok={r_exc['ok']}")
    finally:
        m5.find_pids = orig_fp

    # ---------------- 8. 探针顺序 ----------------
    print("\n--- 8. 探针顺序（静态定位）---")
    p_before = txt5.find('_a8_enum_probe(rec, "before_sweep")')
    sweep_loop = txt5.find("for _round in range(3):", p_before if p_before > 0 else 0)
    p_after = txt5.find('_a8_enum_probe(rec, "before_remaining")')
    rem_enum = txt5.find("remaining = []", p_after if p_after > 0 else 0)
    ret = txt5.find('return {"swept": swept, "remaining": remaining, "rounds": rounds}',
                    rem_enum if rem_enum > 0 else 0)
    info(f"before_sweep@{p_before} < sweep_loop@{sweep_loop} < "
         f"before_remaining@{p_after} < remaining_enum@{rem_enum} < return@{ret}")
    chk("8a", "顺序正确：清扫前探针 → 清扫循环 → 收尾探针 → remaining 枚举 → 返回",
        0 < p_before < sweep_loop < p_after < rem_enum < ret)
    # 探针必须在同一个函数体内（不是别处）
    fn_start = txt5.rfind("def a8_sweep_carrier_processes(", 0, p_before)
    fn_end = txt5.find("\ndef ", p_before)
    in_fn = fn_start != -1 and fn_end != -1 and fn_start < p_before < p_after < fn_end
    chk("8b", "两次探针调用都在 a8_sweep_carrier_processes 函数体内", in_fn)
    # 调用方确实按 remaining 非空走 V-fail
    caller_ok = ("if _a8_res[\"remaining\"]:" in txt5
                 and "note_cleanup_failure(" in txt5)
    chk("8c", "调用方以 remaining 非空 ⇒ note_cleanup_failure（V-fail 路径存在）",
        caller_ok)

    # ---------------- 汇总 ----------------
    print("\n" + "=" * 78)
    conf = [r for r in RESULTS if r[2] == "CONFIRMED"]
    ref = [r for r in RESULTS if r[2] == "REFUTED"]
    print(f"总计 {len(RESULTS)} 项：CONFIRMED={len(conf)}  REFUTED={len(ref)}")
    if ref:
        for item, title, _, detail in ref:
            print(f"  REFUTED {item}: {title}  {detail}")
    print(f"LF16(h4)={b4}  LF16(h5)={l5}  CRLF16(h5)={c5}  bytes(h5)={len(raw5)}")
    print("RESULT:", "ALL CONFIRMED" if not ref else "HAS REFUTED")
    print("=" * 78)
    return 0 if not ref else 1


if __name__ == "__main__":
    sys.exit(main())
