# -*- coding: utf-8 -*-
"""PATCH-D35R step3: build gamemd_r2.exe from the ORIGINAL exe.

Diff set (vs original) is exactly:
  {cave [0x3DF781,0x3DF7C0)} UNION {8 site windows [site_off, site_off+5)}
No other byte may change.

Cave payload (63B):
  +0..+30  : 30B instrumented shared stub
             (record caller ret-addr + hit count, then PATCH_D35 guard logic)
  +30..+49 : 19B block guard (same logic as PATCH_D35, relocs recomputed)
  +49..+63 : 0xCC (int3)

Counter memory (.data zero-fill; NO file bytes -> no diff impact):
  0x009F5000 : last caller return address (site VA + 5)
  0x009F5004 : total stub hit count
"""
import hashlib, os, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

SRC = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work"
DST = os.path.join(OUTDIR, "gamemd_r2.exe")
EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE"

IB = 0x400000
CAVE_VA, CAVE_OFF, CAVE_LEN = 0x7DF781, 0x3DF781, 63
CALLEE = 0x724730
SITE_S6_CONT = 0x6CD8C7
SITE_S6_JOIN = 0x6CD8D8
CTR_LAST, CTR_COUNT = 0x009F5000, 0x009F5004
SITES = [0x6D1632, 0x6D09FA, 0x640427, 0x6D059B,
         0x6D0634, 0x6D1293, 0x6D0940, 0x4A8B75]

def fo(va):
    return va - IB

def rel32(target, insn_va, insn_len=5):
    return (target - (insn_va + insn_len)) & 0xFFFFFFFF

