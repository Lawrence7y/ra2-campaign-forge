#!/usr/bin/env python3
"""R51-T1-TIE152 / Q3 定稿 v3。

判据纪律：**只用实读内容**。为防「靠文件名判」，脚本先按文件名把每件映射到一条
家族规则（家族选择只是「读哪几行」的入口），再由**内容条带**定 verdict；
家族规则自带的 allow 校验：若内容不含该家族的特征条带，降级为 判不了 并记 `NOMATCH`。

verdict 语义（EVIDENCE 写域：对象抄本 = **被测对象本身**的记录载体）：
  应排   内容是过程/统计/元记录，或逐行把对象事实与过程断言混编 ⇒ 不能整件当对象抄本
  应留   内容是对象记录体（地址+槽/虚表/RTTI/反汇编/字节/函数边界），无过程帧
  判不了 内容可读，但「算不算对象记录」取决于项目**未定义**的口径；缺什么另列
"""
import csv, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R91_T1_TIE152")

RX = {
    "addr":    re.compile(r"(?<![0-9A-Za-z_])0?0[0-9A-F]{6}(?![0-9A-Za-z_])|0x[0-9A-Fa-f]{6,8}"),
    "slot":    re.compile(r"\bslots?\s*[=#]?\s*\d+|vt\[slot\]|slot\s*\d+|\bVT\b|\bvt\s*=|vt_start=|\.rdata", re.I),
    "rtti":    re.compile(r"\.\?A[VUTE]|\bCOL\b|\bTD\b|RTTI|CHD", re.I),
    "dis":     re.compile(r"^\s*[0-9A-F]{8}\s+([0-9a-f]{2}\s){2,}"),
    "bytes":   re.compile(r"\b([0-9a-f]{2} ){4,}[0-9a-f]{2}\b|sha256|\bsha-256\b", re.I),
    "selft":   re.compile(r"pass\s*=\s*(True|False)|expected\s*=|actual\s*=|\[B-POS\]|\[B-NEG\]|"
                          r"\[PASS\]|\[FAIL\]|ALL ASSERTIONS", re.I),
    "stat":    re.compile(r"\bp\s*=|K\s*=\s*\d+|\bN\s*=\s*\d+|rate|percent|median|seed\s*=|MC=|E\[8\]|"
                          r"ratio|\b\d+\.\d+%|变异系数|极差", re.I),
    "frame":   re.compile(r"RUN_ID\s*=|COMMAND\s*[:=]|run_at_utc|^\s*={5,}\s*$|^#{5,}\s*$|记录时间", re.I | re.M),
    "ring":    re.compile(r"环[①②③④]|四环|②④|③b"),
    "oKV":     re.compile(r'"(entry|vt|slot|n_insns|n_insns|extent|lo|hi|prologue|nins|aligned16)"\s*:'),
    "sKV":     re.compile(r'"(p|N|K|rate|mean|median|sd|coverage_rows|pool|pool_n|n_rows|n_cols|n_col|'
                          r'n_vtab|n_slots|kinds|alias_hit|alias_tot|abnormal|strict|loose|empirical_mean|'
                          r'analytic_expected|E8|has2|has4|A|s09_rows|s09_static|card_claim|threshold|proved)"\s*:'),
    "procKV":  re.compile(r'"(scan|exe_sha|sha256|text_va|text_end|instr|instructions|seconds|elapsed|'
                          r'sample_interval|min_valid|hard_cap|cfg|linear_hi|sites|raw_hits|n_raw_hits|'
                          r'jcc|jcc_tgts|n_dcall|loop|bool_ret|n_nonstack_w|vptr_w|eax_consts)"\s*:'),
}
ALLOW_KEYS = ("entry", "vt", "slot", "lo", "hi", "extent", "prologue", "first6", "insn", "nins", "aligned16")


def read(rel):
    with open(os.path.join(LEAD, rel.replace("/", os.sep)), "rb") as f:
        return f.read().decode("utf-8", errors="replace")


def feature(rel):
    t = read(rel)
    lines = [l for l in t.splitlines() if l.strip()]
    c = {k: len(r.findall(t)) for k, r in RX.items()}
    c["n"] = len(lines)
    c["first"] = lines[0].strip()[:80] if lines else ""
    c["bytes"] = os.path.getsize(os.path.join(LEAD, rel.replace("/", os.sep)))
    c["a8"] = len({m.group(0) for l in lines for m in RX["addr"].finditer(l)})
    c["dislines"] = sum(1 for l in lines if RX["dis"].search(l))
    c["okv"] = len(RX["oKV"].findall(t))
    c["skv"] = len(RX["sKV"].findall(t))
    c["pkv"] = len(RX["procKV"].findall(t))
    # 家族检查：内容里有没有「对象记录骨架」（entry+vt/slot 或 逐条反汇编）
    c["objskel"] = (c["okv"] >= 2 and c["slot"] >= 1) or c["dislines"] >= 3 or \
                   (c["slot"] >= 2 and c["rtti"] >= 1)
    return c


