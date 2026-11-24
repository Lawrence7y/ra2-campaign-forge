# -*- coding: utf-8 -*-
"""R73 追写：把「我新增纪律 32/33 造成门禁 C1/C2 回归、及随后两次修错」补进四件套。

为什么必须追写：四件套里现在写着「门禁 RED（5 FAIL）」，但中间真实发生过 **7 FAIL**，
成因是我把纪律条数从 28 改成 30 而没同步 DISC_RECHECK.tsv。若不记，下一轮读四件套的人
会以为门禁一直是 5 FAIL —— 那是把一次自伤抹掉。

追写方式：**不改已写入的段**，只在各件末尾追加一个短的「补记」块（纯追加，前缀断言）。
"""
import io, os, sys, hashlib, time

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
LEAD = os.path.dirname(R14)
BASE = os.path.join(R14, "R17_LEAD_BASELINE")
COMMON = os.path.join(R14, "R14_COMMON.md")
LEDGER = os.path.join(LEAD, "GOAL_THREE_TARGETS_20261018.md")
LOCK = os.path.join(LEAD, "LEAD_LOCK")
BOARD = os.path.join(R14, "STATUS_BOARD.md")

EXP = {
    COMMON: (587697, 1081),
    LEDGER: (4702123, 337),
    LOCK: (386819, 137),
    BOARD: (55776, 0),
}
FAILS = []


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


def need(n, c, d=""):
    ck(n, c, d)
    if not c:
        P("")
        P("[ABORT] 硬闸：%s —— 不写 live" % n)
        sys.exit(3)


def sha(b):
    return hashlib.sha256(b).hexdigest()


raw = {p: io.open(p, "rb").read() for p in EXP}
P("=== S0 · 旧状态 ===")
for p, (n, cr) in EXP.items():
    b = raw[p]
    P("  [before] %-34s %8d B CR=%-5d sha=%s"
      % (os.path.basename(p), len(b), b.count(b"\r"), sha(b)[:16]))
    need("旧 %s 字节数" % os.path.basename(p), len(b) == n, "%d vs %d" % (len(b), n))
    need("旧 %s CR" % os.path.basename(p), b.count(b"\r") == cr, str(b.count(b"\r")))
need("前置守卫：本轮补记尚未写入",
     "R73 补记" not in raw[COMMON].decode("utf-8"))

COMMON_ADD = """
### 七 · 🔴 补记：我自己引入过一次门禁回归（5 FAIL → 7 FAIL → 5 FAIL）

本章程新立纪律 32/33 后，`DISC_RECHECK.tsv` 仍是 28 行，而门禁按定义数校验 ⇒ **C1/C2 立即 FAIL**，门禁从 5 FAIL 变 **7 FAIL**。这是**我本轮改动造成的自伤**，不是既有缺陷。
补两行时我又错了三次（全部被我自己的硬闸挡住、未污染 live 之外的东西）：

1. 判据串写成 `零信息格（与 R72 的 W_only 同族`，产物里跨引号边界 ⇒ **命中 0 次**，硬闸拦下；
2. 改用含 `**` 与 `⇒` 的整句，而门禁 C7 用 `re.findall` 编译 ⇒ **`re.error: multiple repeat`**，硬闸拦下；
3. `r"def norm\\(t\\)"` 经写入层后**反斜杠被吃掉**，落盘成 `grep=def norm(t)`（命中 0）⇒ C7 当场 FAIL。已从备份回滚（留 `INCIDENT.r73_bad_grep_escape_*` 取证），并**新增一道往返解析硬闸**：把整行拼进新文本再解析回来，断言第 6 列逐字等于预期判据串且真能命中。补这道闸之后一次写入成功。

⇒ 纪律新条（本条即纪律 32 的又一实证）：**改「定义条数」必须同步改「登记表条数」，否则改的是两个不变量中的一个**。以及：**转义层次必须以「往返解析」验证，不能以「我写的时候是对的」验证**。
本条补记后，`DISC_RECHECK.tsv` = 30 行 / 10,028 B / CR 0，门禁回到 **5 FAIL（C1/C2/C7 全过：C7 30/30、C8 30/30、C10 ok）**。
"""

LEDGER_ADD = """
**九 · 🔴 补记（本轮自伤，必须记）**：新立纪律 32/33 后 `DISC_RECHECK.tsv` 仍 28 行 ⇒ 门禁 **C1/C2 立即 FAIL，5 FAIL 变 7 FAIL**，成因是我把纪律条数从 28 改成 30 却没同步登记表。补两行时又连错三次，全被硬闸拦下：①判据串跨引号边界 ⇒ 产物里命中 0；②改用含 `**`/`⇒` 的整句 ⇒ 门禁 C7 用 `re.findall` 编译时报 `multiple repeat`；③`r"def norm\\\\(t\\\\)"` 经写入层后反斜杠被吃掉、落盘成 `grep=def norm(t)`（C7 当场 FAIL），已从备份回滚（`INCIDENT.r73_bad_grep_escape_*`）并**新增往返解析硬闸**（整行拼进新文本再解析回来，断言第 6 列逐字且真能命中），加闸后一次写入成功。现 `DISC_RECHECK.tsv` = 30 行 / 10,028 B / CR 0，门禁回到 **5 FAIL**（C1/C2/C7 全过）。教训两条：**改定义条数必须同步改登记表**；**转义层次以「往返解析」验证，不以「写的时候是对的」验证**。
"""

