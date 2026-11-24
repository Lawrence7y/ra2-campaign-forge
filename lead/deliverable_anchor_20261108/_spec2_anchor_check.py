# -*- coding: utf-8 -*-
"""_spec2_anchor_check.py — DA-SPEC v2 / S2 条「件内自锚」生成与校验（本规范条文的可执行版）。
用法：
  python -I -X utf8 _spec2_anchor_check.py fill  <文件绝对路径>   # 就地填充锚行两字段（仅限本写域新件）
  python -I -X utf8 _spec2_anchor_check.py check <文件绝对路径>   # 只读校验；退出码 0 = 锚成立
与 v1（_da_anchor_selfcheck.py）的三处差异（对应复核崩点 P3 与本件 S2 条）：
  ①定位与替换统一为行级语义：v1 的 :105 用行首 startswith 定位、:111 用全文件首次出现替换，
    两者可指向不同字节区间（本会话内存实验：同一字节流两口径 canon = a2d0259d… 与 d564c4ca…）；
  ②18 字节前缀全文件仅允许出现 1 次（照录防护）：v1 只数「行首」，缩进/反引号照录不可见——
    审计件自身即含 3 处前缀（:3 真锚行 + :99/:105 规则文本照录），v1 校验仍 ANCHOR OK；
  ③锚行带 eol=raw 字段，显式声明不做任何 EOL 归一化（v1 条文未声明 EOL）。
"""
import hashlib
import sys

PREFIX = b"DA-ANCHOR: sha256="  # 18 字节行首标记


def locate(raw):
    cnt = raw.count(PREFIX)
    if cnt != 1:
        raise ValueError("prefix occurrences=%d (expect 1; 照录防护)" % cnt)
    lines = raw.split(b"\n")
    hit = [i for i, l in enumerate(lines) if l.startswith(PREFIX)]
    if len(hit) != 1:
        raise ValueError("line-start anchor lines=%d (expect 1)" % len(hit))
    return lines, hit[0]


def canon_bytes(lines, ai):
    """行级替换：只把 startswith 选中的那一行的 sha256 字段清零。"""
    l = lines[ai]
    return b"\n".join(lines[:ai] + [l[:18] + b"0" * 64 + l[82:]] + lines[ai + 1:])


def main():
    mode, path = sys.argv[1], sys.argv[2]
    raw = open(path, "rb").read()
    if mode == "fill":
        n = len(raw)
        lines, ai = locate(raw)
        l = lines[ai]
        bi = l.index(b"bytes=")
        l2 = l[:bi + 6] + b"%010d" % n + l[bi + 16:]
        lines[ai] = l2
        a = hashlib.sha256(canon_bytes(lines, ai)).hexdigest().encode("ascii")
        lines[ai] = l2[:18] + a + l2[82:]
        open(path, "wb").write(b"\n".join(lines))
        print("filled bytes=%d anchor=%s" % (n, a.decode()))
        return 0
    # ---- check（只读）----
    lines, ai = locate(raw)
    l = lines[ai]
    field = l[18:82]
    bi = l.index(b"bytes=")
    nbytes = int(l[bi + 6:bi + 16], 10)
    if l[bi + 16:bi + 17] != b" ":
        print("FAIL: bytes field not 10-width")
        return 5
    if len(raw) != nbytes:
        print("FAIL: bytes field=%d actual=%d" % (nbytes, len(raw)))
        return 3
    if b"eol=raw" not in l:
        print("FAIL: eol=raw field missing")
        return 5
    h = hashlib.sha256(canon_bytes(lines, ai)).hexdigest()
    if h != field.decode("ascii"):
        print("FAIL: field=%s canon=%s" % (field.decode("ascii"), h))
        return 4
    print("ANCHOR OK (v2)")
    print("bytes=%d" % len(raw))
    print("anchor=%s" % field.decode("ascii"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
