# -*- coding: utf-8 -*-
"""R17_COMMON_2_9 / verify.py — 可复跑校验（前缀哈希 + CR 计数 + 行数 + 尾部一致）。

从本目录的 R14_COMMON.before_2.9.md 取 before 前缀，校验目标 R14_COMMON.md：
  1) after 长度 == before 长度 + 追加长度（此处追加长度由常量给出）
  2) sha256(after[:before_len]) == sha256(before)   —— 旧字节前缀未变
  3) CR 计数 == 1081（既有 CR 数；追加只用 LF）
  4) 追加段 CR == 0（只含 LF）
  5) 行数（LF split）自洽
运行： python verify.py
"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.abspath(os.path.join(HERE, ".."))
TARGET = os.path.join(R14, "R14_COMMON.md")
BEFORE = os.path.join(HERE, "R14_COMMON.before_2.9.md")

BEFORE_LEN = 236380
BEFORE_SHA = "E7253E44CBEFC446FE8C86519406012FADF10359B212AF5F13BD87EA6325CC5D"
AFTER_LEN  = 241825
AFTER_SHA  = "5543CD991E2FEF28AB3EB12A15E2D4414A196E7A343067A854C011003F0DB500"
EXPECT_CR  = 1081
APPENDED_LEN = 5445

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def cr(b): return b.count(b"\r")
def lf(b): return b.count(b"\n")

def main():
    ok = True
    def chk(name, cond):
        nonlocal ok
        print(("PASS" if cond else "FAIL"), name)
        ok = ok and cond

    before = open(BEFORE, "rb").read()
    after  = open(TARGET, "rb").read()

    chk("before len == %d" % BEFORE_LEN, len(before) == BEFORE_LEN)
    chk("before sha == %s" % BEFORE_SHA, sha(before) == BEFORE_SHA)
    chk("after len == %d" % AFTER_LEN, len(after) == AFTER_LEN)
    chk("after len == before + appended(%d)" % APPENDED_LEN,
        len(after) == len(before) + APPENDED_LEN)
    chk("prefix sha256 unchanged (append-only)",
        len(after) >= BEFORE_LEN and sha(after[:BEFORE_LEN]) == sha(before))
    chk("prefix == recorded BEFORE_SHA", sha(after[:BEFORE_LEN]) == BEFORE_SHA)
    chk("CR count == %d (unchanged)" % EXPECT_CR, cr(after) == EXPECT_CR)
    ap = after[BEFORE_LEN:] if len(after) >= BEFORE_LEN else b""
    chk("appended CR == 0 (LF-only)", cr(ap) == 0)
    chk("after sha == %s" % AFTER_SHA, sha(after) == AFTER_SHA)
    b_lines = before.count(b"\n") + (0 if before.endswith(b"\n") else 1)
    a_lines = after.count(b"\n")  + (0 if after.endswith(b"\n")  else 1)
    print("lines: before=%d after=%d delta=%d" % (b_lines, a_lines, a_lines - b_lines))
    print("CR: before=%d after=%d ; bytes: before=%d after=%d" %
          (cr(before), cr(after), len(before), len(after)))
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
