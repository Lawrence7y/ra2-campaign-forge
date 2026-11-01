#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PENDING_DECISIONS.md 裁决执行（协议第 1/3 条）：
删 D-08、D-09（本线来源，已裁决）；D-07/D-06 他线来源不动（归来源会话更新）；
SYNCPOINT 信标注释保留原字节。断言先行，失败不写。"""
import io, os

PD = "lead/PENDING_DECISIONS.md"
data = io.open(PD, "rb").read()
assert data.count(b"\r\n") == 0, "CRLF appeared — stop"

# 前置断言
assert data.count("## D-06".encode()) == 1
assert data.count("## D-07".encode()) == 1
assert data.count("## D-08".encode()) == 1
assert data.count("## D-09".encode()) == 1
assert data.count("SYNCPOINT 2026-10-24 晚".encode()) == 1
assert data.count("更新 8（2026-10-25，D-09 来源会话".encode()) == 1

i8 = data.find("## D-08".encode())
i9 = data.find("## D-09".encode())
iC = data.find("<!-- SYNCPOINT 2026-10-24 晚".encode())
assert i8 < iC < i9, "boundary order unexpected"

# 切块：保头（..i8）+ 信标段（iC..i9）+ 删 D-09（i9..EOF）
head = data[:i8]
mid = data[iC:i9]          # 信标注释 + 其后空行
tail_after_d9 = b""        # D-09 到 EOF
after = head + mid.rstrip(b"\n") + b"\n"

# 后置断言
assert after.count("## D-08".encode()) == 0
assert after.count("## D-09".encode()) == 0
assert after.count("更新 8（2026-10-25，D-09 来源会话".encode()) == 0
assert after.count("## D-06".encode()) == 1
assert after.count("## D-07".encode()) == 1
assert after.count("SYNCPOINT 2026-10-24 晚".encode()) == 1
assert after.count(b"\r\n") == 0
assert after.startswith(data[:i8])

tmp = PD + ".tmprulerun"
io.open(tmp, "wb").write(after)
os.replace(tmp, PD)
back = io.open(PD, "rb").read()
assert back == after
print("OK: D-08/D-09 removed, D-06/D-07 untouched, beacon kept; %d -> %d bytes" % (len(data), len(back)))
