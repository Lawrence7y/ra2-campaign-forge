# -*- coding: utf-8 -*-
"""
_v3.py — 独立核验脚本（V-C1..V-C6 + V-ALL）
写域唯一：D:\\Project\\ra2-campaign-forge\\lead\\re_chain_v3_verify_20261112\\
零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 attach、不读活进程内存，不写 hook/采样/MiniDump 代码。
所有哈希一律 hashlib.sha256 实算。
"""
import hashlib
import json
import os
import re
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

REPO = r"D:\Project\ra2-campaign-forge"
V2_DIR = os.path.join(REPO, "lead", "re_chain_synth_v2_20261111")
FIX_DIR = os.path.join(REPO, "lead", "re_chain_v2_fix_20261112")
XVER_DIR = os.path.join(REPO, "lead", "re_chain_v2_xverify_20261112")
OUT_DIR = os.path.join(REPO, "lead", "re_chain_v3_verify_20261112")

RE_GRADING = os.path.join(V2_DIR, "RE_GRADING.md")
LEDGER_V2 = os.path.join(V2_DIR, "LEDGER_SECTION_DRAFT_v2.md")
FIX_RECORD = os.path.join(FIX_DIR, "FIX_RECORD.md")
XVERIFY = os.path.join(XVER_DIR, "XVERIFY.md")
EXE = os.path.join(REPO, "ra2bench", "gamemd.exe")

out_lines = []


def P(s=""):
    print(s)
    out_lines.append(s)


def file_info(p):
    if not os.path.isfile(p):
        return False, 0, None
    data = open(p, "rb").read()
    return True, len(data), hashlib.sha256(data).hexdigest()


def read_lines(p):
    return open(p, "r", encoding="utf-8").read().splitlines()


P("==================================================================")
P("V3 INDEPENDENT VERIFICATION (_v3.py)")
P("==================================================================")
P("[0] 靶件与被核验件指纹自核 (hashlib.sha256)")
for label, path in [
    ("gamemd.exe", EXE),
    ("RE_GRADING.md", RE_GRADING),
    ("LEDGER_SECTION_DRAFT_v2.md", LEDGER_V2),
    ("FIX_RECORD.md", FIX_RECORD),
    ("XVERIFY.md", XVERIFY),
]:
    ok, sz, sha = file_info(path)
    P(f"  {label:28s}: exists={ok} size={sz} B sha256={sha}")
P()

rg_lines = read_lines(RE_GRADING)
lv_lines = read_lines(LEDGER_V2)

# ==============================================================================
# V-C1
# ==============================================================================
P("==================================================================")
P("[V-C1] 虚假声称是否已撤")
P("==================================================================")
p_fake = os.path.join(V2_DIR, "_pssim_rerun_out.txt")
exists_fake = os.path.exists(p_fake)
P(f"1) os.path.exists(lead\\re_chain_synth_v2_20261111\\_pssim_rerun_out.txt) = {exists_fake}")

P("2) grep '_pssim_rerun_out' in RE_GRADING.md and LEDGER_SECTION_DRAFT_v2.md:")
for name, lines in [("RE_GRADING.md", rg_lines), ("LEDGER_SECTION_DRAFT_v2.md", lv_lines)]:
    hits = [(i + 1, ln) for i, ln in enumerate(lines) if "_pssim_rerun_out" in ln]
    P(f"  {name}: {len(hits)} hit(s)")
    for ln_no, ln_txt in hits:
        has_link = "[_pssim_rerun_out.txt]" in ln_txt
        P(f"    L{ln_no} (is_markdown_link={has_link}): {ln_txt}")

runlog_path = os.path.join(FIX_DIR, "_pssim_rerun_runlog.txt")
ok_rl, sz_rl, sha_rl = file_info(runlog_path)
P(f"4) _pssim_rerun_runlog.txt: exists={ok_rl}, size={sz_rl} B, sha256={sha_rl}")
if ok_rl:
    rl_lines = read_lines(runlog_path)
    for i, ln in enumerate(rl_lines, 1):
        P(f"    runlog L{i:02d}: {ln}")
drv_stdout_path = os.path.join(FIX_DIR, "_pssim_rerun_driver_stdout.txt")
ok_ds, sz_ds, sha_ds = file_info(drv_stdout_path)
P(f"   _pssim_rerun_driver_stdout.txt: exists={ok_ds}, size={sz_ds} B, sha256={sha_ds}")
P()

