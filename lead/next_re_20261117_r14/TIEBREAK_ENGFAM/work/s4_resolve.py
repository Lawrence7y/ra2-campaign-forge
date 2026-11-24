"""s4: resolve the external identities and the caller side.

  * import directory walk -> name for IAT slot 0x7E15F4 (no pefile)
  * 16 bytes at 0x7F7C80 rendered as a GUID  (the QI IID)
  * Save_Core 0x67D300: full disassembly, every `call` whose target is one of
    the 35 slots (gives the edx argument = which .bss vector each slot receives)
  * for each of the 6 sampled rows: the constructor write that installs the
    DynamicVectorClass<T> vtable into that .bss vector, read as raw bytes, and
    the RTTI name resolved independently from that vtable
"""
import json
import struct

import capstone

import pe

SLOTS = ["0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
         "00680070", "006800F0", "00680170", "006801F0", "00680270",
         "006802F0", "00680370", "006803F0", "00680470", "006804F0",
         "00680570", "006805F0", "00680670", "006806F0", "00680770",
         "006807F0", "00680870", "006808F0", "00680970", "006809F0",
         "00680A70", "00680AF0", "00680B70", "00680BF0", "00680C70",
         "00680CF0", "00680D70", "00680DF0", "00680E70", "00680EF0"]
SAMPLE = ["0067FDF0", "006800F0", "00680470", "006807F0", "00680B70", "00680EF0"]
SAVE_CORE = 0x0067D300
IAT_OLE = 0x007E15F4
IID_QI = 0x007F7C80

# constructor install sites for the .bss vector, as *addresses to read* (the
# audited party lists them; I only use the address and decode the bytes myself)
CTOR = {
    "0067FDF0": 0x004E6E7D, "006800F0": 0x004E697D, "00680470": 0x004E71FD,
    "006807F0": 0x004E78FD, "00680B70": 0x004A6C8D, "00680EF0": 0x0065B17D,
}


def unit(detail=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = detail
    m.skipdata = True
    return m


def imports(p):
    """Walk IMAGE_IMPORT_DESCRIPTOR list; return {iat_slot_va: 'dll!func'}."""
    out = {}
    rva, size = p.dd[1]
    va = p.image_base + rva
    k = 0
    while True:
        ilt, _ts, _fc, name_rva, iat = struct.unpack_from("<IIIII", p.buf, p.off(va + 20 * k, 20))
        if ilt == 0 and name_rva == 0 and iat == 0:
            break
        dll = p.cstr(p.image_base + name_rva)
        t = p.image_base + (ilt or iat)
        j = 0
        while True:
            v = p.u32(t + 4 * j)
            if v == 0:
                break
            if v & 0x80000000:
                nm = f"ord_{v & 0xFFFF}"
            else:
                nm = p.cstr(p.image_base + v + 2)
            out[p.image_base + iat + 4 * j] = f"{dll}!{nm}"
            j += 1
        k += 1
    return out


def guid(p, va):
    d = p.raw(va, 16)
    a, b, c = struct.unpack_from("<IHH", d, 0)
    tail = d[8:]
    return (f"{{{a:08X}-{b:04X}-{c:04X}-{tail[0]:02X}{tail[1]:02X}-"
            + "".join(f"{x:02X}" for x in tail[2:]) + "}")


def dis(p, va, n):
    return list(unit().disasm(p.raw(va, n), va))


def save_core(p):
    print("\n==== Save_Core 0x67D300 -- call sites into the 35 slots")
    insns = dis(p, SAVE_CORE, 0x200)
    slot_va = {int(s, 16): s for s in SLOTS}
    found = []
    for i, ins in enumerate(insns):
        if ins.mnemonic != "call":
            continue
        op = ins.operands[0]
        if op.type != capstone.x86.X86_OP_IMM:
            continue
        tgt = op.imm
        if tgt in slot_va:
            # the edx argument is set by the nearest preceding mov edx,imm32
            arg = None
            for prev in reversed(insns[:i]):
                if prev.mnemonic == "mov" and prev.op_str.startswith("edx,"):
                    v = prev.operands[1]
                    if v.type == capstone.x86.X86_OP_IMM:
                        arg = dict(va=v.imm, at=prev.address,
                                   bytes=prev.bytes.hex(), txt=prev.op_str)
                    break
            found.append(dict(entry=slot_va[tgt], slot=f"{tgt:08X}",
                              site=f"{ins.address:08X}",
                              bytes=ins.bytes.hex(), edx=arg))
    print(f"  {len(insns)} instructions swept; {len(found)} call sites found")
    for f in found:
        e = f["edx"]
        print(f"  {f['entry']}  0x{f['slot']} <- call @0x{f['site']} "
              f"[{f['bytes']}]  edx=.bss 0x{e['va']:08X} "
              f"(mov @0x{e['at']:08X} [{e['bytes']}] {e['txt']})"
              if e else f"  {f['entry']} call @0x{f['site']} edx=UNKNOWN")
    return found


def ctor_check(p, entry, site):
    print(f"\n---- {entry}: constructor vector install @0x{site:08X}")
    ins = dis(p, site, 10)[0]
    print(f"  {site:08X}  {' '.join(f'{b:02X}' for b in ins.bytes):<24} "
          f"{ins.mnemonic} {ins.op_str}")
    dst = ins.operands[0]
    src = ins.operands[1]
    vec = dst.mem.disp
    vt = src.imm
    print(f"  -> writes vt 0x{vt:08X} into .bss 0x{vec:08X}")
    r = p.rtti(vt)
    print(f"  RTTI: COL=0x{r['col']:08X} TD=0x{r['td']:08X} "
          f"TD+8=0x{r['td'] + 8:08X} name={r.get('name')!r}")
    # also show the name bytes on the wire
    nm = r.get("name")
    if nm:
        print(p.hexdump(r["td"] + 8, min(len(nm) + 1, 64)))
    # vtable slot 0/2/4 for reference
    for sl in (0, 4, 8, 12, 16):
        print(f"    vt+0x{sl:02X} = 0x{p.u32(vt + sl):08X}")
    return dict(entry=entry, site=f"{site:08X}", vt=vt, vec=vec,
                col=r["col"], td=r["td"], name=r.get("name"))


def main():
    p = pe.open_pe()
    imps = imports(p)
    print("import directory:", len(imps), "thunks")
    print(f"IAT slot 0x{IAT_OLE:08X} ->", imps.get(IAT_OLE, "NOT FOUND"))
    # slots around it, for context
    for d in range(-4, 40, 4):
        v = imps.get(IAT_OLE + d)
        if v:
            print(f"  0x{IAT_OLE + d:08X}  {v}")
    print(f"\nIID constant @0x{IID_QI:08X} {p.raw(IID_QI, 16).hex()} -> "
          + guid(p, IID_QI))
    print("raw:", p.hexdump(IID_QI, 16))
    found = save_core(p)
    cs = {}
    for e in SAMPLE:
        cs[e] = ctor_check(p, e, CTOR[e])
    with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
              r"\TIEBREAK_ENGFAM\EVIDENCE\resolve.json", "w") as f:
        json.dump(dict(iat_ole=imps.get(IAT_OLE), iid=guid(p, IID_QI),
                       call_sites=found, ctor=cs), f, indent=1)


if __name__ == "__main__":
    main()
