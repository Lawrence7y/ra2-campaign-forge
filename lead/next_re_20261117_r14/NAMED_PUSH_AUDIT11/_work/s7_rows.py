import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

ENTRIES = ["006C2B10", "006C2C90", "006C2E10", "006C2F90", "006C3110", "006C3290",
           "006C3410", "006C3590", "006C3890", "006C3A10", "006C3B90"]

# --- helper: linear disasm to function end (first ret that returns, then padding) ---
def body(va, maxb=400):
    ins = dis(va, maxb)
    out = []
    for i in ins:
        if i.mnemonic == "nop":
            break
        out.append(i)
    return out


def find_vt_installs(vt):
    """all `mov dword ptr [reg(+disp)], imm==vt` sites in .text"""
    name, sva, vsz, rawsz, raw = sec_of(0x401000)
    blob = DATA[raw:raw + rawsz]
    needle = vt.to_bytes(4, "little")
    res = []
    p = blob.find(needle)
    while p >= 0:
        va = sva + p
        # look back for opcode c7 (mov r/m32, imm32)
        for back in range(2, 10):
            if va - back - sva < 0:
                continue
            if (va - back - sva) < len(blob) and blob[p - back] == 0xC7:
                res.append((va))
                break
        p = blob.find(needle, p + 1)
    return res


rows = []
for e in ENTRIES:
    va = int(e, 16)
    r = {"entry": e}
    ins = body(va)
    r["n_insn"] = len(ins)
    r["first_bytes"] = hexs(va, 8)
    r["body"] = [fmt(i) for i in ins]
    imms = [(i.address, i.op_str) for i in ins if i.mnemonic == "mov" and i.op_str.startswith("eax, 0x8")]
    r["guard_imms"] = [(f"{a:08X}", s) for a, s in imms]
    # indirect QI call: call dword ptr [reg] (no disp)
    qis = [i for i in ins if i.mnemonic == "call" and i.op_str == "dword ptr [eax]"]
    r["call_eax_sites"] = [f"{i.address:08X} {i.bytes.hex(' ')}" for i in qis]
    # direct call targets
    calls = [i for i in ins if i.mnemonic == "call" and i.op_str.startswith("0x")]
    r["direct_calls"] = [(f"{i.address:08X}", i.op_str, i.bytes.hex(" ")) for i in calls]
    # test/jge
    tests = [(i.address, i.mnemonic, i.op_str, i.bytes.hex(" ")) for i in ins
             if i.mnemonic in ("test", "jge", "jl", "jns", "js")]
    r["tests"] = [(f"{a:08X}", m, o, b) for a, m, o, b in tests]
    rows.append(r)

with open("rows_facts.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

for r in rows:
    print("=" * 110)
    print(f"ENTRY {r['entry']} n_insn={r['n_insn']} first={r['first_bytes']}")
    for b in r["body"]:
        print("   " + b)
    print("  guards:", r["guard_imms"])
    print("  call [eax]:", r["call_eax_sites"])
    print("  direct calls:", r["direct_calls"])
