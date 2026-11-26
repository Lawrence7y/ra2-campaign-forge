#!/usr/bin/env python3
"""R140-F01-RTTI-BLIND: independent byte-level RTTI counter blind recomputation."""
import hashlib
import json
import re
import signal
import struct
import sys
import time
from collections import Counter
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "ra2bench" / "gamemd.exe"
OUT_DIR = ROOT / "_r140" / "sub"
JSON_PATH = OUT_DIR / "REPORT_F01_BLIND.json"
REPORT_PATH = OUT_DIR / "REPORT_F01_BLIND.md"
SCRIPT_REL = "_r140/sub/r140_f01_blind.py"
CMD_ONE = "timeout 300s python3 " + SCRIPT_REL
INTERNAL_TIMEOUT_S = 280
EXTERNAL_TIMEOUT_S = 300

T0 = time.monotonic()
_op_count = 0


def check_deadline():
    global _op_count
    _op_count += 1
    if (_op_count & 0xFFFF) == 0 and time.monotonic() - T0 > INTERNAL_TIMEOUT_S:
        raise TimeoutError("internal timeout after %ds" % INTERNAL_TIMEOUT_S)


def _alarm(signum, frame):
    raise TimeoutError("SIGALRM timeout after %ds" % (INTERNAL_TIMEOUT_S + 10))


signal.signal(signal.SIGALRM, _alarm)
signal.alarm(INTERNAL_TIMEOUT_S + 10)


def hx(v):
    return None if v is None else hex(v)


