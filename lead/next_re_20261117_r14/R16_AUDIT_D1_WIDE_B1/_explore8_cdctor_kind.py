# -*- coding: utf-8 -*-
"""Classify, for the vtable whose chosen site is a stack temp, each on-`this`
install site: constructor vs deleting-destructor vs other."""
import io, os, sys, bisect, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
IB = 0x400000
import pefile, capstone
EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "ra2youli", "gamemd.exe")
pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    secs.append((IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.get_data()))
end = max(va + max(vs, rs) for va, vs, rs, _d in secs)
buf = bytearray(end - IB + 16)
for va, vs, rs, d in secs:
    buf[va - IB:va - IB + len(d)] = d
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
def dis(va, n):
    return list(md.disasm(bytes(buf[va - IB:va - IB + n]), va))
def u32(va):
    return int.from_bytes(buf[va - IB:va - IB + 4], "little")

sj = json.load(io.open(os.path.join(HERE, "starts.json"), encoding="utf-8"))
allst = sorted(set(int(k, 16) for k in sj["atlas"]) | set(sj["targets"]))
atlas = {int(k, 16): v for k, v in sj["atlas"].items()}

def enclosing(va):
    i = bisect.bisect_right(allst, va) - 1
    for j in range(i, max(-1, i - 8), -1):
        s = allst[j]
        ins = dis(s, va - s + 16)
        if not ins or not any(x.address == va for x in ins):
            continue
        if any(x.mnemonic in ("ret", "retf") for x in ins if x.address < va):
            continue
        return s
    for back in range(1, 0x41):
        s = va - back
        p = s - 1
        npad = 0
        while p > 0x401000 and buf[p - IB] in (0x90, 0xCC):
            npad += 1
            p -= 1
        if npad == 0 or buf[p - IB] not in (0xC3, 0xC2, 0xCC):
            continue
        ins = dis(s, va - s + 16)
        if ins and any(x.address == va for x in ins) and \
           not any(x.mnemonic in ("ret", "retf") for x in ins if x.address < va):
            return s
    return None

def body(h):
    if h is None:
        return []
    n = (atlas.get(h) or 0x200) + 16
    return dis(h, n)

SITES = [0x401953, 0x4019BA, 0x47A9E3, 0x47AA10, 0x47AA3C, 0x535A8A, 0x697A47, 0x759532]
print("vt=007E1668 (CDFileClass) on-`this` install sites")
for s in SITES:
    h = enclosing(s)
    ins = body(h)
    txt = ["%s %s" % (x.mnemonic, x.op_str) for x in ins]
    has_delete_flag = any("test" in t and "[esp" in t and ", 1" in t for t in txt)
    calls_delete = any("0x7c8b3d" in t for t in txt)   # operator delete / free
    ret_imm = any(t.startswith("ret 0x") for t in txt)
    kind = "deleting-dtor" if (has_delete_flag and calls_delete) else ("ctor?" if not calls_delete else "other")
    print("  site=%08X host=%08X kind=%-15s delete_flag=%s del_call=%s retimm=%s"
          % (s, h or 0, kind, has_delete_flag, calls_delete, ret_imm))
    print("     head: %s" % "; ".join(txt[:8]))
