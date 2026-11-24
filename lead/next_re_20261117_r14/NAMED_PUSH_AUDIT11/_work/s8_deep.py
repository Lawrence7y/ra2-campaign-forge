import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

ENTRIES = ["006C2B10", "006C2C90", "006C2E10", "006C2F90", "006C3110", "006C3290",
           "006C3410", "006C3590", "006C3890", "006C3A10", "006C3B90"]


def body(va, maxb=400):
    out = []
    for i in dis(va, maxb):
        if i.mnemonic == "nop":
            break
        out.append(i)
    return out


def is_text_fn(v):
    s = sec_of(v) if v else None
    return bool(s) and s[0] == ".text" and 0x401000 <= v < 0x7E038D


def vt_base_for(slot_va):
    """walk back in 4-byte steps while the words are .text fn pointers; vt base is
    the first word after the COL pointer (i.e. the word at base-4 is NOT a .text fn)."""
    cur = slot_va
    while True:
        prev = cur - 4
        w = u32(prev)
        if not is_text_fn(w):
            return cur
        cur = prev


def vt_layout(vt_va, n=10):
    out = []
    for k in range(n):
        out.append((k, u32(vt_va + 4 * k)))
    return out


def rtti_class(vt_va):
    """strict COL check: col ptr in .rdata, sig pattern, [col+0xC]=TD, TD+8 string .?A"""
    d = {"vt": vt_va}
    col = u32(vt_va - 4)
    d["col"] = col
    if not col:
        return d
    s = sec_of(col)
    d["col_sec"] = s[0] if s else None
    td = u32(col + 0xC)
    d["td"] = td
    if not td:
        return d
    s = sec_of(td)
    d["td_sec"] = s[0] if s else None
    nm = cstr(td + 8, 300)
    d["name"] = nm
    d["name_ok"] = bool(nm and nm.startswith(".?A"))
    return d


def find_imm_writers(imm, window=442000):
    """all sites whose bytes contain c7 <modrm> imm32 (mov r/m32,imm) with imm == imm"""
    name, sva, vsz, rawsz, raw = sec_of(0x401000)
    blob = DATA[raw:raw + rawsz]
    res = []
    for i in range(len(blob) - 10):
        if blob[i] == 0xC7 and blob[i + 1] in (0x00, 0x01, 0x02, 0x03, 0x06, 0x07,
                                               0x40, 0x41, 0x42, 0x43, 0x46, 0x47,
                                               0x44, 0x45):
            # c7 /0 with mod=00/01/10 and rm!=4/5 handled roughly: imm at i+2 (mod00) or i+3 (mod01) or i+6..7
            for offi, tag in ((2, "mod00"), (3, "mod01"), (6, "mod10")):
                if i + offi + 4 <= len(blob):
                    v = int.from_bytes(blob[i + offi:i + offi + 4], "little")
                    if v == imm:
                        res.append((sva + i, tag))
    # dedupe
    seen = set()
    out = []
    for a, t in res:
        if (a, t) in seen:
            continue
        seen.add((a, t))
        out.append((a, t))
    return out


