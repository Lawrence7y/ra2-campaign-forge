# -*- coding: utf-8 -*-
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
DRAFT  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_drafts\§1053.md"
def sha(b): return hashlib.sha256(b).hexdigest().upper()
before = open(LEDGER,"rb").read(); draft = open(DRAFT,"rb").read()
n0 = len(before); h0 = sha(before)
assert h0 == "06A2BE4BCDF045D811D997577FE08B9BAC220BBB845086EFF6FC12318128029F", "台账 sha 不符"
assert not draft.startswith(b"\xef\xbb\xbf") and draft.count(b"\r\n")==0 and draft.endswith(b"\n")
assert draft.split(b"\n")[0].startswith("## §1053".encode("utf-8"))
payload = b"\n" + draft
after = before + payload
assert sha(after[:n0]) == h0, "前缀哈希不等"
open(LEDGER,"wb").write(after)
rr = open(LEDGER,"rb").read()
assert len(rr)==n0+len(payload) and sha(rr[:n0])==h0 and rr[-len(payload):]==payload
print("=== §1053 追加台账 ===")
print("追加前 bytes=%d lines=%d CRLF=%d sha=%s" % (n0, before.count(b"\n"), before.count(b"\r\n"), h0))
print("草稿    bytes=%d LF=%d" % (len(draft), draft.count(b"\n")))
print("追加段  bytes=%d" % len(payload))
print("追加后  bytes=%d (+%d) CRLF=%d(未增)" % (len(rr), len(payload), rr.count(b"\r\n")))
print("前缀哈希验证: %s" % ("PASS" if sha(rr[:n0])==h0 else "FAIL"))
print("读盘复验: PASS   追加段复验: PASS")
print("追加后整文件 sha=%s" % sha(rr))
