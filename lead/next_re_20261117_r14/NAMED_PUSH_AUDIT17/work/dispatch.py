"""Find virtual dispatch sites: read a global holding a network object, then
call dword ptr [reg + disp] -> slot = disp/4."""
import sys
from pe import BY, ORDER, u32, read, fmt, in_text

GLOBALS = [0x887628, 0x887640, 0x887644, 0x88762C, 0x887630]


def scan(globals_, window=28):
    hits = []
    addrs = ORDER
    for idx, a in enumerate(addrs):
        i = BY[a]
        if i.mnemonic != "mov":
            continue
        # mov reg, dword ptr [0x807628]  (capstone prints decimal-ish? no, hex)
        if "dword ptr [0x" not in i.op_str:
            continue
        try:
            base = int(i.op_str.split("dword ptr [0x")[1].split("]")[0], 16)
        except Exception:
            continue
        if base not in globals_:
            continue
        reg = i.op_str.split(",")[0].strip()
        # forward window: look for call dword ptr [reg + disp] / [reg]
        for k in range(1, window):
            if idx + k >= len(addrs):
                break
            j = BY[addrs[idx + k]]
            if j.mnemonic.startswith("ret"):
                break
            if j.mnemonic in ("call", "jmp") and j.op_str.startswith("dword ptr ["):
                op = j.op_str[len("dword ptr ["):-1]
                if op == reg:
                    hits.append((a, base, reg, 0, j))
                elif op.startswith(reg + " + "):
                    try:
                        disp = int(op.split("+")[1].strip(), 16)
                    except Exception:
                        continue
                    hits.append((a, base, reg, disp, j))
                break
    return hits


if __name__ == "__main__":
    g = [int(x, 16) for x in sys.argv[1:]] or GLOBALS
    for a, base, reg, disp, j in scan(g):
        print("load@%08X [%08X] reg=%s -> " % (a, base, reg) + fmt(j) + "   slot=%d" % (disp // 4))
