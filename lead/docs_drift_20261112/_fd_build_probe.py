# -*- coding: utf-8 -*-
"""STEP 2 item 5: read-only build probe of ra2forge, entirely inside write domain.

Run as: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_build_probe.py

No game executable, loader or live process is touched. Only:
  - imports ra2forge.cli (sys.path set in-script because -I isolates cwd);
  - calls main(["example", <write-domain>/demo_campaign.json]);
  - calls main(["build", "--design", <that>, "--out", <write-domain>/build_probe]);
  - fingerprints every produced file with hashlib.

sys.dont_write_bytecode is set BEFORE any import so no __pycache__ is written
outside the write domain.
"""
import sys
sys.dont_write_bytecode = True

import contextlib
import hashlib
import io
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "docs_drift_20261112"
PROBE = WD / "build_probe"
PROBE.mkdir(parents=True, exist_ok=True)
DESIGN = PROBE / "demo_campaign.json"
OUT = PROBE / "out"

# -I removes cwd from sys.path; add the repo root so `import ra2forge` resolves.
sys.path.insert(0, str(ROOT))

from ra2forge.cli import main as cli_main  # noqa: E402

TZ = timezone(timedelta(hours=8))


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(argv):
    so, se = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
        try:
            code = cli_main(argv)
        except SystemExit as e:
            code = e.code
        except BaseException as e:
            code = "EXC:%s:%s" % (type(e).__name__, e)
    return {"argv": argv, "exit": code, "stdout": so.getvalue(), "stderr": se.getvalue()}


results = []
results.append(run(["example", str(DESIGN)]))
results.append(run(["build", "--design", str(DESIGN), "--out", str(OUT)]))

produced = []
if OUT.is_dir():
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            produced.append({
                "rel": p.relative_to(ROOT).as_posix(),
                "bytes": p.stat().st_size,
                "sha256": sha256_of(p),
                "mtime_local": datetime.fromtimestamp(p.stat().st_mtime, TZ).strftime(
                    "%Y-%m-%d %H:%M:%S+08:00"),
            })

report = {
    "generated_at_local": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S+08:00"),
    "command": "python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_build_probe.py",
    "python_version": sys.version,
    "sys_path_inserted": str(ROOT),
    "dont_write_bytecode": sys.dont_write_bytecode,
    "note": "equivalent to `python -m ra2forge example` + `python -m ra2forge build --design ... --out ...`",
    "no_install_flag": True,
    "results": results,
    "produced_files": produced,
}
(PROBE / "BUILD_PROBE_RESULT.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

lines = [
    "# 交付线 C · ra2forge 构建实测（STEP 2 第 5 条）",
    "",
    "> 命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/docs_drift_20261112/_fd_build_probe.py`",
    "> 等价于 `python -m ra2forge example` + `python -m ra2forge build --design ... --out ...`，",
    "> 但用单一 `-I -X utf8 <绝对脚本>` 调用以满足本任务铁律；脚本内 `sys.path.insert` 提供 `PYTHONPATH` 等价物。",
    "> `--install` 未传；**未启动任何游戏/加载器、未读活进程内存、未写游戏目录**。",
    "> `sys.dont_write_bytecode=True` 在任何 import 前置位，避免 `ra2forge/__pycache__` 落在写域外。",
    "",
]
for r in results:
    lines.append("## 调用：`%s`" % " ".join(r["argv"]))
    lines.append("")
    lines.append("- **exit = %s**" % r["exit"])
    lines.append("- stdout：")
    lines.append("```text")
    lines.append(r["stdout"].rstrip() or "(empty)")
    lines.append("```")
    if r["stderr"].strip():
        lines.append("- stderr：")
        lines.append("```text")
        lines.append(r["stderr"].rstrip())
        lines.append("```")
    lines.append("")
lines.append("## 产物（仅写域内，hashlib 实算）")
lines.append("")
lines.append("共 %d 个文件。" % len(produced))
lines.append("")
lines.append("| 文件 | 字节数 | sha256 |")
lines.append("|:--|--:|:--|")
for p in produced:
    lines.append("| `%s` | %d | `%s` |" % (p["rel"], p["bytes"], p["sha256"]))
lines.append("")
(PROBE / "BUILD_PROBE_RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print("BUILD PROBE OK")
for r in results:
    print("argv=%s exit=%s" % (" ".join(r["argv"]), r["exit"]))
    print(r["stdout"].rstrip())
print("produced_files=%d" % len(produced))
