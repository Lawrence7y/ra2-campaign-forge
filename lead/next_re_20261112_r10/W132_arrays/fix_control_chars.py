#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repair the 4 stray control characters in the atlas ledger.

They are leftovers of the known backslash-escape incident class documented in
this project (a raw Python string turned `\\a` / `\\b` / `\\0` into BEL / BS /
NUL).  Each one is repaired by position, with the surrounding text asserted
first, so this cannot touch anything else.

After the repair the ledger is valid text again (it currently makes tools
classify it as a binary file, which blocks ordinary editing).
"""
import io
import shutil
import sys
import time

P = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

# (offset, bad char, expected text with the bad char marked as {C}, replacement)
FIXES = [
    (15539, "\x07", "20261018{C}pply_backup", "20261018\\apply_backup"),
    (289912, "\x08", "'{C}117:'", "'\\b117:'"),
    (563890, "\x00", "{C}x24 归属搞混", "0x24 归属搞混"),
    (572028, "\x00", "不调用 {C}x0047EA90", "不调用 0x0047EA90"),
]

s = io.open(P, encoding="utf-8", newline="").read()
bad_before = [(i, ord(c)) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("control chars before:", [(i, hex(o)) for i, o in bad_before])
if not bad_before:
    print("nothing to do")
    sys.exit(0)

# verify each site before touching it
for off, ch, expect, repl in FIXES:
    want = expect.replace("{C}", ch)
    got = s[max(0, off - 40): off + 40]
    if want not in got:
        print("ABORT: expected %r near offset %d, got %r" % (want, off, got))
        sys.exit(2)

bak = P + ".bak_ctlfix_%s" % time.strftime("%Y%m%d_%H%M%S")
shutil.copy2(P, bak)
print("backup:", bak)

# replace by scanning, so offsets stay valid
out = list(s)
fixed = 0
for off, ch, expect, repl in FIXES:
    want = expect.replace("{C}", ch)
    if out[off] != ch:
        print("ABORT: offset %d no longer holds %r" % (off, ch))
        sys.exit(2)
assert repl  # the replacement is applied to the whole matched span below
    # nothing per-char; handled after the loop
fixed = 0
s2 = "".join(out)
for off, ch, expect, repl in FIXES:
    want = expect.replace("{C}", ch)
    assert s2.count(want) >= 1
    s2 = s2.replace(want, repl, 1)
    fixed += 1

bad_after = [(i, ord(c)) for i, c in enumerate(s2) if ord(c) < 32 and c not in "\n\t"]
print("control chars after :", [(i, hex(o)) for i, o in bad_after])
if bad_after:
    print("ABORT: still bad, not writing")
    sys.exit(3)

io.open(P, "w", encoding="utf-8", newline="").write(s2)
print("repaired %d sites; size %d -> %d bytes" % (fixed, len(s.encode("utf-8")),
                                                   len(s2.encode("utf-8"))))
