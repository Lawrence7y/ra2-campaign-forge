#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_gp_apply.py -- apply the 5-line ledger patch to a COPY only.

The original ledger (lead/GOAL_THREE_TARGETS_20261018.md) is READ-ONLY here.
Steps:
  1. byte-for-byte copy original -> _gp_goal_copy.md, verify with hashlib.sha256
  2. read the COPY; for each of the 5 records require
       (a) the stated 1-based line number exists
       (b) that line's content, excluding its EOL, is byte-for-byte == before
     -> on any mismatch, abort with an error and write nothing.
     Also guard: line 6 must be untouched, the line count must not change, and
     exactly the 5 stated line numbers may differ (no sixth line may change).
  3. write the patched bytes back to the COPY only
  4. difflib.unified_diff(original, copy, n=1) -> _gp_diff.txt
  5. re-verify the original sha256 is still unchanged.

All rewrite data comes from _gp_patch_data.json (transcribed from the ask);
this script invents no replacement text.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "GOAL_THREE_TARGETS_20261018.md"
COPY = HERE / "_gp_goal_copy.md"
DATA = HERE / "_gp_patch_data.json"
DIFF_OUT = HERE / "_gp_diff.txt"

EXPECTED_ORIGINAL_SHA256 = (
    "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_lf_keepends(data: bytes) -> list[bytes]:
    """Split on b'\n' only, keeping EOLs; avoids bytes.splitlines() extras."""
    parts = data.split(b"\n")
    if data.endswith(b"\n"):
        return [p + b"\n" for p in parts[:-1]]
    return [p + b"\n" for p in parts[:-1]] + [parts[-1]]


def content(line: bytes) -> bytes:
    """Line content with exactly one trailing LF (and one CR) removed."""
    if line.endswith(b"\n"):
        line = line[:-1]
        if line.endswith(b"\r"):
            line = line[:-1]
    return line


def eol(line: bytes) -> bytes:
    return line[len(content(line)):]


def abort(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print("ABORT: " + msg, file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    # ---- step 1: copy, read-only on the original -------------------------
    if not ORIGINAL.is_file():
        abort(f"original missing: {ORIGINAL}")
    original_bytes = ORIGINAL.read_bytes()
    orig_hash_before = sha256(original_bytes)
    if orig_hash_before != EXPECTED_ORIGINAL_SHA256:
        abort(
            "original sha256 mismatch: expected "
            f"{EXPECTED_ORIGINAL_SHA256}, got {orig_hash_before}"
        )

    shutil.copyfile(ORIGINAL, COPY)  # byte-for-byte copy; original only read
    copy_bytes = COPY.read_bytes()
    copy_hash = sha256(copy_bytes)
    if copy_hash != orig_hash_before:
        abort(
            f"copy sha256 {copy_hash} != original sha256 {orig_hash_before}"
        )
    print(f"[1] copy OK: {COPY.name} size={len(copy_bytes)} "
          f"sha256={copy_hash} (== original {orig_hash_before})")

    # ---- step 2: load rewrite data ---------------------------------------
    records = json.loads(DATA.read_text(encoding="utf-8"))
    if len(records) != 5:
        abort(f"expected 5 patch records, got {len(records)}")
    for r in records:
        if set(r.keys()) != {"line_no", "before", "after"}:
            abort(f"bad record keys: {sorted(r.keys())}")
        if isinstance(r["after"], str) and (
            "\n" in r["after"] or "\r" in r["after"]
        ):
            abort(f"line {r['line_no']}: after text contains a line break")

    lines = split_lf_keepends(copy_bytes)
    n_lines = len(lines)
    print(f"[2] copy line count (LF-based, 1-based) = {n_lines}")

    # line 6 snapshot (guard required by the ask)
    if n_lines < 6:
        abort("copy has fewer than 6 lines")
    line6_before = lines[5]

    # ---- double validation: line number + byte-exact before -------------
    for r in records:
        no = r["line_no"]
        if not isinstance(no, int) or not (1 <= no <= n_lines):
            abort(f"line_no {no} out of range 1..{n_lines}")
        got = content(lines[no - 1])
        want = r["before"].encode("utf-8")
        if got != want:
            abort(
                f"line {no}: before mismatch (NOT replaced). "
                f"got={got!r} want={want!r}"
            )
        # the before string must also be unique in the whole file, so no
        # accidental extra (sixth) line can be swept in
        hits = [i for i, l in enumerate(lines, 1) if content(l) == want]
        if hits != [no]:
            abort(f"line {no}: before string occurs at {hits}, expected [{no}]")
        print(f"    validated line {no}: byte-exact before, unique occurrence")

    # ---- apply to the copy's in-memory lines -----------------------------
    for r in records:
        no = r["line_no"]
        lines[no - 1] = r["after"].encode("utf-8") + eol(lines[no - 1])

    # ---- guards: no sixth line, line 6 intact, count intact --------------
    if len(lines) != n_lines:
        abort("line count changed during application")
    if lines[5] != line6_before:
        abort("line 6 would be changed -- stopping, no files written")
    orig_lines = split_lf_keepends(copy_bytes)
    changed = [
        i for i, (a, b) in enumerate(zip(orig_lines, lines), 1) if a != b
    ]
    expected_changed = sorted(r["line_no"] for r in records)
    if changed != expected_changed:
        abort(
            f"changed lines {changed} != expected {expected_changed} "
            "-- possible sixth-line modification, stopping"
        )
    print(f"[3] changed lines = {changed}; line 6 unchanged: "
          f"{lines[5] == line6_before}")

    patched_bytes = b"".join(lines)
    COPY.write_bytes(patched_bytes)  # ONLY the copy is written
    print(f"[4] patched COPY size={len(patched_bytes)} "
          f"sha256={sha256(patched_bytes)}")

    # ---- step 3: difflib.unified_diff(original vs copy, n=1) ------------
    a = original_bytes.decode("utf-8").splitlines(keepends=True)
    b = patched_bytes.decode("utf-8").splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            a,
            b,
            fromfile="lead/GOAL_THREE_TARGETS_20261018.md",
            tofile="lead/goal_line_patch_20261110/_gp_goal_copy.md",
            n=1,
            lineterm="\n",
        )
    )
    # write as raw UTF-8 bytes, no Windows newline translation
    DIFF_OUT.write_bytes("".join(diff_lines).encode("utf-8"))
    hunks = sum(1 for l in diff_lines if l.startswith("@@ "))
    dels = sum(
        1 for l in diff_lines
        if l.startswith("-") and not l.startswith("---")
    )
    adds = sum(
        1 for l in diff_lines
        if l.startswith("+") and not l.startswith("+++")
    )
    print(f"[5] {DIFF_OUT.name}: hunks={hunks} deleted={dels} added={adds} "
          f"bytes={DIFF_OUT.stat().st_size}")

    # ---- step 6: original untouched --------------------------------------
    orig_hash_after = sha256(ORIGINAL.read_bytes())
    print(f"[6] original sha256 before={orig_hash_before}")
    print(f"[6] original sha256 after ={orig_hash_after}")
    if orig_hash_after != EXPECTED_ORIGINAL_SHA256:
        abort("original sha256 changed!")
    print("[6] original UNCHANGED -- OK")
    print(f"[sizes] original={len(original_bytes)} "
          f"patched_copy={len(patched_bytes)} "
          f"delta={len(patched_bytes) - len(original_bytes)}")


if __name__ == "__main__":
    main()
