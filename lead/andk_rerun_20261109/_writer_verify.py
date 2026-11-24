# -*- coding: utf-8 -*-
"""_writer_verify.py — 撰写员本次会话独立复核（2026-11-09）
只读原件 / 只写 lead/andk_rerun_20261109/ 内 _writer_* 件；零真机、零采样代码。
用法: python -I -X utf8 "<abs>/_writer_verify.py" before|after
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "andk_rerun_20261109"

# 编排方基线（7 绑定行 + 8 输入文档）
BIND = [
    ("lead/d27_ruling_20261106/check_d27.py",
     "3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", 3764),
    ("lead/d28_ruling_20261106/check_d28.py",
     "5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268", 4539),
    ("lead/d29_ruling_20261106/check_d29.py",
     "2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", 3906),
    ("lead/d30_ruling_20261106/check_d30.py",
     "6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", 3926),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    ("lead/stale_pass_20261109/STALE_PASS_INVENTORY.md",
     "a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798", 63656),
]
DOCS = [
    ("lead/d27_ruling_20261106/RULING_D27.md",
     "a4f56e0f416ee90acaff0b55bcaf77b4ad15d5db55b28a8f0c12329f988b3d0e", 17658),
    ("lead/d27_ruling_20261106/FACTCHECK.md",
     "5a133088c6f99568b0c0ef22d62ab759e4e08ca2008ca059941d885dc05cecb6", 17837),
    ("lead/d28_ruling_20261106/RULING_D28.md",
     "29bb247fbf82d80adf8c9753a7bb3b6d18dfe6bd0583ff1f87f860fb763b5f15", 13897),
    ("lead/d28_ruling_20261106/FACTCHECK.md",
     "f2de988ee2ab0402919c36bf765bb203ff4e4f443a2dd0bc8589ef8d9b114426", 13028),
    ("lead/d29_ruling_20261106/RULING_D29.md",
     "325c950eec4d3275436c10f2d7fd83c738adacdeb489c1e9f0e37a7e17212afb", 12258),
    ("lead/d29_ruling_20261106/FACTCHECK.md",
     "0661f666bc4af56c70baf3aa340943051d1e6ff6dee6041f943d14f08af46767", 12647),
    ("lead/d30_ruling_20261106/RULING_D30.md",
     "d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f", 13197),
    ("lead/d30_ruling_20261106/FACTCHECK.md",
     "2981848eec1b16b0af6fc26233439f665299a45b191f8e1ffd02f8a7d84aef59", 11394),
]
ART = ["_ak_full_console.txt", "_ak_summary.json", "_ak_runs.jsonl",
       "_ak_BAD_NEEDLE_MATRIX.md", "_ak_PER_INPUT_TABLE.md", "_ak_REPORT.md",
       "_ak_selftest_out.txt", "_ak_layout_out.txt", "_ak_REPRO.md",
       "_ak_guard_before.json", "_ak_guard_after.json"]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def binding():
    ok = True
    print("==== 7 BINDING LINES (hashlib, disk) ====")
    for rel, h, n in BIND:
        b = (REPO / rel).read_bytes()
        m = (sha(b) == h and len(b) == n)
        ok &= m
        print("被核对象 SHA256 = %s，字节数 = %d  [%s] %s" %
              (sha(b), len(b), "MATCH" if m else "MISMATCH", rel))
    bad = []
    for rel, h, n in DOCS:
        b = (REPO / rel).read_bytes()
        if not (sha(b) == h and len(b) == n):
            bad.append(rel)
    print("INPUT_DOCS_MATCH_BASELINE = %s  (mismatch=%r)" % (not bad, bad))
    print("ALL_BINDING_LINES_MATCH_DISK = %s" % ok)
    return ok


def art_hashes():
    return {n: sha((W / n).read_bytes()) for n in ART if (W / n).exists()}


def before():
    binding()
    h = art_hashes()
    (W / "_writer_before.json").write_text(
        json.dumps(h, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ARTIFACTS_HASHED_BEFORE = %d" % len(h))


def after():
    binding()
    h0 = json.loads((W / "_writer_before.json").read_text(encoding="utf-8"))
    h1 = art_hashes()
    diffs = [n for n in sorted(set(h0) | set(h1)) if h0.get(n) != h1.get(n)]
    print("ARTIFACT_HASH_DIFFS_AFTER_RERUN = %r" % diffs)
    print("ARTIFACTS_BYTE_IDENTICAL_AFTER_RERUN = %s" % (not diffs))

    runs = [json.loads(l) for l in (W / "_ak_runs.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    print("TOTAL_RUNS_IN_JSONL = %d" % len(runs))
    from collections import Counter
    print("TAG_COUNTS = %r" % dict(sorted(Counter(r["tag"] for r in runs).items())))
    print("ALL_ORIGINALS_UNCHANGED = %s" %
          all(r["originals_unchanged"] for r in runs))

    print("\n==== 12 ABC_ORIGINAL ROWS (per-input original verdict + 8-item fail_items) ====")
    for r in runs:
        if r["tag"] == "ABC_ORIGINAL":
            print("%s/%s mut=%s EXIT=%d verdict=%s fail_items=%r stdout=%r" %
                  (r["gate"], r["exp"], r["mut"], r["exit"], r["verdict"],
                   r["fail_items"], r["stdout"]))
    print("\n==== 36 BAD_NEEDLE ROWS (per cell: injection, exit, verdict, stdout) ====")
    for r in runs:
        if r["tag"] == "BAD_NEEDLE":
            print("%s mut=%-9s EXIT=%d verdict=%-4s fail_items=%r stdout=%r caught=%s" %
                  (r["gate"], r["mut"], r["exit"], r["verdict"], r["fail_items"],
                   r["stdout"], (r["exit"] != 0 and r["verdict"] == "FAIL")))
    print("\n==== STILL-PASS CELLS: stdout equals that gate's A baseline? ====")
    a_out = {r["gate"]: r["stdout"] for r in runs
             if r["tag"] == "ABC_ORIGINAL" and r["mut"] == "A"}
    for r in runs:
        if r["tag"] == "BAD_NEEDLE" and r["mut"] == "OR_ONE":
            print("%s OR_ONE EXIT=%d verdict=%s stdout==A_baseline=%s stdout=%r" %
                  (r["gate"], r["exit"], r["verdict"],
                   r["stdout"] == a_out[r["gate"]], r["stdout"]))

    s = json.loads((W / "_ak_summary.json").read_text(encoding="utf-8"))
    print("\n==== SUMMARY abc (12 rows) ====")
    for r in s["abc"]:
        print("%s %s orig=%s EXIT=%d P_WA=%s P_WB=%s AND_k=%s SENT=%d CAUGHT=%s DP=%s" %
              (r["gate"], r["input"], r["original_verdict"], r["original_exit"],
               r["p_wa"], r["p_wb"], r["and_k"], r["sentinel_exit"],
               r["bad_needle_caught"], r["distinguishable_pass"]))
    print("\n==== SUMMARY per_word / and_matrix / repro ====")
    for r in s["per_word"]:
        print("%s per_word k=%d p=%r AGG=%s CAUGHT=%s DP=%s" %
              (r["gate"], r["k"], r["p"], r["aggregate"],
               r["bad_needle_caught"], r["distinguishable_pass"]))
    for g in ("d27", "d28", "d29", "d30"):
        m = s["and_matrix"][g]
        rp = s["repro"][g]
        print("%s AND_8=%s AND_9=%s caught=%d/%d missed=%r | repro base/inj EXIT=%d/%d identical=%s both_pass=%s" %
              (g, m["and_8"], m["and_9"], m["caught_count"], m["rows"],
               m["missed"], rp["base_exit"], rp["inj_exit"],
               rp["stdout_identical"], rp["both_pass"]))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    mode = sys.argv[1] if len(sys.argv) > 1 else "after"
    (before() if mode == "before" else after())
