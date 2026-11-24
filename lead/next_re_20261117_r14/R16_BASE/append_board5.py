# -*- coding: utf-8 -*-
"""安全追加看板：读全文→拼→断言→一次性写→读回复验。（事故后固定流程）"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
BOARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\STATUS_BOARD.md"
SEG = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_BASE\BOARD_R16_SEG5.md"
def sha(b): return hashlib.sha256(b).hexdigest().upper()

board_before = open(BOARD, "rb").read()
seg = open(SEG, "rb").read()
assert not seg.startswith(b"\xef\xbb\xbf") and seg.count(b"\r\n") == 0
n0 = len(board_before)
payload = b"\n" + seg
full = board_before + payload
assert len(full) == n0 + len(payload) and len(full) > 40_000, "长度异常"
open(BOARD, "wb").write(full)
rr = open(BOARD, "rb").read()
assert len(rr) == len(full) and sha(rr[:n0]) == sha(board_before) and rr[-len(payload):] == payload
lines_new = rr.count(b"\n")
print("board bytes=%d -> %d (+%d)" % (n0, len(rr), len(payload)))
print("board lines=%d" % lines_new)
print("前缀 PASS / 追加段 PASS / 读回 PASS")
