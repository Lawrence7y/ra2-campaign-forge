# -*- coding: utf-8 -*-
"""_append_506.py - append S506 (B boot-table adoption; content in _s506_content.md) to ledgers."""


def append_lines(path, text):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n"); lf = raw.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(x.encode("utf-8") for x in body.split("\n")) + nl
    fh = open(path, "ab")
    try:
        fh.write(out)
    finally:
        fh.close()
    return len(out)


CONTENT = r"D:\Project\ra2-campaign-forge\lead\codex_round_20261030\LEADER_battle\_s506_content.md"
LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

text = open(CONTENT, "r", encoding="utf-8").read()
a = append_lines(LOG, text)
b = append_lines(GOAL, text)
print("APPENDED LOG +%d, GOAL +%d" % (a, b))
