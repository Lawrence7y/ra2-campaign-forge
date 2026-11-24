# -*- coding: utf-8 -*-
"""append_line.py —— 只提供 append_line(path, line) 的共享实现。

设计约束（本卡「只追加，不改写」）：
  * 以 'a+' 追加模式打开，**不读取再重写**，不碰既有任何字节；
  * 追加前先确保文件以 LF 结尾（否则就补一个 LF），再追加「行 + LF」——
    这样原有内容逐字节不变，新增部分恰好是一条完整行；
  * 不做任何编码转换：直接写 UTF-8 bytes。

唯一的「就地」动作是：若原文件末尾缺 LF，则补一个 LF 再写行。
本卡 5 个产物中，纪律 3/4/22/28 的产物已以 LF 结尾，
纪律 27 的 _verdicts.tsv 末尾是否缺 LF 会在 append_link.py 里逐项打印。
"""
import io
import os


def ensure_trailing_lf(path):
    """若文件非空且末尾不是 LF，则补一个 LF。返回是否补过。"""
    size = os.path.getsize(path)
    if size == 0:
        return False
    with io.open(path, 'rb') as f:
        f.seek(-1, os.SEEK_END)
        last = f.read(1)
    if last == b'\n':
        return False
    with io.open(path, 'ab') as f:
        f.write(b'\n')
    return True


def append_line(path, line):
    """在 path 末尾追加一条行（含结尾 LF）。返回 (bytes_before, bytes_after, added_lf)。"""
    if os.path.isfile(path):
        before = os.path.getsize(path)
    else:
        before = 0
    added_lf = ensure_trailing_lf(path)
    with io.open(path, 'ab') as f:
        f.write(line.encode('utf-8') + b'\n')
    return (before, os.path.getsize(path), added_lf)
