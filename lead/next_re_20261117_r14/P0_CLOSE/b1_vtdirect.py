#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 B：补算 10 片「虚表直指、atlas 未收录入口」。

虚表定界完全自 .rdata 现场完成（**不读 vtables_v2.json**）：
  .rdata 中「连续 dword 全部落在 .text 内」的极大游程 = 一张表的槽序列；
  游程前一个 dword 若是指向 RTTI CompleteObjectLocator 的指针
  （COL.sig∈{0,1} ∧ COL+0xC → TypeDescriptor ∧ TD+8 = ".?AV"/".?AU" 名）⇒ 认作 vftable。

计数（与 C07/C09/C10 同口径）：
  槽值 S ∈ .text ∧ S ∉ 任何 atlas 区间 [entry, entry+size) ∧ S%16==0 ∧ 前驱 ∈ {nop,ret,jmp,int3}

输出：VT_DIRECT_ENTRIES.tsv + vt_tables.tsv（定界审计用）
"""
import io
import os
import sys
import json
import struct
import bisect

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p0lib import RawPE, Sweep, Atlas, SLICES, trailing_pad, predecessor   # noqa: E402


def cstr(pe, va, n=256):
    b = pe.read(va, n)
    if not b:
        return None
    z = b.find(b"\x00")
    if z <= 0:
        return None
    return b[:z]


def demangle(s):
    t = s.decode("latin1")
    if t.startswith(".?AV") or t.startswith(".?AU"):
        t = t[4:]
    if t.endswith("@@"):
        t = t[:-2]
    return t.replace("?$", "T_").replace("@", "_")


def sec_runs(pe, secname):
    """返回 (rlo, words)；words[i] 对应 va = rlo + 4*i。"""
    s = pe.byname[secname]
    rlo = pe.imagebase + s["va"]
    buf = pe.read(rlo, s["rawsize"])
    nw = len(buf) // 4
    words = list(struct.unpack_from("<%dI" % nw, buf, 0))
    return rlo, words, nw


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pe = RawPE()
    t = pe.byname[".text"]
    TLO = pe.imagebase + t["va"]
    THI = TLO + t["vsize"]
    sw = Sweep(pe, TLO, THI)
    at = Atlas()
    print(".text=[%08X,%08X)  sweep=%d insn  atlas=%d rows" % (TLO, THI, sw.n, at.n))

    rlo, words, nw = sec_runs(pe, ".rdata")
    print(".rdata=[%08X,%08X) words=%d" % (rlo, rlo + 4 * nw, nw))

    def in_text(v):
        return TLO <= v < THI

    def col_name(colp):
        if not (pe.imagebase <= colp < pe.imagebase + pe.sizeofimage):
            return None, None
        d = pe.try_read(colp, 16)
        if len(d) < 16:
            return None, None
        sig, off, cd, tdp = struct.unpack("<IIII", d)
        if sig not in (0, 1):
            return None, None
        if not (pe.imagebase <= tdp < pe.imagebase + pe.sizeofimage):
            return None, None
        nm = cstr(pe, tdp + 8)
        if not nm or not (nm.startswith(b".?AV") or nm.startswith(b".?AU")):
            return None, None
        return demangle(nm), off

    # 极大 .text 指针游程
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
    print("槽游程（连续 .text 指针）= %d 段，合计 %d 槽"
          % (len(runs), sum(j - i for i, j in runs)))

    tables, bare = [], []
    for i, j in runs:
        va = rlo + 4 * i
        colp = words[i - 1] if i >= 1 else 0
        cls, off = col_name(colp)
        rec = dict(vt=va, n=j - i, slots=words[i:j], col=colp, cls=cls, col_off=off,
                   end=va + 4 * (j - i),
                   next_word=(words[j] if j < nw else None))
        (tables if cls else bare).append(rec)

    print("vftable（COL 可验）= %d 张，槽合计 %d" % (len(tables), sum(x["n"] for x in tables)))
    print("无 COL 的游程（非 vftable：函数指针表/无 RTTI 子表）= %d 段，槽 %d"
          % (len(bare), sum(x["n"] for x in bare)))
    print("表数自校：期望 1214 表 / 14,044 槽 → %s"
          % ("MATCH" if (len(tables) == 1214 and sum(x["n"] for x in tables) == 14044)
             else "MISMATCH（须解释）"))

    # ---- 逐槽检查 ----
    hits = []
    all_slots = 0
    for tb in tables:
        for k, S in enumerate(tb["slots"]):
            all_slots += 1
            if not in_text(S):
                continue
            if at.in_atlas(S):
                continue
            a16 = (S % 16 == 0)
            pr = predecessor(pe, sw, S)
            prev_ok = pr["kind"] in ("nop", "ret", "jmp", "int3")
            pb = pe.read(S - 1, 1)
            pad, padb = trailing_pad(pe, S)
            hole = at.hole(S, TLO, THI)
            hits.append(dict(vt=tb["vt"], slot=k, T=S, cls=tb["cls"], align16=a16,
                             prev=pr["desc"], prev_kind=pr["kind"], prev_ok=prev_ok,
                             prev_byte=(pb.hex() if pb else ""), pad=pad,
                             pass_check=(a16 and prev_ok), hole=hole,
                             nslots=tb["n"]))
    print("虚表槽总数（自定界）= %d；落在 .text 且 atlas 未收录 = %d；其中通过基本检查 = %d"
          % (all_slots, len(hits), sum(1 for h in hits if h["pass_check"])))

    # 片归属（按目标地址；区间取各片 atlas 行区间）
    ranges = []
    for sl in SLICES:
        a, b = at.slice_range(sl)
        ranges.append((sl, a, b))
    ranges.sort(key=lambda x: x[1])

    def slice_of(x):
        for sl, a, b in ranges:
            if a <= x < b:
                return sl
        # 片间夹缝：归到最近的前一片（显式标记）
        for sl, a, b in ranges:
            if x < a:
                return sl + "*"
        return "C10*"

    for h in hits:
        h["slice"] = slice_of(h["T"])

    # 去重：同一目标可被多张表/多个槽直指。计「漏收入口数」的单位必须是**不同地址**
    # （C07=24 / C09=17 / C10=6 均为 distinct 地址口径，见 C07 `_audit\a8_vtdirect.json`）。
    seen = {}
    for h in hits:
        seen.setdefault(h["T"], 0)
        seen[h["T"]] += 1
    for h in hits:
        h["dup"] = seen[h["T"]]

    # ---- 输出 ----
    outp = os.path.join(HERE, "VT_DIRECT_ENTRIES.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="") as f:
        f.write("slice\tvt_addr\tslot_idx\ttarget\talign16\tprev_byte\tin_atlas\tnote\n")
        for h in sorted(hits, key=lambda x: (x["slice"], x["T"], x["vt"], x["slot"])):
            note = ("cls=%s; prev=%s(%s); pad=%d; pass=%s; hole=%s; refs=%d"
                    % (h["cls"], h["prev"], h["prev_kind"], h["pad"],
                       "Y" if h["pass_check"] else "N",
                       ("%08X-%08X" % h["hole"]) if h["hole"] else "none",
                       h["dup"]))
            f.write("%s\t%08X\t%d\t%08X\t%s\t%s\tN\t%s\n" % (
                h["slice"], h["vt"], h["slot"], h["T"],
                "Y" if h["align16"] else "N", h["prev_byte"], note))
    print("wrote %s (%d 行 = %d 个不同地址)" % (outp, len(hits), len(seen)))

    with io.open(os.path.join(HERE, "vt_tables.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("vt_addr\tn_slots\tend\tcol\tcls\tcol_off\n")
        for tb in tables:
            f.write("%08X\t%d\t%08X\t%08X\t%s\t%s\n" % (
                tb["vt"], tb["n"], tb["end"], tb["col"], tb["cls"],
                "" if tb["col_off"] is None else tb["col_off"]))

    # ---- 汇总（distinct 地址 = 可加量；slot 行为辅助） ----
    print("\n=== 各片「虚表直指、atlas 未收录」===")
    print("%-6s %10s %8s %8s" % ("slice", "rows(vt,slot)", "distinct", "dups>1"))
    per = {}
    for sl, a, b in ranges:
        rs = [h for h in hits if h["slice"].startswith(sl)]
        ds = sorted({h["T"] for h in rs})
        per[sl] = dict(lo="%08X" % a, hi="%08X" % b, rows=len(rs), distinct=len(ds),
                       list=["%08X" % x for x in ds])
        print("%-6s %10d %8d %8d" % (sl, len(rs), len(ds),
                                     sum(1 for x in ds if seen[x] > 1)))
    print("%-6s %10d %8d %8d" % ("TOTAL", len(hits), len(seen),
                                 sum(1 for x in seen if seen[x] > 1)))

    # 敏感性：无 COL 游程若也当作表
    extra = 0
    for tb in bare:
        for S in tb["slots"]:
            if in_text(S) and not at.in_atlas(S) and S % 16 == 0:
                pr = predecessor(pe, sw, S)
                if pr["kind"] in ("nop", "ret", "jmp", "int3"):
                    extra += 1
    print("\n敏感性：若把 %d 段无 COL 游程也算作表，另有 %d 个通过检查的目标（不并入交付数）"
          % (len(bare), extra))

    # 敏感性2：不加 align16 / 前驱要求
    print("敏感性：仅「.text ∧ atlas 未收录」= %d；仅加 align16 = %d"
          % (len(hits), sum(1 for h in hits if h["align16"])))

    json.dump(dict(n_tables=len(tables), n_slots=sum(x["n"] for x in tables),
                   n_bare=len(bare), bare_slots=sum(x["n"] for x in bare),
                   n_rows=len(hits), n_distinct=len(seen),
                   per_slice=per, extra_bare=extra),
              io.open(os.path.join(HERE, "vt_direct_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("wrote vt_direct_summary.json")


if __name__ == "__main__":
    main()
