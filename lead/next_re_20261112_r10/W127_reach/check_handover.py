#!/usr/bin/env python3
"""Sanity check on the handover doc after the 2026-11-15 edits."""
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
b = open(p, "rb").read()
print("bytes", len(b))
print("BOM", b[:3] == b"\xef\xbb\xbf")
s = b.decode("utf-8")
print("chars", len(s))
print("crlf", s.count("\r\n"), "lf_total", s.count("\n"))
checks = {
    "1'3c-prime (correction block)": "1'3c\u2032" in s,
    "1'6 (reachability)": "1'6" in s,
    "G2 fix row": "G2" in s,
    "old 20-site claim still present as historical": "无检查调用点是 20 处" in s,
    "dual-guard warning": "崩溃点平移" in s,
}
for k, v in checks.items():
    print("  %-48s %s" % (k, v))
print("headings:")
for line in s.split("\n"):
    if line.startswith("#"):
        print("   ", line[:90])
