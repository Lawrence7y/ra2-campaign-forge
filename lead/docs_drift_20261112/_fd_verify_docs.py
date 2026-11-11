# -*- coding: utf-8 -*-
"""Closing proof: recompute every docs/ fingerprint and compare with the START
manifest, proving docs/ was not modified during this task.

Run as: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_verify_docs.py
"""
import sys
sys.dont_write_bytecode = True

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
DOCS = ROOT / "docs"
WD = ROOT / "lead" / "docs_drift_20261112"
EV = WD / "_evidence"
TZ = timezone(timedelta(hours=8))


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row(p: Path) -> dict:
    st = p.stat()
    return {
        "rel": p.relative_to(ROOT).as_posix(),
        "bytes": st.st_size,
        "sha256": sha256_of(p),
        "mtime_ns": st.st_mtime_ns,
    }


start = json.loads((EV / "00_docs_manifest_start.json").read_text(encoding="utf-8"))
start_rows = start["rows"]
start_tree = start["tree_sha256"]

now_rows = sorted(
    [row(p) for p in DOCS.rglob("*") if p.is_file()],
    key=lambda r: (r["mtime_ns"], r["rel"]),
)
now_payload = json.dumps(now_rows, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
now_tree = hashlib.sha256(now_payload).hexdigest()

s_by_rel = {r["rel"]: r for r in start_rows}
n_by_rel = {r["rel"]: r for r in now_rows}
diffs = []
for rel in sorted(set(s_by_rel) | set(n_by_rel)):
    s, n = s_by_rel.get(rel), n_by_rel.get(rel)
    if s is None:
        diffs.append({"rel": rel, "kind": "ADDED"})
    elif n is None:
        diffs.append({"rel": rel, "kind": "REMOVED"})
    else:
        for k in ("bytes", "sha256", "mtime_ns"):
            if s[k] != n[k]:
                diffs.append({"rel": rel, "kind": "CHANGED", "field": k,
                              "start": s[k], "now": n[k]})

ok = (not diffs) and (start_tree == now_tree) and (len(start_rows) == len(now_rows))

proof = {
    "verified_at_local": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S+08:00"),
    "command": "python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_verify_docs.py",
    "start_file_count": len(start_rows),
    "end_file_count": len(now_rows),
    "start_tree_sha256": start_tree,
    "end_tree_sha256": now_tree,
    "tree_sha256_equal": start_tree == now_tree,
    "diffs": diffs,
    "docs_zero_change": ok,
    "key_files": [
        {"rel": "docs/PROJECT_DIRECTION.md", "bytes": n_by_rel["docs/PROJECT_DIRECTION.md"]["bytes"],
         "sha256": n_by_rel["docs/PROJECT_DIRECTION.md"]["sha256"],
         "mtime_ns": n_by_rel["docs/PROJECT_DIRECTION.md"]["mtime_ns"]},
        {"rel": "docs/WORK_CHAIN.md", "bytes": n_by_rel["docs/WORK_CHAIN.md"]["bytes"],
         "sha256": n_by_rel["docs/WORK_CHAIN.md"]["sha256"],
         "mtime_ns": n_by_rel["docs/WORK_CHAIN.md"]["mtime_ns"]},
    ],
}
(EV / "02_docs_zero_change_proof.json").write_text(
    json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")

lines = [
    "# 收尾指纹证明 · `docs/` 零改动",
    "",
    "> 命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_verify_docs.py`",
    "> 方法：对 `docs/` 递归全部文件重新以 `hashlib.sha256` 实算，与 `_evidence/00_docs_manifest_start.json`",
    "> 逐件比对 `{rel, bytes, sha256, mtime_ns}`，并复算全树聚合指纹。",
    "",
    "| 项 | 起点（STEP 1） | 收尾 | 判定 |",
    "|:--|:--|:--|:--|",
    "| 文件数 | %d | %d | %s |" % (len(start_rows), len(now_rows),
                                "一致" if len(start_rows) == len(now_rows) else "不一致"),
    "| `docs_tree_sha256` | `%s` | `%s` | **%s** |" % (
        start_tree, now_tree, "EQUAL" if start_tree == now_tree else "DIFFERENT"),
    "| 逐件差异（新增/删除/字节/sha/mtime） | — | %d 项 | %s |" % (
        len(diffs), "零差异" if not diffs else "见下"),
    "",
    "**结论：`docs_zero_change = %s`。**" % ok,
    "",
    "## 关键两件（收尾实算）",
    "",
    "| 文件 | bytes | sha256 | mtime_ns |",
    "|:--|--:|:--|--:|",
]
for k in proof["key_files"]:
    lines.append("| `%s` | %d | `%s` | %d |" %
                 (k["rel"], k["bytes"], k["sha256"], k["mtime_ns"]))
lines.append("")
lines.append("> 逐件明细见 `_evidence/02_docs_zero_change_proof.json`（含 `diffs` 数组，本次为空）。")
lines.append("")
(EV / "02_docs_zero_change_proof.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print("DOCS ZERO CHANGE =", ok)
print("start_tree_sha256 =", start_tree)
print("end_tree_sha256   =", now_tree)
print("start_file_count  =", len(start_rows), "end_file_count =", len(now_rows))
print("diffs =", len(diffs))
