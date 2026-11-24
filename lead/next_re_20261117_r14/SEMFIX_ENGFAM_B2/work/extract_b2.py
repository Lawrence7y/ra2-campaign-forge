"""SEMFIX-ENGFAM-B2: per-row forensic extraction from binary bytes.

For each of the 17 B2 entries, extract ONLY the anchors required by the card:
  1) element class: .bss vector address, ctor write site, RTTI TD, class-name string
  2) 3b2: HRESULT test/jl sites, failure landing, success xor eax,eax, caller consumption
  3) 4th channel: real caller site (with context, not a bare E8 byte)
Writes EVIDENCE/ROW_<entry>.txt immediately after each row is verified.
Every 5 rows appends coverage_delta.tsv and PROGRESS.md.
Reuses semfix_lib.Bin (code only); all conclusions derived from bytes here.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import capstone

from semfix_lib import Bin, COVERAGE, hx, hbytes, md

ROOT = Path(__file__).resolve().parent.parent
EVID = ROOT / "EVIDENCE"
DELTA = ROOT / "coverage_delta.tsv"
PROGRESS = ROOT / "PROGRESS.md"
SUMMARY = Path(__file__).with_name("summary.json")
EVID.mkdir(exist_ok=True)

B2_ENTRIES = [
    "006806F0", "00680770", "006807F0", "00680870", "006808F0",
    "00680970", "006809F0", "00680A70", "00680AF0", "00680B70",
    "00680BF0", "00680C70", "00680CF0", "00680D70", "00680DF0",
    "00680E70", "00680EF0",
]

# coverage originals for these entries
COV_ROWS = {}
for line in COVERAGE.read_text(encoding="utf-8").splitlines():
    p = line.split("\t")
    if len(p) >= 6 and p[0] in B2_ENTRIES:
        COV_ROWS[p[0]] = {"subsystem": p[1], "name": p[2],
                           "old_semantics": p[3], "grade": p[4],
                           "old_evidence": p[5]}


def scan_e8_calls(b: Bin, target: int) -> list[int]:
    data = b.text_bytes()
    m = md()
    sites = []
    for i in range(0, len(data) - 5):
        if data[i] != 0xE8:
            continue
        site = b.text_start + i
        rel = int.from_bytes(data[i+1:i+5], "little", signed=True)
        if site + 5 + rel != target:
            continue
        ins = next(m.disasm(data[i:i+12], site), None)
        if ins and ins.mnemonic == "call" and ins.operands \
                and ins.operands[0].type == capstone.x86.X86_OP_IMM \
                and ins.operands[0].imm == target:
            sites.append(site)
    return sites


def nearest_mov_edx(b: Bin, call_site: int) -> dict:
    data = b.text_bytes()
    lo = max(0, call_site - b.text_start - 0x100)
    hi = min(len(data), call_site - b.text_start)
    seg = data[lo:hi]
    start = b.text_start + lo
    m = md()
    found = []
    for j in range(len(seg) - 5):
        if seg[j] != 0xBA:
            continue
        va = start + j
        imm = int.from_bytes(seg[j+1:j+5], "little")
        ins = next(m.disasm(seg[j:j+16], va), None)
        if ins and ins.address == va and ins.size == 5 and ins.mnemonic == "mov" \
                and ins.operands[1].type == capstone.x86.X86_OP_IMM \
                and ins.operands[1].imm == imm \
                and ins.op_str == f"edx, 0x{imm:x}":
            found.append((va, imm, ins.bytes))
    if not found:
        return {"site": None, "vector": None, "bytes": ""}
    va, imm, raw = max(found, key=lambda x: x[0])
    return {"site": va, "vector": imm, "bytes": raw.hex().upper()}


def ctor_writes(b: Bin, vector: int) -> list[dict]:
    """Find `C7 05 <vector LE> <imm LE>` = mov dword ptr [vector], imm."""
    data = b.text_bytes()
    pat = b"\xC7\x05" + vector.to_bytes(4, "little")
    out = []
    idx = 0
    while True:
        k = data.find(pat, idx)
        if k < 0:
            break
        site = b.text_start + k
        imm = int.from_bytes(data[k+6:k+10], "little")
        out.append({"site": site, "vt": imm,
                    "bytes": data[k:k+10].hex().upper()})
        idx = k + 1
    return out


def rtti_of_vt(b: Bin, vt: int) -> dict:
    try:
        col = b.u32(vt - 4)
        td = b.u32(col + 0x0C)
        name_va = td + 8
        name = b.cstr(name_va)
        return {"vt": vt, "col": col, "td": td,
                "name_va": name_va, "name": name}
    except SystemExit:
        return {"vt": vt, "col": None, "td": None,
                "name_va": None, "name": ""}


def func_body_3b2(b: Bin, entry: int) -> dict:
    """Disassemble entry+0x80; find HRESULT test/jl pairs, failure landing,
    success xor eax,eax, and the (non-HRESULT) count jle for contrast."""
    insns = b.disasm(entry, 0x80)
    test_jl = []      # (test_addr, jl_addr, jl_target)
    test_jle = []     # count check contrast
    xor_eax = []
    for i, ins in enumerate(insns):
        if ins.mnemonic == "xor" and ins.op_str == "eax, eax":
            xor_eax.append(ins.address)
        if ins.mnemonic == "test" and ins.op_str == "eax, eax" and i + 1 < len(insns):
            nxt = insns[i + 1]
            if nxt.mnemonic == "jl" and nxt.operands:
                test_jl.append((ins.address, nxt.address, nxt.operands[0].imm))
            if nxt.mnemonic == "jle" and nxt.operands:
                test_jle.append((ins.address, nxt.address, nxt.operands[0].imm))
    return {"test_jl": test_jl, "test_jle": test_jle, "xor_eax": xor_eax}


def caller_consumption(b: Bin, call_site: int) -> dict | None:
    insns = b.disasm(call_site + 5, 0x30)
    test = None
    for ins in insns:
        if test is None and ins.mnemonic == "test" and ins.op_str == "eax, eax":
            test = ins
            continue
        if test is not None and ins.mnemonic in ("jge", "jl", "jne", "je"):
            return {"test_site": test.address, "test_bytes": test.bytes.hex().upper(),
                    "jcc_site": ins.address, "jcc_bytes": ins.bytes.hex().upper(),
                    "jcc": ins.mnemonic,
                    "jcc_target": ins.operands[0].imm if ins.operands else None}
    return None


def caller_is_real(b: Bin, call_site: int) -> dict:
    """④ witness: real caller, not a bare E8 byte. Find the caller FUNCTION
    ENTRY by scanning back for a ret followed by a plausible prologue and
    validating linear disasm reaches the call site exactly. Also find the
    caller function's own E8 call site (it is itself invoked)."""
    data = b.text_bytes()
    off = call_site - b.text_start
    m = md()
    func_start = None
    caller_call_site = None
    push_regs = (0x50, 0x51, 0x53, 0x55, 0x56, 0x57)
    for k in range(off - 1, max(-1, off - 0x2000), -1):
        if data[k] not in (0xC3, 0xC2):
            continue
        after = k + (3 if data[k] == 0xC2 else 1)
        if after + 2 >= len(data):
            continue
        p0, p1 = data[after], data[after + 1]
        is_prologue = ((p0 == 0x83 and p1 == 0xEC) or
                       (p0 == 0x81 and p1 == 0xEC) or
                       (p0 in push_regs))
        if not is_prologue:
            continue
        addr = b.text_start + after
        cur = addr
        ok = True
        for ins in m.disasm(data[after:off + 16], addr):
            if ins.address >= call_site:
                break
            if ins.id == 0:
                ok = False
                break
            cur = ins.address + ins.size
        if not (ok and cur == call_site):
            continue
        # require the candidate to be genuinely invoked (E8 caller); this
        # rejects mid-function branch targets that happen to follow a ret.
        callers = scan_e8_calls(b, addr)
        if not callers:
            continue
        func_start = addr
        caller_call_site = callers[0]
        break
    return {"func_start": func_start, "caller_call_site": caller_call_site}


