"""Adjudication probe: run the REAL _verify_h7_behavior.main() against a
polarity-flipped copy of harness7, and against the pristine file. Reports
exit codes only; nothing in the repo is modified."""
import importlib.util
import tempfile
from pathlib import Path

V = Path("D:/Project/ra2-campaign-forge/lead/goal1_harness7_20261023/_verify_h7_behavior.py")
H7 = Path("D:/Project/ra2-campaign-forge/lead/goal1_harness7_20261023/qc151_trip.harness7.py")

spec = importlib.util.spec_from_file_location("vh7", V)
vh7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh7)

src = H7.read_text(encoding="utf-8")
anchor = 'if _h7_nav_end is not None and _H7_STATE["fs_rect_wait_skipped"]:'
flip = 'if _h7_nav_end is not None and not _H7_STATE["fs_rect_wait_skipped"]:'
assert src.count(anchor) == 1

tmpdir = Path(tempfile.mkdtemp(prefix="h7polar_"))
flipped = tmpdir / "qc151_trip.harness7.py"
flipped.write_text(src.replace(anchor, flip), encoding="utf-8")

print("### pristine ###")
code_p = vh7.main()
print(f"exit={code_p}")
print("### polarity-flipped ###")
vh7.results.clear()
vh7.H7 = flipped
code_f = vh7.main()
print(f"exit={code_f}")
fails = [n for n, ok, d in vh7.results if not ok]
print(f"flipped-suite FAILS: {fails}")
