#!/usr/bin/env python3
"""R143 blind byte-evidence verifier (independent implementation)."""
import collections
import hashlib
import json
import os
import random
import re
import struct
import subprocess
import sys

import capstone
import pefile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXE = os.path.join(ROOT, "ra2bench", "gamemd.exe")
OBJ_STARTS = os.path.join(ROOT, "_r140", "obj_starts.txt")
OUT = os.path.join(os.path.dirname(__file__), "sub_result.json")
IMAGE_BASE = 0x400000
CHUNK = 0x10000
GPR = {"eax", "ebx", "ecx", "edx", "esi", "edi"}
ANY_GPR = GPR | {"esp", "ebp"}
ARITH_MNEMONICS = {
    "add", "sub", "adc", "sbb", "and", "or", "xor", "inc", "dec", "neg",
    "not", "shl", "shr", "sar", "sal", "rol", "ror", "imul", "xchg",
    "bswap", "mul", "div", "idiv",
}
REG_RE = re.compile(r"^([a-z]{3})$")
REG_OFF_RE = re.compile(r"^([a-z]{3})([+-]0x[0-9a-f]+)$")
IMM_RE = re.compile(r"^(0x[0-9a-f]+|[0-9]+)$")
MEM_DWORD_RE = re.compile(r"^dword ptr \[([^\]]+)\]$")
MOV_MEM_IMM_RE = re.compile(r"^dword ptr \[([^\]]+)\],(.+)$")
MOV_REG_MEM_RE = re.compile(r"^([a-z]{3}),dword ptr \[([^\]]+)\]$")
NAME_RE = re.compile(rb"\.\?A[VU][!-~]{1,200}?@@")


def norm(text):
    return re.sub(r"\s*([+,*])\s*", r"\1", text.strip())


def parse_int(text):
    text = text.strip()
    if text.lower().startswith("0x"):
        return int(text, 16)
    if text[:1] in ("+", "-") and text[1:].lower().startswith("0x"):
        return int(text, 16)
    return int(text, 10)


def parse_base_offset(text):
    """Return (base, displacement) for [X], [X+0xN], [X-0xN], else None."""
    m = REG_RE.match(text)
    if m:
        return m.group(1), 0
    m = REG_OFF_RE.match(text)
    if m:
        return m.group(1), parse_int(m.group(2))
    return None


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_sections():
    pe = pefile.PE(EXE, fast_load=True)
    image_base = int(pe.OPTIONAL_HEADER.ImageBase)
    if image_base != IMAGE_BASE:
        raise RuntimeError("unexpected image base: %#x" % image_base)
    sections = []
    for section in pe.sections:
        name = section.Name.rstrip(b"\x00").decode("ascii", "replace")
        sections.append({
            "name": name,
            "va": image_base + int(section.VirtualAddress),
            "vsize": int(section.Misc_VirtualSize),
            "ptr": int(section.PointerToRawData),
            "rsize": int(section.SizeOfRawData),
        })
    by_name = {item["name"]: item for item in sections}
    return sections, by_name


def make_dword_reader(data, sections):
    def dword(va):
        if va is None or va < 0:
            return None
        for section in sections:
            base, ptr, size = section["va"], section["ptr"], section["rsize"]
            if base <= va and va + 4 <= base + size:
                offset = ptr + (va - base)
                if offset >= 0 and offset + 4 <= len(data):
                    return struct.unpack_from("<I", data, offset)[0]
                return None
        return None
    return dword