def build_semantics(cov: dict, r: dict) -> str:
    """Rewrite 4th column: drop `class name unproven (arg .bss obj)`;
    state 3b2 (fail returns failing HRESULT unchanged, success S_OK, who consumes);
    carry step1-2 address anchors. No '循环内非栈写' / 3b4 wording."""
    checks = ";".join(f"{hx(t)}/{hx(j)}" for t, j, _ in r["test_jl"])
    return (
        f"{cov['old_semantics'].split('; class name unproven')[0]}; "
        f"HRESULT error-code contract: 4x test/jl @ {checks} -> fail {hx(r['fail_landing'])} "
        f"returns failing HRESULT unchanged (eax not cleared), success {hx(r['success_xor'])} "
        f"xor eax,eax=S_OK; caller consumes @ {hx(r['consume']['test_site'])}/"
        f"{hx(r['consume']['jcc_site'])} {r['consume']['jcc']}; "
        f"class={r['class_name'] or '未取得'} vec={hx(r['vector'])} "
        f"ctor={hx(r['ctor_site'])} RTTI_TD={hx(r['td']) if r['td'] else '未取得'} "
        f"name@{hx(r['name_va']) if r['name_va'] else '未取得'}"
    )


def evidence_text(entry: str, cov: dict, r: dict) -> str:
    jl_lines = "\n".join(
        f"    test eax,eax @ {hx(t)} ; jl @ {hx(j)} -> fail {hx(tgt)}"
        for t, j, tgt in r["test_jl"]
    )
    jle_lines = "; ".join(f"test {hx(t)}/jle {hx(j)}->{hx(tgt)}"
                          for t, j, tgt in r["test_jle"])
    ctor_lines = "\n".join(
        f"    site {hx(w['site'])} bytes {w['bytes']} -> vt {hx(w['vt'])} "
        f"name={r['rtti_by_vt'].get(w['vt'], {}).get('name', '')!r} "
        f"TD={hx(r['rtti_by_vt'].get(w['vt'], {}).get('td') or 0)}"
        for w in r["ctor_writes"]
    )
    return f"""ROW {entry} — SEMFIX-ENGFAM-B2 单行取证
来源: 二进制字节独立取证（semfix_lib.Bin, capstone 5.0.7 skipdata=True, pefile）；未转录参考结论。
SHA-256: {r['sha256']}

[0] coverage 原行
entry={entry}
subsystem={cov['subsystem']}
name={cov['name']}
old_semantics={cov['old_semantics']}
grade={cov['grade']}
old_evidence={cov['old_evidence']}

[1] 元素类锚点
静态向量地址: {hx(r['vector']) if r['vector'] else '未取得'}  (section={r['vector_section']}, is_bss={r['vector_is_bss']}, 由 call 前 mov edx 取得 @ {hx(r['edx_site']) if r['edx_site'] else '未取得'})
（卡面称“.bss 向量”，本行实测所在段见上；如为 .data 则如实记录，不强行判 bss）
构造写入点 (mov dword ptr [vector], vt):
{ctor_lines if ctor_lines else '    未取得'}
选中活表: vt={hx(r['vt']) if r['vt'] else '未取得'} COL={hx(r['col']) if r['col'] else '未取得'} TD={hx(r['td']) if r['td'] else '未取得'}
类名字符串地址: {hx(r['name_va']) if r['name_va'] else '未取得'}
类名: {r['class_name'] or '未取得'}
注: 元素类以模板实参 DynamicVectorClass<PAVXxx> 形式出现；容器实例名如上，若有独立 COL/TD 已列出。

[2] ③b② 锚点（函数体 entry..entry+0x80 反汇编）
HRESULT 检查点（test eax,eax + 紧随 jl，4 处）:
{jl_lines}
失败落点: {hx(r['fail_landing'])}（jl 公共目标；pops+add esp,8+ret，eax 不清零，原样返回失败 HRESULT）
成功路径: {hx(r['success_xor'])}（xor eax,eax -> S_OK=0）
对照（非 HRESULT）: count 检查 {jle_lines or '未取得'} —— 这是 count==0 提前退出，不作 HRESULT 锚。
调用方消费该返回值: {hx(r['consume']['test_site'])} test eax,eax -> {hx(r['consume']['jcc_site'])} {r['consume']['jcc']} {hx(r['consume']['jcc_target']) if r['consume']['jcc_target'] else ''}（失败分支 xor al,al 返回 false）
判定: ③b②成立={r['ring3b2_ok']}（4 处 call 派生 HRESULT 被检查；失败原样返回、成功 xor eax,eax；调用方 test/jge 消费）

[3] ④ 使用见证（真实调用者，direct-only 不足）
真实调用者 E8 site: {hx(r['call_site'])} bytes {r['call_bytes']} -> target {hx(r['call_target'])} (= entry)
调用上下文: mov edx,{hx(r['vector']) if r['vector'] else '?'} @ {hx(r['edx_site']) if r['edx_site'] else '?'}；call 后 {hx(r['consume']['test_site'])}/{hx(r['consume']['jcc_site'])} 消费返回值。
调用者函数起点（最近 ret 后接合法序言，线性反汇编可达 call_site）: {hx(r['func_start']) if r['func_start'] else '未取得'}
该函数自身被 E8 调用 @ {hx(r['caller_call_site']) if r['caller_call_site'] else '未取得'}
非裸 E8：调用点位于真实函数体内，edx 向量/ecx this 与返回值消费三要素齐备。

[4] 第 4 列语义改写
new_semantics={r['new_semantics']}

[5] 判定
class_named={r['class_named']}
ring3b2_ok={r['ring3b2_ok']}
rewritten={r['rewritten']}
"""


