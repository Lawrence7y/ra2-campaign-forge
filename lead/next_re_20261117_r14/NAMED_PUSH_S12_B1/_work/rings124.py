# -*- coding: utf-8 -*-
"""环① 入口自洽 + 环② 槽位字节 + 环④ 直接调用者/活虚表安装点，一次出全量底账。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))
MAIN_VT = 0x007E3EBC
COL = 0x007FC360
TD = 0x00818D60
out = {}

for n, r in enumerate(rows, 1):
    e = int(r["entry"], 16)
    e, insns = C.disasm_body(r["entry"])
    size = int(r["size"])
    nskip = sum(1 for i in insns if i.id == 0)
    last = insns[-1] if insns else None
    end_ok = bool(last and (last.id == C.X86_INS_RET or last.id == C.X86_INS_JMP))
    # 函数体覆盖：最后一条指令末尾 == entry+size ?
    body_end = (last.address + last.size) if last else 0
    covered = (body_end == e + size)
    hint = int(r["name"].split("::")[-1].replace("vslot", "").replace("slot", ""))
    slot_va = MAIN_VT + 4 * hint
    slot_val = C.u32(slot_va)
    direct = C.find_direct_calls(e)
    rec = dict(
        n=n, entry=r["entry"], name=r["name"], size=size, n_insn=len(insns), n_skip=nskip,
        in_text=C.in_text(e), last_insn=("%08X: %s" % (last.address, last.mnemonic)) if last else None,
        end_ok=end_ok, body_end="%08X" % body_end, body_end_ok=covered,
        hint_slot=hint, slot_va="%08X" % slot_va, slot_val=("%08X" % slot_val) if slot_val else None,
        slot_is_entry=(slot_val == int(r["entry"], 16)),
        col="%08X" % COL, col_sig=C.u32(COL), td="%08X" % TD,
        rtti_name=C.read_cstr(TD + 8, 60),
        vt_slot0="%08X" % (C.u32(MAIN_VT) or 0),
        n_direct=len(direct), direct_callers=["%08X" % x for x in direct[:8]],
    )
    out[r["entry"]] = rec
    print("%2d %s %-24s ①in_text=%s end=%s cov=%s skip=%d | ②槽 %s=%s ==entry? %s | ④direct=%d %s" %
          (n, r["entry"], r["name"], C.in_text(e), end_ok, covered, nskip,
           rec["slot_va"], rec["slot_val"], rec["slot_is_entry"], len(direct),
           rec["direct_callers"][:4]))

json.dump(out, open(os.path.join(here, "rings124.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ④ 安装点复查
print("\n④ 主虚表安装点（.text，非 atexit）:")
for s in C.find_vtable_imm_sites(MAIN_VT)["c7_rm"]:
    va = s["write_va"]
    f = C.atlas_covering(va)
    ax = C.is_atexit_registered(f[0]) if f else None
    ins = C.disasm(va, 8)[0]
    print("   %08X in func %s (%d B) atexit=%s | %s %s" %
          (va, f[1], f[2], bool(ax), ins.mnemonic, ins.op_str))
