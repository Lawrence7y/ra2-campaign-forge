# -*- coding: utf-8 -*-
"""前缀逐字节校验：新 R14_COMMON.md 的前 N 字节必须与改前文件逐字节相同。
N = 改前字节数（180772）。三重校验：
  (1) 旧长度前缀的 sha256 == 改前文件 sha256
  (2) 旧长度前缀与备份文件（改前原样）逐字节比较，首个差异偏移必须为 None
  (3) 追加段（[N, N+delta)）的 sha256 == 待追加块的 sha256（证明只是尾部新增）
"""
import hashlib, os, sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
NEW = os.path.join(ROOT, "R14_COMMON.md")
BAK = os.path.join(ROOT, "_hygiene", "R14_COMMON.COMMON-REFRESH-2.bak")
BLK = os.path.join(ROOT, "COMMON_REFRESH2", "work", "append_block.md")

new = open(NEW, "rb").read()
bak = open(BAK, "rb").read()
blk = open(BLK, "rb").read()
N = len(bak)

print("改前（备份）字节数      = %d" % N)
print("改后字节数              = %d" % len(new))
print("增量                    = %d（待追加块 %d）" % (len(new) - N, len(blk)))
print()

prefix = new[:N]
h_pre = hashlib.sha256(prefix).hexdigest().upper()
h_bak = hashlib.sha256(bak).hexdigest().upper()
print("(1) 旧长度前缀 sha256    = %s" % h_pre)
print("    改前文件   sha256    = %s" % h_bak)
print("    判定                 = %s" % ("一致 ✅" if h_pre == h_bak else "不一致 ❌"))
print()

first_diff = None
for i in range(N):
    if prefix[i] != bak[i]:
        first_diff = i
        break
print("(2) 前缀 × 备份逐字节比较：%s（首个差异偏移 = %s）"
      % ("完全相同 ✅" if first_diff is None else "存在差异 ❌", first_diff))
print()

tail = new[N:]
h_tail = hashlib.sha256(tail).hexdigest().upper()
h_blk = hashlib.sha256(blk).hexdigest().upper()
print("(3) 追加段 sha256        = %s" % h_tail)
print("    待追加块 sha256      = %s" % h_blk)
print("    判定                 = %s" % ("一致 ✅" if h_tail == h_blk else "不一致 ❌"))
print()
print("改后全文 sha256         = %s" % hashlib.sha256(new).hexdigest().upper())
print("结论：%s" % ("纯尾部追加，旧 180772 字节前缀逐字节未变（前缀校验通过）"
                if (h_pre == h_bak and first_diff is None and h_tail == h_blk)
                else "校验失败，需回滚"))
