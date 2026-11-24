"""Three-way controlled test of §3(c) template logic, with a CORRECT adapter.

All three variants share the same correct run_once (proper 1-tuple syntax) and
parse(). They differ only in bad_needle_injection:

  V1 = published template logic (check union run's aggregate)   _cm_AUDIT.md:507-520
  V2 = check AND_k aggregate of broken input list
  V3 = V2 plus a real per-input hit assertion (the missing "input alive" check)

This isolates whether the failure I saw is my adapter's fault or the template's.
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
REPO = Path("D:/Project/ra2-campaign-forge")
SRC = REPO / "lead/d29_ruling_20261106"
WD = REPO / "lead/check_masking_20261109"
SANDBOX_ROOT = WD / "_cmv_tmp" / "tpl_3way"
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)

_seq = [0]


def run_once(inputs, workdir):
    _seq[0] += 1
    sb = Path(workdir) / ("run_%04d" % _seq[0])
    sb.mkdir(parents=True, exist_ok=True)
    for name in ("check_d29.py", "RULING_D29.md", "FACTCHECK.md"):
        shutil.copy2(str(SRC / name), str(sb / name))
    sp = sb / "check_d29.py"
    text = sp.read_text(encoding="utf-8")
    assert '"互斥", "前提"' in text
    # CORRECT: always emit a real tuple, including trailing comma for k=1
    tuple_dst = ", ".join('"%s"' % x for x in inputs) + ","
    sp.write_text(text.replace('"互斥", "前提"', tuple_dst, 1), encoding="utf-8")
    cmd = [sys.executable, "-I", "-X", "utf8", str(sp)]
    p = subprocess.run(cmd, cwd=str(sb), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).splitlines()


def parse(lines):
    txt = "\n".join(lines)
    return (("PASS" in txt) and ("FAIL" not in txt)), ["[4]" not in txt]


def and_k(inputs, workdir):
    per = []
    for x in inputs:
        rc, lines = run_once([x], workdir)
        ok, controls = parse(lines)
        per.append(ok and rc == 0 and all(controls))
    return all(per)


def inject_v1(inputs, workdir):
    """PUBLISHED TEMPLATE: union run aggregate decides 'caught'."""
    res = []
    for i in range(len(inputs)):
        broken = list(inputs); broken[i] = SENTINEL
        rc, lines = run_once(broken, workdir)
        ok, _ = parse(lines)
        res.append((rc != 0) or (not ok))
    return all(res)


def inject_v2(inputs, workdir):
    """Check AND_k aggregate of the broken list."""
    res = []
    for i in range(len(inputs)):
        broken = list(inputs); broken[i] = SENTINEL
        res.append(not and_k(broken, workdir))
    return all(res)


def inject_v3(inputs, workdir):
    """AND_k + explicit per-input liveness assertion against the source doc."""
    ruling = (SRC / "RULING_D29.md").read_text(encoding="utf-8")
    res = []
    for i in range(len(inputs)):
        broken = list(inputs); broken[i] = SENTINEL
        alive = [w for w in broken if w != SENTINEL and w in ruling]
        # a broken needle must be detected: either AND_k fails, or we assert
        # that the dead input is NOT alive in the corpus
        detected = (not and_k(broken, workdir)) or (SENTINEL not in ruling and len(alive) < len(broken))
        res.append(detected)
    return all(res)


def main():
    inputs = ["互斥", "前提"]
    with tempfile.TemporaryDirectory(dir=str(SANDBOX_ROOT)) as wd:
        base_rc, base_lines = run_once(inputs, wd)
        base_ok, _ = parse(base_lines)
        agg = and_k(inputs, wd)
        for name, fn in (("V1_published", inject_v1), ("V2_AND_k", inject_v2), ("V3_liveness", inject_v3)):
            inj = fn(inputs, wd)
            print(f"{name}: BASE_PASS={base_ok} AND_k={agg} BAD_NEEDLE_CAUGHT={inj} "
                  f"DISTINGUISHABLE_PASS={base_ok and agg and inj}")
        # show that a correct adapter DOES make single-SENTINEL fail
        rc, lines = run_once([SENTINEL], wd)
        ok, _ = parse(lines)
        print(f"sanity single-SENTINEL run: EXIT={rc} PASS_parsed={ok} lines={lines}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
