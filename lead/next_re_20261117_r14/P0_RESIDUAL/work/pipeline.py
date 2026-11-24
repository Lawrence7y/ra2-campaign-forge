#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-RESIDUAL 主流水线：枚举 A-E 通道 -> 去重 -> R14-R10 分轨裁定 -> 交付 TSV/统计。

写域仅 P0_RESIDUAL。全程只读 gamemd.exe / COVERAGE。capstone skipdata=True。
站点归属用「函数区间包含」(atlas.owner)，不用 entry_at_or_before。
不读 vtables_v2.json；虚表由 .rdata 现场定界。
"""
import os, sys, csv, json, struct, collections, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from resid_common import (EXE, SHA256, sha256_file, RawPE, Sweep, Atlas, md_new,
                          ATLAS, COVERAGE, PROBE, OUTSIDE, disasm_at, predecessor,
                          trailing_pad, JCC, TERM_KINDS)

OUT = os.path.dirname(HERE)            # P0_RESIDUAL
EVID = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVID, exist_ok=True)

ITEMS_RANGES = [(0xA8EC7C, 0xA8EC80), (0xA8ECBC, 0xA8ECC0), (0xB0F4EC, 0xB0F4F0)]
JT_SPAN = 0x1000
DWORD_PROBE_N = 6
BODY_LIMIT = 4096
TERM_MN = {"ret", "retn", "retf", "jmp"}


def load_set(p, col=0):
    s = set()
    with open(p, encoding="utf-8", errors="replace") as f:
        f.readline()
        for ln in f:
            if not ln.strip():
                continue
            t = ln.rstrip("\n").split("\t")
            try:
                s.add(int(t[col], 16))
            except Exception:
                pass
    return s


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


def body_termination(pe, T, limit=BODY_LIMIT):
    """从 T 线性解码，找首个 ret/jmp；返回 (found, length, desc)。"""
    data = pe.read(T, min(limit, 65536))
    for i in md_new().disasm(data, T):
        if i.mnemonic in TERM_MN:
            return True, (i.address + i.size - T), ("%s %s" % (i.mnemonic, i.op_str)).strip()
    return False, None, "no-ret/jmp-within-%d" % limit


def pointer_table(pe, T, n=DWORD_PROBE_N):
    ds = []
    for k in range(n):
        try:
            ds.append(pe.u32(T + 4 * k))
        except Exception:
            return False, []
    nt = sum(1 for d in ds if pe.in_text(d))
    span = max(ds) - min(ds) if nt == len(ds) else -1
    dense = nt == len(ds) and len(set(ds)) >= 5 and 0 <= span <= JT_SPAN
    return dense, ds


def vftables(pe, TLO, THI):
    """自 .rdata 定界 vftable（不读 vtables_v2.json）。返回 (tables, bare, vt_ranges)。"""
    r = pe.byname[".rdata"]
    rlo = pe.imagebase + r["va"]
    buf = pe.read(rlo, r["rawsize"])
    nw = len(buf) // 4
    words = list(struct.unpack_from("<%dI" % nw, buf, 0))

    def in_text(v):
        return TLO <= v < THI

    def col_ok(colp):
        if not (pe.imagebase <= colp < pe.imagebase + pe.sizeofimage):
            return False
        d = pe.try_read(colp, 16)
        if len(d) < 16:
            return False
        sig, off, cd, tdp = struct.unpack("<IIII", d)
        if sig not in (0, 1):
            return False
        if not (pe.imagebase <= tdp < pe.imagebase + pe.sizeofimage):
            return False
        nm = pe.try_read(tdp + 8, 256)
        if not nm:
            return False
        z = nm.find(b"\x00")
        nm = nm[:z] if z > 0 else nm
        return nm.startswith(b".?AV") or nm.startswith(b".?AU")

    runs = []
    i = 0
    while i < nw:
        if in_text(words[i]):
            j = i
            while j < nw and in_text(words[j]):
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    tables, bare = [], []
    for i, j in runs:
        va = rlo + 4 * i
        colp = words[i - 1] if i >= 1 else 0
        rec = dict(vt=va, n=j - i, slots=words[i:j], col=colp, end=va + 4 * (j - i))
        (tables if col_ok(colp) else bare).append(rec)
    vt_ranges = [(t["vt"], t["end"]) for t in tables]
    return tables, bare, vt_ranges


def fmt_insn_head(pe, T):
    ins = disasm_at(pe, T, n=1, span=16)
    if not ins:
        return ".byte"
    m, o = ins[0][0], ins[0][1]
    return (m + (" " + o if o else "")).strip()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    assert sha256_file() == SHA256, "SHA256 MISMATCH"
    pe = RawPE()
    t = pe.byname[".text"]
    TLO = pe.imagebase + t["va"]
    THI = TLO + t["vsize"]
    sw = Sweep(pe, TLO, THI)
    at = Atlas()
    cov = load_set(COVERAGE)
    probe = load_set(PROBE)
    outside = load_set(OUTSIDE)
    adjudicated = cov | probe | outside          # 已裁定/已知非函数集合
    print(".text=[%08X,%08X) sweep=%d atlas=%d cov=%d probe=%d outside=%d"
          % (TLO, THI, sw.n, at.n, len(cov), len(probe), len(outside)))

    tables, bare, vt_ranges = vftables(pe, TLO, THI)
    print("vftable COL=%d tables/%d slots; bare=%d runs; vt_ranges=%d"
          % (len(tables), sum(x["n"] for x in tables), len(bare), len(vt_ranges)))

    # ---- 全局引用集合（供 sem1/sem2 之用，分轨裁定） ----
    vt_slots_by_target = collections.defaultdict(list)
    for tb in tables:
        for k, S in enumerate(tb["slots"]):
            vt_slots_by_target[S].append((tb["vt"], k))
    rel32_targets = set()
    for i in range(sw.n):
        b = sw.bytes_list[i]
        if len(b) == 5 and b[0] in (0xE8, 0xE9):
            rel = struct.unpack("<i", b[1:5])[0]
            tgt = sw.starts[i] + 5 + rel
            if TLO <= tgt < THI:
                rel32_targets.add(tgt)
    print("rel32 targets(in .text)=%d; vt slot distinct targets=%d"
          % (len(rel32_targets), len(vt_slots_by_target)))

    # =========================================================
    # 候选枚举：每个候选一条记录 (addr, chan, first_insn, prev_byte, align16, source_detail)
    # =========================================================
    cand = {}   # addr -> dict (first occurrence wins for channel priority C>A>B>D>E)

    def add(addr, chan, detail, pr=None, first=None):
        if not (TLO <= addr < THI):
            return
        if at.in_atlas(addr):
            return
        if addr in cand:
            cand[addr]["chans"].add(chan)
            cand[addr]["details"].append("%s:%s" % (chan, detail))
            return
        if pr is None:
            pr = predecessor(pe, sw, addr)
        if first is None:
            first = fmt_insn_head(pe, addr)
        pb = pe.read(addr - 1, 1) if addr > TLO else b"?"
        cand[addr] = dict(addr=addr, chans={chan}, first=first,
                          prev_byte=(pb.hex().upper() if pb else "??"),
                          align16=("Y" if addr % 16 == 0 else "N"),
                          details=["%s:%s" % (chan, detail)],
                          pred_kind=pr["kind"], pred_desc=pr["desc"])

    # -- Channel A: E8/E9 rel32 targets --
    nA = 0
    for i in range(sw.n):
        b = sw.bytes_list[i]
        if len(b) == 5 and b[0] in (0xE8, 0xE9):
            rel = struct.unpack("<i", b[1:5])[0]
            tgt = sw.starts[i] + 5 + rel
            if TLO <= tgt < THI and not at.in_atlas(tgt):
                nA += 1
                add(tgt, "A", "rel32 from %08X op=%02X" % (sw.starts[i], b[0]))
    # -- Channel B: EB rel8 targets --
    nB = 0
    for i in range(sw.n):
        b = sw.bytes_list[i]
        if len(b) == 2 and b[0] == 0xEB:
            rel = struct.unpack("<b", b[1:2])[0]
            tgt = sw.starts[i] + 2 + rel
            if TLO <= tgt < THI and not at.in_atlas(tgt):
                nB += 1
                add(tgt, "B", "rel8 from %08X" % sw.starts[i])
    # -- Channel C: vftable slot values (COL verified) --
    nC = 0
    for tb in tables:
        for k, S in enumerate(tb["slots"]):
            if TLO <= S < THI and not at.in_atlas(S):
                nC += 1
                add(S, "C", "vftable slot vt=%08X idx=%d" % (tb["vt"], k))
    # -- Channel C-bare: bare run slot values (no COL; 敏感性, 归 C 但标注) --
    nCb = 0
    for tb in bare:
        for k, S in enumerate(tb["slots"]):
            if TLO <= S < THI and not at.in_atlas(S):
                nCb += 1
                add(S, "C", "bare-run slot(no COL) vt=%08X idx=%d" % (tb["vt"], k))

    # -- Channel D: forward/orphan scan (16-align + prev term + c4a prologue OR c4b leaf-shape) --
    nD_align = nD_prevok = nD_c4a = nD_c4b = 0
    for A in range((TLO + 15) & ~15, THI, 16):
        if at.in_atlas(A):
            continue
        nD_align += 1
        pr = predecessor(pe, sw, A)
        if pr["kind"] not in TERM_KINDS:
            continue
        nD_prevok += 1
        raw3 = pe.read(A, 3)
        if not raw3:
            continue
        first = disasm_at(pe, A, n=3, span=24)
        fmn = first[0][0] if first else ".byte"
        if fmn in JCC or fmn == ".byte":
            continue
        is_c4a = (raw3[0] == 0x55 or raw3[:2] in (b"\x83\xec", b"\x81\xec"))
        bt, bl, bdesc = body_termination(pe, A)
        is_c4b = bool(leaf_pattern(raw3) and bt and bl is not None and bl >= 2)
        if is_c4a:
            nD_c4a += 1
        if is_c4b:
            nD_c4b += 1
        if is_c4a or is_c4b:
            tag = "D:c4a=%s,c4b=%s,body=%s,prev=%s" % (
                "Y" if is_c4a else "N", "Y" if is_c4b else "N",
                (bl if bl is not None else "none"), pr["kind"])
            add(A, "D", tag, pr=pr, first=fmt_insn_head(pe, A))

    # -- Channel E: atlas size suspicious (entry+size 吞掉后一函数) --
    # 判据：atlas entry 的 pend=entry+size；若 pend 处并无以 pend 结尾的 ret/jmp，则 size 可疑。
    nE = 0
    e_rows = []
    for (e, sz) in at.rows:
        pend = e + sz
        if not (TLO <= pend < THI):
            continue
        # 在 [pend-15,pend) 找恰好以 pend 结尾的指令
        ok = False
        desc = "no-insn-ends-at-pend"
        md = md_new()
        for s in range(pend - 15, pend):
            if s < TLO:
                continue
            d = pe.read(s, 16)
            if not d:
                continue
            for ins in md.disasm(d, s):
                if ins.id and ins.address + ins.size == pend:
                    if ins.mnemonic in ("ret", "retn", "retf", "jmp"):
                        ok = True
                        desc = "%s @%08X+%d" % (ins.mnemonic, s, ins.size)
                    else:
                        desc = "ends-with-%s @%08X" % (ins.mnemonic, s)
                break
        if not ok:
            nE += 1
            e_rows.append((e, sz, pend, desc))
            # 若 pend 本身是 16 对齐且未被 atlas 覆盖，作为候选纳入 E
            if pend % 16 == 0 and not at.in_atlas(pend):
                add(pend, "E", "atlas-size-suspicious entry=%08X size=%d pend=%08X %s"
                    % (e, sz, pend, desc))

    print("Channel counts: A=%d B=%d C(COL)=%d C(bare)=%d D(align=%d prevok=%d c4a=%d c4b=%d) E(suspicious=%d)"
          % (nA, nB, nC, nCb, nD_align, nD_prevok, nD_c4a, nD_c4b, nE))
    print("CANDIDATES_ALL distinct addresses:", len(cand))

    # =========================================================
    # 去重 vs 已裁定集合
    # =========================================================
    dedup_rows = []
    residual = {}
    for a, rec in cand.items():
        reasons = []
        if a in cov:
            reasons.append("in_coverage")
        if a in probe:
            reasons.append("in_probe")
        if a in outside:
            reasons.append("in_outside_atlas")
        if any(x <= a < y for x, y in ITEMS_RANGES):
            reasons.append("in_DynamicVector_Items")
        if reasons:
            dedup_rows.append((a, ",".join(sorted(rec["chans"])), ";".join(reasons),
                               "|".join(rec["details"][:2])))
        else:
            residual[a] = rec
    print("dedup excluded=%d residual=%d" % (len(dedup_rows), len(residual)))

    # =========================================================
    # 分轨裁定
    # =========================================================
    adj_rows = []
    stats = collections.Counter()
    chan_contrib = collections.Counter()
    for a, rec in sorted(residual.items()):
        data = pe.read(a, 4)
        pr_kind = rec["pred_kind"]
        # 判定来源轨：若任一来源是 C 且是 COL slot -> vt_direct；否则 true_entry
        col_slot = None
        for d in rec["details"]:
            if d.startswith("C:vftable slot"):
                # parse vt/idx
                try:
                    part = d.split("vt=")[1]
                    vt = int(part.split(" ")[0], 16)
                    idx = int(part.split("idx=")[1])
                    col_slot = (vt, idx)
                except Exception:
                    pass
                break
        is_col_source = col_slot is not None
        has_bare = any("bare-run slot" in d for d in rec["details"])
        first_byte = data[0] if data else None
        bt, bl, bdesc = body_termination(pe, a)
        dense, dwords = pointer_table(pe, a)
        in_probe = a in probe
        in_vt = any(x <= a < y for x, y in vt_ranges)
        in_items = any(x <= a < y for x, y in ITEMS_RANGES)
        sem1 = "Y" if a in vt_slots_by_target else "N"
        sem2 = "Y" if a in rel32_targets else "N"
        sem3 = "Y" if leaf_pattern(data) else "N"
        sem_any = (sem1 == "Y" or sem2 == "Y" or sem3 == "Y")

        grade = []
        if is_col_source:
            rail = "vt_direct"
            A1 = pe.in_text(a)
            A2 = pr_kind in ("nop", "int3", "ret", "jmp")
            A3 = False
            a3_detail = ""
            # A3: 在 col_slot 对应表内验证（表界 + COL + slot 值）
            vt, idx = col_slot
            rec_tb = None
            for tb in tables:
                if tb["vt"] == vt:
                    rec_tb = tb
                    break
            if rec_tb is not None and 0 <= idx < rec_tb["n"] and rec_tb["end"] == vt + 4 * rec_tb["n"]:
                try:
                    val = pe.u32(vt + 4 * idx)
                    colp = pe.u32(vt - 4)
                    if val == a and col_ok_local(pe, colp):
                        A3 = True
                        a3_detail = "vt=%08X idx=%d col=%08X end=%08X" % (vt, idx, colp, rec_tb["end"])
                except Exception:
                    pass
            A4 = a not in cov and a not in outside and a not in probe
            all_ok = A1 and A2 and A3 and A4
            verdict = "FUNC" if all_ok else "NOT_FUNC"
            if verdict == "NOT_FUNC":
                if not A4:
                    subkind = "ALREADY_IN_COVERAGE"
                elif not A2:
                    subkind = "mid_instruction"
                elif not A3:
                    subkind = "bad_vtable_parse"
                else:
                    subkind = "bad_vtable_parse"
            else:
                subkind = ""
            grade = ["[已证] slot value", "[已证] predecessor-form",
                     "[已证] table-boundary-input-restatement",
                     "[静态推断] slot-value-as-function-entry"]
            ev = "rail=A A1=%s A2=%s(%s) A3=%s(%s) A4=%s pred=%s(%s) first=%s" % (
                "Y" if A1 else "N", "Y" if A2 else "N", pr_kind,
                "Y" if A3 else "N", a3_detail or "no-slot-rec", "Y" if A4 else "N",
                pr_kind, rec["pred_desc"], rec["first"])
            c1 = c2 = c3 = c4 = c5 = c6 = "NA"
        else:
            rail = "true_entry"
            c1 = (a % 16 == 0)
            c2 = first_byte not in (0xE8, 0xE9, 0xEB)
            c3 = pr_kind in ("nop", "ret", "jmp", "int3")
            c4a = (first_byte == 0x55 or data[:2] in (b"\x83\xec", b"\x81\xec"))
            body_ok = bool(bt and bl is not None and bl >= 2)
            c4b = bool(c1 and c2 and c3 and body_ok and sem_any)
            c4 = c4a or c4b
            c5 = not (dense or in_probe)
            c6 = pe.in_text(a) and not in_vt and not in_items and not in_probe
            all_ok = all((c1, c2, c3, c4, c5, c6))
            verdict = "FUNC" if all_ok else "NOT_FUNC"
            if all_ok:
                subkind = ""
            elif not c2:
                subkind = "call_site" if first_byte == 0xE8 else "jump_target"
            elif not c5:
                subkind = "jump_table"
            elif not c6:
                subkind = "data"
            elif not c1 or not c3:
                subkind = "internal_label"
            elif not c4:
                subkind = "stub" if not body_ok else "data"
            else:
                subkind = ""
            if verdict == "NOT_FUNC" and not subkind:
                verdict = "UNDECIDABLE"
            grade = ["[已证] direct-bytes/capstone", "[已证] predecessor-form",
                     "[静态推断] semantic-pattern(c4b)"]
            ev = ("rail=B c1=%s c2=%s c3=%s c4=%s(c4a=%s,c4b=%s) c5=%s c6=%s "
                  "T%%16=%d op=%02X pred=%s(%s) body=%s(%s) sem=%s/%s/%s dense=%s "
                  "in_vt=%s in_items=%s in_probe=%s first=%s source=%s") % (
                "Y" if c1 else "N", "Y" if c2 else "N", "Y" if c3 else "N",
                "Y" if c4 else "N", "Y" if c4a else "N", "Y" if c4b else "N",
                "Y" if c5 else "N", "Y" if c6 else "N", a % 16,
                first_byte if first_byte is not None else 0xFF, pr_kind, rec["pred_desc"],
                (bl if bl is not None else "none"), bdesc, sem1, sem2, sem3,
                "Y" if dense else "N", "Y" if in_vt else "N", "Y" if in_items else "N",
                "Y" if in_probe else "N", rec["first"], "|".join(rec["details"][:2]))
            c1 = "Y" if c1 else "N"
            c2 = "Y" if c2 else "N"
            c3 = "Y" if c3 else "N"
            c4 = "Y" if c4 else "N"
            c5 = "Y" if c5 else "N"
            c6 = "Y" if c6 else "N"

        chankey = "".join(sorted(rec["chans"]))
        adj_rows.append(dict(addr="%08X" % a, chan=chankey, verdict=verdict,
                             subkind=subkind, rail=rail,
                             first=rec["first"], prev=rec["prev_byte"],
                             align16=rec["align16"], pred_kind=pr_kind,
                             c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6,
                             sem1=sem1, sem2=sem2, sem3=sem3,
                             body=(bl if bl is not None else "none"),
                             dense=("Y" if dense else "N"),
                             grade=";".join(grade), evidence=ev,
                             source="|".join(rec["details"])))
        stats[verdict] += 1
        stats["rail_" + rail] += 1
        for ch in rec["chans"]:
            chan_contrib[(ch, verdict)] += 1

    # =========================================================
    # 写交付
    # =========================================================
    # CANDIDATES_ALL.tsv
    with open(os.path.join(OUT, "CANDIDATES_ALL.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("addr\tchan\tfirst_insn\tprev_byte\talign16\tsource_detail\n")
        for a, rec in sorted(cand.items()):
            f.write("%08X\t%s\t%s\t%s\t%s\t%s\n" % (
                a, "".join(sorted(rec["chans"])), rec["first"], rec["prev_byte"],
                rec["align16"], "|".join(rec["details"])))
    # DEDUP_VS_COVERAGE.tsv
    with open(os.path.join(OUT, "DEDUP_VS_COVERAGE.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("addr\tchan\texcluded_reason\tsource_detail\n")
        for a, ch, why, det in sorted(dedup_rows):
            f.write("%08X\t%s\t%s\t%s\n" % (a, ch, why, det))
    # RESIDUAL_ADJUDICATION.tsv
    with open(os.path.join(OUT, "RESIDUAL_ADJUDICATION.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("addr\tchan\tverdict\tsubkind\tevidence\n")
        for r in adj_rows:
            f.write("%s\t%s\t%s\t%s\t%s\n" % (r["addr"], r["chan"], r["verdict"],
                                              r["subkind"], r["evidence"]))
    # EVIDENCE full
    with open(os.path.join(EVID, "ADJUDICATION_FULL.tsv"), "w", encoding="utf-8", newline="") as f:
        cols = ["addr", "chan", "verdict", "subkind", "rail", "first", "prev", "align16",
                "pred_kind", "c1", "c2", "c3", "c4", "c5", "c6", "sem1", "sem2", "sem3",
                "body", "dense", "grade", "evidence", "source"]
        f.write("\t".join(cols) + "\n")
        for r in adj_rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")
    with open(os.path.join(EVID, "CHANNEL_E_SUSPICIOUS.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("entry\tsize_dec\tpend\tend_insn\n")
        for e, sz, pend, desc in e_rows:
            f.write("%08X\t%d\t%08X\t%s\n" % (e, sz, pend, desc))
    with open(os.path.join(EVID, "VT_TABLES.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("vt\tn_slots\tend\tcol\n")
        for tb in tables:
            f.write("%08X\t%d\t%08X\t%08X\n" % (tb["vt"], tb["n"], tb["end"], tb["col"]))

    # stats json
    stat = dict(
        sha256=sha256_file(), text=[TLO, THI], sweep_n=sw.n, atlas_n=at.n,
        n_vt_tables=len(tables), n_vt_slots=sum(x["n"] for x in tables),
        n_bare_runs=len(bare),
        chan_counts=dict(A=nA, B=nB, C_col=nC, C_bare=nCb, D_align=nD_align,
                         D_prevok=nD_prevok, D_c4a=nD_c4a, D_c4b=nD_c4b, E_suspicious=nE),
        candidates_total=len(cand), dedup_excluded=len(dedup_rows), residual=len(residual),
        verdicts=dict(FUNC=stats["FUNC"], NOT_FUNC=stats["NOT_FUNC"],
                      UNDECIDABLE=stats["UNDECIDABLE"]),
        rails=dict(vt_direct=stats["rail_vt_direct"], true_entry=stats["rail_true_entry"]),
        chan_contrib={"%s|%s" % k: v for k, v in sorted(chan_contrib.items())},
    )
    with open(os.path.join(EVID, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stat, f, ensure_ascii=False, indent=1)
    print(json.dumps(stat, ensure_ascii=False, indent=1))


def col_ok_local(pe, colp):
    d = pe.try_read(colp, 16)
    if len(d) < 16:
        return False
    sig, off, cd, tdp = struct.unpack("<IIII", d)
    if sig not in (0, 1):
        return False
    if not (pe.imagebase <= tdp < pe.imagebase + pe.sizeofimage):
        return False
    nm = pe.try_read(tdp + 8, 256)
    if not nm:
        return False
    z = nm.find(b"\x00")
    nm = nm[:z] if z > 0 else nm
    return nm.startswith(b".?AV") or nm.startswith(b".?AU")


if __name__ == "__main__":
    main()
