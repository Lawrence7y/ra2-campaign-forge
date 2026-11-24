"""function-start map from direct call targets + prologue heuristics"""
import struct, core

_targets = None


def call_targets():
    global _targets
    if _targets is not None:
        return _targets
    data = core.read(core.TEXT_LO, core.TEXT_HI - core.TEXT_LO)
    ts = set()
    for i in range(len(data) - 5):
        if data[i] == 0xE8:
            rel = struct.unpack_from("<i", data, i + 1)[0]
            va = core.TEXT_LO + i
            t = (va + 5 + rel) & 0xFFFFFFFF
            if core.TEXT_LO <= t < core.TEXT_HI:
                ts.add(t)
    _targets = sorted(ts)
    return _targets


def owner(site):
    """nearest call-target <= site"""
    ts = call_targets()
    lo, hi = 0, len(ts) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if ts[mid] <= site:
            best = ts[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def is_ctorish(fnva, store_site, n=260):
    """classify a function: ctor / dtor / other, using base-ctor call + free/delete-flag markers"""
    ins = core.fn(fnva, n)
    txt = core.render(ins)
    facts = dict(fn=fnva, store=None, base_call=None, frees=[], delflag=None, ret=None,
                 calls=[])
    for i in ins:
        if i.address == store_site:
            facts["store"] = (i.address, i.mnemonic, i.op_str,
                              " ".join("%02X" % b for b in i.bytes))
        if i.mnemonic == "call":
            t = i.op_str
            facts["calls"].append((i.address, t))
            if t.startswith("0x") and facts["base_call"] is None and i.address < store_site:
                try:
                    facts["base_call"] = (i.address, int(t, 16))
                except ValueError:
                    pass
            if t in ("0x7c8b3d", "0x7c8b32", "0x7c8b1e"):
                facts["frees"].append((i.address, t))
        if i.mnemonic == "test" and "esp + 0x" in i.op_str and ", 1" in i.op_str:
            facts["delflag"] = (i.address, i.op_str)
        if i.mnemonic in ("ret", "retn"):
            facts["ret"] = (i.address, i.op_str)
    facts["text"] = txt
    return facts
