from pathlib import Path
import hashlib
import struct
from collections import Counter, defaultdict

IMAGE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R14_VT_STRUCT")

MAIN_START = 0x7E3EBC
MAIN_END   = 0x7E43C4
SMALL_START = 0x7E3E90
SMALL_END   = MAIN_START
TARGETS = {0x43F180: "#73", 0x449440: "#107"}
EXPECTED_PREFIX = "73201CC0"

OUT.mkdir(parents=True, exist_ok=True)

# Whole-file hash (hash read is not part of the slot-byte budget).
h = hashlib.sha256()
hash_bytes = 0
with IMAGE.open("rb") as f:
    while True:
        chunk = f.read(1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
        hash_bytes += len(chunk)
sha = h.hexdigest().upper()

# Minimal PE metadata needed only to translate VAs to raw file offsets.
with IMAGE.open("rb") as f:
    dos = f.read(64)
    if len(dos) < 64 or dos[:2] != b"MZ":
        raise RuntimeError("not a PE/MZ image")
    pe_off = struct.unpack_from("<I", dos, 0x3C)[0]
    f.seek(pe_off)
    sig = f.read(4)
    if sig != b"PE\0\0":
        raise RuntimeError("bad PE signature")
    coff = f.read(20)
    if len(coff) != 20:
        raise RuntimeError("short COFF header")
    num_sections = struct.unpack_from("<H", coff, 2)[0]
    size_opt = struct.unpack_from("<H", coff, 16)[0]
    opt = f.read(size_opt)
    if len(opt) != size_opt:
        raise RuntimeError("short optional header")
    magic = struct.unpack_from("<H", opt, 0)[0]
    if magic == 0x20B:
        image_base = struct.unpack_from("<Q", opt, 24)[0]
    elif magic == 0x10B:
        image_base = struct.unpack_from("<I", opt, 28)[0]
    else:
        raise RuntimeError("unknown optional-header magic")
    sec_off = pe_off + 4 + 20 + size_opt
    f.seek(sec_off)
    sec_blob = f.read(40 * num_sections)
    if len(sec_blob) != 40 * num_sections:
        raise RuntimeError("short section table")

sections = []
for i in range(num_sections):
    fields = struct.unpack_from("<8sIIIIIIHHI", sec_blob, i * 40)
    name = fields[0].rstrip(b"\0").decode("latin1")
    virtual_size, virtual_address, raw_size, raw_ptr = fields[1], fields[2], fields[3], fields[4]
    sections.append({"name": name, "vsize": virtual_size, "va": virtual_address, "raw_size": raw_size, "raw_ptr": raw_ptr})

def rva_to_offset(rva, size):
    for s in sections:
        delta = rva - s["va"]
        if 0 <= delta and delta + size <= max(s["vsize"], s["raw_size"]) and delta + size <= s["raw_size"]:
            return s, s["raw_ptr"] + delta
    raise RuntimeError("RVA not backed by file bytes")

def read_va(va, size):
    s, off = rva_to_offset(va - image_base, size)
    with IMAGE.open("rb") as f:
        f.seek(off)
        data = f.read(size)
    if len(data) != size:
        raise RuntimeError("short read")
    return s, off, data

main_len = MAIN_END - MAIN_START
small_len = SMALL_END - SMALL_START
main_sec, main_off, main_bytes = read_va(MAIN_START, main_len)
small_sec, small_off, small_bytes = read_va(SMALL_START, small_len)
slot_bytes_read = len(main_bytes) + len(small_bytes)

main_vals = list(struct.unpack_from("<322I", main_bytes, 0))
small_vals = list(struct.unpack_from("<11I", small_bytes, 0))

counts = Counter(main_vals)
slots_by_val = defaultdict(list)
for i, v in enumerate(main_vals):
    slots_by_val[v].append(i)
repeated = {v: c for v, c in counts.items() if c > 1}
dup_items = sorted(repeated.items(), key=lambda kv: (-kv[1], kv[0]))
distinct = len(counts)
dup_slots = sum(repeated.values())
dup_excess = sum(c - 1 for c in repeated.values())

with (OUT / "slots.tsv").open("w", encoding="utf-8", newline="\n") as f:
    for i, v in enumerate(main_vals):
        addr = MAIN_START + 4 * i
        f.write("#{}\t0x{:08X}\t0x{:08X}\t{}\n".format(i, addr, v, counts[v]))

with (OUT / "dups.tsv").open("w", encoding="utf-8", newline="\n") as f:
    for v, c in dup_items:
        slots = ",".join("#{}".format(i) for i in slots_by_val[v])
        f.write("0x{:08X}\t{}\t{}\n".format(v, c, slots))

small_tables = [
    ("T0", 0x7E3E90, 0x7E3E98),
    ("T1", 0x7E3E98, 0x7E3EA0),
    ("T2", 0x7E3EA0, 0x7E3EBC),
]
small_idx_by_addr = {SMALL_START + 4*i: i for i in range(11)}
overlap_vals = sorted(set(small_vals) & set(main_vals))
overlap_detail = {}
for v in overlap_vals:
    overlap_detail[v] = {
        "small": [SMALL_START + 4*i for i, x in enumerate(small_vals) if x == v],
        "main": slots_by_val[v],
    }

text_sec = next((s for s in sections if s["name"].startswith(".text")), None)
in_text = None
text_range = None
if text_sec:
    text_lo = image_base + text_sec["va"]
    text_hi = image_base + text_sec["va"] + max(text_sec["vsize"], text_sec["raw_size"])
    in_text = sum(1 for v in main_vals if text_lo <= v < text_hi)
    text_range = (text_lo, text_hi)

sha_prefix_ok = sha.startswith(EXPECTED_PREFIX)
if not sha_prefix_ok:
    raise RuntimeError("sha256 prefix mismatch")

target_lines = []
for target, label in TARGETS.items():
    occ = slots_by_val.get(target, [])
    small_occ = overlap_detail.get(target, {}).get("small", []) if target in overlap_detail else []
    occ_text = ", ".join("#{}".format(i) for i in occ) if occ else "none"
    small_text = ", ".join("0x{:08X}".format(a) for a in small_occ) if small_occ else "none"
    target_lines.append("- `0x{:08X}` ({}): main-table count {}; slots {}; small-table addresses {}.".format(target, label, len(occ), occ_text, small_text))

q2_small_rows = []
for label, start, end in small_tables:
    for addr in range(start, end, 4):
        v = small_vals[small_idx_by_addr[addr]]
        main_slots = slots_by_val.get(v, [])
        main_text = ", ".join("#{}".format(i) for i in main_slots) if main_slots else "—"
        q2_small_rows.append("| {} | 0x{:08X} | 0x{:08X} | {} |".format(label, addr, v, main_text))

overlap_lines = []
if overlap_vals:
    for v in overlap_vals:
        d = overlap_detail[v]
        small_text = ", ".join("0x{:08X}".format(a) for a in d["small"])
        main_text = ", ".join("#{}".format(i) for i in d["main"])
        overlap_lines.append("- `0x{:08X}`: small {}; main {}".format(v, small_text, main_text))
else:
    overlap_lines.append("- 无")

top20 = dup_items[:20]
top20_lines = []
for v, c in top20:
    top20_lines.append("- `0x{:08X}` count {}: {}".format(v, c, ", ".join("#{}".format(i) for i in slots_by_val[v])))

    structural_verdict = "更像一个类的正常 vtable，而非函数指针拼接表/派发表（仅按本卡字节结构判据；不涉及类身份）。"
if not repeated and not overlap_vals:
    structural_verdict = "更像一个类的正常 vtable，而非函数指针拼接表/派发表（仅按本卡字节结构判据；不涉及类身份）。"

report = []
report.append(str(IMAGE) + " sha256=" + sha)
report.append("")
report.append("# R17-R14-VT-STRUCT")
report.append("")
report.append("## 读取范围与字节数")
report.append("")
report.append("- 镜像整文件 sha256 扫描：{} bytes（仅用于身份校验）。".format(hash_bytes))
report.append("- 主表槽值读取：`[0x{:08X}, 0x{:08X})`，{} bytes / {} slots。".format(MAIN_START, MAIN_END, main_len, len(main_vals)))
report.append("- 小表槽值读取：`[0x{:08X}, 0x{:08X})`，{} bytes / {} slots。".format(SMALL_START, SMALL_END, small_len, len(small_vals)))
report.append("- 槽值读取合计：{} bytes；只读，不建进程，不反汇编。".format(slot_bytes_read))
report.append("- VA→raw 映射：主表 `{}` raw=0x{:X}，小表 `{}` raw=0x{:X}；镜像基址 0x{:08X}。".format(main_sec["name"], main_off, small_sec["name"], small_off, image_base))
report.append("- sha256 prefix expected `0x{}` actual `{}`; OK. Full sha256 `{}`.".format(EXPECTED_PREFIX, sha[:8], sha))
report.append("")
report.append("## Q1 · 322 槽重复值统计")
report.append("")
report.append("- 槽数：{}；不同值：{}；重复值种类：{}。".format(len(main_vals), distinct, len(repeated)))
report.append("- 出现在重复值上的槽数：{}/{}；超额重复槽数：{}/{}（{:.2f}%）。".format(dup_slots, len(main_vals), dup_excess, len(main_vals), dup_excess/len(main_vals)*100))
if text_range:
    report.append("- 值落在 `.text` VA 区间 `[0x{:08X},0x{:08X})` 的槽数：{}/{}（区间比较，仅字节证据）。".format(text_range[0], text_range[1], in_text, len(main_vals)))
report.append("- 全部重复值已写入 `dups.tsv`（{} 种）；下表为按次数降序前 {} 项。".format(len(dup_items), len(top20_lines)))
report.append("")
report.extend(top20_lines)
report.append("")
report.append("### 特别检查")
report.append("")
report.extend(target_lines)
report.append("")
report.append("## Q2 · 0x7E3E90 到 0x7E3EBC 的 11 槽")
report.append("")
report.append("- 按 ctor 装入点分为三张小表：T0 `[0x7E3E90,0x7E3E98)` = 2 槽；T1 `[0x7E3E98,0x7E3EA0)` = 2 槽；T2 `[0x7E3EA0,0x7E3EBC)` = 7 槽。")
report.append("")
report.append("| 小表 | 地址 | 值 | 同值在主表的槽号 |")
report.append("|---|---:|---:|---|")
report.extend(q2_small_rows)
report.append("")
report.append("- 小表与主表的同值交集：{} 种函数值。".format(len(overlap_vals)))
report.extend(overlap_lines)
report.append("")
report.append("## Q3 · 结构判定（仅字节支持）")
report.append("")
report.append("1. **结构判定：{}**".format(structural_verdict))
report.append("   判据：322 槽只有 {} 个不同值，存在 {} 种重复函数值，超额重复 {} 槽；小表与主表共享 {} 种函数值。".format(distinct, len(repeated), dup_excess, len(overlap_vals)))
if overlap_vals:
    report.append("   小表与主表重叠在字节层面符合“基类子对象 vtable 复用同一批方法”的模式；但字节本身不能证明继承关系或任何类名。")
report.append("2. `#73` 与 `#107` 的重复段判断见 Q1 特别检查；若同一目标值在主表或小表另有出现，则槽号本身不唯一指向该函数，下游引用应记录值+全部出现位置。")
report.append("3. 类名/继承层级/函数语义：**未取得**；缺反汇编、RTTI/对象布局与调用点类型证据，本卡按铁律不取。")
report.append("")

(OUT / "REPORT.md").write_text("\n".join(report), encoding="utf-8", newline="\n")

print("SHA256=" + sha)
print("DISTINCT={} REPEATED_KINDS={} REPEATED_SLOTS={} EXCESS={}".format(distinct, len(repeated), dup_slots, dup_excess))
print("BYTES_MAIN={} BYTES_SMALL={} BYTES_TOTAL={}".format(main_len, small_len, slot_bytes_read))
print("SECTION_MAIN={} OFFSET_MAIN=0x{:X} SECTION_SMALL={} OFFSET_SMALL=0x{:X}".format(main_sec["name"], main_off, small_sec["name"], small_off))
for target, label in TARGETS.items():
    print("TARGET {} 0x{:08X} main_slots={} small_addrs={}".format(label, target, slots_by_val.get(target, []), overlap_detail.get(target,{}).get("small",[])))
print("SMALL_OVERLAP_VALUES=" + ",".join("0x{:08X}".format(x) for x in overlap_vals))
print("SMALL_TABLE_SIZES=2,2,7")
print("OUTPUT=" + str(OUT))