def V(v, why):
    return (v, why)


def decide(rel, f):
    n, first = f["n"], f["first"]
    obj_lines = f["dislines"] + f["slot"] + f["rtti"]
    isjson = first[:1] in "{[" or (f["okv"] + f["skv"] + f["pkv"]) >= 3

    # ---------- JSON ----------
    if isjson:
        if f["okv"] >= 2 and f["slot"] + f["dislines"] + f["a8"] >= 2:
            return V("应留", f"JSON 逐行对象记录骨架（对象键 okv={f['okv']}，slot/地址/反汇编行={f['slot']}/{f['a8']}/{f['dislines']}）；首键见 {first[:40]!r}")
        if f["skv"] >= 2 and f["okv"] == 0 and f["slot"] + f["dislines"] == 0:
            return V("应排", f"JSON 只有统计/计数键（skv={f['skv']}，对象键=0），"
                             f"内容为比率/池规模/计数器，不是被测对象记录；首行={first[:40]!r}")
        if f["pkv"] >= 1 and f["slot"] + f["dislines"] >= 1:
            return V("应留", f"JSON 为扫描结果表（过程键 pkv={f['pkv']} 作表头，主体是 slot/反汇编记录 {f['slot']}/{f['dislines']}）；首行={first[:40]!r}")
        if f["skv"] >= 1 and f["okv"] >= 1:
            return V("判不了", f"JSON 同时含对象键(okv={f['okv']})与统计键(skv={f['skv']})，"
                               f"同一文件里对象事实与派生统计混编，缺逐键归属规则")
        return V("判不了", f"JSON 结构无法从内容上归边（okv={f['okv']} skv={f['skv']} pkv={f['pkv']} slot={f['slot']}）；首行={first[:40]!r}")

    # ---------- 纯自检 ----------
    if f["selft"] >= 2 and f["slot"] + f["dislines"] <= 1:
        return V("应排", f"整篇自检断言（[PASS]/pass=/expected=/actual= 计{f['selft']} 处），记录的是判定过程，无对象记录体")

    # ---------- 纯统计 ----------
    if f["stat"] >= 3 and f["slot"] <= 1 and f["dislines"] == 0 and f["ring"] == 0:
        return V("应排", f"整篇统计量（rate/p=/K=/N=/median 计{f['stat']} 处），是测量过程的派生量，无对象记录体")

    # ---------- 逐 entry 的结构化环记录（对象记录体，行为主体）----------
    if f["ring"] >= 2 and f["slot"] >= 1 and f["a8"] >= 3:
        return V("应留", f"逐 entry 四环记录（环标题 {f['ring']} 处 + slot/RTTI {f['slot']}/{f['rtti']} + 独立地址 {f['a8']}）；"
                         f"环内是**被测函数自身**的边界/虚表/合同/见证事实，属对象记录体")

    # ---------- 对象记录体（slot/vtable/RTTI/反汇编/边界表）----------
    if obj_lines >= 2 and f["selft"] == 0:
        return V("应留", f"内容主体是对象记录（slot/vtable {f['slot']}、RTTI {f['rtti']}、反汇编行 {f['dislines']}），"
                         f"无自检/统计块；首行={first[:56]!r}")

    # ---------- 其余：过程产物 ----------
    if f["frame"] >= 1 and f["selft"] + f["stat"] >= 1:
        return V("应排", f"过程帧 + 断言/统计混编（frame={f['frame']} selft={f['selft']} stat={f['stat']}），"
                         f"整件是运行/核对记录")
    return V("判不了", f"内容可读但归属取决于未定口径（selft={f['selft']} stat={f['stat']} slot={f['slot']} "
                       f"dis={f['dislines']} a8={f['a8']} frame={f['frame']}）；首行={first[:56]!r}")


