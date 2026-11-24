#!/usr/bin/env python3
# R75-FALSIFY-1：证伪单条断言。
# 只做三步：(1) 自行统计 R14_COMMON.md 的 0x00 站点分组；(2) Python 字面量实测；(3) 裁定。
# 只读 R14_COMMON.md，不写任何既有文件。

import sys
import os

TARGET = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'R14_COMMON.md')
TARGET = os.path.normpath(TARGET)

OCT = set(b'01234567')


def step1():
    with open(TARGET, 'rb') as f:
        data = f.read()
    offs = [i for i, c in enumerate(data) if c == 0x00]
    grp_oct = []       # 0x00 之后第一个字节在 0x30..0x37
    grp_other = []     # 其它
    for o in offs:
        nxt = data[o + 1:o + 2]
        if nxt and nxt[0] in OCT:
            grp_oct.append((o, nxt, data[o + 1:o + 9]))
        else:
            grp_other.append((o, nxt, data[o + 1:o + 9]))
    print('FILE            :', TARGET)
    print('SIZE_BYTES      :', len(data))
    print('NUL_TOTAL       :', len(offs))
    print('GROUP_OCT_COUNT :', len(grp_oct))
    print('GROUP_OTHER_CNT :', len(grp_other))
    print()
    print('-- A 组：0x00 后第一字节为 0x30..0x37（八进制数字）--')
    for n, (o, nxt, tail) in enumerate(grp_oct, 1):
        print('A%-2d off=%-7d next=0x%02X %-10r tail=%r'
              % (n, o, nxt[0], nxt.decode('latin-1'),
                 tail.decode('utf-8', 'backslashreplace')))
    print()
    print('-- B 组：其余站点 --')
    for n, (o, nxt, tail) in enumerate(grp_other, 1):
        print('B%-2d off=%-7d next=0x%02X %-10r tail=%r'
              % (n, o, nxt[0], nxt.decode('latin-1'),
                 tail.decode('utf-8', 'backslashreplace')))
    return len(offs), len(grp_oct), len(grp_other)


def show(expr):
    val = eval(expr)
    codes = ' '.join('%02X' % b for b in val.encode('latin-1')) if isinstance(val, str) else ''
    raw = ' '.join('%02X' % b for b in val) if isinstance(val, (bytes, bytearray)) else ''
    print('EXPR : %s' % expr)
    print('TYPE : %s' % type(val).__name__)
    print('REPR : %r' % (val,))
    print('LEN  : %d' % len(val))
    print('HEX  : %s' % (codes or raw or '(n/a)'))
    print()


def step2():
    exprs = [
        r'"\x0004393F0"',     # 反斜杠 x 加两位十六进制 00，其后紧跟八进制数字串
        r'"\x00x47C427"',     # 同一机制，其后紧跟 x 开头的地址尾
        r'"\004"',            # 反斜杠 0 加三位八进制数字
        r'"\0004"',           # 反斜杠 0 加三位八进制数字 000，其后余 4
        r'"\004393F0"',       # 反斜杠 0 0 4 打头，其后为数字串
        r'"\0004393F0"',      # 反斜杠 0 0 0 打头，其后为数字串
        r'"\u0000"',          # 反斜杠 u 加四位十六进制
        r'"\u000004393F0"',   # u 转义吃 4 位后紧跟八进制数字串
        r'"\N{NULL}04393F0"', # 命名转义
        r'"\0" + "4393F0"',   # 单字符反斜杠 0 拼接
    ]
    for e in exprs:
        show(e)


def step3():
    lit = r'"\x0004393F0"'
    val = eval(lit).encode('latin-1')
    want = b'\x00' + b'04393F0'
    print('COUNTEREXAMPLE_LITERAL : %s' % lit)
    print('DECODED_HEX            : %s' % ' '.join('%02X' % b for b in val))
    print('DECODED_LEN            : %d' % len(val))
    print('EXPECTED_HEX           : %s' % ' '.join('%02X' % b for b in want))
    print('EXPECTED_LEN           : %d' % len(want))
    print('MATCH                  : %s' % (val == want))
    print('VERDICT                : BROKEN' if val == want else 'VERDICT: undecided')
    return val == want


if __name__ == '__main__':
    tot, a, b = step1()
    print('=' * 70)
    step2()
    print('=' * 70)
    ok = step3()
    print()
    print('SUMMARY total=%d groupA=%d groupB=%d counterexample_match=%s'
          % (tot, a, b, ok))
    sys.exit(0 if ok else 1)
