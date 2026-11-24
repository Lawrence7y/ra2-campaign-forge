#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-GATE · 476 个 atlas 之外入口逐条裁定（R14-R9 双轨 c4）。

写域仅限 lead\\next_re_20261117_r14\\P0_GATE\\。
只读 ra2youli\\gamemd.exe、COVERAGE\\、P0_CLOSE\\ 与 W130_atlas。
capstone 一律 skipdata=True；站点归属只用函数区间包含（Atlas.owner），不用 entry_at_or_before。
不读 vtables_v2.json；虚表槽范围取自 P0_CLOSE\\vt_tables.tsv（自定界 1214 表）。
"""
import os
import re
import sys
import csv
import json
import struct
import bisect
import hashlib
import collections

import capstone

ROOT = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(ROOT, r"lead\next_re_20261117_r14")
OUT = os.path.join(R14, "P0_GATE")
EVID = os.path.join(OUT, "EVIDENCE")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUTSIDE = os.path.join(R14, r"COVERAGE\coverage_outside_atlas.tsv")
COVERAGE = os.path.join(R14, r"COVERAGE\coverage.tsv")
PROBE = os.path.join(R14, r"COVERAGE\probe_and_data_entries.tsv")
TRUE_UNIFIED = os.path.join(R14, r"P0_CLOSE\TRUE_ENTRY_UNIFIED.tsv")
VT_ENTRIES = os.path.join(R14, r"P0_CLOSE\VT_DIRECT_ENTRIES.tsv")
VT_TABLES = os.path.join(R14, r"P0_CLOSE\vt_tables.tsv")
SHA256_EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
JUMP_TABLE_DENSE_SPAN = 0x1000
DWORD_PROBE_N = 6


def eprint(*a):
    print(*a, file=sys.stderr)


class PE:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.buf = f.read()
        self.sha256 = hashlib.sha256(self.buf).hexdigest().upper()
        b = self.buf
        if b[:2] != b"MZ":
            raise ValueError("not MZ")
        e = struct.unpack_from("<I", b, 0x3C)[0]
        if b[e:e + 4] != b"PE\0\0":
            raise ValueError("not PE")
        coff = e + 4
        nsec = struct.unpack_from("<H", b, coff + 2)[0]
        optsz = struct.unpack_from("<H", b, coff + 16)[0]
        opt = coff + 20
        if struct.unpack_from("<H", b, opt)[0] != 0x10B:
            raise ValueError("not PE32")
        self.imagebase = struct.unpack_from("<I", b, opt + 28)[0]
        self.sizeofimage = struct.unpack_from("<I", b, opt + 56)[0]
        secs = []
        p = opt + optsz
        for _ in range(nsec):
            name = b[p:p + 8].rstrip(b"\0").decode("latin1")
            vsize, va, rawsize, raw = struct.unpack_from("<IIII", b, p + 8)
            secs.append(dict(name=name, va=va, vsize=vsize, rawsize=rawsize, raw=raw))
            p += 40
        self.secs = secs
        self.by_name = {s["name"]: s for s in secs}

    def sec_of(self, va):
        rva = va - self.imagebase
        for s in self.secs:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                return s
        return None

    def read(self, va, n):
        out = bytearray()
        while n > 0:
            s = self.sec_of(va)
            if s is None:
                break
            rva = va - self.imagebase
            off = rva - s["va"]
            if off >= s["rawsize"]:
                break
            avail = min(n, s["rawsize"] - off)
            out += self.buf[s["raw"] + off:s["raw"] + off + avail]
            va += avail
            n -= avail
        return bytes(out)

    def u32(self, va):
        d = self.read(va, 4)
        if len(d) < 4:
            raise ValueError("unreadable dword @%08X" % va)
        return struct.unpack("<I", d)[0]

    def text_range(self):
        s = self.by_name[".text"]
        lo = self.imagebase + s["va"]
        return lo, lo + s["vsize"]

    def in_text(self, va):
        lo, hi = self.text_range()
        return lo <= va < hi


def md_new():
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    md.detail = False
    return md


class Atlas:
    def __init__(self, path):
        rows = []
        with open(path, encoding="utf-8", errors="replace") as f:
            header = f.readline().rstrip("\r\n").split("\t")
            for line in f:
                if not line.strip():
                    continue
                d = dict(zip(header, line.rstrip("\r\n").split("\t")))
                rows.append((int(d["entry"], 16), int(d["size"])))
        self.rows = rows
        self.entries = [e for e, _ in rows]
        self.n = len(rows)

    def owner(self, va):
        i = bisect.bisect_right(self.entries, va) - 1
        if i >= 0 and self.entries[i] <= va < self.entries[i] + self.rows[i][1]:
            return self.entries[i]
        return None


def disasm_at(pe, va, span=64, n=6):
    data = pe.read(va, span)
    if not data:
        return [], b""
    out = []
    for ins in md_new().disasm(data, va):
        if ins.id == 0:
            text = ".byte 0x%02x" % ins.bytes[0]
        else:
            text = (ins.mnemonic + (" " + ins.op_str if ins.op_str else "")).strip()
        out.append(dict(addr=ins.address, size=ins.size, text=text,
                        mnemonic=(ins.mnemonic or ".byte"), op=ins.op_str or ""))
        if len(out) >= n:
            break
    return out, data[:min(64, len(data))]


def trailing_pad(pe, va, maxn=64):
    data = pe.read(max(0, va - maxn), min(maxn, 64))
    k = 0
    fill = None
    for c in reversed(data):
        if c not in (0x90, 0xCC):
            break
        if fill is None:
            fill = c
        elif c != fill:
            break
        k += 1
    return k, (hex(fill) if fill is not None else "none")


class Sweep:
    """全 .text 线性解码，仅保存起点/mnemonic，供前驱指令判定。"""
    def __init__(self, pe, lo, hi):
        self.lo, self.hi = lo, hi
        data = pe.read(lo, hi - lo)
        codes = {}
        mncode = []
        starts = []
        size = []
        for ins in md_new().disasm(data, lo):
            c = codes.get(ins.mnemonic)
            if c is None:
                c = len(codes)
                codes[ins.mnemonic] = c
            mncode.append(c)
            starts.append(ins.address)
            size.append(min(255, ins.size))
        self.mncode = mncode
        self.starts = starts
        self.size = size
        self.codes = codes
        self.names = {v: k for k, v in codes.items()}
        self.n = len(starts)

    def index_of(self, va):
        i = bisect.bisect_left(self.starts, va)
        return i if i < self.n and self.starts[i] == va else -1

    def covering(self, va):
        i = bisect.bisect_right(self.starts, va) - 1
        if i >= 0 and self.starts[i] <= va < self.starts[i] + self.size[i]:
            return i
        return -1

    def mn(self, i):
        return self.names[self.mncode[i]]


TERM = {"nop", "ret", "retn", "retf", "jmp", "int3"}


def predecessor(pe, sw, T):
    """与 P0_CLOSE/p0lib.predecessor 同口径：优先全局 sweep，再 15B 重同步。"""
    i = sw.index_of(T)
    if i >= 0:
        if i == 0:
            return dict(kind="none", desc="sweep-head", via="sweep", boundary=True, mn="none")
        p = i - 1
        m = sw.mn(p)
        desc = "%s @%08X+%d" % (m, sw.starts[p], sw.size[p])
        if m == "nop":
            kind = "nop"
        elif m in ("ret", "retn", "retf"):
            kind = "ret"
        elif m == "jmp":
            kind = "jmp"
        elif m == "int3":
            kind = "int3"
        else:
            kind = "other"
        return dict(kind=kind, desc=desc, via="sweep", boundary=kind in TERM, mn=m)

    md = md_new()
    best = None
    for s in range(T - 15, T):
        if s < sw.lo:
            continue
        data = pe.read(s, 16)
        for ins in md.disasm(data, s):
            if ins.id == 0:
                break
            if ins.address + ins.size == T:
                is_sw = sw.index_of(s) >= 0
                cand = (0 if is_sw else 1, -ins.size, s, ins.mnemonic, ins.size)
                if best is None or cand < best:
                    best = cand
            break
    cov = sw.covering(T)
    if best is None:
        desc = "no-insn-ends-at-T"
        if cov >= 0:
            desc += " (sweep: inside %s @%08X+%d)" % (sw.mn(cov), sw.starts[cov], sw.size[cov])
        return dict(kind="other", desc=desc, via="resync", boundary=False, mn="?")
    _, _, s, m, sz = best
    if m == "nop":
        kind = "nop"
    elif m in ("ret", "retn", "retf"):
        kind = "ret"
    elif m == "jmp":
        kind = "jmp"
    elif m == "int3":
        kind = "int3"
    else:
        kind = "other"
    return dict(kind=kind, desc="%s @%08X+%d" % (m, s, sz), via="resync",
                boundary=kind in TERM, mn=m)


def first_col_set(path, skip_header=True):
    out = set()
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if skip_header and i == 0:
                continue
            if not line.strip():
                continue
            out.add(line.split("\t", 1)[0].strip().upper())
    return out


def read_tsv(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def leaf_pattern(data):
    b = data
    if len(b) < 3:
        return False
    if b[0] == 0x8B and (b[1] & 0xF0) == 0x40 and b[2] == 0x24:
        return True
    if b[0] == 0x8B and b[1] == 0x41:
        return True
    if b[0] in (0x57, 0x56, 0x53):
        return True
    return False


def early_terminator(insns):
    for ins in insns:
        if ins["addr"] >= ins["addr"] + 0:  # keep loop simple; checked below
            pass
        if ins["addr"] - ins["addr"] > 1000000:
            pass
    return None


def has_early_ret_or_jmp(insns, T):
    hits = []
    for ins in insns:
        if ins["addr"] >= T + 16:
            break
        if ins["mnemonic"] in ("ret", "retn", "retf", "jmp"):
            hits.append(ins["text"])
    return hits


def build_rel32_targets(pe, atlas, lo, hi):
    targets = set()
    md = md_new()
    data = pe.read(lo, hi - lo)
    for ins in md.disasm(data, lo):
        if ins.bytes and ins.bytes[0] in (0xE8, 0xE9) and ins.op_str.startswith("0x"):
            try:
                t = int(ins.op_str, 16)
            except ValueError:
                continue
            if atlas.owner(ins.address) is not None:
                targets.add(t)
    return targets


def clean(s):
    return str(s).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(EVID, exist_ok=True)

    pe = PE(EXE)
    if pe.sha256 != SHA256_EXPECT:
        raise SystemExit("EXE SHA-256 mismatch: %s" % pe.sha256)
    if pe.imagebase != 0x400000:
        raise SystemExit("unexpected ImageBase")
    TLO, THI = pe.text_range()
    atlas = Atlas(ATLAS)
    sw = Sweep(pe, TLO, THI)
    outside = read_tsv(OUTSIDE)
    if len(outside) != 476:
        raise SystemExit("outside rows != 476: %d" % len(outside))

    coverage = first_col_set(COVERAGE)
    probe = first_col_set(PROBE)
    rel32_targets = build_rel32_targets(pe, atlas, TLO, THI)

    vt_target_slots = collections.defaultdict(list)
    for r in read_tsv(VT_ENTRIES):
        vt_target_slots[int(r["target"], 16)].append("%s/%s" % (r["vt_addr"], r["slot_idx"]))
    vt_ranges = []
    for r in read_tsv(VT_TABLES):
        vt_ranges.append((int(r["vt_addr"], 16), int(r["end"], 16)))
    # 已知 DynamicVectorClass Items 区（.data，来自 R14_COMMON.md:189 / S09-F1\PROGRESS.md:17）
    items_ranges = [(0xA8EC7C, 0xA8EC80), (0xA8ECBC, 0xA8ECC0), (0xB0F4EC, 0xB0F4F0)]

    true_rows = [r for r in read_tsv(TRUE_UNIFIED) if r.get("verdict") == "TRUE"]
    true_set = {int(r["address"], 16) for r in true_rows}
    vt_set = set(vt_target_slots)

    records = []
    for r in outside:
        addr_s = r["entry"].upper()
        T = int(addr_s, 16)
        source = "true_entry" if r["source"] == "TRUE_ENTRY_UNIFIED" else "vt_direct"
        data = pe.read(T, 64)
        if len(data) < 6:
            raise SystemExit("unreadable target %s" % addr_s)
        all_objs = list(md_new().disasm(data, T))

        def fmt_insn(i):
            text = (i.mnemonic + (" " + i.op_str if i.op_str else "")).strip() if i.id else ".byte 0x%02x" % i.bytes[0]
            return dict(addr=i.address, size=i.size, text=text,
                        mnemonic=(i.mnemonic or ".byte"), op=i.op_str or "")

        insns = [fmt_insn(i) for i in all_objs[:6]]
        if not insns:
            raise SystemExit("capstone returned no instruction at %s" % addr_s)
        first_text = "; ".join("%08X: %s" % (i["addr"], i["text"]) for i in insns)
        early_insns = [fmt_insn(i) for i in all_objs if i.address < T + 16]

        c1 = (T % 16 == 0)
        c2 = data[0] not in (0xE8, 0xE9, 0xEB)
        pad, pad_fill = trailing_pad(pe, T)
        pr = predecessor(pe, sw, T)
        c3 = pr["kind"] in ("nop", "ret", "jmp", "int3")

        c4a = (data[0] == 0x55 or data[:2] in (b"\x83\xec", b"\x81\xec"))
        term_hits = has_early_ret_or_jmp(early_insns, T)
        sem1 = T in vt_set
        sem2 = T in rel32_targets
        sem3 = leaf_pattern(data)
        sem_any = sem1 or sem2 or sem3
        c4b = bool(c1 and c2 and c3 and not term_hits and data[0] != 0xE8 and sem_any)
        c4 = c4a or c4b

        dwords = []
        for k in range(DWORD_PROBE_N):
            try:
                dwords.append(pe.u32(T + 4 * k))
            except ValueError:
                dwords.append(0)
        n_textptr = sum(1 for d in dwords if pe.in_text(d))
        span = (max(dwords) - min(dwords)) if n_textptr == len(dwords) else -1
        dense = (n_textptr == len(dwords)) and (len(set(dwords)) >= 5) and (0 <= span <= JUMP_TABLE_DENSE_SPAN)
        in_probe = addr_s in probe
        c5 = not (dense or in_probe)
        in_vt = any(a <= T < b for a, b in vt_ranges)
        in_items = any(a <= T < b for a, b in items_ranges)
        c6 = pe.in_text(T) and not in_vt and not in_items and not in_probe

        owner = atlas.owner(T)
        owner_s = ("%08X" % owner) if owner is not None else "none"
        hole_m = re.search(r"hole=([0-9A-Fa-f]{8})-([0-9A-Fa-f]{8})", r.get("note", ""))
        hole_s = ("%s-%s" % (hole_m.group(1).upper(), hole_m.group(2).upper())) if hole_m else "none"

        all_ok = c1 and c2 and c3 and c4 and c5 and c6
        reason = []
        if not c1:
            reason.append("c1:not-16B-aligned")
        if not c2:
            reason.append("c2:first-byte-E8/E9/EB")
        if not c3:
            reason.append("c3:predecessor-fallthrough")
        if not c4:
            reason.append("c4:no-c4a-and-no-c4b")
        if not c5:
            reason.append("c5:jump-table")
        if not c6:
            reason.append("c6:known-nonfunc-container")
        if all_ok:
            verdict = "FUNC"
            subkind = ""
        else:
            if not c2:
                if data[0] == 0xE8:
                    subkind = "call_site"
                elif data[0] in (0xE9, 0xEB):
                    subkind = "jump_target"
                else:
                    subkind = "data"
            elif not c5:
                subkind = "jump_table"
            elif not c6:
                subkind = "vftable_slot" if in_vt else "data"
            elif not c1:
                subkind = "internal_label"
            elif not c3:
                subkind = "internal_label"
            elif not c4:
                subkind = "stub" if term_hits else "data"
            else:
                subkind = ""
            verdict = "NOT_FUNC" if subkind else "UNDECIDABLE"

        sem_tags = []
        if sem1:
            sem_tags.append("1:vftable_direct")
        if sem2:
            sem_tags.append("2:rel32_from_fn")
        if sem3:
            sem_tags.append("3:leaf_start_pattern")
        if not sem_tags:
            sem_tags.append("none")

        evidence = " | ".join([
            "T%%16=%d" % (T % 16),
            "op=%02X" % data[0],
            "pad=%d*%s" % (pad, pad_fill),
            "prev=%s(%s,via=%s)" % (pr["kind"], pr["desc"], pr["via"]),
            "c4a=%s" % ("Y" if c4a else "N"),
            "c4b=%s" % ("Y" if c4b else "N"),
            "c4b_sem=%s" % "+".join(sem_tags),
            "c4b_early_term=%s" % ("none" if not term_hits else ";".join(term_hits)),
            "c5_dwords=%s" % ",".join("%08X" % d for d in dwords),
            "c5_textptrs=%d/%d" % (n_textptr, len(dwords)),
            "c5_span=%s" % ("n/a" if span < 0 else hex(span)),
            "atlas_owner=%s" % owner_s,
            "atlas_hole=%s" % hole_s,
            "vtable_ranges_hit=%s" % ("Y" if in_vt else "N"),
            "probe_exact_hit=%s" % ("Y" if in_probe else "N"),
            "items_range_hit=%s" % ("Y" if in_items else "N"),
            "rel32_from_fn=%s" % ("Y" if sem2 else "N"),
            "vt_slots=%s" % (",".join(vt_target_slots.get(T, [])) or "none"),
            "source_note=%s" % clean(r.get("note", "")),
        ])
        if verdict == "UNDECIDABLE":
            evidence += " | undecidable_reason=%s" % (";".join(reason) or "none")

        rec = dict(
            addr=addr_s, source=source,
            c1="Y" if c1 else "N", c2="Y" if c2 else "N", c3="Y" if c3 else "N",
            c4="Y" if c4 else "N", c5="Y" if c5 else "N", c6="Y" if c6 else "N",
            verdict=verdict, subkind=subkind, first_insn=first_text,
            prev_byte=("%02X" % pe.read(T - 1, 1)[0]) if T > TLO else "?",
            inside_atlas_owner=owner_s, evidence=evidence,
            c4a="Y" if c4a else "N", c4b="Y" if c4b else "N",
            c4b_sem="+".join(sem_tags), sem1="Y" if sem1 else "N",
            sem2="Y" if sem2 else "N", sem3="Y" if sem3 else "N",
            first6_hex=data[:16].hex().upper(), hole=hole_s,
            prev_desc=pr["desc"], pad_n=pad, pad_fill=pad_fill,
            early_term="none" if not term_hits else ";".join(term_hits),
            dwords=",".join("%08X" % d for d in dwords),
            n_textptr=n_textptr, span=("n/a" if span < 0 else hex(span)),
            in_vt="Y" if in_vt else "N", in_probe="Y" if in_probe else "N",
            in_items="Y" if in_items else "N",
            note=clean(r.get("note", "")),
        )
        records.append(rec)

    # ---- 主交付 ----
    cols = ["addr", "source", "c1", "c2", "c3", "c4", "c5", "c6", "verdict",
            "subkind", "first_insn", "prev_byte", "inside_atlas_owner", "evidence"]
    with open(os.path.join(OUT, "ENTRY_ADJUDICATION.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for rec in records:
            w.writerow({k: rec[k] for k in cols})

    full_cols = cols + ["c4a", "c4b", "c4b_sem", "sem1", "sem2", "sem3",
                        "first6_hex", "hole", "prev_desc", "pad_n", "pad_fill",
                        "early_term", "dwords", "n_textptr", "span",
                        "in_vt", "in_probe", "in_items", "note"]
    with open(os.path.join(EVID, "ENTRY_ADJUDICATION_FULL.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=full_cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for rec in records:
            w.writerow({k: rec[k] for k in full_cols})

    # ---- 计数 ----
    verdicts = collections.Counter(r["verdict"] for r in records)
    subkinds = collections.Counter(r["subkind"] for r in records if r["verdict"] == "NOT_FUNC")
    c_pass = {c: sum(1 for r in records if r[c] == "Y") for c in ("c1", "c2", "c3", "c4", "c5", "c6")}
    c4a_n = sum(1 for r in records if r["c4a"] == "Y")
    c4b_n = sum(1 for r in records if r["c4b"] == "Y")
    both = sum(1 for r in records if r["c4a"] == "Y" and r["c4b"] == "Y")
    c4a_only = c4a_n - both
    c4b_only = c4b_n - both

    sem_buckets = collections.Counter()
    for r in records:
        if r["c4b"] != "Y":
            continue
        tags = tuple(x for x, v in (("1", r["sem1"]), ("2", r["sem2"]), ("3", r["sem3"])) if v == "Y")
        sem_buckets["+".join(tags) if tags else "none"] += 1

    funcs = [r for r in records if r["verdict"] == "FUNC"]
    func_source = collections.Counter(r["source"] for r in funcs)
    func_c4 = collections.Counter()
    for r in funcs:
        if r["c4a"] == "Y" and r["c4b"] == "Y":
            func_c4["c4a+c4b"] += 1
        elif r["c4a"] == "Y":
            func_c4["c4a-only"] += 1
        elif r["c4b"] == "Y":
            func_c4["c4b-only"] += 1
        else:
            func_c4["none"] += 1
    c2_fails = [r for r in records if r["c2"] == "N"]
    addresses = {r["addr"] for r in records}
    inter_cov = len(addresses & coverage)
    inter_probe = len(addresses & probe)
    atlas_owner_hits = sum(1 for r in records if r["inside_atlas_owner"] != "none")

    # ---- 证据文件 ----
    with open(os.path.join(EVID, "semantic_buckets.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("bucket\tcount\n")
        for k, v in sorted(sem_buckets.items()):
            f.write("%s\t%d\n" % (k, v))
    with open(os.path.join(EVID, "c2_fail_details.txt"), "w", encoding="utf-8") as f:
        f.write("# c2=N 的 10 个地址（首字节 E8/E9/EB，按 R14-R9 判 NOT_FUNC）\n")
        for r in c2_fails:
            f.write("%s\t%s\t%s\t%s\t%s\n" % (r["addr"], r["source"], r["subkind"],
                                               r["first_insn"], r["note"]))
    with open(os.path.join(EVID, "inputs.sha256.txt"), "w", encoding="utf-8") as f:
        for p in (EXE, OUTSIDE, COVERAGE, PROBE, TRUE_UNIFIED, VT_ENTRIES, VT_TABLES, ATLAS):
            h = hashlib.sha256(open(p, "rb").read()).hexdigest().upper()
            f.write("%s  %s\n" % (h, os.path.relpath(p, ROOT)))
    with open(os.path.join(EVID, "RECOMPUTE_STDOUT.txt"), "w", encoding="utf-8") as f:
        f.write("capstone_version=%s\n" % capstone.__version__)
        f.write("skipdata=True\n.text=[%08X,%08X)\n" % (TLO, THI))
        f.write("rows=%d unique=%d\n" % (len(records), len(addresses)))
        f.write("c_pass=%s\n" % json.dumps(c_pass, sort_keys=True))
        f.write("c4a=%d c4b=%d both=%d c4a_only=%d c4b_only=%d\n" %
                (c4a_n, c4b_n, both, c4a_only, c4b_only))
        f.write("sem_buckets=%s\n" % json.dumps(sem_buckets, sort_keys=True))
        f.write("verdicts=%s\n" % json.dumps(verdicts, sort_keys=True))
        f.write("subkinds=%s\n" % json.dumps(subkinds, sort_keys=True))
        f.write("func_source=%s func_c4=%s\n" %
                (json.dumps(func_source, sort_keys=True), json.dumps(func_c4, sort_keys=True)))
        f.write("intersection_coverage=%d intersection_probe=%d atlas_owner_hits=%d\n" %
                (inter_cov, inter_probe, atlas_owner_hits))
        f.write("rel32_from_fn_targets=%d vt_targets=%d true_entries_in_unified=%d\n" %
                (len(rel32_targets), len(vt_set), len(true_set)))

    counts = dict(
        rows=len(records), unique=len(addresses),
        c_pass=c_pass, c4a=c4a_n, c4b=c4b_n, c4a_only=c4a_only,
        c4b_only=c4b_only, c4_both=both,
        sem_buckets=dict(sem_buckets), verdicts=dict(verdicts),
        subkinds=dict(subkinds), func_source=dict(func_source),
        func_c4=dict(func_c4),
        c2_fails=[r["addr"] for r in c2_fails],
        intersection_coverage=inter_cov, intersection_probe=inter_probe,
        atlas_owner_hits=atlas_owner_hits,
        text_lo="%08X" % TLO, text_hi="%08X" % THI,
        capstone_version=capstone.__version__, exe_sha256=pe.sha256,
        rel32_from_fn_targets=len(rel32_targets),
        vt_distinct_targets=len(vt_set), true_rows_in_unified=len(true_set),
    )
    with open(os.path.join(EVID, "counts.json"), "w", encoding="utf-8") as f:
        json.dump(counts, f, ensure_ascii=False, indent=2)

    print(open(os.path.join(EVID, "RECOMPUTE_STDOUT.txt"), encoding="utf-8").read(), end="")


if __name__ == "__main__":
    main()
