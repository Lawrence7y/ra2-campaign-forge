# -*- coding: utf-8 -*-
"""_civ_checks_cli.py — 复核员独立求值器的 CLI 包装（只读）。"""
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
from _civ_lib import evaluate  # noqa: E402

doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
v, f = evaluate(doc)
print("INDEPENDENT FACTS:", json.dumps(f, ensure_ascii=False, sort_keys=True, default=str))
if v:
    print("ALERT violations=%d" % len(v))
    for x in v:
        print("  -", x)
    sys.exit(1)
print("OK violations=0")
sys.exit(0)
