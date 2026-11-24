# -*- coding: utf-8 -*-
"""_akv_guard.py — 独立复核员自写：只读域全量 SHA256/字节数快照与比对。

用法（python -I -X utf8 + 绝对路径）：
  python -I -X utf8 ".../_akv_guard.py" before
  python -I -X utf8 ".../_akv_guard.py" after
  python -I -X utf8 ".../_akv_guard.py" compare
快照只写本任务写域 lead/andk_rerun_20261109/ 下 _akv_guard_*.json。
不写、不追加、不覆盖任何绝对只读文件。
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
WRITE = REPO / "lead" / "andk_rerun_20261109"

READONLY_FILES = [
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
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

# 编排方基线（题给），本复核员独立实算比对，不作为唯一依据
EXPECTED = {
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


def snap():
    out = {}
    for rel in READONLY_FILES:
        p = REPO / rel
        b = p.read_bytes()
        out[rel] = [hashlib.sha256(b).hexdigest(), len(b)]
    for rel in READONLY_DIRS:
        for p in sorted((REPO / rel).rglob("*")):
            if p.is_file():
                b = p.read_bytes()
                out[p.relative_to(REPO).as_posix()] = [hashlib.sha256(b).hexdigest(), len(b)]
    return out


def main():
    mode = sys.argv[1]
    if mode in ("before", "after"):
        s = snap()
        (WRITE / ("_akv_guard_%s.json" % mode)).write_text(
            json.dumps(dict(count=len(s), files=s), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        mism = []
        for rel, exp in EXPECTED.items():
            got = tuple(s.get(rel, ["MISSING", -1]))
            if got != exp:
                mism.append((rel, exp, got))
        print("SNAP_MODE =", mode)
        print("SNAP_FILES =", len(s))
        print("BASELINE_15_FILES_MATCH =", not mism)
        if mism:
            for m in mism:
                print("  MISMATCH", m)
        return 0
    a = json.loads((WRITE / "_akv_guard_before.json").read_text(encoding="utf-8"))
    b = json.loads((WRITE / "_akv_guard_after.json").read_text(encoding="utf-8"))
    fa, fb = a["files"], b["files"]
    keys = sorted(set(fa) | set(fb))
    diff = [(k, fa.get(k), fb.get(k)) for k in keys if fa.get(k) != fb.get(k)]
    print("BEFORE_COUNT =", a["count"], "AFTER_COUNT =", b["count"])
    print("READONLY_DIFF_COUNT =", len(diff))
    for k, x, y in diff:
        print("  DIFF", k, x, y)
    mism = []
    for rel, exp in EXPECTED.items():
        if tuple(fb.get(rel, ["MISSING", -1])) != exp:
            mism.append(rel)
    print("FINAL_BASELINE_15_FILES_MATCH =", not mism, mism)
    return 0 if (not diff and not mism) else 1


if __name__ == "__main__":
    raise SystemExit(main())
