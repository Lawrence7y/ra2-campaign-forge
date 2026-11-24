"""找 ole32 CoCreateInstance / CoRegisterClassObject 调用点，并解析其 CLSID 实参"""
import re, struct
import rt
from rt import im

COCREATE = 0x007E15FC
COREGISTER = 0x007E15D8

def find_iat_calls(iat):
    pat = b"\xff\x15" + struct.pack("<I", iat)
    buf = bytes(im.buf)
    out = []
    k = buf.find(pat, 0x1000 - 0x400000 if False else 0)
    start = 0x1000
    while True:
        k = buf.find(pat, start)
        if k < 0: break
        out.append(0x400000 + k)
        start = k + 1
    return [a for a in out if 0x401000 <= a < 0x7E038D]

def back_disasm(va, n=120):
    """从 va 前 n 字节线性反汇编到 va，粗略回溯"""
    s = va - n
    insns = list(im.dis(s, 400, stop_ret=False))
    keep = [i for i in insns if i.address <= va]
    return keep[-30:]

def guid(v):
    d = im.rd(v, 16)
    if len(d) < 16: return None
    d1, d2, d3 = struct.unpack("<IHH", d[:8])
    rest = d[8:]
    return "{%08X-%04X-%04X-%s-%s}" % (d1, d2, d3, rest[:2].hex().upper(), rest[2:].hex().upper())

if __name__ == "__main__":
    for name, iat in (("CoCreateInstance", COCREATE), ("CoRegisterClassObject", COREGISTER)):
        sites = find_iat_calls(iat)
        print(f"### {name} IAT={iat:08X}  call sites = {len(sites)}")
        for s in sites:
            print(f"\n--- site {s:08X} ---")
            for i in back_disasm(s, 100):
                mark = " <<<" if i.address == s else ""
                print(f"  {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic:<7} {i.op_str}{mark}")
        print()