# ==============================================================================
# V-C2
# ==============================================================================
P("==================================================================")
P("[V-C2] 措辞绝对化是否改准 + _regrade_scan_out.txt [OK*] 实算")
P("==================================================================")
P("1) RE_GRADING.md L20-L30 实文:")
for idx in range(19, min(30, len(rg_lines))):
    P(f"  L{idx+1:02d}: {rg_lines[idx]}")

scan_out_path = os.path.join(V2_DIR, "_regrade_scan_out.txt")
ok_so, sz_so, sha_so = file_info(scan_out_path)
P(f"\n2) 实算 _regrade_scan_out.txt (size={sz_so} B, sha256={sha_so}):")
so_lines = read_lines(scan_out_path)
ok_plain = []
ok_star = []
for i, ln in enumerate(so_lines, 1):
    if "[OK*]" in ln:
        ok_star.append((i, ln))
    elif "[OK]" in ln:
        ok_plain.append((i, ln))
P(f"  [OK]  条数 = {len(ok_plain)}")
P(f"  [OK*] 条数 = {len(ok_star)} ; 合计 = {len(ok_plain) + len(ok_star)}")
P("  [OK*] 具体行:")
for ln_no, ln_txt in ok_star:
    P(f"    L{ln_no}: {ln_txt}")
P("  [OK] 中首行仅为小节标题的条目抽核:")
for ln_no, ln_txt in ok_plain:
    if any(k in ln_txt for k in ["[T4", "[T1", "[候选点", "全局对象 0xAA1078", "◆ 5."]):
        P(f"    L{ln_no}: {ln_txt}")
P()

# ==============================================================================
# V-C3
# ==============================================================================
P("==================================================================")
P("[V-C3] R4「无别名逃逸」定级是否已统一")
P("==================================================================")
P("1) 搜索 '无别名逃逸' / '逃逸' 在 LEDGER_SECTION_DRAFT_v2.md 全文:")
for i, ln in enumerate(lv_lines, 1):
    if "逃逸" in ln or "R2" in ln or "R4" in ln:
        P(f"  LEDGER_v2 L{i:02d}: {ln}")

P("\n2) 搜索 '无别名逃逸' / '逃逸' 在 RE_GRADING.md 全文:")
for i, ln in enumerate(rg_lines, 1):
    if "逃逸" in ln:
        P(f"  RE_GRADING L{i:02d}: {ln}")
P()

# ==============================================================================
# V-C4
# ==============================================================================
P("==================================================================")
P("[V-C4] §2 理由列的「推断写成读数」是否已拆出 (R10/R11/R13/R14/R16)")
P("==================================================================")
P("1) RE_GRADING.md 中 R10..R16 及 §2.1 实文:")
for i, ln in enumerate(rg_lines, 1):
    if any(ln.startswith(f"| R{k} |") for k in [10, 11, 12, 13, 14, 15, 16]) or (54 <= i <= 63):
        P(f"  RE_GRADING L{i:02d}: {ln}")

P("\n2) LEDGER_SECTION_DRAFT_v2.md 中对应 A 节 (L23-L31)、C 节 (L46)、备注 (L54-L58):")
for i in list(range(23, 32)) + [46] + list(range(54, 59)):
    if 1 <= i <= len(lv_lines):
        P(f"  LEDGER_v2 L{i:02d}: {lv_lines[i-1]}")
P()

# ==============================================================================
# V-C5
# ==============================================================================
P("==================================================================")
P("[V-C5] 0x5012ED 独立静态反汇编实算 vs 修正件对比")
P("==================================================================")
exe_bytes = open(EXE, "rb").read()
exe_sha = hashlib.sha256(exe_bytes).hexdigest()
exe_len = len(exe_bytes)
EXP_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
P(f"1) gamemd.exe sha256 = {exe_sha} (match={exe_sha == EXP_SHA})")
P(f"   gamemd.exe length = {exe_len} B (match={exe_len == 4825360})")

# Parse PE sections to verify VA->file offset mapping around 0x5012ED and 0x824E28
e_lfanew = struct.unpack_from("<I", exe_bytes, 0x3C)[0]
num_sec = struct.unpack_from("<H", exe_bytes, e_lfanew + 6)[0]
opt_sz = struct.unpack_from("<H", exe_bytes, e_lfanew + 20)[0]
image_base = struct.unpack_from("<I", exe_bytes, e_lfanew + 24 + 28)[0]
sec_off = e_lfanew + 24 + opt_sz
sections = []
for s_i in range(num_sec):
    sh = exe_bytes[sec_off + s_i * 40 : sec_off + (s_i + 1) * 40]
    name = sh[:8].rstrip(b"\x00").decode("ascii", errors="replace")
    vsz, vaddr, rawsz, rawptr = struct.unpack_from("<IIII", sh, 8)
    sections.append((name, image_base + vaddr, vsz, rawptr, rawsz))

