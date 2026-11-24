# -*- coding: utf-8 -*-
"""R16 · 纠正 §1051 追加的行尾：台账约定是 bare LF，首次追加误用 CRLF。

做法（可证可逆）：
  1. 读盘；断言当前 = 首次追加后的长度 4,102,372，且前 4,073,362 字节 sha256 == 追加前 sha256。
     ⇒ 这证明「截断到 4,073,362 即可逐字节还原原件」。
  2. 截断到 4,073,362 并复验 sha256 == 原 sha256（原件完整还原）。
  3. 以 bare LF 重追加：分隔空行 b"\n" + 草稿原字节（草稿本身就是 LF，一字不改）。
  4. 复验前缀哈希 + 读盘。
"""
import hashlib, os, sys

sys.stdout.reconfigure(encoding="utf-8")

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
DRAFT  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_drafts\§1051.md"
OUT    = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_BASE\APPEND_1051_FIX.txt"

N_BEFORE = 4073362
SHA_BEFORE = "A163087F0D25801CD268358EFC44D2F479EE3FE28D097F0BA71099190960CF5A"
N_BAD = 4102372


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    rep = []
    with open(LEDGER, "rb") as f:
        cur = f.read()

    rep.append("=== §1051 追加行尾纠正（CRLF → LF）===")
    rep.append("当前 bytes=%d（预期 %d）" % (len(cur), N_BAD))
    assert len(cur) == N_BAD, "当前长度不符，可能被别人改过，中止"
    assert sha(cur[:N_BEFORE]) == SHA_BEFORE, "前缀哈希不等，中止"
    rep.append("前缀验证：前 %d 字节 sha256 == 追加前 sha256 ⇒ 截断即可逐字节还原原件  PASS" % N_BEFORE)

    truncated = cur[:N_BEFORE]
    assert sha(truncated) == SHA_BEFORE, "截断后 sha256 不等于原件，中止"
    rep.append("截断到 %d 字节后 sha256 = %s" % (len(truncated), sha(truncated)))
    rep.append("与原件逐位相同 ⇒ 还原 PASS（首次追加的 29,010 字节已完全移除，原件一字未损）")

    with open(DRAFT, "rb") as f:
        draft = f.read()
    assert not draft.startswith(b"\xef\xbb\xbf")
    assert draft.count(b"\r\n") == 0 and draft.endswith(b"\n")

    payload = b"\n" + draft          # 空行分隔（bare LF）+ 草稿原字节
    after = truncated + payload

    with open(LEDGER, "wb") as f:
        f.write(after)

    with open(LEDGER, "rb") as f:
        rr = f.read()
    assert len(rr) == N_BEFORE + len(payload)
    assert sha(rr[:N_BEFORE]) == SHA_BEFORE, "读回复验前缀哈希不等"
    assert rr[-len(payload):] == payload, "读回复验追加段不一致"

    crlf = rr.count(b"\r\n")
    lf = rr.count(b"\n") - crlf

    rep.append("")
    rep.append("重追加：分隔空行 1 B + 草稿原字节 %d B = %d B（草稿 LF 原样，未做任何行尾转换）"
               % (len(draft), len(payload)))
    rep.append("追加后 bytes=%d  (+%d)" % (len(rr), len(payload)))
    rep.append("追加后 sha256 = %s" % sha(rr))
    rep.append("行尾分布：CRLF=%d  bare-LF=%d（追加前 CRLF=337 / bare-LF=38750；§1050 段 96 LF/1 CRLF、§1049 段 149 LF/2 CRLF ⇒ 约定是 bare LF）"
               % (crlf, lf))
    rep.append("")
    rep.append("【核心验证】前 %d 字节 sha256 = %s" % (N_BEFORE, sha(rr[:N_BEFORE])))
    rep.append("与追加前整文件 sha256 逐位比对：%s" % ("PASS" if sha(rr[:N_BEFORE]) == SHA_BEFORE else "FAIL"))
    rep.append("读盘复验：PASS")
    rep.append("")
    rep.append("结论：§1051 现为 bare LF，与 §1049/§1050 一致；台账新增 %d 字节，既有内容零改动。" % len(payload))

    txt = "\n".join(rep) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


main()
