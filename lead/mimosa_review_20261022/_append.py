# -*- coding: utf-8 -*-
"""把 S364_SECTION.md 追加到主账本。纯追加，零删除。

★ 本脚本只做一件事：读同目录下的 SECTION 文件，append 到 LEDGER。
  不做任何路径拼接、不接受命令行参数、不执行任何文本内容。
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE.parent / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
SECTION = HERE / "S364_SECTION.md"


def main():
    if not LEDGER.is_file():
        print("FAIL: ledger missing")
        return 2
    if not SECTION.is_file():
        print("FAIL: section missing")
        return 2

    raw = LEDGER.read_bytes()
    add = SECTION.read_bytes().replace(b"\r\n", b"\n")
    print("ledger before :", len(raw), "bytes; CRLF pairs:", raw.count(b"\r\n"))
    print("section bytes :", len(add))

    with open(LEDGER, "ab") as f:
        f.write(add)

    new = LEDGER.read_bytes()
    print("ledger after  :", len(new), "bytes; CRLF pairs:", new.count(b"\r\n"))

    ok = True
    if not new.startswith(raw):
        print("FAIL: prefix changed")
        ok = False
    if new != raw + add:
        print("FAIL: not a pure append")
        ok = False
    if new.count(b"\r\n") != raw.count(b"\r\n"):
        print("FAIL: CRLF introduced")
        ok = False
    if b"\xef\xbb\xbf" in add[:3]:
        print("FAIL: BOM in section")
        ok = False

    print("sha256:", hashlib.sha256(new).hexdigest())
    print("RESULT:", "ALL PASS (pure append, zero deletions, zero CRLF)" if ok else "HAS FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