def main():
    res = {
        "task": "R140-F01-RTTI-BLIND",
        "script_rel": SCRIPT_REL,
        "one_command": CMD_ONE,
        "target_rel": "ra2bench/gamemd.exe",
        "internal_timeout_seconds": INTERNAL_TIMEOUT_S,
        "external_timeout_seconds": EXTERNAL_TIMEOUT_S,
        "timed_out": False,
        "unmeasured_note": "",
    }

    try:
        raw = TARGET.read_bytes()
        res["file_size"] = len(raw)
        res["file_sha256"] = hashlib.sha256(raw).hexdigest()

        pe = pefile.PE(data=raw, fast_load=True)
        image_base = int(pe.OPTIONAL_HEADER.ImageBase)
        res["image_base"] = hx(image_base)
        res["pefile_version"] = getattr(pefile, "__version__", "unknown")

        sections = []
        for s in pe.sections:
            name = s.Name.rstrip(b"\x00").decode("ascii", "replace")
            if name in (".data", ".rdata"):
                sections.append({
                    "name": name,
                    "rva": int(s.VirtualAddress),
                    "virtual_size": int(s.Misc_VirtualSize),
                    "raw_size": int(s.SizeOfRawData),
                    "ptr": int(s.PointerToRawData),
                    "end": int(s.PointerToRawData) + int(s.SizeOfRawData),
                })
        res["sections"] = sections
        res["rva_range_basis"] = "Misc_VirtualSize (virtual RVA extent)"
        res["alignment_basis"] = "file offset aligned to 4 (.data/.rdata PointerToRawData are 4-aligned)"

        def sec_for_off(off):
            for s in sections:
                if s["ptr"] <= off < s["end"]:
                    return s
            return None

        def u32(off):
            if off is None or off < 0:
                return None
            s = sec_for_off(off)
            if s is None or off + 4 > s["end"]:
                return None
            return struct.unpack_from("<I", raw, off)[0]

        def off_va_in(s, off):
            # allow off == end so a vt beginning exactly at raw end still has a VA
            if s["ptr"] <= off <= s["end"]:
                return image_base + s["rva"] + (off - s["ptr"])
            return None

        def rva_in_data(rva):
            return any(s["rva"] <= rva < s["rva"] + s["virtual_size"] for s in sections)

        def aligned_positions(s):
            start = s["ptr"]
            if start % 4:
                start = ((start + 3) // 4) * 4
            for off in range(start, s["end"] - 3, 4):
                yield off

        # ---------------- A1 ----------------
        # MSVC x86 RTTI TypeDescriptor layout:
        #   [S-8] = pVFTable (absolute VA, not an RVA), [S-4] = spare(0), [S..] = ".?AV/.?AU name@@"
        # A1 card rule:
        #   "dword[S-8] 是否落在 .data/.rdata 的 RVA 范围内" is tested as VA(S)-8 (RVA of TD),
        #   to avoid hard-coding the absolute-VA interpretation. We record both results.
        printable = re.compile(rb"[ -~]+")
        string_records = []
        td_records = []
        td_records_alt = []
        for s in sections:
            chunk = raw[s["ptr"]:s["end"]]
            for m in printable.finditer(chunk):
                check_deadline()
                run = m.group()
                if len(run) < 7:
                    continue
                prefix = b".?AV" if run.startswith(b".?AV") else (b".?AU" if run.startswith(b".?AU") else None)
                if prefix is None or not run.endswith(b"@@"):
                    continue
                str_off = s["ptr"] + m.start()
                name = run[len(prefix):-2].decode("ascii", "replace")
                rec = {
                    "string_off": str_off,
                    "string_va": off_va_in(s, str_off),
                    "prefix": prefix.decode("ascii"),
                    "name": name,
                    "string_len": len(run),
                }
                string_records.append(rec)
                p = str_off - 8
                if p < s["ptr"] or p + 4 > s["end"]:
                    continue
                vf = u32(p)
                spare = u32(str_off - 4)
                if vf is None:
                    continue
                td_va = off_va_in(s, p)
                td_rva = td_va - image_base
                base = {
                    "td_off": p,
                    "td_va": td_va,
                    "td_rva": td_rva,
                    "vf_dword": vf,
                    "spare": spare,
                    "name": name,
                    "prefix": rec["prefix"],
                    "section": s["name"],
                }
                if spare == 0 and rva_in_data(td_rva):
                    td_records.append(dict(base, vf_interpretation="td_rva_in_range"))
                if spare == 0 and rva_in_data(vf):
                    td_records_alt.append(dict(base, vf_interpretation="vf_dword_is_rva_in_range"))

        td_by_va = {}
        td_duplicate_va = 0
        for t in td_records:
            if t["td_va"] in td_by_va:
                td_duplicate_va += 1
            else:
                td_by_va[t["td_va"]] = t

        td_by_va_alt = {}
        for t in td_records_alt:
            if t["td_va"] not in td_by_va_alt:
                td_by_va_alt[t["td_va"]] = t

        a1 = {
            "string_total": len(string_records),
            "dot_AV_count": sum(r["prefix"] == ".?AV" for r in string_records),
            "dot_AU_count": sum(r["prefix"] == ".?AU" for r in string_records),
            "td_count": len(td_records),
            "td_distinct_va_count": len(td_by_va),
            "td_duplicate_va_hits": td_duplicate_va,
            "td_count_alt_vf_as_rva": len(td_records_alt),
            "td_distinct_va_count_alt_vf_as_rva": len(td_by_va_alt),
            "td_check_rule": "dword[S-8] 值按 RVA 检验落在 .data/.rdata RVA 范围 AND dword[S-4]==0; TD VA=VA(S)-8",
            "td_check_rule_alt": "MSVC 标准: dword[S-8] 是绝对 VA，换算成 RVA 后落在 .data/.rdata RVA 范围 AND dword[S-4]==0; TD VA=VA(S)-8",
        }
        res["A1"] = a1

        # ---------------- A2 ----------------
        # Primary: MSVC standard absolute-VA interpretation (VF pointer is an absolute VA).
        # Alt: strict card-literal interpretation (VF pointer value is an RVA), preserved for comparison.
        def compute_cols(td_map):
            td_va_set = set(td_map)
            td_ptr_ref_total = 0
            col_pass_records = []
            reject_plus0_nonzero = 0
            reject_v12_mismatch = 0
            reject_unreadable = 0
            for s in sections:
                for off in aligned_positions(s):
                    check_deadline()
                    val = u32(off)
                    if val is None or val not in td_va_set:
                        continue
                    td_ptr_ref_total += 1
                    c = off - 12
                    v0 = u32(c)
                    v12 = u32(c + 12)
                    if v0 is None or v12 is None:
                        reject_unreadable += 1
                        continue
                    if v0 != 0:
                        reject_plus0_nonzero += 1
                    if v12 != val:
                        reject_v12_mismatch += 1
                    if v0 == 0 and v12 == val:
                        col_pass_records.append({
                            "col_off": c,
                            "col_va": off_va_in(s, c),
                            "td_va": val,
                            "name": td_map[val]["name"],
                            "section": s["name"],
                        })
            by_va = {}
            duplicate = 0
            for c in col_pass_records:
                if c["col_va"] in by_va:
                    duplicate += 1
                else:
                    by_va[c["col_va"]] = c
            out = list(by_va.values())
            for c in out:
                c["dword4"] = u32(c["col_off"] + 4)
            return {
                "td_pointer_reference_total": td_ptr_ref_total,
                "col_pass_count": len(col_pass_records),
                "col_distinct_count": len(out),
                "rejected_by_dword_plus0_nonzero": reject_plus0_nonzero,
                "rejected_by_v12_mismatch": reject_v12_mismatch,
                "rejected_by_unreadable": reject_unreadable,
                "duplicate_col_va_hits": duplicate,
                "col_check_rule": "dword[COL+0]==0 AND dword[COL+12]==TD VA; COL=ptr_offset-12",
            }, out

        a2, cols = compute_cols(td_by_va)
        a2_alt, cols_alt = compute_cols(td_by_va_alt)
        res["A2"] = a2
        res["A2_alt_vf_as_rva"] = a2_alt

        # ---------------- A3 ----------------
        # A3: 若 dword[P] == COL VA，则候选虚表首函数指针在 P，虚表起点 vt=P+4；
        # 检验 dword[vt-4]==COL VA 即 dword[P]==COL VA（每引用必过，不额外计）。
        col_va_set = {c["col_va"] for c in cols}
        vt_ref_total = 0
        vt_dedup = set()
        cols_with_vt = set()
        vt_back_mismatch = 0
        for s in sections:
            for off in aligned_positions(s):
                check_deadline()
                val = u32(off)
                if val is None or val not in col_va_set:
                    continue
                back = u32(off)  # vt-4 == off, checked against COL VA
                if back == val:
                    vt_ref_total += 1
                    vt_va = off_va_in(s, off + 4)
                    if vt_va is not None:
                        vt_dedup.add(vt_va)
                    cols_with_vt.add(val)
                else:
                    vt_back_mismatch += 1

        no_vt_cols = [
            {"col_va": hx(c["col_va"]), "name": c["name"]}
            for c in cols if c["col_va"] not in cols_with_vt
        ]
        a3 = {
            "vtable_reference_count": vt_ref_total,
            "vtable_distinct_count": len(vt_dedup),
            "distinct_cols_pointed_back_by_vt": len(cols_with_vt),
            "cols_without_vt_count": len(no_vt_cols),
            "cols_without_vt": no_vt_cols,
            "vt_back_mismatch_count": vt_back_mismatch,
        }
        res["A3"] = a3

        # ---------------- A4 ----------------
        td_col_targets = {c["td_va"] for c in cols}
        td_no_col_va = sorted(set(td_by_va) - td_col_targets)
        td_no_col_list = [
            {"td_va": hx(v), "name": td_by_va[v]["name"]} for v in td_no_col_va
        ]

        def family_of(name):
            if name.endswith("LocomotionClass") or name.endswith("Locomotion"):
                return "Locomotion"
            if name.endswith("TypeClass"):
                return "TypeClass"
            return "Other"

        fam = {}
        for c in cols:
            f = family_of(c["name"])
            d = fam.setdefault(f, {"col_count": 0, "names": set()})
            d["col_count"] += 1
            d["names"].add(c["name"])
        fam_out = {}
        for f in ("Locomotion", "TypeClass", "Other"):
            d = fam.get(f, {"col_count": 0, "names": set()})
            fam_out[f] = {
                "col_count": d["col_count"],
                "distinct_class_count": len(d["names"]),
                "sample_names": sorted(d["names"])[:8],
            }

        a4 = {
            "mdisp_zero_col_count": sum(c["dword4"] == 0 for c in cols),
            "td_without_col_count": len(td_no_col_va),
            "td_without_col": td_no_col_list,
            "family_rule": "name ending LocomotionClass/Locomotion -> Locomotion; ending TypeClass -> TypeClass; else Other",
            "families": fam_out,
        }
        res["A4"] = a4

        # ---------------- A5 ----------------
        filtered = [c for c in cols if c["dword4"] is not None and c["dword4"] <= 0x1000]
        filtered_details = [
            {
                "col_va": hx(c["col_va"]),
                "dword4": hx(c["dword4"]),
                "name": c["name"],
                "pointed_back_by_vt": c["col_va"] in cols_with_vt,
            }
            for c in filtered
        ]
        hist = Counter(c["dword4"] for c in cols if c["dword4"] is not None)
        hist_hex = {hx(k): v for k, v in sorted(hist.items())}
        a5 = {
            "le_0x1000_col_count": len(filtered),
            "le_0x1000_and_vt_back_count": sum(c["col_va"] in cols_with_vt for c in filtered),
            "le_0x1000_col_list": filtered_details,
            "dword4_unreadable_col_count": sum(c["dword4"] is None for c in cols),
            "dword4_histogram_hex": hist_hex,
            "dword4_distinct_value_count": len(hist),
        }
        res["A5"] = a5

        res["unmeasured_note"] = (
            "我没能测到的数：.data/.rdata 虚拟尾部超出 SizeOfRawData 的部分，以及 .text/.rsrc/.detour "
            "中的潜在 RTTI 引用；原因是本卡限定只读 .data/.rdata 的落盘字节，虚拟尾部读不到且不得当 0。"
            "另外，A1 字面写的是『dword[S-8] 落在 .data/.rdata 的 RVA 范围内』，而 MSVC x86 标准中该 "
            "dword 是绝对 VA；为避免猜主会话口径，我两套都实跑并在报告中同时列出，A1『通过检验的 TD 数』"
            "以字面口径为准，A2..A5 以绝对 VA 口径为准。A1..A5 指定口径内无未测项。"
        )
    except TimeoutError as exc:
        res["timed_out"] = True
        res["error"] = str(exc)
        res["unmeasured_note"] = (
            "我没能测到的数：因内部 timeout 中断，A1..A5 后续项未完成；原因是 %s。" % exc
        )

    signal.alarm(0)
    res["elapsed_seconds"] = round(time.monotonic() - T0, 3)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(res, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    JSON_PATH.write_text(json_text, encoding="utf-8")
    json_sha = hashlib.sha256(json_text.encode("utf-8")).hexdigest()
    json_lines = json_text.count("\n") + 1

    def g(section, key, default="N/A"):
        return res.get(section, {}).get(key, default)

    lines = []
    lines.append("# R140-F01-RTTI-BLIND · 独立盲测复算报告")
    lines.append("")
    lines.append("## 运行元数据")
    lines.append("")
    lines.append("| 项目 | 值 |")
    lines.append("|---|---|")
    lines.append("| 脚本路径 | %s |" % SCRIPT_REL)
    lines.append("| 一条命令 | `%s` |" % CMD_ONE)
    lines.append("| 目标文件 | `ra2bench/gamemd.exe` |")
    lines.append("| 文件大小 | %s |" % res.get("file_size", "N/A"))
    lines.append("| sha256 | %s |" % res.get("file_sha256", "N/A"))
    lines.append("| ImageBase | %s |" % res.get("image_base", "N/A"))
    lines.append("| pefile | %s |" % res.get("pefile_version", "N/A"))
    lines.append("| 内部/外部超时 | %ss / %ss |" % (INTERNAL_TIMEOUT_S, EXTERNAL_TIMEOUT_S))
    lines.append("| 是否超时 | %s |" % res.get("timed_out", "N/A"))
    lines.append("| 耗时 | %ss |" % res.get("elapsed_seconds", "N/A"))
    lines.append("| JSON 产物 | `%s` |" % str(JSON_PATH.relative_to(ROOT)))
    lines.append("| JSON sha256 | %s |" % json_sha)
    lines.append("| JSON 行数 | %d |" % json_lines)
    lines.append("| RVA 范围依据 | %s |" % res.get("rva_range_basis", "N/A"))
    lines.append("| 对齐依据 | %s |" % res.get("alignment_basis", "N/A"))
    lines.append("| 节表 | %s |" % "; ".join(
        "%s RVA=%s VS=%s RAW=%s PTR=%s" % (
            s["name"], hx(s["rva"]), hx(s["virtual_size"]), hx(s["raw_size"]), hx(s["ptr"])
        ) for s in res.get("sections", [])
    ))
    lines.append("")

    lines.extend([
        "## A1 · 名字串与 TypeDescriptor", "", "| 项目 | 数值 |", "|---|---:|",
        "| 可打印串总数 | %s |" % g("A1", "string_total"),
        "| .?AV 个数 | %s |" % g("A1", "dot_AV_count"),
        "| .?AU 个数 | %s |" % g("A1", "dot_AU_count"),
        "| 通过检验的 TD 数 | %s |" % g("A1", "td_count"),
        "| 去重 TD VA 数 | %s |" % g("A1", "td_distinct_va_count"),
        "| 重复 TD VA 命中 | %s |" % g("A1", "td_duplicate_va_hits"),
        "| [对照] 字面口径 TD 数（dword[S-8] 当 RVA） | %s |" % g("A1", "td_count_alt_vf_as_rva"),
        "| [对照] 字面口径去重 TD VA 数 | %s |" % g("A1", "td_distinct_va_count_alt_vf_as_rva"),
        "", "A1 规则（主口径）：%s" % g("A1", "td_check_rule", "N/A"),
        "", "A1 规则（字面对照）：%s" % g("A1", "td_check_rule_alt", "N/A"), "",
    ])

    lines.extend([
        "## A2 · COL", "", "| 项目 | 数值 |", "|---|---:|",
        "| TD 指针引用总数 | %s |" % g("A2", "td_pointer_reference_total"),
        "| 通过检验的 COL 数 | %s |" % g("A2", "col_pass_count"),
        "| 去重后 COL 数 | %s |" % g("A2", "col_distinct_count"),
        "| dword[+0] 非零否掉的引用数 | %s |" % g("A2", "rejected_by_dword_plus0_nonzero"),
        "| dword[+12] 不匹配否掉的引用数 | %s |" % g("A2", "rejected_by_v12_mismatch"),
        "| 读不到否掉的引用数 | %s |" % g("A2", "rejected_by_unreadable"),
        "| 重复 COL VA 命中 | %s |" % g("A2", "duplicate_col_va_hits"),
        "", "A2 规则：%s" % g("A2", "col_check_rule", "N/A"), "",
        "### A2 字面对照（dword[S-8] 当 RVA）", "", "| 项目 | 数值 |", "|---|---:|",
        "| TD 指针引用总数 | %s |" % g("A2_alt_vf_as_rva", "td_pointer_reference_total"),
        "| 通过检验的 COL 数 | %s |" % g("A2_alt_vf_as_rva", "col_pass_count"),
        "| 去重后 COL 数 | %s |" % g("A2_alt_vf_as_rva", "col_distinct_count"),
        "| dword[+0] 非零否掉的引用数 | %s |" % g("A2_alt_vf_as_rva", "rejected_by_dword_plus0_nonzero"),
        "| dword[+12] 不匹配否掉的引用数 | %s |" % g("A2_alt_vf_as_rva", "rejected_by_v12_mismatch"),
        "| 读不到否掉的引用数 | %s |" % g("A2_alt_vf_as_rva", "rejected_by_unreadable"),
        "",
    ])

    no_vt = g("A3", "cols_without_vt", [])
    lines.extend([
        "## A3 · 虚表", "", "| 项目 | 数值 |", "|---|---:|",
        "| 虚表引用次数 | %s |" % g("A3", "vtable_reference_count"),
        "| 去重虚表数 | %s |" % g("A3", "vtable_distinct_count"),
        "| 至少一张虚表指回的 distinct COL 数 | %s |" % g("A3", "distinct_cols_pointed_back_by_vt"),
        "| 无虚表指回的 COL 数 | %s |" % g("A3", "cols_without_vt_count"),
        "| 回读不匹配次数 | %s |" % g("A3", "vt_back_mismatch_count"),
        "",
    ])
    if isinstance(no_vt, list) and no_vt:
        lines.extend(["| COL VA | 类名 |", "|---|---|"])
        for item in no_vt:
            lines.append("| %s | %s |" % (item.get("col_va"), item.get("name")))
    lines.append("")

    fam = g("A4", "families", {})
    lines.extend([
        "## A4 · 两个附属数", "", "| 项目 | 数值 |", "|---|---:|",
        "| dword[COL+4]==0 的 COL 数（mdisp 口径） | %s |" % g("A4", "mdisp_zero_col_count"),
        "| 没有任何 COL 指向的 TD 数 | %s |" % g("A4", "td_without_col_count"),
        "", "族规则：%s" % g("A4", "family_rule", "N/A"), "",
        "| 族 | COL 数 | distinct 类数 | 样例类名 |", "|---|---:|---:|---|",
    ])
    if isinstance(fam, dict):
        for f in ("Locomotion", "TypeClass", "Other"):
            d = fam.get(f, {})
            lines.append("| %s | %s | %s | %s |" % (
                f, d.get("col_count", "N/A"), d.get("distinct_class_count", "N/A"),
                ", ".join(d.get("sample_names", [])) or "-"
            ))
    lines.append("")

    filtered = g("A5", "le_0x1000_col_list", [])
    hist = g("A5", "dword4_histogram_hex", {})
    lines.extend([
        "## A5 · 可疑口径检验", "", "| 项目 | 数值 |", "|---|---:|",
        "| dword[COL+4] <= 0x1000 的 COL 数 | %s |" % g("A5", "le_0x1000_col_count"),
        "| 其中被虚表指回的个数 | %s |" % g("A5", "le_0x1000_and_vt_back_count"),
        "| dword[COL+4] 读不到的 COL 数 | %s |" % g("A5", "dword4_unreadable_col_count"),
        "| dword[COL+4] 不同取值数 | %s |" % g("A5", "dword4_distinct_value_count"),
        "", "### A5(2) 被 <=0x1000 口径筛出的 COL", "", "| COL VA | dword[COL+4] | 类名 | 被虚表指回 |", "|---|---|---|---|",
    ])
    if isinstance(filtered, list):
        for item in filtered:
            lines.append("| %s | %s | %s | %s |" % (
                item.get("col_va"), item.get("dword4"), item.get("name"),
                item.get("pointed_back_by_vt")
            ))
    lines.extend(["", "### A5(3) dword[COL+4] 全值直方图", "", "| 取值(hex) | COL 数 |", "|---|---:|"])
    if isinstance(hist, dict):
        for k, v in hist.items():
            lines.append("| %s | %s |" % (k, v))
    lines.append("")

    lines.extend([
        "## 未测项", "",
        str(res.get("unmeasured_note", "N/A")),
        "",
    ])
    report_text = "\n".join(lines)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    report_sha = hashlib.sha256(report_text.encode("utf-8")).hexdigest()
    report_lines = report_text.count("\n") + 1

    # console table
    print("=== R140-F01-RTTI-BLIND CONSOLE TABLE ===")
    print("task=%s sha256=%s size=%s imagebase=%s" % (
        res["task"], res.get("file_sha256", "N/A"), res.get("file_size", "N/A"), res.get("image_base", "N/A")
    ))
    print("A1 strings=%s AV=%s AU=%s TD=%s TD_uniq=%s | alt_TD=%s alt_TD_uniq=%s" % (
        g("A1", "string_total"), g("A1", "dot_AV_count"), g("A1", "dot_AU_count"),
        g("A1", "td_count"), g("A1", "td_distinct_va_count"),
        g("A1", "td_count_alt_vf_as_rva"), g("A1", "td_distinct_va_count_alt_vf_as_rva")
    ))
    print("A2 td_ptr_refs=%s col_pass=%s col_uniq=%s reject_plus0=%s reject_v12=%s reject_unread=%s | alt_col=%s alt_refs=%s" % (
        g("A2", "td_pointer_reference_total"), g("A2", "col_pass_count"), g("A2", "col_distinct_count"),
        g("A2", "rejected_by_dword_plus0_nonzero"), g("A2", "rejected_by_v12_mismatch"),
        g("A2", "rejected_by_unreadable"), g("A2_alt_vf_as_rva", "col_distinct_count"),
        g("A2_alt_vf_as_rva", "td_pointer_reference_total")
    ))
    print("A3 vt_refs=%s vt_uniq=%s cols_with_vt=%s cols_without_vt=%s" % (
        g("A3", "vtable_reference_count"), g("A3", "vtable_distinct_count"),
        g("A3", "distinct_cols_pointed_back_by_vt"), g("A3", "cols_without_vt_count")
    ))
    print("A4 mdisp0=%s td_no_col=%s fam=%s" % (
        g("A4", "mdisp_zero_col_count"), g("A4", "td_without_col_count"),
        {k: (v.get("col_count"), v.get("distinct_class_count")) for k, v in (fam.items() if isinstance(fam, dict) else [])}
    ))
    print("A5 le1000=%s le1000_vt=%s distinct_d4=%s unread_d4=%s" % (
        g("A5", "le_0x1000_col_count"), g("A5", "le_0x1000_and_vt_back_count"),
        g("A5", "dword4_distinct_value_count"), g("A5", "dword4_unreadable_col_count")
    ))
    print("timed_out=%s elapsed=%ss" % (res.get("timed_out"), res.get("elapsed_seconds")))
    print("json=%s sha256=%s lines=%d" % (JSON_PATH, json_sha, json_lines))
    print("report=%s sha256=%s lines=%d" % (REPORT_PATH, report_sha, report_lines))
    print("=== JSON BEGIN ===")
    print(json_text)
    print("=== JSON END ===")


if __name__ == "__main__":
    main()
