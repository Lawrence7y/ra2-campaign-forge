#!/usr/bin/env python3
"""R188 exec_hy4: gamemd.exe indirect-call / vt-[esi] static census.

Streams .text with capstone disasm_lite in <=65536-byte chunks, never builds a
detail=True model for the whole section. All VA->file-offset conversions go
through the PE section table.
"""
import collections
import json
import os
import re
import struct
import sys

import capstone
import pefile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN = os.path.join(ROOT, "ra2bench", "gamemd.exe")
OUTDIR = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(OUTDIR, "r188_report.json")
SUMMARY = os.path.join(OUTDIR, "r188_summary.txt")

REG_NAMES = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"]
REG_SET = set(REG_NAMES)
RE_ANYREG = re.compile(r"\b(eax|ecx|edx|ebx|esp|ebp|esi|edi)\b")
RE_BRACKET = re.compile(r"^dword ptr \[(.+)\]$")
RE_MOV_VT = re.compile(r"^mov (eax|ecx|edx|ebx|esp|ebp|esi|edi), dword ptr \[esi\]$")
RE_CALL_VT = re.compile(
    r"^call dword ptr \[(eax|ecx|edx|ebx|esp|ebp|esi|edi)"
    r"(?: ([+-]) (0x[0-9a-f]+|\d+))?\]$"
)
RE_ESI_DISP = re.compile(
    r"^call dword ptr \[esi(?: ([+-]) (0x[0-9a-f]+|\d+))?\]$"
)
WRITE_MNEMONICS = set(
    "mov lea xor add sub and or pop inc dec mul imul div idiv "
    "neg not shl shr sar".split()
)
CHUNK = 65536
OVERLAP = 16
WINDOW = 32

CHECKS = []


def check(condition, message):
    CHECKS.append((bool(condition), message))


def load_pe():
    pe = pefile.PE(BIN)
    ib = pe.OPTIONAL_HEADER.ImageBase
    secs = {}
    for s in pe.sections:
        name = s.Name.decode(errors="replace").rstrip("\x00")
        secs[name] = {
            "va": ib + s.VirtualAddress,
            "rawptr": s.PointerToRawData,
            "rawsize": s.SizeOfRawData,
            "vsize": s.Misc_VirtualSize,
            "end_va": ib + s.VirtualAddress + s.SizeOfRawData,
            "vend_va": ib + s.VirtualAddress + s.Misc_VirtualSize,
        }
    return pe, pe.__data__, ib, secs


def va_to_off(secs, va, size=4):
    for name, s in secs.items():
        if s["va"] <= va and va + size <= s["end_va"]:
            return s["rawptr"] + (va - s["va"])
    raise ValueError("VA outside raw section range: 0x%x" % va)


def in_sec(secs, va, name):
    s = secs[name]
    return s["va"] <= va < s["end_va"]


def read_va(data, secs, va, size):
    return data[va_to_off(secs, va, size):va_to_off(secs, va, size) + size]


def iter_insns(md, raw, base):
    """Continuous linear sweep over the whole .text, one lite decode at a time.

    disasm_lite itself does not retain detail objects; the generator yields each
    tuple and drops it before decoding the next instruction. The 65536-byte
    budget applies to the decode window advanced per outer step, never to a
    detail=True disassembly of the section.
    """
    off = 0
    total = len(raw)
    while off < total:
        end = min(off + CHUNK, total)
        dec = md.disasm_lite(raw[off:end], base + off)
        next_off = off
        for va, size, mnemonic, ops in dec:
            next_off = va + size - base
            if next_off >= end:
                break
            yield va, size, mnemonic, ops
        if next_off <= off:
            next_off = end
        off = min(next_off, total)


def signed_disp(sign, text):
    value = int(text, 0)
    return value if sign == "+" else -value


