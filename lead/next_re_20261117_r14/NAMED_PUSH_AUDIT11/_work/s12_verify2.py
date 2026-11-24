import sys, json, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

ENTRIES = ["006C2B10", "006C2C90", "006C2E10", "006C2F90", "006C3110", "006C3290",
           "006C3410", "006C3590", "006C3890", "006C3A10", "006C3B90"]
INIT_FN = 0x6BB9A0
INIT_SPAN = 0x2A00


def is_text_fn(v):
    s = sec_of(v) if v else None
    return bool(s) and s[0] == ".text" and 0x401000 <= v < 0x7E038D


def body_short(va, maxb=500):
    out = []
    for k, i in enumerate(dis(va, maxb)):
        if i.mnemonic == "nop" and k > 0:
            break
        out.append(i)
    return out


def body_long(va, maxb=9000):
    out = []
    for i in dis(va, maxb):
        out.append(i)
        if i.mnemonic.startswith("ret"):
            rest = dis(i.address + i.size, 6)
            if rest and rest[0].mnemonic in ("nop", "int3"):
                break
    return out


def vt_writes(ins):
    res = []
    for i in ins:
        if i.mnemonic != "mov":
            continue
        m = re.match(r"dword ptr \[([^\]]+)\], (0x[0-9a-f]+)$", i.op_str)
        if not m:
            continue
        v = int(m.group(2), 16)
        if 0x7E0000 <= v < 0x812000 and v % 4 == 0:
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
                res.append(va - back)
                break
        p = blob.find(needle, p + 1)
    return res


def imm_sites(imm, opcode):
    """sites where `opcode imm32` (e.g. 68 push imm32) appears"""
    name, sva, vsz, rawsz, raw = sec_of(0x401000)
    blob = DATA[raw:raw + rawsz]
    needle = imm.to_bytes(4, "little")
    res = []
    p = blob.find(needle)
    while p >= 0:
        if p >= 1 and blob[p - 1] == opcode:
            res.append(sva + p - 1)
        p = blob.find(needle, p + 1)
    return res


def rtti_class(vt_va):
    d = {"vt": f"{vt_va:08X}"}
    col = u32(vt_va - 4)
    d["col"] = f"{col:08X}" if col else None
    if not col:
        return d
    d["col_sec"] = sec_of(col)[0] if sec_of(col) else None
    td = u32(col + 0xC)
    d["td"] = f"{td:08X}" if td else None
    if not td:
        return d
    nm = cstr(td + 8, 300)
    d["name"] = nm
    d["name_ok"] = bool(nm and nm.startswith(".?A"))
    return d


def tpl_arg(factory_name):
    m = re.search(r"TClassFactory@V(\w+?)@@", factory_name or "")
    return m.group(1) if m else None


