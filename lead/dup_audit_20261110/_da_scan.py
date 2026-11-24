"""只读普查：枚举 lead/ 下内容字节完全相同的 .py 文件组。

运行方式（仓库根目录）：python -I lead/dup_audit_20261110/_da_scan.py
只写 lead/dup_audit_20261110/_da_groups.json 与 _da_summary.txt。
不判断「谁抄了谁」，仅枚举哈希/字节数/路径等事实。
"""

import sys

sys.dont_write_bytecode = True

import hashlib
import json
import os
from collections import defaultdict

ROOT = "lead"
OUT_DIR = os.path.join(ROOT, "dup_audit_20261110")
OUT_JSON = os.path.join(OUT_DIR, "_da_groups.json")
OUT_TXT = os.path.join(OUT_DIR, "_da_summary.txt")


def as_posix(path):
    """统一成 / 分隔符（win32 上 os.walk 返回反斜杠路径）。"""
    return path.replace("\\", "/")


def is_review_path(p):
    """has_review_path 的判定口径：reviews/ 或 reviewer 或 _review。"""
    return "reviews/" in p or "reviewer" in p or "_review" in p


def is_review_copy_candidate(p):
    """REVIEW_COPY 的组内路径口径（契约 5 只列了前两者）。"""
    return "reviews/" in p or "reviewer" in p


def scan():
    """os.walk('lead')，跳过 __pycache__，按 sha256 分组。"""
    groups = defaultdict(list)
    sizes = {}
    py_count = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            full = os.path.join(dirpath, name)
            with open(full, "rb") as fh:
                data = fh.read()
            p = as_posix(full)
            h = hashlib.sha256(data).hexdigest()
            groups[h].append(p)
            sizes[h] = len(data)
            py_count += 1
    return groups, sizes, py_count


def classify(paths):
    """三选一，按契约列举顺序判定（PATCH_COPY 优先）。"""
    if any("patched/" in p for p in paths):
        return "PATCH_COPY"
    if any(is_review_copy_candidate(p) for p in paths) and any(
        "reviews/" not in p for p in paths
    ):
        return "REVIEW_COPY"
    return "BENIGN_DUP"


def meaning(kind, paths):
    n = len(paths)
    n_patched = sum(1 for p in paths if "patched/" in p)
    n_reviews = sum(1 for p in paths if "reviews/" in p)
    if kind == "PATCH_COPY":
        return "共 %d 个内容字节完全相同的 .py 文件，其中 %d 条路径位于 patched/ 改造副本目录。" % (n, n_patched)
    if kind == "REVIEW_COPY":
        return "共 %d 个内容字节完全相同的 .py 文件，含 reviews/ 或 reviewer 路径（%d 条在 reviews/ 下），且至少 1 条同内容路径不在 reviews/ 下。" % (n, n_reviews)
    return "共 %d 个内容字节完全相同的 .py 文件分布于不同路径，组内无 patched/ 路径且不构成 REVIEW_COPY 条件。" % n


def main():
    groups, sizes, py_count = scan()
    dup_hashes = sorted(h for h, ps in groups.items() if len(ps) >= 2)

    out_groups = []
    for h in dup_hashes:
        paths = sorted(groups[h])
        kind = classify(paths)
        out_groups.append(
            {
                "sha256": h,
                "bytes": sizes[h],
                "paths": paths,
                "has_review_path": any(is_review_path(p) for p in paths),
                "kind": kind,
                "meaning": meaning(kind, paths),
            }
        )

    counts = {k: 0 for k in ("PATCH_COPY", "REVIEW_COPY", "BENIGN_DUP")}
    for g in out_groups:
        counts[g["kind"]] += 1

    review_copies = [g for g in out_groups if g["kind"] == "REVIEW_COPY"]
    # 同时命中 PATCH_COPY 与 review 条件的组：按优先级归入 PATCH_COPY，
    # 但作为枚举事实在此单独列出，避免信息丢失。
    overlaps = [
        {
            "sha256": g["sha256"],
            "bytes": g["bytes"],
            "paths": g["paths"],
            "assigned_kind": g["kind"],
            "also_matches": "REVIEW_COPY",
            "has_review_path": g["has_review_path"],
        }
        for g in out_groups
        if g["kind"] == "PATCH_COPY" and g["has_review_path"]
    ]

    doc = {
        "scan": {
            "root": ROOT,
            "note": "os.walk('lead')，跳过 __pycache__，仅 *.py；含本审计脚本自身（内容唯一，未进入任何重复组）",
            "py_files_scanned": py_count,
            "unique_sha256": len(groups),
            "duplicate_groups": len(out_groups),
        },
        "groups": out_groups,
        "summary": {
            "total_groups": len(out_groups),
            "by_kind": counts,
            "review_copy_groups": [
                {
                    "sha256": g["sha256"],
                    "bytes": g["bytes"],
                    "paths": g["paths"],
                    "has_review_path": g["has_review_path"],
                }
                for g in review_copies
            ],
            "kind_rule": "kind 三选一，按契约列举顺序判定：PATCH_COPY 优先，其次 REVIEW_COPY，其余 BENIGN_DUP",
            "patch_review_overlap_groups": overlaps,
        },
    }

    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    lines = []
    lines.append("lead/ 重复 .py 文件普查汇总（只读枚举，不判断复制方向）")
    lines.append("扫描 .py 文件数: %d" % py_count)
    lines.append("唯一 sha256 数: %d" % len(groups))
    lines.append("重复组总数(组内路径数>=2): %d" % len(out_groups))
    lines.append("  PATCH_COPY : %d" % counts["PATCH_COPY"])
    lines.append("  REVIEW_COPY: %d" % counts["REVIEW_COPY"])
    lines.append("  BENIGN_DUP : %d" % counts["BENIGN_DUP"])
    lines.append("判定顺序: PATCH_COPY > REVIEW_COPY > BENIGN_DUP")
    lines.append("")
    lines.append("REVIEW_COPY 完整清单: %d 组" % len(review_copies))
    for g in review_copies:
        lines.append("  sha256=%s bytes=%d paths=%d" % (g["sha256"], g["bytes"], len(g["paths"])))
        for p in g["paths"]:
            lines.append("    " + p)
    lines.append("")
    lines.append("同时含 patched/ 与 review 条件、按优先级归入 PATCH_COPY 的组: %d 组" % len(overlaps))
    for g in overlaps:
        lines.append("  sha256=%s bytes=%d paths=%d assigned_kind=%s also_matches=REVIEW_COPY" % (
            g["sha256"], g["bytes"], len(g["paths"]), g["assigned_kind"]
        ))
        for p in g["paths"]:
            lines.append("    " + p)
    lines.append("")
    lines.append("产物: %s / %s" % (as_posix(OUT_JSON), as_posix(OUT_TXT)))

    with open(OUT_TXT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    print("py_files_scanned=%d unique_sha256=%d duplicate_groups=%d" % (py_count, len(groups), len(out_groups)))
    print("PATCH_COPY=%d REVIEW_COPY=%d BENIGN_DUP=%d" % (
        counts["PATCH_COPY"], counts["REVIEW_COPY"], counts["BENIGN_DUP"]
    ))
    print("wrote %s" % as_posix(OUT_JSON))
    print("wrote %s" % as_posix(OUT_TXT))


if __name__ == "__main__":
    main()
