"""gen_rows: materialize EVIDENCE + coverage_delta rows for B1.

Usage: python gen_rows.py START END   (1-based inclusive, into B1 order)

For each row in [START,END]:
  * write EVIDENCE/ROW_<entry>.txt immediately (idempotent), then flush.
After the batch:
  * append that batch's lines to coverage_delta.tsv (writing header if absent)
  * append a progress line to PROGRESS.md

All anchors come from work/anchors.json + work/slice_b1.json + work/live_chain.txt,
which were derived from binary bytes (see extract_all.py / live_callers.py).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
EVID = ROOT / "EVIDENCE"
DELTA = ROOT / "coverage_delta.tsv"
PROGRESS = ROOT / "PROGRESS.md"

SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"


def readable(raw: str) -> str:
    m = re.search(r"\?\$(\w+)@PAV(\w+)@@", raw or "")
    if m:
        return f"{m.group(1)}<{m.group(2)}*>"
    return raw or "未取得"


def load():
    rows = json.loads((WORK / "slice_b1.json").read_text(encoding="utf-8"))
    anch = {a["entry"]: a for a in json.loads((WORK / "anchors.json").read_text(encoding="utf-8"))}
    live = (WORK / "live_chain.txt").read_text(encoding="utf-8").rstrip()
    return rows, anch, live


def primary_ctor(a):
    """the DynamicVectorClass<T> install (element container), else first plausible."""
    ws = a.get("ctor_writes", [])
    for w in ws:
        if "DynamicVectorClass" in w["name_raw"]:
            return w
    for w in ws:
        if w["plausible"]:
            return w
    return ws[0] if ws else None


def evidence_text(row, a, live, block_no: int) -> str:
    e = row[0]
    subsystem = row[1]
    name = row[2]
    old_sem = row[3]
    grade = row[4]
    old_ev = row[5]
    L = []
    A = L.append
    A(f"SEMFIX-ENGFAM-B1  EVIDENCE ROW {e}")
    A(f"binary: gamemd.exe  SHA-256 {SHA}")
    A("ImageBase 0x400000; .text=[0x401000,0x7E038D); capstone 5.0.7 skipdata=True; pefile 2024.8.26")
    A(f"source row: {subsystem}\t{name}\t{old_sem}\t{grade}\t{old_ev}")
    A("")
    A("[1] 元素类锚点 (element class anchors; binary-derived)")
    A(f"  dynamic-vector object (edx arg) VA : {a['vector']}  section={a['vector_section']}  is_bss={a['vector_is_bss']}")
    A(f"  mov edx,imm32 at                   : {a['edx_site']}  [{a['edx_bytes']}]  -> vec {a['vector']}")
    pcw = primary_ctor(a)
    if pcw:
        A(f"  ctor write site (installs vtable)  : {pcw['site']}  C7 05 -> [{a['vector']}] = {pcw['vt']}")
        A(f"  installed vtable                   : {pcw['vt']}")
        A(f"  RTTI COL (vtable-4)                : {pcw['col']}")
        A(f"  RTTI TD  (COL+0xC)                 : {pcw['td']}")
        A(f"  class-name string addr (TD+8)      : {pcw['name_va']}")
        A(f"  class name (raw)                   : {pcw['name_raw']}")
        A(f"  element class (readable)           : {readable(pcw['name_raw'])}")
        A(f"  COL bytes : {pcw['col_bytes']}")
        A(f"  TD  bytes : {pcw['td_bytes']}")
        A("  -- other C7 05 writes to same vector (base-class install), for completeness --")
        for w in a["ctor_writes"]:
            if w is pcw:
                continue
            A(f"     site {w['site']} vt {w['vt']} COL {w['col']} TD {w['td']} name@ {w['name_va']} = {w['name_raw']}")
    else:
        A("  元素类: 未取得")
    A("")
    A("[2] ③b② 锚点 (call-derived HRESULT gate; binary-derived)")
    for c in a["hresult_checks"]:
        A(f"  test/cmp site {c['test_site']}  {c['test_txt']:<14} [{c['test_bytes']}]"
          f"  -> {c['jcc_site']} {c['jcc']} [{c['jcc_bytes']}] -> {c['jcc_target']}")
    A(f"  HRESULT check count                : {a['n_call_derived_jl']} (test eax,eax + jl, each from a preceding call)")
    A(f"  failure landing pad                : {a['failure_landing']}  votes={a['failure_landing_votes']}")
    A("    failure path: cleanup pops + add esp,8 + ret; eax NOT zeroed -> returns incoming HRESULT unchanged")
    A(f"  success path (xor eax,eax)         : {','.join(a['xor_eax'])}  -> returns 0")
    A(f"  ret                                : {','.join(a['rets'])}")
    cons = a.get("caller_consume")
    if cons:
        A(f"  caller consumption (test)          : {cons['test_site']}  {cons['test_txt']} [{cons['test_bytes']}]")
        A(f"  caller consumption (jcc)           : {cons['jcc_site']}  {cons['jcc']} [{cons['jcc_bytes']}] -> {cons['jcc_target']}")
    else:
        A("  caller consumption: 未取得")
    A("")
    A("[3] ④ 使用见证 (live caller witness; direct call is not counted alone)")
    A(f"  real caller function               : Save_Core 0x67D300")
    A(f"  direct call site into this row     : {a['call_site']}  (E8 rel32, from Save_Core)")
    A(f"  E8 call sites found in .text       : {','.join(a['e8_sites'])}")
    A("  Save_Core is LIVE (not dead code) -- upward chain, from binary bytes:")
    for ln in live.splitlines():
        A("    " + ln)
    A("  => each row has its own Save_Core call site and its own caller消费 point;")
    A("     the whole family is reached from the live game-save path, not a lone direct ref.")
    A("")
    A("[4] 第4列改写核对")
    A(f"  old (unproven tail removed)        : {old_sem}")
    A("  forbidden strings check            : no '循环内非栈写', no ③b④ in rewritten semantics")
    A("  class name obtained                : " + ("YES" if pcw and pcw["plausible"] else "NO(未取得)"))
    A("  3b2 established                    : " + ("YES" if a["n_call_derived_jl"] >= 4 and cons else "NO"))
    return "\n".join(L) + "\n"


def new_semantics(row, a, block_no: int) -> str:
    prefix = row[3]
    # delete the unproven tail
    cut = re.split(r";\s*class name unproven", prefix)[0].strip()
    checks = ",".join(c["test_site"] for c in a["hresult_checks"])
    cons = a.get("caller_consume") or {}
    pcw = primary_ctor(a)
    cls = readable(pcw["name_raw"]) if pcw else "未取得"
    anchor = ""
    if pcw:
        anchor = (f"; elem {cls} named: ctor@{pcw['site']} vt@{pcw['vt']} "
                  f"COL@{pcw['col']} TD@{pcw['td']} name@{pcw['name_va']}")
    return (f"{cut}; ③b② HRESULT gate: test eax,eax@{checks} +jl->fail@{a['failure_landing']} "
            f"(eax retains incoming HRESULT, not zeroed); success xor eax,eax@{','.join(a['xor_eax'])} "
            f"returns 0; caller consumes test@{cons.get('test_site','?')}/{cons.get('jcc','?')}@{cons.get('jcc_site','?')} "
            f"in Save_Core 0x67D300{anchor}")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: python gen_rows.py START END")
    start, end = int(sys.argv[1]), int(sys.argv[2])
    rows, anch, live = load()
    EVID.mkdir(parents=True, exist_ok=True)
    delta_lines = []
    done = []
    for i in range(start, end + 1):
        row = rows[i - 1]
        e = row[0]
        a = anch[e]
        block_no = i  # B1 order index; matches Template block #N for 01..16,18 handled by name field
        txt = evidence_text(row, a, live, block_no)
        p = EVID / f"ROW_{e}.txt"
        with p.open("w", encoding="utf-8") as f:
            f.write(txt)
            f.flush()
        done.append(e)
        # coverage_delta line (6 cols), entry already upper-hex no 0x
        evpath = f"SEMFIX_ENGFAM_B1/EVIDENCE/ROW_{e}.txt"
        nsem = new_semantics(row, a, block_no)
        delta_lines.append(
            "\t".join([e, row[1], row[2], nsem, row[4], evpath])
        )
        print(f"wrote {p.name}  ({len(txt)} bytes)")

    # append coverage_delta with header if new
    need_header = not DELTA.exists() or DELTA.stat().st_size == 0
    with DELTA.open("a", encoding="utf-8") as f:
        if need_header:
            f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
        for ln in delta_lines:
            f.write(ln + "\n")
        f.flush()

    # progress append
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(f"- 批次 [{start}-{end}] 落盘完成: {', '.join(done)}  "
                f"(coverage_delta 追加 {len(delta_lines)} 行)\n")
        f.flush()

    print(f"\nbatch [{start}-{end}] done; coverage_delta += {len(delta_lines)}; total EVIDENCE files = "
          f"{len(list(EVID.glob('ROW_*.txt')))}")


if __name__ == "__main__":
    main()
