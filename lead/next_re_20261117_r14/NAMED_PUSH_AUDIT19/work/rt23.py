# -*- coding: utf-8 -*-
"""㉓ re-verification: for each audited vtable, enumerate every write point,
resolve its enclosing function independently, and classify:
  - ROW_SELF  (write inside the audited entry's own body)
  - ATEXIT    (push <fn>; call 0x7C978A)
  - DELETE_DTOR (test byte[esp+X],1 + call 0x7C8B3D + ret 4)
  - otherwise  (ctor / factory / other)
Also prints the enclosing function's direct-caller count (for live-object evidence).
"""
import sys
from re_lib import Bin, fmt_ins

CASES = [
    (0x7EF600, 0x005FEAF0),
    (0x7F3528, 0x006B5850),
    (0x7F522C, 0x0071CDA0),
    (0x7E1668, 0x00432050),
    (0x7E4A28, 0x0046D000),
    (0x7E4A28, 0x0046D090),
    (0x7F5180, 0x0071B1B0),
]


def main():
    b = Bin()
    done = set()
    for vt, row in CASES:
        key = (vt, row)
        if key in done:
            continue
        done.add(key)
        print("=" * 110)
        print(f"TABLE {vt:08X}   audited row = {row:08X}")
        print("=" * 110)
        w = b.vt_writers(vt)
        print(f"total imm32 write points: {len(w)}")
        cat = {}
        detail = []
        for rec in w:
            ins = b.instr_containing(rec["imm_at"])
            if ins is None:
                cat["UNDECODABLE"] = cat.get("UNDECODABLE", 0) + 1
                continue
            st = b.func_start_of(ins.address)
            ate, p, aev = b.is_atexit_dtor(st)
            dele, dev = b.is_delete_dtor(st)
            kinds = []
            if st == row:
                kinds.append("ROW_SELF")
            if ate:
                kinds.append("ATEXIT")
            if dele:
                kinds.append("DELETE_DTOR")
            if not kinds:
                kinds.append("ctor_or_other")
            tag = "+".join(kinds)
            cat[tag] = cat.get(tag, 0) + 1
            detail.append((ins.address, st, tag, ins.mnemonic + " " + ins.op_str,
                           ins.bytes.hex(" "), dele, dev, p, aev))
        for k, v in sorted(cat.items(), key=lambda x: -x[1]):
            print(f"   {v:5d}  {k}")
        print("\n  detail (non stack-template only):")
        for (ia, st, tag, text, bs, dele, dev, p, aev) in detail:
            if "[esp" in text:
                continue
            nc = len(b.callers_direct(st)) if st else 0
            extra = ""
            if dele:
                extra += f" DELDTOR[test@{dev.get('test_byte_esp_1_at')},free@{dev.get('call_free_at')},ret4={dev.get('ret_4')}]"
            if p:
                extra += f" ATEXIT_AT[{p:#x}]+{aev}"
            print(f"   ins@{ia:08X} in_func={st:08X} tag={tag:<22} n_callers={nc:<3} {text:<42} bytes[{bs}]{extra}")
        print("\n  ATEXIT writers:",
              [(f"{d[0]:08X}", f"{d[1]:08X}") for d in detail if "ATEXIT" in d[2]] or "NONE")
        print()


if __name__ == "__main__":
    main()