LOCK_ADD = """
DA10. 🔴 **补记：我本轮自己造成过一次门禁回归（5 FAIL → 7 FAIL → 5 FAIL）**。新立纪律 32/33 后 `DISC_RECHECK.tsv` 仍 28 行 ⇒ C1/C2 立即 FAIL。补两行时又连错三次（判据串跨引号边界命中 0；含 `**`/`⇒` 的串被 `re.findall` 判 `multiple repeat`；`r"def norm\\\\(t\\\\)"` 经写入层反斜杠被吃掉致 C7 FAIL）—— 三次全被硬闸拦下，第三次已从备份回滚并留 `INCIDENT.r73_bad_grep_escape_*`。**修法加了一道往返解析硬闸**（整行拼进新文本再解析回来，断言第 6 列逐字且真能命中），加闸后一次成功。现 `DISC_RECHECK.tsv` = 30 行 / 10,028 B / CR 0；门禁 **5 FAIL**（C1/C2/C7 全过：C7 30/30、C8 30/30、C10 ok）。⇒ 两条教训：**改定义条数必须同步改登记表**；**转义层次以往返解析验证，不以「写的时候是对的」验证**。
"""

BOARD_ADD = """- 🔴🔴 **补记：我本轮自己造成过一次门禁回归（5 FAIL → 7 FAIL → 5 FAIL）** —— 新立纪律 32/33 后 `DISC_RECHECK.tsv` 仍 28 行 ⇒ **C1/C2 立即 FAIL**。补两行时又连错三次，全部被硬闸拦下：①判据串跨引号边界 ⇒ 产物命中 0；②含 `**`/`⇒` 的串被门禁 C7 的 `re.findall` 判 `multiple repeat`；③`r"def norm\\(t\\)"` 经写入层**反斜杠被吃掉**、落盘成 `grep=def norm(t)` ⇒ C7 当场 FAIL（**已从备份回滚**，留 `INCIDENT.r73_bad_grep_escape_*` 取证）。**修法：新增一道往返解析硬闸**（把整行拼进新文本再解析回来，断言第 6 列逐字 == 预期判据串且真能命中），加闸后一次写入成功
- ✅ **收口数值**：`DISC_RECHECK.tsv` **30 行 / 10,028 B / CR 0**；门禁 **5 FAIL**（C1/C2/C7 全过：**C7 30/30、C8 30/30、C10 ok**）⇒ 本轮把门禁从「跑不起来」变成「跑得起来且条数自洽」，**判据与窗口表一字未改**
- 🔴 **两条教训成文**：**改「定义条数」必须同步改「登记表条数」**（否则改的是两个不变量中的一个）；**转义层次必须以「往返解析」验证，不能以「我写的时候是对的」验证**
"""

P("")
P("=== S1 · 组装与写前断言 ===")
new = {}
new[COMMON] = raw[COMMON].decode("utf-8") + COMMON_ADD
new[LEDGER] = raw[LEDGER].decode("utf-8") + LEDGER_ADD
new[LOCK] = raw[LOCK].decode("utf-8") + LOCK_ADD
new[BOARD] = raw[BOARD].decode("utf-8") + BOARD_ADD
for p, txt in new.items():
    need("纯追加 · %s 旧内容是前缀" % os.path.basename(p),
         txt.encode("utf-8").startswith(raw[p]))
need("新 R14_COMMON CR 仍 1081", new[COMMON].count("\r") == 1081, str(new[COMMON].count("\r")))
need("新台账 CR 仍 337", new[LEDGER].count("\r") == 337, str(new[LEDGER].count("\r")))
need("新 LEAD_LOCK CR 仍 137", new[LOCK].count("\r") == 137, str(new[LOCK].count("\r")))
need("新看板 CR 仍 0", new[BOARD].count("\r") == 0, str(new[BOARD].count("\r")))
nb = new[BOARD].split("\n")
P("  新看板行数 = %d" % len(nb))
need("新看板行数 <= 300", len(nb) <= 300, str(len(nb)))
need("新看板行数 <= 260", len(nb) <= 260, str(len(nb)))
need("追加块无不可见字符",
     not any(ch in "".join(new.values()) for ch in ("​", "﻿")))

P("")
P("=== S2 · 备份 / 写入 / 回读 ===")
ts = time.strftime("%Y%m%d_%H%M%S")
for p in (COMMON, LEDGER, LOCK, BOARD):
    bp = os.path.join(BASE, "SUPERSEDED.before_r73_addendum_%s_%s.md"
                      % (os.path.basename(p), ts))
    with open(bp, "xb") as f:
        f.write(raw[p])
    need("备份 %s sha 一致" % os.path.basename(bp),
         sha(io.open(bp, "rb").read()) == sha(raw[p]))
P("  [write] 一次性写入")
for p in (COMMON, LEDGER, LOCK, BOARD):
    with open(p, "wb") as f:
        f.write(new[p].encode("utf-8"))
for p in (COMMON, LEDGER, LOCK, BOARD):
    got = io.open(p, "rb").read()
    P("  [after] %-34s %8d B CR=%-5d sha=%s"
      % (os.path.basename(p), len(got), got.count(b"\r"), sha(got)[:16]))
    need("回读 %s 字节 == 预期" % os.path.basename(p), got == new[p].encode("utf-8"))
    need("回读 %s 旧内容是前缀" % os.path.basename(p), got.startswith(raw[p]))

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
