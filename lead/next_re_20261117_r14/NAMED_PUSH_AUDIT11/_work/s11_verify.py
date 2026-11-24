import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

ENTRIES = ["006C2B10", "006C2C90", "006C2E10", "006C2F90", "006C3110", "006C3290",
           "006C3410", "006C3590", "006C3890", "006C3A10", "006C3B90"]


def is_text_fn(v):
    s = sec_of(v) if v else None
    return bool(s) and s[0] == ".text" and 0x401000 <= v < 0x7E038D


def body(va, maxb=400, stop_at_pad=True):
    ins = dis(va, maxb)
    out = []
    for k, i in enumerate(ins):
        if stop_at_pad and i.mnemonic == "nop" and k > 0:
            break
        out.append(i)
    return out


def body_long(va, maxb=8000):
    """disassemble a function: stop when a ret is followed by padding (nop/int3/cc)."""
    ins = dis(va, maxb)
    out = []
    for k, i in enumerate(ins):
        out.append(i)
        if i.mnemonic.startswith("ret"):
            rest = dis(i.address + i.size, 8)
            if rest and rest[0].mnemonic in ("nop", "int3"):
                break
    return out


def vt_writes(ins, lo=0x7E0000, hi=0x812000):
    res = []
    for i in ins:
        if i.mnemonic != "mov":
            continue
        m = re.match(r"dword ptr \[([^\]]+)\], (0x[0-9a-f]+)$", i.op_str)
        if not m:
            continue
        v = int(m.group(2), 16)
        if lo <= v < hi and v % 4 == 0:
            res.append((i.address, m.group(1), v, i.bytes.hex(" ")))
    return res


def imm_writers(imm):
    name, sva, vsz, rawsz, raw = sec_of(0x401000)
    blob = DATA[raw:raw + rawsz]
    needle = imm.to_bytes(4, "little")
    res = []
    p = blob.find(needle)
    while p >= 0:
        va = sva + p
        for back in range(1, 8):
            if p - back >= 0 and blob[p - back] == 0xC7:
                res.append((va - back, va))
                break
        p = blob.find(needle, p + 1)
    return res


def rtti_class(vt_va):
    d = {"vt": f"{vt_va:08X}"}
    col = u32(vt_va - 4)
    d["col"] = f"{col:08X}" if col else None
    if not col:
        return d
    s = sec_of(col)
    d["col_sec"] = s[0] if s else None
    td = u32(col + 0xC)
    d["td"] = f"{td:08X}" if td else None
    if not td:
        return d
    d["td_sec"] = sec_of(td)[0] if sec_of(td) else None
    nm = cstr(td + 8, 300)
    d["name"] = nm
    d["name_ok"] = bool(nm and nm.startswith(".?A"))
    return d


def fn_start_guess(va, back=0x600):
    """very rough: walk back to the last byte that follows padding (90/cc) and looks like a prologue."""
    for cand in range(va - 1, va - back, -1):
        b = rd(cand, 3)
        if not b:
            continue
        prev = rd(cand - 1, 1)
        if prev and prev[0] in (0x90, 0xCC, 0xC3):
            nxt = dis(cand, 12)
            if nxt and nxt[0].mnemonic in ("push", "sub", "mov", "lea", "pushfd", "xor", "and", "cmp"):
                return cand
    return None


