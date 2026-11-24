#!/usr/bin/env python3
"""Generate W23 PATCH_RELATIVE.diff: cumulative repo 0.4 -> ra2forge_patched_v7.

Builds two throwaway trees (repo 0.4 copy vs v7 copy, __pycache__ excluded),
runs `git diff --no-index a b`, and rewrites the a/a/... b/b/... header
paths to a/ra2forge/... b/ra2forge/... so the patch replays against the repo
root with plain relative paths (W22 convention). Output is LF, no BOM.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

W23 = Path(__file__).resolve().parent.parent   # this script lives in W23/tools/
V7 = W23 / "ra2forge_patched_v7"
REPO = W23.parents[2]
DIFF_OUT = W23 / "PATCH_RELATIVE.diff"
TREE = W23 / "sandbox" / "_difftree"

a_dir = TREE / "a" / "ra2forge"
b_dir = TREE / "b" / "ra2forge"
for d in (TREE, a_dir, b_dir):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)

for src in sorted((REPO / "ra2forge").glob("*.py")):
    shutil.copyfile(src, a_dir / src.name)
for src in sorted((V7 / "ra2forge").glob("*.py")):
    shutil.copyfile(src, b_dir / src.name)

proc = subprocess.run(
    ["git", "diff", "--no-index", "--no-ext-diff", "a", "b"],
    cwd=str(TREE), capture_output=True, text=True, encoding="utf-8",
    errors="replace")
if proc.returncode not in (0, 1):
    print(f"git diff failed: {proc.returncode}\n{proc.stderr}", file=sys.stderr)
    sys.exit(1)

out_lines = []
for line in proc.stdout.splitlines():
    if line.startswith("diff --git "):
        # "a/a/..." for modified files, "a/b/..." for files that exist only
        # on the b side (new files): normalize both onto a/ra2forge/...
        line = (line.replace(" a/a/", " a/").replace(" a/b/", " a/")
                .replace(" b/b/", " b/")
                .replace("a/ra2forge_old/", "a/ra2forge/")
                .replace("b/ra2forge_new/", "b/ra2forge/"))
    elif line.startswith("--- "):
        line = line.replace("--- a/a/", "--- a/")
    elif line.startswith("+++ "):
        line = line.replace("+++ b/b/", "+++ b/")
    out_lines.append(line)

text = "\n".join(out_lines) + "\n"
# safety: the patch must never mention anything outside ra2forge/
bad = [ln for ln in out_lines
       if (ln.startswith("--- ") or ln.startswith("+++ ")
           or ln.startswith("diff --git "))
       and ("/ra2forge/" not in ln and "/dev/null" not in ln)]
if bad:
    print("unexpected paths in diff:", bad, file=sys.stderr)
    sys.exit(1)
DIFF_OUT.write_bytes(text.encode("utf-8"))
n_files = sum(1 for ln in out_lines if ln.startswith("diff --git "))
n_new = sum(1 for ln in out_lines if ln.startswith("new file mode"))
print(f"written {DIFF_OUT} ({len(text.encode('utf-8'))} bytes, "
      f"{n_files} file(s), {n_new} new file(s))")
