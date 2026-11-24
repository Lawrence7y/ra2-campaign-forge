"""Find virtual-dispatch sites for a given slot offset, where the dispatched object is
traceable to the network-object globals (one level of vtable load allowed)."""
import sys
from pe import BY, ORDER, u32, read, fmt, in_text

GLOBALS = [0x887628, 0x887640, 0x887644, 0x88762C, 0x887630, 0x887634]


def scan_slot(disp_want, window=40, verbose=False):
    out = []
    addrs = ORDER
    for idx, a in enumerate(addrs):
        i = BY[a]
        if i.mnemonic != "mov" or "dword ptr [0x" not in i.op_str:
            continue
        try:
            base = int(i.op_str.split("dword ptr [0x")[1].split("]")[0], 16)
        except Exception:
            continue
        if base not in GLOBALS:
            continue
        reg = i.op_str.split(",")[0].strip()
        vtreg = None
        for k in range(1, window):
            if idx + k >= len(addrs):
                break
            j = BY[addrs[idx + k]]
            if j.mnemonic.startswith("ret"):
                break
            # vtable fetch: mov r2, dword ptr [reg]  or  mov r2, dword ptr [reg + 0]
            if j.mnemonic == "mov" and "dword ptr [" + reg + "]" in j.op_str:
                vtreg = j.op_str.split(",")[0].strip()
            if j.mnemonic in ("call", "jmp") and j.op_str.startswith("dword ptr ["):
                op = j.op_str[len("dword ptr ["):-1]
                for r in ([vtreg] if vtreg else []) + [reg]:
                    if r is None:
                        continue
                    if op == r:
                        d = 0
                    elif op.startswith(r + " + "):
                        try:
                            d = int(op.split("+")[1].strip(), 16)
                        except Exception:
                            continue
                    else:
                        continue
                    if d == disp_want:
                        out.append((a, base, r, j))
                    break
    return out


if __name__ == "__main__":
    for d in [int(x, 16) for x in sys.argv[1:]]:
        hits = scan_slot(d)
        print("disp 0x%02X (slot %d): %d site(s)" % (d, d // 4, len(hits)))
        for a, base, r, j in hits:
            print("    load@%08X [%08X] -> %s" % (a, base, fmt(j)))