def main():
    orig = bytearray(open(SRC, "rb").read())
    buf = bytearray(orig)

    assert bytes(orig[CAVE_OFF:CAVE_OFF+CAVE_LEN]) == b"\xCC"*63
    assert orig[CAVE_OFF-1] == 0xC3
    for s in SITES:
        o = fo(s)
        assert orig[o] == 0xE8, f"site {s:#x} not E8: {orig[o]:02X}"
        tgt = (s+5 + int.from_bytes(orig[o+1:o+5], "little", signed=True)) & 0xFFFFFFFF
        assert tgt == CALLEE

    # ---- 30B instrumented stub @ cave+0 (VA 0x7DF781) ----
    stub = bytearray()
    stub += bytes.fromhex("50")                        # +0  push eax            (save)
    stub += bytes.fromhex("8B442404")                  # +1  mov eax,[esp+4]     ; call return addr (site+5)
    stub += b"\xA3" + struct.pack("<I", CTR_LAST)      # +5  mov [CTR_LAST],eax  ; last caller ret
    stub += b"\xFF\x05" + struct.pack("<I", CTR_COUNT) # +10 inc dword [CTR_COUNT]
    stub += bytes.fromhex("58")                        # +16 pop eax            (restore)
    stub += bytes.fromhex("85C9")                      # +17 test ecx,ecx
    stub += bytes.fromhex("7405")                      # +19 jz +5 -> +26 (add esp,4)
    stub += b"\xE9" + struct.pack("<I", rel32(CALLEE, CAVE_VA+21))  # +21 jmp 0x724730 (tail)
    stub += bytes.fromhex("83C404")                    # +26 add esp,4          (NULL path)
    stub += bytes.fromhex("C3")                        # +29 ret
    assert len(stub) == 30, len(stub)
    assert stub[19] == 0x74 and stub[20] == 0x05

    # ---- 19B block guard @ cave+30 (VA 0x7DF79F) ----
    bg_va = CAVE_VA + 30
    bg = bytearray()
    bg += bytes.fromhex("A1E0718800")                  # mov eax,[0x8871E0]
    bg += bytes.fromhex("85C0")                        # test eax,eax
    bg += bytes.fromhex("7405")                        # jz +5
    bg += b"\xE9" + struct.pack("<I", rel32(SITE_S6_CONT, bg_va+9))
    bg += b"\xE9" + struct.pack("<I", rel32(SITE_S6_JOIN, bg_va+14))
    assert len(bg) == 19

    payload = bytes(stub) + bytes(bg)
    assert len(payload) == 49
    for i, b in enumerate(payload):
        buf[CAVE_OFF + i] = b

    # ---- site wiring ----
    site_info = []
    for s in SITES:
        o = fo(s)
        newrel = rel32(CAVE_VA, s)
        buf[o+1:o+5] = struct.pack("<I", newrel)
        site_info.append((s, o, bytes(orig[o:o+5]), bytes(buf[o:o+5])))

    # ---- strict full-file diff ----
    diffs = [i for i in range(len(orig)) if orig[i] != buf[i]]
    cave_set = set(range(CAVE_OFF, CAVE_OFF+CAVE_LEN))
    site_set = set()
    for s in SITES:
        site_set.update(range(fo(s), fo(s)+5))
    allowed = cave_set | site_set
    outside = [i for i in diffs if i not in allowed]

    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(EV, exist_ok=True)
    open(DST, "wb").write(buf)

    with open(os.path.join(EV, "hashes.txt"), "w") as f:
        f.write(f"orig_gamemd_sha256={hashlib.sha256(bytes(orig)).hexdigest().upper()}\n")
        f.write(f"r2_copy_sha256={hashlib.sha256(bytes(buf)).hexdigest().upper()}\n")
        f.write(f"orig_size={len(orig)}\nr2_size={len(buf)}\n")
        f.write(f"total_diff_bytes={len(diffs)}\n")
        f.write(f"cave_diff_bytes={sum(1 for i in diffs if i in cave_set)}\n")
        f.write(f"site_diff_bytes={sum(1 for i in diffs if i in site_set)}\n")
        f.write(f"outside_allowed_set_diff_count={len(outside)}\n")
        f.write(f"outside_offsets={[hex(i) for i in outside]}\n")
        f.write(f"allowed_cave=[0x{CAVE_OFF:x},0x{CAVE_OFF+CAVE_LEN:x})\n")
        f.write(f"allowed_sites={[f'0x{fo(s):x}..0x{fo(s)+5:x}' for s in SITES]}\n")

    with open(os.path.join(EV, "byte_diff_full.tsv"), "w") as f:
        f.write("offset_hex\tVA_hex\toriginal\tpatched\tregion\n")
        for i in diffs:
            reg = "CAVE" if i in cave_set else ("SITE" if i in site_set else "OUTSIDE!!")
            f.write(f"0x{i:x}\t0x{0x400000+i:x}\t{orig[i]:02X}\t{buf[i]:02X}\t{reg}\n")

    with open(os.path.join(EV, "sites_wired.tsv"), "w") as f:
        f.write("site_VA\tfile_off\torig_5B\tnew_5B\tnew_target\tnew_rel32\n")
        for s, o, ob, nb in site_info:
            rel = int.from_bytes(nb[1:5], "little")
            f.write(f"0x{s:x}\t0x{o:x}\t{ob.hex(' ')}\t{nb.hex(' ')}\t0x{CAVE_VA:x}\t0x{rel:x}\n")

    with open(os.path.join(EV, "cave_r2.txt"), "w") as f:
        f.write(f"CAVE VA [0x7DF781,0x7DF7C0) file [0x3DF781,0x3DF7C0) len=63\n")
        f.write("STUB (30B):       " + " ".join(f"{b:02X}" for b in stub) + "\n")
        f.write("BLOCK GUARD (19B): " + " ".join(f"{b:02X}" for b in bg) + "\n")
        f.write("AFTER (63B):      " + " ".join(f"{b:02X}" for b in buf[CAVE_OFF:CAVE_OFF+63]) + "\n")
        f.write(f"counter_last_VA=0x{CTR_LAST:x} counter_count_VA=0x{CTR_COUNT:x}\n")

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    dlines = ["=== STUB @0x7DF781 ==="]
    for i in md.disasm(bytes(stub), CAVE_VA):
        dlines.append(f"  0x{i.address:x}: {i.bytes.hex(' '):<26} {i.mnemonic} {i.op_str}")
    dlines.append("=== BLOCK GUARD @0x7DF79F ===")
    for i in md.disasm(bytes(bg), bg_va):
        dlines.append(f"  0x{i.address:x}: {i.bytes.hex(' '):<26} {i.mnemonic} {i.op_str}")
    with open(os.path.join(EV, "stub_disasm.txt"), "w") as f:
        f.write("\n".join(dlines) + "\n")

    print("orig sha  =", hashlib.sha256(bytes(orig)).hexdigest().upper())
    print("r2 sha    =", hashlib.sha256(bytes(buf)).hexdigest().upper())
    print("total diffs=", len(diffs), "cave=", sum(1 for i in diffs if i in cave_set),
          "site=", sum(1 for i in diffs if i in site_set), "OUTSIDE=", len(outside))
    print("outside =", [hex(i) for i in outside])
    print("\n".join(dlines))
    print("OK" if not outside else "FAIL")

if __name__ == "__main__":
    main()