def build_vts(data, sections, dword):
    data_sections = [s for s in sections if s["name"] in (".data", ".rdata")]
    td = set()
    name_count = 0
    for section in data_sections:
        base, ptr, size = section["va"], section["ptr"], section["rsize"]
        blob = data[ptr:ptr + size]
        for match in NAME_RE.finditer(blob):
            name_count += 1
            start = base + match.start()
            if dword(start - 4) == 0 and dword(start - 8) is not None:
                td.add(start - 8)

    col = set()
    for section in data_sections:
        base, ptr, size = section["va"], section["ptr"], section["rsize"]
        for offset in range(ptr, ptr + size - 3, 4):
            value = struct.unpack_from("<I", data, offset)[0]
            if value not in td:
                continue
            va = base + (offset - ptr)
            candidate = va - 12
            if (dword(candidate) == 0 and dword(candidate + 12) == value
                    and dword(candidate + 16) not in (0, None)):
                col.add(candidate)

    vts = set()
    for section in data_sections:
        base, ptr, size = section["va"], section["ptr"], section["rsize"]
        for offset in range(ptr, ptr + size - 3, 4):
            value = struct.unpack_from("<I", data, offset)[0]
            if value not in col:
                continue
            va = base + (offset - ptr)
            vt = va + 4
            if dword(vt - 4) == value:
                vts.add(vt)
    return td, col, vts, name_count


def iter_instructions(section):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    base = section["va"]
    ptr = section["ptr"]
    size = section["rsize"]
    pending = b""
    pending_va = base
    with open(EXE, "rb") as handle:
        handle.seek(ptr)
        position = 0
        while position < size:
            chunk = handle.read(min(CHUNK, size - position))
            if not chunk:
                break
            chunk_va = base + position
            blob = pending + chunk
            blob_va = pending_va if pending else chunk_va
            instructions = list(md.disasm_lite(blob, blob_va))
            consumed = 0
            for address, length, mnemonic, op_str in instructions:
                if address + length > chunk_va + len(chunk) and position + len(chunk) < size:
                    break
                consumed += length
                yield address, mnemonic, norm(op_str)
            tail = address + length - (chunk_va + len(chunk))
            if tail > 0 and position + len(chunk) < size:
                pending = blob[address - blob_va:]
                pending_va = address
            else:
                pending = b""
                pending_va = chunk_va + len(chunk)
            position += len(chunk)