rows = []
for e in ENTRIES:
    va = int(e, 16)
    d = {"entry": e}
    ins = body_short(va, 600)
    d["n_insn"] = len(ins)
    d["guards"] = [(f"{i.address:08X}", i.op_str, i.bytes.hex(" ")) for i in ins
                   if i.mnemonic == "mov" and re.match(r"eax, 0x8[0-9a-f]{7}$", i.op_str)]
    d["guard_jcc"] = []
    for idx, i in enumerate(ins):
        if i.mnemonic == "mov" and re.match(r"eax, 0x8[0-9a-f]{7}$", i.op_str):
            pass
    # guards: record preceding test + jcc that skips them
    d["qi"] = [(f"{i.address:08X}", i.bytes.hex(" ")) for i in ins
               if i.mnemonic == "call" and i.op_str == "dword ptr [eax]"]
    d["destroy"] = [(f"{i.address:08X}", i.op_str, i.bytes.hex(" ")) for i in ins
                    if i.mnemonic == "call" and i.op_str.startswith("dword ptr [edx")]
    d["push1"] = [(f"{i.address:08X}", i.bytes.hex(" ")) for i in ins
                  if i.mnemonic == "push" and i.op_str == "1"]
    d["test_jge"] = [(f"{i.address:08X}", i.mnemonic, i.op_str, i.bytes.hex(" "))
                     for i in ins if i.mnemonic in ("test", "jge", "jl")]
    d["eax_writes_after_qi"] = []
    qiset = {i.address for i in ins if i.mnemonic == "call" and i.op_str == "dword ptr [eax]"}
    if qiset:
        q = min(qiset)
        for i in ins:
            if i.address > q and (i.op_str.startswith("eax") or i.op_str.startswith("al") or i.op_str.startswith("ax")) and i.mnemonic != "test":
                d["eax_writes_after_qi"].append(fmt(i))

    # ring2
    slots = []
    for secname in (".rdata", ".data"):
        s = [x for x in SECTIONS if x[0] == secname][0]
        b2 = DATA[s[4]:s[4] + s[3]]
        p = b2.find(va.to_bytes(4, "little"))
        while p >= 0:
            slots.append(s[1] + p)
            p = b2.find(va.to_bytes(4, "little"), p + 1)
    d["slots"] = [f"{x:08X}" for x in slots]
    rdata_slots = [x for x in slots if sec_of(x)[0] == ".rdata"]
    if rdata_slots:
        slot = rdata_slots[0]
        base = slot
        while is_text_fn(u32(base - 4)):
            base -= 4
        d["vt"] = f"{base:08X}"
        d["slot_no"] = (slot - base) // 4
        d["vt_slots"] = [(k, f"{u32(base+4*k):08X}") for k in range(5)]
        d["factory_rtti"] = rtti_class(base)
        d["expected_class"] = tpl_arg(d["factory_rtti"].get("name"))
        d["factory_vt_installers"] = [f"{a:08X}" for a in imm_writers(base)]
        if d["factory_vt_installers"]:
            a = int(d["factory_vt_installers"][0], 16)
            d["factory_ctor_site_bytes"] = hexs(a - 9, 16)
            # find enclosing function by scanning back for prologue after padding
            d["factory_ctor_callers"] = [f"{c:08X}" for c in direct_callers(a - 9)]
            d["factory_ctor_callers2"] = [f"{c:08X}" for c in direct_callers(a - 9 + 0)]  # same
    # registration block for the factory ctor
    ctors = [(i.address, int(i.op_str, 16)) for i in ins
             if i.mnemonic == "call" and i.op_str.startswith("0x") and i.op_str != "0x7c8e17"]
    d["obj_ctor"] = f"{ctors[0][1]:08X}" if ctors else None
    if ctors:
        ctor = ctors[0][1]
        cins = body_long(ctor)
        d["obj_ctor_n"] = len(cins)
        ws = vt_writes(cins)
        # this-register = first "mov <reg>, ecx"
        thisreg = None
        for i in cins[:14]:
            m = re.match(r"(\w+), ecx$", i.op_str)
            if i.mnemonic == "mov" and m:
                thisreg = m.group(1)
                break
        d["this_reg"] = thisreg
        d["obj_all_vt_writes"] = [(f"{a:08X}", dst, f"{v:08X}", by) for a, dst, v, by in ws]
        off0 = []
        for a, dst, v, by in ws:
            if dst in (thisreg,):
                info = rtti_class(v)
                off0.append({"at": f"{a:08X}", "dst": dst, "vt": f"{v:08X}",
                             "slot0": f"{u32(v):08X}", "rtti": info.get("name"),
                             "bytes": by})
        d["obj_off0_writes_thisreg"] = off0
        match = [w for w in off0 if w["rtti"] == (".?AV" + (d.get("expected_class") or "") + "@@")]
        d["obj_main_vt"] = match[0] if match else None
        if match:
            mv = int(match[0]["vt"], 16)
            d["obj_main_vt_writers"] = [f"{a:08X}" for a in imm_writers(mv)]
            slot8 = u32(mv + 0x20)
            d["obj_slot8"] = f"{slot8:08X}" if slot8 else None
            d["obj_slot8_head"] = [fmt(x) for x in dis(slot8, 48)][:12] if slot8 else None
    d["direct_callers"] = [f"{c:08X}" for c in direct_callers(va)]
    rows.append(d)

with open("verify2.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

for d in rows:
    print("=" * 112)
    print(f"ENTRY {d['entry']}  n_insn={d['n_insn']}  direct_callers={d['direct_callers']}")
    print(f"  factory vt={d.get('vt')} slot#{d.get('slot_no')} slots={d.get('vt_slots')}")
    print(f"  factory RTTI={d.get('factory_rtti')}  expected_class={d.get('expected_class')}")
    print(f"  factory vt installers={d.get('factory_vt_installers')} bytes(ctor start)={d.get('factory_ctor_site_bytes')}")
    print(f"  factory ctor callers={d.get('factory_ctor_callers')}")
    print(f"  guards={d['guards']}")
    print(f"  qi={d['qi']} destroy={d['destroy']} push1={d['push1']}")
    print(f"  test/jge={d['test_jge']}")
    print(f"  eax writes after QI: {d['eax_writes_after_qi']}")
    print(f"  obj ctor={d.get('obj_ctor')} n={d.get('obj_ctor_n')} this_reg={d.get('this_reg')}")
    print(f"  obj off0 writes(this)={d.get('obj_off0_writes_thisreg')}")
    print(f"  obj MAIN vt match={d.get('obj_main_vt')}")
    print(f"  obj main vt writers={d.get('obj_main_vt_writers')}")
    print(f"  obj slot8={d.get('obj_slot8')} head={d.get('obj_slot8_head')}")