rows = []
for e in ENTRIES:
    va = int(e, 16)
    d = {"entry": e}
    ins = body(va, 500)
    d["n_insn"] = len(ins)
    d["guards"] = [(f"{i.address:08X}", i.op_str, i.bytes.hex(" ")) for i in ins
                   if i.mnemonic == "mov" and re.match(r"eax, 0x8[0-9a-f]{7}$", i.op_str)]
    d["qi"] = [(f"{i.address:08X}", i.bytes.hex(" ")) for i in ins
               if i.mnemonic == "call" and i.op_str == "dword ptr [eax]"]
    d["branch"] = [fmt(i) for i in ins if i.mnemonic in ("test", "jge", "jl", "jns", "js")]
    d["destroy"] = [(f"{i.address:08X}", i.op_str, i.bytes.hex(" ")) for i in ins
                    if i.mnemonic == "call" and i.op_str.startswith("dword ptr [edx")]
    d["push1"] = [(f"{i.address:08X}", i.bytes.hex(" ")) for i in ins
                  if i.mnemonic == "push" and i.op_str == "1"]
    # ring2 slot
    slots = []
    for secname in (".rdata", ".data"):
        s = [x for x in SECTIONS if x[0] == secname][0]
        b2 = DATA[s[4]:s[4] + s[3]]
        p = b2.find(va.to_bytes(4, "little"))
        while p >= 0:
            slots.append(s[1] + p)
            p = b2.find(va.to_bytes(4, "little"), p + 1)
    s = sec_of(0x401000)
    textb = DATA[s[4]:s[4] + s[3]]
    p = textb.find(va.to_bytes(4, "little"))
    while p >= 0:
        slots.append(s[1] + p)
        p = textb.find(va.to_bytes(4, "little"), p + 1)
    d["slots"] = [f"{x:08X}" for x in slots]
    rdata_slots = [x for x in slots if sec_of(x)[0] == ".rdata"]
    if rdata_slots:
        slot = rdata_slots[0]
        base = slot
        while True:
            prev = u32(base - 4)
            if not is_text_fn(prev):
                break
            base -= 4
        d["vt"] = f"{base:08X}"
        d["slot_addr"] = f"{slot:08X}"
        d["slot_no"] = (slot - base) // 4
        d["vt_slots"] = [(k, f"{u32(base+4*k):08X}") for k in range(6)]
        d["vt_rtti"] = rtti_class(base)
        d["vt_installers"] = [f"{a:08X}" for a, v in imm_writers(base)]
        # ctor that installs it: disassemble a window around installer
        if d["vt_installers"]:
            a = int(d["vt_installers"][0], 16)
            d["vt_installer_bytes"] = hexs(a, 10)
            d["vt_installer_fn"] = f"{fn_start_guess(a):08X}" if fn_start_guess(a) else None
    # object ctor
    ctors = [(f"{i.address:08X}", i.op_str) for i in ins
             if i.mnemonic == "call" and i.op_str.startswith("0x") and i.op_str not in ("0x7c8e17",)]
    d["obj_ctor_site"] = ctors[0] if ctors else None
    if ctors:
        ctor = int(ctors[0][1], 16)
        d["obj_ctor"] = f"{ctor:08X}"
        cins = body_long(ctor)
        d["obj_ctor_n"] = len(cins)
        ws = vt_writes(cins)
        d["obj_ctor_vt_writes"] = [(f"{a:08X}", dst, f"{v:08X}", by) for a, dst, v, by in ws]
        off0 = [w for w in ws if w[1] in ("esi", "eax", "ecx", "edi", "ebp", "esi+0", "ebx")]
        d["obj_main_vt"] = f"{off0[0][2]:08X}" if off0 else None
        if off0:
            mv = off0[0][2]
            d["obj_main_vt_slot0"] = f"{u32(mv):08X}"
            d["obj_main_vt_slot0_420260"] = (u32(mv) == 0x410260)
            d["obj_main_vt_rtti"] = rtti_class(mv)
            d["obj_main_vt_write_site"] = f"{off0[0][0]:08X}"
            d["obj_main_vt_writers"] = [f"{a:08X}" for a, v in imm_writers(mv)]
            slot8 = u32(mv + 0x20)
            d["obj_vt_slot8"] = f"{slot8:08X}" if slot8 else None
            if slot8:
                d["obj_vt_slot8_body"] = [fmt(x) for x in dis(slot8, 60)][:14]
    d["direct_callers"] = [f"{c:08X}" for c in direct_callers(va)]
    rows.append(d)

with open("verify_rows.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

for d in rows:
    print("=" * 112)
    print(f"ENTRY {d['entry']}  n_insn={d['n_insn']}  direct_callers={d['direct_callers']}")
    print(f"  slots={d['slots']}")
    print(f"  factory vt={d.get('vt')} slot#{d.get('slot_no')}@{d.get('slot_addr')} "
          f"slots={d.get('vt_slots')}")
    print(f"  factory RTTI={d.get('vt_rtti')}")
    print(f"  factory vt installers={d.get('vt_installers')} installer_fn={d.get('vt_installer_fn')} "
          f"bytes={d.get('vt_installer_bytes')}")
    print(f"  guards={[g[0]+':'+g[1] for g in d['guards']]}")
    print(f"  qi={d['qi']} destroy={d['destroy']} push1={d['push1']}")
    print(f"  branch={d['branch']}")
    print(f"  obj ctor={d.get('obj_ctor')} (n={d.get('obj_ctor_n')}) site={d.get('obj_ctor_site')}")
    print(f"  obj vt writes={d.get('obj_ctor_vt_writes')}")
    print(f"  obj MAIN vt={d.get('obj_main_vt')} write@{d.get('obj_main_vt_write_site')} "
          f"writers={d.get('obj_main_vt_writers')}")
    print(f"  obj main vt slot0={d.get('obj_main_vt_slot0')} ==0x410260? {d.get('obj_main_vt_slot0_420260')} "
          f"RTTI={d.get('obj_main_vt_rtti')}")
    print(f"  obj vt slot8={d.get('obj_vt_slot8')} body={d.get('obj_vt_slot8_body')}")
