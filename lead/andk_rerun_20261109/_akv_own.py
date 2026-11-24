# -*- coding: utf-8 -*-
"""_akv_own.py — 独立复核员自写的最小实现（不 import / 不复用 _ak_shell.py）。

覆盖：
  - 四件 A/B/C 逐输入判定 + 显式 AND_k(k=2) + BAD_NEEDLE_CAUGHT
  - 36 行坏针矩阵逐格实跑，逐格打印 EXIT/STDOUT/FAIL_ITEMS/是否被抓
  - 4 格「注入后仍 PASS」自己复现并检查 stdout 与 A 基线逐字节相同
  - d28 parents[2] 路径布局陷阱（放浅一层 → EXIT=2）与输入确实来自沙箱的探针
  - 上游脚本侧注射复现（BASE vs INJ stdout 逐字一致）
  - 每次跑完独立 hashlib 复核 15 个原件 SHA256/字节未变
所有写入只在 lead/andk_rerun_20261109/_akv_own/ 与 _akv_own* 文件。
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
WD = LEAD / "andk_rerun_20261109"
LAB = WD / "_akv_own"
SENT = "AKV_ZERO_HIT_NEEDLE_20261109"

# -- 与 _ak_shell.py 不同的配置结构：按「源码/输入/布局」分开写 --
SRC = {
    "d27": dict(folder="d27_ruling_20261106", script="check_d27.py", ruling="RULING_D27.md",
                a="外推", b="卡顿不存在", or_item=6, decl="main", lit4="循环论证"),
    "d28": dict(folder="d28_ruling_20261106", script="check_d28.py", ruling="RULING_D28.md",
                a="历史数字", b="1681", or_item=4, decl="q1q2", lit4=None),
    "d29": dict(folder="d29_ruling_20261106", script="check_d29.py", ruling="RULING_D29.md",
                a="互斥", b="前提", or_item=4, decl="q1", lit4=None),
    "d30": dict(folder="d30_ruling_20261106", script="check_d30.py", ruling="RULING_D30.md",
                a="93.98", b="误报率", or_item=4, decl="q1", lit4=None),
}
SEQ = ("d27", "d28", "d29", "d30")

TRACKED = (
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
    "lead/d27_ruling_20261106/RULING_D27.md",
    "lead/d27_ruling_20261106/FACTCHECK.md",
    "lead/d28_ruling_20261106/RULING_D28.md",
    "lead/d28_ruling_20261106/FACTCHECK.md",
    "lead/d29_ruling_20261106/RULING_D29.md",
    "lead/d29_ruling_20261106/FACTCHECK.md",
    "lead/d30_ruling_20261106/RULING_D30.md",
    "lead/d30_ruling_20261106/FACTCHECK.md",
    "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md",
)
BASELINE = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/d27_ruling_20261106/check_d27.py": ("3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", 3764),
    "lead/d28_ruling_20261106/check_d28.py": ("5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268", 4539),
    "lead/d29_ruling_20261106/check_d29.py": ("2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", 3906),
    "lead/d30_ruling_20261106/check_d30.py": ("6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", 3926),
    "lead/d27_ruling_20261106/RULING_D27.md": ("a4f56e0f416ee90acaff0b55bcaf77b4ad15d5db55b28a8f0c12329f988b3d0e", 17658),
    "lead/d27_ruling_20261106/FACTCHECK.md": ("5a133088c6f99568b0c0ef22d62ab759e4e08ca2008ca059941d885dc05cecb6", 17837),
    "lead/d28_ruling_20261106/RULING_D28.md": ("29bb247fbf82d80adf8c9753a7bb3b6d18dfe6bd0583ff1f87f860fb763b5f15", 13897),
    "lead/d28_ruling_20261106/FACTCHECK.md": ("f2de988ee2ab0402919c36bf765bb203ff4e4f443a2dd0bc8589ef8d9b114426", 13028),
    "lead/d29_ruling_20261106/RULING_D29.md": ("325c950eec4d3275436c10f2d7fd83c738adacdeb489c1e9f0e37a7e17212afb", 12258),
    "lead/d29_ruling_20261106/FACTCHECK.md": ("0661f666bc4af56c70baf3aa340943051d1e6ff6dee6041f943d14f08af46767", 12647),
    "lead/d30_ruling_20261106/RULING_D30.md": ("d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f", 13197),
    "lead/d30_ruling_20261106/FACTCHECK.md": ("2981848eec1b16b0af6fc26233439f665299a45b191f8e1ffd02f8a7d84aef59", 11394),
    "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md": ("a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798", 63656),
}

RUNLOG = []


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def originals_unchanged() -> bool:
    for rel, (h, n) in BASELINE.items():
        q = ROOT / rel
        if not q.is_file():
            return False
        raw = q.read_bytes()
        if (digest(raw), len(raw)) != (h, n):
            return False
    return True


def load_original(gate):
    c = SRC[gate]
    d = LEAD / c["folder"]
    return (d / c["script"]).read_bytes(), (d / c["ruling"]).read_bytes(), (d / "FACTCHECK.md").read_bytes()


def fresh(tag: str):
    """独立布局：返回 (script_path, input_dir, cwd, note)。"""
    r = LAB / tag
    if r.exists():
        shutil.rmtree(r)
    if tag.startswith("d27"):
        sd, idir, cwd = r, r / "lead" / "d27_ruling_20261106", r
        note = "d27: cwd=R, DIRECTORY=Path('lead/d27_ruling_20261106') 相对 cwd"
    elif tag.startswith("d28"):
        sd, idir, cwd = r / "a" / "b", r / "lead" / "d28_ruling_20261106", r
        note = "d28: script=R/a/b, parents[2]=R, input=R/lead/d28_ruling_20261106"
    elif tag.startswith("d29"):
        sd, idir, cwd = r, r, r
        note = "d29: script与input同目录 R, __file__.parent=R"
    elif tag.startswith("d30"):
        sd, idir, cwd = r, r, r
        note = "d30: script与input同目录 R, __file__.parent=R"
    else:
        raise ValueError(tag)
    sd.mkdir(parents=True, exist_ok=True)
    idir.mkdir(parents=True, exist_ok=True)
    return sd, idir, cwd, note


def one_run(tag: str, gate: str, script: bytes, docs: dict, label: str,
            script_dir_override=None):
    sd, idir, cwd, note = fresh(tag)
    if script_dir_override is not None:
        sd = script_dir_override
        sd.mkdir(parents=True, exist_ok=True)
    sp = sd / ("probe_%s.py" % gate)
    sp.write_bytes(script)
    for name, raw in docs.items():
        (idir / name).write_bytes(raw)
    argv = [sys.executable, "-I", "-X", "utf8", str(sp)]
    p = subprocess.run(argv, cwd=str(cwd), capture_output=True)
    ok = originals_unchanged()
    text = p.stdout.decode("utf-8", errors="replace")
    verdict = "PASS" if (p.returncode == 0 and "PASS" in text and "FAIL" not in text) else "FAIL"
    items = sorted({int(x) for x in re.findall(r"\[(\d+)\]", text)})
    rec = dict(label=label, gate=gate, tag=tag, cmd=argv, cwd=str(cwd),
               script_path=str(sp), script_sha256=digest(script), script_bytes=len(script),
               inputs={n: [digest(v), len(v)] for n, v in docs.items()},
               exit=p.returncode, stdout=text, stdout_sha256=digest(p.stdout),
               stderr=p.stderr.decode("utf-8", errors="replace"),
               verdict=verdict, fail_items=items, originals_unchanged=ok, note=note)
    RUNLOG.append(rec)
    return rec


# ------------------------------------------------------------------ 变体
def script_variant(gate: str, kind: str, original: bytes):
    c = SRC[gate]
    t = original.decode("utf-8")
    tup = '("%s", "%s")' % (c["a"], c["b"])
    if kind == "BASE":
        return original, "原件逐字节副本"
    assert t.count(tup) == 1, (gate, "tuple count", t.count(tup))
    w = {"WA": c["a"], "WB": c["b"], "SENT": SENT}[kind]
    return t.replace(tup, '("%s",)' % w, 1).encode("utf-8"), "OR 元组 -> 单元素 %r" % w


def upstream_injection(gate: str, original: bytes):
    """脚本侧：只把第二根针字面量换成哨兵，OR 结构不变、输入不变。"""
    c = SRC[gate]
    t = original.decode("utf-8")
    needle = '"%s"' % c["b"]
    assert t.count(needle) == 1, (gate, "needle count", t.count(needle))
    return t.replace(needle, '"%s"' % SENT, 1).encode("utf-8")


def doc_variant(gate: str, kind: str, ruling: bytes, fact: bytes):
    """返回 (docs dict, 描述)。与 _ak_shell.make_docs 独立实现。"""
    c = SRC[gate]
    rn = c["ruling"]
    r = ruling.decode("utf-8")
    f = fact.decode("utf-8")
    docs = {rn: r.encode("utf-8"), "FACTCHECK.md": f.encode("utf-8")}
    if kind in ("A", "NONE"):
        return docs, "A：原件逐字节副本，两词都在"
    if kind == "B":
        nb = r.count(c["b"])
        assert nb >= 1
        r = r.replace(c["b"], "")
        docs[rn] = r.encode("utf-8")
        return docs, "B：删第二根针 %r 共 %d 处（第一根针保留）" % (c["b"], nb)
    if kind == "C":
        na, nb = r.count(c["a"]), r.count(c["b"])
        assert na >= 1 and nb >= 1
        r = r.replace(c["a"], "").replace(c["b"], "")
        docs[rn] = r.encode("utf-8")
        return docs, "C：两词全删 %r(%d) + %r(%d)" % (c["a"], na, c["b"], nb)
    raise ValueError(kind)


def matrix_mutation(gate: str, code: str, ruling: bytes, fact: bytes):
    """9 行坏针注射的独立实现。返回 (docs, 描述, 期望触发的检查项号)。"""
    c = SRC[gate]
    rn = c["ruling"]
    r = ruling.decode("utf-8")
    f = fact.decode("utf-8")
    docs = {rn: None, "FACTCHECK.md": fact}

    if code == "M1":                       # [1] 缺文件
        docs = {"FACTCHECK.md": fact}
        # 为保证是「缺 RULING 还是缺 FACTCHECK」与执行员同口径，删 FACTCHECK
        docs = {rn: ruling}
        return docs, "[1] 删 FACTCHECK.md（缺文件）", 1
    if code == "M2":                       # [2] 声明行
        if c["decl"] == "main":
            r, n = re.subn(r"(?m)^main:[^\n]*$", "main: AKV_BROKEN_DECL", r)
            assert n == 1
        elif c["decl"] == "q1":
            r, n = re.subn(r"(?m)^q1:[^\n]*$", "q1: AKV_BROKEN_DECL", r)
            assert n == 1
        else:
            r, n = re.subn(r"(?m)^(q1|q2):[^\n]*$", lambda m: m.group(1) + ": AKV_BROKEN_DECL", r)
            assert n == 2, (gate, n)
        docs[rn] = r.encode("utf-8")
        return docs, "[2] 声明行改成非法值（%d 行）" % n, 2
    if code == "M3":                       # [3] 必需小节
        r, n = re.subn(r"(?m)^(##[ \t]+\d+[.、．]?[ \t]*)诚实账[ \t]*$", r"\1AKV_诚实账改名", r)
        assert n == 1, (gate, n)
        docs[rn] = r.encode("utf-8")
        return docs, "[3] 把『## 7 诚实账』改名，7 个必需小节缺 1", 3
    if code == "M4":                       # d27 [4] 单字面量
        assert c["lit4"] and r.count(c["lit4"]) >= 1
        n = r.count(c["lit4"])
        r = r.replace(c["lit4"], "")
        docs[rn] = r.encode("utf-8")
        return docs, "[4] 删单一字面量 %r（%d 处）" % (c["lit4"], n), 4
    if code == "M5":                       # [5] 本次不授权
        n = r.count("本次不授权")
        assert n >= 1
        r = r.replace("本次不授权", "")
        docs[rn] = r.encode("utf-8")
        return docs, "[5] 删『本次不授权』（%d 处）" % n, 5
    if code == "MOR":                      # OR 项：两词全删
        na, nb = r.count(c["a"]), r.count(c["b"])
        assert na >= 1 and nb >= 1
        r = r.replace(c["a"], "").replace(c["b"], "")
        docs[rn] = r.encode("utf-8")
        return docs, "[%d] OR 两词全删 %r(%d)+%r(%d)" % (c["or_item"], c["a"], na, c["b"], nb), c["or_item"]
    if code == "MORB":                     # ★ 只杀一根针
        nb = r.count(c["b"])
        assert nb >= 1
        r = r.replace(c["b"], "")
        docs[rn] = r.encode("utf-8")
        return docs, "[%db] OR 只杀第二根针 %r（%d 处），第一根 %r 保留" % (c["or_item"], c["b"], nb, c["a"]), c["or_item"]
    if code == "M6":                       # d28/29/30 [6] AND 词表删『外推』
        n = r.count("外推")
        assert n >= 1
        r = r.replace("外推", "")
        docs[rn] = r.encode("utf-8")
        return docs, "[6] 删 AND 词表里的『外推』（%d 处）" % n, 6
    if code == "M7":                       # [7] 引用行号
        r, n = re.subn(r"(\.(?:md|py|json)):(\d+)", r"\1:AKV_NOT_A_NUMBER", r)
        assert n >= 8, (gate, n)
        docs[rn] = r.encode("utf-8")
        return docs, "[7] 把 %d 处 file:line 的行号换成非数字" % n, 7
    if code == "M8":                       # [8] selfBias
        n = f.count("selfBias")
        assert n >= 1
        f = f.replace("selfBias", "")
        docs["FACTCHECK.md"] = f.encode("utf-8")
        docs[rn] = ruling
        return docs, "[8] FACTCHECK 删 selfBias（%d 处）" % n, 8
    raise ValueError(code)


MATRIX = {
    "d27": [("1", "M1"), ("2", "M2"), ("3", "M3"), ("4", "M4"), ("5", "M5"),
            ("6", "MOR"), ("6b", "MORB"), ("7", "M7"), ("8", "M8")],
    "d28": [("1", "M1"), ("2", "M2"), ("3", "M3"), ("4", "MOR"), ("4b", "MORB"),
            ("5", "M5"), ("6", "M6"), ("7", "M7"), ("8", "M8")],
    "d29": [("1", "M1"), ("2", "M2"), ("3", "M3"), ("4", "MOR"), ("4b", "MORB"),
            ("5", "M5"), ("6", "M6"), ("7", "M7"), ("8", "M8")],
    "d30": [("1", "M1"), ("2", "M2"), ("3", "M3"), ("4", "MOR"), ("4b", "MORB"),
            ("5", "M5"), ("6", "M6"), ("7", "M7"), ("8", "M8")],
}

LINES = []


def say(s=""):
    LINES.append(s)
    print(s)


def main():
    LAB.mkdir(parents=True, exist_ok=True)
    say("AKV INDEPENDENT RE-RUN — python %s" % sys.version.split()[0])
    say("ALL OUTPUTS UNDER %s" % LAB)
    say("")

    # ---------------- 基线 + A/B/C ----------------
    abc = {}
    for gate in SEQ:
        orig, ruling, fact = load_original(gate)
        say("==== %s : BASELINE / A / B / C ====" % gate)
        base = one_run("%s_base" % gate, gate, orig, {SRC[gate]["ruling"]: ruling, "FACTCHECK.md": fact}, "%s_BASE" % gate)
        say("BASE  EXIT=%d %r script_sha=%s" % (base["exit"], base["stdout"], base["script_sha256"][:16]))
        for inp in ("A", "B", "C"):
            docs, desc = doc_variant(gate, inp, ruling, fact)
            row = {}
            for kind in ("BASE", "WA", "WB", "SENT"):
                sb, sd = script_variant(gate, kind, orig)
                row[kind] = one_run("%s_%s_%s" % (gate, inp, kind), gate, sb, docs,
                                    "%s_%s_%s" % (gate, inp, kind))
            pwa = row["WA"]["verdict"] == "PASS" and row["WA"]["exit"] == 0
            pwb = row["WB"]["verdict"] == "PASS" and row["WB"]["exit"] == 0
            caught = row["SENT"]["verdict"] == "FAIL" and row["SENT"]["exit"] != 0
            agg = pwa and pwb
            abc["%s_%s" % (gate, inp)] = dict(
                original_exit=row["BASE"]["exit"], original_stdout=row["BASE"]["stdout"],
                original_stdout_sha256=row["BASE"]["stdout_sha256"],
                p_wa=pwa, p_wb=pwb, and_k=agg, bad_needle_caught=caught,
                distinguishable_pass=(agg and caught),
                doc_desc=desc,
                runs={k: dict(exit=v["exit"], verdict=v["verdict"], stdout=v["stdout"],
                              stdout_sha256=v["stdout_sha256"], cmd=v["cmd"]) for k, v in row.items()})
            say("  input %s  original EXIT=%d %r" % (inp, row["BASE"]["exit"], row["BASE"]["stdout"]))
            say("     WA EXIT=%d %r | WB EXIT=%d %r | SENT EXIT=%d %r" %
                (row["WA"]["exit"], row["WA"]["stdout"], row["WB"]["exit"], row["WB"]["stdout"],
                 row["SENT"]["exit"], row["SENT"]["stdout"]))
            say("     P_WA=%s P_WB=%s AND_2=%s BAD_NEEDLE_CAUGHT=%s DISTINGUISHABLE_PASS=%s" %
                (pwa, pwb, agg, caught, agg and caught))
            if inp == "B":
                say("     ★ B 原件 stdout 与 A 原件 stdout 逐字节相同 = %s" %
                    (row["BASE"]["stdout_sha256"] == abc["%s_A" % gate]["original_stdout_sha256"]))
        say("")

    # ---------------- 36 行矩阵逐格 ----------------
    say("==== BAD-NEEDLE MATRIX : 36 CELLS, ONE REAL SUBPROCESS PER CELL ====")
    matrix = []
    for gate in SEQ:
        orig, ruling, fact = load_original(gate)
        pre = one_run("%s_mat_pre" % gate, gate, orig,
                      {SRC[gate]["ruling"]: ruling, "FACTCHECK.md": fact}, "%s_MATRIX_PRE" % gate)
        say("--- %s (注入前 BASE EXIT=%d %r) ---" % (gate, pre["exit"], pre["stdout"]))
        for item, code in MATRIX[gate]:
            docs, desc, expected = matrix_mutation(gate, code, ruling, fact)
            post = one_run("%s_mat_%s" % (gate, item), gate, orig, docs,
                           "%s_ITEM_%s" % (gate, item))
            caught = (post["exit"] != 0 and post["verdict"] == "FAIL")
            intended = expected in post["fail_items"]
            same_as_a = post["stdout"] == abc["%s_A" % gate]["original_stdout"]
            rec = dict(gate=gate, item=item, code=code, desc=desc, expected_item=expected,
                       before_exit=pre["exit"], before_verdict=pre["verdict"],
                       after_exit=post["exit"], after_verdict=post["verdict"],
                       after_stdout=post["stdout"], after_stdout_sha256=post["stdout_sha256"],
                       fail_items=post["fail_items"], intended_item_failed=intended,
                       caught=caught, stdout_same_as_A=same_as_a, cmd=post["cmd"],
                       script_sha256=post["script_sha256"])
            matrix.append(rec)
            say("  [%s] item %-3s %s" % (gate, item, desc))
            say("       CMD = %s" % " ".join('"%s"' % x for x in post["cmd"]))
            say("       EXIT %d -> %d | verdict %s -> %s | FAIL_ITEMS=%s | 期望项%d命中=%s | 是否被抓=%s" %
                (pre["exit"], post["exit"], pre["verdict"], post["verdict"],
                 post["fail_items"], expected, intended, caught))
            say("       STDOUT = %r" % post["stdout"])
            if post["verdict"] == "PASS":
                say("       ★★ 注入后仍 PASS：stdout 与 A 基线逐字节相同 = %s（sha256=%s）" %
                    (same_as_a, post["stdout_sha256"]))
        say("")

    andm = {}
    for gate in SEQ:
        rows = [m for m in matrix if m["gate"] == gate]
        eight = [m for m in rows if not m["item"].endswith("b")]
        andm[gate] = dict(and_8=all(m["caught"] for m in eight),
                          and_9=all(m["caught"] for m in rows),
                          caught=sum(1 for m in rows if m["caught"]),
                          rows=len(rows),
                          missed=[m["item"] for m in rows if not m["caught"]],
                          nonintended=[m["item"] for m in rows if not m["intended_item_failed"]])
        say("%s : AND_8=%s AND_9=%s caught=%d/%d missed=%r nonintended_fail_items=%r" %
            (gate, andm[gate]["and_8"], andm[gate]["and_9"], andm[gate]["caught"],
             andm[gate]["rows"], andm[gate]["missed"], andm[gate]["nonintended"]))
    say("")

    # ---------------- d28 parents[2] 布局陷阱 + 沙箱输入探针 ----------------
    say("==== d28 parents[2] LAYOUT TRAP + SANDBOX-INPUT PROBES ====")
    orig, ruling, fact = load_original("d28")
    docs = {"RULING_D28.md": ruling, "FACTCHECK.md": fact}
    # 正常布局
    good = one_run("d28_layout_ok", "d28", orig, docs, "D28_LAYOUT_OK")
    say(" 正常 R/a/b  : EXIT=%d %r" % (good["exit"], good["stdout"]))
    # 放浅一层：脚本 R/a/check.py，输入仍在 R/lead/d28_ruling_20261106
    shallow = one_run("d28_layout_shallow", "d28", orig, docs, "D28_SHALLOW",
                      script_dir_override=LAB / "d28_layout_shallow" / "a")
    say(" 浅一层 R/a  : EXIT=%d %r  (期望 2=文件缺失)" % (shallow["exit"], shallow["stdout"]))
    # 探针：把沙箱 RULING 写成空文件；若读到只读原件则不会报「为空」
    empty_docs = {"RULING_D28.md": b"", "FACTCHECK.md": fact}
    probe = one_run("d28_probe_empty", "d28", orig, empty_docs, "D28_PROBE_EMPTY")
    say(" 沙箱 RULING 置空: EXIT=%d %r  (出现『为空』证明读的是沙箱副本)" % (probe["exit"], probe["stdout"]))
    # 探针：删沙箱 RULING，检查缺失信息里的路径
    nodoc = {"FACTCHECK.md": fact}
    probe2 = one_run("d28_probe_missing", "d28", orig, nodoc, "D28_PROBE_MISSING")
    say(" 沙箱 RULING 缺失: EXIT=%d %r" % (probe2["exit"], probe2["stdout"]))
    say(" 脚本副本绝对路径 = %s" % probe2["script_path"])
    say("")

    # ---------------- 上游脚本侧注射复现 ----------------
    say("==== UPSTREAM SCRIPT-SIDE INJECTION REPRO (BASE vs INJ) ====")
    repro = {}
    for gate in SEQ:
        orig, ruling, fact = load_original(gate)
        inj = upstream_injection(gate, orig)
        docs = {SRC[gate]["ruling"]: ruling, "FACTCHECK.md": fact}
        b = one_run("%s_repro_base" % gate, gate, orig, docs, "%s_REPRO_BASE" % gate)
        u = one_run("%s_repro_inj" % gate, gate, inj, docs, "%s_REPRO_INJ" % gate)
        ident = (b["stdout"] == u["stdout"] and b["exit"] == u["exit"])
        repro[gate] = dict(base_exit=b["exit"], inj_exit=u["exit"],
                           base_stdout=b["stdout"], inj_stdout=u["stdout"],
                           stdout_identical=(b["stdout"] == u["stdout"]),
                           stdout_sha_identical=(b["stdout_sha256"] == u["stdout_sha256"]),
                           exit_identical=(b["exit"] == u["exit"]),
                           both_pass=(b["verdict"] == "PASS" and u["verdict"] == "PASS"),
                           inj_script_sha256=u["script_sha256"], inj_script_bytes=u["script_bytes"])
        say("  %s BASE EXIT=%d %r / INJ EXIT=%d %r" % (gate, b["exit"], b["stdout"], u["exit"], u["stdout"]))
        say("     stdout 逐字一致=%s stdout_sha 一致=%s EXIT 一致=%s 两者均 PASS=%s 完全一致=%s" %
            (repro[gate]["stdout_identical"], repro[gate]["stdout_sha_identical"],
             repro[gate]["exit_identical"], repro[gate]["both_pass"], ident))
        say("     INJ 脚本 sha256=%s bytes=%d" % (u["script_sha256"], u["script_bytes"]))
    say("")

    # ---------------- 汇总 ----------------
    say("==== SUMMARY ====")
    say("TOTAL_REAL_SUBPROCESS_RUNS = %d" % len(RUNLOG))
    say("ALL_RUNS_ORIGINALS_UNCHANGED = %s" % all(x["originals_unchanged"] for x in RUNLOG))
    say("FINAL_ORIGINALS_UNCHANGED = %s" % originals_unchanged())
    say("MATRIX_CELLS = %d ; CAUGHT = %d ; MISSED = %d" %
        (len(matrix), sum(1 for m in matrix if m["caught"]), sum(1 for m in matrix if not m["caught"])))
    still_pass = ["%s/%s" % (m["gate"], m["item"]) for m in matrix if m["after_verdict"] == "PASS"]
    say("CELLS_WITH_STILL_PASS = %r" % still_pass)
    for gate in SEQ:
        say("%s A=%s B=%s C=%s" % (gate,
            abc[gate + "_A"]["distinguishable_pass"],
            abc[gate + "_B"]["distinguishable_pass"],
            abc[gate + "_C"]["distinguishable_pass"]))

    payload = dict(python=sys.version.split()[0], total_runs=len(RUNLOG),
                   all_originals_unchanged=all(x["originals_unchanged"] for x in RUNLOG),
                   abc=abc, matrix=matrix, and_matrix=andm, repro=repro,
                   layout=dict(good=good, shallow=shallow, probe_empty=probe, probe_missing=probe2),
                   runs=RUNLOG)
    (WD / "_akv_own.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    (WD / "_akv_own_out.txt").write_text("\n".join(LINES) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
