# -*- coding: utf-8 -*-
"""STEP1: re_atlas/ 全量指纹实算（字节数 / sha256 / mtime），hashlib 实算，无手写估计。
只读遍历，输出 TSV 到写域 stdout/stderr。"""
import hashlib
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge\re_atlas"
OUT = r"D:\Project\ra2-campaign-forge\lead\re_atlas_reassess_20261112\step1_re_atlas_manifest.tsv"


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    rows = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full)
                digest = sha256_of(full)
                rel = os.path.relpath(full, r"D:\Project\ra2-campaign-forge")
                rows.append((rel, st.st_size, st.st_mtime, digest))
            except OSError as exc:
                sys.stderr.write("ERR %s: %s\n" % (full, exc))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("path\tbytes\tmtime_epoch\tmtime_local\tsha256\n")
        for rel, size, mtime, digest in rows:
            import datetime
            local = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            f.write("%s\t%d\t%.6f\t%s\t%s\n" % (rel, size, mtime, local, digest))
    sys.stdout.write("files=%d\n" % len(rows))
    # 关键文件汇总（STATUS/LEDGER/INDEX/kb 卷/HANDOFF）
    def is_key(rel: str) -> bool:
        return (rel in (r"re_atlas\STATUS.md", r"re_atlas\LEDGER.md",
                        r"re_atlas\INDEX.md", r"re_atlas\HANDOFF_TO_GOAL3T.md")
                or rel.startswith(r"re_atlas\kb" + os.sep))

    keys = [r for r in rows if is_key(r[0])]
    sys.stdout.write("--- key files ---\n")
    for rel, size, mtime, digest in keys:
        import datetime
        local = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write("%s\tbytes=%d\tmtime=%s\tsha256=%s\n" % (rel, size, local, digest))
    # 最后修改时间排序（top 15，看最后活动）
    rows_sorted = sorted(rows, key=lambda r: r[2], reverse=True)[:15]
    sys.stdout.write("--- last modified top15 ---\n")
    for rel, size, mtime, digest in rows_sorted:
        import datetime
        local = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write("%s\tmtime=%s\n" % (rel, local))
    return 0


if __name__ == "__main__":
    sys.exit(main())
