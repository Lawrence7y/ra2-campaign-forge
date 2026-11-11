# -*- coding: utf-8 -*-
"""_append_513.py - append S513 (calibration audit + BOOT#7 handover) to ledgers.

沿用 _append_5xx 家族写法：探测目标文件主行尾，只追加、不改写已有字节。
本轮额外加一道守卫：追加后必须满足「HEAD 原字节 + 新增段」前缀关系，否则不落盘。
"""

import subprocess

LEDGERS = [
    "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md",
    "D:/Project/ra2-campaign-forge/lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md",
]
CONTENT = "D:/Project/ra2-campaign-forge/lead/offline_waittrace_20261102/_s513_content.md"


def append_lines(path, text):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(x.encode("utf-8") for x in body.split("\n")) + nl
    fh = open(path, "ab")
    try:
        fh.write(out)
    finally:
        fh.close()
    return len(out)


def head_bytes(path):
    rel = path.replace("D:/Project/ra2-campaign-forge/", "")
    return subprocess.run(["git", "show", "HEAD:" + rel],
                          capture_output=True, cwd="D:/Project/ra2-campaign-forge").stdout


text = open(CONTENT, "r", encoding="utf-8").read()
for path in LEDGERS:
    before = open(path, "rb").read()
    head = head_bytes(path)
    if not before.startswith(head):
        raise SystemExit("ABORT %s: 工作树不是 HEAD 的前缀扩展，拒绝追加" % path)
    n = append_lines(path, text)
    after = open(path, "rb").read()
    if after[:len(before)] != before or not after.startswith(head):
        raise SystemExit("ABORT %s: 追加破坏了既有字节" % path)
    print("APPENDED %-70s +%d bytes  (head+%d)" % (path.rsplit("/", 1)[-1], n, len(after) - len(head)))
