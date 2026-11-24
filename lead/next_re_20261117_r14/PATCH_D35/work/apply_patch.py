# -*- coding: utf-8 -*-
"""PATCH-D35 step3: write 13B shared stub + 19B block guard into the 63B int3 cave.
CAVE (card-bound): only bytes inside [0x7DF781, 0x7DF7C0) may change.
Verifies byte-for-byte that all differences lie inside the cave.
"""
import hashlib
import pefile

SRC = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DST = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35\work\gamemd_patched.exe"
CAVE_VA, CAVE_OFF, CAVE_LEN = 0x7DF781, 0x3DF781, 63
IMAGEBASE = 0x400000
CALLEE = 0x724730            # ret 4 thiscall callee
SITE_S6_MOV = 0x6CD8C2       # A1 E0 71 88 00  mov eax,[0x8871E0]
SITE_S6_CONT = 0x6CD8C7      # 6A 00 ... continue original block
SITE_S6_JOIN = 0x6CD8D8      # join point after the guarded block

def rel32(target, from_va, insn_len=5):
    return (target - (from_va + insn_len)) & 0xFFFFFFFF

def main():
    orig = open(SRC, "rb").read()
    buf = bytearray(orig)

    # --- preconditions on original bytes ---
    assert buf[CAVE_OFF:CAVE_OFF+CAVE_LEN] == b"\xCC"*63, "cave not 63x CC"
    assert buf[CAVE_OFF-1] == 0xC3, "predecessor 0x7DF780 not ret"
    assert bytes(buf[0x6CD8C2-IMAGEBASE+0:0]) == b""  # noop
    # file offset of 0x6CD8C2 = RVA 0x2CD8C2 (section .text: VA=0x1000,Raw=0x1000)
    off_s6 = 0x6CD8C2 - IMAGEBASE  # == 0x2CD8C2 ; .text VA==RawPtr so offset==RVA
    assert off_s6 == 0x2CD8C2
    assert bytes(buf[off_s6:off_s6+5]) == bytes.fromhex("A1E0718800"), \
        "site 0x6CD8C2 not A1 E0 71 88 00: " + bytes(buf[off_s6:off_s6+5]).hex()

    # --- 13B shared stub @ cave+0 ---
    stub_va = CAVE_VA
    stub = bytearray()
    stub += bytes.fromhex("85C9")            # test ecx,ecx
    stub += bytes.fromhex("7405")            # jz +5 -> add esp,4 (cave+9)
    stub += b"\xE9" + rel32(CALLEE, stub_va+4).to_bytes(4, "little")  # jmp 0x724730 (tail)
    stub += bytes.fromhex("83C404")          # add esp,4
    stub += b"\xC3"                          # ret
    assert len(stub) == 13, len(stub)

    # --- 19B block guard @ cave+13 ---
    block_va = CAVE_VA + 13
    block = bytearray()
    block += bytes.fromhex("A1E0718800")     # mov eax,[0x8871E0] (replay overwritten site insn)
    block += bytes.fromhex("85C0")           # test eax,eax
    block += bytes.fromhex("7405")           # jz +5 -> null path (block+14)
    block += b"\xE9" + rel32(SITE_S6_CONT, block_va+9).to_bytes(4, "little")  # jmp 0x6CD8C7 (non-null)
    block += b"\xE9" + rel32(SITE_S6_JOIN, block_va+14).to_bytes(4, "little") # jmp 0x6CD8D8 (null)
    assert len(block) == 19, len(block)

    payload = bytes(stub) + bytes(block)     # 32B
    assert len(payload) == 32
    for i, b in enumerate(payload):
        buf[CAVE_OFF + i] = b

    open(DST, "wb").write(buf)

    # --- verification ---
    new = open(DST, "rb").read()
    assert len(new) == len(orig)
    diffs = [i for i in range(len(orig)) if orig[i] != new[i]]
    outside = [i for i in diffs if not (CAVE_OFF <= i < CAVE_OFF + CAVE_LEN)]
    print("stub  =", stub.hex(" "))
    print("block =", block.hex(" "))
    print("rel32 jmp->0x724730 =", hex(int.from_bytes(stub[5:9], "little")))
    print("rel32 jmp->0x6CD8C7 =", hex(int.from_bytes(block[10:14], "little")))
    print("rel32 jmp->0x6CD8D8 =", hex(int.from_bytes(block[15:19], "little")))
    print("total diffs =", len(diffs))
    print("diff offset set =", [hex(i) for i in diffs])
    print("diff VA set =", [hex(IMAGEBASE+i) for i in diffs])
    print("OUTSIDE-CAVE diffs =", len(outside), [hex(i) for i in outside])
    print("cave tail (remaining int3) =",
          sum(1 for b in new[CAVE_OFF+32:CAVE_OFF+63] if b == 0xCC), "/31")
    print("orig sha256 =", hashlib.sha256(orig).hexdigest().upper())
    print("patched sha256 =", hashlib.sha256(new).hexdigest().upper())

if __name__ == "__main__":
    main()
