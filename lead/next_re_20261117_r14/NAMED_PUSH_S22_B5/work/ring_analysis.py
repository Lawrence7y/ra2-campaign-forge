# -*- coding: utf-8 -*-
"""For each of 9 vector rows: characterize ALL return sites (AL/EAX convention),
find vtable install/write sites + containing function + atexit/destructor status (④).
Also find the exact slot-2 RTTI resolution bytes (②)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b5_rows.json"), encoding="utf-8") as f:
    rows = json.load(f)
with open(os.path.join(HERE, "dump.json"), encoding="utf-8") as f:
    dump = json.load(f)

RESULT = {}
for r in rows:
    entry = r["entry"]; ea = int(entry, 16); size = int(r["size"])
    insns = R.disasm_body(ea, size)

    # --- return sites: last AL/EAX-setting insn before each ret ---
    rets = []
    for i, ins in enumerate(insns):
        if ins.id == X86_INS_RET:
            # walk back up to 8 insns for mov al,xor al,mov eax
            setter = None
            for j in range(i - 1, max(-1, i - 9), -1):
                p = insns[j]
                if p.id in (X86_INS_POP, X86_INS_ADD, X86_INS_LEA):
                    continue
                if p.id == X86_INS_MOV and len(p.operands) == 2:
                    a, b = p.operands
                    if a.type == X86_OP_REG and a.reg in (X86_REG_AL, X86_REG_AX, X86_REG_EAX):
                        setter = "%s %s, %s" % (p.mnemonic, p.op_str.split(",")[0].strip(), b.imm & 0xFF if b.type == X86_OP_IMM else p.op_str) if b.type == X86_OP_IMM else ("%s %s" % (p.mnemonic, p.op_str))
                        break
                if p.id == X86_INS_XOR and len(p.operands) == 2:
                    a, b = p.operands
                    if a.type == X86_OP_REG and a.reg in (X86_REG_AL, X86_REG_AX, X86_REG_EAX) and a.reg == b.reg:
                        setter = "xor %s,%s (=0)" % (p.reg_name(a.reg), p.reg_name(b.reg))
                        break
                if p.id == X86_INS_SETE and len(p.operands) == 2:
                    setter = "sete (bool)"
                    break
            rets.append({"ret_va": "%08X" % ins.address, "ret_bytes": ins.bytes.hex(), "al_setter": setter})
    # classify boolean-ness
    boolish = all((rt["al_setter"] and ("0" in rt["al_setter"] or "1" in rt["al_setter"] or "bool" in rt["al_setter"] or "sete" in rt["al_setter"])) for rt in rets)

    # --- ② exact slot resolution (wide scan, choose slot_no==2 & rtti matching) ---
    d = dump[entry]
    slot2 = None
    for s in d["slots"]:
        sv = int(s["slot_va"], 16)
        for k in range(0, 0x80):
            vb = sv - 4 * k
            col = C.u32(vb - 4)
            if not col or not C.va_in(col):
                continue
            if C.u32(col) != 0:
                continue
            td = C.u32(col + 0xC)
            if not td or not C.va_in(td):
                continue
            name = C.read_cstr(td + 8, 200)
            if ".?AV" in name and k == 2:
                slot2 = {"slot_va": s["slot_va"], "vtable_base": "%08X" % vb, "slot_no": k,
                         "col": "%08X" % col, "td": "%08X" % td,
                         "name_va": "%08X" % (td + 8), "rtti_name": name,
                         "col_word_va": "%08X" % (vb - 4),
                         "vtable_base_word": "%08X" % C.u32(vb),
                         "slot_word": "%08X" % C.u32(sv)}
                break
        if slot2:
            break

    # --- ④ vtable install/write sites ---
    writes = None
    if slot2:
        vt = int(slot2["vtable_base"], 16)
        w = C.find_vtable_writes(vt)
        installs = []
        for g in w["global"]:
            wva = g["write_va"] if isinstance(g["write_va"], str) else "%08X" % g["write_va"]
            f = C.find_containing_atlas_func(int(wva, 16))
            atex = bool(C.is_atexit_registered(f[0])) if f else False
            installs.append({"write_va": wva, "global": g.get("global"),
                             "in_func": ("%08X" % f[0], f[1], f[2]) if f else None,
                             "atexit": atex})
        for rw in w["regdisp"]:
            rva = "%08X" % rw
            f = C.find_containing_atlas_func(rw)
            atex = bool(C.is_atexit_registered(f[0])) if f else False
            installs.append({"write_va": rva, "global": None,
                             "in_func": ("%08X" % f[0], f[1], f[2]) if f else None,
                             "atexit": atex})
        writes = {"global": [("%08X" % x) if isinstance(x, int) else x for x in w["global"]] if False else [],
                  "imm_loads": ["%08X" % x for x in w["imm_load"]],
                  "installs": installs}

    RESULT[entry] = {
        "name": r["name"], "rets": rets, "boolish_return": boolish,
        "slot2": slot2, "writes": writes,
        "direct_callers": d["direct_callers"],
    }

with open(os.path.join(HERE, "ring_analysis.json"), "w", encoding="utf-8") as f:
    json.dump(RESULT, f, ensure_ascii=False, indent=1)

for entry, d in RESULT.items():
    print("=" * 105)
    print(entry, d["name"])
    print("  ② slot2:", d["slot2"])
    print("  ③ return sites (%d), boolish=%s:" % (len(d["rets"]), d["boolish_return"]))
    for rt in d["rets"]:
        print("     %s %s <- %s" % (rt["ret_va"], rt["ret_bytes"], rt["al_setter"]))
    print("  ④ direct callers:", d["direct_callers"])
    print("  ④ vtable installs:")
    if d["writes"]:
        for ins in d["writes"]["installs"]:
            print("     write@%s global=%s in_func=%s atexit=%s" % (
                ins["write_va"], ins["global"], ins["in_func"], ins["atexit"]))
        print("     imm_loads:", d["writes"]["imm_loads"])
    else:
        print("     (no vtable resolved)")
