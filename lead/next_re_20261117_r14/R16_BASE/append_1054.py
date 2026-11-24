# -*- coding: utf-8 -*-
"""追加 §1054 入台账。安全做法：先读全文→算新全文→断言长度与哈希→一次性写盘→读回复验。
（上一轮事故教训：不在脚本里复用单字母变量名，不做增量写。）"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
DRAFT  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_drafts\§1054.md"
EXPECT_SHA = "9D37C44BFF46D3BD9C3C6ADD52A3B7E53E780F95385AA81A2FE6DFB12146597A"

def sha(b): return hashlib.sha256(b).hexdigest().upper()

ledger_before = open(LEDGER, "rb").read()
draft = open(DRAFT, "rb").read()

assert sha(ledger_before) == EXPECT_SHA, "台账 sha 与预期不符，中止"
assert not draft.startswith(b"\xef\xbb\xbf"), "草稿带 BOM"
assert draft.count(b"\r\n") == 0, "草稿含 CRLF"
assert draft.endswith(b"\n"), "草稿不以 LF 结尾"
assert draft.split(b"\n")[0].startswith("## §1054".encode("utf-8")), "草稿首行不是 §1054 标题"

n_before = len(ledger_before)
payload = b"\n" + draft
full_after = ledger_before + payload
n_after = len(full_after)

# 断言长度合理：应恰好增加 payload 长度，且大于原长度
assert n_after == n_before + len(payload), "长度算术不符"
assert n_after > n_before > 4_000_000, "长度异常，中止"

# 一次性写盘
with open(LEDGER, "wb") as f:
    f.write(full_after)

# 读回复验
reread = open(LEDGER, "rb").read()
assert len(reread) == n_after, "读回长度不符"
assert sha(reread[:n_before]) == EXPECT_SHA, "前缀哈希不等"
assert reread[-len(payload):] == payload, "追加段不一致"
assert reread.count(b"\r\n") == ledger_before.count(b"\r\n"), "CRLF 计数变了"

print("=== §1054 追加台账 ===")
print("追加前 bytes=%d lines=%d CRLF=%d" % (n_before, ledger_before.count(b"\n"), ledger_before.count(b"\r\n")))
print("草稿    bytes=%d LF=%d" % (len(draft), draft.count(b"\n")))
print("追加后 bytes=%d (+%d) lines=%d CRLF=%d(未增)" % (n_after, len(payload), reread.count(b"\n"), reread.count(b"\r\n")))
print("前缀哈希验证: PASS")
print("读盘复验: PASS   追加段复验: PASS   CRLF 未增: PASS")
print("新台账 sha=%s" % sha(reread))
