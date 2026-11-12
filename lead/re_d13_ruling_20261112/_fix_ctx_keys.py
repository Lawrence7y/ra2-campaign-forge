# -*- coding: utf-8 -*-
"""把候选件里 stub 的旧 context 键（eip）升级为新结构（ip/sp/bits 等）。

原因：_get_context 重构为「按位宽分流」后返回 {"bits","ip","sp",...}，
      而离线单测的 stub 仍在产出 {"eip"}，会导致 walk_stub 取不到键。
"""
import io
import sys

P = r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112\e3_stack_sampler_candidate.py"

NEW_CTX = '{"bits": 32, "ip": 0x401000, "sp": 0x1000, "bp": 0x1100, "eflags": 0x202, "cs": 0x1b}'

REPLACEMENTS = [
    # walk_stub 里取 ctx["eip"] → ctx["ip"]
    ('lambda ctx, depth: [ctx["eip"]]', 'lambda ctx, depth: [ctx["ip"]]'),
    # 带偏移的 context stub
    ('"get_context_stub": lambda h: {"eip": 0x401000 + (h - 1000)}',
     '"get_context_stub": lambda h: {"bits": 32, "ip": 0x401000 + (h - 1000), '
     '"sp": 0x1000, "bp": 0x1100, "eflags": 0x202, "cs": 0x1b}'),
    # 固定 context stub
    ('"get_context_stub": lambda h: {"eip": 0x401000}',
     '"get_context_stub": lambda h: ' + NEW_CTX),
    # 显式 dict 字面量
    ('[{"eip": 0x401000}]', '[{"bits": 32, "ip": 0x401000, "sp": 0x1000}]'),
    # boom 用的 ctx（无需改，但保持一致）
    ('{"eip": 0x401000 + (h - 1000)}', '{"bits": 32, "ip": 0x401000 + (h - 1000)}'),
]


def main():
    src = io.open(P, encoding="utf-8").read()
    orig_len = len(src)
    total = 0
    for old, new in REPLACEMENTS:
        n = src.count(old)
        if n:
            src = src.replace(old, new)
            total += n
            print("replaced %d x %r" % (n, old[:60]))
    if total == 0:
        print("!! 无匹配，可能已改过")
    io.open(P, "w", encoding="utf-8", newline="").write(src)
    print("\nbytes: %d -> %d" % (orig_len, len(src)))

    # 残留检查
    left = []
    for ln, line in enumerate(src.splitlines(), 1):
        if '"eip"' in line or "ctx[\"eip\"]" in line:
            left.append((ln, line.strip()[:110]))
    if left:
        print("\n!! 仍有 eip 残留：")
        for ln, t in left:
            print("  L%d: %s" % (ln, t))
        return 1
    print("\n[OK] 无 eip 残留")
    return 0


if __name__ == "__main__":
    sys.exit(main())