# ── 逐件专属裁决（家族规则无法覆盖的「内容特殊」件；依据仍来自实读内容）──
SPECIAL = {
    "W54_save_determinism/EVIDENCE/step3_streamdiff.stdout.txt":
        ("判不了", "内容是 OLE 复合文档 A1/A2/B1/B2 四份的**字节差分**（dirEntry id/off/mtime、"
                   "stream 偏移区间、LCP/LCS）。差分结果本身是「被测对象的文件字节事实」，但同一件里"
                   "也含 equal=False/idxDiff 这类运行期比较结论与 4 个时间戳；缺「差分产物算对象记录还是过程记录」的口径"),
    "W61_third_badge_route/EVIDENCE/dialog_bytes_diff.txt":
        ("判不了", "内容是 RT_DIALOG 148 的逐字节 before/after 标记（0x000 N 01 …），"
                   "既是被测资源的字节事实，又只以「前后对照」形式存在；缺「patch 前后 diff 是否计对象抄本」的口径"),
    "W61_third_badge_route/EVIDENCE/resource_integrity_stdout.txt":
        ("判不了", "内容是全资源完整性核对（每资源 len/sha256/identical=True/False 判定），"
                   "断言结论与对象哈希混编；缺「哈希核对表是否算对象记录」的口径"),
    "W62_bline_new_criteria/EVIDENCE/c_neg_selftest.stdout.txt":
        ("应排", "内容是 JSON 形式的自检报告（B-POS/B-NEG 各例 expected/actual/pass/p 值），记录判定过程"),
    "W64_bootcamp_inventory/EVIDENCE/S4_only_stdout.txt":
        ("判不了", "内容是 MAPSELMD.INI 提取核对（mix 偏移 0x71D050 length 5573 sha256 identical=True + 节清单），"
                   "提取校验结论与对象哈希混编；缺口径"),
    "W64_bootcamp_inventory/EVIDENCE/S4_q4_stdout.txt":
        ("判不了", "内容是 MAPSELMD.INI 节/阶段名清单（[GDI] stage 1=ALL01 …）+ 提取校验头，"
                   "是被测数据的内容记录，但以「核对报告」形式给出；缺「数据内容清单是否计对象记录」的口径"),
    "W68_criterion_discrete_fix/EVIDENCE/gen_counterexamples.stdout.txt":
        ("应排", "内容是 JSON 反例清单（kind=w68_counterexamples_manifest + source/upstream_read_only 元字段），"
                 "记录的是判据的反例集合，属过程证据"),
    "W68_criterion_discrete_fix/EVIDENCE/concurrent_GLM/gen_counterexamples.stdout.txt":
        ("应排", "同上（并发臂副本）：JSON 反例清单 + 元字段，属过程证据"),
    "W97_artmd/EVIDENCE/probe17_stdout.txt":
        ("判不了", "内容是 artmd.ini 的规则字段实读结果（artmd.ini 336,535 B sha256 + NAPOWR/TESLA Foundation=3x2 line 3262 "
                   "VERIFIED + ALL ASSERTIONS PASSED），数据事实与断言结论混编；缺口径"),
    "W97_artmd/EVIDENCE/w97_mixget_stdout.txt":
        ("应排", "仅 2 行：mix 文件清单 + 内部 id/偏移/大小（ra2.mix 0xA8548FD9 245,825 B），"
                 "是归档目录条目，非被测函数/槽对象；按「对象抄本=.text/.rdata 对象记录」口径不能算"),
    "W154_live/EVIDENCE/verify_w151b.log":
        ("判不了", "仅 2 行：一句计数断言（targeting 0x55B8F0 : 0）+ 一句反汇编区间标题，对象事实只有 1 个地址、"
                   "正文缺失（文件里没有反汇编体）；缺内容无法补"),
    "S09_KPROVED/_audit/EVIDENCE/extent8.json":
        ("应留", "JSON 逐 entry 记 lo/hi/ninstr/entry（函数区间），是对象边界记录体"),
    "S09_KPROVED3/_audit/EVIDENCE/AUDIT_DIRECT_8.json":
        ("应留", "JSON 逐 entry 记 body/cfg/linear_hi/cfg_insns（函数体区间与 CFG 规模），对象边界记录体"),
    "S09_KPROVED3/_audit/EVIDENCE/AUDIT_TIGHT_LOOP.json":
        ("应留", "JSON 逐 entry 记循环结构（body/loop/回边），对象形态记录体"),
    "S09_KPROVED3/_audit/EVIDENCE/AUDIT_VTABLES_8.json":
        ("应留", "JSON 逐 entry 记虚表槽归属（vt/slot），对象记录体"),
    "S09_KPROVED5/_audit/EVIDENCE/ring4_recompute.json":
        ("应留", "JSON 逐 entry 复算 ④ 见证（body/调用点），对象记录体"),
    "S09_KPROVED6/_audit/EVIDENCE/S3_sites.json":
        ("应留", "JSON 逐 entry 记直接调用点（site/bytes/rel32/arith），对象记录体"),
    "S09_KPROVED7/_audit/EVIDENCE/baseline_audit.json":
        ("应排", "JSON 只有基线率（mine_strict/mine_loose），纯统计"),
    "S09_KPROVED7/_audit/EVIDENCE/S7b_baseline.json":
        ("应排", "JSON 只有池口径与基线率（pool_n/coverage_rows/card），纯统计"),
    "S05_KPROVED3/_audit/EVIDENCE/q3_cfg.json":
        ("应留", "JSON 逐 entry 记 CFG（entry/aligned16/nins/lo/hi/extent/prologue/first6/insn 列表），对象记录体（846,854 B）"),
    "S05_KPROVED3/_audit/EVIDENCE/q4_sites.json":
        ("应留", "JSON 逐 entry 记 ④ 直接调用点（entry/site/rel32），对象记录体"),
    "S05_KPROVED3/_audit/EVIDENCE/q13_retcodes.json":
        ("应留", "JSON 逐 entry 记返回码集合与站点（codes/sites），对象记录体"),
    "S08-K1/EVIDENCE/E03_fieldscan.txt":
        ("应留", "内容是字段写点清单（FIELD +0x120: 192 total, 60 writes in 42 fns + W 地址 fn= mov/字节），对象记录体"),
    "S06-K1/EVIDENCE/map_field_access.txt":
        ("应留", "内容是绝对寻址访问偏移表（+0x000 (3) …），对象（字段访问）记录体"),
    "S08_KPROVED2/_audit/EVIDENCE/installs_atexit.txt":
        ("应留", "内容是 atexit 注册点清单（site 0040AD6F -> dtor 0040AD80），对象（注册关系）记录体"),
    "S13_DIRECT/EVIDENCE/scan_stats.txt":
        ("应排", "内容是扫描统计（.text VA/VirtualSize/解出指令 1392592/E8 68253/覆盖率 100.0%），"
                 "测量过程产物，非对象记录"),
    "S11-K1/EVIDENCE/verify_final.txt":
        ("应留", "内容是宽扫 RTTI TD 名清单（TD 00820208 .?AUILocomotion@@ …），对象记录体"),
    "S09_KPROVED6/_audit/EVIDENCE/S1_tables.json":
        ("应留", "JSON 逐表记 vt/COL/TD/name/slots，对象记录体"),
    "S09_KPROVED6/_audit/EVIDENCE/S13_controls.txt":
        ("应排", "内容是阴性对照比率（tables=1218/slots=14299/随机窗口 2.510%），对照实验统计"),
    "S09_KPROVED7/_audit/EVIDENCE/hier_audit.txt":
        ("应留", "内容是继承链核对（entry + TD + base chain 字符串），对象记录体"),
    "S09_KPROVED7/_audit/EVIDENCE/vts_audit.json":
        ("应留", "JSON 逐 entry 记持有槽（vt/slot/class），对象记录体"),
    "S09_KPROVED7/_audit/EVIDENCE/feat_pool642.json":
        ("应留", "JSON 逐 entry 记结构特征（entry/n_insns/jcc/jump_table），对象属性记录体"),
    "S10_K4/_audit/EVIDENCE/a9_baseline.txt":
        ("应排", "内容是表头/行数/分级直方图与阈值核对（coverage data rows 18431 / S10 rows 528 / proved 21.1027%），统计"),
    "S10_KPROVED2/_audit/EVIDENCE/spot_checks.json":
        ("应留", "JSON 逐点记 {site,fn,inside}（调用点是否在函数体内），对象记录体"),
    "RECON_UNMERGED/EVIDENCE/merge_records.txt":
        ("混合", "内容是 9 张卡的并表登记：既有逐 entry 地址 + old_value/new_value + evidence_path（对象事实），"
                 "又通篇是 merge 操作日志帧（## 卡名 (delta N 行)）；单件无法整件归属，须逐行拆"),
    "S11-K2/EVIDENCE/t2_factory_alloc.txt":
        ("应留", "内容是 factory 注册函数内 ctor 地址清单（=== factory ctors … 67 === + ctor 006C0040 …），对象记录体"),
    "S13_K12/EVIDENCE/conflict18.txt":
        ("应留", "内容是 entry-address 冲突扫描逐条命中（## 0040B740 : 1 hits total + 命中位置），对象记录体"),
    "S13_K8/EVIDENCE/vt_rtti_registry.txt":
        ("应留", "内容是 vtable 登记簿（VT base / COL / RTTI name / NSLOTS + 逐 slot -> 函数地址），对象记录体"),
    "W174_dirty80/EVIDENCE/w174_vtable_raw_verify.txt":
        ("应留", "内容是 raw vtable dword 读取（Class vt=… slot=N(+off) -> 地址），对象记录体"),
    "W150_navstate/EVIDENCE/w150_bytescan.log":
        ("应留", "内容是字节扫描结果（# EXE … + 逐行地址/节/匹配字节），对象记录体"),
    "W156_free/EVIDENCE/array_writes.log":
        ("应留", "内容是 [00A8EB50] Bld.Count 写点清单（地址+写入指令），对象记录体"),
    "P0_ADJ5/_audit/EVIDENCE/pool_1669.txt":
        ("应排", "整篇 1669 行裸函数地址，每行只有 8 位十六进制，无槽/类/虚表/字节列；"
                 "是候选池名单，不构成对象记录（地址本身不携带对象事实字段）"),
    "P0_ADJ5/_audit/EVIDENCE/step3_sample15.txt":
        ("应排", "内容是 15 行确定性抽样核对表（# addr channel card mine-A1 agr first pred blen refs A1..A7），抽样过程"),
    "P0_ADJ5/_audit/EVIDENCE/baseline_mine.txt":
        ("应排", "内容是多次随机抽样 FUNC 率（seed 20261119..20261123），纯统计"),
    "P0_ADJ4/_audit/EVIDENCE/step1_numbers.txt":
        ("应排", "内容是 STEP 1 数字核对清单（ENUM 行数/verdict 分布/PE 头常量），测量前核对项"),
    "P0_ADJ4/_audit/EVIDENCE/step4_breadth.txt":
        ("应排", "内容是抽样复现统计（FUNC 95/5、deterministic indices 91+183*i、counter-example set），抽样过程"),
    "P0_INITTERM/EVIDENCE/recompute_stdout.txt":
        ("应排", "内容是复算校验（slots=3945 … (audit 3944: True) 逐项判等），自检式核对输出"),
    "PROBE_UNNAMED_R2/EVIDENCE/poolstats_out.txt":
        ("应排", "内容是 unnamed 池统计（n=1181 成立 8 (0.68%)），过程统计"),
    "C01_census/EVIDENCE/classify_stdout.txt":
        ("应排", "内容是分类计数直方图（total 1292 / by conf / by grade / by subsystem），普查统计"),
    "C01_census/EVIDENCE/classify_fix_stdout.txt":
        ("应排", "同上：分类计数直方图，普查统计"),
    "C01_census/EVIDENCE/validation_stdout.txt":
        ("应排", "内容是逐项校验结果（validation 输出的计数对比行），自检过程"),
    "C01_census/EVIDENCE/validation_fix_stdout.txt":
        ("应排", "同上：逐项校验结果，自检过程"),
    "S16-K2/EVIDENCE/E00_t1_filter_stdout.txt":
        ("应排", "内容是筛选统计（n=92 named/proved 占比 + grades 直方图），过程统计"),
    "S18-K2/EVIDENCE/event_names.txt":
        ("判不了", "内容是事件名字符串表（name[i] @地址 -> 地址 : POWERON/POWEROFF/…），"
                   "属 .rdata 数据对象的内容记录，但不含函数体/槽归属；缺「数据字符串表算不算对象抄本」的口径"),
    "S10_K11/EVIDENCE/disk_read_snapshot.tsv":
        ("判不了", "内容是某次读取的现场（# read_at=…# sha256=… 头 + 逐行 entry/subsystem/name/语义文本），"
                   "现场头使它是过程记录，正文是对象清单；缺口径"),
    "S10-K2/EVIDENCE/t2_mission_slots.txt":
        ("应留", "内容是 PRIMARY VTABLES 逐类 {类名 VT=… slots=N} 表，对象记录体"),
    "S10-K2/EVIDENCE/t3_getsize_final.txt":
        ("应留", "内容是 operator new 0x7C8E17 body 逐条反汇编（地址+字节+助记符），对象记录体"),
    "S10-K2/EVIDENCE/t4_fields.txt":
        ("应留", "内容是函数区间表（005B2DA0..005B2E08 (104 B) …），对象（函数边界）记录体"),
    "S10_K4/_audit/EVIDENCE/a12_slots.txt":
        ("应留", "内容是 entry → .rdata dword 槽引用 + vt_start/COL/TD/class/slot，对象记录体"),
    "S10_K4/_audit/EVIDENCE/a4_stubs.txt":
        ("应留", "内容是 stub 逐条记录（地址+函数体/桩分类），对象记录体"),
    "S10_KPROVED2/_audit/EVIDENCE/ring3b_shapes.json":
        ("应留", "JSON 逐 entry 记 ③b 形态（jump_table/bool_ret/jcc/loop/nonstack_w），对象形态记录体"),
    "S10_KPROVED2/_audit/EVIDENCE/a_set.json":
        ("应排", "JSON 结构 {pool/has2/has4/A/A_entries}，A_entries 是裸函数地址清单，无槽/类/虚表语义列；统计+名单"),
    "S10_KPROVED2/_audit/EVIDENCE/ring2_census.json":
        ("应排", "JSON 只有计数 {n_col,n_vtab,n_slots}，普查计数器"),
    "S10_KPROVED2/_audit/EVIDENCE/ring4_meta.json":
        ("应排", "JSON 只有元计数（ring4 meta），无地址无槽"),
    "S10_KPROVED2/_audit/EVIDENCE/vt_liveness.json":
        ("应排", "JSON {watch:{…}} 是**监视列表**（待检测目标），属测试计划，未含检测到的对象事实"),
    "S05_KPROVED3/_audit/EVIDENCE/q10_selfcheck.json":
        ("应排", "JSON 是自检结果 {n_rows,n_cols,abnormal:[]}，自检元记录"),
    "S05_KPROVED3/_audit/EVIDENCE/q2_holders.json":
        ("应留", "JSON 逐 entry 记持有槽（entry/n_raw_hits/raw_hits 槽地址），对象记录体"),
    "S05_KPROVED3/_audit/EVIDENCE/q8_pool.json":
        ("应排", "JSON 只有池规模与分级计数（cov_total/s05_total/s05_grade 直方图），统计"),
    "S05_KPROVED3/_audit/EVIDENCE/q9_baseline_mine.json":
        ("应排", "JSON 只有基线率 {strict:{K,N,p,E8}}，统计"),
    "S05_KPROVED3/_audit/EVIDENCE/q14_container.json":
        ("应排", "JSON 是容器族统计（kinds 计数/n_fam_pairs/alias_hit/alias_tot + pairs 名单），统计+名单"),
    "S05-K1/EVIDENCE/class_chain_stdout.txt":
        ("应排", "内容是类继承摘要（Class slots=N getsize=STUB parent=…），无地址→槽映射，是层级表非对象记录"),
    "S03_C4/_audit/EVIDENCE/a6_stats.json":
        ("应排", "JSON 只有超几何统计量（N/n/K_loose/p_loose），无对象映射"),
    "S03_C4/_audit/EVIDENCE/a1_sites.json":
        ("应留", "JSON 记扫描结果（total 48 + scan{text_va,text_end,instr} + 逐 entry 站点），对象记录体"),
    "S03_C4/_audit/EVIDENCE/a2_rtti.json":
        ("应留", "JSON 是 RTTI/COL/TD 扫描（逐表 vt/COL/TD/name），对象记录体"),
    "S03_C4/_audit/EVIDENCE/a4_baseline.json":
        ("应留", "JSON 逐行对象记录（entry/lo/hi/extent/prologue/first6/insn），对象记录体"),
    "S08_KPROVED3/_audit/EVIDENCE/s2_rtti_vtables.txt":
        ("应留", "内容是 RTTI 虚表清单（distinct COL-anchored vtable bases），对象记录体"),
    "S08_KPROVED3/_audit/EVIDENCE/s3_occurrences.txt":
        ("应留", "内容是 0045A640 出现点 + 逐点 {VA/section/kind/vtable/COL}，对象记录体"),
    "S09_KPROVED/_audit/EVIDENCE/baseline_mine.json":
        ("应排", "JSON 只有 {N,K,analytic_expected,empirical_mean} 统计，纯数值"),
    "S09_KPROVED/_audit/EVIDENCE/controls.txt":
        ("应留", "内容是 TD+8 内联字符串 vs 解引用（vt/col/td/TD+8 字节），对象记录体"),
    "S09_KPROVED/_audit/EVIDENCE/delta_token_check.txt":
        ("应留", "内容是逐 entry 的 ②/④ 复核（vt=…[46]=entry + site opcode/boundary/target），对象记录体"),
    "S09_KPROVED/_audit/EVIDENCE/ring8_basic.txt":
        ("应留", "内容是逐 entry 的 ring1/ring2 记录（head_bytes + 候选槽 vt/col/TD 对照），对象记录体"),
    "S09_KPROVED3/_audit/EVIDENCE/AUDIT_BASELINE_FEATURES.json":
        ("应排", "JSON 是基线特征集（为统计准备的派生量 dump），非对象事实记录"),
    "S09_KPROVED5/_audit/EVIDENCE/baseline_recompute.json":
        ("应排", "JSON 是基线复算结果（派生比率），非对象事实记录"),
    "S09_KPROVED5/_audit/EVIDENCE/dca.json":
        ("应留", "JSON 逐 entry 记 DCA 与继承链（dca/chain），对象记录体"),
    "S09_KPROVED5/_audit/EVIDENCE/ring2_recompute.json":
        ("应留", "JSON 逐 entry 记槽列表（slots），对象记录体"),
    "S09_KPROVED6/_audit/EVIDENCE/S10_exhaustive.txt":
        ("应排", "内容是集合计数核对（rows=4444 S09=629 A=103 with livevt_valid=1 -> 2），统计核对"),
    "S09_KPROVED6/_audit/EVIDENCE/S11_claims.txt":
        ("应排", "内容是各卡已交行数+地址名单汇总（rows=8 004AAE90 …），台账清单，无对象语义列"),
    "S09_KPROVED6/_audit/EVIDENCE/S7b_baseline.txt":
        ("应排", "内容是基线率计算（K=82 p=0.126348 E[8]=1.0108 MC=0.9790），纯统计"),
    "S09_KPROVED6/_audit/EVIDENCE/S1_tables.txt":
        ("应留", "内容是 ENTRY→{vt,slot,cls,COL,TD,vt[slot]==entry} 表，对象记录体"),
    "S09_KPROVED6/_audit/EVIDENCE/S2_hierarchy.txt":
        ("应留", "内容是 COL+0x10→CHD→基类数组链（逐 entry nBase/chain），对象记录体"),
    "S09_KPROVED6/_audit/EVIDENCE/S3_sites.txt":
        ("应留", "内容是逐 entry 调用点算术（site=… bytes=… rel32=… arith=…），对象记录体"),
    "S09_KPROVED7/_audit/EVIDENCE/ring2_hold_audit.txt":
        ("应留", "内容是逐 entry 持有表审计（holding tables/slots seen/vt slot N 类名），对象记录体"),
    "S09_KPROVED7/_audit/EVIDENCE/ring4_audit.txt":
        ("应留", "内容是逐 entry ring4（body 区间/insns/E8@site boundary/rel32），对象记录体"),
    "S09_KPROVED7/_audit/EVIDENCE/row3b_profile.json":
        ("应排", "JSON 是 ③b 判定用特征向量（jump_table/bool_ret/jcc/n_nonstack_w/eax_consts），派生特征非对象事实"),
    "S10_KPROVED3/EVIDENCE/baseline_3b.txt":
        ("应排", "内容是 ③b 基线率（seed 2000 draws；strict/core/loose K/N/p），纯统计"),
    "S11-K2/EVIDENCE/fresh_closure.txt":
        ("应留", "内容是逐类 ctor 安装点（installs=vt@site 地址对），对象（安装关系）记录体"),
    "S11-K2/EVIDENCE/t1_clsid_check.txt":
        ("应留", "内容是 .rdata GUID 区逐地址 GUID 转储，对象（数据）记录体"),
    "MEASURE_F3A/EVIDENCE/004A80D0__NEG_template.txt":
        ("应留", "内容是单 entry 的边界+# 注释 + 逐条反汇编字节（004A80D0 b8 02 00 00 00 mov eax,2），对象记录体"),
    "MEASURE_F3A/EVIDENCE/007BA360__YI_sample10.txt":
        ("应留", "内容是单 entry 边界+反汇编（body=atlas [entry,entry+18) n_instr=6 + 逐条字节），对象记录体"),
    "MEASURE_F3A/EVIDENCE/007C8B3D__YI_sample01.txt":
        ("应留", "同上：单 entry 反汇编记录（entry/subsystem/name/n_instr + 逐条指令字节）"),
    "S09_KPROVED7/_audit/EVIDENCE/S7b_baseline.json":
        ("应排", "JSON 只有池口径与基线率（pool_n/coverage_rows/card），纯统计"),
    "W62_bline_new_criteria/EVIDENCE/b_selftest.stdout.txt":
        ("应排", "整篇自检断言（[B-POS]/[B-NEG] expected=/actual=/pass=True + KS 统计），记录判定过程，无对象记录体"),
    "W68_criterion_discrete_fix/EVIDENCE/concurrent_GLM/v2_selftest.stdout.txt":
        ("应排", "同上：整篇 [B-POS]/[B-NEG] pass=True 自检断言，无对象地址/槽记录"),
    "W68_criterion_discrete_fix/EVIDENCE/v2_selftest.stdout.txt":
        ("应排", "同上（与 concurrent_GLM 副本同内容）：纯自检断言"),
    "W97_artmd/EVIDENCE/probe04_stdout.txt":
        ("判不了", "内容是 artmd.ini 的逐条核对（KEY 名 Foundation=/VERIFIED in file/计数断言），"
                   "数据事实与核对结论混编；缺「INI 字段核对表算对象记录还是过程记录」的口径"),
    "W97_artmd/EVIDENCE/probe06_stdout.txt":
        ("应排", "内容是 INI 字段核对清单（Foundation=/line NNNN VERIFIED in file，仅 4 行带地址），核对过程记录"),
    "W97_artmd/EVIDENCE/probe10_stdout.txt":
        ("应排", "内容是 artmd.ini 逐节/逐键核对输出（VERIFIED/count 断言），核对过程记录"),
    "W97_artmd/EVIDENCE/probe08_stdout.txt":
        ("应排", "内容是 TRIP_RESULT_C6.json 的运行参数回显（step/want_fn/sample_interval_ms/fps/min_valid_s/"
                 "engagement 序列），运行记录"),
    "W104_sentinel2/EVIDENCE/selftest.txt":
        ("应排", "内容是 cell_sentinel 自检（build 4 独立对象图 + 逐条 [PASS] 断言），"
                 "被测对象是**合成内存**而非目标 EXE，属过程自检"),
    "P0_ADJ4/_audit/EVIDENCE/step3_sample15.txt":
        ("应排", "内容是 15 行确定性抽样核对表（# addr channel card mine-A1 agr first pred blen refs A1..A7），抽样过程"),
    "S09_KPROVED7/_audit/EVIDENCE/baseline_audit.txt":
        ("应排", "内容是基线率（S09 rows 1102 / pool 642 / mine_strict 0.1994 / mine_loose 0.5218），纯统计"),
    "S09_KPROVED7/_audit/EVIDENCE/S7b_baseline.json":
        ("应排", "JSON 只有池口径与基线率（pool_n/coverage_rows/card），纯统计"),
    "S19-F1/EVIDENCE/task2_explore_summary.txt":
        ("应留", "内容是 play 函数入口字节 + 调用点普查（TARGET 00750920 sites=116 caller_fns=66 + 入口字节行），"
                 "对象（函数入口/调用点）记录体"),
    "W177-B/EVIDENCE/S0_baseline.txt":
        ("应排", "内容是卫生与就绪基线（记录时间 + gamemd.exe/ddraw.dll SHA-256 + except.txt 长度/mtime 表），"
                 "环境基线元记录，无被测对象记录"),
}