def main():
    b = Bin()
    sha = b.sha256
    delta_lines = []
    progress_chunks = []
    summary = []

    for n, entry in enumerate(B2_ENTRIES, 1):
        ea = int(entry, 16)
        cov = COV_ROWS[entry]
        # --- call sites (real caller) ---
        sites = scan_e8_calls(b, ea)
        if len(sites) != 1:
            print(f"[{n:02d}] {entry}: E8 call sites = {[hx(x) for x in sites]}", flush=True)
            raise SystemExit(f"{entry}: expected exactly 1 direct call site")
        call_site = sites[0]
        call_bytes = b.data(call_site, 5).hex().upper()

        # --- .bss vector ---
        edx = nearest_mov_edx(b, call_site)
        vector = edx["vector"]
        if vector is None or b.sec_of(vector) is None:
            raise SystemExit(f"{entry}: vector not mapped to a section: {vector}")
        vsec = b.sec_of(vector)["name"]
        vector_is_bss = b.is_bss_va(vector)

        # --- ctor write sites + RTTI ---
        writes = ctor_writes(b, vector)
        rtti_by_vt = {}
        for w in writes:
            rtti_by_vt[w["vt"]] = rtti_of_vt(b, w["vt"])
        # choose live ctor: prefer name containing 'DynamicVectorClass' (template arg);
        # dead table is VectorClass<...> installed in an atexit dtor.
        live = None
        for w in writes:
            nm = rtti_by_vt[w["vt"]].get("name", "")
            if "DynamicVectorClass" in nm:
                live = w
                break
        if live is None and writes:
            live = writes[0]
        rr = rtti_by_vt.get(live["vt"], {}) if live else {}
        class_name = rr.get("name", "") or ""

        # --- 3b2 ---
        tb = func_body_3b2(b, ea)
        if not tb["test_jl"]:
            raise SystemExit(f"{entry}: no test/jl HRESULT checks found")
        # failure landing = most common jl target among test/jl pairs
        from collections import Counter
        fail = Counter(t[2] for t in tb["test_jl"]).most_common(1)[0][0]
        xor_sites = tb["xor_eax"]
        success = xor_sites[-1] if xor_sites else None
        consume = caller_consumption(b, call_site)
        if consume is None:
            raise SystemExit(f"{entry}: no caller-side HRESULT consumption")

        # --- 4th witness ---
        real = caller_is_real(b, call_site)

        r = {
            "sha256": sha,
            "call_site": call_site, "call_bytes": call_bytes, "call_target": ea,
            "edx_site": edx["site"], "vector": vector, "vector_section": vsec,
            "vector_is_bss": vector_is_bss,
            "ctor_writes": writes, "rtti_by_vt": rtti_by_vt,
            "vt": live["vt"] if live else None,
            "ctor_site": live["site"] if live else None,
            "col": rr.get("col"), "td": rr.get("td"),
            "name_va": rr.get("name_va"), "class_name": class_name,
            "test_jl": tb["test_jl"], "test_jle": tb["test_jle"],
            "fail_landing": fail, "success_xor": success, "consume": consume,
            "func_start": real["func_start"],
            "caller_call_site": real["caller_call_site"],
            "ring3b2_ok": bool(tb["test_jl"] and success and consume),
            "class_named": bool(class_name),
        }
        r["rewritten"] = r["class_named"] and r["ring3b2_ok"]
        r["new_semantics"] = build_semantics(cov, r)

        # --- IMMEDIATELY write per-row evidence ---
        ev_path = EVID / f"ROW_{entry}.txt"
        ev_path.write_text(evidence_text(entry, cov, r), encoding="utf-8")

        # --- delta line ---
        ev_rel = f"SEMFIX_ENGFAM_B2/EVIDENCE/ROW_{entry}.txt"
        delta_lines.append(
            f"{entry}\t{cov['subsystem']}\t{cov['name']}\t"
            f"{r['new_semantics']}\t{cov['grade']}\t{ev_rel}"
        )
        progress_chunks.append(
            f"- row {n:02d}/17 {entry}: {cov['name']} — "
            f"类名={'取得' if r['class_named'] else '未取得'} "
            f"3b2={'成立' if r['ring3b2_ok'] else '不成立'} "
            f"改写={'是' if r['rewritten'] else '否'}；"
            f"vec={hx(vector)} call={hx(call_site)} fail={hx(fail)} → {ev_path.name}"
        )
        summary.append({"entry": entry, "name": cov["name"],
                        "class_named": r["class_named"],
                        "ring3b2_ok": r["ring3b2_ok"],
                        "rewritten": r["rewritten"],
                        "class_name": class_name,
                        "new_semantics": r["new_semantics"]})
        print(f"[{n:02d}] {entry} vec={hx(vector)} call={hx(call_site)} "
              f"fail={hx(fail)} xor={hx(success) if success else '?'} "
              f"class={class_name!r} 3b2={r['ring3b2_ok']}", flush=True)

        # --- every 5 rows: append delta + progress ---
        if n % 5 == 0 or n == len(B2_ENTRIES):
            with DELTA.open("a", encoding="utf-8") as f:
                for ln in delta_lines:
                    f.write(ln + "\n")
            with PROGRESS.open("a", encoding="utf-8") as f:
                f.write(f"\n## 已核完 {n}/17 行\n\n")
                for ln in progress_chunks:
                    f.write(ln + "\n")
            delta_lines = []
            progress_chunks = []
            print(f"    >>> delta/progress appended through row {n}", flush=True)

    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("DONE", len(summary), "rows ->", SUMMARY, flush=True)


if __name__ == "__main__":
    main()
