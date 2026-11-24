from pathlib import Path
import hashlib
import struct

CANONICAL = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
PATCHED = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35R\work\run\gamemd.exe")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_IMG_PIN")
EXPECTED_CANONICAL = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
OUT.mkdir(parents=True, exist_ok=True)

def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()

def hx(n):
    return "0x%X" % n

def parse_pe(data):
    if data[:2] != b"MZ":
        raise ValueError("missing MZ")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew:e_lfanew + 4] != b"PE\0\0":
        raise ValueError("missing PE signature")
    num_sections = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    size_opt = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    opt = e_lfanew + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    if magic == 0x10B:
        image_base = struct.unpack_from("<I", data, opt + 28)[0]
    elif magic == 0x20B:
        image_base = struct.unpack_from("<Q", data, opt + 24)[0]
    else:
        raise ValueError("unknown optional magic " + hx(magic))
    size_headers = struct.unpack_from("<I", data, opt + 60)[0]
    sections = []
    sec = opt + size_opt
    for i in range(num_sections):
        off = sec + i * 40
        name = data[off:off + 8].split(b"\0", 1)[0].decode("ascii", "replace")
        virtual_size, virtual_address, size_raw, ptr_raw = struct.unpack_from("<IIII", data, off + 8)
        sections.append({
            "name": name,
            "virtual_size": virtual_size,
            "virtual_address": virtual_address,
            "size_raw": size_raw,
            "ptr_raw": ptr_raw,
        })
    return {"image_base": image_base, "size_headers": size_headers, "sections": sections,
            "section_table_start": sec, "section_table_len": num_sections * 40}

def map_va(pe, off):
    if off < pe["size_headers"]:
        return hx(pe["image_base"] + off)
    for s in pe["sections"]:
        if s["ptr_raw"] <= off < s["ptr_raw"] + s["size_raw"]:
            return hx(pe["image_base"] + s["virtual_address"] + (off - s["ptr_raw"]))
    return "UNMAPPED"

def map_file_off(pe, va):
    rva = va - pe["image_base"]
    if rva < 0:
        return None
    if rva < pe["size_headers"]:
        return rva
    for s in pe["sections"]:
        if s["virtual_address"] <= rva < s["virtual_address"] + s["size_raw"]:
            return s["ptr_raw"] + (rva - s["virtual_address"])
    return None

def bytes_repr(a, b):
    return (" ".join("%02X" % x for x in a), " ".join("%02X" % x for x in b))

def range_repr(a, b):
    if len(a) <= 32:
        return bytes_repr(a, b)
    return (
        " ".join("%02X" % x for x in a[:16]) + " ... " + " ".join("%02X" % x for x in a[-16:]),
        " ".join("%02X" % x for x in b[:16]) + " ... " + " ".join("%02X" % x for x in b[-16:]),
    )

def diff_count(a, b, start, end):
    return sum(1 for i in range(start, end) if a[i] != b[i])

a = CANONICAL.read_bytes()
b = PATCHED.read_bytes()
ha, hb = sha256(a), sha256(b)
pe_a = parse_pe(a)
pe_b = parse_pe(b)

ranges = []
total = 0
start = None
common = min(len(a), len(b))
for i in range(common):
    if a[i] != b[i]:
        total += 1
        if start is None:
            start = i
    elif start is not None:
        ranges.append((start, i))
        start = None
if start is not None:
    ranges.append((start, common))
if len(a) != len(b):
    ranges.append((common, max(len(a), len(b))))
    total += abs(len(a) - len(b))

diff_lines = ["file_off\tva\tlen\tbytes_in_canonical\tbytes_in_patched"]
for s, e in ranges:
    ca, cb = range_repr(a[s:e], b[s:e])
    diff_lines.append(hx(s) + "\t" + map_va(pe_a, s) + "\t" + str(e - s) + "\t" + ca + "\t" + cb)
(OUT / "diff_ranges.tsv").write_text("\n".join(diff_lines) + "\n", encoding="utf-8")

(OUT / "hashes.tsv").write_text(
    str(CANONICAL) + "\t" + str(len(a)) + "\t" + ha + "\n" +
    str(PATCHED) + "\t" + str(len(b)) + "\t" + hb + "\n", encoding="utf-8"
)

regions = [
    ("range", "0x6F2B40-0x6F3267", 0x6F2B40, 0x6F3267),
    ("range", "0x6F4300-0x6F44F0", 0x6F4300, 0x6F44F0),
    ("range", "0x43B680-0x43B740", 0x43B680, 0x43B740),
    ("range", "0x43B740-0x43BCDE", 0x43B740, 0x43BCDE),
    ("range", "0x43BCF0-0x43C0D0", 0x43BCF0, 0x43C0D0),
]
for addr in [0x6F322F, 0x6F3237, 0x43B74B, 0x43B688, 0x6F2B46, 0x6F430B, 0x65A7E8, 0x65A753]:
    regions.append(("single8", hx(addr), addr, addr + 8))

