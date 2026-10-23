"""把 S397_SECTION.md 追加到台账（纯追加，零覆盖）。

★ 纪律同 _append_s369.py：断言前缀不变、CRLF 计数不变、标题此前不存在。
★ 本节标题用 `# §397`（与 §395/§396 的写法一致），故查 `# §397`。
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEDGER = ROOT / "lead" / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
SECTION = ROOT / "lead" / "goal1_harness6_20261022" / "S397_SECTION.md"


def main() -> int:
    raw = LEDGER.read_bytes()
    add = SECTION.read_bytes()

    if "§397".encode("utf-8") in raw:
        print("REFUSE: §397 已存在，不重复追加")
        return 1

    if not add.endswith(b"\n"):
        add += b"\n"
    sep = b"" if raw.endswith(b"\n") else b"\n"

    new = raw + sep + add
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
