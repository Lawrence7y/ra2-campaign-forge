"""For each candidate install site of a vtable, print its host function and screen for ㉓ dtor markers."""
from pe import (BY_ADDR, TEXT_LO, TEXT_HI, u32, read, fmt, MD2)

DTOR_MARKERS = [0x7258D0, 0x7C8B3D, 0x7C978A, 0x7C8B9B]


def fstart(va, cap=6000):
    """Walk backwards to a plausible function start: after a ret/int3/nop pad run."""
    a = va
    steps = 0
    while a > TEXT_LO and steps < cap:
        prev = None
        # find instruction whose end == a
        p = a - 1
        for back in range(1, 16):
            cand = BY_ADDR.get(a - back)
            if cand is not None and a - back + cand.size == a:
                prev = cand
                break
        if prev is None:
            break
        if prev.mnemonic in ("ret", "retn", "retf", "int3", "jmp"):
            return a
        if prev.mnemonic == "nop":
            # measure nop run backwards
            b = prev.address
            while BY_ADDR.get(b) is not None and BY_ADDR[b].mnemonic == "nop":
                b -= 1
            if BY_ADDR.get(b + 1) is not None:
                return b + 1
        a = prev.address
        steps += 1
    return a


def _imm(i):
    """imm of a single-operand call/push, parsed from text (BY_ADDR insns carry no detail)."""
    s = i.op_str.strip()
    if s.startswith("0x"):
        try:
            return int(s, 16)
        except ValueError:
            return None
    return None


def scan(va_lo, va_hi):
    out = []
    a = va_lo
    while a < va_hi:
        i = BY_ADDR.get(a)
        if i is None:
            a += 1
            continue
        if i.mnemonic in ("call", "push"):
            v = _imm(i)
            if v is not None and v in DTOR_MARKERS:
                out.append(i)
            elif (i.mnemonic == "push" and v is not None
                  and TEXT_LO <= v < TEXT_HI and v < 0x7C0000):
                out.append(i)
        a += i.size
    return out


def report_site(site, label=""):
    st = fstart(site)
    a = st
    while BY_ADDR.get(a) is not None and BY_ADDR[a].mnemonic in ("nop", "int3"):
        a += BY_ADDR[a].size
    st = a
    body = []
    a = st
    while a < TEXT_HI and len(body) < 2500:
        i = BY_ADDR.get(a)
        if i is None:
            break
        body.append(i)
        a += i.size
        if i.mnemonic.startswith("ret"):
            break
    end = body[-1].address + body[-1].size if body else st
    print("SITE %08X %s" % (site, label))
    print("   host fn approx %08X .. %08X (%d insns), last=%s" % (
        st, end, len(body), fmt(body[-1]) if body else "?"))
    print("   head:")
    for i in body[:6]:
        print("      " + fmt(i))
    mk = scan(st, end)
    print("   marker-ish insns in host (call/push of dtor/system addrs):")
    for i in mk[:20]:
        print("      " + fmt(i))
    if not mk:
        print("      (none)")
    print("   SITE INSNS (call/push/indirect-call of interest):")
    for i in body:
        if i.mnemonic in ("call", "push"):
            print("      " + fmt(i))
    return st, end


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        report_site(int(arg, 16))