def va_to_foff(va):
    for name, sva, vsz, rawptr, rawsz in sections:
        if sva <= va < sva + max(vsz, rawsz):
            return rawptr + (va - sva), name
    return va - image_base, "fallback"

fo_5012ed, sec_5012ed = va_to_foff(0x5012ED)
fo_824e28, sec_824e28 = va_to_foff(0x824E28)
le32_at_5012ed = struct.unpack_from("<I", exe_bytes, fo_5012ed)[0]
str_at_824e28 = exe_bytes[fo_824e28 : fo_824e28 + 16].split(b"\x00")[0].decode("ascii", errors="replace")
P(f"2) PE 节映射核实: ImageBase=0x{image_base:08X}")
P(f"   VA 0x5012ED -> section={sec_5012ed}, file_offset=0x{fo_5012ed:X}; LE32 @0x5012ED = 0x{le32_at_5012ed:08X}")
P(f"   VA 0x824E28 -> section={sec_824e28}, file_offset=0x{fo_824e28:X}; ASCII @0x824E28 = '{str_at_824e28}'")

md = Cs(CS_ARCH_X86, CS_MODE_32)
P("\n3) Capstone 独立反汇编 0x5012EC..0x501300:")
fo_start, _ = va_to_foff(0x5012EC)
fo_end, _ = va_to_foff(0x501300)
for ins in md.disasm(exe_bytes[fo_start:fo_end], 0x5012EC):
    P(f"   0x{ins.address:06X}  {ins.bytes.hex():16s}  {ins.mnemonic:6s} {ins.op_str}")

P("\n4) Capstone 独立反汇编所在函数上下文 0x501210..0x50139B (关键片段 0x501210..0x501230 & 0x5012D9..0x50139A):")
fo_fn_s, _ = va_to_foff(0x501210)
fo_fn_e, _ = va_to_foff(0x50139B)
for ins in md.disasm(exe_bytes[fo_fn_s:fo_fn_e], 0x501210):
    if (0x501210 <= ins.address <= 0x501228) or (0x5012D9 <= ins.address <= 0x50130E) or (0x501380 <= ins.address <= 0x50139A):
        P(f"   0x{ins.address:06X}  {ins.bytes.hex():16s}  {ins.mnemonic:6s} {ins.op_str}")
P()

# ==============================================================================
# V-C6 & V-ALL
# ==============================================================================
P("==================================================================")
P("[V-C6 & V-ALL] LEDGER_SECTION_DRAFT_v2.md A 节纯净度 & 证据可定位性核验")
P("==================================================================")
# Extract Section A table rows
a_rows = []
in_sec_a = False
for i, ln in enumerate(lv_lines, 1):
    if ln.startswith("## A ·"):
        in_sec_a = True
        continue
    if in_sec_a and ln.startswith("## "):
        break
    if in_sec_a and ln.startswith("| §6xx 待编号 |"):
        parts = [c.strip() for c in ln.strip().strip("|").split("|")]
        a_rows.append((i, parts[0], parts[1], parts[2]))

P(f"A 节条目总数 = {len(a_rows)}")
UNCERTAIN_WORDS = ["未核实", "未验", "待证", "未证", "未决", "未定谳", "可能", "猜测", "疑似", "或许", "外推", "假说"]
c6_flagged = []
for idx, (ln_no, col_id, col_read, col_ev) in enumerate(a_rows, 1):
    hits = [w for w in UNCERTAIN_WORDS if w in col_read or w in col_ev]
    if hits:
        c6_flagged.append((idx, ln_no, hits, col_read, col_ev))
    P(f"  A-{idx:02d} (L{ln_no:02d}): uncertain_words={hits}")
    P(f"        读数: {col_read}")
    P(f"        证据: {col_ev}")

P(f"\n[V-C6 汇总] A 节含不确定词 ('{'/'.join(UNCERTAIN_WORDS)}') 的条目数 = {len(c6_flagged)}")

# V-ALL classification
# Mapping abbreviations from LEDGER_SECTION_DRAFT_v2.md L7:
ABBR_MAP = {
    "sf": os.path.join(REPO, "lead", "slot2_fullscan_20261111", "_sf_scan_out.txt"),
    "cw": os.path.join(REPO, "lead", "re_crashwriter_static_20261110", "_cw_disasm_out.txt"),
    "ps": os.path.join(REPO, "lead", "playerctrl_semantics_20261111", "_ps_disasm_out.txt"),
    "oo": os.path.join(REPO, "lead", "re_orphan_owners_20261110", "_oo_map_out.txt"),
    "md": os.path.join(REPO, "lead", "re_map_preset_decode_20261110", "_md_parse_out.txt"),
    "ld": os.path.join(REPO, "lead", "re_loadbench_diff_20261110", "_ld_diff_out.txt"),
}

