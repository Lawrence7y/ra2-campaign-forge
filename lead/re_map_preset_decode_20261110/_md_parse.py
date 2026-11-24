# -*- coding: utf-8 -*-
"""_md_parse.py -- RA2/YR 地图预置单位表逐槽位解析（只读磁盘，不碰游戏/进程）。

输入三份只读地图：
  A scratch/boot_probe/arm_a/XMP29U2.MAP          (311,822 B)
  B ra2bench/[2]0LoadBench_U0400.yrm              (92,332 B)
  C out/loadbench/[2]0LoadBench_U0400.yrm         (25,604 B)

产出：
  lead/re_map_preset_decode_20261110/_md_parse_out.txt
  lead/re_map_preset_decode_20261110/_md_parse_out.json
"""
import sys

sys.dont_write_bytecode = True  # 本目录不落 __pycache__

import hashlib
import json
import os
import re
from collections import Counter, OrderedDict

ROOT = r"D:\Project\ra2-campaign-forge"
FILES = OrderedDict([
    ("A_XMP29U2_MAP", os.path.join(ROOT, "scratch", "boot_probe", "arm_a", "XMP29U2.MAP")),
    ("B_ra2bench_yrm", os.path.join(ROOT, "ra2bench", "[2]0LoadBench_U0400.yrm")),
    ("C_out_loadbench_yrm", os.path.join(ROOT, "out", "loadbench", "[2]0LoadBench_U0400.yrm")),
])
OUT_DIR = os.path.join(ROOT, "lead", "re_map_preset_decode_20261110")

# RA2/YR 预置对象小节（本任务关注前三类；Aircraft 一并探查以防遗漏）
PRESET_SECTIONS = ["Units", "Infantry", "Structures", "Aircraft"]

INI_HEADER = re.compile(r"^\s*\[([^\[\]]+)\]\s*$")
EKV = re.compile(r"^\s*([^=]+?)\s*=\s*(.*?)\s*$")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def line_ending_analysis(data):
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    return {"CRLF": crlf, "LF_only": lf}


def try_decode(data):
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace"), "latin-1?replace"


def parse_ini(text):
    """把 INI 文本切成 OrderedDict[section -> list[(key, raw_value)]]。
    保留：小节顺序、小节内行序、重复 key（如 PreviewPack 1=,2=）、无值行。
    注释行（;开头）与小节外的散行分别归入 _comments / _orphan。"""
    doc = OrderedDict()
    order = []
    cur = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        m = INI_HEADER.match(line)
        if m:
            cur = m.group(1)
            if cur not in doc:
                doc[cur] = []
                order.append(cur)
            doc[cur].append(("_section_line@", lineno))  # 记小节起始行
            continue
        m = EKV.match(line)
        if m and cur is not None:
            doc[cur].append((m.group(1), m.group(2)))
        elif cur is not None:
            doc[cur].append(("<non-kv>", line))
        else:
            doc.setdefault("_orphan", []).append((str(lineno), line))
    return doc, order


def entry_owner_type(entries):
    """把小节条目解析为 (id, owner, type)。行形如 `ID=Owner,Type,CellX,CellY,...`。
    假设 0 号字段=owner、1 号字段=type——三份文件观察一致（.MAP 与两份 .yrm
    的 Structures 均为 Neutral/X、Units 均为 屋名/型号）。返回解析失败行清单。"""
    out, bad = [], []
    for key, val in entries:
        if key.startswith("_") or key == "<non-kv>":
            continue
        parts = val.split(",")
        if len(parts) < 2:
            bad.append((key, val))
            continue
        out.append((key, parts[0], parts[1]))
    return out, bad


