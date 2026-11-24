"""Diagnosis of §3(c) template port result.

The published template's bad_needle_injection() calls run_once(broken) -- i.e.
the UNION run with a dead needle -- and then checks that union run's aggregate.
That is exactly the masked boolean the defect lives in. So it can never return
True for an OR-compressed gate. Here I test the minimal correction: require the
AND_k aggregate (real_per_input_selftest) to become FAIL when input i is broken.

Only bad_needle_injection is changed; everything else is identical to
_cmv_template_port.py.
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
REPO = Path("D:/Project/ra2-campaign-forge")
SRC = REPO / "lead/d29_ruling_20261106"
WD = REPO / "lead/check_masking_20261109"
SANDBOX_ROOT = WD / "_cmv_tmp" / "tpl_fix"
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)


def run_once(inputs, workdir):
    sb = Path(workdir) / ("run_" + str(abs(hash(tuple(inputs)))))
    sb.mkdir(parents=True, exist_ok=True)
    for name in ("check_d29.py", "RULING_D29.md", "FACTCHECK.md"):
        shutil.copy2(str(SRC / name), str(sb / name))
    sp = sb / "check_d29.py"
    text = sp.read_text(encoding="utf-8")
    assert '"互斥", "前提"' in text
    sp.write_text(text.replace('"互斥", "前提"',
                               ", ".join('"%s"' % x for x in inputs), 1),
                  encoding="utf-8")
    cmd = [sys.executable, "-I", "-X", "utf8", str(sp)]
    p = subprocess.run(cmd, cwd=str(sb), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).splitlines()


def parse(lines):
    txt = "\n".join(lines)
    return (("PASS" in txt) and ("FAIL" not in txt)), ["[4]" not in txt]


def real_per_input_selftest(inputs, workdir):
    per = []
    for i, x in enumerate(inputs):
        rc, lines = run_once([x], workdir)
        ok, controls = parse(lines)
        per.append(ok and rc == 0 and all(controls))
        print(f"  input[{i}] = {x!r}: SELF_TEST={'PASS' if per[-1] else 'FAIL'}")
    return all(per)


def bad_needle_injection(inputs, workdir):
    """MINIMAL CORRECTION: check that AND_k aggregate fails, not the union run."""
    results = []
    for i in range(len(inputs)):
        broken = list(inputs)
        broken[i] = SENTINEL
        agg = real_per_input_selftest(broken, workdir)
        caught = not agg                      # AND_k must become FAIL
        results.append(caught)
        print(f"  broken[{i}] -> SENTINEL: caught={caught}")
    return all(results)


def main():
    inputs = ["互斥", "前提"]
    with tempfile.TemporaryDirectory(dir=str(SANDBOX_ROOT)) as workdir:
        base_rc, base_lines = run_once(inputs, workdir)
        base_ok, _ = parse(base_lines)
        agg = real_per_input_selftest(inputs, workdir)
        inj = bad_needle_injection(inputs, workdir)
        print(f"BASE_PASS={base_ok}  AND_k={agg}  BAD_NEEDLE_CAUGHT={inj}")
        verdict = base_ok and agg and inj
        print("DISTINGUISHABLE_PASS =", verdict)
        return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
