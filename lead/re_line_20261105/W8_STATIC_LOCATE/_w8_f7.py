# -*- coding: utf-8 -*-
"""W8-F7 只读探针 · 索敌执行计数 / 限频计时器（TASK.md §2 F7 四问）

用法: python -I -X utf8 _w8_f7.py > _w8_f7_out.txt 2>&1
     （输出文件由 shell 重定向生成，脚本本身零写盘）
铁律: 零真机 / 零采样 / 零注入 / 只读 gamemd.exe 磁盘镜像；唯一写域 = W8_STATIC_LOCATE/
"""
import sys, time, struct, bisect
from collections import defaultdict

SWARM = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104"

_buf = []
def P(*a):
    s = " ".join(str(x) for x in a)
    _buf.append(s)
    try:
        print(s, flush=True)
    except Exception:
        pass

def D(va, n, title):
    P("-- disasm %08x (%s) --" % (va, title))
    for a, b, m, o in eng.disasm(va, n):
        P("  %08x  %-20s %s %s" % (a, b, m, o))

def main():
    global eng
    sys.path.insert(0, SWARM)
    from ra2tool import Engine
    eng = Engine()
    T0 = time.time()
    P("### W8-F7 PROBE start %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

    # A. SELF-CERT
    P()
    P("== A. SELF-CERT ==")
    P("SHA256", eng.sha)
    P("FILE_BYTES", len(eng.raw))
    P("IMAGE_BASE", hex(eng.IB))
    t1 = time.time(); stream = eng.stream; t2 = time.time()
    cov = 100.0 * sum(i.size for i in stream) / eng.TSZ
    P("COVERAGE pct=%.14f insns=%d resync=%d text_size=%d (stream build %.1fs)"
      % (cov, len(stream), eng._resync, eng.TSZ, t2 - t1))

    # B. RAW BYTE UPPER-BOUND SCANS
    P()
    P("== B. RAW .text BYTE SCAN (upper bound, misalign-inclusive) ==")
    def raw_scan(opc, target):
        tb = eng.raw[eng.TB:eng.TB + eng.TSZ]; tlo = eng.TLO
        hits = []; i = 0
        while True:
            i = tb.find(bytes([opc]), i)
            if i < 0:
                break
            rel = struct.unpack_from("<i", tb, i + 1)[0]
            if tlo + i + 5 + rel == target:
                hits.append(tlo + i)
            i += 1
        return hits
    TGTS = {
        0x6F8DF0: "Greatest_Threat", 0x6FB010: "fn_6FB010(UpdateReload?)",
        0x4D9920: "FOOT_v241_wrap", 0x445F00: "BLDG_v241_wrap",
        0x743190: "UNIT_v241_wrap", 0x51E140: "INF_v241_wrap",
        0x736CA0: "UNIT_v265_wrap", 0x4D4280: "fn_4D4280", 0x740B10: "fn_740B10",
    }
    for tgt, nm in sorted(TGTS.items()):
        P("RAW_E8 to %s (%08x): %s" % (nm, tgt, [hex(x) for x in raw_scan(0xE8, tgt)]))
        P("RAW_E9 to %s (%08x): %s" % (nm, tgt, [hex(x) for x in raw_scan(0xE9, tgt)]))

    # C. FULL-STREAM CENSUS (single pass)
    P()
    P("== C. FULL-STREAM CENSUS (resynced linear decode, single pass) ==")
    GTLO, GTHI = 0x6F8DF0, 0x6F9DB0
    ABS_KEEP = {0xA8EC34, 0xA8ED84, 0xB0EA52}
    FLD_KEEP = {0x350, 0x1FC, 0x204, 0x2FC, 0x688, 0x684, 0x5D4, 0x54E0,
                0x69C, 0x698, 0x6A0, 0x3E4}
    INI_STRS = {0x81BBE0: "Ammo", 0x843A50: "EmptyReload", 0x843A5C: "Reload",
                0x843A40: "ReloadIncrement", 0x843DB8: "PipWrap"}
    call_map = defaultdict(list); jmp_map = defaultdict(list)
    vt3c4 = []; vt424 = []
    abs_hits = defaultdict(list)
    fld_hits = defaultdict(list); fld_cnt = defaultdict(int)
    imm_hits = defaultdict(list)
    abs_writes = []
    FLD_CAP = 60
    t3 = time.time()
    for idx, ins in enumerate(stream):
        if (idx % 200000) == 0:
            print("  pass progress: %d of %d (%.0fs)" % (idx, len(stream), time.time() - t3),
                  flush=True)
        try:
            ops = ins.operands
        except Exception:
            continue
        mn = ins.mnemonic; a = ins.address
        if mn in ("call", "jmp") and ops and ops[0].type == 2:
            t = ops[0].imm
            if t in TGTS:
                (call_map if mn == "call" else jmp_map)[t].append((a, ins.bytes.hex()))
        if mn == "call" and ops and ops[0].type == 3:
            if "+ 0x3c4]" in ins.op_str:
                vt3c4.append(a)
            elif "+ 0x424]" in ins.op_str:
                vt424.append(a)
        for op in ops:
            if op.type == 2:
                if op.imm in INI_STRS:
                    imm_hits[op.imm].append(a)
            elif op.type == 3:
                m = op.mem
                if m.base == 0 and m.index == 0:
                    d = m.disp; w = bool(op.access & 2)
                    if d in ABS_KEEP:
                        abs_hits[d].append((a, "W" if w else "R", mn, ins.op_str, ins.bytes.hex()))
                    if w:
                        abs_writes.append((a, d, mn, ins.op_str))
                else:
                    d = m.disp
                    if d in FLD_KEEP:
                        fld_cnt[d] += 1
                        if len(fld_hits[d]) < FLD_CAP:
                            fld_hits[d].append((a, "W" if (op.access & 2) else "R", mn, ins.op_str))
    P("pass done, elapsed %.1fs" % (time.time() - t3))
    P()
    P("-- C1. decoded-stream direct call and jmp targets (resynced decode) --")
    for tgt in sorted(TGTS):
        P("STREAM_CALL to %s (%08x): %s" % (TGTS[tgt], tgt,
          [(hex(s), b) for s, b in call_map.get(tgt, ())]))
        P("STREAM_JMP  to %s (%08x): %s" % (TGTS[tgt], tgt,
          [(hex(s), b) for s, b in jmp_map.get(tgt, ())]))
    P()
    P("-- C2. virtual dispatch sites --")
    P("CALL [reg+0x3C4] (v241 Greatest_Threat slot) count=%d" % len(vt3c4))
    for a in vt3c4:
        P("   %08x" % a)
    P("CALL [reg+0x424] (v265 slot of 0x6FB010) count=%d" % len(vt424))
    for a in vt424:
        P("   %08x" % a)
    P()
    P("-- C3. abs-disp hits for kept globals --")
    for d in sorted(ABS_KEEP):
        hits = abs_hits.get(d, [])
        P("ABS %08x count=%d" % (d, len(hits)))
        for a, rw, mn, ops, bh in hits[:240]:
            P("   %08x %s %s %s  [%s]" % (a, rw, mn, ops, bh))
        if len(hits) > 240:
            P("   (hits truncated at 240, total %d)" % len(hits))
    P()
    P("-- C4. [reg+disp] field family (counts, first %d sites each) --" % FLD_CAP)
    for d in sorted(FLD_KEEP):
        P("FLD +0x%X count=%d" % (d, fld_cnt.get(d, 0)))
        for a, rw, mn, ops in fld_hits.get(d, []):
            P("   %08x %s %s %s" % (a, rw, mn, ops))
    P()
    P("-- C5. INI-key string imm references --")
    for va, nm in sorted(INI_STRS.items()):
        sites = imm_hits.get(va, [])
        P("STR %08x (%s) imm-site count=%d: %s" % (va, nm, len(sites), [hex(x) for x in sites]))
    P()
    P("-- C6. absolute-dword WRITE census (filtered) --")
    gt_w = [w for w in abs_writes if GTLO <= w[0] < GTHI]
    P("GT body [%08x,%08x) abs-dword-writes count=%d:" % (GTLO, GTHI, len(gt_w)))
    for a, d, mn, ops in gt_w:
        P("   %08x disp=%08x %s %s" % (a, d, mn, ops))
    for lo, hi, nm in ((0x445F00, 0x445F70, "BLDG wrap"), (0x4D9920, 0x4D995C, "FOOT wrap"),
                       (0x743190, 0x743220, "UNIT v241 wrap"), (0x736CA0, 0x736D60, "UNIT v265 wrap")):
        w2 = [w for w in abs_writes if lo <= w[0] < hi]
        P("%s [%08x,%08x) abs-dword-writes count=%d %s"
          % (nm, lo, hi, len(w2), [(hex(a), hex(d)) for a, d, _, _ in w2]))
    w3 = [w for w in abs_writes if 0xA8EC30 <= w[1] < 0xA8EC38]
    P("abs-dword-writes with disp in [A8EC30, A8EC38) count=%d:" % len(w3))
    for a, d, mn, ops in w3:
        P("   %08x disp=%08x %s %s" % (a, d, mn, ops))
    w4 = [w for w in abs_writes if w[1] == 0xA8ED84]
    P("abs-dword-writes with disp==0xA8ED84 (CurrentFrame) count=%d: %s"
      % (len(w4), [(hex(a), mn) for a, d, mn, _ in w4]))

    # D. VT3C4 SITE WINDOWS (throttle hunt)
    P()
    P("== D. v241 dispatch windows: throttle pattern hunt ==")
    addrs = [i.address for i in stream]
    by = eng.by()
    aw = sorted(abs_writes, key=lambda x: x[0]); aw_addrs = [x[0] for x in aw]
    cf_sites = sorted(a for a, rw, mn, ops, bh in abs_hits.get(0xA8ED84, ()))

    def fstart(va, maxback=0x3000):
        lo = va - maxback
        k = bisect.bisect_left(addrs, va) - 1
        while k >= 0 and addrs[k] >= lo:
            mn = by[addrs[k]].mnemonic
            if mn == "int3" or mn.startswith("ret"):
                return addrs[k + 1] if k + 1 < len(addrs) else None
            k -= 1
        return None

    def wscan(lo, hi, tag):
        k1 = bisect.bisect_left(addrs, lo); k2 = bisect.bisect_left(addrs, hi)
        h7 = []
        for ins in stream[k1:k2]:
            if ins.mnemonic in ("test", "and"):
                try:
                    ops = ins.operands
                except Exception:
                    continue
                for op in ops:
                    if op.type == 2 and op.imm in (7, -8, 0xFFFFFFF8):
                        h7.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
                        break
        i1 = bisect.bisect_left(aw_addrs, lo); i2 = bisect.bisect_left(aw_addrs, hi)
        wr = aw[i1:i2]
        i3 = bisect.bisect_left(cf_sites, lo); i4 = bisect.bisect_left(cf_sites, hi)
        cf = cf_sites[i3:i4]
        P("WINDOW %s [%08x,%08x) size=0x%X: test-and-imm7=%d absdwordWR=%d CurrentFrame-read=%d"
          % (tag, lo, hi, hi - lo, len(h7), len(wr), len(cf)))
        for x in h7:
            P("   AND7 %08x %s %s [%s]" % x)
        for x in wr:
            P("   WR  %08x disp=%08x %s %s" % x)
        for x in cf:
            P("   CFR %08x" % x)

    P("(function starts below are heuristic: nearest preceding ret or int3 boundary in resynced stream)")
    for a in vt3c4:
        fs = fstart(a)
        if fs is None:
            P("SITE %08x: no boundary found within 0x3000 bytes" % a)
            continue
        wscan(fs, a + 0x10, "vt3c4 site %08x" % a)
    P()
    wscan(0x445F00, 0x445F70, "BLDG_v241_wrap(full)")
    wscan(0x4D9920, 0x4D995C, "FOOT_v241_wrap(full)")
    wscan(0x4D4280, 0x4D45A0, "fn_4D4280(0x320 window)")
    wscan(0x740B10, 0x740C10, "fn_740B10(0x100 window)")
    wscan(0x736CA0, 0x736D60, "UNIT_v265_wrap")
    wscan(0x4F8440, 0x4F9000, "HouseClass_Update(head 0xBC0)")

    # E. FIXED DISASMS
    P()
    P("== E. FIXED DISASMS ==")
    for va in (0x6FB010, 0x6F8DF0, 0x445F00, 0x4D9920, 0x736CA0, 0x743190, 0x4D4280, 0x51E140):
        P("PAD before %08x: %s" % (va, eng.rd(va - 4, 4).hex()))
    P()
    D(0x6FB010, 0x70, "0x6FB010 body plus padding")
    P()
    D(0x6F8DF0, 0x60, "Greatest_Threat entry (RMW plus early exit)")
    P()
    D(0x6FB080, 0xC0, "0x6FB08 reload-duration calc")
    P()
    D(0x4D3780, 0x28, "vtable73 claimed target")
    P()
    D(0x445F00, 0x70, "BLDG v241 wrapper full")
    P()
    D(0x4D9920, 0x40, "FOOT v241 wrapper full")
    P()
    D(0x736CA0, 0xC0, "UNIT v265 wrapper (direct 0x6FB010 caller)")
    P()
    D(0x743190, 0x60, "UNIT v241 wrapper head")
    P()
    D(0x4D4280, 0x120, "fn_4D4280 head (upstream of FOOT wrap)")
    P()
    D(0x740B10, 0x40, "fn_740B10 head (UnitClass v151)")
    P()
    D(0x51E140, 0x40, "INF v241 head (House shared-target fast path)")
    P()
    D(0x4F8DA0, 0xA0, "HouseClass Update modulo-100 region")
    P()
    D(0x4F8F70, 0x70, "HouseClass Update and-7 region")
    P()
    D(0x714740, 0x180, "TechnoTypeClass LoadFromINI claimed Ammo region")

    # F. VTABLE SLOT PROBES
    P()
    P("== F. VTABLE SLOT PROBES (u32 reads) ==")
    slots = [
        (0x7F4D24, "TechnoClass v241 = 0x7F4960+0x3C4"),
        (0x7F4D84, "TechnoClass v265 = 0x7F4960+0x424"),
        (0x7E9058, "FootClass v241 = 0x7E8C94+0x3C4"),
        (0x7EB41C, "InfantryClass v241 = 0x7EB058+0x3C4"),
        (0x7E4280, "BuildingClass v241 = 0x7E3EBC+0x3C4"),
        (0x7F6034, "UnitClass v241 = 0x7F5C70+0x3C4"),
        (0x7F6094, "UnitClass v265 = 0x7F5C70+0x424"),
        (0x7F4A84, "TechnoClass v73 = 0x7F4960+0x124"),
        (0x7F5D94, "UnitClass v73 = 0x7F5C70+0x124"),
        (0x7EB17C, "InfantryClass v73 = 0x7EB058+0x124"),
        (0x7E8DB8, "FootClass v73 = 0x7E8C94+0x124"),
    ]
    for va, nm in slots:
        P("u32(%08x) = %08x   ; %s" % (va, eng.u32(va), nm))

    # G. INI STRING BYTES
    P()
    P("== G. INI KEY STRINGS (raw bytes at claimed VAs) ==")
    for va, nm in sorted(INI_STRS.items()):
        b = eng.rd(va, 20).split(b"\0")[0]
        P("STR %08x expect=%-16s got=%r" % (va, nm, b))

    P()
    P("### W8-F7 PROBE end, %.1fs total" % (time.time() - T0))

if __name__ == "__main__":
    main()