def analyze(path):
    data = read_bytes(path)
    text, enc = try_decode(data)
    doc, order = parse_ini(text)
    res = OrderedDict()
    res["path"] = os.path.relpath(path, ROOT).replace("\\", "/")
    res["size_bytes"] = len(data)
    res["sha256_16"] = sha256_of(path)[:16]
    res["sha256_full"] = sha256_of(path)
    res["line_endings"] = line_ending_analysis(data)
    res["decode_encoding"] = enc
    res["n_sections"] = len(order)
    res["section_order"] = order
    res["first_line"] = text.splitlines()[0] if text else ""
    # 容器判读特征
    res["has_ini_sections"] = bool(order)
    res["has_previewpack"] = "PreviewPack" in doc
    res["has_isomappack5"] = "IsoMapPack5" in doc
    res["has_digest"] = "Digest" in doc
    res["fa2_header_comment"] = text.lstrip().startswith("; Map created with FinalAlert")
    # 预置小节
    res["preset_sections_present"] = [s for s in PRESET_SECTIONS if s in doc]
    res["preset_sections_absent"] = [s for s in PRESET_SECTIONS if s not in doc]
    stats = {}
    for sec in PRESET_SECTIONS:
        if sec not in doc:
            stats[sec] = {"present": False, "entries": 0}
            continue
        rows, bad = entry_owner_type(doc[sec])
        owner_counts = Counter()
        owner_types = {}
        for _id, owner, typ in rows:
            owner_counts[owner] += 1
            owner_types.setdefault(owner, Counter())[typ] += 1
        stats[sec] = {
            "present": True,
            "entries": len(rows),
            "unparsed": bad,
            "owner_counts": OrderedDict(sorted(owner_counts.items(), key=lambda kv: -kv[1])),
            "owner_types": {o: dict(c.most_common()) for o, c in owner_types.items()},
        }
    res["presets"] = stats
    # 元信息
    for probe in ("Basic", "Header", "Map", "Houses"):
        if probe in doc:
            kv = {}
            for k, v in doc[probe]:
                if not k.startswith("_") and k != "<non-kv>":
                    kv[k] = v
            res["meta_" + probe] = kv
    # Special 屋车辆/步兵预置（判据 240/120 的直接核对项）
    special = {}
    for sec in ("Units", "Infantry"):
        if sec in stats and stats[sec].get("present"):
            special[sec] = stats[sec]["owner_types"].get("Special", {})
    res["special_house_presets"] = special
    # 打包段/辅助段规模（判"富/简版"用）
    pack_keys = ("PreviewPack", "IsoMapPack5", "OverlayPack", "OverlayDataPack",
                 "Terrain", "Smudge")
    res["pack_entry_counts"] = {
        k: sum(1 for kk, _v in doc[k] if not kk.startswith("_") and kk != "<non-kv>")
        for k in pack_keys if k in doc}
    res["aux_sections"] = {
        k: len(doc[k]) for k in ("Triggers", "Tags", "Actions", "Events",
                                 "AITriggerTypesEnable", "Ranking") if k in doc}
    return res


def family_scan():
    """LoadBench 家族出处扫描：所有同名族 yrm 的预置规模（只读）。"""
    import glob
    rows = []
    pats = [
        os.path.join(ROOT, "out", "loadbench", "*0LoadBench_*.yrm"),
        os.path.join(ROOT, "out", "loadbench", "pristine", "*", "*0LoadBench_*.yrm"),
        os.path.join(ROOT, "ra2bench", "*0LoadBench_*.yrm"),
    ]
    seen = set()
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            ap = os.path.abspath(p)
            if ap in seen:
                continue
            seen.add(ap)
            data = read_bytes(p)
            cur = None
            n = Counter()
            for raw in data.decode("utf-8", "replace").splitlines():
                line = raw.strip()
                if not line:
                    continue
                if INI_HEADER.match(line):
                    s = INI_HEADER.match(line).group(1)
                    cur = s if s in ("Units", "Infantry", "Structures") else None
                    continue
                if cur and "=" in line:
                    n[cur] += 1
            rows.append({
                "path": os.path.relpath(p, ROOT).replace("\\", "/"),
                "size_bytes": len(data),
                "sha256_16": hashlib.sha256(data).hexdigest()[:16],
                "Units": n["Units"], "Infantry": n["Infantry"],
                "Structures": n["Structures"],
            })
    return rows


