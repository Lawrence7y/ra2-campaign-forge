# -*- coding: utf-8 -*-
"""STATUS_PANEL 指纹复核（零真机；只读仓库；写域仅本目录）。

命令固定为：python -I -X utf8 <本文件绝对路径>
指纹一律 hashlib.sha256(实读字节)，不引用任何"记忆中的哈希"。
不重跑 panel_forensics.py，不启动游戏，不读活进程内存。
"""
from pathlib import Path
import hashlib
import datetime

ROOT = Path(r"D:\Project\ra2-campaign-forge")
OUTDIR = Path(r"D:\Project\ra2-campaign-forge\lead\status_panel_20261112")

REL_FILES = [
    r"ra2bench\gamemd.exe",
    r"ra2youli\gamemd.exe",
    r"ra2bench\ra2render.dll",
    r"re_atlas\evidence\binary_identity.txt",
    r"docs\PROJECT_DIRECTION.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\status_panel_20261112\panel_forensics_stdout.txt",
    r"lead\re_progress_check_20261111\RE_PROGRESS_20261111.md",
    r"lead\re_line_20261105\W11_EXCEPT_FRESHNESS\W11_EXCEPT_FRESHNESS.md",
    r"lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\W9_SINGLESTEP.md",
    r"lead\r2_unclosed_b_20261108\B_BREAKPOINTS_2_6.md",
    r"lead\criteria_r3_verify_20261108\R2_BREAKPOINTS_CLOSURE.md",
    r"re_atlas\STATUS.md",
    r"re_atlas\LEDGER.md",
]

lines = []
lines.append("=== STATUS_PANEL fingerprint recheck ===")
lines.append("RUN_AT=" + datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
lines.append("Command: python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\status_panel_20261112\\_panel_assemble.py")
lines.append("method: hashlib.sha256(path.read_bytes()); size=len(bytes); lines=len(read_text(utf-8).splitlines())")
lines.append("scope: read-only outside OUTDIR; written file = _panel_assemble_stdout.txt only")
for rel in REL_FILES:
    p = ROOT / rel
    if not p.is_file():
        lines.append(rel + " | exists=False")
        continue
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    try:
        n = len(p.read_text(encoding="utf-8").splitlines())
    except Exception:
        n = None
    mt = datetime.datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(timespec="seconds")
    lines.append("%s | size=%d | sha256=%s | mtime=%s | lines=%s" % (rel, len(b), h, mt, n))

txt = "\n".join(lines) + "\n"
print(txt, end="")
(OUTDIR / "_panel_assemble_stdout.txt").write_text(txt, encoding="utf-8")
