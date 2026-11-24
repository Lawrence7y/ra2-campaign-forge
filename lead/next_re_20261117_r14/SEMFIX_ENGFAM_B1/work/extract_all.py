"""extract_all: derive every required anchor for all 17 B1 rows from binary bytes.

Anchors per row:
  元素类: .bss vector address, ctor write site, RTTI descriptor (COL/TD),
          class-name string address + name.
  ③b②: HRESULT checks (test/cmp eax + jl/jne), failure landing pad,
        success xor eax,eax, caller-side consumption (test/jge).
  ④: real caller (Save_Core direct call) + live upward caller chain hint.
"""
from __future__ import annotations

import json
from pathlib import Path

import capstone

from semfix_lib import Bin, hx, hbytes

OUT = Path(__file__).resolve().parent.parent / "work" / "anchors.json"
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
B1 = [
    "0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
    "00680070", "006800F0", "00680170", "006801F0", "00680270",
    "006802F0", "00680370", "006803F0", "00680470", "006804F0",
    "00680570", "00680670",
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


def is_plausible(name: str) -> bool:
    if not name:
        return False
    letters = sum(ch.isalpha() for ch in name)
    return letters >= 3


def clean_name(name: str) -> str:
    if not name:
        return ""
    s = name
    for prefix in (".?AV", ".?AU"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    return s.replace("@@", "")


def main():
    b = Bin()
    slot_vas = {int(s, 16): s for s in SLOTS}
    calls = scan_e8(b, set(slot_vas))
    c705 = scan_c705(b)

    insns = list(unit().disasm(b.data(SAVE_CORE, CHAIN_END - SAVE_CORE), SAVE_CORE))
    last_edx = None
    chain = {}
    for ins in insns:
        if ins.mnemonic == "mov" and ins.op_str.startswith("edx,"):
            op = ins.operands[1]
            if op.type == capstone.x86.X86_OP_IMM:
                last_edx = (op.imm, ins.address, ins.bytes.hex().upper())
        elif ins.mnemonic == "call":
            op = ins.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and op.imm in slot_vas:
                chain[op.imm] = (ins.address, last_edx)

    out = []
    for s in B1:
        e = int(s, 16)
        rec = {"entry": s}
        cs = chain.get(e)
        if not cs:
            rec["error"] = "no Save_Core call site"
            out.append(rec)
            continue
        call_site, edx = cs
        vec, edx_site, edx_bytes = edx
        rec["call_site"] = hx(call_site)
        rec["edx_site"] = hx(edx_site)
        rec["edx_bytes"] = edx_bytes
        rec["vector"] = hx(vec)
        sec = b.sec_of(vec)
        rec["vector_section"] = sec["name"] if sec else None
        rec["vector_is_bss"] = b.is_bss_va(vec)

        after = list(unit().disasm(b.data(call_site + 5, 0x40), call_site + 5))
        cons = None
        for x in after:
            if x.mnemonic in ("test", "cmp") and "eax" in x.op_str:
                nxt = None
                j = after.index(x) + 1
                if j < len(after) and after[j].mnemonic.startswith("j"):
                    nxt = after[j]
                tgt = None
                if nxt and nxt.operands and nxt.operands[0].type == capstone.x86.X86_OP_IMM:
                    tgt = hx(nxt.operands[0].imm)
                cons = {
                    "test_site": hx(x.address),
                    "test_txt": f"{x.mnemonic} {x.op_str}",
                    "test_bytes": x.bytes.hex().upper(),
                    "jcc_site": hx(nxt.address) if nxt else None,
                    "jcc": nxt.mnemonic if nxt else None,
                    "jcc_target": tgt or (nxt.op_str if nxt else None),
                    "jcc_bytes": nxt.bytes.hex().upper() if nxt else None,
                }
                break
        rec["caller_consume"] = cons
        rec["e8_sites"] = [hx(x) for x in calls.get(e, [])]

        writes = c705.get(vec, [])
        wrecs = []
        for site, vt in writes:
            r = b.rtti(vt)
            wrecs.append({
                "site": hx(site), "vt": hx(vt),
                "col": hx(r["col"]), "td": hx(r["td"]),
                "name_va": hx(r["name_va"]), "name_raw": r["name"],
                "name_clean": clean_name(r["name"]),
                "plausible": is_plausible(r["name"]),
                "col_bytes": r["col_bytes"], "td_bytes": r["td_bytes"],
            })
        rec["ctor_writes"] = wrecs

        ins = body(b, e)
        checks = []
        xors = []
        returns = []
        for i, x in enumerate(ins):
            if x.mnemonic in ("test", "cmp") and x.op_str.replace(" ", "").startswith("eax,"):
                nxt = ins[i + 1] if i + 1 < len(ins) else None
                if nxt and nxt.mnemonic in ("jl", "jne", "jb", "jbe"):
                    tgt = None
                    if nxt.operands and nxt.operands[0].type == capstone.x86.X86_OP_IMM:
                        tgt = hx(nxt.operands[0].imm)
                    checks.append({
                        "test_site": hx(x.address),
                        "test_txt": f"{x.mnemonic} {x.op_str}",
                        "test_bytes": x.bytes.hex().upper(),
                        "jcc_site": hx(nxt.address),
                        "jcc": nxt.mnemonic,
                        "jcc_target": tgt or nxt.op_str,
                        "jcc_bytes": nxt.bytes.hex().upper(),
                    })
            if x.mnemonic == "xor" and x.op_str.replace(" ", "") == "eax,eax":
                xors.append(hx(x.address))
            if x.mnemonic == "ret":
                returns.append(hx(x.address))
        landing = {}
        for c in checks:
            landing[c["jcc_target"]] = landing.get(c["jcc_target"], 0) + 1
        rec["hresult_checks"] = checks
        rec["xor_eax"] = xors
        rec["rets"] = returns
        rec["failure_landing"] = max(landing, key=landing.get) if landing else None
        rec["failure_landing_votes"] = landing
        rec["n_call_derived_jl"] = len(checks)
        out.append(rec)

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("entry    vec       section  writes jl landing   xor       consume         class")
    for rec in out:
        if rec.get("error"):
            print(rec["entry"], "ERROR", rec["error"])
            continue
        cls = next((w["name_clean"] for w in rec["ctor_writes"] if w["plausible"]), "未取得")
        ctor = ",".join(w["site"] for w in rec["ctor_writes"]) or "-"
        cons = f"{rec['caller_consume']['test_site']}/{rec['caller_consume']['jcc_site']}" if rec["caller_consume"] else "-"
        print(f"{rec['entry']}  {rec['vector']}  {rec['vector_section']:<7}  "
              f"{len(rec['ctor_writes']):<6} {rec['n_call_derived_jl']:<2} "
              f"{rec['failure_landing']}  {','.join(rec['xor_eax']):<8}  {cons:<14} {cls}")
    print("\n->", OUT)


if __name__ == "__main__":
    main()
