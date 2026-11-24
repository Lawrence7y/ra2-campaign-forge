import sys, core, struct

def refs_imm(target):
    return core.imm32_refs(target)

def refs_call(target):
    """E8 rel32 calls landing exactly on target"""
    out = []
    data = core.read(core.TEXT_LO, core.TEXT_HI - core.TEXT_LO)
    for i in range(len(data) - 5):
        if data[i] == 0xE8:
            rel = struct.unpack_from("<i", data, i + 1)[0]
            va = core.TEXT_LO + i
            if (va + 5 + rel) & 0xFFFFFFFF == target:
                out.append(va)
    return out

def find_fn_start(va, back=0x400):
    """walk back for CC padding to guess function start"""
    lo = max(core.TEXT_LO, va - back)
    d = core.read(lo, va - lo)
    k = d.rfind(b"\xcc")
    if k >= 0:
        return lo + k + 1
    return None

if __name__ == "__main__":
    mode, t = sys.argv[1], int(sys.argv[2], 16)
    if mode == "imm":
        rs = refs_imm(t)
    elif mode == "call":
        rs = refs_call(t)
    else:
        rs = []
    print("%s refs to %08X: %d" % (mode, t, len(rs)))
    for r in rs[:60]:
        print("   %08X  (fn start ~ %s)" % (r, hex(find_fn_start(r)) if find_fn_start(r) else "?"))
