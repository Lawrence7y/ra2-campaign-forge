"""CLSID 映射：注册块中 (factory ctor -> CLSID)；CoCreateInstance 站点的 rclsid"""
import re, struct
import rt
from rt import im
from com2 import find_iat_calls, window, guid, COCREATE, COREG

ENTRIES = ["006C5210","006C5390","006C5510","006C5690","006C5810","006C5990",
           "006C5B10","006C5C90","006C5E10","006C5F90","006C6110"]
CTORS = {  # 由 ② / 产品构造独立得到的工厂构造器
 "006C5210":0x006C5140,"006C5390":0x006C52C0,"006C5510":0x006C5440,"006C5690":0x006C55C0,
 "006C5810":0x006C5740,"006C5990":0x006C58C0,"006C5B10":0x006C5A40,"006C5C90":0x006C5BC0,
 "006C5E10":0x006C5D40,"006C5F90":0x006C5EC0,"006C6110":0x006C6040}

def insns_from(va, n=120):
    return list(im.dis(va, n, stop_ret=False))

def call_sites_to(target):
    """e8/e9 rel32 指向 target"""
    out = []
    buf = bytes(im.buf)
    off = 0x401000
    while off < 0x7E038D - 5:
        b = buf[off-0x400000:(off-0x400000)+5]
        if len(b) == 5 and b[0] in (0xE8, 0xE9):
            rel = struct.unpack("<i", b[1:5])[0]
            if off + 5 + rel == target:
                out.append(off)
        off += 1
    return out

def clsid_after(callsite, n=40):
    """从 call 之后找第一个 push imm32 落在 .rdata 且形如 GUID 的值"""
    ins = insns_from(callsite, n)
    for i in ins[1:]:
        m = re.match(r"^0x([0-9a-f]+)$", i.op_str)
        if i.mnemonic == "push" and m:
            v = int(m.group(1), 16)
            if 0x7E1000 <= v < 0x812000:
                g = guid(v)
                if g and not g.startswith("{0000"):
                    return v, g, i.address
        if i.mnemonic.startswith("ret") or (i.mnemonic == "call" and i.address > callsite):
            break
    return None, None, None

def rclsid_of_site(site, n=16):
    w = window(site, n)
    last_push = None
    for i in w:
        if i.mnemonic == "push":
            last_push = i
    if last_push is None:
        return None, None, "no-push-found"
    m = re.match(r"^0x([0-9a-f]+)$", last_push.op_str)
    if m:
        v = int(m.group(1), 16)
        if 0x7E1000 <= v < 0x812000:
            return v, guid(v), f"{last_push.address:08X} push imm"
        return v, None, f"{last_push.address:08X} push imm(non-GUID)"
    return None, None, f"{last_push.address:08X} push {last_push.op_str} (寄存器/动态)"

if __name__ == "__main__":
    out = []
    out.append("## A. 工厂 → 注册 CLSID（CoRegisterClassObject 前的 push）")
    reg = {}
    for e, ct in CTORS.items():
        sites = call_sites_to(ct)
        for s in sites:
            cv, cg, at = clsid_after(s)
            out.append(f"  entry {e} ctor {ct:08X} called@{s:08X} -> CLSID {cg} (push@{at and f'{at:08X}'})")
            if e not in reg and cg:
                reg[e] = (cv, cg, s, at)
    out.append("")
    out.append("## B. CoCreateInstance 21 个站点的 rclsid")
    used = {}
    for s in find_iat_calls(COCREATE):
        v, g, how = rclsid_of_site(s)
        out.append(f"  site {s:08X} rclsid={g} [{how}]")
        if g:
            used.setdefault(g, []).append(s)
    out.append("")
    out.append("## C. 交集")
    for e in ENTRIES:
        if e in reg:
            g = reg[e][1]
            hit = used.get(g, [])
            out.append(f"  entry {e}  CLSID {g}  被 CoCreateInstance 使用于: {[f'{x:08X}' for x in hit]}")
    open("clsid_map.txt","w",encoding="utf-8").write("\n".join(out)+"\n")
    print("\n".join(out))
