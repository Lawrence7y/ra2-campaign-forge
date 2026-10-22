"""把 S370_SECTION.md 追加到台账（纯追加，零覆盖）。"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEDGER = ROOT / "lead" / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
SECTION = ROOT / "lead/goal2_rc4_trigger_20261022/S370_SECTION.md"


def main() -> int:
    raw = LEDGER.read_bytes()
    add = SECTION.read_bytes()

    if "## §370".encode("utf-8") in raw:
        print("REFUSE: §370 已存在")
        return 1

    if not add.endswith(b"\n"):
        add += b"\n"
    if not raw.endswith(b"\n"):
        add = b"\n" + add

    new = raw + add
    if new != raw + add or new[:len(raw)] != raw:
        print("REFUSE: 追加结果异常")
        return 1
    if new.count(b"\r\n") != raw.count(b"\r\n"):
        print("REFUSE: CRLF 计数变化")
        return 1

    LEDGER.write_bytes(new)
    print("APPENDED  %d -> %d bytes  (+%d)"
          % (len(raw), len(new), len(new) - len(raw)))
    print("sha256 %s -> %s"
          % (hashlib.sha256(raw).hexdigest()[:16],
             hashlib.sha256(new).hexdigest()[:16]))
    print("CRLF %d (unchanged)" % new.count(b"\r\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
