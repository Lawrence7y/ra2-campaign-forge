# -*- coding: utf-8 -*-
r"""W70 bootstrap: generate ADAPTED tool copies from the COPIED W63 tools.

Discipline (HANDOFF §5 / task card): NEVER import another card's script (its
output paths are hardcoded).  We COPY w63_*.py into THIS card as w70_*.py and
apply literal string replacements so every write lands in W70's own out/.
"""
from pathlib import Path

T = Path(__file__).resolve().parent


def gen(src, dst, reps):
    s = (T / src).read_text(encoding="utf-8")
    for a, b in reps:
        assert a in s, "missing literal pattern %r in %s" % (a, src)
        s = s.replace(a, b)
    (T / dst).write_text(s, encoding="utf-8")
    print("wrote %-18s %6d bytes" % (dst, len(s)))


# ---- w70_lib.py : re-point card paths, add per-trip screenshot prefix --------
gen("w63_lib.py", "w70_lib.py", [
    ("W63_route_a_e2e", "W70_c_repeatability"),
    ('LOCK = RUN / ".game_instance.lock"',
     'LOCK = RUN / ".game_instance.lock"\n'
     'SHOT_PREFIX = ""   # W70: set by each driver so screenshots never collide'),
    ("def screenshot(sink: Sink, label: str, hwnd=None, bbox=None):\n"
     "    from PIL import ImageGrab",
     "def screenshot(sink: Sink, label: str, hwnd=None, bbox=None):\n"
     "    label = SHOT_PREFIX + label\n"
     "    from PIL import ImageGrab"),
    ("W63 route(a) E2E card", "W70 card"),
])

# ---- w70_common.py : re-point CARD, swap lib import, lock owner w70 ----------
gen("w63_common.py", "w70_common.py", [
    ("W63_route_a_e2e", "W70_c_repeatability"),
    ("import w63_lib as L", "import w70_lib as L"),
    ('def lock_claim_w63(purpose: str):\n    L.lock_claim("w63", purpose)',
     'def lock_claim_w70(purpose: str):\n    L.lock_claim("w70", purpose)'),
])

# ---- w70_trip.py : per-trip TAG + screenshots, lock owner w70 ---------------
gen("w63_run.py", "w70_trip.py", [
    ("import w63_lib as L", "import w70_lib as L"),
    ("import w63_common as C", "import w70_common as C"),
    ('TAG = "run"',
     'TAG = sys.argv[1] if len(sys.argv) > 1 else "run"\n'
     'L.SHOT_PREFIX = TAG + "_"'),
    ("C.lock_claim_w63(", "C.lock_claim_w70("),
    ('owner="w63"', 'owner="w70"'),
    ('C.OUT / "TRIP_RESULT.json"', 'C.OUT / ("TRIP_%s.json" % TAG)'),
    ("W63 route(a) E2E trip", "W70 trip"),
    ("W63 route(a) trip FINISHED", "W70 trip FINISHED"),
])

print("GEN OK")
