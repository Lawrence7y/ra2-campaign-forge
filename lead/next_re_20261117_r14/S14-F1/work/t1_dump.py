#!/usr/bin/env python3
"""Dump raw capstone windows for S14-F1 analysis (skipdata=True)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import wbase

OUT = Path(__file__).resolve().parents[1] / "EVIDENCE"
OUT.mkdir(parents=True, exist_ok=True)

WINDOWS = {
    "E01_update_window.txt": (0x4F8440, 0x4F9440),
    "E02_aitrigger_eval.txt": (0x6F0AB0, 0x6F0FB8),
    "E03_conditionmet.txt": (0x41E720, 0x41EAA9),
    "E04_createteam.txt": (0x6F09C0, 0x6F0A6E),
    "E05_team_ctor.txt": (0x6E8A90, 0x6E8DE1),
    "E06_foot_ai_window.txt": (0x4DA530, 0x4DAF48),
    "E07_house_caller_window.txt": (0x55DE40, 0x55E2B0),
    "E09_aitrigger_parse.txt": (0x41FB10, 0x41FC90),
    "E10_aitrigger_loadlist.txt": (0x41F2E0, 0x41F580),
    "E11_aitrigger_rulesloader.txt": (0x41F580, 0x41FB10),
}

for name, (a, b) in WINDOWS.items():
    txt = wbase.dump_range(a, b)
    (OUT / name).write_text(f"; capstone 5.0.7 skipdata=True; VA [{a:#x},{b:#x})\n{txt}\n", encoding="utf-8")
    print(name, len(txt.splitlines()))
