"""Corrected 甲' outer shell (external, zero source modification) — grounded run.

Fixes the three defects the reviewer found in _cm_AUDIT.md §3(c) (:469-536):
  1) parse() now receives rc (the published signature could not see it);
  2) controls is guaranteed non-empty (published parse needed the caller to invent it);
  3) k=1 tuple replacement keeps a trailing comma (published adapter degraded to str);
  4) ROOT CAUSE: bad_needle_injection() no longer trusts the union run's aggregate
     (which is exactly the masked boolean). It requires AND_k(broken) to FAIL.

Proved against check_d29.py's OR word table ("互斥","前提"), copy-only sandbox.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
REPO = Path("D:/Project/ra2-campaign-forge")
SRC = REPO / "lead/d29_ruling_20261106"
ORIGINAL_TUPLE = '"互斥", "前提"'
INPUTS = ["互斥", "前提"]
_seq = [0]


def run_once(inputs, workdir):
    """Adapter (b): hardcoded literal table -> copy the gate into a sandbox,
    replace the tuple with `inputs`, never write back to the audited source."""
    _seq[0] += 1
    sb = Path(workdir) / ("run_%04d" % _seq[0])
    sb.mkdir(parents=True, exist_ok=True)
    for name in ("check_d29.py", "RULING_D29.md", "FACTCHECK.md"):
        shutil.copy2(str(SRC / name), str(sb / name))
    sp = sb / "check_d29.py"
    text = sp.read_text(encoding="utf-8")
    assert ORIGINAL_TUPLE in text
    # trailing comma => remains a REAL tuple even when k == 1
    dst = ", ".join('"%s"' % x for x in inputs) + ","
    sp.write_text(text.replace(ORIGINAL_TUPLE, dst, 1), encoding="utf-8")
    cmd = [sys.executable, "-I", "-X", "utf8", str(sp)]
    p = subprocess.run(cmd, cwd=str(sb), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).splitlines(), " ".join(cmd)


def parse(rc, lines):
    """Returns (aggregate_pass, controls). controls is NON-EMPTY by construction."""
    txt = "\n".join(lines)
    aggregate_pass = (rc == 0) and ("PASS" in txt) and ("FAIL" not in txt)
    controls = ["[4]" not in txt]        # OR-item [4] not reported as failed
    return aggregate_pass, controls


def real_per_input_selftest(inputs, workdir):
    """甲' core: run the unmodified gate once per input; AGGREGATE = AND_k."""
    per = []
    for i, x in enumerate(inputs):
        rc, lines, _ = run_once([x], workdir)          # single input, NOT the union
        ok, controls = parse(rc, lines)
        per.append(ok and rc == 0 and all(controls))
        print(f"  input[{i}] = {x!r}: SELF_TEST={'PASS' if per[-1] else 'FAIL'}"
              f" controls={sum(controls)}/{len(controls)}")
    return all(per)


def bad_needle_injection(inputs, workdir):
    """Requirement: with input i replaced by a guaranteed-zero-hit sentinel,
    AND_k(broken) MUST FAIL. Do NOT trust the union run's aggregate boolean."""
    results = []
    for i in range(len(inputs)):
        broken = list(inputs)
        broken[i] = SENTINEL
        caught = not real_per_input_selftest(broken, workdir)
        results.append(caught)
        print(f"  broken[{i}] -> {SENTINEL}: caught={caught}")
    return all(results)


def main():
    WD = REPO / "lead/check_masking_20261109"
    (WD / "_cmd_tmp").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(WD / "_cmd_tmp")) as wd:
        base_rc, base_lines, cmd = run_once(INPUTS, wd)
        base_ok, _ = parse(base_rc, base_lines)
        print("BASE CMD =", cmd)
        print("BASE EXIT =", base_rc, "lines =", base_lines)
        agg = real_per_input_selftest(INPUTS, wd)
        inj = bad_needle_injection(INPUTS, wd)
        print(f"BASE_PASS={base_ok}  AND_k={agg}  BAD_NEEDLE_CAUGHT={inj}")
        verdict = base_ok and agg and inj
        print("DISTINGUISHABLE_PASS =", verdict)
        return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
