# -*- coding: utf-8 -*-
"""_ak_shell.py — 甲' 可部署外壳（AND_k 重跑执行员，2026-11-09）

零真机 / 零采样代码 / 零进程内存读取。唯一写域 = lead/andk_rerun_20261109/。
所有被核脚本、输入文档均在写域沙箱内逐字节复制后执行；绝不运行原件、绝不改原件。

用法（全部 python -I -X utf8 + 绝对路径）：
  python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode selftest
  python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/andk_rerun_20261109/_ak_shell.py" --mode full

三套路径布局（显式，逐件不同，见 LAYOUT）：
  d27: DIRECTORY = Path("lead/d27_ruling_20261106")            -> CWD 相对；cwd = <sandbox>/<gate>/<exp>/
  d28: root = Path(__file__).resolve().parents[2]               -> 副本必须深 3 层；脚本在 <root>/a/b/，输入在 <root>/lead/d28_ruling_20261106/
  d29/d30: directory = Path(__file__).resolve().parent          -> 输入必须与副本脚本同目录
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
SRC = REPO / "lead"
WRITE = SRC / "andk_rerun_20261109"
WORK = WRITE / "sandbox"
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"

# 编排方实跑基线指纹（题给【编排方实跑：基线指纹】），用于每次跑完复核原件未变
ORCHESTRATOR_BASELINE = {
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

# 绝对只读域（两件台账 + 6 个目录），用于全量快照复核
READONLY_DIRS = [
    "lead/d27_ruling_20261106",
    "lead/d28_ruling_20261106",
    "lead/d29_ruling_20261106",
    "lead/d30_ruling_20261106",
    "lead/stale_pass_20261109",
    "lead/k1bit_detect_20261109",
    "lead/detect_triage_20261109",
    "lead/refsync_scope_20261109",
]
READONLY_FILES = ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]

GATES = {
    "d27": dict(dir="d27_ruling_20261106", check="check_d27.py", ruling="RULING_D27.md",
                words=("外推", "卡顿不存在"), or_tuple='("外推", "卡顿不存在")',
                or_item=6, or_line=84, decl="main", and_literal=None, lit4="循环论证"),
    "d28": dict(dir="d28_ruling_20261106", check="check_d28.py", ruling="RULING_D28.md",
                words=("历史数字", "1681"), or_tuple='("历史数字", "1681")',
                or_item=4, or_line=90, decl="q1/q2", and_literal="外推", lit4=None),
    "d29": dict(dir="d29_ruling_20261106", check="check_d29.py", ruling="RULING_D29.md",
                words=("互斥", "前提"), or_tuple='("互斥", "前提")',
                or_item=4, or_line=76, decl="q1", and_literal="外推", lit4=None),
    "d30": dict(dir="d30_ruling_20261106", check="check_d30.py", ruling="RULING_D30.md",
                words=("93.98", "误报率"), or_tuple='("93.98", "误报率")',
                or_item=4, or_line=76, decl="q1", and_literal="外推", lit4=None),
}
ORDER = ("d27", "d28", "d29", "d30")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path):
    b = path.read_bytes()
    return sha(b), len(b)


def write_text(name: str, text: str) -> None:
    with (WRITE / name).open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_json(name: str, obj) -> None:
    write_text(name, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def snapshot_all():
    """只读域全量快照：相对路径 -> [sha256, bytes]"""
    out = {}
    for rel in READONLY_FILES:
        p = REPO / rel
        h, n = digest(p)
        out[rel] = [h, n]
    for rel in READONLY_DIRS:
        for p in sorted((REPO / rel).rglob("*")):
            if p.is_file():
                h, n = digest(p)
                out[p.relative_to(REPO).as_posix()] = [h, n]
    return out


def verify_originals(strict=True):
    """每次跑完复核原件 SHA256 + 字节数未变（hashlib）。"""
    bad = []
    for rel, (h, n) in ORCHESTRATOR_BASELINE.items():
        p = REPO / rel
        if not p.is_file():
            bad.append((rel, "MISSING"))
            continue
        h2, n2 = digest(p)
        if (h2, n2) != (h, n):
            bad.append((rel, (h2, n2)))
    if bad and strict:
        raise RuntimeError("原件 SHA256 变化，中止: %r" % (bad,))
    return not bad


# ---------------------------------------------------------------- 路径布局
class Layout:
    def __init__(self, gate, root):
        self.gate = gate
        self.root = root
        if gate == "d27":
            # check_d27.py:8 DIRECTORY = Path("lead/d27_ruling_20261106") —— CWD 相对
            self.script_dir = root
            self.input_dir = root / "lead" / "d27_ruling_20261106"
            self.cwd = root
            self.note = ("CWD 相对：cwd=<root>；脚本=<root>/check_d27.py；"
                         "输入=<root>/lead/d27_ruling_20261106/；"
                         "DIRECTORY 相对 cwd 解析命中输入目录")
        elif gate == "d28":
            # check_d28.py:54-55 parents[2] / lead / d28_ruling_20261106
            self.script_dir = root / "a" / "b"
            self.input_dir = root / "lead" / "d28_ruling_20261106"
            self.cwd = root
            self.note = ("parents[2]：脚本=<root>/a/b/check_d28.py；"
                         "parents[2]=<root>；输入=<root>/lead/d28_ruling_20261106/；"
                         "若副本只放 <root>/a/（缺一层）则 parents[2] 指向别处 => EXIT=2")
        else:
            # check_d29.py:50 / check_d30.py:50 __file__.resolve().parent
            self.script_dir = root
            self.input_dir = root
            self.cwd = root
            self.note = ("同目录：脚本=<root>/check_dNN.py；输入=<root>/RULING_DNN.md + "
                         "<root>/FACTCHECK.md；directory=__file__.parent=<root>")
        self.cwd_resolve = str(self.cwd)


def script_bytes(gate, variant):
    """返回被核脚本副本的字节。BASE=原件逐字节副本；WA/WB/SENT=OR 元组单元素化；UP=上游注射。"""
    cfg = GATES[gate]
    p = SRC / cfg["dir"] / cfg["check"]
    b = p.read_bytes()
    t = b.decode("utf-8")
    if variant == "BASE":
        return b, "原件逐字节副本（未改一个字节）"
    if variant in ("WA", "WB", "SENT"):
        word = {"WA": cfg["words"][0], "WB": cfg["words"][1], "SENT": SENTINEL}[variant]
        assert t.count(cfg["or_tuple"]) == 1, (gate, "OR tuple occurrence != 1")
        new = '("%s",)' % word
        return t.replace(cfg["or_tuple"], new, 1).encode("utf-8"), \
            "OR 元组 %s -> 单元素 %s" % (cfg["or_tuple"], new)
    if variant == "UP":
        needle = '"%s"' % cfg["words"][1]
        assert t.count(needle) == 1, (gate, "needle occurrence != 1", t.count(needle))
        return t.replace(needle, '"%s"' % SENTINEL, 1).encode("utf-8"), \
            "上游口径：只把脚本里第二根针 %s 换成 %s（OR 结构不变）" % (needle, SENTINEL)
    raise ValueError(variant)


def original_docs(gate):
    cfg = GATES[gate]
    d = SRC / cfg["dir"]
    return {cfg["ruling"]: (d / cfg["ruling"]).read_bytes(),
            "FACTCHECK.md": (d / "FACTCHECK.md").read_bytes()}


def make_docs(gate, mut):
    """返回 (docs dict, 变更说明)。docs 缺 FACTCHECK.md 键 = 制造缺文件。"""
    cfg = GATES[gate]
    rn = cfg["ruling"]
    docs = original_docs(gate)
    r = docs[rn].decode("utf-8")
    f = docs["FACTCHECK.md"].decode("utf-8")
    wa, wb = cfg["words"]
    desc = "未改：两词都在，输入文档为原件逐字节副本"
    if mut in ("A", "BASE", "NONE"):
        pass
    elif mut in ("B", "OR_ONE"):
        n = r.count(wb)
        assert n > 0
        r = r.replace(wb, "")
        desc = "从 %s 全文删除第二根针 %r（%d 处）；第一根针 %r 保留" % (rn, wb, n, wa)
    elif mut in ("C", "OR_BOTH"):
        na, nb = r.count(wa), r.count(wb)
        assert na > 0 and nb > 0
        r = r.replace(wa, "").replace(wb, "")
        desc = "从 %s 全文删除两根针 %r(%d 处) 与 %r(%d 处)" % (rn, wa, na, wb, nb)
    elif mut == "I1":
        del docs["FACTCHECK.md"]
        desc = "删除 FACTCHECK.md（缺文件负控）"
    elif mut == "I2":
        r, n = re.subn(r"(?m)^(main|q1|q2):[^\n]*$",
                       lambda m: m.group(1) + ": NEEDLE_DELETED", r)
        assert n == (2 if gate == "d28" else 1), (gate, "decl count", n)
        desc = "把 %d 行合法声明改成不合法字面量" % n
    elif mut == "I3":
        r, n = re.subn(r"(?m)^##( [ \t]*\d+[.、．]?[ \t]+)诚实账[ \t]*$",
                       lambda m: "##" + m.group(1) + "诚实账_已删", r)
        assert n == 1, (gate, "heading count", n)
        desc = "把二级标题『## 7 诚实账』改名，使 7 个必需小节缺 1 个"
    elif mut == "I4LIT":
        lit = cfg["lit4"]
        assert lit and lit in r
        n = r.count(lit)
        r = r.replace(lit, "")
        desc = "删除 d27 第 4 项单一字面量 %r（%d 处）" % (lit, n)
    elif mut == "I5":
        n = r.count("本次不授权")
        assert n > 0
        r = r.replace("本次不授权", "")
        desc = "删除第 5 项单一字面量『本次不授权』（%d 处）" % n
    elif mut == "I6AND":
        lit = cfg["and_literal"]
        assert lit and lit in r
        n = r.count(lit)
        r = r.replace(lit, "")
        desc = "删除第 6 项 AND 词表里的 %r（%d 处）" % (lit, n)
    elif mut == "I7":
        r, n = re.subn(r"(\.(?:md|py|json)):\d+", r"\1:NEEDLE_DELETED", r)
        assert n >= 8, (gate, "citation count", n)
        desc = "把 %d 处 file:line 引用的行号换成非数字，令引用计数 <8" % n
    elif mut == "I8":
        n = f.count("selfBias")
        assert n > 0
        f = f.replace("selfBias", "")
        desc = "从 FACTCHECK.md 删除第 8 项字面量 selfBias（%d 处）" % n
    else:
        raise ValueError(mut)
    if rn in docs:
        docs[rn] = r.encode("utf-8")
    if "FACTCHECK.md" in docs:
        docs["FACTCHECK.md"] = f.encode("utf-8")
    return docs, desc


RUNS = []


def do_run(gate, exp, variant, mut, tag):
    """生成→落盘→驱动一次真实独立运行；返回逐运行记录。"""
    root = WORK / gate / exp
    if root.exists():
        shutil.rmtree(root)
    lay = Layout(gate, root)
    lay.script_dir.mkdir(parents=True, exist_ok=True)
    lay.input_dir.mkdir(parents=True, exist_ok=True)

    sb, script_desc = script_bytes(gate, variant)
    fname = "check_%s_%s.py" % (gate, variant)
    spath = lay.script_dir / fname
    spath.write_bytes(sb)
    docs, doc_desc = make_docs(gate, mut)
    for name, data in docs.items():
        (lay.input_dir / name).write_bytes(data)

    cmd_list = [sys.executable, "-I", "-X", "utf8", str(spath)]
    cmd = ' '.join('"%s"' % c if (' ' in c or '\\' in c) else c for c in cmd_list)
    p = subprocess.run(cmd_list, cwd=str(lay.cwd), capture_output=True)
    out = p.stdout.decode("utf-8", errors="replace")
    err = p.stderr.decode("utf-8", errors="replace")
    unchanged = verify_originals(strict=True)   # ★ 每次跑完复核原件 SHA256 未变
    verdict = "PASS" if (p.returncode == 0 and "PASS" in out and "FAIL" not in out) else "FAIL"
    fail_items = sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", out)))
    rec = dict(
        tag=tag, gate=gate, exp=exp, variant=variant, mut=mut,
        layout=lay.note, cwd=str(lay.cwd),
        script_path=str(spath), script_sha256=sha(sb), script_bytes=len(sb),
        script_desc=script_desc, doc_desc=doc_desc,
        inputs={n: dict(sha256=sha(d), bytes=len(d), path=str(lay.input_dir / n))
                for n, d in docs.items()},
        inputs_written=sorted(docs.keys()),
        cmd=cmd, python=sys.version.split()[0],
        exit=p.returncode, stdout=out, stderr=err,
        stdout_sha256=sha(p.stdout), stderr_sha256=sha(p.stderr),
        verdict=verdict, fail_items=fail_items,
        originals_unchanged=unchanged,
    )
    RUNS.append(rec)
    return rec


def fmt_run(rec):
    return ("[%s] gate=%s exp=%s variant=%s mut=%s\n"
            "  CMD = %s\n  CWD = %s\n"
            "  被核脚本 = %s sha256=%s bytes=%d\n"
            "  输入 = %s\n"
            "  EXIT = %d  verdict = %s  FAIL_ITEMS = %s\n"
            "  STDOUT = %r\n  STDERR = %r\n"
            "  stdout_sha256 = %s\n  原件未变 = %s\n" %
            (rec["tag"], rec["gate"], rec["exp"], rec["variant"], rec["mut"],
             rec["cmd"], rec["cwd"], rec["script_path"], rec["script_sha256"],
             rec["script_bytes"],
             ", ".join("%s(%s,%dB)" % (n, v["sha256"][:12], v["bytes"])
                       for n, v in sorted(rec["inputs"].items())),
             rec["exit"], rec["verdict"], rec["fail_items"],
             rec["stdout"], rec["stderr"], rec["stdout_sha256"],
             rec["originals_unchanged"]))


def items_for(gate):
    """每件 8 项 + OR 项额外一根「杀单针」哨兵，共 9 行。"""
    cfg = GATES[gate]
    if gate == "d27":
        rows = [
            (1, "[1] 两文件存在/非空/UTF-8", "I1"),
            (2, "[2] ^main:(A|B|C)$ 声明行", "I2"),
            (3, "[3] 7 个必需二级标题", "I3"),
            (4, "[4] 新证据是否成立 ⊇ 循环论证（单字面量）", "I4LIT"),
            (5, "[5] 授权边界 ⊇ 本次不授权（单字面量）", "I5"),
            (6, "[6] 未背书 ⊇ 外推 OR 卡顿不存在  ← OR 项（两词全删）", "OR_BOTH"),
            (6.5, "[6b] OR 项只杀一根针（删『%s』）" % cfg["words"][1], "OR_ONE"),
            (7, "[7] 裁决书引用 ≥8 处", "I7"),
            (8, "[8] FACTCHECK ⊇ selfBias", "I8"),
        ]
    else:
        rows = [
            (1, "[1] 两文件存在/非空/UTF-8", "I1"),
            (2, "[2] %s 恰一行合法声明" % cfg["decl"], "I2"),
            (3, "[3] 7 个必需小节", "I3"),
            (4, "[4] %s  ← OR 项（两词全删）" % " / ".join(cfg["words"]), "OR_BOTH"),
            (4.5, "[4b] OR 项只杀一根针（删『%s』）" % cfg["words"][1], "OR_ONE"),
            (5, "[5] 授权边界 ⊇ 本次不授权（单字面量）", "I5"),
            (6, "[6] 未背书 AND 词表（删『%s』）" % cfg["and_literal"], "I6AND"),
            (7, "[7] 裁决书引用 ≥8 处", "I7"),
            (8, "[8] FACTCHECK ⊇ selfBias", "I8"),
        ]
    return rows


def main_full():
    WRITE.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    snap0 = snapshot_all()
    write_json("_ak_guard_before.json", dict(count=len(snap0), files=snap0))
    verify_originals(strict=True)

    # ---- 12 份沙箱副本：每件 3 份（WA/WB/SENT），显式落点 ----
    twelve = []
    for gate in ORDER:
        lay_root = WORK / gate / "twelve"
        lay = Layout(gate, lay_root)
        if lay_root.exists():
            shutil.rmtree(lay_root)
        lay.script_dir.mkdir(parents=True, exist_ok=True)
        lay.input_dir.mkdir(parents=True, exist_ok=True)
        docs = original_docs(gate)
        for n, d in docs.items():
            (lay.input_dir / n).write_bytes(d)
        for variant in ("WA", "WB", "SENT"):
            sb, sd = script_bytes(gate, variant)
            fn = "_w_%s_%s.py" % (gate, {"WA": "A", "WB": "B", "SENT": "S"}[variant])
            p = lay.script_dir / fn
            p.write_bytes(sb)
            twelve.append(dict(gate=gate, variant=variant, path=str(p),
                               sha256=sha(sb), bytes=len(sb), desc=sd,
                               input_dir=str(lay.input_dir), cwd=str(lay.cwd),
                               layout=lay.note))
    write_json("_ak_twelve.json", twelve)
    write_text("_ak_twelve_out.txt",
               "12 份沙箱副本（生成→落盘清单，均在本任务写域）\n" +
               "\n".join("%s %-4s %s sha256=%s bytes=%d\n    %s\n    input_dir=%s cwd=%s\n    layout=%s" %
                         (t["gate"], t["variant"], t["path"], t["sha256"], t["bytes"],
                          t["desc"], t["input_dir"], t["cwd"], t["layout"])
                         for t in twelve) + "\n")
    # 驱动这 12 份（真实独立运行，原样输入）
    twelve_runs = []
    for t in twelve:
        cmd_list = [sys.executable, "-I", "-X", "utf8", t["path"]]
        p = subprocess.run(cmd_list, cwd=t["cwd"], capture_output=True)
        out = p.stdout.decode("utf-8", errors="replace")
        unchanged = verify_originals(strict=True)
        twelve_runs.append(dict(gate=t["gate"], variant=t["variant"], path=t["path"],
                                cmd=' '.join('"%s"' % c for c in cmd_list),
                                exit=p.returncode, stdout=out,
                                stdout_sha256=sha(p.stdout),
                                verdict="PASS" if p.returncode == 0 and "PASS" in out and "FAIL" not in out else "FAIL",
                                originals_unchanged=unchanged,
                                script_sha256=t["sha256"], script_bytes=t["bytes"]))
        RUNS.append(dict(tag="TWELVE", gate=t["gate"], exp="twelve", variant=t["variant"],
                         mut="NONE", layout=t["layout"], cwd=t["cwd"],
                         script_path=t["path"], script_sha256=t["sha256"],
                         script_bytes=t["bytes"], script_desc=t["desc"],
                         doc_desc="原件逐字节副本（两词都在）",
                         inputs={n: dict(sha256=sha(d), bytes=len(d), path=str(Path(t["input_dir"]) / n))
                                 for n, d in original_docs(t["gate"]).items()},
                         inputs_written=sorted(original_docs(t["gate"]).keys()),
                         cmd=' '.join('"%s"' % c for c in cmd_list),
                         python=sys.version.split()[0], exit=p.returncode,
                         stdout=out, stderr=p.stderr.decode("utf-8", errors="replace"),
                         stdout_sha256=sha(p.stdout),
                         stderr_sha256=sha(p.stderr),
                         verdict=twelve_runs[-1]["verdict"],
                         fail_items=sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", out))),
                         originals_unchanged=unchanged))

    # ---- 基线：未改内容，逐件独立跑 ----
    base = {}
    for gate in ORDER:
        base[gate] = do_run(gate, "baseline", "BASE", "NONE", "BASELINE")

    # ---- A/B/C 逐输入：每件每输入跑 BASE/WA/WB/SENT 四次 ----
    abc = {}
    for gate in ORDER:
        for label, mut in (("A", "A"), ("B", "B"), ("C", "C")):
            key = "%s_%s" % (gate, label)
            abc[key] = dict(
                doc=do_run(gate, "abc_%s" % label, "BASE", mut, "ABC_ORIGINAL"),
                WA=do_run(gate, "abc_%s_WA" % label, "WA", mut, "ABC_WORDA"),
                WB=do_run(gate, "abc_%s_WB" % label, "WB", mut, "ABC_WORDB"),
                SENT=do_run(gate, "abc_%s_SENT" % label, "SENT", mut, "ABC_SENTINEL"),
            )

    # ---- 上游注射实证复现：BASE vs UP（只把脚本第二根针换成哨兵），输入原件 ----
    repro = {}
    for gate in ORDER:
        b = do_run(gate, "repro_base", "BASE", "NONE", "REPRO_BASE")
        u = do_run(gate, "repro_up", "UP", "NONE", "REPRO_INJECTED")
        repro[gate] = dict(base=b, injected=u,
                           stdout_identical=(b["stdout"] == u["stdout"]),
                           stdout_sha_identical=(b["stdout_sha256"] == u["stdout_sha256"]),
                           exit_identical=(b["exit"] == u["exit"]),
                           both_pass=(b["verdict"] == "PASS" and u["verdict"] == "PASS"))

    # ---- 坏针哨兵全矩阵：件 × 项 ----
    matrix = []
    for gate in ORDER:
        for num, label, mut in items_for(gate):
            pre = base[gate]
            post = do_run(gate, "inj_%s" % str(num).replace(".", "p"),
                          "BASE", mut, "BAD_NEEDLE")
            caught = post["verdict"] == "FAIL" and post["exit"] != 0
            matrix.append(dict(gate=gate, item=num, label=label, mut=mut,
                               before=pre["verdict"], before_exit=pre["exit"],
                               after=post["verdict"], after_exit=post["exit"],
                               after_stdout=post["stdout"], after_fail_items=post["fail_items"],
                               caught=caught, doc_desc=post["doc_desc"],
                               cmd=post["cmd"]))

    # ---- 汇总 ----
    lines_abc = []
    abc_table = []
    for gate in ORDER:
        for label in ("A", "B", "C"):
            k = "%s_%s" % (gate, label)
            a = abc[k]
            p_wa = a["WA"]["verdict"] == "PASS"
            p_wb = a["WB"]["verdict"] == "PASS"
            andk = p_wa and p_wb
            caught = a["SENT"]["exit"] != 0 and a["SENT"]["verdict"] == "FAIL"
            dist = andk and caught
            row = dict(gate=gate, input=label, original_verdict=a["doc"]["verdict"],
                       original_exit=a["doc"]["exit"], original_stdout=a["doc"]["stdout"],
                       p_wa=p_wa, p_wb=p_wb, and_k=andk,
                       sentinel_exit=a["SENT"]["exit"], bad_needle_caught=caught,
                       distinguishable_pass=dist,
                       doc_desc=a["doc"]["doc_desc"])
            abc_table.append(row)
            lines_abc.append(fmt_run(a["doc"]) + fmt_run(a["WA"]) + fmt_run(a["WB"]) +
                             fmt_run(a["SENT"]) +
                             "  >> AGGREGATE = AND_k(P_WA, P_WB) = AND_k(%s, %s) = %s\n"
                             "  >> BAD_NEEDLE_CAUGHT = %s ; DISTINGUISHABLE_PASS = %s\n\n" %
                             (p_wa, p_wb, andk, caught, dist))

    # 上游口径：12 份副本在原件输入上的 AND_k（k=2 真实逐词运行）
    per_word = []
    for gate in ORDER:
        rows = [r for r in twelve_runs if r["gate"] == gate]
        wa = next(r for r in rows if r["variant"] == "WA")
        wb = next(r for r in rows if r["variant"] == "WB")
        se = next(r for r in rows if r["variant"] == "SENT")
        p = [wa["verdict"] == "PASS", wb["verdict"] == "PASS"]
        agg = all(p)
        caught = se["exit"] != 0 and se["verdict"] == "FAIL"
        per_word.append(dict(gate=gate, k=2, p=p, aggregate=agg,
                             bad_needle_caught=caught,
                             distinguishable_pass=agg and caught,
                             wa=wa, wb=wb, sentinel=se))

    # AND_8 / AND_9：坏针矩阵里每行「是否被抓」的合取
    and_matrix = {}
    for gate in ORDER:
        rows = [m for m in matrix if m["gate"] == gate]
        eight = [m for m in rows if isinstance(m["item"], int)]
        and_matrix[gate] = dict(
            and_8=all(m["caught"] for m in eight),
            and_9=all(m["caught"] for m in rows),
            caught_count=sum(1 for m in rows if m["caught"]),
            rows=len(rows), eight_count=len(eight),
            missed=[m["label"] for m in rows if not m["caught"]])

    snap1 = snapshot_all()
    write_json("_ak_guard_after.json", dict(count=len(snap1), files=snap1))
    diff = []
    for k in sorted(set(snap0) | set(snap1)):
        if snap0.get(k) != snap1.get(k):
            diff.append(dict(path=k, before=snap0.get(k), after=snap1.get(k)))

    summary = dict(
        python=sys.version.split()[0], repo=str(REPO), write_domain=str(WRITE),
        total_runs=len(RUNS), gate_runs=len(RUNS),
        originals_unchanged_after_every_run=all(r["originals_unchanged"] for r in RUNS),
        readonly_snapshot_files_before=len(snap0), readonly_snapshot_files_after=len(snap1),
        readonly_snapshot_diff=diff,
        orchestrator_baseline_verified=True,
        layouts={g: dict(note=Layout(g, WORK / g / "<exp>").note,
                         script_dir=str(Layout(g, WORK / g / "<exp>").script_dir),
                         input_dir=str(Layout(g, WORK / g / "<exp>").input_dir),
                         cwd=str(Layout(g, WORK / g / "<exp>").cwd)) for g in ORDER},
        baseline={g: dict(exit=base[g]["exit"], stdout=base[g]["stdout"],
                          verdict=base[g]["verdict"],
                          script_sha256=base[g]["script_sha256"],
                          script_bytes=base[g]["script_bytes"],
                          cmd=base[g]["cmd"]) for g in ORDER},
        abc=abc_table, per_word=per_word, matrix=matrix, and_matrix=and_matrix,
        repro={g: dict(base_exit=repro[g]["base"]["exit"],
                       inj_exit=repro[g]["injected"]["exit"],
                       base_stdout=repro[g]["base"]["stdout"],
                       inj_stdout=repro[g]["injected"]["stdout"],
                       stdout_identical=repro[g]["stdout_identical"],
                       stdout_sha_identical=repro[g]["stdout_sha_identical"],
                       exit_identical=repro[g]["exit_identical"],
                       both_pass=repro[g]["both_pass"],
                       base_cmd=repro[g]["base"]["cmd"],
                       inj_cmd=repro[g]["injected"]["cmd"],
                       inj_script_sha256=repro[g]["injected"]["script_sha256"],
                       inj_script_bytes=repro[g]["injected"]["script_bytes"]) for g in ORDER},
        twelve=twelve, twelve_runs=twelve_runs,
    )
    write_json("_ak_summary.json", summary)
    with (WRITE / "_ak_runs.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in RUNS:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_text("_ak_abc_out.txt", "A/B/C 三次逐输入完整输出与退出码（含 WA/WB/SENT 对照）\n\n" +
               "".join(lines_abc))

    ml = ["坏针哨兵矩阵（件 × 项 × 注入前/后判定 × 是否被抓）",
          "判据：注入前 = BASE 基线；注入后 = 注入副本实跑；是否被抓 = 注入后 EXIT≠0 且 verdict=FAIL", ""]
    for gate in ORDER:
        ml.append("=== %s ===" % gate)
        for m in [x for x in matrix if x["gate"] == gate]:
            ml.append("  item %-4s %-58s 注入前=%s(EXIT=%d) 注入后=%s(EXIT=%d) 是否被抓=%s" %
                      (m["item"], m["label"], m["before"], m["before_exit"],
                       m["after"], m["after_exit"], m["caught"]))
            ml.append("      注射: %s" % m["doc_desc"])
            ml.append("      STDOUT = %r" % m["after_stdout"])
            ml.append("      CMD = %s" % m["cmd"])
        ml.append("")
    write_text("_ak_matrix_out.txt", "\n".join(ml) + "\n")

    rl = ["上游注射实证复现（脚本侧杀一根针，输入原件不变）", ""]
    for gate in ORDER:
        r = summary["repro"][gate]
        rl.append("=== %s ===\nBASE CMD = %s\nINJ  CMD = %s\n"
                  "BASE EXIT=%d STDOUT=%r\nINJ  EXIT=%d STDOUT=%r\n"
                  "stdout 逐字一致=%s stdout_sha256 一致=%s EXIT 一致=%s 两者均 PASS=%s\n" %
                  (gate, r["base_cmd"], r["inj_cmd"], r["base_exit"], r["base_stdout"],
                   r["inj_exit"], r["inj_stdout"], r["stdout_identical"],
                   r["stdout_sha_identical"], r["exit_identical"], r["both_pass"]))
    write_text("_ak_repro_out.txt", "\n".join(rl) + "\n")

    ll = ["三套路径布局（显式落点，可复现）", ""]
    for gate in ORDER:
        lay = Layout(gate, WORK / gate / "<exp>")
        ll.append("=== %s ===\n  script_dir = %s\n  input_dir  = %s\n  cwd        = %s\n  %s" %
                  (gate, lay.script_dir, lay.input_dir, lay.cwd, lay.note))
        ll.append("  基线实跑 EXIT=%d STDOUT=%r" %
                  (base[gate]["exit"], base[gate]["stdout"]))
    ll.append("\n原件全量只读快照：before=%d files / after=%d files / diff=%d" %
              (len(snap0), len(snap1), len(diff)))
    write_text("_ak_layout_out.txt", "\n".join(ll) + "\n")

    print("TOTAL_RUNS = %d" % len(RUNS))
    print("ORIGINALS_UNCHANGED_AFTER_EVERY_RUN = %s" %
          all(r["originals_unchanged"] for r in RUNS))
    print("READONLY_SNAPSHOT_DIFF = %d" % len(diff))
    for g in ORDER:
        print("  %s baseline EXIT=%d %r ; AND_k(k=2)=%s ; AND_8=%s ; AND_9=%s ; missed=%r ; repro_identical=%s" %
              (g, base[g]["exit"], base[g]["stdout"],
               next(x["aggregate"] for x in per_word if x["gate"] == g),
               and_matrix[g]["and_8"], and_matrix[g]["and_9"],
               and_matrix[g]["missed"], summary["repro"][g]["stdout_identical"]))
    return 0


def main_selftest():
    """外壳自检：正控（好输入 PASS）+ 负控（缺文件 FAIL）。"""
    WORK.mkdir(parents=True, exist_ok=True)
    verify_originals(strict=True)
    out = []
    pos = do_run("d29", "selftest_pos", "BASE", "NONE", "SELFTEST_POS")
    neg = do_run("d29", "selftest_neg", "BASE", "I1", "SELFTEST_NEG")
    # 第三控：OR 项两词全删必须 FAIL（外壳能区分）
    third = do_run("d29", "selftest_or_both", "BASE", "OR_BOTH", "SELFTEST_OR_BOTH")
    ok = (pos["exit"] == 0 and pos["verdict"] == "PASS" and
          neg["exit"] != 0 and neg["verdict"] == "FAIL" and
          third["exit"] != 0 and third["verdict"] == "FAIL" and
          pos["originals_unchanged"] and neg["originals_unchanged"] and third["originals_unchanged"])
    out.append("SELF_TEST = %s" % ("PASS" if ok else "FAIL"))
    out.append("正控 好输入: EXIT=%d verdict=%s STDOUT=%r" % (pos["exit"], pos["verdict"], pos["stdout"]))
    out.append("负控 缺文件: EXIT=%d verdict=%s STDOUT=%r" % (neg["exit"], neg["verdict"], neg["stdout"]))
    out.append("加控 OR 双删: EXIT=%d verdict=%s STDOUT=%r" % (third["exit"], third["verdict"], third["stdout"]))
    for r in (pos, neg, third):
        out.append(fmt_run(r))
    write_text("_ak_selftest_out.txt", "\n".join(out) + "\n")
    print("\n".join(out[:4]))
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("selftest", "full"), default="full")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main_selftest() if a.mode == "selftest" else main_full())
