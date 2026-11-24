# -*- coding: utf-8 -*-
"""R16 · 把 _drafts/§1051.md 逐字追加进台账（append-only + 字节前缀哈希验证）。

规则：
  1. 严禁改动已存在的任何字节 —— 追加后取「旧长度前缀」重算 sha256，必须等于追加前整文件 sha256。
  2. 台账行尾是 CRLF；草稿是 LF。追加时把草稿 LF→CRLF（不改任何字符内容），并在最前面加一个空行（与 §1050 接缝一致）。
  3. 草稿内容一字不改（除行尾归一）。
"""
import hashlib, os, sys

sys.stdout.reconfigure(encoding="utf-8")

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
DRAFT  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_drafts\§1051.md"
OUT    = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_BASE\APPEND_1051.txt"


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    with open(LEDGER, "rb") as f:
        before = f.read()
    with open(DRAFT, "rb") as f:
        draft = f.read()

    n_before = len(before)
    h_before = sha(before)
    lines_before = before.count(b"\r\n")

    # 草稿：校验是纯 LF、无 BOM、以 LF 结尾
    assert not draft.startswith(b"\xef\xbb\xbf"), "草稿带 BOM"
    n_lf = draft.count(b"\n")
    n_crlf = draft.count(b"\r\n")
    assert n_crlf == 0, "草稿已含 CRLF，预期纯 LF"
    assert draft.endswith(b"\n"), "草稿不以换行结尾"

    body = draft.replace(b"\n", b"\r\n")
    sep = b"\r\n"                     # 空行分隔（台账 §1050 接缝同为一行空行）
    payload = sep + body

    after = before + payload
    n_after = len(after)

    # 前缀哈希：旧长度前缀必须逐位相同
    prefix = after[:n_before]
    assert sha(prefix) == h_before, "前缀哈希不等 —— 已存在内容被改动，中止"

    with open(LEDGER, "wb") as f:
        f.write(after)

    # 复验：重新读盘
    with open(LEDGER, "rb") as f:
        reread = f.read()
    assert len(reread) == n_after
    assert sha(reread[:n_before]) == h_before, "读回复验前缀哈希不等"
    assert reread[-len(payload):] == payload, "读回复验追加段不一致"

    rep = []
    rep.append("=== §1051 追加台账 · append-only 验证 ===")
    rep.append("台账      : %s" % LEDGER)
    rep.append("草稿      : %s" % DRAFT)
    rep.append("")
    rep.append("追加前  bytes=%d  lines(CRLF)=%d  sha256=%s" % (n_before, lines_before, h_before))
    rep.append("草稿    bytes=%d  LF=%d  CRLF=%d  BOM=no" % (len(draft), n_lf, n_crlf))
    rep.append("追加段  bytes=%d = 分隔空行 2 + 草稿行尾归一后 %d" % (len(payload), len(body)))
    rep.append("追加后  bytes=%d  (+%d)" % (n_after, n_after - n_before))
    rep.append("")
    rep.append("【核心验证】取追加后文件的前 %d 字节重算 sha256：" % n_before)
    rep.append("  %s" % sha(prefix))
    rep.append("与追加前整文件 sha256 逐位比对：%s" % ("PASS" if sha(prefix) == h_before else "FAIL"))
    rep.append("读盘复验（写完重新打开）：%s" % ("PASS" if sha(reread[:n_before]) == h_before else "FAIL"))
    rep.append("追加段字节复验：%s" % ("PASS" if reread[-len(payload):] == payload else "FAIL"))
    rep.append("")
    rep.append("追加后整文件 sha256 = %s" % sha(reread))
    rep.append("追加后 lines(CRLF) = %d  (+%d)" % (reread.count(b"\r\n"), reread.count(b"\r\n") - lines_before))
    rep.append("")
    rep.append("字符内容未改：仅 LF→CRLF 行尾归一 + 前置一个空行；正文一字未动。")

    txt = "\n".join(rep) + "\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


main()
