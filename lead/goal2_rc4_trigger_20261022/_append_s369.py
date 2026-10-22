"""把 S369_SECTION.md 追加到台账（纯追加，零覆盖）。

★ 纪律：只追加；先断言 `new == raw + add`（逐字节），再断言 CRLF 计数不变，
  最后断言 `## §369` 标题此前不存在（防重复追加）。
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEDGER = ROOT / "lead" / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
SECTION = ROOT / "lead/goal2_rc4_trigger_20261022/S369_SECTION.md"


def main() -> int:
    raw = LEDGER.read_bytes()
    add = SECTION.read_bytes()

    if b"## \xc2\xa7369" in raw or "## §369".encode("utf-8") in raw:
        print("REFUSE: §369 已存在，不重复追加")
        return 1

    if not add.endswith(b"\n"):
        add += b"\n"
    if not raw.endswith(b"\n"):
        add = b"\n" + add

    new = raw + add
    if new != raw + add:
        print("REFUSE: 追加结果非 raw+add")
        return 1
    if new[:len(raw)] != raw:
        print("REFUSE: 前缀被改动")
        return 1

    crlf_before = raw.count(b"\r\n")
    crlf_after = new.count(b"\r\n")
    if crlf_before != crlf_after:
        print("REFUSE: CRLF 计数变化 %d -> %d" % (crlf_before, crlf_after))
        return 1

    LEDGER.write_bytes(new)
    print("APPENDED  %d -> %d bytes  (+%d)"
          % (len(raw), len(new), len(new) - len(raw)))
    print("sha256 %s -> %s"
          % (hashlib.sha256(raw).hexdigest()[:16],
             hashlib.sha256(new).hexdigest()[:16]))
    print("CRLF %d (unchanged)" % crlf_after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