def main():
    results = OrderedDict()
    for tag, path in FILES.items():
        results[tag] = analyze(path)
    family = family_scan()
    # ra2bench yrm 是否为某个家族件的字节复制
    b_sha = results["B_ra2bench_yrm"]["sha256_16"]
    twin = [r["path"] for r in family
            if r["sha256_16"] == b_sha and "ra2bench" not in r["path"]]

    # ---- 两份 .yrm 的结构差集 ----
    b, c = results["B_ra2bench_yrm"], results["C_out_loadbench_yrm"]
    sections_b = set(b["section_order"])
    sections_c = set(c["section_order"])
    diff = {
        "only_in_ra2bench_yrm": sorted(sections_b - sections_c),
        "only_in_out_yrm": sorted(sections_c - sections_b),
    }

    # ---- 汇总判据核对 ----
    a, = [results["A_XMP29U2_MAP"]]
    checks = []
    def add(name, claim, actual, verdict):
        checks.append({"claim": name, "claimed": claim, "actual": actual, "verdict": verdict})

    a_struct = a["presets"]["Structures"]["entries"]
    add("XMP29U2.MAP 建筑=0", 0, a_struct, "符合" if a_struct == 0 else "不符")
    b_struct = b["presets"]["Structures"]["entries"]
    c_struct = c["presets"]["Structures"]["entries"]
    add("yrm 建筑=41", 41, {"ra2bench_yrm": b_struct, "out_yrm": c_struct},
        "ra2bench 符合 / out 不符" if b_struct == 41 and c_struct != 41 else
        ("符合" if b_struct == 41 and c_struct == 41 else "不符"))
    add("XMP29U2.MAP [Units]=3360", 3360, a["presets"]["Units"]["entries"],
        "符合" if a["presets"]["Units"]["entries"] == 3360 else "不符")
    add("XMP29U2.MAP [Infantry]=2240", 2240, a["presets"]["Infantry"]["entries"],
        "符合" if a["presets"]["Infantry"]["entries"] == 2240 else "不符")
    sp_a_u = a["presets"]["Units"]["owner_types"].get("Special", {})
    sp_a_u_total = sum(sp_a_u.values())
    add(".MAP Special 车辆预置=240", 240, sp_a_u_total,
        "符合" if sp_a_u_total == 240 else "不符")
    sp_b_u = b["presets"]["Units"]["owner_types"].get("Special", {})
    sp_c_u = c["presets"]["Units"]["owner_types"].get("Special", {})
    add("yrm Special 车辆预置=120", 120,
        {"ra2bench_yrm": sum(sp_b_u.values()), "out_yrm": sum(sp_c_u.values())},
        ("ra2bench 不符 / out 符合" if sum(sp_c_u.values()) == 120 and sum(sp_b_u.values()) != 120
         else ("符合" if sum(sp_c_u.values()) == 120 and sum(sp_b_u.values()) == 120 else "不符")))
    add("yrm 车辆=1680 / 步兵=1120", {"units": 1680, "infantry": 1120},
        {"ra2bench_yrm": {"units": b["presets"]["Units"]["entries"],
                          "infantry": b["presets"]["Infantry"]["entries"]},
         "out_yrm": {"units": c["presets"]["Units"]["entries"],
                     "infantry": c["presets"]["Infantry"]["entries"]}},
        "两份 yrm 均不符（见正文）")

    summary = {
        "files": {k: {"size": v["size_bytes"], "sha16": v["sha256_16"],
                      "n_sections": v["n_sections"],
                      "preset_entries": {s: v["presets"][s]["entries"]
                                         for s in PRESET_SECTIONS if s in v["presets"]}}
                  for k, v in results.items()},
        "yrm_struct_diff": diff,
        "claim_checks": checks,
    }

    # ---- 文本报告 ----
    lines = []
    w = lines.append
    w("=" * 78)
    w("RA2/YR 地图预置单位表解析  (_md_parse.py)  -- 只读磁盘件，未启动游戏/读进程")
    w("=" * 78)
    for tag, r in results.items():
        w("")
        w("-" * 78)
        w("[%s]  %s" % (tag, r["path"]))
        w("  size=%d B  sha256=%s" % (r["size_bytes"], r["sha256_full"]))
        w("  first_line=%r" % r["first_line"])
        w("  line_endings=%s  encoding=%s" % (r["line_endings"], r["decode_encoding"]))
        w("  sections=%d  order=%s" % (r["n_sections"], ", ".join(r["section_order"])))
        w("  特征: PreviewPack=%s IsoMapPack5=%s Digest=%s FA2注释头=%s"
          % (r["has_previewpack"], r["has_isomappack5"], r["has_digest"],
             r["fa2_header_comment"]))
        w("  打包段条目数: %s" % json.dumps(r.get("pack_entry_counts", {})))
        if r.get("aux_sections"):
            w("  辅助段行数(触发器等): %s" % json.dumps(r["aux_sections"]))
        for probe in ("Basic", "Header", "Map", "Houses"):
            if "meta_" + probe in r:
                m = r["meta_" + probe]
                keys = ("Name", "Author", "Player", "Width", "Height",
                        "StartX", "StartY", "Size", "LocalSize", "Theater")
                shown = ["%s=%s" % (k, m[k]) for k in keys if k in m]
                if probe == "Houses":
                    shown = ["%s" % v for k, v in list(m.items())]
                w("  [%s] %s" % (probe, "  ".join(shown) if shown else "(空/仅键)"))
        w("  预置小节: 在场=%s 缺席=%s"
          % (r["preset_sections_present"], r["preset_sections_absent"]))
        for sec in PRESET_SECTIONS:
            s = r["presets"][sec]
            if not s.get("present"):
                w("    [%s] 不存在 → 0 条目" % sec)
                continue
            w("    [%s] 条目=%d (未解析行=%d)" % (sec, s["entries"], len(s["unparsed"])))
            w("      按屋: %s" % json.dumps(s["owner_counts"], ensure_ascii=False))
            for o, t in s["owner_types"].items():
                w("        %-14s 型号分布: %s" % (o, json.dumps(t, ensure_ascii=False)))
        if "special_house_presets" in r:
            w("  Special 屋预置(判据核对项): %s"
              % json.dumps(r["special_house_presets"], ensure_ascii=False))
    w("")
    w("-" * 78)
    w("两份 .yrm 结构差集 (ra2bench 92,332B vs out 25,604B)")
    w("  仅 ra2bench 有: %s" % ", ".join(diff["only_in_ra2bench_yrm"]))
    w("  仅 out 有: %s" % ", ".join(diff["only_in_out_yrm"]))
    w("")
    w("-" * 78)
    w("LoadBench 家族出处扫描 (out/loadbench + pristine/* + ra2bench, 只读)")
    w("  ra2bench yrm 的字节孪生件: %s" % (", ".join(twin) if twin else "(无)"))
    for r in family:
        w("  %-58s %8dB  Units=%-5d Infantry=%-5d Structures=%d"
          % (r["path"], r["size_bytes"], r["Units"], r["Infantry"], r["Structures"]))
    w("")
    w("-" * 78)
    w("台账声称核对 (声称 vs 实算)")
    for ch in checks:
        w("  * %s" % ch["claim"])
        w("      声称: %s" % json.dumps(ch["claimed"], ensure_ascii=False))
        w("      实算: %s" % json.dumps(ch["actual"], ensure_ascii=False, sort_keys=False))
        w("      判定: %s" % ch["verdict"])
    w("")
    txt = "\n".join(lines) + "\n"

    json_out = {
        "generated_by": "lead/re_map_preset_decode_20261110/_md_parse.py",
        "mode": "offline disk-only",
        "files": results,
        "yrm_struct_diff": diff,
        "family_scan": family,
        "ra2bench_yrm_byte_twins": twin,
        "claim_checks": checks,
        "summary": summary,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "_md_parse_out.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    with open(os.path.join(OUT_DIR, "_md_parse_out.json"), "w", encoding="utf-8") as f:
        json.dump(json_out, f, ensure_ascii=False, indent=2)
    print(txt)


if __name__ == "__main__":
    main()
