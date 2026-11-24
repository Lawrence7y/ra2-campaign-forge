# -*- coding: utf-8 -*-
"""COMMON-FIX · 追加执行 + 前后指纹（append-only；前缀逐字节校验）。
运行：python -I append_and_hash.py
"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Project\ra2-campaign-forge")
COMMON = ROOT / r"lead\next_re_20261117_r14\R14_COMMON.md"
BAK = ROOT / r"lead\next_re_20261117_r14\_hygiene\R14_COMMON.COMMON-FIX.bak"
BLOCK = Path(__file__).with_name("append_block.md")
HASHOUT = ROOT / r"lead\next_re_20261117_r14\COMMON_FIX\HASH.txt"

EXPECT_SHA = "669F9137CC9B24168052DF653728405E7CCA260A9094FC35758AA63AE176B715"

data = COMMON.read_bytes()
sha_before = hashlib.sha256(data).hexdigest().upper()
if sha_before != EXPECT_SHA:
    raise SystemExit("ABORT: 改前 SHA 与记录不符：%s（可能并发写入，停止追加）" % sha_before)
print("before bytes =", len(data))
print("before sha256 =", sha_before)

# 1) 备份（字节精确）
BAK.write_bytes(data)
bak_sha = hashlib.sha256(BAK.read_bytes()).hexdigest().upper()
print("backup =", BAK)
print("backup sha256 =", bak_sha, "(== before:", bak_sha == sha_before, ")")

# 2) 追加（前导分隔：保证与既有末行之间恰一个空行）
block = BLOCK.read_bytes()
if data.endswith(b"\n\n"):
    sep = b""
elif data.endswith(b"\n"):
    sep = b"\n"
else:
    sep = b"\n\n"
new = data + sep + block
COMMON.write_bytes(new)

# 3) 校验：前缀逐字节一致（旧行 0 变更）
after = COMMON.read_bytes()
prefix_ok = after[: len(data)] == data
sha_after = hashlib.sha256(after).hexdigest().upper()
print("after bytes =", len(after))
print("after sha256 =", sha_after)
print("appended bytes =", len(after) - len(data))
print("prefix byte-identical =", prefix_ok)
print("lines before/after (splitlines) =", len(data.splitlines()), "/", len(after.splitlines()))

# 4) HASH.txt
hash_txt = f"""# COMMON-FIX · R14_COMMON.md 追加前后指纹（铁律：追加前/后各记一次）
file: lead\\next_re_20261117_r14\\R14_COMMON.md
recorded_by: COMMON-FIX (agent-127, 本轮 R14_COMMON 唯一写者)
recorded_at: 2026-11-20 Asia/Shanghai
tool: python -I COMMON_FIX\\work\\append_and_hash.py

[BEFORE]
bytes  = {len(data)}
sha256 = {sha_before}
lines(splitlines) = {len(data.splitlines())}
backup = lead\\next_re_20261117_r14\\_hygiene\\R14_COMMON.COMMON-FIX.bak
backup_bytes = {len(data)}
backup_sha256 = {bak_sha}  (== BEFORE sha256: {bak_sha == sha_before})

[AFTER]
bytes  = {len(after)}
sha256 = {sha_after}
lines(splitlines) = {len(after.splitlines())}
appended_bytes = {len(after) - len(data)}
appended_source = COMMON_FIX\\work\\append_block.md (§11.1–§11.4 + 本轮刷新记录 COMMON-FIX)

[APPEND-ONLY 自检]
prefix_byte_identical = {prefix_ok}  (after[:{len(data)}] == before 逐字节一致 ⇒ 既有行 0 变更)
separator = {'none (file 已以空行结尾)' if sep == b'' else 'one blank line before ---'}
"""
HASHOUT.write_text(hash_txt, encoding="utf-8")
print("[saved]", HASHOUT)
