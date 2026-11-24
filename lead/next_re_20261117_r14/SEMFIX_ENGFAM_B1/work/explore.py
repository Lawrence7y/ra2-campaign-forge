"""Explore: derive all anchors for slot 0067FDF0 from binary bytes only."""
from __future__ import annotations

import capstone
from semfix_lib import Bin, hx, hbytes

SAVE_CORE = 0x0067D300
CHAIN_END = 0x0067F000
SLOTS = [
    "0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
    "00680070", "006800F0", "00680170", "006801F0", "00680270",
    "006802F0", "00680370", "006803F0", "00680470", "006804F0",
    "00680570", "006805F0", "00680670", "006806F0", "00680770",
    "006807F0", "00680870", "006808F0", "00680970", "006809F0",
    "00680A70", "00680AF0", "00680B70", "00680BF0", "00680C70",
    "00680CF0", "00680D70", "00680DF0", "00680E70", "00680EF0",
]


def unit():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


def scan_e8(b: Bin, targets: set[int]):
    data = b.text_bytes()
    hits = {t: [] for t in targets}
    for i, byte in enumerate(data):
        if byte != 0xE8 or i + 5 > len(data):
            continue
        site = b.text_start + i
        rel = int.from_bytes(data[i + 1:i + 5], "little", signed=True)
        tgt = site + 5 + rel
        if tgt in hits:
            hits[tgt].append(site)
    return hits


def scan_c705(b: Bin):
    """{dst: [(site, imm)]} for C7 05 dst32 imm32"""
    data = b.text_bytes()
    idx = {}
    i = 0
    while True:
        i = data.find(b"\xC7\x05", i)
        if i < 0 or i + 10 > len(data):
            break
        dst = int.from_bytes(data[i + 2:i + 6], "little")
        imm = int.from_bytes(data[i + 6:i + 10], "little")
        idx.setdefault(dst, []).append((b.text_start + i, imm))
        i += 1
    return idx


def body(b: Bin, va: int, maxlen=0x90):
    out = []
    for ins in unit().disasm(b.data(va, maxlen), va):
        out.append(ins)
        if ins.mnemonic in ("ret", "retf"):
            nxt = ins.address + ins.size
            if b.data(nxt, 1)[0] in (0x90, 0xCC, 0x00):
                break
    return out


def main():
    b = Bin()
    print("text", hex(b.text_start), hex(b.text_end))
    slot_vas = {int(s, 16): s for s in SLOTS}
    calls = scan_e8(b, set(slot_vas))
    c705 = scan_c705(b)

    # Save_Core chain: track mov edx,imm before each slot call
    insns = list(unit().disasm(b.data(SAVE_CORE, CHAIN_END - SAVE_CORE), SAVE_CORE))
    last_edx = None
    chain = {}
    for ins in insns:
        if ins.mnemonic == "mov" and ins.op_str.startswith("edx,"):
            op = ins.operands[1]
            if op.type == capstone.x86.X86_OP_IMM:
                last_edx = (op.imm, ins.address)
        elif ins.mnemonic == "call":
            op = ins.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and op.imm in slot_vas:
                chain[op.imm] = (ins.address, last_edx)

    # ---- dump slot 0067FDF0 ----
    e = 0x0067FDF0
    print(f"\n===== SLOT {hx(e)} =====")
    print(f"E8 call sites: {[hx(x) for x in calls.get(e, [])]}")
    print(f"chain: call_site={hx(chain[e][0])} edx={hx(chain[e][1][0])}@{hx(chain[e][1][1])}")
    vec = chain[e][1][0]
    print(f"vector bss? {b.is_bss_va(vec)} section={b.sec_of(vec)['name'] if b.sec_of(vec) else None}")
    print(f"C7 05 writes to vec {hx(vec)}: {[(hx(s), hx(v)) for s, v in c705.get(vec, [])]}")

    print("\n--- function body ---")
    ins = body(b, e)
    for x in ins:
        print(f"  {hx(x.address)}  {hbytes(x.bytes):<24} {x.mnemonic} {x.op_str}")

    # focus anchors
    print("\n--- eax checks / xor / ret ---")
    for i, x in enumerate(ins):
        if x.mnemonic in ("test", "cmp") and x.op_str.replace(" ", "").startswith("eax,"):
            print(f"  CHECK {hx(x.address)} {x.mnemonic} {x.op_str}", end="")
            if i + 1 < len(ins) and ins[i + 1].mnemonic.startswith("j"):
                nx = ins[i + 1]
                tgt = nx.operands[0].imm if nx.operands and nx.operands[0].type == capstone.x86.X86_OP_IMM else None
                print(f" -> {hx(nx.address)} {nx.mnemonic} {hx(tgt) if tgt else nx.op_str}")
            else:
                print()
        if x.mnemonic == "xor" and x.op_str.replace(" ", "") == "eax,eax":
            print(f"  XOR   {hx(x.address)} {x.mnemonic} {x.op_str}")
        if x.mnemonic == "ret":
            print(f"  RET   {hx(x.address)}")

    # caller consumption in Save_Core after the slot call
    cs = chain[e][0]
    print(f"\n--- caller consumption after call {hx(cs)} ---")
    for x in ins:
        pass
    after = list(unit().disasm(b.data(cs + 5, 0x40), cs + 5))
    for x in after:
        if x.mnemonic in ("test", "cmp") and "eax" in x.op_str:
            print(f"  {hx(x.address)} {x.mnemonic} {x.op_str}")
            for y in after[after.index(x) + 1:after.index(x) + 3]:
                print(f"    -> {hx(y.address)} {y.mnemonic} {y.op_str}")
            break


if __name__ == "__main__":
    main()
