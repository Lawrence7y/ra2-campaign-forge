# -*- coding: utf-8 -*-
"""R16 · 把 _drafts/§1052.md 逐字追加进台账（append-only + 字节前缀哈希验证）。

行尾：台账约定是 bare LF（§1049/§1050/§1051 正文均 LF，仅 337 处历史 CRLF）。
本次按 bare LF 追加：分隔空行 b"\n" + 草稿原字节（草稿本身纯 LF、无 BOM、以 LF 结尾）。
"""
import hashlib, os, sys

sys.stdout.reconfigure(encoding="utf-8")

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
DRAFT  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_drafts\§1052.md"
OUT    = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_BASE\APPEND_1052.txt"


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    with open(LEDGER, "rb") as f:
        before = f.read()
    with open(DRAFT, "rb") as f:
        draft = f.read()

    n_before = len(before)
    h_before = sha(before)
    crlf_before = before.count(b"\r\n")

    assert h_before == "E0D84CBFB387172EDD48F7F088A7AB18D280271AA87AE0EE103206FEDF47BF6F", "台账 sha 与预期不符，中止"
    assert not draft.startswith(b"\xef\xbb\xbf"), "草稿带 BOM"
    assert draft.count(b"\r\n") == 0, "草稿含 CRLF"
    assert draft.endswith(b"\n"), "草稿不以 LF 结尾"
    assert draft.split(b"\n")[0].startswith("## §1052".encode("utf-8")), "草稿首行不是 §1052 标题"

    payload = b"\n" + draft
    after = before + payload
    prefix = after[:n_before]
    assert sha(prefix) == h_before, "前缀哈希不等，中止"

    with open(LEDGER, "wb") as f:
        f.write(after)

    with open(LEDGER, "rb") as f:
        rr = f.read()
    assert len(rr) == n_before + len(payload)
    assert sha(rr[:n_before]) == h_before, "读回复验前缀哈希不等"
    assert rr[-len(payload):] == payload, "读回复验追加段不一致"

    crlf_after = rr.count(b"\r\n")
    txt = "\n".join([
        "=== §1052 追加台账 · append-only 验证 ===",
        "追加前  bytes=%d  lines=%d  CRLF=%d  sha256=%s" % (n_before, before.count(b"\n"), crlf_before, h_before),
        "草稿    bytes=%d  LF=%d  CRLF=0  BOM=no  首行=## §1052" % (len(draft), draft.count(b"\n")),
        "追加段  bytes=%d（分隔空行 1 + 草稿 %d）" % (len(payload), len(draft)),
        "追加后  bytes=%d  (+%d)  CRLF=%d（未增）" % (len(rr), len(payload), crlf_after),
        "",
        "【核心验证】前 %d 字节 sha256 = %s" % (n_before, sha(rr[:n_before])),
        "与追加前整文件 sha256 逐位比对：%s" % ("PASS" if sha(rr[:n_before]) == h_before else "FAIL"),
        "读盘复验：PASS   追加段字节复验：PASS",
        "",
        "追加后整文件 sha256 = %s" % sha(rr),
        "追加后 max § = 见台账末节（应为 §1052）",
    ]) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


main()
