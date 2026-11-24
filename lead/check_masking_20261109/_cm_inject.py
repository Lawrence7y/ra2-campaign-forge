"""Bad-input injection driver for check_d27 / check_d29 / check_d30.

READ-ONLY with respect to every audited source file. For each scenario we build
a fresh sandbox directory INSIDE the sole write domain
lead/check_masking_20261109/_cm_tmp/<case>/<scenario>/, copy the gate script
and its two input documents there byte-for-byte, then mutate ONLY those copies.
The gate is launched as a subprocess with cwd = that sandbox directory.

Two injection families:
  A) DOC-side   : delete one keyword from a section body, leaving sibling
                  keyword(s) alive -> "one input dead, rest alive".
  B) SCRIPT-side: replace one keyword literal in the gate's tuple with a
                  guaranteed zero-hit sentinel, leaving all other checks intact
                  -> the abstract "broken needle" analogue of the masking audit.

All writes are confined to WD; a resolve()-based containment assertion guards
every write. Run: python -I -X utf8 <this file>
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

WD = Path("D:/Project/ra2-campaign-forge/lead/check_masking_20261109")
TMP = WD / "_cm_tmp"
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"

CASES = {
    # d27's DIRECTORY is CWD-relative ("lead/d27_ruling_20261106"), so its
    # sandbox must contain that nested subpath; d29/d30 use __file__.parent.
    "d27": ("lead/d27_ruling_20261106", "check_d27.py",
            ("RULING_D27.md", "FACTCHECK.md"), "lead/d27_ruling_20261106"),
    "d29": ("lead/d29_ruling_20261106", "check_d29.py",
            ("RULING_D29.md", "FACTCHECK.md"), ""),
    "d30": ("lead/d30_ruling_20261106", "check_d30.py",
            ("RULING_D30.md", "FACTCHECK.md"), ""),
}


def guard(p: Path) -> Path:
    """Reject anything that escapes the sole write domain."""
    root = WD.resolve()
    q = p.resolve()
    if root != q and root not in q.parents:
        raise ValueError("write outside write domain: " + str(q))
    return q


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def doc_dir(sandbox: Path, info) -> Path:
    """Where the gate expects its input documents (d27 uses a CWD-relative subdir)."""
    return sandbox / info[3] if info[3] else sandbox


def doc_delete(filename, old, new, count=1):
    def mutate(sandbox: Path, info):
        p = guard(doc_dir(sandbox, info) / filename)
        before_bytes = p.read_bytes()
        text = before_bytes.decode("utf-8-sig")
        before = text.count(old)
        text2 = text.replace(old, new, count)
        after_bytes = text2.encode("utf-8")
        guard(p).write_bytes(after_bytes)
        return (f"DOC {filename}: {old!r} -> {new!r} x{count}; "
                f"occurrences {before} -> {text2.count(old)}; "
                f"bytes {len(before_bytes)} -> {len(after_bytes)}")
    return mutate


def script_swap(old_literal, new_literal):
    def mutate(sandbox: Path, info):
        p = guard(sandbox / info[1])
        before_bytes = p.read_bytes()
        text = before_bytes.decode("utf-8")
        before = text.count(old_literal)
        after_bytes = text.replace(old_literal, new_literal).encode("utf-8")
        guard(p).write_bytes(after_bytes)
        return (f"SCRIPT {info[1]}: {old_literal!r} -> {new_literal!r}; "
                f"occurrences {before} -> {text.count(new_literal)}; "
                f"bytes {len(before_bytes)} -> {len(after_bytes)}; "
                f"sha256 {sha(before_bytes)[:16]} -> {sha(after_bytes)[:16]}")
    return mutate


def identity(sandbox: Path, info):
    p = guard(sandbox / info[1])
    return ("CONTROL: byte-identical copies, no mutation; script sha256="
            + sha(p.read_bytes()))


SCENARIOS = [
    ("d27", "control", "CONTROL (copies unmodified)", identity),
    ("d27", "a_kill_1", "A: kill '外推' in 未背书, sibling '卡顿不存在' alive",
     doc_delete("RULING_D27.md", "外推", SENTINEL)),
    ("d27", "a_kill_2", "A: kill '卡顿不存在' in 未背书, sibling '外推' alive",
     doc_delete("RULING_D27.md", "卡顿不存在", SENTINEL)),
    ("d27", "b_kill_2", "B: script tuple -> ('外推', SENTINEL)",
     script_swap('"卡顿不存在"', '"' + SENTINEL + '"')),
    ("d27", "b_kill_1", "B: script tuple -> (SENTINEL, '卡顿不存在')",
     script_swap('"外推"', '"' + SENTINEL + '"')),
    ("d27", "neg_ctrl", "NEG-CONTROL: kill sole keyword '循环论证' of check [4]",
     doc_delete("RULING_D27.md", "循环论证", SENTINEL)),

    ("d29", "control", "CONTROL (copies unmodified)", identity),
    ("d29", "a_kill_1", "A: kill '前提' in 冲突是否成立, sibling '互斥' alive",
     doc_delete("RULING_D29.md", "前提", SENTINEL)),
    ("d29", "a_kill_2", "A: kill ALL '互斥' in 冲突是否成立, sibling '前提' alive",
     doc_delete("RULING_D29.md", "互斥", SENTINEL, count=99)),
    ("d29", "b_kill_2", "B: script tuple -> ('互斥', SENTINEL)",
     script_swap('"前提"', '"' + SENTINEL + '"')),
    ("d29", "b_kill_1", "B: script tuple -> (SENTINEL, '前提')",
     script_swap('"互斥"', '"' + SENTINEL + '"')),
    ("d29", "neg_ctrl", "NEG-CONTROL: kill require_all=True word '191' in 未背书",
     doc_delete("RULING_D29.md", "191", SENTINEL)),
    ("d29", "neg_ctrl_all", "NEG-CONTROL(all): kill ALL '191' -> AND-path must FAIL",
     doc_delete("RULING_D29.md", "191", SENTINEL, count=99)),
    ("d29", "and_kill_1", "AND-extra: kill ALL '外推' (one of 3 required words)",
     doc_delete("RULING_D29.md", "外推", SENTINEL, count=99)),

    ("d30", "control", "CONTROL (copies unmodified)", identity),
    ("d30", "a_kill_1", "A: kill ALL '93.98' in 三档权衡的实质, sibling '误报率' alive",
     doc_delete("RULING_D30.md", "93.98", SENTINEL, count=99)),
    ("d30", "a_kill_2", "A: kill ALL '误报率' in 三档权衡的实质, sibling '93.98' alive",
     doc_delete("RULING_D30.md", "误报率", SENTINEL, count=99)),
    ("d30", "b_kill_2", "B: script tuple -> ('93.98', SENTINEL)",
     script_swap('"误报率"', '"' + SENTINEL + '"')),
    ("d30", "b_kill_1", "B: script tuple -> (SENTINEL, '误报率')",
     script_swap('"93.98"', '"' + SENTINEL + '"')),
    ("d30", "neg_ctrl", "NEG-CONTROL: kill require_all=True word '栈采样' in 未背书",
     doc_delete("RULING_D30.md", "栈采样", SENTINEL)),
    ("d30", "neg_ctrl_all", "NEG-CONTROL(all): kill ALL '栈采样' -> AND-path must FAIL",
     doc_delete("RULING_D30.md", "栈采样", SENTINEL, count=99)),
    ("d30", "and_kill_1", "AND-extra: kill ALL '外推' (one of 2 required words)",
     doc_delete("RULING_D30.md", "外推", SENTINEL, count=99)),
]


def run(sandbox: Path, script_name: str):
    cmd = [sys.executable, "-I", "-X", "utf8", str(guard(sandbox / script_name))]
    p = subprocess.run(cmd, cwd=str(sandbox.resolve()), capture_output=True,
                        text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or ""), " ".join(cmd)


def main():
    lines = []
    def w(s=""):
        print(s)
        lines.append(s)

    w("REPO = D:/Project/ra2-campaign-forge")
    w("WRITE DOMAIN = " + str(WD))
    w("SENTINEL = " + SENTINEL)
    w("python = " + sys.executable)
    w()
    w("=== SOURCE FINGERPRINTS BEFORE (read-only) ===")
    for tag, (sub, script, _, _) in CASES.items():
        p = Path("D:/Project/ra2-campaign-forge") / sub / script
        b = p.read_bytes()
        w(f"{tag}: {sub}/{script} bytes = {len(b)} sha256 = {sha(b)}")
    w()

    if TMP.exists():
        shutil.rmtree(str(TMP))
    TMP.mkdir(parents=True, exist_ok=True)

    results = []
    for tag, slug, label, mutate in SCENARIOS:
        sub, script, docs, docsub = CASES[tag]
        src = Path("D:/Project/ra2-campaign-forge") / sub
        sandbox = guard(TMP / tag / slug)
        docs_at = doc_dir(sandbox, CASES[tag])
        docs_at.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src / script), str(sandbox / script))
        for d in docs:
            shutil.copy2(str(src / d), str(docs_at / d))
        w("=" * 78)
        w(f"[{tag}] {label}")
        w("  " + mutate(sandbox, CASES[tag]))
        rc, out, cmd = run(sandbox, script)
        w("  CMD = " + cmd)
        w("  CWD = " + str(sandbox.resolve()))
        w(f"  EXIT = {rc}")
        for ln in out.rstrip("\n").splitlines():
            w("  | " + ln)
        results.append((tag, slug, label, rc, out))
        w()

    w("=== SOURCE FINGERPRINTS AFTER (must be unchanged) ===")
    for tag, (sub, script, _, _) in CASES.items():
        p = Path("D:/Project/ra2-campaign-forge") / sub / script
        b = p.read_bytes()
        w(f"{tag}: bytes = {len(b)} sha256 = {sha(b)}")
    w()
    w("=== SUMMARY TABLE ===")
    w(f"{'tag':5} {'slug':10} {'exit':>5} {'verdict':>8}  label")
    for tag, slug, label, rc, out in results:
        w(f"{tag:5} {slug:10} {rc:>5} {'PASS' if rc == 0 else 'FAIL':>8}  {label}")
    w()
    injected = [r for r in results if r[1] != "control"]
    masked = [r for r in injected if r[3] == 0]
    w(f"injected scenarios = {len(injected)}")
    w(f"injected scenarios still EXIT=0 (PASS) = {len(masked)}")
    w("DONE")

    dest = guard(WD / "_cm_injection_out.txt")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n[written] " + str(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