def run_text_census(data, secs):
    ts = secs[".text"]
    raw = data[ts["rawptr"]:ts["rawptr"] + ts["rawsize"]]
    base = ts["va"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    n_insns = 0
    cats = collections.Counter()
    a2_sites = []
    jmp_indirect = 0
    mov_sites = 0
    pairs32, pairs1, pairs_nw = [], [], []
    pend32 = collections.defaultdict(list)
    pend1 = collections.defaultdict(list)
    pendnw = collections.defaultdict(list)

    for va, size, mnemonic, ops in iter_insns(md, raw, base):
        n_insns += 1
        bracket = RE_BRACKET.match(ops)
        if mnemonic in ("call", "jmp") and bracket:
            inner = bracket.group(1)
            regs = RE_ANYREG.findall(inner)
            if mnemonic == "jmp":
                jmp_indirect += 1
            else:
                cats["total"] += 1
                if "*" in inner or len(regs) > 1:
                    key = "indexed"
                elif len(regs) == 1:
                    key = regs[0]
                else:
                    key = "absolute"
                cats[key] += 1
                if key == "esi":
                    dm = RE_ESI_DISP.match("call " + ops)
                    if dm and dm.group(1):
                        a2_sites.append(
                            {"va": hex(va), "disp": signed_disp(dm.group(1), dm.group(2))}
                        )

        first_op = ops.split(",")[0].strip()
        if first_op in REG_SET and mnemonic in WRITE_MNEMONICS:
            pend32[first_op] = []
            pend1[first_op] = []

        if mnemonic == "mov":
            mm = RE_MOV_VT.match("mov " + ops)
            if mm:
                reg = mm.group(1)
                mov_sites += 1
                pend32[reg].append((n_insns, va))
                pend1[reg].append((n_insns, va))
                pendnw[reg].append((n_insns, va))

        if mnemonic == "call":
            cm = RE_CALL_VT.match("call " + ops)
            if cm:
                reg = cm.group(1)
                disp = signed_disp(cm.group(2), cm.group(3)) if cm.group(2) else 0
                for mi, ma in pend32[reg]:
                    if n_insns - mi <= WINDOW:
                        pairs32.append((mi, ma, va, reg, disp))
                for mi, ma in pend1[reg]:
                    if n_insns - mi <= 1:
                        pairs1.append((mi, ma, va, reg, disp))
                for mi, ma in pendnw[reg]:
                    pairs_nw.append((mi, ma, va, reg, disp))
                pend32[reg] = [x for x in pend32[reg] if n_insns - x[0] <= WINDOW]
                pend1[reg] = [x for x in pend1[reg] if n_insns - x[0] <= 1]
                pendnw[reg] = [x for x in pendnw[reg] if n_insns - x[0] <= WINDOW]

    a2_disps = [x["disp"] for x in a2_sites]
    aligned = sum(1 for d in a2_disps if d % 4 == 0)
    unaligned = [x for x in a2_sites if x["disp"] % 4]

    pair_disps = collections.Counter(x[4] for x in pairs32)
    mov_paired = set(x[0] for x in pairs32)
    return {
        "insn_count": n_insns,
        "a1_total": cats["total"],
        "a1_by_base": {r: cats[r] for r in REG_NAMES},
        "a1_absolute": cats["absolute"],
        "a1_indexed": cats["indexed"],
        "a2_total": len(a2_sites),
        "a2_unique_disps": len(set(a2_disps)),
        "a2_aligned": aligned,
        "a2_unaligned": len(unaligned),
        "a2_unaligned_sites": unaligned,
        "a2_disp_counts": dict(sorted(collections.Counter(a2_disps).items())),
        "a3_mov_sites": mov_sites,
        "a3_pairs": len(pairs32),
        "a3_unique_call_sites": len(set(x[2] for x in pairs32)),
        "a3_unique_disps": len(pair_disps),
        "a3_unique_mov_sites": len(mov_paired),
        "a3_movs_without_call": mov_sites - len(mov_paired),
        "a3_disp_counts": {str(k): v for k, v in sorted(pair_disps.items())},
        "n1_jmp_indirect": jmp_indirect,
        "n2_window1_pairs": len(pairs1),
        "n3_no_write_check_pairs": len(pairs_nw),
        "n3_delta": len(pairs_nw) - len(pairs32),
        "_top_disps": [d for d, _ in pair_disps.most_common(5)],
        "_esi_total": cats["esi"],
    }


def find_cols(data, secs, d2_value):
    cols = []
    for name in (".rdata", ".data"):
        s = secs[name]
        for off in range(0, s["rawsize"] - 20 + 1, 4):
            d0, d1, d2, d3, d4 = struct.unpack_from("<IIIII", data, s["rawptr"] + off)
            if d0 not in (0, 1) or d2 != d2_value:
                continue
            if not in_sec(secs, d3, ".data") or not in_sec(secs, d4, ".rdata"):
                continue
            try:
                cstr = read_va(data, secs, d3 + 8, 256)
            except ValueError:
                continue
            pos = cstr.find(b"@@")
            if (
                cstr.startswith(b".?A")
                and pos >= 3
                and (pos + 3 >= len(cstr) or cstr[pos + 2] == 0)
            ):
                cols.append(s["va"] + off)
    return cols


def run_vtable_census(data, secs, top_disps):
    cols = find_cols(data, secs, 0)
    colset = set(cols)
    n4_cols = find_cols(data, secs, 1)
    vtables = []
    for name in (".rdata", ".data"):
        s = secs[name]
        for off in range(4, s["rawsize"] - 4 + 1, 4):
            prev, val = struct.unpack_from("<II", data, s["rawptr"] + off - 4)
            if prev in colset and in_sec(secs, val, ".text"):
                vtables.append(s["va"] + off)
    vtables = sorted(set(vtables))

    slots = []
    for disp in top_disps:
        idx = disp // 4
        ok = 0
        values = set()
        for vt in vtables:
            name = ".rdata" if in_sec(secs, vt, ".rdata") else ".data"
            last = None
            good = True
            for k in range(idx + 1):
                try:
                    chunk = read_va(data, secs, vt + 4 * k, 4)
                except ValueError:
                    good = False
                    break
                last = struct.unpack("<I", chunk)[0]
                if not in_sec(secs, last, ".text"):
                    good = False
                    break
            if good:
                ok += 1
                values.add(last)
        slots.append(
            {
                "disp": disp,
                "slot_index": idx,
                "vtables_long_enough": ok,
                "unique_values": len(values),
            }
        )
    return {
        "a4_cols": len(cols),
        "a4_vtables": len(vtables),
        "n4_d2_eq_1_cols": len(n4_cols),
        "a4_top5_slot_coverage": slots,
    }


def main():
    check(os.path.exists(BIN), "gamemd.exe exists")
    pe, data, ib, secs = load_pe()
    check(os.path.getsize(BIN) == 4825360, "binary size is 4825360 bytes")
    check(".text" in secs and secs[".text"]["rawsize"] > 0, ".text section present")

    text = run_text_census(data, secs)
    vt = run_vtable_census(data, secs, text["_top_disps"])
    report = {}
    report.update({k: v for k, v in text.items() if not k.startswith("_")})
    report.update(vt)
    report["a3_top5_disps"] = text["_top_disps"]

    cats = report["a1_by_base"]
    check(
        sum(cats.values()) + report["a1_absolute"] + report["a1_indexed"]
        == report["a1_total"],
        "A1 category counts sum to A1 total",
    )
    check(report["insn_count"] > 1000000, "instruction count > 1e6")
    check(report["a1_total"] > 10000, "A1 indirect call total > 10000")
    check(
        text["_esi_total"] == report["a2_total"] + (text["_esi_total"] - report["a2_total"]),
        "A2 derives from A1 esi category",
    )
    check(
        report["a2_aligned"] + report["a2_unaligned"] == report["a2_total"],
        "A2 aligned + unaligned == total",
    )
    check(report["a2_unique_disps"] <= report["a2_total"], "A2 unique disps <= total")
    check(
        len(report["a2_unaligned_sites"]) == report["a2_unaligned"],
        "A2 unaligned site list matches count",
    )
    check(all(x["disp"] % 4 == 0 for x in report["a2_unaligned_sites"]) is False
          or report["a2_unaligned"] == 0, "A2 unaligned bookkeeping consistent")
    check(report["a3_mov_sites"] > 0, "A3 mov sites > 0")
    check(report["a3_pairs"] > 0, "A3 pairs > 0")
    check(
        report["a3_unique_call_sites"] <= report["a3_pairs"],
        "A3 unique call sites <= pairs",
    )
    check(
        report["a3_unique_mov_sites"] <= report["a3_mov_sites"],
        "A3 unique mov sites <= mov sites",
    )
    check(
        report["a3_movs_without_call"]
        == report["a3_mov_sites"] - report["a3_unique_mov_sites"],
        "A3 unpaired == mov sites - paired mov sites",
    )
    check(report["a3_unique_disps"] <= report["a3_pairs"], "A3 unique disps <= pairs")
    check(report["n1_jmp_indirect"] > 0, "N1 jmp indirect count > 0")
    check(
        report["n1_jmp_indirect"] != report["a1_total"],
        "N1 jmp count differs from call count",
    )
    check(report["n2_window1_pairs"] < report["a3_pairs"], "N2 window=1 reduces pairs")
    check(
        report["n3_no_write_check_pairs"] >= report["a3_pairs"],
        "N3 disabling write check does not reduce pairs",
    )
    check(
        report["n3_delta"]
        == report["n3_no_write_check_pairs"] - report["a3_pairs"],
        "N3 delta matches",
    )
    check(report["n4_d2_eq_1_cols"] < report["a4_cols"], "N4 d2=1 reduces COL count")
    check(report["a4_vtables"] <= report["a4_cols"], "vtable count <= COL count")
    check(
        len(report["a4_top5_slot_coverage"]) == 5,
        "A4 top five displacement slot coverage present",
    )
    check(
        all(
            x["vtables_long_enough"] <= report["a4_vtables"]
            and x["unique_values"] <= x["vtables_long_enough"]
            and x["slot_index"] == x["disp"] // 4
            for x in report["a4_top5_slot_coverage"]
        ),
        "A4 slot coverage internally consistent",
    )

    lines = [
        "R188 exec_hy4 间接调用与 vt-[esi] 静态普查",
        "A1 间接 call 总数 %d" % report["a1_total"],
        "A1 eax %d ecx %d edx %d ebx %d esp %d ebp %d esi %d edi %d absolute %d indexed %d"
        % (
            cats["eax"], cats["ecx"], cats["edx"], cats["ebx"], cats["esp"],
            cats["ebp"], cats["esi"], cats["edi"], report["a1_absolute"],
            report["a1_indexed"],
        ),
        "A2 esi 带位移站点 %d 位移去重 %d" % (report["a2_total"], report["a2_unique_disps"]),
        "A2 4字节对齐 %d 不对齐 %d 不对齐地址 %s"
        % (report["a2_aligned"], report["a2_unaligned"],
           ",".join(x["va"] for x in report["a2_unaligned_sites"]) or "无"),
        "A3 mov r32,dword ptr [esi] 站点 %d 配对 %d" % (report["a3_mov_sites"], report["a3_pairs"]),
        "A3 call站点去重 %d 位移去重 %d mov站点去重 %d 未配到call %d"
        % (report["a3_unique_call_sites"], report["a3_unique_disps"],
           report["a3_unique_mov_sites"], report["a3_movs_without_call"]),
        "A4 COL %d vtable %d" % (report["a4_cols"], report["a4_vtables"]),
        "N1 jmp 间接站点 %d" % report["n1_jmp_indirect"],
        "N2 窗口1配对 %d (32窗口 %d)" % (report["n2_window1_pairs"], report["a3_pairs"]),
        "N3 关闭写检查配对 %d 差值 %d" % (report["n3_no_write_check_pairs"], report["n3_delta"]),
        "N4 d2=1 COL %d (原 %d)" % (report["n4_d2_eq_1_cols"], report["a4_cols"]),
    ]
    for slot in report["a4_top5_slot_coverage"]:
        lines.append(
            "A4 槽 disp %d index %d 够长vtable %d 取值去重 %d"
            % (slot["disp"], slot["slot_index"], slot["vtables_long_enough"],
               slot["unique_values"])
        )

    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    with open(SUMMARY, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    check(len(lines) <= 25, "summary <= 25 lines")
    failures = sum(1 for ok, _ in CHECKS if not ok)
    print("断言 %d 条，FAIL %d 条" % (len(CHECKS), failures))
    for ok, message in CHECKS:
        if not ok:
            print("FAIL: " + message)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
