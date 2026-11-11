"""DLC capability audit — baseline / closing fingerprint collector.

Run as:  python -I -X utf8 <ABS_PATH_TO_THIS_FILE> <ABS_OUTPUT_JSON_PATH>

READ-ONLY except for the single output JSON path (which must live inside the
write domain).  Every digest is computed with hashlib over real bytes; nothing
is estimated, quoted from a report, or copied from a document.

Scopes
------
A) audit_scope : content sha256 of every regular file in
   docs/, ra2forge/, mcp/, examples/, README.md (the existing read-only files
   this audit touches) — recursive.
B) ra2youli_top : content sha256 of EVERY top-level regular file in ra2youli/.
   Also emits "list_sha256" = sha256 of the sorted "name<TAB>size" lines,
   i.e. the ra2youli top-level file-list hash requested by the receipt.
C) repo_top : informational name+size+mtime_ns manifest of the ROOT's own
   top-level entries only (bounded, no recursion into huge trees).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "dlc_capability_audit_20261112"
RA2YOULI = ROOT / "ra2youli"
CONTENT_DIRS = ("docs", "ra2forge", "mcp", "examples")
CONTENT_ROOT_FILES = ("README.md",)
VOLATILE_TOP_DIRS = {
    ".git", ".asar-dump", ".blind1_tmp", ".commandcode", ".dsh-probe",
    ".dsh-watch", ".e12tmp_base", ".e12tmp_launch", ".e12tmp_leader",
    ".e12tmp_repair", ".e12tmp_review", ".mimosa", ".pi", ".tmp",
    ".workbuddy", ".zcode", ".zcode-watch", "%TEMP%qc95rev_pyc",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canon_hash(lines: list[str]) -> str:
    return sha256_bytes("\n".join(lines).encode("utf-8") + b"\n")


def walk_files(base: Path, skip_dirs: set[str] | None = None):
    """Yield (relative_posix_path, absolute_path, size) deterministically."""
    skip_dirs = skip_dirs or set()
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in skip_dirs and (Path(dirpath) / d) != WD
        )
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            try:
                if not p.is_file() or p.is_symlink():
                    continue
                size = p.stat().st_size
            except OSError as exc:
                out.append((f"__ERROR__ {p.relative_to(ROOT).as_posix()}: {exc}", p, -1))
                continue
            out.append((p.relative_to(ROOT).as_posix(), p, size))
    return sorted(out, key=lambda t: t[0])


def content_scope() -> dict:
    files = []
    for d in CONTENT_DIRS:
        files.extend(walk_files(ROOT / d))
    for name in CONTENT_ROOT_FILES:
        p = ROOT / name
        if p.is_file():
            files.append((name, p, p.stat().st_size))
    files = sorted(set(files), key=lambda t: t[0])
    records = []
    errors = []
    for rel, p, size in files:
        if rel.startswith("__ERROR__"):
            errors.append(rel)
            continue
        try:
            records.append({"path": rel, "size": size, "sha256": sha256_file(p)})
        except OSError as exc:
            errors.append(f"{rel}: read failed: {exc}")
    lines = [f"{r['path']}\t{r['size']}\t{r['sha256']}" for r in records]
    return {
        "file_count": len(records),
        "total_bytes": sum(r["size"] for r in records),
        "aggregate_sha256": canon_hash(lines),
        "errors": errors,
        "files": records,
    }


def ra2youli_top() -> dict:
    entries = []
    errors = []
    for p in sorted(RA2YOULI.iterdir(), key=lambda q: q.name):
        try:
            if not p.is_file() or p.is_symlink():
                continue
            size = p.stat().st_size
        except OSError as exc:
            errors.append(f"{p.name}: stat failed: {exc}")
            continue
        try:
            digest = sha256_file(p)
        except OSError as exc:
            errors.append(f"{p.name}: read failed: {exc}")
            continue
        entries.append({"name": p.name, "size": size, "sha256": digest})
    list_lines = [f"{e['name']}\t{e['size']}" for e in entries]
    content_lines = [f"{e['name']}\t{e['size']}\t{e['sha256']}" for e in entries]
    return {
        "file_count": len(entries),
        "total_bytes": sum(e["size"] for e in entries),
        "list_sha256": canon_hash(list_lines),          # ra2youli 顶层文件清单哈希
        "content_aggregate_sha256": canon_hash(content_lines),
        "errors": errors,
        "files": entries,
    }


def repo_top() -> dict:
    """Bounded, informational: ROOT's own top-level entries only."""
    rows = []
    errors = []
    for p in sorted(ROOT.iterdir(), key=lambda q: q.name):
        try:
            st = p.stat()
            rows.append({"name": p.name,
                         "kind": "dir" if p.is_dir() else "file",
                         "size": st.st_size,
                         "mtime_ns": st.st_mtime_ns})
        except OSError as exc:
            errors.append(f"{p.name}: {exc}")
    lines = [f"{r['name']}\t{r['kind']}\t{r['size']}\t{r['mtime_ns']}"
             for r in rows]
    return {
        "entry_count": len(rows),
        "manifest_sha256": canon_hash(lines),
        "errors": errors,
        "note": ("informational: ROOT top-level entries only, no recursion; "
                 "mtime_ns included so a rewritten existing root file is visible"),
        "entries": rows,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fingerprint.py <ABS_OUTPUT_JSON_PATH>", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    if not out.is_absolute():
        print("output path must be absolute", file=sys.stderr)
        return 2
    if WD not in out.parents and out != WD:
        print("output path must be inside the write domain", file=sys.stderr)
        return 2
    result = {
        "tool": "hashlib (python -I -X utf8)",
        "root": str(ROOT),
        "write_domain": str(WD),
        "audit_scope": content_scope(),
        "ra2youli_top": ra2youli_top(),
        "repo_top": repo_top(),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    a = result["audit_scope"]
    r = result["ra2youli_top"]
    t = result["repo_top"]
    print(f"output            = {out}")
    print(f"audit_scope       : files={a['file_count']} bytes={a['total_bytes']} "
          f"aggregate_sha256={a['aggregate_sha256']}")
    print(f"  errors          = {a['errors']}")
    print(f"ra2youli_top      : files={r['file_count']} bytes={r['total_bytes']}")
    print(f"  list_sha256     = {r['list_sha256']}")
    print(f"  content_agg     = {r['content_aggregate_sha256']}")
    print(f"  errors          = {r['errors']}")
    print(f"repo_top(info)    : entries={t['entry_count']} "
          f"manifest_sha256={t['manifest_sha256']}")
    print(f"  errors          = {t['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
