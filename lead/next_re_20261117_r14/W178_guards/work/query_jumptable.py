"""Resolve FUN_006CC390 jump table and prove a path to 0x6CD8CD."""
import os
import struct
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))
import analyze as a

ENTRY = 0x6CC390
SITE = 0x6CD8CD
JT = 0x6CDE44


def main():
    b = a.Bin(a.EXE)
    head = [a.insn_text(i) for i in a.disasm_range(b, ENTRY, ENTRY + 0x40) if i.id]
    print("HEAD")
    for x in head:
        print("  " + x)

    # Read 64 dwords, print code-looking entries and the first non-code one.
    print("JUMP_TABLE")
    entries = []
    for idx in range(64):
        val = struct.unpack("<I", b.read(JT + idx * 4, 4))[0]
        is_code = 0x401000 <= val <= 0x7E038D
        if is_code:
            entries.append(val)
            if idx < 24:
                print(f"  [{idx:#04x}] {val:#010x}")
        else:
            print(f"  first non-code [{idx:#04x}] {val:#010x}")
            break
    print(f"code_entry_count={len(entries)} unique={len(set(entries))}")

    instrs = a.disasm_range(b, ENTRY, ENTRY + 6835)
    by = {i.address: k for k, i in enumerate(instrs) if i.id}

    def succ(ins, k):
        nxt = instrs[k + 1].address if k + 1 < len(instrs) else None
        m = ins.mnemonic
        if m == "ret" or m.startswith("retf"):
            return []
        if m == "jmp":
            t = a.parse_target(ins.op_str)
            if t is None:
                # this function's only indirect jmp is the head table
                return entries
            return [t]
        if m.startswith("j"):
            t = a.parse_target(ins.op_str)
            return [x for x in (t, nxt) if x is not None]
        if m == "call":
            return [nxt] if nxt is not None else []
        return [nxt] if nxt is not None else []

    q = deque([(instrs[0].address,)])
    seen = {instrs[0].address}
    path = None
    while q:
        p = q.popleft()
        last = p[-1]
        k = by.get(last)
        if k is None:
            continue
        ins = instrs[k]
        if last == SITE:
            path = p
            break
        for s in succ(ins, k):
            if s not in seen:
                seen.add(s)
                q.append(p + (s,))
    print(f"site_reachable_with_jt={path is not None} reachable_addrs={len(seen)}")
    if path:
        print("PATH")
        for x in path:
            k = by.get(x)
            if k is not None:
                print("  " + a.insn_text(instrs[k]))


if __name__ == "__main__":
    main()
