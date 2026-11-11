# -*- coding: utf-8 -*-
"""_append_514.py - append S514 (occ_a definition discrimination) to ledgers.

沿用 _append_513 守卫：工作树必须是 HEAD 的前缀扩展，追加后既有字节不变。
"""

import subprocess

ROOT = "D:/Project/ra2-campaign-forge"
LEDGERS = [
    ROOT + "/lead/GOAL_THREE_TARGETS_20261018.md",
    ROOT + "/lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md",
]
CONTENT = ROOT + "/lead/offline_waittrace_20261102/_s514_content.md"


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
    rel = path.replace(ROOT + "/", "")
    return subprocess.run(["git", "show", "HEAD:" + rel],
                          capture_output=True, cwd=ROOT).stdout


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
    print("APPENDED %-40s +%d bytes  (head+%d)"
          % (path.rsplit("/", 1)[-1], n, len(after) - len(head)))
