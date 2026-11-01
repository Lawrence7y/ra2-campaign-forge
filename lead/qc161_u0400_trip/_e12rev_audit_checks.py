# -*- coding: utf-8 -*-
"""_e12rev_audit_checks.py — 复核点1：非恒真审计（只读分析自检源码，不改被复核件）。"""
import re

SRC = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_drive_c2_x_e12_selftest.py"
src = open(SRC, encoding="utf-8").read().splitlines()

calls = []
i = 0
while i < len(src):
    l = src[i]
    if re.match(r'\s*check\("', l):
        buf = l
        depth = l.count("(") - l.count(")")
        j = i
        while depth > 0:
            j += 1
            buf += "\n" + src[j]
            depth += src[j].count("(") - src[j].count(")")
        calls.append((i + 1, buf))
        i = j
    i += 1

print("total check call-sites:", len(calls))


def split_top(inner):
    parts, cur, depth, instr, q, k = [], "", 0, False, "", 0
    while k < len(inner):
        ch = inner[k]
        if instr:
            cur += ch
            if ch == "\\" and k + 1 < len(inner):
                cur += inner[k + 1]
                k += 2
                continue
            if ch == q:
                instr = False
        else:
            if ch in "\"'":
                instr = True
                q = ch
                cur += ch
            elif ch in "([{":
                depth += 1
                cur += ch
            elif ch in ")]}":
                depth -= 1
                cur += ch
            elif ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += ch
        k += 1
    parts.append(cur)
    return parts


VARREF = re.compile(
    r"\b(r\d?|r2|rf|rh|rc1|rc2|rcn|rw|re1|ro|rr|rpv|rmd|ridt|rnat|rzero|rbref|rbc|rwf|"
    r"rd|rnew|rex|f\d+|nw0|hits0|m|ops2?|st\d?|tl[a-z0-9_]*|_sr|_dt|_srows|drv_src|bad|"
    r"caught|p|res|out|e12|ec|res)\b"
)
rows = []
for ln, buf in calls:
    cid = re.search(r'check\("([^"]+)"', buf).group(1)
    inner = buf[buf.index('("') + 1:]
    # remove trailing ")"
    inner = inner[: inner.rfind(")")]
    parts = split_top(inner)
    cond = parts[2].strip() if len(parts) >= 3 else "??"
    refs = VARREF.findall(cond)
    taut = cond in ("True", "1", "not []") or (not refs and "sha256" not in cond and "gate_decision" not in cond)
    rows.append((cid, ln, bool(refs), taut, cond[:120].replace("\n", " ")))

print("%-26s %-5s %-6s %-6s %s" % ("cid", "line", "refs?", "TAUT?", "cond"))
for cid, ln, has, taut, cond in rows:
    flag = "  <== CHECK" if (taut or not has) else ""
    print("%-26s %-5d %-6s %-6s %s%s" % (cid, ln, has, taut, cond, flag))
