"""s1: derive the 34 rows, their direct call sites, .bss vector arguments,
and caller-side HRESULT consumption from the binary bytes."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import capstone

from semfix_lib import Bin, COVERAGE, hx, hbytes, load_target_rows, md

OUT = Path(__file__).with_name("scan1.json")


def scan_e8(bin: Bin, targets: set[int]) -> dict[int, list[int]]:
    data = bin.text_bytes()
    hits: dict[int, list[int]] = defaultdict(list)
    m = md()
    for i, b in enumerate(data):
        if b != 0xE8 or i + 5 > len(data):
            continue
        site = bin.text_start + i
        rel = int.from_bytes(data[i + 1:i + 5], "little", signed=True)
        tgt = site + 5 + rel
        if tgt not in targets:
            continue
        ins = next(m.disasm(data[i:i + 12], site), None)
        if (
            ins
            and ins.address == site
            and ins.mnemonic == "call"
            and ins.operands
            and ins.operands[0].type == capstone.x86.X86_OP_IMM
            and ins.operands[0].imm == tgt
        ):
            hits[tgt].append(site)
    return hits


def nearest_edx(bin: Bin, call_site: int) -> dict:
    data = bin.text_bytes()
    lo = max(0, call_site - bin.text_start - 0x80)
    hi = min(len(data), call_site - bin.text_start)
    seg = data[lo:hi]
    start = bin.text_start + lo
    m = md()
    found = []
    for j, b in enumerate(seg):
        if b != 0xBA or j + 5 > len(seg):
            continue
        va = start + j
        imm = int.from_bytes(seg[j + 1:j + 5], "little")
        ins = next(m.disasm(seg[j:j + 16], va), None)
        if (
            ins
            and ins.address == va
            and ins.size == 5
            and ins.mnemonic == "mov"
            and ins.op_str == f"edx, 0x{imm:x}"
            and ins.operands[1].type == capstone.x86.X86_OP_IMM
            and ins.operands[1].imm == imm
        ):
            found.append((va, imm, ins.bytes))
    if not found:
        raise SystemExit(f"no mov edx,imm before call {call_site:#x}")
    va, imm, raw = max(found, key=lambda x: x[0])
    return {"site": va, "bytes": raw.hex().upper(), "vector": imm}


def caller_consumption(bin: Bin, call_site: int) -> dict:
    insns = bin.disasm(call_site + 5, 0x30)
    test = None
    for ins in insns:
        if test is None and ins.mnemonic == "test" and ins.op_str == "eax, eax":
            test = ins
            continue
        if test is not None and ins.mnemonic in ("jge", "jl", "jne", "je"):
            return {
                "test_site": test.address,
                "test_bytes": test.bytes.hex().upper(),
                "jcc_site": ins.address,
                "jcc_bytes": ins.bytes.hex().upper(),
                "jcc": ins.mnemonic,
                "jcc_target": ins.operands[0].imm,
            }
    raise SystemExit(f"no test/jcc consumption after call {call_site:#x}")


def main():
    b = Bin()
    rows = load_target_rows()
    assert len(rows) == 34, len(rows)
    targets = {int(r[0], 16) for r in rows}
    calls = scan_e8(b, targets)
    out = []
    for r in rows:
        entry = int(r[0], 16)
        sites = calls.get(entry, [])
        if len(sites) != 1:
            raise SystemExit(f"{r[0]}: expected 1 direct call, got {[hx(x) for x in sites]}")
        site = sites[0]
        call_ins = next(
            i for i in b.disasm(site, 8) if i.address == site and i.mnemonic == "call"
        )
        edx = nearest_edx(b, site)
        if not b.is_bss_va(edx["vector"]):
            s = b.sec_of(edx["vector"])
            raise SystemExit(
                f"{r[0]}: vector {edx['vector']:#x} not in zero-raw section: {s}"
            )
        cons = caller_consumption(b, site)
        out.append(
            {
                "entry": r[0],
                "subsystem": r[1],
                "name": r[2],
                "old_semantics": r[3],
                "grade": r[4],
                "old_evidence": r[5],
                "call_site": hx(site),
                "call_bytes": call_ins.bytes.hex().upper(),
                "call_target": hx(call_ins.operands[0].imm),
                "edx_site": hx(edx["site"]),
                "edx_bytes": edx["bytes"],
                "vector": hx(edx["vector"]),
                "vector_section": b.sec_of(edx["vector"])["name"],
                "test_site": hx(cons["test_site"]),
                "test_bytes": cons["test_bytes"],
                "jcc_site": hx(cons["jcc_site"]),
                "jcc_bytes": cons["jcc_bytes"],
                "jcc": cons["jcc"],
                "jcc_target": hx(cons["jcc_target"]),
            }
        )
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"rows={len(out)} unique_vectors={len(set(x['vector'] for x in out))}")
    for x in out:
        print(
            f"{x['entry']} call={x['call_site']} vec={x['vector']}@{x['edx_site']} "
            f"consume={x['test_site']}/{x['jcc_site']} {x['jcc']}"
        )
    print("->", OUT)


if __name__ == "__main__":
    main()
