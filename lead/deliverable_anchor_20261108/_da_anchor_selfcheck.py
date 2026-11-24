# -*- coding: utf-8 -*-
"""_da_anchor_selfcheck.py — DA-SPEC R1 件内自锚复核算法（规范条文的可执行版）。
用法：python -I -X utf8 _da_anchor_selfcheck.py <被检文件绝对路径>
步骤：①唯一性检查；②bytes 字段 vs 实际字节数；③sha256 字段清零后全文件重算比对。
退出码 0 = 锚成立；非 0 = 锚失效。只读，不修改文件。
"""
import hashlib
import sys

MARK = b"DA-ANCHOR: sha256="  # 18 字节行首标记


def main(path):
    raw = open(path, "rb").read()
    lines = raw.split(b"\n")
    hits = [l for l in lines if l.startswith(MARK)]
    if len(hits) != 1:
        print("FAIL: anchor lines found = %d (expect 1)" % len(hits))
        return 2
    line = hits[0]
    field = line[18:18 + 64]
    bi = line.index(b"bytes=")
    nbytes_field = int(line[bi + 6:bi + 16], 10)
    if len(raw) != nbytes_field:
        print("FAIL: bytes field=%d actual=%d" % (nbytes_field, len(raw)))
        return 3
    canon = raw.replace(line, line[:18] + b"0" * 64 + line[18 + 64:], 1)
    actual = hashlib.sha256(canon).hexdigest()
    if actual != field.decode("ascii"):
        print("FAIL: sha256 field=%s canonical=%s" % (field.decode(), actual))
        return 4
    print("ANCHOR OK")
    print("bytes=%d" % len(raw))
    print("sha256(field)=%s" % field.decode())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
