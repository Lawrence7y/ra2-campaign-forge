"""Independent bad-input injection reproduction (no modification of audited sources).

Creates fresh sandboxes in the sole write domain under _cmv_tmp/, byte-copies
each gate script and its two input documents, mutates ONLY those copies, then
runs with cwd = sandbox. Also re-runs the writer's own _cm_tmp B-family copies
to check the claimed outputs reproduce verbatim.
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path("D:/Project/ra2-campaign-forge")
WD = REPO / "lead/check_masking_20261109"
TMP = WD / "_cmv_tmp"
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"

CASES = {
    "d27": ("lead/d27_ruling_20261106", "check_d27.py",
            ("RULING_D27.md", "FACTCHECK.md"), "lead/d27_ruling_20261106"),
    "d29": ("lead/d29_ruling_20261106", "check_d29.py",
            ("RULING_D29.md", "FACTCHECK.md"), ""),
    "d30": ("lead/d30_ruling_20261106", "check_d30.py",
            ("RULING_D30.md", "FACTCHECK.md"), ""),
}

# (tag, own_slug, description, old_literal, new_literal, writer_copy_slug)
SCENARIOS = [
    ("d27", "v_b_kill_2", "kill 2nd OR word '卡顿不存在' in script tuple",
     '"卡顿不存在"', '"' + SENTINEL + '"', "b_kill_2"),
    ("d29", "v_b_kill_2", "kill 2nd OR word '前提' in script tuple",
     '"前提"', '"' + SENTINEL + '"', "b_kill_2"),
    ("d30", "v_b_kill_2", "kill 2nd OR word '误报率' in script tuple",
     '"误报率"', '"' + SENTINEL + '"', "b_kill_2"),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(script, cwd):
    cmd = [sys.executable, "-I", "-X", "utf8", str(script)]
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or ""), " ".join(cmd)


def main():
    print("=== PART 1: FRESH INDEPENDENT SANDBOXES (B-family, script-side dead needle) ===")
    if TMP.exists():
        shutil.rmtree(str(TMP))
    TMP.mkdir(parents=True, exist_ok=True)
    for tag, slug, desc, old, new, _ in SCENARIOS:
        sub, script, docs, docsub = CASES[tag]
        src = REPO / sub
        sandbox = TMP / tag / slug
        docs_at = sandbox / docsub if docsub else sandbox
        docs_at.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src / script), str(sandbox / script))
        for d in docs:
            shutil.copy2(str(src / d), str(docs_at / d))
        sp = sandbox / script
        before = sp.read_bytes()
        text = before.decode("utf-8")
        n_before = text.count(old)
        text2 = text.replace(old, new)
        after = text2.encode("utf-8")
        sp.write_bytes(after)
        print()
        print(f"[{tag}] {slug}: {desc}")
        print(f"  copy mutation: {old!r} -> {new!r}; occurrences {n_before} -> {text2.count(new)}")
        print(f"  copy sha256 = {sha(before)} -> {sha(after)}  bytes = {len(before)} -> {len(after)}")
        rc, out, cmd = run(sp, sandbox)
        print(f"  CMD = {cmd}")
        print(f"  CWD = {sandbox}")
        print(f"  EXIT = {rc}")
        for ln in out.rstrip("\n").splitlines():
            print("  | " + ln)
        print(f"  VERDICT = {'STILL_PASS (masked)' if rc == 0 else 'FAIL (caught)'}")

    print()
    print("=== PART 2: RE-RUN WRITER'S OWN _cm_tmp B-FAMILY COPIES (verbatim reproduction) ===")
    for tag, slug, desc, old, new, wslug in SCENARIOS:
        sub, script, docs, docsub = CASES[tag]
        sandbox = WD / "_cm_tmp" / tag / wslug
        sp = sandbox / script
        print()
        print(f"[{tag}] writer copy {sandbox}")
        if not sp.is_file():
            print("  MISSING COPY - cannot reproduce")
            continue
        print(f"  copy sha256 = {sha(sp.read_bytes())} bytes = {sp.stat().st_size}")
        rc, out, cmd = run(sp, sandbox)
        print(f"  CMD = {cmd}")
        print(f"  CWD = {sandbox}")
        print(f"  EXIT = {rc}")
        for ln in out.rstrip("\n").splitlines():
            print("  | " + ln)

    print()
    print("=== PART 3: A-FAMILY (DOC-side) fresh sandbox, d27 kill sole '卡顿不存在' ===")
    tag = "d27"
    sub, script, docs, docsub = CASES[tag]
    src = REPO / sub
    sandbox = TMP / tag / "v_a_kill_2"
    docs_at = sandbox / docsub
    docs_at.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src / script), str(sandbox / script))
    for d in docs:
        shutil.copy2(str(src / d), str(docs_at / d))
    dp = docs_at / "RULING_D27.md"
    b0 = dp.read_bytes()
    t0 = b0.decode("utf-8-sig")
    t1 = t0.replace("卡顿不存在", SENTINEL, 1)
    dp.write_bytes(t1.encode("utf-8"))
    print(f"  DOC mutation: '卡顿不存在' occurrences {t0.count('卡顿不存在')} -> {t1.count('卡顿不存在')}; bytes {len(b0)} -> {dp.stat().st_size}")
    rc, out, cmd = run(sandbox / script, sandbox)
    print(f"  CMD = {cmd}")
    print(f"  CWD = {sandbox}")
    print(f"  EXIT = {rc}")
    for ln in out.rstrip("\n").splitlines():
        print("  | " + ln)

    print()
    print("=== PART 4: NEG-CONTROL (d29 AND-path must FAIL when all '191' killed) ===")
    tag = "d29"
    sub, script, docs, docsub = CASES[tag]
    src = REPO / sub
    sandbox = TMP / tag / "v_neg_ctrl_all"
    sandbox.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src / script), str(sandbox / script))
    for d in docs:
        shutil.copy2(str(src / d), str(sandbox / d))
    dp = sandbox / "RULING_D29.md"
    t0 = dp.read_bytes().decode("utf-8")
    t1 = t0.replace("191", SENTINEL, 99)
    dp.write_bytes(t1.encode("utf-8"))
    print(f"  DOC mutation: '191' occurrences {t0.count('191')} -> {t1.count('191')}")
    rc, out, cmd = run(sandbox / script, sandbox)
    print(f"  CMD = {cmd}")
    print(f"  EXIT = {rc}")
    for ln in out.rstrip("\n").splitlines():
        print("  | " + ln)

    print()
    print("=== PART 5: SOURCE FINGERPRINTS AFTER ALL MY RUNS (unchanged?) ===")
    expect = {
        "d27": "3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c",
        "d29": "2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14",
        "d30": "6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd",
    }
    for tag, (sub, script, _, _) in CASES.items():
        p = REPO / sub / script
        b = p.read_bytes()
        print(f"  {tag}: bytes={len(b)} sha256={sha(b)} MATCH={sha(b) == expect[tag]}")
    print("DONE")


if __name__ == "__main__":
    sys.exit(main())
