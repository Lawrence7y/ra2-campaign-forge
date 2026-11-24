import os
import struct
from collections import Counter

def main():
    exe_path = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
    out_dir = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W5b_ptr_scan"
    os.makedirs(out_dir, exist_ok=True)

    result_md_path = os.path.join(out_dir, "RESULT.md")
    stdout_txt_path = os.path.join(out_dir, "stdout.txt")

    with open(exe_path, "rb") as f:
        data = f.read()

    file_size = len(data)

    # Parse PE header
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    pe_sig = data[e_lfanew:e_lfanew+4]
    if pe_sig != b"PE\x00\x00":
        raise ValueError(f"Invalid PE signature: {pe_sig}")

    num_sections = struct.unpack_from("<H", data, e_lfanew + 4 + 2)[0]
    opt_hdr_size = struct.unpack_from("<H", data, e_lfanew + 4 + 16)[0]
    opt_magic = struct.unpack_from("<H", data, e_lfanew + 24)[0]
    if opt_magic != 0x10B:
        raise ValueError(f"Expected 32-bit PE (0x10B), got: {hex(opt_magic)}")

    image_base = struct.unpack_from("<I", data, e_lfanew + 24 + 28)[0]

    sec_tbl_offset = e_lfanew + 24 + opt_hdr_size
    sections = []
    for i in range(num_sections):
        sec_off = sec_tbl_offset + i * 40
        sec_bytes = data[sec_off:sec_off+40]
        name = sec_bytes[:8].rstrip(b"\x00").decode("latin-1", errors="replace")
        vsize, va_rva, raw_size, raw_ptr = struct.unpack_from("<IIII", sec_bytes, 8)
        sections.append({
            "name": name,
            "vsize": vsize,
            "rva": va_rva,
            "raw_size": raw_size,
            "raw_ptr": raw_ptr,
        })

    def offset_to_sec_and_va(off):
        for s in sections:
            if s["raw_ptr"] <= off < s["raw_ptr"] + s["raw_size"]:
                rva = off - s["raw_ptr"] + s["rva"]
                va = image_base + rva
                return s["name"], va
        return "(none)", None

    TARGET_MIN = 0x00606800
    TARGET_MAX = 0x00607F40

    hits = []  # list of (off, val, sec, va)

    for off in range(0, file_size - 3):
        v = struct.unpack_from("<I", data, off)[0]
        if TARGET_MIN <= v <= TARGET_MAX:
            sec, va = offset_to_sec_and_va(off)
            hits.append((off, v, sec, va))

    total_hits = len(hits)
    by_section = Counter(h[2] for h in hits)

    # Contiguous segments (adjacent hit offset delta <= 4 bytes, len >= 3)
    segments_le4 = []
    if hits:
        curr_seg = [hits[0]]
        for h in hits[1:]:
            if h[0] - curr_seg[-1][0] <= 4:
                curr_seg.append(h)
            else:
                if len(curr_seg) >= 3:
                    segments_le4.append(curr_seg)
                curr_seg = [h]
        if len(curr_seg) >= 3:
            segments_le4.append(curr_seg)

    # Exact 4-byte stride segments (off[i] - off[i-1] == 4, len >= 3)
    segments_eq4 = []
    if hits:
        curr_seg = [hits[0]]
        for h in hits[1:]:
            if h[0] - curr_seg[-1][0] == 4:
                curr_seg.append(h)
            else:
                if len(curr_seg) >= 3:
                    segments_eq4.append(curr_seg)
                curr_seg = [h]
        if len(curr_seg) >= 3:
            segments_eq4.append(curr_seg)

    # Generate RESULT.md content
    lines = []
    lines.append("# Pointer Scan Result")
    lines.append("")
    lines.append(f"- **Target Binary**: `{exe_path}` ({file_size:,} bytes)")
    lines.append(f"- **ImageBase**: `0x{image_base:08X}`")
    lines.append(f"- **Target Range**: `[0x{TARGET_MIN:08X}, 0x{TARGET_MAX:08X}]` (inclusive)")
    lines.append(f"- **Scan Mode**: 1-byte sliding window (`struct.unpack_from('<I', data, off)`)")
    lines.append("")
    lines.append("## 1. 命中总数与节分布")
    lines.append("")
    lines.append(f"- **命中总数**: **{total_hits}**")
    lines.append("")
    lines.append("| 节名称 (Section) | 命中数量 | 节内 Raw 范围 | 节内 VA 范围 |")
    lines.append("|---|---|---|---|")
    for s in sections:
        cnt = by_section.get(s["name"], 0)
        s_raw_start = s["raw_ptr"]
        s_raw_end = s["raw_ptr"] + s["raw_size"]
        s_va_start = image_base + s["rva"]
        s_va_end = s_va_start + s["vsize"]
        lines.append(f"| `{s['name']}` | {cnt} | `0x{s_raw_start:08X}..0x{s_raw_end:08X}` | `0x{s_va_start:08X}..0x{s_va_end:08X}` |")
    if "(none)" in by_section:
        lines.append(f"| `(none)` | {by_section['(none)']} | 外挂/头/间断 | - |")
    lines.append("")

    lines.append("## 2. 连续段检测 (相邻命中间隔 <= 4 字节，长度 >= 3)")
    lines.append("")
    if not segments_le4:
        lines.append("**未发现任何 >=3 个连续命中的段（间隔 <= 4 字节）。不存在该区间的连续指针表。**")
    else:
        lines.append(f"共发现 **{len(segments_le4)}** 个连续段（间隔 <= 4 字节）：")
        lines.append("")
        for idx, seg in enumerate(segments_le4, 1):
            start_off, start_val, start_sec, start_va = seg[0]
            end_off, end_val, end_sec, end_va = seg[-1]
            lines.append(f"### 段 {idx} (长度: {len(seg)})")
            lines.append(f"- **节**: `{start_sec}`")
            lines.append(f"- **Raw 范围**: `0x{start_off:08X}..0x{end_off:08X}`")
            lines.append(f"- **VA 范围**: `0x{start_va:08X}..0x{end_va:08X}`")
            lines.append("- **条目详情**:")
            lines.append("| 序号 | 文件偏移 (Raw) | VA | 目标值 (Target Value) |")
            lines.append("|---|---|---|---|")
            for i, (off, val, sec, va) in enumerate(seg, 1):
                lines.append(f"| {i} | `0x{off:08X}` | `0x{va:08X}` | `0x{val:08X}` |")
            lines.append("")

    lines.append("### 精确步长 == 4 字节的指针表 (off[i] - off[i-1] == 4)")
    if not segments_eq4:
        lines.append("- **严格 4 字节步长连续段 (>=3 项)**: **无**")
    else:
        lines.append(f"- **严格 4 字节步长连续段 (>=3 项)**: 共 {len(segments_eq4)} 段")
        for idx, seg in enumerate(segments_eq4, 1):
            lines.append(f"  - 段 {idx}: {len(seg)} 项，VA `0x{seg[0][3]:08X}..0x{seg[-1][3]:08X}` in `{seg[0][2]}`")
    lines.append("")

    lines.append("## 3. 前 40 条命中详情")
    lines.append("")
    lines.append("| 序号 | 文件偏移 (Raw) | 节 | VA | 命中值 (DWORD) |")
    lines.append("|---|---|---|---|---|")
    for i, (off, val, sec, va) in enumerate(hits[:40], 1):
        lines.append(f"| {i} | `0x{off:08X}` | `{sec}` | `0x{va:08X}` | `0x{val:08X}` |")

    if total_hits > 40:
        lines.append(f"| ... | *(剩余 {total_hits - 40} 条省略)* | | | |")
    lines.append("")

    result_content = "\n".join(lines) + "\n"
    with open(result_md_path, "w", encoding="utf-8") as f:
        f.write(result_content)

    # stdout output
    stdout_summary = []
    stdout_summary.append(f"Total hits: {total_hits}")
    stdout_summary.append("By section: " + ", ".join(f"{k}: {v}" for k, v in by_section.items()))
    stdout_summary.append(f"Segments (delta <= 4, len >= 3): {len(segments_le4)}")
    stdout_summary.append(f"Segments (stride == 4, len >= 3): {len(segments_eq4)}")
    if segments_le4:
        for idx, seg in enumerate(segments_le4, 1):
            stdout_summary.append(f"  Segment {idx}: len={len(seg)}, VA=0x{seg[0][3]:08X}..0x{seg[-1][3]:08X} in {seg[0][2]}")
    else:
        stdout_summary.append("  No continuous pointer table segment found.")

    stdout_str = "\n".join(stdout_summary) + "\n"
    print(stdout_str)
    with open(stdout_txt_path, "w", encoding="utf-8") as f:
        f.write(stdout_str)

if __name__ == "__main__":
    main()
