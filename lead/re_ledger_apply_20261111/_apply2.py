
# -*- coding: utf-8 -*-
import os, hashlib, sys
ROOT = r"D:\Project\ra2-campaign-forge"
TARGET = os.path.join(ROOT, r"lead\GOAL_THREE_TARGETS_20261018.md")
OUT = os.path.join(ROOT, r"lead\re_ledger_apply_20261111")
START = "## \u2193\u2193\u2193 \u8349\u6848\u6b63\u6587\uff08\u4ece\u8fd9\u91cc\u5f00\u59cb\u6574\u6bb5\u590d\u5236\uff09\u2193\u2193\u2193"
END = "## \u2191\u2191\u2191 \u8349\u6848\u6b63\u6587\u7ed3\u675f \u2191\u2191\u2191"
ENTRIES = [
 ("\u00a7605", r"lead\ledger_appendix_20261108\_la_draft1_n9_p6_erratum.md", 4735),
 ("\u00a7606", r"lead\ledger_appendix_20261108\_la_draft2_o4_necessity.md", 4097),
 ("\u00a7607", r"lead\ledger_appendix_20261108\_la_draft3_s604_gapdiff.md", 4894),
 ("\u00a7608", r"lead\ledger_appendix_20261108\_la_draft4_yi_supersede_jia.md", 6318),
 ("\u00a7609", r"lead\s604_verdict_entry_20261109\_ve_DRAFT_S609.md", 8388),
]
def sha(b): return hashlib.sha256(b).hexdigest()

before = open(TARGET, "rb").read()
b_len, b_sha = len(before), sha(before)
print("BEFORE size=%d sha=%s" % (b_len, b_sha))

bodies = []
for sec, rel, exp in ENTRIES:
    src = open(os.path.join(ROOT, rel), "r", encoding="utf-8", newline="").read()
    i = src.index(START); j = src.index(END)
    body = src[i+len(START):j]
    body = body.lstrip("\r\n")
    b = body.encode("utf-8")
    print("%s extract=%dB expect=%dB %s sha=%s" % (sec, len(b), exp, "LEN_OK" if len(b)==exp else "LEN_MISMATCH", sha(b)[:16]))
    assert len(b) == exp, sec
    bodies.append((sec, body))

# \u00a7609 \u5fc5\u987b\u5e26 unconfirmed \u6807\u8bb0\uff08\u5408\u8ba2\u672c \u00a75 \u8981\u6c42\uff1apartial -> unconfirmed\uff09
for k, (sec, body) in enumerate(bodies):
    if sec == "\u00a7609" and "unconfirmed" not in body:
        first_nl = body.index("\n")
        title = body[:first_nl]
        bodies[k] = (sec, title + "\uff08**unconfirmed**\uff1a\u590d\u6838 verdict=partial\uff0c\u7167\u5408\u8ba2\u672c \u00a75 \u8981\u6c42\u6807\u8bb0\uff09" + body[first_nl:])
        print("S609: unconfirmed marker INSERTED by dispatcher")

payload = ("\n\n" + "".join(b for _, b in bodies)).encode("utf-8")
print("PAYLOAD bytes=%d sha=%s" % (len(payload), sha(payload)[:16]))

with open(TARGET, "ab") as f:
    f.write(payload)

after = open(TARGET, "rb").read()
print("AFTER size=%d sha=%s" % (len(after), sha(after)))

ok = True
def chk(name, cond, extra=""):
    global ok
    print("%s: %s %s" % (name, "PASS" if cond else "FAIL", extra))
    if not cond: ok = False

chk("4a prefix-unchanged", sha(after[:b_len]) == b_sha, sha(after[:b_len])[:16])
txt = after.decode("utf-8")
for sec, body in bodies:
    n = txt.count("\n" + sec + " ")
    chk("4b %s occurs once" % sec, n == 1, "count=%d" % n)
chk("4c size", len(after) == b_len + len(payload), "%d = %d + %d" % (len(after), b_len, len(payload)))
chk("4d utf8-lines", len(txt.splitlines()) == len(before.decode("utf-8").splitlines()) + payload.decode("utf-8").count("\n"))
print("EXIT=%d" % (0 if ok else 1))