P("\n[V-ALL 逐条检查 A 节证据列]")
cnt_with_line = 0
cnt_file_only = 0
cnt_no_ev = 0
subclause_no_line = []

for idx, (ln_no, col_id, col_read, col_ev) in enumerate(a_rows, 1):
    if not col_ev:
        cnt_no_ev += 1
        P(f"  A-{idx:02d} (L{ln_no:02d}): [无证据]")
        continue
    # Split by ';'
    clauses = [c.strip() for c in col_ev.split(";") if c.strip()]
    clause_results = []
    has_any_line_ref = False
    has_unlined_clause = False
    for cl in clauses:
        m = re.match(r"^(sf|cw|ps|oo|md|ld):(.+)$", cl)
        if m:
            abbr, rng_str = m.group(1), m.group(2)
            fpath = ABBR_MAP[abbr]
            f_lines = read_lines(fpath)
            n_lines = len(f_lines)
            # parse Lx-Ly or Lx
            ranges = [r.strip() for r in rng_str.split(",")]
            rng_ok_list = []
            for r in ranges:
                mr = re.match(r"^L?(\d+)(?:-L?(\d+))?$", r)
                if mr:
                    a = int(mr.group(1))
                    b = int(mr.group(2)) if mr.group(2) else a
                    valid = (1 <= a <= b <= n_lines)
                    rng_ok_list.append(f"{r}(valid={valid},total={n_lines})")
                    if valid:
                        has_any_line_ref = True
                else:
                    rng_ok_list.append(f"{r}(UNPARSED)")
            clause_results.append(f"{abbr} -> {', '.join(rng_ok_list)}")
        else:
            has_unlined_clause = True
            subclause_no_line.append((idx, ln_no, cl))
            clause_results.append(f"NON_FILE_LINE_CLAUSE('{cl}')")
    if has_any_line_ref:
        cnt_with_line += 1
    else:
        cnt_file_only += 1
    P(f"  A-{idx:02d} (L{ln_no:02d}): has_line_ref={has_any_line_ref}, has_unlined_subclause={has_unlined_clause} | {' ; '.join(clause_results)}")

P(f"\n[V-ALL 计数汇总（按条，共 {len(a_rows)} 条）]:")
P(f"  有行号 (文件:行 可定位) : {cnt_with_line} / {len(a_rows)}")
P(f"  只文件名 (无行号)       : {cnt_file_only} / {len(a_rows)}")
P(f"  无证据                  : {cnt_no_ev} / {len(a_rows)}")
if subclause_no_line:
    P("  [注] 含附加非 '缩写:行号' 子句的条目（主引用已有 文件:行，附加子句未写文件名+行号）:")
    for idx, ln_no, cl in subclause_no_line:
        P(f"    A-{idx:02d} (L{ln_no:02d}): '{cl}' （对应 RE_GRADING R9 L45 为 scratch/boot_probe/arm_a/XMP29U2.MAP:107-263）")

out_file = os.path.join(OUT_DIR, "_v3_stdout.txt")

# ==============================================================================
# V-INTEGRITY: 170 既有件指纹复核（确认除两份被修正件外 168 件零漂移）
# ==============================================================================
P("\n==================================================================")
P("[V-INTEGRITY] 170 个既有件基线对拍 (基于 _fix_baseline.json)")
P("==================================================================")
fix_base_path = os.path.join(FIX_DIR, "_fix_baseline.json")
if os.path.isfile(fix_base_path):
    base_data = json.load(open(fix_base_path, "r", encoding="utf-8"))
    drift_list = []
    missing_list = []
    for rel_p, val in base_data.items():
        abs_p = os.path.join(REPO, rel_p)
        if not os.path.isfile(abs_p):
            missing_list.append(rel_p)
        else:
            b = open(abs_p, "rb").read()
            cur = [hashlib.sha256(b).hexdigest(), len(b)]
            if list(val) != cur:
                drift_list.append((rel_p, val, cur))
    P(f"  baseline_total={len(base_data)} drift={len(drift_list)} missing={len(missing_list)}")
    for rp, old_v, new_v in drift_list:
        P(f"    DRIFT: {rp}: {old_v[0][:12]}..({old_v[1]} B) -> {new_v[0][:12]}..({new_v[1]} B)")

with open(out_file, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(out_lines) + "\n")
P(f"\n[DONE] stdout written to {out_file}")
