#!/usr/bin/env python3
"""Append W127 ledger sections (§825-§827) to the ledger, encoding-safe.

The ledger is UTF-8 without BOM and uses CRLF line endings.
(This is asserted, not assumed: a previous inline attempt compared against a
string that PowerShell had mangled through backtick escapes.)
"""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
ADD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W127_reach\ledger_sections_825_827.md"

raw = open(LEDGER, "rb").read()
if raw[:3] == b"\xef\xbb\xbf":
    sys.exit("ABORT: ledger has a UTF-8 BOM; would double it")
src = raw.decode("utf-8")                     # strict: raises if not valid UTF-8
n_crlf = src.count("\r\n")
n_lf = src.count("\n")
print("ledger bytes=%d chars=%d crlf=%d lf_total=%d" % (len(raw), len(src), n_crlf, n_lf))

if "## §825" in src:
    sys.exit("ABORT: §825 already present")

sec = io.open(ADD, encoding="utf-8").read()
if "\r\n" not in sec:
    sec = sec.replace("\n", "\r\n")
    print("converted appended section to CRLF")

out = src.rstrip("\r\n") + "\r\n\r\n" + sec.lstrip("\r\n")
if not out.endswith("\r\n"):
    out += "\r\n"

open(LEDGER, "wb").write(out.encode("utf-8"))

# verify
back = open(LEDGER, "rb").read().decode("utf-8")
print("new bytes=%d chars=%d" % (len(open(LEDGER, 'rb').read()), len(back)))
print("sections now:",
      [s for s in ("## §825", "## §826", "## §827") if s in back])
print("tail repr:", repr(back[-160:]))
