"""把四个【更正】段插入台账对应节的末尾（不删原文，只在节尾追加）。

★ 纪律
  - 只在指定节的**末尾**（下一个 `## §NNN` 标题之前）插入；
  - 原文一个字节都不删：插入后断言 `new` 去掉插入内容后 == `raw`；
  - CRLF 计数不变；
  - 每个更正段只插一次（已存在则拒）。
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEDGER = ROOT / "lead" / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
CARD = ROOT / "lead" / "goal2_rc4_trigger_20261022"

# (锚点节号, 更正件)
JOBS = [
    ("347", CARD / "CORR_352.md"),
    ("349", CARD / "CORR_349.md"),
    ("356", CARD / "CORR_356.md"),
    ("359", CARD / "CORR_359.md"),
]


def main() -> int:
    raw = LEDGER.read_bytes()
    text = raw.decode("utf-8")

    # 先全部预检，任一不过就整体不动
    plan = []
    for sec, cf in JOBS:
        if not cf.is_file():
            print("REFUSE: 缺更正件", cf)
            return 1
        body = cf.read_text(encoding="utf-8")
        marker = body.splitlines()[0].strip()
        if marker in text:
            print("SKIP: §%s 已含该更正段（%s）" % (sec, marker[:40]))
            continue
        head = "## §%s\u3000" % sec
        idx = text.find(head)
        if idx < 0:
            print("REFUSE: 找不到 §%s 标题" % sec)
            return 1
        # 找下一个节标题（## §）
        nxt = text.find("\n## §", idx + len(head))
        if nxt < 0:
            print("REFUSE: §%s 之后没有下一节，无法定位节尾" % sec)
            return 1
        plan.append((sec, nxt, body))

    if not plan:
        print("无待插入项（全部已存在）")
        return 0

    # 从后往前插，避免偏移失效
    plan.sort(key=lambda x: x[1], reverse=True)
    new_text = text
    for sec, pos, body in plan:
        if not body.endswith("\n"):
            body += "\n"
        insert = "\n" + body
        new_text = new_text[:pos] + insert + new_text[pos:]
        print("INSERT §%s at offset %d (+%d bytes)"
              % (sec, pos, len(insert.encode("utf-8"))))

    new = new_text.encode("utf-8")

    # ★ 反向校验：把插入内容全部移除后必须逐字节等于原文
    stripped = new_text
    for sec, pos, body in plan:
        if not body.endswith("\n"):
            body += "\n"
        insert = "\n" + body
        if insert not in stripped:
            print("REFUSE: 反查不到插入内容 §%s" % sec)
            return 1
        stripped = stripped.replace(insert, "", 1)
    if stripped.encode("utf-8") != raw:
        print("REFUSE: 反向重建 != 原文（有字节被改动）")
        return 1

    if new.count(b"\r\n") != raw.count(b"\r\n"):
        print("REFUSE: CRLF 计数变化")
        return 1

    LEDGER.write_bytes(new)
    print()
    print("OK  %d -> %d bytes (+%d)"
          % (len(raw), len(new), len(new) - len(raw)))
    print("sha256 %s -> %s"
          % (hashlib.sha256(raw).hexdigest()[:16],
             hashlib.sha256(new).hexdigest()[:16]))
    print("反向重建 == 原文：PASS（零删除）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