def analyze(entry_hex):
    va = int(entry_hex, 16)
    d = {"entry": entry_hex}
    ins = body(va)
    d["n_insn"] = len(ins)
    d["body"] = [fmt(i) for i in ins]

    # ---- ring ② : find slot ----
    name, sva, vsz, rawsz, raw = sec_of(0x401000)
    blob = DATA[raw:raw + rawsz]
    needle = va.to_bytes(4, "little")
    slots = []
    p = blob.find(needle)
    while p >= 0:
        slots.append(sva + p)
        p = blob.find(needle, p + 1)
    # also .rdata/.data occurrences
    for secname in (".rdata", ".data"):
        s = [x for x in SECTIONS if x[0] == secname][0]
        b2 = DATA[s[4]:s[4] + s[3]]
        p = b2.find(needle)
        while p >= 0:
            slots.append(s[1] + p)
            p = b2.find(needle, p + 1)
    d["va_slots_all"] = [f"{x:08X}" for x in slots]
    rdata_slots = [x for x in slots if sec_of(x) and sec_of(x)[0] == ".rdata"]
    d["slots_rdata"] = [f"{x:08X}" for x in rdata_slots]
    if rdata_slots:
        slot = rdata_slots[0]
        base = vt_base_for(slot)
        d["vt"] = f"{base:08X}"
        d["slot"] = f"{slot:08X}"
        d["slot_no"] = (slot - base) // 4
        d["vt_slots"] = [(k, f"{v:08X}" if v else None) for k, v in vt_layout(base, 8)]
        d["rtti"] = rtti_class(base)
        d["vt_slot0_is_410260"] = (u32(base) == 0x410260)
        # who installs this factory vt?
        d["vt_install_sites"] = [f"{a:08X} {t}" for a, t in find_imm_writers(base)]

    # ---- ring ③ : guards / main site / branch ----
    d["guard_imms"] = [(f"{i.address:08X}", i.op_str, i.bytes.hex(" ")) for i in ins
                       if i.mnemonic == "mov" and i.op_str.startswith("eax, 0x8")]
    d["qi_call"] = [(f"{i.address:08X}", i.bytes.hex(" ")) for i in ins
                    if i.mnemonic == "call" and i.op_str == "dword ptr [eax]"]
    d["branch_after_qi"] = []
    for idx, i in enumerate(ins):
        if i.mnemonic == "call" and i.op_str == "dword ptr [eax]":
            for j in ins[idx + 1:idx + 8]:
                d["branch_after_qi"].append(fmt(j))
    d["fail_path_call"] = [(f"{i.address:08X}", i.op_str, i.bytes.hex(" ")) for i in ins
                           if i.mnemonic == "call" and i.op_str.startswith("dword ptr [edx")]
    d["push_1_sites"] = [(f"{i.address:08X}", i.bytes.hex(" ")) for i in ins
                         if i.mnemonic == "push" and i.op_str == "1"]

    # ---- created object ctor ----
    ctors = [(f"{i.address:08X}", i.op_str) for i in ins
             if i.mnemonic == "call" and i.op_str.startswith("0x") and i.op_str != "0x7c8e17"]
    d["alloc_ctor_sites"] = ctors
    if ctors:
        ctor = int(ctors[0][1], 16)
        d["obj_ctor"] = f"{ctor:08X}"
        ci = dis(ctor, 80)
        d["obj_ctor_body"] = [fmt(x) for x in ci]
        # find mov [reg], imm vt  inside this ctor
        inm = [x for x in ci if x.mnemonic == "mov" and x.op_str.startswith("dword ptr [") and ", 0x7" in x.op_str]
        vts = []
        for x in inm:
            imm = int(x.op_str.split(",")[-1].strip(), 16)
            vts.append((f"{x.address:08X}", f"{imm:08X}", x.bytes.hex(" ")))
        d["obj_ctor_vt_writes"] = vts
        # follow one more level (ctor may tail-call another ctor)
        sub = [x for x in ci if x.mnemonic in ("call", "jmp") and x.op_str.startswith("0x")]
        d["obj_ctor_outcalls"] = [(f"{x.address:08X}", x.mnemonic, x.op_str) for x in sub]
        for x in sub:
            t = int(x.op_str, 16)
            if not is_text_fn(t):
                continue
            si = dis(t, 140)
            vts2 = []
            for y in si:
                if y.mnemonic == "mov" and y.op_str.startswith("dword ptr [") and ", 0x7" in y.op_str:
                    imm = int(y.op_str.split(",")[-1].strip(), 16)
                    vts2.append((f"{y.address:08X}", f"{imm:08X}", y.bytes.hex(" ")))
            if vts2:
                d.setdefault("obj_ctor_sub_vt", []).append(
                    {"fn": f"{t:08X}", "vts": vts2, "n_insn": len(si)})
    return d


rows = [analyze(e) for e in ENTRIES]
with open("deep.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

for r in rows:
    print("=" * 118)
    print(f"ENTRY {r['entry']}  n_insn={r['n_insn']}")
    print(f"  VA slots(all)={r['va_slots_all']}")
    if "vt" in r:
        print(f"  factory vt={r['vt']} slot#{r['slot_no']}@{r['slot']}  slots={r['vt_slots']}")
        print(f"  factory RTTI: {r['rtti']}")
        print(f"  factory vt[0]==0x410260 ? {r['vt_slot0_is_410260']}")
        print(f"  factory vt install sites: {r['vt_install_sites']}")
    print(f"  guards={r['guard_imms']}")
    print(f"  QI call={r['qi_call']} failpath={r['fail_path_call']} push1={r['push_1_sites']}")
    print(f"  branch after QI: {r['branch_after_qi']}")
    print(f"  obj ctor={r.get('obj_ctor')} sites={r['alloc_ctor_sites']}")
    print(f"  obj ctor vt writes={r.get('obj_ctor_vt_writes')}")
    print(f"  obj ctor outcalls={r.get('obj_ctor_outcalls')}")
    print(f"  obj ctor sub vt={r.get('obj_ctor_sub_vt')}")
