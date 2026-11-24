"""atexit registration scan: every `push imm32 ; ... ; call 0x7C978A` in .text.
Returns the set of destructor function addresses registered with atexit."""
import sys
from pe import BY, ORDER, fmt

ATEXIT = 0x7C978A


def scan():
    regs = []
    for a in ORDER:
        i = BY[a]
        if i.mnemonic != "call" or i.op_str != "0x7c978a":
            continue
        # the argument is pushed somewhere in the preceding <=4 instructions
        idx = ORDER.index(a)
        val = None
        site = None
        for k in range(1, 5):
            if idx - k < 0:
                break
            j = BY[ORDER[idx - k]]
            if j.mnemonic == "push" and j.op_str.startswith("0x"):
                try:
                    val = int(j.op_str, 16)
                except ValueError:
                    pass
                site = j.address
                break
            if j.mnemonic == "mov" and j.op_str.startswith("dword ptr [esp"):
                # mov dword ptr [esp], imm
                parts = j.op_str.split(",")
                if len(parts) == 2 and parts[1].strip().startswith("0x"):
                    try:
                        val = int(parts[1].strip(), 16)
                    except ValueError:
                        pass
                    site = j.address
                break
        regs.append((a, site, val))
    return regs


if __name__ == "__main__":
    r = scan()
    print("atexit register sites: %d" % len(r))
    targets = set()
    for a, site, val in r:
        print("  call@%08X  arg_site=%s  arg=%s" % (a, "%08X" % site if site else "-",
                                                    "%08X" % val if val else "-"))
        if val:
            targets.add(val)
    print("distinct registered function addresses: %d" % len(targets))
    want = [int(x, 16) for x in sys.argv[1:]]
    for w in want:
        print("  %08X registered with atexit: %s" % (w, w in targets))