reg_lines = ["kind\tname\tva_start\tva_end\tfile_start\tfile_end\tlen\tdiff_bytes\tidentical"]
reg_results = []
for kind, name, vs, ve in regions:
    fo = map_file_off(pe_a, vs)
    fe = map_file_off(pe_a, ve)
    if fo is None or fe is None:
        reg_results.append(False)
        reg_lines.append(kind + "\t" + name + "\t" + hx(vs) + "\t" + hx(ve) + "\tUNMAPPED\tUNMAPPED\t" + str(ve - vs) + "\tNA\tDIFF")
        continue
    dc = diff_count(a, b, fo, fe)
    same = dc == 0
    reg_results.append(same)
    reg_lines.append(kind + "\t" + name + "\t" + hx(vs) + "\t" + hx(ve) + "\t" + hx(fo) + "\t" + hx(fe) + "\t" + str(ve - vs) + "\t" + str(dc) + "\t" + ("same" if same else "DIFF"))
(OUT / "region_check.tsv").write_text("\n".join(reg_lines) + "\n", encoding="utf-8")

if all(reg_results):
    conclusion = "能：本卡指定的关心 VA 区间与单点 8 字节邻域在两文件中均为同字节；已发现的差异均不在指定关心区间内。"
elif any(reg_results):
    conclusion = "部分能：本卡指定区间中仅部分为同字节；存在落在本卡指定关心区间内的差异，不能整体无损平移。"
else:
    conclusion = "不能：本卡指定关心区间内存在字节差异，上一轮在副本上的字节结论不能无损平移到基准镜像。"

sections_same = (
    pe_a["section_table_start"] == pe_b["section_table_start"] and
    a[pe_a["section_table_start"]:pe_a["section_table_start"] + pe_a["section_table_len"]] ==
    b[pe_b["section_table_start"]:pe_b["section_table_start"] + pe_b["section_table_len"]]
)

rep = []
rep.append(ha)
rep.append("")
rep.append("# R17-IMG-PIN 报告")
rep.append("")
rep.append("- canonical/基准: " + str(CANONICAL))
rep.append("- patched/副本: " + str(PATCHED))
rep.append("- 基准 sha256 期望匹配: " + str(ha == EXPECTED_CANONICAL).lower())
rep.append("- 副本 sha256 期望前缀 36a87577: " + str(hb.lower().startswith("36a87577")).lower())
rep.append("")
rep.append("## 第 1 步 · 钉哈希")
rep.append("")
rep.append("| file | size | sha256 |")
rep.append("|---|---:|---|")
rep.append("| canonical | " + str(len(a)) + " | " + ha + " |")
rep.append("| patched | " + str(len(b)) + " | " + hb + " |")
rep.append("")
rep.append("## 第 2 步 · 全文件字节差异")
rep.append("")
rep.append("- 差异字节总数: " + str(total))
rep.append("- 差异区间个数: " + str(len(ranges)))
rep.append("- PE image base: " + hx(pe_a["image_base"]) + "; section table identical between files: " + str(sections_same).lower())
rep.append("- VA 由 canonical 的 PE 节表换算；区间按半开 [start,end) 计。")
rep.append("")
rep.append("| # | file_off_start | file_off_end | len | VA_start | VA_end | bytes_in_canonical | bytes_in_patched |")
rep.append("|---:|---|---|---:|---|---|---|---|")
for idx, (s, e) in enumerate(ranges, 1):
    ca, cb = range_repr(a[s:e], b[s:e])
    va_s = map_va(pe_a, s)
    va_e = hx(int(va_s, 16) + (e - s)) if va_s != "UNMAPPED" else "UNMAPPED"
    rep.append("| " + str(idx) + " | " + hx(s) + " | " + hx(e) + " | " + str(e - s) + " | " + va_s + " | " + va_e + " | " + ca + " | " + cb + " |")
rep.append("")
rep.append("完整机器可读差异表见 diff_ranges.tsv；长度 >32 的区间按首 16 字节 ... 末 16 字节显示。")
rep.append("")
rep.append("## 第 3 步 · 指定区间同字节检查")
rep.append("")
rep.append("指定地址按 VA 处理；单点 8 字节邻域按 VA 的 [addr, addr+8) 计算；比较前经 PE 节表换算为文件偏移。")
rep.append("")
rep.append("| kind | name | VA_start | VA_end | file_start | file_end | len | diff_bytes | identical |")
rep.append("|---|---|---|---|---|---|---:|---:|---|")
for line in reg_lines[1:]:
    cells = line.split("\t")
    rep.append("| " + " | ".join(cells) + " |")
rep.append("")
rep.append("## 结论")
rep.append("")
rep.append(conclusion)
rep.append("")
(OUT / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")

print("canonical_sha=" + ha)
print("patched_sha=" + hb)
print("canonical_size=" + str(len(a)))
print("patched_size=" + str(len(b)))
print("diff_bytes=" + str(total))
print("diff_ranges=" + str(len(ranges)))
print("all_regions_same=" + str(all(reg_results)).lower())
print("conclusion=" + conclusion)