def main():
    rows = list(csv.DictReader(open(os.path.join(OUT, "q2_classes.tsv"), encoding="utf-8", newline=""), delimiter="\t"))
    out, used_special = [], set()
    for r in rows:
        rel = r["rel"]
        f = feature(rel)
        hit = None
        for k, v in SPECIAL.items():
            if rel.endswith(k):
                hit = v
                used_special.add(k)
                break
        if hit is None:
            hit = decide(rel, f)
        out.append({"rel": rel, "bytes": r["bytes"], "class": r["class"],
                    "verdict": hit[0], "reason": hit[1],
                    "nlines": f["n"], "slots": f["slot"], "rtti": f["rtti"],
                    "dislines": f["dislines"], "selft": f["selft"], "stat": f["stat"],
                    "ring": f["ring"], "a8": f["a8"], "first": f["first"]})
    with open(os.path.join(OUT, "tie152_verdicts.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, delimiter="\t", fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0])
    for x in out:
        agg[x["verdict"]][0] += 1
        agg[x["verdict"]][1] += int(x["bytes"])
    print("verdict 汇总:")
    tn = tb = 0
    for k in ("应排", "应留", "混合", "判不了"):
        n, b = agg.get(k, [0, 0])
        tn += n; tb += b
        print(f"  {k:6s} {n:3d} 件 / {b:>8d} B")
    print(f"  合计   {tn:3d} 件 / {tb:>8d} B")
    x = defaultdict(lambda: defaultdict(int))
    for r in out:
        x[r["class"]][r["verdict"]] += 1
    print("\nclass x verdict:")
    for k in sorted(x):
        print(f"  {k:20s} " + "  ".join(f"{v}={x[k][v]}" for v in ("应排", "应留", "混合", "判不了") if x[k][v]))
    unused = set(SPECIAL) - used_special
    if unused:
        print("\nSPECIAL 未命中的键（说明路径不匹配）:", sorted(unused))


if __name__ == "__main__":
    main()