def collect_writes(instructions, vts):
    reg_writes = []
    absolute_writes = 0
    for address, mnemonic, operands in instructions:
        if mnemonic != "mov":
            continue
        match = MOV_MEM_IMM_RE.match(operands)
        if not match or not IMM_RE.match(match.group(2)):
            continue
        target = match.group(1)
        base_offset = parse_base_offset(target)
        if base_offset is not None and base_offset[0] in GPR:
            base, displacement = base_offset
            reg_writes.append({
                "site": address,
                "base": base,
                "disp": displacement,
                "imm": parse_int(match.group(2)),
            })
        elif target.startswith("0x"):
            absolute_writes += 1
    in_vts = [item for item in reg_writes if item["imm"] in vts]
    zero = [item for item in in_vts if item["disp"] == 0]
    nonzero = [item for item in in_vts if item["disp"] != 0]
    zero_vts = {item["imm"] for item in zero}
    nonzero_vts = {item["imm"] for item in nonzero}
    histogram = collections.Counter(item["disp"] for item in in_vts)
    return {
        "all_register_indexed_writes": len(reg_writes),
        "absolute_global_writes_excluded": absolute_writes,
        "writes_with_imm_in_vts": len(in_vts),
        "vts_writes_disp_zero": len(zero),
        "vts_writes_disp_nonzero": len(nonzero),
        "vts_writes_disp_zero_distinct_vt": len(zero_vts),
        "vts_writes_disp_zero_distinct_over_vts": round(len(zero_vts) / len(vts), 6) if vts else None,
        "vts_writes_disp_nonzero_distinct_vt": len(nonzero_vts),
        "vts_writes_displacement_histogram_top8": [
            {"disp": disp, "count": count}
            for disp, count in sorted(histogram.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
    }, [item["site"] for item in zero], in_vts


def collect_dispatch_and_loads(instructions, vts, function_starts):
    dispatch_points = []
    all_mem_loads = []
    all_mem_loads_zero = 0
    state = {}
    state["*"] = {"kind": "unknown"}
    pending_reset = False

    def set_reg(reg, value):
        state[reg] = dict(value)

    def others():
        return {"kind": "other"}

    for address, mnemonic, operands in instructions:
        if pending_reset:
            state.clear()
            state["*"] = {"kind": "unknown"}
            pending_reset = False
        if mnemonic == "mov":
            match = MOV_REG_MEM_RE.match(operands)
            if match and match.group(1) in ANY_GPR:
                reg = match.group(1)
                base_offset = parse_base_offset(match.group(2))
                if base_offset is not None:
                    base, displacement = base_offset
                    all_mem_loads.append((address, base, displacement))
                    if displacement == 0:
                        all_mem_loads_zero += 1
                    set_reg(reg, {
                        "kind": "load", "base": base, "disp": displacement,
                        "va": address,
                    })
                else:
                    set_reg(reg, others())
            else:
                first = operands.split(",", 1)[0].strip()
                if first in ANY_GPR:
                    set_reg(first, others())
        elif mnemonic == "lea":
            first = operands.split(",", 1)[0].strip()
            if first in ANY_GPR:
                set_reg(first, others())
        elif mnemonic == "pop":
            if operands in ANY_GPR:
                set_reg(operands, others())
        elif mnemonic in ARITH_MNEMONICS:
            first = operands.split(",", 1)[0].strip()
            if first in ANY_GPR:
                set_reg(first, others())
        elif mnemonic in ("call", "jmp"):
            match = MEM_DWORD_RE.match(operands)
            if match:
                base_offset = parse_base_offset(match.group(1))
                if base_offset is not None and base_offset[0] in GPR:
                    info = state.get(base_offset[0], state["*"])
                    dispatch_points.append({
                        "site": address,
                        "mnemonic": mnemonic,
                        "base": base_offset[0],
                        "disp": base_offset[1],
                        "kind": info["kind"],
                        "load": {
                            "base": info.get("base"),
                            "disp": info.get("disp"),
                            "va": info.get("va"),
                        } if info["kind"] == "load" else None,
                    })
            if mnemonic == "call":
                for reg in ("eax", "ecx", "edx"):
                    set_reg(reg, {"kind": "clobber"})
    return dispatch_points, all_mem_loads, all_mem_loads_zero


def summarize_c2(dispatch_points):
    kind_histogram = collections.Counter(item["kind"] for item in dispatch_points)
    loads = [item for item in dispatch_points if item["kind"] == "load"]
    stack = [item for item in loads if item["load"]["base"] in ("esp", "ebp")]
    obj = [item for item in loads if item["load"]["base"] in GPR]
    unknown_other = [item for item in loads if item["load"]["base"] not in ("esp", "ebp") and item["load"]["base"] not in GPR]
    stack_zero = sum(1 for item in stack if item["load"]["disp"] == 0)
    obj_zero = sum(1 for item in obj if item["load"]["disp"] == 0)
    return {
        "dispatch_total": len(dispatch_points),
        "dispatch_kind_histogram": dict(sorted(kind_histogram.items())),
        "dispatch_kind_load_total": len(loads),
        "dispatch_kind_load_stack_total": len(stack),
        "dispatch_kind_load_stack_disp_zero": stack_zero,
        "dispatch_kind_load_stack_disp_zero_ratio": round(stack_zero / len(stack), 6) if stack else None,
        "dispatch_kind_load_object_total": len(obj),
        "dispatch_kind_load_object_disp_zero": obj_zero,
        "dispatch_kind_load_object_disp_zero_ratio": round(obj_zero / len(obj), 6) if obj else None,
        "dispatch_kind_load_other_base_total": len(unknown_other),
    }, obj


def summarize_c3(obj_loads, all_mem_loads, all_mem_loads_zero, vts):
    baseline_ratio = all_mem_loads_zero / len(all_mem_loads) if all_mem_loads else 0.0
    obj_zero = sum(1 for item in obj_loads if item["load"]["disp"] == 0)
    obj_ratio = obj_zero / len(obj_loads) if obj_loads else 0.0
    enrichment = obj_ratio / baseline_ratio if baseline_ratio else None
    shifted = {}
    for displacement in (0, 4, 8, 0xc, 0x10):
        count = sum(1 for item in obj_loads if item["load"]["disp"] == displacement)
        shifted["disp_%s" % (hex(displacement) if displacement else "0")] = count
    return {
        "all_memory_loads": len(all_mem_loads),
        "all_memory_loads_disp_zero": all_mem_loads_zero,
        "all_memory_loads_disp_zero_ratio": round(baseline_ratio, 6),
        "object_load_disp_zero_ratio": round(obj_ratio, 6),
        "enrichment_over_unconditional_baseline": round(enrichment, 6) if enrichment is not None else None,
        "object_load_displacement_counts": shifted,
    }


def fake_control(data, sections, vts, disp_zero_sites):
    values = []
    for section in sections:
        if section["name"] not in (".data", ".rdata"):
            continue
        ptr, size = section["ptr"], section["rsize"]
        for offset in range(ptr, ptr + size - 3, 4):
            values.append(struct.unpack_from("<I", data, offset)[0])
    rng = random.Random(143)
    fake_set = set(rng.sample(values, len(vts))) if len(values) >= len(vts) else set(values)
    fake_zero_sites = [site for site, imm in disp_zero_sites if imm in fake_set]
    fake_distinct = {imm for site, imm in disp_zero_sites if imm in fake_set}
    return {
        "sample_pool_aligned_dwords": len(values),
        "sample_size": len(vts),
        "fake_vt_set_size": len(fake_set),
        "fake_vt_set_disp_zero_sites": len(fake_zero_sites),
        "fake_vt_set_disp_zero_distinct_covered": len(fake_distinct),
    }


def load_function_starts(text_section):
    """Approximate function entries as objdump starts after a linear gap."""
    with open(OBJ_STARTS, "rt") as handle:
        starts = [int(line.strip(), 16) for line in handle if line.strip()]
    low = text_section["va"]
    high = low + text_section["rsize"]
    result = set()
    previous = None
    for address in starts:
        if low <= address < high and (previous is None or address != previous + 1):
            result.add(address)
        previous = address
    return result, len(starts)


def obdump_control(dispatch_points, section, starts=None):
    if starts is None:
        with open(OBJ_STARTS, "rt") as handle:
            starts = {int(line.strip(), 16) for line in handle if line.strip()}
    sites = [item["site"] for item in dispatch_points]
    hit = sum(1 for site in sites if site in starts)
    return {
        "objdump_text_instruction_starts": len(starts),
        "dispatch_sites": len(sites),
        "dispatch_sites_in_objdump_starts": hit,
        "dispatch_coverage_ratio": round(hit / len(sites), 6) if sites else None,
        "baseline_starts_over_text_raw_size": round(len(starts) / section["rsize"], 6),
        "baseline_size_ratio_over_coverage": round((len(starts) / section["rsize"]) / (hit / len(sites)), 6) if hit else None,
    }


def fixed_bytes(dword):
    start = 0x47C420
    end = 0x47C450
    offset = dword(start)
    del offset
    for section in SECTIONS:
        if section["va"] <= start and end <= section["va"] + section["rsize"]:
            file_offset = section["ptr"] + (start - section["va"])
            break
    else:
        raise RuntimeError("fixed byte range not mapped")
    with open(EXE, "rb") as handle:
        handle.seek(file_offset)
        blob = handle.read(end - start)
    temp = os.path.join(os.path.dirname(__file__), "sub_47c420.bin")
    with open(temp, "wb") as handle:
        handle.write(blob)
    output = subprocess.run(
        ["i686-w64-mingw32-objdump", "-D", "-b", "binary", "-m", "i386",
         "--adjust-vma=" + hex(start), temp],
        capture_output=True, text=True, check=True,
    ).stdout
    objdump = {}
    for line in output.splitlines():
        match = re.match(r"\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(.*)", line)
        if match:
            address = int(match.group(1), 16)
            objdump[address] = {
                "bytes": "".join(match.group(2).split()),
                "text": match.group(3).strip(),
            }
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    cap = {}
    for address, size, mnemonic, op_str in md.disasm_lite(blob, start):
        cap[address] = {
            "bytes": blob[address - start:address - start + size].hex(),
            "mnemonic": mnemonic,
            "op_str": norm(op_str),
        }
    targets = {}
    for address in (0x47C437, 0x47C440):
        od = objdump.get(address, {})
        cs = cap.get(address, {})
        targets[hex(address)] = {
            "objdump_bytes": od.get("bytes"),
            "objdump_text": od.get("text"),
            "capstone_bytes": cs.get("bytes"),
            "capstone_mnemonic": cs.get("mnemonic"),
            "capstone_op_str": cs.get("op_str"),
            "bytes_match": od.get("bytes") == cs.get("bytes"),
        }
    return {
        "range": "0x47c420..0x47c450",
        "file_offset": hex(file_offset),
        "raw_bytes": blob.hex(),
        "instructions": targets,
    }


def main():
    global SECTIONS
    with open(EXE, "rb") as handle:
        data = handle.read()
    sections, by_name = load_sections()
    SECTIONS = sections
    dword = make_dword_reader(data, sections)
    td, col, vts, name_count = build_vts(data, sections, dword)
    instructions = list(iter_instructions(by_name[".text"]))
    function_starts, objdump_start_count = load_function_starts(by_name[".text"])
    c1, disp_zero_sites, c1_in_vts = collect_writes(instructions, vts)
    dispatch_points, all_mem_loads, all_mem_loads_zero = collect_dispatch_and_loads(
        instructions, vts, function_starts)
    c2, obj_loads = summarize_c2(dispatch_points)
    c3 = summarize_c3(obj_loads, all_mem_loads, all_mem_loads_zero, vts)
    c4 = fake_control(data, sections, vts, [(item["site"], item["imm"]) for item in c1_in_vts if item["disp"] == 0])
    c5 = obdump_control(dispatch_points, by_name[".text"], starts=None)
    c6 = fixed_bytes(dword)
    result = {
        "card": "R143 blind byte-evidence verification",
        "binary": {
            "path": os.path.relpath(EXE, ROOT),
            "size": len(data),
            "sha256": sha256_file(EXE),
            "image_base": hex(IMAGE_BASE),
        },
        "vts": {
            "decorated_names": name_count,
            "td_count": len(td),
            "col_count": len(col),
            "vts_distinct": len(vts),
        },
        "text_scan": {
            "chunk_size": hex(CHUNK),
            "instruction_count": len(instructions),
        },
        "function_boundary_approximation": {
            "objdump_text_instruction_starts": objdump_start_count,
            "approximate_function_starts": len(function_starts),
            "method": "linear_start_with_gap",
        },
        "c1_write_side": c1,
        "c2_read_side": c2,
        "c3_control": c3,
        "c3d_fake_vt_control": c4,
        "c3e_independent_decoder_control": c5,
        "c6_fixed_bytes": c6,
    }
    with open(OUT, "wt") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print("\nSELF-CHECK")
    print("binary sha256", result["binary"]["sha256"])
    print("TD", len(td), "COL", len(col), "VTS", len(vts), "names", name_count)
    print("text instructions", len(instructions))
    print("C1 writes in VTS", c1["writes_with_imm_in_vts"], "disp0", c1["vts_writes_disp_zero"],
          "nonzero", c1["vts_writes_disp_nonzero"], "disp0 distinct vt", c1["vts_writes_disp_zero_distinct_vt"],
          "ratio", c1["vts_writes_disp_zero_distinct_over_vts"], "nonzero distinct", c1["vts_writes_disp_nonzero_distinct_vt"])
    print("C1 histogram", c1["vts_writes_displacement_histogram_top8"])
    print("C2 dispatch", c2["dispatch_total"], "kinds", c2["dispatch_kind_histogram"])
    print("C2 stack", c2["dispatch_kind_load_stack_total"], c2["dispatch_kind_load_stack_disp_zero"],
          c2["dispatch_kind_load_stack_disp_zero_ratio"], "object", c2["dispatch_kind_load_object_total"],
          c2["dispatch_kind_load_object_disp_zero"], c2["dispatch_kind_load_object_disp_zero_ratio"])
    print("C3 baseline", c3["all_memory_loads"], c3["all_memory_loads_disp_zero"],
          c3["all_memory_loads_disp_zero_ratio"], "enrichment", c3["enrichment_over_unconditional_baseline"],
          "shifted", c3["object_load_displacement_counts"])
    print("C3d fake", c4)
    print("C3e objdump", c5)
    print("C6 fixed", c6["instructions"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
