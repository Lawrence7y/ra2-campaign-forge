"""W178 independent static evidence collector.

Read-only against C:/D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe.
All outputs go under W178_guards/EVIDENCE.

Channels:
  A. full .text linear disassembly with capstone skipdata=True (no function_atlas)
  B. function_atlas.tsv interval containment (entry <= site < entry+size)
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from collections import defaultdict, deque

import capstone
import pefile

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUTDIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "W178_guards", "EVIDENCE")
EXPECTED_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

IMAGE_BASE = 0x400000
TARGET_REMOVE = 0x724730
SITE_6CD8CD = 0x6CD8CD
GLOBAL_887368 = 0x887368
GLOBAL_8871E0 = 0x8871E0
# Independent boundary evidence (ret + alignment padding), used only for the two atlas-hole sites.
GAP_FUNCS = {
    0x6D15CB: (0x6D1570, 0x6D15E4),  # ret @0x6D15E3, nop pad follows
    0x6D1605: (0x6D15F0, 0x6D160B),  # ret @0x6D160A, nop pad follows
}
JT_6CC390 = 0x6CDE44
ECX_REGS = {"ECX", "CX", "CL", "CH"}
EAX_REGS = {"EAX", "AX", "AL", "AH"}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


class Bin:
    def __init__(self, path: str):
        self.pe = pefile.PE(path, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode("utf-8", "replace").rstrip("\x00")
            self.sections.append({
                "name": name,
                "va": self.image_base + s.VirtualAddress,
                "vsize": s.Misc_VirtualSize,
                "raw": s.PointerToRawData,
                "rawsize": s.SizeOfRawData,
            })
        self.text = next(s for s in self.sections if s["name"] == ".text")

    def read(self, va: int, n: int) -> bytes:
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.pe.__data__[off:off + n]
        raise ValueError(f"VA {va:#x}+{n} not in raw section range")

    def raw_all(self, s):
        return self.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]


def md(skipdata=True, detail=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.skipdata = skipdata
    m.detail = detail
    return m


def insn_text(i) -> str:
    return f"{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}".rstrip()


def reg_names(insn, kind: str) -> set[str]:
    if not insn.id:
        return set()
    try:
        regs = insn.regs_access()[0 if kind == "read" else 1]
    except Exception:
        return set()
    return {insn.reg_name(r) for r in regs}


def canon_reg(name: str) -> str:
    n = name.upper()
    if n in ECX_REGS:
        return "ECX"
    if n in EAX_REGS:
        return "EAX"
    if n in {"EBX", "BX", "BL", "BH"}:
        return "EBX"
    if n in {"EDX", "DX", "DL", "DH"}:
        return "EDX"
    if n in {"ESI", "SI"}:
        return "ESI"
    if n in {"EDI", "DI"}:
        return "EDI"
    if n in {"EBP", "BP"}:
        return "EBP"
    if n in {"ESP", "SP"}:
        return "ESP"
    return n


def writes_reg(insn, canonical: str) -> bool:
    return canonical in {canon_reg(r) for r in reg_names(insn, "write")}


def parse_target(op_str: str):
    op_str = op_str.strip()
    if op_str.startswith("0x"):
        try:
            return int(op_str, 16)
        except ValueError:
            return None
    return None


def load_atlas():
    rows = []
    with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 2:
                continue
            try:
                entry = int(p[0], 16)
                size = int(p[1], 10)
            except ValueError:
                continue
            rows.append({"entry": entry, "size": size, "raw": dict(zip(header, p))})
    rows.sort(key=lambda r: r["entry"])
    return rows


def containing(rows, va: int):
    hits = [r for r in rows if r["entry"] <= va < r["entry"] + r["size"]]
    if not hits:
        return None
    return min(hits, key=lambda r: r["size"])


def full_sweep(b):
    m = md(skipdata=True, detail=True)
    data = b.raw_all(b.text)
    starts = set()
    calls = defaultdict(list)
    jmps = defaultdict(list)
    insn_count = 0
    skip_count = 0
    mem_writes = defaultdict(list)
    imm_loads = defaultdict(list)
    targets = {GLOBAL_887368, GLOBAL_8871E0}
    for insn in m.disasm(data, b.text["va"]):
        if insn.id == 0:
            skip_count += 1
            continue
        insn_count += 1
        starts.add(insn.address)
        if insn.mnemonic == "call":
            t = parse_target(insn.op_str)
            if t is not None:
                calls[t].append(insn.address)
        elif insn.mnemonic == "jmp":
            t = parse_target(insn.op_str)
            if t is not None:
                jmps[t].append(insn.address)
        # memory writes, both absolute and [base+disp] forms
        try:
            ops = insn.operands
        except Exception:
            ops = []
        for op in ops:
            if op.type == capstone.x86.X86_OP_MEM:
                mem = op.mem
                disp = mem.disp & 0xFFFFFFFF
                access = getattr(op, "access", None)
                is_write = access == capstone.CS_AC_WRITE
                # capstone's access not always populated on all builds; fall back to op0 for stores
                if op is ops[0] and insn.mnemonic.split()[0] in {
                    "mov", "movzx", "movsx", "add", "sub", "inc", "dec", "and", "or", "xor", "lea", "xchg"
                }:
                    is_write = True
                if is_write and disp in targets:
                    mem_writes[disp].append({
                        "va": insn.address,
                        "text": insn_text(insn),
                        "kind": "abs" if mem.base == 0 and mem.index == 0 else "reg+disp",
                        "base": insn.reg_name(mem.base) if mem.base else None,
                    })
            elif op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) in targets:
                if insn.mnemonic == "mov" and ops and ops[0].type == capstone.x86.X86_OP_REG:
                    imm_loads[op.imm & 0xFFFFFFFF].append({
                        "va": insn.address,
                        "reg": insn.reg_name(ops[0].reg),
                        "text": insn_text(insn),
                    })
    return {
        "starts": starts,
        "calls": dict(calls),
        "jmps": dict(jmps),
        "insn_count": insn_count,
        "skip_count": skip_count,
        "mem_writes": dict(mem_writes),
        "imm_loads": dict(imm_loads),
    }


def disasm_range(b, start: int, end: int):
    return list(md(skipdata=True, detail=True).disasm(b.read(start, end - start), start))


def resolve_reg(instrs, idx: int, canonical: str, max_steps=80):
    """Backward linear register source resolver (returns last write text, no CFG promises)."""
    reg = canonical
    steps = 0
    j = idx - 1
    while j >= 0 and steps < max_steps:
        ins = instrs[j]
        if ins.id and writes_reg(ins, reg):
            text = insn_text(ins)
            if ins.mnemonic == "mov" and len(ins.operands) == 2:
                src = ins.operands[1]
                if src.type == capstone.x86.X86_OP_REG:
                    nxt = canon_reg(ins.reg_name(src.reg))
                    if nxt != reg:
                        reg = nxt
                        j -= 1
                        steps += 1
                        continue
                if src.type == capstone.x86.X86_OP_IMM:
                    return f"imm {src.imm:#x} @ {ins.address:#x}: {text}"
                if src.type == capstone.x86.X86_OP_MEM:
                    return f"mem {ins.op_str} @ {ins.address:#x}: {text}"
            if ins.mnemonic == "lea":
                return f"lea {ins.op_str} @ {ins.address:#x}: {text}"
            return f"other-write {ins.mnemonic} @ {ins.address:#x}: {text}"
        j -= 1
        steps += 1
    return f"entry-value/{canonical}"


def reachable_from_entry(instrs, target: int, extra_indirect_targets=None):
    if not instrs:
        return False, []
    by_addr = {i.address: k for k, i in enumerate(instrs)}
    if target not in by_addr:
        return False, []
    start = instrs[0].address
    q = deque([start])
    prev = {start: None}
    while q:
        a = q.popleft()
        k = by_addr.get(a)
        if k is None:
            continue
        ins = instrs[k]
        if a == target:
            path = []
            cur = a
            while cur is not None:
                path.append(cur)
                cur = prev.get(cur)
            return True, list(reversed(path))
        nxt = instrs[k + 1].address if k + 1 < len(instrs) else None
        m = ins.mnemonic
        if m == "ret" or m.startswith("retf"):
            continue
        if m == "jmp":
            t = parse_target(ins.op_str)
            succ = [t] if t is not None else list(extra_indirect_targets or [])
        elif m.startswith("j"):
            t = parse_target(ins.op_str)
            succ = [x for x in (t, nxt) if x is not None]
        elif m == "call":
            succ = [nxt] if nxt is not None else []
        else:
            succ = [nxt] if nxt is not None else []
        for s in succ:
            if s not in prev:
                prev[s] = a
                q.append(s)
    return False, []


def dword_refs(b, value: int):
    pat = struct.pack("<I", value)
    out = []
    for s in b.sections:
        data = b.raw_all(s)
        start = 0
        while True:
            i = data.find(pat, start)
            if i < 0:
                break
            out.append({"section": s["name"], "va": s["va"] + i})
            start = i + 1
    return out


def imm_refs(b, values):
    """Full linear sweep: immediate operands equal to any of `values`."""
    out = defaultdict(list)
    m = md(skipdata=True, detail=True)
    data = b.raw_all(b.text)
    for insn in m.disasm(data, b.text["va"]):
        if insn.id == 0:
            continue
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) in values:
                out[op.imm & 0xFFFFFFFF].append({"va": insn.address, "text": insn_text(insn)})
    return dict(out)


def jump_table_entries(b, table_va, count):
    return [
        struct.unpack("<I", b.read(table_va + 4 * i, 4))[0]
        for i in range(count)
    ]


def ecx_writes(instrs, site_idx):
    out = []
    for k, ins in enumerate(instrs[:site_idx]):
        if writes_reg(ins, "ECX"):
            out.append({"idx": k, "va": ins.address, "text": insn_text(ins)})
    return out


def zero_guard_on_ecx(instrs, site_idx):
    last = None
    for k in range(site_idx - 1, -1, -1):
        if writes_reg(instrs[k], "ECX"):
            last = k
            break
    if last is None:
        return {"last_write": None, "ecx_zero_tests": [], "forward_je": [], "guards_on_this": []}
    ecx_zero_tests = []
    forward_je = []
    for k in range(last, site_idx):
        ins = instrs[k]
        if ins.mnemonic == "test" and len(ins.operands) == 2:
            a, c = ins.operands
            if (a.type == c.type == capstone.x86.X86_OP_REG
                    and canon_reg(ins.reg_name(a.reg)) == "ECX"
                    and canon_reg(ins.reg_name(c.reg)) == "ECX"):
                ecx_zero_tests.append({"va": ins.address, "kind": "test ecx,ecx", "text": insn_text(ins)})
        if ins.mnemonic == "cmp" and len(ins.operands) == 2:
            a, c = ins.operands
            if (a.type == capstone.x86.X86_OP_REG
                    and canon_reg(ins.reg_name(a.reg)) == "ECX"
                    and c.type == capstone.x86.X86_OP_IMM and c.imm == 0):
                ecx_zero_tests.append({"va": ins.address, "kind": "cmp ecx,0", "text": insn_text(ins)})
        if ins.mnemonic in {"je", "jz"}:
            t = parse_target(ins.op_str)
            if t is not None and t > instrs[site_idx].address:
                forward_je.append({"va": ins.address, "target": t, "text": insn_text(ins)})
    return {
        "last_write": last,
        "last_write_text": insn_text(instrs[last]) if last is not None else None,
        "ecx_zero_tests": ecx_zero_tests,
        "forward_je": forward_je,
        "guards_on_this": ecx_zero_tests,
    }


def context(b, center: int, before=12, after=8):
    lo = center - before * 8 - 16
    hi = center + after * 8 + 16
    ins = [i for i in disasm_range(b, lo, hi) if i.id]
    out = []
    for i in ins:
        mark = ">>" if i.address == center else "  "
        out.append(f"{mark} {insn_text(i)}")
    return "\n".join(out)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    digest = sha256(EXE)
    b = Bin(EXE)
    rows = load_atlas()
    sw = full_sweep(b)
    sites = sorted(sw["calls"].get(TARGET_REMOVE, []))
    reports = []
    interesting_entries = {r["entry"] for r in rows if any(
        s in GAP_FUNCS and GAP_FUNCS[s][0] == r["entry"] for s in sites
    )}
    for s in GAP_FUNCS:
        interesting_entries.add(GAP_FUNCS[s][0])
    imm_by_value = imm_refs(b, interesting_entries)

    for site in sites:
        fn = containing(rows, site)
        gap = site in GAP_FUNCS
        if gap:
            start, end = GAP_FUNCS[site]
            fn = {"entry": start, "size": end - start, "raw": {"source": "independent-boundary"}}
        elif fn is None:
            reports.append({"site": site, "error": "no containing atlas interval"})
            continue
        else:
            start, end = fn["entry"], fn["entry"] + fn["size"]
        instrs = disasm_range(b, start, end)
        by_addr = {i.address: k for k, i in enumerate(instrs)}
        k = by_addr.get(site)
        if k is None:
            reports.append({"site": site, "fn": fn["entry"], "error": "site not an instruction boundary from fn entry"})
            continue
        ecx_w = ecx_writes(instrs, k)
        zguard = zero_guard_on_ecx(instrs, k)
        source = resolve_reg(instrs, k, "ECX")
        reach, path = reachable_from_entry(instrs, site)
        callers = sw["calls"].get(fn["entry"], [])
        fptrs = dword_refs(b, fn["entry"])
        imms = imm_by_value.get(fn["entry"], [])
        static_refs = len(callers) + len(fptrs) + len(imms)
        prev = []
        for j in range(max(0, k - 14), k + 2):
            if instrs[j].id:
                prev.append((">> " if instrs[j].address == site else "   ") + insn_text(instrs[j]))
        reports.append({
            "site": site,
            "site_hex": f"{site:08X}",
            "fn": fn["entry"],
            "fn_hex": f"{fn['entry']:08X}",
            "fn_size": fn["size"],
            "fn_source": fn.get("raw", {}).get("source", "atlas-interval"),
            "site_boundary": site in sw["starts"],
            "ecx_source": source,
            "ecx_writes": ecx_w,
            "zero_guard": zguard,
            "reachable_from_fn_entry": reach,
            "path_len": len(path),
            "direct_callers_of_fn": callers,
            "direct_caller_count": len(callers),
            "dword_refs_to_fn": fptrs[:10],
            "dword_ref_count": len(fptrs),
            "imm_refs_to_fn": imms[:10],
            "imm_ref_count": len(imms),
            "host_static_ref_count": static_refs,
            "host_reachability_grade": "static-ref" if static_refs else "zero-static-ref",
            "prev_14": prev,
        })

    # 0x6CD8CD
    fn6 = containing(rows, SITE_6CD8CD)
    jt6 = jump_table_entries(b, JT_6CC390, 12)
    ins6 = disasm_range(b, fn6["entry"], fn6["entry"] + fn6["size"])
    by6 = {i.address: k for k, i in enumerate(ins6)}
    k6 = by6[SITE_6CD8CD]
    reach6, path6 = reachable_from_entry(ins6, SITE_6CD8CD, extra_indirect_targets=jt6)
    six = {
        "site": SITE_6CD8CD,
        "fn": fn6["entry"],
        "fn_size": fn6["size"],
        "site_boundary": SITE_6CD8CD in sw["starts"],
        "eax_source": resolve_reg(ins6, k6, "EAX"),
        "ecx_source": resolve_reg(ins6, k6, "ECX"),
        "reachable_from_fn_entry": reach6,
        "reach_path_len": len(path6),
        "jump_table_entries": [f"{x:#010x}" for x in jt6],
        "direct_callers_of_fn": sw["calls"].get(fn6["entry"], []),
        "dword_refs_to_fn_count": len(dword_refs(b, fn6["entry"])),
        "prev_14": [(">> " if ins6[j].address == SITE_6CD8CD else "   ") + insn_text(ins6[j])
                    for j in range(max(0, k6 - 14), k6 + 4) if ins6[j].id],
    }

    remove_head = [insn_text(i) for i in disasm_range(b, TARGET_REMOVE, TARGET_REMOVE + 24) if i.id][:8]
    global_writers = {}
    for g in (GLOBAL_887368, GLOBAL_8871E0):
        writers = sw["mem_writes"].get(g, [])
        enriched = []
        for w in writers:
            wf = containing(rows, w["va"])
            enriched.append({
                **w,
                "writer_fn": wf["entry"] if wf else None,
                "callers_of_writer_fn": sw["calls"].get(wf["entry"], []) if wf else [],
            })
        global_writers[f"{g:08X}"] = {
            "mem_writes": writers,
            "imm_loads": sw["imm_loads"].get(g, []),
            "writers": enriched,
            "contexts": [
                {"va": w["va"], "text": w["text"], "ctx": context(b, w["va"], 10, 5)}
                for w in writers
            ],
        }

    core = {
        "sha256": digest,
        "sha256_ok": digest == EXPECTED_SHA,
        "image_base": b.image_base,
        "text": b.text,
        "sweep": {
            "insn_count": sw["insn_count"],
            "skipdata_bytes": sw["skip_count"],
            "calls_to_724730": sites,
            "calls_to_724730_count": len(sites),
            "raw_e8_hits_to_724730": [
                {"site": s, "instruction_boundary": s in sw["starts"]}
                for s in sites
            ],
        },
        "remove_head": remove_head,
        "sites": reports,
        "site_6cd8cd": six,
        "global_writers": global_writers,
    }
    with open(os.path.join(OUTDIR, "w178_core.json"), "w", encoding="utf-8") as f:
        json.dump(core, f, ensure_ascii=False, indent=2)

    lines = []
    lines.append(f"SHA256={digest} OK={digest == EXPECTED_SHA}")
    lines.append(f"ImageBase={b.image_base:#x} .text={b.text}")
    lines.append(f"FULL_SWEEP insn_count={sw['insn_count']} skipdata_bytes={sw['skip_count']}")
    lines.append(f"calls_to_724730={len(sites)}")
    lines.append("SITES " + " ".join(f"{s:08X}" for s in sites))
    lines.append("REMOVE_HEAD")
    lines.extend("  " + x for x in remove_head)
    lines.append("")
    for r in reports:
        lines.append(f"=== SITE {r.get('site_hex', r.get('site'))} ===")
        if "error" in r:
            lines.append("ERROR " + r["error"])
            continue
        lines.append(f"fn={r['fn_hex']} size={r['fn_size']} fn_source={r['fn_source']} "
                     f"boundary={r['site_boundary']} reachable_from_entry={r['reachable_from_fn_entry']} "
                     f"path_len={r['path_len']}")
        lines.append(f"ecx_source={r['ecx_source']}")
        lines.append(f"zero_guard={json.dumps(r['zero_guard'], ensure_ascii=False)}")
        lines.append(f"ecx_writes_count={len(r['ecx_writes'])}")
        for w in r["ecx_writes"]:
            lines.append("  ECXW " + w["text"])
        lines.append(f"direct_callers_of_fn_count={r['direct_caller_count']} "
                     f"callers={[hex(x) for x in r['direct_callers_of_fn'][:8]]}")
        lines.append(f"dword_refs_to_fn_count={r['dword_ref_count']} imm_refs_to_fn_count={r['imm_ref_count']} "
                     f"host_grade={r['host_reachability_grade']}")
        lines.extend(r["prev_14"])
        lines.append("")
    lines.append("=== SITE 006CD8CD ===")
    for k2, v2 in six.items():
        if k2 != "prev_14":
            lines.append(f"{k2}={v2}")
    lines.extend(six["prev_14"])
    lines.append("")
    for g, payload in global_writers.items():
        lines.append(f"=== GLOBAL 0x{g} ===")
        lines.append("mem_writes=" + json.dumps(payload["mem_writes"], ensure_ascii=False))
        lines.append("imm_loads=" + json.dumps(payload["imm_loads"], ensure_ascii=False))
        for c in payload["contexts"]:
            lines.append(f"--- writer {c['va']:#x} ---")
            lines.append(c["ctx"])
        lines.append("")
    with open(os.path.join(OUTDIR, "w178_dump.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # compact site table for downstream
    tsv = []
    for r in reports:
        tsv.append("\t".join([
            r.get("site_hex", ""),
            r.get("fn_hex", ""),
            r.get("ecx_source", "").replace("\t", " "),
            str(r.get("reachable_from_fn_entry", "")),
            str(r.get("direct_caller_count", "")),
            str(len(r.get("ecx_writes", []))),
            r.get("host_reachability_grade", ""),
            str(len(r.get("zero_guard", {}).get("ecx_zero_tests", []))),
        ]))
    with open(os.path.join(OUTDIR, "site_table.tsv"), "w", encoding="utf-8") as f:
        f.write("site\tfn\tecx_source\treachable_from_fn_entry\tdirect_caller_count\tecx_write_count\thost_grade\tecx_zero_tests_after_last_write\n")
        f.write("\n".join(tsv))

    print(json.dumps({
        "sha256_ok": digest == EXPECTED_SHA,
        "insn_count": sw["insn_count"],
        "skipdata_bytes": sw["skip_count"],
        "call_count": len(sites),
        "site_boundaries": sum(1 for r in reports if r.get("site_boundary")),
        "ecx_global_887368": sum(1 for r in reports if "0x887368" in r.get("ecx_source", "")),
        "reachable_from_entry": sum(1 for r in reports if r.get("reachable_from_fn_entry")),
        "zero_static_ref_hosts": sum(1 for r in reports if r.get("host_reachability_grade") == "zero-static-ref"),
        "proven_reachable_null_sites": sum(1 for r in reports if r.get("reachable_from_fn_entry") and r.get("host_reachability_grade") == "static-ref"),
        "ecx_zero_guard_sites": sum(1 for r in reports if r.get("zero_guard", {}).get("ecx_zero_tests")),
        "six_boundary": six["site_boundary"],
        "six_reachable": six["reachable_from_fn_entry"],
        "six_callers": len(six["direct_callers_of_fn"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
